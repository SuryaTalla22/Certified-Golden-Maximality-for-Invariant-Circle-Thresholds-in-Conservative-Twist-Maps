#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2m_two_regime import write_collar_plan


def main() -> int:
    p = argparse.ArgumentParser(description="Generate Phase-2M near-critical collar microsegment jobs.")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--output", default="artifacts/proof_audit/lower_corridor/phase2m_collar_plan.json")
    p.add_argument("--run-script", default="scripts/audit/run_phase2m_collar_jobs.sh")
    p.add_argument("--python-executable", default=sys.executable)
    p.add_argument("--max-jobs", type=int, default=None, help="Generate only the first N jobs for a smoke test.")
    args = p.parse_args()
    payload = write_collar_plan(root=args.repo_root, output_path=args.output, run_script_path=args.run_script, python_executable=args.python_executable, max_jobs=args.max_jobs)
    print(json.dumps({
        "output": args.output,
        "run_script": payload.get("run_script"),
        "job_count": payload.get("job_count"),
        "start": payload.get("start"),
        "final_anchor": payload.get("final_anchor"),
    }, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
