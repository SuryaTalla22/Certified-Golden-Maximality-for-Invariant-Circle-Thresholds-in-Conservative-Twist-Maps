#!/usr/bin/env python
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase4i_spectral_forensics import run_phase4i_forensics


def parse_csv_ints(s: str):
    return [int(x) for x in s.split(',') if x.strip()]

def parse_csv_floats(s: str):
    return [float(x) for x in s.split(',') if x.strip()]


def main():
    ap = argparse.ArgumentParser(description='Track B Phase 4i spectral forensics')
    ap.add_argument('--npz', action='append', required=True, help='Seed npz path; repeatable')
    ap.add_argument('--grid-factors', default='1,2,4')
    ap.add_argument('--nu-grid', default='1.002,1.003,1.005')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--omega-override', type=float, default=None)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    summary = run_phase4i_forensics(
        npz_paths=args.npz,
        grid_factors=parse_csv_ints(args.grid_factors),
        nu_grid=parse_csv_floats(args.nu_grid),
        out_dir=args.out_dir,
        workers=args.workers,
        omega_override=args.omega_override,
        force=args.force,
    )
    print(f"[phase4i-forensics] summary={args.out_dir}/phase4i_forensics_summary.json")

if __name__ == '__main__':
    main()
