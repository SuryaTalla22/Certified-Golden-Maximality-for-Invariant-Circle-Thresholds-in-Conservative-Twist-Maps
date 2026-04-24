from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.transversality_window import (
    build_transversality_window_certificate,
    build_validated_critical_surface_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_transversality_window_report,
    build_validated_critical_surface_bridge_report,
)


def _nearby_family() -> HarmonicFamily:
    return HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])


def test_transversality_window_certificate_localizes_crossing_with_positive_floor() -> None:
    cert = build_transversality_window_certificate(_nearby_family(), family_label='nearby')
    assert cert.theorem_status.startswith('proxy-transversality-window-')
    assert cert.localized_window is not None
    assert cert.window_radius is not None
    assert cert.window_radius <= cert.path_parameters['target_window_radius'] + 1e-12
    assert cert.theorem_flags['endpoint_sign_change'] is True
    assert cert.theorem_flags['derivative_floor_positive'] is True
    assert cert.derivative_floor_proxy > cert.path_parameters['transversality_floor']
    assert len(cert.window_samples) >= 5


def test_validated_critical_surface_bridge_upgrades_coarse_bridge() -> None:
    cert = build_validated_critical_surface_bridge_certificate(_nearby_family(), family_label='nearby')
    assert cert.theorem_status.startswith('proxy-critical-surface-window-bridge-')
    assert cert.localized_radius is not None
    assert cert.theorem_flags['localized_transversality_window'] is True
    assert cert.theorem_flags['endpoint_sign_change'] is True
    assert cert.theorem_flags['derivative_floor_positive'] is True


def test_driver_reports_expose_window_surfaces() -> None:
    family = _nearby_family()
    window = build_transversality_window_report(family=family, family_label='nearby')
    bridge = build_validated_critical_surface_bridge_report(family=family, family_label='nearby')
    assert window['theorem_status'].startswith('proxy-transversality-window-')
    assert bridge['theorem_status'].startswith('proxy-critical-surface-window-bridge-')
    assert 'window_samples' in window
    assert 'transversality_window_certificate' in bridge
