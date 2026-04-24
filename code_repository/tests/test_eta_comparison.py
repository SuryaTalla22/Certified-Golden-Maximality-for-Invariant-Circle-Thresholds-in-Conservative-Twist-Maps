from __future__ import annotations

from kam_theorem_suite.eta_comparison import (
    build_eta_threshold_comparison_certificate,
    build_proto_envelope_eta_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_eta_threshold_comparison_report,
    build_proto_envelope_eta_bridge_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def _nearby_family() -> HarmonicFamily:
    return HarmonicFamily(harmonics=[(1.03, 1, 0.03), (0.08, 2, -0.01), (0.02, 3, 0.01)])


def test_eta_threshold_comparison_builds_local_anchor(monkeypatch) -> None:
    import kam_theorem_suite.eta_comparison as ec

    monkeypatch.setattr(
        ec,
        'build_validated_threshold_compatibility_bridge_certificate',
        lambda **kwargs: _Dummy({
            'theorem_status': 'validated-threshold-compatibility-bridge-strong',
            'validated_window': [0.97113, 0.97115],
            'certified_center': 0.97114,
            'certified_radius': 1.0e-5,
        }),
    )
    monkeypatch.setattr(ec, 'golden_inverse', lambda: 0.6180339887498948)

    cert = build_eta_threshold_comparison_certificate(family=_nearby_family())
    d = cert.to_dict()
    assert d['theorem_status'].startswith('eta-threshold-comparison-')
    assert d['eta_interval'] is not None
    assert d['threshold_interval'] == [0.97113, 0.97115]
    assert d['theorem_flags']['golden_endpoint_anchor'] is True
    assert d['local_envelope_anchor']['threshold_lower'] == 0.97113


def test_proto_envelope_eta_bridge_reports_positive_panel_gap(monkeypatch) -> None:
    import kam_theorem_suite.eta_comparison as ec

    monkeypatch.setattr(
        ec,
        'build_eta_threshold_comparison_certificate',
        lambda **kwargs: _Dummy({
            'theorem_status': 'eta-threshold-comparison-strong',
            'local_envelope_anchor': {
                'threshold_lower': 0.97113,
                'threshold_upper': 0.97115,
                'eta_center': 1 / (5 ** 0.5),
            },
        }),
    )
    panel_records = [
        {'eta_approx': 1 / (5 ** 0.5), 'threshold_lo': 0.97113, 'threshold_hi': 0.97115, 'is_golden': True},
        {'eta_approx': 1 / (8 ** 0.5), 'threshold_lo': 0.97085, 'threshold_hi': 0.97095, 'is_golden': False},
    ]
    cert = build_proto_envelope_eta_bridge_certificate(family=_nearby_family(), panel_records=panel_records)
    d = cert.to_dict()
    assert d['theorem_status'].startswith('proto-envelope-eta-bridge-')
    assert d['theorem_flags']['panel_gap_positive'] is True
    assert d['proto_envelope_relation']['anchor_lower_minus_panel_nongolden_upper'] > 0.0


def test_driver_reports_expose_eta_comparison_surfaces(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(
        pd,
        'build_eta_threshold_comparison_certificate',
        lambda **kwargs: _Dummy({'theorem_status': 'eta-threshold-comparison-moderate', 'eta_interval': [0.44, 0.45]}),
    )
    monkeypatch.setattr(
        pd,
        'build_proto_envelope_eta_bridge_certificate',
        lambda **kwargs: _Dummy({'theorem_status': 'proto-envelope-eta-bridge-weak', 'proto_envelope_relation': {}}),
    )
    report = build_eta_threshold_comparison_report(family=_nearby_family(), family_label='nearby')
    bridge = build_proto_envelope_eta_bridge_report(family=_nearby_family(), family_label='nearby')
    assert report['theorem_status'].startswith('eta-threshold-comparison-')
    assert bridge['theorem_status'].startswith('proto-envelope-eta-bridge-')


def test_proto_envelope_eta_bridge_exposes_one_variable_statement_mode_certificate(monkeypatch) -> None:
    import kam_theorem_suite.eta_comparison as ec

    monkeypatch.setattr(
        ec,
        'build_eta_threshold_comparison_certificate',
        lambda **kwargs: _Dummy({
            'theorem_status': 'eta-threshold-comparison-strong',
            'local_envelope_anchor': {
                'threshold_lower': 0.97113,
                'threshold_upper': 0.97115,
                'eta_center': 1 / (5 ** 0.5),
            },
        }),
    )
    panel_records = [
        {'eta_approx': 1 / (5 ** 0.5), 'threshold_lo': 0.97113, 'threshold_hi': 0.97115, 'is_golden': True},
        {'eta_approx': 0.40, 'threshold_lo': 0.97092, 'threshold_hi': 0.97094, 'is_golden': False},
        {'eta_approx': 0.35, 'threshold_lo': 0.97084, 'threshold_hi': 0.97086, 'is_golden': False},
    ]
    cert = build_proto_envelope_eta_bridge_certificate(family=_nearby_family(), panel_records=panel_records)
    d = cert.to_dict()
    assert d['statement_mode_certificate']['candidate_mode'] == 'one-variable'
    assert d['statement_mode_certificate']['mode_lock_status'] == 'one-variable-supported'
