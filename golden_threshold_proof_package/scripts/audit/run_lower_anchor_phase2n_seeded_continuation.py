#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2n import (
    Phase2NAttemptConfig,
    atomic_write_json,
    parse_float_list,
    parse_int_list,
    run_single_N_attempt,
    score_key,
    summarize_attempts,
    build_phase2e_candidate_from_best_attempt,
)


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


def _linspace(a: float, b: float, n: int) -> list[float]:
    if n <= 1:
        return [float(b)]
    step = (float(b) - float(a)) / float(n - 1)
    return [float(a) + i * step for i in range(int(n))]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase-2N seeded continuation over a short K ladder for fixed N/oversample/sigma.")
    parser.add_argument("--segment-id", default="phase2n_seeded_collar_000")
    parser.add_argument("--K-start", type=float, required=True)
    parser.add_argument("--K-stop", type=float, required=True)
    parser.add_argument("--num-steps", type=int, default=6)
    parser.add_argument("--K-values", default=None, help="Comma-separated explicit K values. Overrides start/stop/num-steps.")
    parser.add_argument("--segment-half-width", type=float, default=2.5e-4)
    parser.add_argument("--N", type=int, default=1024)
    parser.add_argument("--oversample-factor", type=int, default=64)
    parser.add_argument("--sigma-cap", type=float, default=1.0e-4)
    parser.add_argument("--seed-json", default=None)
    parser.add_argument("--out-dir", default="artifacts/proof_audit/lower_corridor/phase2n_seeded")
    parser.add_argument("--table-dir", default="tables/proof_audit/lower_corridor/phase2n_seeded")
    parser.add_argument("--no-raw-certificate", action="store_true")
    parser.add_argument("--stop-on-margin-drop", type=float, default=None, help="Stop if strict radii margin falls below this value.")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    out_dir = _resolve(args.out_dir); table_dir = _resolve(args.table_dir)
    assert out_dir is not None and table_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True); table_dir.mkdir(parents=True, exist_ok=True)
    K_values = list(parse_float_list(args.K_values)) if args.K_values else _linspace(args.K_start, args.K_stop, args.num_steps)
    attempts = []
    seed_json = str(_resolve(args.seed_json)) if args.seed_json else None
    started = time.time()
    summary_path = out_dir / f"{args.segment_id}_seeded_continuation_summary.json"

    for idx, K in enumerate(K_values):
        sid = f"{args.segment_id}_{idx:03d}"
        out = out_dir / f"{sid}_N{args.N}_K{K:.10f}.json"
        cfg = Phase2NAttemptConfig(
            segment_id=sid,
            K_lo=float(K - args.segment_half_width),
            K_hi=float(K + args.segment_half_width),
            K_mid=float(K),
            N=int(args.N),
            oversample_factor=int(args.oversample_factor),
            sigma_cap=float(args.sigma_cap),
            seed_path=seed_json,
            seed_policy="previous-phase2n-result" if idx > 0 else ("json-resampled" if seed_json else "none"),
            created_by="phase2n-seeded-continuation",
        )
        result = run_single_N_attempt(cfg, include_raw_certificate=not args.no_raw_certificate)
        atomic_write_json(out, result.to_dict(include_raw_certificate=not args.no_raw_certificate))
        d = result.to_dict(include_raw_certificate=False)
        d["_path"] = _rel(out)
        attempts.append(d)
        # Use the just-written result as the next seed if it contains raw cert data.
        if not args.no_raw_certificate and out.exists():
            seed_json = str(out)
        summary = summarize_attempts(attempts)
        summary.update({
            "schema": "phase2n_seeded_continuation_summary_v1",
            "segment_id": args.segment_id,
            "K_values": K_values,
            "N": int(args.N),
            "oversample_factor": int(args.oversample_factor),
            "sigma_cap": float(args.sigma_cap),
            "elapsed_seconds": time.time() - started,
        })
        atomic_write_json(summary_path, summary)
        if args.stop_on_margin_drop is not None and result.score.radii_margin < float(args.stop_on_margin_drop):
            break

    csv_path = table_dir / f"{args.segment_id}_seeded_continuation.csv"
    fields = ["path", "status", "segment_id", "K_mid", "N", "oversample_factor", "sigma_cap", "sigma_used", "theorem_ready", "radii_margin", "residual_Y", "linear_Z", "radius_r", "tail_T", "finite_radii_margin", "source_theorem_margin", "elapsed_seconds", "failure_reasons"]
    final_summary = summarize_attempts(attempts)
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in final_summary.get("rows", []):
            rr = dict(row)
            rr["failure_reasons"] = ";".join(str(x) for x in rr.get("failure_reasons", []) or [])
            writer.writerow({k: rr.get(k) for k in fields})

    best = final_summary.get("best")
    candidate_path = out_dir / f"{args.segment_id}_best_single_segment_candidate.json"
    if best and best.get("path"):
        bp = ROOT / best["path"] if not Path(best["path"]).is_absolute() else Path(best["path"])
        best_attempt = json.loads(bp.read_text())
        candidate = build_phase2e_candidate_from_best_attempt(best_attempt, source_artifact=_rel(candidate_path))
        atomic_write_json(candidate_path, candidate)

    final_summary.update({
        "schema": "phase2n_seeded_continuation_summary_v1",
        "segment_id": args.segment_id,
        "K_values": K_values,
        "N": int(args.N),
        "oversample_factor": int(args.oversample_factor),
        "sigma_cap": float(args.sigma_cap),
        "csv_path": _rel(csv_path),
        "best_candidate_path": _rel(candidate_path) if candidate_path.exists() else None,
        "elapsed_seconds": time.time() - started,
    })
    atomic_write_json(summary_path, final_summary)
    os.write(1, (json.dumps({
        "summary_path": _rel(summary_path),
        "csv_path": _rel(csv_path),
        "best_candidate_path": _rel(candidate_path) if candidate_path.exists() else None,
        "attempt_count": final_summary.get("attempt_count", 0),
        "theorem_ready_count": final_summary.get("theorem_ready_count", 0),
        "best": final_summary.get("best"),
    }, indent=2, sort_keys=True) + "\n").encode())
    return 2 if args.strict and final_summary.get("theorem_ready_count", 0) == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
