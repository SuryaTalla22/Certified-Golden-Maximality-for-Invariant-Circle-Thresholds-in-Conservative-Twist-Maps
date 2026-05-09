#!/usr/bin/env python3
from __future__ import annotations

"""Run the Phase-6 GL(2,Z) normalization proof audit."""

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.gl2z_normalization_audit import (  # noqa: E402
    build_gl2z_normalization_audit,
    load_certified_universe,
    write_gl2z_audit_outputs,
)
from kam_theorem_suite.audit.proof_bundle_validator import validate_proof_audit_bundle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certified-universe", default=str(ROOT / "CERTIFIED_UNIVERSE.json"))
    parser.add_argument("--bound", type=int, default=3)
    parser.add_argument("--out-dir", default=str(ROOT / "artifacts/proof_audit/gl2z_normalization"))
    parser.add_argument("--table-dir", default=str(ROOT / "tables/proof_audit/gl2z_normalization"))
    parser.add_argument("--fig-dir", default=str(ROOT / "figures/proof_audit/gl2z_normalization"))
    parser.add_argument("--strict", action="store_true", help="exit nonzero if the audit bundle does not validate")
    parser.add_argument("--no-figures", action="store_true", help="skip optional GL(2,Z) PDF figure generation")
    args = parser.parse_args(argv)

    universe = load_certified_universe(args.certified_universe)
    report = build_gl2z_normalization_audit(universe, bound=args.bound)
    failures = validate_proof_audit_bundle(report["gl2z_audit"])
    report["validator_failures"] = [f.to_dict() for f in failures]
    if failures:
        report["status"] = "failed"
        if "proof_audit_validator_failed" not in report["failure_fields"]:
            report["failure_fields"].append("proof_audit_validator_failed")

    if args.no_figures:
        import kam_theorem_suite.audit.gl2z_normalization_audit as _gl2z_mod
        _gl2z_mod._write_figures = lambda report, fig_dir: None
    outputs = write_gl2z_audit_outputs(report, args.out_dir, args.table_dir, args.fig_dir)
    result = {
        "status": report["status"],
        "certified": report["certified"] and not failures,
        "validator_failure_count": len(failures),
        "failure_fields": report["failure_fields"],
        "outputs": outputs,
        "candidate_count": report["candidate_count"],
        "accepted_distinct_representative_count": report["accepted_distinct_representative_count"],
        "analytic_conjugacy_claimed": report["analytic_conjugacy_claimed"],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if args.strict and (report["status"] != "passed" or failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
