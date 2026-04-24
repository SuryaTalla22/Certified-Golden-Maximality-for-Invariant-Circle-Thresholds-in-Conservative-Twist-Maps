from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.stable_manifold import build_stable_manifold_chart_certificate
from kam_theorem_suite.proof_driver import build_stable_manifold_chart_report


def _nearby_family() -> HarmonicFamily:
    return HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])


def test_stable_manifold_chart_identifies_local_graph_transform_proxy() -> None:
    cert = build_stable_manifold_chart_certificate(_nearby_family(), family_label='nearby')
    assert cert.theorem_status.startswith('proxy-stable-manifold-chart-')
    assert cert.unstable_dimension == 1
    assert cert.stable_dimension >= 1
    assert cert.manifold_flags['stable_block_contracting'] is True
    assert cert.manifold_flags['unstable_block_expanding'] is True
    assert cert.graph_transform_contraction < 1.0
    assert cert.stable_chart_radius > 0.0
    assert len(cert.chart_sample_points) >= 1


def test_driver_report_exposes_stable_manifold_chart_surface() -> None:
    report = build_stable_manifold_chart_report(family=_nearby_family(), family_label='nearby')
    assert report['theorem_status'].startswith('proxy-stable-manifold-chart-')
    assert 'transformed_jacobian' in report
    assert 'chart_sample_points' in report


def test_default_golden_family_now_carries_positive_radius_witness() -> None:
    cert = build_stable_manifold_chart_certificate(HarmonicFamily())
    assert cert.theorem_status == 'proxy-stable-manifold-chart-identified'
    assert cert.stable_chart_radius > 0.0
    assert cert.validated_chart_radius_lower_bound == cert.stable_chart_radius
    assert cert.radius_components['spectral_gap_radius_lower_bound'] > 0.0 or cert.radius_components['stable_direction_radius_lower_bound'] > 0.0
    assert cert.manifold_flags['radius_witness_from_enclosure_or_gap'] is True
