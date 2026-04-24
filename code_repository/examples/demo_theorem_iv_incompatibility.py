from pprint import pprint

from kam_theorem_suite.proof_driver import (
    build_golden_irrational_incompatibility_report,
    build_golden_two_sided_incompatibility_bridge_report,
)

if __name__ == "__main__":
    upper = build_golden_irrational_incompatibility_report(
        n_terms=6,
        keep_last=3,
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
    )
    pprint({
        "status": upper["theorem_status"],
        "upper": [upper["selected_upper_lo"], upper["selected_upper_hi"]],
        "barrier": [upper["selected_barrier_lo"], upper["selected_barrier_hi"]],
        "tail_qs": upper["selected_tail_qs"],
    })

    bridge = build_golden_two_sided_incompatibility_bridge_report(
        K_values=(0.45, 0.55, 0.65),
        n_terms=6,
        keep_last=3,
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
    )
    pprint({
        "status": bridge["theorem_status"],
        "gap_to_upper": bridge["relation"]["gap_to_upper"],
        "gap_to_barrier": bridge["relation"]["gap_to_barrier"],
    })
