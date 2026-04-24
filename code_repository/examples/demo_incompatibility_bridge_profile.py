from __future__ import annotations

import os
import sys

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kam_theorem_suite.incompatibility_bridge_profile import (
    build_golden_incompatibility_bridge_profile_certificate,
)


def main() -> None:
    cert = build_golden_incompatibility_bridge_profile_certificate(
        n_terms=3,
        keep_last=2,
        min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        crossing_max_depth=4,
        crossing_min_width=5.0e-4,
        band_initial_subdivisions=1,
        band_max_depth=2,
        band_min_width=1.0e-3,
        min_tail_members=2,
    ).to_dict()
    print('theorem_status:', cert['theorem_status'])
    print('selected_profile_name:', cert['selected_profile_name'])
    print('selected_bridge_status:', cert['selected_bridge'].get('theorem_status'))
    print('viable_profile_names:', cert['viable_profile_names'])


if __name__ == '__main__':
    main()
