#!/usr/bin/env python
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description='Summarize Track B Phase 5C interval-backend output.')
    ap.add_argument('summary_json')
    ap.add_argument('--top', type=int, default=20)
    args = ap.parse_args()
    with open(args.summary_json, 'r', encoding='utf-8') as f:
        s = json.load(f)
    out = {
        'schema': 'theorem_iii_trackb_phase5c_compact_report_v1',
        'status': s.get('status'),
        'diagnostic_only': s.get('diagnostic_only', True),
        'theorem_facing': s.get('theorem_facing', False),
        'promotion_allowed': s.get('promotion_allowed', False),
        'important_warning': s.get('important_warning'),
        'parameters': s.get('parameters', {}),
        'counts': s.get('counts', {}),
        'top_candidates': s.get('top_candidates', [])[:args.top],
        'interpretation_hints': {
            'green_light': 'If backend_ready candidates retain positive lower margin under conservative z/q inflation, proceed to Phase 5D certificate assembly scaffold.',
            'watch_Z': 'Z_interval_upper is the dominant risk; target is comfortably below 0.5.',
            'watch_margin': 'radii_relative_margin_interval_lower above 0.25 leaves room for a formal interval implementation.'
        }
    }
    print(json.dumps(out, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
