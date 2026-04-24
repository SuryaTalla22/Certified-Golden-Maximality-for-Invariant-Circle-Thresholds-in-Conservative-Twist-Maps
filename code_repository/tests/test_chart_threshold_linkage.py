from __future__ import annotations

from kam_theorem_suite.chart_threshold_linkage import (
    build_chart_threshold_linkage_certificate,
    build_golden_chart_threshold_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_chart_threshold_linkage_report,
    build_golden_chart_threshold_bridge_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from tests.test_certified_tail_modulus_control import _synthetic_ladder


def _nearby_family() -> HarmonicFamily:
    return HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_chart_threshold_linkage_certificate_aligns_chart_window_with_threshold_packages(monkeypatch) -> None:
    import kam_theorem_suite.chart_threshold_linkage as ctl

    monkeypatch.setattr(
        ctl,
        'build_golden_lower_neighborhood_stability_certificate',
        lambda **kwargs: _Dummy({
            'stable_lower_bound': 0.97100,
            'stable_window_lo': 0.97100,
            'stable_window_hi': 0.97108,
            'theorem_status': 'golden-lower-neighborhood-stability-strong',
        }),
    )
    monkeypatch.setattr(
        ctl,
        'build_golden_irrational_incompatibility_certificate',
        lambda **kwargs: _Dummy({
            'selected_upper_lo': 0.97117,
            'selected_upper_hi': 0.97122,
            'selected_barrier_lo': 1.020,
            'selected_barrier_hi': 1.030,
            'theorem_status': 'golden-irrational-incompatibility-strong',
        }),
    )
    monkeypatch.setattr(
        ctl,
        'build_theorem_v_explicit_error_certificate',
        lambda *args, **kwargs: _Dummy({
            'compatible_limit_interval_lo': 0.97110,
            'compatible_limit_interval_hi': 0.97120,
            'theorem_status': 'theorem-v-explicit-error-law-strong',
        }),
    )

    cert = build_chart_threshold_linkage_certificate(
        family=_nearby_family(),
        family_label='nearby',
        threshold_center=0.97115,
        threshold_scale=2.0e-4,
        base_K_values=[0.9709, 0.9710, 0.97105],
        ladder=_synthetic_ladder(),
    )
    d = cert.to_dict()
    assert d['theorem_status'].startswith('chart-threshold-linkage-')
    assert d['theorem_flags']['renormalization_bridge_validated'] is True
    assert d['theorem_flags']['critical_window_intersects_theorem_v_interval'] is True
    assert d['linkage_relation']['critical_estimate_inside_theorem_v_interval'] is True
    assert d['linkage_relation']['critical_estimate_above_lower_bound'] is True
    assert d['linkage_relation']['critical_estimate_below_upper_bound'] is True
    assert d['mapped_critical_interval'][0] <= d['mapped_critical_center'] <= d['mapped_critical_interval'][1]


def test_golden_chart_threshold_bridge_builds_aligned_interval(monkeypatch) -> None:
    import kam_theorem_suite.chart_threshold_linkage as ctl

    monkeypatch.setattr(
        ctl,
        'build_chart_threshold_linkage_certificate',
        lambda **kwargs: _Dummy({
            'rho': 0.618,
            'family_label': 'nearby',
            'theorem_status': 'chart-threshold-linkage-strong',
            'linkage_relation': {
                'aligned_interval_lo': 0.97111,
                'aligned_interval_hi': 0.97115,
                'lower_to_upper_gap': 2.0e-4,
            },
        }),
    )
    cert = build_golden_chart_threshold_bridge_certificate(family=_nearby_family(), family_label='nearby')
    d = cert.to_dict()
    assert d['theorem_status'].startswith('golden-chart-threshold-bridge-')
    assert d['aligned_interval'] == [0.97111, 0.97115]
    assert d['theorem_flags']['aligned_interval_nonempty'] is True


def test_driver_reports_expose_chart_threshold_surfaces(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(
        pd,
        'build_chart_threshold_linkage_certificate',
        lambda **kwargs: _Dummy({'theorem_status': 'chart-threshold-linkage-moderate', 'mapped_critical_center': 0.97115}),
    )
    monkeypatch.setattr(
        pd,
        'build_golden_chart_threshold_bridge_certificate',
        lambda **kwargs: _Dummy({'theorem_status': 'golden-chart-threshold-bridge-partial', 'aligned_interval': None}),
    )

    report = build_chart_threshold_linkage_report(family=_nearby_family(), family_label='nearby')
    bridge = build_golden_chart_threshold_bridge_report(family=_nearby_family(), family_label='nearby')
    assert report['theorem_status'].startswith('chart-threshold-linkage-')
    assert bridge['theorem_status'].startswith('golden-chart-threshold-bridge-')
