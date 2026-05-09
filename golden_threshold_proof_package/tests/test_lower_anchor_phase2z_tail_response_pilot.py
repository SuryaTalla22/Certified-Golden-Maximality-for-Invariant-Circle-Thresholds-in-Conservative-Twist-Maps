from kam_theorem_suite.audit.lower_anchor_phase2z_tail_response_pilot import build_phase2z_plan, select_phase2z_tail_response_indices


def test_phase2z_selects_q_safe_tail_rows():
    phase2y = {
        "required_improvement_rows": [
            {"index": 1, "bucket": "q_over_one", "finite_contraction_q": 1.01, "deficit": 1e-8, "tail_response_factor_needed": 0.9, "guard_factor_needed": 0.9},
            {"index": 2, "bucket": "q_boundary", "finite_contraction_q": 0.995, "deficit": 2e-8, "tail_response_factor_needed": 0.91, "guard_factor_needed": 0.95, "recommended_upgrade": "modewise_tail_response_sharpening"},
            {"index": 3, "bucket": "tail_or_guard_dominated", "finite_contraction_q": 0.97, "deficit": 3e-8, "tail_response_factor_needed": 0.95, "guard_factor_needed": 0.85},
            {"index": 4, "bucket": "safe_q_small_gap", "finite_contraction_q": 0.88, "deficit": 4e-8, "tail_response_factor_needed": 0.99, "guard_factor_needed": 0.99},
        ]
    }
    rows = select_phase2z_tail_response_indices(phase2y, max_indices=10)
    assert [r.index for r in rows] == [2, 3]
    assert rows[0].reason == "tail_response_first"
    assert rows[1].reason == "guard_first"


def test_phase2z_plan_contains_indices_and_fail_closed_command(tmp_path):
    p = tmp_path / "phase2y.json"
    p.write_text('{"required_improvement_rows":[{"index":5,"bucket":"safe_q_small_gap","finite_contraction_q":0.88,"deficit":1e-8,"tail_response_factor_needed":0.9,"guard_factor_needed":0.9}]}')
    plan = build_phase2z_plan(phase2y_path=p, summary_path="summary.json", seed_json="seed.json", label="demo", max_indices=10, workers=64)
    assert plan["selected_count"] == 1
    assert plan["indices_csv"] == "5"
    assert "--indices" in plan["command"]
    assert "--n-values" in plan["command"]
    assert "1024" in plan["command"]
    assert plan["theorem_facing"] is False
    assert plan["promotion_allowed"] is False
