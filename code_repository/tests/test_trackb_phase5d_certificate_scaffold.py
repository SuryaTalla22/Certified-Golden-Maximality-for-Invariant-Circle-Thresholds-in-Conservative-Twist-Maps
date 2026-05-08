from pathlib import Path
from kam_theorem_suite.lower_param.phase5d_certificate_scaffold import (
    assemble_certificate_scaffold,
    select_candidate,
    validate_certificate_scaffold,
    run_negative_controls,
    write_json,
)


def _candidate():
    r = 3e-5
    y = 7.0e-8
    z = 0.23
    q = 551.0
    lhs = y + z * r + q * r * r
    return {
        "K": 0.971635,
        "M": 8192,
        "nu": 1.001,
        "radius": r,
        "grid_factor": 4,
        "grid_size": 32768,
        "cutoff_spec": "full",
        "tail_start_frac": 0.9,
        "Y_interval_upper": y,
        "Z_interval_upper": z,
        "Q_interval_upper": q,
        "radii_lhs_interval_upper": lhs,
        "radii_margin_interval_lower": r - lhs,
        "radii_relative_margin_interval_lower": (r - lhs) / r,
        "small_divisor_min_denominator_lower": 1.0e-3,
        "small_divisor_min_mode": 2584,
        "cohomology_inverse_linf_resolved_upper": 920.0,
        "residual_l1_nu_total_upper": 2.1e-8,
        "scalar_residual_linf": 1.7e-9,
        "derivative_residual_linf": 2.1e-5,
        "upper_triangular_defect_linf_max": 1.8e-4,
        "a11_minus_1_linf": 5e-6,
        "a21_linf": 1.8e-4,
        "a22_minus_1_linf": 3e-6,
        "source_frame_det_defect_linf": 3e-16,
        "target_frame_det_defect_linf": 3e-16,
        "twist_average": 1.4,
        "twist_min": -0.2,
        "twist_max": 7.0,
        "dominant_interval_term": "Zr_interval",
        "recommendation_label": "backend_ready_candidate",
        "any_positive_interval_margin": True,
        "npz_path": "seed.npz",
        "record_path": "record.json",
        "tail_residual_component_upper": 1e-9,
    }


def test_assemble_and_validate():
    cand = _candidate()
    cert = assemble_certificate_scaffold(cand, {"selection_mode": "unit_test"})
    replay = validate_certificate_scaffold(cert)
    assert replay["passed"], replay["failed_checks"]
    assert cert["theorem_facing"] is False
    assert cert["promotion_allowed"] is False
    assert cert["interval_backend_bounds"]["radii_margin_interval_lower_recomputed"] > 0


def test_negative_controls_fail():
    cert = assemble_certificate_scaffold(_candidate(), {"selection_mode": "unit_test"})
    neg = run_negative_controls(cert)
    assert neg["negative_controls_passed"] is True


def test_select_candidate_prefers_ready_full(tmp_path: Path):
    c1 = _candidate()
    c1["cutoff_spec"] = "frac:0.95"
    c2 = _candidate()
    c2["cutoff_spec"] = "full"
    summary = {"top_candidates": [c1, c2]}
    p = tmp_path / "summary.json"
    write_json(p, summary)
    selected, info = select_candidate(summary_path=p, prefer_cutoff="full", prefer_tail_start=0.9, prefer_radius=3e-5)
    assert selected["cutoff_spec"] == "full"
    assert info["candidate_count"] == 2
