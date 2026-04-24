from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import build_rational_upper_ladder_report
from kam_theorem_suite.standard_map import HarmonicFamily

GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0

fam = HarmonicFamily()
specs = [
    ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
    ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
]
report = build_rational_upper_ladder_report(
    rho=GOLDEN,
    specs=specs,
    family=fam,
    initial_subdivisions=2,
    max_depth=2,
)
print(json.dumps({
    "ladder_quality": report["ladder_quality"],
    "successful_crossing_count": report["successful_crossing_count"],
    "successful_band_count": report["successful_band_count"],
    "best_crossing_lower_bound": report["best_crossing_lower_bound"],
}, indent=2))
