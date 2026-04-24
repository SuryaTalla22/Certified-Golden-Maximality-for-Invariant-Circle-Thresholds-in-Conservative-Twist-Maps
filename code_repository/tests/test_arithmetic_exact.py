from __future__ import annotations

from kam_theorem_suite.arithmetic_exact import (
    cycle_eta_estimates,
    known_constant_type_eta,
    periodic_cf_value,
)


def test_golden_periodic_value():
    rho = float(periodic_cf_value((1,), dps=100))
    assert abs(rho - 1.618033988749895) < 1e-12


def test_constant_type_eta_formula_matches_known_values():
    assert abs(known_constant_type_eta(1) - 1 / (5 ** 0.5)) < 1e-15
    assert abs(known_constant_type_eta(2) - 1 / (8 ** 0.5)) < 1e-15


def test_cycle_eta_estimate_for_golden_is_close_to_expected_value():
    stats = cycle_eta_estimates((1,), burn_in_cycles=18, dps=150)
    assert abs(stats["eta_lo"] - 1 / (5 ** 0.5)) < 2e-3
    assert stats["eta_hi"] >= stats["eta_lo"]
