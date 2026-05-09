#!/usr/bin/env python3
from __future__ import annotations

import argparse
from kam_theorem_suite.lower_param.phase5d_certificate_scaffold import assemble_phase5d, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="Assemble diagnostic Phase 5D Track B certificate scaffold from Phase 5C backend output.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--phase5c-summary", default=None, help="Path to phase5c_interval_backend_summary.json or compact report with top_candidates.")
    src.add_argument("--record", default=None, help="Path to one explicit Phase 5C backend record JSON.")
    ap.add_argument("--prefer-cutoff", default="full")
    ap.add_argument("--prefer-tail-start", type=float, default=0.90)
    ap.add_argument("--prefer-radius", type=float, default=3e-5)
    ap.add_argument("--min-anchor-k", type=float, default=0.971635)
    ap.add_argument("--min-margin", type=float, default=0.0)
    ap.add_argument("--min-relative-margin", type=float, default=0.25)
    ap.add_argument("--max-z", type=float, default=0.5)
    ap.add_argument("--skip-negative-controls", action="store_true")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    summary = assemble_phase5d(
        summary_path=args.phase5c_summary,
        record_path=args.record,
        out_dir=args.out_dir,
        prefer_cutoff=args.prefer_cutoff,
        prefer_tail_start=args.prefer_tail_start,
        prefer_radius=args.prefer_radius,
        min_anchor_k=args.min_anchor_k,
        min_margin=args.min_margin,
        min_relative_margin=args.min_relative_margin,
        max_z=args.max_z,
        run_negatives=not args.skip_negative_controls,
        force=args.force,
    )
    print(f"[phase5d] certificate={summary['certificate_path']}")
    print(f"[phase5d] replay_passed={summary['replay_passed']} negative_controls_passed={summary['negative_controls_passed']}")


if __name__ == "__main__":
    main()
