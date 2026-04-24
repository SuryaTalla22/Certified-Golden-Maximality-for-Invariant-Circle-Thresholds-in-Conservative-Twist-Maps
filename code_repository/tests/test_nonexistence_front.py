from __future__ import annotations

from kam_theorem_suite.nonexistence_front import (
    build_golden_nonexistence_front_certificate,
)
from kam_theorem_suite.proof_driver import build_golden_nonexistence_front_report


def test_golden_nonexistence_front_smoke(monkeypatch) -> None:
    import kam_theorem_suite.nonexistence_front as nf

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(nf, 'build_golden_lower_neighborhood_stability_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-lower-neighborhood-stability-strong',
        'stable_lower_bound': 0.5,
        'stable_window_hi': 0.55,
        'stable_window_width': 0.05,
        'distinct_resolution_signatures': [[64, 96, 128], [80, 112, 144]],
    }))
    monkeypatch.setattr(nf, 'build_golden_adaptive_support_core_neighborhood_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-adaptive-support-core-neighborhood-failed', 'selected_bridge': {'theorem_status': 'golden-incompatibility-theorem-bridge-failed'}}))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_strict_bridge_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-incompatibility-theorem-bridge-failed', 'missing_hypotheses': ['supporting_tail_exists']}))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_theorem_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-theorem-bridge-strong',
        'certified_upper_lo': 0.97,
        'certified_upper_hi': 0.971,
        'certified_upper_width': 0.001,
        'certified_barrier_lo': 1.02,
        'certified_barrier_hi': 1.03,
        'certified_barrier_width': 0.01,
        'certified_tail_qs': [8, 13],
        'certified_tail_is_suffix': True,
        'bridge_margin': 0.1,
        'missing_hypotheses': [],
        'supporting_entry_count': 2,
        'support_fraction_floor': 1.0,
        'entry_coverage_floor': 1.0,
    }))
    cert = build_golden_nonexistence_front_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-nonexistence-front-strong'
    assert cert['missing_hypotheses'] == []
    assert cert['relation']['gap_to_upper'] > 0
    assert cert['remaining_analytic_lifts']


def test_front_can_be_moderate_when_upper_or_lower_is_not_fully_closed(monkeypatch) -> None:
    import kam_theorem_suite.nonexistence_front as nf

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(nf, 'build_golden_lower_neighborhood_stability_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-lower-neighborhood-stability-weak',
        'stable_lower_bound': 0.8,
        'stable_window_hi': 0.81,
        'stable_window_width': 0.01,
        'distinct_resolution_signatures': [[64, 96, 128]],
    }))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_theorem_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-theorem-bridge-moderate',
        'certified_upper_lo': 0.95,
        'certified_upper_hi': 0.951,
        'certified_upper_width': 0.001,
        'certified_barrier_lo': 1.0,
        'certified_barrier_hi': 1.01,
        'certified_barrier_width': 0.01,
        'certified_tail_qs': [8],
        'certified_tail_is_suffix': False,
        'bridge_margin': -0.05,
        'missing_hypotheses': ['gap_dominates_localization'],
        'supporting_entry_count': 1,
        'support_fraction_floor': 0.5,
        'entry_coverage_floor': 0.5,
    }))
    cert = build_golden_nonexistence_front_certificate(base_K_values=[0.3], min_tail_members=1).to_dict()
    assert cert['theorem_status'] == 'golden-nonexistence-front-moderate'
    assert 'upper_bridge_closed' in cert['missing_hypotheses']


def test_driver_exposes_nonexistence_front(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_nonexistence_front_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-nonexistence-front-weak', 'relation': {'gap_to_upper': 0.2}, 'remaining_analytic_lifts': [{'name': 'obstruction_implies_no_analytic_circle'}]}})())
    report = build_golden_nonexistence_front_report(base_K_values=[0.3])
    assert report['theorem_status'].startswith('golden-nonexistence-front-')
    assert report['remaining_analytic_lifts']
