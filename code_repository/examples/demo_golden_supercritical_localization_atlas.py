from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.proof_driver import (  # noqa: E402
    build_golden_supercritical_localization_atlas_report,
)


def main() -> None:
    atlas = build_golden_supercritical_localization_atlas_report(
        n_terms=3,
        keep_last=1,
        min_q=5,
        crossing_center_offsets=(0.0,),
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=1,
    )
    print({
        "atlas_status": atlas["theorem_status"],
        "successful_entry_count": atlas["successful_entry_count"],
        "clustered_entry_count": atlas["clustered_entry_count"],
        "atlas_upper_source": atlas["atlas_upper_source"],
    })


if __name__ == "__main__":
    main()
