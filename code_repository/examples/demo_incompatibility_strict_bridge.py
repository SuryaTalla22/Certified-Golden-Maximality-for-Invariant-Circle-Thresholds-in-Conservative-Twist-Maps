from __future__ import annotations

import json
import os
import sys

if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kam_theorem_suite.incompatibility_strict_bridge import (
    build_golden_incompatibility_strict_bridge_certificate,
)


def main() -> None:
    cert = build_golden_incompatibility_strict_bridge_certificate(
        n_terms=3,
        keep_last=2,
        min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        crossing_max_depth=4,
        crossing_min_width=5e-4,
        band_initial_subdivisions=1,
        band_max_depth=2,
        band_min_width=1e-3,
        min_cluster_size=2,
        min_tail_members=1,
        min_support_fraction=0.75,
        min_entry_coverage=0.75,
    )
    print(json.dumps(cert.to_dict(), indent=2))


if __name__ == '__main__':
    main()
