import numpy as np
from pathlib import Path

from kam_theorem_suite.lower_param.phase5b_interval_component import run_phase5b_interval_components


def test_phase5b_smoke(tmp_path: Path):
    M = 64
    theta = np.arange(M) / M
    u = 0.01 * np.sin(2*np.pi*theta)
    npz = tmp_path / "K0p0100000000_M64_test.npz"
    np.savez(npz, u=u, K=0.01)
    out = tmp_path / "out"
    s = run_phase5b_interval_components(
        npz_paths=[str(npz)],
        nu_grid=[1.001],
        cutoffs=["full", "frac:0.95"],
        tail_start_fracs=[0.75],
        grid_factors=[1],
        radii=[1e-5],
        workers=1,
        out_dir=str(out),
        force=True,
    )
    assert s["counts"]["completed_records"] == 2
    assert (out / "phase5b_interval_component_summary.json").exists()
    assert (out / "phase5b_interval_component_results.csv").exists()
