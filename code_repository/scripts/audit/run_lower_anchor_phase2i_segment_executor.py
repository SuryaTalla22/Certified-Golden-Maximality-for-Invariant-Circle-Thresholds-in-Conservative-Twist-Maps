#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2i_segment_executor import run_phase2i_bounded_execution


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bounded Phase-2I executor for missing lower-anchor segments.")
    p.add_argument("--repo-root", default=str(ROOT))
    p.add_argument("--plan", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_full_grid_plan.json")
    p.add_argument("--lower-dir", default="artifacts/proof_audit/lower_corridor")
    p.add_argument("--refinement-dir", default="artifacts/proof_audit/lower_corridor/phase2g_refinements")
    p.add_argument("--table-dir", default="tables/proof_audit/lower_corridor/phase2g_refinements")
    p.add_argument("--report-out", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2i_bounded_execution_report.json")
    p.add_argument("--refreshed-status-out", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2i_refreshed_phase2h_status.json")
    p.add_argument("--log-dir", default="artifacts/proof_audit/lower_corridor/phase2i_logs")
    p.add_argument("--python-executable", default=sys.executable)
    p.add_argument("--site", action="store_true", help="Do not pass -S to segment subprocesses.")
    p.add_argument("--n-values", default="64,96,128,192,256,384,512")
    p.add_argument("--oversample-factor", type=int, default=16)
    p.add_argument("--sigma-cap", type=float, default=0.02)
    p.add_argument("--segment-timeout-seconds", type=float, default=900.0)
    p.add_argument("--max-segments", type=int, default=None)
    p.add_argument("--include-failed-present", action="store_true")
    p.add_argument("--extra-pythonpath", action="append", default=[])
    args = p.parse_args(argv)
    report = run_phase2i_bounded_execution(
        repo_root=args.repo_root,
        plan_path=args.plan,
        lower_dir=args.lower_dir,
        refinement_dir=args.refinement_dir,
        table_dir=args.table_dir,
        report_path=args.report_out,
        refreshed_status_path=args.refreshed_status_out,
        log_dir=args.log_dir,
        python_executable=args.python_executable,
        no_site=not args.site,
        n_values=args.n_values,
        oversample_factor=args.oversample_factor,
        sigma_cap=args.sigma_cap,
        segment_timeout_seconds=args.segment_timeout_seconds,
        max_segments=args.max_segments,
        include_failed_present=args.include_failed_present,
        extra_pythonpath=args.extra_pythonpath,
    )
    print(json.dumps({
        "schema": report.schema,
        "requested_segment_count": report.requested_segment_count,
        "executed_segment_count": report.executed_segment_count,
        "timeout_count": report.timeout_count,
        "candidate_created_count": report.candidate_created_count,
        "theorem_ready_after_run_count": report.theorem_ready_after_run_count,
        "before_ready_count": report.before_ready_count,
        "after_ready_count": report.after_ready_count,
        "before_missing_count": report.before_missing_count,
        "after_missing_count": report.after_missing_count,
        "before_failed_count": report.before_failed_count,
        "after_failed_count": report.after_failed_count,
        "promotion_allowed_after_run": report.promotion_allowed_after_run,
        "using_mpmath_fallback": report.preflight.using_mpmath_fallback,
        "preflight_error": report.preflight.import_error,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(int(code))
