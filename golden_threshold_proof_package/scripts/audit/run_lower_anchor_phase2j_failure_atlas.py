#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2j_adaptive_rescue import build_and_write_phase2j_plan


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build the Phase-2J lower-anchor failure atlas and rescue scripts.")
    p.add_argument("--candidate", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2i_merged_candidate.json")
    p.add_argument("--strict-report", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2i_strict_ingestion_check.json")
    p.add_argument("--atlas-out", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2j_failure_atlas.json")
    p.add_argument("--csv-out", default="tables/proof_audit/lower_corridor/lower_anchor_phase2j_failure_atlas.csv")
    p.add_argument("--script-out", default="scripts/audit/run_phase2j_rescue_segments.sh")
    p.add_argument("--dry-run-script-out", default="scripts/audit/run_phase2j_rescue_segments_dryrun.sh")
    p.add_argument("--max-variants-per-parent", type=int, default=None)
    p.add_argument("--python-executable", default="python")
    p.add_argument("--no-site", action="store_true", help="Insert -S after the Python executable in generated rescue commands.")
    args = p.parse_args(argv)
    summary = build_and_write_phase2j_plan(
        candidate_path=ROOT / args.candidate if not Path(args.candidate).is_absolute() else Path(args.candidate),
        strict_report_path=ROOT / args.strict_report if args.strict_report and not Path(args.strict_report).is_absolute() else (Path(args.strict_report) if args.strict_report else None),
        atlas_out=ROOT / args.atlas_out if not Path(args.atlas_out).is_absolute() else Path(args.atlas_out),
        csv_out=ROOT / args.csv_out if not Path(args.csv_out).is_absolute() else Path(args.csv_out),
        script_out=ROOT / args.script_out if not Path(args.script_out).is_absolute() else Path(args.script_out),
        dry_run_script_out=ROOT / args.dry_run_script_out if args.dry_run_script_out and not Path(args.dry_run_script_out).is_absolute() else (Path(args.dry_run_script_out) if args.dry_run_script_out else None),
        max_variants_per_parent=args.max_variants_per_parent,
        python_executable=args.python_executable,
        no_site=bool(args.no_site),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
