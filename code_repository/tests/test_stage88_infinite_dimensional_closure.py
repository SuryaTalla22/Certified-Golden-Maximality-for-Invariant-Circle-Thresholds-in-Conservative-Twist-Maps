from __future__ import annotations

import math

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.torus_validator import (
    build_analytic_invariant_circle_certificate,
    build_infinite_dimensional_closure_witness,
)


GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage88_infinite_dimensional_closure_can_be_certified(monkeypatch) -> None:
    import kam_theorem_suite.torus_validator as tv

    cert = build_analytic_invariant_circle_certificate(GOLDEN, 0.3, HarmonicFamily(), N=32, sigma_cap=0.02)
    cert.theorem_margin = 1.0e-3
    monkeypatch.setattr(tv, 'build_fourier_tail_closure_certificate', lambda *args, **kwargs: _Dummy({
        'tail_sum_certified': True,
        'tail_ready_for_theorem': True,
        'tail_closure_margin': 1.0e-3,
        'theorem_status': 'fourier-tail-closure-strong',
    }))
    monkeypatch.setattr(tv, 'build_small_divisor_closure_certificate', lambda *args, **kwargs: _Dummy({
        'divisor_tail_law_certified': True,
        'small_divisor_ready_for_theorem': True,
        'small_divisor_closure_margin': 1.0,
        'theorem_status': 'small-divisor-closure-strong',
    }))
    monkeypatch.setattr(tv, 'build_invariance_defect_closure_certificate', lambda *args, **kwargs: _Dummy({
        'defect_ready_for_closure': True,
        'combined_theorem_defect': 1.0e-8,
        'theorem_status': 'invariance-defect-closure-strong',
    }))
    witness = build_infinite_dimensional_closure_witness(cert).to_dict()
    assert witness['closure_status'] == 'infinite-dimensional-closure-strong'
    assert witness['tail_closure_certified'] is True
    assert witness['small_divisor_closure_certified'] is True
    assert witness['invariance_defect_closure_certified'] is True


def test_stage88_infinite_dimensional_closure_detects_missing_tail() -> None:
    cert = build_analytic_invariant_circle_certificate(GOLDEN, 0.3, HarmonicFamily(), N=32, sigma_cap=0.02)
    witness = build_infinite_dimensional_closure_witness(cert).to_dict()
    assert witness['closure_status'] in {
        'infinite-dimensional-closure-partial',
        'infinite-dimensional-closure-failed',
    }
