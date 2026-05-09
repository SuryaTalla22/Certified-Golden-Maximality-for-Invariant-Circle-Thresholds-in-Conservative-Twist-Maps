#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from kam_theorem_suite.audit.lower_anchor_phase2o_tail_radius import (  # noqa: E402
    Phase2OScanConfig,
    atomic_write_json,
    build_phase2o_candidate,
    build_phase2o_report,
    parse_float_list,
    print_compact_report,
    write_phase2o_csv,
    write_phase2o_report,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Phase 2O tail/radius scan for a Phase-2N lower-anchor attempt. "
            "Consumes a Phase-2N summary/candidate/single-N JSON and writes a fail-closed proof-budget report."
        )
    )
    ap.add_argument("--input", required=True, help="Phase-2N batch summary, single-N attempt, or best candidate JSON")
    ap.add_argument(
        "--out",
        default="artifacts/proof_audit/lower_corridor/phase2o_tail_radius/phase2o_tail_radius_scan.json",
        help="Output JSON report path",
    )
    ap.add_argument(
        "--csv",
        default="tables/proof_audit/lower_corridor/phase2o_tail_radius/phase2o_tail_radius_scan.csv",
        help="Output CSV table path",
    )
    ap.add_argument(
        "--candidate-out",
        default="artifacts/proof_audit/lower_corridor/phase2o_tail_radius/phase2o_tail_radius_candidate.json",
        help="Phase-2O single-segment candidate output path",
    )
    ap.add_argument("--radius-multipliers", default="1.0,1.02,1.05,1.1,1.2,1.5,2.0,2.5,3.0,3.25,3.5,4.0")
    ap.add_argument("--sigma-values", default="0.0001,0.000075,0.00005,0.000025,0.00001,0.000005,0.0000025,0.000001")
    ap.add_argument("--tail-band-fractions", default="0.5,0.65,0.75,0.85")
    ap.add_argument("--tail-safety-factors", default="2,4,8,16")
    ap.add_argument("--nonlinear-margin-fraction", type=float, default=0.25)
    ap.add_argument("--outward-rounding-tolerance", type=float, default=1.0e-12)
    ap.add_argument("--theorem-margin-safety-factor", type=float, default=10.0)
    ap.add_argument("--min-theorem-sigma", type=float, default=1.0e-8)
    ap.add_argument("--include-raw-input", action="store_true", help="Include raw Phase-2N attempt in the report JSON")
    ap.add_argument(
        "--allow-experimental-candidate",
        action="store_true",
        help="Allow the candidate JSON to select a diagnostic positive row. The candidate remains diagnostic/non-promotable.",
    )
    args = ap.parse_args()

    cfg = Phase2OScanConfig(
        input_path=str(args.input),
        radius_multipliers=parse_float_list(args.radius_multipliers),
        sigma_values=parse_float_list(args.sigma_values),
        tail_band_fractions=parse_float_list(args.tail_band_fractions),
        tail_safety_factors=parse_float_list(args.tail_safety_factors),
        nonlinear_margin_fraction=float(args.nonlinear_margin_fraction),
        outward_rounding_tolerance=float(args.outward_rounding_tolerance),
        theorem_margin_safety_factor=float(args.theorem_margin_safety_factor),
        min_theorem_sigma=float(args.min_theorem_sigma),
        allow_experimental_candidate=bool(args.allow_experimental_candidate),
    )
    report = build_phase2o_report(args.input, cfg)
    write_phase2o_report(report, args.out, include_raw_input=bool(args.include_raw_input))
    write_phase2o_csv(report, args.csv)
    candidate = build_phase2o_candidate(
        report,
        source_artifact=str(args.out),
        allow_experimental=bool(args.allow_experimental_candidate),
    )
    atomic_write_json(args.candidate_out, candidate)
    print(print_compact_report(report))
    print(f"wrote report: {args.out}")
    print(f"wrote csv: {args.csv}")
    print(f"wrote candidate: {args.candidate_out}")
    # A diagnostic non-closure is still a successful audit run; closure status is in the JSON.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
