"""Theorem III Track B Phase 5A: radii-prep / intervalization scaffold.

This module is intentionally diagnostic-only.  It computes proof-shaped
quantities around a selected parameterization seed, but it does not use
outward-rounded arithmetic and it must not be promoted to a theorem-facing
certificate.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import json
import math
import os
import re

import numpy as np

try:
    from .phase4i_common import (
        GOLDEN_ROTATION,
        TWOPI,
        SeedData,
        csv_write,
        derivative_l1_nu,
        ensure_dir,
        fft_coeff,
        interp_values,
        l1_nu,
        load_seed,
        modes,
        sanitize_float_tag,
        scalar_residual_on_grid_from_core,
        spectral_derivative,
        spectral_shift,
        write_json,
    )
except Exception:  # pragma: no cover - only for unusually old overlays
    GOLDEN_ROTATION = (math.sqrt(5.0) - 1.0) / 2.0
    TWOPI = 2.0 * math.pi

    def ensure_dir(path: str | Path) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
        path = Path(path)
        ensure_dir(path.parent)
        tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)

    def csv_write(path: str | Path, rows: Sequence[Dict[str, Any]]) -> None:
        import csv
        path = Path(path)
        ensure_dir(path.parent)
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        keys: List[str] = []
        seen = set()
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    keys.append(k); seen.add(k)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in keys})

    def modes(n: int) -> np.ndarray:
        return np.fft.fftfreq(n, d=1.0/n).astype(int)

    def fft_coeff(v: np.ndarray) -> np.ndarray:
        return np.fft.fft(v) / v.size

    def values_from_coeff(c: np.ndarray) -> np.ndarray:
        return np.fft.ifft(c * c.size)

    def spectral_shift(v: np.ndarray, omega: float) -> np.ndarray:
        n = v.size
        k = modes(n)
        return np.fft.ifft(np.fft.fft(v) * np.exp(1j*TWOPI*k*omega)).real

    def spectral_derivative(v: np.ndarray) -> np.ndarray:
        n = v.size
        k = modes(n)
        return np.fft.ifft(np.fft.fft(v) * (1j*TWOPI*k)).real

    def interp_values(v: np.ndarray, L: int) -> np.ndarray:
        v = np.asarray(v, dtype=float)
        M = v.size
        if L == M:
            return v.copy()
        if L < M:
            raise ValueError(f"Cannot interpolate from M={M} to smaller L={L}")
        cM = fft_coeff(v)
        cL = np.zeros(L, dtype=complex)
        kM = modes(M)
        idxL = {int(k): i for i, k in enumerate(modes(L))}
        for i, k in enumerate(kM):
            j = idxL.get(int(k))
            if j is not None:
                cL[j] = cM[i]
        return values_from_coeff(cL).real

    def scalar_residual_on_grid_from_core(u_core: np.ndarray, K: float, omega: float, L: int, sign: int = 1) -> np.ndarray:
        u = interp_values(u_core, L)
        theta = np.arange(L, dtype=float) / float(L)
        return spectral_shift(u, omega) - 2*u + spectral_shift(u, -omega) - sign * (K/TWOPI)*np.sin(TWOPI*(theta+u))

    def l1_nu(v: np.ndarray, nu: float) -> float:
        c = fft_coeff(v); k = np.abs(modes(v.size))
        return float(np.sum(np.abs(c) * (float(nu)**k)))

    def derivative_l1_nu(v: np.ndarray, nu: float) -> float:
        c = fft_coeff(v); k = np.abs(modes(v.size))
        return float(np.sum(np.abs(c) * (TWOPI*k) * (float(nu)**k)))

    def sanitize_float_tag(x: float, ndigits: int = 10) -> str:
        return f"{x:.{ndigits}f}".replace("-", "m").replace(".", "p")

    class SeedData:  # minimal stub
        def __init__(self, path: str, u: np.ndarray, K: float, omega: float, M: int, keys: List[str]):
            self.path, self.u, self.K, self.omega, self.M, self.keys = path, u, K, omega, M, keys

    def load_seed(npz_path: str | Path, omega_override: Optional[float] = None) -> SeedData:
        with np.load(str(npz_path), allow_pickle=False) as z:
            keys = list(z.files)
            u = None
            for nm in ["u", "u_grid", "u_values", "embedding_u", "phase_u", "graph_u", "solution_u", "u_real", "u_samples"]:
                if nm in z.files:
                    u = np.asarray(z[nm], dtype=float).reshape(-1); break
            if u is None:
                raise KeyError(f"Could not find u in {npz_path}; keys={keys}")
            K = float(np.asarray(z["K"]).reshape(-1)[0]) if "K" in z.files else float(re.search(r"K([0-9]+p[0-9]+)", Path(npz_path).name).group(1).replace("p", "."))
            omega = float(np.asarray(z["omega"]).reshape(-1)[0]) if "omega" in z.files else GOLDEN_ROTATION
        if omega_override is not None:
            omega = float(omega_override)
        return SeedData(str(npz_path), u, K, omega, u.size, keys)


@dataclass(frozen=True)
class Phase5ARadiiPrepConfig:
    npz_path: str
    nu: float
    cutoff_spec: str
    tail_start_frac: float
    grid_factor: int
    out_dir: str
    omega_override: Optional[float] = None
    force: bool = False
    sign: int = 1
    radii: Tuple[float, ...] = (1e-10, 3e-10, 1e-9, 3e-9, 1e-8, 3e-8, 1e-7, 3e-7, 1e-6, 3e-6, 1e-5)


def _record_path(out_dir: str, npz_path: str, nu: float, cutoff_spec: str, tail_start_frac: float, grid_factor: int) -> Path:
    cut_tag = cutoff_spec.replace(":", "").replace(".", "p")
    tag = f"{Path(npz_path).stem}_nu{sanitize_float_tag(float(nu), 4)}_{cut_tag}_tail{sanitize_float_tag(float(tail_start_frac),3)}_Lx{int(grid_factor)}"
    return Path(out_dir) / "records" / (tag + ".phase5a_radii_prep.json")


def _parse_cutoff(cutoff_spec: str, M: int) -> Tuple[Optional[int], str]:
    s = str(cutoff_spec).strip().lower()
    max_mode = M // 2 - 1
    if s in {"full", "none", "max"}:
        return max_mode, "full"
    if s.startswith("frac:"):
        frac = float(s.split(":", 1)[1])
        return max(1, min(max_mode, int(math.floor(frac * max_mode)))), f"frac:{frac:g}"
    if s.startswith("mode:"):
        val = int(s.split(":", 1)[1])
        return max(1, min(max_mode, val)), f"mode:{val}"
    # Allow bare integers for convenience.
    try:
        val = int(s)
        return max(1, min(max_mode, val)), f"mode:{val}"
    except Exception as exc:
        raise ValueError(f"Unrecognized cutoff spec {cutoff_spec!r}") from exc


def _mode_mask(n: int, cutoff_mode: Optional[int]) -> np.ndarray:
    k = np.abs(modes(n))
    if cutoff_mode is None:
        return np.ones(n, dtype=bool)
    return k <= int(cutoff_mode)


def _weighted_coeff_norm_from_coeff(c: np.ndarray, nu: float, derivative: bool = False, mask: Optional[np.ndarray] = None) -> float:
    n = c.size
    kk = np.abs(modes(n)).astype(float)
    weights = float(nu) ** kk
    if derivative:
        weights = weights * (TWOPI * kk)
    vals = np.abs(c) * weights
    if mask is not None:
        vals = vals[mask]
    return float(np.sum(vals))


def _tail_shell_ratios(cabs: np.ndarray, cutoff_mode: int, tail_start_frac: float) -> Dict[str, Any]:
    n = cabs.size
    kk = np.abs(modes(n))
    max_mode = int(np.max(kk))
    start = max(1, int(math.floor(float(tail_start_frac) * max_mode)))
    shell_mask = (kk >= start) & (kk <= max_mode)
    shell_vals = cabs[shell_mask]
    core_vals = cabs[kk <= cutoff_mode]
    tail_vals = cabs[kk > cutoff_mode]

    # Crude geometric envelope from nonzero sorted-by-mode maxima.  Diagnostic only.
    mode_max = []
    for m in range(start, max_mode + 1):
        vals = cabs[kk == m]
        if vals.size:
            mode_max.append(float(np.max(vals)))
    nz = [x for x in mode_max if x > 0]
    if len(nz) >= 4:
        ratios = [nz[i+1] / nz[i] for i in range(len(nz)-1) if nz[i] > 0]
        # Use a conservative high quantile but cap below 1 if possible.
        ratio_q90 = float(np.quantile(ratios, 0.90)) if ratios else 1.0
        ratio_max = float(max(ratios)) if ratios else 1.0
        geom_ratio_proxy = min(0.999999, max(0.0, ratio_q90))
    else:
        ratio_q90 = None
        ratio_max = None
        geom_ratio_proxy = None
    return {
        "tail_start_mode": int(start),
        "tail_start_frac": float(tail_start_frac),
        "observed_core_l1_plain": float(np.sum(core_vals)),
        "observed_tail_l1_plain": float(np.sum(tail_vals)),
        "observed_tail_to_core_l1_plain": float(np.sum(tail_vals) / max(np.sum(core_vals), 1e-300)),
        "shell_max_abs_coeff": float(np.max(shell_vals)) if shell_vals.size else 0.0,
        "shell_sum_abs_coeff": float(np.sum(shell_vals)) if shell_vals.size else 0.0,
        "geom_ratio_q90_proxy": ratio_q90,
        "geom_ratio_max_observed": ratio_max,
        "geom_ratio_for_tail_proxy": geom_ratio_proxy,
    }


def _small_divisor_stats(n: int, omega: float, cutoff_mode: int, nu: float) -> Dict[str, Any]:
    kk = modes(n)
    mask = (np.abs(kk) > 0) & (np.abs(kk) <= cutoff_mode)
    ksel = kk[mask]
    den = np.abs(np.exp(1j * TWOPI * ksel * float(omega)) - 1.0)
    inv = 1.0 / np.maximum(den, 1e-300)
    worst_idx = int(np.argmax(inv)) if inv.size else 0
    weights = float(nu) ** np.abs(ksel)
    return {
        "small_divisor_cutoff_mode": int(cutoff_mode),
        "small_divisor_min_denominator": float(np.min(den)) if den.size else None,
        "small_divisor_min_mode": int(ksel[int(np.argmin(den))]) if den.size else None,
        "cohomology_inverse_linf_resolved": float(np.max(inv)) if inv.size else None,
        "cohomology_inverse_linf_mode": int(ksel[worst_idx]) if inv.size else None,
        "cohomology_inverse_weighted_proxy": float(np.max(inv * weights / np.maximum(weights, 1e-300))) if inv.size else None,
    }


def _cohomology_correction_norms(cR: np.ndarray, omega: float, cutoff_mode: int, nu: float) -> Dict[str, Any]:
    n = cR.size
    kk = modes(n)
    mask = (np.abs(kk) > 0) & (np.abs(kk) <= cutoff_mode)
    den = np.abs(np.exp(1j * TWOPI * kk * float(omega)) - 1.0)
    corr = np.zeros_like(cR, dtype=complex)
    corr[mask] = cR[mask] / (np.exp(1j * TWOPI * kk[mask] * float(omega)) - 1.0)
    weights = float(nu) ** np.abs(kk)
    deriv_weights = weights * (TWOPI * np.abs(kk))
    return {
        "cohomology_residual_correction_l1_nu_proxy": float(np.sum(np.abs(corr) * weights)),
        "cohomology_residual_correction_derivative_l1_nu_proxy": float(np.sum(np.abs(corr) * deriv_weights)),
        "cohomology_zero_mode_residual_abs": float(abs(cR[0])),
        "cohomology_correction_max_coeff_proxy": float(np.max(np.abs(corr))) if corr.size else 0.0,
    }


def _standard_map_frame_metrics(u_core: np.ndarray, K: float, omega: float, L: int, sign: int = 1) -> Dict[str, Any]:
    u = interp_values(u_core, L)
    theta = np.arange(L, dtype=float) / float(L)
    up = spectral_derivative(u)
    up_m = spectral_shift(up, -omega)
    tx = 1.0 + up
    tr = up - up_m
    norm2 = tx*tx + tr*tr
    nx = -tr / norm2
    nr = tx / norm2

    # target frame recomputed from shifted tangent
    tx_t = spectral_shift(tx, omega)
    tr_t = spectral_shift(tr, omega)
    norm2_t = tx_t*tx_t + tr_t*tr_t
    nx_t = -tr_t / norm2_t
    nr_t = tx_t / norm2_t

    x = theta + u
    c = np.cos(TWOPI * x)
    # sign=1 matches the scalar residual convention used by the successful diagnostics.
    b = sign * K * c
    # DF * source tangent/normal for map [[1+b,1],[b,1]]
    y1x = (1.0 + b) * tx + tr
    y1r = b * tx + tr
    y2x = (1.0 + b) * nx + nr
    y2r = b * nx + nr

    # Coordinates in target frame M_t^{-1} y.  Since det([T,N])=1,
    # inverse is [[nr_t, -nx_t], [-tr_t, tx_t]].
    a11 = nr_t * y1x - nx_t * y1r
    a21 = -tr_t * y1x + tx_t * y1r
    a12 = nr_t * y2x - nx_t * y2r
    a22 = -tr_t * y2x + tx_t * y2r

    source_det = tx*nr - nx*tr
    target_det = tx_t*nr_t - nx_t*tr_t
    frame_norm = np.sqrt(tx*tx + tr*tr) + np.sqrt(nx*nx + nr*nr)
    target_frame_norm = np.sqrt(tx_t*tx_t + tr_t*tr_t) + np.sqrt(nx_t*nx_t + nr_t*nr_t)

    return {
        "frame_grid_size": int(L),
        "frame_tangent_norm_min": float(np.min(np.sqrt(norm2))),
        "frame_tangent_norm_max": float(np.max(np.sqrt(norm2))),
        "frame_normal_norm_max": float(np.max(np.sqrt(nx*nx + nr*nr))),
        "frame_source_det_defect_linf": float(np.max(np.abs(source_det - 1.0))),
        "frame_target_det_defect_linf": float(np.max(np.abs(target_det - 1.0))),
        "frame_norm_sum_max_proxy": float(np.max(frame_norm)),
        "target_frame_norm_sum_max_proxy": float(np.max(target_frame_norm)),
        "a11_minus_1_linf": float(np.max(np.abs(a11 - 1.0))),
        "a21_linf": float(np.max(np.abs(a21))),
        "a22_minus_1_linf": float(np.max(np.abs(a22 - 1.0))),
        "upper_triangular_defect_linf_max": float(max(np.max(np.abs(a11 - 1.0)), np.max(np.abs(a21)), np.max(np.abs(a22 - 1.0)))),
        "twist_average": float(np.mean(a12)),
        "twist_min": float(np.min(a12)),
        "twist_max": float(np.max(a12)),
        "twist_centered_linf": float(np.max(np.abs(a12 - np.mean(a12)))),
    }


def _candidate_radii_analysis(Y: float, Z: float, Q: float, radii: Sequence[float]) -> Dict[str, Any]:
    rows = []
    best = None
    for r in radii:
        rr = float(r)
        lhs = float(Y + Z*rr + Q*rr*rr)
        margin = float(rr - lhs)
        row = {"r": rr, "lhs_proxy": lhs, "margin_proxy": margin, "relative_margin_proxy": margin / max(rr, 1e-300)}
        rows.append(row)
        if best is None or row["margin_proxy"] > best["margin_proxy"]:
            best = row
    positive = [row for row in rows if row["margin_proxy"] > 0]
    return {
        "radii_rows": rows,
        "best_radius_proxy": best["r"] if best else None,
        "best_radii_margin_proxy": best["margin_proxy"] if best else None,
        "best_relative_margin_proxy": best["relative_margin_proxy"] if best else None,
        "any_positive_radii_margin_proxy": bool(positive),
        "positive_radius_count_proxy": int(len(positive)),
    }


def _readiness_label(rec: Dict[str, Any]) -> Tuple[str, int]:
    scalar = rec.get("scalar_residual_linf") or math.inf
    deriv = rec.get("derivative_residual_linf") or math.inf
    tri = rec.get("upper_triangular_defect_linf_max") or math.inf
    y = rec.get("Y_cohomology_proxy") or math.inf
    pos = bool(rec.get("any_positive_radii_margin_proxy"))
    if scalar <= 2e-9 and deriv <= 3e-5 and tri <= 1.5e-4:
        return "excellent_pre_interval_candidate", 6
    if scalar <= 1e-8 and deriv <= 5e-5 and tri <= 2.5e-4:
        return "strong_pre_interval_candidate", 5
    if scalar <= 1e-8 and deriv <= 8e-5 and tri <= 4e-4:
        return "moderate_pre_interval_candidate", 4
    if scalar <= 1e-7 and deriv <= 2e-4:
        return "needs_more_radii_or_frame_work", 3
    return "weak_or_not_ready", 1


def audit_phase5a_one(cfg: Phase5ARadiiPrepConfig) -> Dict[str, Any]:
    out_path = _record_path(cfg.out_dir, cfg.npz_path, cfg.nu, cfg.cutoff_spec, cfg.tail_start_frac, cfg.grid_factor)
    if out_path.exists() and not cfg.force:
        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)
    seed = load_seed(cfg.npz_path, omega_override=cfg.omega_override)
    M = int(seed.M)
    L = int(M * int(cfg.grid_factor))
    cutoff_mode, cutoff_label = _parse_cutoff(cfg.cutoff_spec, M)
    # When evaluating on an oversampled grid, interpret cutoff in native-mode units.
    cutoff_mode_L = int(cutoff_mode)

    R = scalar_residual_on_grid_from_core(seed.u, seed.K, seed.omega, L, sign=cfg.sign)
    dR = spectral_derivative(R)
    cR = fft_coeff(R)
    kk = np.abs(modes(L))
    core_mask = kk <= cutoff_mode_L
    tail_mask = kk > cutoff_mode_L

    scalar_linf = float(np.max(np.abs(R)))
    derivative_linf = float(np.max(np.abs(dR)))
    residual_l1_nu_total = _weighted_coeff_norm_from_coeff(cR, cfg.nu, derivative=False)
    residual_l1_nu_core = _weighted_coeff_norm_from_coeff(cR, cfg.nu, derivative=False, mask=core_mask)
    residual_l1_nu_tail = _weighted_coeff_norm_from_coeff(cR, cfg.nu, derivative=False, mask=tail_mask)
    derivative_l1_nu_total = _weighted_coeff_norm_from_coeff(cR, cfg.nu, derivative=True)
    derivative_l1_nu_core = _weighted_coeff_norm_from_coeff(cR, cfg.nu, derivative=True, mask=core_mask)
    derivative_l1_nu_tail = _weighted_coeff_norm_from_coeff(cR, cfg.nu, derivative=True, mask=tail_mask)

    small = _small_divisor_stats(L, seed.omega, cutoff_mode_L, cfg.nu)
    cohom = _cohomology_correction_norms(cR, seed.omega, cutoff_mode_L, cfg.nu)
    tail = _tail_shell_ratios(np.abs(cR), cutoff_mode_L, cfg.tail_start_frac)
    frame = _standard_map_frame_metrics(seed.u, seed.K, seed.omega, L, sign=cfg.sign)

    # Diagnostic proof-shaped constants.  These are deliberately named proxies.
    Y = cohom["cohomology_residual_correction_l1_nu_proxy"]
    Z = min(0.999999999, float(frame["upper_triangular_defect_linf_max"]) * max(float(small.get("cohomology_inverse_linf_resolved") or 1.0), 1.0))
    # A crude nonlinear proxy, scaled by the map curvature and frame size.  This is not rigorous.
    frame_scale = max(float(frame["frame_norm_sum_max_proxy"]), float(frame["target_frame_norm_sum_max_proxy"]), 1.0)
    Q = float((TWOPI * abs(seed.K) + abs(seed.K) + 1.0) * frame_scale * frame_scale)
    rad = _candidate_radii_analysis(Y, Z, Q, cfg.radii)

    rec: Dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase5a_radii_prep_record_v1",
        "status": "phase5a-radii-prep-record-complete",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "important_warning": "Double-precision proof-shaped proxies only; no outward rounding; not a theorem certificate.",
        "npz_path": cfg.npz_path,
        "K": float(seed.K),
        "omega": float(seed.omega),
        "M": int(M),
        "grid_factor": int(cfg.grid_factor),
        "grid_size": int(L),
        "nu": float(cfg.nu),
        "cutoff_spec": cfg.cutoff_spec,
        "cutoff_label": cutoff_label,
        "cutoff_mode_native_units": int(cutoff_mode),
        "tail_start_frac": float(cfg.tail_start_frac),
        "scalar_residual_linf": scalar_linf,
        "derivative_residual_linf": derivative_linf,
        "residual_l1_nu_total": residual_l1_nu_total,
        "residual_l1_nu_core": residual_l1_nu_core,
        "residual_l1_nu_tail_observed": residual_l1_nu_tail,
        "residual_l1_nu_tail_to_core_observed": float(residual_l1_nu_tail / max(residual_l1_nu_core, 1e-300)),
        "derivative_l1_nu_total": derivative_l1_nu_total,
        "derivative_l1_nu_core": derivative_l1_nu_core,
        "derivative_l1_nu_tail_observed": derivative_l1_nu_tail,
        "derivative_l1_nu_tail_to_core_observed": float(derivative_l1_nu_tail / max(derivative_l1_nu_core, 1e-300)),
        **small,
        **cohom,
        **tail,
        **frame,
        "Y_cohomology_proxy": float(Y),
        "Z_linear_reducibility_proxy": float(Z),
        "Q_nonlinear_proxy": float(Q),
    }
    rec.update(rad)
    label, score = _readiness_label(rec)
    rec["recommendation_label"] = label
    rec["recommendation_score"] = int(score)

    # Dominant obstruction heuristic.
    pieces = {
        "Y_cohomology_proxy": abs(float(Y)),
        "Z_linear_reducibility_proxy": abs(float(Z)),
        "Q_nonlinear_proxy_scaled_1e-8sq": abs(float(Q)) * 1e-16,
        "observed_tail_l1_nu": abs(float(residual_l1_nu_tail)),
        "upper_triangular_defect": abs(float(frame["upper_triangular_defect_linf_max"])),
    }
    rec["dominant_proxy_term"] = max(pieces, key=pieces.get)
    rec["dominant_proxy_value"] = float(pieces[rec["dominant_proxy_term"]])

    write_json(out_path, rec)
    return rec


def _compact_row(rec: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "K", "M", "grid_factor", "grid_size", "nu", "cutoff_spec", "cutoff_mode_native_units", "tail_start_frac",
        "scalar_residual_linf", "derivative_residual_linf", "upper_triangular_defect_linf_max", "a21_linf",
        "twist_average", "twist_min", "twist_max", "frame_tangent_norm_min", "frame_tangent_norm_max",
        "small_divisor_min_denominator", "small_divisor_min_mode", "cohomology_inverse_linf_resolved",
        "residual_l1_nu_total", "derivative_l1_nu_total", "residual_l1_nu_tail_to_core_observed", "derivative_l1_nu_tail_to_core_observed",
        "cohomology_residual_correction_l1_nu_proxy", "cohomology_zero_mode_residual_abs",
        "Y_cohomology_proxy", "Z_linear_reducibility_proxy", "Q_nonlinear_proxy",
        "best_radius_proxy", "best_radii_margin_proxy", "best_relative_margin_proxy", "any_positive_radii_margin_proxy",
        "dominant_proxy_term", "recommendation_label", "recommendation_score", "npz_path",
    ]
    return {k: rec.get(k) for k in keys}


def run_phase5a_radii_prep(
    npz_paths: Sequence[str],
    nu_grid: Sequence[float],
    cutoff_specs: Sequence[str],
    tail_start_fracs: Sequence[float],
    grid_factors: Sequence[int],
    out_dir: str,
    workers: int = 1,
    omega_override: Optional[float] = None,
    force: bool = False,
    radii: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    ensure_dir(Path(out_dir) / "records")
    radii_tuple = tuple(float(x) for x in (radii or (1e-10, 3e-10, 1e-9, 3e-9, 1e-8, 3e-8, 1e-7, 3e-7, 1e-6, 3e-6, 1e-5)))
    cfgs: List[Phase5ARadiiPrepConfig] = []
    for p in npz_paths:
        for gf in grid_factors:
            for nu in nu_grid:
                for cut in cutoff_specs:
                    for tsf in tail_start_fracs:
                        cfgs.append(Phase5ARadiiPrepConfig(
                            npz_path=str(p), nu=float(nu), cutoff_spec=str(cut), tail_start_frac=float(tsf),
                            grid_factor=int(gf), out_dir=out_dir, omega_override=omega_override, force=force, radii=radii_tuple,
                        ))
    if workers and workers > 1 and len(cfgs) > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=min(int(workers), len(cfgs))) as ex:
            records = list(ex.map(audit_phase5a_one, cfgs))
    else:
        records = [audit_phase5a_one(c) for c in cfgs]

    rows = [_compact_row(r) for r in records]
    rows.sort(key=lambda r: (
        -(r.get("recommendation_score") or 0),
        abs(r.get("upper_triangular_defect_linf_max") or math.inf),
        abs(r.get("derivative_residual_linf") or math.inf),
        abs(r.get("scalar_residual_linf") or math.inf),
    ))
    counts: Dict[str, int] = {"tasks": len(cfgs), "completed_records": len(records)}
    for r in rows:
        lab = str(r.get("recommendation_label"))
        counts[lab] = counts.get(lab, 0) + 1
    summary = {
        "schema": "theorem_iii_trackb_phase5a_radii_prep_summary_v1",
        "status": "phase5a-radii-prep-complete",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "important_warning": "These are double-precision radii-prep proxies, not interval or theorem-facing bounds.",
        "counts": counts,
        "parameters": {
            "npz_count": len(npz_paths),
            "nu_grid": list(map(float, nu_grid)),
            "cutoff_specs": list(map(str, cutoff_specs)),
            "tail_start_fracs": list(map(float, tail_start_fracs)),
            "grid_factors": list(map(int, grid_factors)),
            "radii": list(map(float, radii_tuple)),
            "workers_requested": int(workers),
            "workers_used": min(int(workers), len(cfgs)) if workers else 1,
        },
        "interpretation_hints": {
            "next_if_promising": "Implement outward-rounded residual/tail/small-divisor bounds for the selected nu/cutoff/core model.",
            "next_if_Z_dominates": "Improve automatic-reducibility frame or carry H1 seed into FHL-frame Newton.",
            "next_if_tail_dominates": "Use smaller nu, stricter cutoff, or sharper analytic tail model.",
            "next_if_Y_dominates": "Improve seed residual or preconditioned cohomology solve.",
        },
        "top_candidates": rows,
    }
    write_json(Path(out_dir) / "phase5a_radii_prep_summary.json", summary)
    csv_write(Path(out_dir) / "phase5a_radii_prep_results.csv", rows)
    # Also save top records for easy inspection.
    write_json(Path(out_dir) / "phase5a_ranked_candidates.json", {"top_candidates": rows[:50]})
    return summary
