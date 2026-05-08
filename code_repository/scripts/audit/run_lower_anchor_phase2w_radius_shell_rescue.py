#!/usr/bin/env python3
"""Phase 2W: targeted radius-shell rescue for near-miss microsegments.

This driver is intentionally narrower than Phase 2U/2V.  It targets already
small pieces whose best Phase 2P rows missed by tiny margins, usually because
Phase 2O/2P did not try a sufficiently fine radius shell past the previous
profile cap.

It orchestrates existing repository scripts only:
  - run_lower_anchor_phase2n_batch.py
  - run_lower_anchor_phase2o_radius_tail_scan.py
  - run_lower_anchor_phase2p_modewise_tail_scan.py

The driver is checkpoint-friendly and safe to rerun.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Iterable, Optional

getcontext().prec = 40

ROOT = Path.cwd()
ART_ROOT = Path("artifacts/proof_audit/lower_corridor/phase2w_shell")
TAB_ROOT = Path("tables/proof_audit/lower_corridor/phase2w_shell")
REPLAY_ROOT = Path("artifacts/proof_audit/replay")


def d(x) -> Decimal:
    return Decimal(str(x))


def fmt_dec(x: Decimal) -> str:
    s = format(x, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def slug_float(x: float | str) -> str:
    return f"{float(x):.3e}".replace(".", "p")


def parse_indices(s: str | None) -> list[int]:
    if not s:
        return []
    out: list[int] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


@dataclass
class Piece:
    index: int
    label: str
    segment_id: str
    base_K_lo: str
    base_K_hi: str
    K_lo: str
    K_hi: str
    K_mid: str


def make_pieces(label: str, K_lo: str | float, K_hi: str | float, pieces: int, overlap: str | float = "0.0000001") -> list[Piece]:
    lo = d(K_lo)
    hi = d(K_hi)
    ov = d(overlap)
    width = (hi - lo) / Decimal(pieces)
    out: list[Piece] = []
    for i in range(pieces):
        base_lo = lo + width * Decimal(i)
        base_hi = lo + width * Decimal(i + 1)
        exp_lo = max(lo, base_lo - ov)
        exp_hi = min(hi, base_hi + ov)
        mid = (exp_lo + exp_hi) / Decimal(2)
        piece_label = f"{label}_p{i:04d}"
        out.append(Piece(
            index=i,
            label=piece_label,
            segment_id=f"phase2w_{piece_label}",
            base_K_lo=fmt_dec(base_lo),
            base_K_hi=fmt_dec(base_hi),
            K_lo=fmt_dec(exp_lo),
            K_hi=fmt_dec(exp_hi),
            K_mid=fmt_dec(mid),
        ))
    return out


@dataclass
class Profile:
    name: str
    radius_multipliers: str
    sigma_values: str
    p_sigma_values: str
    tail_cutoffs: str
    timeout_n: float = 600.0
    timeout_o: float = 900.0
    timeout_p: float = 900.0


def profile_config(name: str) -> Profile:
    profiles = {
        # Focused around the observed near-best range, while extending beyond
        # prior x1.25 cap for rows with contraction room.
        "shell": Profile(
            name="shell",
            radius_multipliers="1.0,1.08,1.12,1.16,1.20,1.22,1.24,1.25,1.26,1.27,1.28,1.29,1.30,1.32,1.34,1.36,1.38,1.40,1.42,1.45,1.50,1.55,1.60",
            sigma_values="0.000001,0.00000075,0.0000005,0.00000025,0.0000001",
            p_sigma_values="0.000001,0.00000075,0.0000005,0.00000025,0.0000001",
            tail_cutoffs="1024,1280,1536,1792,2048",
        ),
        # Even narrower, for quick testing of a single piece.
        "needle": Profile(
            name="needle",
            radius_multipliers="1.16,1.20,1.22,1.24,1.25,1.26,1.27,1.28,1.29,1.30,1.32,1.34,1.36,1.38,1.40,1.42",
            sigma_values="0.00000025,0.0000001",
            p_sigma_values="0.00000025,0.0000001",
            tail_cutoffs="1280,1536,1792",
            timeout_o=600.0,
            timeout_p=600.0,
        ),
        # Wider fallback if shell shows radius room but still misses.
        "wide": Profile(
            name="wide",
            radius_multipliers="1.0,1.05,1.08,1.1,1.12,1.14,1.16,1.18,1.2,1.22,1.24,1.25,1.26,1.27,1.28,1.29,1.30,1.32,1.34,1.36,1.38,1.40,1.45,1.50,1.60,1.75,2.0",
            sigma_values="0.000001,0.00000075,0.0000005,0.00000025,0.0000001",
            p_sigma_values="0.000001,0.00000075,0.0000005,0.00000025,0.0000001",
            tail_cutoffs="1024,1280,1536,1792,2048,3072",
            timeout_o=1200.0,
            timeout_p=1200.0,
        ),
    }
    if name not in profiles:
        raise ValueError(f"unknown profile {name!r}; choices={sorted(profiles)}")
    return profiles[name]


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def write_json(path: str | Path, data: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True))


def selected_row(candidate_path: Path) -> dict:
    if not candidate_path.exists():
        return {}
    data = load_json(candidate_path)
    row = data.get("selected_phase2p_row") or {}
    seg = (data.get("anchor_segments") or [{}])[0]
    out = {
        "path": str(candidate_path),
        "K_lo": seg.get("K_lo"),
        "K_hi": seg.get("K_hi"),
        "theorem_facing": data.get("theorem_facing"),
        "promotion_allowed": data.get("promotion_allowed"),
        "closure_level": data.get("closure_level"),
        "failure_fields": data.get("failure_fields"),
    }
    for k in [
        "theorem_ready", "model_name", "sigma", "radius_r", "radius_multiplier",
        "finite_contraction_q", "tail_cutoff", "radii_margin", "tail_T",
        "allowable_tail_max", "tail_response_bound", "nonlinear_guard", "failure_reasons",
    ]:
        out[k] = row.get(k)
    return out


def is_ready(candidate_path: Path) -> bool:
    if not candidate_path.exists():
        return False
    d0 = load_json(candidate_path)
    row = d0.get("selected_phase2p_row") or {}
    return bool(d0.get("theorem_facing") and d0.get("promotion_allowed") and row.get("theorem_ready") and not (d0.get("failure_fields") or row.get("failure_reasons")))


def run_cmd(cmd: list[str], timeout: float, log_path: Path, dry_run: bool = False) -> dict:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"cmd": cmd, "timeout": timeout, "log_path": str(log_path)}
    if dry_run:
        rec.update({"returncode": None, "elapsed_seconds": 0, "timed_out": False, "dry_run": True})
        with log_path.open("a") as f:
            f.write("[dry-run] " + " ".join(cmd) + "\n")
        return rec
    t0 = time.time()
    try:
        with log_path.open("a") as f:
            f.write("\n$ " + " ".join(cmd) + "\n")
            f.flush()
            proc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
        rec.update({"returncode": proc.returncode, "elapsed_seconds": time.time() - t0, "timed_out": False})
    except subprocess.TimeoutExpired:
        rec.update({"returncode": 124, "elapsed_seconds": time.time() - t0, "timed_out": True})
        with log_path.open("a") as f:
            f.write(f"\n[TIMEOUT after {timeout} seconds]\n")
    return rec


def piece_paths(label: str, piece: Piece) -> dict[str, Path]:
    base = ART_ROOT / label
    tab = TAB_ROOT / label
    return {
        "base": base,
        "phase2o_dir": base / "phase2o",
        "phase2p_dir": base / "phase2p",
        "ready_dir": base / "ready",
        "phase2o_table": tab / "phase2o",
        "phase2p_table": tab / "phase2p",
        "log": REPLAY_ROOT / f"phase2w_{label}" / f"{piece.label}.log",
        "phase2n_summary": Path("artifacts/proof_audit/lower_corridor/phase2n_probes") / f"{piece.segment_id}_phase2n_batch_summary.json",
        "phase2n_attempt": Path("artifacts/proof_audit/lower_corridor/phase2n_probes") / f"{piece.segment_id}_N1024_os16_sg0p0001.json",
        "phase2o_out": base / "phase2o" / f"{piece.segment_id}_tail_radius_scan.json",
        "phase2o_csv": tab / "phase2o" / f"{piece.segment_id}_tail_radius_scan.csv",
        "phase2o_candidate": base / "phase2o" / f"{piece.segment_id}_tail_radius_candidate.json",
        "phase2p_out": base / "phase2p" / f"{piece.segment_id}_modewise_tail_scan.json",
        "phase2p_csv": tab / "phase2p" / f"{piece.segment_id}_modewise_tail_scan.csv",
        "phase2p_candidate": base / "phase2p" / f"{piece.segment_id}_modewise_tail_candidate.json",
        "ready_candidate": base / "ready" / f"{piece.segment_id}_THEOREM_READY_candidate.json",
    }


def run_piece(args_tuple) -> dict:
    args, piece = args_tuple
    prof = profile_config(args.profile)
    paths = piece_paths(args.label, piece)
    for key in ["phase2o_dir", "phase2p_dir", "phase2o_table", "phase2p_table", "ready_dir"]:
        paths[key].mkdir(parents=True, exist_ok=True)

    if paths["ready_candidate"].exists() and not args.force:
        row = selected_row(paths["ready_candidate"])
        return {**asdict(piece), "status": "already-ready", "closed": True, "selected": row, "ready_candidate": str(paths["ready_candidate"]), "run_results": []}

    py = sys.executable
    run_results = []

    n_cmd = [
        py, "scripts/audit/run_lower_anchor_phase2n_batch.py",
        "--segment-id", piece.segment_id,
        "--K-lo", piece.K_lo,
        "--K-hi", piece.K_hi,
        "--K-mid", piece.K_mid,
        "--N-values", "1024",
        "--oversample-factors", "16",
        "--sigma-caps", "0.0001",
        "--timeout-seconds", str(args.timeout_n or prof.timeout_n),
        "--skip-existing",
        "--seed-json", args.seed_json,
    ]
    if args.force:
        # Phase2N does not necessarily support --force in older patches.  Keep
        # cache semantics for 2N and refresh O/P below, where it matters.
        pass
    run_results.append({"phase": "phase2n", **run_cmd(n_cmd, args.timeout_n or prof.timeout_n, paths["log"], args.dry_run)})
    if run_results[-1].get("returncode") not in (0, None):
        return {**asdict(piece), "status": "phase2n-failed", "closed": False, "run_results": run_results}

    o_cmd = [
        py, "scripts/audit/run_lower_anchor_phase2o_radius_tail_scan.py",
        "--input", str(paths["phase2n_summary"]),
        "--out", str(paths["phase2o_out"]),
        "--csv", str(paths["phase2o_csv"]),
        "--candidate-out", str(paths["phase2o_candidate"]),
        "--radius-multipliers", prof.radius_multipliers,
        "--sigma-values", prof.sigma_values,
        "--tail-band-fractions", "0.5,0.65,0.75,0.85",
        "--tail-safety-factors", "2,4,8,16",
    ]
    run_results.append({"phase": "phase2o", **run_cmd(o_cmd, args.timeout_o or prof.timeout_o, paths["log"], args.dry_run)})
    if run_results[-1].get("returncode") not in (0, None):
        return {**asdict(piece), "status": "phase2o-failed", "closed": False, "run_results": run_results}

    p_cmd = [
        py, "scripts/audit/run_lower_anchor_phase2p_modewise_tail_scan.py",
        "--input", str(paths["phase2o_candidate"]),
        "--out", str(paths["phase2p_out"]),
        "--csv", str(paths["phase2p_csv"]),
        "--candidate-out", str(paths["phase2p_candidate"]),
        "--sigma-values", prof.p_sigma_values,
        "--tail-cutoffs", prof.tail_cutoffs,
        "--oversample-factors", "16",
    ]
    run_results.append({"phase": "phase2p", **run_cmd(p_cmd, args.timeout_p or prof.timeout_p, paths["log"], args.dry_run)})

    row = selected_row(paths["phase2p_candidate"])
    closed = is_ready(paths["phase2p_candidate"])
    status = "closed" if closed else "not-closed"
    ready_candidate = str(paths["ready_candidate"])
    if closed and not args.dry_run:
        paths["ready_candidate"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(paths["phase2p_candidate"], paths["ready_candidate"])
    return {**asdict(piece), "status": status, "closed": closed, "selected": row, "ready_candidate": ready_candidate, "phase2p_candidate": str(paths["phase2p_candidate"]), "run_results": run_results}


def indices_from_summary(path: str | Path, top_k: int) -> list[int]:
    data = load_json(path)
    inds = []
    for row in data.get("best_failed_rows", []):
        p = row.get("path", "")
        m = re.search(r"_p(\d{4})_", p)
        if m:
            inds.append(int(m.group(1)))
    return sorted(set(inds[:top_k]))


def summarize(label: str, pieces: list[Piece], results: list[dict]) -> dict:
    rows = []
    for p in pieces:
        paths = piece_paths(label, p)
        row = selected_row(paths["ready_candidate"] if paths["ready_candidate"].exists() else paths["phase2p_candidate"])
        rows.append({**asdict(p), "closed": is_ready(paths["ready_candidate"]), "ready_candidate": str(paths["ready_candidate"]), **{f"selected_{k}": v for k, v in row.items()}})
    closed_count = sum(1 for r in rows if r["closed"])
    pending = [r for r in rows if not r["closed"]]
    best_failed = []
    for r in rows:
        if r["closed"]:
            continue
        try:
            margin = float(r.get("selected_radii_margin"))
        except Exception:
            margin = -1e99
        best_failed.append((margin, r))
    best_failed = [r for _, r in sorted(best_failed, key=lambda x: x[0], reverse=True)[:20]]
    return {
        "status": "phase2w-complete" if not pending else "phase2w-incomplete",
        "label": label,
        "closed_count": closed_count,
        "pending_count": len(pending),
        "result_count": len(results),
        "results": results,
        "pieces": rows,
        "best_failed_rows": best_failed,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", required=True)
    ap.add_argument("--K-lo", required=True)
    ap.add_argument("--K-hi", required=True)
    ap.add_argument("--seed-json", default="")
    ap.add_argument("--pieces", type=int, required=True)
    ap.add_argument("--overlap", default="0.0000001")
    ap.add_argument("--piece-start", type=int, default=0)
    ap.add_argument("--piece-stop", type=int, default=None)
    ap.add_argument("--piece-indices", default="")
    ap.add_argument("--from-summary", default="")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--profile", default="shell", choices=["needle", "shell", "wide"])
    ap.add_argument("--timeout-n", type=float, default=None)
    ap.add_argument("--timeout-o", type=float, default=None)
    ap.add_argument("--timeout-p", type=float, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--inspect-existing", action="store_true")
    args = ap.parse_args(argv)

    # Avoid BLAS/OpenMP oversubscription in child processes.
    for name in ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"]:
        os.environ.setdefault(name, "1")

    all_pieces = make_pieces(args.label, args.K_lo, args.K_hi, args.pieces, args.overlap)
    selected = parse_indices(args.piece_indices)
    if args.from_summary:
        selected.extend(indices_from_summary(args.from_summary, args.top_k))
        selected = sorted(set(selected))
    if not selected:
        stop = args.piece_stop if args.piece_stop is not None else args.pieces
        selected = list(range(args.piece_start, stop))
    pieces = [p for p in all_pieces if p.index in set(selected)]

    if args.inspect_existing:
        summary = summarize(args.label, pieces, [])
        print(json.dumps(summary, indent=2))
        return 0

    print("=" * 80)
    print(f"Phase 2W radius-shell rescue: {args.label}")
    print(f"target interval: [{args.K_lo}, {args.K_hi}]")
    print(f"pieces total: {args.pieces}; selected: {len(pieces)}; workers: {args.workers}; profile: {args.profile}")
    if args.dry_run:
        print("DRY RUN: commands will be logged but not executed")
    print("=" * 80)

    if not args.seed_json and not args.inspect_existing:
        print("ERROR: --seed-json is required for execution", file=sys.stderr)
        return 2

    results: list[dict] = []
    with cf.ProcessPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = [ex.submit(run_piece, (args, p)) for p in pieces]
        for fut in cf.as_completed(futs):
            res = fut.result()
            results.append(res)
            sel = res.get("selected", {}) or {}
            msg = "closed" if res.get("closed") else res.get("status")
            print(f"[{msg}] piece {res.get('index'):04d} {res.get('segment_id')} margin={sel.get('radii_margin')} q={sel.get('finite_contraction_q')} model={sel.get('model_name')}", flush=True)

    summary = summarize(args.label, pieces, results)
    out = ART_ROOT / args.label / f"phase2w_{args.label}_run_summary.json"
    csv_path = TAB_ROOT / args.label / f"phase2w_{args.label}_pieces.csv"
    write_json(out, {**summary, "summary_path": str(out), "csv_path": str(csv_path)})
    write_csv(csv_path, summary["pieces"])

    print("\nPhase 2W complete.")
    print(json.dumps({
        "status": summary["status"],
        "closed_count": summary["closed_count"],
        "pending_count": summary["pending_count"],
        "summary_path": str(out),
        "csv_path": str(csv_path),
        "best_failed_rows": summary["best_failed_rows"][:5],
    }, indent=2))
    return 0 if summary["pending_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
