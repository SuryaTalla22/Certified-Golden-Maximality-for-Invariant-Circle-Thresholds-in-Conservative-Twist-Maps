#!/usr/bin/env python
from __future__ import annotations
import argparse, json


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("summary_json")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()
    with open(args.summary_json) as f:
        s = json.load(f)
    out = dict(s)
    out["top_candidates"] = s.get("top_candidates", [])[: args.top]
    print(json.dumps(out, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
