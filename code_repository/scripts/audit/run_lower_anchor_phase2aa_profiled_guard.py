#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_phase2aa_profiled_guard import (
    run_profiled_guard_audit,
    write_profiled_guard_outputs,
)


def _parse_floats(s: str) -> tuple[float, ...]:
    vals: list[float] = []
    for part in str(s).split(','):
        part = part.strip()
        if part:
            vals.append(float(part))
    return tuple(vals)


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 2AA Stage 2A diagnostic profiled nonlinear/tail guard audit.")
    ap.add_argument('--summary', required=True, help='Stage 1B run summary with candidate paths.')
    ap.add_argument('--candidate', action='append', default=[], help='Additional candidate JSON path; may be repeated.')
    ap.add_argument('--root', default='.', help='Repository root used to resolve relative candidate paths.')
    ap.add_argument('--q-target', type=float, default=1.0, help='q gate for diagnostic closure; use 1.0 for current finite contraction condition.')
    ap.add_argument('--old-ledger-tolerance', type=float, default=1.0e-10)
    ap.add_argument('--tail-response-factors', default='0.98,0.96,0.94,0.92,0.90')
    ap.add_argument('--out', required=True)
    ap.add_argument('--csv', required=True)
    args = ap.parse_args()

    report = run_profiled_guard_audit(
        summary_path=args.summary,
        candidate_paths=args.candidate,
        root=args.root,
        q_target=float(args.q_target),
        old_ledger_tolerance=float(args.old_ledger_tolerance),
        tail_response_factors=_parse_floats(args.tail_response_factors),
    )
    write_profiled_guard_outputs(report, out=args.out, csv_path=args.csv)
    print({
        'status': report.get('status'),
        'record_count': report.get('record_count'),
        'q_safe_count': report.get('q_safe_count'),
        'q_blocked_count': report.get('q_blocked_count'),
        'records_with_any_q_gated_diagnostic_closure': report.get('records_with_any_q_gated_diagnostic_closure'),
        'records_with_any_tail_guard_diagnostic_closure_before_q_gate': report.get('records_with_any_tail_guard_diagnostic_closure_before_q_gate'),
        'out': str(Path(args.out)),
        'csv': str(Path(args.csv)),
    })
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
