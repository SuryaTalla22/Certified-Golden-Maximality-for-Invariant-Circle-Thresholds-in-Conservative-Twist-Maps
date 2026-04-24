from __future__ import annotations

"""Runtime-aware seed prediction for late Theorem-V rows.

This module provides a *cheap* front end for deciding whether a future golden
convergent should be attacked directly or left to the transport/tail law.
It deliberately avoids any expensive local certification work.
"""

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Mapping, Sequence

import numpy as np


@dataclass
class TheoremVRowSeedPrediction:
    label: str
    p: int
    q: int
    predictive_center: float
    predictive_center_source: str
    predictive_window_lo: float
    predictive_window_hi: float
    predictive_window_width: float
    predictive_half_width: float
    theorem_target_center: float | None
    theorem_target_width: float | None
    q_power_extrapolated_center: float | None
    last_center: float | None
    observed_recent_shift: float | None
    estimated_runtime_hours: float
    direct_attempt_recommended: bool
    recommendation: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVRowAttemptDecision:
    label: str
    estimated_runtime_hours: float
    budget_hours: float
    allow_direct_refinement: bool
    hard_q_cap: int
    attempt_direct_refinement: bool
    decision: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def _safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if isfinite(out) else None


def _extract_entries(ladder: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    entries = list((ladder or {}).get("approximants") or [])
    out: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        q = entry.get("q")
        p = entry.get("p")
        try:
            q = int(q)
            p = int(p)
        except Exception:
            continue
        lo = _safe_float(entry.get("crossing_root_window_lo", entry.get("crossing_K_lo")))
        hi = _safe_float(entry.get("crossing_root_window_hi", entry.get("crossing_K_hi")))
        center = _safe_float(entry.get("crossing_center"))
        if center is None and lo is not None and hi is not None:
            center = 0.5 * (lo + hi)
        width = _safe_float(entry.get("crossing_root_window_width"))
        if width is None and lo is not None and hi is not None:
            width = hi - lo
        out.append({
            "p": p,
            "q": q,
            "label": str(entry.get("label", f"gold-{p}/{q}")),
            "center": center,
            "width": width,
            "lo": lo,
            "hi": hi,
        })
    out.sort(key=lambda item: int(item["q"]))
    return out


def estimate_runtime_hours_for_future_row(
    *,
    q: int,
    reference_q: int = 233,
    reference_hours: float = 6.0,
    scaling_exponent: float = 2.3,
    targeted_window_width: float | None = None,
    reference_window_width: float = 1.4852338044718527e-3,
    seeded_multiplier: float = 0.35,
) -> float:
    """Very conservative runtime estimate for a targeted heavy-row attempt.

    The estimate is intentionally heuristic.  It is used only for *planning* and
    stop/go decisions, never as a theorem ingredient.
    """
    ratio = max(float(q) / max(float(reference_q), 1.0), 1.0)
    estimate = float(reference_hours) * (ratio ** float(scaling_exponent))
    if targeted_window_width is not None and targeted_window_width > 0.0:
        width_ratio = min(max(float(targeted_window_width) / float(reference_window_width), 1e-3), 1.0)
        estimate *= max(width_ratio ** 0.4, 0.2)
    estimate *= float(seeded_multiplier)
    return float(max(estimate, 0.05))


def predict_future_golden_row_seed(
    ladder: Mapping[str, Any] | None,
    *,
    p: int,
    q: int,
    theorem_target_interval: Sequence[float] | None = None,
    explicit_error_certificate: Mapping[str, Any] | None = None,
    reference_q: int = 233,
    reference_hours: float = 6.0,
    scaling_exponent: float = 2.3,
    direct_recommendation_hours: float = 8.0,
) -> TheoremVRowSeedPrediction:
    entries = _extract_entries(ladder)
    theorem_target_center = None
    theorem_target_width = None
    if theorem_target_interval is not None and len(theorem_target_interval) >= 2:
        lo = _safe_float(theorem_target_interval[0])
        hi = _safe_float(theorem_target_interval[1])
        if lo is not None and hi is not None and hi >= lo:
            theorem_target_center = 0.5 * (lo + hi)
            theorem_target_width = hi - lo

    usable = [e for e in entries if e["center"] is not None]
    q_power_center = None
    source = "fallback"
    last_center = usable[-1]["center"] if usable else theorem_target_center
    if len(usable) >= 2:
        xs = np.array([1.0 / (float(e["q"]) ** 2) for e in usable], dtype=float)
        ys = np.array([float(e["center"]) for e in usable], dtype=float)
        try:
            deg = 1 if len(usable) < 4 else 2
            coeff = np.polyfit(xs, ys, deg=deg)
            q_power_center = float(np.polyval(coeff, 1.0 / (float(q) ** 2)))
            source = f"q^-2 extrapolation (deg={deg})"
        except Exception:
            q_power_center = None

    recent_shift = None
    if len(usable) >= 2:
        recent_shift = abs(float(usable[-1]["center"]) - float(usable[-2]["center"]))

    candidates = [c for c in (theorem_target_center, q_power_center, last_center) if c is not None]
    predictive_center = float(sum(candidates) / len(candidates)) if candidates else 0.9712
    if theorem_target_width is not None:
        base_half_width = max(4.0 * theorem_target_width, 5.0e-6)
    else:
        base_half_width = 2.5e-4
    if recent_shift is not None:
        base_half_width = max(base_half_width, 1.5 * float(recent_shift))
    last_width = None
    if usable:
        widths = [_safe_float(e["width"]) for e in usable[-2:]]
        widths = [w for w in widths if w is not None]
        if widths:
            last_width = max(widths)
            base_half_width = max(base_half_width, 0.75 * float(last_width))
    predictive_window_lo = float(predictive_center - base_half_width)
    predictive_window_hi = float(predictive_center + base_half_width)
    predictive_window_width = float(predictive_window_hi - predictive_window_lo)

    estimate = estimate_runtime_hours_for_future_row(
        q=q,
        reference_q=reference_q,
        reference_hours=reference_hours,
        scaling_exponent=scaling_exponent,
        targeted_window_width=predictive_window_width,
    )
    recommended = bool(estimate <= float(direct_recommendation_hours))
    if q >= 610:
        recommended = False
    recommendation = "targeted-direct-attempt-reasonable" if recommended else "prefer-transport-tail-closure"
    notes = (
        "Predictive center built from the current theorem target, q^-2 extrapolation, and the last certified centers. "
        "This is a runtime-planning object only; it does not certify the future row."
    )
    if theorem_target_width is not None:
        notes += f" Current theorem-target width: {float(theorem_target_width):.6g}."
    if recent_shift is not None:
        notes += f" Observed recent center shift: {float(recent_shift):.6g}."

    return TheoremVRowSeedPrediction(
        label=f"gold-{int(p)}/{int(q)}",
        p=int(p),
        q=int(q),
        predictive_center=float(predictive_center),
        predictive_center_source=source,
        predictive_window_lo=float(predictive_window_lo),
        predictive_window_hi=float(predictive_window_hi),
        predictive_window_width=float(predictive_window_width),
        predictive_half_width=float(base_half_width),
        theorem_target_center=theorem_target_center,
        theorem_target_width=theorem_target_width,
        q_power_extrapolated_center=q_power_center,
        last_center=last_center,
        observed_recent_shift=recent_shift,
        estimated_runtime_hours=float(estimate),
        direct_attempt_recommended=bool(recommended),
        recommendation=recommendation,
        notes=notes,
    )


def decide_runtime_aware_row_attempt(
    seed: Mapping[str, Any],
    *,
    budget_hours: float,
    allow_direct_refinement: bool,
    hard_q_cap: int = 400,
) -> TheoremVRowAttemptDecision:
    q = int(seed.get("q") or 0)
    est = float(seed.get("estimated_runtime_hours") or 0.0)
    label = str(seed.get("label", f"gold-?/{q}"))
    if not allow_direct_refinement:
        decision = "skip-direct-attempt-disabled"
        attempt = False
        notes = "Direct runtime-aware row attempts are disabled; use the transport/tail closure path only."
    elif q > int(hard_q_cap):
        decision = "skip-direct-attempt-q-cap"
        attempt = False
        notes = "The target denominator exceeds the hard runtime cap; keep this row as fallback-only."
    elif est > float(budget_hours):
        decision = "skip-direct-attempt-budget"
        attempt = False
        notes = "The predicted direct-runtime cost exceeds the configured budget; prefer the transport/tail closure path."
    elif not bool(seed.get("direct_attempt_recommended", False)):
        decision = "skip-direct-attempt-not-recommended"
        attempt = False
        notes = "The predictive seed itself recommends transport/tail closure rather than a direct row attempt."
    else:
        decision = "attempt-targeted-direct-refinement"
        attempt = True
        notes = "The predicted runtime cost is within budget; a seeded narrow-window direct attempt is reasonable."
    return TheoremVRowAttemptDecision(
        label=label,
        estimated_runtime_hours=float(est),
        budget_hours=float(budget_hours),
        allow_direct_refinement=bool(allow_direct_refinement),
        hard_q_cap=int(hard_q_cap),
        attempt_direct_refinement=bool(attempt),
        decision=decision,
        notes=notes,
    )


__all__ = [
    "TheoremVRowSeedPrediction",
    "TheoremVRowAttemptDecision",
    "predict_future_golden_row_seed",
    "estimate_runtime_hours_for_future_row",
    "decide_runtime_aware_row_attempt",
]
