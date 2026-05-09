from __future__ import annotations

"""Asymptotic audits for refined rational upper ladders.

This module extends the one-shot refinement layer by asking a sharper question:
what happens to the selected upper-side object when we progressively discard the
low-denominator approximants and re-run the refinement on higher-denominator
tails only?

The goal is not to prove convergence of the rational ladder.  The goal is to
produce a theorem-facing *audit* that distinguishes:

1. a raw/refined upper ladder that looks coherent only once,
2. an upper ladder whose selected object is stable across several high-q tails,
3. an upper ladder that drifts enough that it should be treated as unsettled.

The output remains honest: it is an audit of stabilization and drift, not a
proof of irrational nonexistence.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .upper_ladder_refinement import refine_rational_upper_ladder


@dataclass
class AsymptoticUpperLadderSlice:
    q_threshold: int
    included_labels: list[str]
    included_qs: list[int]
    crossing_count: int
    selected_cluster_index: int | None
    selected_cluster_status: str
    selected_window_lo: float | None
    selected_window_hi: float | None
    selected_window_width: float | None
    selected_center: float | None
    refinement_status: str
    raw_quality: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AsymptoticUpperLadderAuditReport:
    raw_successful_crossing_count: int
    q_thresholds: list[int]
    slices: list[dict[str, Any]]
    usable_slice_count: int
    stable_tail_start_index: int | None
    stable_tail_q_threshold: int | None
    stable_tail_length: int
    stable_tail_center_drift_max: float | None
    stable_tail_width_nonincreasing_fraction: float | None
    audited_upper_lo: float | None
    audited_upper_hi: float | None
    audited_upper_width: float | None
    audited_upper_source_threshold: int | None
    narrowest_slice_threshold: int | None
    narrowest_slice_width: float | None
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["best_audited_crossing_lower_bound"] = d["audited_upper_lo"]
        d["best_audited_crossing_upper_bound"] = d["audited_upper_hi"]
        d["best_audited_crossing_width"] = d["audited_upper_width"]
        d["audited_status"] = d["status"]
        return d


def _extract_entries(ladder: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for entry in ladder.get("approximants", []):
        lo = entry.get("crossing_root_window_lo")
        hi = entry.get("crossing_root_window_hi")
        q = entry.get("q")
        if lo is None or hi is None or q in (None, 0):
            continue
        out.append(dict(entry))
    return sorted(out, key=lambda e: int(e.get("q", 0)))


def _default_thresholds(qs: Sequence[int], *, min_members: int) -> list[int]:
    uniq = sorted(set(int(q) for q in qs))
    if len(uniq) < min_members:
        return []
    return [int(uniq[i]) for i in range(0, len(uniq) - min_members + 1)]


def _selected_window(refined: dict[str, Any]) -> tuple[float | None, float | None, float | None, float | None]:
    lo = refined.get("best_refined_crossing_lower_bound")
    hi = refined.get("best_refined_crossing_upper_bound")
    width = refined.get("best_refined_crossing_width")
    if lo is None or hi is None:
        return None, None, None, None
    lo_f = float(lo)
    hi_f = float(hi)
    width_f = float(width) if width is not None else float(hi_f - lo_f)
    return lo_f, hi_f, width_f, 0.5 * (lo_f + hi_f)


def _slice_from_subset(
    ladder: dict[str, Any],
    subset: list[dict[str, Any]],
    *,
    base_tol: float,
    q2_scale: float,
    min_subset: int,
) -> AsymptoticUpperLadderSlice:
    sub_ladder = dict(ladder)
    sub_ladder["approximants"] = subset
    sub_ladder["successful_crossing_count"] = len(subset)
    refined = refine_rational_upper_ladder(
        sub_ladder,
        base_tol=base_tol,
        q2_scale=q2_scale,
        min_subset=min_subset,
    ).to_dict()
    lo, hi, width, center = _selected_window(refined)
    qs = [int(e.get("q", 0)) for e in subset]
    labels = [str(e.get("label", f"{e.get('p')}/{e.get('q')}")) for e in subset]
    return AsymptoticUpperLadderSlice(
        q_threshold=min(qs) if qs else 0,
        included_labels=labels,
        included_qs=qs,
        crossing_count=len(subset),
        selected_cluster_index=refined.get("selected_cluster_index"),
        selected_cluster_status=str(refined.get("selected_cluster_status", "failed")),
        selected_window_lo=lo,
        selected_window_hi=hi,
        selected_window_width=width,
        selected_center=center,
        refinement_status=str(refined.get("refinement_status", "failed")),
        raw_quality=str(refined.get("raw_ladder_quality", ladder.get("ladder_quality", "failed"))),
        notes=str(refined.get("notes", "")),
    )


def audit_refined_upper_ladder_asymptotics(
    ladder: dict[str, Any],
    *,
    q_thresholds: Sequence[int] | None = None,
    min_members: int = 2,
    base_tol: float = 2.5e-4,
    q2_scale: float = 0.1,
    min_subset: int = 2,
    center_drift_tol: float = 5e-4,
) -> AsymptoticUpperLadderAuditReport:
    """Audit upper-ladder stabilization across denominator thresholds.

    For each denominator threshold ``q_min`` we keep only approximants with
    ``q >= q_min`` and re-run the refinement layer.  The resulting sequence of
    selected windows is then checked for center stabilization and width
    monotonicity on a high-denominator tail.
    """
    entries = _extract_entries(ladder)
    raw_count = len(entries)
    if raw_count < min_members:
        return AsymptoticUpperLadderAuditReport(
            raw_successful_crossing_count=raw_count,
            q_thresholds=[],
            slices=[],
            usable_slice_count=0,
            stable_tail_start_index=None,
            stable_tail_q_threshold=None,
            stable_tail_length=0,
            stable_tail_center_drift_max=None,
            stable_tail_width_nonincreasing_fraction=None,
            audited_upper_lo=None,
            audited_upper_hi=None,
            audited_upper_width=None,
            audited_upper_source_threshold=None,
            narrowest_slice_threshold=None,
            narrowest_slice_width=None,
            status="insufficient-asymptotic-data",
            notes="Not enough successful crossing entries are available for a denominator-tail audit.",
        )

    qs = [int(e.get("q", 0)) for e in entries]
    thresholds = [int(q) for q in (q_thresholds if q_thresholds is not None else _default_thresholds(qs, min_members=min_members))]
    slices: list[AsymptoticUpperLadderSlice] = []
    for qmin in thresholds:
        subset = [e for e in entries if int(e.get("q", 0)) >= int(qmin)]
        if len(subset) < min_members:
            continue
        slices.append(
            _slice_from_subset(
                ladder,
                subset,
                base_tol=base_tol,
                q2_scale=q2_scale,
                min_subset=min_subset,
            )
        )

    usable = [s for s in slices if s.selected_window_lo is not None and s.selected_window_hi is not None]
    if not usable:
        return AsymptoticUpperLadderAuditReport(
            raw_successful_crossing_count=raw_count,
            q_thresholds=[s.q_threshold for s in slices],
            slices=[s.to_dict() for s in slices],
            usable_slice_count=0,
            stable_tail_start_index=None,
            stable_tail_q_threshold=None,
            stable_tail_length=0,
            stable_tail_center_drift_max=None,
            stable_tail_width_nonincreasing_fraction=None,
            audited_upper_lo=None,
            audited_upper_hi=None,
            audited_upper_width=None,
            audited_upper_source_threshold=None,
            narrowest_slice_threshold=None,
            narrowest_slice_width=None,
            status="audit-no-usable-slices",
            notes="Tail refinements were built, but none produced a selected upper window.",
        )

    # Analyze suffix stabilization among usable slices.
    best_tail_start = None
    best_tail_len = 0
    best_tail_drift = None
    best_tail_noninc = None
    for start in range(len(usable)):
        tail = usable[start:]
        if len(tail) < 2:
            continue
        centers = [float(s.selected_center) for s in tail if s.selected_center is not None]
        widths = [float(s.selected_window_width) for s in tail if s.selected_window_width is not None]
        if len(centers) != len(tail) or len(widths) != len(tail):
            continue
        drift = max(abs(b - a) for a, b in zip(centers[:-1], centers[1:])) if len(centers) >= 2 else 0.0
        total = max(1, len(widths) - 1)
        noninc = sum(1 for a, b in zip(widths[:-1], widths[1:]) if b <= a + 1e-15) / total
        if drift <= center_drift_tol and noninc >= 0.5:
            if len(tail) > best_tail_len:
                best_tail_start = start
                best_tail_len = len(tail)
                best_tail_drift = drift
                best_tail_noninc = float(noninc)

    narrowest = min(usable, key=lambda s: float(s.selected_window_width))
    audited_lo = audited_hi = audited_width = None
    audited_threshold = None
    status = "drifting-upper-ladder"
    notes = "High-denominator tails were audited, but stabilization was not strong enough to justify an asymptotic upgrade."
    if best_tail_start is not None:
        tail = usable[best_tail_start:]
        lo = max(float(s.selected_window_lo) for s in tail)
        hi = min(float(s.selected_window_hi) for s in tail)
        if hi >= lo:
            audited_lo = float(lo)
            audited_hi = float(hi)
            audited_width = float(hi - lo)
            audited_threshold = int(tail[0].q_threshold)
            status = "asymptotically-stable-upper-ladder"
            notes = (
                "A denominator-tail of refined upper objects stabilizes in center and retains a nonempty common intersection; "
                "the audited upper object is the common tail intersection."
            )
        else:
            representative = min(tail, key=lambda s: float(s.selected_window_width))
            audited_lo = float(representative.selected_window_lo)
            audited_hi = float(representative.selected_window_hi)
            audited_width = float(representative.selected_window_width)
            audited_threshold = int(representative.q_threshold)
            status = "asymptotically-audited-upper-ladder"
            notes = (
                "A denominator-tail stabilizes in center, but the selected windows do not share a common intersection; "
                "the narrowest stable-tail slice is retained as the audited upper object."
            )
    elif len(usable) >= 2:
        status = "audited-but-unsettled-upper-ladder"
        notes = (
            "Several denominator tails were audited, but the selected upper object still drifts more than the stabilization tolerance. "
            "The audit is informative but does not support a tail-stable upgrade."
        )

    return AsymptoticUpperLadderAuditReport(
        raw_successful_crossing_count=raw_count,
        q_thresholds=[int(s.q_threshold) for s in slices],
        slices=[s.to_dict() for s in slices],
        usable_slice_count=len(usable),
        stable_tail_start_index=None if best_tail_start is None else int(best_tail_start),
        stable_tail_q_threshold=None if best_tail_start is None else int(usable[best_tail_start].q_threshold),
        stable_tail_length=int(best_tail_len),
        stable_tail_center_drift_max=None if best_tail_drift is None else float(best_tail_drift),
        stable_tail_width_nonincreasing_fraction=best_tail_noninc,
        audited_upper_lo=audited_lo,
        audited_upper_hi=audited_hi,
        audited_upper_width=audited_width,
        audited_upper_source_threshold=audited_threshold,
        narrowest_slice_threshold=int(narrowest.q_threshold),
        narrowest_slice_width=float(narrowest.selected_window_width),
        status=status,
        notes=notes,
    )
