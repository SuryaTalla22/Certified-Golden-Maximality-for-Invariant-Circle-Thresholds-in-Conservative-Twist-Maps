from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.validated_renormalization_package import build_validated_renormalization_package_promotion_certificate
from kam_theorem_suite.validated_critical_surface_theorem import (
    build_validated_critical_surface_theorem_discharge_certificate,
    build_validated_critical_surface_theorem_promotion_certificate,
)


def test_stage90_critical_surface_finalization() -> None:
    family = HarmonicFamily()
    renorm = build_validated_renormalization_package_promotion_certificate(family=family).to_dict()
    strong_stable = {
        'theorem_status': 'proxy-stable-manifold-chart-identified',
        'stable_chart_radius': 0.03,
        'graph_transform_contraction': 0.81,
    }
    strong_coarse = {
        'theorem_status': 'proxy-critical-surface-family-bridge-identified',
        'critical_surface_gap': 0.04,
    }
    strong_validated = {
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
    }
    discharge = build_validated_critical_surface_theorem_discharge_certificate(
        family=family,
        validated_renormalization_package_promotion=renorm,
        stable_manifold_certificate=strong_stable,
        critical_surface_bridge_certificate=strong_coarse,
        validated_critical_surface_bridge_certificate=strong_validated,
        active_assumptions=[],
    ).to_dict()
    promotion = build_validated_critical_surface_theorem_promotion_certificate(
        family=family,
        discharge_certificate=discharge,
    ).to_dict()

    assert discharge['residual_burden_summary']['stable_manifold_equals_true_critical_surface'] is True
    assert discharge['residual_burden_summary']['critical_parameter_identification_certified'] is True
    assert discharge['residual_burden_summary']['critical_surface_transversality_certified'] is True
    assert promotion['theorem_flags']['stable_manifold_equals_true_critical_surface'] is True
    assert promotion['theorem_flags']['critical_parameter_identification_certified'] is True
    assert promotion['theorem_flags']['critical_surface_transversality_certified'] is True
    assert promotion['theorem_flags']['papergrade_final'] is True
