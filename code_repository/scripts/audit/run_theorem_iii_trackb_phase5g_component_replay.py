#!/usr/bin/env python3
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5g_formal_components import replay_phase5g_attachment, summarize_phase5g


def main() -> None:
    p = argparse.ArgumentParser(description="Replay Phase 5G residual/small-divisor component attachment candidate.")
    p.add_argument("--certificate", required=True)
    p.add_argument("--attachment", required=True)
    p.add_argument("--seed-npz", required=True)
    p.add_argument("--required-min-lower-anchor-k", type=float, required=True)
    p.add_argument("--require-nu", type=float, required=True)
    p.add_argument("--require-radius", type=float, required=True)
    p.add_argument("--require-cutoff", required=True)
    p.add_argument("--require-tail-start", type=float, required=True)
    p.add_argument("--min-relative-margin", type=float, default=0.25)
    p.add_argument("--max-z", type=float, default=0.5)
    p.add_argument("--residual-slack", type=float, default=1e-13)
    p.add_argument("--small-divisor-slack", type=float, default=1e-14)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    summary = replay_phase5g_attachment(
        certificate_path=args.certificate,
        attachment_path=args.attachment,
        seed_npz=args.seed_npz,
        out_dir=args.out_dir,
        required_min_lower_anchor_k=args.required_min_lower_anchor_k,
        require_nu=args.require_nu,
        require_radius=args.require_radius,
        require_cutoff=args.require_cutoff,
        require_tail_start=args.require_tail_start,
        min_relative_margin=args.min_relative_margin,
        max_z=args.max_z,
        residual_slack=args.residual_slack,
        small_divisor_slack=args.small_divisor_slack,
        force=args.force,
    )
    summarize_phase5g(
        f"{args.out_dir}/phase5g_component_replay_summary.json",
        f"{args.out_dir}/phase5g_replay_compact_report.json",
    )
    print(f"[phase5g] replay={args.out_dir}/phase5g_component_replay_summary.json")
    print(f"[phase5g] compact={args.out_dir}/phase5g_replay_compact_report.json")
    if not summary.get("passed", False):
        raise SystemExit(2)

if __name__ == "__main__":
    main()
