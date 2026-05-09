#!/usr/bin/env python3
from __future__ import annotations

import argparse
from kam_theorem_suite.lower_param.phase5f_formal_attachment import (
    load_json,
    replay_formal_attachment_candidate,
    _atomic_write_json,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Replay Phase 5F formal-attachment candidate.")
    p.add_argument("--attachment", required=True)
    p.add_argument("--require-nu", type=float, default=1.001)
    p.add_argument("--require-radius", type=float, default=3e-5)
    p.add_argument("--require-cutoff", default="full")
    p.add_argument("--require-tail-start", type=float, default=0.90)
    p.add_argument("--required-min-lower-anchor-k", type=float, default=0.971635)
    p.add_argument("--min-relative-margin", type=float, default=0.25)
    p.add_argument("--max-z", type=float, default=0.5)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    import os
    os.makedirs(args.out_dir, exist_ok=True)
    attachment = load_json(args.attachment)
    replay = replay_formal_attachment_candidate(
        attachment,
        min_anchor_k=args.required_min_lower_anchor_k,
        max_z=args.max_z,
        min_relative_margin=args.min_relative_margin,
        require_nu=args.require_nu,
        require_radius=args.require_radius,
        require_cutoff=args.require_cutoff,
        require_tail_start=args.require_tail_start,
    )
    out = f"{args.out_dir}/phase5f_attachment_candidate_replay_summary.json"
    if os.path.exists(out) and not args.force:
        raise FileExistsError(f"Refusing to overwrite {out}; use --force")
    _atomic_write_json(out, replay)
    print(f"[phase5f-replay] summary={out}")
    print(f"[phase5f-replay] passed={replay['passed']} promotion_ready={replay['promotion_ready']}")


if __name__ == "__main__":
    main()
