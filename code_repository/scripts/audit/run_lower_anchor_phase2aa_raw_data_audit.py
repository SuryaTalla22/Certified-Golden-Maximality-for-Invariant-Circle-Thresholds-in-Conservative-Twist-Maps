#!/usr/bin/env python
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json

from kam_theorem_suite.audit.lower_anchor_phase2aa_raw_data_audit import (
    audit_candidate,
    atomic_write_json,
    extract_candidate_rows,
    load_json,
    summarize_audits,
    write_csv,
)


def parse_indices(raw: str | None) -> tuple[int, ...]:
    if not raw:
        return ()
    out = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return tuple(sorted(set(out)))


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 2AA-A raw-data availability audit for Theorem III lower-collar candidates.")
    ap.add_argument("--phase2y", action="append", default=[], help="Phase-2Y sensitivity/required-improvement JSON. May be repeated.")
    ap.add_argument("--summary", action="append", default=[], help="Phase-2V/Phase-2X run summary JSON. May be repeated.")
    ap.add_argument("--root", default=".", help="Repository root used to resolve relative candidate paths.")
    ap.add_argument("--target-indices", default="5,133,114,119,142,131,120,15,155,11", help="Comma-separated p-indices to prioritize/audit. Use empty string for all extracted rows.")
    ap.add_argument("--max-rows", type=int, default=64, help="Maximum candidate rows to audit after extraction. Set 0 for no cap.")
    ap.add_argument("--workers", type=int, default=64, help="Concurrent artifact reads/probes.")
    ap.add_argument("--no-deep", action="store_true", help="Disable source-sample residual recomputation probe.")
    ap.add_argument("--out", required=True, help="Output JSON path.")
    ap.add_argument("--csv", required=True, help="Output CSV path.")
    args = ap.parse_args()

    payloads = []
    input_paths = []
    for p in [*args.phase2y, *args.summary]:
        if not p:
            continue
        path = Path(p)
        input_paths.append(str(path))
        if path.exists():
            payloads.append(load_json(path))
        else:
            print(f"[warn] missing input: {path}")
    if not payloads:
        raise SystemExit("No readable --phase2y/--summary JSON inputs were provided.")

    target_indices = parse_indices(args.target_indices)
    max_rows = None if int(args.max_rows) == 0 else int(args.max_rows)
    rows = extract_candidate_rows(*payloads, target_indices=target_indices, max_rows=max_rows)
    print(f"Phase 2AA-A raw-data audit: extracted {len(rows)} candidate rows")
    print(f"target_indices={list(target_indices) if target_indices else 'ALL'}; workers={args.workers}; deep={not args.no_deep}")

    records = []
    workers = max(1, int(args.workers))
    if workers == 1:
        for row in rows:
            records.append(audit_candidate(row, root=args.root, deep=not args.no_deep))
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(audit_candidate, row, root=args.root, deep=not args.no_deep) for row in rows]
            for fut in as_completed(futs):
                rec = fut.result()
                records.append(rec)
                print(
                    f"[audit] p{int(rec.get('index') or -1):04d} exists={rec.get('artifact_exists')} "
                    f"stage1_ready={rec.get('raw_data_stage1_ready')} "
                    f"tail_ready={rec.get('availability_flags',{}).get('enough_for_tail_guard_prototype')} "
                    f"diag_ready={rec.get('availability_flags',{}).get('enough_for_diagonal_scaling_prototype')}"
                )
    records.sort(key=lambda r: (999999 if r.get('index') is None else int(r.get('index')), str(r.get('candidate_path'))))
    summary = summarize_audits(records)
    payload = {
        "schema": "phase2aa_stage1_raw_data_audit_v1",
        "status": summary["status"],
        "inputs": input_paths,
        "parameters": {
            "root": str(args.root),
            "target_indices": list(target_indices),
            "max_rows": max_rows,
            "workers": workers,
            "deep": not args.no_deep,
        },
        "summary": summary,
        "records": records,
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
    }
    atomic_write_json(args.out, payload)
    write_csv(args.csv, records)
    print(json.dumps({"status": payload["status"], **summary, "out": args.out, "csv": args.csv}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
