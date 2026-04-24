from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kam_theorem_suite.nonexistence_front import build_golden_nonexistence_front_certificate


if __name__ == '__main__':
    cert = build_golden_nonexistence_front_certificate(
        base_K_values=[0.30, 0.45, 0.60],
        lower_shift_grid=(0.0,),
        lower_resolution_sets=((64, 96, 128),),
        lower_min_cluster_size=1,
        n_terms=3,
        keep_last=2,
        min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        crossing_max_depth=4,
        crossing_min_width=5.0e-4,
        band_initial_subdivisions=1,
        band_max_depth=2,
        band_min_width=1.0e-3,
        min_cluster_size=1,
        min_tail_members=1,
        min_support_fraction=0.5,
        min_entry_coverage=0.5,
    ).to_dict()
    print('status:', cert['theorem_status'])
    print('gap_to_upper:', cert['relation'].get('gap_to_upper'))
    print('computational_front_margin:', cert.get('computational_front_margin'))
    print('missing_hypotheses:', cert.get('missing_hypotheses'))
    print('remaining_analytic_lifts:', [row['name'] for row in cert.get('remaining_analytic_lifts', [])])
