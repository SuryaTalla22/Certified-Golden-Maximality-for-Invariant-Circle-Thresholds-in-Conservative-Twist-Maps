from __future__ import annotations

from kam_theorem_suite.class_campaigns import ArithmeticClassSpec
from kam_theorem_suite.class_exhaustion_screen import (
    _select_best_upper_object,
    build_near_top_threat_set_partition_certificate,
    promote_omitted_class_global_control_certificate,
    promote_screened_panel_global_completeness_certificate,
)
from kam_theorem_suite.proof_driver import build_class_exhaustion_screen_report


def test_upper_object_priority_prefers_asymptotic_then_refined_then_raw():
    raw = {"best_crossing_lower_bound": 0.97, "best_crossing_upper_bound": 0.98}
    refined = {
        "best_refined_crossing_lower_bound": 0.971,
        "best_refined_crossing_upper_bound": 0.972,
        "best_refined_crossing_width": 0.001,
    }
    audit = {"audited_upper_lo": 0.9712, "audited_upper_hi": 0.9716, "audited_upper_width": 0.0004}
    src, lo, hi, width = _select_best_upper_object(raw, refined, audit)
    assert src == "asymptotic-upper-ladder"
    assert lo == 0.9712 and hi == 0.9716 and width == 0.0004

    src2, *_ = _select_best_upper_object(raw, refined, {})
    assert src2 == "refined-upper-ladder"

    src3, *_ = _select_best_upper_object(raw, {}, {})
    assert src3 == "raw-upper-ladder"


def test_class_exhaustion_screen_report_smoke():
    specs = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label="silver"),
        ArithmeticClassSpec(preperiod=(), period=(3,), label="bronze"),
    ]
    rep = build_class_exhaustion_screen_report(
        specs,
        reference_crossing_center=0.9713,
        reference_lower_bound=0.9711,
        max_q=30,
        keep_last=2,
        q_min=2,
        initial_subdivisions=2,
        max_depth=2,
        min_width=1e-3,
    )
    assert rep["reference_label"] == "golden"
    assert len(rep["classes"]) == 2
    assert rep["status"] in {
        "all-screened-classes-dominated",
        "screen-has-overlapping-challengers",
        "screen-has-undecided-challengers",
        "screen-is-arithmetic-heavy",
        "partial-class-exhaustion-screen",
    }
    assert rep["dominated_count"] + rep["overlapping_count"] + rep["arithmetic_only_count"] + rep["undecided_count"] == 2
    assert {c["selected_upper_source"] for c in rep["classes"]} <= {
        "asymptotic-upper-ladder",
        "refined-upper-ladder",
        "raw-upper-ladder",
        "no-upper-object",
    }


def test_class_exhaustion_screen_exposes_theorem_facing_certificates():
    specs = [ArithmeticClassSpec(preperiod=(), period=(2,), label="silver")]
    rep = build_class_exhaustion_screen_report(
        specs,
        reference_crossing_center=0.9713,
        reference_lower_bound=0.9711,
        max_q=20,
        keep_last=2,
        q_min=2,
        initial_subdivisions=2,
        max_depth=1,
        min_width=1e-3,
    )
    assert 'arithmetic_ranking_certificate' in rep
    assert 'pruning_region_certificate' in rep
    assert 'screened_panel_global_completeness_certificate' in rep
    assert rep['arithmetic_ranking_certificate']['covers_screened_panel'] is True
    assert rep['screened_panel_global_completeness_certificate']['status'] in {
        'screened-panel-global-completeness-frontier',
        'screened-panel-global-completeness-certified',
    }



def test_near_top_threat_set_partition_certificate_can_certify_complete_partition():
    partition = build_near_top_threat_set_partition_certificate(
        screened_panel_certificate={
            'screened_panel_labels': ['silver'],
            'panel_has_no_overlaps': True,
            'panel_has_no_undecided': True,
            'theorem_level_complete_records': [
                {
                    'class_label': 'silver',
                    'completion_source': 'screen theorem',
                    'completion_reason': 'screened class certified complete',
                    'certificate_name': 'screened_panel_global_completeness_certificate',
                }
            ],
        },
        arithmetic_ranking_certificate={
            'theorem_level_ranked_labels': ['silver', 'bronze'],
            'proves_exact_near_top_lagrange_spectrum_ranking': True,
        },
        pruning_region_certificate={
            'theorem_level_dominated_labels': ['bronze'],
            'proves_theorem_level_pruning_of_dominated_regions': True,
        },
        termination_exclusion_promotion_certificate={
            'candidate_labels': [],
            'promoted_labels': [],
            'proves_termination_search_promotes_to_theorem_exclusion': True,
        },
    )
    assert partition['status'] == 'near-top-threat-set-partition-certified'
    assert partition['partition_complete'] is True
    assert partition['covered_by_theorem_level_screen'] == ['silver']
    assert partition['dominated_outside_screen'] == ['bronze']
    assert partition['uncovered_labels'] == []



def test_promoted_screened_panel_certificate_uses_partition_certificate():
    cert = promote_screened_panel_global_completeness_certificate(
        screened_panel_certificate={
            'screened_panel_labels': ['silver'],
            'panel_has_no_overlaps': True,
            'panel_has_no_undecided': True,
            'theorem_level_complete_records': [
                {
                    'class_label': 'silver',
                    'completion_source': 'screen theorem',
                    'completion_reason': 'screened class certified complete',
                    'certificate_name': 'screened_panel_global_completeness_certificate',
                }
            ],
        },
        arithmetic_ranking_certificate={
            'theorem_level_ranked_labels': ['silver'],
            'proves_exact_near_top_lagrange_spectrum_ranking': True,
        },
        pruning_region_certificate={
            'theorem_level_dominated_labels': [],
            'proves_theorem_level_pruning_of_dominated_regions': True,
        },
        termination_exclusion_promotion_certificate={
            'candidate_labels': [],
            'promoted_labels': [],
            'proves_termination_search_promotes_to_theorem_exclusion': True,
        },
    )
    assert cert['status'] == 'screened-panel-global-completeness-certified'
    assert cert['screened_panel_globally_complete'] is True
    assert cert['near_top_threat_set_partition_certificate']['partition_complete'] is True



def test_promoted_omitted_class_global_control_certificate_uses_partition_and_support_provenance():
    screen = promote_screened_panel_global_completeness_certificate(
        screened_panel_certificate={
            'screened_panel_labels': ['silver'],
            'panel_has_no_overlaps': True,
            'panel_has_no_undecided': True,
            'theorem_level_complete_records': [
                {
                    'class_label': 'silver',
                    'completion_source': 'screen theorem',
                    'completion_reason': 'screened class certified complete',
                    'certificate_name': 'screened_panel_global_completeness_certificate',
                }
            ],
        },
        arithmetic_ranking_certificate={
            'theorem_level_ranked_labels': ['silver', 'bronze', 'nickel'],
            'proves_exact_near_top_lagrange_spectrum_ranking': True,
        },
        pruning_region_certificate={
            'theorem_level_dominated_labels': ['bronze'],
            'proves_theorem_level_pruning_of_dominated_regions': True,
        },
        termination_exclusion_promotion_certificate={
            'candidate_labels': ['nickel'],
            'promoted_labels': ['nickel'],
            'proves_termination_search_promotes_to_theorem_exclusion': True,
        },
    )
    cert = promote_omitted_class_global_control_certificate(
        screened_panel_certificate=screen,
        partition_certificate=screen['near_top_threat_set_partition_certificate'],
        arithmetic_ranking_certificate={
            'theorem_level_ranked_labels': ['silver', 'bronze', 'nickel'],
            'proves_exact_near_top_lagrange_spectrum_ranking': True,
        },
        pruning_region_certificate={
            'theorem_level_dominated_labels': ['bronze'],
            'proves_theorem_level_pruning_of_dominated_regions': True,
        },
        termination_exclusion_promotion_certificate={
            'candidate_labels': ['nickel'],
            'promoted_labels': ['nickel'],
            'proves_termination_search_promotes_to_theorem_exclusion': True,
        },
    )
    assert cert['status'] == 'omitted-class-global-control-certified'
    assert cert['omitted_classes_globally_controlled'] is True
    assert cert['omitted_labels'] == ['bronze', 'nickel']
    assert cert['uncontrolled_omitted_labels'] == []
    assert {row['class_label'] for row in cert['control_records']} == {'bronze', 'nickel'}
