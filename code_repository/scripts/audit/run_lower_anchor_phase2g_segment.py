#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_heavy_certificate import (
    HeavyLowerAnchorConfig,
    run_heavy_lower_anchor_certificate_on_segments,
    write_heavy_lower_anchor_outputs,
)


def _parse_ints(raw: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in raw.split(",") if x.strip())


def _rel(path: str | Path) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except Exception:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one explicit Phase-2G refined lower-anchor segment.")
    parser.add_argument("--segment-id", required=True)
    parser.add_argument("--K-lo", type=float, required=True)
    parser.add_argument("--K-hi", type=float, required=True)
    parser.add_argument("--K-mid", type=float, required=True)
    parser.add_argument("--N-values", default="64,96,128,192,256,384,512")
    parser.add_argument("--oversample-factor", type=int, default=16)
    parser.add_argument("--sigma-cap", type=float, default=0.02)
    parser.add_argument("--max-wall-seconds", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out-dir", default="artifacts/proof_audit/lower_corridor/phase2g_refinements")
    parser.add_argument("--table-dir", default="tables/proof_audit/lower_corridor/phase2g_refinements")
    parser.add_argument("--candidate-name", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    cfg = HeavyLowerAnchorConfig(
        start_K=float(args.K_lo),
        final_anchor_lo=float(args.K_lo),
        final_anchor_hi=float(args.K_hi),
        N_values=_parse_ints(args.N_values),
        oversample_factor=int(args.oversample_factor),
        sigma_cap=float(args.sigma_cap),
        dry_run=bool(args.dry_run),
        max_wall_seconds=args.max_wall_seconds,
    )
    seg = {"segment_id": args.segment_id, "K_lo": args.K_lo, "K_hi": args.K_hi, "K_mid": args.K_mid}
    report = run_heavy_lower_anchor_certificate_on_segments([seg], cfg)
    candidate_name = args.candidate_name or f"{args.segment_id}_candidate.json"
    summary = write_heavy_lower_anchor_outputs(
        report,
        out_dir=ROOT / args.out_dir if not Path(args.out_dir).is_absolute() else Path(args.out_dir),
        table_dir=ROOT / args.table_dir if not Path(args.table_dir).is_absolute() else Path(args.table_dir),
        candidate_name=candidate_name,
    )
    payload = {
        "schema": "phase2g_lower_anchor_refined_segment_cli_summary_v1",
        "segment_id": args.segment_id,
        "candidate_path": _rel(summary["candidate_path"]),
        "report_path": _rel(summary["report_path"]),
        "promotion_allowed": bool(summary.get("promotion_allowed")),
        "failure_fields": list(summary.get("failure_fields", [])),
        "theorem_ready_record_count": report.theorem_ready_record_count,
        "attempted_record_count": report.attempted_record_count,
    }
    os.write(1, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode())
    exit_code = 2 if args.strict and report.theorem_ready_record_count != report.attempted_record_count else 0
    os._exit(int(exit_code))


if __name__ == "__main__":
    main()
    os._exit(0)
