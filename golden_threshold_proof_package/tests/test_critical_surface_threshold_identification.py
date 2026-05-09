from __future__ import annotations

from kam_theorem_suite.critical_surface_threshold_identification import (
    build_critical_surface_threshold_identification_discharge_certificate,
    build_critical_surface_threshold_identification_promotion_certificate,
)
from kam_theorem_suite.standard_map import HarmonicFamily


def test_critical_surface_threshold_identification_discharge_front_complete_when_local_geometry_is_strong():
    cert = build_critical_surface_threshold_identification_discharge_certificate(
        family=HarmonicFamily(),
        stable_manifold_certificate={
            'theorem_status': 'proxy-stable-manifold-chart-identified',
            'stable_chart_radius': 0.03,
        },
        critical_surface_bridge_certificate={
            'theorem_status': 'proxy-critical-surface-family-bridge-identified',
        },
        validated_critical_surface_bridge_certificate={
            'theorem_status': 'proxy-critical-surface-window-bridge-validated',
            'theorem_flags': {
                'localized_transversality_window': True,
                'derivative_floor_positive': True,
                'window_narrow_enough': True,
            },
            'localized_center': 1.0,
            'localized_radius': 0.02,
            'transversality_margin': 0.07,
            'derivative_floor_proxy': 0.05,
        },
        active_assumptions=[
            'golden_stable_manifold_is_true_critical_surface',
            'family_chart_crossing_identifies_true_critical_parameter',
            'golden_critical_surface_transversality_on_class',
            'theorem_grade_banach_manifold_universality_class',
        ],
    ).to_dict()
    assert cert['theorem_status'] == 'critical-surface-threshold-identification-discharge-front-complete'
    assert cert['promotion_ready'] is True
    assert cert['residual_burden_summary']['status'] == 'critical-surface-threshold-promotion-frontier'
    assert cert['residual_burden_summary']['upstream_context_assumptions'] == ['theorem_grade_banach_manifold_universality_class']



def test_critical_surface_threshold_identification_promotion_theorem_becomes_conditionally_strong_when_identification_assumptions_are_absorbed():
    discharge = build_critical_surface_threshold_identification_discharge_certificate(
        family=HarmonicFamily(),
        stable_manifold_certificate={
            'theorem_status': 'proxy-stable-manifold-chart-identified',
            'stable_chart_radius': 0.03,
        },
        critical_surface_bridge_certificate={
            'theorem_status': 'proxy-critical-surface-family-bridge-identified',
        },
        validated_critical_surface_bridge_certificate={
            'theorem_status': 'proxy-critical-surface-window-bridge-validated',
            'theorem_flags': {
                'localized_transversality_window': True,
                'derivative_floor_positive': True,
                'window_narrow_enough': True,
            },
            'localized_center': 1.0,
            'localized_radius': 0.02,
            'transversality_margin': 0.07,
            'derivative_floor_proxy': 0.05,
        },
        active_assumptions=[
            'theorem_grade_banach_manifold_universality_class',
            'validated_true_renormalization_fixed_point_package',
        ],
    ).to_dict()
    cert = build_critical_surface_threshold_identification_promotion_certificate(
        family=HarmonicFamily(),
        discharge_certificate=discharge,
    ).to_dict()
    assert cert['theorem_status'] == 'critical-surface-threshold-promotion-theorem-conditional-strong'
    assert cert['theorem_flags']['promotion_theorem_available'] is True
    assert cert['theorem_flags']['promotion_theorem_discharged'] is False
    assert cert['residual_burden_summary']['status'] == 'critical-surface-threshold-promotion-theorem-conditional-strong'
    assert cert['upstream_context_assumptions'] == [
        'theorem_grade_banach_manifold_universality_class',
        'validated_true_renormalization_fixed_point_package',
    ]
