#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from kam_theorem_suite.audit.lower_anchor_phase2z_tail_response_pilot import load_json, summarize_phase2z_run, write_json


def tail(path: str | Path, n: int = 100) -> str:
    p = Path(path)
    if not p.exists():
        return f"MISSING: {p}"
    lines = p.read_text(errors="replace").splitlines()
    return "\n".join(lines[-n:])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Print compact Phase-2Z tail-response pilot report.")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--run-summary", required=True)
    ap.add_argument("--log", default="logs/pass1_012b1/phase2z_tail_response_pilot.log")
    ap.add_argument("--out", default="artifacts/proof_audit/lower_corridor/phase2z_tail_response/collar_012b1_phase2z_tail_response_fast_report.json")
    args = ap.parse_args(argv)
    plan = load_json(args.plan)
    run_summary = load_json(args.run_summary)
    report = summarize_phase2z_run(run_summary, plan)
    report["plan_path"] = str(args.plan)
    report["run_summary_path"] = str(args.run_summary)
    report["log_tail"] = tail(args.log, 160)
    write_json(args.out, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"WROTE: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
