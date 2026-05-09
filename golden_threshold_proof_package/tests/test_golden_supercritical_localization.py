from __future__ import annotations

from kam_theorem_suite.golden_supercritical_localization import (
    build_golden_supercritical_localization_certificate,
    build_golden_two_sided_localization_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_golden_supercritical_localization_report,
    build_golden_two_sided_localization_bridge_report,
)


def test_golden_supercritical_localization_certificate_smoke() -> None:
    cert = build_golden_supercritical_localization_certificate(
        n_terms=6,
        keep_last=3,
        min_q=5,
        crossing_center_offsets=(-4.0e-4, 0.0, 4.0e-4),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=2,
    )
    d = cert.to_dict()
    assert d['total_round_count'] >= 1
    assert d['best_round_index'] is None or d['best_round_index'] >= 0
    assert d['theorem_status'] in {
        'golden-supercritical-localization-strong',
        'golden-supercritical-localization-moderate',
        'golden-supercritical-localization-weak',
        'golden-supercritical-localization-fragile',
        'golden-supercritical-localization-failed',
    }


def test_golden_two_sided_localization_bridge_smoke(monkeypatch) -> None:
    import kam_theorem_suite.golden_supercritical_localization as gsl

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(gsl, 'continue_golden_aposteriori_certificates', lambda *a, **k: _Dummy({'last_success_K': 0.5, 'success_prefix_len': 3, 'steps': []}))
    monkeypatch.setattr(gsl, 'build_golden_supercritical_localization_certificate', lambda *a, **k: _Dummy({'localized_upper_source': 'refined-upper-ladder', 'localized_upper_lo': 0.97, 'localized_upper_hi': 0.971, 'localized_upper_width': 0.001, 'localized_band_lo': 1.02, 'localized_band_hi': 1.04, 'localized_support_size': 3, 'total_round_count': 2, 'theorem_status': 'golden-supercritical-localization-strong'}))
    bridge = build_golden_two_sided_localization_bridge_certificate(K_values=[0.3])
    d = bridge.to_dict()
    assert d['relation']['lower_success_prefix_len'] == 3
    assert d['theorem_status'] == 'golden-two-sided-localization-strong'


def test_driver_layer_exposes_golden_supercritical_localization_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_supercritical_localization_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'total_round_count': 1, 'theorem_status': 'golden-supercritical-localization-failed'}})())
    monkeypatch.setattr(pd, 'build_golden_two_sided_localization_bridge_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'relation': {'status': 'golden-two-sided-localization-incomplete'}, 'theorem_status': 'golden-two-sided-localization-incomplete'}})())

    localization = build_golden_supercritical_localization_report()
    bridge = build_golden_two_sided_localization_bridge_report(K_values=[0.3])
    assert localization['total_round_count'] >= 1
    assert bridge['relation']['status'] == bridge['theorem_status']
