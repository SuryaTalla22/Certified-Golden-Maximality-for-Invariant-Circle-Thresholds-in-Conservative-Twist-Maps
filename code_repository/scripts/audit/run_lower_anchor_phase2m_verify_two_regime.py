#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2m_two_regime import verify_collar, assemble_two_regime_certificate


def main() -> int:
    p = argparse.ArgumentParser(description="Verify collar coverage and assemble the Phase-2M two-regime lower certificate.")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()
    collar = verify_collar(root=args.repo_root)
    cert = assemble_two_regime_certificate(root=args.repo_root)
    print(json.dumps({
        "collar_theorem_facing": collar.get("theorem_facing"),
        "collar_covered_interval": collar.get("covered_interval"),
        "collar_failure_fields": collar.get("failure_fields"),
        "two_regime_theorem_facing": cert.get("theorem_facing"),
        "two_regime_covered_interval": cert.get("covered_interval"),
        "final_anchor_reached": cert.get("final_anchor_reached"),
        "failure_fields": cert.get("failure_fields"),
        "two_regime_output": "artifacts/proof_audit/lower_corridor/lower_two_regime_certificate.json",
    }, indent=2, sort_keys=True))
    if args.strict and not cert.get("theorem_facing"):
        return 4
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
