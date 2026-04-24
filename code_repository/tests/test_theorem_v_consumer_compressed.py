from __future__ import annotations

from kam_theorem_suite.threshold_identification_lift import build_golden_threshold_identification_lift_certificate


def test_threshold_identification_accepts_compressed_v_certificate() -> None:
    theorem_v_compressed = {
        'theorem_status': 'golden-theorem-v-compressed-contract-strong',
        'compressed_contract': {'theorem_status': 'golden-theorem-v-compressed-contract-strong'},
        'active_assumptions': [],
        'open_hypotheses': [],
        'final_transport_bridge': {'theorem_target_interval': [0.25, 0.26]},
    }
    cert = build_golden_threshold_identification_lift_certificate(
        base_K_values=[0.2],
        theorem_iv_certificate={'theorem_status': 'golden-theorem-iv-final-strong', 'active_assumptions': [], 'open_hypotheses': []},
        theorem_v_compressed_certificate=theorem_v_compressed,
        compatibility_bridge_certificate={
            'theorem_status': 'validated-threshold-compatibility-bridge-strong',
            'validated_window': [0.25, 0.26],
            'certified_center': 0.255,
            'certified_radius': 0.005,
            'theorem_flags': {'family_vs_threshold_localized': True, 'threshold_window_certified': True, 'renorm_chart_window_compatible': True},
            'compatibility_window_certificate': {'compatibility_relation': {'window_nested_in_chart': True}, 'linkage_certificate': {'theorem_status': 'threshold-chart-linkage-strong'}},
        },
        assume_validated_true_renormalization_fixed_point_package=True,
        assume_golden_stable_manifold_is_true_critical_surface=True,
        assume_family_chart_crossing_identifies_true_critical_parameter=True,
        assume_localized_compatibility_window_identifies_true_irrational_threshold=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-threshold-identification-lift-conditional-strong'
