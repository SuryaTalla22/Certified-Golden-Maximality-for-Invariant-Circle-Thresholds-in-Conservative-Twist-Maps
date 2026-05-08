#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2m_two_regime import execute_collar_jobs


def main() -> int:
    p = argparse.ArgumentParser(description="Execute Phase-2M collar jobs from a generated plan.")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--plan", default="artifacts/proof_audit/lower_corridor/phase2m_collar_plan.json")
    p.add_argument("--max-jobs", type=int, default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--timeout-seconds", type=float, default=None)
    args = p.parse_args()
    payload = execute_collar_jobs(root=args.repo_root, plan_path=args.plan, max_jobs=args.max_jobs, force=args.force, timeout_seconds=args.timeout_seconds)
    print(json.dumps({
        "attempted_count": payload.get("attempted_count"),
        "skipped_ready_count": payload.get("skipped_ready_count"),
        "theorem_ready_job_count": payload.get("theorem_ready_job_count"),
        "timeout_count": payload.get("timeout_count"),
        "summary": "artifacts/proof_audit/lower_corridor/phase2m_collar_execution_summary.json",
    }, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
