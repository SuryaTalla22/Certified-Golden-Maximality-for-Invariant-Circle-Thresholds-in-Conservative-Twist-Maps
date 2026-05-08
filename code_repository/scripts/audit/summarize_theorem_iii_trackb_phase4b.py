#!/usr/bin/env python
from __future__ import annotations

import argparse, json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description='Compact summary for Track B Phase 4b')
    ap.add_argument('summary_json')
    ap.add_argument('--top', type=int, default=40)
    args = ap.parse_args()
    d = json.loads(Path(args.summary_json).read_text(encoding='utf-8'))
    out = {
        'schema': 'theorem_iii_trackb_phase4b_compact_report_v1',
        'status': d.get('status'),
        'counts': d.get('counts'),
        'parameters': d.get('parameters'),
        'interpretation_hints': {
            'diagnostic_only': True,
            'primary_fix_checked': 'Corrects the previous Phase 4 nonperiodic x-shift residual bug by using lift-aware x_target=theta+omega+u(theta+omega).',
            'main_decision': 'If lift-aware embedding residual is tiny but tangent/triangular defect remains ~1e-3 or larger, the next step is high-resolution/dealiased seed refinement, not intervalization.',
        },
        'top_candidates': d.get('ranked_candidates', [])[:args.top],
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
