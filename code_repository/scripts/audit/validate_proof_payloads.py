#!/usr/bin/env python3
from __future__ import annotations

"""Run the Phase-8 hardened validator on proof-audit payloads."""

from pathlib import Path
import argparse
import json
import sys

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.proof_payload_validator import validate_proof_audit_bundle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="artifacts/proof_audit", help="Audit directory or single bundle JSON file.")
    parser.add_argument("--allow-known-lower-gap", action="store_true", help="Allow the current Phase-2 final-anchor gap while still hardening all other fields.")
    parser.add_argument("--out", default="artifacts/proof_audit/replay/phase8_hardened_validator_report.json")
    args = parser.parse_args(argv)

    report = validate_proof_audit_bundle(args.path, allow_known_lower_gap=args.allow_known_lower_gap)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0 if str(report.get("status", "")).startswith("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
