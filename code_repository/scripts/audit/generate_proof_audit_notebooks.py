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

from kam_theorem_suite.audit.proof_audit_notebooks import write_proof_audit_notebooks, validate_proof_audit_notebook_inventory  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase-9 proof-audit notebooks.")
    parser.add_argument("--notebook-dir", default="notebooks/proof_audit")
    parser.add_argument("--no-overwrite", action="store_true")
    parser.add_argument("--out", default="artifacts/proof_audit/notebooks/phase9_notebook_generation_report.json")
    args = parser.parse_args(argv)
    inventory = write_proof_audit_notebooks(repository_root=ROOT, notebook_dir=args.notebook_dir, overwrite=not args.no_overwrite)
    failures = validate_proof_audit_notebook_inventory(repository_root=ROOT, notebook_dir=args.notebook_dir)
    report = {"schema": "phase9_notebook_generation_report_v1", "status": "passed" if not failures else "failed", "inventory": inventory, "failures": failures}
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
