from __future__ import annotations

from kam_theorem_suite.chart_threshold_linkage import build_chart_threshold_linkage_certificate
from kam_theorem_suite.threshold_identification_lift import build_golden_threshold_identification_lift_certificate


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_chart_threshold_linkage_reads_compressed_theorem_v_target_interval(monkeypatch) -> None:
    import kam_theorem_suite.chart_threshold_linkage as ctl

    monkeypatch.setattr(
        ctl,
        'build_validated_critical_surface_bridge_certificate',
        lambda *args, **kwargs: _Dummy({'theorem_status': 'proxy-critical-surface-window-bridge-strong', 'localized_center': 0.0, 'localized_radius': 1.0e-4}),
    )
    lower = {'certified_below_threshold_interval': [0.21, 0.25]}
    upper = {'nonexistence_front': {'upper_bridge_promotion': {'strongest_candidate': {'selected_upper_hi': 0.9718, 'selected_barrier_lo': 1.02}}}}
    theorem_v = {
        'theorem_status': 'golden-theorem-v-compressed-contract-strong',
        'compressed_contract': {'target_interval': {'lo': 0.97136, 'hi': 0.97137}},
    }

    cert = build_chart_threshold_linkage_certificate(
        lower_certificate=lower,
        upper_certificate=upper,
        theorem_v_certificate=theorem_v,
    ).to_dict()
    relation = cert['linkage_relation']
    assert relation['theorem_v_interval_lo'] == 0.97136
    assert relation['theorem_v_interval_hi'] == 0.97137
    assert relation['lower_bound'] == 0.25
    assert relation['upper_hi'] == 0.9718


def test_identification_lift_refines_window_to_transport_witness_when_bridge_is_only_moderate(monkeypatch) -> None:
    import kam_theorem_suite.threshold_identification_lift as til

    monkeypatch.setattr(til, 'build_validated_threshold_compatibility_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'validated-threshold-compatibility-bridge-moderate',
        'validated_window': [0.97102, 0.97129],
        'certified_center': 0.971155,
        'certified_radius': 1.35e-4,
        'theorem_flags': {
            'compatibility_window_available': True,
            'validated_window_nonempty': True,
            'positive_localization_margins': False,
        },
        'compatibility_window_certificate': {
            'theorem_status': 'threshold-compatibility-window-moderate',
            'compatibility_relation': {'compatibility_center_gap_from_chart_center': 0.0},
            'linkage_certificate': {'theorem_status': 'chart-threshold-linkage-moderate'},
        },
    }))
    monkeypatch.setattr(til, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-front-only',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    theorem_v = {
        'theorem_status': 'golden-theorem-v-compressed-contract-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'compressed_contract': {'target_interval': {'lo': 0.97136285, 'hi': 0.97136717}},
    }

    cert = build_golden_threshold_identification_lift_certificate(
        base_K_values=[0.25],
        theorem_v_compressed_certificate=theorem_v,
    ).to_dict()
    assert cert['identified_window'] == [0.97136285, 0.97136717]
    assert cert['identified_bridge_native_tail_witness_interval'] == [0.97136285, 0.97136717]
    assert cert['theorem_status'] == 'golden-threshold-identification-lift-front-complete'
