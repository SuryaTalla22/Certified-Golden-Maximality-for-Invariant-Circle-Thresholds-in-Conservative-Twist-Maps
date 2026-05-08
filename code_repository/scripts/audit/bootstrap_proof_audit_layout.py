#!/usr/bin/env python3
from __future__ import annotations

"""Create the Phase-0/1 proof-audit directory layout."""

from pathlib import Path
import argparse


AUDIT_DIRS = (
    "kam_theorem_suite/audit",
    "scripts/audit",
    "artifacts/proof_audit",
    "figures/proof_audit",
    "notebooks/proof_audit",
    "tables/proof_audit",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=".")
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    for rel in AUDIT_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)
    print("created/verified proof-audit layout under", root)
    for rel in AUDIT_DIRS:
        print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
