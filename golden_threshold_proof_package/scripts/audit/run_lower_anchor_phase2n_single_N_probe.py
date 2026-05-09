#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2n import (
    Phase2NAttemptConfig,
    atomic_write_json,
    run_single_N_attempt,
    write_single_N_attempt,
)


def _resolve(path: str | None) -> Path | None:
    if path is None:
        return None
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run exactly one Phase-2N lower-anchor N/K attempt and write it immediately.")
    parser.add_argument("--segment-id", required=True)
    parser.add_argument("--K-lo", type=float, required=True)
    parser.add_argument("--K-hi", type=float, required=True)
    parser.add_argument("--K-mid", type=float, required=True)
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--oversample-factor", type=int, default=64)
    parser.add_argument("--sigma-cap", type=float, default=1.0e-4)
    parser.add_argument("--seed-json", default=None)
    parser.add_argument("--seed-policy", default="json-resampled")
    parser.add_argument("--out", required=True)
    parser.add_argument("--no-raw-certificate", action="store_true", help="Write only summaries/ledgers, not full u/z arrays.")
    parser.add_argument("--strict", action="store_true", help="Exit 2 unless this single attempt is theorem-ready.")
    args = parser.parse_args(argv)

    out = _resolve(args.out)
    assert out is not None
    out.parent.mkdir(parents=True, exist_ok=True)
    started_payload = {
        "schema": "phase2n_single_N_started_v1",
        "status": "started",
        "segment_id": args.segment_id,
        "K_mid": float(args.K_mid),
        "N": int(args.N),
        "oversample_factor": int(args.oversample_factor),
        "sigma_cap": float(args.sigma_cap),
    }
    atomic_write_json(out.with_suffix(out.suffix + ".started.json"), started_payload)

    cfg = Phase2NAttemptConfig(
        segment_id=str(args.segment_id),
        K_lo=float(args.K_lo),
        K_hi=float(args.K_hi),
        K_mid=float(args.K_mid),
        N=int(args.N),
        oversample_factor=int(args.oversample_factor),
        sigma_cap=float(args.sigma_cap),
        seed_path=(None if args.seed_json is None else str(_resolve(args.seed_json))),
        seed_policy=str(args.seed_policy),
    )
    result = run_single_N_attempt(cfg, include_raw_certificate=not args.no_raw_certificate)
    write_single_N_attempt(result, out, include_raw_certificate=not args.no_raw_certificate)
    summary = {
        "schema": "phase2n_single_N_cli_summary_v1",
        "out": str(out.relative_to(ROOT) if out.is_relative_to(ROOT) else out),
        "status": result.status,
        "theorem_ready": result.theorem_ready,
        "score": result.score.to_dict(),
        "elapsed_seconds": result.elapsed_seconds,
    }
    os.write(1, (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode())
    return 2 if args.strict and not result.theorem_ready else 0


if __name__ == "__main__":
    raise SystemExit(main())
