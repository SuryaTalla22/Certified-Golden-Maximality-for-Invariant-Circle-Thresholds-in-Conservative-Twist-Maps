#!/usr/bin/env python3
import argparse
from kam_theorem_suite.lower_param.phase6_final_integration import replay_phase6_final_integration


def main():
    ap = argparse.ArgumentParser(description="Phase 6: replay final Theorem III Track B lower-anchor artifact.")
    ap.add_argument("--final-artifact", required=True)
    ap.add_argument("--theorem-i-artifact")
    ap.add_argument("--theorem-ii-artifact")
    ap.add_argument("--theorem-iv-artifact")
    ap.add_argument("--required-min-lower-anchor-k", type=float, required=True)
    ap.add_argument("--require-nu", type=float, required=True)
    ap.add_argument("--require-radius", type=float, required=True)
    ap.add_argument("--require-cutoff", required=True)
    ap.add_argument("--require-tail-start", type=float, required=True)
    ap.add_argument("--min-relative-margin", type=float, default=0.25)
    ap.add_argument("--max-z", type=float, default=0.5)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    replay_phase6_final_integration(
        final_artifact_path=args.final_artifact,
        theorem_i_artifact=args.theorem_i_artifact,
        theorem_ii_artifact=args.theorem_ii_artifact,
        theorem_iv_artifact=args.theorem_iv_artifact,
        required_min_lower_anchor_k=args.required_min_lower_anchor_k,
        require_nu=args.require_nu,
        require_radius=args.require_radius,
        require_cutoff=args.require_cutoff,
        require_tail_start=args.require_tail_start,
        min_relative_margin=args.min_relative_margin,
        max_z=args.max_z,
        out_dir=args.out_dir,
        force=args.force,
    )

if __name__ == "__main__":
    main()
