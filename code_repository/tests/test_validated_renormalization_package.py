from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.validated_renormalization_package import (
    build_validated_renormalization_package_discharge_certificate,
    build_validated_renormalization_package_promotion_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_validated_renormalization_package_discharge_report,
    build_validated_renormalization_package_promotion_report,
)


def _nearby_family() -> HarmonicFamily:
    return HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])


def test_validated_renormalization_package_discharge_is_machine_readable() -> None:
    cert = build_validated_renormalization_package_discharge_certificate(
        family=_nearby_family(),
        active_assumptions=['theorem_grade_banach_manifold_universality_class'],
    ).to_dict()
    assert cert['theorem_status'].startswith('validated-renormalization-package-discharge-')
    assert 'hypotheses' in cert
    assert 'residual_burden_summary' in cert
    assert 'package_specific_assumptions' in cert


def test_validated_renormalization_package_promotion_absorbs_package_specific_assumptions_when_local_front_complete() -> None:
    discharge = build_validated_renormalization_package_discharge_certificate(
        renormalization_class_certificate={'admissible_near_chart': True, 'status': 'near_golden_chart_scaffold', 'chart_margins': {'a': 0.2}},
        renormalization_operator_certificate={'operator_status': 'proxy-renormalization-operator-stable-chart', 'contraction_metrics': {'chart_radius_ratio': 0.7}},
        fixed_point_certificate={'theorem_status': 'proxy-fixed-point-iteration-contracting', 'contraction_ratio_estimate': 0.6},
        fixed_point_enclosure_certificate={'theorem_status': 'proxy-fixed-point-enclosure-validated', 'invariance_margin': 0.05},
        spectral_splitting_certificate={'theorem_status': 'proxy-spectral-splitting-identified', 'domination_margin': 0.11},
        stable_manifold_certificate={'theorem_status': 'proxy-stable-manifold-chart-identified', 'stable_chart_radius': 0.03, 'graph_transform_contraction': 0.81},
        active_assumptions=['theorem_grade_banach_manifold_universality_class'],
    ).to_dict()
    promotion = build_validated_renormalization_package_promotion_certificate(discharge_certificate=discharge).to_dict()
    assert promotion['theorem_status'] == 'validated-renormalization-package-promotion-theorem-conditional-strong'
    assert promotion['theorem_flags']['validated_true_renormalization_fixed_point_package_available'] is True
    assert promotion['package_specific_assumptions'] == []
    assert promotion['upstream_context_assumptions'] == ['theorem_grade_banach_manifold_universality_class']


def test_driver_reports_expose_validated_renormalization_package_surfaces() -> None:
    discharge = build_validated_renormalization_package_discharge_report(family=_nearby_family())
    promotion = build_validated_renormalization_package_promotion_report(family=_nearby_family())
    assert discharge['theorem_status'].startswith('validated-renormalization-package-discharge-')
    assert promotion['theorem_status'].startswith('validated-renormalization-package-promotion-theorem-')
    assert 'residual_burden_summary' in promotion


def test_default_golden_family_now_yields_discharged_validated_renormalization_package() -> None:
    promotion = build_validated_renormalization_package_promotion_certificate(family=HarmonicFamily()).to_dict()
    assert promotion['theorem_status'] == 'validated-renormalization-package-promotion-theorem-discharged'
    assert promotion['residual_burden_summary']['status'] == 'validated-renormalization-package-discharged'
    assert promotion['theorem_flags']['validated_true_renormalization_fixed_point_package_available'] is True
