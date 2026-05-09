#!/usr/bin/env python3
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5g_formal_components import generate_phase5g_attachment, summarize_phase5g


def main() -> None:
    p = argparse.ArgumentParser(description="Generate Phase 5G residual/small-divisor formal component attachment candidate.")
    p.add_argument("--certificate", required=True)
    p.add_argument("--base-attachment", required=True)
    p.add_argument("--seed-npz", required=True)
    p.add_argument("--phase5c-summary", default=None)
    p.add_argument("--require-nu", type=float, required=True)
    p.add_argument("--require-radius", type=float, required=True)
    p.add_argument("--require-cutoff", required=True)
    p.add_argument("--require-tail-start", type=float, required=True)
    p.add_argument("--grid-factor", type=int, default=4)
    p.add_argument("--residual-slack", type=float, default=1e-13)
    p.add_argument("--small-divisor-slack", type=float, default=1e-14)
    p.add_argument("--force-sign", type=int, choices=[-1, 1], default=None)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    summary = generate_phase5g_attachment(
        certificate_path=args.certificate,
        base_attachment_path=args.base_attachment,
        seed_npz=args.seed_npz,
        phase5c_summary_path=args.phase5c_summary,
        out_dir=args.out_dir,
        nu=args.require_nu,
        radius=args.require_radius,
        cutoff_spec=args.require_cutoff,
        tail_start=args.require_tail_start,
        grid_factor=args.grid_factor,
        residual_slack=args.residual_slack,
        small_divisor_slack=args.small_divisor_slack,
        force_sign=args.force_sign,
        force=args.force,
    )
    summarize_phase5g(
        f"{args.out_dir}/phase5g_component_summary.json",
        f"{args.out_dir}/phase5g_compact_report.json",
    )
    print(f"[phase5g] attachment={summary['attachment_path']}")
    print(f"[phase5g] summary={args.out_dir}/phase5g_component_summary.json")
    print(f"[phase5g] compact={args.out_dir}/phase5g_compact_report.json")

if __name__ == "__main__":
    main()
