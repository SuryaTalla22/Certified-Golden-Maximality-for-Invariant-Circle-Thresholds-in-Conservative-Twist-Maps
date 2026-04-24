from __future__ import annotations

from kam_theorem_suite.golden_recurrence_rate_control import build_golden_recurrence_rate_certificate
from kam_theorem_suite.proof_driver import build_golden_recurrence_rate_report
from tests.test_certified_tail_modulus_control import _synthetic_ladder


def test_golden_recurrence_rate_builds_phi_step_profile() -> None:
    cert = build_golden_recurrence_rate_certificate(_synthetic_ladder(), min_chain_length=5)
    d = cert.to_dict()
    assert d['theorem_status'].startswith('golden-recurrence-rate-')
    assert d['chain_length'] >= 5
    assert d['chosen_step_exponent'] is not None
    assert d['chosen_step_exponent'] > 0.0
    assert d['exact_fibonacci_recurrence'] is True
    assert d['actual_tail_dominated_by_golden_rate'] is True
    assert d['golden_tail_nonincreasing'] is True
    assert d['selected_golden_interval_lo'] is not None
    assert d['selected_golden_interval_hi'] is not None
    assert d['rate_golden_intersection_lo'] is not None
    assert d['rate_golden_intersection_hi'] is not None
    assert d['first_golden_tail_radius'] >= d['last_golden_tail_radius']


def test_driver_exposes_golden_recurrence_rate_layer() -> None:
    report = build_golden_recurrence_rate_report(_synthetic_ladder(), min_chain_length=5)
    assert report['chain_length'] >= 5
    assert report['theorem_status'].startswith('golden-recurrence-rate-')
