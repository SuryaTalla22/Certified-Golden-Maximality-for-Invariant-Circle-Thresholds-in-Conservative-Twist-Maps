from __future__ import annotations

"""Evidence-weighted challenger-exhaustion search.

This module upgrades the earlier adaptive search loop by letting the search
policy learn from *what happened in prior rounds*.

The key idea is modest but useful: challenger classes should not receive the
same budget merely because they are all currently non-dominated.  Some classes
repeatedly remain overlapping and also improve when additional effort is spent;
others consume escalation budget without producing a sharper upper-side object.
This module records that evidence and uses it to rank and escalate challengers
more intelligently.

The resulting workflow is still not the final exhaustion theorem.  It is a more
search-efficient and more theorem-facing policy for deciding where the next
certification effort should go.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .class_campaigns import ArithmeticClassSpec
from .class_exhaustion_screen import build_class_exhaustion_record
from .standard_map import HarmonicFamily


_SOURCE_RANK = {
    "asymptotic-upper-ladder": 0,
    "refined-upper-ladder": 1,
    "raw-upper-ladder": 2,
    "no-upper-object": 3,
}

_STATUS_WEIGHT = {
    "overlapping": 100.0,
    "undecided": 78.0,
    "arithmetic-weaker-only": 28.0,
    "dominated": -1.0e6,
}


@dataclass
class EvidenceWeightedClassState:
    class_label: str
    max_q: int
    n_terms: int
    q_min: int
    keep_last: int | None
    crossing_half_width: float
    band_offset_lo: float
    band_offset_hi: float
    refinement_base_tol: float
    refinement_q2_scale: float
    refinement_min_subset: int
    asymptotic_min_members: int
    asymptotic_center_drift_tol: float
    rounds_run: int = 0
    escalations: int = 0
    survival_rounds: int = 0
    overlap_rounds: int = 0
    undecided_rounds: int = 0
    arithmetic_only_rounds: int = 0
    dominated_rounds: int = 0
    no_upper_rounds: int = 0
    upper_object_rounds: int = 0
    improvement_rounds: int = 0
    source_upgrade_rounds: int = 0
    stagnation_rounds: int = 0
    consecutive_survival_rounds: int = 0
    last_selected_upper_hi: float | None = None
    last_selected_upper_width: float | None = None
    last_selected_upper_source: str | None = None
    last_margin_to_reference: float | None = None
    best_selected_upper_hi: float | None = None
    best_selected_upper_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["wasted_escalations"] = self.wasted_escalations()
        return d

    def wasted_escalations(self) -> int:
        productive = self.improvement_rounds + self.source_upgrade_rounds
        return max(0, self.escalations - productive)


@dataclass
class EvidenceWeightedRound:
    round_index: int
    active_classes: list[str]
    top_priority_classes: list[str]
    escalated_classes: list[str]
    records: list[dict[str, Any]]
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceWeightedSearchReport:
    reference_label: str
    reference_lower_bound: float
    reference_crossing_center: float
    family_label: str
    rounds: list[dict[str, Any]]
    final_records: list[dict[str, Any]]
    dominated_count: int
    overlapping_count: int
    arithmetic_only_count: int
    undecided_count: int
    strongest_remaining_class: str | None
    strongest_remaining_upper_bound: float | None
    strongest_remaining_source: str | None
    total_escalations: int
    terminated_early: bool
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _float_or_none(x: Any) -> float | None:
    return None if x is None else float(x)


def _build_initial_state(
    spec: ArithmeticClassSpec,
    *,
    max_q: int,
    n_terms: int,
    q_min: int,
    keep_last: int | None,
    crossing_half_width: float,
    band_offset_lo: float,
    band_offset_hi: float,
    refinement_base_tol: float,
    refinement_q2_scale: float,
    refinement_min_subset: int,
    asymptotic_min_members: int,
    asymptotic_center_drift_tol: float,
) -> EvidenceWeightedClassState:
    return EvidenceWeightedClassState(
        class_label=spec.normalized_label(),
        max_q=int(max_q),
        n_terms=int(n_terms),
        q_min=int(q_min),
        keep_last=None if keep_last is None else int(keep_last),
        crossing_half_width=float(crossing_half_width),
        band_offset_lo=float(band_offset_lo),
        band_offset_hi=float(band_offset_hi),
        refinement_base_tol=float(refinement_base_tol),
        refinement_q2_scale=float(refinement_q2_scale),
        refinement_min_subset=int(refinement_min_subset),
        asymptotic_min_members=int(asymptotic_min_members),
        asymptotic_center_drift_tol=float(asymptotic_center_drift_tol),
    )


def _build_record_for_state(
    spec: ArithmeticClassSpec,
    state: EvidenceWeightedClassState,
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily,
    target_residue: float,
    auto_localize_crossing: bool,
    initial_subdivisions: int,
    max_depth: int,
    min_width: float,
) -> dict[str, Any]:
    rec = build_class_exhaustion_record(
        spec,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        family=family,
        max_q=state.max_q,
        n_terms=state.n_terms,
        q_min=state.q_min,
        keep_last=state.keep_last,
        crossing_half_width=state.crossing_half_width,
        band_offset_lo=state.band_offset_lo,
        band_offset_hi=state.band_offset_hi,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        refinement_base_tol=state.refinement_base_tol,
        refinement_q2_scale=state.refinement_q2_scale,
        refinement_min_subset=state.refinement_min_subset,
        asymptotic_min_members=state.asymptotic_min_members,
        asymptotic_center_drift_tol=state.asymptotic_center_drift_tol,
    ).to_dict()
    rec["search_state"] = state.to_dict()
    return rec


def _update_state_from_record(
    state: EvidenceWeightedClassState,
    record: dict[str, Any],
    *,
    upper_improvement_tol: float,
    width_improvement_tol: float,
) -> EvidenceWeightedClassState:
    status = str(record.get("pruning_status", "undecided"))
    upper_hi = _float_or_none(record.get("selected_upper_hi"))
    upper_width = _float_or_none(record.get("selected_upper_width"))
    source = str(record.get("selected_upper_source", "no-upper-object"))
    margin = _float_or_none(record.get("selected_upper_margin_to_reference"))
    has_upper = upper_hi is not None

    improved_hi = (
        has_upper and state.last_selected_upper_hi is not None
        and upper_hi < state.last_selected_upper_hi - upper_improvement_tol
    )
    improved_width = (
        has_upper and upper_width is not None and state.last_selected_upper_width is not None
        and upper_width < state.last_selected_upper_width - width_improvement_tol
    )
    source_upgrade = (
        state.last_selected_upper_source is not None
        and _SOURCE_RANK.get(source, 9) < _SOURCE_RANK.get(state.last_selected_upper_source, 9)
    )
    any_productive = bool(improved_hi or improved_width or source_upgrade)

    state.rounds_run += 1
    if status == "dominated":
        state.dominated_rounds += 1
        state.consecutive_survival_rounds = 0
    else:
        state.survival_rounds += 1
        state.consecutive_survival_rounds += 1
    if status == "overlapping":
        state.overlap_rounds += 1
    elif status == "undecided":
        state.undecided_rounds += 1
    elif status == "arithmetic-weaker-only":
        state.arithmetic_only_rounds += 1

    if has_upper:
        state.upper_object_rounds += 1
        if state.best_selected_upper_hi is None or upper_hi < state.best_selected_upper_hi:
            state.best_selected_upper_hi = upper_hi
            state.best_selected_upper_source = source
    else:
        state.no_upper_rounds += 1

    if any_productive:
        state.improvement_rounds += int(bool(improved_hi or improved_width))
        state.source_upgrade_rounds += int(bool(source_upgrade))
        state.stagnation_rounds = 0
    elif status != "dominated" and state.rounds_run > 1:
        state.stagnation_rounds += 1

    state.last_selected_upper_hi = upper_hi
    state.last_selected_upper_width = upper_width
    state.last_selected_upper_source = source
    state.last_margin_to_reference = margin
    return state


def _evidence_priority_score(record: dict[str, Any], state: EvidenceWeightedClassState) -> float:
    status = str(record.get("pruning_status", "undecided"))
    score = _STATUS_WEIGHT.get(status, 0.0)
    if score < -1e5:
        return score

    margin = _float_or_none(record.get("selected_upper_margin_to_reference"))
    if margin is None:
        score += 8.0
    elif margin < 0.0:
        score += min(24.0, 14.0 + 4000.0 * min(0.005, -margin))
    else:
        score += max(0.0, 8.0 - 6000.0 * min(0.001, margin))

    score += 6.0 * min(4, state.consecutive_survival_rounds)
    score += 4.0 * min(3, state.overlap_rounds + state.undecided_rounds)
    score += 5.0 * min(4, state.improvement_rounds + state.source_upgrade_rounds)
    score -= 4.0 * min(4, state.stagnation_rounds)
    score -= 3.0 * min(4, state.wasted_escalations())
    if state.no_upper_rounds >= 2 and state.upper_object_rounds == 0:
        score -= 5.0
    return score


def _priority_reason(record: dict[str, Any], state: EvidenceWeightedClassState) -> str:
    status = str(record.get("pruning_status", "undecided"))
    reasons: list[str] = [f"status={status}"]
    margin = _float_or_none(record.get("selected_upper_margin_to_reference"))
    if margin is None:
        reasons.append("no-upper-object")
    elif margin < 0:
        reasons.append("upper-overlaps-reference")
    else:
        reasons.append("upper-below-reference")
    if state.consecutive_survival_rounds >= 2:
        reasons.append("persistent-survivor")
    if state.improvement_rounds + state.source_upgrade_rounds > 0:
        reasons.append("productive-under-escalation")
    if state.stagnation_rounds >= 2:
        reasons.append("stagnating")
    if state.wasted_escalations() >= 2:
        reasons.append("budget-heavy")
    return ", ".join(reasons)


def _escalate_state_evidence_weighted(
    state: EvidenceWeightedClassState,
    record: dict[str, Any],
    *,
    max_q_step: int,
    keep_last_step: int,
    n_terms_step: int,
    width_growth: float,
    width_cap: float,
    asymptotic_member_cap: int,
    productive_q_multiplier: float,
    sparse_width_multiplier: float,
    stagnation_width_multiplier: float,
) -> EvidenceWeightedClassState:
    status = str(record.get("pruning_status", "undecided"))
    has_upper = record.get("selected_upper_hi") is not None

    next_max_q = state.max_q
    next_n_terms = state.n_terms
    next_keep_last = state.keep_last
    next_width = state.crossing_half_width
    next_asym = state.asymptotic_min_members

    productive = (state.improvement_rounds + state.source_upgrade_rounds) > 0 and state.stagnation_rounds == 0
    sparse = (not has_upper) or (state.no_upper_rounds >= 2 and state.upper_object_rounds == 0)
    stagnating = state.stagnation_rounds >= 2 or state.wasted_escalations() >= 2

    if status in {"overlapping", "undecided"}:
        q_step = max_q_step
        n_step = n_terms_step
        keep_step = keep_last_step
        if productive:
            q_step = max(max_q_step + 1, int(round(max_q_step * productive_q_multiplier)))
            n_step = max(n_terms_step + 2, int(round(n_terms_step * productive_q_multiplier)))
            keep_step = keep_last_step + 1
            next_asym = min(asymptotic_member_cap, state.asymptotic_min_members + 1)
        elif stagnating:
            q_step = max(2, max_q_step // 2)
            n_step = max(4, n_terms_step // 2)
            keep_step = keep_last_step
        next_max_q += q_step
        next_n_terms += n_step
        next_keep_last = None if state.keep_last is None else state.keep_last + keep_step

    if sparse:
        next_width = min(width_cap, state.crossing_half_width * width_growth * sparse_width_multiplier)
    elif stagnating and status != "dominated":
        next_width = min(width_cap, state.crossing_half_width * width_growth * stagnation_width_multiplier)
    elif status in {"overlapping", "undecided"}:
        next_width = min(width_cap, state.crossing_half_width * width_growth)

    if status == "arithmetic-weaker-only" and state.wasted_escalations() >= 2:
        next_max_q = state.max_q
        next_n_terms = state.n_terms
        next_keep_last = state.keep_last
        next_width = state.crossing_half_width

    return EvidenceWeightedClassState(
        class_label=state.class_label,
        max_q=next_max_q,
        n_terms=next_n_terms,
        q_min=state.q_min,
        keep_last=next_keep_last,
        crossing_half_width=next_width,
        band_offset_lo=state.band_offset_lo,
        band_offset_hi=state.band_offset_hi,
        refinement_base_tol=state.refinement_base_tol,
        refinement_q2_scale=state.refinement_q2_scale,
        refinement_min_subset=state.refinement_min_subset,
        asymptotic_min_members=next_asym,
        asymptotic_center_drift_tol=state.asymptotic_center_drift_tol,
        rounds_run=state.rounds_run,
        escalations=state.escalations + 1,
        survival_rounds=state.survival_rounds,
        overlap_rounds=state.overlap_rounds,
        undecided_rounds=state.undecided_rounds,
        arithmetic_only_rounds=state.arithmetic_only_rounds,
        dominated_rounds=state.dominated_rounds,
        no_upper_rounds=state.no_upper_rounds,
        upper_object_rounds=state.upper_object_rounds,
        improvement_rounds=state.improvement_rounds,
        source_upgrade_rounds=state.source_upgrade_rounds,
        stagnation_rounds=state.stagnation_rounds,
        consecutive_survival_rounds=state.consecutive_survival_rounds,
        last_selected_upper_hi=state.last_selected_upper_hi,
        last_selected_upper_width=state.last_selected_upper_width,
        last_selected_upper_source=state.last_selected_upper_source,
        last_margin_to_reference=state.last_margin_to_reference,
        best_selected_upper_hi=state.best_selected_upper_hi,
        best_selected_upper_source=state.best_selected_upper_source,
    )


def _summarize_report(
    records: list[dict[str, Any]],
    *,
    reference_lower_bound: float,
    reference_label: str,
    reference_crossing_center: float,
    family: HarmonicFamily,
    rounds: list[dict[str, Any]],
    total_escalations: int,
    terminated_early: bool,
) -> EvidenceWeightedSearchReport:
    dominated = sum(1 for r in records if r.get("pruning_status") == "dominated")
    overlapping = sum(1 for r in records if r.get("pruning_status") == "overlapping")
    arithmetic_only = sum(1 for r in records if r.get("pruning_status") == "arithmetic-weaker-only")
    undecided = sum(1 for r in records if r.get("pruning_status") == "undecided")

    remaining = [r for r in records if r.get("pruning_status") != "dominated" and r.get("selected_upper_hi") is not None]
    strongest_remaining_class = None
    strongest_remaining_upper_bound = None
    strongest_remaining_source = None
    if remaining:
        best = min(remaining, key=lambda r: float(r["selected_upper_hi"]))
        strongest_remaining_class = str(best["class_label"])
        strongest_remaining_upper_bound = float(best["selected_upper_hi"])
        strongest_remaining_source = str(best["selected_upper_source"])

    if records and dominated == len(records):
        status = "all-screened-classes-dominated"
    elif overlapping:
        status = "evidence-weighted-search-has-overlapping-challengers"
    elif undecided:
        status = "evidence-weighted-search-has-undecided-challengers"
    elif arithmetic_only:
        status = "evidence-weighted-search-is-arithmetic-heavy"
    else:
        status = "evidence-weighted-search-partial-exhaustion"

    notes = (
        "This search loop learns from round history. Persistent classes that improve under escalation "
        "receive more denominator depth, while classes that consume budget without sharpening their "
        "upper-side object are deprioritized. It is still a search policy, not the final exhaustion theorem."
    )
    return EvidenceWeightedSearchReport(
        reference_label=str(reference_label),
        reference_lower_bound=float(reference_lower_bound),
        reference_crossing_center=float(reference_crossing_center),
        family_label=type(family).__name__,
        rounds=rounds,
        final_records=records,
        dominated_count=dominated,
        overlapping_count=overlapping,
        arithmetic_only_count=arithmetic_only,
        undecided_count=undecided,
        strongest_remaining_class=strongest_remaining_class,
        strongest_remaining_upper_bound=strongest_remaining_upper_bound,
        strongest_remaining_source=strongest_remaining_source,
        total_escalations=int(total_escalations),
        terminated_early=bool(terminated_early),
        status=status,
        notes=notes,
    )


def build_evidence_weighted_class_exhaustion_search(
    specs: Sequence[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    reference_label: str = "golden",
    family: HarmonicFamily | None = None,
    rounds: int = 4,
    per_round_budget: int = 2,
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
) -> EvidenceWeightedSearchReport:
    family = family or HarmonicFamily()
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    if per_round_budget <= 0:
        raise ValueError("per_round_budget must be positive")

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

    rounds_out: list[dict[str, Any]] = []
    total_escalations = 0
    final_records: list[dict[str, Any]] = []
    terminated_early = False

    for ridx in range(1, rounds + 1):
        records = []
        for label, spec in spec_map.items():
            rec = _build_record_for_state(
                spec,
                state_map[label],
                reference_crossing_center=reference_crossing_center,
                reference_lower_bound=reference_lower_bound,
                family=family,
                target_residue=target_residue,
                auto_localize_crossing=auto_localize_crossing,
                initial_subdivisions=initial_subdivisions,
                max_depth=max_depth,
                min_width=min_width,
            )
            state_map[label] = _update_state_from_record(
                state_map[label],
                rec,
                upper_improvement_tol=upper_improvement_tol,
                width_improvement_tol=width_improvement_tol,
            )
            rec["evidence_state"] = state_map[label].to_dict()
            rec["priority_score"] = _evidence_priority_score(rec, state_map[label])
            rec["priority_reason"] = _priority_reason(rec, state_map[label])
            records.append(rec)

        records.sort(key=lambda r: (-float(r["priority_score"]), str(r.get("class_label"))))
        final_records = records

        survivors = [
            r for r in records
            if str(r.get("pruning_status")) in {"overlapping", "undecided", "arithmetic-weaker-only"}
        ]
        priority = survivors[:per_round_budget]
        priority_labels = [str(r["class_label"]) for r in priority]

        escalated_labels: list[str] = []
        if ridx < rounds:
            for rec in priority:
                label = str(rec["class_label"])
                state_map[label] = _escalate_state_evidence_weighted(
                    state_map[label],
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
                escalated_labels.append(label)
                total_escalations += 1

        round_status = "all-dominated" if not survivors else "evidence-weighted-search-continues"
        if escalated_labels:
            round_notes = (
                "Priority classes were selected using current threat together with round-history evidence "
                "about persistence, productivity under escalation, and wasted budget."
            )
        else:
            round_notes = (
                "No further escalations were needed because all currently screened classes were dominated "
                "or this was the final round."
            )
        rounds_out.append(EvidenceWeightedRound(
            round_index=ridx,
            active_classes=[str(r["class_label"]) for r in records],
            top_priority_classes=priority_labels,
            escalated_classes=escalated_labels,
            records=records,
            status=round_status,
            notes=round_notes,
        ).to_dict())

        if not survivors:
            terminated_early = True
            break

    return _summarize_report(
        final_records,
        reference_lower_bound=reference_lower_bound,
        reference_label=reference_label,
        reference_crossing_center=reference_crossing_center,
        family=family,
        rounds=rounds_out,
        total_escalations=total_escalations,
        terminated_early=terminated_early,
    )


__all__ = [
    "EvidenceWeightedClassState",
    "EvidenceWeightedRound",
    "EvidenceWeightedSearchReport",
    "build_evidence_weighted_class_exhaustion_search",
]
