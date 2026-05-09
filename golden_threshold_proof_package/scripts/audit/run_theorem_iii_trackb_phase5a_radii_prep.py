#!/usr/bin/env python3
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase5a_radii_prep import run_phase5a_radii_prep


def _split_csv(s: str):
    return [x.strip() for x in str(s).split(',') if x.strip()]


def _floats(s: str):
    return [float(x) for x in _split_csv(s)]


def _ints(s: str):
    return [int(x) for x in _split_csv(s)]


def main() -> None:
    ap = argparse.ArgumentParser(description='Track B Phase 5A radii-prep / intervalization scaffold (diagnostic only).')
    ap.add_argument('--npz', action='append', required=True, help='Input selected seed .npz. Repeatable.')
    ap.add_argument('--nu-grid', default='1.001,1.002,1.003')
    ap.add_argument('--cutoffs', default='full,frac:0.98,frac:0.95,frac:0.90')
    ap.add_argument('--tail-start-fracs', default='0.50,0.75,0.90')
    ap.add_argument('--grid-factors', default='1,2,4')
    ap.add_argument('--radii', default='1e-10,3e-10,1e-9,3e-9,1e-8,3e-8,1e-7,3e-7,1e-6,3e-6,1e-5')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--omega-override', type=float, default=None)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    summary = run_phase5a_radii_prep(
        npz_paths=args.npz,
        nu_grid=_floats(args.nu_grid),
        cutoff_specs=_split_csv(args.cutoffs),
        tail_start_fracs=_floats(args.tail_start_fracs),
        grid_factors=_ints(args.grid_factors),
        radii=_floats(args.radii),
        workers=args.workers,
        omega_override=args.omega_override,
        out_dir=args.out_dir,
        force=args.force,
    )
    print(f"[phase5a] completed={summary['counts']['completed_records']} summary={args.out_dir}/phase5a_radii_prep_summary.json")

if __name__ == '__main__':
    main()
