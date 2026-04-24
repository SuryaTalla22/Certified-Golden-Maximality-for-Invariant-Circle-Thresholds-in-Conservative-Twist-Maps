from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_golden_theorem_ii_to_v_identification_discharge_report,
    build_golden_threshold_identification_discharge_lift_report,
)
from kam_theorem_suite.threshold_identification_discharge import (
    build_golden_threshold_identification_discharge_certificate,
)
from kam_theorem_suite.theorem_viii_reduction_lift import (
    build_golden_theorem_viii_reduction_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload
    def to_dict(self):
        return dict(self._payload)


def _strong_workstream(active_assumptions=None, window=None, ready=False):
    return {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': list(active_assumptions or []),
        'assumptions': [
            {'name': 'theorem_grade_banach_manifold_universality_class'},
            {'name': 'validated_true_renormalization_fixed_point_package'},
            {'name': 'golden_stable_manifold_is_true_critical_surface'},
            {'name': 'family_chart_crossing_identifies_true_critical_parameter'},
            {'name': 'golden_critical_surface_transversality_on_class'},
        ],
        'critical_parameter_window': list(window or [0.97108, 0.97112]),
        'critical_surface_identification_summary': {
            'threshold_identification_ready': bool(ready),
            'local_identification_margin': 2.0e-5 if ready else None,
            'residual_burden_status': 'critical-surface-threshold-identification-frontier' if ready else 'mixed-workstream-frontier',
        },
        'critical_surface_threshold_identification_discharge': {
            'theorem_status': 'critical-surface-threshold-identification-discharge-front-complete' if ready else 'critical-surface-threshold-identification-discharge-conditional-partial',
            'promotion_ready': bool(ready),
            'local_identification_margin': 2.0e-5 if ready else None,
            'residual_burden_summary': {
                'status': 'critical-surface-threshold-promotion-frontier' if ready else 'workstream-local-prerequisite-frontier',
                'promotion_ready': bool(ready),
                'local_front_complete': bool(ready),
                'identification_specific_assumptions': [
                    'golden_stable_manifold_is_true_critical_surface',
                    'family_chart_crossing_identifies_true_critical_parameter',
                    'golden_critical_surface_transversality_on_class',
                ] if ready else [],
                'upstream_context_assumptions': list(active_assumptions or []),
                'local_identification_margin': 2.0e-5 if ready else None,
            },
        },
        'critical_surface_threshold_identification_promotion': {
            'theorem_status': ('critical-surface-threshold-promotion-theorem-conditional-strong' if ready and not active_assumptions else ('critical-surface-threshold-promotion-theorem-front-complete' if ready else 'critical-surface-threshold-promotion-theorem-conditional-partial')),
            'theorem_flags': {
                'promotion_theorem_available': bool(ready and not active_assumptions),
                'promotion_theorem_discharged': False,
            },
            'promotion_margin': 2.0e-5 if ready else None,
            'residual_burden_summary': {
                'status': 'critical-surface-threshold-promotion-theorem-conditional-strong' if ready and not active_assumptions else ('critical-surface-threshold-promotion-theorem-frontier' if ready else 'critical-surface-threshold-promotion-local-prerequisite-frontier'),
                'promotion_theorem_ready': bool(ready),
                'promotion_theorem_available': bool(ready and not active_assumptions),
                'promotion_theorem_discharged': False,
                'upstream_context_assumptions': list(active_assumptions or []),
                'promotion_margin': 2.0e-5 if ready else None,
            },
        },
    }


def _strong_identification(local_active_assumptions=None, upstream_active_assumptions=None, window=None):
    return {
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': sorted(set((local_active_assumptions or []) + (upstream_active_assumptions or []))),
        'upstream_active_assumptions': list(upstream_active_assumptions or ['final_function_space_promotion']),
        'local_active_assumptions': list(local_active_assumptions or [
            'validated_true_renormalization_fixed_point_package',
            'golden_stable_manifold_is_true_critical_surface',
            'family_chart_crossing_identifies_true_critical_parameter',
            'localized_compatibility_window_identifies_true_irrational_threshold',
        ]),
        'identified_window': list(window or [0.97109, 0.97111]),
    }


def test_threshold_identification_discharge_absorbs_workstream_owned_assumptions(monkeypatch):
    import kam_theorem_suite.threshold_identification_discharge as tid

    monkeypatch.setattr(tid, 'build_golden_theorem_i_ii_certificate', lambda **kwargs: _Dummy(_strong_workstream(active_assumptions=['validated_true_renormalization_fixed_point_package'])))
    monkeypatch.setattr(tid, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(_strong_identification()))

    cert = build_golden_threshold_identification_discharge_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-discharge-lift-front-complete'
    assert cert['local_active_assumptions'] == ['localized_compatibility_window_identifies_true_irrational_threshold']
    assert 'validated_true_renormalization_fixed_point_package' in cert['upstream_active_assumptions']
    assert 'validated_true_renormalization_fixed_point_package' not in cert['local_active_assumptions']


def test_threshold_identification_discharge_conditional_strong_when_residual_local_hinge_is_toggled_on(monkeypatch):
    import kam_theorem_suite.threshold_identification_discharge as tid

    monkeypatch.setattr(tid, 'build_golden_theorem_i_ii_certificate', lambda **kwargs: _Dummy(_strong_workstream()))
    monkeypatch.setattr(tid, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(_strong_identification(local_active_assumptions=[
        'validated_true_renormalization_fixed_point_package',
        'golden_stable_manifold_is_true_critical_surface',
        'family_chart_crossing_identifies_true_critical_parameter',
        'localized_compatibility_window_identifies_true_irrational_threshold',
    ], upstream_active_assumptions=[])))

    cert = build_golden_threshold_identification_discharge_certificate(
        base_K_values=[0.3],
        assume_localized_compatibility_window_identifies_true_irrational_threshold=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-discharge-lift-conditional-strong'
    assert cert['local_active_assumptions'] == []


def test_threshold_identification_discharge_window_overlap_hypothesis(monkeypatch):
    import kam_theorem_suite.threshold_identification_discharge as tid

    monkeypatch.setattr(tid, 'build_golden_theorem_i_ii_certificate', lambda **kwargs: _Dummy(_strong_workstream(window=[0.97100, 0.97110])))
    monkeypatch.setattr(tid, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(_strong_identification(window=[0.97108, 0.97112])))

    cert = build_golden_threshold_identification_discharge_certificate(base_K_values=[0.3]).to_dict()
    assert cert['overlap_window'] == [0.97108, 0.9711]
    assert abs(cert['overlap_width'] - 2.0e-05) < 1.0e-12
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['workstream_threshold_windows_overlap']['satisfied'] is True


def test_threshold_identification_discharge_partial_when_front_is_not_closed(monkeypatch):
    import kam_theorem_suite.threshold_identification_discharge as tid

    monkeypatch.setattr(tid, 'build_golden_theorem_i_ii_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-partial',
        'open_hypotheses': ['theorem_ii_proxy_stable_manifold_chart_identified'],
        'active_assumptions': ['validated_true_renormalization_fixed_point_package'],
        'assumptions': [{'name': 'validated_true_renormalization_fixed_point_package'}],
        'critical_parameter_window': [0.97108, 0.97112],
    }))
    monkeypatch.setattr(tid, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(_strong_identification()))

    cert = build_golden_threshold_identification_discharge_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-discharge-lift-conditional-partial'
    assert 'theorem_i_ii_front_complete' in cert['open_hypotheses']


def test_driver_exposes_threshold_identification_discharge_reports(monkeypatch):
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_threshold_identification_discharge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-discharge-lift-front-complete',
        'local_active_assumptions': ['localized_compatibility_window_identifies_true_irrational_threshold'],
    }))
    monkeypatch.setattr(pd, 'build_golden_theorem_ii_to_v_identification_discharge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-discharge-lift-conditional-strong',
        'local_active_assumptions': [],
    }))

    lift_report = build_golden_threshold_identification_discharge_lift_report(base_K_values=[0.3])
    theorem_report = build_golden_theorem_ii_to_v_identification_discharge_report(base_K_values=[0.3])
    assert lift_report['theorem_status'] == 'golden-threshold-identification-discharge-lift-front-complete'
    assert theorem_report['theorem_status'] == 'golden-threshold-identification-discharge-lift-conditional-strong'


def test_theorem_viii_accepts_identification_discharge_certificate(monkeypatch):
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
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': ['strict_golden_top_gap_theorem'],
    }))
    monkeypatch.setattr(tviiil, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['finite_screened_panel_is_globally_complete'],
    }))

    cert = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.3],
        threshold_identification_discharge_certificate={
            'theorem_status': 'golden-threshold-identification-discharge-lift-front-complete',
            'open_hypotheses': [],
            'active_assumptions': ['final_function_space_promotion'],
        },
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-viii-reduction-lift-front-complete'
    assert 'final_function_space_promotion' in cert['upstream_active_assumptions']


def test_threshold_identification_discharge_reports_bridge_native_tail_witness_inside_workstream_overlap(monkeypatch):
    import kam_theorem_suite.threshold_identification_discharge as tid

    monkeypatch.setattr(tid, 'build_golden_theorem_i_ii_certificate', lambda **kwargs: _Dummy(_strong_workstream(window=[0.971085, 0.971115])))
    monkeypatch.setattr(tid, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        **_strong_identification(window=[0.97108, 0.97112]),
        'bridge_native_tail_witness_interval': [0.97109, 0.97111],
        'bridge_native_tail_witness_source': 'golden_limit_bridge.native_late_coherent_suffix_witness',
        'bridge_native_tail_witness_status': 'native-late-coherent-suffix-strong',
        'identified_bridge_native_tail_witness_interval': [0.97109, 0.97111],
        'identified_bridge_native_tail_witness_width': 2.0e-05,
    }))

    cert = build_golden_threshold_identification_discharge_certificate(base_K_values=[0.3]).to_dict()
    assert cert['bridge_native_tail_witness_interval'] == [0.97109, 0.97111]
    assert cert['discharged_bridge_native_tail_witness_interval'] == [0.97109, 0.97111]
    assert abs(cert['discharged_bridge_native_tail_witness_width'] - 2.0e-05) < 1.0e-12
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['bridge_native_tail_witness_survives_discharge_window_overlap']['satisfied'] is True


def test_threshold_identification_discharge_surfaces_workstream_identification_frontier(monkeypatch):
    import kam_theorem_suite.threshold_identification_discharge as tid

    monkeypatch.setattr(tid, 'build_golden_theorem_i_ii_certificate', lambda **kwargs: _Dummy(_strong_workstream(ready=True)))
    monkeypatch.setattr(tid, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(_strong_identification()))

    cert = build_golden_threshold_identification_discharge_certificate(base_K_values=[0.3]).to_dict()
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['workstream_critical_surface_identification_ready']['satisfied'] is True
    assert cert['residual_burden_summary']['status'] == 'localized-compatibility-identification-frontier'
    assert cert['workstream_critical_surface_identification_summary']['threshold_identification_ready'] is True
    assert cert['workstream_critical_surface_threshold_identification_discharge']['promotion_ready'] is True


def test_threshold_identification_discharge_surfaces_workstream_promotion_frontier_when_local_hinge_is_not_isolated(monkeypatch):
    import kam_theorem_suite.threshold_identification_discharge as tid

    monkeypatch.setattr(tid, 'build_golden_theorem_i_ii_certificate', lambda **kwargs: _Dummy(_strong_workstream(ready=True)))
    monkeypatch.setattr(tid, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(_strong_identification(local_active_assumptions=[
        'validated_true_renormalization_fixed_point_package',
        'golden_stable_manifold_is_true_critical_surface',
        'family_chart_crossing_identifies_true_critical_parameter',
        'localized_compatibility_window_identifies_true_irrational_threshold',
        'auxiliary_local_threshold_linkage_hinge',
    ])))

    cert = build_golden_threshold_identification_discharge_certificate(base_K_values=[0.3]).to_dict()
    assert cert['residual_burden_summary']['status'] == 'critical-surface-threshold-promotion-theorem-available'
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['workstream_critical_surface_threshold_discharge_front_complete']['satisfied'] is True
    assert hyp['workstream_critical_surface_threshold_promotion_ready']['satisfied'] is True



def test_threshold_identification_discharge_uses_promoted_workstream_theorem_when_available(monkeypatch):
    import kam_theorem_suite.threshold_identification_discharge as tid

    monkeypatch.setattr(tid, 'build_golden_theorem_i_ii_certificate', lambda **kwargs: _Dummy(_strong_workstream(active_assumptions=[], ready=True)))
    monkeypatch.setattr(tid, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(_strong_identification()))

    cert = build_golden_threshold_identification_discharge_certificate(base_K_values=[0.3]).to_dict()
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['workstream_critical_surface_threshold_promotion_theorem_available']['satisfied'] is True
    assert cert['residual_burden_summary']['status'] == 'localized-compatibility-identification-frontier'
    assert cert['workstream_critical_surface_threshold_identification_promotion']['theorem_status'] == 'critical-surface-threshold-promotion-theorem-conditional-strong'
