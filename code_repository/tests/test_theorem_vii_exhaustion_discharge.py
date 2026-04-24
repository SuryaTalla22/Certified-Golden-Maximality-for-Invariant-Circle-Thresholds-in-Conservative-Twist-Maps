from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_golden_theorem_vii_discharge_report,
    build_golden_theorem_vii_exhaustion_discharge_lift_report,
)
from kam_theorem_suite.theorem_vii_exhaustion_discharge import (
    build_golden_theorem_vii_exhaustion_discharge_lift_certificate,
)
from kam_theorem_suite.theorem_viii_reduction_lift import (
    build_golden_theorem_viii_reduction_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload
    def to_dict(self):
        return dict(self._payload)


def _strong_vii(upstream=None, local=None):
    if upstream is None:
        upstream = [
        'localized_compatibility_window_identifies_true_irrational_threshold',
        'one_variable_eta_envelope_law',
        'strict_golden_top_gap_theorem',
    ]
    upstream = list(upstream)
    if local is None:
        local = [
        'finite_screened_panel_is_globally_complete',
        'omitted_nongolden_irrationals_outside_screened_panel_controlled',
    ]
    local = list(local)
    return {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete',
        'family_label': 'standard-sine',
        'reference_lower_bound': 0.97105,
        'reference_crossing_center': 0.97110,
        'open_hypotheses': [],
        'upstream_active_assumptions': upstream,
        'local_active_assumptions': local,
        'active_assumptions': upstream + local,
        'termination_aware_search_report': {
            'active_count': 0,
            'deferred_count': 0,
            'undecided_count': 0,
            'overlapping_count': 0,
        },
        'assumptions': [
            {'name': 'exact_near_top_lagrange_spectrum_ranking', 'assumed': False},
            {'name': 'theorem_level_pruning_of_dominated_regions', 'assumed': False},
            {'name': 'finite_screened_panel_is_globally_complete', 'assumed': False},
            {'name': 'deferred_or_retired_classes_are_globally_dominated', 'assumed': False},
            {'name': 'termination_search_promotes_to_theorem_exclusion', 'assumed': False},
            {'name': 'omitted_nongolden_irrationals_outside_screened_panel_controlled', 'assumed': False},
        ],
    }


def _strong_vi_discharge(active=None, local=None, statement_mode='two-variable'):
    if active is None:
        active = [
        'localized_compatibility_window_identifies_true_irrational_threshold',
        'one_variable_eta_envelope_law',
        'strict_golden_top_gap_theorem',
    ]
    active = list(active)
    if local is None:
        local = ['localized_compatibility_window_identifies_true_irrational_threshold']
    local = list(local)
    return {
        'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-front-complete',
        'statement_mode': statement_mode,
        'open_hypotheses': [],
        'active_assumptions': active,
        'local_active_assumptions': local,
        'current_most_dangerous_challenger_upper': 0.97102,
    }


def test_theorem_vii_discharge_reduces_upstream_burden(monkeypatch):
    import kam_theorem_suite.theorem_vii_exhaustion_discharge as tviid

    monkeypatch.setattr(tviid, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy(_strong_vii(upstream=[
        'validated_true_renormalization_fixed_point_package',
        'golden_stable_manifold_is_true_critical_surface',
        'family_chart_crossing_identifies_true_critical_parameter',
        'localized_compatibility_window_identifies_true_irrational_threshold',
        'one_variable_eta_envelope_law',
        'strict_golden_top_gap_theorem',
    ])))
    monkeypatch.setattr(tviid, 'build_golden_theorem_vi_discharge_certificate', lambda **kwargs: _Dummy(_strong_vi_discharge(active=[
        'localized_compatibility_window_identifies_true_irrational_threshold',
        'one_variable_eta_envelope_law',
        'strict_golden_top_gap_theorem',
    ])))

    cert = build_golden_theorem_vii_exhaustion_discharge_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vii-exhaustion-discharge-lift-front-complete'
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['theorem_vii_upstream_burden_reduced_by_discharge']['satisfied'] is True
    assert 'validated_true_renormalization_fixed_point_package' not in cert['upstream_active_assumptions']
    assert abs(cert['current_near_top_exhaustion_upper_bound'] - 0.97102) < 1.0e-12
    assert abs(cert['current_near_top_exhaustion_margin'] - 3.0e-05) < 1.0e-12
    assert cert['current_near_top_exhaustion_pending_count'] == 0
    assert cert['current_near_top_exhaustion_status'] == 'near-top-exhaustion-strong'
    assert cert['current_screened_panel_dominance_certificate']['status'] == 'screened-panel-dominance-strong'
    assert cert['residual_burden_summary']['status'] == 'global-completeness-and-omitted-control-frontier'
    assert cert['global_completeness_certificate']['theorem_status'] == 'golden-theorem-vii-global-completeness-promotion-frontier'


def test_theorem_vii_discharge_conditional_strong_when_all_assumptions_cleared(monkeypatch):
    import kam_theorem_suite.theorem_vii_exhaustion_discharge as tviid

    monkeypatch.setattr(tviid, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy(_strong_vii(upstream=[], local=[])))
    monkeypatch.setattr(tviid, 'build_golden_theorem_vi_discharge_certificate', lambda **kwargs: _Dummy(_strong_vi_discharge(active=[], local=[])))

    cert = build_golden_theorem_vii_exhaustion_discharge_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong'
    assert cert['active_assumptions'] == []


def test_theorem_vii_discharge_exposes_explicit_near_top_dominance_hypothesis(monkeypatch):
    import kam_theorem_suite.theorem_vii_exhaustion_discharge as tviid

    monkeypatch.setattr(tviid, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy(_strong_vii()))
    monkeypatch.setattr(tviid, 'build_golden_theorem_vi_discharge_certificate', lambda **kwargs: _Dummy(_strong_vi_discharge()))

    cert = build_golden_theorem_vii_exhaustion_discharge_lift_certificate(base_K_values=[0.3]).to_dict()
    hypotheses = {row['name']: row for row in cert['hypotheses']}
    assert hypotheses['all_near_top_challengers_dominated']['satisfied'] is True
    assert cert['residual_burden_summary']['status'] == 'global-completeness-and-omitted-control-frontier'


def test_driver_exposes_theorem_vii_discharge_reports(monkeypatch):
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_theorem_vii_exhaustion_discharge_lift_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vii-exhaustion-discharge-lift-front-complete',
        'active_assumptions': ['one_variable_eta_envelope_law'],
    }))
    monkeypatch.setattr(pd, 'build_golden_theorem_vii_discharge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong',
        'active_assumptions': [],
    }))

    lift = build_golden_theorem_vii_exhaustion_discharge_lift_report(base_K_values=[0.3])
    theorem = build_golden_theorem_vii_discharge_report(base_K_values=[0.3])
    assert lift['theorem_status'] == 'golden-theorem-vii-exhaustion-discharge-lift-front-complete'
    assert theorem['theorem_status'] == 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong'


def test_theorem_viii_accepts_theorem_vii_discharge_certificate(monkeypatch):
    import kam_theorem_suite.theorem_viii_reduction_lift as tviiil

    monkeypatch.setattr(tviiil, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-front-only',
        'open_hypotheses': [],
        'active_assumptions': ['obstruction_implies_no_analytic_circle'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_v_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-v-transport-lift-front-only',
        'open_hypotheses': [],
        'active_assumptions': ['validated_function_space_continuation_transport'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'statement_mode': 'two-variable',
        'open_hypotheses': [],
        'active_assumptions': ['strict_golden_top_gap_theorem'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['final_function_space_promotion'],
    }))

    cert = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.3],
        theorem_vii_exhaustion_discharge_certificate={
            'theorem_status': 'golden-theorem-vii-exhaustion-discharge-lift-front-complete',
            'open_hypotheses': [],
            'active_assumptions': ['one_variable_eta_envelope_law'],
            'theorem_vi_discharge_shell': {
                'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-front-complete',
                'statement_mode': 'two-variable',
                'open_hypotheses': [],
                'active_assumptions': ['one_variable_eta_envelope_law'],
                'threshold_identification_discharge_shell': {
                    'theorem_status': 'golden-threshold-identification-discharge-lift-front-complete',
                    'open_hypotheses': [],
                    'active_assumptions': ['localized_compatibility_window_identifies_true_irrational_threshold'],
                },
            },
        },
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-viii-reduction-lift-front-complete'
    assert cert['theorem_vii_shell']['theorem_status'] == 'golden-theorem-vii-exhaustion-discharge-lift-front-complete'
    assert cert['statement_mode'] == 'two-variable'


def test_theorem_vii_discharge_reuses_theorem_vi_shell_as_proxy_when_no_discharge_certificate_is_supplied(monkeypatch):
    import kam_theorem_suite.theorem_vii_exhaustion_discharge as tviid

    def _boom(*args, **kwargs):
        raise AssertionError('Theorem VI discharge builder should not run when a reusable Theorem VI shell is already available')

    monkeypatch.setattr(tviid, 'build_golden_theorem_vi_discharge_certificate', _boom)
    cert = build_golden_theorem_vii_exhaustion_discharge_lift_certificate(
        base_K_values=[0.3],
        theorem_vii_certificate=_strong_vii(),
        theorem_vi_certificate={
            'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-partial',
            'open_hypotheses': ['threshold_identification_front_complete'],
            'active_assumptions': ['one_variable_eta_envelope_law'],
            'local_active_assumptions': ['one_variable_eta_envelope_law'],
            'statement_mode': 'one-variable',
            'current_local_top_gap_certificate': {'current_most_dangerous_challenger_upper': 0.3005},
        },
    ).to_dict()
    assert cert['theorem_vi_discharge_shell']['theorem_status'] == 'golden-theorem-vi-envelope-lift-conditional-partial'
    assert cert['theorem_vi_discharge_shell']['current_most_dangerous_challenger_upper'] == 0.3005
