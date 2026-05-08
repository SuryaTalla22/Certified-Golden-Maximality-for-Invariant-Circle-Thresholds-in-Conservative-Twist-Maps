#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import os

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2k_rescue_execution import run_phase2k_controller


def _relativize(payload: dict) -> dict:
    root = ROOT.resolve()
    def conv(x):
        if isinstance(x, dict):
            return {k: conv(v) for k, v in x.items()}
        if isinstance(x, list):
            return [conv(v) for v in x]
        if isinstance(x, str):
            try:
                p = Path(x)
                if p.is_absolute():
                    return p.resolve().relative_to(root).as_posix()
            except Exception:
                return x
        return x
    return conv(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase-2K rescue execution, merge, and strict-ingestion controller.")
    parser.add_argument("--atlas", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2j_failure_atlas.json")
    parser.add_argument("--rescue-dir", default="artifacts/proof_audit/lower_corridor/phase2j_rescue")
    parser.add_argument("--log-dir", default="artifacts/proof_audit/lower_corridor/phase2k_logs")
    parser.add_argument("--merged-candidate", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2k_merged_rescued_candidate.json")
    parser.add_argument("--summary-out", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2k_execution_summary.json")
    parser.add_argument("--lower-bundle", default="artifacts/proof_audit/lower_corridor/lower_corridor_audit.bundle.json")
    parser.add_argument("--strict-ingestion-report", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2k_strict_ingestion_check.json")
    parser.add_argument("--strict-ingestion-bundle", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2k_strict_ingestion_check.bundle.json")
    parser.add_argument("--prefix-candidate", action="append", default=None, help="Candidate containing theorem-ready prefix rows. Can be repeated.")
    parser.add_argument("--execute", action="store_true", help="Actually run rescue subprocesses. Without this, summarize existing candidates only.")
    parser.add_argument("--dry-run", action="store_true", help="Write planned commands/logs but do not execute heavy subprocesses.")
    parser.add_argument("--force", action="store_true", help="Rerun variants even if their candidate file already exists.")
    parser.add_argument("--max-variants", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=None)
    parser.add_argument("--python-executable", default=None)
    parser.add_argument("--no-site", action="store_true", help="Force -S in generated variant commands.")
    parser.add_argument("--site", action="store_true", help="Remove -S from generated variant commands.")
    parser.add_argument("--skip-strict-ingestion", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return nonzero unless merged candidate is promotable and strict ingestion passes.")
    args = parser.parse_args(argv)

    no_site = None
    if args.no_site:
        no_site = True
    if args.site:
        no_site = False
    prefixes = args.prefix_candidate or ["artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_000_candidate.json"]
    summary = run_phase2k_controller(
        atlas_path=ROOT / args.atlas if not Path(args.atlas).is_absolute() else Path(args.atlas),
        repo_root=ROOT,
        rescue_dir=ROOT / args.rescue_dir if not Path(args.rescue_dir).is_absolute() else Path(args.rescue_dir),
        log_dir=ROOT / args.log_dir if not Path(args.log_dir).is_absolute() else Path(args.log_dir),
        merged_candidate_path=ROOT / args.merged_candidate if not Path(args.merged_candidate).is_absolute() else Path(args.merged_candidate),
        summary_out=ROOT / args.summary_out if not Path(args.summary_out).is_absolute() else Path(args.summary_out),
        lower_bundle_path=ROOT / args.lower_bundle if not Path(args.lower_bundle).is_absolute() else Path(args.lower_bundle),
        strict_ingestion_report_path=ROOT / args.strict_ingestion_report if not Path(args.strict_ingestion_report).is_absolute() else Path(args.strict_ingestion_report),
        strict_ingestion_bundle_path=ROOT / args.strict_ingestion_bundle if not Path(args.strict_ingestion_bundle).is_absolute() else Path(args.strict_ingestion_bundle),
        prefix_candidate_paths=[ROOT / p if not Path(p).is_absolute() else Path(p) for p in prefixes],
        execute=bool(args.execute),
        dry_run=bool(args.dry_run),
        force=bool(args.force),
        max_variants=args.max_variants,
        timeout_seconds=args.timeout_seconds,
        python_executable=args.python_executable,
        no_site=no_site,
        strict_ingestion_check=not bool(args.skip_strict_ingestion),
    )
    payload = summary.to_dict()
    compact = {
        "schema": payload["schema"],
        "rescue_variant_count": payload["rescue_variant_count"],
        "execution_attempted_count": payload["execution_attempted_count"],
        "existing_candidate_count": payload["existing_candidate_count"],
        "theorem_ready_rescue_row_count": payload["theorem_ready_rescue_row_count"],
        "successful_parent_count": payload["successful_parent_count"],
        "failed_parent_count": payload["failed_parent_count"],
        "coverage_interval": payload["coverage_interval"],
        "final_anchor_reached": payload["final_anchor_reached"],
        "merged_promotion_allowed": payload["merged_promotion_allowed"],
        "strict_ingestion_passed": payload["strict_ingestion_passed"],
        "failure_fields": payload["failure_fields"],
        "merged_candidate_path": payload["merged_candidate_path"],
        "summary_out": str(ROOT / args.summary_out if not Path(args.summary_out).is_absolute() else Path(args.summary_out)),
    }
    print(json.dumps(_relativize(compact), indent=2, sort_keys=True))
    if args.strict and not (summary.merged_promotion_allowed and summary.strict_ingestion_passed is True and not summary.failure_fields):
        return 2
    return 0


if __name__ == "__main__":
    rc = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(int(rc))
