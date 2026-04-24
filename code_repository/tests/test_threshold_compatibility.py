from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_threshold_compatibility_window_report,
    build_validated_threshold_compatibility_bridge_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.threshold_compatibility import (
    build_threshold_compatibility_window_certificate,
    build_validated_threshold_compatibility_bridge_certificate,
)


def _nearby_family() -> HarmonicFamily:
    return HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_threshold_compatibility_window_localizes_common_interval(monkeypatch) -> None:
    import kam_theorem_suite.threshold_compatibility as tc

    monkeypatch.setattr(
        tc,
        'build_chart_threshold_linkage_certificate',
        lambda **kwargs: _Dummy({
            'rho': 0.618,
            'family_label': 'nearby',
            'theorem_status': 'chart-threshold-linkage-strong',
            'mapped_critical_center': 0.971145,
            'mapped_critical_interval': [0.97112, 0.97118],
            'linkage_relation': {
                'lower_bound': 0.97105,
                'lower_window_lo': 0.97105,
                'lower_window_hi': 0.97111,
                'upper_hi': 0.97120,
                'theorem_v_interval_lo': 0.97110,
                'theorem_v_interval_hi': 0.97116,
            },
        }),
    )
    cert = build_threshold_compatibility_window_certificate(family=_nearby_family(), family_label='nearby')
    d = cert.to_dict()
    assert d['theorem_status'].startswith('threshold-compatibility-window-')
    assert d['theorem_flags']['compatibility_interval_nonempty'] is True
    assert d['compatibility_interval'] == [0.97112, 0.97116]
    assert d['theorem_flags']['compatibility_center_inside_two_sided_corridor'] is True
    assert d['theorem_flags']['compatibility_center_inside_theorem_v_interval'] is True


def test_validated_threshold_compatibility_bridge_builds_tightened_window(monkeypatch) -> None:
    import kam_theorem_suite.threshold_compatibility as tc

    monkeypatch.setattr(
        tc,
        'build_threshold_compatibility_window_certificate',
        lambda **kwargs: _Dummy({
            'rho': 0.618,
            'family_label': 'nearby',
            'theorem_status': 'threshold-compatibility-window-strong',
            'theorem_flags': {'compatibility_margins_positive': True},
            'compatibility_relation': {
                'tightened_window_lo': 0.97113,
                'tightened_window_hi': 0.97115,
            },
        }),
    )
    cert = build_validated_threshold_compatibility_bridge_certificate(family=_nearby_family(), family_label='nearby')
    d = cert.to_dict()
    assert d['validated_window'] == [0.97113, 0.97115]
    assert d['theorem_flags']['positive_localization_margins'] is True
    assert d['theorem_status'].startswith('validated-threshold-compatibility-bridge-')


def test_driver_reports_expose_threshold_compatibility_surfaces(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(
        pd,
        'build_threshold_compatibility_window_certificate',
        lambda **kwargs: _Dummy({'theorem_status': 'threshold-compatibility-window-moderate', 'compatibility_interval': [0.97112, 0.97115]}),
    )
    monkeypatch.setattr(
        pd,
        'build_validated_threshold_compatibility_bridge_certificate',
        lambda **kwargs: _Dummy({'theorem_status': 'validated-threshold-compatibility-bridge-weak', 'validated_window': None}),
    )

    report = build_threshold_compatibility_window_report(family=_nearby_family(), family_label='nearby')
    bridge = build_validated_threshold_compatibility_bridge_report(family=_nearby_family(), family_label='nearby')
    assert report['theorem_status'].startswith('threshold-compatibility-window-')
    assert bridge['theorem_status'].startswith('validated-threshold-compatibility-bridge-')
