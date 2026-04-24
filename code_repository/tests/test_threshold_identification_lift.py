from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_golden_theorem_ii_to_v_identification_report,
    build_golden_threshold_identification_lift_report,
)
from kam_theorem_suite.threshold_identification_lift import (
    build_golden_threshold_identification_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload
    def to_dict(self):
        return dict(self._payload)


def test_threshold_identification_front_complete_when_bridge_and_front_shells_are_closed(monkeypatch) -> None:
    import kam_theorem_suite.threshold_identification_lift as til

    monkeypatch.setattr(til, 'build_validated_threshold_compatibility_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'validated-threshold-compatibility-bridge-strong',
        'validated_window': [0.97105, 0.97115],
        'certified_center': 0.9711,
        'certified_radius': 5.0e-5,
        'theorem_flags': {
            'compatibility_window_available': True,
            'validated_window_nonempty': True,
            'positive_localization_margins': True,
        },
        'compatibility_window_certificate': {
            'theorem_status': 'threshold-compatibility-window-strong',
            'compatibility_relation': {
                'compatibility_center_gap_from_chart_center': 1.0e-5,
            },
            'linkage_certificate': {
                'theorem_status': 'chart-threshold-linkage-strong',
            },
        },
    }))
    monkeypatch.setattr(til, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-front-only',
        'open_hypotheses': [],
        'active_assumptions': ['final_function_space_promotion'],
    }))
    monkeypatch.setattr(til, 'build_golden_theorem_v_compressed_lift_certificate', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-only',
        'open_hypotheses': [],
        'active_assumptions': ['validated_function_space_continuation_transport'],
    })

    cert = build_golden_threshold_identification_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-lift-front-complete'
    assert cert['open_hypotheses'] == []
    assert cert['upstream_active_assumptions'] == [
        'final_function_space_promotion',
        'validated_function_space_continuation_transport',
    ]
    assert 'localized_compatibility_window_identifies_true_irrational_threshold' in cert['local_active_assumptions']



def test_threshold_identification_conditional_strong_when_all_assumptions_are_toggled_on(monkeypatch) -> None:
    import kam_theorem_suite.threshold_identification_lift as til

    monkeypatch.setattr(til, 'build_validated_threshold_compatibility_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'validated-threshold-compatibility-bridge-strong',
        'validated_window': [0.97108, 0.97112],
        'certified_center': 0.9711,
        'certified_radius': 2.0e-5,
        'theorem_flags': {
            'compatibility_window_available': True,
            'validated_window_nonempty': True,
            'positive_localization_margins': True,
        },
        'compatibility_window_certificate': {
            'theorem_status': 'threshold-compatibility-window-strong',
            'compatibility_relation': {
                'compatibility_center_gap_from_chart_center': 0.0,
            },
            'linkage_certificate': {
                'theorem_status': 'chart-threshold-linkage-strong',
            },
        },
    }))
    monkeypatch.setattr(til, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(til, 'build_golden_theorem_v_compressed_lift_certificate', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })

    cert = build_golden_threshold_identification_lift_certificate(
        base_K_values=[0.3],
        assume_validated_true_renormalization_fixed_point_package=True,
        assume_golden_stable_manifold_is_true_critical_surface=True,
        assume_family_chart_crossing_identifies_true_critical_parameter=True,
        assume_localized_compatibility_window_identifies_true_irrational_threshold=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-lift-conditional-strong'
    assert cert['active_assumptions'] == []



def test_threshold_identification_stays_partial_when_bridge_or_fronts_are_not_closed(monkeypatch) -> None:
    import kam_theorem_suite.threshold_identification_lift as til

    monkeypatch.setattr(til, 'build_validated_threshold_compatibility_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'validated-threshold-compatibility-bridge-moderate',
        'validated_window': [0.9710, 0.9712],
        'certified_center': 0.9711,
        'certified_radius': 1.0e-4,
        'theorem_flags': {
            'compatibility_window_available': True,
            'validated_window_nonempty': True,
            'positive_localization_margins': False,
        },
        'compatibility_window_certificate': {
            'theorem_status': 'threshold-compatibility-window-moderate',
            'compatibility_relation': {
                'compatibility_center_gap_from_chart_center': 8.0e-5,
            },
            'linkage_certificate': {
                'theorem_status': 'chart-threshold-linkage-moderate',
            },
        },
    }))
    monkeypatch.setattr(til, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-conditional-partial',
        'open_hypotheses': ['window_to_window_separation'],
        'active_assumptions': ['final_function_space_promotion'],
    }))
    monkeypatch.setattr(til, 'build_golden_theorem_v_compressed_lift_certificate', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-conditional-partial',
        'open_hypotheses': ['transport_stack_closed'],
        'active_assumptions': ['validated_function_space_continuation_transport'],
    })

    cert = build_golden_threshold_identification_lift_certificate(
        base_K_values=[0.3],
        assume_validated_true_renormalization_fixed_point_package=True,
        assume_golden_stable_manifold_is_true_critical_surface=True,
        assume_family_chart_crossing_identifies_true_critical_parameter=True,
        assume_localized_compatibility_window_identifies_true_irrational_threshold=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-lift-conditional-partial'
    assert 'validated_threshold_compatibility_bridge_closed' in cert['open_hypotheses']
    assert 'theorem_iv_front_complete' in cert['open_hypotheses']
    assert 'theorem_v_front_complete' in cert['open_hypotheses']



def test_driver_exposes_threshold_identification_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_threshold_identification_lift_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'active_assumptions': ['validated_true_renormalization_fixed_point_package'],
    }))
    monkeypatch.setattr(pd, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-conditional-strong',
        'active_assumptions': [],
    }))

    lift_report = build_golden_threshold_identification_lift_report(base_K_values=[0.3])
    theorem_report = build_golden_theorem_ii_to_v_identification_report(base_K_values=[0.3])
    assert lift_report['theorem_status'] == 'golden-threshold-identification-lift-front-complete'
    assert theorem_report['theorem_status'] == 'golden-threshold-identification-lift-conditional-strong'


def test_threshold_identification_reports_bridge_native_tail_witness_inside_identified_window(monkeypatch) -> None:
    import kam_theorem_suite.threshold_identification_lift as til

    monkeypatch.setattr(til, 'build_validated_threshold_compatibility_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'validated-threshold-compatibility-bridge-strong',
        'validated_window': [0.97108, 0.97112],
        'certified_center': 0.97110,
        'certified_radius': 2.0e-5,
        'theorem_flags': {
            'compatibility_window_available': True,
            'validated_window_nonempty': True,
            'positive_localization_margins': True,
        },
        'compatibility_window_certificate': {
            'theorem_status': 'threshold-compatibility-window-strong',
            'compatibility_relation': {
                'compatibility_center_gap_from_chart_center': 0.0,
            },
            'linkage_certificate': {
                'theorem_status': 'chart-threshold-linkage-strong',
            },
        },
    }))
    monkeypatch.setattr(til, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-front-only',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(til, 'build_golden_theorem_v_compressed_lift_certificate', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-only',
        'open_hypotheses': [],
        'active_assumptions': [],
        'convergence_front': {
            'relation': {
                'native_late_coherent_suffix_witness_lo': 0.97109,
                'native_late_coherent_suffix_witness_hi': 0.97111,
                'native_late_coherent_suffix_status': 'native-late-coherent-suffix-strong',
                'native_late_coherent_suffix_source': 'golden_limit_bridge.native_late_coherent_suffix_witness',
            },
        },
    })

    cert = build_golden_threshold_identification_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['bridge_native_tail_witness_interval'] == [0.97109, 0.97111]
    assert cert['identified_bridge_native_tail_witness_interval'] == [0.97109, 0.97111]
    assert abs(cert['identified_bridge_native_tail_witness_width'] - 2.0e-05) < 1.0e-12
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['bridge_native_tail_witness_survives_identified_window']['satisfied'] is True
