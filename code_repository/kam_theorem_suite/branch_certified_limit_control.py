from __future__ import annotations

"""Branch-certified irrational-limit control.

This module is the next step after :mod:`irrational_limit_control`.

The previous q-tail layer fit crossing centers against ``1/q^p`` and wrapped the
fit with an explicit residual budget.  That was useful, but it still depended
heavily on an asymptotic model.  The goal here is different: build the strongest
*non-model-based* irrational-limit object that can be extracted from the local
branch certificates already present in the bundle.

The construction uses only theorem-facing local data attached to each rational
approximant, chiefly

1. the certified root window for the residue crossing,
2. the monotonicity / interval-Newton tier of that local crossing theorem,
3. any one-sided derivative interval available from the branch summary, and
4. branch-tube diagnostics such as tangent inclusion and residual width.

The resulting certificate is still not a proof of rational-to-irrational
convergence.  What it *does* provide is a branch-certified tail envelope: a
single interval that contains every selected high-denominator root window and is
weighted toward the entries with the strongest local certification.
"""

from dataclasses import asdict, dataclass
from itertools import combinations
from math import inf, isfinite
from typing import Any, Iterable, Sequence


@dataclass
class BranchCertifiedTailEntry:
    label: str
    p: int
    q: int
    center: float
    window_lo: float
    window_hi: float
    window_width: float
    certification_tier: str
    derivative_backed: bool
    derivative_floor: float | None
    tangent_inclusion_success: bool | None
    branch_residual_width: float | None
    branch_tube_sup_width: float | None
    interval_newton_success: bool
    included_in_selected_tail: bool
    local_weight: float
    envelope_radius_contribution: float | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BranchCertifiedIrrationalLimitCertificate:
    rho_target: float | None
    family_label: str | None
    selected_source: str
    selected_q_threshold: int | None
    entry_count: int
    usable_entry_count: int
    selected_tail_qs: list[int]
    selected_tail_labels: list[str]
    selected_tail_member_count: int
    derivative_backed_fraction: float | None
    interval_newton_fraction: float | None
    tangent_success_fraction: float | None
    selected_consensus_center: float | None
    selected_limit_interval_lo: float | None
    selected_limit_interval_hi: float | None
    selected_limit_interval_width: float | None
    pairwise_overlap_fraction: float | None
    tail_center_diameter: float | None
    max_local_root_radius: float | None
    min_derivative_floor: float | None
    theorem_status: str
    notes: str
    entries: list[BranchCertifiedTailEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho_target": self.rho_target,
            "family_label": self.family_label,
            "selected_source": str(self.selected_source),
            "selected_q_threshold": self.selected_q_threshold,
            "entry_count": int(self.entry_count),
            "usable_entry_count": int(self.usable_entry_count),
            "selected_tail_qs": [int(x) for x in self.selected_tail_qs],
            "selected_tail_labels": [str(x) for x in self.selected_tail_labels],
            "selected_tail_member_count": int(self.selected_tail_member_count),
            "derivative_backed_fraction": self.derivative_backed_fraction,
            "interval_newton_fraction": self.interval_newton_fraction,
            "tangent_success_fraction": self.tangent_success_fraction,
            "selected_consensus_center": self.selected_consensus_center,
            "selected_limit_interval_lo": self.selected_limit_interval_lo,
            "selected_limit_interval_hi": self.selected_limit_interval_hi,
            "selected_limit_interval_width": self.selected_limit_interval_width,
            "pairwise_overlap_fraction": self.pairwise_overlap_fraction,
            "tail_center_diameter": self.tail_center_diameter,
            "max_local_root_radius": self.max_local_root_radius,
            "min_derivative_floor": self.min_derivative_floor,
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
            "entries": [e.to_dict() for e in self.entries],
        }


def _window_intersection(windows: Iterable[tuple[float, float]]) -> tuple[float | None, float | None, float | None]:
    windows = list(windows)
    if not windows:
        return None, None, None
    lo = max(float(w[0]) for w in windows)
    hi = min(float(w[1]) for w in windows)
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _source_thresholds(refined: dict[str, Any] | None, asymptotic_audit: dict[str, Any] | None) -> list[int]:
    out: list[int] = []
    if refined:
        qs = refined.get("selected_cluster_member_qs") or []
        if qs:
            out.append(int(min(int(q) for q in qs)))
    if asymptotic_audit:
        thr = asymptotic_audit.get("audited_upper_source_threshold")
        if thr is not None:
            out.append(int(thr))
        thr = asymptotic_audit.get("stable_tail_q_threshold")
        if thr is not None:
            out.append(int(thr))
    return sorted(set(out))


def _default_thresholds(entries: Sequence[dict[str, Any]], *, min_members: int) -> list[int]:
    qs = sorted({int(e["q"]) for e in entries})
    if len(qs) < min_members:
        return []
    return [int(qs[i]) for i in range(0, len(qs) - min_members + 1)]


def _tail_from_threshold(entries: Sequence[dict[str, Any]], q_threshold: int) -> list[dict[str, Any]]:
    return [e for e in entries if int(e["q"]) >= int(q_threshold)]


def _extract_branch_certified_entries(ladder: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for entry in ladder.get("approximants", []) or []:
        lo = entry.get("crossing_root_window_lo")
        hi = entry.get("crossing_root_window_hi")
        q = entry.get("q")
        if lo is None or hi is None or q in (None, 0):
            continue
        lo_f = float(lo)
        hi_f = float(hi)
        center = entry.get("crossing_center")
        if center is None:
            center = 0.5 * (lo_f + hi_f)
        width = entry.get("crossing_root_window_width")
        if width is None:
            width = hi_f - lo_f

        crossing = dict(entry.get("crossing_certificate") or {})
        if not crossing:
            crossing = dict((entry.get("bridge_report") or {}).get("crossing_certificate") or {})
        branch_summary = dict(crossing.get("branch_summary") or {})
        tube = dict(branch_summary.get("branch_tube") or {})
        gp_lo = branch_summary.get("gprime_interval_lo")
        gp_hi = branch_summary.get("gprime_interval_hi")
        derivative_away = bool(crossing.get("derivative_away_from_zero", False))
        deriv_floor = None
        if derivative_away and gp_lo is not None and gp_hi is not None:
            gp_lo_f = float(gp_lo)
            gp_hi_f = float(gp_hi)
            if gp_lo_f > 0.0 or gp_hi_f < 0.0:
                deriv_floor = float(min(abs(gp_lo_f), abs(gp_hi_f)))

        newton = dict(crossing.get("interval_newton") or {})
        interval_newton_success = bool(newton.get("success", False) or crossing.get("certification_tier") == "interval_newton")
        tangent_success = branch_summary.get("tangent_inclusion_success")
        local_weight = (deriv_floor if deriv_floor is not None and deriv_floor > 0.0 else 0.25) / max(float(width), 1e-15)
        out.append(
            {
                "label": str(entry.get("label", f"{entry.get('p')}/{entry.get('q')}")),
                "p": int(entry.get("p", 0)),
                "q": int(q),
                "center": float(center),
                "lo": lo_f,
                "hi": hi_f,
                "width": float(width),
                "certification_tier": str(crossing.get("certification_tier", entry.get("status", "unknown"))),
                "derivative_backed": bool(deriv_floor is not None and deriv_floor > 0.0),
                "derivative_floor": deriv_floor,
                "tangent_inclusion_success": None if tangent_success is None else bool(tangent_success),
                "branch_residual_width": None if tube.get("branch_residual_width") is None else float(tube.get("branch_residual_width")),
                "branch_tube_sup_width": None if tube.get("tube_sup_width") is None else float(tube.get("tube_sup_width")),
                "interval_newton_success": bool(interval_newton_success),
                "local_weight": float(local_weight),
            }
        )
    return sorted(out, key=lambda e: (e["q"], e["p"], e["center"]))


def _pairwise_overlap_fraction(entries: Sequence[dict[str, Any]]) -> float | None:
    if len(entries) <= 1:
        return 1.0
    total = 0
    ok = 0
    for a, b in combinations(entries, 2):
        total += 1
        if min(float(a["hi"]), float(b["hi"])) >= max(float(a["lo"]), float(b["lo"])):
            ok += 1
    return float(ok / total) if total else 1.0


def _tail_center_diameter(entries: Sequence[dict[str, Any]]) -> float | None:
    if not entries:
        return None
    centers = [float(e["center"]) for e in entries]
    return float(max(centers) - min(centers)) if centers else None


def _weighted_center(entries: Sequence[dict[str, Any]]) -> float | None:
    if not entries:
        return None
    weights = [max(float(e.get("local_weight", 0.0)), 1e-18) for e in entries]
    total = sum(weights)
    if total <= 0.0:
        return float(sum(float(e["center"]) for e in entries) / len(entries))
    return float(sum(w * float(e["center"]) for w, e in zip(weights, entries)) / total)


def _derive_tail_interval(entries: Sequence[dict[str, Any]]) -> tuple[float | None, float | None, float | None, float | None]:
    if not entries:
        return None, None, None, None
    center = _weighted_center(entries)
    if center is None:
        return None, None, None, None
    radius = max(abs(float(e["center"]) - center) + 0.5 * float(e["width"]) for e in entries)
    lo = float(center - radius)
    hi = float(center + radius)
    return float(center), lo, hi, float(hi - lo)


def _fraction_true(values: Sequence[bool | None]) -> float | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return float(sum(bool(v) for v in vals) / len(vals))


def _positive_min(values: Sequence[float | None]) -> float | None:
    vals = [float(v) for v in values if v is not None and float(v) > 0.0 and isfinite(float(v))]
    return float(min(vals)) if vals else None


def _select_best_tail(candidates: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    def score(c: dict[str, Any]) -> tuple[float, ...]:
        width = float(c.get("selected_limit_interval_width") if c.get("selected_limit_interval_width") is not None else inf)
        deriv_frac = float(c.get("derivative_backed_fraction") or 0.0)
        newton_frac = float(c.get("interval_newton_fraction") or 0.0)
        overlap_frac = float(c.get("pairwise_overlap_fraction") or 0.0)
        q_thr = int(c.get("selected_q_threshold") or 0)
        members = int(c.get("selected_tail_member_count") or 0)
        return (-deriv_frac, -newton_frac, -overlap_frac, width, -q_thr, -members)
    return min(candidates, key=score)


def build_branch_certified_irrational_limit_certificate(
    ladder: dict[str, Any],
    *,
    refined: dict[str, Any] | None = None,
    asymptotic_audit: dict[str, Any] | None = None,
    rho_target: float | None = None,
    family_label: str | None = None,
    q_thresholds: Sequence[int] | None = None,
    min_members: int = 3,
) -> BranchCertifiedIrrationalLimitCertificate:
    """Build a non-model-based irrational-limit tail envelope from local branch certificates."""
    entries = _extract_branch_certified_entries(ladder)
    entry_count = len(ladder.get("approximants", []) or [])
    usable_count = len(entries)
    if usable_count < min_members:
        return BranchCertifiedIrrationalLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            selected_source="insufficient-data",
            selected_q_threshold=None,
            entry_count=int(entry_count),
            usable_entry_count=int(usable_count),
            selected_tail_qs=[],
            selected_tail_labels=[],
            selected_tail_member_count=0,
            derivative_backed_fraction=None,
            interval_newton_fraction=None,
            tangent_success_fraction=None,
            selected_consensus_center=None,
            selected_limit_interval_lo=None,
            selected_limit_interval_hi=None,
            selected_limit_interval_width=None,
            pairwise_overlap_fraction=None,
            tail_center_diameter=None,
            max_local_root_radius=None,
            min_derivative_floor=None,
            theorem_status="branch-certified-limit-incomplete",
            notes="Not enough certified root windows are available to build a branch-certified irrational-tail envelope.",
            entries=[],
        )

    source_thresholds = _source_thresholds(refined, asymptotic_audit)
    default_thresholds = _default_thresholds(entries, min_members=min_members)
    thresholds = [int(t) for t in (q_thresholds or [])]
    thresholds = sorted(set(thresholds + source_thresholds + default_thresholds))

    candidates: list[dict[str, Any]] = []
    for thr in thresholds:
        tail = _tail_from_threshold(entries, thr)
        if len(tail) < min_members:
            continue
        consensus_center, interval_lo, interval_hi, interval_width = _derive_tail_interval(tail)
        derivative_frac = _fraction_true([bool(e["derivative_backed"]) for e in tail])
        newton_frac = _fraction_true([bool(e["interval_newton_success"]) for e in tail])
        tangent_frac = _fraction_true([e.get("tangent_inclusion_success") for e in tail])
        pairwise_overlap = _pairwise_overlap_fraction(tail)
        tail_diameter = _tail_center_diameter(tail)
        max_radius = max(0.5 * float(e["width"]) for e in tail)
        min_deriv = _positive_min([e.get("derivative_floor") for e in tail])
        candidates.append(
            {
                "selected_source": "source-seeded" if thr in source_thresholds else "default-tail",
                "selected_q_threshold": int(thr),
                "tail": tail,
                "derivative_backed_fraction": derivative_frac,
                "interval_newton_fraction": newton_frac,
                "tangent_success_fraction": tangent_frac,
                "selected_consensus_center": consensus_center,
                "selected_limit_interval_lo": interval_lo,
                "selected_limit_interval_hi": interval_hi,
                "selected_limit_interval_width": interval_width,
                "pairwise_overlap_fraction": pairwise_overlap,
                "tail_center_diameter": tail_diameter,
                "max_local_root_radius": float(max_radius),
                "min_derivative_floor": min_deriv,
                "selected_tail_qs": [int(e["q"]) for e in tail],
                "selected_tail_labels": [str(e["label"]) for e in tail],
                "selected_tail_member_count": int(len(tail)),
            }
        )

    best = _select_best_tail(candidates)
    if best is None:
        return BranchCertifiedIrrationalLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            selected_source="no-admissible-tail",
            selected_q_threshold=None,
            entry_count=int(entry_count),
            usable_entry_count=int(usable_count),
            selected_tail_qs=[],
            selected_tail_labels=[],
            selected_tail_member_count=0,
            derivative_backed_fraction=None,
            interval_newton_fraction=None,
            tangent_success_fraction=None,
            selected_consensus_center=None,
            selected_limit_interval_lo=None,
            selected_limit_interval_hi=None,
            selected_limit_interval_width=None,
            pairwise_overlap_fraction=None,
            tail_center_diameter=None,
            max_local_root_radius=None,
            min_derivative_floor=None,
            theorem_status="branch-certified-limit-incomplete",
            notes="Threshold candidates existed but none retained enough high-denominator entries to form a tail envelope.",
            entries=[],
        )

    selected_labels = set(best["selected_tail_labels"])
    selected_qs = set(best["selected_tail_qs"])
    result_entries: list[BranchCertifiedTailEntry] = []
    for e in entries:
        included = str(e["label"]) in selected_labels and int(e["q"]) in selected_qs
        contribution = None
        center = best.get("selected_consensus_center")
        if included and center is not None:
            contribution = float(abs(float(e["center"]) - float(center)) + 0.5 * float(e["width"]))
        result_entries.append(
            BranchCertifiedTailEntry(
                label=str(e["label"]),
                p=int(e["p"]),
                q=int(e["q"]),
                center=float(e["center"]),
                window_lo=float(e["lo"]),
                window_hi=float(e["hi"]),
                window_width=float(e["width"]),
                certification_tier=str(e["certification_tier"]),
                derivative_backed=bool(e["derivative_backed"]),
                derivative_floor=None if e.get("derivative_floor") is None else float(e["derivative_floor"]),
                tangent_inclusion_success=e.get("tangent_inclusion_success"),
                branch_residual_width=None if e.get("branch_residual_width") is None else float(e["branch_residual_width"]),
                branch_tube_sup_width=None if e.get("branch_tube_sup_width") is None else float(e["branch_tube_sup_width"]),
                interval_newton_success=bool(e["interval_newton_success"]),
                included_in_selected_tail=bool(included),
                local_weight=float(e["local_weight"]),
                envelope_radius_contribution=contribution,
                status="selected" if included else "unused",
            )
        )

    overlap_fraction = best.get("pairwise_overlap_fraction")
    deriv_frac = best.get("derivative_backed_fraction")
    newton_frac = best.get("interval_newton_fraction")
    width = best.get("selected_limit_interval_width")
    max_radius = best.get("max_local_root_radius")
    if width is not None and deriv_frac is not None and newton_frac is not None and max_radius is not None:
        if deriv_frac >= 2.0 / 3.0 and newton_frac >= 1.0 / 3.0 and (overlap_fraction or 0.0) >= 1.0 / 3.0 and float(width) <= 6.0 * float(max_radius):
            status = "branch-certified-limit-strong"
        elif deriv_frac >= 0.5 and (overlap_fraction or 0.0) > 0.0:
            status = "branch-certified-limit-moderate"
        else:
            status = "branch-certified-limit-weak"
    else:
        status = "branch-certified-limit-weak"

    notes = (
        "This is a non-model-based irrational-tail envelope built only from local branch-certified crossing windows. "
        "It does not prove convergence, but it replaces part of the previous fit-driven layer with an interval containing all selected high-denominator certified roots and weighted toward the entries with the strongest local derivative-backed certification."
    )
    return BranchCertifiedIrrationalLimitCertificate(
        rho_target=None if rho_target is None else float(rho_target),
        family_label=family_label,
        selected_source=str(best.get("selected_source")),
        selected_q_threshold=int(best.get("selected_q_threshold")) if best.get("selected_q_threshold") is not None else None,
        entry_count=int(entry_count),
        usable_entry_count=int(usable_count),
        selected_tail_qs=[int(x) for x in best.get("selected_tail_qs", [])],
        selected_tail_labels=[str(x) for x in best.get("selected_tail_labels", [])],
        selected_tail_member_count=int(best.get("selected_tail_member_count", 0)),
        derivative_backed_fraction=None if best.get("derivative_backed_fraction") is None else float(best.get("derivative_backed_fraction")),
        interval_newton_fraction=None if best.get("interval_newton_fraction") is None else float(best.get("interval_newton_fraction")),
        tangent_success_fraction=None if best.get("tangent_success_fraction") is None else float(best.get("tangent_success_fraction")),
        selected_consensus_center=None if best.get("selected_consensus_center") is None else float(best.get("selected_consensus_center")),
        selected_limit_interval_lo=None if best.get("selected_limit_interval_lo") is None else float(best.get("selected_limit_interval_lo")),
        selected_limit_interval_hi=None if best.get("selected_limit_interval_hi") is None else float(best.get("selected_limit_interval_hi")),
        selected_limit_interval_width=None if best.get("selected_limit_interval_width") is None else float(best.get("selected_limit_interval_width")),
        pairwise_overlap_fraction=None if best.get("pairwise_overlap_fraction") is None else float(best.get("pairwise_overlap_fraction")),
        tail_center_diameter=None if best.get("tail_center_diameter") is None else float(best.get("tail_center_diameter")),
        max_local_root_radius=None if best.get("max_local_root_radius") is None else float(best.get("max_local_root_radius")),
        min_derivative_floor=None if best.get("min_derivative_floor") is None else float(best.get("min_derivative_floor")),
        theorem_status=status,
        notes=notes,
        entries=result_entries,
    )


__all__ = [
    "BranchCertifiedTailEntry",
    "BranchCertifiedIrrationalLimitCertificate",
    "build_branch_certified_irrational_limit_certificate",
]
