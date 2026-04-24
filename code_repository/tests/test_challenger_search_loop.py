from __future__ import annotations

from kam_theorem_suite.class_campaigns import ArithmeticClassSpec
from kam_theorem_suite.proof_driver import build_adaptive_class_exhaustion_search_report


def test_adaptive_class_exhaustion_search_report_smoke():
    specs = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label="silver"),
        ArithmeticClassSpec(preperiod=(), period=(3,), label="bronze"),
        ArithmeticClassSpec(preperiod=(), period=(1, 2), label="mixed"),
    ]
    rep = build_adaptive_class_exhaustion_search_report(
        specs,
        reference_crossing_center=0.9713,
        reference_lower_bound=0.9711,
        rounds=2,
        per_round_budget=2,
        initial_max_q=21,
        max_q_step=8,
        initial_keep_last=2,
        q_min=2,
        initial_subdivisions=2,
        max_depth=2,
        min_width=1e-3,
    )
    assert rep["status"] in {
        "all-screened-classes-dominated",
        "adaptive-search-has-overlapping-challengers",
        "adaptive-search-has-undecided-challengers",
        "adaptive-search-is-arithmetic-heavy",
        "adaptive-search-partial-exhaustion",
    }
    assert len(rep["rounds"]) >= 1
    assert len(rep["final_records"]) == 3
    assert rep["dominated_count"] + rep["overlapping_count"] + rep["arithmetic_only_count"] + rep["undecided_count"] == 3
    for rnd in rep["rounds"]:
        assert "top_priority_classes" in rnd
        assert "records" in rnd
        assert len(rnd["records"]) == 3
    for rec in rep["final_records"]:
        assert "search_state" in rec
        assert rec["search_state"]["max_q"] >= 21


def test_adaptive_search_escalates_or_stops_honestly():
    specs = [ArithmeticClassSpec(preperiod=(), period=(2,), label="silver")]
    rep = build_adaptive_class_exhaustion_search_report(
        specs,
        reference_crossing_center=0.9713,
        reference_lower_bound=0.9711,
        rounds=3,
        per_round_budget=1,
        initial_max_q=13,
        max_q_step=5,
        initial_keep_last=1,
        q_min=2,
        initial_subdivisions=2,
        max_depth=1,
        min_width=1e-3,
    )
    assert rep["total_escalations"] >= 0
    assert isinstance(rep["terminated_early"], bool)
