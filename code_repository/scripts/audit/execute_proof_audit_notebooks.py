#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.proof_audit_notebooks import execute_proof_audit_notebooks, validate_proof_audit_notebook_inventory  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute Phase-9 proof-audit notebooks as lightweight CI preflight.")
    parser.add_argument("--notebook-dir", default="notebooks/proof_audit")
    parser.add_argument("--out", default="artifacts/proof_audit/notebooks/phase9_notebook_execution_report.json")
    args = parser.parse_args(argv)
    inventory_failures = validate_proof_audit_notebook_inventory(repository_root=ROOT, notebook_dir=args.notebook_dir)
    if inventory_failures:
        report = {"schema": "phase9_proof_audit_notebook_execution_v1", "status": "failed", "inventory_failures": inventory_failures}
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": report.get("status"), "inventory_failure_count": len(inventory_failures)}, indent=2, sort_keys=True))
        return 2
    report = execute_proof_audit_notebooks(repository_root=ROOT, notebook_dir=args.notebook_dir, out_path=args.out)
    print(json.dumps({"status": report.get("status"), "notebook_count": report.get("notebook_count"), "failed_count": report.get("failed_count"), "report": args.out}, indent=2, sort_keys=True))
    return 0 if report.get("status") == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
