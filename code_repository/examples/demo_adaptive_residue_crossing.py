from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.proof_driver import build_adaptive_residue_crossing_report
from kam_theorem_suite.standard_map import HarmonicFamily

if __name__ == "__main__":
    fam = HarmonicFamily()
    rep = build_adaptive_residue_crossing_report(
        3,
        5,
        0.95,
        0.99,
        fam,
        max_depth=5,
        min_width=5e-4,
    )
    pprint({
        "status": rep["status"],
        "analyzed_windows": rep["analyzed_windows"],
        "best_window": rep["best_window"],
    })
