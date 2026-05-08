#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_regeneration import (
    LowerAnchorRegenerationConfig,
    run_lower_anchor_regeneration,
    write_regeneration_outputs,
)


def _parse_probe_at(raw: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in raw.split(",") if x.strip()) or ("last",)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Phase-2C finite lower-anchor candidate and audit report.")
    parser.add_argument("--start-K", type=float, default=0.265)
    parser.add_argument("--final-anchor", nargs=2, type=float, default=[0.9716350, 0.9716360], metavar=("LO", "HI"))
    parser.add_argument("--segments", type=int, default=10)
    parser.add_argument("--overlap", type=float, default=1.0e-7)
    parser.add_argument("--N", type=int, default=32)
    parser.add_argument("--oversample-factor", type=int, default=2)
    parser.add_argument("--include-analytic-probe", action="store_true", default=True)
    parser.add_argument("--no-analytic-probe", dest="include_analytic_probe", action="store_false")
    parser.add_argument("--analytic-N-values", default="32,64")
    parser.add_argument("--analytic-probe-at", default="last", help="Comma-separated subset of all,first,middle,last")
    parser.add_argument("--sigma-cap", type=float, default=0.02)
    parser.add_argument("--out-dir", default="artifacts/proof_audit/lower_corridor")
    parser.add_argument("--table-dir", default="tables/proof_audit/lower_corridor")
    parser.add_argument("--fig-dir", default="figures/proof_audit/lower_corridor")
    parser.add_argument("--no-figures", action="store_true")
    parser.add_argument("--candidate-name", default="lower_anchor_finite_dimensional_candidate.json")
    parser.add_argument("--strict", action="store_true", help="Return nonzero unless the candidate is theorem-promotable.")
    args = parser.parse_args(argv)

    analytic_N = tuple(int(x.strip()) for x in args.analytic_N_values.split(",") if x.strip())
    cfg = LowerAnchorRegenerationConfig(
        start_K=float(args.start_K),
        final_anchor_lo=float(args.final_anchor[0]),
        final_anchor_hi=float(args.final_anchor[1]),
        n_segments=int(args.segments),
        overlap=float(args.overlap),
        N=int(args.N),
        oversample_factor=int(args.oversample_factor),
        include_analytic_probe=bool(args.include_analytic_probe),
        analytic_probe_N_values=analytic_N,
        analytic_probe_at=_parse_probe_at(args.analytic_probe_at),
        sigma_cap=float(args.sigma_cap),
    )
    report = run_lower_anchor_regeneration(cfg)
    summary = write_regeneration_outputs(
        report,
        out_dir=ROOT / args.out_dir,
        table_dir=ROOT / args.table_dir,
        fig_dir=None if args.no_figures else ROOT / args.fig_dir,
        candidate_name=str(args.candidate_name),
    )
    rel = {}
    for key, value in summary.items():
        if key.endswith("_path") and isinstance(value, str):
            try:
                rel[key] = Path(value).resolve().relative_to(ROOT).as_posix()
            except Exception:
                rel[key] = value
        elif key == "figure_paths":
            vals = []
            for p in value:
                try:
                    vals.append(Path(p).resolve().relative_to(ROOT).as_posix())
                except Exception:
                    vals.append(p)
            rel[key] = vals
        else:
            rel[key] = value
    rel["finite_success_count"] = report.finite_success_count
    rel["theorem_ready_record_count"] = report.theorem_ready_record_count
    rel["min_finite_margin"] = report.min_finite_margin
    rel["min_analytic_margin"] = report.min_analytic_margin
    print(json.dumps(rel, indent=2, sort_keys=True))
    return 2 if args.strict and not report.promotion_allowed else 0


if __name__ == "__main__":
    raise SystemExit(main())
