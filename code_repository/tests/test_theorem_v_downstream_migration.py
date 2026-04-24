from __future__ import annotations

from kam_theorem_suite.threshold_identification_lift import build_golden_threshold_identification_lift_certificate
from kam_theorem_suite.theorem_v_batched import build_golden_theorem_v_certificate_batched
from kam_theorem_suite.theorem_viii_reduction_lift import build_golden_theorem_viii_reduction_lift_certificate


class _Dummy:
    def __init__(self, payload):
        self._payload = payload
    def to_dict(self):
        return dict(self._payload)


def test_identification_lift_forwards_prebuilt_objects_into_compatibility_bridge(monkeypatch) -> None:
    import kam_theorem_suite.threshold_identification_lift as til

    seen = {}

    def _bridge(**kwargs):
        seen.update(kwargs)
        return _Dummy({
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
                'compatibility_relation': {'compatibility_center_gap_from_chart_center': 0.0},
                'linkage_certificate': {'theorem_status': 'chart-threshold-linkage-strong'},
            },
        })

    monkeypatch.setattr(til, 'build_validated_threshold_compatibility_bridge_certificate', _bridge)
    cert = build_golden_threshold_identification_lift_certificate(
        base_K_values=[0.3],
        theorem_iii_certificate={'stable_lower_bound': 0.97},
        theorem_iv_certificate={'theorem_status': 'golden-theorem-iv-final-strong', 'open_hypotheses': [], 'active_assumptions': []},
        theorem_v_certificate={'theorem_status': 'golden-theorem-v-final-strong', 'open_hypotheses': [], 'active_assumptions': [], 'compatible_limit_interval_lo': 0.97108, 'compatible_limit_interval_hi': 0.97112},
        theorem_v_compressed_certificate={'theorem_status': 'golden-theorem-v-compressed-contract-strong', 'open_hypotheses': [], 'active_assumptions': [], 'theorem_v_shell': {'theorem_status': 'golden-theorem-v-final-strong'}},
    ).to_dict()
    assert cert['theorem_status'] in {
        'golden-threshold-identification-lift-front-complete',
        'golden-threshold-identification-lift-conditional-partial',
        'golden-threshold-identification-lift-conditional-strong',
    }
    assert seen['base_K_values'] == [0.3]
    assert seen['lower_certificate']['stable_lower_bound'] == 0.97
    assert seen['upper_certificate']['theorem_status'] == 'golden-theorem-iv-final-strong'
    assert seen['theorem_v_certificate']['theorem_status'] == 'golden-theorem-v-final-strong'


def test_theorem_v_batched_returns_compressed_downstream_certificate(monkeypatch) -> None:
    import kam_theorem_suite.theorem_v_batched as tvb

    monkeypatch.setattr(tvb, 'build_golden_rational_to_irrational_convergence_certificate_batched', lambda **kwargs: {
        'certificate': {'front': True},
        'stage_timings': {},
        'stage_cache_dir': '/tmp/theorem_v_batches_test',
    })
    monkeypatch.setattr(tvb, '_build_or_load_stage', lambda name, builder, **kwargs: builder())
    monkeypatch.setattr(tvb, 'build_golden_theorem_v_transport_lift_certificate', lambda **kwargs: {'theorem_status': 'golden-theorem-v-final-strong'})
    monkeypatch.setattr(tvb, 'build_golden_theorem_v_compressed_lift_certificate', lambda **kwargs: {'theorem_status': 'golden-theorem-v-compressed-contract-strong'})

    bundle = build_golden_theorem_v_certificate_batched(base_K_values=[0.3], theorem_iii_certificate={'theorem_status': 'iii'}, theorem_iv_certificate={'theorem_status': 'iv'}, use_cache=False)
    assert bundle['certificate']['theorem_status'] == 'golden-theorem-v-final-strong'
    assert bundle['compressed_certificate']['theorem_status'] == 'golden-theorem-v-compressed-contract-strong'
    assert bundle['downstream_certificate']['theorem_status'] == 'golden-theorem-v-compressed-contract-strong'


def test_theorem_viii_accepts_compressed_theorem_v_certificate() -> None:
    cert = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.3],
        theorem_iii_certificate={'theorem_status': 'golden-theorem-iii-final-strong', 'theorem_iii_final_status': 'golden-theorem-iii-final-strong', 'certified_below_threshold_interval': [0.96, 0.97]},
        theorem_iv_certificate={'theorem_status': 'golden-theorem-iv-final-strong'},
        theorem_v_certificate={
            'theorem_status': 'golden-theorem-v-compressed-contract-strong',
            'compressed_contract': {
                'theorem_status': 'golden-theorem-v-compressed-contract-strong',
                'target_interval': {'lo': 0.97108, 'hi': 0.97112, 'width': 4.0e-5},
                'uniform_majorant': {'preserves_golden_gap': True},
            },
            'open_hypotheses': [],
            'active_assumptions': [],
        },
        threshold_identification_certificate={'theorem_status': 'golden-threshold-identification-lift-front-complete', 'open_hypotheses': [], 'active_assumptions': []},
        theorem_vi_certificate={'theorem_status': 'golden-theorem-vi-envelope-lift-global-one-variable-strong'},
        theorem_vii_certificate={'theorem_status': 'golden-theorem-vii-exhaustion-discharge-final-strong', 'open_hypotheses': [], 'active_assumptions': [], 'theorem_vii_codepath_final': True, 'theorem_vii_papergrade_final': True},
        theorem_i_ii_workstream_certificate={'theorem_status': 'golden-theorem-i-ii-workstream-lift-papergrade-final', 'active_assumptions': [], 'residual_burden_summary': {'promotion_theorem_discharged': True}},
    ).to_dict()
    assert cert['theorem_v_final_certified'] is True
    assert cert['theorem_v_target_interval'] == [0.97108, 0.97112]
    assert cert['theorem_v_gap_preservation_certified'] is True
