from __future__ import annotations

from kam_theorem_suite import (
    ArithmeticClassSpec,
    build_termination_aware_class_exhaustion_search_report,
)


def _demo_report() -> dict:
    specs = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label="silver"),
        ArithmeticClassSpec(preperiod=(), period=(3,), label="bronze"),
        ArithmeticClassSpec(preperiod=(), period=(1, 2), label="mixed"),
    ]
    return build_termination_aware_class_exhaustion_search_report(
        specs,
        reference_crossing_center=0.97135,
        reference_lower_bound=0.9711,
        rounds=3,
        per_round_budget=2,
        deferred_probe_budget=1,
        deferred_probe_every=2,
        initial_max_q=21,
        max_q_step=8,
        initial_keep_last=2,
        q_min=2,
        initial_subdivisions=2,
        max_depth=1,
        min_width=1e-3,
    )


def test_termination_aware_search_report_smoke() -> None:
    report = _demo_report()
    assert report["status"] in {
        "termination-aware-search-has-active-overlaps",
        "termination-aware-search-has-active-undecided",
        "termination-aware-search-ended-with-deferred-survivors",
        "termination-aware-search-partial-exhaustion",
        "all-screened-classes-dominated",
    }
    assert report["active_count"] + report["deferred_count"] + report["retired_count"] == len(report["final_records"])
    assert len(report["rounds"]) >= 1


def test_termination_aware_search_defers_or_retires_some_unproductive_class() -> None:
    report = _demo_report()
    records = {r["class_label"]: r for r in report["final_records"]}
    # In the small demo regime at least one non-golden challenger should be removed
    # from the active escalation pool by the lifecycle logic.
    inactive = [
        lbl for lbl, rec in records.items()
        if rec["lifecycle_status"] in {"deferred", "retired"}
    ]
    assert inactive
    # Bronze is the archetypal arithmetic-only/no-upper class in the current demo.
    assert records["bronze"]["lifecycle_status"] in {"active", "deferred", "retired"}
    assert records["bronze"]["termination_status"] != "initial-active"

from kam_theorem_suite.termination_aware_search import (
    _build_deferred_retired_domination_certificate,
    _build_termination_exclusion_promotion_certificate,
)


def test_deferred_or_retired_classes_do_not_count_as_globally_dominated_without_provenance() -> None:
    records = [
        {'class_label': 'silver', 'lifecycle_status': 'deferred', 'pruning_status': 'overlapping'},
        {'class_label': 'bronze', 'lifecycle_status': 'retired', 'pruning_status': 'dominated', 'global_domination_provenance': 'dominated-by-current-upper-evidence'},
    ]
    dom = _build_deferred_retired_domination_certificate(records)
    term = _build_termination_exclusion_promotion_certificate(
        records,
        deferred_retired_domination_certificate=dom,
    )
    assert dom['proves_deferred_or_retired_classes_are_globally_dominated'] is False
    assert 'silver' in dom['unresolved_labels']
    assert term['proves_termination_search_promotes_to_theorem_exclusion'] is False
