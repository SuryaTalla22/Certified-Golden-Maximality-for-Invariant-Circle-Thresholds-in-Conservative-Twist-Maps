from __future__ import annotations

from kam_theorem_suite import proof_driver
from kam_theorem_suite import threshold_identification_transport_discharge as mod
from kam_theorem_suite import theorem_vi_envelope_discharge as thm6


class DummyCert:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return dict(self._data)


def _theorem_v_front_complete(*, active=None, interval=None, status='golden-theorem-v-transport-lift-front-complete'):
    active = [] if active is None else list(active)
    lo, hi = interval or (0.97108, 0.97112)
    return {
        'rho': 0.618,
        'family_label': 'standard-sine',
        'open_hypotheses': [],
        'theorem_status': status,
        'active_assumptions': list(active),
        'convergence_front': {
            'theorem_v_explicit_error_control': {
                'compatible_limit_interval_lo': float(lo),
                'compatible_limit_interval_hi': float(hi),
            }
        },
    }


def _identification_discharge_front_complete(*, upstream=None, local=None, identified=None, status='golden-threshold-identification-discharge-lift-front-complete'):
    upstream = [] if upstream is None else list(upstream)
    local = [] if local is None else list(local)
    return {
        'rho': 0.618,
        'family_label': 'standard-sine',
        'open_hypotheses': [],
        'theorem_status': status,
        'upstream_active_assumptions': list(upstream),
        'local_active_assumptions': list(local),
        'active_assumptions': list(upstream) + [x for x in local if x not in upstream],
        'identified_window': list(identified or [0.97109, 0.97111]),
        'residual_burden_summary': {
            'status': 'critical-surface-threshold-promotion-frontier' if upstream else 'localized-compatibility-identification-frontier',
        },
    }


def test_transport_discharge_reduces_broad_hinge(monkeypatch):
    theorem_v = _theorem_v_front_complete(active=[
        'validated_function_space_continuation_transport',
        'unique_branch_continuation_to_true_irrational_threshold',
        'uniform_error_law_preserves_golden_gap',
    ])
    discharge = _identification_discharge_front_complete(
        upstream=['final_function_space_promotion'],
        local=['localized_compatibility_window_identifies_true_irrational_threshold'],
    )
    monkeypatch.setattr(mod, 'build_golden_theorem_v_certificate', lambda **kwargs: DummyCert(theorem_v))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: DummyCert(discharge))

    cert = mod.build_golden_threshold_identification_transport_discharge_certificate(base_K_values=[0.9, 0.95]).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-transport-discharge-lift-front-complete'
    assert cert['local_active_assumptions'] == ['unique_true_threshold_branch_inside_transport_locked_window']
    assert 'unique_branch_continuation_to_true_irrational_threshold' not in cert['upstream_active_assumptions']
    assert 'validated_function_space_continuation_transport' in cert['upstream_active_assumptions']
    names = {row['name']: row for row in cert['hypotheses']}
    assert names['identified_window_locked_by_transport_interval']['satisfied'] is True
    assert names['broader_identification_hinge_reduced_to_locked_window_uniqueness']['satisfied'] is True
    assert cert['residual_burden_summary']['status'] == 'transport-locked-local-uniqueness-frontier'


def test_transport_discharge_conditional_strong_when_local_uniqueness_toggled(monkeypatch):
    theorem_v = _theorem_v_front_complete(active=['unique_branch_continuation_to_true_irrational_threshold'])
    discharge = _identification_discharge_front_complete(upstream=[], local=['localized_compatibility_window_identifies_true_irrational_threshold'])
    monkeypatch.setattr(mod, 'build_golden_theorem_v_certificate', lambda **kwargs: DummyCert(theorem_v))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: DummyCert(discharge))

    cert = mod.build_golden_threshold_identification_transport_discharge_certificate(
        base_K_values=[0.9, 0.95],
        assume_unique_true_threshold_branch_inside_transport_locked_window=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-transport-discharge-lift-conditional-strong'
    assert cert['local_active_assumptions'] == []


def test_transport_discharge_driver_reports(monkeypatch):
    monkeypatch.setattr(proof_driver, 'build_golden_threshold_identification_transport_discharge_certificate', lambda **kwargs: DummyCert({
        'theorem_status': 'golden-threshold-identification-transport-discharge-lift-front-complete',
        'local_active_assumptions': ['unique_true_threshold_branch_inside_transport_locked_window'],
    }))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate', lambda **kwargs: DummyCert({
        'theorem_status': 'golden-threshold-identification-transport-discharge-lift-conditional-strong',
        'local_active_assumptions': [],
    }))
    lift = proof_driver.build_golden_threshold_identification_transport_discharge_lift_report(base_K_values=[0.3])
    theorem = proof_driver.build_golden_theorem_ii_to_v_identification_transport_discharge_report(base_K_values=[0.3])
    assert lift['theorem_status'] == 'golden-threshold-identification-transport-discharge-lift-front-complete'
    assert theorem['theorem_status'] == 'golden-threshold-identification-transport-discharge-lift-conditional-strong'


def test_theorem_vi_accepts_transport_discharge_certificate(monkeypatch):
    theorem_vi = {
        'rho': 0.618,
        'family_label': 'standard-sine',
        'statement_mode': 'one-variable',
        'threshold_identification_shell': {
            'active_assumptions': [
                'validated_true_renormalization_fixed_point_package',
                'golden_stable_manifold_is_true_critical_surface',
                'family_chart_crossing_identifies_true_critical_parameter',
                'localized_compatibility_window_identifies_true_irrational_threshold',
            ],
            'open_hypotheses': [],
            'theorem_status': 'golden-threshold-identification-lift-front-complete',
        },
        'assumptions': [
            {'name': 'one_variable_eta_envelope_law', 'assumed': False, 'source': 'test', 'note': ''},
        ],
        'local_active_assumptions': ['one_variable_eta_envelope_law'],
        'active_assumptions': ['one_variable_eta_envelope_law'],
        'open_hypotheses': [],
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
    }
    transport_discharge = {
        'theorem_status': 'golden-threshold-identification-transport-discharge-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['obstruction_excludes_analytic_circle', 'unique_true_threshold_branch_inside_transport_locked_window'],
        'local_active_assumptions': ['unique_true_threshold_branch_inside_transport_locked_window'],
    }
    monkeypatch.setattr(thm6, 'build_golden_theorem_vi_certificate', lambda **kwargs: DummyCert(theorem_vi))
    cert = thm6.build_golden_theorem_vi_envelope_discharge_lift_certificate(
        base_K_values=[0.9, 0.95],
        threshold_identification_transport_discharge_certificate=transport_discharge,
    ).to_dict()
    assert cert['upstream_active_assumptions'] == ['obstruction_excludes_analytic_circle', 'unique_true_threshold_branch_inside_transport_locked_window']
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['identification_residual_hinge_isolated']['satisfied'] is True



def test_transport_discharge_auto_discharges_local_uniqueness_from_certificate(monkeypatch):
    theorem_v = _theorem_v_front_complete(active=['unique_branch_continuation_to_true_irrational_threshold'])
    theorem_v['convergence_front'].update({
        'relation': {
            'lower_bound': 0.97090,
            'lower_window_hi': 0.97100,
            'upper_tail_status': 'golden-upper-tail-stability-strong',
            'transport_chain_qs': [13, 21, 34, 55],
            'pairwise_transport_chain_qs': [13, 21, 34, 55],
            'triple_transport_cocycle_chain_qs': [13, 21, 34, 55],
        },
        'transport_certified_control': {
            'theorem_status': 'transport-certified-limit-strong',
            'limit_interval_lo': 0.971092,
            'limit_interval_hi': 0.971108,
            'telescoping_tail_bound': 1.0e-6,
            'last_transport_step_bound': 1.0e-6,
            'derivative_backed_fraction': 0.8,
            'endpoint_transport_fraction': 0.8,
        },
        'pairwise_transport_control': {
            'theorem_status': 'pairwise-transport-chain-strong',
            'limit_interval_lo': 0.971094,
            'limit_interval_hi': 0.971106,
            'pair_chain_intersection_lo': 0.971095,
            'pair_chain_intersection_hi': 0.971105,
            'last_pair_interval_width': 1.0e-5,
            'telescoping_pair_tail_bound': 1.0e-6,
        },
        'triple_transport_cocycle_control': {
            'theorem_status': 'triple-transport-cocycle-strong',
            'limit_interval_lo': 0.971095,
            'limit_interval_hi': 0.971105,
            'triple_chain_intersection_lo': 0.971096,
            'triple_chain_intersection_hi': 0.971104,
            'last_triple_interval_width': 8.0e-6,
            'telescoping_triple_tail_bound': 1.0e-6,
        },
        'global_transport_potential_control': {
            'theorem_status': 'global-transport-potential-strong',
            'selected_limit_interval_lo': 0.971096,
            'selected_limit_interval_hi': 0.971104,
        },
        'tail_cauchy_potential_control': {
            'theorem_status': 'tail-cauchy-potential-strong',
            'selected_limit_interval_lo': 0.971097,
            'selected_limit_interval_hi': 0.971103,
        },
        'certified_tail_modulus_control': {
            'theorem_status': 'certified-tail-modulus-strong',
            'selected_limit_interval_lo': 0.971098,
            'selected_limit_interval_hi': 0.971102,
        },
        'rate_aware_tail_modulus_control': {
            'theorem_status': 'rate-aware-tail-modulus-strong',
            'modulus_rate_intersection_lo': 0.9710985,
            'modulus_rate_intersection_hi': 0.9711015,
        },
        'theorem_v_explicit_error_control': {
            'theorem_status': 'theorem-v-explicit-error-law-strong',
            'compatible_limit_interval_lo': 0.971091,
            'compatible_limit_interval_hi': 0.971109,
            'last_monotone_total_error_radius': 2.0e-7,
            'last_raw_total_error_radius': 2.0e-7,
        },
    })
    discharge = _identification_discharge_front_complete(upstream=[], local=['localized_compatibility_window_identifies_true_irrational_threshold'], identified=[0.971091, 0.971109])
    monkeypatch.setattr(mod, 'build_golden_theorem_v_certificate', lambda **kwargs: DummyCert(theorem_v))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: DummyCert(discharge))

    cert = mod.build_golden_threshold_identification_transport_discharge_certificate(base_K_values=[0.9, 0.95]).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-transport-discharge-lift-conditional-strong'
    assert cert['local_active_assumptions'] == []
    assert cert['transport_locked_uniqueness_certificate']['theorem_status'] == 'transport-locked-threshold-uniqueness-conditional-strong'
    assert cert['transport_locked_uniqueness_certificate']['threshold_identification_ready'] is True
    assert cert['identified_threshold_branch_interval'] is not None
    assert cert['residual_burden_summary']['status'] == 'transport-locked-identification-ready'
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['transport_locked_branch_identifies_true_threshold_object']['satisfied'] is True



def test_transport_discharge_residual_burden_becomes_critical_surface_frontier_when_upstream_remains(monkeypatch):
    theorem_v = _theorem_v_front_complete(active=['validated_function_space_continuation_transport'])
    discharge = _identification_discharge_front_complete(
        upstream=['family_chart_crossing_identifies_true_critical_parameter'],
        local=['localized_compatibility_window_identifies_true_irrational_threshold'],
        identified=[0.971091, 0.971109],
    )
    strong_uniqueness = {
        'theorem_status': 'transport-locked-threshold-uniqueness-conditional-strong',
        'threshold_identification_ready': True,
        'threshold_identification_interval': [0.971097, 0.971103],
        'threshold_identification_margin': 2.0e-6,
        'uniqueness_margin': 2.0e-6,
        'residual_identification_obstruction': None,
    }
    monkeypatch.setattr(mod, 'build_golden_theorem_v_certificate', lambda **kwargs: DummyCert(theorem_v))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: DummyCert(discharge))

    cert = mod.build_golden_threshold_identification_transport_discharge_certificate(
        base_K_values=[0.9, 0.95],
        transport_locked_uniqueness_certificate=strong_uniqueness,
    ).to_dict()
    assert cert['local_active_assumptions'] == []
    assert cert['residual_burden_summary']['status'] == 'critical-surface-threshold-promotion-frontier'



def test_transport_discharge_treats_promoted_workstream_theorem_as_upstream_available(monkeypatch):
    theorem_v = _theorem_v_front_complete(active=['unique_branch_continuation_to_true_irrational_threshold'])
    discharge = _identification_discharge_front_complete(upstream=[], local=[], identified=[0.971091, 0.971109])
    discharge['residual_burden_summary'] = {
        'status': 'critical-surface-threshold-promotion-theorem-available',
    }
    monkeypatch.setattr(mod, 'build_golden_theorem_v_certificate', lambda **kwargs: DummyCert(theorem_v))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: DummyCert(discharge))

    cert = mod.build_golden_threshold_identification_transport_discharge_certificate(base_K_values=[0.9, 0.95]).to_dict()
    assert cert['residual_burden_summary']['status'] == 'transport-locked-local-uniqueness-frontier'
