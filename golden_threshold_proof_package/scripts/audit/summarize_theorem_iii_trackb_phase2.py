#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Compact summary for Track B Phase 2 tail audit.")
    p.add_argument("summary", help="Path to phase2_tail_audit_summary.json")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--include-records", action="store_true")
    args = p.parse_args()
    data = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    ranked = data.get("ranked_candidates", [])[: args.top]
    out = {
        "schema": "theorem_iii_trackb_phase2_compact_report_v1",
        "status": data.get("status"),
        "counts": data.get("counts"),
        "parameters": data.get("parameters"),
        "top_candidates": ranked,
        "interpretation_hints": {
            "best_proof_seed_rule": "Prefer high M, small residual_linf, stable positive decay strip, and conservative nu not too close to 1.",
            "diagnostic_only": True,
            "next_phase": "Use the selected seed(s) to implement small-divisor/cohomology bounds and then automatic reducibility.",
        },
    }
    if args.include_records:
        out["records"] = data.get("records", [])
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
