#!/usr/bin/env python3
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5h_cohomology_frame_components import generate_phase5h_attachment, summarize_phase5h


def main() -> None:
    p = argparse.ArgumentParser(description="Generate Phase 5H cohomology-inverse and frame/reducibility component attachment.")
    p.add_argument("--certificate", required=True)
    p.add_argument("--base-attachment", required=True)
    p.add_argument("--seed-npz", required=True)
    p.add_argument("--phase5c-summary", default=None)
    p.add_argument("--required-min-lower-anchor-k", type=float, default=0.971635)
    p.add_argument("--require-nu", type=float, required=True)
    p.add_argument("--require-radius", type=float, required=True)
    p.add_argument("--require-cutoff", required=True)
    p.add_argument("--require-tail-start", type=float, required=True)
    p.add_argument("--min-relative-margin", type=float, default=0.25)
    p.add_argument("--max-z", type=float, default=0.5)
    p.add_argument("--small-divisor-slack", type=float, default=1e-14)
    p.add_argument("--frame-slack", type=float, default=1e-12)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    summary = generate_phase5h_attachment(
        certificate_path=args.certificate,
        base_attachment_path=args.base_attachment,
        seed_npz=args.seed_npz,
        phase5c_summary_path=args.phase5c_summary,
        out_dir=args.out_dir,
        require_nu=args.require_nu,
        require_radius=args.require_radius,
        require_cutoff=args.require_cutoff,
        require_tail_start=args.require_tail_start,
        min_relative_margin=args.min_relative_margin,
        max_z=args.max_z,
        small_divisor_slack=args.small_divisor_slack,
        frame_slack=args.frame_slack,
        force=args.force,
    )
    summarize_phase5h(
        f"{args.out_dir}/phase5h_component_summary.json",
        f"{args.out_dir}/phase5h_compact_report.json",
    )
    print(f"[phase5h] attachment={summary['attachment_path']}")
    print(f"[phase5h] summary={args.out_dir}/phase5h_component_summary.json")
    print(f"[phase5h] compact={args.out_dir}/phase5h_compact_report.json")

if __name__ == "__main__":
    main()
