from __future__ import annotations

import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import build_refined_rational_upper_ladder_report
from kam_theorem_suite.standard_map import HarmonicFamily


def main() -> None:
    golden = (math.sqrt(5.0) - 1.0) / 2.0
    fam = HarmonicFamily()
    specs = [
        ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
        ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
        ApproximantWindowSpec(8, 13, 0.9710, 0.9725, 1.04, 1.06, label="gold-8/13"),
    ]
    report = build_refined_rational_upper_ladder_report(
        rho=golden,
        specs=specs,
        family=fam,
        initial_subdivisions=2,
        max_depth=2,
    )
    refined = report["refined_upper_ladder"]
    print({
        "status": refined["status"],
        "selected_cluster_member_labels": refined["selected_cluster_member_labels"],
        "best_interval": (
            refined["best_refined_crossing_lower_bound"],
            refined["best_refined_crossing_upper_bound"],
        ),
        "improved_width": refined["refinement_improved_width"],
    })


if __name__ == "__main__":
    main()
