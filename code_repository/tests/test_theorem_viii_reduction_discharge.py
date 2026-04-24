from __future__ import annotations

from kam_theorem_suite import proof_driver
from kam_theorem_suite.theorem_viii_reduction_discharge import (
    build_golden_theorem_viii_reduction_discharge_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def _baseline_shell(*, active=None, local=None, statement_mode='one-variable', status='golden-theorem-viii-reduction-lift-front-complete'):
    active = [] if active is None else list(active)
    local = [] if local is None else list(local)
    assumptions = [
        {'name': 'final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality', 'assumed': 'final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality' not in local, 'source': 'test', 'note': ''},
        {'name': 'gl2z_orbit_uniqueness_and_normalization_closed', 'assumed': 'gl2z_orbit_uniqueness_and_normalization_closed' not in local, 'source': 'test', 'note': ''},
        {'name': 'final_universality_class_matches_reduction_statement', 'assumed': 'final_universality_class_matches_reduction_statement' not in local, 'source': 'test', 'note': ''},
    ]
    return {
        'rho': 0.618,
        'family_label': 'standard-sine',
        'statement_mode': statement_mode,
        'assumptions': assumptions,
        'upstream_active_assumptions': list(active),
        'local_active_assumptions': list(local),
        'active_assumptions': list(active) + [x for x in local if x not in active],
        'open_hypotheses': [],
        'theorem_status': status,
    }


def _vii_discharge_shell(*, active=None, local=None, status='golden-theorem-vii-exhaustion-discharge-lift-front-complete', statement_mode='one-variable'):
    active = [] if active is None else list(active)
    local = [] if local is None else list(local)
    return {
        'theorem_status': status,
        'open_hypotheses': [],
        'active_assumptions': list(active),
        'local_active_assumptions': list(local),
        'reference_lower_bound': 0.97109,
        'current_near_top_exhaustion_upper_bound': 0.97106,
        'current_near_top_exhaustion_margin': 3.0e-05,
        'current_near_top_exhaustion_pending_count': 0,
        'current_near_top_exhaustion_source': 'theorem_vi_discharge.current_most_dangerous_challenger_upper + theorem_vii_shell.termination_aware_search_report',
        'current_near_top_exhaustion_status': 'near-top-exhaustion-strong',
        'theorem_vii_shell': {
            'termination_aware_search_report': {
                'active_count': 0,
                'deferred_count': 0,
                'undecided_count': 0,
                'overlapping_count': 0,
            },
        },
        'theorem_vi_discharge_shell': {
            'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-front-complete',
            'statement_mode': statement_mode,
            'open_hypotheses': [],
            'active_assumptions': list(active),
            'threshold_identification_discharge_shell': {
                'theorem_status': 'golden-threshold-identification-discharge-lift-front-complete',
                'open_hypotheses': [],
                'active_assumptions': ['localized_compatibility_window_identifies_true_irrational_threshold'],
                'local_active_assumptions': ['localized_compatibility_window_identifies_true_irrational_threshold'],
                'bridge_native_tail_witness_source': 'golden_limit_bridge.native_late_coherent_suffix_witness',
                'bridge_native_tail_witness_status': 'native-late-coherent-suffix-strong',
                'discharged_bridge_native_tail_witness_interval': [0.97109, 0.97111],
                'discharged_bridge_native_tail_witness_width': 2.0e-05,
                'overlap_window': [0.971085, 0.971125],
                'overlap_width': 4.0e-05,
            },
            'theorem_vi_shell': {
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
            },
            'discharged_identified_branch_witness_interval': [0.97109, 0.97111],
            'discharged_identified_branch_witness_width': 2.0e-05,
            'discharged_identified_branch_witness_source': 'golden_limit_bridge.native_late_coherent_suffix_witness',
            'discharged_identified_branch_witness_status': 'native-late-coherent-suffix-strong',
            'current_top_gap_scale': 4.0e-05,
            'current_most_dangerous_challenger_upper': 0.97106,
            'discharged_witness_width_vs_current_top_gap_margin': 2.0e-05,
            'discharged_witness_lower_vs_current_near_top_challenger_upper_margin': 3.0e-05,
            'discharged_witness_geometry_min_margin': 2.0e-05,
            'discharged_witness_geometry_status': 'discharged-witness-geometry-strong',
        },
    }


def test_theorem_viii_discharge_reduces_upstream_burden():
    baseline = _baseline_shell(
        active=[
            'validated_true_renormalization_fixed_point_package',
            'golden_stable_manifold_is_true_critical_surface',
            'family_chart_crossing_identifies_true_critical_parameter',
            'localized_compatibility_window_identifies_true_irrational_threshold',
            'strict_golden_top_gap_theorem',
            'finite_screened_panel_is_globally_complete',
        ],
        local=['final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality'],
    )
    discharge_viii = _baseline_shell(
        active=[
            'localized_compatibility_window_identifies_true_irrational_threshold',
            'strict_golden_top_gap_theorem',
            'finite_screened_panel_is_globally_complete',
        ],
        local=['final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality'],
    )
    vii_discharge = _vii_discharge_shell(active=['localized_compatibility_window_identifies_true_irrational_threshold', 'strict_golden_top_gap_theorem', 'finite_screened_panel_is_globally_complete'])

    cert = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.9, 0.95],
        baseline_theorem_viii_certificate=baseline,
        theorem_viii_certificate=discharge_viii,
        theorem_vii_exhaustion_discharge_certificate=vii_discharge,
    ).to_dict()

    assert cert['theorem_status'] == 'golden-theorem-viii-reduction-discharge-lift-front-complete'
    assert cert['residual_non_global_hinges'] == ['localized_compatibility_window_identifies_true_irrational_threshold']
    assert cert['residual_global_active_assumptions'] == [
        'final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality',
        'finite_screened_panel_is_globally_complete',
        'strict_golden_top_gap_theorem',
    ]
    names = {row['name']: row for row in cert['hypotheses']}
    assert names['reduction_upstream_burden_reduced_by_discharge']['satisfied'] is True
    assert names['discharged_identified_branch_witness_available_for_reduction']['satisfied'] is True
    assert names['discharged_witness_narrower_than_identification_overlap_for_reduction']['satisfied'] is True
    assert names['discharged_witness_compatible_with_current_top_gap_scale_for_reduction']['satisfied'] is True
    assert cert['discharged_identified_branch_witness_interval'] == [0.97109, 0.97111]
    assert abs(cert['discharged_identified_branch_witness_width'] - 2.0e-05) < 1.0e-12
    assert abs(cert['inherited_current_top_gap_scale'] - 4.0e-05) < 1.0e-12
    assert abs(cert['inherited_current_most_dangerous_challenger_upper'] - 0.97106) < 1.0e-12
    assert abs(cert['inherited_discharged_witness_width_vs_current_top_gap_margin'] - 2.0e-05) < 1.0e-12
    assert abs(cert['inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin'] - 3.0e-05) < 1.0e-12
    assert abs(cert['inherited_discharged_witness_geometry_min_margin'] - 2.0e-05) < 1.0e-12
    assert cert['inherited_discharged_witness_geometry_status'] == 'discharged-witness-geometry-strong'
    assert abs(cert['inherited_current_near_top_exhaustion_upper_bound'] - 0.97106) < 1.0e-12
    assert abs(cert['inherited_current_near_top_exhaustion_margin'] - 3.0e-05) < 1.0e-12
    assert cert['inherited_current_near_top_exhaustion_pending_count'] == 0
    assert cert['inherited_current_near_top_exhaustion_status'] == 'near-top-exhaustion-strong'
    assert abs(cert['current_reduction_geometry_witness_vs_overlap_margin'] - 2.0e-05) < 1.0e-12
    assert abs(cert['current_reduction_geometry_top_gap_scale'] - 4.0e-05) < 1.0e-12
    assert abs(cert['current_reduction_geometry_challenger_upper_bound'] - 0.97106) < 1.0e-12
    assert abs(cert['current_reduction_geometry_exhaustion_upper_bound'] - 0.97106) < 1.0e-12
    assert abs(cert['current_reduction_geometry_witness_width_vs_top_gap_margin'] - 2.0e-05) < 1.0e-12
    assert abs(cert['current_reduction_geometry_witness_lower_vs_challenger_upper_margin'] - 3.0e-05) < 1.0e-12
    assert cert['current_reduction_geometry_pending_count'] == 0
    assert abs(cert['current_reduction_geometry_min_margin'] - 2.0e-05) < 1.0e-12
    assert cert['current_reduction_geometry_status'] == 'current-reduction-geometry-strong'
    assert names['inherited_near_top_exhaustion_summary_available_for_reduction']['satisfied'] is True
    assert names['inherited_near_top_exhaustion_summary_strong_for_reduction']['satisfied'] is True
    assert names['current_reduction_geometry_summary_available_for_reduction']['satisfied'] is True
    assert names['current_reduction_geometry_summary_strong_for_reduction']['satisfied'] is True


def test_theorem_viii_discharge_conditional_strong_two_variable():
    baseline = _baseline_shell(status='golden-theorem-viii-reduction-lift-conditional-two-variable-strong', statement_mode='two-variable')
    discharge_viii = _baseline_shell(status='golden-theorem-viii-reduction-lift-conditional-two-variable-strong', statement_mode='two-variable')
    vii_discharge = {
        'theorem_status': 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'reference_lower_bound': 0.97109,
        'current_near_top_exhaustion_upper_bound': 0.97106,
        'current_near_top_exhaustion_margin': 3.0e-05,
        'current_near_top_exhaustion_pending_count': 0,
        'current_near_top_exhaustion_source': 'theorem_vi_discharge.current_most_dangerous_challenger_upper + theorem_vii_shell.termination_aware_search_report',
        'current_near_top_exhaustion_status': 'near-top-exhaustion-strong',
        'theorem_vi_discharge_shell': {
            'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-conditional-two-variable-strong',
            'statement_mode': 'two-variable',
            'open_hypotheses': [],
            'active_assumptions': [],
            'threshold_identification_discharge_shell': {
                'theorem_status': 'golden-threshold-identification-discharge-lift-conditional-strong',
                'open_hypotheses': [],
                'active_assumptions': [],
                'local_active_assumptions': [],
                'bridge_native_tail_witness_source': 'golden_limit_bridge.native_late_coherent_suffix_witness',
                'bridge_native_tail_witness_status': 'native-late-coherent-suffix-strong',
                'discharged_bridge_native_tail_witness_interval': [0.97109, 0.97111],
                'discharged_bridge_native_tail_witness_width': 2.0e-05,
                'overlap_window': [0.971085, 0.971125],
                'overlap_width': 4.0e-05,
            },
            'theorem_vi_shell': {
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
            },
            'discharged_identified_branch_witness_interval': [0.97109, 0.97111],
            'discharged_identified_branch_witness_width': 2.0e-05,
            'discharged_identified_branch_witness_source': 'golden_limit_bridge.native_late_coherent_suffix_witness',
            'discharged_identified_branch_witness_status': 'native-late-coherent-suffix-strong',
            'current_top_gap_scale': 4.0e-05,
            'current_most_dangerous_challenger_upper': 0.97106,
            'discharged_witness_width_vs_current_top_gap_margin': 2.0e-05,
            'discharged_witness_lower_vs_current_near_top_challenger_upper_margin': 3.0e-05,
            'discharged_witness_geometry_min_margin': 2.0e-05,
            'discharged_witness_geometry_status': 'discharged-witness-geometry-strong',
        },
    }

    cert = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.9, 0.95],
        baseline_theorem_viii_certificate=baseline,
        theorem_viii_certificate=discharge_viii,
        theorem_vii_exhaustion_discharge_certificate=vii_discharge,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-viii-reduction-discharge-lift-conditional-two-variable-strong'
    assert cert['residual_global_active_assumptions'] == []
    assert cert['residual_non_global_hinges'] == []
    assert cert['discharged_identified_branch_witness_interval'] == [0.97109, 0.97111]
    assert cert['inherited_discharged_witness_geometry_status'] == 'discharged-witness-geometry-strong'
    assert cert['inherited_current_near_top_exhaustion_status'] == 'near-top-exhaustion-strong'
    assert cert['current_reduction_geometry_status'] == 'current-reduction-geometry-strong'


def test_theorem_viii_discharge_infers_nested_shells_from_vii_discharge():
    baseline = _baseline_shell(active=['validated_function_space_continuation_transport'])
    discharge_viii = _baseline_shell(active=['localized_compatibility_window_identifies_true_irrational_threshold'])
    vii_discharge = _vii_discharge_shell(active=['localized_compatibility_window_identifies_true_irrational_threshold'], statement_mode='two-variable')

    cert = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.9, 0.95],
        baseline_theorem_viii_certificate=baseline,
        theorem_viii_certificate=discharge_viii,
        theorem_vii_exhaustion_discharge_certificate=vii_discharge,
    ).to_dict()
    assert cert['theorem_vi_discharge_shell']['theorem_status'] == 'golden-theorem-vi-envelope-discharge-lift-front-complete'
    assert cert['threshold_identification_discharge_shell']['theorem_status'] == 'golden-threshold-identification-discharge-lift-front-complete'
    assert cert['discharged_identified_branch_witness_interval'] == [0.97109, 0.97111]
    assert cert['inherited_discharged_witness_geometry_status'] == 'discharged-witness-geometry-strong'
    assert cert['inherited_current_near_top_exhaustion_status'] == 'near-top-exhaustion-strong'
    assert cert['statement_mode'] == 'one-variable'


def test_driver_exposes_uniform_theorem_viii_discharge_current_reduction_geometry_summary(monkeypatch):
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_theorem_viii_reduction_discharge_lift_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-viii-reduction-discharge-lift-front-complete',
        'statement_mode': 'one-variable',
        'residual_global_active_assumptions': ['strict_golden_top_gap_theorem'],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'theorem-viii discharge lift',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    }))
    monkeypatch.setattr(pd, 'build_golden_theorem_viii_discharge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-viii-reduction-discharge-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'residual_global_active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'theorem-viii discharge theorem',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    }))

    lift_report = proof_driver.build_golden_theorem_viii_reduction_discharge_lift_report(base_K_values=[0.3])
    theorem_report = proof_driver.build_golden_theorem_viii_discharge_report(base_K_values=[0.3])
    assert lift_report['theorem_status'] == 'golden-theorem-viii-reduction-discharge-lift-front-complete'
    assert theorem_report['theorem_status'] == 'golden-theorem-viii-reduction-discharge-lift-conditional-one-variable-strong'
    lift_summary = lift_report['current_reduction_geometry_summary']
    theorem_summary = theorem_report['current_reduction_geometry_summary']
    assert lift_summary['available'] is True
    assert lift_summary['status'] == 'current-reduction-geometry-strong'
    assert abs(lift_summary['minimum_certified_margin'] - 2.0e-05) < 1.0e-12
    assert lift_summary['report_kind'] == 'theorem-viii-reduction-discharge-lift-report'
    assert lift_summary['discharge_aware'] is True
    assert theorem_summary['available'] is True
    assert theorem_summary['status'] == 'current-reduction-geometry-strong'
    assert abs(theorem_summary['minimum_certified_margin'] - 2.0e-05) < 1.0e-12
    assert theorem_summary['report_kind'] == 'theorem-viii-discharge-report'
    assert theorem_summary['discharge_aware'] is True
    extracted = proof_driver.extract_theorem_viii_current_reduction_geometry_summary(lift_report)
    assert extracted['status'] == 'current-reduction-geometry-strong'
    assert extracted['discharge_aware'] is True


def test_theorem_viii_discharge_reuses_baseline_upstream_shells_when_rebuilding(monkeypatch):
    import kam_theorem_suite.theorem_viii_reduction_discharge as tviiid

    baseline = _baseline_shell()
    baseline.update({
        'theorem_iii_shell': {'theorem_status': 'golden-theorem-iii-final-strong', 'certified_below_threshold_interval': [0.9, 0.95]},
        'theorem_iv_shell': {'theorem_status': 'golden-theorem-iv-final-strong'},
        'theorem_v_shell': {'theorem_status': 'golden-theorem-v-compressed-contract-strong', 'theorem_target_interval': [0.91, 0.92], 'gap_preservation_margin': 1.0e-4},
        'workstream_shell': {'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete', 'open_hypotheses': [], 'active_assumptions': []},
    })
    vii_discharge = _vii_discharge_shell()

    captured = {}

    def _fake_build_viii(**kwargs):
        captured.update(kwargs)
        return _Dummy({
            **baseline,
            'theorem_status': 'golden-theorem-viii-reduction-lift-front-complete',
            'upstream_active_assumptions': [],
            'local_active_assumptions': [],
            'active_assumptions': [],
            'open_hypotheses': [],
        })

    monkeypatch.setattr(tviiid, 'build_golden_theorem_viii_certificate', _fake_build_viii)
    monkeypatch.setattr(tviiid, 'build_golden_theorem_i_ii_workstream_lift_certificate', lambda **kwargs: _Dummy(baseline['workstream_shell']))

    cert = tviiid.build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.9, 0.95],
        baseline_theorem_viii_certificate=baseline,
        theorem_vii_exhaustion_discharge_certificate=vii_discharge,
    ).to_dict()

    assert captured['theorem_iii_certificate'] == baseline['theorem_iii_shell']
    assert captured['theorem_iv_certificate'] == baseline['theorem_iv_shell']
    assert captured['theorem_v_certificate'] == baseline['theorem_v_shell']
    assert captured['theorem_i_ii_workstream_certificate'] == baseline['workstream_shell']
    assert cert['theorem_iii_final_certified'] is True
    assert cert['theorem_iv_final_certified'] is True
    assert cert['theorem_v_final_certified'] is True


def test_theorem_viii_lift_infers_iv_and_v_from_vi_or_vii_when_identification_is_discharge_shaped(monkeypatch):
    import kam_theorem_suite.theorem_viii_reduction_lift as tviiil

    vii_discharge = _vii_discharge_shell()
    vii_discharge['theorem_vi_discharge_shell']['theorem_vi_shell']['threshold_identification_shell'] = {
        'theorem_status': 'golden-threshold-identification-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }
    vii_discharge['theorem_vi_discharge_shell']['theorem_vi_shell']['theorem_iv_shell'] = {
        'theorem_status': 'golden-theorem-iv-final-strong',
        'active_assumptions': [],
        'open_hypotheses': [],
    }
    vii_discharge['theorem_vi_discharge_shell']['theorem_vi_shell']['theorem_v_shell'] = {
        'theorem_status': 'golden-theorem-v-compressed-contract-strong',
        'active_assumptions': [],
        'open_hypotheses': [],
        'theorem_target_interval': [0.91, 0.92],
        'gap_preservation_margin': 1.0e-4,
    }

    called = {'iv': 0, 'v': 0}

    def _fail_iv(**kwargs):
        called['iv'] += 1
        raise AssertionError('should not rebuild theorem iv')

    def _fail_v(**kwargs):
        called['v'] += 1
        raise AssertionError('should not rebuild theorem v')

    monkeypatch.setattr(tviiil, 'build_golden_theorem_iv_certificate', _fail_iv)
    monkeypatch.setattr(tviiil, 'build_golden_theorem_v_certificate', _fail_v)

    cert = tviiil.build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.9, 0.95],
        theorem_vii_exhaustion_discharge_certificate=vii_discharge,
    ).to_dict()

    assert cert['theorem_iv_shell']['theorem_status'] == 'golden-theorem-iv-final-strong'
    assert cert['theorem_v_shell']['theorem_status'] == 'golden-theorem-v-compressed-contract-strong'
    assert called == {'iv': 0, 'v': 0}
