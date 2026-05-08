#!/usr/bin/env python3
from __future__ import annotations

import argparse
from kam_theorem_suite.lower_param.phase5f_formal_attachment import assemble_phase5f


def main() -> None:
    p = argparse.ArgumentParser(description="Generate Phase 5F formal-attachment candidate (fail-closed).")
    p.add_argument("--certificate", required=True)
    p.add_argument("--phase5c-summary", required=True)
    p.add_argument("--require-nu", type=float, default=1.001)
    p.add_argument("--require-radius", type=float, default=3e-5)
    p.add_argument("--require-cutoff", default="full")
    p.add_argument("--require-tail-start", type=float, default=0.90)
    p.add_argument("--required-min-lower-anchor-k", type=float, default=0.971635)
    p.add_argument("--min-margin", type=float, default=0.0)
    p.add_argument("--min-relative-margin", type=float, default=0.25)
    p.add_argument("--max-z", type=float, default=0.5)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    summary = assemble_phase5f(
        certificate_path=args.certificate,
        phase5c_summary_path=args.phase5c_summary,
        out_dir=args.out_dir,
        require_nu=args.require_nu,
        require_radius=args.require_radius,
        require_cutoff=args.require_cutoff,
        require_tail_start=args.require_tail_start,
        min_anchor_k=args.required_min_lower_anchor_k,
        max_z=args.max_z,
        min_relative_margin=args.min_relative_margin,
        min_margin=args.min_margin,
        force=args.force,
    )
    print(f"[phase5f] summary={args.out_dir}/phase5f_attachment_candidate_summary.json")
    print(f"[phase5f] replay_passed={summary['replay_passed']} promotion_ready={summary['promotion_ready']}")
    print(f"[phase5f] expected_phase5e_decision={summary['expected_phase5e_decision']}")


if __name__ == "__main__":
    main()
