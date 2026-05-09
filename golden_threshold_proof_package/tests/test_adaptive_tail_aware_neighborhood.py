from __future__ import annotations

from kam_theorem_suite.adaptive_tail_aware_neighborhood import (
    build_golden_adaptive_tail_aware_neighborhood_certificate,
)
from kam_theorem_suite.nonexistence_front import (
    build_golden_nonexistence_front_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_golden_adaptive_tail_aware_neighborhood_report,
)


def _coherence_payload(*, center: float, support_rows, witness_blocks, status='golden-adaptive-tail-coherence-moderate'):
    entries = []
    offsets = (-1.0e-4, 0.0, 1.0e-4)
    for idx, shift in enumerate(offsets):
        block = witness_blocks[min(idx, len(witness_blocks) - 1)]
        entries.append({
            'crossing_center': center + shift,
            'selected_upper_lo': 0.97,
            'selected_upper_hi': 0.971,
            'selected_barrier_lo': 1.02,
            'selected_barrier_hi': 1.03,
            'witness_qs': block,
            'exact_tail_qs': block,
            'generated_qs': [5, 8, 13],
        })
    return {
        'theorem_status': status,
        'entries': entries,
        'successful_entry_indices': [0, 1, 2],
        'clustered_entry_indices': [0, 1, 2],
        'supporting_entry_indices': [0, 1, 2],
        'coherence_tail_qs': [5, 8],
        'coherence_tail_support_fraction': 0.67,
        'coherence_tail_entry_coverage_floor': 0.67,
        'coherence_tail_is_suffix_of_generated_union': False,
        'stable_upper_lo': 0.97,
        'stable_upper_hi': 0.971,
        'stable_barrier_lo': 1.02,
        'stable_barrier_hi': 1.03,
        'stable_incompatibility_gap': 0.049,
        'support_profile': support_rows,
    }


def test_tail_aware_neighborhood_selects_tail_block_refinement(monkeypatch) -> None:
    import kam_theorem_suite.adaptive_tail_aware_neighborhood as atan

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    baseline_support = [
        {'q': 5, 'witness_support_fraction': 1.0, 'tail_support_fraction': 1.0},
        {'q': 8, 'witness_support_fraction': 1.0, 'tail_support_fraction': 1.0},
        {'q': 13, 'witness_support_fraction': 0.34, 'tail_support_fraction': 0.34},
    ]

    def _stub_coherence(**kwargs):
        center = float(kwargs.get('crossing_center', 0.0))
        if abs(center - 0.971735406) < 5e-7:
            return _Dummy(_coherence_payload(
                center=center,
                support_rows=baseline_support,
                witness_blocks=[[5, 8], [5, 8], [5, 8]],
                status='golden-adaptive-tail-coherence-strong',
            ))
        return _Dummy(_coherence_payload(
            center=center,
            support_rows=baseline_support,
            witness_blocks=[[5], [5, 8], [5]],
            status='golden-adaptive-tail-coherence-fragile',
        ))

    monkeypatch.setattr(atan, 'build_golden_adaptive_tail_coherence_certificate', _stub_coherence)
    monkeypatch.setattr(atan, '_build_golden_incompatibility_strict_bridge_from_coherence_payload', lambda coherence, **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-theorem-bridge-strong' if len(coherence.get('coherence_tail_qs', [5, 8])) >= 2 else 'golden-incompatibility-theorem-bridge-failed',
        'certified_tail_qs': coherence.get('coherence_tail_qs', [5, 8]),
        'supporting_entry_count': 2,
        'support_fraction_floor': 1.0,
        'entry_coverage_floor': 1.0,
        'bridge_margin': 0.2,
    }))
    monkeypatch.setattr(atan, 'build_golden_adaptive_support_core_neighborhood_certificate', lambda **kwargs: _Dummy({
        'selected_center': 0.971635406,
        'selected_atlas_shift_grid': [-1.0e-4, 0.0, 1.0e-4],
        'selected_bridge': {'certified_tail_qs': [5]},
    }))
    cert = build_golden_adaptive_tail_aware_neighborhood_certificate(
        crossing_center=0.971635406,
        atlas_shifts=(-1.0e-4, 0.0, 1.0e-4),
        min_tail_members=2,
        max_tail_candidates=2,
    ).to_dict()
    assert cert['selected_source_label'].startswith('tail-block-')
    assert len(cert['selected_target_tail_qs']) >= 2
    assert cert['selected_bridge']['theorem_status'] == 'golden-incompatibility-theorem-bridge-strong'
    assert len(cert['selected_bridge']['certified_tail_qs']) >= 2
    assert cert['theorem_status'].startswith('golden-adaptive-tail-aware-neighborhood-')


def test_nonexistence_front_uses_tail_aware_neighborhood_before_profile(monkeypatch) -> None:
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
        'certified_upper_lo': 0.97,
        'certified_upper_hi': 0.971,
        'certified_upper_width': 0.001,
        'certified_barrier_lo': 1.02,
        'certified_barrier_hi': 1.03,
        'certified_barrier_width': 0.01,
        'certified_tail_qs': [5],
        'certified_tail_is_suffix': False,
        'bridge_margin': -0.1,
        'missing_hypotheses': ['tail_support_fraction'],
        'supporting_entry_count': 1,
        'support_fraction_floor': 0.5,
        'entry_coverage_floor': 0.5,
    }))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_strict_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-theorem-bridge-failed',
        'missing_hypotheses': ['supporting_tail_exists'],
    }))
    monkeypatch.setattr(nf, 'build_golden_adaptive_support_core_neighborhood_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-adaptive-support-core-neighborhood-fragile',
        'selected_bridge': {'theorem_status': 'golden-incompatibility-theorem-bridge-weak'},
    }))
    monkeypatch.setattr(nf, 'build_golden_adaptive_tail_aware_neighborhood_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-adaptive-tail-aware-neighborhood-strong',
        'selected_bridge': {
            'theorem_status': 'golden-incompatibility-theorem-bridge-strong',
            'certified_upper_lo': 0.97,
            'certified_upper_hi': 0.971,
            'certified_upper_width': 0.001,
            'certified_barrier_lo': 1.02,
            'certified_barrier_hi': 1.03,
            'certified_barrier_width': 0.01,
            'certified_tail_qs': [5, 8],
            'certified_tail_is_suffix': True,
            'bridge_margin': 0.2,
            'missing_hypotheses': [],
            'supporting_entry_count': 2,
            'support_fraction_floor': 1.0,
            'entry_coverage_floor': 1.0,
        },
    }))
    monkeypatch.setattr(nf, 'build_golden_incompatibility_bridge_profile_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-incompatibility-bridge-profile-fragile',
        'selected_profile_name': 'strict',
        'viable_profile_count': 1,
        'strong_profile_count': 0,
        'selected_bridge': {'theorem_status': 'golden-incompatibility-theorem-bridge-weak'},
    }))
    cert = build_golden_nonexistence_front_certificate(base_K_values=[0.3]).to_dict()
    assert cert['relation']['upper_status'] == 'golden-incompatibility-theorem-bridge-strong'
    assert cert['relation']['upper_tail_aware_neighborhood_status'] == 'golden-adaptive-tail-aware-neighborhood-strong'
    assert cert['theorem_status'] == 'golden-nonexistence-front-strong'


def test_driver_exposes_tail_aware_neighborhood_report(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_adaptive_tail_aware_neighborhood_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-adaptive-tail-aware-neighborhood-weak', 'selected_source_label': 'baseline'}})())
    report = build_golden_adaptive_tail_aware_neighborhood_report()
    assert report['theorem_status'].startswith('golden-adaptive-tail-aware-neighborhood-')
    assert report['selected_source_label']
