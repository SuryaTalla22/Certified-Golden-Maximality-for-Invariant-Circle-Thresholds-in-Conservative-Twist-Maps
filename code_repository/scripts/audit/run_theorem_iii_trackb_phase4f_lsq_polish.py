#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from kam_theorem_suite.lower_param.oversampled_lsq_polish import LSQPolishConfig, run_many, write_outputs


def parse_csv_ints(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(',') if x.strip()]


def parse_csv_floats(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(',') if x.strip()]


def parse_cutoffs(s: str) -> list[int | None]:
    out = []
    for x in s.split(','):
        x = x.strip().lower()
        if not x:
            continue
        if x in {'none', 'full', 'null'}:
            out.append(None)
        else:
            out.append(int(x))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description='Track B Phase 4f oversampled least-squares dealiased polish')
    ap.add_argument('--npz', action='append', required=True, help='Input seed .npz. May be repeated.')
    ap.add_argument('--M-outs', required=True, help='Comma-separated output resolutions, e.g. 4096,8192')
    ap.add_argument('--oversamples', default='2', help='Comma-separated oversampling factors')
    ap.add_argument('--cutoff-modes', default='full', help='Comma-separated cutoff modes or full')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--max-newton', type=int, default=8)
    ap.add_argument('--accept-oversampled-linf', type=float, default=1e-10)
    ap.add_argument('--accept-projected-linf', type=float, default=1e-10)
    ap.add_argument('--accept-core-linf', type=float, default=1e-8)
    ap.add_argument('--lsmr-atol', type=float, default=1e-12)
    ap.add_argument('--lsmr-btol', type=float, default=1e-12)
    ap.add_argument('--lsmr-maxiter', type=int, default=1000)
    ap.add_argument('--lsmr-conlim', type=float, default=1e12)
    ap.add_argument('--damping-min', type=float, default=1e-7)
    ap.add_argument('--gauge-index', type=int, default=0)
    ap.add_argument('--gauge-weight', type=float, default=1.0)
    ap.add_argument('--omega-override', type=float, default=None)
    ap.add_argument('--nu', type=float, default=1.003)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        raise SystemExit(f'{out_dir} exists and is nonempty; pass --force to overwrite/add')
    out_dir.mkdir(parents=True, exist_ok=True)

    configs = []
    for npz in args.npz:
        for M in parse_csv_ints(args.M_outs):
            for ov in parse_csv_ints(args.oversamples):
                for cut in parse_cutoffs(args.cutoff_modes):
                    configs.append(LSQPolishConfig(
                        input_npz=npz,
                        M_out=M,
                        oversample=ov,
                        cutoff_mode=cut,
                        max_newton=args.max_newton,
                        accept_oversampled_linf=args.accept_oversampled_linf,
                        accept_projected_linf=args.accept_projected_linf,
                        accept_core_linf=args.accept_core_linf,
                        lsmr_atol=args.lsmr_atol,
                        lsmr_btol=args.lsmr_btol,
                        lsmr_maxiter=args.lsmr_maxiter,
                        lsmr_conlim=args.lsmr_conlim,
                        damping_min=args.damping_min,
                        gauge_index=args.gauge_index,
                        gauge_weight=args.gauge_weight,
                        omega_override=args.omega_override,
                        nu=args.nu,
                    ))
    results = run_many(configs, out_dir, workers=args.workers)
    summary = write_outputs(results, out_dir, parameters={
        'npz_count': len(args.npz),
        'M_outs': parse_csv_ints(args.M_outs),
        'oversamples': parse_csv_ints(args.oversamples),
        'cutoff_modes': args.cutoff_modes,
        'workers_requested': args.workers,
        'workers_used': max(1, min(args.workers, len(configs) or 1)),
        'max_newton': args.max_newton,
        'accept_oversampled_linf': args.accept_oversampled_linf,
        'accept_projected_linf': args.accept_projected_linf,
        'accept_core_linf': args.accept_core_linf,
        'lsmr_atol': args.lsmr_atol,
        'lsmr_btol': args.lsmr_btol,
        'lsmr_maxiter': args.lsmr_maxiter,
        'lsmr_conlim': args.lsmr_conlim,
        'damping_min': args.damping_min,
        'gauge_index': args.gauge_index,
        'gauge_weight': args.gauge_weight,
        'nu': args.nu,
    })
    print(f"Wrote {out_dir / 'phase4f_lsq_polish_summary.json'}")
    print(summary['counts'])


if __name__ == '__main__':
    main()
