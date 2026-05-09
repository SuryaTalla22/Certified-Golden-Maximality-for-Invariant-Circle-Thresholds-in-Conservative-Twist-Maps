from __future__ import annotations

import numpy as np

from kam_theorem_suite.lower_param.lift_alias_audit import scalar_residual_lift_aware, lift_embedding_and_tangent_audit


def test_lift_aware_embedding_residual_matches_scalar_residual_at_zero_K():
    M=64; K=0.0; omega=(5**0.5-1)/2
    u=np.zeros(M)
    aud=lift_embedding_and_tangent_audit(u,K,omega)
    assert np.max(np.abs(aud['scalar_residual'])) < 1e-14
    assert np.max(np.abs(aud['x_lift_residual'])) < 1e-14
    assert np.max(np.abs(aud['r_lift_residual'])) < 1e-14
    assert np.max(np.abs(aud['tangent_residual_x'])) < 1e-12
    assert np.max(np.abs(aud['tangent_residual_r'])) < 1e-12


def test_scalar_residual_shape():
    M=32; u=0.01*np.sin(2*np.pi*np.arange(M)/M)
    r=scalar_residual_lift_aware(u,0.1,(5**0.5-1)/2)
    assert r.shape == (M,)
    assert np.all(np.isfinite(r))
