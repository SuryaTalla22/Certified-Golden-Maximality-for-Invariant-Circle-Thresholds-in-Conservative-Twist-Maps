#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from kam_theorem_suite.lower_param.phase5e_promotion_gate import compact_report


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize Phase 5E promotion gate output.")
    p.add_argument("summary_json")
    p.add_argument("--out", default=None)
    args = p.parse_args()
    with Path(args.summary_json).open("r", encoding="utf-8") as f:
        summary = json.load(f)
    report = compact_report(summary)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
