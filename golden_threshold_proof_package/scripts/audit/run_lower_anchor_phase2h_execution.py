#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2h_execution import (
    build_phase2h_execution_status,
    candidate_paths_for_merge,
    write_phase2h_missing_segment_script,
    write_phase2h_status,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Phase-2H inventory/merge controller for lower-anchor completion.")
    p.add_argument("--plan", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_full_grid_plan.json")
    p.add_argument("--lower-dir", default="artifacts/proof_audit/lower_corridor")
    p.add_argument("--refinement-dir", default="artifacts/proof_audit/lower_corridor/phase2g_refinements")
    p.add_argument("--status-out", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2h_execution_status.json")
    p.add_argument("--script-out", default="scripts/audit/run_phase2h_missing_segments.sh")
    p.add_argument("--merge-list-out", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2h_merge_inputs.json")
    p.add_argument("--merged-candidate", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2h_merged_candidate.json")
    p.add_argument("--strict-ingestion-report", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2h_strict_ingestion_check.json")
    p.add_argument("--n-values", default="64,96,128,192,256,384,512")
    p.add_argument("--oversample-factor", type=int, default=16)
    p.add_argument("--sigma-cap", type=float, default=0.02)
    p.add_argument("--write-run-script", action="store_true")
    p.add_argument("--list-merge-inputs", action="store_true")
    p.add_argument("--strict", action="store_true", help="Return nonzero unless promotion is currently allowed.")
    args = p.parse_args(argv)

    status = build_phase2h_execution_status(
        plan_path=ROOT / args.plan if not Path(args.plan).is_absolute() else Path(args.plan),
        lower_dir=ROOT / args.lower_dir if not Path(args.lower_dir).is_absolute() else Path(args.lower_dir),
        refinement_dir=ROOT / args.refinement_dir if not Path(args.refinement_dir).is_absolute() else Path(args.refinement_dir),
        merged_candidate_path=ROOT / args.merged_candidate if not Path(args.merged_candidate).is_absolute() else Path(args.merged_candidate),
        strict_ingestion_report_path=ROOT / args.strict_ingestion_report if not Path(args.strict_ingestion_report).is_absolute() else Path(args.strict_ingestion_report),
    )
    write_phase2h_status(status, ROOT / args.status_out if not Path(args.status_out).is_absolute() else Path(args.status_out))
    if args.write_run_script:
        write_phase2h_missing_segment_script(
            status=status,
            out_path=ROOT / args.script_out if not Path(args.script_out).is_absolute() else Path(args.script_out),
            out_dir=args.refinement_dir,
            n_values=args.n_values,
            oversample_factor=args.oversample_factor,
            sigma_cap=args.sigma_cap,
        )
    merge_inputs = candidate_paths_for_merge(
        status=status,
        lower_dir=ROOT / args.lower_dir if not Path(args.lower_dir).is_absolute() else Path(args.lower_dir),
        refinement_dir=ROOT / args.refinement_dir if not Path(args.refinement_dir).is_absolute() else Path(args.refinement_dir),
    )
    merge_inputs_for_json = []
    for item in merge_inputs:
        ip = Path(item)
        try:
            merge_inputs_for_json.append(ip.resolve().relative_to(ROOT).as_posix())
        except Exception:
            merge_inputs_for_json.append(str(item))
    if args.list_merge_inputs:
        out = ROOT / args.merge_list_out if not Path(args.merge_list_out).is_absolute() else Path(args.merge_list_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"schema": "phase2h_merge_input_list_v1", "candidate_paths": merge_inputs_for_json}, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "schema": status.schema,
        "ready_segment_count": status.ready_segment_count,
        "missing_segment_count": status.missing_segment_count,
        "failed_segment_count": status.failed_segment_count,
        "final_anchor_reached_by_available_segments": status.final_anchor_reached_by_available_segments,
        "strict_ingestion_passed": status.strict_ingestion_passed,
        "promotion_allowed": status.promotion_allowed,
        "failure_fields": list(status.failure_fields),
        "merge_input_count": len(merge_inputs),
        "merge_inputs": merge_inputs_for_json,
    }, indent=2, sort_keys=True))
    return 2 if args.strict and not status.promotion_allowed else 0


if __name__ == "__main__":
    raise SystemExit(main())
