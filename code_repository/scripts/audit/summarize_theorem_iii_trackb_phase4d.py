#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description='Summarize Track B Phase 4d target-frame audit.')
    ap.add_argument('summary_json')
    ap.add_argument('--top', type=int, default=40)
    args = ap.parse_args()
    data = json.loads(Path(args.summary_json).read_text(encoding='utf-8'))
    rows = data.get('ranked_candidates') or data.get('top_candidates') or []
    compact = {
        'schema': 'theorem_iii_trackb_phase4d_compact_report_v1',
        'status': data.get('status'),
        'counts': data.get('counts'),
        'parameters': data.get('parameters'),
        'interpretation_hints': data.get('interpretation_hints'),
        'top_candidates': rows[:args.top],
    }
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
