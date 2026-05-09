#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from kam_theorem_suite.lower_param.phase5f_formal_attachment import summarize_phase5f


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize Phase 5F attachment candidate summary.")
    p.add_argument("summary_json")
    p.add_argument("--out", default=None)
    args = p.parse_args()
    compact = summarize_phase5f(args.summary_json, args.out)
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
