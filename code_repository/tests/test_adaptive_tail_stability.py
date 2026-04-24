from __future__ import annotations

from kam_theorem_suite.adaptive_tail_stability import (
    build_golden_adaptive_tail_stability_certificate,
    build_golden_two_sided_adaptive_tail_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_golden_adaptive_tail_stability_report,
    build_golden_two_sided_adaptive_tail_bridge_report,
)


def test_golden_adaptive_tail_stability_smoke() -> None:
    cert = build_golden_adaptive_tail_stability_certificate(
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
        min_stable_tail_members=1,
    ).to_dict()
    assert cert["theorem_status"].startswith("golden-adaptive-tail-stability-")
    assert cert["entries"]
    assert cert["successful_entry_indices"]


def test_driver_exposes_adaptive_tail_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(
        pd,
        "build_golden_adaptive_tail_stability_certificate",
        lambda **kwargs: type(
            "D",
            (),
            {
                "to_dict": lambda self: {
                    "theorem_status": "golden-adaptive-tail-stability-moderate",
                    "stable_upper_lo": 0.97,
                    "stable_barrier_lo": 1.02,
                    "clustered_entry_indices": [0, 1],
                }
            },
        )(),
    )
    monkeypatch.setattr(
        pd,
        "build_golden_two_sided_adaptive_tail_bridge_certificate",
        lambda **kwargs: type(
            "D",
            (),
            {
                "to_dict": lambda self: {
                    "theorem_status": "golden-two-sided-adaptive-tail-partial",
                    "relation": {"gap_to_upper": 0.1},
                }
            },
        )(),
    )
    upper = build_golden_adaptive_tail_stability_report()
    bridge = build_golden_two_sided_adaptive_tail_bridge_report(K_values=[0.3])
    assert upper["theorem_status"].startswith("golden-adaptive-tail-stability-")
    assert bridge["theorem_status"].startswith("golden-two-sided-adaptive-tail-")


def test_two_sided_adaptive_tail_bridge_smoke(monkeypatch) -> None:
    import kam_theorem_suite.adaptive_tail_stability as ats

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(ats, 'continue_golden_aposteriori_certificates', lambda *a, **k: _Dummy({'last_stable_K': 0.5, 'last_success_K': 0.5}))
    monkeypatch.setattr(ats, 'build_golden_adaptive_tail_stability_certificate', lambda *a, **k: _Dummy({'stable_upper_lo': 0.97, 'stable_upper_hi': 0.971, 'stable_barrier_lo': 1.02, 'stable_barrier_hi': 1.04, 'stable_tail_qs': [5, 8], 'stable_tail_support_count': 2, 'clustered_entry_indices': [0, 1], 'theorem_status': 'golden-adaptive-tail-stability-strong'}))
    cert = build_golden_two_sided_adaptive_tail_bridge_certificate(K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-two-sided-adaptive-tail-strong'
    assert cert['relation']['gap_to_upper'] > 0
