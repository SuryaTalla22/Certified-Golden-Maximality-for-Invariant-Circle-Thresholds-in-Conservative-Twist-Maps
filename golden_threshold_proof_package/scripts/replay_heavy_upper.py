#!/usr/bin/env python3
from __future__ import annotations

"""Phase-7 upper heavy replay/audit boundary.

This script regenerates the Phase-3 upper-obstruction proof-audit payload from
the cached theorem-IV promotion artifact.  It verifies the analytic-incompatibility
margin and writes a replay-level report.  It does not mutate the cached theorem-IV
artifact.
"""

from pathlib import Path
import argparse
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.proof_bundle_validator import validate_proof_audit_bundle  # noqa: E402
from kam_theorem_suite.audit.replay_protocol import write_json  # noqa: E402
from kam_theorem_suite.audit.upper_obstruction_margin import (  # noqa: E402
    DEFAULT_SOURCE_ARTIFACT,
    audit_upper_obstruction_from_promotion,
    load_upper_bridge_promotion,
    write_upper_obstruction_audit_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("verify-existing", "regenerate-heavy", "verify-or-regenerate"), default="verify-or-regenerate")
    parser.add_argument("--promotion", default=DEFAULT_SOURCE_ARTIFACT)
    parser.add_argument("--out-dir", default="artifacts/proof_audit/upper_obstruction")
    parser.add_argument("--table-dir", default="tables/proof_audit/upper_obstruction")
    parser.add_argument("--fig-dir", default="figures/proof_audit/upper_obstruction")
    parser.add_argument("--report", default="artifacts/proof_audit/replay/heavy_upper_report.json")
    args = parser.parse_args(argv)

    started = time.perf_counter()
    bundle_path = ROOT / args.out_dir / "upper_obstruction_audit.bundle.json"
    if args.mode == "verify-existing" and not bundle_path.exists():
        report = {
            "schema": "phase7_heavy_upper_report_v1",
            "status": "missing-existing-audit",
            "mode": args.mode,
            "outputs": {},
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(report, ROOT / args.report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    promotion_path = (ROOT / args.promotion).resolve() if not Path(args.promotion).is_absolute() else Path(args.promotion)
    promotion = load_upper_bridge_promotion(promotion_path)
    audit_report = audit_upper_obstruction_from_promotion(promotion, source_artifact=args.promotion)
    failures = validate_proof_audit_bundle(audit_report["upper_audit"])
    audit_report = dict(audit_report)
    audit_report["validator_failures"] = [f.to_dict() for f in failures]
    if failures:
        audit_report["status"] = "failed"
    outputs = write_upper_obstruction_audit_outputs(
        audit_report,
        artifact_dir=ROOT / args.out_dir,
        table_dir=ROOT / args.table_dir,
        figure_dir=ROOT / args.fig_dir,
    )
    report = {
        "schema": "phase7_heavy_upper_report_v1",
        "status": "passed" if audit_report.get("status") == "passed" else "failed-closed",
        "mode": args.mode,
        "promotion_source": args.promotion,
        "validator_failures": audit_report["validator_failures"],
        "analytic_incompatibility_margin": audit_report.get("analytic_incompatibility_margin"),
        "gap_minus_upper_width": audit_report.get("gap_minus_upper_width"),
        "outputs": outputs,
        "runtime_seconds": time.perf_counter() - started,
    }
    write_json(report, ROOT / args.report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
