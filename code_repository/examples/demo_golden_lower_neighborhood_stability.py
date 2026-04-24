from __future__ import annotations

from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from kam_theorem_suite import (
    build_golden_lower_neighborhood_stability_report,
    build_golden_two_sided_neighborhood_tail_bridge_report,
)


def main() -> None:
    lower = build_golden_lower_neighborhood_stability_report(
        base_K_values=(0.25, 0.35, 0.45),
        shift_grid=(-0.01, 0.0, 0.01),
        resolution_sets=((32, 48),),
        sigma_cap=0.02,
    )
    print("lower-status:", lower["theorem_status"])
    print("stable-lower-bound:", lower["stable_lower_bound"])
    print("cluster-size:", len(lower["clustered_entry_indices"]))

    bridge = build_golden_two_sided_neighborhood_tail_bridge_report(
        base_K_values=(0.25, 0.35, 0.45),
        lower_shift_grid=(-0.01, 0.0, 0.01),
        lower_resolution_sets=((32, 48),),
        sigma_cap=0.02,
        n_terms=3,
        keep_last=1,
        min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        crossing_center_offsets=(0.0,),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=1,
        support_fraction_threshold=0.5,
        min_tail_members=1,
        min_cluster_size=1,
        min_stable_tail_members=1,
    )
    print("bridge-status:", bridge["theorem_status"])
    print("gap-to-upper:", bridge["relation"]["gap_to_upper"])


if __name__ == "__main__":
    main()
