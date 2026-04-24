from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.critical_surface import (
    build_family_transversality_certificate,
    build_critical_surface_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_family_transversality_report,
    build_critical_surface_bridge_report,
)


def _nearby_family() -> HarmonicFamily:
    return HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])


def test_family_transversality_certificate_brackets_codim_one_crossing() -> None:
    cert = build_family_transversality_certificate(_nearby_family(), family_label='nearby')
    assert cert.theorem_status.startswith('proxy-critical-surface-crossing-')
    assert cert.theorem_flags['codim_one_unstable'] is True
    assert cert.theorem_flags['sign_change_detected'] is True
    assert cert.theorem_flags['transverse_crossing_detected'] is True
    assert cert.selected_crossing_interval is not None
    assert cert.transversality_margin > 0.0
    assert len(cert.samples) >= 3


def test_critical_surface_bridge_report_exposes_localized_crossing_window() -> None:
    report = build_critical_surface_bridge_report(family=_nearby_family(), family_label='nearby')
    assert report['theorem_status'].startswith('proxy-critical-surface-family-bridge-')
    assert report['critical_window_radius'] is not None
    assert report['theorem_flags']['critical_window_localized'] is True
    assert 'transversality_certificate' in report


def test_driver_reports_expose_transversality_and_bridge_surfaces() -> None:
    family = _nearby_family()
    trans = build_family_transversality_report(family=family, family_label='nearby')
    bridge = build_critical_surface_bridge_report(family=family, family_label='nearby')
    assert trans['theorem_status'].startswith('proxy-critical-surface-crossing-')
    assert bridge['theorem_status'].startswith('proxy-critical-surface-family-bridge-')
    assert 'samples' in trans
    assert 'critical_window_center' in bridge
