from __future__ import annotations

import numpy as np

from kam_theorem_suite.lower_param.dealiased_polish import DealiasedProjectedResidual, resample_periodic


def test_zero_seed_residual_is_finite():
    op = DealiasedProjectedResidual(64, 0.1, oversample=2)
    u = np.zeros(64)
    r = op.residual_projected(u, pin=False)
    assert r.shape == (64,)
    assert np.all(np.isfinite(r))


def test_resample_preserves_constant():
    u = np.ones(64) * 0.125
    v = resample_periodic(u, 128)
    assert v.shape == (128,)
    assert np.max(np.abs(v - 0.125)) < 1e-12
