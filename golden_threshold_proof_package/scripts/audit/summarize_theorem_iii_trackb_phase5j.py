#!/usr/bin/env python3
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5j_branch_graph import summarize_phase5j


def main() -> None:
    ap = argparse.ArgumentParser(description="Copy/normalize Phase 5J compact summary.")
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    summarize_phase5j(args.input, args.out)


if __name__ == "__main__":
    main()
