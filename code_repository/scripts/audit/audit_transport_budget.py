#!/usr/bin/env python3
from __future__ import annotations

"""Generate the Phase-4 transport-budget proof-audit artifacts.

This script intentionally does not write a cached Theorem-V theorem artifact.  It
builds a lightweight proof-audit payload from the compact compressed-contract
fields and writes only the derived budget ledger, tables, and figures.
"""

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.proof_bundle_validator import validate_proof_audit_bundle  # noqa: E402
from kam_theorem_suite.audit.transport_budget import (  # noqa: E402
    audit_transport_budget,
    load_transport_input_payload,
    write_transport_budget_audit_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-json",
        default=None,
        help="Optional lightweight transport-input JSON or compact Theorem-V shell. If omitted, use minimal paper replay inputs.",
    )
    parser.add_argument(
        "--stage-cache",
        default="artifacts/final_discharge/stage_cache",
        help="Accepted for protocol symmetry; not used to store or load Theorem V artifacts.",
    )
    parser.add_argument("--artifact-dir", default="artifacts/proof_audit/transport_budget")
    parser.add_argument("--table-dir", default="tables/proof_audit/transport_budget")
    parser.add_argument("--figure-dir", default="figures/proof_audit/transport_budget")
    args = parser.parse_args(argv)

    input_payload = load_transport_input_payload(None if args.input_json is None else ROOT / args.input_json)
    # Record the stage-cache boundary in the source artifact without reading or writing Theorem-V+ caches.
    input_payload.setdefault("stage_cache_boundary", args.stage_cache)
    report = audit_transport_budget(input_payload)

    failures = validate_proof_audit_bundle(report["transport_audit"])
    if failures:
        report = dict(report)
        report["validator_failures"] = [f.to_dict() for f in failures]
        report["status"] = "failed"
    else:
        report = dict(report)
        report["validator_failures"] = []

    outputs = write_transport_budget_audit_outputs(
        report,
        artifact_dir=ROOT / args.artifact_dir,
        table_dir=ROOT / args.table_dir,
        figure_dir=ROOT / args.figure_dir,
    )
    print(json.dumps({"status": report["status"], "outputs": outputs, "validator_failures": report["validator_failures"]}, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
