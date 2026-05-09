from __future__ import annotations

import json
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_phase2aa_raw_data_audit import (
    audit_candidate,
    extract_candidate_rows,
    recompute_scalar_margin_from_row,
    summarize_audits,
)


def test_recompute_scalar_margin_from_row_matches_tail_components():
    row = {
        "radius_r": 10.0,
        "residual_Y": 1.0,
        "linear_Z": 0.2,
        "tail_response_bound": 2.0,
        "nonlinear_guard": 1.5,
        "radii_margin": 3.5,
    }
    out = recompute_scalar_margin_from_row(row)
    assert out["available"] is True
    assert abs(out["computed_margin"] - 3.5) < 1e-12
    assert out["matches_1e_minus_10"] is True


def test_extract_candidate_rows_from_phase2y_and_summary_deduplicates():
    payload = {
        "required_improvement_rows": [
            {"index": 5, "path": "a/p0005.json", "deficit": 1.0},
            {"index": 133, "path": "a/p0133.json", "deficit": 2.0},
        ],
        "best_failed_rows": [{"path": "a/p0005.json", "radii_margin": -1.0}],
    }
    rows = extract_candidate_rows(payload, target_indices=(5, 133))
    assert len(rows) == 2
    assert {r["index"] for r in rows} == {5, 133}


def test_audit_candidate_detects_raw_fields(tmp_path: Path):
    candidate = {
        "schema": "synthetic_phase2p_report",
        "status": "synthetic",
        "raw_certificate": {
            "K": 0.1,
            "rho": 0.6180339887498949,
            "sigma_used": 1e-7,
            "cohomological_inverse_bound": 2.0,
            "small_divisor_min_exact": 0.1,
            "source_validation": {"u": [0.0] * 64, "z": [0.0] * 65, "lambda_value": 0.0},
        },
        "rows": [{
            "model_name": "row",
            "radius_r": 10.0,
            "residual_Y": 1.0,
            "linear_Z": 0.2,
            "tail_T": 3.5,
            "tail_response_bound": 2.0,
            "nonlinear_guard": 1.5,
            "radii_margin": 3.5,
            "finite_contraction_q": 0.2,
            "sigma": 1e-7,
            "modewise_tail_ledger": {"top_contributors": [{"mode": 1, "response": 1.0}]},
            "residual_coefficients": [0.0] * 64,
            "finite_matrix": [[1.0, 0.0], [0.0, 1.0]],
            "approx_inverse": [[1.0, 0.0], [0.0, 1.0]],
        }],
    }
    path = tmp_path / "p0005.json"
    path.write_text(json.dumps(candidate))
    rec = audit_candidate({"index": 5, "path": str(path), "model_name": "row"}, root=".", deep=False)
    flags = rec["availability_flags"]
    assert flags["has_source_samples"] is True
    assert flags["has_residual_coefficients_or_samples"] is True
    assert flags["has_finite_matrix_or_jacobian"] is True
    assert flags["has_approx_inverse_or_preconditioner"] is True
    assert flags["has_modewise_tail_profile"] is True
    assert rec["raw_data_stage1_ready"] is True


def test_summarize_audits_counts_missing():
    summary = summarize_audits([
        {"artifact_exists": True, "raw_data_stage1_ready": False, "availability_flags": {"enough_for_tail_guard_prototype": True}, "missing_for_full_stage1_success": ["finite_linearized_matrix_or_operator"]},
        {"artifact_exists": True, "raw_data_stage1_ready": True, "availability_flags": {"enough_for_tail_guard_prototype": True}, "missing_for_full_stage1_success": []},
    ])
    assert summary["record_count"] == 2
    assert summary["raw_data_stage1_ready_count"] == 1
    assert summary["missing_field_counts"]["finite_linearized_matrix_or_operator"] == 1
