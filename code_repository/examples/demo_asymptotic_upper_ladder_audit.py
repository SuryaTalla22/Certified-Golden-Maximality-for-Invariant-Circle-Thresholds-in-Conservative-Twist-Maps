from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import build_asymptotic_upper_ladder_audit_report
from kam_theorem_suite.standard_map import HarmonicFamily


def main() -> None:
    golden = (math.sqrt(5.0) - 1.0) / 2.0
    fam = HarmonicFamily()
    specs = [
        ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
        ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
        ApproximantWindowSpec(8, 13, 0.9710, 0.9725, 1.04, 1.06, label="gold-8/13"),
        ApproximantWindowSpec(13, 21, 0.9710, 0.9720, 1.04, 1.06, label="gold-13/21"),
    ]
    report = build_asymptotic_upper_ladder_audit_report(
        rho=golden,
        specs=specs,
        family=fam,
        initial_subdivisions=2,
        max_depth=2,
    )
    out = ROOT / "outputs" / "demo_asymptotic_upper_ladder_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"saved {out}")
    print(report["status"])


if __name__ == "__main__":
    main()
