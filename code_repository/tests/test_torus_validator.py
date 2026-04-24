from __future__ import annotations

import math

from kam_theorem_suite.proof_driver import (
    build_existence_crossing_bridge_report,
    build_torus_validation_report,
)
from kam_theorem_suite.torus_validator import (
    solve_invariant_circle_graph,
    validate_invariant_circle_graph,
)
from kam_theorem_suite.standard_map import HarmonicFamily


GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def test_invariant_circle_solver_converges_for_subcritical_golden_case():
    fam = HarmonicFamily()
    sol = solve_invariant_circle_graph(GOLDEN, 0.5, fam, N=64)
    assert sol.success
    assert sol.residual_inf < 1e-10
    assert abs(sol.lambda_value) < 1e-10


def test_invariant_circle_validator_closes_radii_polynomial_ball():
    fam = HarmonicFamily()
    val = validate_invariant_circle_graph(GOLDEN, 0.5, fam, N=64)
    assert val.success
    assert val.radius > 0.0
    assert val.contraction_bound < 1.0
    assert val.oversampled_residual_inf < 1e-10


def test_driver_bridge_includes_torus_and_crossing_sections():
    fam = HarmonicFamily()
    torus = build_torus_validation_report(GOLDEN, 0.5, fam, N=64)
    assert torus["success"]
    bridge = build_existence_crossing_bridge_report(
        rho=GOLDEN,
        K=0.5,
        p=3,
        q=5,
        K_lo=0.969,
        K_hi=0.972,
        family=fam,
        N=64,
    )
    assert "torus_validation" in bridge
    assert "crossing_window" in bridge
    assert bridge["relation"]["torus_validated"]
