from __future__ import annotations

from kam_theorem_suite.interval_utils import iv_scalar, iv_vec
from kam_theorem_suite.standard_map import (
    HarmonicFamily,
    residue_derivative,
    residue_derivative_iv,
    solve_periodic_orbit,
)


def test_interval_residue_derivative_contains_point_derivative():
    fam = HarmonicFamily()
    sol = solve_periodic_orbit(3, 5, 0.96, fam)
    assert sol["success"]
    x = sol["x"]
    point_val = residue_derivative(x, 3, 0.96, fam)
    dR_iv, tangent_res = residue_derivative_iv(iv_vec(x, 1e-12), 3, iv_scalar(0.96), fam)
    assert tangent_res.success
    assert float(dR_iv.a) <= point_val <= float(dR_iv.b)
