#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kam_theorem_suite.lower_param.dealiased_polish import run_phase4e_dealiased_polish


def _csv_ints(s: str | None):
    if not s:
        return []
    return [int(x) for x in s.split(',') if x.strip()]


def _npz_from_compact_report(path: str | None, *, label_contains: str | None = None, top: int | None = None):
    if not path:
        return []
    d = json.loads(Path(path).read_text())
    out = []
    for row in d.get('top_candidates', []):
        if label_contains and label_contains not in str(row.get('recommendation_label', '')):
            continue
        p = row.get('npz_path') or row.get('output_npz')
        if p:
            out.append(p)
        if top is not None and len(out) >= int(top):
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description='Track B Phase 4e dealiased Newton seed polish.')
    ap.add_argument('--npz', action='append', default=[])
    ap.add_argument('--from-compact-report', default=None, help='Optional Phase 4d compact report; uses npz_path rows from top_candidates.')
    ap.add_argument('--label-contains', default=None)
    ap.add_argument('--top', type=int, default=None)
    ap.add_argument('--M-outs', required=True)
    ap.add_argument('--oversample', type=int, default=4)
    ap.add_argument('--cutoff-mode', type=int, default=None)
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--max-newton', type=int, default=16)
    ap.add_argument('--newton-tol', type=float, default=1e-12)
    ap.add_argument('--accept-projected-linf', type=float, default=1e-10)
    ap.add_argument('--accept-core-linf', type=float, default=1e-8)
    ap.add_argument('--gmres-rtol', type=float, default=1e-12)
    ap.add_argument('--gmres-atol', type=float, default=1e-14)
    ap.add_argument('--gmres-restart', type=int, default=220)
    ap.add_argument('--gmres-maxiter', type=int, default=2200)
    ap.add_argument('--damping-min', type=float, default=1e-6)
    ap.add_argument('--nu', type=float, default=1.003)
    ap.add_argument('--omega-override', type=float, default=None)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    npz_paths = list(args.npz or [])
    npz_paths.extend(_npz_from_compact_report(args.from_compact_report, label_contains=args.label_contains, top=args.top))
    if not npz_paths:
        raise SystemExit('No npz inputs selected. Use --npz or --from-compact-report.')
    summary = run_phase4e_dealiased_polish(
        npz_paths=npz_paths,
        M_outs=_csv_ints(args.M_outs),
        out_dir=args.out_dir,
        workers=args.workers,
        oversample=args.oversample,
        cutoff_mode=args.cutoff_mode,
        max_newton=args.max_newton,
        newton_tol=args.newton_tol,
        accept_projected_linf=args.accept_projected_linf,
        accept_core_linf=args.accept_core_linf,
        gmres_rtol=args.gmres_rtol,
        gmres_atol=args.gmres_atol,
        gmres_restart=args.gmres_restart,
        gmres_maxiter=args.gmres_maxiter,
        damping_min=args.damping_min,
        nu=args.nu,
        omega_override=args.omega_override,
        force=args.force,
    )
    print(f"wrote {args.out_dir}/phase4e_dealiased_polish_summary.json")
    print(summary['counts'])


if __name__ == '__main__':
    main()
