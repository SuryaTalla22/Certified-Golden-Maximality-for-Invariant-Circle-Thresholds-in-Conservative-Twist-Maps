#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from kam_theorem_suite.audit.lower_anchor_phase2aa_stage2a_expand import build_expand_report, write_json


def main() -> int:
    ap = argparse.ArgumentParser(description="Print compact Phase 2AA Stage 2A-Expand report.")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--export-summary", required=True)
    ap.add_argument("--profiled", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    report = build_expand_report(
        plan_path=args.plan,
        export_summary_path=args.export_summary,
        profiled_guard_path=args.profiled,
    )
    write_json(args.out, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"WROTE: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
