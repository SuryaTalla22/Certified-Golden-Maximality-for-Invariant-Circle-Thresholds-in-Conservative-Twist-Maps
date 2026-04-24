from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_validated_universality_class_theorem_discharge_report,
    build_validated_universality_class_theorem_promotion_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.validated_universality_class_theorem import (
    build_validated_universality_class_theorem_discharge_certificate,
    build_validated_universality_class_theorem_promotion_certificate,
)


_BASE_UNIVERSALITY = {
    'admissible': True,
    'status': 'admissible',
    'admissibility_margins': {
        'exact_symplectic_margin': 1.0e-12,
        'twist_margin': 1.0,
        'anchor_amplitude_margin': 0.2,
        'anchor_phase_margin': 0.1,
        'higher_mode_energy_margin': 0.3,
        'weighted_mode_budget_margin': 2.0,
        'max_mode_margin': 4.0,
        'strip_width_margin': 0.05,
    },
}

_BASE_RENORM_CLASS = {
    'admissible_near_chart': True,
    'status': 'near_golden_chart_scaffold',
    'chart_margins': {'chart_margin': 0.1},
}


def test_validated_universality_class_discharge_certificate_builds_machine_readably() -> None:
    cert = build_validated_universality_class_theorem_discharge_certificate(
        family=HarmonicFamily(),
        universality_class_certificate=_BASE_UNIVERSALITY,
        renormalization_class_certificate=_BASE_RENORM_CLASS,
        active_assumptions=['theorem_grade_banach_manifold_universality_class'],
    ).to_dict()
    assert cert['local_front_complete'] is True
    assert cert['theorem_status'] == 'validated-universality-class-theorem-front-complete'
    assert cert['package_specific_assumptions'] == ['theorem_grade_banach_manifold_universality_class']
    assert cert['residual_burden_summary']['status'] == 'validated-universality-class-theorem-promotion-frontier'


def test_validated_universality_class_promotion_becomes_available_when_assumption_clears() -> None:
    discharge = build_validated_universality_class_theorem_discharge_certificate(
        family=HarmonicFamily(),
        universality_class_certificate=_BASE_UNIVERSALITY,
        renormalization_class_certificate=_BASE_RENORM_CLASS,
        active_assumptions=[],
    ).to_dict()
    promotion = build_validated_universality_class_theorem_promotion_certificate(
        family=HarmonicFamily(),
        discharge_certificate=discharge,
    ).to_dict()
    assert promotion['promotion_theorem_available'] is True
    assert promotion['promotion_theorem_discharged'] is True
    assert promotion['theorem_flags']['theorem_grade_banach_manifold_universality_class_available'] is True
    assert promotion['theorem_status'] == 'validated-universality-class-theorem-promotion-discharged'


def test_validated_universality_class_reports_roundtrip() -> None:
    discharge = build_validated_universality_class_theorem_discharge_report(
        family=HarmonicFamily(),
        universality_class_certificate=_BASE_UNIVERSALITY,
        renormalization_class_certificate=_BASE_RENORM_CLASS,
        active_assumptions=['theorem_grade_banach_manifold_universality_class'],
    )
    promotion = build_validated_universality_class_theorem_promotion_report(
        family=HarmonicFamily(),
        discharge_certificate=discharge,
    )
    assert discharge['theorem_status'] == 'validated-universality-class-theorem-front-complete'
    assert promotion['theorem_status'] == 'validated-universality-class-theorem-promotion-discharged'
