#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2g_refinement import (
    build_phase2g_refinement_plan,
    load_json,
    write_phase2g_refinement_outputs,
)


def _parse_ints(raw: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in raw.split(",") if x.strip())


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except Exception:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase-2G adaptive refinement planner for failed Phase-2E/2F lower-anchor candidates."
    )
    parser.add_argument("--candidate", required=True, help="Merged or chunk lower-anchor candidate JSON to diagnose.")
    parser.add_argument("--plan", default=None, help="Optional full-grid plan JSON used to propose missing final-anchor segments.")
    parser.add_argument("--final-anchor", nargs=2, type=float, default=[0.9716350, 0.9716360], metavar=("LO", "HI"))
    parser.add_argument("--subdivisions", type=int, default=2)
    parser.add_argument("--near-critical-subdivisions", type=int, default=4)
    parser.add_argument("--overlap", type=float, default=1.0e-7)
    parser.add_argument("--N-values", default="64,96,128,192,256,384,512")
    parser.add_argument("--oversample-factor", type=int, default=16)
    parser.add_argument("--sigma-cap", type=float, default=0.02)
    parser.add_argument("--tolerance", type=float, default=1.0e-12)
    parser.add_argument("--out-json", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2g_refinement_plan.json")
    parser.add_argument("--out-csv", default="tables/proof_audit/lower_corridor/lower_anchor_phase2g_refinement_segments.csv")
    parser.add_argument("--out-shell", default="scripts/audit/run_phase2g_refinement_segments.sh")
    parser.add_argument("--refinement-out-dir", default="artifacts/proof_audit/lower_corridor/phase2g_refinements")
    parser.add_argument("--refinement-table-dir", default="tables/proof_audit/lower_corridor/phase2g_refinements")
    parser.add_argument("--strict", action="store_true", help="Return nonzero if no actionable refinement segment is produced.")
    args = parser.parse_args(argv)

    candidate_path = ROOT / args.candidate if not Path(args.candidate).is_absolute() else Path(args.candidate)
    plan_path = None if args.plan is None else (ROOT / args.plan if not Path(args.plan).is_absolute() else Path(args.plan))
    candidate = load_json(candidate_path)
    plan = None if plan_path is None or not plan_path.exists() else load_json(plan_path)
    ref_plan = build_phase2g_refinement_plan(
        candidate,
        candidate_path=_rel(candidate_path),
        plan=plan,
        plan_path=None if plan_path is None else _rel(plan_path),
        final_anchor=args.final_anchor,
        subdivisions=args.subdivisions,
        near_critical_subdivisions=args.near_critical_subdivisions,
        overlap=args.overlap,
        n_values=_parse_ints(args.N_values),
        oversample_factor=args.oversample_factor,
        sigma_cap=args.sigma_cap,
        tolerance=args.tolerance,
    )
    summary = write_phase2g_refinement_outputs(
        ref_plan,
        out_json=ROOT / args.out_json if not Path(args.out_json).is_absolute() else Path(args.out_json),
        out_csv=ROOT / args.out_csv if args.out_csv and not Path(args.out_csv).is_absolute() else args.out_csv,
        out_shell=ROOT / args.out_shell if args.out_shell and not Path(args.out_shell).is_absolute() else args.out_shell,
        repo_root=ROOT,
        out_dir=args.refinement_out_dir,
        table_dir=args.refinement_table_dir,
    )
    payload = {
        "schema": "phase2g_lower_anchor_refinement_cli_summary_v1",
        "candidate": _rel(candidate_path),
        "plan": None if plan_path is None else _rel(plan_path),
        "first_blocker": ref_plan.first_blocker,
        "failure_fields": list(ref_plan.failure_fields),
        "actionable": ref_plan.actionable,
        "refinement_segment_count": len(ref_plan.refinement_segments),
        **{k: (_rel(Path(v)) if isinstance(v, str) and k.endswith("_path") else v) for k, v in summary.items()},
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.strict and not ref_plan.actionable:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
