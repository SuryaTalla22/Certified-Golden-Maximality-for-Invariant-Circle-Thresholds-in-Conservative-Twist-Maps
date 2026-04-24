from __future__ import annotations

from kam_theorem_suite.proof_driver import build_rate_aware_tail_modulus_report
from kam_theorem_suite.rate_aware_tail_modulus_control import build_rate_aware_tail_modulus_certificate
from tests.test_certified_tail_modulus_control import _synthetic_ladder


def test_rate_aware_tail_modulus_builds_q_scaled_rate_profile() -> None:
    cert = build_rate_aware_tail_modulus_certificate(_synthetic_ladder(), min_chain_length=5)
    d = cert.to_dict()
    assert d['theorem_status'].startswith('rate-aware-tail-modulus-')
    assert d['chain_length'] >= 5
    assert d['chosen_rate_exponent'] is not None
    assert d['chosen_rate_exponent'] > 0.0
    assert d['actual_tail_dominated_by_rate'] is True
    assert d['rate_tail_nonincreasing'] is True
    assert d['selected_rate_interval_lo'] is not None
    assert d['selected_rate_interval_hi'] is not None
    assert d['modulus_rate_intersection_lo'] is not None
    assert d['modulus_rate_intersection_hi'] is not None
    assert d['first_rate_tail_radius'] >= d['last_rate_tail_radius']


def test_driver_exposes_rate_aware_tail_modulus_layer() -> None:
    report = build_rate_aware_tail_modulus_report(_synthetic_ladder(), min_chain_length=5)
    assert report['chain_length'] >= 5
    assert report['theorem_status'].startswith('rate-aware-tail-modulus-')
