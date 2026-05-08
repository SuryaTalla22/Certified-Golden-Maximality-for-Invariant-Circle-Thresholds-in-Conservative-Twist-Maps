#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description='Summarize Track B Phase 4f LSQ polish')
    ap.add_argument('summary_json')
    ap.add_argument('--top', type=int, default=20)
    args = ap.parse_args()
    d = json.loads(Path(args.summary_json).read_text())
    rows = d.get('top_candidates', [])[: args.top]
    compact = {
        'schema': 'theorem_iii_trackb_phase4f_compact_report_v1',
        'status': d.get('status'),
        'diagnostic_only': True,
        'parameters': d.get('parameters', {}),
        'counts': d.get('counts', {}),
        'interpretation_hints': {
            'main_decision': 'If oversampled and core residuals drop below about 1e-10/1e-8 and Phase 4d audit improves, keep the LSQ-polished seed. If projected residual is good but oversampled residual remains large, discard this route.',
            'next_step': 'Audit top output_npz files with Phase 4d target-frame audit.',
        },
        'top_candidates': rows,
    }
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
