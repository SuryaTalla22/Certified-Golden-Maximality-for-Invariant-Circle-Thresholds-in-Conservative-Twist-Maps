#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from kam_theorem_suite.audit.lower_anchor_phase2x_weighted_finite import parse_float_csv, write_json
from kam_theorem_suite.audit.lower_anchor_phase2y_validator_upgrade import (
    REQUIRED_FIELDS,
    TRIAL_FIELDS,
    build_phase2y_report,
    write_csv,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Phase 2Y diagnostic sensitivity audit for lower-collar validator upgrades.")
    p.add_argument("--summary", action="append", default=[], help="Phase 2V/2X summary JSON. May be repeated.")
    p.add_argument("--autopsy", action="append", default=[], help="Phase 2X autopsy JSON. May be repeated.")
    p.add_argument("--candidate", action="append", default=[], help="Individual failed candidate JSON. May be repeated.")
    p.add_argument("--out", required=True, help="Output JSON report path.")
    p.add_argument("--csv", required=True, help="Output required-improvement CSV path.")
    p.add_argument("--trials-csv", required=True, help="Output sensitivity-trials CSV path.")
    p.add_argument("--q-target", type=float, default=0.999)
    p.add_argument("--margin-safety", type=float, default=0.0)
    p.add_argument("--top-k-trials", type=int, default=96)
    p.add_argument("--guard-factors", default="1.0,0.95,0.9,0.85,0.8,0.75,0.7,0.65,0.6")
    p.add_argument("--tail-response-factors", default="1.0,0.98,0.96,0.94,0.92,0.9")
    p.add_argument("--q-factors", default="1.0,0.999,0.9975,0.995,0.9925,0.99,0.985,0.98")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    guard_factors = parse_float_csv(args.guard_factors, positive=True)
    tail_factors = parse_float_csv(args.tail_response_factors, positive=True)
    q_factors = parse_float_csv(args.q_factors, positive=True)
    report = build_phase2y_report(
        summaries=args.summary,
        autopsies=args.autopsy,
        candidates=args.candidate,
        q_target=float(args.q_target),
        margin_safety=float(args.margin_safety),
        top_k_trials=int(args.top_k_trials),
        guard_factors=guard_factors,
        tail_response_factors=tail_factors,
        q_factors=q_factors,
    )
    write_json(args.out, report)
    write_csv(args.csv, report["required_improvement_rows"], REQUIRED_FIELDS)
    write_csv(args.trials_csv, report["sensitivity_trials"], TRIAL_FIELDS)
    print({
        "status": report["status"],
        "diagnostic_only": report["diagnostic_only"],
        "row_count": report["summary"]["row_count"],
        "bucket_counts": report["summary"]["bucket_counts"],
        "recommended_upgrade_counts": report["summary"]["recommended_upgrade_counts"],
        "guard_only_10pct_count": report["summary"]["guard_only_10pct_count"],
        "guard_only_15pct_count": report["summary"]["guard_only_15pct_count"],
        "guard_only_20pct_count": report["summary"]["guard_only_20pct_count"],
        "needs_finite_q_upgrade_count": report["summary"]["needs_finite_q_upgrade_count"],
        "minimal_closing_trial_record_count": report["summary"]["minimal_closing_trial_record_count"],
        "out": args.out,
        "csv": args.csv,
        "trials_csv": args.trials_csv,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
