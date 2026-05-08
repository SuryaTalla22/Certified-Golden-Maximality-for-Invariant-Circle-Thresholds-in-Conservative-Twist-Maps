#!/usr/bin/env python
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5c_interval_backend import run_phase5c_interval_backend


def csv_floats(s: str):
    return [float(x) for x in s.split(',') if x]

def csv_ints(s: str):
    return [int(x) for x in s.split(',') if x]

def csv_strs(s: str):
    return [x for x in s.split(',') if x]


def main() -> None:
    ap = argparse.ArgumentParser(description='Track B Phase 5C outward-rounded interval-backend scaffold.')
    ap.add_argument('--npz', action='append', required=True, help='Input selected seed .npz. Can be repeated.')
    ap.add_argument('--nu-grid', type=csv_floats, default=[1.001])
    ap.add_argument('--cutoffs', type=csv_strs, default=['frac:0.95'])
    ap.add_argument('--tail-start-fracs', type=csv_floats, default=[0.90])
    ap.add_argument('--grid-factors', type=csv_ints, default=[4])
    ap.add_argument('--radii', type=csv_floats, default=[3e-5])
    ap.add_argument('--interval-inflation', type=float, default=0.15)
    ap.add_argument('--z-inflation', type=float, default=0.15)
    ap.add_argument('--q-inflation', type=float, default=0.15)
    ap.add_argument('--rounding-slack', type=float, default=1e-12)
    ap.add_argument('--small-divisor-slack', type=float, default=1e-15)
    ap.add_argument('--residual-slack', type=float, default=1e-14)
    ap.add_argument('--tail-safety', type=float, default=2.0)
    ap.add_argument('--q-scale', type=float, default=0.038)
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    summary = run_phase5c_interval_backend(
        npz_paths=args.npz,
        nu_grid=args.nu_grid,
        cutoffs=args.cutoffs,
        tail_start_fracs=args.tail_start_fracs,
        grid_factors=args.grid_factors,
        radii=args.radii,
        interval_inflation=args.interval_inflation,
        z_inflation=args.z_inflation,
        q_inflation=args.q_inflation,
        rounding_slack=args.rounding_slack,
        small_divisor_slack=args.small_divisor_slack,
        residual_slack=args.residual_slack,
        tail_safety=args.tail_safety,
        q_scale=args.q_scale,
        workers=args.workers,
        out_dir=args.out_dir,
        force=args.force,
    )
    print(f"[phase5c] summary={args.out_dir}/phase5c_interval_backend_summary.json")
    print(f"[phase5c] backend_ready={summary['counts']['backend_ready_candidate']} / {summary['counts']['completed_records']}")

if __name__ == '__main__':
    main()
