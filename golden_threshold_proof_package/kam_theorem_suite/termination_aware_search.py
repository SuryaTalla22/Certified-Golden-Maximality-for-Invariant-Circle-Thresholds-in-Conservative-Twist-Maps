from __future__ import annotations

"""Termination-aware challenger exhaustion search.

This module strengthens the evidence-weighted search loop by adding an explicit
*search-lifecycle* layer.  The goal is not to declare difficult challengers
mathematically eliminated when they are not.  Instead, it adds a principled way
for the search policy to stop spending escalation budget on classes that look
unproductive under the current local certification machinery.

The key distinction is between proof status and search status:

- ``pruning_status`` remains the theorem-facing quantity coming from the current
  class-level evidence (dominated / overlapping / arithmetic-weaker-only /
  undecided);
- ``lifecycle_status`` records how the search policy is treating that class
  right now (active / deferred / retired).

A class may therefore be deferred for search reasons even if it is not yet
mathematically dominated.  This lets the budget concentrate on the few classes
that are both threatening *and* responsive to escalation.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .class_campaigns import ArithmeticClassSpec
from .evidence_weighted_search import (
    EvidenceWeightedClassState,
    _build_initial_state,
    _build_record_for_state,
    _evidence_priority_score,
    _escalate_state_evidence_weighted,
    _priority_reason,
    _summarize_report as _unused_summarize,  # imported for consistency only
    _update_state_from_record,
)
from .standard_map import HarmonicFamily


@dataclass
class SearchLifecycleState:
    class_label: str
    lifecycle_status: str = "active"
    termination_status: str = "active"
    termination_reason: str = "initial-active"
    termination_round: int | None = None
    last_evaluated_round: int = 0
    last_probe_round: int = 0
    active_rounds: int = 0
    deferred_rounds: int = 0
    retired_rounds: int = 0
    reactivations: int = 0
    consecutive_deferred_rounds: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TerminationAwareRound:
    round_index: int
    evaluated_classes: list[str]
    active_classes: list[str]
    deferred_classes: list[str]
    retired_classes: list[str]
    probed_deferred_classes: list[str]
    top_priority_classes: list[str]
    escalated_classes: list[str]
    newly_deferred_classes: list[str]
    newly_retired_classes: list[str]
    reactivated_classes: list[str]
    records: list[dict[str, Any]]
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TerminationAwareSearchReport:
    reference_label: str
    reference_lower_bound: float
    reference_crossing_center: float
    family_label: str
    rounds: list[dict[str, Any]]
    final_records: list[dict[str, Any]]
    active_count: int
    deferred_count: int
    retired_count: int
    dominated_count: int
    overlapping_count: int
    arithmetic_only_count: int
    undecided_count: int
    strongest_active_class: str | None
    strongest_active_upper_bound: float | None
    strongest_active_source: str | None
    total_escalations: int
    total_deferrals: int
    total_reactivations: int
    deferred_retired_domination_certificate: dict[str, Any]
    termination_exclusion_promotion_certificate: dict[str, Any]
    terminated_early: bool
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _float_or_none(x: Any) -> float | None:
    return None if x is None else float(x)


def _initial_lifecycle_state(spec: ArithmeticClassSpec) -> SearchLifecycleState:
    return SearchLifecycleState(class_label=spec.normalized_label())


def _probe_due(life: SearchLifecycleState, *, current_round: int, deferred_probe_every: int) -> bool:
    if life.lifecycle_status != "deferred":
        return False
    return (current_round - life.last_probe_round) >= deferred_probe_every


def _reactivation_candidate(record: dict[str, Any], state: EvidenceWeightedClassState) -> bool:
    status = str(record.get("pruning_status", "undecided"))
    source = str(record.get("selected_upper_source", "no-upper-object"))
    margin = _float_or_none(record.get("selected_upper_margin_to_reference"))
    productive = (state.improvement_rounds + state.source_upgrade_rounds) > 0 and state.stagnation_rounds == 0
    threatening = status in {"overlapping", "undecided"}
    upper_present = record.get("selected_upper_hi") is not None
    upper_strong = source in {"asymptotic-upper-ladder", "refined-upper-ladder"}
    close_upper = margin is not None and margin < 5e-4
    return threatening and (productive or (upper_present and (upper_strong or close_upper)))


def _apply_round_accounting(life: SearchLifecycleState) -> SearchLifecycleState:
    if life.lifecycle_status == "active":
        life.active_rounds += 1
        life.consecutive_deferred_rounds = 0
    elif life.lifecycle_status == "deferred":
        life.deferred_rounds += 1
        life.consecutive_deferred_rounds += 1
    else:
        life.retired_rounds += 1
        life.consecutive_deferred_rounds = 0
    return life


def _decide_lifecycle(
    life: SearchLifecycleState,
    state: EvidenceWeightedClassState,
    record: dict[str, Any],
    *,
    round_index: int,
    retire_dominated: bool,
    arithmetic_deferral_rounds: int,
    arithmetic_wasted_escalations: int,
    no_upper_deferral_rounds: int,
    stagnation_deferral_rounds: int,
    stagnation_wasted_escalations: int,
) -> tuple[SearchLifecycleState, str | None]:
    """Decide the search lifecycle after evaluating a class.

    Returns ``(updated_life, transition_tag)`` where ``transition_tag`` is one
    of ``None``, ``deferred``, ``retired``, or ``reactivated``.
    """
    prev_status = life.lifecycle_status
    status = str(record.get("pruning_status", "undecided"))
    has_upper = record.get("selected_upper_hi") is not None

    transition: str | None = None

    # Dominated classes can be retired immediately because the current evidence
    # already proves the search need not continue for them.
    if retire_dominated and status == "dominated":
        if life.lifecycle_status != "retired":
            transition = "retired"
        life.lifecycle_status = "retired"
        life.termination_status = "retired-dominated"
        life.termination_reason = "dominated-by-current-upper-evidence"
        life.termination_round = round_index
        return _apply_round_accounting(life), transition

    # Deferred classes can return to active search if a probe finds them both
    # threatening and newly responsive under the current evidence.
    if prev_status == "deferred" and _reactivation_candidate(record, state):
        life.lifecycle_status = "active"
        life.termination_status = "reactivated"
        life.termination_reason = "probe-found-productive-threat"
        life.termination_round = round_index
        life.reactivations += 1
        life.last_probe_round = round_index
        transition = "reactivated"
        return _apply_round_accounting(life), transition

    # Search-only deferral logic for classes that are not mathematically gone
    # but are currently poor uses of additional budget.
    if (
        status == "arithmetic-weaker-only"
        and not has_upper
        and state.no_upper_rounds >= arithmetic_deferral_rounds
        and state.wasted_escalations() >= arithmetic_wasted_escalations
    ):
        if prev_status != "deferred":
            transition = "deferred"
        life.lifecycle_status = "deferred"
        life.termination_status = "deferred-arithmetic-passive"
        life.termination_reason = (
            "arithmetic-only-for-several-rounds with no upper object and repeated wasted escalation"
        )
        life.termination_round = round_index
        life.last_probe_round = round_index
        return _apply_round_accounting(life), transition

    if (
        not has_upper
        and state.upper_object_rounds == 0
        and state.no_upper_rounds >= no_upper_deferral_rounds
        and state.consecutive_survival_rounds >= no_upper_deferral_rounds
    ):
        if prev_status != "deferred":
            transition = "deferred"
        life.lifecycle_status = "deferred"
        life.termination_status = "deferred-no-upper-persistent"
        life.termination_reason = "persistent survivor without any upper object"
        life.termination_round = round_index
        life.last_probe_round = round_index
        return _apply_round_accounting(life), transition

    if (
        status in {"overlapping", "undecided"}
        and state.stagnation_rounds >= stagnation_deferral_rounds
        and state.wasted_escalations() >= stagnation_wasted_escalations
    ):
        if prev_status != "deferred":
            transition = "deferred"
        life.lifecycle_status = "deferred"
        life.termination_status = f"deferred-stagnating-{status}"
        life.termination_reason = "threat persists but escalation is no longer sharpening the upper object"
        life.termination_round = round_index
        life.last_probe_round = round_index
        return _apply_round_accounting(life), transition

    # Default: remain or become active.
    if prev_status != "active":
        transition = "reactivated"
        life.reactivations += 1
    life.lifecycle_status = "active"
    life.termination_status = "active"
    life.termination_reason = "currently in active search pool"
    life.termination_round = round_index
    return _apply_round_accounting(life), transition


def _attach_lifecycle(
    record: dict[str, Any],
    state: EvidenceWeightedClassState,
    life: SearchLifecycleState,
) -> dict[str, Any]:
    out = dict(record)
    out["evidence_state"] = state.to_dict()
    out["lifecycle_state"] = life.to_dict()
    out["lifecycle_status"] = life.lifecycle_status
    out["termination_status"] = life.termination_status
    out["termination_reason"] = life.termination_reason
    out["termination_round"] = life.termination_round
    out["reactivations"] = life.reactivations
    domination_provenance = out.get("global_domination_provenance")
    if domination_provenance is None and out.get("pruning_status") == "dominated":
        domination_provenance = "dominated-by-current-upper-evidence"
    out["global_domination_provenance"] = domination_provenance
    exclusion_provenance = out.get("termination_exclusion_provenance")
    if exclusion_provenance is None and life.lifecycle_status == "retired" and domination_provenance is not None:
        exclusion_provenance = str(domination_provenance)
    out["termination_exclusion_provenance"] = exclusion_provenance
    return out


def _sort_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lifecycle_rank = {"active": 0, "deferred": 1, "retired": 2}
    return sorted(
        records,
        key=lambda r: (
            lifecycle_rank.get(str(r.get("lifecycle_status", "active")), 9),
            -float(r.get("priority_score", -1e9)),
            str(r.get("class_label")),
        ),
    )


def _build_deferred_retired_domination_certificate(records: list[dict[str, Any]]) -> dict[str, Any]:
    deferred = [r for r in records if r.get("lifecycle_status") == "deferred"]
    retired = [r for r in records if r.get("lifecycle_status") == "retired"]
    deferred_labels = [str(r.get("class_label", "unknown")) for r in deferred]
    retired_labels = [str(r.get("class_label", "unknown")) for r in retired]
    unresolved_labels = [
        str(r.get("class_label", "unknown"))
        for r in deferred + retired
        if not r.get("global_domination_provenance")
    ]
    proves = len(unresolved_labels) == 0
    if proves and (deferred_labels or retired_labels):
        status = "deferred-retired-domination-certified"
    elif proves:
        status = "no-deferred-or-retired-classes"
    else:
        status = "deferred-retired-domination-frontier"
    return {
        "status": status,
        "deferred_labels": deferred_labels,
        "retired_labels": retired_labels,
        "unresolved_labels": unresolved_labels,
        "proves_deferred_or_retired_classes_are_globally_dominated": proves,
        "notes": (
            "Deferred or retired classes only clear the theorem-side global-domination burden when each such class carries explicit global-domination provenance. "
            "Search lifecycle status alone never counts as theorem-grade domination."
        ),
    }


def _build_termination_exclusion_promotion_certificate(
    records: list[dict[str, Any]],
    *,
    deferred_retired_domination_certificate: dict[str, Any],
) -> dict[str, Any]:
    candidate_labels = [
        str(r.get("class_label", "unknown"))
        for r in records
        if r.get("lifecycle_status") in {"deferred", "retired"}
    ]
    promoted_labels = [
        str(r.get("class_label", "unknown"))
        for r in records
        if r.get("lifecycle_status") in {"deferred", "retired"} and r.get("termination_exclusion_provenance")
    ]
    unresolved_labels = [label for label in candidate_labels if label not in promoted_labels]
    proves = bool(deferred_retired_domination_certificate.get("proves_deferred_or_retired_classes_are_globally_dominated", False)) and len(unresolved_labels) == 0
    if proves and candidate_labels:
        status = "termination-exclusion-promotion-certified"
    elif proves:
        status = "termination-exclusion-vacuous"
    else:
        status = "termination-exclusion-promotion-frontier"
    return {
        "status": status,
        "candidate_labels": candidate_labels,
        "promoted_labels": promoted_labels,
        "unresolved_labels": unresolved_labels,
        "proves_termination_search_promotes_to_theorem_exclusion": proves,
        "notes": (
            "Termination-aware search only promotes to theorem exclusion when every deferred/retired class has explicit exclusion provenance in addition to lifecycle status."
        ),
    }


def _summarize_termination_report(
    records: list[dict[str, Any]],
    *,
    reference_lower_bound: float,
    reference_label: str,
    reference_crossing_center: float,
    family: HarmonicFamily,
    rounds: list[dict[str, Any]],
    total_escalations: int,
    total_deferrals: int,
    total_reactivations: int,
    terminated_early: bool,
) -> TerminationAwareSearchReport:
    ordered = _sort_records(records)
    active = [r for r in ordered if r.get("lifecycle_status") == "active"]
    deferred = [r for r in ordered if r.get("lifecycle_status") == "deferred"]
    retired = [r for r in ordered if r.get("lifecycle_status") == "retired"]

    dominated = sum(1 for r in ordered if r.get("pruning_status") == "dominated")
    overlapping = sum(1 for r in ordered if r.get("pruning_status") == "overlapping")
    arithmetic_only = sum(1 for r in ordered if r.get("pruning_status") == "arithmetic-weaker-only")
    undecided = sum(1 for r in ordered if r.get("pruning_status") == "undecided")

    active_with_upper = [r for r in active if r.get("selected_upper_hi") is not None]
    strongest_active_class = None
    strongest_active_upper_bound = None
    strongest_active_source = None
    if active_with_upper:
        best = min(active_with_upper, key=lambda r: float(r["selected_upper_hi"]))
        strongest_active_class = str(best["class_label"])
        strongest_active_upper_bound = float(best["selected_upper_hi"])
        strongest_active_source = str(best.get("selected_upper_source"))

    if active and any(r.get("pruning_status") == "overlapping" for r in active):
        status = "termination-aware-search-has-active-overlaps"
    elif active and any(r.get("pruning_status") == "undecided" for r in active):
        status = "termination-aware-search-has-active-undecided"
    elif not active and deferred:
        status = "termination-aware-search-ended-with-deferred-survivors"
    elif ordered and dominated == len(ordered):
        status = "all-screened-classes-dominated"
    else:
        status = "termination-aware-search-partial-exhaustion"

    deferred_retired_domination_certificate = _build_deferred_retired_domination_certificate(ordered)
    termination_exclusion_promotion_certificate = _build_termination_exclusion_promotion_certificate(
        ordered,
        deferred_retired_domination_certificate=deferred_retired_domination_certificate,
    )
    notes = (
        "This search loop separates theorem-facing pruning status from search-facing lifecycle status. "
        "Classes may be deferred when they remain threatening but have become unproductive under the current "
        "local certification machinery. Deferred classes are not treated as dominated; they are simply removed "
        "from the active escalation budget until a probe justifies reactivation. The attached certificates make explicit whether any deferred/retired outcomes have actually been promoted to theorem-grade domination or exclusion."
    )
    return TerminationAwareSearchReport(
        reference_label=str(reference_label),
        reference_lower_bound=float(reference_lower_bound),
        reference_crossing_center=float(reference_crossing_center),
        family_label=type(family).__name__,
        rounds=rounds,
        final_records=ordered,
        active_count=len(active),
        deferred_count=len(deferred),
        retired_count=len(retired),
        dominated_count=int(dominated),
        overlapping_count=int(overlapping),
        arithmetic_only_count=int(arithmetic_only),
        undecided_count=int(undecided),
        strongest_active_class=strongest_active_class,
        strongest_active_upper_bound=strongest_active_upper_bound,
        strongest_active_source=strongest_active_source,
        total_escalations=int(total_escalations),
        total_deferrals=int(total_deferrals),
        total_reactivations=int(total_reactivations),
        deferred_retired_domination_certificate=deferred_retired_domination_certificate,
        termination_exclusion_promotion_certificate=termination_exclusion_promotion_certificate,
        terminated_early=bool(terminated_early),
        status=status,
        notes=notes,
    )


def build_termination_aware_class_exhaustion_search(
    specs: Sequence[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    reference_label: str = "golden",
    family: HarmonicFamily | None = None,
    rounds: int = 4,
    per_round_budget: int = 2,
    deferred_probe_budget: int = 1,
    deferred_probe_every: int = 2,
    initial_max_q: int = 89,
    max_q_step: int = 55,
    initial_n_terms: int = 96,
    n_terms_step: int = 24,
    q_min: int = 8,
    initial_keep_last: int | None = 4,
    keep_last_step: int = 1,
    initial_crossing_half_width: float = 2.5e-3,
    width_growth: float = 1.30,
    width_cap: float = 1.2e-2,
    productive_q_multiplier: float = 1.6,
    sparse_width_multiplier: float = 1.25,
    stagnation_width_multiplier: float = 1.10,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refinement_base_tol: float = 2.5e-4,
    refinement_q2_scale: float = 0.1,
    refinement_min_subset: int = 2,
    asymptotic_min_members: int = 2,
    asymptotic_member_cap: int = 5,
    asymptotic_center_drift_tol: float = 5e-4,
    upper_improvement_tol: float = 2.5e-5,
    width_improvement_tol: float = 2.5e-5,
    retire_dominated: bool = True,
    arithmetic_deferral_rounds: int = 2,
    arithmetic_wasted_escalations: int = 1,
    no_upper_deferral_rounds: int = 3,
    stagnation_deferral_rounds: int = 2,
    stagnation_wasted_escalations: int = 2,
) -> TerminationAwareSearchReport:
    family = family or HarmonicFamily()
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    if per_round_budget <= 0:
        raise ValueError("per_round_budget must be positive")
    if deferred_probe_budget < 0:
        raise ValueError("deferred_probe_budget must be nonnegative")
    if deferred_probe_every <= 0:
        raise ValueError("deferred_probe_every must be positive")

    spec_map = {spec.normalized_label(): spec for spec in specs}
    state_map = {
        spec.normalized_label(): _build_initial_state(
            spec,
            max_q=initial_max_q,
            n_terms=initial_n_terms,
            q_min=q_min,
            keep_last=initial_keep_last,
            crossing_half_width=initial_crossing_half_width,
            band_offset_lo=band_offset_lo,
            band_offset_hi=band_offset_hi,
            refinement_base_tol=refinement_base_tol,
            refinement_q2_scale=refinement_q2_scale,
            refinement_min_subset=refinement_min_subset,
            asymptotic_min_members=asymptotic_min_members,
            asymptotic_center_drift_tol=asymptotic_center_drift_tol,
        )
        for spec in specs
    }
    life_map = {spec.normalized_label(): _initial_lifecycle_state(spec) for spec in specs}
    cached_records: dict[str, dict[str, Any]] = {}

    rounds_out: list[dict[str, Any]] = []
    total_escalations = 0
    total_deferrals = 0
    total_reactivations = 0
    terminated_early = False
    final_records: list[dict[str, Any]] = []

    for ridx in range(1, rounds + 1):
        active_labels = [lbl for lbl, lf in life_map.items() if lf.lifecycle_status == "active"]
        deferred_labels = [lbl for lbl, lf in life_map.items() if lf.lifecycle_status == "deferred"]
        retired_labels = [lbl for lbl, lf in life_map.items() if lf.lifecycle_status == "retired"]

        # Probe the strongest deferred classes using their last known priority.
        deferred_candidates = []
        for lbl in deferred_labels:
            if not _probe_due(life_map[lbl], current_round=ridx, deferred_probe_every=deferred_probe_every):
                continue
            cached = cached_records.get(lbl, {})
            score = float(cached.get("priority_score", -1e9))
            deferred_candidates.append((score, lbl))
        deferred_candidates.sort(reverse=True)
        probed_labels = [lbl for _, lbl in deferred_candidates[:deferred_probe_budget]]

        evaluated_labels = list(dict.fromkeys(active_labels + probed_labels))
        records_this_round: dict[str, dict[str, Any]] = {}
        newly_deferred: list[str] = []
        newly_retired: list[str] = []
        reactivated: list[str] = []

        for lbl in evaluated_labels:
            spec = spec_map[lbl]
            rec = _build_record_for_state(
                spec,
                state_map[lbl],
                reference_crossing_center=reference_crossing_center,
                reference_lower_bound=reference_lower_bound,
                family=family,
                target_residue=target_residue,
                auto_localize_crossing=auto_localize_crossing,
                initial_subdivisions=initial_subdivisions,
                max_depth=max_depth,
                min_width=min_width,
            )
            state_map[lbl] = _update_state_from_record(
                state_map[lbl],
                rec,
                upper_improvement_tol=upper_improvement_tol,
                width_improvement_tol=width_improvement_tol,
            )
            rec["priority_score"] = _evidence_priority_score(rec, state_map[lbl])
            rec["priority_reason"] = _priority_reason(rec, state_map[lbl])
            life_map[lbl].last_evaluated_round = ridx
            if lbl in probed_labels:
                life_map[lbl].last_probe_round = ridx
            life_map[lbl], transition = _decide_lifecycle(
                life_map[lbl],
                state_map[lbl],
                rec,
                round_index=ridx,
                retire_dominated=retire_dominated,
                arithmetic_deferral_rounds=arithmetic_deferral_rounds,
                arithmetic_wasted_escalations=arithmetic_wasted_escalations,
                no_upper_deferral_rounds=no_upper_deferral_rounds,
                stagnation_deferral_rounds=stagnation_deferral_rounds,
                stagnation_wasted_escalations=stagnation_wasted_escalations,
            )
            if transition == "deferred":
                newly_deferred.append(lbl)
                total_deferrals += 1
            elif transition == "retired":
                newly_retired.append(lbl)
            elif transition == "reactivated":
                reactivated.append(lbl)
                total_reactivations += 1
            rec = _attach_lifecycle(rec, state_map[lbl], life_map[lbl])
            cached_records[lbl] = rec
            records_this_round[lbl] = rec

        # Carry forward cached records for unevaluated classes.
        for lbl in spec_map:
            if lbl in records_this_round:
                continue
            if lbl in cached_records:
                rec = dict(cached_records[lbl])
            else:
                # Should only happen if a class was never evaluated, which in
                # practice occurs only for empty round counts; keep a minimal stub.
                rec = {
                    "class_label": lbl,
                    "pruning_status": "undecided",
                    "selected_upper_hi": None,
                    "selected_upper_source": "no-upper-object",
                    "priority_score": -1e6,
                    "priority_reason": "unevaluated",
                }
            rec = _attach_lifecycle(rec, state_map[lbl], life_map[lbl])
            records_this_round[lbl] = rec

        ordered = _sort_records(list(records_this_round.values()))
        final_records = ordered
        active_records = [r for r in ordered if r.get("lifecycle_status") == "active"]
        survivors = [
            r for r in active_records
            if str(r.get("pruning_status")) in {"overlapping", "undecided", "arithmetic-weaker-only"}
        ]
        priority = survivors[:per_round_budget]
        priority_labels = [str(r["class_label"]) for r in priority]

        escalated_labels: list[str] = []
        if ridx < rounds:
            for rec in priority:
                lbl = str(rec["class_label"])
                state_map[lbl] = _escalate_state_evidence_weighted(
                    state_map[lbl],
                    rec,
                    max_q_step=max_q_step,
                    keep_last_step=keep_last_step,
                    n_terms_step=n_terms_step,
                    width_growth=width_growth,
                    width_cap=width_cap,
                    asymptotic_member_cap=asymptotic_member_cap,
                    productive_q_multiplier=productive_q_multiplier,
                    sparse_width_multiplier=sparse_width_multiplier,
                    stagnation_width_multiplier=stagnation_width_multiplier,
                )
                escalated_labels.append(lbl)
                total_escalations += 1

        if not survivors and not probed_labels and all(life_map[lbl].lifecycle_status != "active" for lbl in spec_map):
            round_status = "no-active-survivors"
            round_notes = (
                "All remaining non-dominated classes are deferred under the current search lifecycle. "
                "No active class justified further escalation this round."
            )
        elif not survivors:
            round_status = "active-pool-cleared"
            round_notes = (
                "No active class required escalation this round. Deferred probes may still reactivate classes later."
            )
        else:
            round_status = "termination-aware-search-continues"
            round_notes = (
                "Escalation was restricted to the active threat pool. Deferred classes were either skipped or probed "
                "lightly according to the probe schedule."
            )

        rounds_out.append(TerminationAwareRound(
            round_index=ridx,
            evaluated_classes=evaluated_labels,
            active_classes=[lbl for lbl, lf in life_map.items() if lf.lifecycle_status == "active"],
            deferred_classes=[lbl for lbl, lf in life_map.items() if lf.lifecycle_status == "deferred"],
            retired_classes=[lbl for lbl, lf in life_map.items() if lf.lifecycle_status == "retired"],
            probed_deferred_classes=probed_labels,
            top_priority_classes=priority_labels,
            escalated_classes=escalated_labels,
            newly_deferred_classes=newly_deferred,
            newly_retired_classes=newly_retired,
            reactivated_classes=reactivated,
            records=ordered,
            status=round_status,
            notes=round_notes,
        ).to_dict())

        no_active = not any(lf.lifecycle_status == "active" for lf in life_map.values())
        if no_active and not any(_probe_due(lf, current_round=ridx + 1, deferred_probe_every=deferred_probe_every) for lf in life_map.values()):
            terminated_early = True
            break

    return _summarize_termination_report(
        final_records,
        reference_lower_bound=reference_lower_bound,
        reference_label=reference_label,
        reference_crossing_center=reference_crossing_center,
        family=family,
        rounds=rounds_out,
        total_escalations=total_escalations,
        total_deferrals=total_deferrals,
        total_reactivations=total_reactivations,
        terminated_early=terminated_early,
    )


__all__ = [
    "SearchLifecycleState",
    "TerminationAwareRound",
    "TerminationAwareSearchReport",
    "build_termination_aware_class_exhaustion_search",
]
