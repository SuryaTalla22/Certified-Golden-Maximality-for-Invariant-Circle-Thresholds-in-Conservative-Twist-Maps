#!/usr/bin/env python3
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5fb_hash_binding import bind_certificate_hash


def main() -> None:
    p = argparse.ArgumentParser(description="Bind a Phase 5F attachment candidate to a Phase 5D scaffold SHA256 hash.")
    p.add_argument("--certificate", required=True)
    p.add_argument("--attachment", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    summary = bind_certificate_hash(
        certificate_path=args.certificate,
        attachment_path=args.attachment,
        out_dir=args.out_dir,
        force=args.force,
    )
    print(f"[phase5fb] bound_attachment={summary['hash_bound_attachment_path']}")
    print(f"[phase5fb] summary={args.out_dir}/phase5fb_hash_binding_summary.json")


if __name__ == "__main__":
    main()
