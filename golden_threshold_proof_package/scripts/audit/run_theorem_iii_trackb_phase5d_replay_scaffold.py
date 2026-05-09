#!/usr/bin/env python3
from __future__ import annotations

import argparse
from kam_theorem_suite.lower_param.phase5d_certificate_scaffold import replay_certificate_file


def main() -> None:
    ap = argparse.ArgumentParser(description="Replay/validate a Phase 5D diagnostic certificate scaffold.")
    ap.add_argument("--certificate", required=True)
    ap.add_argument("--min-margin", type=float, default=0.0)
    ap.add_argument("--min-relative-margin", type=float, default=0.25)
    ap.add_argument("--max-z", type=float, default=0.5)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    replay = replay_certificate_file(
        certificate_path=args.certificate,
        out_dir=args.out_dir,
        min_margin=args.min_margin,
        min_relative_margin=args.min_relative_margin,
        max_z=args.max_z,
        force=args.force,
    )
    print(f"[phase5d-replay] passed={replay['passed']} failed_checks={len(replay['failed_checks'])}")


if __name__ == "__main__":
    main()
