from __future__ import annotations

"""Rational-to-irrational limit-control certificates.

This module is the first explicit attempt to package a theorem-facing version of
Theorem V from the roadmap: turning a *ladder* of rational crossing windows into
an object that behaves like an explicit error-control statement for the
irrational threshold.

The implementation remains honest.  It does **not** prove the full
rational-to-irrational convergence theorem.  What it does provide is a sharply
structured bridge object built from:

1. a denominator-tail of rational crossing windows,
2. a weighted affine fit in the asymptotic variable ``x = 1/q^p`` (default
   ``p = 2``),
3. an explicit tail error budget of the form

       E(q) = |slope| / q^p + residual_sup + 0.5 * window_width,

   which bounds the mismatch between the fitted irrational limit candidate and a
   certified rational crossing window, and
4. a certified interval intersection across the active tail.

The resulting certificate is not yet a theorem that ``K_{p_n/q_n}`` converges to
``\\Lambda_F(\\rho)``.  It is a more theorem-facing object than the previous raw
ladder audit because it exposes:

- a candidate irrational limit interval,
- an explicit q-dependent error function, and
- diagnostics on whether that interval is stable across denominator tails.
"""

from dataclasses import asdict, dataclass
from itertools import combinations
from math import inf, isfinite
from typing import Any, Iterable, Sequence


@dataclass
class RationalLimitTailEntry:
    label: str
    p: int
    q: int
    center: float
    window_lo: float
    window_hi: float
    window_width: float
    model_prediction: float
    fit_residual: float
    model_term_bound: float
    total_error_bound: float
    implied_limit_lo: float
    implied_limit_hi: float
    included_in_selected_tail: bool
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RationalIrrationalConvergenceCertificate:
    rho_target: float | None
    family_label: str | None
    selected_source: str
    selected_q_threshold: int | None
    model_power: float
    entry_count: int
    usable_entry_count: int
    selected_tail_qs: list[int]
    selected_tail_labels: list[str]
    selected_tail_member_count: int
    fitted_limit_value: float | None
    fitted_slope: float | None
    fit_residual_sup: float | None
    fit_residual_rms: float | None
    max_total_error_bound: float | None
    limit_interval_lo: float | None
    limit_interval_hi: float | None
    limit_interval_width: float | None
    monotone_width_fraction: float | None
    center_drift_max: float | None
    theorem_status: str
    notes: str
    entries: list[RationalLimitTailEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho_target": self.rho_target,
            "family_label": self.family_label,
            "selected_source": str(self.selected_source),
            "selected_q_threshold": self.selected_q_threshold,
            "model_power": float(self.model_power),
            "entry_count": int(self.entry_count),
            "usable_entry_count": int(self.usable_entry_count),
            "selected_tail_qs": [int(x) for x in self.selected_tail_qs],
            "selected_tail_labels": [str(x) for x in self.selected_tail_labels],
            "selected_tail_member_count": int(self.selected_tail_member_count),
            "fitted_limit_value": self.fitted_limit_value,
            "fitted_slope": self.fitted_slope,
            "fit_residual_sup": self.fit_residual_sup,
            "fit_residual_rms": self.fit_residual_rms,
            "max_total_error_bound": self.max_total_error_bound,
            "limit_interval_lo": self.limit_interval_lo,
            "limit_interval_hi": self.limit_interval_hi,
            "limit_interval_width": self.limit_interval_width,
            "monotone_width_fraction": self.monotone_width_fraction,
            "center_drift_max": self.center_drift_max,
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
            "entries": [e.to_dict() for e in self.entries],
        }


def _extract_crossing_entries(ladder: dict[str, Any]) -> list[dict[str, Any]]:
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
        out.append(
            {
                "label": str(entry.get("label", f"{entry.get('p')}/{entry.get('q')}")),
                "p": int(entry.get("p", 0)),
                "q": int(q),
                "center": float(center),
                "lo": lo_f,
                "hi": hi_f,
                "width": float(width),
            }
        )
    return sorted(out, key=lambda e: (e["q"], e["p"], e["center"]))


def _weighted_affine_fit(entries: Sequence[dict[str, Any]], *, model_power: float) -> tuple[float, float, float, float]:
    if not entries:
        return 0.0, 0.0, inf, inf
    if len(entries) == 1:
        y = float(entries[0]["center"])
        return y, 0.0, 0.0, 0.0
    xs = [1.0 / (float(e["q"]) ** float(model_power)) for e in entries]
    ys = [float(e["center"]) for e in entries]
    ws = [max(1.0, float(e["q"])) for e in entries]
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
    residual_sup = max(abs(r) for r in residuals) if residuals else 0.0
    residual_rms = (sum(r * r for r in residuals) / len(residuals)) ** 0.5 if residuals else 0.0
    return float(intercept), float(slope), float(residual_sup), float(residual_rms)


def _window_intersection(windows: Iterable[tuple[float, float]]) -> tuple[float | None, float | None, float | None]:
    windows = list(windows)
    if not windows:
        return None, None, None
    lo = max(float(w[0]) for w in windows)
    hi = min(float(w[1]) for w in windows)
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _width_nonincreasing_fraction(entries: Sequence[dict[str, Any]]) -> float | None:
    if len(entries) <= 1:
        return 1.0
    ordered = sorted(entries, key=lambda e: int(e["q"]))
    total = max(1, len(ordered) - 1)
    ok = sum(1 for a, b in zip(ordered[:-1], ordered[1:]) if float(b["width"]) <= float(a["width"]) + 1e-15)
    return float(ok / total)


def _center_drift_max(entries: Sequence[dict[str, Any]]) -> float | None:
    if len(entries) <= 1:
        return 0.0
    ordered = sorted(entries, key=lambda e: int(e["q"]))
    drifts = [abs(float(b["center"]) - float(a["center"])) for a, b in zip(ordered[:-1], ordered[1:])]
    return float(max(drifts)) if drifts else 0.0


def _default_thresholds(entries: Sequence[dict[str, Any]], *, min_members: int) -> list[int]:
    qs = sorted({int(e["q"]) for e in entries})
    if len(qs) < min_members:
        return []
    return [int(qs[i]) for i in range(0, len(qs) - min_members + 1)]


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


def _tail_from_threshold(entries: Sequence[dict[str, Any]], q_threshold: int) -> list[dict[str, Any]]:
    return [e for e in entries if int(e["q"]) >= int(q_threshold)]


def build_rational_irrational_convergence_certificate(
    ladder: dict[str, Any],
    *,
    refined: dict[str, Any] | None = None,
    asymptotic_audit: dict[str, Any] | None = None,
    rho_target: float | None = None,
    family_label: str | None = None,
    q_thresholds: Sequence[int] | None = None,
    min_members: int = 3,
    model_power: float = 2.0,
    center_drift_tol: float = 5.0e-4,
) -> RationalIrrationalConvergenceCertificate:
    """Build an explicit q-tail convergence-control bridge certificate.

    Parameters
    ----------
    ladder:
        Rational upper ladder report or any compatible dictionary containing an
        ``approximants`` list with crossing windows.
    refined, asymptotic_audit:
        Optional outputs from the refinement and asymptotic-audit layers.  When
        supplied, their selected thresholds are used as preferred tail seeds.
    model_power:
        The asymptotic variable is ``x = 1/q**model_power``.  The default
        ``model_power = 2`` reflects the current ladder heuristics.
    """
    entries = _extract_crossing_entries(ladder)
    entry_count = len(ladder.get("approximants", []) or [])
    usable_count = len(entries)
    if usable_count < min_members:
        notes = "Not enough rational crossing windows are available for an explicit q-tail convergence-control audit."
        return RationalIrrationalConvergenceCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            selected_source="insufficient-data",
            selected_q_threshold=None,
            model_power=float(model_power),
            entry_count=int(entry_count),
            usable_entry_count=int(usable_count),
            selected_tail_qs=[],
            selected_tail_labels=[],
            selected_tail_member_count=0,
            fitted_limit_value=None,
            fitted_slope=None,
            fit_residual_sup=None,
            fit_residual_rms=None,
            max_total_error_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            monotone_width_fraction=None,
            center_drift_max=None,
            theorem_status="irrational-limit-control-insufficient-data",
            notes=notes,
            entries=[],
        )

    thresholds = [int(q) for q in (q_thresholds or [])]
    thresholds.extend(_default_thresholds(entries, min_members=min_members))
    thresholds.extend(_source_thresholds(refined, asymptotic_audit))
    thresholds = sorted(set(t for t in thresholds if t > 0))

    best_payload: dict[str, Any] | None = None
    for thr in thresholds:
        tail = _tail_from_threshold(entries, thr)
        if len(tail) < min_members:
            continue
        intercept, slope, residual_sup, residual_rms = _weighted_affine_fit(tail, model_power=model_power)
        tail_windows: list[tuple[float, float]] = []
        per_entry: list[dict[str, Any]] = []
        max_total = 0.0
        for e in tail:
            q = float(e["q"])
            model_term = abs(float(slope)) / (q ** float(model_power))
            total_error = model_term + float(residual_sup) + 0.5 * float(e["width"])
            max_total = max(max_total, total_error)
            lo = float(e["center"]) - total_error
            hi = float(e["center"]) + total_error
            tail_windows.append((lo, hi))
            per_entry.append(
                {
                    **e,
                    "model_prediction": float(intercept + slope / (q ** float(model_power))),
                    "fit_residual": float(e["center"] - (intercept + slope / (q ** float(model_power)))),
                    "model_term_bound": float(model_term),
                    "total_error_bound": float(total_error),
                    "implied_limit_lo": float(lo),
                    "implied_limit_hi": float(hi),
                }
            )
        lim_lo, lim_hi, lim_w = _window_intersection(tail_windows)
        width_noninc = _width_nonincreasing_fraction(tail)
        drift_max = _center_drift_max(tail)
        has_intersection = lim_w is not None
        score = (
            1 if has_intersection else 0,
            len(tail),
            int(min(e["q"] for e in tail)),
            -float(lim_w if lim_w is not None else max_total),
            -(float(drift_max) if drift_max is not None else inf),
        )
        payload = {
            "q_threshold": int(thr),
            "tail": tail,
            "per_entry": per_entry,
            "intercept": float(intercept),
            "slope": float(slope),
            "residual_sup": float(residual_sup),
            "residual_rms": float(residual_rms),
            "max_total": float(max_total),
            "limit_lo": lim_lo,
            "limit_hi": lim_hi,
            "limit_w": lim_w,
            "width_noninc": width_noninc,
            "drift_max": drift_max,
            "score": score,
        }
        if best_payload is None or payload["score"] > best_payload["score"]:
            best_payload = payload

    if best_payload is None:
        notes = "Denominator tails were generated, but none contained enough members for a usable convergence-control audit."
        return RationalIrrationalConvergenceCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            selected_source="no-usable-tail",
            selected_q_threshold=None,
            model_power=float(model_power),
            entry_count=int(entry_count),
            usable_entry_count=int(usable_count),
            selected_tail_qs=[],
            selected_tail_labels=[],
            selected_tail_member_count=0,
            fitted_limit_value=None,
            fitted_slope=None,
            fit_residual_sup=None,
            fit_residual_rms=None,
            max_total_error_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            monotone_width_fraction=None,
            center_drift_max=None,
            theorem_status="irrational-limit-control-no-usable-tail",
            notes=notes,
            entries=[],
        )

    tail = best_payload["tail"]
    limit_lo = best_payload["limit_lo"]
    limit_hi = best_payload["limit_hi"]
    limit_w = best_payload["limit_w"]
    width_noninc = best_payload["width_noninc"]
    drift_max = best_payload["drift_max"]
    if limit_w is not None and len(tail) >= 4 and (width_noninc is None or width_noninc >= 0.5) and (drift_max is None or drift_max <= center_drift_tol):
        status = "irrational-limit-control-strong"
        notes = (
            "A denominator tail of rational crossing windows supports an explicit q-dependent error budget with a nonempty common limit interval. "
            "This is a theorem-facing bridge toward rational-to-irrational threshold convergence, but not yet the final convergence theorem."
        )
    elif limit_w is not None and len(tail) >= 3:
        status = "irrational-limit-control-moderate"
        notes = (
            "A denominator tail of rational crossing windows supports a nonempty common limit interval under the explicit q-dependent error budget, "
            "but the tail is still too short or too weakly stabilized for the strongest status."
        )
    elif limit_w is not None:
        status = "irrational-limit-control-weak"
        notes = "A small denominator tail supports a usable explicit limit interval, but the convergence-control evidence remains limited."
    else:
        status = "irrational-limit-control-fragile"
        notes = (
            "The fitted tail does not retain a nonempty common limit interval under the explicit error budget. "
            "The audit is informative but does not yet stabilize into a strong convergence-control object."
        )

    selected_qs = [int(e["q"]) for e in tail]
    selected_labels = [str(e["label"]) for e in tail]
    included = {(int(e["p"]), int(e["q"])) for e in tail}
    out_entries: list[RationalLimitTailEntry] = []
    intercept = best_payload["intercept"]
    slope = best_payload["slope"]
    residual_sup = best_payload["residual_sup"]
    for e in entries:
        q = float(e["q"])
        model_pred = float(intercept + slope / (q ** float(model_power)))
        fit_residual = float(e["center"] - model_pred)
        model_term = abs(float(slope)) / (q ** float(model_power))
        total_error = model_term + float(residual_sup) + 0.5 * float(e["width"])
        implied_lo = float(e["center"]) - total_error
        implied_hi = float(e["center"]) + total_error
        in_tail = (int(e["p"]), int(e["q"])) in included
        out_entries.append(
            RationalLimitTailEntry(
                label=str(e["label"]),
                p=int(e["p"]),
                q=int(e["q"]),
                center=float(e["center"]),
                window_lo=float(e["lo"]),
                window_hi=float(e["hi"]),
                window_width=float(e["width"]),
                model_prediction=model_pred,
                fit_residual=fit_residual,
                model_term_bound=float(model_term),
                total_error_bound=float(total_error),
                implied_limit_lo=implied_lo,
                implied_limit_hi=implied_hi,
                included_in_selected_tail=bool(in_tail),
                status="selected-tail" if in_tail else "usable",
            )
        )

    source = "tail-threshold-search"
    if asymptotic_audit and best_payload["q_threshold"] == asymptotic_audit.get("audited_upper_source_threshold"):
        source = "asymptotic-upper-tail"
    elif refined and best_payload["q_threshold"] in _source_thresholds(refined, None):
        source = "refined-upper-cluster"

    return RationalIrrationalConvergenceCertificate(
        rho_target=None if rho_target is None else float(rho_target),
        family_label=family_label,
        selected_source=source,
        selected_q_threshold=int(best_payload["q_threshold"]),
        model_power=float(model_power),
        entry_count=int(entry_count),
        usable_entry_count=int(usable_count),
        selected_tail_qs=selected_qs,
        selected_tail_labels=selected_labels,
        selected_tail_member_count=len(selected_qs),
        fitted_limit_value=float(intercept),
        fitted_slope=float(slope),
        fit_residual_sup=float(residual_sup),
        fit_residual_rms=float(best_payload["residual_rms"]),
        max_total_error_bound=float(best_payload["max_total"]),
        limit_interval_lo=None if limit_lo is None else float(limit_lo),
        limit_interval_hi=None if limit_hi is None else float(limit_hi),
        limit_interval_width=None if limit_w is None else float(limit_w),
        monotone_width_fraction=None if width_noninc is None else float(width_noninc),
        center_drift_max=None if drift_max is None else float(drift_max),
        theorem_status=status,
        notes=notes,
        entries=out_entries,
    )


__all__ = [
    "RationalLimitTailEntry",
    "RationalIrrationalConvergenceCertificate",
    "build_rational_irrational_convergence_certificate",
]
