#!/usr/bin/env python3
from __future__ import annotations

import argparse
from kam_theorem_suite.lower_param.phase5e_promotion_gate import GateThresholds, run_phase5e_promotion_gate


def main() -> None:
    p = argparse.ArgumentParser(description="Run Phase 5E fail-closed theorem promotion gate.")
    p.add_argument("--certificate", required=True)
    p.add_argument("--formal-attachment", default=None)
    p.add_argument("--required-min-lower-anchor-k", type=float, default=0.971635)
    p.add_argument("--min-margin", type=float, default=0.0)
    p.add_argument("--min-relative-margin", type=float, default=0.25)
    p.add_argument("--max-z", type=float, default=0.5)
    p.add_argument("--max-q", type=float, default=float("inf"))
    p.add_argument("--max-y", type=float, default=float("inf"))
    p.add_argument("--require-nu", type=float, default=None)
    p.add_argument("--require-radius", type=float, default=None)
    p.add_argument("--require-cutoff", default=None)
    p.add_argument("--require-tail-start", type=float, default=None)
    p.add_argument("--no-template", action="store_true")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    thresholds = GateThresholds(
        required_min_lower_anchor_K=args.required_min_lower_anchor_k,
        min_margin=args.min_margin,
        min_relative_margin=args.min_relative_margin,
        max_z=args.max_z,
        max_q=args.max_q,
        max_y=args.max_y,
        require_nu=args.require_nu,
        require_radius=args.require_radius,
        require_cutoff=args.require_cutoff,
        require_tail_start=args.require_tail_start,
    )
    summary = run_phase5e_promotion_gate(
        certificate_path=args.certificate,
        formal_attachment_path=args.formal_attachment,
        thresholds=thresholds,
        out_dir=args.out_dir,
        emit_template=not args.no_template,
        force=args.force,
    )
    print(f"[phase5e] status={summary['status']} decision={summary['decision']}")
    print(f"[phase5e] summary={args.out_dir}/phase5e_promotion_gate_summary.json")


if __name__ == "__main__":
    main()
