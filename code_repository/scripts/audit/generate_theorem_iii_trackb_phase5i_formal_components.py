#!/usr/bin/env python3
from __future__ import annotations

import argparse
from kam_theorem_suite.lower_param.phase5i_nonlinear_tail import (
    add_common_threshold_args,
    generate_phase5i_attachment,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Generate Phase 5I nonlinear/tail formal-component attachment candidate.")
    p.add_argument("--certificate", required=True)
    p.add_argument("--base-attachment", required=True)
    p.add_argument("--phase5c-summary", required=True)
    add_common_threshold_args(p)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    generate_phase5i_attachment(
        certificate_path=args.certificate,
        base_attachment_path=args.base_attachment,
        phase5c_summary_path=args.phase5c_summary,
        required_min_lower_anchor_k=args.required_min_lower_anchor_k,
        require_nu=args.require_nu,
        require_radius=args.require_radius,
        require_cutoff=args.require_cutoff,
        require_tail_start=args.require_tail_start,
        min_relative_margin=args.min_relative_margin,
        max_z=args.max_z,
        max_q=args.max_q,
        max_tail_residual=args.max_tail_residual,
        max_tail_derivative=args.max_tail_derivative,
        out_dir=args.out_dir,
        force=args.force,
    )


if __name__ == "__main__":
    main()
