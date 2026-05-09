#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2m_two_regime import freeze_regime_i


def main() -> int:
    p = argparse.ArgumentParser(description="Freeze the theorem-ready Regime-I lower chain through a target K.")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--start", type=float, default=0.265)
    p.add_argument("--target-hi", type=float, default=0.9600001)
    p.add_argument("--output", default="artifacts/proof_audit/lower_corridor/lower_regime_I_chain.json")
    p.add_argument("--extra-glob", action="append", default=None, help="Optional extra candidate glob, repeatable.")
    p.add_argument("--strict", action="store_true", help="Exit nonzero if Regime I is not theorem-facing.")
    args = p.parse_args()
    payload = freeze_regime_i(root=args.repo_root, start=args.start, target_hi=args.target_hi, output_path=args.output, extra_globs=args.extra_glob)
    print(json.dumps({
        "output": args.output,
        "theorem_facing": payload.get("theorem_facing"),
        "covered_interval": payload.get("covered_interval"),
        "min_segment_margin": payload.get("min_segment_margin"),
        "min_internal_overlap": payload.get("min_internal_overlap"),
        "failure_fields": payload.get("failure_fields"),
        "selected_segment_count": len(payload.get("anchor_segments", [])),
    }, indent=2, sort_keys=True))
    if args.strict and not payload.get("theorem_facing"):
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
