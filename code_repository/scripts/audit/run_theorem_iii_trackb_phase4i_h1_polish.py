#!/usr/bin/env python
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.phase4i_h1_polish import run_phase4i_h1_polish


def parse_csv_ints(s: str):
    return [int(x) for x in s.split(',') if x.strip()]

def parse_csv_floats(s: str):
    return [float(x) for x in s.split(',') if x.strip()]

def parse_csv_strs(s: str):
    return [x.strip() for x in s.split(',') if x.strip()]


def main():
    ap = argparse.ArgumentParser(description='Track B Phase 4i derivative-weighted H1 polish')
    ap.add_argument('--npz', action='append', required=True, help='Input seed npz; repeatable')
    ap.add_argument('--M-outs', default='4096')
    ap.add_argument('--oversamples', default='2')
    ap.add_argument('--cutoffs', default='full,frac:0.95')
    ap.add_argument('--lambda-h1', default='0.5,1.0,2.0,4.0')
    ap.add_argument('--eta-high', default='0,1e-8')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--max-newton', type=int, default=8)
    ap.add_argument('--accept-scalar-linf', type=float, default=1e-8)
    ap.add_argument('--accept-derivative-linf', type=float, default=5e-5)
    ap.add_argument('--lsmr-atol', type=float, default=1e-12)
    ap.add_argument('--lsmr-btol', type=float, default=1e-12)
    ap.add_argument('--lsmr-maxiter', type=int, default=900)
    ap.add_argument('--lsmr-conlim', type=float, default=1e12)
    ap.add_argument('--damping-min', type=float, default=1e-7)
    ap.add_argument('--nu', type=float, default=1.003)
    ap.add_argument('--omega-override', type=float, default=None)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    run_phase4i_h1_polish(
        npz_paths=args.npz,
        M_outs=parse_csv_ints(args.M_outs),
        oversamples=parse_csv_ints(args.oversamples),
        cutoff_specs=parse_csv_strs(args.cutoffs),
        lambda_h1_values=parse_csv_floats(args.lambda_h1),
        eta_high_values=parse_csv_floats(args.eta_high),
        out_dir=args.out_dir,
        workers=args.workers,
        omega_override=args.omega_override,
        max_newton=args.max_newton,
        lsmr_atol=args.lsmr_atol,
        lsmr_btol=args.lsmr_btol,
        lsmr_maxiter=args.lsmr_maxiter,
        lsmr_conlim=args.lsmr_conlim,
        damping_min=args.damping_min,
        accept_scalar_linf=args.accept_scalar_linf,
        accept_derivative_linf=args.accept_derivative_linf,
        nu=args.nu,
        force=args.force,
    )
    print(f"[phase4i-h1] summary={args.out_dir}/phase4i_h1_polish_summary.json")

if __name__ == '__main__':
    main()
