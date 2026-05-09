#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from kam_theorem_suite.lower_param.lift_alias_audit import load_npz_list_from_phase3_summary, run_phase4b_lift_alias_audit


def parse_floats(s: str):
    return tuple(float(x) for x in s.split(',') if x.strip())


def parse_ints(s: str):
    return tuple(int(x) for x in s.split(',') if x.strip())


def main() -> None:
    ap = argparse.ArgumentParser(description='Track B Phase 4b lift-aware residual / aliasing audit')
    ap.add_argument('--phase3-summary', required=True)
    ap.add_argument('--selection', default='strong', choices=['strong','all'])
    ap.add_argument('--anchors', default=None)
    ap.add_argument('--resolutions', default=None)
    ap.add_argument('--top', type=int, default=None)
    ap.add_argument('--npz', action='append', default=None, help='Explicit npz path; may be repeated. If supplied, phase3 filtering is skipped.')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--oversample-factors', default='1,2,4')
    ap.add_argument('--cutoff-fracs', default='1.0,0.90,0.75,0.50')
    ap.add_argument('--nu-grid', default='1.002,1.003,1.005')
    ap.add_argument('--tail-start-fracs', default='0.50,0.75,0.90')
    ap.add_argument('--omega-override', type=float, default=None)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    if args.npz:
        npz_paths = [str(Path(p)) for p in args.npz]
    else:
        npz_paths = load_npz_list_from_phase3_summary(
            args.phase3_summary,
            selection=args.selection,
            anchors=parse_floats(args.anchors) if args.anchors else None,
            resolutions=parse_ints(args.resolutions) if args.resolutions else None,
            top=args.top,
        )
    print(f'[phase4b] auditing {len(npz_paths)} npz file(s)')
    summary = run_phase4b_lift_alias_audit(
        npz_paths=npz_paths,
        out_dir=args.out_dir,
        workers=args.workers,
        oversample_factors=parse_ints(args.oversample_factors),
        cutoff_fracs=parse_floats(args.cutoff_fracs),
        nu_grid=parse_floats(args.nu_grid),
        tail_start_fracs=parse_floats(args.tail_start_fracs),
        omega_override=args.omega_override,
        force=args.force,
    )
    print(f"[phase4b] status={summary['status']} counts={summary['counts']}")
    print(f"[phase4b] summary={Path(args.out_dir) / 'phase4b_lift_alias_summary.json'}")


if __name__ == '__main__':
    main()
