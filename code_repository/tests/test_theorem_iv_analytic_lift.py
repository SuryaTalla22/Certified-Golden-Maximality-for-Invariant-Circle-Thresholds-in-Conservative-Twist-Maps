from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_golden_analytic_incompatibility_lift_report,
    build_golden_theorem_iv_report,
)
from kam_theorem_suite.theorem_iv_analytic_lift import (
    build_golden_analytic_incompatibility_lift_certificate,
)


def test_analytic_lift_front_only_when_front_is_strong(monkeypatch) -> None:
    import kam_theorem_suite.theorem_iv_analytic_lift as tal

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(tal, 'build_golden_nonexistence_front_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-nonexistence-front-strong',
        'computational_front_margin': 0.12,
        'hypotheses': [
            {'name': 'stable_lower_object', 'satisfied': True, 'source': 'lower', 'note': 'ok', 'margin': 1.0},
            {'name': 'upper_bridge_closed', 'satisfied': True, 'source': 'upper', 'note': 'ok', 'margin': 0.1},
        ],
    }))
    cert = build_golden_analytic_incompatibility_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-analytic-incompatibility-lift-front-only'
    assert cert['open_hypotheses'] == []
    assert set(cert['active_assumptions']) == {
        'obstruction_implies_no_analytic_circle',
        'final_function_space_promotion',
        'universality_class_embedding',
    }


def test_analytic_lift_conditional_strong_when_assumptions_are_toggled_on(monkeypatch) -> None:
    import kam_theorem_suite.theorem_iv_analytic_lift as tal

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(tal, 'build_golden_nonexistence_front_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-nonexistence-front-strong',
        'computational_front_margin': 0.2,
        'hypotheses': [
            {'name': 'stable_lower_object', 'satisfied': True, 'source': 'lower', 'note': 'ok', 'margin': 1.0},
            {'name': 'upper_bridge_closed', 'satisfied': True, 'source': 'upper', 'note': 'ok', 'margin': 0.1},
        ],
    }))
    cert = build_golden_analytic_incompatibility_lift_certificate(
        base_K_values=[0.3],
        assume_final_function_space_promotion=True,
        assume_obstruction_excludes_analytic_circle=True,
        assume_universality_embedding=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-analytic-incompatibility-lift-conditional-strong'
    assert cert['active_assumptions'] == []


def test_analytic_lift_stays_partial_when_front_is_not_closed(monkeypatch) -> None:
    import kam_theorem_suite.theorem_iv_analytic_lift as tal

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(tal, 'build_golden_nonexistence_front_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-nonexistence-front-moderate',
        'computational_front_margin': 0.01,
        'hypotheses': [
            {'name': 'stable_lower_object', 'satisfied': True, 'source': 'lower', 'note': 'ok', 'margin': 1.0},
            {'name': 'upper_bridge_closed', 'satisfied': False, 'source': 'upper', 'note': 'open', 'margin': -0.05},
        ],
    }))
    cert = build_golden_analytic_incompatibility_lift_certificate(
        base_K_values=[0.3],
        assume_final_function_space_promotion=True,
        assume_obstruction_excludes_analytic_circle=True,
        assume_universality_embedding=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-analytic-incompatibility-lift-conditional-partial'
    assert cert['open_hypotheses'] == ['upper_bridge_closed']


def test_driver_exposes_analytic_lift_and_theorem_iv_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    class _Dummy:
        def __init__(self, payload):
            self._payload = payload
        def to_dict(self):
            return dict(self._payload)

    monkeypatch.setattr(pd, 'build_golden_analytic_incompatibility_lift_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-front-only',
        'active_assumptions': ['final_function_space_promotion'],
    }))
    monkeypatch.setattr(pd, 'build_golden_theorem_iv_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-analytic-incompatibility-lift-conditional-strong',
        'active_assumptions': [],
    }))

    lift_report = build_golden_analytic_incompatibility_lift_report(base_K_values=[0.3])
    theorem_report = build_golden_theorem_iv_report(base_K_values=[0.3])
    assert lift_report['theorem_status'] == 'golden-analytic-incompatibility-lift-front-only'
    assert theorem_report['theorem_status'] == 'golden-analytic-incompatibility-lift-conditional-strong'
