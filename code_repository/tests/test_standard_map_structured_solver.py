import numpy as np

from kam_theorem_suite.standard_map import (
    HarmonicFamily,
    periodic_orbit_residual,
    solve_periodic_orbit,
)


def test_structured_solver_converges_on_seeded_orbit():
    family = HarmonicFamily()
    p, q, K = 13, 21, 0.95
    seed = np.arange(q, dtype=float) * (p / q)
    sol = solve_periodic_orbit(p, q, K, family=family, x0=seed)
    assert sol["success"]
    res = periodic_orbit_residual(np.asarray(sol["x"], dtype=float), p, K, family)
    assert float(np.max(np.abs(res))) < 1e-8
