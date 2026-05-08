#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2n import (
    atomic_write_json,
    collect_attempts,
    parse_float_list,
    parse_int_list,
    summarize_attempts,
    build_phase2e_candidate_from_best_attempt,
)

SINGLE = ROOT / "scripts" / "audit" / "run_lower_anchor_phase2n_single_N_probe.py"


def _resolve(path: str | None) -> Path | None:
    if path is None:
        return None
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except Exception:
        return str(p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a memory-safe grid of Phase-2N single-N probes using one subprocess per attempt.")
    parser.add_argument("--segment-id", default="phase2n_collar_000")
    parser.add_argument("--K-lo", type=float, required=True)
    parser.add_argument("--K-hi", type=float, required=True)
    parser.add_argument("--K-mid", type=float, required=True)
    parser.add_argument("--N-values", default="1024,1536")
    parser.add_argument("--oversample-factors", default="64,128")
    parser.add_argument("--sigma-caps", default="0.0001")
    parser.add_argument("--seed-json", default=None)
    parser.add_argument("--out-dir", default="artifacts/proof_audit/lower_corridor/phase2n_probes")
    parser.add_argument("--table-dir", default="tables/proof_audit/lower_corridor/phase2n_probes")
    parser.add_argument("--timeout-seconds", type=float, default=None)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--no-raw-certificate", action="store_true")
    parser.add_argument("--stop-after-ready", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    out_dir = _resolve(args.out_dir); table_dir = _resolve(args.table_dir)
    assert out_dir is not None and table_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True); table_dir.mkdir(parents=True, exist_ok=True)
    Ns = parse_int_list(args.N_values)
    overs = parse_int_list(args.oversample_factors)
    sigmas = parse_float_list(args.sigma_caps)
    started = time.time()
    executions = []
    attempt_paths: list[Path] = []
    summary_path = out_dir / f"{args.segment_id}_phase2n_batch_summary.json"

    for N in Ns:
        for osfac in overs:
            for sigma in sigmas:
                tag = f"{args.segment_id}_N{N}_os{osfac}_sg{str(sigma).replace('.', 'p').replace('-', 'm')}"
                out = out_dir / f"{tag}.json"
                attempt_paths.append(out)
                if args.skip_existing and out.exists():
                    executions.append({"tag": tag, "out": _rel(out), "skipped_existing": True})
                    continue
                cmd = [
                    sys.executable,
                    str(SINGLE),
                    "--segment-id", str(args.segment_id),
                    "--K-lo", str(args.K_lo),
                    "--K-hi", str(args.K_hi),
                    "--K-mid", str(args.K_mid),
                    "--N", str(N),
                    "--oversample-factor", str(osfac),
                    "--sigma-cap", str(sigma),
                    "--out", str(out),
                ]
                if args.seed_json:
                    cmd.extend(["--seed-json", str(_resolve(args.seed_json))])
                if args.no_raw_certificate:
                    cmd.append("--no-raw-certificate")
                t0 = time.time()
                try:
                    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=args.timeout_seconds)
                    timed_out = False
                    returncode = proc.returncode
                    stdout = proc.stdout[-4000:]
                    stderr = proc.stderr[-4000:]
                except subprocess.TimeoutExpired as exc:
                    timed_out = True
                    returncode = None
                    stdout = (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else ""
                    stderr = (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else ""
                elapsed = time.time() - t0
                executions.append({
                    "tag": tag,
                    "out": _rel(out),
                    "cmd": cmd,
                    "returncode": returncode,
                    "timed_out": timed_out,
                    "elapsed_seconds": elapsed,
                    "stdout_tail": stdout,
                    "stderr_tail": stderr,
                })
                attempts = []
                for p in attempt_paths:
                    if p.exists():
                        d = json.loads(p.read_text())
                        d["_path"] = _rel(p)
                        attempts.append(d)
                summary = summarize_attempts(attempts)
                summary.update({
                    "schema": "phase2n_batch_summary_v1",
                    "segment_id": args.segment_id,
                    "K_lo": float(args.K_lo),
                    "K_hi": float(args.K_hi),
                    "K_mid": float(args.K_mid),
                    "executions": executions,
                    "elapsed_seconds": time.time() - started,
                })
                atomic_write_json(summary_path, summary)
                if args.stop_after_ready and summary.get("theorem_ready_count", 0) > 0:
                    break
            if args.stop_after_ready and summary_path.exists() and json.loads(summary_path.read_text()).get("theorem_ready_count", 0) > 0:
                break
        if args.stop_after_ready and summary_path.exists() and json.loads(summary_path.read_text()).get("theorem_ready_count", 0) > 0:
            break

    attempts = []
    for p in attempt_paths:
        if p.exists():
            d = json.loads(p.read_text())
            d["_path"] = _rel(p)
            attempts.append(d)
    summary = summarize_attempts(attempts)
    summary.update({
        "schema": "phase2n_batch_summary_v1",
        "segment_id": args.segment_id,
        "K_lo": float(args.K_lo),
        "K_hi": float(args.K_hi),
        "K_mid": float(args.K_mid),
        "executions": executions,
        "elapsed_seconds": time.time() - started,
    })
    atomic_write_json(summary_path, summary)

    csv_path = table_dir / f"{args.segment_id}_phase2n_batch_summary.csv"
    fields = ["path", "status", "segment_id", "K_mid", "N", "oversample_factor", "sigma_cap", "sigma_used", "theorem_ready", "radii_margin", "residual_Y", "linear_Z", "radius_r", "tail_T", "finite_radii_margin", "source_theorem_margin", "elapsed_seconds", "failure_reasons"]
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in summary.get("rows", []):
            row = dict(row)
            row["failure_reasons"] = ";".join(str(x) for x in row.get("failure_reasons", []) or [])
            writer.writerow({k: row.get(k) for k in fields})

    candidate_path = out_dir / f"{args.segment_id}_best_single_segment_candidate.json"
    best = summary.get("best")
    if best and best.get("path"):
        best_attempt = json.loads((ROOT / best["path"]).read_text()) if not Path(best["path"]).is_absolute() else json.loads(Path(best["path"]).read_text())
        candidate = build_phase2e_candidate_from_best_attempt(best_attempt, source_artifact=_rel(candidate_path))
        atomic_write_json(candidate_path, candidate)
        summary["best_candidate_path"] = _rel(candidate_path)
        atomic_write_json(summary_path, summary)

    os.write(1, (json.dumps({
        "summary_path": _rel(summary_path),
        "csv_path": _rel(csv_path),
        "best_candidate_path": _rel(candidate_path) if candidate_path.exists() else None,
        "attempt_count": summary.get("attempt_count", 0),
        "theorem_ready_count": summary.get("theorem_ready_count", 0),
        "best": summary.get("best"),
    }, indent=2, sort_keys=True) + "\n").encode())
    return 2 if args.strict and summary.get("theorem_ready_count", 0) == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
