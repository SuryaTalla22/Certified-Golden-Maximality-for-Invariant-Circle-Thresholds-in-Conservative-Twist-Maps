from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kam_theorem_suite.adaptive_tail_coherence import build_golden_adaptive_tail_coherence_certificate


if __name__ == '__main__':
    cert = build_golden_adaptive_tail_coherence_certificate(
        n_terms=3,
        keep_last=2,
        min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        crossing_max_depth=4,
        crossing_min_width=5e-4,
        band_initial_subdivisions=1,
        band_max_depth=2,
        band_min_width=1e-3,
        min_cluster_size=1,
        min_tail_members=1,
        min_q_support_fraction=0.5,
        min_entry_tail_coverage=0.5,
    ).to_dict()
    print('theorem_status:', cert['theorem_status'])
    print('coherence_tail_qs:', cert['coherence_tail_qs'])
    print('coherence_tail_is_suffix_of_generated_union:', cert['coherence_tail_is_suffix_of_generated_union'])
    print('supporting_entry_indices:', cert['supporting_entry_indices'])
    print('stable_upper:', cert['stable_upper_lo'], cert['stable_upper_hi'])
    print('stable_barrier:', cert['stable_barrier_lo'], cert['stable_barrier_hi'])
    print('stable_incompatibility_gap:', cert['stable_incompatibility_gap'])
    print('support_profile:', cert['support_profile'])
