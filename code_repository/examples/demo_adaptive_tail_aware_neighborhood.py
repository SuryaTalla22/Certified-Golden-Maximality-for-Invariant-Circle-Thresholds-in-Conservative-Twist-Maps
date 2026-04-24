from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.proof_driver import build_golden_adaptive_tail_aware_neighborhood_report


if __name__ == '__main__':
    report = build_golden_adaptive_tail_aware_neighborhood_report(
        n_terms=3,
        keep_last=2,
        min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        refinement_radius_factors=(1.5, 1.0, 0.5),
        max_tail_candidates=3,
        min_cluster_size=1,
        min_tail_members=1,
        crossing_max_depth=4,
        crossing_min_width=5e-4,
        band_initial_subdivisions=1,
        band_max_depth=2,
        band_min_width=1e-3,
    )
    print('status:', report['theorem_status'])
    print('selected_source_label:', report['selected_source_label'])
    print('selected_target_tail_qs:', report.get('selected_target_tail_qs'))
    print('selected_bridge_status:', report['selected_bridge'].get('theorem_status'))
    print('selected_tail:', report['selected_bridge'].get('certified_tail_qs'))
