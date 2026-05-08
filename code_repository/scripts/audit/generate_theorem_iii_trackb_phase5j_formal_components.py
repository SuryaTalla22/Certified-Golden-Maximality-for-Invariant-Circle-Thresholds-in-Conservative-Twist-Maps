#!/usr/bin/env python3
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5j_branch_graph import generate_phase5j_attachment


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Phase 5J branch/chart and graph-consumption component attachment.")
    ap.add_argument("--certificate", required=True)
    ap.add_argument("--base-attachment", required=True)
    ap.add_argument("--required-min-lower-anchor-k", type=float, required=True)
    ap.add_argument("--require-nu", type=float, required=True)
    ap.add_argument("--require-radius", type=float, required=True)
    ap.add_argument("--require-cutoff", required=True)
    ap.add_argument("--require-tail-start", type=float, required=True)
    ap.add_argument("--expected-family", default="standard_sine_twist_map")
    ap.add_argument("--expected-omega", default="golden")
    ap.add_argument("--min-relative-margin", type=float, default=0.25)
    ap.add_argument("--max-z", type=float, default=0.5)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    generate_phase5j_attachment(
        certificate_path=args.certificate,
        base_attachment_path=args.base_attachment,
        required_min_lower_anchor_k=args.required_min_lower_anchor_k,
        require_nu=args.require_nu,
        require_radius=args.require_radius,
        require_cutoff=args.require_cutoff,
        require_tail_start=args.require_tail_start,
        expected_family=args.expected_family,
        expected_omega=args.expected_omega,
        min_relative_margin=args.min_relative_margin,
        max_z=args.max_z,
        out_dir=args.out_dir,
        force=args.force,
    )


if __name__ == "__main__":
    main()
