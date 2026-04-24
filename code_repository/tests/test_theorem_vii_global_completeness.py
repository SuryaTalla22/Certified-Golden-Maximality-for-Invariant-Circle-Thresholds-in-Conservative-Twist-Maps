from __future__ import annotations

from kam_theorem_suite.theorem_vii_global_completeness import (
    build_golden_theorem_vii_global_completeness_certificate,
)


def _base_vii(local=None, upstream=None, residual=None):
    if local is None:
        local = [
            'finite_screened_panel_is_globally_complete',
            'omitted_nongolden_irrationals_outside_screened_panel_controlled',
        ]
    if upstream is None:
        upstream = []
    if residual is None:
        residual = {'local_front_hypotheses': [], 'status': 'global-screened-panel-completeness-frontier'}
    return {
        'family_label': 'standard-sine',
        'current_screened_panel_dominance_certificate': {
            'status': 'screened-panel-dominance-strong',
            'dominance_margin': 3.0e-05,
            'near_top_frontier_closed': True,
        },
        'residual_burden_summary': residual,
        'local_active_assumptions': list(local),
        'upstream_active_assumptions': list(upstream),
        'active_assumptions': list(upstream) + list(local),
        'assumptions': [
            {'name': 'exact_near_top_lagrange_spectrum_ranking', 'assumed': 'exact_near_top_lagrange_spectrum_ranking' not in local},
            {'name': 'theorem_level_pruning_of_dominated_regions', 'assumed': 'theorem_level_pruning_of_dominated_regions' not in local},
            {'name': 'finite_screened_panel_is_globally_complete', 'assumed': 'finite_screened_panel_is_globally_complete' not in local},
            {'name': 'deferred_or_retired_classes_are_globally_dominated', 'assumed': 'deferred_or_retired_classes_are_globally_dominated' not in local},
            {'name': 'termination_search_promotes_to_theorem_exclusion', 'assumed': 'termination_search_promotes_to_theorem_exclusion' not in local},
            {'name': 'omitted_nongolden_irrationals_outside_screened_panel_controlled', 'assumed': 'omitted_nongolden_irrationals_outside_screened_panel_controlled' not in local},
        ],
    }


def test_global_completeness_certificate_exposes_split_frontier() -> None:
    cert = build_golden_theorem_vii_global_completeness_certificate(_base_vii()).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vii-global-completeness-promotion-frontier'
    assert cert['residual_burden_summary']['status'] == 'global-completeness-and-omitted-control-frontier'
    assert cert['readiness_summary']['promotion_ready'] is True


def test_global_completeness_certificate_can_isolate_omitted_class_control() -> None:
    cert = build_golden_theorem_vii_global_completeness_certificate(_base_vii(local=['omitted_nongolden_irrationals_outside_screened_panel_controlled'])).to_dict()
    assert cert['residual_burden_summary']['status'] == 'omitted-class-global-control-frontier'
    assert cert['theorem_status'] == 'golden-theorem-vii-global-completeness-promotion-frontier'


def test_global_completeness_certificate_detects_support_frontier() -> None:
    local = [
        'exact_near_top_lagrange_spectrum_ranking',
        'theorem_level_pruning_of_dominated_regions',
        'deferred_or_retired_classes_are_globally_dominated',
        'termination_search_promotes_to_theorem_exclusion',
    ]
    cert = build_golden_theorem_vii_global_completeness_certificate(_base_vii(local=local)).to_dict()
    assert cert['residual_burden_summary']['status'] == 'global-exhaustion-support-frontier'
    assert cert['theorem_status'] == 'golden-theorem-vii-global-completeness-support-frontier'


def test_global_completeness_certificate_can_be_fully_discharged_conditionally() -> None:
    cert = build_golden_theorem_vii_global_completeness_certificate(_base_vii(local=[], upstream=[])).to_dict()
    assert cert['residual_burden_summary']['status'] == 'fully-discharged'
    assert cert['theorem_status'] == 'golden-theorem-vii-global-completeness-conditional-strong'


def test_global_completeness_certificate_can_clear_support_frontier_via_certificates() -> None:
    cert = build_golden_theorem_vii_global_completeness_certificate(
        _base_vii(
            local=[
                'exact_near_top_lagrange_spectrum_ranking',
                'theorem_level_pruning_of_dominated_regions',
                'deferred_or_retired_classes_are_globally_dominated',
                'termination_search_promotes_to_theorem_exclusion',
                'finite_screened_panel_is_globally_complete',
                'omitted_nongolden_irrationals_outside_screened_panel_controlled',
            ]
        )
        | {
            'support_certificates': {
                'exact_near_top_lagrange_spectrum_ranking_certificate': {
                    'status': 'exact-near-top-ranking-certificate-strong',
                    'proves_exact_near_top_lagrange_spectrum_ranking': True,
                },
                'theorem_level_pruning_certificate': {
                    'status': 'theorem-level-dominated-regions-certified',
                    'proves_theorem_level_pruning_of_dominated_regions': True,
                },
                'deferred_retired_domination_certificate': {
                    'status': 'deferred-retired-domination-certified',
                    'proves_deferred_or_retired_classes_are_globally_dominated': True,
                },
                'termination_search_exclusion_certificate': {
                    'status': 'termination-exclusion-promotion-certified',
                    'proves_termination_search_promotes_to_theorem_exclusion': True,
                },
            }
        }
    ).to_dict()
    assert cert['residual_burden_summary']['status'] == 'global-completeness-and-omitted-control-frontier'
    assert cert['theorem_status'] == 'golden-theorem-vii-global-completeness-promotion-frontier'
    assert cert['readiness_summary']['support_ready'] is True



def test_global_completeness_certificate_uses_panel_and_omitted_control_certificates() -> None:
    cert = build_golden_theorem_vii_global_completeness_certificate(
        _base_vii(
            local=[
                'finite_screened_panel_is_globally_complete',
                'omitted_nongolden_irrationals_outside_screened_panel_controlled',
            ]
        )
        | {
            'support_certificates': {
                'screened_panel_global_completeness_certificate': {
                    'status': 'screened-panel-global-completeness-certified',
                    'screened_panel_globally_complete': True,
                },
                'omitted_class_global_control_certificate': {
                    'status': 'omitted-class-global-control-certified',
                    'omitted_classes_globally_controlled': True,
                },
            }
        }
    ).to_dict()
    assert cert['residual_burden_summary']['status'] == 'fully-discharged'
    assert cert['theorem_status'] == 'golden-theorem-vii-global-completeness-conditional-strong'
    assert cert['readiness_summary']['full_global_ready'] is True



def test_global_completeness_certificate_builds_partition_and_can_isolate_omitted_control() -> None:
    cert = build_golden_theorem_vii_global_completeness_certificate(
        _base_vii(local=[
            'exact_near_top_lagrange_spectrum_ranking',
            'theorem_level_pruning_of_dominated_regions',
            'finite_screened_panel_is_globally_complete',
            'deferred_or_retired_classes_are_globally_dominated',
            'termination_search_promotes_to_theorem_exclusion',
            'omitted_nongolden_irrationals_outside_screened_panel_controlled',
        ])
        | {
            'support_certificates': {
                'exact_near_top_lagrange_spectrum_ranking_certificate': {
                    'status': 'exact-near-top-ranking-certificate-strong',
                    'theorem_level_ranked_labels': ['silver', 'bronze'],
                    'proves_exact_near_top_lagrange_spectrum_ranking': True,
                },
                'theorem_level_pruning_certificate': {
                    'status': 'theorem-level-dominated-regions-certified',
                    'theorem_level_dominated_labels': ['bronze'],
                    'proves_theorem_level_pruning_of_dominated_regions': True,
                },
                'deferred_retired_domination_certificate': {
                    'status': 'no-deferred-or-retired-classes',
                    'deferred_labels': [],
                    'retired_labels': [],
                    'proves_deferred_or_retired_classes_are_globally_dominated': True,
                },
                'termination_search_exclusion_certificate': {
                    'status': 'termination-exclusion-vacuous',
                    'candidate_labels': [],
                    'promoted_labels': [],
                    'proves_termination_search_promotes_to_theorem_exclusion': True,
                },
                'screened_panel_global_completeness_certificate': {
                    'status': 'screened-panel-global-completeness-frontier',
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
            }
        }
    ).to_dict()
    assert cert['near_top_threat_set_partition_certificate']['partition_complete'] is True
    assert cert['support_certificates']['omitted_class_global_control_certificate']['omitted_classes_globally_controlled'] is True
    assert cert['residual_burden_summary']['status'] == 'fully-discharged'
    assert cert['theorem_status'] == 'golden-theorem-vii-global-completeness-conditional-strong'



def test_global_completeness_certificate_can_promote_omitted_tail_control_from_partition_pipeline() -> None:
    cert = build_golden_theorem_vii_global_completeness_certificate(
        _base_vii(local=[
            'exact_near_top_lagrange_spectrum_ranking',
            'theorem_level_pruning_of_dominated_regions',
            'finite_screened_panel_is_globally_complete',
            'deferred_or_retired_classes_are_globally_dominated',
            'termination_search_promotes_to_theorem_exclusion',
            'omitted_nongolden_irrationals_outside_screened_panel_controlled',
        ])
        | {
            'support_certificates': {
                'exact_near_top_lagrange_spectrum_ranking_certificate': {
                    'status': 'exact-near-top-ranking-certificate-strong',
                    'theorem_level_ranked_labels': ['silver', 'bronze', 'nickel'],
                    'proves_exact_near_top_lagrange_spectrum_ranking': True,
                },
                'theorem_level_pruning_certificate': {
                    'status': 'theorem-level-dominated-regions-certified',
                    'theorem_level_dominated_labels': ['bronze'],
                    'proves_theorem_level_pruning_of_dominated_regions': True,
                },
                'deferred_retired_domination_certificate': {
                    'status': 'no-deferred-or-retired-classes',
                    'deferred_labels': [],
                    'retired_labels': [],
                    'proves_deferred_or_retired_classes_are_globally_dominated': True,
                },
                'termination_search_exclusion_certificate': {
                    'status': 'termination-exclusion-promotion-certified',
                    'candidate_labels': ['nickel'],
                    'promoted_labels': ['nickel'],
                    'proves_termination_search_promotes_to_theorem_exclusion': True,
                },
                'screened_panel_global_completeness_certificate': {
                    'status': 'screened-panel-global-completeness-frontier',
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
            }
        }
    ).to_dict()
    assert cert['support_certificates']['omitted_class_global_control_certificate']['status'] == 'omitted-class-global-control-certified'
    assert cert['support_certificates']['omitted_class_global_control_certificate']['omitted_classes_globally_controlled'] is True
    assert cert['residual_burden_summary']['status'] == 'fully-discharged'
    assert cert['theorem_status'] == 'golden-theorem-vii-global-completeness-conditional-strong'
