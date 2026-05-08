#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from kam_theorem_suite.audit.lower_anchor_phase2p_modewise_tail import (  # noqa: E402
    Phase2PScanConfig,
    atomic_write_json,
    build_phase2p_candidate,
    build_phase2p_report,
    parse_float_list,
    parse_int_list,
    print_compact_report,
    write_phase2p_csv,
    write_phase2p_report,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Phase 2P modewise tail-response scan for the Theorem-III lower anchor. "
            "Consumes a Phase-2O candidate/report or Phase-2N attempt and writes a fail-closed modewise tail audit."
        )
    )
    ap.add_argument("--input", required=True, help="Phase-2O candidate/report, Phase-2N summary, or Phase-2N single-N JSON")
    ap.add_argument(
        "--out",
        default="artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_modewise_tail_scan.json",
        help="Output JSON report path",
    )
    ap.add_argument(
        "--csv",
        default="tables/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_modewise_tail_scan.csv",
        help="Output CSV table path",
    )
    ap.add_argument(
        "--candidate-out",
        default="artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_modewise_tail_candidate.json",
        help="Output Phase-2P single-segment candidate path",
    )
    ap.add_argument("--sigma-values", default="0.0001,0.000075,0.00005,0.000025,0.00001,0.000005,0.0000025,0.000001")
    ap.add_argument("--tail-cutoffs", default="1024,2048,4096,8192,16384")
    ap.add_argument("--oversample-factors", default="16")
    ap.add_argument("--outward-rounding-tolerance", type=float, default=1.0e-12)
    ap.add_argument("--theorem-margin-safety-factor", type=float, default=10.0)
    ap.add_argument("--min-theorem-sigma", type=float, default=1.0e-8)
    ap.add_argument("--golden-rho-tolerance", type=float, default=1.0e-12)
    ap.add_argument("--include-raw-input", action="store_true", help="Include raw input and Phase-2N attempt in the report JSON")
    args = ap.parse_args()

    cfg = Phase2PScanConfig(
        input_path=str(args.input),
        sigma_values=parse_float_list(args.sigma_values),
        tail_cutoffs=parse_int_list(args.tail_cutoffs),
        oversample_factors=parse_int_list(args.oversample_factors),
        outward_rounding_tolerance=float(args.outward_rounding_tolerance),
        theorem_margin_safety_factor=float(args.theorem_margin_safety_factor),
        min_theorem_sigma=float(args.min_theorem_sigma),
        golden_rho_tolerance=float(args.golden_rho_tolerance),
    )
    report = build_phase2p_report(args.input, cfg)
    write_phase2p_report(report, args.out, include_raw_input=bool(args.include_raw_input))
    write_phase2p_csv(report, args.csv)
    candidate = build_phase2p_candidate(report, source_artifact=str(args.out))
    atomic_write_json(args.candidate_out, candidate)
    print(print_compact_report(report))
    print(f"wrote report: {args.out}")
    print(f"wrote csv: {args.csv}")
    print(f"wrote candidate: {args.candidate_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
