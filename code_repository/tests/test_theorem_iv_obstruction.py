from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import (
    build_golden_irrational_incompatibility_report,
    build_golden_two_sided_incompatibility_bridge_report,
    build_periodic_ladder_incompatibility_report,
)
from kam_theorem_suite.theorem_iv_obstruction import (
    build_golden_two_sided_incompatibility_bridge_certificate,
)
from kam_theorem_suite.hyperbolicity_certifier import certify_sustained_hyperbolic_tail


def _light_upper_kwargs():
    return dict(
        n_terms=3,
        keep_last=1,
        min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        crossing_center_offsets=(0.0,),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=1,
        support_fraction_threshold=0.5,
        min_tail_members=1,
        min_stable_tail_members=1,
        min_cluster_size=1,
    )


def test_periodic_ladder_incompatibility_report_smoke() -> None:
    specs = [
        ApproximantWindowSpec(3, 5, 0.969, 0.972, 1.02, 1.05, label="3/5"),
        ApproximantWindowSpec(5, 8, 0.969, 0.972, 1.02, 1.05, label="5/8"),
    ]
    report = build_periodic_ladder_incompatibility_report(
        specs,
        initial_subdivisions=1,
        max_depth=0,
        min_tail_members=1,
    )
    assert report["theorem_status"].startswith("periodic-ladder-incompatibility-")
    assert report["hyperbolic_tail"]["theorem_status"].startswith("sustained-hyperbolic-tail-")


def test_hyperbolicity_certifier_synthetic_tail() -> None:
    tail = certify_sustained_hyperbolic_tail([
        {"q": 5, "label": "5", "crossing_root_window_lo": 0.97, "crossing_root_window_hi": 0.971, "hyperbolic_band_lo": 1.02, "hyperbolic_band_hi": 1.03, "crossing_certificate": {"certification_tier": "interval_newton"}},
        {"q": 8, "label": "8", "crossing_root_window_lo": 0.9702, "crossing_root_window_hi": 0.9708, "hyperbolic_band_lo": 1.021, "hyperbolic_band_hi": 1.029, "crossing_certificate": {"certification_tier": "interval_newton"}},
    ], min_tail_members=1).to_dict()
    assert tail["theorem_status"].startswith("sustained-hyperbolic-tail-")
    assert tail["witness_qs"] == [5, 8]


def test_golden_irrational_incompatibility_report_smoke(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_irrational_incompatibility_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-irrational-incompatibility-strong', 'selected_upper_source': 'tail-stability', 'ladder_hyperbolic_tail': {'theorem_status': 'sustained-hyperbolic-tail-strong'}}})())
    report = build_golden_irrational_incompatibility_report(**_light_upper_kwargs())
    assert report["theorem_status"].startswith("golden-irrational-incompatibility-")
    assert report["selected_upper_source"]
    assert "ladder_hyperbolic_tail" in report


def test_golden_two_sided_incompatibility_bridge_smoke(monkeypatch) -> None:
    import kam_theorem_suite.theorem_iv_obstruction as tio

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(tio, 'continue_golden_aposteriori_certificates', lambda *a, **k: _Dummy({'last_stable_K': 0.5, 'last_success_K': 0.5}))
    monkeypatch.setattr(tio, 'build_golden_irrational_incompatibility_certificate', lambda *a, **k: _Dummy({'selected_upper_source': 'tail-stability', 'selected_upper_lo': 0.97, 'selected_upper_hi': 0.971, 'selected_barrier_source': 'tail-stability', 'selected_barrier_lo': 1.02, 'selected_barrier_hi': 1.04, 'selected_tail_qs': [5, 8], 'selected_tail_is_suffix': True, 'theorem_status': 'golden-irrational-incompatibility-strong'}))
    monkeypatch.setattr(tio, 'build_golden_nonexistence_front_certificate', lambda *a, **k: _Dummy({'theorem_status': 'golden-nonexistence-front-strong', 'computational_front_margin': 0.1, 'remaining_analytic_lifts': [{'name': 'obstruction_implies_no_analytic_circle'}]}))
    cert = build_golden_two_sided_incompatibility_bridge_certificate(K_values=[0.3])
    d = cert.to_dict()
    assert d['theorem_status'] == 'golden-two-sided-incompatibility-strong'
    assert d['relation']['tail_is_suffix'] is True


def test_driver_layer_exposes_theorem_iv_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_irrational_incompatibility_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'theorem_status': 'golden-irrational-incompatibility-fragile', 'selected_upper_source': 'support-audit'}})())
    monkeypatch.setattr(pd, 'build_golden_two_sided_incompatibility_bridge_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'relation': {'gap_to_upper': 0.1}, 'theorem_status': 'golden-two-sided-incompatibility-partial'}})())

    upper = build_golden_irrational_incompatibility_report()
    bridge = build_golden_two_sided_incompatibility_bridge_report(K_values=[0.3])
    assert upper['theorem_status'].startswith('golden-irrational-incompatibility-')
    assert bridge['theorem_status'].startswith('golden-two-sided-incompatibility-')
