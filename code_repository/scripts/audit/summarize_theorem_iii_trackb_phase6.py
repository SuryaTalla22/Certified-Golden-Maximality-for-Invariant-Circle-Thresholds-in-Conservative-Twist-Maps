#!/usr/bin/env python3
import argparse
from kam_theorem_suite.lower_param.phase6_final_integration import summarize_phase6


def main():
    ap = argparse.ArgumentParser(description="Summarize Phase 6 final integration/replay output.")
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    summarize_phase6(args.input, args.out)

if __name__ == "__main__":
    main()
