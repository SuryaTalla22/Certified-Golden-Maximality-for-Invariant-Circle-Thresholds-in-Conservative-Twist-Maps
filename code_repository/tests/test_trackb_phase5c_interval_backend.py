from __future__ import annotations
import numpy as np
from pathlib import Path
from kam_theorem_suite.lower_param.phase5c_interval_backend import run_phase5c_interval_backend


def test_phase5c_smoke(tmp_path: Path):
    M = 128
    u = np.zeros(M)
    npz = tmp_path / 'K0p0100000000_M128.npz'
    np.savez(npz, u=u, K=0.01, omega=(np.sqrt(5)-1)/2)
    out = tmp_path / 'out'
    s = run_phase5c_interval_backend(
        npz_paths=[str(npz)], nu_grid=[1.001], cutoffs=['frac:0.90'], tail_start_fracs=[0.90],
        grid_factors=[1], radii=[1e-4], interval_inflation=0.05, z_inflation=0.05, q_inflation=0.05,
        rounding_slack=1e-12, small_divisor_slack=1e-15, residual_slack=1e-14, tail_safety=2.0,
        q_scale=0.038, workers=1, out_dir=str(out), force=True)
    assert s['counts']['completed_records'] == 1
    assert (out / 'phase5c_interval_backend_summary.json').exists()
    assert (out / 'records').exists()
