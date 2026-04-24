from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.universality_class import (
    build_family_analytic_profile,
    build_family_normalization_profile,
    build_universality_class_certificate,
)


def test_family_profiles_standard_map_are_well_formed() -> None:
    family = HarmonicFamily()
    analytic = build_family_analytic_profile(family)
    norm = build_family_normalization_profile(family)
    assert analytic.harmonic_count == 1
    assert analytic.max_mode == 1
    assert analytic.anchor_amplitude == 1.0
    assert analytic.anchor_phase == 0.0
    assert analytic.strip_width_proxy >= 0.03
    assert norm.normalization_score >= 0.0


def test_standard_family_is_admissible_in_scaffold_class() -> None:
    cert = build_universality_class_certificate(HarmonicFamily(), family_label='standard')
    assert cert.admissible is True
    assert cert.status == 'admissible'
    assert cert.admissibility_flags['anchor_amplitude'] is True
    assert cert.admissibility_flags['twist'] is True


def test_heavily_distorted_family_fails_admissibility() -> None:
    family = HarmonicFamily(harmonics=[(1.9, 1, 1.1), (1.2, 6, 0.4), (0.8, 9, -0.2)])
    cert = build_universality_class_certificate(family, family_label='distorted', max_mode_allowed=8)
    assert cert.admissible is False
    assert cert.admissibility_flags['max_mode'] is False or cert.admissibility_flags['anchor_amplitude'] is False
