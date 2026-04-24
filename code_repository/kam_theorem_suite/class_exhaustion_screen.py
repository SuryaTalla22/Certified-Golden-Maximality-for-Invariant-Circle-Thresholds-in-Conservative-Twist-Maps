from __future__ import annotations

"""Class-level challenger exhaustion screens.

This module pushes the per-class asymptotic upper-ladder audit into a more
exhaustion-facing direction.  The goal is still to remain honest:

- this is not the final challenger-exhaustion theorem;
- it does not prove irrational nonexistence for a whole arithmetic class;
- it does provide a structured, repeatable *screen* across several challenger
  classes, ranking the strongest currently available upper-side object for each
  class and comparing it against a trusted golden lower bound.

Compared with the earlier one-class audit layers, this module adds two things:

1. consistent per-class selection of the best available upper object
   (asymptotic audit > refined ladder > raw ladder), and
2. an aggregate screen over several challenger classes that identifies which
   classes are currently dominated, overlapping, arithmetic-only, or still
   undecided.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from .asymptotic_upper_ladder_audit import audit_refined_upper_ladder_asymptotics
from .challenger_pruning import (
    build_theorem_level_pruning_certificate,
    classify_challenger_against_golden,
)
from .class_campaigns import (
    ArithmeticClassSpec,
    build_campaign_window_specs,
    build_class_ladder_report,
)
from .standard_map import HarmonicFamily
from .two_sided_irrational_atlas import build_rational_upper_ladder
from .upper_ladder_refinement import refine_rational_upper_ladder


@dataclass
class ClassExhaustionRecord:
    class_label: str
    preperiod: tuple[int, ...]
    period: tuple[int, ...]
    rho: float
    eta_lo: float
    eta_hi: float
    eta_center: float
    approximant_count: int
    raw_ladder_quality: str
    refined_status: str
    asymptotic_status: str
    selected_upper_source: str
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_upper_width: float | None
    selected_upper_margin_to_reference: float | None
    earliest_band_lo: float | None
    latest_band_hi: float | None
    pruning_status: str
    reason: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ClassExhaustionScreenReport:
    reference_label: str
    reference_lower_bound: float
    reference_crossing_center: float
    family_label: str
    classes: list[dict[str, Any]]
    dominated_count: int
    overlapping_count: int
    arithmetic_only_count: int
    undecided_count: int
    asymptotic_upper_count: int
    refined_upper_count: int
    raw_upper_count: int
    no_upper_count: int
    strongest_remaining_class: str | None
    strongest_remaining_upper_bound: float | None
    strongest_remaining_source: str | None
    arithmetic_ranking_certificate: dict[str, Any]
    pruning_region_certificate: dict[str, Any]
    near_top_threat_set_partition_certificate: dict[str, Any]
    screened_panel_global_completeness_certificate: dict[str, Any]
    omitted_class_global_control_certificate: dict[str, Any]
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _float_or_none(x: Any) -> float | None:
    return None if x is None else float(x)


def _select_best_upper_object(
    raw: dict[str, Any],
    refined: dict[str, Any],
    audit: dict[str, Any],
) -> tuple[str, float | None, float | None, float | None]:
    """Pick the strongest currently available upper-side object.

    Preference order is intentionally theorem-facing:
    asymptotic audited object > refined cluster object > raw ladder object.
    """
    alo = _float_or_none(audit.get("audited_upper_lo"))
    ahi = _float_or_none(audit.get("audited_upper_hi"))
    aw = _float_or_none(audit.get("audited_upper_width"))
    if alo is not None and ahi is not None:
        return "asymptotic-upper-ladder", alo, ahi, aw

    rlo = _float_or_none(refined.get("best_refined_crossing_lower_bound"))
    rhi = _float_or_none(refined.get("best_refined_crossing_upper_bound"))
    rw = _float_or_none(refined.get("best_refined_crossing_width"))
    if rlo is not None and rhi is not None:
        return "refined-upper-ladder", rlo, rhi, rw

    lo = _float_or_none(raw.get("best_crossing_lower_bound"))
    hi = _float_or_none(raw.get("best_crossing_upper_bound"))
    w = None
    if lo is not None and hi is not None:
        w = float(hi - lo)
        return "raw-upper-ladder", lo, hi, w

    return "no-upper-object", None, None, None


def _build_arithmetic_ranking_certificate(
    records: Sequence[Mapping[str, Any]],
    *,
    theorem_level_ranked_labels: Iterable[str] | None = None,
) -> dict[str, Any]:
    theorem_level_labels = {str(x) for x in (theorem_level_ranked_labels or [])}
    ranking = sorted(
        [
            {
                "class_label": str(r.get("class_label", "unknown")),
                "eta_hi": float(r.get("eta_hi", 0.0)),
                "eta_lo": float(r.get("eta_lo", 0.0)),
            }
            for r in records
        ],
        key=lambda row: (-row["eta_hi"], -row["eta_lo"], row["class_label"]),
    )
    screened_labels = [row["class_label"] for row in ranking]
    theorem_level_available = bool(screened_labels) and all(label in theorem_level_labels for label in screened_labels)
    if theorem_level_available:
        status = "exact-near-top-ranking-certificate-strong"
    elif screened_labels:
        status = "screened-panel-ranking-certificate-available"
    else:
        status = "screened-panel-ranking-certificate-missing"
    return {
        "status": status,
        "ranking": ranking,
        "screened_class_labels": screened_labels,
        "theorem_level_ranked_labels": sorted(theorem_level_labels),
        "proves_exact_near_top_lagrange_spectrum_ranking": theorem_level_available,
        "covers_screened_panel": bool(screened_labels),
        "notes": (
            "This certificate records the arithmetic ordering presently visible on the screened panel. "
            "It only clears the theorem-side ranking burden when every screened label is backed by an explicit theorem-level ranking promotion."
        ),
    }



def _normalize_theorem_level_complete_records(
    records: Sequence[Mapping[str, Any]],
    *,
    theorem_level_complete_labels: Iterable[str] | None = None,
    theorem_level_complete_records: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    labels = {str(x) for x in (theorem_level_complete_labels or [])}
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in theorem_level_complete_records or []:
        label = str(row.get("class_label", row.get("label", "unknown")))
        normalized.append({
            "class_label": label,
            "completion_source": str(row.get("completion_source", "theorem-level-completeness-record")),
            "completion_reason": str(row.get("completion_reason", "screened challenger promoted to theorem-level complete near-top record")),
            "certificate_name": str(row.get("certificate_name", "screened_panel_global_completeness_certificate")),
        })
        seen.add(label)
    known_labels = {str(r.get("class_label", "unknown")) for r in records}
    for label in sorted(labels):
        if label in seen or label not in known_labels:
            continue
        normalized.append({
            "class_label": label,
            "completion_source": "theorem-level-complete-label",
            "completion_reason": "screened challenger listed as theorem-level complete",
            "certificate_name": "screened_panel_global_completeness_certificate",
        })
    return normalized


def build_near_top_threat_set_partition_certificate(
    *,
    screened_panel_certificate: Mapping[str, Any],
    arithmetic_ranking_certificate: Mapping[str, Any] | None = None,
    pruning_region_certificate: Mapping[str, Any] | None = None,
    deferred_retired_domination_certificate: Mapping[str, Any] | None = None,
    termination_exclusion_promotion_certificate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    screened_panel_certificate = dict(screened_panel_certificate)
    arithmetic_ranking_certificate = {} if arithmetic_ranking_certificate is None else dict(arithmetic_ranking_certificate)
    pruning_region_certificate = {} if pruning_region_certificate is None else dict(pruning_region_certificate)
    deferred_retired_domination_certificate = {} if deferred_retired_domination_certificate is None else dict(deferred_retired_domination_certificate)
    termination_exclusion_promotion_certificate = {} if termination_exclusion_promotion_certificate is None else dict(termination_exclusion_promotion_certificate)

    screened_labels = {str(x) for x in screened_panel_certificate.get("screened_panel_labels", [])}
    theorem_level_complete_records = [dict(x) for x in screened_panel_certificate.get("theorem_level_complete_records", [])]
    theorem_level_complete_labels = {str(x.get("class_label", x.get("label", "unknown"))) for x in theorem_level_complete_records}
    ranking_labels = {str(x) for x in arithmetic_ranking_certificate.get("theorem_level_ranked_labels", [])}
    dominated_labels = {str(x) for x in pruning_region_certificate.get("theorem_level_dominated_labels", [])}
    termination_candidate_labels = {str(x) for x in termination_exclusion_promotion_certificate.get("candidate_labels", [])}
    termination_promoted_labels = {str(x) for x in termination_exclusion_promotion_certificate.get("promoted_labels", [])}
    deferred_retired_labels = {
        str(x)
        for x in list(deferred_retired_domination_certificate.get("deferred_labels", []))
        + list(deferred_retired_domination_certificate.get("retired_labels", []))
    }

    covered_by_theorem_level_screen = sorted(screened_labels & theorem_level_complete_labels)
    dominated_outside_screen = sorted(dominated_labels - screened_labels)
    ranking_excluded_labels = sorted((ranking_labels - screened_labels) - set(dominated_outside_screen) - termination_promoted_labels)
    termination_excluded_labels = sorted((termination_promoted_labels | deferred_retired_labels) - screened_labels - set(dominated_outside_screen) - set(ranking_excluded_labels))

    relevant_threat_labels = screened_labels | ranking_labels | dominated_labels | termination_candidate_labels | deferred_retired_labels | theorem_level_complete_labels
    covered_labels = set(covered_by_theorem_level_screen) | set(dominated_outside_screen) | set(ranking_excluded_labels) | set(termination_excluded_labels)
    uncovered_labels = sorted(relevant_threat_labels - covered_labels)

    panel_has_no_overlaps = bool(screened_panel_certificate.get("panel_has_no_overlaps", False))
    panel_has_no_undecided = bool(screened_panel_certificate.get("panel_has_no_undecided", False))
    proves_ranking = bool(arithmetic_ranking_certificate.get("proves_exact_near_top_lagrange_spectrum_ranking", False))
    proves_pruning = bool(pruning_region_certificate.get("proves_theorem_level_pruning_of_dominated_regions", False))
    proves_termination = bool(termination_exclusion_promotion_certificate.get("proves_termination_search_promotes_to_theorem_exclusion", False)) or not termination_candidate_labels

    partition_complete = bool(relevant_threat_labels or screened_labels) and panel_has_no_overlaps and panel_has_no_undecided and proves_ranking and proves_pruning and proves_termination and not uncovered_labels
    if partition_complete:
        status = "near-top-threat-set-partition-certified"
    elif relevant_threat_labels or screened_labels:
        status = "near-top-threat-set-partition-frontier"
    else:
        status = "near-top-threat-set-partition-missing"

    return {
        "status": status,
        "screened_labels": sorted(screened_labels),
        "covered_by_theorem_level_screen": covered_by_theorem_level_screen,
        "dominated_outside_screen": dominated_outside_screen,
        "ranking_excluded_labels": ranking_excluded_labels,
        "termination_excluded_labels": termination_excluded_labels,
        "relevant_threat_labels": sorted(relevant_threat_labels),
        "uncovered_labels": uncovered_labels,
        "partition_complete": partition_complete,
        "proves_screened_panel_global_completeness": partition_complete,
        "notes": (
            "This certificate partitions the currently explicit near-top challenger threat set into screened labels, theorem-level dominated labels outside the screen, ranking-side exclusions, and termination-promotion exclusions. "
            "The screened panel becomes theorem-grade globally complete only when this finite threat set is fully partitioned with no overlaps or undecided screened survivors remaining."
        ),
    }


def promote_screened_panel_global_completeness_certificate(
    *,
    screened_panel_certificate: Mapping[str, Any],
    arithmetic_ranking_certificate: Mapping[str, Any] | None = None,
    pruning_region_certificate: Mapping[str, Any] | None = None,
    deferred_retired_domination_certificate: Mapping[str, Any] | None = None,
    termination_exclusion_promotion_certificate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = dict(screened_panel_certificate)
    partition_certificate = build_near_top_threat_set_partition_certificate(
        screened_panel_certificate=base,
        arithmetic_ranking_certificate=arithmetic_ranking_certificate,
        pruning_region_certificate=pruning_region_certificate,
        deferred_retired_domination_certificate=deferred_retired_domination_certificate,
        termination_exclusion_promotion_certificate=termination_exclusion_promotion_certificate,
    )
    promoted = dict(base)
    promoted.update({
        "near_top_threat_set_partition_certificate": partition_certificate,
        "covered_by_theorem_level_screen": list(partition_certificate.get("covered_by_theorem_level_screen", [])),
        "dominated_outside_screen": list(partition_certificate.get("dominated_outside_screen", [])),
        "ranking_excluded_labels": list(partition_certificate.get("ranking_excluded_labels", [])),
        "termination_excluded_labels": list(partition_certificate.get("termination_excluded_labels", [])),
        "uncovered_labels": list(partition_certificate.get("uncovered_labels", [])),
        "near_top_threat_set_fully_partitioned": bool(partition_certificate.get("partition_complete", False)),
    })
    if bool(partition_certificate.get("proves_screened_panel_global_completeness", False)) or bool(base.get("screened_panel_globally_complete", False)):
        promoted["status"] = "screened-panel-global-completeness-certified"
        promoted["screened_panel_globally_complete"] = True
    elif promoted.get("screened_panel_labels") or base.get("status") == "screened-panel-global-completeness-frontier":
        promoted["status"] = "screened-panel-global-completeness-frontier"
        promoted["screened_panel_globally_complete"] = False
    else:
        promoted["status"] = "screened-panel-global-completeness-missing"
        promoted["screened_panel_globally_complete"] = False
    return promoted


def promote_omitted_class_global_control_certificate(
    *,
    omitted_control_certificate: Mapping[str, Any] | None = None,
    partition_certificate: Mapping[str, Any] | None = None,
    screened_panel_certificate: Mapping[str, Any] | None = None,
    arithmetic_ranking_certificate: Mapping[str, Any] | None = None,
    pruning_region_certificate: Mapping[str, Any] | None = None,
    deferred_retired_domination_certificate: Mapping[str, Any] | None = None,
    termination_exclusion_promotion_certificate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = {} if omitted_control_certificate is None else dict(omitted_control_certificate)
    arithmetic_ranking_certificate = {} if arithmetic_ranking_certificate is None else dict(arithmetic_ranking_certificate)
    pruning_region_certificate = {} if pruning_region_certificate is None else dict(pruning_region_certificate)
    deferred_retired_domination_certificate = {} if deferred_retired_domination_certificate is None else dict(deferred_retired_domination_certificate)
    termination_exclusion_promotion_certificate = {} if termination_exclusion_promotion_certificate is None else dict(termination_exclusion_promotion_certificate)
    screened_panel_certificate = {} if screened_panel_certificate is None else dict(screened_panel_certificate)

    if partition_certificate is None:
        partition_certificate = build_near_top_threat_set_partition_certificate(
            screened_panel_certificate=screened_panel_certificate,
            arithmetic_ranking_certificate=arithmetic_ranking_certificate,
            pruning_region_certificate=pruning_region_certificate,
            deferred_retired_domination_certificate=deferred_retired_domination_certificate,
            termination_exclusion_promotion_certificate=termination_exclusion_promotion_certificate,
        )
    else:
        partition_certificate = dict(partition_certificate)

    omitted_labels = sorted(
        set(partition_certificate.get("dominated_outside_screen", []))
        | set(partition_certificate.get("ranking_excluded_labels", []))
        | set(partition_certificate.get("termination_excluded_labels", []))
    )
    dominated_outside_screen = {str(x) for x in partition_certificate.get("dominated_outside_screen", [])}
    ranking_excluded_labels = {str(x) for x in partition_certificate.get("ranking_excluded_labels", [])}
    termination_excluded_labels = {str(x) for x in partition_certificate.get("termination_excluded_labels", [])}
    deferred_labels = {str(x) for x in deferred_retired_domination_certificate.get("deferred_labels", [])}
    retired_labels = {str(x) for x in deferred_retired_domination_certificate.get("retired_labels", [])}
    termination_promoted_labels = {str(x) for x in termination_exclusion_promotion_certificate.get("promoted_labels", [])}

    pruning_ready = bool(pruning_region_certificate.get("proves_theorem_level_pruning_of_dominated_regions", False))
    ranking_ready = bool(arithmetic_ranking_certificate.get("proves_exact_near_top_lagrange_spectrum_ranking", False))
    deferred_ready = bool(deferred_retired_domination_certificate.get("proves_deferred_or_retired_classes_are_globally_dominated", False))
    termination_ready = bool(termination_exclusion_promotion_certificate.get("proves_termination_search_promotes_to_theorem_exclusion", False))
    partition_complete = bool(partition_certificate.get("partition_complete", False))
    screen_complete = bool(screened_panel_certificate.get("screened_panel_globally_complete", False)) or bool(partition_certificate.get("proves_screened_panel_global_completeness", False))

    controlled_by_pruning = sorted(dominated_outside_screen) if pruning_ready else []
    controlled_by_ranking = sorted(ranking_excluded_labels) if ranking_ready and screen_complete else []
    controlled_by_termination_exclusion = sorted(termination_excluded_labels & termination_promoted_labels) if termination_ready else []
    controlled_by_deferred_retired_domination = sorted(termination_excluded_labels & (deferred_labels | retired_labels)) if deferred_ready else []

    control_records: list[dict[str, Any]] = []
    for label in omitted_labels:
        if label in controlled_by_pruning:
            control_records.append({
                "class_label": label,
                "control_source": "theorem-level-pruning",
                "control_reason": "omitted class lies in a theorem-level dominated region outside the screened panel",
                "certificate_name": "theorem_level_pruning_certificate",
            })
        elif label in controlled_by_ranking:
            control_records.append({
                "class_label": label,
                "control_source": "exact-near-top-ranking",
                "control_reason": "omitted class is excluded by the theorem-level near-top arithmetic ranking once the screened panel is complete",
                "certificate_name": "exact_near_top_lagrange_spectrum_ranking_certificate",
            })
        elif label in controlled_by_termination_exclusion:
            control_records.append({
                "class_label": label,
                "control_source": "termination-exclusion-promotion",
                "control_reason": "omitted class is excluded by a theorem-grade termination-promotion certificate",
                "certificate_name": "termination_search_exclusion_certificate",
            })
        elif label in controlled_by_deferred_retired_domination:
            control_records.append({
                "class_label": label,
                "control_source": "deferred-retired-domination",
                "control_reason": "omitted class is globally dominated despite being deferred or retired operationally",
                "certificate_name": "deferred_retired_domination_certificate",
            })

    controlled_labels = {str(row["class_label"]) for row in control_records}
    uncontrolled_omitted_labels = sorted(set(omitted_labels) - controlled_labels)
    base_omitted_classes_globally_controlled = bool(base.get("omitted_classes_globally_controlled", False))
    if base_omitted_classes_globally_controlled:
        if not omitted_labels:
            omitted_labels = [str(x) for x in base.get("omitted_labels", [])]
        if not control_records:
            control_records = [dict(x) for x in base.get("control_records", [])]
        if not uncontrolled_omitted_labels:
            uncontrolled_omitted_labels = [str(x) for x in base.get("uncontrolled_omitted_labels", [])]
    omitted_classes_globally_controlled = base_omitted_classes_globally_controlled or (
        screen_complete and partition_complete and len(uncontrolled_omitted_labels) == 0
    )

    promoted = dict(base)
    promoted.update({
        "near_top_threat_set_partition_certificate": partition_certificate,
        "screened_panel_global_completeness_status": str(screened_panel_certificate.get("status", "screened-panel-global-completeness-missing")),
        "screened_panel_globally_complete": screen_complete,
        "partition_complete": partition_complete,
        "omitted_labels": omitted_labels,
        "controlled_by_pruning": controlled_by_pruning,
        "controlled_by_ranking": controlled_by_ranking,
        "controlled_by_termination_exclusion": controlled_by_termination_exclusion,
        "controlled_by_deferred_retired_domination": controlled_by_deferred_retired_domination,
        "control_records": control_records,
        "uncontrolled_omitted_labels": uncontrolled_omitted_labels,
        "omitted_classes_globally_controlled": omitted_classes_globally_controlled,
    })
    if omitted_classes_globally_controlled and omitted_labels:
        promoted["status"] = str(base.get("status", "omitted-class-global-control-certified")) if base_omitted_classes_globally_controlled else "omitted-class-global-control-certified"
    elif omitted_classes_globally_controlled:
        promoted["status"] = str(base.get("status", "omitted-class-global-control-vacuous")) if base_omitted_classes_globally_controlled else "omitted-class-global-control-vacuous"
    elif omitted_labels or partition_complete or screen_complete:
        promoted["status"] = "omitted-class-global-control-frontier"
    else:
        promoted["status"] = "omitted-class-global-control-missing"
    promoted["notes"] = (
        "This certificate promotes omitted non-golden classes outside the screened panel into explicit control records. "
        "It clears the theorem-side omitted-tail burden only when the screened panel is already globally complete, the near-top threat set is fully partitioned, and every omitted label is accounted for by theorem-grade pruning, ranking, deferred/retired domination, or termination-exclusion provenance."
    )
    return promoted


def _build_screened_panel_global_completeness_certificate(
    records: Sequence[Mapping[str, Any]],
    *,
    arithmetic_ranking_certificate: Mapping[str, Any],
    pruning_region_certificate: Mapping[str, Any],
    theorem_level_complete_labels: Iterable[str] | None = None,
    theorem_level_complete_records: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    screened_labels = [str(r.get("class_label", "unknown")) for r in records]
    theorem_level_complete_records = _normalize_theorem_level_complete_records(
        records,
        theorem_level_complete_labels=theorem_level_complete_labels,
        theorem_level_complete_records=theorem_level_complete_records,
    )
    theorem_level_complete_labels = {str(row.get("class_label", "unknown")) for row in theorem_level_complete_records}
    overlapping = [str(r.get("class_label", "unknown")) for r in records if str(r.get("pruning_status", "")) == "overlapping"]
    undecided = [str(r.get("class_label", "unknown")) for r in records if str(r.get("pruning_status", "")) == "undecided"]
    all_screened_promoted = bool(screened_labels) and all(label in theorem_level_complete_labels for label in screened_labels)
    theorem_level_available = (
        bool(arithmetic_ranking_certificate.get("proves_exact_near_top_lagrange_spectrum_ranking", False))
        and bool(pruning_region_certificate.get("proves_theorem_level_pruning_of_dominated_regions", False))
        and not overlapping
        and not undecided
        and all_screened_promoted
    )
    if theorem_level_available:
        status = "screened-panel-global-completeness-certified"
    elif screened_labels:
        status = "screened-panel-global-completeness-frontier"
    else:
        status = "screened-panel-global-completeness-missing"
    return {
        "status": status,
        "screened_panel_labels": screened_labels,
        "overlapping_labels": overlapping,
        "undecided_labels": undecided,
        "theorem_level_complete_labels": sorted(theorem_level_complete_labels),
        "theorem_level_complete_records": theorem_level_complete_records,
        "panel_has_no_overlaps": not overlapping,
        "panel_has_no_undecided": not undecided,
        "screened_panel_globally_complete": theorem_level_available,
        "notes": (
            "This certificate isolates the difference between a strong finite screened panel and a theorem-grade claim that the panel is globally complete for the near-top threat set."
        ),
    }


def build_class_exhaustion_record(
    spec: ArithmeticClassSpec,
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily | None = None,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    crossing_half_width: float = 2.5e-3,
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
    asymptotic_center_drift_tol: float = 5e-4,
) -> ClassExhaustionRecord:
    family = family or HarmonicFamily()
    ladder = build_class_ladder_report(
        spec,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
    ).to_dict()
    window_specs = build_campaign_window_specs(
        spec,
        reference_crossing_center=reference_crossing_center,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
        crossing_half_width=crossing_half_width,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
    )
    raw = build_rational_upper_ladder(
        rho=float(ladder["rho"]),
        specs=window_specs,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()
    refined = refine_rational_upper_ladder(
        raw,
        base_tol=refinement_base_tol,
        q2_scale=refinement_q2_scale,
        min_subset=refinement_min_subset,
    ).to_dict()
    audit = audit_refined_upper_ladder_asymptotics(
        raw,
        min_members=asymptotic_min_members,
        base_tol=refinement_base_tol,
        q2_scale=refinement_q2_scale,
        min_subset=refinement_min_subset,
        center_drift_tol=asymptotic_center_drift_tol,
    ).to_dict()

    source, ulo, uhi, uw = _select_best_upper_object(raw, refined, audit)
    pruning_status, reason = classify_challenger_against_golden(
        golden_lower_bound=reference_lower_bound,
        eta_lo=float(ladder["eta_lo"]),
        eta_hi=float(ladder["eta_hi"]),
        threshold_upper_bound=uhi,
    )
    margin = None if uhi is None else float(reference_lower_bound - float(uhi))
    notes = (
        "Best upper object selected by priority asymptotic > refined > raw. "
        "This is a class-level exhaustion screen, not the final exhaustion theorem."
    )
    return ClassExhaustionRecord(
        class_label=str(ladder["class_label"]),
        preperiod=tuple(spec.preperiod),
        period=tuple(spec.period),
        rho=float(ladder["rho"]),
        eta_lo=float(ladder["eta_lo"]),
        eta_hi=float(ladder["eta_hi"]),
        eta_center=float(ladder["eta_center"]),
        approximant_count=len(ladder.get("approximants", [])),
        raw_ladder_quality=str(raw.get("ladder_quality", "failed")),
        refined_status=str(refined.get("status", "failed")),
        asymptotic_status=str(audit.get("status", "failed")),
        selected_upper_source=str(source),
        selected_upper_lo=ulo,
        selected_upper_hi=uhi,
        selected_upper_width=uw,
        selected_upper_margin_to_reference=margin,
        earliest_band_lo=_float_or_none(raw.get("earliest_band_lo")),
        latest_band_hi=_float_or_none(raw.get("latest_band_hi")),
        pruning_status=str(pruning_status),
        reason=str(reason),
        notes=notes,
    )


def build_class_exhaustion_screen(
    specs: Sequence[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    reference_label: str = "golden",
    family: HarmonicFamily | None = None,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    crossing_half_width: float = 2.5e-3,
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
    asymptotic_center_drift_tol: float = 5e-4,
    theorem_level_ranked_labels: Iterable[str] | None = None,
    theorem_level_dominated_labels: Iterable[str] | None = None,
    theorem_level_complete_labels: Iterable[str] | None = None,
    theorem_level_complete_records: Sequence[Mapping[str, Any]] | None = None,
) -> ClassExhaustionScreenReport:
    family = family or HarmonicFamily()
    records = [
        build_class_exhaustion_record(
            spec,
            reference_crossing_center=reference_crossing_center,
            reference_lower_bound=reference_lower_bound,
            family=family,
            max_q=max_q,
            n_terms=n_terms,
            q_min=q_min,
            keep_last=keep_last,
            crossing_half_width=crossing_half_width,
            band_offset_lo=band_offset_lo,
            band_offset_hi=band_offset_hi,
            target_residue=target_residue,
            auto_localize_crossing=auto_localize_crossing,
            initial_subdivisions=initial_subdivisions,
            max_depth=max_depth,
            min_width=min_width,
            refinement_base_tol=refinement_base_tol,
            refinement_q2_scale=refinement_q2_scale,
            refinement_min_subset=refinement_min_subset,
            asymptotic_min_members=asymptotic_min_members,
            asymptotic_center_drift_tol=asymptotic_center_drift_tol,
        ).to_dict()
        for spec in specs
    ]
    status_rank = {"dominated": 0, "overlapping": 1, "arithmetic-weaker-only": 2, "undecided": 3}
    records.sort(
        key=lambda r: (
            status_rank.get(str(r.get("pruning_status")), 99),
            r.get("selected_upper_hi") is None,
            float(r.get("selected_upper_hi") or 1e9),
            str(r.get("class_label")),
        )
    )

    dominated = sum(1 for r in records if r["pruning_status"] == "dominated")
    overlapping = sum(1 for r in records if r["pruning_status"] == "overlapping")
    arithmetic_only = sum(1 for r in records if r["pruning_status"] == "arithmetic-weaker-only")
    undecided = sum(1 for r in records if r["pruning_status"] == "undecided")
    asym_count = sum(1 for r in records if r["selected_upper_source"] == "asymptotic-upper-ladder")
    ref_count = sum(1 for r in records if r["selected_upper_source"] == "refined-upper-ladder")
    raw_count = sum(1 for r in records if r["selected_upper_source"] == "raw-upper-ladder")
    no_upper_count = sum(1 for r in records if r["selected_upper_source"] == "no-upper-object")

    remaining = [r for r in records if r["pruning_status"] != "dominated" and r.get("selected_upper_hi") is not None]
    strongest_remaining = None
    strongest_upper = None
    strongest_source = None
    if remaining:
        best = min(remaining, key=lambda r: float(r["selected_upper_hi"]))
        strongest_remaining = str(best["class_label"])
        strongest_upper = float(best["selected_upper_hi"])
        strongest_source = str(best["selected_upper_source"])

    arithmetic_ranking_certificate = _build_arithmetic_ranking_certificate(
        records,
        theorem_level_ranked_labels=theorem_level_ranked_labels,
    )
    pruning_region_certificate = build_theorem_level_pruning_certificate(
        records,
        theorem_level_dominated_labels=theorem_level_dominated_labels,
    )
    screened_panel_global_completeness_certificate = _build_screened_panel_global_completeness_certificate(
        records,
        arithmetic_ranking_certificate=arithmetic_ranking_certificate,
        pruning_region_certificate=pruning_region_certificate,
        theorem_level_complete_labels=theorem_level_complete_labels,
        theorem_level_complete_records=theorem_level_complete_records,
    )
    near_top_threat_set_partition_certificate = build_near_top_threat_set_partition_certificate(
        screened_panel_certificate=screened_panel_global_completeness_certificate,
        arithmetic_ranking_certificate=arithmetic_ranking_certificate,
        pruning_region_certificate=pruning_region_certificate,
    )
    screened_panel_global_completeness_certificate = promote_screened_panel_global_completeness_certificate(
        screened_panel_certificate=screened_panel_global_completeness_certificate,
        arithmetic_ranking_certificate=arithmetic_ranking_certificate,
        pruning_region_certificate=pruning_region_certificate,
    )
    omitted_class_global_control_certificate = promote_omitted_class_global_control_certificate(
        partition_certificate=near_top_threat_set_partition_certificate,
        screened_panel_certificate=screened_panel_global_completeness_certificate,
        arithmetic_ranking_certificate=arithmetic_ranking_certificate,
        pruning_region_certificate=pruning_region_certificate,
    )

    if records and dominated == len(records):
        overall = "all-screened-classes-dominated"
    elif overlapping:
        overall = "screen-has-overlapping-challengers"
    elif undecided:
        overall = "screen-has-undecided-challengers"
    elif arithmetic_only:
        overall = "screen-is-arithmetic-heavy"
    else:
        overall = "partial-class-exhaustion-screen"

    notes = (
        "This report aggregates per-class asymptotic/refined/raw upper-ladder evidence into a single challenger screen. "
        "It is stronger than one-class audits, but it is still not the final challenger-exhaustion theorem. "
        "The attached ranking/pruning/completeness certificates distinguish what is merely screened from what has been promoted theoremically."
    )
    return ClassExhaustionScreenReport(
        reference_label=str(reference_label),
        reference_lower_bound=float(reference_lower_bound),
        reference_crossing_center=float(reference_crossing_center),
        family_label=type(family).__name__,
        classes=records,
        dominated_count=int(dominated),
        overlapping_count=int(overlapping),
        arithmetic_only_count=int(arithmetic_only),
        undecided_count=int(undecided),
        asymptotic_upper_count=int(asym_count),
        refined_upper_count=int(ref_count),
        raw_upper_count=int(raw_count),
        no_upper_count=int(no_upper_count),
        strongest_remaining_class=strongest_remaining,
        strongest_remaining_upper_bound=strongest_upper,
        strongest_remaining_source=strongest_source,
        arithmetic_ranking_certificate=arithmetic_ranking_certificate,
        pruning_region_certificate=pruning_region_certificate,
        near_top_threat_set_partition_certificate=near_top_threat_set_partition_certificate,
        screened_panel_global_completeness_certificate=screened_panel_global_completeness_certificate,
        omitted_class_global_control_certificate=omitted_class_global_control_certificate,
        status=overall,
        notes=notes,
    )


__all__ = [
    "ClassExhaustionRecord",
    "ClassExhaustionScreenReport",
    "build_near_top_threat_set_partition_certificate",
    "promote_screened_panel_global_completeness_certificate",
    "promote_omitted_class_global_control_certificate",
    "_select_best_upper_object",
    "build_class_exhaustion_record",
    "build_class_exhaustion_screen",
]
