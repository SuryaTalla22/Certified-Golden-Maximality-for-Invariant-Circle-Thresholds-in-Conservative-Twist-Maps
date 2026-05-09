from kam_theorem_suite.lower_param.standard_sine_embedding import SeedSolveConfig, solve_anchor_with_continuation

def test_trackb_phase1_seed_smoke_low_k():
    cfg=SeedSolveConfig(K_target=0.01,M=32,continuation_steps=2,max_newton=5,gmres_rtol=1e-8,gmres_restart=20,gmres_maxiter=80,accept_linf=1e-6)
    r=solve_anchor_with_continuation(cfg)
    assert r.residual_linf < 1e-6
    assert r.to_dict()["diagnostic_only"] is True
