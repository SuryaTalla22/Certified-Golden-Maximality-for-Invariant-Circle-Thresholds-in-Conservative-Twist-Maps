import numpy as np
from pathlib import Path
from kam_theorem_suite.lower_param.tangent_consistency_audit import run_phase4g_tangent_consistency


def test_phase4g_zero_seed(tmp_path):
    # At K=0, u=0 is exactly invariant for both signs; tangent residual should vanish.
    p = tmp_path / "K0p0000000000_M64_test.npz"
    np.savez(p, u=np.zeros(64), K=0.0)
    out = tmp_path / "out"
    s = run_phase4g_tangent_consistency([str(p)], str(out), grid_factors=[1,2])
    row = s["top_candidates"][0]
    assert row["best_native_scalar_residual_linf"] < 1e-12
    assert row["max_tangent_residual_linf_over_grids_best_sign"] < 1e-10
