"""Phase 5B interval-component audit scaffold for Track B Theorem III.

This module is intentionally conservative but still diagnostic: it computes
component-wise, proof-shaped bounds around a selected numerical seed.  It does
not yet use a formal interval-arithmetic backend, so all outputs are marked
``theorem_facing = False`` and ``promotion_allowed = False``.

The goal is to identify whether the Phase 4i selected seed has component bounds
that are plausible for a later outward-rounded theorem-facing validator.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import csv
import json
import math
import os
import re
from typing import Any, Iterable

import numpy as np

TWOPI = 2.0 * math.pi
GOLDEN_OMEGA = (math.sqrt(5.0) - 1.0) / 2.0


def _ensure_dir(p: str | Path) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    _ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def _parse_float_list(s: str | Iterable[float]) -> list[float]:
    if isinstance(s, str):
        return [float(x) for x in s.split(",") if x.strip()]
    return [float(x) for x in s]


def _parse_str_list(s: str | Iterable[str]) -> list[str]:
    if isinstance(s, str):
        return [x.strip() for x in s.split(",") if x.strip()]
    return [str(x).strip() for x in s]


def _parse_int_list(s: str | Iterable[int]) -> list[int]:
    if isinstance(s, str):
        return [int(x) for x in s.split(",") if x.strip()]
    return [int(x) for x in s]


def _safe_float(x: Any, default: float | None = None) -> float | None:
    try:
        arr = np.asarray(x)
        if arr.size == 0:
            return default
        return float(arr.reshape(-1)[0])
    except Exception:
        return default


def _k_from_filename(path: str | Path) -> float | None:
    name = Path(path).name
    m = re.search(r"K(\d+)p(\d+)", name)
    if not m:
        return None
    return float(f"{m.group(1)}.{m.group(2)}")


def _sanitize_token(x: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", x.replace(":", ""))


def centered_modes(M: int) -> np.ndarray:
    # Compatible with fftshift(fft(v))/M ordering for even M.
    return np.arange(-M // 2, M // 2, dtype=int)


def coeff_from_values(v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    v = np.asarray(v, dtype=float)
    M = int(v.size)
    c = np.fft.fftshift(np.fft.fft(v)) / M
    return centered_modes(M), c


def values_from_coeff(modes: np.ndarray, coeff: np.ndarray, L: int) -> np.ndarray:
    M = int(coeff.size)
    if L < M:
        # Truncate safely to requested size.
        keep = np.abs(modes) < L // 2
        modes = modes[keep]
        coeff = coeff[keep]
        M = int(coeff.size)
    cL = np.zeros(L, dtype=complex)
    center = L // 2
    for k, ck in zip(modes, coeff):
        j = center + int(k)
        if 0 <= j < L:
            cL[j] = ck
    return np.fft.ifft(np.fft.ifftshift(cL)) * L


def load_seed(npz_path: str | Path, omega_override: float | None = None) -> dict[str, Any]:
    npz_path = str(npz_path)
    with np.load(npz_path, allow_pickle=False) as z:
        keys = set(z.files)
        u_key = None
        for cand in ("u", "u_values", "u_grid", "values", "embedding_u"):
            if cand in keys:
                u_key = cand
                break
        if u_key is None:
            # Fallback: first one-dimensional real-valued array with length > 16.
            for k in z.files:
                arr = np.asarray(z[k])
                if arr.ndim == 1 and arr.size > 16 and np.isrealobj(arr):
                    u_key = k
                    break
        if u_key is None:
            raise ValueError(f"Could not identify u array in {npz_path}; keys={sorted(keys)}")
        u = np.asarray(z[u_key], dtype=float).reshape(-1)

        K = None
        for cand in ("K", "k", "parameter_K", "K_value"):
            if cand in keys:
                K = _safe_float(z[cand])
                break
        if K is None:
            K = _k_from_filename(npz_path)
        if K is None:
            raise ValueError(f"Could not infer K from {npz_path}")

        omega = omega_override
        if omega is None:
            for cand in ("omega", "rotation", "rho"):
                if cand in keys:
                    omega = _safe_float(z[cand])
                    break
        if omega is None:
            omega = GOLDEN_OMEGA

    return {"npz_path": npz_path, "u": u, "M": int(u.size), "K": float(K), "omega": float(omega)}


def eval_u_and_derivative(u: np.ndarray, L: int, omega: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    modes, c = coeff_from_values(u)
    phase = np.exp(1j * TWOPI * modes * omega)
    u_vals = values_from_coeff(modes, c * phase, L).real
    du_vals = values_from_coeff(modes, (1j * TWOPI * modes) * c * phase, L).real
    return u_vals, du_vals


def residual_values(u: np.ndarray, K: float, omega: float, L: int) -> np.ndarray:
    u0, _ = eval_u_and_derivative(u, L, 0.0)
    up, _ = eval_u_and_derivative(u, L, omega)
    um, _ = eval_u_and_derivative(u, L, -omega)
    theta = np.arange(L, dtype=float) / L
    return up - 2.0 * u0 + um - (K / TWOPI) * np.sin(TWOPI * (theta + u0))


def derivative_residual_values(u: np.ndarray, K: float, omega: float, L: int) -> np.ndarray:
    u0, du0 = eval_u_and_derivative(u, L, 0.0)
    _, dup = eval_u_and_derivative(u, L, omega)
    _, dum = eval_u_and_derivative(u, L, -omega)
    theta = np.arange(L, dtype=float) / L
    return dup - 2.0 * du0 + dum - K * np.cos(TWOPI * (theta + u0)) * (1.0 + du0)


def weighted_l1_from_values(v: np.ndarray, nu: float, cutoff_mode: int | None = None) -> tuple[float, float, float, float]:
    modes, c = coeff_from_values(v)
    weights = np.power(float(nu), np.abs(modes))
    absw = np.abs(c) * weights
    total = float(np.sum(absw))
    if cutoff_mode is None:
        cutoff_mode = int(np.max(np.abs(modes)))
    core_mask = np.abs(modes) <= int(cutoff_mode)
    core = float(np.sum(absw[core_mask]))
    tail = float(np.sum(absw[~core_mask]))
    ratio = float(tail / max(core, 1e-300))
    return total, core, tail, ratio


def cohomology_bound_from_residual(v: np.ndarray, nu: float, omega: float, cutoff_mode: int) -> tuple[float, float, int, float, float]:
    modes, c = coeff_from_values(v)
    nonzero = modes != 0
    core = (np.abs(modes) <= int(cutoff_mode)) & nonzero
    den = np.abs(np.exp(1j * TWOPI * modes[core] * omega) - 1.0)
    if den.size == 0:
        return 0.0, math.inf, 0, 0.0, 0.0
    min_idx = int(np.argmin(den))
    min_den = float(den[min_idx])
    min_mode = int(modes[core][min_idx])
    inv_max = float(np.max(1.0 / den))
    weights = np.power(float(nu), np.abs(modes[core]))
    y = float(np.sum(np.abs(c[core]) / den * weights))
    zero_mode = float(abs(c[modes == 0][0])) if np.any(modes == 0) else 0.0
    return y, min_den, min_mode, inv_max, zero_mode


def tangent_frame_components(u: np.ndarray, K: float, omega: float, L: int) -> dict[str, float]:
    theta = np.arange(L, dtype=float) / L
    u0, du0 = eval_u_and_derivative(u, L, 0.0)
    um, dum = eval_u_and_derivative(u, L, -omega)
    up, dup = eval_u_and_derivative(u, L, omega)

    x = theta + u0
    xp = 1.0 + du0
    r = omega + u0 - um
    rp = du0 - dum

    # Source tangent and symplectic normal with det=1.
    T1 = xp
    T2 = rp
    n2 = T1 * T1 + T2 * T2
    N1 = -T2 / n2
    N2 = T1 / n2

    # Target frame recomputed from shifted tangent, not shifted normal.
    Tp1 = 1.0 + dup
    Tp2 = dup - du0
    n2p = Tp1 * Tp1 + Tp2 * Tp2
    Np1 = -Tp2 / n2p
    Np2 = Tp1 / n2p

    # Standard-sine map derivative consistent with scalar residual sign.
    c = K * np.cos(TWOPI * x)
    # DF = [[1+c, 1], [c, 1]] applied to source frame columns.
    DT1_1 = (1.0 + c) * T1 + T2
    DT1_2 = c * T1 + T2
    DN1_1 = (1.0 + c) * N1 + N2
    DN1_2 = c * N1 + N2

    # M_target^{-1}; det is 1 by construction, inverse [[Np2, -Np1], [-Tp2, Tp1]].
    a11 = Np2 * DT1_1 - Np1 * DT1_2
    a21 = -Tp2 * DT1_1 + Tp1 * DT1_2
    a12 = Np2 * DN1_1 - Np1 * DN1_2
    a22 = -Tp2 * DN1_1 + Tp1 * DN1_2

    det_source = T1 * N2 - T2 * N1
    det_target = Tp1 * Np2 - Tp2 * Np1
    tangent_res = np.maximum(np.abs(DT1_1 - Tp1), np.abs(DT1_2 - Tp2))
    upper_def = np.maximum.reduce([np.abs(a11 - 1.0), np.abs(a21), np.abs(a22 - 1.0)])
    tangent_norm = np.sqrt(T1 * T1 + T2 * T2)

    return {
        "frame_tangent_norm_min": float(np.min(tangent_norm)),
        "frame_tangent_norm_max": float(np.max(tangent_norm)),
        "source_frame_det_defect_linf": float(np.max(np.abs(det_source - 1.0))),
        "target_frame_det_defect_linf": float(np.max(np.abs(det_target - 1.0))),
        "tangent_residual_linf": float(np.max(tangent_res)),
        "a11_minus_1_linf": float(np.max(np.abs(a11 - 1.0))),
        "a21_linf": float(np.max(np.abs(a21))),
        "a22_minus_1_linf": float(np.max(np.abs(a22 - 1.0))),
        "upper_triangular_defect_linf_max": float(np.max(upper_def)),
        "twist_average": float(np.mean(a12)),
        "twist_min": float(np.min(a12)),
        "twist_max": float(np.max(a12)),
    }


def cutoff_to_mode(cutoff: str, M: int) -> int:
    max_mode = M // 2 - 1
    cutoff = str(cutoff)
    if cutoff == "full":
        return max_mode
    if cutoff.startswith("frac:"):
        frac = float(cutoff.split(":", 1)[1])
        return max(1, min(max_mode, int(math.floor(frac * max_mode))))
    return max(1, min(max_mode, int(cutoff)))


def inflate(x: float, rel: float, abs_floor: float) -> float:
    y = abs(float(x)) * (1.0 + float(rel)) + float(abs_floor)
    return float(np.nextafter(y, math.inf))


@dataclass(frozen=True)
class Phase5BConfig:
    npz_path: str
    nu: float
    cutoff_spec: str
    tail_start_frac: float
    grid_factor: int
    radius: float
    rounding_slack: float = 1e-10
    interval_inflation: float = 0.05
    q_scale: float = 0.038
    omega_override: float | None = None
    out_dir: str = "artifacts/proof_audit/theorem_iii_trackb/phase5b_interval_components"


def audit_one_phase5b(cfg: Phase5BConfig) -> dict[str, Any]:
    seed = load_seed(cfg.npz_path, cfg.omega_override)
    u = seed["u"]
    M = int(seed["M"])
    K = float(seed["K"])
    omega = float(seed["omega"])
    L = int(M * int(cfg.grid_factor))
    cutoff_mode = cutoff_to_mode(cfg.cutoff_spec, M)

    R = residual_values(u, K, omega, L)
    dR = derivative_residual_values(u, K, omega, L)
    scalar_linf = float(np.max(np.abs(R)))
    derivative_linf = float(np.max(np.abs(dR)))

    residual_l1_total, residual_l1_core, residual_l1_tail, residual_tail_ratio = weighted_l1_from_values(R, cfg.nu, cutoff_mode)
    derivative_l1_total, derivative_l1_core, derivative_l1_tail, derivative_tail_ratio = weighted_l1_from_values(dR, cfg.nu, cutoff_mode)
    Y, min_den, min_mode, inv_max, zero_mode = cohomology_bound_from_residual(R, cfg.nu, omega, cutoff_mode)
    geom = tangent_frame_components(u, K, omega, L)

    # Component-wise inflated bounds.  These are not a substitute for interval arithmetic, but
    # make the diagnostic less brittle and identify which bounds need theorem-grade treatment.
    infl = float(cfg.interval_inflation)
    floor = float(cfg.rounding_slack)
    Yb = inflate(Y + zero_mode, infl, floor)
    Zb = inflate(inv_max * geom["upper_triangular_defect_linf_max"], infl, floor)
    frame_max = geom["frame_tangent_norm_max"]
    Q_raw = inv_max * max(1.0, abs(K)) * (1.0 + frame_max) * float(cfg.q_scale)
    Qb = inflate(Q_raw, infl, floor)
    tail_res_b = inflate(residual_l1_tail, infl, floor)
    tail_der_b = inflate(derivative_l1_tail, infl, floor)
    r = float(cfg.radius)
    lhs = Yb + Zb * r + Qb * r * r + tail_res_b
    margin = r - lhs
    rel_margin = margin / r if r > 0 else -math.inf

    dominant_terms = {
        "Y_bound": Yb,
        "Zr_bound": Zb * r,
        "Qr2_bound": Qb * r * r,
        "tail_residual_bound": tail_res_b,
        "tail_derivative_bound_scaled": tail_der_b * r,
    }
    dominant = max(dominant_terms.items(), key=lambda kv: kv[1])[0]

    component_ready = bool(margin > 0 and Zb < 0.5 and residual_l1_total < 1e-5 and cfg.nu <= 1.0015)
    warning = None
    if cfg.nu > 1.0015 and (residual_tail_ratio > 10.0 or derivative_tail_ratio > 10.0):
        warning = "large_weighted_tail_at_this_nu"
    elif Zb >= 0.5:
        warning = "Z_bound_large"
    elif margin <= 0:
        warning = "no_positive_margin_at_this_radius"

    label = "component_ready_candidate" if component_ready else "component_diagnostic_candidate"
    if warning:
        label = warning

    payload: dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase5b_interval_component_record_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "important_warning": "This record uses conservative double-precision component inflation, not a formal interval arithmetic proof.",
        "npz_path": cfg.npz_path,
        "K": K,
        "M": M,
        "omega": omega,
        "grid_size": L,
        "grid_factor": int(cfg.grid_factor),
        "nu": float(cfg.nu),
        "cutoff_spec": cfg.cutoff_spec,
        "cutoff_mode_native_units": int(cutoff_mode),
        "tail_start_frac": float(cfg.tail_start_frac),
        "radius": r,
        "rounding_slack": float(cfg.rounding_slack),
        "interval_inflation": float(cfg.interval_inflation),
        "scalar_residual_linf": scalar_linf,
        "derivative_residual_linf": derivative_linf,
        "residual_l1_nu_total": residual_l1_total,
        "residual_l1_nu_core": residual_l1_core,
        "residual_l1_nu_tail": residual_l1_tail,
        "residual_l1_nu_tail_to_core_observed": residual_tail_ratio,
        "derivative_l1_nu_total": derivative_l1_total,
        "derivative_l1_nu_core": derivative_l1_core,
        "derivative_l1_nu_tail": derivative_l1_tail,
        "derivative_l1_nu_tail_to_core_observed": derivative_tail_ratio,
        "small_divisor_min_denominator": min_den,
        "small_divisor_min_mode": min_mode,
        "cohomology_inverse_linf_resolved": inv_max,
        "cohomology_zero_mode_residual_abs": zero_mode,
        "Y_cohomology_raw": Y,
        "Y_component_bound": Yb,
        "Z_linear_raw": inv_max * geom["upper_triangular_defect_linf_max"],
        "Z_component_bound": Zb,
        "Q_nonlinear_raw": Q_raw,
        "Q_component_bound": Qb,
        "tail_residual_component_bound": tail_res_b,
        "tail_derivative_component_bound": tail_der_b,
        "radii_lhs_component_bound": lhs,
        "radii_margin_component": margin,
        "radii_relative_margin_component": rel_margin,
        "any_positive_component_margin": bool(margin > 0),
        "dominant_component_term": dominant,
        "recommendation_label": label,
        "recommendation_score": 5 if component_ready else (3 if margin > 0 else 1),
    }
    payload.update(geom)

    token = f"K{K:.10f}_M{M}_nu{cfg.nu:g}_{_sanitize_token(cfg.cutoff_spec)}_g{cfg.grid_factor}_r{r:g}".replace(".", "p").replace("-", "m")
    rec_path = Path(cfg.out_dir) / "records" / f"{token}.phase5b_interval_component.json"
    _write_json(rec_path, payload)
    row = dict(payload)
    row["record_path"] = str(rec_path)
    return row


def _row_for_csv(row: dict[str, Any]) -> dict[str, Any]:
    keep = [
        "K", "M", "nu", "cutoff_spec", "cutoff_mode_native_units", "grid_factor", "grid_size", "radius",
        "scalar_residual_linf", "derivative_residual_linf", "residual_l1_nu_total", "derivative_l1_nu_total",
        "small_divisor_min_denominator", "small_divisor_min_mode", "cohomology_inverse_linf_resolved",
        "Y_component_bound", "Z_component_bound", "Q_component_bound", "tail_residual_component_bound",
        "upper_triangular_defect_linf_max", "a21_linf", "twist_average", "twist_min", "twist_max",
        "radii_lhs_component_bound", "radii_margin_component", "radii_relative_margin_component",
        "dominant_component_term", "recommendation_label", "recommendation_score", "record_path", "npz_path"
    ]
    return {k: row.get(k) for k in keep}


def run_phase5b_interval_components(
    *,
    npz_paths: list[str],
    nu_grid: list[float],
    cutoffs: list[str],
    tail_start_fracs: list[float],
    grid_factors: list[int],
    radii: list[float],
    workers: int,
    out_dir: str,
    rounding_slack: float = 1e-10,
    interval_inflation: float = 0.05,
    q_scale: float = 0.038,
    omega_override: float | None = None,
    force: bool = False,
) -> dict[str, Any]:
    out = Path(out_dir)
    if force and out.exists():
        import shutil
        shutil.rmtree(out)
    _ensure_dir(out / "records")

    cfgs: list[Phase5BConfig] = []
    for npz in npz_paths:
        for nu in nu_grid:
            for cutoff in cutoffs:
                for tail in tail_start_fracs:
                    for gf in grid_factors:
                        for radius in radii:
                            cfgs.append(Phase5BConfig(
                                npz_path=npz,
                                nu=float(nu),
                                cutoff_spec=str(cutoff),
                                tail_start_frac=float(tail),
                                grid_factor=int(gf),
                                radius=float(radius),
                                rounding_slack=float(rounding_slack),
                                interval_inflation=float(interval_inflation),
                                q_scale=float(q_scale),
                                omega_override=omega_override,
                                out_dir=str(out),
                            ))

    if workers <= 1:
        rows = [audit_one_phase5b(c) for c in cfgs]
    else:
        from concurrent.futures import ProcessPoolExecutor
        try:
            with ProcessPoolExecutor(max_workers=int(workers)) as ex:
                rows = list(ex.map(audit_one_phase5b, cfgs))
        except BaseException as exc:
            # This diagnostic stage has few tasks but each task may allocate
            # large FFT work arrays.  On shared systems, aggressive process
            # counts can fail before any mathematical calculation is reached.
            # Fall back to serial execution; the numerical records are
            # independent of task scheduling.
            print(f"[phase5b] parallel execution failed ({type(exc).__name__}: {exc}); falling back to serial execution", flush=True)
            rows = [audit_one_phase5b(c) for c in cfgs]

    rows.sort(key=lambda r: (
        -int(bool(r.get("any_positive_component_margin"))),
        -float(r.get("radii_relative_margin_component", -1e99)),
        float(r.get("Z_component_bound", 1e99)),
        float(r.get("Y_component_bound", 1e99)),
    ))

    ranked_path = out / "phase5b_ranked_candidates.json"
    _write_json(ranked_path, {"candidates": rows[:100]})

    csv_path = out / "phase5b_interval_component_results.csv"
    csv_rows = [_row_for_csv(r) for r in rows]
    if csv_rows:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            w.writeheader()
            w.writerows(csv_rows)

    counts: dict[str, int] = {"tasks": len(cfgs), "completed_records": len(rows)}
    for r in rows:
        lab = str(r.get("recommendation_label", "unknown"))
        counts[lab] = counts.get(lab, 0) + 1

    summary = {
        "schema": "theorem_iii_trackb_phase5b_interval_component_summary_v1",
        "status": "phase5b-interval-component-audit-complete",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "important_warning": "Conservative double-precision component-inflated audit only; not a formal outward-rounded interval proof.",
        "parameters": {
            "npz_count": len(npz_paths),
            "nu_grid": nu_grid,
            "cutoffs": cutoffs,
            "tail_start_fracs": tail_start_fracs,
            "grid_factors": grid_factors,
            "radii": radii,
            "workers_requested": workers,
            "rounding_slack": rounding_slack,
            "interval_inflation": interval_inflation,
            "q_scale": q_scale,
        },
        "counts": counts,
        "interpretation_hints": {
            "next_if_component_ready": "Port the residual, small-divisor, frame, and tail bounds to a real outward-rounded/interval backend.",
            "next_if_Z_dominates": "Improve or intervalize the automatic-reducibility defect carefully; keep Z_bound below roughly 0.3-0.5.",
            "next_if_tail_warning": "Use nu=1.001 first, or implement sharper analytic tail majorants before increasing nu.",
        },
        "top_candidates": rows[:40],
    }
    _write_json(out / "phase5b_interval_component_summary.json", summary)
    return summary


def summarize_phase5b(summary_path: str | Path, top: int = 30) -> dict[str, Any]:
    with Path(summary_path).open("r", encoding="utf-8") as f:
        s = json.load(f)
    compact = {
        "schema": "theorem_iii_trackb_phase5b_compact_report_v1",
        "status": s.get("status"),
        "diagnostic_only": s.get("diagnostic_only", True),
        "theorem_facing": s.get("theorem_facing", False),
        "promotion_allowed": s.get("promotion_allowed", False),
        "important_warning": s.get("important_warning"),
        "parameters": s.get("parameters", {}),
        "counts": s.get("counts", {}),
        "top_candidates": s.get("top_candidates", [])[: int(top)],
    }
    return compact
