#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_heavy_certificate import (
    HeavyLowerAnchorConfig,
    run_heavy_lower_anchor_certificate,
    write_heavy_lower_anchor_outputs,
)


def _parse_ints(raw: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in raw.split(",") if x.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Phase-2E heavy adaptive lower-anchor analytic Krawczyk candidate.")
    parser.add_argument("--start-K", type=float, default=0.265)
    parser.add_argument("--final-anchor", nargs=2, type=float, default=[0.9716350, 0.9716360], metavar=("LO", "HI"))
    parser.add_argument("--overlap", type=float, default=1.0e-7)
    parser.add_argument("--N-values", default="64,96,128,192")
    parser.add_argument("--oversample-factor", type=int, default=8)
    parser.add_argument("--sigma-cap", type=float, default=0.02)
    parser.add_argument("--refinement-levels", type=int, default=0)
    parser.add_argument("--max-segments", type=int, default=None)
    parser.add_argument("--segment-start", type=int, default=0, help="Zero-based adaptive-grid segment index to start from.")
    parser.add_argument("--segment-stop", type=int, default=None, help="Exclusive adaptive-grid segment index to stop at.")
    parser.add_argument("--max-wall-seconds", type=float, default=None, help="Stop before starting another segment after this wall-time budget.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out-dir", default="artifacts/proof_audit/lower_corridor")
    parser.add_argument("--table-dir", default="tables/proof_audit/lower_corridor")
    parser.add_argument("--candidate-name", default="lower_anchor_heavy_candidate.json")
    parser.add_argument("--disable-phase2e-direct-radii-ledger", action="store_true", help="Use the legacy aggregate Phase-2D terms instead of the Phase-2E modewise radii ledger.")
    parser.add_argument("--phase2e-nonlinear-margin-fraction", type=float, default=0.25)
    parser.add_argument("--strict", action="store_true", help="Return nonzero unless the generated candidate is promotable.")
    args = parser.parse_args(argv)
    cfg = HeavyLowerAnchorConfig(
        start_K=float(args.start_K),
        final_anchor_lo=float(args.final_anchor[0]),
        final_anchor_hi=float(args.final_anchor[1]),
        overlap=float(args.overlap),
        N_values=_parse_ints(args.N_values),
        oversample_factor=int(args.oversample_factor),
        sigma_cap=float(args.sigma_cap),
        refinement_levels=int(args.refinement_levels),
        max_segments=args.max_segments,
        segment_start=args.segment_start,
        segment_stop=args.segment_stop,
        max_wall_seconds=args.max_wall_seconds,
        dry_run=bool(args.dry_run),
        use_phase2e_direct_radii_ledger=not bool(args.disable_phase2e_direct_radii_ledger),
        phase2e_nonlinear_margin_fraction=float(args.phase2e_nonlinear_margin_fraction),
    )
    report = run_heavy_lower_anchor_certificate(cfg)
    summary = write_heavy_lower_anchor_outputs(
        report,
        out_dir=ROOT / args.out_dir,
        table_dir=ROOT / args.table_dir,
        candidate_name=str(args.candidate_name),
    )
    rel = {}
    for key, value in summary.items():
        if isinstance(value, str) and key.endswith("_path"):
            try:
                rel[key] = Path(value).resolve().relative_to(ROOT).as_posix()
            except Exception:
                rel[key] = value
        else:
            rel[key] = value
    rel.update({
        "status": report.status,
        "theorem_ready_record_count": report.theorem_ready_record_count,
        "attempted_record_count": report.attempted_record_count,
        "min_analytic_margin": report.min_analytic_margin,
        "min_phase2b_margin": report.min_phase2b_margin,
    })
    print(json.dumps(rel, indent=2, sort_keys=True))
    return 2 if args.strict and not report.promotion_allowed else 0


if __name__ == "__main__":
    raise SystemExit(main())
