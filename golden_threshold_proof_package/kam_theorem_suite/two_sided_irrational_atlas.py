from __future__ import annotations

"""Two-sided irrational threshold atlas builders.

This module is the next step after the multiresolution irrational existence
atlas and the rational obstruction atlas.  It still does **not** claim a full
irrational nonexistence theorem.  What it does provide is a more theorem-facing
"two-sided corridor" object built from:

1. a multiresolution continuation atlas on the irrational existence side, and
2. a multi-approximant rational ladder of local crossing certificates plus
   later hyperbolic bands on the obstruction side.

The output is designed to answer a sharper question than the earlier bridge
reports: *how coherent is the current upper-side obstruction evidence across a
whole approximant ladder, and how cleanly does it separate from the strongest
implemented lower-side existence evidence?*
"""

from dataclasses import asdict, dataclass
from fractions import Fraction
from statistics import median
from typing import Any, Sequence

from .irrational_existence_atlas import continue_invariant_circle_multiresolution
from .obstruction_atlas import ApproximantWindowSpec, build_approximant_atlas_entry
from .standard_map import HarmonicFamily
from .upper_ladder_refinement import refine_rational_upper_ladder
from .asymptotic_upper_ladder_audit import audit_refined_upper_ladder_asymptotics


@dataclass
class RationalUpperLadderEntry:
    p: int
    q: int
    label: str
    rho: float
    rho_error: float
    crossing_root_window_lo: float | None
    crossing_root_window_hi: float | None
    crossing_root_window_width: float | None
    crossing_center: float | None
    hyperbolic_band_lo: float | None
    hyperbolic_band_hi: float | None
    hyperbolic_band_width: float | None
    first_supercritical_gap: float | None
    status: str
    bridge_report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RationalUpperLadderReport:
    rho_target: float
    family_label: str
    approximants: list[dict[str, Any]]
    successful_crossing_count: int
    successful_band_count: int
    best_crossing_lower_bound: float | None
    best_crossing_upper_bound: float | None
    crossing_union_lo: float | None
    crossing_union_hi: float | None
    crossing_union_width: float | None
    crossing_intersection_lo: float | None
    crossing_intersection_hi: float | None
    crossing_intersection_width: float | None
    crossing_center_median: float | None
    earliest_band_lo: float | None
    latest_band_hi: float | None
    band_union_width: float | None
    ladder_quality: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TwoSidedIrrationalThresholdAtlas:
    rho: float
    family_label: str
    quality_floor: str
    target_residue: float
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_QUALITY_ORDER = {"failed": 0, "weak": 1, "moderate": 2, "strong": 3}


def _fraction_rho(p: int, q: int) -> float:
    return float(Fraction(int(p), int(q)))


def _crossing_center(lo: float | None, hi: float | None) -> float | None:
    if lo is None or hi is None:
        return None
    return 0.5 * (float(lo) + float(hi))


def _ladder_quality(successful_crossings: int, successful_bands: int, has_intersection: bool) -> str:
    if successful_crossings >= 3 and successful_bands >= 2 and has_intersection:
        return "strong"
    if successful_crossings >= 2 and successful_bands >= 1:
        return "moderate"
    if successful_crossings >= 1:
        return "weak"
    return "failed"


def build_rational_upper_ladder(
    rho: float,
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
) -> RationalUpperLadderReport:
    """Build a multi-approximant upper-side ladder near a target irrational.

    Each approximant contributes a local crossing certificate and, when
    available, a later sustained hyperbolic band.  The ladder aggregates these
    entries into union/intersection summaries that are more informative than a
    single approximant window.
    """
    family = family or HarmonicFamily()
    entries: list[RationalUpperLadderEntry] = []
    crossing_los: list[float] = []
    crossing_his: list[float] = []
    crossing_centers: list[float] = []
    band_los: list[float] = []
    band_his: list[float] = []

    specs_sorted = sorted(list(specs), key=lambda s: (s.q, s.p))
    for spec in specs_sorted:
        entry = build_approximant_atlas_entry(
            spec,
            family=family,
            target_residue=target_residue,
            auto_localize_crossing=auto_localize_crossing,
            initial_subdivisions=initial_subdivisions,
            max_depth=max_depth,
            min_width=min_width,
        )
        center = _crossing_center(entry.crossing_root_window_lo, entry.crossing_root_window_hi)
        out = RationalUpperLadderEntry(
            p=int(entry.p),
            q=int(entry.q),
            label=str(entry.label),
            rho=float(entry.rho),
            rho_error=float(abs(entry.rho - float(rho))),
            crossing_root_window_lo=None if entry.crossing_root_window_lo is None else float(entry.crossing_root_window_lo),
            crossing_root_window_hi=None if entry.crossing_root_window_hi is None else float(entry.crossing_root_window_hi),
            crossing_root_window_width=None if entry.crossing_root_window_width is None else float(entry.crossing_root_window_width),
            crossing_center=None if center is None else float(center),
            hyperbolic_band_lo=None if entry.hyperbolic_band_lo is None else float(entry.hyperbolic_band_lo),
            hyperbolic_band_hi=None if entry.hyperbolic_band_hi is None else float(entry.hyperbolic_band_hi),
            hyperbolic_band_width=None if entry.hyperbolic_band_lo is None or entry.hyperbolic_band_hi is None else float(entry.hyperbolic_band_hi - entry.hyperbolic_band_lo),
            first_supercritical_gap=None if entry.gap_from_crossing_to_band is None else float(entry.gap_from_crossing_to_band),
            status=str(entry.status),
            bridge_report=dict(entry.bridge_report),
        )
        entries.append(out)
        if out.crossing_root_window_lo is not None and out.crossing_root_window_hi is not None:
            crossing_los.append(float(out.crossing_root_window_lo))
            crossing_his.append(float(out.crossing_root_window_hi))
            if out.crossing_center is not None:
                crossing_centers.append(float(out.crossing_center))
        if out.hyperbolic_band_lo is not None and out.hyperbolic_band_hi is not None:
            band_los.append(float(out.hyperbolic_band_lo))
            band_his.append(float(out.hyperbolic_band_hi))

    crossing_union_lo = min(crossing_los) if crossing_los else None
    crossing_union_hi = max(crossing_his) if crossing_his else None
    crossing_union_width = None if crossing_union_lo is None or crossing_union_hi is None else float(crossing_union_hi - crossing_union_lo)
    crossing_intersection_lo = max(crossing_los) if crossing_los else None
    crossing_intersection_hi = min(crossing_his) if crossing_his else None
    if crossing_intersection_lo is not None and crossing_intersection_hi is not None and crossing_intersection_hi >= crossing_intersection_lo:
        crossing_intersection_width = float(crossing_intersection_hi - crossing_intersection_lo)
    else:
        crossing_intersection_lo = None
        crossing_intersection_hi = None
        crossing_intersection_width = None
    crossing_center_median = float(median(crossing_centers)) if crossing_centers else None
    earliest_band_lo = min(band_los) if band_los else None
    latest_band_hi = max(band_his) if band_his else None
    band_union_width = None if earliest_band_lo is None or latest_band_hi is None else float(latest_band_hi - earliest_band_lo)

    successful_crossings = len(crossing_los)
    successful_bands = len(band_los)
    quality = _ladder_quality(successful_crossings, successful_bands, crossing_intersection_width is not None)
    if crossing_intersection_width is not None:
        best_lo = float(crossing_intersection_lo)
        best_hi = float(crossing_intersection_hi)
        note_core = "upper-side cluster intersection available"
    else:
        best_lo = crossing_union_lo
        best_hi = crossing_union_hi
        note_core = "upper-side cluster intersection not available; falling back to crossing union"
    notes = (
        f"Rational upper ladder only. {note_core}. This is not yet an irrational nonexistence theorem; "
        "it is a coherent upper-side obstruction summary across several approximants."
    )
    return RationalUpperLadderReport(
        rho_target=float(rho),
        family_label=type(family).__name__,
        approximants=[e.to_dict() for e in entries],
        successful_crossing_count=int(successful_crossings),
        successful_band_count=int(successful_bands),
        best_crossing_lower_bound=best_lo,
        best_crossing_upper_bound=best_hi,
        crossing_union_lo=crossing_union_lo,
        crossing_union_hi=crossing_union_hi,
        crossing_union_width=crossing_union_width,
        crossing_intersection_lo=crossing_intersection_lo,
        crossing_intersection_hi=crossing_intersection_hi,
        crossing_intersection_width=crossing_intersection_width,
        crossing_center_median=crossing_center_median,
        earliest_band_lo=earliest_band_lo,
        latest_band_hi=latest_band_hi,
        band_union_width=band_union_width,
        ladder_quality=quality,
        notes=notes,
    )


def _extract_lower_bound(multires_report: dict[str, Any]) -> float | None:
    value = multires_report.get("last_stable_K")
    if value is not None:
        return float(value)
    bracket = multires_report.get("stable_threshold_bracket")
    if isinstance(bracket, (list, tuple)) and len(bracket) == 2 and bracket[0] is not None:
        return float(bracket[0])
    return None


def build_two_sided_irrational_threshold_atlas(
    rho: float,
    K_values: Sequence[float],
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    N_values: Sequence[int] = (64, 96, 128),
    quality_floor: str = "moderate",
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    refinement_base_tol: float = 2.5e-4,
    refinement_q2_scale: float = 0.1,
    refinement_min_subset: int = 2,
    audit_upper_ladder_asymptotics: bool = True,
    asymptotic_min_members: int = 2,
    asymptotic_center_drift_tol: float = 5e-4,
) -> TwoSidedIrrationalThresholdAtlas:
    """Combine the best implemented lower and upper objects into one report."""
    family = family or HarmonicFamily()
    lower = continue_invariant_circle_multiresolution(
        rho=rho,
        K_values=K_values,
        family=family,
        N_values=N_values,
        quality_floor=quality_floor,
    ).to_dict()
    upper = build_rational_upper_ladder(
        rho=rho,
        specs=specs,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()
    refined_upper = None
    if refine_upper_ladder:
        refined_upper = refine_rational_upper_ladder(
            upper,
            base_tol=refinement_base_tol,
            q2_scale=refinement_q2_scale,
            min_subset=refinement_min_subset,
        ).to_dict()
    asymptotic_audit = None
    if audit_upper_ladder_asymptotics:
        audit_input = refined_upper if refined_upper is not None else upper
        asymptotic_audit = audit_refined_upper_ladder_asymptotics(
            upper,
            min_members=asymptotic_min_members,
            base_tol=refinement_base_tol,
            q2_scale=refinement_q2_scale,
            min_subset=refinement_min_subset,
            center_drift_tol=asymptotic_center_drift_tol,
        ).to_dict()

    lower_bound = _extract_lower_bound(lower)
    if asymptotic_audit is not None and asymptotic_audit.get("audited_upper_lo") is not None:
        upper_lo = asymptotic_audit.get("audited_upper_lo")
        upper_hi = asymptotic_audit.get("audited_upper_hi")
        upper_source = "asymptotic-upper-ladder"
    elif refined_upper is not None and refined_upper.get("best_refined_crossing_lower_bound") is not None:
        upper_lo = refined_upper.get("best_refined_crossing_lower_bound")
        upper_hi = refined_upper.get("best_refined_crossing_upper_bound")
        upper_source = "refined-upper-ladder"
    else:
        upper_lo = upper.get("best_crossing_lower_bound")
        upper_hi = upper.get("best_crossing_upper_bound")
        upper_source = "raw-upper-ladder"
    earliest_band_lo = upper.get("earliest_band_lo")
    gap_to_upper = None if lower_bound is None or upper_lo is None else float(upper_lo - lower_bound)
    gap_to_band = None if lower_bound is None or earliest_band_lo is None else float(earliest_band_lo - lower_bound)

    stable_prefix_len = int(lower.get("stable_prefix_len", 0))
    ladder_quality = str(upper.get("ladder_quality", "failed"))
    has_upper_cluster = upper.get("crossing_intersection_width") is not None
    has_band = upper.get("successful_band_count", 0) > 0
    has_refined_cluster = refined_upper is not None and refined_upper.get("selected_cluster_index") is not None
    has_asymptotic_audit = asymptotic_audit is not None and asymptotic_audit.get("audited_upper_lo") is not None

    if lower_bound is not None and upper_lo is not None and gap_to_upper is not None and gap_to_upper > 0.0:
        if has_asymptotic_audit and has_band and ladder_quality in {"strong", "moderate"}:
            status = "two-sided-asymptotic-corridor"
        elif has_refined_cluster and has_band and ladder_quality in {"strong", "moderate"}:
            status = "two-sided-refined-corridor"
        elif has_upper_cluster and has_band and ladder_quality in {"strong", "moderate"}:
            status = "two-sided-clustered-corridor"
        elif has_band:
            status = "two-sided-corridor-with-band"
        else:
            status = "two-sided-corridor"
    elif lower_bound is not None and upper_lo is not None:
        status = "overlapping-two-sided-evidence"
    elif lower_bound is not None:
        status = "lower-side-only"
    elif upper_lo is not None:
        status = "upper-side-only"
    else:
        status = "incomplete"

    relation = {
        "lower_bound_K": lower_bound,
        "upper_object_lo": upper_lo,
        "upper_object_hi": upper_hi,
        "earliest_band_lo": earliest_band_lo,
        "gap_lower_to_upper": gap_to_upper,
        "gap_lower_to_band": gap_to_band,
        "stable_prefix_len": stable_prefix_len,
        "ladder_quality": ladder_quality,
        "has_upper_cluster": bool(has_upper_cluster),
        "has_refined_cluster": bool(has_refined_cluster),
        "has_asymptotic_audit": bool(has_asymptotic_audit),
        "has_band": bool(has_band),
        "upper_object_source": upper_source,
        "status": status,
        # backward/inspection-friendly aliases
        "lower_vs_upper_gap": gap_to_upper,
        "lower_vs_band_gap": gap_to_band,
        "upper_cluster_available": bool(has_upper_cluster),
        "refined_cluster_available": bool(has_refined_cluster),
        "asymptotic_audit_available": bool(has_asymptotic_audit),
    }
    notes = (
        "Two-sided irrational corridor only. The lower side comes from the multiresolution collocation-based "
        f"existence atlas at quality floor '{quality_floor}', while the upper side comes from a rational obstruction ladder. "
        "This is a stronger bridge object than the earlier one-approximant corridor, but it is still not a full irrational nonexistence theorem."
    )
    return TwoSidedIrrationalThresholdAtlas(
        rho=float(rho),
        family_label=type(family).__name__,
        quality_floor=str(quality_floor),
        target_residue=float(target_residue),
        lower_side=lower,
        upper_side={**upper, "refined_cluster": refined_upper, "asymptotic_audit": asymptotic_audit},
        relation=relation,
        notes=notes,
    )
