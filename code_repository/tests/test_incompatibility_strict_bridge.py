from __future__ import annotations

from kam_theorem_suite.incompatibility_strict_bridge import (
    build_golden_incompatibility_strict_bridge_certificate,
)
from kam_theorem_suite.proof_driver import build_golden_incompatibility_strict_bridge_report


def test_strict_bridge_promotion_can_extract_strict_core(monkeypatch) -> None:
    import kam_theorem_suite.incompatibility_strict_bridge as isb

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(isb, 'build_golden_adaptive_tail_coherence_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-adaptive-tail-coherence-fragile',
        'clustered_entry_indices': [0, 1, 2],
        'successful_entry_indices': [0, 1, 2],
        'entries': [
            {
                'selected_upper_lo': 0.97, 'selected_upper_hi': 0.9704,
                'selected_barrier_lo': 1.02, 'selected_barrier_hi': 1.021,
                'witness_qs': [5, 8], 'generated_qs': [5, 8],
            },
            {
                'selected_upper_lo': 0.9701, 'selected_upper_hi': 0.9705,
                'selected_barrier_lo': 1.0202, 'selected_barrier_hi': 1.0212,
                'witness_qs': [5], 'generated_qs': [5, 8],
            },
            {
                'selected_upper_lo': 0.9702, 'selected_upper_hi': 0.97045,
                'selected_barrier_lo': 1.0201, 'selected_barrier_hi': 1.0211,
                'witness_qs': [5], 'generated_qs': [5, 8],
            },
        ],
    }))
    cert = build_golden_incompatibility_strict_bridge_certificate(
        min_cluster_size=2,
        min_tail_members=1,
        min_support_fraction=0.75,
        min_entry_coverage=0.75,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-incompatibility-theorem-bridge-strong'
    assert cert['source_name'] == 'strict-bridge-promotion'
    assert cert['certified_tail_qs'] == [5]
    assert cert['support_fraction_floor'] >= 0.75
    assert cert['entry_coverage_floor'] >= 0.75



def test_theorem_iv_uses_strict_bridge_promotion_when_direct_bridge_is_weak(monkeypatch) -> None:
    import kam_theorem_suite.theorem_iv_obstruction as tio

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    neutral = _Dummy({'selected_upper_lo': None, 'selected_upper_hi': None})
    monkeypatch.setattr(tio, 'build_golden_supercritical_obstruction_certificate', lambda **kwargs: _Dummy({'selected_upper_source': 'base', 'selected_upper_lo': None, 'selected_upper_hi': None, 'ladder': {}}))
    monkeypatch.setattr(tio, 'build_golden_supercritical_continuation_certificate', lambda **kwargs: _Dummy({}))
    monkeypatch.setattr(tio, 'build_golden_upper_support_audit_certificate', lambda **kwargs: _Dummy({}))
    monkeypatch.setattr(tio, 'build_golden_upper_tail_stability_certificate', lambda **kwargs: _Dummy({}))
    monkeypatch.setattr(tio, 'build_golden_adaptive_incompatibility_certificate', lambda **kwargs: _Dummy({}))
    monkeypatch.setattr(tio, 'build_golden_adaptive_tail_stability_certificate', lambda **kwargs: _Dummy({}))
    monkeypatch.setattr(tio, 'build_golden_adaptive_tail_coherence_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-adaptive-tail-coherence-fragile'}))
    monkeypatch.setattr(tio, 'build_golden_incompatibility_theorem_bridge_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-incompatibility-theorem-bridge-weak', 'source_name': 'direct-bridge', 'certified_upper_lo': 0.97, 'certified_upper_hi': 0.971, 'certified_barrier_lo': None, 'certified_barrier_hi': None, 'certified_tail_qs': [], 'certified_tail_is_suffix': False, 'missing_hypotheses': ['supporting_tail_exists']}))
    monkeypatch.setattr(tio, 'build_golden_incompatibility_strict_bridge_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-incompatibility-theorem-bridge-strong', 'source_name': 'strict-bridge-promotion', 'certified_upper_lo': 0.97, 'certified_upper_hi': 0.9705, 'certified_barrier_lo': 1.02, 'certified_barrier_hi': 1.021, 'certified_tail_qs': [8, 13], 'certified_tail_is_suffix': True, 'missing_hypotheses': []}))
    monkeypatch.setattr(tio, 'build_golden_incompatibility_bridge_profile_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-incompatibility-bridge-profile-weak', 'selected_bridge': {}}))
    monkeypatch.setattr(tio, 'certify_sustained_hyperbolic_tail', lambda *a, **k: _Dummy({}))
    cert = tio.build_golden_irrational_incompatibility_certificate().to_dict()
    assert cert['theorem_bridge']['source_name'] == 'strict-bridge-promotion'
    assert cert['selected_upper_source'] == 'strict-bridge-promotion'
    assert cert['theorem_status'] == 'golden-irrational-incompatibility-strong'



def test_nonexistence_front_uses_strict_bridge_promotion(monkeypatch) -> None:
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
    monkeypatch.setattr(nf, 'build_golden_incompatibility_theorem_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-theorem-bridge-weak',
        'certified_upper_lo': 0.95,
        'certified_upper_hi': 0.951,
        'certified_upper_width': 0.001,
        'certified_barrier_lo': None,
        'certified_barrier_hi': None,
        'certified_barrier_width': None,
        'certified_tail_qs': [],
        'certified_tail_is_suffix': False,
        'bridge_margin': -0.1,
        'missing_hypotheses': ['supporting_tail_exists'],
        'supporting_entry_count': 1,
        'support_fraction_floor': None,
        'entry_coverage_floor': None,
    }))
    monkeypatch.setattr(nf, 'build_golden_adaptive_support_core_neighborhood_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-adaptive-support-core-neighborhood-failed', 'selected_bridge': {'theorem_status': 'golden-incompatibility-theorem-bridge-failed'}}))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_strict_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-theorem-bridge-strong',
        'source_name': 'strict-bridge-promotion',
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
    monkeypatch.setattr(nf, 'build_golden_incompatibility_bridge_profile_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-incompatibility-bridge-profile-weak', 'selected_profile_name': 'none', 'selected_bridge': {}}))
    cert = nf.build_golden_nonexistence_front_certificate(base_K_values=[0.3]).to_dict()
    assert cert['relation']['upper_promotion_status'] == 'golden-incompatibility-theorem-bridge-strong'
    assert cert['upper_bridge']['source_name'] == 'strict-bridge-promotion'
    assert cert['theorem_status'] == 'golden-nonexistence-front-strong'



def test_driver_exposes_strict_bridge_report(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_incompatibility_strict_bridge_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-incompatibility-theorem-bridge-strong', 'source_name': 'strict-bridge-promotion'}})())
    report = build_golden_incompatibility_strict_bridge_report()
    assert report['theorem_status'].startswith('golden-incompatibility-theorem-bridge-')
    assert report['source_name'] == 'strict-bridge-promotion'
