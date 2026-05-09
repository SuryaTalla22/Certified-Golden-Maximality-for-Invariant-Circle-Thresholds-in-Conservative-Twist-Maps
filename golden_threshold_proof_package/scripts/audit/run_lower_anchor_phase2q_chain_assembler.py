#!/usr/bin/env python3
"""Assemble Phase-2P theorem-ready lower-collar segments into a chain audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2q_chain import (  # noqa: E402
    Phase2QConfig,
    assemble_phase2q_chain,
    build_phase2q_candidate,
    discover_candidate_paths,
    print_report_summary,
    report_to_dict,
    write_json,
    write_segment_csv,
)


def _split_csv_flags(values: list[str] | None) -> list[str]:
    out: list[str] = []
    for v in values or []:
        for token in str(v).split(","):
            token = token.strip()
            if token:
                out.append(token)
    return out


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", action="append", default=[], help="Explicit Phase-2P candidate path. May be repeated or comma-separated.")
    ap.add_argument("--candidates", default="", help="Comma-separated explicit Phase-2P candidate paths.")
    ap.add_argument("--candidate-glob", action="append", default=[], help="Glob pattern for Phase-2P candidates. May be repeated.")
    ap.add_argument("--out", required=True, help="Output Phase-2Q chain audit JSON.")
    ap.add_argument("--csv", required=True, help="Output Phase-2Q segment table CSV.")
    ap.add_argument("--candidate-out", required=True, help="Output Phase-2Q theorem-facing chain candidate JSON.")
    ap.add_argument("--expected-start", type=float, default=None, help="Expected chain start K value.")
    ap.add_argument("--expected-end", type=float, default=None, help="Expected chain end K value.")
    ap.add_argument("--expected-regime-i-hi", type=float, default=None, help="Certified Regime-I upper endpoint that must meet the first collar segment.")
    ap.add_argument("--final-anchor-hi", type=float, default=None, help="Optional final anchor endpoint for full-collar closure.")
    ap.add_argument("--overlap-tolerance", type=float, default=1.0e-10, help="Allowed positive gap between adjacent intervals.")
    ap.add_argument("--minimum-overlap", type=float, default=None, help="Optional required overlap for every adjacent interval.")
    ap.add_argument("--min-segment-margin", type=float, default=0.0, help="Minimum strictly positive segment radii margin.")
    ap.add_argument("--allow-duplicate-intervals", action="store_true", help="Do not reject duplicate [K_lo,K_hi] intervals.")
    ap.add_argument("--allow-non-phase2p", action="store_true", help="Do not require closure_level=phase2p_modewise_tail_closure.")
    ap.add_argument("--allow-nonpromotable", action="store_true", help="Do not require theorem_facing/promotion_allowed on input segments.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    explicit = _split_csv_flags(args.candidate)
    if args.candidates:
        explicit.extend(_split_csv_flags([args.candidates]))
    globs = _split_csv_flags(args.candidate_glob)
    paths = discover_candidate_paths(candidates=explicit, candidate_globs=globs)

    cfg = Phase2QConfig(
        expected_start=args.expected_start,
        expected_end=args.expected_end,
        expected_regime_i_hi=args.expected_regime_i_hi,
        final_anchor_hi=args.final_anchor_hi,
        overlap_tolerance=args.overlap_tolerance,
        minimum_overlap=args.minimum_overlap,
        min_segment_margin=args.min_segment_margin,
        require_phase2p_closure=not args.allow_non_phase2p,
        require_theorem_facing=not args.allow_nonpromotable,
        require_promotion_allowed=not args.allow_nonpromotable,
        allow_duplicate_intervals=args.allow_duplicate_intervals,
    )

    result = assemble_phase2q_chain(paths, cfg)
    report = report_to_dict(result)
    candidate = build_phase2q_candidate(result)

    write_json(args.out, report)
    write_segment_csv(args.csv, result)
    write_json(args.candidate_out, candidate)

    print(json.dumps(print_report_summary(result), indent=2))
    print(f"wrote report: {args.out}")
    print(f"wrote csv: {args.csv}")
    print(f"wrote candidate: {args.candidate_out}")

    return 0 if result.theorem_facing else 2


if __name__ == "__main__":
    raise SystemExit(main())
