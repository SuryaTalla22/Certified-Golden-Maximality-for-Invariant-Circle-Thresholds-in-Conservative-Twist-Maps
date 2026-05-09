#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2m_two_regime import diagnose_collar_failures


def main() -> int:
    p = argparse.ArgumentParser(description="Build Phase-2M forensic diagnostics for near-critical collar failures.")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--candidate-glob", default="artifacts/proof_audit/lower_corridor/phase2j_rescue/phase2e_heavy_anchor_segment_00[5-9]*_candidate.json")
    p.add_argument("--json-out", default="artifacts/proof_audit/lower_corridor/phase2m_collar_diagnostics.json")
    p.add_argument("--csv-out", default="tables/proof_audit/lower_corridor/phase2m_segment005_terms.csv")
    p.add_argument("--strict-sigma", action="store_true", help="Exit nonzero if requested sigma was not propagated into the ledger.")
    args = p.parse_args()
    payload = diagnose_collar_failures(root=args.repo_root, candidate_glob=args.candidate_glob, json_out=args.json_out, csv_out=args.csv_out)
    print(json.dumps({
        "json_out": args.json_out,
        "csv_out": args.csv_out,
        "row_count": payload.get("row_count"),
        "ready_row_count": payload.get("ready_row_count"),
        "sigma_mismatch_count": payload.get("sigma_mismatch_count"),
        "dominant_term_counts": payload.get("dominant_term_counts"),
        "failure_reason_counts": payload.get("failure_reason_counts"),
        "failure_fields": payload.get("failure_fields"),
    }, indent=2, sort_keys=True))
    if args.strict_sigma and payload.get("sigma_mismatch_count", 0):
        return 3
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
