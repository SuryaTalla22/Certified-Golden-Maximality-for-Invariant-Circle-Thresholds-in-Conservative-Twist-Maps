#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from kam_theorem_suite.lower_param.seed_refinement import run_refinement
from kam_theorem_suite.lower_param.lift_alias_audit import load_npz_list_from_phase3_summary


def parse_floats(s: str): return tuple(float(x) for x in s.split(',') if x.strip())
def parse_ints(s: str): return tuple(int(x) for x in s.split(',') if x.strip())


def main() -> None:
    ap=argparse.ArgumentParser(description='Track B Phase 4c: refine a high-resolution seed from an existing Phase 1 embedding')
    ap.add_argument('--phase3-summary', required=False)
    ap.add_argument('--selection', default='strong', choices=['strong','all'])
    ap.add_argument('--anchors', default=None)
    ap.add_argument('--resolutions', default=None)
    ap.add_argument('--seed-npz', action='append', default=None)
    ap.add_argument('--M-outs', required=True)
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--max-newton', type=int, default=24)
    ap.add_argument('--gmres-rtol', type=float, default=1e-12)
    ap.add_argument('--gmres-atol', type=float, default=1e-14)
    ap.add_argument('--gmres-restart', type=int, default=180)
    ap.add_argument('--gmres-maxiter', type=int, default=1600)
    ap.add_argument('--newton-tol', type=float, default=1e-12)
    ap.add_argument('--accept-linf', type=float, default=1e-10)
    ap.add_argument('--damping-min', type=float, default=1e-5)
    ap.add_argument('--nu', type=float, default=1.003)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--force', action='store_true')
    args=ap.parse_args()
    if args.seed_npz:
        seeds=[str(Path(p)) for p in args.seed_npz]
    else:
        if not args.phase3_summary:
            raise SystemExit('Either --seed-npz or --phase3-summary is required')
        seeds=load_npz_list_from_phase3_summary(args.phase3_summary, selection=args.selection, anchors=parse_floats(args.anchors) if args.anchors else None, resolutions=parse_ints(args.resolutions) if args.resolutions else None)
    print(f'[phase4c] seeds={len(seeds)} M_outs={args.M_outs}')
    summary=run_refinement(seed_npzs=seeds, M_outs=parse_ints(args.M_outs), out_dir=args.out_dir, workers=args.workers, force=args.force, max_newton=args.max_newton, gmres_rtol=args.gmres_rtol, gmres_atol=args.gmres_atol, gmres_restart=args.gmres_restart, gmres_maxiter=args.gmres_maxiter, newton_tol=args.newton_tol, accept_linf=args.accept_linf, damping_min=args.damping_min, nu=args.nu)
    print(f"[phase4c] status={summary['status']} counts={summary['counts']}")
    print(f"[phase4c] summary={Path(args.out_dir)/'phase4c_refinement_summary.json'}")

if __name__=='__main__': main()
