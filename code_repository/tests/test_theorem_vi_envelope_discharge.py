from __future__ import annotations

from kam_theorem_suite import proof_driver
from kam_theorem_suite import theorem_vi_envelope_discharge as mod
from kam_theorem_suite import theorem_vii_exhaustion_lift as thm7
from kam_theorem_suite import theorem_viii_reduction_lift as thm8


class DummyCert:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return dict(self._data)


def _theorem_vi_front_complete(*, active=None, local=None, statement_mode='one-variable', status='golden-theorem-vi-envelope-lift-front-complete'):
    active = [] if active is None else list(active)
    local = [] if local is None else list(local)
    assumptions = [
        {'name': 'one_variable_eta_envelope_law', 'assumed': 'one_variable_eta_envelope_law' not in local, 'source': 'test', 'note': ''},
        {'name': 'strict_golden_top_gap_theorem', 'assumed': 'strict_golden_top_gap_theorem' not in local, 'source': 'test', 'note': ''},
        {'name': 'challenger_exhaustion_beyond_current_panel', 'assumed': 'challenger_exhaustion_beyond_current_panel' not in local, 'source': 'test', 'note': ''},
    ]
    return {
        'rho': 0.618,
        'family_label': 'standard-sine',
        'statement_mode': statement_mode,
        'threshold_identification_shell': {
            'active_assumptions': list(active),
            'open_hypotheses': [],
            'theorem_status': 'golden-threshold-identification-lift-front-complete',
        },
        'proto_envelope_bridge': {
            'proto_envelope_relation': {
                'anchor_lower_minus_panel_nongolden_upper': 4.0e-05,
                'panel_nongolden_max_upper_bound': 0.97106,
            },
            'theorem_flags': {'anchor_gap_against_panel_positive': True},
        },
        'near_top_challenger_surface': {
            'near_top_relation': {
                'golden_lower_minus_most_dangerous_upper': 4.0e-05,
                'most_dangerous_threshold_upper': 0.97106,
            },
            'theorem_flags': {'panel_gap_positive': True},
        },
        'assumptions': assumptions,
        'local_active_assumptions': list(local),
        'active_assumptions': list(active) + [x for x in local if x not in active],
        'open_hypotheses': [],
        'theorem_status': status,
    }


def _discharge_front_complete(*, active=None, local=None, status='golden-threshold-identification-discharge-lift-front-complete'):
    active = [] if active is None else list(active)
    local = [] if local is None else list(local)
    return {
        'rho': 0.618,
        'family_label': 'standard-sine',
        'local_active_assumptions': list(local),
        'active_assumptions': list(active),
        'bridge_native_tail_witness_source': 'golden_limit_bridge.native_late_coherent_suffix_witness',
        'bridge_native_tail_witness_status': 'native-late-coherent-suffix-strong',
        'discharged_bridge_native_tail_witness_interval': [0.97109, 0.97111],
        'discharged_bridge_native_tail_witness_width': 2.0e-05,
        'open_hypotheses': [],
        'theorem_status': status,
    }


def test_theorem_vi_envelope_discharge_reduces_upstream_burden(monkeypatch):
    theorem_vi = _theorem_vi_front_complete(
        active=[
            'validated_true_renormalization_fixed_point_package',
            'golden_stable_manifold_is_true_critical_surface',
            'family_chart_crossing_identifies_true_critical_parameter',
            'localized_compatibility_window_identifies_true_irrational_threshold',
            'obstruction_excludes_analytic_circle',
        ],
        local=['one_variable_eta_envelope_law', 'strict_golden_top_gap_theorem'],
    )
    discharge = _discharge_front_complete(
        active=['localized_compatibility_window_identifies_true_irrational_threshold', 'obstruction_excludes_analytic_circle'],
        local=['localized_compatibility_window_identifies_true_irrational_threshold'],
    )
    monkeypatch.setattr(mod, 'build_golden_theorem_vi_certificate', lambda **kwargs: DummyCert(theorem_vi))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: DummyCert(discharge))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate', lambda **kwargs: DummyCert(discharge))

    cert = mod.build_golden_theorem_vi_envelope_discharge_lift_certificate(base_K_values=[0.9, 0.95]).to_dict()
    assert cert['upstream_active_assumptions'] == ['localized_compatibility_window_identifies_true_irrational_threshold', 'obstruction_excludes_analytic_circle']
    assert cert['local_active_assumptions'] == ['one_variable_eta_envelope_law', 'strict_golden_top_gap_theorem']
    names = {row['name']: row for row in cert['hypotheses']}
    assert names['identification_discharge_reduces_upstream_burden']['satisfied'] is True
    assert names['discharged_identified_branch_witness_available']['satisfied'] is True
    assert names['discharged_witness_width_compatible_with_current_top_gap_scale']['satisfied'] is True
    assert names['discharged_witness_sits_above_current_near_top_challenger_upper']['satisfied'] is True
    assert cert['discharged_identified_branch_witness_interval'] == [0.97109, 0.97111]
    assert abs(cert['discharged_identified_branch_witness_width'] - 2.0e-05) < 1.0e-12
    assert abs(cert['current_top_gap_scale'] - 4.0e-05) < 1.0e-12
    assert abs(cert['current_most_dangerous_challenger_upper'] - 0.97106) < 1.0e-12
    assert abs(cert['discharged_witness_width_vs_current_top_gap_margin'] - 2.0e-05) < 1.0e-12
    assert abs(cert['discharged_witness_lower_vs_current_near_top_challenger_upper_margin'] - 3.0e-05) < 1.0e-12
    assert abs(cert['discharged_witness_geometry_min_margin'] - 2.0e-05) < 1.0e-12
    assert cert['discharged_witness_geometry_status'] == 'discharged-witness-geometry-strong'
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-discharge-lift-front-complete'


def test_theorem_vi_envelope_discharge_conditional_strong(monkeypatch):
    theorem_vi = _theorem_vi_front_complete(active=[], local=[], statement_mode='one-variable', status='golden-theorem-vi-envelope-lift-conditional-one-variable-strong')
    discharge = _discharge_front_complete(active=[], local=[], status='golden-threshold-identification-discharge-lift-conditional-strong')
    monkeypatch.setattr(mod, 'build_golden_theorem_vi_certificate', lambda **kwargs: DummyCert(theorem_vi))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: DummyCert(discharge))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate', lambda **kwargs: DummyCert(discharge))

    cert = mod.build_golden_theorem_vi_envelope_discharge_lift_certificate(base_K_values=[0.9, 0.95]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-discharge-lift-conditional-one-variable-strong'
    assert cert['active_assumptions'] == []
    assert cert['discharged_identified_branch_witness_interval'] == [0.97109, 0.97111]
    assert cert['discharged_witness_geometry_status'] == 'discharged-witness-geometry-strong'


def test_theorem_vii_accepts_theorem_vi_envelope_discharge_certificate(monkeypatch):
    discharge_vi = {
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-front-complete',
        'active_assumptions': ['localized_compatibility_window_identifies_true_irrational_threshold'],
    }

    monkeypatch.setattr(thm7, 'build_class_exhaustion_screen', lambda *args, **kwargs: DummyCert({'classes': [{'label': 'silver'}]}))
    monkeypatch.setattr(thm7, 'build_adaptive_class_exhaustion_search', lambda *args, **kwargs: DummyCert({'rounds': [1]}))
    monkeypatch.setattr(thm7, 'build_evidence_weighted_class_exhaustion_search', lambda *args, **kwargs: DummyCert({'rounds': [1]}))
    monkeypatch.setattr(thm7, 'build_termination_aware_class_exhaustion_search', lambda *args, **kwargs: DummyCert({'deferred_classes': [], 'retired_classes': [], 'strongest_active_upper_bound': 0.5}))

    cert = thm7.build_golden_theorem_vii_exhaustion_lift_certificate(
        base_K_values=[0.9, 0.95],
        theorem_vi_envelope_discharge_certificate=discharge_vi,
        reference_lower_bound=0.9,
        reference_crossing_center=0.925,
    ).to_dict()
    assert cert['theorem_vi_shell']['theorem_status'] == 'golden-theorem-vi-envelope-discharge-lift-front-complete'


def test_theorem_viii_accepts_theorem_vi_envelope_discharge_certificate():
    discharge_vi = {
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-front-complete',
        'active_assumptions': ['localized_compatibility_window_identifies_true_irrational_threshold'],
    }
    cert = thm8.build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.9, 0.95],
        theorem_iv_certificate={'open_hypotheses': [], 'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete', 'active_assumptions': []},
        theorem_v_certificate={'open_hypotheses': [], 'theorem_status': 'golden-theorem-v-transport-lift-front-complete', 'active_assumptions': []},
        threshold_identification_discharge_certificate={'open_hypotheses': [], 'theorem_status': 'golden-threshold-identification-discharge-lift-front-complete', 'active_assumptions': []},
        theorem_vi_envelope_discharge_certificate=discharge_vi,
        theorem_vii_certificate={'open_hypotheses': [], 'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete', 'active_assumptions': []},
    ).to_dict()
    assert cert['theorem_vi_shell']['theorem_status'] == 'golden-theorem-vi-envelope-discharge-lift-front-complete'


def test_theorem_vi_envelope_discharge_driver_report(monkeypatch):
    theorem_vi = _theorem_vi_front_complete(active=['validated_true_renormalization_fixed_point_package', 'localized_compatibility_window_identifies_true_irrational_threshold'], local=['one_variable_eta_envelope_law'])
    discharge = _discharge_front_complete(active=['localized_compatibility_window_identifies_true_irrational_threshold'], local=['localized_compatibility_window_identifies_true_irrational_threshold'])
    monkeypatch.setattr(mod, 'build_golden_theorem_vi_certificate', lambda **kwargs: DummyCert(theorem_vi))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: DummyCert(discharge))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate', lambda **kwargs: DummyCert(discharge))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_envelope_discharge_lift_certificate', mod.build_golden_theorem_vi_envelope_discharge_lift_certificate)
    data = proof_driver.build_golden_theorem_vi_envelope_discharge_lift_report(base_K_values=[0.9, 0.95])
    assert data['theorem_status'] == 'golden-theorem-vi-envelope-discharge-lift-front-complete'


def test_theorem_vi_envelope_discharge_surfaces_global_theorem_burden_only_when_local_geometry_is_strong(monkeypatch):
    theorem_vi = _theorem_vi_front_complete(
        active=['validated_true_renormalization_fixed_point_package'],
        local=['one_variable_eta_envelope_law', 'strict_golden_top_gap_theorem'],
    )
    discharge = _discharge_front_complete(
        active=['validated_true_renormalization_fixed_point_package'],
        local=[],
    )
    monkeypatch.setattr(mod, 'build_golden_theorem_vi_certificate', lambda **kwargs: DummyCert(theorem_vi))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: DummyCert(discharge))
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate', lambda **kwargs: DummyCert(discharge))

    cert = mod.build_golden_theorem_vi_envelope_discharge_lift_certificate(base_K_values=[0.9, 0.95]).to_dict()
    assert cert['current_local_top_gap_certificate']['status'] == 'current-local-top-gap-strong'
    assert cert['residual_burden_summary']['status'] == 'global-theorem-burden-only'
    assert cert['statement_mode_diagnostics']['current_local_geometry_supports_top_gap_promotion'] is True



def test_discharge_shell_promotes_strict_top_gap_when_witness_geometry_is_strong() -> None:
    from kam_theorem_suite.theorem_vi_envelope_discharge import build_golden_theorem_vi_envelope_discharge_lift_certificate

    theorem_vi_certificate = {
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'statement_mode': 'one-variable',
        'statement_mode_diagnostics': {
            'candidate_mode': 'one-variable',
            'mode_lock_status': 'one-variable-supported',
            'status': 'statement-mode-certificate-one-variable-supported',
        },
        'open_hypotheses': [],
        'local_active_assumptions': [
            'one_variable_eta_envelope_law',
            'strict_golden_top_gap_theorem',
            'challenger_exhaustion_beyond_current_panel',
        ],
        'assumptions': [
            {'name': 'one_variable_eta_envelope_law', 'assumed': False, 'source': 'fixture', 'note': 'fixture'},
            {'name': 'strict_golden_top_gap_theorem', 'assumed': False, 'source': 'fixture', 'note': 'fixture'},
            {'name': 'challenger_exhaustion_beyond_current_panel', 'assumed': False, 'source': 'fixture', 'note': 'fixture'},
        ],
        'near_top_challenger_surface': {
            'theorem_flags': {
                'all_threshold_bounded_challengers_dominated': True,
                'no_undecided_challengers': True,
            },
            'near_top_relation': {
                'golden_lower_minus_most_dangerous_upper': 0.02,
                'most_dangerous_threshold_upper': 0.971,
            },
        },
        'proto_envelope_bridge': {
            'proto_envelope_relation': {
                'anchor_lower_minus_panel_nongolden_upper': 0.02,
                'panel_nongolden_max_upper_bound': 0.971,
            },
        },
    }
    discharge_certificate = {
        'theorem_status': 'golden-theorem-ii-to-v-identification-transport-discharge-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'discharged_bridge_native_tail_witness_interval': [0.97103, 0.971035],
        'discharged_bridge_native_tail_witness_width': 5.0e-06,
        'bridge_native_tail_witness_source': 'fixture',
        'bridge_native_tail_witness_status': 'strong',
    }

    cert = build_golden_theorem_vi_envelope_discharge_lift_certificate(
        base_K_values=[0.3],
        theorem_vi_certificate=theorem_vi_certificate,
        threshold_identification_transport_discharge_certificate=discharge_certificate,
    ).to_dict()
    assert cert['strict_golden_top_gap_certificate']['screened_panel_strict_top_gap_status'] == 'strict-golden-top-gap-discharged-screened-panel-strong'
    assert cert['strict_golden_top_gap_certificate']['local_top_gap_promoted_beyond_raw_gap'] is True
    assert 'strict_golden_top_gap_theorem' not in cert['local_active_assumptions']
    assert 'challenger_exhaustion_beyond_current_panel' in cert['local_active_assumptions']
