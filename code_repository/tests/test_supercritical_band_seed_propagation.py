from kam_theorem_suite import supercritical_bands as sb


def test_supercritical_band_recursion_uses_parent_branch_seeds(monkeypatch):
    calls = []

    def fake_certify(*, p, q, K_lo, K_hi, family, x_guess=None, target_residue=0.25):
        calls.append(x_guess)
        return sb.HyperbolicWindowCertificate(
            p=p,
            q=q,
            K_lo=K_lo,
            K_hi=K_hi,
            target_residue=target_residue,
            residue_interval_lo=0.3,
            residue_interval_hi=0.4,
            abs_residue_interval_lo=0.3,
            abs_residue_interval_hi=0.4,
            g_interval_lo=0.05,
            g_interval_hi=0.15,
            gprime_interval_lo=-1.0,
            gprime_interval_hi=1.0,
            trace_interval_lo=0.0,
            trace_interval_hi=0.0,
            trace_abs_lower_bound=0.0,
            hyperbolicity_margin=-1.0,
            regime="mixed",
            certified_above_target=False,
            certified_hyperbolic=False,
            tangent_inclusion_success=False,
            branch_tube={"x_left": [1.0], "x_mid": [2.0], "x_right": [3.0]},
            message="stub",
        )

    monkeypatch.setattr(sb, "certify_hyperbolic_window", fake_certify)
    sb.build_supercritical_band_report(1, 3, 0.1, 0.2, initial_subdivisions=1, max_depth=1, min_width=1e-6)
    assert calls[0] is None
    assert calls[1] is not None
    assert calls[2] is not None
