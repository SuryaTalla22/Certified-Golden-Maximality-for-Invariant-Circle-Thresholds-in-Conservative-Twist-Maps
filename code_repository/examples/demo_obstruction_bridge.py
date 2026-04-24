from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import math

from kam_theorem_suite.proof_driver import build_existence_obstruction_bridge_report

golden = (math.sqrt(5.0) - 1.0) / 2.0
report = build_existence_obstruction_bridge_report(
    rho=golden,
    K_subcritical=0.5,
    K_supercritical_lo=0.969,
    K_supercritical_hi=0.972,
    p=3,
    q=5,
    N=64,
)
print(report["relation"])
print(report["periodic_obstruction"]["regime"], report["periodic_obstruction"]["certified_crossing_side"])
