from __future__ import annotations

from kam_theorem_suite.incompatibility_bridge_profile import (
    build_golden_incompatibility_bridge_profile_certificate,
)
from kam_theorem_suite.nonexistence_front import (
    build_golden_nonexistence_front_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_golden_incompatibility_bridge_profile_report,
)


def test_bridge_profile_selects_best_available_profile(monkeypatch) -> None:
    import kam_theorem_suite.incompatibility_bridge_profile as ibp

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    def _stub_bridge(**kwargs):
        ratio = kwargs.get('min_gap_to_width_ratio', 1.0)
        if ratio >= 1.0:
            return _Dummy({'theorem_status': 'golden-incompatibility-theorem-bridge-failed', 'bridge_margin': -1.0})
        if ratio >= 0.5:
            return _Dummy({'theorem_status': 'golden-incompatibility-theorem-bridge-strong', 'bridge_margin': 0.2, 'certified_tail_qs': [8, 13], 'supporting_entry_count': 2})
        return _Dummy({'theorem_status': 'golden-incompatibility-theorem-bridge-moderate', 'bridge_margin': 0.1, 'certified_tail_qs': [8], 'supporting_entry_count': 1})

    monkeypatch.setattr(ibp, 'build_golden_incompatibility_theorem_bridge_certificate', _stub_bridge)
    cert = build_golden_incompatibility_bridge_profile_certificate().to_dict()
    assert cert['selected_profile_name'] == 'balanced'
    assert cert['selected_bridge']['theorem_status'] == 'golden-incompatibility-theorem-bridge-strong'
    assert cert['viable_profile_count'] == 2
    assert cert['theorem_status'].startswith('golden-incompatibility-bridge-profile-')



def test_nonexistence_front_uses_profile_when_direct_bridge_fails(monkeypatch) -> None:
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
    monkeypatch.setattr(nf, 'build_golden_adaptive_tail_aware_neighborhood_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-adaptive-tail-aware-neighborhood-failed', 'selected_bridge': {'theorem_status': 'golden-incompatibility-theorem-bridge-failed'}}))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_strict_bridge_certificate', lambda **kwargs: _Dummy({'theorem_status': 'golden-incompatibility-theorem-bridge-failed', 'missing_hypotheses': ['supporting_tail_exists']}))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_theorem_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-theorem-bridge-failed',
        'missing_hypotheses': ['coherent_upper_object'],
    }))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_bridge_profile_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-bridge-profile-moderate',
        'selected_profile_name': 'balanced',
        'viable_profile_count': 2,
        'strong_profile_count': 1,
        'selected_bridge': {
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
        },
    }))
    cert = build_golden_nonexistence_front_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-nonexistence-front-strong'
    assert cert['relation']['upper_status'] == 'golden-incompatibility-theorem-bridge-strong'
    assert cert['relation']['upper_profile_selected_name'] == 'balanced'



def test_driver_exposes_bridge_profile_report(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_incompatibility_bridge_profile_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-incompatibility-bridge-profile-weak', 'selected_profile_name': 'lightweight'}})())
    report = build_golden_incompatibility_bridge_profile_report()
    assert report['theorem_status'].startswith('golden-incompatibility-bridge-profile-')
    assert report['selected_profile_name']
