from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.fixed_point_enclosure import build_fixed_point_enclosure_certificate
from kam_theorem_suite.spectral_splitting import build_spectral_splitting_certificate
from kam_theorem_suite.proof_driver import (
    build_fixed_point_enclosure_report,
    build_spectral_splitting_report,
)


def _nearby_family() -> HarmonicFamily:
    return HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])


def test_fixed_point_enclosure_is_positive_and_machine_readable() -> None:
    cert = build_fixed_point_enclosure_certificate(_nearby_family(), family_label='nearby')
    assert cert.theorem_status.startswith('proxy-fixed-point-enclosure-')
    assert cert.enclosure_flags['iteration_contracting'] is True
    assert cert.enclosure_flags['chart_contracting'] is True
    assert cert.enclosure_flags['invariance_margin_positive'] is True
    assert cert.enclosure_radius >= 0.0
    assert 'anchor_phase_shift' in cert.coordinate_enclosure


def test_spectral_splitting_identifies_transverse_unstable_proxy() -> None:
    cert = build_spectral_splitting_certificate(_nearby_family(), family_label='nearby')
    assert cert.theorem_status.startswith('proxy-spectral-splitting-')
    assert cert.unstable_dimension == 1
    assert cert.stable_dimension >= 1
    assert cert.splitting_flags['stable_cluster_contracting'] is True
    assert cert.splitting_flags['spectral_gap_identified'] is True
    assert cert.transverse_multiplier > 1.0


def test_driver_reports_expose_enclosure_and_splitting_surfaces() -> None:
    family = _nearby_family()
    enc = build_fixed_point_enclosure_report(family=family, family_label='nearby')
    split = build_spectral_splitting_report(family=family, family_label='nearby')
    assert enc['theorem_status'].startswith('proxy-fixed-point-enclosure-')
    assert split['theorem_status'].startswith('proxy-spectral-splitting-')
    assert 'coordinate_enclosure' in enc
    assert 'augmented_jacobian_proxy' in split
