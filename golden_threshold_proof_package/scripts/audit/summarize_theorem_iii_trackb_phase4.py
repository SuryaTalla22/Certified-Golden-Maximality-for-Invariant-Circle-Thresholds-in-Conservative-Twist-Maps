#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Compact summary for Track B Phase 4 automatic-reducibility/radii-proxy audit.")
    p.add_argument("summary", help="Path to phase4_auto_reducibility_summary.json")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--include-records", action="store_true")
    args = p.parse_args()
    data = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    ranked = data.get("ranked_candidates", [])[: args.top]
    out = {
        "schema": "theorem_iii_trackb_phase4_compact_report_v1",
        "status": data.get("status"),
        "counts": data.get("counts"),
        "parameters": data.get("parameters"),
        "top_candidates": ranked,
        "interpretation_hints": {
            "diagnostic_only": True,
            "best_seed_rule": "Prefer final-anchor M=1024 if embedding residual, triangular defect, frame determinant defect, and twist nonzero diagnostics are strong.",
            "important_warning": "These are double-precision automatic-reducibility diagnostics and radii proxies, not theorem-facing proof constants.",
            "next_phase": "Intervalize Fourier arithmetic, exactify small divisors, and build the theorem-facing radii-polynomial certificate for the selected final-anchor seed.",
        },
    }
    if args.include_records:
        out["records"] = data.get("records", [])
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
