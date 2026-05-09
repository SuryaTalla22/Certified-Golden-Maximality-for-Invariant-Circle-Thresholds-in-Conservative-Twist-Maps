#!/usr/bin/env python3
from __future__ import annotations

"""Run a lightweight diagnostic study of transport-budget margin amplification.

The study is not theorem-facing heavy regeneration.  It consumes the Phase-4
budget ledger, applies transparent component-reduction scenarios, and writes a
CSV/JSON/PDF summary to guide later expensive computations.
"""

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.transport_budget import (  # noqa: E402
    audit_transport_budget,
    build_transport_budget_ledger,
    load_transport_input_payload,
    run_margin_amplification_study,
    write_margin_amplification_outputs,
)


def _ledger_from_audit_json(path: Path):
    data = json.loads(path.read_text())
    if "ledger" in data:
        # Rebuild from the source input rather than trusting the stored ledger as theorem evidence.
        audit = data.get("transport_audit", {})
        shell = audit.get("shell_payload", {}) if isinstance(audit, dict) else {}
        target = shell.get("target_interval", {}) if isinstance(shell, dict) else {}
        budget = shell.get("uniform_majorant", {}).get("budget", {}) if isinstance(shell.get("uniform_majorant", {}), dict) else {}
        input_payload = {
            "source_artifact": "diagnostic-margin-study-from-transport-budget-audit",
            "target_interval": [target.get("lo", data.get("target_interval", [0.971635, 0.971637])[0]), target.get("hi", data.get("target_interval", [0.971635, 0.971637])[1])],
            "target_width": target.get("width", data.get("target_width")),
            "available_gap": budget.get("available_gap", data.get("available_gap")),
            "branch_label": data.get("ledger", {}).get("branch_label", "golden-native-tail"),
            "chart_label": data.get("ledger", {}).get("chart_label", "standard-sine-threshold-chart"),
            "raw_shell_consumed": False,
        }
        return build_transport_budget_ledger(input_payload)
    return build_transport_budget_ledger(load_transport_input_payload(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-json", default="artifacts/proof_audit/transport_budget/transport_budget_audit.json")
    parser.add_argument("--artifact-dir", default="artifacts/proof_audit/transport_budget")
    parser.add_argument("--table-dir", default="tables/proof_audit/transport_budget")
    parser.add_argument("--figure-dir", default="figures/proof_audit/transport_budget")
    args = parser.parse_args(argv)

    audit_path = ROOT / args.audit_json
    if audit_path.exists():
        ledger = _ledger_from_audit_json(audit_path)
    else:
        # Make the baseline audit in memory if the script is run before the audit script.
        report = audit_transport_budget(load_transport_input_payload(None))
        ledger = build_transport_budget_ledger(report.get("ledger", {})) if False else build_transport_budget_ledger(load_transport_input_payload(None))
    study = run_margin_amplification_study(ledger)
    outputs = write_margin_amplification_outputs(
        study,
        artifact_dir=ROOT / args.artifact_dir,
        table_dir=ROOT / args.table_dir,
        figure_dir=ROOT / args.figure_dir,
    )
    print(json.dumps({"status": "passed", "best_strategy": study["best_strategy"], "outputs": outputs}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
