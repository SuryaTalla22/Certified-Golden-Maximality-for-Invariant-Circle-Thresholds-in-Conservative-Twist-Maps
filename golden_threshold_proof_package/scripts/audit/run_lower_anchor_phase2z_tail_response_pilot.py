#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from kam_theorem_suite.audit.lower_anchor_phase2z_tail_response_pilot import build_phase2z_plan, write_json

THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "BLIS_NUM_THREADS": "1",
    "PYTHONUNBUFFERED": "1",
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Phase 2Z tail-response pilot: select q-safe collar-012b1 rows and rerun Phase-2P with deeper tail scan.")
    ap.add_argument("--phase2y", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--seed-json", required=True)
    ap.add_argument("--label", default="collar_012b1_phase2z_tail_response_pilot")
    ap.add_argument("--max-indices", type=int, default=74)
    ap.add_argument("--workers", type=int, default=64)
    ap.add_argument("--q-target", type=float, default=0.999)
    ap.add_argument("--max-tail-factor-needed", type=float, default=0.92)
    ap.add_argument("--max-guard-factor-needed", type=float, default=0.90)
    ap.add_argument("--tail-cutoffs", default="1536,2048,3072,4096,6144,8192,12288")
    ap.add_argument("--phase2p-sigma-values", default="0.0000001,0.000000075,0.00000005,0.000000025")
    ap.add_argument("--phase2o-sigma-values", default="0.0000001,0.00000025,0.0000005,0.000001")
    ap.add_argument("--radius-multipliers", default="0.95,0.98,1.0,1.02,1.04,1.06,1.08,1.1,1.12,1.14,1.16,1.18,1.2,1.25,1.3")
    ap.add_argument("--plan-out", default="artifacts/proof_audit/lower_corridor/phase2z_tail_response/collar_012b1_phase2z_tail_response_plan.json")
    ap.add_argument("--run", action="store_true", help="Actually execute the generated Phase-2X command. Without this, only write the plan.")
    ap.add_argument("--log", default="logs/pass1_012b1/phase2z_tail_response_pilot.log")
    args = ap.parse_args(argv)

    plan = build_phase2z_plan(
        phase2y_path=args.phase2y,
        summary_path=args.summary,
        seed_json=args.seed_json,
        label=args.label,
        max_indices=args.max_indices,
        workers=args.workers,
        q_target=args.q_target,
        max_tail_factor_needed=args.max_tail_factor_needed,
        max_guard_factor_needed=args.max_guard_factor_needed,
        tail_cutoffs=args.tail_cutoffs,
        phase2p_sigma_values=args.phase2p_sigma_values,
        phase2o_sigma_values=args.phase2o_sigma_values,
        radius_multipliers=args.radius_multipliers,
    )
    write_json(args.plan_out, plan)
    print(json.dumps({
        "status": plan["status"],
        "selected_count": plan["selected_count"],
        "indices_csv": plan["indices_csv"],
        "bucket_counts": plan["bucket_counts"],
        "plan_out": args.plan_out,
        "command_string": plan["command_string"],
    }, indent=2, sort_keys=True))

    if not args.run:
        return 0
    if not plan.get("indices_csv"):
        print("No indices selected; not running.", file=sys.stderr)
        return 2
    env = os.environ.copy()
    env.update(THREAD_ENV)
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w") as log:
        log.write("# Phase 2Z generated command\n")
        log.write(plan["command_string"] + "\n\n")
        log.flush()
        proc = subprocess.run(plan["command"], cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
    print(json.dumps({"status": "phase2z-subprocess-finished", "returncode": proc.returncode, "log": str(log_path)}, indent=2))
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
