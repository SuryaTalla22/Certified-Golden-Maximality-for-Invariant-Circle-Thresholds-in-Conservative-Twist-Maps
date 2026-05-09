from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from kam_theorem_suite.audit.lower_anchor_phase2o_tail_radius import (
    Phase2OScanConfig,
    build_phase2o_candidate,
    build_phase2o_report,
    parse_float_list,
)


def _write_synthetic_attempt(path: Path, *, tail_l1: float = 1e-12) -> None:
    N = 16
    u = (1e-5 * np.sin(2 * np.pi * np.arange(N) / N)).tolist()
    attempt = {
        "schema": "phase2n_single_N_attempt_v1",
        "status": "phase2n-diagnostic-single-N",
        "config": {
            "segment_id": "synthetic",
            "K_lo": 0.1,
            "K_hi": 0.1001,
            "K_mid": 0.10005,
            "N": N,
            "oversample_factor": 4,
            "sigma_cap": 1e-4,
        },
        "strict_ledger": {
            "rho": 0.6180339887498949,
            "K": 0.10005,
            "N": N,
            "sigma": 1e-4,
            "residual_Y": 1e-12,
            "linear_defect_Z": 0.1,
            "radius_r": 1e-5,
            "tail_bound_T": 1e-12,
            "radii_lhs": 1.0000002e-6,
            "radii_margin": 8.999998e-6,
            "tail_response_bound": 1e-12,
            "nonlinear_response_bound": 0.0,
            "theorem_ready": True,
            "failure_reasons": [],
        },
        "score": {
            "theorem_ready": True,
            "radii_margin": 8.999998e-6,
            "residual_Y": 1e-12,
            "linear_Z": 0.1,
            "radius_r": 1e-5,
            "tail_T": 1e-12,
            "finite_radii_margin": 1e-5,
            "source_theorem_margin": 1e-5,
            "selected_N": N,
            "sigma": 1e-4,
            "failure_reasons": [],
        },
        "raw_certificate": {
            "rho": 0.6180339887498949,
            "K": 0.10005,
            "N": N,
            "sigma_used": 1e-4,
            "strip_width_proxy": 0.01,
            "finite_eta": 1e-12,
            "finite_B_norm": 2.0,
            "finite_lipschitz_bound": 1.0,
            "finite_contraction_bound": 2e-5,
            "finite_radii_margin": 9e-6,
            "cohomological_inverse_bound": 2.0,
            "tail_bound": {
                "tail_l1": tail_l1,
                "theorem_usable": True,
            },
            "source_validation": {
                "u": u,
                "z": u + [0.0],
                "lambda_value": 0.0,
            },
        },
    }
    path.write_text(json.dumps(attempt))


def test_parse_float_list():
    assert parse_float_list("1,2,2,0,-3,4") == (1.0, 2.0, 4.0)


def test_phase2o_report_and_candidate(tmp_path: Path):
    p = tmp_path / "attempt.json"
    _write_synthetic_attempt(p)
    cfg = Phase2OScanConfig(
        input_path=str(p),
        radius_multipliers=(1.0, 1.5),
        sigma_values=(1e-4, 5e-5),
        tail_band_fractions=(0.65,),
        tail_safety_factors=(4.0,),
    )
    report = build_phase2o_report(p, cfg)
    assert report.input_summary.has_raw_certificate
    assert report.theorem_eligible_count >= 1
    assert report.strict_source_row.theorem_ready
    candidate = build_phase2o_candidate(report, source_artifact="synthetic")
    assert candidate["schema"] == "phase2o_single_segment_candidate_v1"
    assert candidate["anchor_segments"]
