import numpy as np
from kam_theorem_suite.lower_param.oversampled_lsq_polish import OversampledLeastSquaresResidual


def test_augmented_shapes_and_adjoint_smoke():
    M = 32
    op = OversampledLeastSquaresResidual(M, K=0.1, oversample=2, gauge_value=0.0)
    u = np.zeros(M)
    A = op.linop_augmented(u)
    x = np.random.default_rng(1).normal(size=M)
    y = np.random.default_rng(2).normal(size=op.L + 1)
    Ax = A.matvec(x)
    ATy = A.rmatvec(y)
    assert Ax.shape == (op.L + 1,)
    assert ATy.shape == (M,)
    assert np.all(np.isfinite(Ax))
    assert np.all(np.isfinite(ATy))


def test_residual_small_at_zero_for_K_zero():
    M = 32
    op = OversampledLeastSquaresResidual(M, K=0.0, oversample=2)
    u = np.zeros(M)
    assert np.max(np.abs(op.residual_L_only(u))) < 1e-14
