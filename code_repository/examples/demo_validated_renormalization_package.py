from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.validated_renormalization_package import (
    build_validated_renormalization_package_discharge_certificate,
    build_validated_renormalization_package_promotion_certificate,
)

family = HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])

discharge = build_validated_renormalization_package_discharge_certificate(
    family=family,
    active_assumptions=['theorem_grade_banach_manifold_universality_class'],
)
promotion = build_validated_renormalization_package_promotion_certificate(
    family=family,
    discharge_certificate=discharge.to_dict(),
)

print('discharge theorem status:', discharge.theorem_status)
print('promotion theorem status:', promotion.theorem_status)
print('promotion residual burden:', promotion.residual_burden_summary)
