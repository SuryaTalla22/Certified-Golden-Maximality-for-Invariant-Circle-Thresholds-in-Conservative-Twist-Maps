from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import build_two_sided_irrational_threshold_atlas_report
from kam_theorem_suite.standard_map import HarmonicFamily

GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0

fam = HarmonicFamily()
specs = [
    ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
    ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
]
report = build_two_sided_irrational_threshold_atlas_report(
    rho=GOLDEN,
    K_values=[0.5, 0.6, 0.7],
    specs=specs,
    family=fam,
    N_values=(32, 48, 64),
    quality_floor="weak",
    initial_subdivisions=2,
    max_depth=2,
)
print(json.dumps({
    "status": report["relation"]["status"],
    "lower_bound_K": report["relation"]["lower_bound_K"],
    "upper_object_lo": report["relation"]["upper_object_lo"],
    "ladder_quality": report["relation"]["ladder_quality"],
}, indent=2))
