from kam_theorem_suite.proof_driver import (
    build_golden_upper_support_audit_report,
    build_golden_two_sided_support_audit_bridge_report,
)


def _light_kwargs():
    return dict(
        n_terms=3,
        keep_last=1,
        min_q=5,
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        crossing_center_offsets=(0.0,),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=1,
        support_fraction_threshold=0.5,
        min_tail_members=1,
    )


def test_golden_upper_support_audit_report_smoke():
    report = build_golden_upper_support_audit_report(**_light_kwargs())
    assert report["theorem_status"].startswith("golden-supercritical-support-audit-")
    assert "atlas_summary" in report
    assert isinstance(report["witnesses"], list)
    assert isinstance(report["robust_qs"], list)


def test_golden_upper_support_audit_has_vote_dicts():
    report = build_golden_upper_support_audit_report(**_light_kwargs())
    assert isinstance(report["support_vote_counts"], dict)
    assert isinstance(report["band_vote_counts"], dict)
    if report["witness_count"] > 0:
        assert report["tail_support_min_votes"] >= 1


def test_golden_two_sided_support_audit_bridge_smoke():
    report = build_golden_two_sided_support_audit_bridge_report(
        K_values=(0.45, 0.55, 0.65),
        **_light_kwargs(),
    )
    assert report["theorem_status"].startswith("golden-two-sided-support-audit-")
    assert "relation" in report
    assert "upper_side" in report
