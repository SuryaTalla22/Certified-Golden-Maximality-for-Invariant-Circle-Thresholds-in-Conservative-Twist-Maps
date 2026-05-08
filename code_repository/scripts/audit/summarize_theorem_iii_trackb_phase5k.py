#!/usr/bin/env python3
import argparse
from kam_theorem_suite.lower_param.phase5k_global_promotion import summarize_phase5k


def main():
    ap = argparse.ArgumentParser(description="Summarize Phase 5K JSON output.")
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    summarize_phase5k(args.input, args.out)

if __name__ == "__main__":
    main()
