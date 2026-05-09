#!/usr/bin/env python3
"""
Phase 2V: targeted micro-rescue closer for extremely narrow lower-anchor gaps.

This is a deliberately narrower, faster successor to Phase 2U for the situation where
many microsegments miss by only ~1e-8 but broad Phase 2P grids time out.

Design goals:
  * use a fine fixed subdivision (typically 256 or 512 pieces);
  * run a very narrow, evidence-driven 2O/2P grid;
  * checkpoint after every piece;
  * skip theorem-ready pieces on rerun;
  * support chunked execution on a CPU node;
  * assemble with Phase 2Q when all pieces close.

It orchestrates existing scripts:
  2N: scripts/audit/run_lower_anchor_phase2n_batch.py
  2O: scripts/audit/run_lower_anchor_phase2o_radius_tail_scan.py
  2P: scripts/audit/run_lower_anchor_phase2p_modewise_tail_scan.py
  2Q: scripts/audit/run_lower_anchor_phase2q_chain_assembler.py
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any

getcontext().prec = 60

ART_ROOT = Path("artifacts/proof_audit/lower_corridor/phase2v_micro")
TABLE_ROOT = Path("tables/proof_audit/lower_corridor/phase2v_micro")
REPLAY_ROOT = Path("artifacts/proof_audit/replay")
PHASE2N_ROOT = Path("artifacts/proof_audit/lower_corridor/phase2n_probes")

THREAD_LIMIT_ENV = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "BLIS_NUM_THREADS": "1",
}

PROFILES = {
    # The narrow default based on collar_012b1 evidence: best rows were near
    # sigma=1e-7, tail_cutoff=1536, radius_multiplier~1.08--1.20.
    "needle": {
        "radius_multipliers": "1.0,1.04,1.06,1.08,1.1,1.12,1.14,1.16,1.18,1.2,1.22,1.25",
        "phase2o_sigma_values": "0.0000001",
        "phase2p_sigma_values": "0.0000001,0.00000025,0.0000005,0.000001",
        "tail_cutoffs": "1024,1536,2048",
        "tail_band_fractions": "0.65,0.85",
        "tail_safety_factors": "2,4",
    },
    # Even smaller P grid: useful when Phase 2P is timing out and logs already
    # show the best row is sg=1e-7/cut=1536.
    "needle1536": {
        "radius_multipliers": "1.0,1.04,1.06,1.08,1.1,1.12,1.14,1.16,1.18,1.2,1.22,1.25",
        "phase2o_sigma_values": "0.0000001",
        "phase2p_sigma_values": "0.0000001",
        "tail_cutoffs": "1536",
        "tail_band_fractions": "0.65",
        "tail_safety_factors": "2",
    },
    # Wider radius/sigma probe without returning to the huge Phase 2U aggressive grid.
    "rescue": {
        "radius_multipliers": "1.0,1.02,1.04,1.06,1.08,1.1,1.12,1.14,1.16,1.18,1.2,1.22,1.24,1.26,1.28,1.3,1.35,1.4",
        "phase2o_sigma_values": "0.000001,0.00000075,0.0000005,0.00000025,0.0000001",
        "phase2p_sigma_values": "0.000001,0.00000075,0.0000005,0.00000025,0.0000001",
        "tail_cutoffs": "1024,1536,2048,3072",
        "tail_band_fractions": "0.5,0.65,0.85",
        "tail_safety_factors": "2,4,8",
    },
}


def dec(x: str | float | int | Decimal) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def fmt_dec(x: Decimal, places: int = 12) -> str:
    q = Decimal(1).scaleb(-places)
    y = x.quantize(q)
    s = format(y, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def split_csv(value: str | None, fallback: str) -> str:
    return value if value is not None and value.strip() else fallback


def load_json(path: Path | str) -> dict[str, Any]:
    with Path(path).open("r") as f:
        return json.load(f)


def write_json(path: Path | str, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)


def env_for_subprocess() -> dict[str, str]:
    env = os.environ.copy()
    env.update(THREAD_LIMIT_ENV)
    return env


def generate_pieces(K_lo: str, K_hi: str, pieces: int, overlap: str, label: str) -> list[dict[str, Any]]:
    lo = dec(K_lo)
    hi = dec(K_hi)
    ov = dec(overlap)
    width = (hi - lo) / dec(pieces)
    half = ov / dec(2)
    out: list[dict[str, Any]] = []
    for i in range(pieces):
        base_lo = lo + width * dec(i)
        base_hi = lo + width * dec(i + 1)
        seg_lo = max(lo, base_lo - half)
        seg_hi = min(hi, base_hi + half)
        mid = (base_lo + base_hi) / dec(2)
        out.append({
            "index": i,
            "piece_label": f"{label}_p{i:04d}",
            "segment_id": f"phase2v_{label}_p{i:04d}",
            "K_lo": fmt_dec(seg_lo),
            "K_hi": fmt_dec(seg_hi),
            "K_mid": fmt_dec(mid),
            "base_K_lo": fmt_dec(base_lo),
            "base_K_hi": fmt_dec(base_hi),
        })
    return out


def phase_paths(label: str, seg_id: str) -> dict[str, Path]:
    base = ART_ROOT / label
    tables = TABLE_ROOT / label
    logs = REPLAY_ROOT / f"phase2v_{label}"
    return {
        "base": base,
        "tables": tables,
        "logs": logs,
        "ready_dir": base / "ready",
        "phase2o_dir": base / "phase2o",
        "phase2p_dir": base / "phase2p",
        "phase2o_table_dir": tables / "phase2o",
        "phase2p_table_dir": tables / "phase2p",
        "piece_log": logs / f"{seg_id}.log",
        "phase2n_summary": PHASE2N_ROOT / f"{seg_id}_phase2n_batch_summary.json",
        "phase2n_attempt": PHASE2N_ROOT / f"{seg_id}_N1024_os16_sg0p0001.json",
        "phase2o_out": base / "phase2o" / f"{seg_id}_tail_radius_scan.json",
        "phase2o_csv": tables / "phase2o" / f"{seg_id}_tail_radius_scan.csv",
        "phase2o_candidate": base / "phase2o" / f"{seg_id}_tail_radius_candidate.json",
        "phase2p_out": base / "phase2p" / f"{seg_id}_modewise_tail_scan.json",
        "phase2p_csv": tables / "phase2p" / f"{seg_id}_modewise_tail_scan.csv",
        "phase2p_candidate": base / "phase2p" / f"{seg_id}_modewise_tail_candidate.json",
        "ready_candidate": base / "ready" / f"{seg_id}_THEOREM_READY_candidate.json",
    }


def ensure_dirs(paths: dict[str, Path]) -> None:
    for key in ["base", "tables", "logs", "ready_dir", "phase2o_dir", "phase2p_dir", "phase2o_table_dir", "phase2p_table_dir"]:
        paths[key].mkdir(parents=True, exist_ok=True)


def is_ready_candidate(path: Path | str) -> bool:
    path = Path(path)
    if not path.exists():
        return False
    try:
        d = load_json(path)
    except Exception:
        return False
    row = d.get("selected_phase2p_row") or {}
    return bool(
        d.get("theorem_facing") is True
        and d.get("promotion_allowed") is True
        and not d.get("failure_fields")
        and row.get("theorem_ready") is True
        and not row.get("failure_reasons")
    )


def best_row_from_candidate(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    try:
        d = load_json(path)
    except Exception:
        return {"path": str(path), "read_error": True}
    row = d.get("selected_phase2p_row") or {}
    seg = (d.get("anchor_segments") or [{}])[0]
    return {
        "path": str(path),
        "K_lo": seg.get("K_lo"),
        "K_hi": seg.get("K_hi"),
        "theorem_facing": d.get("theorem_facing"),
        "promotion_allowed": d.get("promotion_allowed"),
        "closure_level": d.get("closure_level"),
        "failure_fields": d.get("failure_fields"),
        "theorem_ready": row.get("theorem_ready"),
        "model_name": row.get("model_name"),
        "sigma": row.get("sigma"),
        "radius_r": row.get("radius_r"),
        "radius_multiplier": row.get("radius_multiplier"),
        "finite_contraction_q": row.get("finite_contraction_q"),
        "tail_cutoff": row.get("tail_cutoff"),
        "radii_margin": row.get("radii_margin"),
        "tail_T": row.get("tail_T"),
        "allowable_tail_max": row.get("allowable_tail_max"),
        "tail_response_bound": row.get("tail_response_bound"),
        "nonlinear_guard": row.get("nonlinear_guard"),
        "failure_reasons": row.get("failure_reasons"),
    }


def run_cmd(cmd: list[str], log_path: Path, timeout: float | None, dry_run: bool = False) -> dict[str, Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd_s = " ".join(cmd)
    if dry_run:
        with log_path.open("a") as f:
            f.write("\n[dry-run] $ " + cmd_s + "\n")
        return {"returncode": 0, "dry_run": True, "cmd": cmd}
    started = time.time()
    with log_path.open("a") as f:
        f.write("\n$ " + cmd_s + "\n")
        f.flush()
        try:
            proc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env_for_subprocess(), timeout=timeout, text=True)
            return {"returncode": proc.returncode, "timed_out": False, "elapsed_seconds": time.time() - started, "cmd": cmd}
        except subprocess.TimeoutExpired:
            f.write(f"\n[TIMEOUT after {timeout} seconds]\n")
            return {"returncode": 124, "timed_out": True, "elapsed_seconds": time.time() - started, "cmd": cmd}


def piece_commands(piece: dict[str, Any], args: argparse.Namespace, profile: dict[str, str]) -> tuple[list[str], list[str], list[str]]:
    seg_id = piece["segment_id"]
    paths = phase_paths(args.label, seg_id)
    py = sys.executable

    phase2n = [
        py, "scripts/audit/run_lower_anchor_phase2n_batch.py",
        "--segment-id", seg_id,
        "--K-lo", piece["K_lo"],
        "--K-hi", piece["K_hi"],
        "--K-mid", piece["K_mid"],
        "--N-values", args.n_values,
        "--oversample-factors", args.oversample_factors,
        "--sigma-caps", args.phase2n_sigma_caps,
        "--timeout-seconds", str(args.phase2n_timeout_seconds),
    ]
    if not args.force_phase2n:
        phase2n.append("--skip-existing")
    if args.seed_json:
        phase2n.extend(["--seed-json", args.seed_json])

    phase2o = [
        py, "scripts/audit/run_lower_anchor_phase2o_radius_tail_scan.py",
        "--input", str(paths["phase2n_summary"]),
        "--out", str(paths["phase2o_out"]),
        "--csv", str(paths["phase2o_csv"]),
        "--candidate-out", str(paths["phase2o_candidate"]),
        "--radius-multipliers", split_csv(args.radius_multipliers, profile["radius_multipliers"]),
        "--sigma-values", split_csv(args.phase2o_sigma_values, profile["phase2o_sigma_values"]),
        "--tail-band-fractions", split_csv(args.tail_band_fractions, profile["tail_band_fractions"]),
        "--tail-safety-factors", split_csv(args.tail_safety_factors, profile["tail_safety_factors"]),
    ]

    phase2p = [
        py, "scripts/audit/run_lower_anchor_phase2p_modewise_tail_scan.py",
        "--input", str(paths["phase2o_candidate"]),
        "--out", str(paths["phase2p_out"]),
        "--csv", str(paths["phase2p_csv"]),
        "--candidate-out", str(paths["phase2p_candidate"]),
        "--sigma-values", split_csv(args.phase2p_sigma_values, profile["phase2p_sigma_values"]),
        "--tail-cutoffs", split_csv(args.tail_cutoffs, profile["tail_cutoffs"]),
        "--oversample-factors", args.oversample_factors,
    ]
    return phase2n, phase2o, phase2p


def run_piece(piece: dict[str, Any], args: argparse.Namespace, profile: dict[str, str]) -> dict[str, Any]:
    paths = phase_paths(args.label, piece["segment_id"])
    ensure_dirs(paths)
    result: dict[str, Any] = {
        **piece,
        "ready_candidate": str(paths["ready_candidate"]),
        "phase2p_candidate": str(paths["phase2p_candidate"]),
        "log_path": str(paths["piece_log"]),
    }

    if is_ready_candidate(paths["ready_candidate"]) and not args.force:
        result.update({"closed": True, "status": "ready-existing", "selected": best_row_from_candidate(paths["ready_candidate"])})
        return result

    if args.force:
        for key in ["phase2o_out", "phase2o_csv", "phase2o_candidate", "phase2p_out", "phase2p_csv", "phase2p_candidate", "ready_candidate"]:
            try:
                paths[key].unlink()
            except FileNotFoundError:
                pass

    phase2n, phase2o, phase2p = piece_commands(piece, args, profile)
    if args.dry_run:
        result.update({"closed": False, "status": "dry-run", "commands": [phase2n, phase2o, phase2p]})
        return result

    run_results = []
    for phase_name, cmd, timeout in [
        ("phase2n", phase2n, args.phase2n_timeout_seconds),
        ("phase2o", phase2o, args.phase2o_timeout_seconds),
        ("phase2p", phase2p, args.phase2p_timeout_seconds),
    ]:
        rr = run_cmd(cmd, paths["piece_log"], timeout=timeout)
        rr["phase"] = phase_name
        run_results.append(rr)
        if phase_name == "phase2n" and not paths["phase2n_summary"].exists():
            result.update({"closed": False, "status": "phase2n-failed", "run_results": run_results})
            return result
        if phase_name == "phase2o" and not paths["phase2o_candidate"].exists():
            result.update({"closed": False, "status": "phase2o-failed", "run_results": run_results})
            return result
        if phase_name == "phase2p" and not paths["phase2p_candidate"].exists():
            result.update({"closed": False, "status": "phase2p-failed", "run_results": run_results})
            return result

    ready = is_ready_candidate(paths["phase2p_candidate"])
    selected = best_row_from_candidate(paths["phase2p_candidate"])
    if ready:
        shutil.copy2(paths["phase2p_candidate"], paths["ready_candidate"])
        result.update({"closed": True, "status": "closed", "selected": selected, "run_results": run_results})
    else:
        result.update({"closed": False, "status": "not-closed", "selected": selected, "run_results": run_results})
    return result


def summarize(args: argparse.Namespace, pieces: list[dict[str, Any]], results: list[dict[str, Any]], assemble: dict[str, Any] | None = None) -> dict[str, Any]:
    closed = [r for r in results if r.get("closed")]
    pending = [r for r in results if not r.get("closed")]

    def margin_key(r: dict[str, Any]) -> float:
        v = (r.get("selected") or {}).get("radii_margin")
        return float(v) if isinstance(v, (float, int)) else -1e99

    best_failed = sorted(pending, key=margin_key, reverse=True)[:50]
    return {
        "status": "phase2v-complete" if results and not pending else "phase2v-incomplete",
        "label": args.label,
        "K_lo": args.K_lo,
        "K_hi": args.K_hi,
        "pieces_requested": args.pieces,
        "piece_start": args.piece_start,
        "piece_stop": args.piece_stop,
        "profile": args.profile,
        "workers": args.workers,
        "result_count": len(results),
        "closed_count": len(closed),
        "pending_count": len(pending),
        "ready_candidates": [r.get("ready_candidate") for r in sorted(closed, key=lambda x: x.get("index", 0))],
        "best_failed_rows": [r.get("selected") or r for r in best_failed],
        "assemble_report": assemble or {},
        "pieces": pieces,
        "results": sorted(results, key=lambda x: x.get("index", -1)),
    }


def write_summary(args: argparse.Namespace, pieces: list[dict[str, Any]], results: list[dict[str, Any]], assemble: dict[str, Any] | None = None) -> dict[str, Any]:
    base = ART_ROOT / args.label
    table = TABLE_ROOT / args.label
    base.mkdir(parents=True, exist_ok=True)
    table.mkdir(parents=True, exist_ok=True)
    summary = summarize(args, pieces, results, assemble=assemble)
    summary_path = base / f"phase2v_{args.label}_run_summary.json"
    write_json(summary_path, summary)

    csv_path = table / f"phase2v_{args.label}_pieces.csv"
    with csv_path.open("w", newline="") as f:
        fields = [
            "index", "segment_id", "K_lo", "K_hi", "K_mid", "status", "closed", "radii_margin",
            "tail_T", "allowable_tail_max", "finite_contraction_q", "model_name", "failure_reasons", "ready_candidate", "log_path",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sorted(results, key=lambda x: x.get("index", -1)):
            sel = r.get("selected") or {}
            w.writerow({
                "index": r.get("index"),
                "segment_id": r.get("segment_id"),
                "K_lo": r.get("K_lo"),
                "K_hi": r.get("K_hi"),
                "K_mid": r.get("K_mid"),
                "status": r.get("status"),
                "closed": r.get("closed"),
                "radii_margin": sel.get("radii_margin"),
                "tail_T": sel.get("tail_T"),
                "allowable_tail_max": sel.get("allowable_tail_max"),
                "finite_contraction_q": sel.get("finite_contraction_q"),
                "model_name": sel.get("model_name"),
                "failure_reasons": sel.get("failure_reasons"),
                "ready_candidate": r.get("ready_candidate"),
                "log_path": r.get("log_path"),
            })
    summary["summary_path"] = str(summary_path)
    summary["csv_path"] = str(csv_path)
    return summary


def assemble_chain(args: argparse.Namespace, results: list[dict[str, Any]]) -> dict[str, Any]:
    closed = sorted([r for r in results if r.get("closed")], key=lambda x: x.get("index", 0))
    if len(closed) != len(results) or not closed:
        return {"assembled": False, "reason": "not_all_pieces_closed"}
    base = ART_ROOT / args.label
    table = TABLE_ROOT / args.label
    out = base / f"phase2v_{args.label}_split_chain_audit.json"
    csv_path = table / f"phase2v_{args.label}_split_chain_segments.csv"
    cand = base / f"phase2v_{args.label}_split_chain_candidate.json"
    cmd = [sys.executable, "scripts/audit/run_lower_anchor_phase2q_chain_assembler.py"]
    for r in closed:
        cmd.extend(["--candidate", r["ready_candidate"]])
    cmd.extend([
        "--expected-start", args.K_lo,
        "--expected-end", args.K_hi,
        "--expected-regime-i-hi", args.K_lo,
        "--overlap-tolerance", args.overlap_tolerance,
        "--out", str(out),
        "--csv", str(csv_path),
        "--candidate-out", str(cand),
    ])
    log = REPLAY_ROOT / f"phase2v_{args.label}" / f"phase2v_{args.label}_assemble.log"
    rr = run_cmd(cmd, log, timeout=args.phase2q_timeout_seconds, dry_run=args.dry_run)
    report = {"assembled": False, "command_result": rr, "out": str(out), "csv": str(csv_path), "candidate": str(cand), "log_path": str(log)}
    if cand.exists():
        try:
            d = load_json(cand)
            report.update({
                "theorem_facing": d.get("theorem_facing"),
                "promotion_allowed": d.get("promotion_allowed"),
                "closure_level": d.get("closure_level"),
                "failure_fields": d.get("failure_fields"),
                "chain_summary": d.get("chain_summary"),
                "assembled": bool(d.get("theorem_facing") and d.get("promotion_allowed") and not d.get("failure_fields")),
            })
        except Exception as e:
            report["read_error"] = repr(e)
    return report


def inspect_existing(args: argparse.Namespace) -> int:
    pieces = generate_pieces(args.K_lo, args.K_hi, args.pieces, args.piece_overlap, args.label)
    results = []
    for piece in pieces:
        paths = phase_paths(args.label, piece["segment_id"])
        if is_ready_candidate(paths["ready_candidate"]):
            results.append({**piece, "closed": True, "status": "ready-existing", "ready_candidate": str(paths["ready_candidate"]), "selected": best_row_from_candidate(paths["ready_candidate"])})
        elif paths["phase2p_candidate"].exists():
            results.append({**piece, "closed": False, "status": "not-closed-existing", "ready_candidate": str(paths["ready_candidate"]), "selected": best_row_from_candidate(paths["phase2p_candidate"])})
        else:
            results.append({**piece, "closed": False, "status": "missing", "ready_candidate": str(paths["ready_candidate"])})
    summary = write_summary(args, pieces, results)
    print(json.dumps({
        "status": "inspect-existing",
        "closed_count": summary["closed_count"],
        "pending_count": summary["pending_count"],
        "summary_path": summary["summary_path"],
        "csv_path": summary["csv_path"],
        "best_failed_rows": summary["best_failed_rows"][:10],
    }, indent=2))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Phase 2V targeted fixed micro-rescue closer")
    ap.add_argument("--label", required=True)
    ap.add_argument("--K-lo", dest="K_lo", required=True)
    ap.add_argument("--K-hi", dest="K_hi", required=True)
    ap.add_argument("--seed-json", default="")
    ap.add_argument("--pieces", type=int, default=256)
    ap.add_argument("--piece-overlap", default="0.0000002")
    ap.add_argument("--piece-start", type=int, default=0)
    ap.add_argument("--piece-stop", type=int, default=None)
    ap.add_argument("--workers", type=int, default=48)
    ap.add_argument("--profile", choices=sorted(PROFILES), default="needle")
    ap.add_argument("--force", action="store_true", help="Regenerate this script's Phase 2O/2P outputs")
    ap.add_argument("--force-phase2n", action="store_true", help="Do not pass --skip-existing to Phase 2N")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--inspect-existing", action="store_true")
    ap.add_argument("--assemble-only", action="store_true")
    ap.add_argument("--no-assemble", action="store_true")
    ap.add_argument("--overlap-tolerance", default="1e-10")

    ap.add_argument("--phase2n-timeout-seconds", type=float, default=900.0)
    ap.add_argument("--phase2o-timeout-seconds", type=float, default=900.0)
    ap.add_argument("--phase2p-timeout-seconds", type=float, default=900.0)
    ap.add_argument("--phase2q-timeout-seconds", type=float, default=900.0)

    ap.add_argument("--n-values", default="1024")
    ap.add_argument("--oversample-factors", default="16")
    ap.add_argument("--phase2n-sigma-caps", default="0.0001")
    ap.add_argument("--radius-multipliers", default=None)
    ap.add_argument("--phase2o-sigma-values", default=None)
    ap.add_argument("--phase2p-sigma-values", default=None)
    ap.add_argument("--tail-cutoffs", default=None)
    ap.add_argument("--tail-band-fractions", default=None)
    ap.add_argument("--tail-safety-factors", default=None)
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.pieces <= 0:
        raise SystemExit("--pieces must be positive")
    if args.piece_stop is None:
        args.piece_stop = args.pieces
    args.piece_start = max(0, args.piece_start)
    args.piece_stop = min(args.pieces, args.piece_stop)
    profile = PROFILES[args.profile]

    print("=" * 80)
    print(f"Phase 2V targeted micro-rescue closer: {args.label}")
    print(f"target interval: [{args.K_lo}, {args.K_hi}]")
    print(f"pieces: {args.pieces}; selected range: [{args.piece_start}, {args.piece_stop}); workers: {args.workers}; profile: {args.profile}")
    print("=" * 80)

    pieces_all = generate_pieces(args.K_lo, args.K_hi, args.pieces, args.piece_overlap, args.label)
    pieces = pieces_all[args.piece_start:args.piece_stop]

    if args.inspect_existing:
        return inspect_existing(args)

    if args.assemble_only:
        results = []
        for piece in pieces_all:
            paths = phase_paths(args.label, piece["segment_id"])
            if is_ready_candidate(paths["ready_candidate"]):
                results.append({**piece, "closed": True, "status": "ready-existing", "ready_candidate": str(paths["ready_candidate"]), "selected": best_row_from_candidate(paths["ready_candidate"])})
            else:
                results.append({**piece, "closed": False, "status": "not-ready", "ready_candidate": str(paths["ready_candidate"]), "selected": best_row_from_candidate(paths["phase2p_candidate"])})
        assemble = None if args.no_assemble else assemble_chain(args, results)
        summary = write_summary(args, pieces_all, results, assemble)
        print(json.dumps({k: summary[k] for k in ["status", "closed_count", "pending_count", "summary_path", "csv_path", "assemble_report"]}, indent=2))
        return 0 if summary["pending_count"] == 0 and (args.no_assemble or (assemble or {}).get("assembled")) else 2

    if args.dry_run:
        for piece in pieces[: min(8, len(pieces))]:
            cmds = piece_commands(piece, args, profile)
            print(f"\n[piece {piece['index']}] {piece['segment_id']} [{piece['K_lo']}, {piece['K_hi']}]")
            for cmd in cmds:
                print("$ " + " ".join(cmd))
        print(f"\n[dry-run] shown {min(8, len(pieces))} of {len(pieces)} selected pieces")
        return 0

    results: list[dict[str, Any]] = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(run_piece, piece, args, profile) for piece in pieces]
        for fut in cf.as_completed(futures):
            r = fut.result()
            results.append(r)
            sel = r.get("selected") or {}
            print(f"[{r.get('status')}] piece {r.get('index'):04d} {r.get('segment_id')} margin={sel.get('radii_margin')} ready={r.get('closed')}", flush=True)
            write_summary(args, pieces, results)

    assemble = None
    if not args.no_assemble and args.piece_start == 0 and args.piece_stop == args.pieces:
        assemble = assemble_chain(args, results)
    summary = write_summary(args, pieces_all if args.piece_start == 0 and args.piece_stop == args.pieces else pieces, results, assemble)
    print("\nPhase 2V complete.")
    print(json.dumps({
        "status": summary["status"],
        "closed_count": summary["closed_count"],
        "pending_count": summary["pending_count"],
        "summary_path": summary["summary_path"],
        "csv_path": summary["csv_path"],
        "assemble_report": summary.get("assemble_report"),
        "best_failed_rows": summary.get("best_failed_rows", [])[:10],
    }, indent=2))
    if summary["pending_count"] != 0:
        return 2
    if not args.no_assemble and args.piece_start == 0 and args.piece_stop == args.pieces and not (assemble or {}).get("assembled"):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
