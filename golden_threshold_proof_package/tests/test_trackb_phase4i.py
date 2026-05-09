from __future__ import annotations
import numpy as np

from kam_theorem_suite.lower_param.phase4i_common import (
    GOLDEN_ROTATION,
    interp_values,
    interp_adjoint_values,
    scalar_residual_on_grid_from_core,
)
from kam_theorem_suite.lower_param.phase4i_h1_polish import _make_operator


def test_interp_adjoint_identity_small():
    rng = np.random.default_rng(123)
    M = 16
    L = 64
    x = rng.normal(size=M)
    y = rng.normal(size=L)
    lhs = float(np.dot(interp_values(x, L), y))
    rhs = float(np.dot(x, interp_adjoint_values(y, M)))
    assert abs(lhs - rhs) < 1e-10


def test_zero_residual_at_K0_u0():
    u = np.zeros(32)
    r = scalar_residual_on_grid_from_core(u, 0.0, GOLDEN_ROTATION, 32)
    assert np.max(np.abs(r)) < 1e-14


def test_h1_operator_adjoint_small():
    rng = np.random.default_rng(456)
    M = 16
    L = 32
    u = 1e-3 * rng.normal(size=M)
    A, F, _ = _make_operator(u, 0.1, GOLDEN_ROTATION, L, lambda_h1=0.7, eta_high=1e-8, cutoff_mode=6)
    x = rng.normal(size=M)
    y = rng.normal(size=A.shape[0])
    lhs = float(np.dot(A.matvec(x), y))
    rhs = float(np.dot(x, A.rmatvec(y)))
    assert abs(lhs - rhs) < 1e-7 * max(1.0, abs(lhs), abs(rhs))
