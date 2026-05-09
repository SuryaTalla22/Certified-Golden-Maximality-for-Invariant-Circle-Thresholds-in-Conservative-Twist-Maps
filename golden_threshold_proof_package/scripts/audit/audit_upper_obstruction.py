#!/usr/bin/env python3
from __future__ import annotations

"""Generate the Phase-3 upper-obstruction proof-audit artifacts."""

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.upper_obstruction_margin import (  # noqa: E402
    DEFAULT_SOURCE_ARTIFACT,
    audit_upper_obstruction_from_promotion,
    load_upper_bridge_promotion,
    write_upper_obstruction_audit_outputs,
)
from kam_theorem_suite.audit.proof_bundle_validator import validate_proof_audit_bundle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--promotion",
        default=DEFAULT_SOURCE_ARTIFACT,
        help="Path to theorem_iv_upper_bridge_promotion.json relative to repository root.",
    )
    parser.add_argument("--artifact-dir", default="artifacts/proof_audit/upper_obstruction")
    parser.add_argument("--table-dir", default="tables/proof_audit/upper_obstruction")
    parser.add_argument("--figure-dir", default="figures/proof_audit/upper_obstruction")
    args = parser.parse_args(argv)

    promotion_path = (ROOT / args.promotion).resolve()
    promotion = load_upper_bridge_promotion(promotion_path)
    report = audit_upper_obstruction_from_promotion(promotion, source_artifact=args.promotion)

    failures = validate_proof_audit_bundle(report["upper_audit"])
    if failures:
        report = dict(report)
        report["validator_failures"] = [f.to_dict() for f in failures]
        report["status"] = "failed"
    else:
        report = dict(report)
        report["validator_failures"] = []

    outputs = write_upper_obstruction_audit_outputs(
        report,
        artifact_dir=ROOT / args.artifact_dir,
        table_dir=ROOT / args.table_dir,
        figure_dir=ROOT / args.figure_dir,
    )
    print(json.dumps({"status": report["status"], "outputs": outputs, "validator_failures": report["validator_failures"]}, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
