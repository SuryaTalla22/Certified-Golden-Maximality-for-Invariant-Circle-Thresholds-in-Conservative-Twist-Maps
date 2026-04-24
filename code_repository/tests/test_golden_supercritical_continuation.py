from __future__ import annotations

from kam_theorem_suite.golden_supercritical_continuation import (
    build_golden_supercritical_continuation_certificate,
    build_golden_two_sided_continuation_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_golden_supercritical_continuation_report,
    build_golden_two_sided_continuation_bridge_report,
)


def test_golden_supercritical_continuation_certificate_smoke() -> None:
    cert = build_golden_supercritical_continuation_certificate(
        n_terms=6,
        keep_last=3,
        min_q=5,
        crossing_center_offsets=(-4.0e-4, 0.0, 4.0e-4),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
    )
    d = cert.to_dict()
    assert d['successful_step_count'] >= 0
    assert d['usable_upper_step_count'] >= 0
    assert d['theorem_status'] in {
        'golden-supercritical-continuation-strong',
        'golden-supercritical-continuation-moderate',
        'golden-supercritical-continuation-weak',
        'golden-supercritical-continuation-fragile',
        'golden-supercritical-continuation-failed',
    }


def test_golden_two_sided_continuation_bridge_smoke(monkeypatch) -> None:
    import kam_theorem_suite.golden_supercritical_continuation as gsc

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(gsc, 'continue_golden_aposteriori_certificates', lambda *a, **k: _Dummy({'last_success_K': 0.5, 'success_prefix_len': 3, 'steps': []}))
    monkeypatch.setattr(gsc, 'build_golden_supercritical_continuation_certificate', lambda *a, **k: _Dummy({'stable_upper_source': 'refined-upper-ladder', 'stable_upper_lo': 0.97, 'stable_upper_hi': 0.971, 'stable_upper_width': 0.001, 'stable_band_lo': 1.02, 'stable_band_hi': 1.04, 'stable_upper_support_size': 3, 'stable_band_support_size': 2, 'theorem_status': 'golden-supercritical-continuation-strong'}))
    bridge = build_golden_two_sided_continuation_bridge_certificate(K_values=[0.3])
    d = bridge.to_dict()
    assert d['relation']['lower_success_prefix_len'] == 3
    assert d['theorem_status'] == 'golden-two-sided-continuation-strong'


def test_driver_layer_exposes_golden_supercritical_continuation_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_supercritical_continuation_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'successful_step_count': 0, 'theorem_status': 'golden-supercritical-continuation-failed'}})())
    monkeypatch.setattr(pd, 'build_golden_two_sided_continuation_bridge_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'relation': {'status': 'golden-two-sided-continuation-incomplete'}, 'theorem_status': 'golden-two-sided-continuation-incomplete'}})())

    continuation = build_golden_supercritical_continuation_report()
    bridge = build_golden_two_sided_continuation_bridge_report(K_values=[0.3])
    assert continuation['successful_step_count'] >= 0
    assert bridge['relation']['status'] == bridge['theorem_status']
