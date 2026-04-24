from __future__ import annotations

from kam_theorem_suite.proof_driver import build_golden_theorem_iv_report
from kam_theorem_suite.theorem_iv_analytic_lift import build_golden_analytic_incompatibility_lift_certificate


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage87_theorem_iv_final_strong_when_contradiction_is_certified(monkeypatch) -> None:
    import kam_theorem_suite.theorem_iv_analytic_lift as tal

    monkeypatch.setattr(tal, 'build_golden_nonexistence_front_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-nonexistence-front-strong',
        'computational_front_margin': 0.12,
        'contradiction_summary': {
            'theorem_status': 'golden-nonexistence-contradiction-strong',
            'supercritical_obstruction_locked': True,
            'support_geometry_certified': True,
            'tail_coherence_certified': True,
            'tail_stability_certified': True,
            'nonexistence_contradiction_certified': True,
            'contradiction_margin': 0.11,
            'residual_burden': [],
        },
        'hypotheses': [
            {'name': 'stable_lower_object', 'satisfied': True, 'source': 'lower', 'note': 'ok', 'margin': 1.0},
            {'name': 'upper_bridge_closed', 'satisfied': True, 'source': 'upper', 'note': 'ok', 'margin': 0.1},
        ],
    }))
    cert = build_golden_analytic_incompatibility_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-iv-final-strong'
    assert cert['analytic_incompatibility_certified'] is True
    assert cert['active_assumptions'] == []
    assert cert['residual_iv_burden'] == []


def test_stage87_theorem_iv_contradiction_assembled_when_one_final_piece_is_missing(monkeypatch) -> None:
    import kam_theorem_suite.theorem_iv_analytic_lift as tal

    monkeypatch.setattr(tal, 'build_golden_nonexistence_front_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-nonexistence-front-strong',
        'computational_front_margin': 0.05,
        'contradiction_summary': {
            'theorem_status': 'golden-nonexistence-contradiction-partial',
            'supercritical_obstruction_locked': True,
            'support_geometry_certified': True,
            'tail_coherence_certified': True,
            'tail_stability_certified': False,
            'nonexistence_contradiction_certified': False,
            'contradiction_margin': 0.01,
            'residual_burden': ['tail_stability_certified'],
        },
        'hypotheses': [
            {'name': 'stable_lower_object', 'satisfied': True, 'source': 'lower', 'note': 'ok', 'margin': 1.0},
            {'name': 'upper_bridge_closed', 'satisfied': True, 'source': 'upper', 'note': 'ok', 'margin': 0.1},
        ],
    }))
    cert = build_golden_analytic_incompatibility_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-iv-contradiction-assembled'
    assert cert['analytic_incompatibility_certified'] is False
    assert 'tail_stability_certified' in cert['residual_iv_burden']


def test_stage87_driver_exposes_final_theorem_iv(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-iv-final-strong',
        'analytic_incompatibility_certified': True,
        'residual_iv_burden': [],
    }))
    report = build_golden_theorem_iv_report(base_K_values=[0.3])
    assert report['theorem_status'] == 'golden-theorem-iv-final-strong'
    assert report['analytic_incompatibility_certified'] is True
