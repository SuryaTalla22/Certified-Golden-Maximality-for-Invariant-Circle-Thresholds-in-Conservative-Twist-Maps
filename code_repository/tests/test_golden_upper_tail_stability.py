from kam_theorem_suite.proof_driver import (
    build_golden_upper_tail_stability_report,
    build_golden_two_sided_tail_stability_bridge_report,
)

def _light_kwargs():
    return dict(
        n_terms=3, keep_last=1, min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        crossing_center_offsets=(0.0,),
        initial_subdivisions=1, max_depth=0,
        refine_upper_ladder=False, max_rounds=1,
        support_fraction_threshold=0.5, min_tail_members=1,
        min_cluster_size=1, min_stable_tail_members=1,
    )

def test_golden_upper_tail_stability_report_smoke():
    report = build_golden_upper_tail_stability_report(**_light_kwargs())
    assert report['theorem_status'].startswith('golden-supercritical-tail-stability-')
    assert isinstance(report['entries'], list)
    assert isinstance(report['stable_q_union'], list)

def test_golden_upper_tail_stability_indices_consistent():
    report = build_golden_upper_tail_stability_report(**_light_kwargs())
    n = len(report['entries'])
    assert all(0 <= i < n for i in report['successful_entry_indices'])
    assert all(0 <= i < n for i in report['clustered_entry_indices'])
    if report['stable_tail_qs']:
        assert report['stable_tail_support_count'] >= 1

def test_golden_two_sided_tail_stability_bridge_smoke():
    report = build_golden_two_sided_tail_stability_bridge_report(K_values=(0.45, 0.55, 0.65), **_light_kwargs())
    assert report['theorem_status'].startswith('golden-two-sided-tail-stability-')
    assert 'relation' in report and 'upper_side' in report
