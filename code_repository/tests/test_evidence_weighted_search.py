from __future__ import annotations

from kam_theorem_suite.class_campaigns import ArithmeticClassSpec
from kam_theorem_suite.evidence_weighted_search import build_evidence_weighted_class_exhaustion_search
from kam_theorem_suite.proof_driver import build_evidence_weighted_class_exhaustion_search_report


def test_evidence_weighted_search_report_smoke() -> None:
    specs = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
        ArithmeticClassSpec(preperiod=(), period=(3,), label='bronze'),
        ArithmeticClassSpec(preperiod=(), period=(1, 2), label='mixed'),
    ]
    rep = build_evidence_weighted_class_exhaustion_search_report(
        specs,
        reference_crossing_center=0.97135,
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
    assert rep['status'] in {
        'all-screened-classes-dominated',
        'evidence-weighted-search-has-overlapping-challengers',
        'evidence-weighted-search-has-undecided-challengers',
        'evidence-weighted-search-is-arithmetic-heavy',
        'evidence-weighted-search-partial-exhaustion',
    }
    assert len(rep['rounds']) >= 1
    assert len(rep['final_records']) == 3
    for rnd in rep['rounds']:
        assert 'top_priority_classes' in rnd
        assert 'records' in rnd
    for rec in rep['final_records']:
        assert 'evidence_state' in rec
        assert 'priority_score' in rec
        assert 'priority_reason' in rec


def test_evidence_weighted_search_tracks_history() -> None:
    specs = [ArithmeticClassSpec(preperiod=(), period=(2,), label='silver')]
    rep = build_evidence_weighted_class_exhaustion_search(
        specs,
        reference_crossing_center=0.97135,
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
    ).to_dict()
    rec = rep['final_records'][0]
    state = rec['evidence_state']
    assert state['rounds_run'] >= 1
    assert state['wasted_escalations'] >= 0
    assert isinstance(rec['priority_score'], float)
    assert isinstance(rec['priority_reason'], str) and rec['priority_reason']
