#!/usr/bin/env python3
import argparse
from kam_theorem_suite.lower_param.phase5k_global_promotion import independent_replay_and_promote


def main():
    ap = argparse.ArgumentParser(description="Phase 5K: independent replay and promoted formal attachment generation.")
    ap.add_argument("--certificate", required=True)
    ap.add_argument("--backend-candidate", required=True)
    ap.add_argument("--attachment-candidate", required=True)
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
    independent_replay_and_promote(
        certificate_path=args.certificate,
        backend_candidate_path=args.backend_candidate,
        attachment_candidate_path=args.attachment_candidate,
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
