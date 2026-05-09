#!/usr/bin/env python3
"""
Phase 2T parallel adaptive gap closer for the Theorem III lower-collar proof.

This script closes a difficult K-interval by adaptively subdividing it into
smaller overlapping pieces and running the existing Phase 2N -> Phase 2O ->
Phase 2P pipeline on many pieces in parallel.

It intentionally does not implement any new theorem lemma. It orchestrates the
already theorem-facing scripts:

  scripts/audit/run_lower_anchor_phase2n_batch.py
  scripts/audit/run_lower_anchor_phase2o_radius_tail_scan.py
  scripts/audit/run_lower_anchor_phase2p_modewise_tail_scan.py
  scripts/audit/run_lower_anchor_phase2q_chain_assembler.py

Typical use for the current gap:

  python scripts/audit/run_lower_anchor_phase2t_parallel_gap_closer.py \
    --label collar_012b1 \
    --K-lo 0.9662501 \
    --K-hi 0.9663752 \
    --seed-json artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_collar_012a_N1024_os16_sg0p0001.json \
    --initial-pieces 16 \
    --max-depth 3 \
    --workers 64

Design goals:
  * embarrassingly-parallel execution across independent sub-collars;
  * strict promotion only if Phase 2P exports theorem_facing=true and
    promotion_allowed=true;
  * resumable output paths;
  * automatic recursive split for failed pieces;
  * final Phase 2Q assembly of the split gap if every leaf closes.
"""

import argparse
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


DEFAULT_RADIUS_MULTIPLIERS = (
    "1.0,1.02,1.05,1.08,1.1,1.12,1.14,1.15,1.16,1.17,1.18,"
    "1.19,1.2,1.21,1.22,1.23,1.24,1.25,1.3,1.35,1.4,1.5,"
    "1.75,2.0,2.25,2.5,2.75,3.0,3.5,4.0,5.0,6.0"
)
DEFAULT_SIGMA_VALUES_2O = "0.0001,0.00001,0.000005,0.0000025,0.000001,0.00000075,0.0000005,0.00000025,0.0000001"
DEFAULT_SIGMA_VALUES_2P = "0.0001,0.000075,0.00005,0.000025,0.00001,0.000005,0.0000025,0.000001,0.00000075,0.0000005,0.00000025,0.0000001"
DEFAULT_TAIL_CUTOFFS = "1024,1536,2048,3072,4096,8192,16384,32768"
DEFAULT_TAIL_BANDS = "0.5,0.65,0.75,0.85"
DEFAULT_TAIL_SAFETY = "2,4,8,16"


def safe_label(text):
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(text)).strip("_")


def ensure_dirs():
    for p in [
        "artifacts/proof_audit/replay",
        "artifacts/proof_audit/lower_corridor/phase2t_parallel",
        "artifacts/proof_audit/lower_corridor/phase2n_probes",
        "artifacts/proof_audit/lower_corridor/phase2o_tail_radius",
        "artifacts/proof_audit/lower_corridor/phase2p_modewise_tail",
        "artifacts/proof_audit/lower_corridor/phase2q_chain",
        "tables/proof_audit/lower_corridor/phase2t_parallel",
        "tables/proof_audit/lower_corridor/phase2o_tail_radius",
        "tables/proof_audit/lower_corridor/phase2p_modewise_tail",
        "tables/proof_audit/lower_corridor/phase2q_chain",
    ]:
        Path(p).mkdir(parents=True, exist_ok=True)


def parse_float_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [float(x) for x in value]
    return [float(x.strip()) for x in str(value).split(",") if x.strip()]


def format_float(x):
    # Keep enough precision to preserve exact-looking K endpoints while avoiding
    # unreadable binary-representation strings.
    return f"{float(x):.12f}".rstrip("0").rstrip(".")


def load_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def theorem_ready_candidate(path):
    try:
        d = load_json(path)
    except Exception:
        return False
    row = d.get("selected_phase2p_row", {})
    return bool(
        d.get("theorem_facing") is True
        and d.get("promotion_allowed") is True
        and not d.get("failure_fields")
        and row.get("theorem_ready") is True
        and not row.get("failure_reasons")
    )


def segment_from_candidate(path):
    try:
        d = load_json(path)
        s = (d.get("anchor_segments") or [{}])[0]
        return float(s.get("K_lo")), float(s.get("K_hi"))
    except Exception:
        return None, None


def selected_row(path):
    try:
        d = load_json(path)
        return d.get("selected_phase2p_row", {}) or {}
    except Exception:
        return {}


def interval_pieces(K_lo, K_hi, pieces, overlap=1e-7, label_prefix="piece", depth=0):
    """Return overlapping interval specs covering [K_lo, K_hi]."""
    pieces = int(pieces)
    if pieces < 1:
        raise ValueError("pieces must be >= 1")
    width = (float(K_hi) - float(K_lo)) / pieces
    out = []
    for i in range(pieces):
        base_lo = float(K_lo) + i * width
        base_hi = float(K_lo) + (i + 1) * width
        lo = base_lo if i == 0 else base_lo - overlap
        hi = base_hi if i == pieces - 1 else base_hi + overlap
        mid = 0.5 * (lo + hi)
        out.append({
            "depth": int(depth),
            "piece_index": int(i),
            "piece_count": int(pieces),
            "label": f"{label_prefix}_d{int(depth):02d}_p{i:04d}",
            "base_K_lo": base_lo,
            "base_K_hi": base_hi,
            "K_lo": lo,
            "K_hi": hi,
            "K_mid": mid,
            "partial_final": False,
        })
    return out


def split_failed_piece(piece, split_factor, overlap):
    prefix = piece["label"]
    return interval_pieces(
        piece["base_K_lo"],
        piece["base_K_hi"],
        int(split_factor),
        overlap=float(overlap),
        label_prefix=prefix,
        depth=int(piece.get("depth", 0)) + 1,
    )


def make_env():
    env = os.environ.copy()
    # Prevent BLAS/OpenMP oversubscription on CPU nodes.
    for k in [
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "BLIS_NUM_THREADS",
    ]:
        env[k] = "1"
    return env


def run_cmd(cmd, log_path, dry_run=False, cwd=None):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    printable = " ".join(str(x) for x in cmd)
    if dry_run:
        log_path.write_text("[dry-run] " + printable + "\n")
        return {"returncode": 0, "duration_seconds": 0.0, "cmd": cmd, "log_path": str(log_path), "dry_run": True}
    t0 = time.time()
    proc = subprocess.run(
        [str(x) for x in cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=cwd,
        env=make_env(),
    )
    duration = time.time() - t0
    log_path.write_text(proc.stdout or "")
    return {"returncode": proc.returncode, "duration_seconds": duration, "cmd": cmd, "log_path": str(log_path), "dry_run": False}


def piece_paths(label):
    label = safe_label(label)
    return {
        "phase2n_summary": f"artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_{label}_phase2n_batch_summary.json",
        "phase2n_single": f"artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_{label}_N1024_os16_sg0p0001.json",
        "phase2o_scan": f"artifacts/proof_audit/lower_corridor/phase2o_tail_radius/phase2o_{label}_tail_radius_scan.json",
        "phase2o_csv": f"tables/proof_audit/lower_corridor/phase2o_tail_radius/phase2o_{label}_tail_radius_scan.csv",
        "phase2o_candidate": f"artifacts/proof_audit/lower_corridor/phase2o_tail_radius/phase2o_{label}_tail_radius_candidate.json",
        "phase2p_scan": f"artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_{label}_modewise_tail_scan.json",
        "phase2p_csv": f"tables/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_{label}_modewise_tail_scan.csv",
        "phase2p_candidate": f"artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_{label}_modewise_tail_candidate.json",
        "ready_candidate": f"artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_{label}_THEOREM_READY_candidate.json",
        "log_2n": f"artifacts/proof_audit/replay/phase2t_{label}_2n.log",
        "log_2o": f"artifacts/proof_audit/replay/phase2t_{label}_2o.log",
        "log_2p": f"artifacts/proof_audit/replay/phase2t_{label}_2p.log",
    }


def phase2n_command(args, piece, paths, seed_json):
    return [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2n_batch.py",
        "--segment-id", f"phase2n_{safe_label(piece['label'])}",
        "--K-lo", format_float(piece["K_lo"]),
        "--K-hi", format_float(piece["K_hi"]),
        "--K-mid", format_float(piece["K_mid"]),
        "--N-values", args.N_values,
        "--oversample-factors", args.oversample_factors,
        "--sigma-caps", args.sigma_caps,
        "--timeout-seconds", str(args.timeout_seconds),
        "--skip-existing",
        "--seed-json", seed_json,
    ]


def phase2o_command(args, paths):
    return [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2o_radius_tail_scan.py",
        "--input", paths["phase2n_summary"],
        "--out", paths["phase2o_scan"],
        "--csv", paths["phase2o_csv"],
        "--candidate-out", paths["phase2o_candidate"],
        "--radius-multipliers", args.radius_multipliers,
        "--sigma-values", args.sigma_values_2o,
        "--tail-band-fractions", args.tail_band_fractions,
        "--tail-safety-factors", args.tail_safety_factors,
    ]


def phase2p_command(args, paths):
    return [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2p_modewise_tail_scan.py",
        "--input", paths["phase2o_candidate"],
        "--out", paths["phase2p_scan"],
        "--csv", paths["phase2p_csv"],
        "--candidate-out", paths["phase2p_candidate"],
        "--sigma-values", args.sigma_values_2p,
        "--tail-cutoffs", args.tail_cutoffs,
        "--oversample-factors", args.oversample_factors,
    ]


def run_one_piece(args, piece):
    label = safe_label(piece["label"])
    paths = piece_paths(label)
    result = {
        "label": piece["label"],
        "safe_label": label,
        "depth": piece.get("depth"),
        "K_lo": piece["K_lo"],
        "K_hi": piece["K_hi"],
        "K_mid": piece["K_mid"],
        "base_K_lo": piece.get("base_K_lo"),
        "base_K_hi": piece.get("base_K_hi"),
        "paths": paths,
        "commands": [],
        "closed": False,
        "ready_candidate": None,
        "error": None,
    }

    if args.resume and theorem_ready_candidate(paths["ready_candidate"]):
        result["closed"] = True
        result["ready_candidate"] = paths["ready_candidate"]
        result["resumed"] = True
        result["selected_phase2p_row"] = selected_row(paths["ready_candidate"])
        return result

    try:
        cmd = phase2n_command(args, piece, paths, args.seed_json)
        r = run_cmd(cmd, paths["log_2n"], dry_run=args.dry_run)
        result["commands"].append({"phase": "2N", **r})
        if r["returncode"] != 0:
            result["error"] = f"Phase 2N failed with return code {r['returncode']}"
            return result

        cmd = phase2o_command(args, paths)
        r = run_cmd(cmd, paths["log_2o"], dry_run=args.dry_run)
        result["commands"].append({"phase": "2O", **r})
        if r["returncode"] != 0:
            result["error"] = f"Phase 2O failed with return code {r['returncode']}"
            return result

        cmd = phase2p_command(args, paths)
        r = run_cmd(cmd, paths["log_2p"], dry_run=args.dry_run)
        result["commands"].append({"phase": "2P", **r})
        if r["returncode"] != 0:
            result["error"] = f"Phase 2P failed with return code {r['returncode']}"
            return result

        if args.dry_run:
            result["closed"] = False
            result["error"] = "dry-run did not execute candidate production"
            return result

        if theorem_ready_candidate(paths["phase2p_candidate"]):
            shutil.copyfile(paths["phase2p_candidate"], paths["ready_candidate"])
            result["closed"] = True
            result["ready_candidate"] = paths["ready_candidate"]
            result["selected_phase2p_row"] = selected_row(paths["ready_candidate"])
        else:
            result["selected_phase2p_row"] = selected_row(paths["phase2p_candidate"])
            result["failure_summary"] = summarize_failed_candidate(paths["phase2p_candidate"])
        return result
    except Exception as exc:
        result["error"] = repr(exc)
        return result


def summarize_failed_candidate(path):
    try:
        d = load_json(path)
        row = d.get("selected_phase2p_row", {}) or {}
        return {
            "theorem_facing": d.get("theorem_facing"),
            "promotion_allowed": d.get("promotion_allowed"),
            "closure_level": d.get("closure_level"),
            "failure_fields": d.get("failure_fields"),
            "theorem_ready": row.get("theorem_ready"),
            "radii_margin": row.get("radii_margin"),
            "tail_T": row.get("tail_T"),
            "allowable_tail_max": row.get("allowable_tail_max"),
            "finite_contraction_q": row.get("finite_contraction_q"),
            "failure_reasons": row.get("failure_reasons"),
            "model_name": row.get("model_name"),
        }
    except Exception as exc:
        return {"error": repr(exc), "path": path}


def run_level(args, pieces):
    results = []
    if args.workers <= 1:
        for p in pieces:
            print(f"[piece] {p['label']} [{format_float(p['K_lo'])}, {format_float(p['K_hi'])}]", flush=True)
            results.append(run_one_piece(args, p))
        return results

    with ThreadPoolExecutor(max_workers=int(args.workers)) as ex:
        fut_to_piece = {ex.submit(run_one_piece, args, p): p for p in pieces}
        for fut in as_completed(fut_to_piece):
            p = fut_to_piece[fut]
            try:
                r = fut.result()
            except Exception as exc:
                r = {"label": p["label"], "closed": False, "error": repr(exc), "K_lo": p["K_lo"], "K_hi": p["K_hi"]}
            status = "closed" if r.get("closed") else "failed"
            print(f"[piece {status}] {p['label']} [{format_float(p['K_lo'])}, {format_float(p['K_hi'])}]", flush=True)
            results.append(r)
    return results


def write_piece_csv(path, results):
    rows = []
    for r in results:
        row = r.get("selected_phase2p_row") or r.get("failure_summary") or {}
        rows.append({
            "label": r.get("label"),
            "depth": r.get("depth"),
            "K_lo": r.get("K_lo"),
            "K_hi": r.get("K_hi"),
            "closed": r.get("closed"),
            "ready_candidate": r.get("ready_candidate"),
            "error": r.get("error"),
            "model_name": row.get("model_name"),
            "radii_margin": row.get("radii_margin"),
            "tail_T": row.get("tail_T"),
            "allowable_tail_max": row.get("allowable_tail_max"),
            "finite_contraction_q": row.get("finite_contraction_q"),
            "failure_reasons": ";".join(str(x) for x in (row.get("failure_reasons") or [])),
        })
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "label", "depth", "K_lo", "K_hi", "closed", "ready_candidate", "error",
            "model_name", "radii_margin", "tail_T", "allowable_tail_max", "finite_contraction_q", "failure_reasons",
        ])
        writer.writeheader()
        writer.writerows(rows)


def assemble_gap_chain(args, ready_candidates):
    if not ready_candidates:
        return {"assembled": False, "reason": "no ready candidates"}
    label = safe_label(args.label)
    out = f"artifacts/proof_audit/lower_corridor/phase2t_parallel/phase2t_{label}_split_chain_audit.json"
    csv_path = f"tables/proof_audit/lower_corridor/phase2t_parallel/phase2t_{label}_split_chain_segments.csv"
    candidate_out = f"artifacts/proof_audit/lower_corridor/phase2t_parallel/phase2t_{label}_split_chain_candidate.json"
    cmd = [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2q_chain_assembler.py",
    ]
    for c in ready_candidates:
        cmd.extend(["--candidate", c])
    cmd.extend([
        "--expected-start", format_float(args.K_lo),
        "--expected-end", format_float(args.K_hi),
        "--overlap-tolerance", str(args.overlap_tolerance),
        "--out", out,
        "--csv", csv_path,
        "--candidate-out", candidate_out,
    ])
    if args.expected_regime_i_hi is not None:
        cmd.extend(["--expected-regime-i-hi", format_float(args.expected_regime_i_hi)])
    r = run_cmd(cmd, f"artifacts/proof_audit/replay/phase2t_{label}_assemble_gap.log", dry_run=args.dry_run)
    report = {
        "assembled": False,
        "returncode": r.get("returncode"),
        "cmd": r.get("cmd"),
        "log_path": r.get("log_path"),
        "out": out,
        "csv": csv_path,
        "candidate_out": candidate_out,
    }
    if not args.dry_run and Path(candidate_out).exists():
        try:
            d = load_json(candidate_out)
            report["theorem_facing"] = d.get("theorem_facing")
            report["promotion_allowed"] = d.get("promotion_allowed")
            report["failure_fields"] = d.get("failure_fields")
            report["chain_summary"] = d.get("chain_summary")
            report["assembled"] = bool(d.get("theorem_facing") and d.get("promotion_allowed") and not d.get("failure_fields"))
        except Exception as exc:
            report["parse_error"] = repr(exc)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="Phase 2T parallel adaptive gap closer")
    ap.add_argument("--label", required=True, help="Human label for the gap, e.g. collar_012b1")
    ap.add_argument("--K-lo", type=float, required=True)
    ap.add_argument("--K-hi", type=float, required=True)
    ap.add_argument("--seed-json", required=True)
    ap.add_argument("--initial-pieces", type=int, default=8)
    ap.add_argument("--split-factor", type=int, default=2)
    ap.add_argument("--max-depth", type=int, default=3)
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--overlap", type=float, default=1e-7)
    ap.add_argument("--overlap-tolerance", type=float, default=1e-10)
    ap.add_argument("--expected-regime-i-hi", type=float, default=None)
    ap.add_argument("--N-values", default="1024")
    ap.add_argument("--oversample-factors", default="16")
    ap.add_argument("--sigma-caps", default="0.0001")
    ap.add_argument("--timeout-seconds", type=float, default=1200.0)
    ap.add_argument("--radius-multipliers", default=DEFAULT_RADIUS_MULTIPLIERS)
    ap.add_argument("--sigma-values-2o", default=DEFAULT_SIGMA_VALUES_2O)
    ap.add_argument("--sigma-values-2p", default=DEFAULT_SIGMA_VALUES_2P)
    ap.add_argument("--tail-cutoffs", default=DEFAULT_TAIL_CUTOFFS)
    ap.add_argument("--tail-band-fractions", default=DEFAULT_TAIL_BANDS)
    ap.add_argument("--tail-safety-factors", default=DEFAULT_TAIL_SAFETY)
    ap.add_argument("--resume", action="store_true", default=True, help="reuse theorem-ready piece candidates if present")
    ap.add_argument("--no-resume", action="store_false", dest="resume")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-assemble", action="store_true")
    args = ap.parse_args(argv)

    ensure_dirs()
    label = safe_label(args.label)
    summary_path = f"artifacts/proof_audit/lower_corridor/phase2t_parallel/phase2t_{label}_run_summary.json"
    csv_path = f"tables/proof_audit/lower_corridor/phase2t_parallel/phase2t_{label}_pieces.csv"

    print("=" * 80)
    print(f"Phase 2T parallel gap closer: {args.label}")
    print(f"target interval: [{format_float(args.K_lo)}, {format_float(args.K_hi)}]")
    print(f"initial pieces: {args.initial_pieces}; max depth: {args.max_depth}; workers: {args.workers}")
    print("=" * 80)

    all_results = []
    closed_results = []
    pending = interval_pieces(args.K_lo, args.K_hi, args.initial_pieces, overlap=args.overlap, label_prefix=label, depth=0)

    for depth in range(args.max_depth + 1):
        if not pending:
            break
        print(f"\n[depth {depth}] running {len(pending)} pieces with {args.workers} workers", flush=True)
        level_results = run_level(args, pending)
        all_results.extend(level_results)
        closed = [r for r in level_results if r.get("closed")]
        failed = []
        for piece, result in zip(pending, level_results):
            # The concurrent path returns results out of order, so recover piece by label.
            pass
        # Reconstruct failed pieces by label.
        result_by_label = {r.get("label"): r for r in level_results}
        failed_pieces = []
        for piece in pending:
            r = result_by_label.get(piece["label"], {})
            if r.get("closed"):
                closed_results.append(r)
            else:
                failed_pieces.append(piece)

        print(f"[depth {depth}] closed={len(closed)} failed={len(failed_pieces)}", flush=True)
        if not failed_pieces:
            pending = []
            break
        if depth >= args.max_depth:
            pending = failed_pieces
            break
        next_pending = []
        for piece in failed_pieces:
            next_pending.extend(split_failed_piece(piece, args.split_factor, args.overlap))
        pending = next_pending
        write_json(summary_path, current_summary(args, all_results, closed_results, pending, None))
        write_piece_csv(csv_path, all_results)

    # Order ready candidates by K_lo for assembly.
    ready_candidates = []
    for r in closed_results:
        c = r.get("ready_candidate")
        if c and Path(c).exists():
            klo, khi = segment_from_candidate(c)
            ready_candidates.append((klo if klo is not None else r.get("K_lo"), khi if khi is not None else r.get("K_hi"), c))
    ready_candidates.sort(key=lambda x: (x[0], x[1]))
    ready_paths = [c for _, _, c in ready_candidates]

    assemble_report = None
    if not args.no_assemble and ready_paths:
        print(f"\n[assemble] assembling {len(ready_paths)} theorem-ready pieces", flush=True)
        assemble_report = assemble_gap_chain(args, ready_paths)
        print(json.dumps(assemble_report, indent=2), flush=True)

    summary = current_summary(args, all_results, closed_results, pending, assemble_report)
    write_json(summary_path, summary)
    write_piece_csv(csv_path, all_results)
    print("\nPhase 2T summary:")
    print(json.dumps(summary, indent=2))
    print(f"wrote summary: {summary_path}")
    print(f"wrote csv: {csv_path}")

    if args.dry_run:
        return 0
    if pending:
        return 2
    if assemble_report and not assemble_report.get("assembled"):
        return 3
    return 0


def current_summary(args, all_results, closed_results, pending, assemble_report):
    return {
        "status": "phase2t-complete" if not pending else "phase2t-incomplete",
        "label": args.label,
        "K_lo": args.K_lo,
        "K_hi": args.K_hi,
        "initial_pieces": args.initial_pieces,
        "split_factor": args.split_factor,
        "max_depth": args.max_depth,
        "workers": args.workers,
        "attempt_count": len(all_results),
        "closed_count": len([r for r in all_results if r.get("closed")]),
        "pending_count": len(pending or []),
        "closed_candidates": [r.get("ready_candidate") for r in all_results if r.get("closed") and r.get("ready_candidate")],
        "pending_pieces": pending or [],
        "assemble_report": assemble_report,
        "best_failed_rows": best_failed_rows(all_results, limit=10),
    }


def best_failed_rows(results, limit=10):
    rows = []
    for r in results:
        if r.get("closed"):
            continue
        row = r.get("selected_phase2p_row") or r.get("failure_summary") or {}
        margin = row.get("radii_margin")
        try:
            margin_sort = float(margin)
        except Exception:
            margin_sort = -1e99
        rows.append({
            "label": r.get("label"),
            "K_lo": r.get("K_lo"),
            "K_hi": r.get("K_hi"),
            "error": r.get("error"),
            "radii_margin": margin,
            "tail_T": row.get("tail_T"),
            "allowable_tail_max": row.get("allowable_tail_max"),
            "finite_contraction_q": row.get("finite_contraction_q"),
            "failure_reasons": row.get("failure_reasons"),
            "model_name": row.get("model_name"),
            "_sort": margin_sort,
        })
    rows.sort(key=lambda x: x.get("_sort", -1e99), reverse=True)
    for r in rows:
        r.pop("_sort", None)
    return rows[:limit]


if __name__ == "__main__":
    raise SystemExit(main())
