#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.arithmetic_domain_grammar import load_certified_universe, run_nonvacuous_omitted_tail_study


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostic nonvacuous omitted-tail envelope study")
    parser.add_argument("--certified-universe", default="CERTIFIED_UNIVERSE.json")
    parser.add_argument("--eta-star-lo", type=float, default=0.0)
    parser.add_argument("--eta-star-hi", type=float, default=0.25)
    parser.add_argument("--envelope-safety-margin", type=float, default=1.0e-6)
    parser.add_argument("--out-json", default="artifacts/proof_audit/arithmetic_domain/nonvacuous_omitted_tail_study.json")
    args = parser.parse_args()
    universe = load_certified_universe(args.certified_universe)
    study = run_nonvacuous_omitted_tail_study(
        universe,
        eta_star_interval=(args.eta_star_lo, args.eta_star_hi),
        envelope_safety_margin=args.envelope_safety_margin,
    )
    out = Path(args.out_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(study, indent=2, sort_keys=True))
    print("status:", "passed" if study["certified"] else "failed")
    print("theorem_facing:", study["theorem_facing"])
    print("margin:", study["margin"])
    print("output:", out)
    return 0 if study["certified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
