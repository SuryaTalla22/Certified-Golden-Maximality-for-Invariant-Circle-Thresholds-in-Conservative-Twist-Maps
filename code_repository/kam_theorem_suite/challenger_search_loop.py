from __future__ import annotations

"""Adaptive challenger-exhaustion search loops.

This module turns the static class-level exhaustion screen into a lightweight,
priority-driven search policy.  The aim is still modest and honest:

- this is not a theorem of challenger exhaustion;
- it does not prove that the selected search policy is optimal;
- it *does* provide a reproducible way to spend additional certification effort
  on the classes that remain most threatening after a screen.

The core idea is simple.  Start with a uniform class-level screen, then repeat:

1. rank the non-dominated classes by a threat score,
2. escalate only the top few classes by increasing their ladder depth and/or
   widening their campaign windows when evidence is too sparse,
3. rebuild the per-class records with the updated settings, and
4. stop early if every screened class is dominated.

This produces a search history that is much closer to a genuine exhaustion
workflow than the earlier static screen, while remaining computationally light
and deterministic enough for tests and notebooks.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .class_campaigns import ArithmeticClassSpec
from .class_exhaustion_screen import build_class_exhaustion_record
from .standard_map import HarmonicFamily


@dataclass
class ChallengerSearchState:
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChallengerSearchRound:
    round_index: int
    active_classes: list[str]
    escalated_classes: list[str]
    top_priority_classes: list[str]
    records: list[dict[str, Any]]
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChallengerSearchLoopReport:
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


_STATUS_PRIORITY = {
    "overlapping": 0,
    "undecided": 1,
    "arithmetic-weaker-only": 2,
    "dominated": 3,
}


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
) -> ChallengerSearchState:
    return ChallengerSearchState(
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
    state: ChallengerSearchState,
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


def _threat_score(record: dict[str, Any], reference_lower_bound: float) -> tuple[Any, ...]:
    status = str(record.get("pruning_status", "undecided"))
    status_rank = _STATUS_PRIORITY.get(status, 99)
    upper_hi = _float_or_none(record.get("selected_upper_hi"))
    margin = _float_or_none(record.get("selected_upper_margin_to_reference"))
    source = str(record.get("selected_upper_source", "no-upper-object"))
    upper_missing = upper_hi is None
    # Larger threat should sort first.  We therefore place more dangerous states
    # earlier by minimizing the tuple below.
    source_rank = {
        "asymptotic-upper-ladder": 0,
        "refined-upper-ladder": 1,
        "raw-upper-ladder": 2,
        "no-upper-object": 3,
    }.get(source, 9)
    # Negative margin means the challenger upper bound sits above the trusted
    # golden lower bound and is therefore more threatening.
    margin_key = 1e9 if margin is None else float(margin)
    upper_key = 1e9 if upper_hi is None else float(upper_hi)
    return (status_rank, upper_missing, margin_key, source_rank, upper_key, str(record.get("class_label")))


def _summarize_records(
    records: list[dict[str, Any]],
    *,
    reference_lower_bound: float,
    reference_label: str,
    reference_crossing_center: float,
    family: HarmonicFamily,
    rounds: list[dict[str, Any]],
    total_escalations: int,
    terminated_early: bool,
) -> ChallengerSearchLoopReport:
    ordered = sorted(records, key=lambda r: _threat_score(r, reference_lower_bound))
    dominated = sum(1 for r in ordered if r.get("pruning_status") == "dominated")
    overlapping = sum(1 for r in ordered if r.get("pruning_status") == "overlapping")
    arithmetic_only = sum(1 for r in ordered if r.get("pruning_status") == "arithmetic-weaker-only")
    undecided = sum(1 for r in ordered if r.get("pruning_status") == "undecided")

    remaining = [r for r in ordered if r.get("pruning_status") != "dominated" and r.get("selected_upper_hi") is not None]
    strongest_remaining_class = None
    strongest_remaining_upper_bound = None
    strongest_remaining_source = None
    if remaining:
        best = min(remaining, key=lambda r: float(r["selected_upper_hi"]))
        strongest_remaining_class = str(best["class_label"])
        strongest_remaining_upper_bound = float(best["selected_upper_hi"])
        strongest_remaining_source = str(best["selected_upper_source"])

    if ordered and dominated == len(ordered):
        status = "all-screened-classes-dominated"
    elif overlapping:
        status = "adaptive-search-has-overlapping-challengers"
    elif undecided:
        status = "adaptive-search-has-undecided-challengers"
    elif arithmetic_only:
        status = "adaptive-search-is-arithmetic-heavy"
    else:
        status = "adaptive-search-partial-exhaustion"

    notes = (
        "This adaptive search loop re-screens the current challenger set round by round, "
        "allocating extra ladder depth and/or wider campaign windows only to the strongest "
        "surviving challengers. It is a search policy, not the final exhaustion theorem."
    )
    return ChallengerSearchLoopReport(
        reference_label=str(reference_label),
        reference_lower_bound=float(reference_lower_bound),
        reference_crossing_center=float(reference_crossing_center),
        family_label=type(family).__name__,
        rounds=rounds,
        final_records=ordered,
        dominated_count=int(dominated),
        overlapping_count=int(overlapping),
        arithmetic_only_count=int(arithmetic_only),
        undecided_count=int(undecided),
        strongest_remaining_class=strongest_remaining_class,
        strongest_remaining_upper_bound=strongest_remaining_upper_bound,
        strongest_remaining_source=strongest_remaining_source,
        total_escalations=int(total_escalations),
        terminated_early=bool(terminated_early),
        status=status,
        notes=notes,
    )


def _escalate_state(
    state: ChallengerSearchState,
    record: dict[str, Any],
    *,
    max_q_step: int,
    keep_last_step: int,
    n_terms_step: int,
    width_growth: float,
    width_cap: float,
    asymptotic_member_cap: int,
) -> ChallengerSearchState:
    status = str(record.get("pruning_status", "undecided"))
    has_upper = record.get("selected_upper_hi") is not None
    next_width = state.crossing_half_width
    next_max_q = state.max_q
    next_n_terms = state.n_terms
    next_keep_last = state.keep_last
    next_asym = state.asymptotic_min_members

    # Threatening classes get more denominator depth.  Classes with no upper
    # object also get wider campaign windows so the next round has a better
    # chance of finding a usable crossing ladder.
    if status in {"overlapping", "undecided"}:
        next_max_q = state.max_q + max_q_step
        next_n_terms = state.n_terms + n_terms_step
        next_keep_last = None if state.keep_last is None else state.keep_last + keep_last_step
        next_asym = min(asymptotic_member_cap, state.asymptotic_min_members + 1)
    if not has_upper or status == "undecided":
        next_width = min(width_cap, state.crossing_half_width * width_growth)

    return ChallengerSearchState(
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
        rounds_run=state.rounds_run + 1,
        escalations=state.escalations + 1,
    )


def build_adaptive_class_exhaustion_search(
    specs: Sequence[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    reference_label: str = "golden",
    family: HarmonicFamily | None = None,
    rounds: int = 3,
    per_round_budget: int = 2,
    initial_max_q: int = 89,
    max_q_step: int = 55,
    initial_n_terms: int = 96,
    n_terms_step: int = 24,
    q_min: int = 8,
    initial_keep_last: int | None = 4,
    keep_last_step: int = 1,
    initial_crossing_half_width: float = 2.5e-3,
    width_growth: float = 1.35,
    width_cap: float = 1.2e-2,
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
) -> ChallengerSearchLoopReport:
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
    last_records: list[dict[str, Any]] = []
    terminated_early = False

    for ridx in range(1, rounds + 1):
        records = [
            _build_record_for_state(
                spec_map[label],
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
            for label in spec_map
        ]
        records.sort(key=lambda r: _threat_score(r, reference_lower_bound))
        last_records = records

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
                state_map[label] = _escalate_state(
                    state_map[label],
                    rec,
                    max_q_step=max_q_step,
                    keep_last_step=keep_last_step,
                    n_terms_step=n_terms_step,
                    width_growth=width_growth,
                    width_cap=width_cap,
                    asymptotic_member_cap=asymptotic_member_cap,
                )
                escalated_labels.append(label)
                total_escalations += 1

        round_status = "all-dominated" if not survivors else "search-continues"
        round_notes = (
            "Top surviving challengers were reallocated more ladder depth and/or wider campaign windows."
            if escalated_labels else
            "No further escalations were needed because all currently screened classes were dominated or this was the final round."
        )
        rounds_out.append(
            ChallengerSearchRound(
                round_index=ridx,
                active_classes=[str(r["class_label"]) for r in records],
                escalated_classes=escalated_labels,
                top_priority_classes=priority_labels,
                records=records,
                status=round_status,
                notes=round_notes,
            ).to_dict()
        )

        if not survivors:
            terminated_early = True
            break

    return _summarize_records(
        last_records,
        reference_lower_bound=reference_lower_bound,
        reference_label=reference_label,
        reference_crossing_center=reference_crossing_center,
        family=family,
        rounds=rounds_out,
        total_escalations=total_escalations,
        terminated_early=terminated_early,
    )


__all__ = [
    "ChallengerSearchState",
    "ChallengerSearchRound",
    "ChallengerSearchLoopReport",
    "build_adaptive_class_exhaustion_search",
]
