from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_golden_theorem_viii_reduction_lift_report,
    build_golden_theorem_viii_report,
    extract_theorem_viii_current_reduction_geometry_summary,
)
from kam_theorem_suite.theorem_viii_reduction_lift import (
    build_golden_theorem_viii_reduction_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload
    def to_dict(self):
        return dict(self._payload)


def test_theorem_viii_front_complete_when_all_shells_are_packaged(monkeypatch) -> None:
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
    monkeypatch.setattr(tviiil, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['validated_true_renormalization_fixed_point_package'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': ['strict_golden_top_gap_theorem'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['finite_screened_panel_is_globally_complete'],
    }))

    cert = build_golden_theorem_viii_reduction_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-viii-reduction-lift-front-complete'
    assert cert['statement_mode'] == 'one-variable'
    assert cert['open_hypotheses'] == []
    assert 'strict_golden_top_gap_theorem' in cert['upstream_active_assumptions']
    assert 'final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality' in cert['local_active_assumptions']





def test_theorem_viii_lift_exposes_native_current_reduction_geometry_summary() -> None:
    cert = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.97109],
        theorem_iv_certificate={
            'theorem_status': 'golden-analytic-incompatibility-lift-front-only',
            'open_hypotheses': [],
            'active_assumptions': ['obstruction_implies_no_analytic_circle'],
        },
        theorem_v_certificate={
            'theorem_status': 'golden-theorem-v-transport-lift-front-only',
            'open_hypotheses': [],
            'active_assumptions': ['validated_function_space_continuation_transport'],
        },
        threshold_identification_discharge_certificate={
            'theorem_status': 'golden-threshold-identification-discharge-lift-front-complete',
            'open_hypotheses': [],
            'active_assumptions': ['validated_true_renormalization_fixed_point_package'],
            'overlap_window': [0.97108, 0.97112],
            'overlap_width': 4.0e-05,
            'discharged_bridge_native_tail_witness_interval': [0.97109, 0.97111],
            'discharged_bridge_native_tail_witness_width': 2.0e-05,
            'bridge_native_tail_witness_source': 'threshold-identification discharge',
            'bridge_native_tail_witness_status': 'bridge-native-tail-witness-strong',
        },
        theorem_vi_envelope_discharge_certificate={
            'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-front-complete',
            'statement_mode': 'one-variable',
            'open_hypotheses': [],
            'active_assumptions': ['strict_golden_top_gap_theorem'],
            'current_top_gap_scale': 4.0e-05,
            'current_most_dangerous_challenger_upper': 0.97106,
        },
        theorem_vii_exhaustion_discharge_certificate={
            'theorem_status': 'golden-theorem-vii-exhaustion-discharge-lift-front-complete',
            'open_hypotheses': [],
            'active_assumptions': ['finite_screened_panel_is_globally_complete'],
            'reference_lower_bound': 0.97109,
            'current_near_top_exhaustion_upper_bound': 0.97106,
            'current_near_top_exhaustion_margin': 3.0e-05,
            'current_near_top_exhaustion_pending_count': 0,
            'current_near_top_exhaustion_source': 'theorem-vii discharge',
            'current_near_top_exhaustion_status': 'near-top-exhaustion-strong',
        },
    ).to_dict()

    assert cert['theorem_status'] == 'golden-theorem-viii-reduction-lift-front-complete'
    assert abs(cert['current_reduction_geometry_witness_vs_overlap_margin'] - 2.0e-05) < 1.0e-12
    assert abs(cert['current_reduction_geometry_top_gap_scale'] - 4.0e-05) < 1.0e-12
    assert abs(cert['current_reduction_geometry_challenger_upper_bound'] - 0.97106) < 1.0e-12
    assert abs(cert['current_reduction_geometry_exhaustion_upper_bound'] - 0.97106) < 1.0e-12
    assert abs(cert['current_reduction_geometry_witness_width_vs_top_gap_margin'] - 2.0e-05) < 1.0e-12
    assert abs(cert['current_reduction_geometry_witness_lower_vs_challenger_upper_margin'] - 3.0e-05) < 1.0e-12
    assert cert['current_reduction_geometry_pending_count'] == 0
    assert abs(cert['current_reduction_geometry_min_margin'] - 2.0e-05) < 1.0e-12
    assert cert['current_reduction_geometry_status'] == 'current-reduction-geometry-strong'
    names = {row['name']: row for row in cert['hypotheses']}
    assert names['current_reduction_geometry_summary_available']['satisfied'] is True
    assert names['current_reduction_geometry_summary_strong']['satisfied'] is True

def test_theorem_viii_one_variable_conditional_strong_when_all_assumptions_are_toggled_on(monkeypatch) -> None:
    import kam_theorem_suite.theorem_viii_reduction_lift as tviiil

    monkeypatch.setattr(tviiil, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_v_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-v-transport-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))

    cert = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.3],
        assume_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality=True,
        assume_gl2z_orbit_uniqueness_and_normalization_closed=True,
        assume_final_universality_class_matches_reduction_statement=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong'
    assert cert['active_assumptions'] == []



def test_theorem_viii_stays_partial_when_statement_mode_or_shells_remain_open(monkeypatch) -> None:
    import kam_theorem_suite.theorem_viii_reduction_lift as tviiil

    monkeypatch.setattr(tviiil, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-conditional-partial',
        'open_hypotheses': ['strong_nonexistence_front'],
        'active_assumptions': ['obstruction_implies_no_analytic_circle'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_v_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-v-transport-lift-conditional-partial',
        'open_hypotheses': ['global_transport_potential_control'],
        'active_assumptions': ['validated_function_space_continuation_transport'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-conditional-partial',
        'open_hypotheses': ['theorem_iv_front_complete'],
        'active_assumptions': ['validated_true_renormalization_fixed_point_package'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'statement_mode': 'unresolved',
        'open_hypotheses': [],
        'active_assumptions': ['one_variable_eta_envelope_law'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-partial',
        'open_hypotheses': ['theorem_vi_front_complete'],
        'active_assumptions': ['finite_screened_panel_is_globally_complete'],
    }))

    cert = build_golden_theorem_viii_reduction_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-viii-reduction-lift-conditional-partial'
    assert 'theorem_iv_front_complete' in cert['open_hypotheses']
    assert 'theorem_v_front_complete' in cert['open_hypotheses']
    assert 'threshold_identification_front_complete' in cert['open_hypotheses']
    assert 'theorem_vi_statement_mode_resolved' in cert['open_hypotheses']
    assert 'theorem_vii_front_complete' in cert['open_hypotheses']



def test_driver_exposes_uniform_theorem_viii_current_reduction_geometry_summary(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_theorem_viii_reduction_lift_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-viii-reduction-lift-front-complete',
        'statement_mode': 'one-variable',
        'active_assumptions': ['final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality'],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'theorem-viii lift',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    }))
    monkeypatch.setattr(pd, 'build_golden_theorem_viii_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'theorem-viii theorem',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    }))

    lift_report = build_golden_theorem_viii_reduction_lift_report(base_K_values=[0.3])
    theorem_report = build_golden_theorem_viii_report(base_K_values=[0.3])
    assert lift_report['theorem_status'] == 'golden-theorem-viii-reduction-lift-front-complete'
    assert theorem_report['theorem_status'] == 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong'
    lift_summary = lift_report['current_reduction_geometry_summary']
    theorem_summary = theorem_report['current_reduction_geometry_summary']
    assert lift_summary['available'] is True
    assert lift_summary['status'] == 'current-reduction-geometry-strong'
    assert abs(lift_summary['minimum_certified_margin'] - 2.0e-05) < 1.0e-12
    assert lift_summary['report_kind'] == 'theorem-viii-reduction-lift-report'
    assert lift_summary['discharge_aware'] is False
    assert theorem_summary['available'] is True
    assert theorem_summary['status'] == 'current-reduction-geometry-strong'
    assert abs(theorem_summary['minimum_certified_margin'] - 2.0e-05) < 1.0e-12
    assert theorem_summary['report_kind'] == 'theorem-viii-report'
    assert theorem_summary['discharge_aware'] is False
    extracted = extract_theorem_viii_current_reduction_geometry_summary(theorem_report)
    assert extracted['status'] == 'current-reduction-geometry-strong'
    assert extracted['discharge_aware'] is False


def test_theorem_viii_reuses_nested_theorem_v_from_identification_tree(monkeypatch) -> None:
    import kam_theorem_suite.theorem_viii_reduction_lift as tviiil

    def _should_not_build_theorem_v(**kwargs):
        raise AssertionError('theorem_v should have been reused from the identification tree')

    monkeypatch.setattr(tviiil, 'build_golden_theorem_v_certificate', _should_not_build_theorem_v)

    cert = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.3],
        theorem_iii_certificate={
            'theorem_status': 'golden-theorem-iii-final-strong',
            'open_hypotheses': [],
            'active_assumptions': [],
            'certified_below_threshold_interval': [0.97108, 0.97109],
        },
        theorem_iv_certificate={
            'theorem_status': 'golden-theorem-iv-final-strong',
            'open_hypotheses': [],
            'active_assumptions': [],
        },
        threshold_identification_certificate={
            'theorem_status': 'golden-threshold-identification-theorem-front-complete',
            'open_hypotheses': [],
            'active_assumptions': [],
            'transport_discharge_shell': {
                'threshold_identification_discharge_shell': {
                    'identification_shell': {
                        'theorem_v_shell': {
                            'theorem_status': 'golden-theorem-v-compressed-contract-strong',
                            'compressed_contract': {
                                'theorem_status': 'golden-theorem-v-compressed-contract-strong',
                                'target_interval': {'lo': 0.97109, 'hi': 0.97111},
                                'uniform_majorant': {'gap_preservation_certified': True},
                            },
                            'open_hypotheses': [],
                            'active_assumptions': [],
                        },
                    },
                },
            },
        },
        theorem_vi_certificate={
            'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
            'statement_mode': 'one-variable',
            'open_hypotheses': [],
            'active_assumptions': [],
        },
        theorem_vii_certificate={
            'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete',
            'open_hypotheses': [],
            'active_assumptions': [],
            'reference_lower_bound': 0.97109,
            'current_near_top_exhaustion_upper_bound': 0.97106,
            'current_near_top_exhaustion_margin': 3.0e-05,
            'current_near_top_exhaustion_pending_count': 0,
            'current_near_top_exhaustion_source': 'theorem-vii',
            'current_near_top_exhaustion_status': 'near-top-exhaustion-strong',
        },
        theorem_i_ii_workstream_certificate={
            'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete',
            'open_hypotheses': [],
            'active_assumptions': [],
        },
    ).to_dict()

    assert cert['theorem_v_shell']['compressed_contract']['target_interval']['lo'] == 0.97109
    names = {row['name']: row for row in cert['hypotheses']}
    assert names['theorem_v_front_complete']['satisfied'] is True


def test_theorem_viii_filters_orchestration_only_kwargs_before_calling_upstream_wrappers(monkeypatch) -> None:
    import kam_theorem_suite.theorem_viii_reduction_lift as tviiil

    def _mock_theorem_iii(*, base_K_values, family=None, rho=None, **kwargs):
        assert 'theorem_v_compressed_certificate' not in kwargs
        return _Dummy({'theorem_status': 'golden-theorem-iii-final-strong', 'active_assumptions': [], 'open_hypotheses': [], 'certified_below_threshold_interval': [0.29, 0.3]})

    monkeypatch.setattr(tviiil, 'build_golden_theorem_iii_certificate', _mock_theorem_iii)
    monkeypatch.setattr(tviiil, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-theorem-iv-final-strong', 'active_assumptions': [], 'open_hypotheses': []}))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_v_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-theorem-v-lift-front-complete', 'active_assumptions': [], 'open_hypotheses': [], 'compressed_contract_certificate': {'theorem_status': 'golden-theorem-v-compressed-contract-front-complete'}, 'target_interval': [0.29, 0.3], 'gap_preservation_certificate': {'gap_preservation_certified': True}}))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-threshold-identification-lift-front-complete', 'active_assumptions': [], 'open_hypotheses': []}))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete', 'active_assumptions': [], 'open_hypotheses': [], 'statement_mode': 'one-variable'}))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete', 'active_assumptions': [], 'open_hypotheses': [], 'reference_lower_bound': 0.3}))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_i_ii_workstream_lift_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete', 'active_assumptions': [], 'open_hypotheses': []}))

    cert = build_golden_theorem_viii_reduction_lift_certificate(base_K_values=[0.3], theorem_v_compressed_certificate={'dummy': True}).to_dict()
    assert cert['theorem_iii_shell']['theorem_status'] == 'golden-theorem-iii-final-strong'
