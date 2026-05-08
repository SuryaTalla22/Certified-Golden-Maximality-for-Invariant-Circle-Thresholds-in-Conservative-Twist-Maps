#!/usr/bin/env python3
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5fb_hash_binding import replay_hash_binding


def main() -> None:
    p = argparse.ArgumentParser(description="Replay Phase 5F-b certificate-hash binding checks.")
    p.add_argument("--certificate", required=True)
    p.add_argument("--attachment", required=True)
    p.add_argument("--required-min-lower-anchor-k", type=float, default=0.971635)
    p.add_argument("--require-nu", type=float, default=1.001)
    p.add_argument("--require-radius", type=float, default=3e-5)
    p.add_argument("--require-cutoff", default="full")
    p.add_argument("--require-tail-start", type=float, default=0.90)
    p.add_argument("--min-relative-margin", type=float, default=0.25)
    p.add_argument("--max-z", type=float, default=0.5)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    summary = replay_hash_binding(
        certificate_path=args.certificate,
        attachment_path=args.attachment,
        out_dir=args.out_dir,
        force=args.force,
        required_min_lower_anchor_k=args.required_min_lower_anchor_k,
        require_nu=args.require_nu,
        require_radius=args.require_radius,
        require_cutoff=args.require_cutoff,
        require_tail_start=args.require_tail_start,
        min_relative_margin=args.min_relative_margin,
        max_z=args.max_z,
    )
    print(f"[phase5fb] replay_passed={summary['passed']}")
    print(f"[phase5fb] replay_summary={args.out_dir}/phase5fb_hash_binding_replay_summary.json")


if __name__ == "__main__":
    main()
