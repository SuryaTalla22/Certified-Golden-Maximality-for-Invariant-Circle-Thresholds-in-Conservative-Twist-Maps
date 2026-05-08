#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from kam_theorem_suite.lower_param.phase5g_formal_components import summarize_phase5g


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize Phase 5G-b component or replay report.")
    p.add_argument("input")
    p.add_argument("--out", default=None)
    args = p.parse_args()
    compact = summarize_phase5g(args.input, args.out)
    compact["phase5gb_note"] = "sign/hash-corrected Phase 5G-b report"
    if args.out:
        from kam_theorem_suite.lower_param.phase5g_formal_components import write_json
        write_json(args.out, compact)
    print(json.dumps(compact, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
