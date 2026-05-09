#!/usr/bin/env python3
from __future__ import annotations

"""Attempt to build final replay shells from a proof-audit bundle."""

from pathlib import Path
import argparse
import json
import sys


def _insert_repo_on_path(repository_root: Path) -> None:
    root = repository_root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit_bundle")
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--allow-missing-layers", action="store_true")
    parser.add_argument("--expect-fail", action="store_true")
    args = parser.parse_args()

    root = Path(args.repository_root).resolve()
    _insert_repo_on_path(root)
    from kam_theorem_suite.paper_replay_inputs import build_shells_from_proof_audit

    try:
        shells = build_shells_from_proof_audit(
            Path(args.audit_bundle),
            allow_missing_layers=args.allow_missing_layers,
        )
    except Exception as exc:
        print(f"proof-audit replay rejected: {exc}")
        return 0 if args.expect_fail else 1
    print(json.dumps({"status": "accepted", "num_shells": len(shells)}, indent=2, sort_keys=True))
    return 1 if args.expect_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
