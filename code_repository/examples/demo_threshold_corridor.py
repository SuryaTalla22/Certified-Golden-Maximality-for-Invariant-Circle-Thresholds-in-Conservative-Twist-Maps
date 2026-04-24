from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import math

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.threshold_bracketing import build_threshold_corridor_report

def main() -> None:
    fam = HarmonicFamily()
    golden = (math.sqrt(5.0) - 1.0) / 2.0
    rep = build_threshold_corridor_report(
        rho=golden,
        K_values=[0.5, 0.6, 0.7],
        p=3,
        q=5,
        crossing_K_lo=0.9738,
        crossing_K_hi=0.9742,
        family=fam,
        N=64,
    )
    print("status:", rep.status)
    print("lower bound:", rep.lower_bound_K)
    print("rational window:", rep.rational_root_window_lo, rep.rational_root_window_hi)
    print("gap:", rep.lower_vs_rational_gap)

if __name__ == "__main__":
    main()
