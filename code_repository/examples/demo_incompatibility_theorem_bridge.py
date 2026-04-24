from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ is None or __package__ == '':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kam_theorem_suite.proof_driver import (
    build_golden_incompatibility_theorem_bridge_report,
    build_golden_two_sided_incompatibility_theorem_bridge_report,
)

if __name__ == '__main__':
    upper = build_golden_incompatibility_theorem_bridge_report(
        n_terms=3, keep_last=2, min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        crossing_max_depth=4, crossing_min_width=5e-4,
        band_initial_subdivisions=1, band_max_depth=2, band_min_width=1e-3,
        min_cluster_size=1, min_tail_members=1,
        min_support_fraction=0.5, min_entry_coverage=0.5,
    )
    bridge = build_golden_two_sided_incompatibility_theorem_bridge_report(
        K_values=[0.96, 0.965, 0.97],
        n_terms=3, keep_last=2, min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        crossing_max_depth=4, crossing_min_width=5e-4,
        band_initial_subdivisions=1, band_max_depth=2, band_min_width=1e-3,
        min_cluster_size=1, min_tail_members=1,
        min_support_fraction=0.5, min_entry_coverage=0.5,
    )
    print(json.dumps({
        'upper_status': upper['theorem_status'],
        'bridge_margin': upper['bridge_margin'],
        'missing_hypotheses': upper['missing_hypotheses'],
        'two_sided_status': bridge['theorem_status'],
        'gap_to_upper': bridge['relation']['gap_to_upper'],
    }, indent=2))
