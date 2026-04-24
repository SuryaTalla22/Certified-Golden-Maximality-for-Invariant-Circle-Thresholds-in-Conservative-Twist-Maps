from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.universality_class import build_universality_class_certificate
from kam_theorem_suite.renormalization_class import build_renormalization_class_certificate
from kam_theorem_suite.validated_universality_class_theorem import (
    build_validated_universality_class_theorem_discharge_certificate,
    build_validated_universality_class_theorem_promotion_certificate,
)


def test_stage90_universality_class_finalization() -> None:
    family = HarmonicFamily()
    discharge = build_validated_universality_class_theorem_discharge_certificate(
        family=family,
        universality_class_certificate=build_universality_class_certificate(family).to_dict(),
        renormalization_class_certificate=build_renormalization_class_certificate(family).to_dict(),
        active_assumptions=[],
    ).to_dict()
    promotion = build_validated_universality_class_theorem_promotion_certificate(
        family=family,
        discharge_certificate=discharge,
    ).to_dict()

    assert discharge['theorem_flags']['banach_manifold_class_citeable'] is True
    assert discharge['residual_burden_summary']['papergrade_final'] is True
    assert promotion['theorem_flags']['banach_manifold_class_citeable'] is True
    assert promotion['theorem_flags']['papergrade_final'] is True
    assert promotion['residual_burden_summary']['papergrade_final'] is True
