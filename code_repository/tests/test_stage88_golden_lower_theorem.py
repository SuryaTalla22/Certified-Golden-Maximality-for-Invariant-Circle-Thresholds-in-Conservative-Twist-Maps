from __future__ import annotations

from kam_theorem_suite.golden_aposteriori import build_golden_theorem_iii_final_certificate


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage88_golden_lower_theorem_closes_when_all_witnesses_are_present(monkeypatch) -> None:
    import kam_theorem_suite.golden_aposteriori as gap

    monkeypatch.setattr(gap, 'build_golden_aposteriori_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'golden-aposteriori-bridge-strong',
        'selected_N': 64,
        'analytic_certificate': {},
    }))
    monkeypatch.setattr(gap, 'build_analytic_invariant_circle_certificate', lambda *args, **kwargs: _Dummy({}))
    monkeypatch.setattr(gap, 'build_infinite_dimensional_closure_witness', lambda *args, **kwargs: _Dummy({
        'resolved_mode_validation_certified': True,
        'tail_closure_certified': True,
        'small_divisor_closure_certified': True,
        'invariance_defect_closure_certified': True,
        'closure_status': 'infinite-dimensional-closure-strong',
    }))
    monkeypatch.setattr(gap, 'build_multiresolution_limit_closure_certificate', lambda *args, **kwargs: _Dummy({
        'limit_profile_ready_for_closure': True,
        'multiresolution_closure_status': 'multiresolution-limit-closure-strong',
    }))

    from kam_theorem_suite import torus_continuation as tc
    from kam_theorem_suite import golden_lower_neighborhood_stability as glns

    monkeypatch.setattr(tc, 'continue_invariant_circle_validations', lambda *args, **kwargs: _Dummy({}))
    monkeypatch.setattr(tc, 'build_torus_continuation_closure_certificate', lambda *args, **kwargs: _Dummy({
        'all_steps_locally_closed': True,
        'continuation_interval': [0.2, 0.3],
    }))
    monkeypatch.setattr(glns, 'build_golden_lower_neighborhood_stability_certificate', lambda *args, **kwargs: _Dummy({}))
    monkeypatch.setattr(glns, 'build_golden_lower_theorem_neighborhood_certificate', lambda *args, **kwargs: _Dummy({
        'lower_interval_certified': True,
        'stable_lower_interval': [0.18, 0.29],
    }))

    cert = build_golden_theorem_iii_final_certificate(base_K_values=[0.2, 0.25, 0.3]).to_dict()
    assert cert['theorem_iii_final_status'] == 'golden-theorem-iii-final-strong'
    assert cert['analytic_invariant_circle_exists'] is True
    assert cert['certified_below_threshold_interval'] == [0.2, 0.29]


def test_stage88_golden_lower_theorem_remains_incomplete_without_interval(monkeypatch) -> None:
    import kam_theorem_suite.golden_aposteriori as gap

    monkeypatch.setattr(gap, 'build_golden_aposteriori_certificate', lambda *args, **kwargs: _Dummy({'selected_N': 64}))
    monkeypatch.setattr(gap, 'build_analytic_invariant_circle_certificate', lambda *args, **kwargs: _Dummy({}))
    monkeypatch.setattr(gap, 'build_infinite_dimensional_closure_witness', lambda *args, **kwargs: _Dummy({
        'resolved_mode_validation_certified': True,
        'tail_closure_certified': True,
        'small_divisor_closure_certified': True,
        'invariance_defect_closure_certified': True,
        'closure_status': 'infinite-dimensional-closure-strong',
    }))
    cert = build_golden_theorem_iii_final_certificate(
        base_K_values=[0.2],
        continuation_closure_certificate={'all_steps_locally_closed': True, 'continuation_interval': None},
        lower_neighborhood_certificate={'lower_interval_certified': False, 'stable_lower_interval': None},
        multiresolution_limit_closure_certificate={'limit_profile_ready_for_closure': True},
    ).to_dict()
    assert cert['theorem_iii_final_status'] == 'golden-theorem-iii-infinite-dimensional-closure-incomplete'
    assert 'lower_interval_certified' in cert['residual_theorem_iii_burden']
