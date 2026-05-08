from __future__ import annotations

"""Phase 2AA Stage 2A: diagnostic profiled nonlinear/tail guard.

This module consumes Stage-1B ``raw_validation_payload`` candidate artifacts and
builds an explicitly diagnostic old-vs-profiled ledger.  It does **not** promote
any row to theorem-facing status.  The purpose is to determine whether the raw
coefficient/sample data expose enough structure to justify implementing a
future theorem-grade coefficient-aware nonlinear majorant.

The Stage-2A prototype reports several models, deliberately separated by
strength:

* ``curvature_sup_tube``: a fail-closed sanity model using the sampled supremum
  of the sine curvature profile plus a tube cushion.  In near-critical standard
  map data this usually gives essentially no improvement, but it is useful as a
  conservative baseline.
* ``curvature_quantile_99_tube`` and ``curvature_quantile_95_tube``:
  diagnostic robust-profile models.  These are not theorem-facing because a
  quantile does not bound the whole analytic tube.
* ``curvature_mean_l1``: an exploratory L1/profile model.  It is useful for
  deciding whether a genuinely coefficient-aware/sequence-space proof could
  recover the missing 1e-8 scale.  It is **not** theorem eligible.
* optional tail-response factors: purely sensitivity-style diagnostic factors
  applied to the old modewise tail response to show how much margin would move
  if a future tail majorant sharpened by 2--10%.

A row is classified as closed by a model only diagnostically, and q>=1 rows are
separately marked ``blocked_by_q`` even if their profiled tail/guard inequality
would become positive.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import csv
import json
import math
import statistics

import numpy as np

RAW_PAYLOAD_KEY = "raw_validation_payload"
PROFILED_GUARD_VERSION = "phase2aa_profiled_guard_v1"


def _as_mapping(x: Any) -> Mapping[str, Any]:
    return x if isinstance(x, Mapping) else {}


def _finite_float(x: Any, default: float | None = None) -> float | None:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _finite_int(x: Any, default: int | None = None) -> int | None:
    y = _finite_float(x)
    return default if y is None else int(y)


def _complex_array_from_payload(payload: Mapping[str, Any] | None) -> np.ndarray:
    p = _as_mapping(payload)
    real = p.get("real", [])
    imag = p.get("imag", [])
    try:
        r = np.asarray(real, dtype=float)
        i = np.asarray(imag, dtype=float)
        n = min(r.size, i.size)
        if n <= 0:
            return np.asarray([], dtype=complex)
        return r[:n] + 1j * i[:n]
    except Exception:
        return np.asarray([], dtype=complex)


def _real_array(x: Any) -> np.ndarray:
    try:
        return np.asarray(x, dtype=float).reshape(-1)
    except Exception:
        return np.asarray([], dtype=float)


def _safe_quantile(values: np.ndarray, q: float, default: float = 1.0) -> float:
    if values.size == 0:
        return float(default)
    return float(np.quantile(values, q))


def _safe_mean(values: np.ndarray, default: float = 1.0) -> float:
    if values.size == 0:
        return float(default)
    return float(np.mean(values))


def _margin(radius: float | None, residual: float | None, linear_z: float | None, tail_T: float | None) -> float | None:
    if radius is None or residual is None or linear_z is None or tail_T is None:
        return None
    return float(radius - (residual + linear_z * radius + tail_T))


def _classification(q: float | None, old_margin: float | None, profiled_margin: float | None, *, q_target: float = 1.0) -> str:
    if profiled_margin is None:
        return "blocked_by_missing_payload"
    if q is not None and q >= q_target:
        if profiled_margin > 0.0:
            return "tail_guard_would_close_but_blocked_by_q"
        return "blocked_by_q_and_tail_guard"
    if profiled_margin > 0.0:
        return "closed_by_profiled_guard_diagnostic"
    if old_margin is not None and profiled_margin > old_margin:
        return "improved_but_not_closed"
    return "no_meaningful_profiled_improvement"


@dataclass(frozen=True)
class ProfileModelResult:
    model_name: str
    model_kind: str
    theorem_eligible: bool
    diagnostic_only: bool
    nonlinear_guard_factor: float
    tail_response_factor: float
    nonlinear_guard_profiled: float | None
    tail_response_bound_profiled: float | None
    tail_T_profiled: float | None
    radii_margin_profiled: float | None
    margin_improvement: float | None
    would_close_tail_guard_inequality: bool
    would_close_with_q_gate: bool
    classification: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProfiledGuardRecord:
    candidate_path: str
    index: int | None
    K_lo: float | None
    K_hi: float | None
    q: float | None
    old_radius_r: float | None
    old_residual_Y: float | None
    old_linear_Z: float | None
    old_tail_response_bound: float | None
    old_nonlinear_guard: float | None
    old_tail_T: float | None
    old_allowable_tail_max: float | None
    old_radii_margin: float | None
    old_margin_recomputed: float | None
    old_ledger_replay_error: float | None
    old_ledger_replay_passed: bool
    source_sample_count: int
    residual_sample_count: int
    fourier_coeff_count: int
    curvature_stats: dict[str, float]
    coefficient_profile: dict[str, float]
    tail_profile_stats: dict[str, float]
    required_reductions: dict[str, float | None]
    models: list[ProfileModelResult]
    best_model_name: str | None
    best_profiled_margin: float | None
    best_profiled_classification: str | None
    recommended_next_action: str
    diagnostic_only: bool = True
    theorem_facing: bool = False
    promotion_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["models"] = [m.to_dict() for m in self.models]
        return d


def _candidate_index_from_path(path: str | Path) -> int | None:
    import re
    m = re.search(r"_p(\d{4})_", str(path))
    if not m:
        return None
    return int(m.group(1))


def _curvature_stats(raw: Mapping[str, Any]) -> dict[str, float]:
    src = _as_mapping(raw.get("source_validation"))
    u = _real_array(src.get("u", []))
    n = int(u.size)
    if n <= 0:
        return {"available": 0.0}
    theta = np.arange(n, dtype=float) / float(n)
    # Standard-sine graph equation curvature profile.  For f(theta)=(2pi)^-1 sin(2pi theta),
    # |f''|/(2pi) = |sin(2pi theta)|.  The absolute 2pi scale cancels in
    # factor comparisons, so we export normalized curvature statistics.
    curv = np.abs(np.sin(2.0 * math.pi * (theta + u)))
    radius = _finite_float(_as_mapping(raw.get("scalar_ledger_recompute")).get("radius_r"), 0.0) or 0.0
    # A tiny tube cushion for diagnostics.  It is capped because this is only a
    # model selector, not a theorem bound.
    tube_cushion = min(0.25, 2.0 * math.pi * abs(radius))
    return {
        "available": 1.0,
        "sample_count": float(n),
        "curvature_abs_sup": float(np.max(curv)),
        "curvature_abs_q999": _safe_quantile(curv, 0.999),
        "curvature_abs_q99": _safe_quantile(curv, 0.99),
        "curvature_abs_q95": _safe_quantile(curv, 0.95),
        "curvature_abs_mean": _safe_mean(curv),
        "tube_cushion": float(tube_cushion),
        "curvature_sup_tube_factor": float(min(1.0, np.max(curv) + tube_cushion)),
        "curvature_q99_tube_factor": float(min(1.0, _safe_quantile(curv, 0.99) + tube_cushion)),
        "curvature_q95_tube_factor": float(min(1.0, _safe_quantile(curv, 0.95) + tube_cushion)),
        "curvature_mean_l1_factor": float(min(1.0, _safe_mean(curv) + 0.25 * tube_cushion)),
    }


def _coefficient_profile(raw: Mapping[str, Any]) -> dict[str, float]:
    coeffs = _complex_array_from_payload(_as_mapping(raw.get("source_fourier_coefficients")))
    if coeffs.size == 0:
        return {"available": 0.0}
    abs_c = np.abs(coeffs)
    n = int(abs_c.size)
    total_l1 = float(np.sum(abs_c))
    total_l2 = float(np.linalg.norm(abs_c))
    if total_l1 <= 0:
        total_l1 = 0.0
    # The exporter uses numpy FFT order; use index bands as diagnostic profiles,
    # not theorem statements.
    low_cut = max(1, n // 16)
    mid_cut = max(1, n // 8)
    high_cut = max(1, n // 4)
    low_l1 = float(np.sum(abs_c[:low_cut]))
    mid_l1 = float(np.sum(abs_c[:mid_cut]))
    high_l1 = float(np.sum(abs_c[high_cut:]))
    spectral_high_fraction = 0.0 if total_l1 <= 0 else float(high_l1 / total_l1)
    spectral_mid_fraction = 0.0 if total_l1 <= 0 else float(mid_l1 / total_l1)
    spectral_effective_modes = 0.0 if total_l2 <= 0 else float((total_l1 / total_l2) ** 2)
    return {
        "available": 1.0,
        "coefficient_count": float(n),
        "source_coeff_l1": total_l1,
        "source_coeff_l2": total_l2,
        "low_band_l1_first_n_over_16": low_l1,
        "mid_band_l1_first_n_over_8": mid_l1,
        "high_band_l1_after_n_over_4": high_l1,
        "spectral_high_fraction_after_n_over_4": spectral_high_fraction,
        "spectral_mid_fraction_first_n_over_8": spectral_mid_fraction,
        "spectral_effective_mode_count": spectral_effective_modes,
    }


def _tail_profile_stats(raw: Mapping[str, Any]) -> dict[str, float]:
    tail = _as_mapping(raw.get("tail_profile"))
    led = _as_mapping(tail.get("modewise_tail_ledger"))
    top = led.get("top_contributors", [])
    if not isinstance(top, Sequence):
        top = []
    contribs: list[float] = []
    for row in top:
        rr = _as_mapping(row)
        val = _finite_float(rr.get("response_contribution"))
        if val is not None:
            contribs.append(val)
    response = _finite_float(led.get("modewise_tail_response"))
    top_sum = float(sum(contribs))
    top1 = float(max(contribs)) if contribs else 0.0
    top_fraction = None if response is None or response <= 0 else float(top_sum / response)
    top1_fraction = None if response is None or response <= 0 else float(top1 / response)
    return {
        "available": 1.0 if led else 0.0,
        "modewise_tail_response": 0.0 if response is None else float(response),
        "modewise_finite_response": float(_finite_float(led.get("modewise_finite_response"), 0.0) or 0.0),
        "modewise_remainder_response": float(_finite_float(led.get("modewise_remainder_response"), 0.0) or 0.0),
        "tail_l1_bound": float(_finite_float(led.get("tail_l1_bound"), 0.0) or 0.0),
        "top_contributor_count": float(len(contribs)),
        "top_contributor_response_sum": top_sum,
        "top_contributor_response_fraction": 0.0 if top_fraction is None else float(top_fraction),
        "top1_response_fraction": 0.0 if top1_fraction is None else float(top1_fraction),
        "worst_finite_inverse": float(_finite_float(led.get("worst_finite_inverse"), 0.0) or 0.0),
        "worst_finite_inverse_mode": float(_finite_float(led.get("worst_finite_inverse_mode"), 0.0) or 0.0),
    }


def _required_reductions(ledger: Mapping[str, Any]) -> dict[str, float | None]:
    old_margin = _finite_float(ledger.get("radii_margin"))
    deficit = None if old_margin is None else max(0.0, -float(old_margin))
    guard = _finite_float(ledger.get("nonlinear_guard"))
    tail_response = _finite_float(ledger.get("tail_response_bound"))
    tail_T = _finite_float(ledger.get("tail_T"))
    q = _finite_float(ledger.get("finite_contraction_q"))
    return {
        "deficit": deficit,
        "guard_reduction_frac_needed": None if deficit is None or guard is None or guard <= 0 else float(deficit / guard),
        "tail_response_reduction_frac_needed": None if deficit is None or tail_response is None or tail_response <= 0 else float(deficit / tail_response),
        "tail_T_reduction_frac_needed": None if deficit is None or tail_T is None or tail_T <= 0 else float(deficit / tail_T),
        "q_reduction_needed_to_0p999": None if q is None else float(max(0.0, q - 0.999)),
    }


def _build_model(
    *,
    name: str,
    kind: str,
    theorem_eligible: bool,
    guard_factor: float,
    tail_factor: float,
    ledger: Mapping[str, Any],
    old_margin: float | None,
    q: float | None,
    notes: str,
    q_target: float,
) -> ProfileModelResult:
    radius = _finite_float(ledger.get("radius_r"))
    residual = _finite_float(ledger.get("residual_Y"))
    linear_z = _finite_float(ledger.get("linear_Z"))
    old_guard = _finite_float(ledger.get("nonlinear_guard"))
    old_tail_response = _finite_float(ledger.get("tail_response_bound"))
    new_guard = None if old_guard is None else float(max(0.0, min(1.0, guard_factor)) * old_guard)
    new_tail_response = None if old_tail_response is None else float(max(0.0, min(1.0, tail_factor)) * old_tail_response)
    new_tail_T = None if new_guard is None or new_tail_response is None else float(new_guard + new_tail_response)
    new_margin = _margin(radius, residual, linear_z, new_tail_T)
    improvement = None if new_margin is None or old_margin is None else float(new_margin - old_margin)
    closes_tail = bool(new_margin is not None and new_margin > 0.0)
    closes_with_q = bool(closes_tail and (q is None or q < q_target))
    return ProfileModelResult(
        model_name=name,
        model_kind=kind,
        theorem_eligible=bool(theorem_eligible),
        diagnostic_only=True,
        nonlinear_guard_factor=float(guard_factor),
        tail_response_factor=float(tail_factor),
        nonlinear_guard_profiled=new_guard,
        tail_response_bound_profiled=new_tail_response,
        tail_T_profiled=new_tail_T,
        radii_margin_profiled=new_margin,
        margin_improvement=improvement,
        would_close_tail_guard_inequality=closes_tail,
        would_close_with_q_gate=closes_with_q,
        classification=_classification(q, old_margin, new_margin, q_target=q_target),
        notes=str(notes),
    )


def analyze_candidate(
    candidate: Mapping[str, Any],
    *,
    candidate_path: str | Path = "<memory>",
    q_target: float = 1.0,
    old_ledger_tolerance: float = 1.0e-10,
    extra_tail_response_factors: Sequence[float] = (0.98, 0.96, 0.94, 0.92, 0.90),
) -> ProfiledGuardRecord:
    raw = _as_mapping(candidate.get(RAW_PAYLOAD_KEY))
    ledger = _as_mapping(raw.get("scalar_ledger_recompute"))
    selected = _as_mapping(raw.get("selected_row_snapshot")) or _as_mapping(candidate.get("selected_phase2p_row"))

    q = _finite_float(ledger.get("finite_contraction_q"), _finite_float(selected.get("finite_contraction_q")))
    old_margin = _finite_float(ledger.get("radii_margin"), _finite_float(selected.get("radii_margin")))
    recomputed = _finite_float(ledger.get("recomputed_margin"))
    if recomputed is None:
        recomputed = _margin(
            _finite_float(ledger.get("radius_r")),
            _finite_float(ledger.get("residual_Y")),
            _finite_float(ledger.get("linear_Z")),
            _finite_float(ledger.get("tail_T")),
        )
    replay_error = None if old_margin is None or recomputed is None else float(recomputed - old_margin)
    replay_passed = bool(replay_error is not None and abs(replay_error) <= old_ledger_tolerance)

    curv = _curvature_stats(raw)
    coeff = _coefficient_profile(raw)
    tail_stats = _tail_profile_stats(raw)
    req = _required_reductions(ledger)

    models: list[ProfileModelResult] = []
    # Conservative/sanity model: essentially should not improve unless curvature sup < 1.
    models.append(_build_model(
        name="curvature_sup_tube_guard_only",
        kind="conservative_sanity",
        theorem_eligible=False,  # still diagnostic until interval tube proof is implemented
        guard_factor=float(curv.get("curvature_sup_tube_factor", 1.0)),
        tail_factor=1.0,
        ledger=ledger,
        old_margin=old_margin,
        q=q,
        notes="Sampled curvature supremum plus tube cushion; diagnostic sanity baseline, not an interval proof.",
        q_target=q_target,
    ))
    models.append(_build_model(
        name="curvature_q99_tube_guard_only",
        kind="robust_sample_profile",
        theorem_eligible=False,
        guard_factor=float(curv.get("curvature_q99_tube_factor", 1.0)),
        tail_factor=1.0,
        ledger=ledger,
        old_margin=old_margin,
        q=q,
        notes="99% curvature profile model. Not theorem-facing; indicates whether rare peaks dominate the scalar guard.",
        q_target=q_target,
    ))
    models.append(_build_model(
        name="curvature_q95_tube_guard_only",
        kind="robust_sample_profile",
        theorem_eligible=False,
        guard_factor=float(curv.get("curvature_q95_tube_factor", 1.0)),
        tail_factor=1.0,
        ledger=ledger,
        old_margin=old_margin,
        q=q,
        notes="95% curvature profile model. Not theorem-facing; stress test for coefficient-aware majorants.",
        q_target=q_target,
    ))
    models.append(_build_model(
        name="curvature_mean_l1_guard_only",
        kind="exploratory_l1_profile",
        theorem_eligible=False,
        guard_factor=float(curv.get("curvature_mean_l1_factor", 1.0)),
        tail_factor=1.0,
        ledger=ledger,
        old_margin=old_margin,
        q=q,
        notes="Exploratory L1/average-curvature proxy. It can motivate a sequence-space proof but is not itself a proof.",
        q_target=q_target,
    ))

    # Tail response sensitivity models. These are intentionally diagnostic. They
    # tell us how much a future true tail majorant must sharpen once raw data are available.
    for tf in extra_tail_response_factors:
        tf = float(tf)
        models.append(_build_model(
            name=f"tail_response_factor_{tf:.3f}_old_guard",
            kind="tail_response_sensitivity",
            theorem_eligible=False,
            guard_factor=1.0,
            tail_factor=tf,
            ledger=ledger,
            old_margin=old_margin,
            q=q,
            notes="Diagnostic tail-response sensitivity using the old nonlinear guard.",
            q_target=q_target,
        ))
        models.append(_build_model(
            name=f"tail_response_factor_{tf:.3f}_mean_l1_guard",
            kind="combined_tail_and_l1_guard_sensitivity",
            theorem_eligible=False,
            guard_factor=float(curv.get("curvature_mean_l1_factor", 1.0)),
            tail_factor=tf,
            ledger=ledger,
            old_margin=old_margin,
            q=q,
            notes="Combined diagnostic sensitivity: hypothetical tail sharpening plus exploratory L1 guard.",
            q_target=q_target,
        ))

    best = None
    for m in models:
        if m.radii_margin_profiled is None:
            continue
        if best is None or (best.radii_margin_profiled is not None and m.radii_margin_profiled > best.radii_margin_profiled):
            best = m
    if best is None:
        rec_action = "payload_missing_or_unusable"
    elif best.would_close_with_q_gate:
        rec_action = "profiled_guard_path_promising_expand_to_more_q_safe_rows"
    elif best.would_close_tail_guard_inequality and q is not None and q >= q_target:
        rec_action = "tail_guard_path_promising_but_requires_stage2b_q_scaling"
    elif q is not None and q >= q_target:
        rec_action = "prioritize_stage2b_diagonal_scaling_then_retest_guard"
    elif best.margin_improvement is not None and best.margin_improvement > 1.0e-8:
        rec_action = "guard_improves_meaningfully_but_needs_true_tail_or_stronger_majorant"
    else:
        rec_action = "coefficient_profile_not_sufficient_prioritize_fhl_or_diagonal_scaling"

    src = _as_mapping(raw.get("source_validation"))
    res = _as_mapping(raw.get("residual"))
    coeffs = _complex_array_from_payload(_as_mapping(raw.get("source_fourier_coefficients")))
    return ProfiledGuardRecord(
        candidate_path=str(candidate_path),
        index=_candidate_index_from_path(candidate_path),
        K_lo=_finite_float(_as_mapping(raw.get("K_interval", {})).get(0) if False else (raw.get("K_interval") or [None, None])[0]),
        K_hi=_finite_float((raw.get("K_interval") or [None, None])[1]),
        q=q,
        old_radius_r=_finite_float(ledger.get("radius_r")),
        old_residual_Y=_finite_float(ledger.get("residual_Y")),
        old_linear_Z=_finite_float(ledger.get("linear_Z")),
        old_tail_response_bound=_finite_float(ledger.get("tail_response_bound")),
        old_nonlinear_guard=_finite_float(ledger.get("nonlinear_guard")),
        old_tail_T=_finite_float(ledger.get("tail_T")),
        old_allowable_tail_max=_finite_float(ledger.get("allowable_tail_max")),
        old_radii_margin=old_margin,
        old_margin_recomputed=recomputed,
        old_ledger_replay_error=replay_error,
        old_ledger_replay_passed=replay_passed,
        source_sample_count=int(len(src.get("u", []) or [])),
        residual_sample_count=int(len(res.get("samples", []) or [])),
        fourier_coeff_count=int(coeffs.size),
        curvature_stats=curv,
        coefficient_profile=coeff,
        tail_profile_stats=tail_stats,
        required_reductions=req,
        models=models,
        best_model_name=None if best is None else best.model_name,
        best_profiled_margin=None if best is None else best.radii_margin_profiled,
        best_profiled_classification=None if best is None else best.classification,
        recommended_next_action=rec_action,
    )


def _extract_candidate_paths_from_summary(summary: Mapping[str, Any], *, root: str | Path = ".") -> list[Path]:
    root = Path(root)
    paths: list[Path] = []
    for row in summary.get("best_failed_rows", []) or []:
        rr = _as_mapping(row)
        p = rr.get("path") or rr.get("phase2p_candidate")
        if p:
            paths.append(root / str(p))
    for row in summary.get("results", []) or []:
        rr = _as_mapping(row)
        p = rr.get("phase2p_candidate") or rr.get("candidate") or rr.get("path")
        if p:
            paths.append(root / str(p))
    # stable unique, preserving order
    out: list[Path] = []
    seen: set[str] = set()
    for p in paths:
        key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def run_profiled_guard_audit(
    *,
    summary_path: str | Path | None = None,
    candidate_paths: Sequence[str | Path] = (),
    root: str | Path = ".",
    q_target: float = 1.0,
    old_ledger_tolerance: float = 1.0e-10,
    tail_response_factors: Sequence[float] = (0.98, 0.96, 0.94, 0.92, 0.90),
) -> dict[str, Any]:
    root = Path(root)
    paths: list[Path] = [root / str(p) for p in candidate_paths]
    summary_obj: Mapping[str, Any] = {}
    if summary_path is not None:
        sp = Path(summary_path)
        if not sp.is_absolute():
            sp = root / sp
        try:
            summary_obj = json.loads(sp.read_text())
            paths.extend(_extract_candidate_paths_from_summary(summary_obj, root=root))
        except Exception:
            summary_obj = {}
    # unique
    unique: list[Path] = []
    seen: set[str] = set()
    for p in paths:
        key = str(p)
        if key not in seen:
            seen.add(key)
            unique.append(p)

    records: list[ProfiledGuardRecord] = []
    missing: list[str] = []
    errors: list[dict[str, str]] = []
    for p in unique:
        if not p.exists():
            missing.append(str(p))
            continue
        try:
            cand = json.loads(p.read_text())
            records.append(analyze_candidate(
                cand,
                candidate_path=p,
                q_target=q_target,
                old_ledger_tolerance=old_ledger_tolerance,
                extra_tail_response_factors=tail_response_factors,
            ))
        except Exception as exc:
            errors.append({"path": str(p), "error": repr(exc)})

    rec_dicts = [r.to_dict() for r in records]
    action_counts: dict[str, int] = {}
    model_close_counts: dict[str, int] = {}
    model_tail_close_counts: dict[str, int] = {}
    model_improvement_sums: dict[str, list[float]] = {}
    for r in records:
        action_counts[r.recommended_next_action] = action_counts.get(r.recommended_next_action, 0) + 1
        for m in r.models:
            if m.would_close_with_q_gate:
                model_close_counts[m.model_name] = model_close_counts.get(m.model_name, 0) + 1
            if m.would_close_tail_guard_inequality:
                model_tail_close_counts[m.model_name] = model_tail_close_counts.get(m.model_name, 0) + 1
            if m.margin_improvement is not None:
                model_improvement_sums.setdefault(m.model_name, []).append(float(m.margin_improvement))
    model_mean_improvements = {
        k: float(statistics.mean(v)) for k, v in sorted(model_improvement_sums.items()) if v
    }
    q_safe_records = [r for r in records if r.q is not None and r.q < q_target]
    q_blocked_records = [r for r in records if r.q is not None and r.q >= q_target]
    closed_any = [r for r in records if any(m.would_close_with_q_gate for m in r.models)]
    tail_closed_any = [r for r in records if any(m.would_close_tail_guard_inequality for m in r.models)]

    summary = {
        "schema": PROFILED_GUARD_VERSION,
        "status": "phase2aa-stage2a-profiled-guard-complete" if records else "phase2aa-stage2a-profiled-guard-empty",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "summary_path": None if summary_path is None else str(summary_path),
        "candidate_count": len(unique),
        "record_count": len(records),
        "missing_candidate_count": len(missing),
        "error_count": len(errors),
        "old_ledger_replay_passed_count": sum(1 for r in records if r.old_ledger_replay_passed),
        "q_safe_count": len(q_safe_records),
        "q_blocked_count": len(q_blocked_records),
        "records_with_any_q_gated_diagnostic_closure": len(closed_any),
        "records_with_any_tail_guard_diagnostic_closure_before_q_gate": len(tail_closed_any),
        "recommended_next_action_counts": action_counts,
        "model_q_gated_close_counts": model_close_counts,
        "model_tail_guard_close_counts": model_tail_close_counts,
        "model_mean_margin_improvements": model_mean_improvements,
        "best_records_by_profiled_margin": sorted(rec_dicts, key=lambda d: d.get("best_profiled_margin") if d.get("best_profiled_margin") is not None else -1e99, reverse=True)[:20],
        "records": rec_dicts,
        "missing_candidates": missing,
        "errors": errors,
        "interpretation": _interpretation(len(records), len(q_safe_records), len(closed_any), len(tail_closed_any), action_counts),
    }
    return summary


def _interpretation(record_count: int, q_safe_count: int, closed_count: int, tail_closed_count: int, action_counts: Mapping[str, int]) -> list[str]:
    notes: list[str] = []
    if record_count <= 0:
        notes.append("No usable Stage-1B raw-payload candidates were analyzed; rerun/export Stage 1B first.")
        return notes
    if closed_count > 0:
        notes.append("At least one q-safe row closes diagnostically under a profiled model; expand Stage 2A to more q<1 rows and implement theorem-grade interval majorant next.")
    elif tail_closed_count > 0:
        notes.append("Some rows would pass the tail/guard inequality but remain blocked by q>=1; prioritize Stage 2B diagonal finite-Krawczyk scaling on those rows.")
    elif q_safe_count > 0:
        notes.append("No q-safe row closes diagnostically; inspect model_mean_margin_improvements to decide whether a stronger true nonlinear/tail majorant is worthwhile or whether to prioritize FHL-style validation.")
    if action_counts.get("prioritize_stage2b_diagonal_scaling_then_retest_guard", 0) > 0:
        notes.append("Several records are q-blocked; Stage 2B diagonal/weighted finite-norm scaling is required for them.")
    notes.append("All Stage-2A profiled models are diagnostic-only and must not be promoted without an outward-rounded theorem proof.")
    return notes


def write_profiled_guard_outputs(report: Mapping[str, Any], *, out: str | Path, csv_path: str | Path | None = None) -> None:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if csv_path is None:
        return
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for rec in report.get("records", []) or []:
        base = {
            "index": rec.get("index"),
            "candidate_path": rec.get("candidate_path"),
            "K_lo": rec.get("K_lo"),
            "K_hi": rec.get("K_hi"),
            "q": rec.get("q"),
            "old_margin": rec.get("old_radii_margin"),
            "old_tail_response": rec.get("old_tail_response_bound"),
            "old_guard": rec.get("old_nonlinear_guard"),
            "best_model": rec.get("best_model_name"),
            "best_profiled_margin": rec.get("best_profiled_margin"),
            "best_classification": rec.get("best_profiled_classification"),
            "recommended_next_action": rec.get("recommended_next_action"),
            "old_ledger_replay_passed": rec.get("old_ledger_replay_passed"),
        }
        for m in rec.get("models", []) or []:
            row = dict(base)
            row.update({
                "model_name": m.get("model_name"),
                "model_kind": m.get("model_kind"),
                "guard_factor": m.get("nonlinear_guard_factor"),
                "tail_factor": m.get("tail_response_factor"),
                "profiled_margin": m.get("radii_margin_profiled"),
                "margin_improvement": m.get("margin_improvement"),
                "would_close_tail_guard": m.get("would_close_tail_guard_inequality"),
                "would_close_with_q_gate": m.get("would_close_with_q_gate"),
                "classification": m.get("classification"),
            })
            rows.append(row)
    fieldnames = [
        "index", "candidate_path", "K_lo", "K_hi", "q", "old_margin", "old_tail_response", "old_guard",
        "best_model", "best_profiled_margin", "best_classification", "recommended_next_action", "old_ledger_replay_passed",
        "model_name", "model_kind", "guard_factor", "tail_factor", "profiled_margin", "margin_improvement",
        "would_close_tail_guard", "would_close_with_q_gate", "classification",
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


__all__ = [
    "PROFILED_GUARD_VERSION",
    "analyze_candidate",
    "run_profiled_guard_audit",
    "write_profiled_guard_outputs",
]
