from __future__ import annotations

from kam_theorem_suite.nonexistence_front import build_golden_nonexistence_front_certificate


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage87_nonexistence_front_builds_contradiction_summary(monkeypatch) -> None:
    import kam_theorem_suite.nonexistence_front as nf

    monkeypatch.setattr(nf, 'build_golden_lower_neighborhood_stability_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-lower-neighborhood-stability-strong',
        'stable_lower_bound': 0.5,
        'stable_window_hi': 0.55,
        'stable_window_width': 0.05,
        'distinct_resolution_signatures': [[64, 96, 128], [80, 112, 144]],
    }))
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
        'bridge_margin': 0.08,
        'missing_hypotheses': [],
        'supporting_entry_count': 2,
        'support_fraction_floor': 1.0,
        'entry_coverage_floor': 1.0,
    }))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_strict_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-theorem-bridge-strong',
    }))
    monkeypatch.setattr(nf, 'build_golden_adaptive_support_core_neighborhood_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-adaptive-support-core-neighborhood-strong',
        'selected_bridge': {'theorem_status': 'golden-incompatibility-theorem-bridge-strong'},
    }))
    monkeypatch.setattr(nf, 'build_golden_adaptive_tail_aware_neighborhood_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-adaptive-tail-aware-neighborhood-strong',
        'selected_bridge': {'theorem_status': 'golden-incompatibility-theorem-bridge-strong'},
    }))
    monkeypatch.setattr(nf, 'build_golden_adaptive_tail_stability_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-adaptive-tail-stability-strong',
        'stable_incompatibility_gap': 0.04,
    }))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_bridge_profile_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-bridge-profile-strong',
        'selected_profile_name': 'dense-support',
        'viable_profile_count': 1,
        'strong_profile_count': 1,
        'selected_bridge': {'theorem_status': 'golden-incompatibility-theorem-bridge-strong'},
    }))

    cert = build_golden_nonexistence_front_certificate(base_K_values=[0.3], force_tail_stability=True, force_support_core_neighborhood=True, force_tail_aware_neighborhood=True).to_dict()
    assert cert['theorem_status'] == 'golden-nonexistence-front-strong'
    summary = cert['contradiction_summary']
    assert summary['supercritical_obstruction_locked'] is True
    assert summary['support_geometry_certified'] is True
    assert summary['tail_coherence_certified'] is True
    assert summary['tail_stability_certified'] is True
    assert summary['nonexistence_contradiction_certified'] is True
    assert summary['theorem_status'] == 'golden-nonexistence-contradiction-strong'
