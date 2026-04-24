from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.theorem_v_transport_lift import (
    build_golden_theorem_v_transport_lift_certificate,
)


if __name__ == "__main__":
    cert = build_golden_theorem_v_transport_lift_certificate(
        base_K_values=[0.965, 0.968, 0.971],
        lower_shift_grid=(-0.01, 0.0, 0.01),
        lower_resolution_sets=((48, 64), (64, 80)),
        sigma_cap=0.05,
        n_terms=8,
        keep_last=5,
        min_q=5,
        max_q=21,
        initial_subdivisions=3,
        max_depth=3,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        atlas_center_offsets=(-8.0e-4, 0.0, 8.0e-4),
        crossing_center_offsets=(-4.0e-4, 0.0, 4.0e-4),
        min_tail_members=1,
        min_stable_tail_members=1,
        asymptotic_min_members=1,
        limit_min_members=2,
        branch_limit_min_members=2,
        nested_limit_min_members=2,
        convergent_min_chain_length=3,
        transport_min_chain_length=3,
        pairwise_min_chain_length=3,
        triple_min_chain_length=3,
        global_potential_min_chain_length=3,
        tail_cauchy_min_chain_length=3,
    ).to_dict()

    print("Theorem V transport lift status:", cert["theorem_status"])
    print("Open front hypotheses:", cert["open_hypotheses"])
    print("Active assumptions:", cert["active_assumptions"])
    pprint(cert["notes"])
