from __future__ import annotations

from kam_theorem_suite.incompatibility_theorem_bridge import (
    build_golden_incompatibility_theorem_bridge_certificate,
    build_golden_two_sided_incompatibility_theorem_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_golden_incompatibility_theorem_bridge_report,
    build_golden_two_sided_incompatibility_theorem_bridge_report,
)


def test_golden_incompatibility_theorem_bridge_smoke() -> None:
    cert = build_golden_incompatibility_theorem_bridge_certificate(
        n_terms=3, keep_last=2, min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        crossing_max_depth=4, crossing_min_width=5e-4,
        band_initial_subdivisions=1, band_max_depth=2, band_min_width=1e-3,
        min_cluster_size=1, min_tail_members=1,
        min_support_fraction=0.5, min_entry_coverage=0.5,
    ).to_dict()
    assert cert['theorem_status'].startswith('golden-incompatibility-theorem-bridge-')
    assert cert['hypotheses']
    assert 'coherent_upper_object' in [h['name'] for h in cert['hypotheses']]


def test_bridge_ledger_can_close_strongly(monkeypatch) -> None:
    import kam_theorem_suite.incompatibility_theorem_bridge as itb

    class _Dummy:
        def __init__(self, payload): self._payload = payload
        def to_dict(self): return dict(self._payload)

    monkeypatch.setattr(itb, 'build_golden_adaptive_tail_coherence_certificate', lambda **kwargs: _Dummy({
        'stable_upper_lo': 0.97, 'stable_upper_hi': 0.9705, 'stable_upper_width': 5e-4,
        'stable_barrier_lo': 1.02, 'stable_barrier_hi': 1.021, 'stable_barrier_width': 1e-3,
        'stable_incompatibility_gap': 0.0495, 'coherence_tail_qs': [8, 13],
        'coherence_tail_start_q': 8, 'coherence_tail_is_suffix_of_generated_union': True,
        'supporting_entry_indices': [0, 1], 'coherence_tail_support_fraction': 1.0,
        'coherence_tail_entry_coverage_floor': 1.0, 'theorem_status': 'golden-adaptive-tail-coherence-strong',
    }))
    cert = build_golden_incompatibility_theorem_bridge_certificate(
        min_cluster_size=2, min_tail_members=2,
        min_support_fraction=0.75, min_entry_coverage=0.75,
        require_suffix_tail=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-incompatibility-theorem-bridge-strong'
    assert cert['missing_hypotheses'] == []
    assert cert['gap_to_localization_ratio'] > 1.0


def test_two_sided_incompatibility_theorem_bridge_smoke(monkeypatch) -> None:
    import kam_theorem_suite.incompatibility_theorem_bridge as itb

    class _Dummy:
        def __init__(self, payload): self._payload = payload
        def to_dict(self): return dict(self._payload)

    monkeypatch.setattr(itb, 'continue_golden_aposteriori_certificates', lambda *a, **k: _Dummy({'last_stable_K': 0.5, 'last_success_K': 0.5}))
    monkeypatch.setattr(itb, 'build_golden_incompatibility_theorem_bridge_certificate', lambda *a, **k: _Dummy({'certified_upper_lo': 0.97, 'certified_upper_hi': 0.971, 'certified_barrier_lo': 1.02, 'certified_barrier_hi': 1.04, 'certified_tail_qs': [8, 13], 'certified_tail_is_suffix': True, 'bridge_margin': 0.1, 'missing_hypotheses': [], 'theorem_status': 'golden-incompatibility-theorem-bridge-strong'}))
    cert = build_golden_two_sided_incompatibility_theorem_bridge_certificate(K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-two-sided-incompatibility-theorem-bridge-strong'
    assert cert['relation']['gap_to_upper'] > 0


def test_driver_exposes_incompatibility_theorem_bridge_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_incompatibility_theorem_bridge_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-incompatibility-theorem-bridge-moderate', 'hypotheses': [{'name': 'coherent_upper_object'}]}})())
    monkeypatch.setattr(pd, 'build_golden_two_sided_incompatibility_theorem_bridge_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-two-sided-incompatibility-theorem-bridge-partial', 'relation': {'gap_to_upper': 0.1}}})())
    upper = build_golden_incompatibility_theorem_bridge_report()
    bridge = build_golden_two_sided_incompatibility_theorem_bridge_report(K_values=[0.3])
    assert upper['theorem_status'].startswith('golden-incompatibility-theorem-bridge-')
    assert bridge['theorem_status'].startswith('golden-two-sided-incompatibility-theorem-bridge-')
