#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from kam_theorem_suite.audit.lower_anchor_phase2x_weighted_finite import (
    AUTOPSY_CSV_FIELDS,
    autopsy_records,
    load_json,
    records_from_summary,
    record_from_candidate,
    row_to_csv_flat,
    summarize_records,
    write_csv,
    write_json,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Phase 2X failure autopsy for lower-anchor microsegment candidates.")
    p.add_argument("--summary", action="append", default=[], help="Phase 2U/2V/2W run summary JSON. May be repeated.")
    p.add_argument("--candidate", action="append", default=[], help="Individual Phase 2P candidate JSON. May be repeated.")
    p.add_argument("--out", required=True, help="Output JSON report path.")
    p.add_argument("--csv", required=True, help="Output CSV table path.")
    p.add_argument("--top-k", type=int, default=25, help="Number of highest-priority failed rows to include in top_failed_rows.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    records = []
    sources = []
    for sp in args.summary:
        src_records = records_from_summary(sp)
        records.extend(src_records)
        sources.append({"kind": "summary", "path": sp, "record_count": len(src_records)})
    for cp in args.candidate:
        try:
            records.append(record_from_candidate(cp, source_kind="candidate_cli"))
            sources.append({"kind": "candidate", "path": cp, "record_count": 1})
        except Exception as e:
            sources.append({"kind": "candidate", "path": cp, "error": str(e), "record_count": 0})
    rows = autopsy_records(records)
    flat = [row_to_csv_flat(r) for r in rows]
    write_csv(args.csv, flat, AUTOPSY_CSV_FIELDS)
    top_failed = [r.to_dict() for r in rows if not r.record.theorem_ready][: args.top_k]
    report = {
        "schema": "phase2x_failure_autopsy_v1",
        "status": "phase2x-autopsy-complete",
        "sources": sources,
        "summary": summarize_records([r.record for r in rows]),
        "bucket_counts": {},
        "top_failed_rows": top_failed,
        "rows": [r.to_dict() for r in rows],
        "csv_path": args.csv,
        "out_path": args.out,
    }
    counts = {}
    for r in rows:
        counts[r.bucket] = counts.get(r.bucket, 0) + 1
    report["bucket_counts"] = counts
    write_json(args.out, report)
    print({
        "status": report["status"],
        "record_count": report["summary"]["record_count"],
        "failed_count": report["summary"]["failed_count"],
        "best_margin": report["summary"].get("best_margin"),
        "bucket_counts": counts,
        "out": args.out,
        "csv": args.csv,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
