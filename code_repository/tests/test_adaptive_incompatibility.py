from __future__ import annotations

from kam_theorem_suite.adaptive_incompatibility import (
    build_adaptive_incompatibility_atlas_certificate,
    build_golden_adaptive_incompatibility_certificate,
)
from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import (
    build_adaptive_incompatibility_atlas_report,
    build_golden_adaptive_incompatibility_report,
)


def test_adaptive_incompatibility_atlas_localizes_and_attaches_band() -> None:
    specs = [
        ApproximantWindowSpec(3, 5, 0.95, 0.99, 1.02, 1.05, label="3/5"),
        ApproximantWindowSpec(5, 8, 0.95, 0.99, 1.02, 1.05, label="5/8"),
    ]
    cert = build_adaptive_incompatibility_atlas_certificate(
        specs,
        crossing_max_depth=5,
        crossing_min_width=5e-4,
        band_initial_subdivisions=1,
        band_max_depth=3,
        band_min_width=1e-3,
        min_tail_members=1,
    ).to_dict()
    assert cert["theorem_status"].startswith("adaptive-incompatibility-")
    assert cert["interval_newton_count"] >= 1
    assert cert["fully_certified_count"] >= 1
    assert cert["entries"][0]["adaptive_crossing"]["status"] == "interval_newton"


def test_driver_exposes_adaptive_incompatibility_reports() -> None:
    specs = [ApproximantWindowSpec(3, 5, 0.95, 0.99, 1.02, 1.05, label="3/5")]
    report = build_adaptive_incompatibility_atlas_report(
        specs,
        crossing_max_depth=5,
        crossing_min_width=5e-4,
        band_initial_subdivisions=1,
        band_max_depth=2,
        band_min_width=1e-3,
        min_tail_members=1,
    )
    assert report["entries"]
    assert report["entries"][0]["localized_crossing_source"].startswith("adaptive-")


def test_golden_adaptive_report_smoke(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(
        pd,
        "build_golden_adaptive_incompatibility_certificate",
        lambda **kwargs: type(
            "D",
            (),
            {
                "to_dict": lambda self: {
                    "theorem_status": "golden-adaptive-incompatibility-moderate",
                    "selected_upper_lo": 0.97,
                    "selected_barrier_lo": 1.02,
                    "atlas": {"theorem_status": "adaptive-incompatibility-moderate"},
                }
            },
        )(),
    )
    report = build_golden_adaptive_incompatibility_report()
    assert report["theorem_status"].startswith("golden-adaptive-incompatibility-")
    assert report["atlas"]["theorem_status"].startswith("adaptive-incompatibility-")


def test_theorem_iv_package_prefers_adaptive_upper_object(monkeypatch) -> None:
    import kam_theorem_suite.theorem_iv_obstruction as tio

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(tio, 'build_golden_supercritical_obstruction_certificate', lambda **kwargs: _Dummy({'selected_upper_source': 'raw-upper-ladder', 'selected_upper_lo': 0.971, 'selected_upper_hi': 0.972, 'ladder': {'approximants': []}, 'earliest_hyperbolic_band_lo': 1.03, 'latest_hyperbolic_band_hi': 1.04}))
    monkeypatch.setattr(tio, 'build_golden_supercritical_continuation_certificate', lambda **kwargs: _Dummy({'stable_upper_lo': 0.9708, 'stable_upper_hi': 0.9715, 'stable_band_lo': 1.025, 'stable_band_hi': 1.035}))
    monkeypatch.setattr(tio, 'build_golden_upper_support_audit_certificate', lambda **kwargs: _Dummy({'audited_upper_lo': 0.9707, 'audited_upper_hi': 0.9714, 'audited_band_lo': 1.024, 'audited_band_hi': 1.034, 'robust_tail_qs': [5, 8], 'tail_is_suffix_of_generated': True}))
    monkeypatch.setattr(tio, 'build_golden_upper_tail_stability_certificate', lambda **kwargs: _Dummy({'stable_upper_lo': 0.9706, 'stable_upper_hi': 0.9713, 'stable_band_lo': 1.023, 'stable_band_hi': 1.033, 'stable_tail_qs': [5, 8], 'stable_tail_is_suffix_of_generated_union': True}))
    monkeypatch.setattr(tio, 'build_golden_adaptive_incompatibility_certificate', lambda **kwargs: _Dummy({'selected_upper_lo': 0.9699, 'selected_upper_hi': 0.9702, 'selected_barrier_lo': 1.021, 'selected_barrier_hi': 1.031, 'atlas': {'hyperbolic_tail': {'tail_qs': [5, 8], 'tail_is_suffix_of_generated': True}}, 'theorem_status': 'golden-adaptive-incompatibility-strong'}))
    monkeypatch.setattr(tio, 'build_golden_adaptive_tail_stability_certificate', lambda **kwargs: _Dummy({'stable_upper_lo': 0.9695, 'stable_upper_hi': 0.9698, 'stable_barrier_lo': 1.0205, 'stable_barrier_hi': 1.0305, 'stable_tail_qs': [5, 8], 'stable_tail_is_suffix_of_generated_union': True, 'theorem_status': 'golden-adaptive-tail-stability-strong'}))
    monkeypatch.setattr(tio, 'build_golden_adaptive_tail_coherence_certificate', lambda **kwargs: _Dummy({'stable_upper_lo': 0.9692, 'stable_upper_hi': 0.9696, 'stable_barrier_lo': 1.0202, 'stable_barrier_hi': 1.0302, 'coherence_tail_qs': [5, 8], 'coherence_tail_is_suffix_of_generated_union': True, 'theorem_status': 'golden-adaptive-tail-coherence-strong'}))
    monkeypatch.setattr(tio, 'certify_sustained_hyperbolic_tail', lambda *a, **k: _Dummy({'tail_qs': [5, 8], 'tail_is_suffix_of_generated': True}))

    cert = tio.build_golden_irrational_incompatibility_certificate(min_tail_members=1).to_dict()
    assert cert['selected_upper_source'] == 'adaptive-tail-coherence'
    assert cert['adaptive_upper_package']['theorem_status'] == 'golden-adaptive-incompatibility-strong'
    assert cert['adaptive_tail_stability']['theorem_status'] == 'golden-adaptive-tail-stability-strong'
