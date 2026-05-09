from __future__ import annotations

from kam_theorem_suite.adaptive_tail_coherence import (
    build_golden_adaptive_tail_coherence_certificate,
    build_golden_two_sided_adaptive_tail_coherence_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_golden_adaptive_tail_coherence_report,
    build_golden_two_sided_adaptive_tail_coherence_bridge_report,
)


def test_golden_adaptive_tail_coherence_smoke() -> None:
    cert = build_golden_adaptive_tail_coherence_certificate(
        n_terms=3,
        keep_last=2,
        min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        crossing_max_depth=4,
        crossing_min_width=5e-4,
        band_initial_subdivisions=1,
        band_max_depth=2,
        band_min_width=1e-3,
        min_cluster_size=1,
        min_tail_members=1,
        min_q_support_fraction=0.5,
        min_entry_tail_coverage=0.5,
    ).to_dict()
    assert cert['theorem_status'].startswith('golden-adaptive-tail-coherence-')
    assert cert['entries']
    assert cert['successful_entry_indices']
    assert cert['support_profile']


def test_support_profile_tail_can_survive_when_exact_intersection_is_empty(monkeypatch) -> None:
    import kam_theorem_suite.adaptive_tail_coherence as atc

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    payloads = [
        {
            'selected_upper_lo': 0.97,
            'selected_upper_hi': 0.971,
            'selected_barrier_lo': 1.02,
            'selected_barrier_hi': 1.03,
            'incompatibility_gap': 0.049,
            'atlas': {'hyperbolic_tail': {'generated_qs': [5, 8, 13], 'witness_qs': [5, 8, 13], 'tail_qs': [8, 13]}},
            'theorem_status': 'golden-adaptive-incompatibility-moderate',
        },
        {
            'selected_upper_lo': 0.9702,
            'selected_upper_hi': 0.9709,
            'selected_barrier_lo': 1.0205,
            'selected_barrier_hi': 1.031,
            'incompatibility_gap': 0.0496,
            'atlas': {'hyperbolic_tail': {'generated_qs': [5, 8, 13], 'witness_qs': [5, 8, 13], 'tail_qs': [13]}},
            'theorem_status': 'golden-adaptive-incompatibility-moderate',
        },
        {
            'selected_upper_lo': 0.9701,
            'selected_upper_hi': 0.9708,
            'selected_barrier_lo': 1.0207,
            'selected_barrier_hi': 1.0308,
            'incompatibility_gap': 0.0499,
            'atlas': {'hyperbolic_tail': {'generated_qs': [5, 8, 13], 'witness_qs': [8, 13], 'tail_qs': [8, 13]}},
            'theorem_status': 'golden-adaptive-incompatibility-moderate',
        },
    ]
    seq = iter(payloads)
    monkeypatch.setattr(atc, 'build_golden_adaptive_incompatibility_certificate', lambda **kwargs: _Dummy(next(seq)))
    cert = build_golden_adaptive_tail_coherence_certificate(
        atlas_shifts=(-1e-4, 0.0, 1e-4),
        min_cluster_size=1,
        min_tail_members=2,
        min_q_support_fraction=2/3,
        min_entry_tail_coverage=0.5,
        min_tail_support_fraction=2/3,
    ).to_dict()
    assert cert['coherence_tail_qs'] in ([5, 8, 13], [8, 13])
    assert cert['coherence_tail_support_fraction'] is not None
    assert cert['coherence_tail_support_fraction'] >= 2/3
    assert cert['theorem_status'] in {
        'golden-adaptive-tail-coherence-strong',
        'golden-adaptive-tail-coherence-moderate',
    }



def test_driver_exposes_adaptive_tail_coherence_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(
        pd,
        'build_golden_adaptive_tail_coherence_certificate',
        lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-adaptive-tail-coherence-moderate', 'coherence_tail_qs': [8, 13], 'stable_upper_lo': 0.97}})(),
    )
    monkeypatch.setattr(
        pd,
        'build_golden_two_sided_adaptive_tail_coherence_bridge_certificate',
        lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-two-sided-adaptive-tail-coherence-partial', 'relation': {'gap_to_upper': 0.1}}})(),
    )
    upper = build_golden_adaptive_tail_coherence_report()
    bridge = build_golden_two_sided_adaptive_tail_coherence_bridge_report(K_values=[0.3])
    assert upper['theorem_status'].startswith('golden-adaptive-tail-coherence-')
    assert bridge['theorem_status'].startswith('golden-two-sided-adaptive-tail-coherence-')



def test_two_sided_adaptive_tail_coherence_bridge_smoke(monkeypatch) -> None:
    import kam_theorem_suite.adaptive_tail_coherence as atc

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(atc, 'continue_golden_aposteriori_certificates', lambda *a, **k: _Dummy({'last_stable_K': 0.5, 'last_success_K': 0.5}))
    monkeypatch.setattr(atc, 'build_golden_adaptive_tail_coherence_certificate', lambda *a, **k: _Dummy({'stable_upper_lo': 0.97, 'stable_upper_hi': 0.971, 'stable_barrier_lo': 1.02, 'stable_barrier_hi': 1.04, 'coherence_tail_qs': [8, 13], 'supporting_entry_indices': [0, 1], 'theorem_status': 'golden-adaptive-tail-coherence-strong'}))
    cert = build_golden_two_sided_adaptive_tail_coherence_bridge_certificate(K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-two-sided-adaptive-tail-coherence-strong'
    assert cert['relation']['gap_to_upper'] > 0
