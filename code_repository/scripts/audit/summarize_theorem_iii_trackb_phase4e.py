#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kam_theorem_suite.lower_param.dealiased_polish import summarize_phase4e


def main() -> None:
    ap = argparse.ArgumentParser(description='Summarize Track B Phase 4e dealiased polish results.')
    ap.add_argument('summary_json')
    ap.add_argument('--top', type=int, default=20)
    args = ap.parse_args()
    print(json.dumps(summarize_phase4e(args.summary_json, top=args.top), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
