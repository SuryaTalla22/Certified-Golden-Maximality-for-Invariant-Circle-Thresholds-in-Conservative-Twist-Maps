from __future__ import annotations

from kam_theorem_suite.proof_driver import build_transport_slope_weighted_golden_rate_report
from kam_theorem_suite.transport_slope_weighted_golden_rate_control import build_transport_slope_weighted_golden_rate_certificate
from tests.test_certified_tail_modulus_control import _synthetic_ladder


def test_transport_slope_weighted_golden_rate_builds_weighted_phi_profile() -> None:
    cert = build_transport_slope_weighted_golden_rate_certificate(_synthetic_ladder(), min_chain_length=5)
    d = cert.to_dict()
    assert d['theorem_status'].startswith('transport-slope-weighted-golden-rate-')
    assert d['chain_length'] >= 5
    assert d['chosen_weighted_step_exponent'] is not None
    assert d['chosen_weighted_step_exponent'] > 0.0
    assert d['transport_strength_mean'] is not None
    assert d['actual_tail_dominated_by_weighted_rate'] is True
    assert d['weighted_tail_nonincreasing'] is True
    assert d['selected_weighted_interval_lo'] is not None
    assert d['selected_weighted_interval_hi'] is not None
    assert d['weighted_golden_intersection_lo'] is not None
    assert d['weighted_golden_intersection_hi'] is not None
    assert d['first_weighted_tail_radius'] >= d['last_weighted_tail_radius']


def test_driver_exposes_transport_slope_weighted_golden_rate_layer() -> None:
    report = build_transport_slope_weighted_golden_rate_report(_synthetic_ladder(), min_chain_length=5)
    assert report['chain_length'] >= 5
    assert report['theorem_status'].startswith('transport-slope-weighted-golden-rate-')
