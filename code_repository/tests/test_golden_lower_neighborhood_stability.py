from kam_theorem_suite.proof_driver import (
    build_golden_lower_neighborhood_stability_report,
    build_golden_two_sided_neighborhood_tail_bridge_report,
)


def _light_upper_kwargs():
    return dict(
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


def test_golden_lower_neighborhood_stability_report_smoke():
    report = build_golden_lower_neighborhood_stability_report(
        base_K_values=(0.2, 0.3, 0.4),
        shift_grid=(-0.01, 0.0, 0.01),
        resolution_sets=((32, 48),),
        sigma_cap=0.02,
        min_cluster_size=1,
    )
    assert report["theorem_status"].startswith("golden-lower-neighborhood-stability-")
    assert isinstance(report["entries"], list)
    assert isinstance(report["distinct_resolution_signatures"], list)


def test_golden_lower_neighborhood_cluster_indices_consistent():
    report = build_golden_lower_neighborhood_stability_report(
        base_K_values=(0.2, 0.3, 0.4),
        shift_grid=(-0.01, 0.0, 0.01),
        resolution_sets=((32, 48),),
        sigma_cap=0.02,
        min_cluster_size=1,
    )
    n = len(report["entries"])
    assert all(0 <= i < n for i in report["successful_entry_indices"])
    assert all(0 <= i < n for i in report["clustered_entry_indices"])
    if report["clustered_entry_indices"]:
        assert report["stable_lower_bound"] is not None


def test_golden_two_sided_neighborhood_tail_bridge_smoke():
    report = build_golden_two_sided_neighborhood_tail_bridge_report(
        base_K_values=(0.2, 0.3, 0.4),
        lower_shift_grid=(-0.01, 0.0, 0.01),
        lower_resolution_sets=((32, 48),),
        sigma_cap=0.02,
        **_light_upper_kwargs(),
    )
    assert report["theorem_status"].startswith("golden-two-sided-neighborhood-tail-")
    assert "relation" in report and "upper_side" in report and "lower_side" in report
