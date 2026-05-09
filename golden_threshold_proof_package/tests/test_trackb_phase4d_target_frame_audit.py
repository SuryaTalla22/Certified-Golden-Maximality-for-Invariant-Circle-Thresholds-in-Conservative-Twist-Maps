import numpy as np

from kam_theorem_suite.lower_param.target_frame_audit import metrics_for_u, target_frame_auto_reducibility_audit


def test_zero_embedding_k0_has_exact_reducibility_shape():
    M = 128
    u = np.zeros(M)
    aud = target_frame_auto_reducibility_audit(u, 0.0, (np.sqrt(5.0)-1.0)/2.0)
    assert np.max(np.abs(aud['scalar_residual'])) < 1e-14
    assert np.max(np.abs(aud['x_lift_residual'])) < 1e-14
    assert np.max(np.abs(aud['r_lift_residual'])) < 1e-14
    assert np.max(np.abs(aud['A11'] - 1.0)) < 1e-14
    assert np.max(np.abs(aud['A21'])) < 1e-14
    assert np.max(np.abs(aud['A22'] - 1.0)) < 1e-14
    assert abs(float(np.mean(aud['A12'])) - 1.0) < 1e-14
    assert np.max(np.abs(aud['det_source'] - 1.0)) < 1e-14
    assert np.max(np.abs(aud['det_target'] - 1.0)) < 1e-14


def test_metrics_include_old_and_target_frame_fields():
    M = 64
    theta = np.arange(M) / M
    u = 1e-4 * np.sin(2*np.pi*theta)
    met = metrics_for_u(u, 0.1, (np.sqrt(5.0)-1.0)/2.0, [1.003], [0.75])
    sm = met['scalar_metrics']
    assert 'target_frame_det_defect_linf' in sm
    assert 'shifted_normal_target_det_defect_linf' in sm
    assert sm['target_frame_det_defect_linf'] < 1e-12
    assert 'nu_1.003000' in met['weighted_metrics']
