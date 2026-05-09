from __future__ import annotations

from kam_theorem_suite.golden_supercritical import (
    build_golden_supercritical_obstruction_certificate,
    build_golden_two_sided_bridge_certificate,
    generate_golden_convergent_specs,
)
from kam_theorem_suite.proof_driver import (
    build_golden_supercritical_obstruction_report,
    build_golden_two_sided_bridge_report,
)


def test_generate_golden_convergent_specs_monotone_q() -> None:
    specs = generate_golden_convergent_specs(n_terms=8, keep_last=4, min_q=3)
    qs = [s.q for s in specs]
    assert len(specs) >= 3
    assert qs == sorted(qs)
    assert all(spec.label.startswith("gold-") for spec in specs)


def test_golden_supercritical_obstruction_certificate_smoke() -> None:
    cert = build_golden_supercritical_obstruction_certificate(
        n_terms=6,
        keep_last=3,
        min_q=5,
        initial_subdivisions=1,
        max_depth=1,
    )
    d = cert.to_dict()
    assert d['successful_crossing_count'] >= 0
    assert d['selected_upper_source'] in {'asymptotic-upper-ladder', 'refined-upper-ladder', 'raw-upper-ladder', 'no-upper-object'}
    assert d['theorem_status'] in {
        'golden-supercritical-obstruction-strong',
        'golden-supercritical-obstruction-moderate',
        'golden-supercritical-obstruction-weak',
        'golden-supercritical-obstruction-failed',
    }


def test_golden_two_sided_bridge_smoke(monkeypatch) -> None:
    import kam_theorem_suite.golden_supercritical as gs

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(gs, 'continue_golden_aposteriori_certificates', lambda *a, **k: _Dummy({'last_success_K': 0.5, 'success_prefix_len': 2, 'steps': []}))
    monkeypatch.setattr(gs, 'build_golden_supercritical_obstruction_certificate', lambda *a, **k: _Dummy({'selected_upper_source': 'refined-upper-ladder', 'selected_upper_lo': 0.97, 'selected_upper_hi': 0.971, 'selected_upper_width': 0.001, 'earliest_hyperbolic_band_lo': 1.03, 'successful_crossing_count': 2, 'successful_band_count': 1, 'theorem_status': 'golden-supercritical-obstruction-moderate'}))
    bridge = build_golden_two_sided_bridge_certificate(K_values=[0.3])
    d = bridge.to_dict()
    assert d['relation']['lower_success_prefix_len'] == 2
    assert d['theorem_status'] == 'golden-two-sided-bridge-moderate'


def test_driver_layer_exposes_golden_supercritical_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_supercritical_obstruction_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'successful_crossing_count': 0}})())
    monkeypatch.setattr(pd, 'build_golden_two_sided_bridge_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'relation': {'status': 'golden-incomplete'}, 'theorem_status': 'golden-incomplete'}})())

    obstruction = build_golden_supercritical_obstruction_report()
    bridge = build_golden_two_sided_bridge_report(K_values=[0.3])
    assert obstruction['successful_crossing_count'] >= 0
    assert bridge['relation']['status'] == bridge['theorem_status']
