from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.validated_critical_surface_theorem import (
    build_validated_critical_surface_theorem_discharge_certificate,
    build_validated_critical_surface_theorem_promotion_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_validated_critical_surface_theorem_discharge_report,
    build_validated_critical_surface_theorem_promotion_report,
)


def test_validated_critical_surface_theorem_discharge_is_machine_readable() -> None:
    cert = build_validated_critical_surface_theorem_discharge_certificate(
        family=HarmonicFamily(),
        active_assumptions=[
            'golden_stable_manifold_is_true_critical_surface',
            'family_chart_crossing_identifies_true_critical_parameter',
        ],
    ).to_dict()
    assert cert['theorem_status'].startswith('validated-critical-surface-theorem-discharge-')
    assert 'hypotheses' in cert
    assert 'residual_burden_summary' in cert


def test_validated_critical_surface_theorem_promotion_absorbs_workstream_specific_assumptions_when_local_front_is_complete() -> None:
    discharge = build_validated_critical_surface_theorem_discharge_certificate(
        family=HarmonicFamily(),
        validated_renormalization_package_promotion={
            'theorem_flags': {'validated_true_renormalization_fixed_point_package_available': True},
            'promotion_margin': 0.03,
        },
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
    promotion = build_validated_critical_surface_theorem_promotion_certificate(
        family=HarmonicFamily(),
        discharge_certificate=discharge,
    ).to_dict()
    assert promotion['theorem_status'] == 'validated-critical-surface-theorem-promotion-conditional-strong'
    assert promotion['theorem_flags']['workstream_specific_critical_surface_theorem_available'] is True
    assert promotion['active_assumptions'] == ['theorem_grade_banach_manifold_universality_class']
    assert promotion['absorbed_package_specific_assumptions'] == [
        'golden_stable_manifold_is_true_critical_surface',
        'family_chart_crossing_identifies_true_critical_parameter',
        'golden_critical_surface_transversality_on_class',
    ]


def test_driver_reports_expose_validated_critical_surface_theorem_surfaces() -> None:
    discharge = build_validated_critical_surface_theorem_discharge_report(family=HarmonicFamily())
    promotion = build_validated_critical_surface_theorem_promotion_report(family=HarmonicFamily())
    assert discharge['theorem_status'].startswith('validated-critical-surface-theorem-discharge-')
    assert promotion['theorem_status'].startswith('validated-critical-surface-theorem-promotion-')
