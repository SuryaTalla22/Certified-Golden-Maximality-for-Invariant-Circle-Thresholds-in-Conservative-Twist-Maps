#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_heavy_certificate import HeavyLowerAnchorConfig
from kam_theorem_suite.audit.lower_anchor_phase2e_full_grid import (
    check_phase2b_strict_ingestion,
    run_phase2e_chunk,
    write_merged_phase2e_anchor_candidate,
    write_phase2e_full_grid_plan,
)


def _parse_ints(raw: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in raw.split(",") if x.strip())


def _relativize(summary: dict) -> dict:
    out = {}
    for k, v in summary.items():
        if isinstance(v, str) and (k.endswith("_path") or k in {"out_path", "candidate_path"}):
            try:
                out[k] = Path(v).resolve().relative_to(ROOT).as_posix()
            except Exception:
                out[k] = v
        else:
            out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase-2F full-grid/chunk orchestration for the Phase-2E lower-anchor analytic certificate."
    )
    parser.add_argument("--start-K", type=float, default=0.265)
    parser.add_argument("--final-anchor", nargs=2, type=float, default=[0.9716350, 0.9716360], metavar=("LO", "HI"))
    parser.add_argument("--overlap", type=float, default=1.0e-7)
    parser.add_argument("--N-values", default="64,96,128,192")
    parser.add_argument("--oversample-factor", type=int, default=8)
    parser.add_argument("--sigma-cap", type=float, default=0.02)
    parser.add_argument("--segment-start", type=int, default=0)
    parser.add_argument("--segment-stop", type=int, default=None)
    parser.add_argument("--max-segments", type=int, default=None)
    parser.add_argument("--max-wall-seconds", type=float, default=None)
    parser.add_argument("--chunk-index", type=int, default=None, help="Optional chunk index used only in default output naming.")
    parser.add_argument("--chunk-size", type=int, default=None, help="Set segment-start/stop from chunk-index and chunk-size.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--merge-candidates", nargs="*", default=None, help="Merge these chunk candidate JSON files instead of running a new chunk.")
    parser.add_argument("--check-strict-ingestion", action="store_true", help="After merge/run, attempt strict Phase-2B ingestion.")
    parser.add_argument("--lower-bundle", default="artifacts/proof_audit/lower_corridor/lower_corridor_audit.bundle.json")
    parser.add_argument("--out-dir", default="artifacts/proof_audit/lower_corridor")
    parser.add_argument("--table-dir", default="tables/proof_audit/lower_corridor")
    parser.add_argument("--candidate-name", default=None)
    parser.add_argument("--merged-candidate-name", default="lower_anchor_phase2f_merged_candidate.json")
    parser.add_argument("--plan-name", default="lower_anchor_phase2f_full_grid_plan.json")
    parser.add_argument("--strict", action="store_true", help="Return nonzero unless the output is promotable/strict-ingestion-ready.")
    args = parser.parse_args(argv)

    if args.chunk_index is not None and args.chunk_size is not None:
        args.segment_start = int(args.chunk_index) * int(args.chunk_size)
        args.segment_stop = args.segment_start + int(args.chunk_size)

    out_dir = ROOT / args.out_dir
    table_dir = ROOT / args.table_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    base_cfg = HeavyLowerAnchorConfig(
        start_K=float(args.start_K),
        final_anchor_lo=float(args.final_anchor[0]),
        final_anchor_hi=float(args.final_anchor[1]),
        overlap=float(args.overlap),
        N_values=_parse_ints(args.N_values),
        oversample_factor=int(args.oversample_factor),
        sigma_cap=float(args.sigma_cap),
        segment_start=int(args.segment_start),
        segment_stop=args.segment_stop,
        max_segments=args.max_segments,
        max_wall_seconds=args.max_wall_seconds,
        dry_run=bool(args.dry_run),
    )

    plan_path = write_phase2e_full_grid_plan(out_dir / args.plan_name, base_cfg)
    if args.plan_only:
        summary = {"schema": "phase2f_lower_anchor_full_grid_cli_summary_v1", "mode": "plan-only", "plan_path": str(plan_path)}
        print(json.dumps(_relativize(summary), indent=2, sort_keys=True))
        return 0

    if args.merge_candidates is not None and len(args.merge_candidates) > 0:
        merged_path = out_dir / args.merged_candidate_name
        merged = write_merged_phase2e_anchor_candidate(
            [ROOT / p if not Path(p).is_absolute() else Path(p) for p in args.merge_candidates],
            out_path=merged_path,
            final_anchor=args.final_anchor,
        )
        summary = {
            "schema": "phase2f_lower_anchor_full_grid_cli_summary_v1",
            "mode": "merge",
            "plan_path": str(plan_path),
            "candidate_path": str(merged_path),
            "promotion_allowed": bool(merged.get("promotion_allowed")),
            "theorem_facing": bool(merged.get("theorem_facing")),
            "diagnostic_only": bool(merged.get("diagnostic_only")),
            "failure_fields": list(merged.get("failure_fields", [])),
        }
    else:
        if args.candidate_name is None:
            if args.chunk_index is not None:
                candidate_name = f"lower_anchor_phase2f_chunk_{int(args.chunk_index):03d}_candidate.json"
            else:
                candidate_name = "lower_anchor_phase2f_chunk_candidate.json"
        else:
            candidate_name = args.candidate_name
        summary = run_phase2e_chunk(
            config=base_cfg,
            out_dir=out_dir,
            table_dir=table_dir,
            candidate_name=candidate_name,
        )
        summary["schema"] = "phase2f_lower_anchor_full_grid_cli_summary_v1"
        summary["mode"] = "chunk"
        summary["plan_path"] = str(plan_path)

    if args.check_strict_ingestion:
        candidate_path = Path(summary.get("candidate_path") or summary.get("candidate_path", ""))
        if not candidate_path:
            candidate_path = out_dir / args.merged_candidate_name
        if not candidate_path.is_absolute():
            candidate_path = ROOT / candidate_path
        ingestion = check_phase2b_strict_ingestion(
            lower_bundle_path=ROOT / args.lower_bundle if not Path(args.lower_bundle).is_absolute() else Path(args.lower_bundle),
            candidate_path=candidate_path,
            out_json=out_dir / "lower_anchor_phase2f_strict_ingestion_check.json",
            out_bundle=out_dir / "lower_anchor_phase2f_strict_ingestion_check.bundle.json",
            out_csv=table_dir / "lower_anchor_phase2f_strict_ingestion_segments.csv",
            out_tex=table_dir / "lower_anchor_phase2f_strict_ingestion_segments.tex",
            final_anchor=args.final_anchor,
        )
        summary["strict_ingestion_report"] = "artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_strict_ingestion_check.json"
        summary["strict_ingestion_passed"] = bool(ingestion.get("strict_ingestion_passed", False))
    else:
        summary.setdefault("strict_ingestion_passed", False)

    print(json.dumps(_relativize(summary), indent=2, sort_keys=True))
    if args.strict:
        if not bool(summary.get("promotion_allowed")):
            return 2
        if args.check_strict_ingestion and not bool(summary.get("strict_ingestion_passed")):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
