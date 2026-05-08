#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from kam_theorem_suite.lower_param.phase5b_interval_component import summarize_phase5b


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize Phase 5B interval-component audit")
    ap.add_argument("summary_json")
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()
    print(json.dumps(summarize_phase5b(args.summary_json, top=args.top), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
