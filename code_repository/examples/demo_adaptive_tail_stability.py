from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.adaptive_tail_stability import build_golden_adaptive_tail_stability_certificate


def main() -> None:
    cert = build_golden_adaptive_tail_stability_certificate(
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
        min_stable_tail_members=1,
    ).to_dict()
    print('status:', cert['theorem_status'])
    print('stable upper:', cert['stable_upper_lo'], cert['stable_upper_hi'])
    print('stable barrier:', cert['stable_barrier_lo'], cert['stable_barrier_hi'])
    print('stable tail qs:', cert['stable_tail_qs'])


if __name__ == '__main__':
    main()
