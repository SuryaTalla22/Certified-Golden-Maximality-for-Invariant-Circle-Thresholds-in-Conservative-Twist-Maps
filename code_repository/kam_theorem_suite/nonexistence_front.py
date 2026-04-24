from __future__ import annotations

"""Two-sided nonexistence front certificates.

The stage-34 incompatibility theorem bridge compressed the upper-side obstruction
package into an explicit hypothesis ledger.  The next theorem-facing move is to
pair that ledger with the strongest *current lower-side object* rather than with
just a single continuation profile.

This module therefore combines:
- the lower neighborhood-stability certificate, and
- the explicit upper incompatibility theorem bridge,

into one two-sided *nonexistence front* object.  The resulting certificate does
not prove irrational nonexistence.  What it does provide is the sharpest current
machine-readable statement of how close the code is to a genuine Theorem-IV-style
nonexistence theorem front.

Crucially, it separates two kinds of gaps:
1. computational/front gaps that can be assessed from existing certificates, and
2. remaining analytic lifts that are still needed before a real theorem can be
   claimed.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .golden_lower_neighborhood_stability import (
    build_golden_lower_neighborhood_stability_certificate,
)
from .incompatibility_theorem_bridge import (
    build_golden_incompatibility_theorem_bridge_certificate,
)
from .incompatibility_bridge_profile import (
    build_golden_incompatibility_bridge_profile_certificate,
)
from .incompatibility_strict_bridge import (
    build_golden_incompatibility_strict_bridge_certificate,
)
from .adaptive_support_core_neighborhood import (
    build_golden_adaptive_support_core_neighborhood_certificate,
)
from .adaptive_tail_aware_neighborhood import (
    build_golden_adaptive_tail_aware_neighborhood_certificate,
)
from .adaptive_tail_stability import (
    build_golden_adaptive_tail_stability_certificate,
)
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _status_rank(status: str) -> int:
    if str(status).endswith('-strong'):
        return 4
    if str(status).endswith('-moderate'):
        return 3
    if str(status).endswith('-weak'):
        return 2
    if str(status).endswith('-fragile'):
        return 1
    return 0


@dataclass
class NonexistenceFrontHypothesisRow:
    name: str
    satisfied: bool
    margin: float | None
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalyticLiftRow:
    name: str
    status: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _default_remaining_analytic_lifts() -> list[AnalyticLiftRow]:
    return [
        AnalyticLiftRow(
            "obstruction_implies_no_analytic_circle",
            "open",
            "Promote the current coherent supercritical obstruction package into a theorem that is genuinely incompatible with analytic invariant-circle persistence in the final function space.",
        ),
        AnalyticLiftRow(
            "final_function_space_promotion",
            "open",
            "Upgrade the lower-side neighborhood object from the current collocation/a-posteriori bridge into the final infinite-dimensional analytic theorem package.",
        ),
        AnalyticLiftRow(
            "universality_class_embedding",
            "open",
            "Embed both sides of the current nonexistence front into the final renormalization-stable universality class used by the endpoint theorem.",
        ),
    ]


@dataclass
class GoldenNonexistenceFrontCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_bridge: dict[str, Any]
    upper_bridge_promotion: dict[str, Any]
    upper_support_core_neighborhood: dict[str, Any]
    upper_tail_aware_neighborhood: dict[str, Any]
    upper_tail_stability: dict[str, Any]
    upper_bridge_profile: dict[str, Any]
    relation: dict[str, Any]
    contradiction_summary: dict[str, Any]
    hypotheses: list[NonexistenceFrontHypothesisRow]
    satisfied_hypotheses: list[str]
    missing_hypotheses: list[str]
    computational_front_margin: float | None
    remaining_analytic_lifts: list[AnalyticLiftRow]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "lower_side": dict(self.lower_side),
            "upper_bridge": dict(self.upper_bridge),
            "upper_bridge_promotion": dict(self.upper_bridge_promotion),
            "upper_support_core_neighborhood": dict(self.upper_support_core_neighborhood),
            "upper_tail_aware_neighborhood": dict(self.upper_tail_aware_neighborhood),
            "upper_tail_stability": dict(self.upper_tail_stability),
            "upper_bridge_profile": dict(self.upper_bridge_profile),
            "relation": dict(self.relation),
            "contradiction_summary": dict(self.contradiction_summary),
            "hypotheses": [row.to_dict() for row in self.hypotheses],
            "satisfied_hypotheses": [str(x) for x in self.satisfied_hypotheses],
            "missing_hypotheses": [str(x) for x in self.missing_hypotheses],
            "computational_front_margin": self.computational_front_margin,
            "remaining_analytic_lifts": [row.to_dict() for row in self.remaining_analytic_lifts],
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }



def _strong_or_moderate_status(status: str) -> bool:
    return _status_rank(status) >= 3


def _build_contradiction_summary(
    *,
    relation: dict[str, Any],
    front_status: str,
    front_margin: float | None,
    upper: dict[str, Any],
    upper_bridge_promotion: dict[str, Any],
    upper_support_core_neighborhood: dict[str, Any],
    upper_tail_aware_neighborhood: dict[str, Any],
    upper_tail_stability: dict[str, Any],
    upper_bridge_profile: dict[str, Any],
) -> dict[str, Any]:
    theorem_bridge_status = str(upper.get("theorem_status", "unknown"))
    strict_bridge_status = str(upper_bridge_promotion.get("theorem_status", "not-built"))
    support_core_status = str(upper_support_core_neighborhood.get("theorem_status", "not-built"))
    tail_aware_status = str(upper_tail_aware_neighborhood.get("theorem_status", "not-built"))
    tail_stability_status = str(upper_tail_stability.get("theorem_status", "not-built"))
    bridge_profile_status = str(upper_bridge_profile.get("theorem_status", "not-built"))
    support_core_selected_status = str((upper_support_core_neighborhood.get("selected_bridge", {}) or {}).get("theorem_status", "not-built"))
    tail_aware_selected_status = str((upper_tail_aware_neighborhood.get("selected_bridge", {}) or {}).get("theorem_status", "not-built"))

    supercritical_obstruction_locked = theorem_bridge_status == "golden-incompatibility-theorem-bridge-strong"
    strict_bridge_certified = strict_bridge_status == "golden-incompatibility-theorem-bridge-strong" or supercritical_obstruction_locked
    support_geometry_certified = any(
        _strong_or_moderate_status(status)
        for status in (support_core_status, tail_aware_status, support_core_selected_status, tail_aware_selected_status)
    )
    tail_coherence_certified = supercritical_obstruction_locked
    tail_stability_certified = any(
        _strong_or_moderate_status(status)
        for status in (tail_stability_status, tail_aware_status, bridge_profile_status)
    )
    positive_window_separation = bool((relation.get("gap_to_upper_window") is not None) and (float(relation.get("gap_to_upper_window")) > 0.0))
    contradiction_margin_candidates = [
        front_margin,
        relation.get("gap_to_upper"),
        relation.get("gap_to_upper_window"),
        relation.get("gap_to_barrier"),
        relation.get("bridge_margin"),
        upper_tail_stability.get("stable_incompatibility_gap"),
    ]
    contradiction_margin_values = [float(x) for x in contradiction_margin_candidates if x is not None]
    contradiction_margin = min(contradiction_margin_values) if contradiction_margin_values else None

    residual_burden: list[str] = []
    if not supercritical_obstruction_locked:
        residual_burden.append("supercritical_obstruction_locked")
    if not strict_bridge_certified:
        residual_burden.append("strict_bridge_certified")
    if not support_geometry_certified:
        residual_burden.append("support_geometry_certified")
    if not tail_coherence_certified:
        residual_burden.append("tail_coherence_certified")
    if not tail_stability_certified:
        residual_burden.append("tail_stability_certified")
    if not positive_window_separation:
        residual_burden.append("positive_window_separation")

    nonexistence_contradiction_certified = bool(
        front_status == "golden-nonexistence-front-strong"
        and supercritical_obstruction_locked
        and strict_bridge_certified
        and support_geometry_certified
        and tail_coherence_certified
        and tail_stability_certified
        and positive_window_separation
        and contradiction_margin is not None
        and contradiction_margin >= -1.0e-15
    )

    if nonexistence_contradiction_certified:
        contradiction_status = "golden-nonexistence-contradiction-strong"
    elif front_status == "golden-nonexistence-front-strong" and not residual_burden:
        contradiction_status = "golden-nonexistence-contradiction-assembled"
    elif front_status in {"golden-nonexistence-front-strong", "golden-nonexistence-front-moderate"}:
        contradiction_status = "golden-nonexistence-contradiction-partial"
    elif front_status != "golden-nonexistence-front-failed":
        contradiction_status = "golden-nonexistence-contradiction-fragile"
    else:
        contradiction_status = "golden-nonexistence-contradiction-failed"

    return {
        "theorem_bridge_status": theorem_bridge_status,
        "strict_bridge_status": strict_bridge_status,
        "support_core_status": support_core_status,
        "tail_aware_status": tail_aware_status,
        "tail_stability_status": tail_stability_status,
        "bridge_profile_status": bridge_profile_status,
        "support_core_selected_status": support_core_selected_status,
        "tail_aware_selected_status": tail_aware_selected_status,
        "supercritical_obstruction_locked": bool(supercritical_obstruction_locked),
        "strict_bridge_certified": bool(strict_bridge_certified),
        "support_geometry_certified": bool(support_geometry_certified),
        "tail_coherence_certified": bool(tail_coherence_certified),
        "tail_stability_certified": bool(tail_stability_certified),
        "positive_window_separation": bool(positive_window_separation),
        "nonexistence_contradiction_certified": bool(nonexistence_contradiction_certified),
        "contradiction_margin": contradiction_margin,
        "theorem_status": contradiction_status,
        "residual_burden": residual_burden,
    }


def build_golden_nonexistence_front_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    lower_shift_grid: Sequence[float] = (-0.015, 0.0, 0.015),
    lower_resolution_sets: Sequence[Sequence[int]] = ((64, 96, 128), (80, 112, 144)),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    lower_min_cluster_size: int = 2,
    lower_neighborhood_stability_certificate: Mapping[str, Any] | None = None,
    upper_tail_coherence_certificate: Mapping[str, Any] | None = None,
    upper_bridge_certificate: Mapping[str, Any] | None = None,
    upper_bridge_promotion_certificate: Mapping[str, Any] | None = None,
    upper_support_core_neighborhood_certificate: Mapping[str, Any] | None = None,
    upper_tail_aware_neighborhood_certificate: Mapping[str, Any] | None = None,
    upper_tail_stability_certificate: Mapping[str, Any] | None = None,
    upper_bridge_profile_certificate: Mapping[str, Any] | None = None,
    min_tail_members: int = 2,
    min_clearance_ratio: float = 1.0,
    require_suffix_tail: bool = False,
    **upper_kwargs,
) -> GoldenNonexistenceFrontCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)

    if lower_neighborhood_stability_certificate is not None:
        lower = dict(lower_neighborhood_stability_certificate)
    else:
        lower = build_golden_lower_neighborhood_stability_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            shift_grid=lower_shift_grid,
            resolution_sets=lower_resolution_sets,
            sigma_cap=sigma_cap,
            use_multiresolution=use_multiresolution,
            oversample_factor=oversample_factor,
            min_cluster_size=lower_min_cluster_size,
        ).to_dict()
    profile_requested = bool(upper_kwargs.get('force_bridge_profile', False))
    direct_upper_kwargs = dict(upper_kwargs)
    direct_upper_kwargs.pop('force_bridge_profile', None)
    bridge_upper_kwargs = dict(direct_upper_kwargs)
    neighborhood_upper_kwargs = dict(direct_upper_kwargs)
    bridge_profile_upper_kwargs = dict(direct_upper_kwargs)
    if upper_tail_coherence_certificate is not None:
        bridge_upper_kwargs.setdefault('adaptive_tail_coherence_certificate', upper_tail_coherence_certificate)
        bridge_profile_upper_kwargs.setdefault('adaptive_tail_coherence_certificate', upper_tail_coherence_certificate)
        neighborhood_upper_kwargs.setdefault('baseline_tail_coherence_certificate', upper_tail_coherence_certificate)
    if upper_support_core_neighborhood_certificate is not None:
        neighborhood_upper_kwargs.setdefault('support_core_neighborhood_certificate', upper_support_core_neighborhood_certificate)

    if upper_bridge_certificate is not None:
        upper = dict(upper_bridge_certificate)
    else:
        upper = build_golden_incompatibility_theorem_bridge_certificate(
            family=family,
            rho=rho,
            min_tail_members=min_tail_members,
            require_suffix_tail=require_suffix_tail,
            **bridge_upper_kwargs,
        ).to_dict()
    upper_bridge_promotion: dict[str, Any] = {}
    if upper_bridge_promotion_certificate is not None:
        upper_bridge_promotion = dict(upper_bridge_promotion_certificate)
        if _status_rank(str(upper_bridge_promotion.get('theorem_status', ''))) > _status_rank(str(upper.get('theorem_status', ''))):
            upper = dict(upper_bridge_promotion)
    elif _status_rank(str(upper.get('theorem_status', ''))) <= 2 or bool(upper_kwargs.get('force_strict_bridge_promotion', False)):
        upper_bridge_promotion = build_golden_incompatibility_strict_bridge_certificate(
            family=family,
            rho=rho,
            min_tail_members=min_tail_members,
            require_suffix_tail=require_suffix_tail,
            **bridge_upper_kwargs,
        ).to_dict()
        if _status_rank(str(upper_bridge_promotion.get('theorem_status', ''))) > _status_rank(str(upper.get('theorem_status', ''))):
            upper = dict(upper_bridge_promotion)
    upper_support_core_neighborhood: dict[str, Any] = {}
    if upper_support_core_neighborhood_certificate is not None:
        upper_support_core_neighborhood = dict(upper_support_core_neighborhood_certificate)
        candidate_upper = dict(upper_support_core_neighborhood.get('selected_bridge', {}) or {})
        if _status_rank(str(candidate_upper.get('theorem_status', ''))) > _status_rank(str(upper.get('theorem_status', ''))):
            upper = candidate_upper
    elif _status_rank(str(upper.get('theorem_status', ''))) <= 2 or bool(upper_kwargs.get('force_support_core_neighborhood', False)):
        upper_support_core_neighborhood = build_golden_adaptive_support_core_neighborhood_certificate(
            family=family,
            rho=rho,
            min_tail_members=min_tail_members,
            require_suffix_tail=require_suffix_tail,
            **neighborhood_upper_kwargs,
        ).to_dict()
        candidate_upper = dict(upper_support_core_neighborhood.get('selected_bridge', {}) or {})
        if _status_rank(str(candidate_upper.get('theorem_status', ''))) > _status_rank(str(upper.get('theorem_status', ''))):
            upper = candidate_upper
    upper_tail_aware_neighborhood: dict[str, Any] = {}
    if upper_tail_aware_neighborhood_certificate is not None:
        upper_tail_aware_neighborhood = dict(upper_tail_aware_neighborhood_certificate)
        candidate_upper = dict(upper_tail_aware_neighborhood.get('selected_bridge', {}) or {})
        if _status_rank(str(candidate_upper.get('theorem_status', ''))) > _status_rank(str(upper.get('theorem_status', ''))):
            upper = candidate_upper
    elif _status_rank(str(upper.get('theorem_status', ''))) <= 2 or bool(upper_kwargs.get('force_tail_aware_neighborhood', False)):
        upper_tail_aware_neighborhood = build_golden_adaptive_tail_aware_neighborhood_certificate(
            family=family,
            rho=rho,
            min_tail_members=min_tail_members,
            require_suffix_tail=require_suffix_tail,
            **neighborhood_upper_kwargs,
        ).to_dict()
        candidate_upper = dict(upper_tail_aware_neighborhood.get('selected_bridge', {}) or {})
        if _status_rank(str(candidate_upper.get('theorem_status', ''))) > _status_rank(str(upper.get('theorem_status', ''))):
            upper = candidate_upper
    upper_tail_stability: dict[str, Any] = {}
    if upper_tail_stability_certificate is not None:
        upper_tail_stability = dict(upper_tail_stability_certificate)
    elif (
        _status_rank(str(upper.get('theorem_status', ''))) <= 3
        or bool(upper_kwargs.get('force_tail_stability', False))
        or bool(upper_kwargs.get('force_analytic_contradiction', False))
    ):
        upper_tail_stability = build_golden_adaptive_tail_stability_certificate(
            family=family,
            rho=rho,
            min_stable_tail_members=min_tail_members,
            **direct_upper_kwargs,
        ).to_dict()
    upper_bridge_profile: dict[str, Any] = {}
    if upper_bridge_profile_certificate is not None:
        upper_bridge_profile = dict(upper_bridge_profile_certificate)
        candidate_upper = dict(upper_bridge_profile.get('selected_bridge', {}) or {})
        if _status_rank(str(candidate_upper.get('theorem_status', ''))) > _status_rank(str(upper.get('theorem_status', ''))):
            upper = candidate_upper
    elif _status_rank(str(upper.get('theorem_status', ''))) <= 2 or profile_requested:
        upper_bridge_profile = build_golden_incompatibility_bridge_profile_certificate(
            family=family,
            rho=rho,
            min_tail_members=min_tail_members,
            require_suffix_tail=require_suffix_tail,
            **bridge_profile_upper_kwargs,
        ).to_dict()
        candidate_upper = dict(upper_bridge_profile.get('selected_bridge', {}) or {})
        if _status_rank(str(candidate_upper.get('theorem_status', ''))) > _status_rank(str(upper.get('theorem_status', ''))):
            upper = candidate_upper

    lower_bound = lower.get("stable_lower_bound")
    lower_hi = lower.get("stable_window_hi")
    lower_width = lower.get("stable_window_width")
    lower_status = str(lower.get("theorem_status", "unknown"))

    upper_lo = upper.get("certified_upper_lo")
    upper_hi = upper.get("certified_upper_hi")
    upper_width = upper.get("certified_upper_width")
    barrier_lo = upper.get("certified_barrier_lo")
    barrier_hi = upper.get("certified_barrier_hi")
    barrier_width = upper.get("certified_barrier_width")
    upper_status = str(upper.get("theorem_status", "unknown"))
    bridge_margin = upper.get("bridge_margin")
    tail_qs = [int(x) for x in upper.get("certified_tail_qs", [])]
    tail_is_suffix = bool(upper.get("certified_tail_is_suffix", False))
    upper_missing = [str(x) for x in upper.get("missing_hypotheses", [])]

    gap_to_upper = None if lower_bound is None or upper_lo is None else float(float(upper_lo) - float(lower_bound))
    gap_to_upper_window = None if lower_hi is None or upper_lo is None else float(float(upper_lo) - float(lower_hi))
    gap_to_barrier = None if lower_bound is None or barrier_lo is None else float(float(barrier_lo) - float(lower_bound))
    gap_to_barrier_window = None if lower_hi is None or barrier_lo is None else float(float(barrier_lo) - float(lower_hi))

    clearance_scale = max(
        1e-12,
        float(lower_width or 0.0),
        float(upper_width or 0.0),
    )
    clearance_ratio = None if gap_to_upper is None else float(gap_to_upper / clearance_scale)

    lower_strong_or_moderate = lower_status in {
        "golden-lower-neighborhood-stability-strong",
        "golden-lower-neighborhood-stability-moderate",
    }
    cross_resolution_count = len(lower.get("distinct_resolution_signatures", []))
    supporting_entry_count = int(upper.get("supporting_entry_count", 0))
    support_fraction = upper.get("support_fraction_floor")
    entry_coverage_floor = upper.get("entry_coverage_floor")

    relation = {
        "lower_status": lower_status,
        "upper_status": upper_status,
        "lower_bound": None if lower_bound is None else float(lower_bound),
        "lower_window_hi": None if lower_hi is None else float(lower_hi),
        "lower_window_width": None if lower_width is None else float(lower_width),
        "upper_crossing_lo": None if upper_lo is None else float(upper_lo),
        "upper_crossing_hi": None if upper_hi is None else float(upper_hi),
        "upper_crossing_width": None if upper_width is None else float(upper_width),
        "upper_barrier_lo": None if barrier_lo is None else float(barrier_lo),
        "upper_barrier_hi": None if barrier_hi is None else float(barrier_hi),
        "upper_barrier_width": None if barrier_width is None else float(barrier_width),
        "gap_to_upper": gap_to_upper,
        "gap_to_upper_window": gap_to_upper_window,
        "gap_to_barrier": gap_to_barrier,
        "gap_to_barrier_window": gap_to_barrier_window,
        "clearance_ratio": clearance_ratio,
        "bridge_margin": bridge_margin,
        "tail_qs": [int(x) for x in tail_qs],
        "tail_is_suffix": bool(tail_is_suffix),
        "supporting_entry_count": int(supporting_entry_count),
        "support_fraction_floor": None if support_fraction is None else float(support_fraction),
        "entry_coverage_floor": None if entry_coverage_floor is None else float(entry_coverage_floor),
        "upper_missing_hypotheses": [str(x) for x in upper_missing],
        "upper_promotion_status": str(upper_bridge_promotion.get("theorem_status", "not-built")),
        "upper_support_core_neighborhood_status": str(upper_support_core_neighborhood.get("theorem_status", "not-built")),
        "upper_support_core_selected_status": str((upper_support_core_neighborhood.get("selected_bridge", {}) or {}).get("theorem_status", "not-built")),
        "upper_tail_aware_neighborhood_status": str(upper_tail_aware_neighborhood.get("theorem_status", "not-built")),
        "upper_tail_aware_selected_status": str((upper_tail_aware_neighborhood.get("selected_bridge", {}) or {}).get("theorem_status", "not-built")),
        "upper_tail_stability_status": str(upper_tail_stability.get("theorem_status", "not-built")),
        "upper_tail_stability_gap": None if upper_tail_stability.get("stable_incompatibility_gap") is None else float(upper_tail_stability.get("stable_incompatibility_gap")),
        "upper_profile_status": str(upper_bridge_profile.get("theorem_status", "not-built")),
        "upper_profile_selected_name": str(upper_bridge_profile.get("selected_profile_name", "none")),
        "upper_profile_viable_profile_count": int(upper_bridge_profile.get("viable_profile_count", 0)),
        "upper_profile_strong_profile_count": int(upper_bridge_profile.get("strong_profile_count", 0)),
    }

    hypotheses = [
        NonexistenceFrontHypothesisRow(
            "stable_lower_object",
            lower_strong_or_moderate,
            float(cross_resolution_count - 2),
            "lower-neighborhood-stability",
            "A coherent lower-side golden persistence object survives across neighboring continuation grids and at least moderate resolution support.",
        ),
        NonexistenceFrontHypothesisRow(
            "cross_resolution_lower_support",
            cross_resolution_count >= 2,
            float(cross_resolution_count - 2),
            "lower-neighborhood-stability",
            "The lower-side object is not tied to a single resolution signature.",
        ),
        NonexistenceFrontHypothesisRow(
            "upper_bridge_closed",
            upper_status == "golden-incompatibility-theorem-bridge-strong",
            None if bridge_margin is None else float(bridge_margin),
            "incompatibility-theorem-bridge",
            "The strongest current upper obstruction package closes as an explicit theorem-facing bridge.",
        ),
        NonexistenceFrontHypothesisRow(
            "lower_to_upper_separation",
            gap_to_upper is not None and gap_to_upper > 0.0,
            gap_to_upper,
            "lower-vs-upper",
            "The stable lower persistence anchor lies strictly below the certified upper crossing onset.",
        ),
        NonexistenceFrontHypothesisRow(
            "window_to_window_separation",
            gap_to_upper_window is not None and gap_to_upper_window > 0.0,
            gap_to_upper_window,
            "lower-vs-upper",
            "The full lower stability window lies strictly below the certified upper crossing onset.",
        ),
        NonexistenceFrontHypothesisRow(
            "clearance_dominates_widths",
            clearance_ratio is not None and clearance_ratio >= float(min_clearance_ratio),
            None if clearance_ratio is None else float(clearance_ratio - float(min_clearance_ratio)),
            "lower-vs-upper",
            "The lower-to-upper clearance is not merely positive; it dominates the current localization widths.",
        ),
        NonexistenceFrontHypothesisRow(
            "barrier_separation",
            gap_to_barrier is not None and gap_to_barrier > 0.0,
            gap_to_barrier,
            "lower-vs-barrier",
            "The stable lower persistence anchor lies strictly below the coherent hyperbolic barrier.",
        ),
        NonexistenceFrontHypothesisRow(
            "upper_tail_supported",
            bool(tail_qs),
            float(len(tail_qs)) if tail_qs else None,
            "incompatibility-theorem-bridge",
            "A denominator block/tail currently supports the upper obstruction bridge.",
        ),
        NonexistenceFrontHypothesisRow(
            "upper_tail_suffix",
            (not require_suffix_tail) or tail_is_suffix,
            1.0 if tail_is_suffix else 0.0,
            "incompatibility-theorem-bridge",
            "Suffix stability is recorded for the supporting denominator block when required.",
        ),
    ]

    satisfied = [row.name for row in hypotheses if row.satisfied]
    missing = [row.name for row in hypotheses if not row.satisfied]
    margin_candidates = [
        gap_to_upper,
        gap_to_upper_window,
        gap_to_barrier,
        None if clearance_ratio is None else float(clearance_ratio - float(min_clearance_ratio)),
        float(cross_resolution_count - 2),
        float(len(tail_qs) - int(min_tail_members)) if tail_qs else None,
        None if bridge_margin is None else float(bridge_margin),
    ]
    if require_suffix_tail:
        margin_candidates.append(1.0 if tail_is_suffix else -1.0)
    finite = [float(x) for x in margin_candidates if x is not None]
    front_margin = min(finite) if finite else None

    remaining_analytic_lifts = _default_remaining_analytic_lifts()
    contradiction_summary = _build_contradiction_summary(
        relation=relation,
        front_status='golden-nonexistence-front-strong' if all(row.satisfied for row in hypotheses) else ('golden-nonexistence-front-moderate' if (lower_bound is not None and upper_lo is not None and gap_to_upper is not None and gap_to_upper > 0.0 and barrier_lo is not None and gap_to_barrier is not None and gap_to_barrier > 0.0) else ('golden-nonexistence-front-weak' if (lower_bound is not None and upper_lo is not None and gap_to_upper is not None and gap_to_upper > 0.0) else ('golden-nonexistence-front-fragile' if (lower_bound is not None or upper_lo is not None) else 'golden-nonexistence-front-failed'))),
        front_margin=front_margin,
        upper=upper,
        upper_bridge_promotion=upper_bridge_promotion,
        upper_support_core_neighborhood=upper_support_core_neighborhood,
        upper_tail_aware_neighborhood=upper_tail_aware_neighborhood,
        upper_tail_stability=upper_tail_stability,
        upper_bridge_profile=upper_bridge_profile,
    )

    if all(row.satisfied for row in hypotheses):
        status = "golden-nonexistence-front-strong"
        notes = "The current code now closes a sharp two-sided nonexistence front: a neighborhood-stable lower golden persistence object sits strictly below an explicit upper incompatibility theorem bridge with quantitative clearance. The remaining gap is no longer front assembly but the final analytic lifts recorded separately."
    elif (
        lower_bound is not None
        and upper_lo is not None
        and gap_to_upper is not None
        and gap_to_upper > 0.0
        and barrier_lo is not None
        and gap_to_barrier is not None
        and gap_to_barrier > 0.0
    ):
        status = "golden-nonexistence-front-moderate"
        notes = "The current code has a genuine two-sided nonexistence front with positive separation, but either the lower neighborhood support or the upper theorem bridge is still missing a stronger stability condition."
    elif lower_bound is not None and upper_lo is not None and gap_to_upper is not None and gap_to_upper > 0.0:
        status = "golden-nonexistence-front-weak"
        notes = "The current lower and upper fronts separate, but the two-sided package is still too fragile to count as a sharp nonexistence front."
    elif lower_bound is not None or upper_lo is not None:
        status = "golden-nonexistence-front-fragile"
        notes = "Only one side of the intended nonexistence front is currently well enough localized to compare honestly."
    else:
        status = "golden-nonexistence-front-failed"
        notes = "The current certificates do not yet assemble into a usable two-sided nonexistence front."

    contradiction_summary['front_status'] = status

    return GoldenNonexistenceFrontCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_bridge=upper,
        upper_bridge_promotion=upper_bridge_promotion,
        upper_support_core_neighborhood=upper_support_core_neighborhood,
        upper_tail_aware_neighborhood=upper_tail_aware_neighborhood,
        upper_tail_stability=upper_tail_stability,
        upper_bridge_profile=upper_bridge_profile,
        relation=relation,
        contradiction_summary=contradiction_summary,
        hypotheses=hypotheses,
        satisfied_hypotheses=satisfied,
        missing_hypotheses=missing,
        computational_front_margin=front_margin,
        remaining_analytic_lifts=remaining_analytic_lifts,
        theorem_status=status,
        notes=notes,
    )


__all__ = [
    "NonexistenceFrontHypothesisRow",
    "AnalyticLiftRow",
    "GoldenNonexistenceFrontCertificate",
    "build_golden_nonexistence_front_certificate",
]
