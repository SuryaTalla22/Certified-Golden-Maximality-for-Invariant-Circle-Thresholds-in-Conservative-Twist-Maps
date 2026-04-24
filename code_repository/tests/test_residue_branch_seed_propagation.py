import numpy as np

from kam_theorem_suite import residue_branch as rb


def test_adaptive_crossing_propagates_parent_branch_seeds(monkeypatch):
    calls = []

    def fake_analyze(*, p, q, K_lo, K_hi, family, x_guess=None, target_residue=0.25, depth=0):
        calls.append(None if x_guess is None else np.asarray(x_guess, dtype=float).tolist())
        left = [depth + 1.0]
        mid = [depth + 2.0]
        right = [depth + 3.0]
        return rb.ResidueBranchWindowCertificate(
            p=p,
            q=q,
            K_lo=K_lo,
            K_hi=K_hi,
            depth=depth,
            target_residue=target_residue,
            branch_tube={"x_left": left, "x_mid": mid, "x_right": right},
            g_interval_lo=-1.0,
            g_interval_hi=1.0,
            gprime_interval_lo=-1.0,
            gprime_interval_hi=1.0,
            derivative_sign="mixed",
            derivative_away_from_zero=False,
            strict_sign_change=False,
            monotone_unique_crossing=False,
            endpoint_left={"side": "mixed"},
            endpoint_mid={"side": "mixed"},
            endpoint_right={"side": "mixed"},
            interval_newton={"success": False},
            status="incomplete",
            message="stub",
        )

    monkeypatch.setattr(rb, "analyze_residue_branch_window", fake_analyze)
    rb.adaptive_localize_residue_crossing(1, 3, 0.1, 0.2, max_depth=1, min_width=1e-6)
    assert calls[0] is None
    assert calls[1] is not None
    assert calls[2] is not None
