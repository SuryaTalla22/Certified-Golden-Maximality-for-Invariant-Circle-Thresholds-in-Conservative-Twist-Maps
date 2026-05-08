from __future__ import annotations

from kam_theorem_suite.audit.lower_anchor_phase2aa_raw_payload_export import (
    RAW_PAYLOAD_VERSION,
    attach_raw_validation_payload_to_candidate,
    build_raw_validation_payload,
)


def _attempt():
    u = [0.01, -0.005, 0.002, -0.001, 0.0005, -0.00025, 0.0001, -0.00005]
    z = u + [0.0]
    return {
        "raw_certificate": {
            "rho": 0.6180339887498949,
            "K": 0.1,
            "N": len(u),
            "sigma_used": 1e-4,
            "finite_B_norm": 2.5,
            "finite_lipschitz_bound": 0.3,
            "finite_contraction_bound": 0.7,
            "cohomological_inverse_bound": 3.0,
            "source_validation": {
                "u": u,
                "z": z,
                "lambda_value": 0.0,
            },
            "small_divisor_audit": {"cohomological_inverse_bound": 3.0},
        }
    }


def _row():
    return {
        "model_name": "unit_test_row",
        "sigma": 1e-4,
        "oversample_factor": 4,
        "radius_r": 1.0,
        "residual_Y": 0.1,
        "linear_Z": 0.2,
        "finite_nonlinear_term": 0.2,
        "finite_contraction_q": 0.7,
        "finite_poly_margin": 0.1,
        "tail_T": 0.3,
        "tail_response_bound": 0.2,
        "nonlinear_guard": 0.1,
        "allowable_tail_max": 0.7,
        "radii_margin": 0.4,
        "modewise_tail_ledger": {
            "golden_diophantine_constant": 1.7,
            "worst_finite_inverse": 2.0,
            "worst_finite_inverse_mode": 5,
        },
    }


def test_build_raw_payload_contains_stage1_fields():
    payload = build_raw_validation_payload(
        phase2n_attempt=_attempt(),
        selected_row=_row(),
        input_summary={"K_lo": 0.09, "K_hi": 0.11, "K_mid": 0.1, "rho": 0.6180339887498949, "N": 8},
        source_artifact="unit.json",
        stage="phase2p",
    )
    assert payload["raw_validation_payload_version"] == RAW_PAYLOAD_VERSION
    assert payload["source_validation"]["available"] is True
    assert len(payload["source_validation"]["u"]) == 8
    assert payload["source_fourier_coefficients"]["length"] == 8
    assert payload["residual"]["available"] is True
    assert payload["finite_linearization"]["available"] is True
    assert len(payload["finite_linearization"]["jacobian_row_abs_sums"]) == 9
    assert payload["preconditioner"]["available"] is True
    assert len(payload["preconditioner"]["inverse_norm_proxy_vector"]) >= 2
    assert payload["scalar_ledger_recompute"]["available"] is True


def test_attach_raw_payload_does_not_promote_candidate():
    candidate = {"schema": "phase2p_single_segment_candidate_v1", "theorem_facing": False, "promotion_allowed": False}
    out = attach_raw_validation_payload_to_candidate(
        candidate,
        phase2n_attempt=_attempt(),
        selected_row=_row(),
        input_summary={"K_lo": 0.09, "K_hi": 0.11, "K_mid": 0.1, "rho": 0.6180339887498949, "N": 8},
        source_artifact="unit.json",
        stage="phase2p",
    )
    assert out["theorem_facing"] is False
    assert out["promotion_allowed"] is False
    assert out["phase2aa_stage1b_export"]["does_not_change_theorem_facing_status"] is True
    assert out["rows"][0]["model_name"] == "unit_test_row"
    assert out["raw_validation_payload"]["source_validation"]["available"] is True
