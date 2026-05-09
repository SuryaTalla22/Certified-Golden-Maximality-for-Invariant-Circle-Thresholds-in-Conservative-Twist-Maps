#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Compact summary for Track B Phase 3 small-divisor/cohomology audit.")
    p.add_argument("summary", help="Path to phase3_small_divisor_summary.json")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--include-records", action="store_true")
    args = p.parse_args()
    data = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    ranked = data.get("ranked_candidates", [])[: args.top]
    out = {
        "schema": "theorem_iii_trackb_phase3_compact_report_v1",
        "status": data.get("status"),
        "counts": data.get("counts"),
        "parameters": data.get("parameters"),
        "top_candidates": ranked,
        "interpretation_hints": {
            "diagnostic_only": True,
            "best_seed_rule": "Prefer final-anchor M=1024 if cohomology correction norm is small at nu=1.003/1.005 and zero-mode residual is tiny.",
            "important_warning": "These are double-precision small-divisor/cohomology diagnostics; Phase 4 must replace them with interval/exact arithmetic and automatic reducibility.",
            "next_phase": "Use the selected seed to implement automatic reducibility and radii-polynomial constants.",
        },
    }
    if args.include_records:
        out["records"] = data.get("records", [])
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
