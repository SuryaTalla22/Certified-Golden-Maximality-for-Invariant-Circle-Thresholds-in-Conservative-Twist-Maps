#!/usr/bin/env python3
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5b_interval_component import (
    _parse_float_list, _parse_int_list, _parse_str_list, run_phase5b_interval_components,
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 5B interval-component audit scaffold for Track B Theorem III")
    ap.add_argument("--npz", action="append", required=True, help="Selected seed .npz; repeatable")
    ap.add_argument("--nu-grid", default="1.001")
    ap.add_argument("--cutoffs", default="full,frac:0.95")
    ap.add_argument("--tail-start-fracs", default="0.75,0.90")
    ap.add_argument("--grid-factors", default="4")
    ap.add_argument("--radii", default="3e-6,1e-5,3e-5")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--rounding-slack", type=float, default=1e-10)
    ap.add_argument("--interval-inflation", type=float, default=0.05)
    ap.add_argument("--q-scale", type=float, default=0.038)
    ap.add_argument("--omega-override", type=float, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    summary = run_phase5b_interval_components(
        npz_paths=args.npz,
        nu_grid=_parse_float_list(args.nu_grid),
        cutoffs=_parse_str_list(args.cutoffs),
        tail_start_fracs=_parse_float_list(args.tail_start_fracs),
        grid_factors=_parse_int_list(args.grid_factors),
        radii=_parse_float_list(args.radii),
        workers=args.workers,
        out_dir=args.out_dir,
        rounding_slack=args.rounding_slack,
        interval_inflation=args.interval_inflation,
        q_scale=args.q_scale,
        omega_override=args.omega_override,
        force=args.force,
    )
    print(f"[phase5b] summary={args.out_dir}/phase5b_interval_component_summary.json")
    print(f"[phase5b] completed={summary['counts'].get('completed_records')} tasks={summary['counts'].get('tasks')}")


if __name__ == "__main__":
    main()
