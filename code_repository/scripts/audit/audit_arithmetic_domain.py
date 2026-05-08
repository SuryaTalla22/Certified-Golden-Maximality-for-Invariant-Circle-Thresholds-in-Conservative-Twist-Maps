#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.arithmetic_domain_grammar import (
    build_default_theorem_vii_support,
    build_domain_exhaustion_audit,
    load_certified_universe,
    save_domain_audit_outputs,
)
from kam_theorem_suite.audit.proof_bundle_validator import validate_proof_audit_bundle


def _load_optional_json(path: str | None) -> dict | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"support JSON not found: {p}")
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"support JSON must be an object: {p}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase-5 arithmetic-domain grammar audit")
    parser.add_argument("--certified-universe", default="CERTIFIED_UNIVERSE.json")
    parser.add_argument("--theorem-vii-support-json", default=None, help="optional lightweight support payload; no V-or-above artifact is required")
    parser.add_argument("--stage-cache", default="artifacts/final_discharge/stage_cache", help="accepted for CLI compatibility; not used by the lightweight domain audit")
    parser.add_argument("--out-json", default="artifacts/proof_audit/arithmetic_domain/arithmetic_domain_audit.json")
    parser.add_argument("--out-bundle-json", default="artifacts/proof_audit/arithmetic_domain/arithmetic_domain_audit.bundle.json")
    parser.add_argument("--out-csv", default="tables/proof_audit/arithmetic_domain/arithmetic_domain_records.csv")
    parser.add_argument("--out-counts-csv", default="tables/proof_audit/arithmetic_domain/domain_grammar_counts.csv")
    parser.add_argument("--out-tex", default="tables/proof_audit/arithmetic_domain/arithmetic_domain_records.tex")
    parser.add_argument("--out-counts-tex", default="tables/proof_audit/arithmetic_domain/domain_grammar_counts.tex")
    parser.add_argument("--fig-dir", default="figures/proof_audit/arithmetic_domain")
    args = parser.parse_args()

    universe = load_certified_universe(args.certified_universe)
    support = _load_optional_json(args.theorem_vii_support_json) or build_default_theorem_vii_support(universe)
    report = build_domain_exhaustion_audit(universe, support)
    outputs = save_domain_audit_outputs(
        report,
        out_json=args.out_json,
        out_bundle_json=args.out_bundle_json,
        records_csv=args.out_csv,
        counts_csv=args.out_counts_csv,
        records_tex=args.out_tex,
        counts_tex=args.out_counts_tex,
        fig_dir=args.fig_dir,
    )
    failures = validate_proof_audit_bundle(report["domain_audit"])
    print("status:", report["status"])
    print("route_counts:", report["route_counts"])
    print("omitted_tail_status:", report["omitted_tail_status"])
    print("validator_failures:", [f.to_dict() for f in failures])
    print("outputs:", outputs)
    return 0 if report["status"] == "passed" and not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
