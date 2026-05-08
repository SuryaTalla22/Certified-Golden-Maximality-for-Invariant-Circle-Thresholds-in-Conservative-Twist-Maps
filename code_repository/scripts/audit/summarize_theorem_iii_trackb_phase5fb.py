#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
from kam_theorem_suite.lower_param.phase5fb_hash_binding import summarize_phase5fb


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize Phase 5F-b hash-binding or replay output.")
    p.add_argument("summary_json")
    p.add_argument("--out", required=False)
    args = p.parse_args()
    compact = summarize_phase5fb(args.summary_json)
    text = json.dumps(compact, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
