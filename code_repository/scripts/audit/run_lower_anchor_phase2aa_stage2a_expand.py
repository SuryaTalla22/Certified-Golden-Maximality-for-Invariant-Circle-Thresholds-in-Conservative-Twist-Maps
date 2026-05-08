#!/usr/bin/env python
from __future__ import annotations

"""Run Phase 2AA Stage 2A-Expand.

This wrapper:
  1. builds a q-safe/tail-guard expansion plan from Phase-2Y;
  2. optionally regenerates those indices with Stage-1B raw-payload export;
  3. optionally runs the Stage-2A profiled-guard diagnostic on the expanded cohort.

All outputs are diagnostic-only.  No theorem-facing status is promoted.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from kam_theorem_suite.audit.lower_anchor_phase2aa_stage2a_expand import build_expand_plan, write_json


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 2AA Stage 2A expanded profiled-guard diagnostic cohort.")
    ap.add_argument("--phase2y", required=True, help="Phase-2Y sensitivity JSON.")
    ap.add_argument("--summary", required=True, help="Original Phase-2V 012b1 summary JSON.")
    ap.add_argument("--seed-json", required=True, help="Seed JSON for Stage-1B raw-payload export.")
    ap.add_argument("--label", default="collar_012b1_phase2aa_stage2a_expand")
    ap.add_argument("--max-indices", type=int, default=96)
    ap.add_argument("--q-cutoff", type=float, default=0.999)
    ap.add_argument("--max-tail-response-reduction", type=float, default=0.25)
    ap.add_argument("--max-guard-reduction", type=float, default=0.35)
    ap.add_argument("--workers", type=int, default=64)
    ap.add_argument("--profile", default="pinpoint", choices=["weighted", "nlift1536", "nlift2048", "pinpoint"])
    ap.add_argument("--tail-response-factors", default="0.98,0.96,0.94,0.92,0.90,0.88,0.86")
    ap.add_argument("--q-target", type=float, default=1.0)
    ap.add_argument("--old-ledger-tolerance", type=float, default=1.0e-10)
    ap.add_argument("--plan-out", default="artifacts/proof_audit/lower_corridor/phase2aa_stage2a_expand/collar_012b1_phase2aa_stage2a_expand_plan.json")
    ap.add_argument("--export-summary-out", default=None)
    ap.add_argument("--profiled-out", default="artifacts/proof_audit/lower_corridor/phase2aa_stage2a_expand/collar_012b1_phase2aa_stage2a_expand_profiled_guard.json")
    ap.add_argument("--profiled-csv", default="tables/proof_audit/lower_corridor/phase2aa_stage2a_expand/collar_012b1_phase2aa_stage2a_expand_profiled_guard.csv")
    ap.add_argument("--run", action="store_true", help="Actually run export+profiled guard. Omit for plan-only.")
    ap.add_argument("--force", action="store_true", help="Force Stage-1B regeneration of selected candidates.")
    args = ap.parse_args()

    plan = build_expand_plan(
        phase2y_path=args.phase2y,
        max_indices=args.max_indices,
        q_cutoff=args.q_cutoff,
        max_tail_response_reduction=args.max_tail_response_reduction,
        max_guard_reduction=args.max_guard_reduction,
    )
    write_json(args.plan_out, plan)
    print(json.dumps({
        "status": plan.get("status"),
        "selected_count": plan.get("selected_count"),
        "selected_indices_csv": plan.get("selected_indices_csv"),
        "bucket_counts": plan.get("bucket_counts"),
        "recommended_upgrade_counts": plan.get("recommended_upgrade_counts"),
        "plan_out": args.plan_out,
    }, indent=2, sort_keys=True), flush=True)

    if not args.run:
        print("Plan-only mode. Re-run with --run to regenerate payloads and profile guards.")
        return 0
    if not plan.get("selected_indices"):
        print("No selected indices; nothing to run.")
        return 3

    export_summary = args.export_summary_out or f"artifacts/proof_audit/lower_corridor/phase2x_weighted/{args.label}_export/phase2x_{args.label}_export_run_summary.json"
    export_cmd = [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2aa_stage1b_export_pilot.py",
        "--summary", args.summary,
        "--seed-json", args.seed_json,
        "--indices", plan["selected_indices_csv"],
        "--label", f"{args.label}_export",
        "--workers", str(args.workers),
        "--profile", args.profile,
        "--out", export_summary,
    ]
    if args.force:
        export_cmd.append("--force")
    print("$ " + " ".join(export_cmd), flush=True)
    proc = subprocess.run(export_cmd, cwd=str(REPO), text=True)
    if proc.returncode not in (0, 2):
        return int(proc.returncode)

    profiled_cmd = [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2aa_profiled_guard.py",
        "--summary", export_summary,
        "--root", ".",
        "--q-target", str(args.q_target),
        "--old-ledger-tolerance", str(args.old_ledger_tolerance),
        "--tail-response-factors", args.tail_response_factors,
        "--out", args.profiled_out,
        "--csv", args.profiled_csv,
    ]
    print("$ " + " ".join(profiled_cmd), flush=True)
    proc2 = subprocess.run(profiled_cmd, cwd=str(REPO), text=True)
    if proc2.returncode != 0:
        return int(proc2.returncode)

    print(json.dumps({
        "status": "phase2aa-stage2a-expand-run-complete",
        "plan_out": args.plan_out,
        "export_summary": export_summary,
        "profiled_out": args.profiled_out,
        "profiled_csv": args.profiled_csv,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
