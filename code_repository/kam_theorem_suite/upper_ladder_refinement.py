from __future__ import annotations

"""Refinement tools for rational upper ladders.

This module strengthens the upper-side object used by the two-sided irrational
corridor machinery.  The previous stage aggregated rational crossings using a
plain union/intersection summary.  That was honest but too coarse: a single
outlying low-denominator approximant could destroy the intersection even when a
higher-denominator subfamily was clearly coherent.

The present layer adds two theorem-facing ideas:

1. **crossing-cluster refinement**: successful crossing windows are grouped into
   consistency clusters using overlap and denominator-aware center agreement;
2. **denominator-aware consistency checks**: inside each cluster we measure how
   well the crossing centers stabilize against the asymptotic variable
   ``x = 1/q^2`` and whether a high-denominator overlapping subcluster exists.

The output is still not a proof of irrational nonexistence.  What it *does*
produce is a more structured upper-side object that can be consumed by the
irrational corridor reports without relying solely on raw union/intersection
bookkeeping.
"""

from dataclasses import asdict, dataclass
from itertools import combinations
from statistics import median
from typing import Any, Iterable, Sequence


@dataclass
class RefinedCrossingCluster:
    cluster_id: int
    member_labels: list[str]
    member_qs: list[int]
    member_centers: list[float]
    member_widths: list[float]
    member_count: int
    q_min: int
    q_max: int
    pairwise_consistency_fraction: float
    fit_intercept: float | None
    fit_slope: float | None
    fit_max_abs_residual: float | None
    fit_rms_residual: float | None
    fit_residual_scaled_by_q2: float | None
    width_nonincreasing_fraction: float | None
    raw_intersection_lo: float | None
    raw_intersection_hi: float | None
    raw_intersection_width: float | None
    refined_subset_labels: list[str]
    refined_subset_qs: list[int]
    refined_lo: float | None
    refined_hi: float | None
    refined_width: float | None
    denominator_consistency_status: str
    refinement_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RefinedRationalUpperLadderReport:
    raw_ladder_quality: str
    raw_successful_crossing_count: int
    clusters: list[dict[str, Any]]
    selected_cluster_index: int | None
    selected_cluster_status: str
    selected_cluster_member_labels: list[str]
    selected_cluster_member_qs: list[int]
    best_refined_crossing_lower_bound: float | None
    best_refined_crossing_upper_bound: float | None
    best_refined_crossing_width: float | None
    raw_best_crossing_lower_bound: float | None
    raw_best_crossing_upper_bound: float | None
    raw_best_crossing_width: float | None
    refinement_improved_width: float | None
    refinement_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # a few aliases make the notebook/report side more convenient and also
        # soften schema drift between stages.
        d["best_crossing_lower_bound"] = d["best_refined_crossing_lower_bound"]
        d["best_crossing_upper_bound"] = d["best_refined_crossing_upper_bound"]
        d["best_crossing_width"] = d["best_refined_crossing_width"]
        d["status"] = d["refinement_status"]
        return d


def _extract_crossing_entries(ladder: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in ladder.get("approximants", []):
        lo = entry.get("crossing_root_window_lo")
        hi = entry.get("crossing_root_window_hi")
        q = entry.get("q")
        if lo is None or hi is None or q in (None, 0):
            continue
        lo = float(lo)
        hi = float(hi)
        center = entry.get("crossing_center")
        if center is None:
            center = 0.5 * (lo + hi)
        width = entry.get("crossing_root_window_width")
        if width is None:
            width = hi - lo
        entries.append(
            {
                "label": str(entry.get("label", f"{entry.get('p')}/{entry.get('q')}")),
                "p": int(entry.get("p", 0)),
                "q": int(q),
                "lo": lo,
                "hi": hi,
                "center": float(center),
                "width": float(width),
                "status": str(entry.get("status", "unknown")),
            }
        )
    return sorted(entries, key=lambda e: (e["q"], e["p"], e["center"]))


def _consistency_tolerance(qi: int, qj: int, *, base_tol: float, q2_scale: float) -> float:
    return float(base_tol + q2_scale * ((1.0 / (qi * qi)) + (1.0 / (qj * qj))))


def _entries_consistent(a: dict[str, Any], b: dict[str, Any], *, base_tol: float, q2_scale: float) -> bool:
    # strongest signal: actual overlap of the certified windows.
    if min(a["hi"], b["hi"]) >= max(a["lo"], b["lo"]):
        return True
    tol = _consistency_tolerance(a["q"], b["q"], base_tol=base_tol, q2_scale=q2_scale)
    center_gap = abs(float(a["center"]) - float(b["center"]))
    interval_gap = max(0.0, max(a["lo"], b["lo"]) - min(a["hi"], b["hi"]))
    return center_gap <= tol or interval_gap <= tol


def _connected_components(entries: Sequence[dict[str, Any]], *, base_tol: float, q2_scale: float) -> list[list[int]]:
    n = len(entries)
    seen = [False] * n
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if _entries_consistent(entries[i], entries[j], base_tol=base_tol, q2_scale=q2_scale):
                adj[i].append(j)
                adj[j].append(i)
    comps: list[list[int]] = []
    for i in range(n):
        if seen[i]:
            continue
        stack = [i]
        seen[i] = True
        comp: list[int] = []
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    stack.append(v)
        comps.append(sorted(comp))
    return comps


def _pairwise_consistency_fraction(entries: Sequence[dict[str, Any]], *, base_tol: float, q2_scale: float) -> float:
    if len(entries) <= 1:
        return 1.0
    total = 0
    ok = 0
    for a, b in combinations(entries, 2):
        total += 1
        if _entries_consistent(a, b, base_tol=base_tol, q2_scale=q2_scale):
            ok += 1
    return float(ok / total) if total else 1.0


def _fit_centers_against_q2(entries: Sequence[dict[str, Any]]) -> tuple[float | None, float | None, float | None, float | None, float | None]:
    if not entries:
        return None, None, None, None, None
    if len(entries) == 1:
        c = float(entries[0]["center"])
        return c, 0.0, 0.0, 0.0, 0.0
    xs = [1.0 / (e["q"] * e["q"]) for e in entries]
    ys = [float(e["center"]) for e in entries]
    ws = [float(e["q"]) for e in entries]  # emphasize higher denominators
    sw = sum(ws)
    sx = sum(w * x for w, x in zip(ws, xs))
    sy = sum(w * y for w, y in zip(ws, ys))
    sxx = sum(w * x * x for w, x in zip(ws, xs))
    sxy = sum(w * x * y for w, x, y in zip(ws, xs, ys))
    denom = sw * sxx - sx * sx
    if abs(denom) < 1e-18:
        intercept = sy / sw
        slope = 0.0
    else:
        slope = (sw * sxy - sx * sy) / denom
        intercept = (sy - slope * sx) / sw
    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    max_abs = max(abs(r) for r in residuals)
    rms = (sum(r * r for r in residuals) / len(residuals)) ** 0.5
    scaled = max(abs(r) * (e["q"] ** 2) for r, e in zip(residuals, entries))
    return float(intercept), float(slope), float(max_abs), float(rms), float(scaled)


def _width_nonincreasing_fraction(entries: Sequence[dict[str, Any]]) -> float | None:
    if len(entries) <= 1:
        return 1.0
    ordered = sorted(entries, key=lambda e: e["q"])
    total = 0
    ok = 0
    for a, b in zip(ordered[:-1], ordered[1:]):
        total += 1
        if float(b["width"]) <= float(a["width"]) + 1e-15:
            ok += 1
    return float(ok / total) if total else 1.0


def _window_intersection(entries: Iterable[dict[str, Any]]) -> tuple[float | None, float | None, float | None]:
    entries = list(entries)
    if not entries:
        return None, None, None
    lo = max(float(e["lo"]) for e in entries)
    hi = min(float(e["hi"]) for e in entries)
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _best_overlapping_subset(entries: Sequence[dict[str, Any]], *, min_subset: int = 2) -> tuple[list[dict[str, Any]], float | None, float | None, float | None]:
    if len(entries) < min_subset:
        return [], None, None, None
    best_subset: list[dict[str, Any]] = []
    best_score: tuple[float, ...] | None = None
    best_lo = best_hi = best_w = None
    for r in range(len(entries), min_subset - 1, -1):
        for idxs in combinations(range(len(entries)), r):
            subset = [entries[i] for i in idxs]
            lo, hi, width = _window_intersection(subset)
            if width is None:
                continue
            score = (
                float(r),
                float(sum(e["q"] for e in subset)),
                float(min(e["q"] for e in subset)),
                -float(width),
            )
            if best_score is None or score > best_score:
                best_score = score
                best_subset = subset
                best_lo, best_hi, best_w = lo, hi, width
        if best_subset:
            break
    return best_subset, best_lo, best_hi, best_w


def _consistency_status(member_count: int, pairwise_fraction: float, raw_intersection_width: float | None, fit_max_abs_residual: float | None, width_noninc: float | None) -> str:
    if member_count >= 3 and raw_intersection_width is not None and pairwise_fraction >= 0.8:
        if fit_max_abs_residual is None or fit_max_abs_residual <= 5e-4:
            if width_noninc is None or width_noninc >= 0.5:
                return "strong"
    if member_count >= 2 and (raw_intersection_width is not None or pairwise_fraction >= 0.6):
        return "moderate"
    if member_count >= 1:
        return "weak"
    return "failed"


def _refinement_status(consistency_status: str, refined_width: float | None) -> str:
    if refined_width is not None and consistency_status in {"strong", "moderate"}:
        return f"refined-{consistency_status}"
    if consistency_status != "failed":
        return f"envelope-{consistency_status}"
    return "failed"


def refine_rational_upper_ladder(
    ladder: dict[str, Any],
    *,
    base_tol: float = 2.5e-4,
    q2_scale: float = 0.1,
    min_subset: int = 2,
) -> RefinedRationalUpperLadderReport:
    """Refine the crossing structure inside a rational upper ladder.

    Parameters
    ----------
    ladder:
        Dictionary output from :func:`build_rational_upper_ladder`.
    base_tol, q2_scale:
        Pairwise consistency parameters.  Two crossing objects are linked when
        their windows overlap or when their centers/interval gap are smaller
        than ``base_tol + q2_scale*(1/q_i^2 + 1/q_j^2)``.
    min_subset:
        Minimum size of the high-denominator overlapping subset we search for in
        each cluster.
    """
    entries = _extract_crossing_entries(ladder)
    raw_lo = ladder.get("best_crossing_lower_bound")
    raw_hi = ladder.get("best_crossing_upper_bound")
    raw_width = None
    if raw_lo is not None and raw_hi is not None:
        raw_width = float(raw_hi) - float(raw_lo)

    if not entries:
        return RefinedRationalUpperLadderReport(
            raw_ladder_quality=str(ladder.get("ladder_quality", "failed")),
            raw_successful_crossing_count=int(ladder.get("successful_crossing_count", 0)),
            clusters=[],
            selected_cluster_index=None,
            selected_cluster_status="failed",
            selected_cluster_member_labels=[],
            selected_cluster_member_qs=[],
            best_refined_crossing_lower_bound=raw_lo,
            best_refined_crossing_upper_bound=raw_hi,
            best_refined_crossing_width=raw_width,
            raw_best_crossing_lower_bound=raw_lo,
            raw_best_crossing_upper_bound=raw_hi,
            raw_best_crossing_width=raw_width,
            refinement_improved_width=None,
            refinement_status="failed",
            notes="No successful crossing entries were available for refinement.",
        )

    comps = _connected_components(entries, base_tol=base_tol, q2_scale=q2_scale)
    clusters: list[RefinedCrossingCluster] = []
    for cid, comp in enumerate(comps):
        members = [entries[i] for i in comp]
        raw_lo_c, raw_hi_c, raw_w_c = _window_intersection(members)
        refined_subset, refined_lo, refined_hi, refined_w = _best_overlapping_subset(members, min_subset=min_subset)
        pair_frac = _pairwise_consistency_fraction(members, base_tol=base_tol, q2_scale=q2_scale)
        fit_intercept, fit_slope, fit_max_abs, fit_rms, fit_scaled = _fit_centers_against_q2(members)
        width_noninc = _width_nonincreasing_fraction(members)
        consistency = _consistency_status(len(members), pair_frac, raw_w_c, fit_max_abs, width_noninc)
        refinement = _refinement_status(consistency, refined_w)
        if refined_w is not None:
            notes = "High-denominator overlapping subset found inside cluster."
        elif raw_w_c is not None:
            notes = "Whole cluster intersects already; subset search not needed."
        else:
            notes = "Cluster is denominator-consistent but lacks a nonempty common intersection; using envelope information only."
        clusters.append(
            RefinedCrossingCluster(
                cluster_id=int(cid),
                member_labels=[str(e["label"]) for e in members],
                member_qs=[int(e["q"]) for e in members],
                member_centers=[float(e["center"]) for e in members],
                member_widths=[float(e["width"]) for e in members],
                member_count=int(len(members)),
                q_min=int(min(e["q"] for e in members)),
                q_max=int(max(e["q"] for e in members)),
                pairwise_consistency_fraction=float(pair_frac),
                fit_intercept=fit_intercept,
                fit_slope=fit_slope,
                fit_max_abs_residual=fit_max_abs,
                fit_rms_residual=fit_rms,
                fit_residual_scaled_by_q2=fit_scaled,
                width_nonincreasing_fraction=width_noninc,
                raw_intersection_lo=raw_lo_c,
                raw_intersection_hi=raw_hi_c,
                raw_intersection_width=raw_w_c,
                refined_subset_labels=[str(e["label"]) for e in refined_subset],
                refined_subset_qs=[int(e["q"]) for e in refined_subset],
                refined_lo=refined_lo,
                refined_hi=refined_hi,
                refined_width=refined_w,
                denominator_consistency_status=consistency,
                refinement_status=refinement,
                notes=notes,
            )
        )

    def cluster_score(c: RefinedCrossingCluster) -> tuple[float, ...]:
        status_rank = {"strong": 3, "moderate": 2, "weak": 1, "failed": 0}[c.denominator_consistency_status]
        refined_bonus = 1 if c.refined_width is not None else 0
        width = c.refined_width if c.refined_width is not None else (c.raw_intersection_width if c.raw_intersection_width is not None else 1e9)
        multi_member_bonus = 1 if c.member_count >= 2 else 0
        return (
            float(multi_member_bonus),
            float(status_rank),
            float(refined_bonus),
            float(c.member_count),
            float(sum(c.member_qs)),
            float(min(c.member_qs) if c.member_qs else 0),
            -float(width),
        )

    selected_idx = None
    if clusters:
        selected_idx = max(range(len(clusters)), key=lambda i: cluster_score(clusters[i]))
        selected = clusters[selected_idx]
    else:
        selected = None

    if selected is not None:
        if selected.refined_lo is not None and selected.refined_hi is not None:
            best_lo = float(selected.refined_lo)
            best_hi = float(selected.refined_hi)
            best_w = float(selected.refined_width)
        elif selected.raw_intersection_lo is not None and selected.raw_intersection_hi is not None:
            best_lo = float(selected.raw_intersection_lo)
            best_hi = float(selected.raw_intersection_hi)
            best_w = float(selected.raw_intersection_width)
        else:
            # Safe fallback: stay with the raw upper-ladder object rather than inventing a narrower window.
            best_lo = None if raw_lo is None else float(raw_lo)
            best_hi = None if raw_hi is None else float(raw_hi)
            best_w = raw_width
        selected_labels = list(selected.member_labels)
        selected_qs = list(selected.member_qs)
        selected_status = str(selected.refinement_status)
    else:
        best_lo = None if raw_lo is None else float(raw_lo)
        best_hi = None if raw_hi is None else float(raw_hi)
        best_w = raw_width
        selected_labels = []
        selected_qs = []
        selected_status = "failed"

    improvement = None
    if raw_width is not None and best_w is not None:
        improvement = float(raw_width - best_w)

    if selected is None:
        status = "failed"
        notes = "No refinement cluster could be formed."
    elif best_w is not None and raw_width is not None and best_w < raw_width:
        status = "refined-upper-ladder"
        notes = "Selected cluster improves the raw upper-side width using an overlapping, denominator-aware subfamily."
    else:
        status = "audited-upper-ladder"
        notes = "Selected cluster adds denominator-aware auditing but does not beat the raw width; the raw upper-side object is retained."

    return RefinedRationalUpperLadderReport(
        raw_ladder_quality=str(ladder.get("ladder_quality", "failed")),
        raw_successful_crossing_count=int(ladder.get("successful_crossing_count", 0)),
        clusters=[c.to_dict() for c in clusters],
        selected_cluster_index=None if selected_idx is None else int(selected_idx),
        selected_cluster_status=selected_status,
        selected_cluster_member_labels=selected_labels,
        selected_cluster_member_qs=selected_qs,
        best_refined_crossing_lower_bound=best_lo,
        best_refined_crossing_upper_bound=best_hi,
        best_refined_crossing_width=best_w,
        raw_best_crossing_lower_bound=None if raw_lo is None else float(raw_lo),
        raw_best_crossing_upper_bound=None if raw_hi is None else float(raw_hi),
        raw_best_crossing_width=raw_width,
        refinement_improved_width=improvement,
        refinement_status=status,
        notes=notes,
    )
