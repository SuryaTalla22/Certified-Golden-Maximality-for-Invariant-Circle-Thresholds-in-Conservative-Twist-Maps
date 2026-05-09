#!/usr/bin/env python
from __future__ import annotations

import argparse

from kam_theorem_suite.lower_param.target_frame_audit import load_npz_list_from_phase3_summary, run_phase4d_target_frame_audit


def _csv_floats(s: str | None):
    if not s:
        return None
    return [float(x) for x in s.split(',') if x.strip()]


def _csv_ints(s: str | None):
    if not s:
        return None
    return [int(x) for x in s.split(',') if x.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description='Track B Phase 4d target-frame automatic-reducibility audit.')
    ap.add_argument('--phase3-summary', default=None)
    ap.add_argument('--selection', default='strong')
    ap.add_argument('--anchors', default=None)
    ap.add_argument('--resolutions', default=None)
    ap.add_argument('--npz', action='append', default=[])
    ap.add_argument('--top', type=int, default=None)
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--oversample-factors', default='1,2,4')
    ap.add_argument('--cutoff-fracs', default='1.0,0.95,0.90,0.75,0.50')
    ap.add_argument('--nu-grid', default='1.002,1.003,1.005')
    ap.add_argument('--tail-start-fracs', default='0.50,0.75,0.90')
    ap.add_argument('--omega-override', type=float, default=None)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    npz_paths = list(args.npz or [])
    if args.phase3_summary:
        npz_paths.extend(load_npz_list_from_phase3_summary(
            args.phase3_summary,
            selection=args.selection,
            anchors=_csv_floats(args.anchors),
            resolutions=_csv_ints(args.resolutions),
            top=args.top,
        ))
    if not npz_paths:
        raise SystemExit('No input npz files selected. Provide --npz or --phase3-summary.')
    summary = run_phase4d_target_frame_audit(
        npz_paths=npz_paths,
        out_dir=args.out_dir,
        workers=args.workers,
        oversample_factors=_csv_ints(args.oversample_factors) or [1, 2, 4],
        cutoff_fracs=_csv_floats(args.cutoff_fracs) or [1.0, 0.95, 0.90, 0.75, 0.50],
        nu_grid=_csv_floats(args.nu_grid) or [1.002, 1.003, 1.005],
        tail_start_fracs=_csv_floats(args.tail_start_fracs) or [0.50, 0.75, 0.90],
        omega_override=args.omega_override,
        force=args.force,
    )
    print(f"wrote {args.out_dir}/phase4d_target_frame_summary.json")
    print(summary['counts'])


if __name__ == '__main__':
    main()
