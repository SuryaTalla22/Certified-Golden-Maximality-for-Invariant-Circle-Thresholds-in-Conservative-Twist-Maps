from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_golden_theorem_vii_exhaustion_lift_report,
    build_golden_theorem_vii_report,
)
from kam_theorem_suite.theorem_vii_exhaustion_lift import (
    build_golden_theorem_vii_exhaustion_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload
    def to_dict(self):
        return dict(self._payload)


def test_theorem_vii_front_complete_when_screen_and_search_stack_are_closed(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    monkeypatch.setattr(tviil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['one_variable_eta_envelope_law'],
    }))
    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', lambda specs, **kwargs: _Dummy({
        'status': 'partial-class-exhaustion-screen',
        'classes': [{'class_label': 'silver'}],
    }))
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'adaptive-search-partial-exhaustion',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'evidence-weighted-search-partial-exhaustion',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'termination-aware-search-partial-exhaustion',
        'rounds': [{'round_index': 1}],
        'active_count': 0,
        'deferred_count': 0,
        'overlapping_count': 0,
        'undecided_count': 0,
        'strongest_active_upper_bound': None,
    }))

    cert = build_golden_theorem_vii_exhaustion_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vii-exhaustion-lift-front-complete'
    assert cert['open_hypotheses'] == []
    assert cert['upstream_active_assumptions'] == ['one_variable_eta_envelope_law']
    assert cert['current_screened_panel_dominance_certificate']['status'] == 'screened-panel-dominance-strong'
    assert cert['residual_burden_summary']['status'] == 'global-exhaustion-support-frontier'
    assert cert['global_completeness_certificate']['theorem_status'] == 'golden-theorem-vii-global-completeness-support-frontier'
    assert 'finite_screened_panel_is_globally_complete' in cert['local_active_assumptions']



def test_theorem_vii_conditional_strong_when_all_assumptions_are_toggled_on(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    monkeypatch.setattr(tviil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'classes': [{'class_label': 'silver'}, {'class_label': 'bronze'}],
    }))
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
        'active_count': 0,
        'deferred_count': 0,
        'overlapping_count': 0,
        'undecided_count': 0,
        'strongest_active_upper_bound': None,
    }))

    cert = build_golden_theorem_vii_exhaustion_lift_certificate(
        base_K_values=[0.3],
        assume_exact_near_top_lagrange_spectrum_ranking=True,
        assume_theorem_level_pruning_of_dominated_regions=True,
        assume_finite_screened_panel_is_globally_complete=True,
        assume_deferred_or_retired_classes_are_globally_dominated=True,
        assume_termination_search_promotes_to_theorem_exclusion=True,
        assume_omitted_nongolden_irrationals_outside_screened_panel_controlled=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vii-exhaustion-lift-conditional-strong'
    assert cert['active_assumptions'] == []



def test_theorem_vii_stays_partial_when_search_stack_is_not_closed(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    monkeypatch.setattr(tviil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-partial',
        'open_hypotheses': ['threshold_identification_front_complete'],
        'active_assumptions': ['one_variable_eta_envelope_law'],
    }))
    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', lambda specs, **kwargs: _Dummy({
        'status': 'screen-has-overlapping-challengers',
        'classes': [{'class_label': 'silver'}],
    }))
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'adaptive-search-has-overlapping-challengers',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'evidence-weighted-search-has-overlapping-challengers',
        'rounds': [],
    }))
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'termination-aware-search-has-overlapping-challengers',
        'rounds': [{'round_index': 1}],
        'active_count': 1,
        'deferred_count': 1,
        'overlapping_count': 1,
        'undecided_count': 1,
        'strongest_active_upper_bound': 0.305,
    }))

    cert = build_golden_theorem_vii_exhaustion_lift_certificate(
        base_K_values=[0.3],
        assume_exact_near_top_lagrange_spectrum_ranking=True,
        assume_theorem_level_pruning_of_dominated_regions=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vii-exhaustion-lift-conditional-partial'
    assert 'theorem_vi_front_complete' in cert['open_hypotheses']
    assert 'evidence_weighted_search_executed' in cert['open_hypotheses']
    assert 'no_overlapping_final_challengers' in cert['open_hypotheses']
    assert 'no_active_search_classes_remaining' in cert['open_hypotheses']


def test_theorem_vii_residual_burden_becomes_global_when_near_top_panel_is_closed(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    monkeypatch.setattr(tviil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'classes': [{'class_label': 'silver'}],
        'dominated_count': 1,
        'strongest_remaining_upper_bound': None,
    }))
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
        'active_count': 0,
        'deferred_count': 0,
        'overlapping_count': 0,
        'undecided_count': 0,
        'strongest_active_upper_bound': None,
    }))

    cert = build_golden_theorem_vii_exhaustion_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['current_screened_panel_dominance_certificate']['status'] == 'screened-panel-dominance-strong'
    assert cert['residual_burden_summary']['status'] == 'global-exhaustion-support-frontier'
    assert cert['global_completeness_certificate']['residual_burden_summary']['status'] == 'global-exhaustion-support-frontier'
    assert 'all_near_top_challengers_dominated' in cert['discharged_hypotheses']


def test_driver_exposes_theorem_vii_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_theorem_vii_exhaustion_lift_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete',
        'active_assumptions': ['finite_screened_panel_is_globally_complete'],
    }))
    monkeypatch.setattr(pd, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'active_assumptions': [],
    }))

    lift_report = build_golden_theorem_vii_exhaustion_lift_report(base_K_values=[0.3])
    theorem_report = build_golden_theorem_vii_report(base_K_values=[0.3])
    assert lift_report['theorem_status'] == 'golden-theorem-vii-exhaustion-lift-front-complete'
    assert theorem_report['theorem_status'] == 'golden-theorem-vii-exhaustion-lift-conditional-strong'


def test_theorem_vii_support_certificates_clear_support_frontier_without_manual_toggles(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    monkeypatch.setattr(tviil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'classes': [{'class_label': 'silver'}],
        'arithmetic_ranking_certificate': {
            'status': 'exact-near-top-ranking-certificate-strong',
            'proves_exact_near_top_lagrange_spectrum_ranking': True,
        },
        'pruning_region_certificate': {
            'status': 'theorem-level-dominated-regions-certified',
            'proves_theorem_level_pruning_of_dominated_regions': True,
        },
        'screened_panel_global_completeness_certificate': {
            'status': 'screened-panel-global-completeness-frontier',
            'screened_panel_globally_complete': False,
        },
    }))
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
        'active_count': 0,
        'deferred_count': 0,
        'overlapping_count': 0,
        'undecided_count': 0,
        'strongest_active_upper_bound': None,
        'deferred_retired_domination_certificate': {
            'status': 'no-deferred-or-retired-classes',
            'proves_deferred_or_retired_classes_are_globally_dominated': True,
        },
        'termination_exclusion_promotion_certificate': {
            'status': 'termination-exclusion-vacuous',
            'proves_termination_search_promotes_to_theorem_exclusion': True,
        },
    }))

    cert = build_golden_theorem_vii_exhaustion_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['residual_burden_summary']['status'] == 'global-completeness-and-omitted-control-frontier'
    assert cert['global_completeness_certificate']['readiness_summary']['support_ready'] is True
    assert 'exact_near_top_lagrange_spectrum_ranking' not in cert['local_active_assumptions']
    assert 'finite_screened_panel_is_globally_complete' in cert['local_active_assumptions']



def test_theorem_vii_can_be_fully_discharged_via_certificate_pipeline(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    monkeypatch.setattr(tviil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'classes': [{'class_label': 'silver'}],
        'arithmetic_ranking_certificate': {
            'status': 'exact-near-top-ranking-certificate-strong',
            'proves_exact_near_top_lagrange_spectrum_ranking': True,
        },
        'pruning_region_certificate': {
            'status': 'theorem-level-dominated-regions-certified',
            'proves_theorem_level_pruning_of_dominated_regions': True,
        },
        'screened_panel_global_completeness_certificate': {
            'status': 'screened-panel-global-completeness-certified',
            'screened_panel_globally_complete': True,
        },
    }))
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
        'active_count': 0,
        'deferred_count': 0,
        'overlapping_count': 0,
        'undecided_count': 0,
        'strongest_active_upper_bound': None,
        'deferred_retired_domination_certificate': {
            'status': 'no-deferred-or-retired-classes',
            'proves_deferred_or_retired_classes_are_globally_dominated': True,
        },
        'termination_exclusion_promotion_certificate': {
            'status': 'termination-exclusion-vacuous',
            'proves_termination_search_promotes_to_theorem_exclusion': True,
        },
    }))

    cert = build_golden_theorem_vii_exhaustion_lift_certificate(
        base_K_values=[0.3],
        omitted_class_global_control_certificate={
            'status': 'omitted-class-global-control-certified',
            'omitted_classes_globally_controlled': True,
        },
    ).to_dict()
    assert cert['global_completeness_certificate']['residual_burden_summary']['status'] == 'fully-discharged'
    assert cert['local_active_assumptions'] == []
    assert cert['active_assumptions'] == []
    assert cert['theorem_status'] == 'golden-theorem-vii-exhaustion-lift-conditional-strong'



def test_theorem_vii_screened_panel_completeness_can_discharge_via_partition_pipeline(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    monkeypatch.setattr(tviil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'classes': [{'class_label': 'silver'}],
        'arithmetic_ranking_certificate': {
            'status': 'exact-near-top-ranking-certificate-strong',
            'theorem_level_ranked_labels': ['silver', 'bronze'],
            'proves_exact_near_top_lagrange_spectrum_ranking': True,
        },
        'pruning_region_certificate': {
            'status': 'theorem-level-dominated-regions-certified',
            'theorem_level_dominated_labels': ['bronze'],
            'proves_theorem_level_pruning_of_dominated_regions': True,
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
    }))
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
        'active_count': 0,
        'deferred_count': 0,
        'overlapping_count': 0,
        'undecided_count': 0,
        'strongest_active_upper_bound': None,
        'deferred_retired_domination_certificate': {
            'status': 'no-deferred-or-retired-classes',
            'deferred_labels': [],
            'retired_labels': [],
            'proves_deferred_or_retired_classes_are_globally_dominated': True,
        },
        'termination_exclusion_promotion_certificate': {
            'status': 'termination-exclusion-vacuous',
            'candidate_labels': [],
            'promoted_labels': [],
            'proves_termination_search_promotes_to_theorem_exclusion': True,
        },
    }))

    cert = build_golden_theorem_vii_exhaustion_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['support_certificates']['near_top_threat_set_partition_certificate']['partition_complete'] is True
    assert cert['support_certificates']['omitted_class_global_control_certificate']['omitted_classes_globally_controlled'] is True
    assert cert['global_completeness_certificate']['residual_burden_summary']['status'] == 'fully-discharged'
    assert 'finite_screened_panel_is_globally_complete' not in cert['local_active_assumptions']
    assert 'omitted_nongolden_irrationals_outside_screened_panel_controlled' not in cert['local_active_assumptions']



def test_theorem_vii_omitted_class_global_control_can_discharge_via_partition_pipeline(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    monkeypatch.setattr(tviil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'classes': [{'class_label': 'silver'}],
        'arithmetic_ranking_certificate': {
            'status': 'exact-near-top-ranking-certificate-strong',
            'theorem_level_ranked_labels': ['silver', 'bronze', 'nickel'],
            'proves_exact_near_top_lagrange_spectrum_ranking': True,
        },
        'pruning_region_certificate': {
            'status': 'theorem-level-dominated-regions-certified',
            'theorem_level_dominated_labels': ['bronze'],
            'proves_theorem_level_pruning_of_dominated_regions': True,
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
    }))
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
    }))
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', lambda specs, **kwargs: _Dummy({
        'status': 'all-screened-classes-dominated',
        'rounds': [{'round_index': 1}],
        'active_count': 0,
        'deferred_count': 0,
        'overlapping_count': 0,
        'undecided_count': 0,
        'strongest_active_upper_bound': None,
        'deferred_retired_domination_certificate': {
            'status': 'no-deferred-or-retired-classes',
            'deferred_labels': [],
            'retired_labels': [],
            'proves_deferred_or_retired_classes_are_globally_dominated': True,
        },
        'termination_exclusion_promotion_certificate': {
            'status': 'termination-exclusion-promotion-certified',
            'candidate_labels': ['nickel'],
            'promoted_labels': ['nickel'],
            'proves_termination_search_promotes_to_theorem_exclusion': True,
        },
    }))

    cert = build_golden_theorem_vii_exhaustion_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['support_certificates']['omitted_class_global_control_certificate']['status'] == 'omitted-class-global-control-certified'
    assert cert['support_certificates']['omitted_class_global_control_certificate']['omitted_classes_globally_controlled'] is True
    assert cert['global_completeness_certificate']['residual_burden_summary']['status'] == 'fully-discharged'
    assert 'omitted_nongolden_irrationals_outside_screened_panel_controlled' not in cert['local_active_assumptions']


def test_theorem_vii_reuses_theorem_vi_near_top_surface_without_rebuilding_search_stack(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    def _boom(*args, **kwargs):
        raise AssertionError('full class-exhaustion/search stack should not run when Theorem VI already provides the near-top challenger surface')

    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', _boom)
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', _boom)
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', _boom)
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', _boom)
    monkeypatch.setattr(tviil, 'build_near_top_eta_challenger_comparison_certificate', lambda specs, **kwargs: _Dummy({
        'challenger_records': [
            {'label': 'silver', 'status': 'arithmetic-weaker-only', 'reason': 'eta separated', 'eta_interval': [0.40, 0.41], 'threshold_upper_bound': None, 'threshold_lower_bound': None, 'threshold_source': 'near-top-eta-anchor'},
            {'label': 'bronze', 'status': 'arithmetic-weaker-only', 'reason': 'eta separated', 'eta_interval': [0.39, 0.40], 'threshold_upper_bound': None, 'threshold_lower_bound': None, 'threshold_source': 'near-top-eta-anchor'},
            {'label': 'near-golden-12', 'status': 'arithmetic-weaker-only', 'reason': 'eta separated', 'eta_interval': [0.41, 0.42], 'threshold_upper_bound': None, 'threshold_lower_bound': None, 'threshold_source': 'near-top-eta-anchor'},
        ],
        'theorem_status': 'near-top-eta-challenger-comparison-moderate',
        'global_nongolden_ceiling_certificate': {'global_ceiling_theorem_certified': False},
        'near_top_relation': {'arithmetic_only_labels': ['silver', 'bronze', 'near-golden-12']},
        'theorem_flags': {'challenger_records_available': True},
        'notes': 'seeded near-top surface',
    }))

    cert = tviil.build_golden_theorem_vii_exhaustion_lift_certificate(
        base_K_values=[0.3],
        theorem_vi_certificate={
            'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-partial',
            'open_hypotheses': ['threshold_identification_front_complete'],
            'active_assumptions': [],
            'eta_threshold_anchor': {'family_label': 'standard-sine', 'eta_interval': [0.44, 0.45], 'threshold_interval': [0.3, 0.31], 'local_envelope_anchor': {}},
            'near_top_challenger_surface': {},
        },
    ).to_dict()
    assert cert['class_exhaustion_screen']['status'] == 'near-top-surface-screen-front-complete'
    assert cert['adaptive_search_report']['status'] == 'adaptive-search-seeded-from-theorem-vi-near-top-surface'
    assert cert['termination_aware_search_report']['status'] == 'termination-aware-search-seeded-from-theorem-vi-near-top-surface'
    assert 'theorem_vi_front_complete' in cert['open_hypotheses']


def test_theorem_vii_reuses_nested_vi_shell_from_discharge_object(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_lift as tviil

    def _unexpected(*args, **kwargs):
        raise AssertionError('full class-exhaustion search stack should not run when nested Theorem VI shell is available')

    monkeypatch.setattr(tviil, 'build_class_exhaustion_screen', _unexpected)
    monkeypatch.setattr(tviil, 'build_adaptive_class_exhaustion_search', _unexpected)
    monkeypatch.setattr(tviil, 'build_evidence_weighted_class_exhaustion_search', _unexpected)
    monkeypatch.setattr(tviil, 'build_termination_aware_class_exhaustion_search', _unexpected)
    monkeypatch.setattr(
        tviil,
        'build_near_top_eta_challenger_comparison_certificate',
        lambda specs, **kwargs: _Dummy({
            'family_label': 'standard-sine',
            'golden_anchor_certificate': {'threshold_interval': [0.29, 0.31]},
            'challenger_records': [
                {
                    'label': 'silver',
                    'status': 'dominated-by-golden-threshold-anchor',
                    'threshold_lower_bound': 0.25,
                    'threshold_upper_bound': 0.28,
                    'threshold_source': 'mock-near-top',
                },
                {
                    'label': 'bronze',
                    'status': 'dominated-by-golden-threshold-anchor',
                    'threshold_lower_bound': 0.24,
                    'threshold_upper_bound': 0.27,
                    'threshold_source': 'mock-near-top',
                },
                {
                    'label': 'near-golden-12',
                    'status': 'dominated-by-golden-threshold-anchor',
                    'threshold_lower_bound': 0.245,
                    'threshold_upper_bound': 0.279,
                    'threshold_source': 'mock-near-top',
                },
            ],
            'panel_records': [],
            'theorem_status': 'near-top-eta-challenger-comparison-strong',
            'notes': 'mock near-top surface',
        }),
    )

    cert = build_golden_theorem_vii_exhaustion_lift_certificate(
        base_K_values=[0.3],
        theorem_vi_envelope_discharge_certificate={
            'family_label': 'standard-sine',
            'theorem_status': 'golden-theorem-vi-envelope-discharge-conditional-strong',
            'open_hypotheses': [],
            'active_assumptions': [],
            'theorem_vi_shell': {
                'family_label': 'standard-sine',
                'eta_threshold_anchor': {
                    'family_label': 'standard-sine',
                    'eta_interval': [0.3, 0.301],
                    'threshold_interval': [0.299, 0.301],
                },
                'near_top_challenger_surface': {
                    'family_label': 'standard-sine',
                    'challenger_records': [],
                    'panel_records': [],
                    'theorem_status': 'near-top-eta-challenger-comparison-partial',
                },
            },
        },
    ).to_dict()

    assert cert['theorem_status'] in {
        'golden-theorem-vii-exhaustion-lift-front-complete',
        'golden-theorem-vii-exhaustion-lift-conditional-partial',
        'golden-theorem-vii-exhaustion-lift-conditional-strong',
    }
    assert cert['class_exhaustion_screen']['classes']
    assert cert['class_exhaustion_screen']['classes'][0]['notes'].startswith('Derived from the existing Theorem VI near-top challenger surface')
