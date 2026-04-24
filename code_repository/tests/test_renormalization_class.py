from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.renormalization_class import (
    build_renormalization_chart_profile,
    build_renormalization_class_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_universality_class_report,
    build_renormalization_class_report,
)


def test_chart_profile_for_nearby_family_is_small() -> None:
    family = HarmonicFamily(harmonics=[(1.02, 1, 0.01), (0.04, 2, 0.0)])
    profile = build_renormalization_chart_profile(family)
    assert profile.chart_radius_proxy >= 0.0
    assert profile.transversality_proxy > 0.0


def test_near_standard_family_is_chart_admissible() -> None:
    family = HarmonicFamily(harmonics=[(1.03, 1, 0.02), (0.05, 2, 0.01)])
    cert = build_renormalization_class_certificate(family, family_label='near_chart')
    assert cert.admissible_near_chart is True
    assert cert.chart_flags['transversality'] is True


def test_driver_reports_expose_new_scaffolding() -> None:
    family = HarmonicFamily()
    uni = build_universality_class_report(family=family, family_label='standard')
    ren = build_renormalization_class_report(family=family, family_label='standard')
    assert uni['admissible'] is True
    assert 'analytic_profile' in uni
    assert ren['admissible_near_chart'] is True
    assert 'chart_profile' in ren
