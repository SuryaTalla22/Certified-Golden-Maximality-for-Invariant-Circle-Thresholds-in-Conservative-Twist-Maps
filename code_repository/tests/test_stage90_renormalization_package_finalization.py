from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.validated_renormalization_package import (
    build_validated_renormalization_package_discharge_certificate,
    build_validated_renormalization_package_promotion_certificate,
)


def test_stage90_renormalization_package_finalization() -> None:
    family = HarmonicFamily()
    discharge = build_validated_renormalization_package_discharge_certificate(
        family=family,
        active_assumptions=[],
    ).to_dict()
    promotion = build_validated_renormalization_package_promotion_certificate(
        family=family,
        discharge_certificate=discharge,
    ).to_dict()

    assert discharge['residual_burden_summary']['true_fixed_point_package_certified'] is True
    assert discharge['residual_burden_summary']['spectral_splitting_citeable'] is True
    assert discharge['residual_burden_summary']['stable_manifold_citeable'] is True
    assert promotion['theorem_flags']['true_fixed_point_package_certified'] is True
    assert promotion['theorem_flags']['spectral_splitting_citeable'] is True
    assert promotion['theorem_flags']['stable_manifold_citeable'] is True
    assert promotion['theorem_flags']['papergrade_final'] is True
