from __future__ import annotations

from kam_theorem_suite.audit.lower_anchor_phase2aa_stage2a_expand import select_expand_rows, build_expand_plan
import json
from pathlib import Path


def test_select_expand_rows_prefers_qsafe_sensitive_rows():
    phase2y = {
        "required_improvement_rows": [
            {
                "index": 5,
                "bucket": "safe_q_small_gap",
                "finite_contraction_q": 0.88,
                "needs_finite_q_upgrade": False,
                "deficit": 1e-8,
                "radii_margin": -1e-8,
                "tail_response_reduction_frac_needed": 0.04,
                "guard_reduction_frac_needed": 0.11,
                "tail_response_factor_needed": 0.96,
                "guard_factor_needed": 0.89,
                "recommended_upgrade": "coefficient_aware_nonlinear_guard",
                "closeable_by_tail_response_5pct": True,
            },
            {
                "index": 6,
                "bucket": "q_over_one",
                "finite_contraction_q": 1.01,
                "needs_finite_q_upgrade": True,
                "deficit": 1e-8,
                "tail_response_reduction_frac_needed": 0.01,
                "guard_reduction_frac_needed": 0.01,
                "recommended_upgrade": "diagonal_or_weighted_finite_krawczyk",
            },
            {
                "index": 7,
                "bucket": "tail_or_guard_dominated",
                "finite_contraction_q": 0.97,
                "needs_finite_q_upgrade": False,
                "deficit": 1e-7,
                "tail_response_reduction_frac_needed": 0.20,
                "guard_reduction_frac_needed": 0.30,
                "recommended_upgrade": "modewise_tail_response_sharpening",
            },
        ]
    }
    rows = select_expand_rows(phase2y, max_indices=10)
    assert [r.index for r in rows] == [5, 7]
    assert rows[0].priority_score < rows[1].priority_score


def test_build_expand_plan(tmp_path: Path):
    p = tmp_path / "phase2y.json"
    p.write_text(json.dumps({"required_improvement_rows": [{
        "index": 123,
        "bucket": "q_boundary",
        "finite_contraction_q": 0.995,
        "needs_finite_q_upgrade": False,
        "deficit": 2e-8,
        "tail_response_reduction_frac_needed": 0.06,
        "guard_reduction_frac_needed": 0.18,
        "recommended_upgrade": "coefficient_aware_nonlinear_guard",
        "closeable_by_tail_response_10pct": True,
    }]}))
    plan = build_expand_plan(phase2y_path=p, max_indices=5)
    assert plan["status"] == "phase2aa-stage2a-expand-plan-complete"
    assert plan["selected_indices"] == [123]
    assert plan["selected_indices_csv"] == "123"
    assert plan["promotion_allowed"] is False
