from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.renormalization import build_renormalization_operator_certificate
from kam_theorem_suite.renormalization_fixed_point import build_renormalization_fixed_point_certificate
from kam_theorem_suite.linearization_bounds import build_linearization_bounds_certificate
from kam_theorem_suite.proof_driver import (
    build_renormalization_operator_report,
    build_renormalization_fixed_point_report,
    build_linearization_bounds_report,
)


def _nearby_family() -> HarmonicFamily:
    return HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])


def test_proxy_operator_normalizes_anchor_and_contracts_higher_modes() -> None:
    cert = build_renormalization_operator_certificate(_nearby_family(), family_label='nearby')
    assert cert.operator_status.startswith('proxy-renormalization-operator-')
    assert cert.operator_flags['anchor_normalized'] is True
    assert cert.operator_flags['higher_modes_nonexpanding'] is True
    assert cert.contraction_metrics['higher_mode_energy_ratio'] <= 1.0 + 1e-12
    assert cert.contraction_metrics['phase_ratio'] <= 1.0 + 1e-12


def test_fixed_point_iteration_records_nonincreasing_defects_for_nearby_family() -> None:
    cert = build_renormalization_fixed_point_certificate(_nearby_family(), family_label='nearby', iterations=5)
    assert cert.theorem_status.startswith('proxy-fixed-point-iteration-')
    assert len(cert.nodes) == 5
    assert cert.defect_history_nonincreasing is True
    assert cert.radius_history_nonincreasing is True
    assert cert.final_fixed_point_defect >= 0.0


def test_linearization_bounds_expose_chart_jacobian_proxy() -> None:
    cert = build_linearization_bounds_certificate(_nearby_family(), family_label='nearby')
    assert cert.theorem_status.startswith('proxy-linearization-bounds-')
    assert len(cert.jacobian_proxy) == 4
    assert all(len(row) == 4 for row in cert.jacobian_proxy)
    assert cert.spectral_radius_upper_bound >= cert.stable_radius_upper_bound
    assert cert.linearization_flags['stable_proxy_contracting'] is True
    assert cert.linearization_flags['unstable_proxy_identified'] is True


def test_driver_reports_expose_new_renormalization_surfaces() -> None:
    family = _nearby_family()
    op = build_renormalization_operator_report(family=family, family_label='nearby')
    fp = build_renormalization_fixed_point_report(family=family, family_label='nearby', iterations=4)
    lin = build_linearization_bounds_report(family=family, family_label='nearby')
    assert op['operator_status'].startswith('proxy-renormalization-operator-')
    assert fp['theorem_status'].startswith('proxy-fixed-point-iteration-')
    assert lin['theorem_status'].startswith('proxy-linearization-bounds-')
    assert 'output_chart_profile' in op
    assert 'final_chart_profile' in fp
    assert 'jacobian_proxy' in lin
