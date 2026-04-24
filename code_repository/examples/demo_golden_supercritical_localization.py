from __future__ import annotations

from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite import (
    build_golden_supercritical_localization_report,
    build_golden_two_sided_localization_bridge_report,
)


def main() -> None:
    localization = build_golden_supercritical_localization_report(
        n_terms=5,
        keep_last=2,
        min_q=5,
        crossing_center_offsets=(-4.0e-4, 0.0, 4.0e-4),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=2,
    )
    print(json.dumps({
        "status": localization["theorem_status"],
        "rounds": localization["total_round_count"],
        "best_round_status": localization["best_round_status"],
        "localized_upper_lo": localization["localized_upper_lo"],
        "localized_upper_hi": localization["localized_upper_hi"],
    }, indent=2))

    bridge = build_golden_two_sided_localization_bridge_report(
        K_values=[0.3],
        N_values=(24,),
        use_multiresolution=False,
        n_terms=5,
        keep_last=2,
        min_q=5,
        crossing_center_offsets=(-4.0e-4, 0.0, 4.0e-4),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=2,
    )
    print(json.dumps({
        "bridge_status": bridge["theorem_status"],
        "relation": bridge["relation"],
    }, indent=2))


if __name__ == "__main__":
    main()
