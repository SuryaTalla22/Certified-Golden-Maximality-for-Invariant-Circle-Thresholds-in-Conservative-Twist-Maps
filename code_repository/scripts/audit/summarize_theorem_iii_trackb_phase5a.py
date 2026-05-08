#!/usr/bin/env python3
from __future__ import annotations
import argparse, json


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('summary_json')
    ap.add_argument('--top', type=int, default=30)
    args = ap.parse_args()
    with open(args.summary_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data = dict(data)
    data['top_candidates'] = data.get('top_candidates', [])[:args.top]
    print(json.dumps(data, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
