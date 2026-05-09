from __future__ import annotations
import json
import numpy as np

from kam_theorem_suite.lower_param.phase5a_radii_prep import run_phase5a_radii_prep


def test_phase5a_radii_prep_smoke(tmp_path):
    M = 64
    theta = np.arange(M) / M
    u = 1e-3 * np.sin(2*np.pi*theta)
    path = tmp_path / 'K0p1000000000_M64_test.npz'
    np.savez(path, u=u, K=np.array([0.1]), omega=np.array([(5**0.5-1)/2]))
    out = tmp_path / 'out'
    summary = run_phase5a_radii_prep(
        npz_paths=[str(path)],
        nu_grid=[1.001],
        cutoff_specs=['full','frac:0.9'],
        tail_start_fracs=[0.75],
        grid_factors=[1],
        out_dir=str(out),
        workers=1,
        force=True,
    )
    assert summary['status'] == 'phase5a-radii-prep-complete'
    assert summary['counts']['completed_records'] == 2
    assert (out / 'phase5a_radii_prep_summary.json').exists()
    assert (out / 'phase5a_radii_prep_results.csv').exists()
    first = summary['top_candidates'][0]
    assert first['K'] == 0.1
    assert first['M'] == M
    assert 'Y_cohomology_proxy' in first
    assert 'recommendation_label' in first
