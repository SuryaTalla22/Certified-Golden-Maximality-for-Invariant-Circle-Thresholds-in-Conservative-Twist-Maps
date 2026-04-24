from __future__ import annotations

from kam_theorem_suite.proof_driver import build_golden_theorem_iii_report


def test_stage88_driver_exposes_final_theorem_iii(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload

        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(pd, 'build_golden_theorem_iii_certificate', lambda **kwargs: _Dummy({
        'theorem_iii_final_status': 'golden-theorem-iii-final-strong',
        'analytic_invariant_circle_exists': True,
        'certified_below_threshold_interval': [0.2, 0.29],
    }))
    report = build_golden_theorem_iii_report(base_K_values=[0.2, 0.25])
    assert report['theorem_iii_final_status'] == 'golden-theorem-iii-final-strong'
    assert report['analytic_invariant_circle_exists'] is True
