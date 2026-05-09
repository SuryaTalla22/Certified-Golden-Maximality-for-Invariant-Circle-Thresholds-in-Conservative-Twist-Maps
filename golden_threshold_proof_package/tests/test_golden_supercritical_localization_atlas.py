from __future__ import annotations

from kam_theorem_suite.golden_supercritical_localization_atlas import (
    build_golden_supercritical_localization_atlas_certificate,
    build_golden_two_sided_localization_atlas_bridge_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_golden_supercritical_localization_atlas_report,
    build_golden_two_sided_localization_atlas_bridge_report,
)


def test_golden_supercritical_localization_atlas_certificate_smoke() -> None:
    cert = build_golden_supercritical_localization_atlas_certificate(
        n_terms=3,
        keep_last=1,
        min_q=5,
        crossing_center_offsets=(0.0,),
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=1,
    )
    d = cert.to_dict()
    assert d['successful_entry_count'] >= 0
    assert len(d['entries']) == 3
    assert d['theorem_status'] in {
        'golden-supercritical-localization-atlas-strong',
        'golden-supercritical-localization-atlas-moderate',
        'golden-supercritical-localization-atlas-weak',
        'golden-supercritical-localization-atlas-fragile',
        'golden-supercritical-localization-atlas-failed',
    }


def test_golden_two_sided_localization_atlas_bridge_smoke(monkeypatch) -> None:
    import kam_theorem_suite.golden_supercritical_localization_atlas as gsla

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(gsla, 'continue_golden_aposteriori_certificates', lambda *a, **k: _Dummy({'last_success_K': 0.5, 'success_prefix_len': 3, 'steps': []}))
    monkeypatch.setattr(gsla, 'build_golden_supercritical_localization_atlas_certificate', lambda *a, **k: _Dummy({'atlas_upper_source': 'refined-upper-ladder', 'atlas_upper_lo': 0.97, 'atlas_upper_hi': 0.971, 'atlas_upper_width': 0.001, 'atlas_band_lo': 1.02, 'atlas_band_hi': 1.04, 'atlas_support_size': 3, 'successful_entry_count': 4, 'theorem_status': 'golden-supercritical-localization-atlas-strong'}))
    bridge = build_golden_two_sided_localization_atlas_bridge_certificate(K_values=[0.3])
    d = bridge.to_dict()
    assert d['relation']['atlas_successful_entry_count'] == 4
    assert d['theorem_status'] == 'golden-two-sided-localization-atlas-strong'


def test_driver_layer_exposes_golden_supercritical_localization_atlas_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_supercritical_localization_atlas_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'clustered_entry_count': 1, 'theorem_status': 'golden-supercritical-localization-atlas-failed'}})())
    monkeypatch.setattr(pd, 'build_golden_two_sided_localization_atlas_bridge_certificate', lambda **kwargs: type('D', (), {'to_dict': lambda self: {'relation': {'status': 'golden-two-sided-localization-atlas-incomplete'}, 'theorem_status': 'golden-two-sided-localization-atlas-incomplete'}})())

    atlas = build_golden_supercritical_localization_atlas_report()
    bridge = build_golden_two_sided_localization_atlas_bridge_report(K_values=[0.3])
    assert atlas['clustered_entry_count'] >= 0
    assert bridge['relation']['status'] == bridge['theorem_status']
