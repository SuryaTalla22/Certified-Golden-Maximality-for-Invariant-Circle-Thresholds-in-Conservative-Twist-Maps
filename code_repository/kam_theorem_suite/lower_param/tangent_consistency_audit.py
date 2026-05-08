"""Phase 4g tangent/embedding consistency diagnostics for Theorem III Track B.

Diagnostic only.  This module is intentionally standalone/robust: it loads a saved
Track-B embedding .npz, infers the periodic graph u(theta), and compares the
scalar invariance residual with the tangent/cocycle residual for both standard-map
sign conventions.  The goal is to distinguish (i) true aliasing/high-frequency
residual from (ii) a frame/map-convention/derivative mismatch in the automatic
reducibility audit.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

GOLDEN_OMEGA = (math.sqrt(5.0) - 1.0) / 2.0


def _real_array(z: np.lib.npyio.NpzFile, names: Sequence[str]) -> Optional[np.ndarray]:
    for name in names:
        if name in z.files:
            arr = np.asarray(z[name])
            if arr.ndim == 1 and arr.size >= 8:
                if np.iscomplexobj(arr):
                    if np.max(np.abs(arr.imag)) < 1e-8 * max(1.0, float(np.max(np.abs(arr.real)))):
                        arr = arr.real
                    else:
                        continue
                return np.asarray(arr, dtype=float)
    return None


def _scalar_from_npz_or_name(z: np.lib.npyio.NpzFile, names: Sequence[str], path: str, regex: Optional[str] = None) -> Optional[float]:
    for name in names:
        if name in z.files:
            arr = np.asarray(z[name])
            if arr.size == 1:
                try:
                    return float(arr.reshape(()))
                except Exception:
                    pass
    if regex:
        m = re.search(regex, Path(path).name)
        if m:
            s = m.group(1).replace("p", ".")
            try:
                return float(s)
            except Exception:
                return None
    return None


def _infer_u_from_npz(npz_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    meta: Dict[str, Any] = {}
    with np.load(npz_path, allow_pickle=False) as z:
        meta["npz_keys"] = list(z.files)
        K = _scalar_from_npz_or_name(z, ["K", "K_target", "k", "parameter"], npz_path, r"K([0-9]+p[0-9]+)")
        omega = _scalar_from_npz_or_name(z, ["omega", "rotation", "rho"], npz_path, None)
        if omega is None:
            omega = GOLDEN_OMEGA
        meta["K"] = K
        meta["omega"] = omega

        # Most likely names from the Track-B bundles.
        u = _real_array(z, ["u", "u_grid", "u_values", "u_theta", "graph_u", "embedding_u"])
        if u is not None:
            meta["u_source"] = "direct_u_key"
            return u, meta

        # If x is saved as a lift sampled at theta_j, recover periodic u = x - theta.
        x = _real_array(z, ["x", "x_grid", "x_values", "embedding_x"])
        if x is not None:
            n = x.size
            theta = np.arange(n, dtype=float) / float(n)
            u = x - theta
            # remove nearest integer/lift drift and mean-wrap if necessary
            u = u - np.round(np.median(u))
            meta["u_source"] = "x_minus_theta"
            return u, meta

        # If coefficients are saved, reconstruct grid values.
        for name in ["u_hat", "u_coeffs", "coeffs", "fourier_coeffs"]:
            if name in z.files:
                coeff = np.asarray(z[name])
                if coeff.ndim == 1 and coeff.size >= 8:
                    # Guess numpy FFT ordering if same length; otherwise assume centered coefficients.
                    if coeff.size % 2 == 0:
                        u = np.fft.ifft(coeff).real * coeff.size
                    else:
                        # centered modes -m..m; reconstruct on same number of grid points
                        n = coeff.size
                        modes = np.arange(-(n // 2), n // 2 + 1)
                        theta = np.arange(n, dtype=float) / float(n)
                        u = np.zeros(n, dtype=complex)
                        for c, k in zip(coeff, modes):
                            u += c * np.exp(2j * np.pi * k * theta)
                        u = u.real
                    meta["u_source"] = f"coefficients:{name}"
                    return np.asarray(u, dtype=float), meta

    raise ValueError(f"Could not infer periodic graph u(theta) from {npz_path}")


def _fft_freq_int(n: int) -> np.ndarray:
    return np.fft.fftfreq(n, d=1.0 / n)


def _spectral_shift(values: np.ndarray, alpha: float, out_n: Optional[int] = None) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    n = values.size
    coeff = np.fft.fft(values)
    if out_n is None or out_n == n:
        k = _fft_freq_int(n)
        return np.fft.ifft(coeff * np.exp(2j * np.pi * k * alpha)).real
    # evaluate trigonometric interpolant on out_n points, shifted by alpha
    theta = np.arange(out_n, dtype=float) / float(out_n) + alpha
    k = _fft_freq_int(n)
    # chunked evaluation avoids huge memory for large out_n? n=4096, out=16384 is okay-ish but use FFT zero-padding instead.
    # Construct zero-padded FFT coefficients for evaluation on out_n grid at theta+alpha.
    if out_n < n:
        raise ValueError("out_n must be >= n")
    # zero pad in frequency domain preserving FFT ordering
    coeff_shifted = coeff * np.exp(2j * np.pi * k * alpha)
    pad = np.zeros(out_n, dtype=complex)
    half = n // 2
    pad[:half] = coeff_shifted[:half]
    pad[-(n - half):] = coeff_shifted[half:]
    return np.fft.ifft(pad).real * (out_n / n)


def _spectral_derivative(values: np.ndarray, out_n: Optional[int] = None, shift: float = 0.0) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    n = values.size
    coeff = np.fft.fft(values)
    k = _fft_freq_int(n)
    dcoeff = (2j * np.pi * k) * coeff
    if out_n is None or out_n == n:
        return np.fft.ifft(dcoeff * np.exp(2j * np.pi * k * shift)).real
    if out_n < n:
        raise ValueError("out_n must be >= n")
    dcoeff_shifted = dcoeff * np.exp(2j * np.pi * k * shift)
    pad = np.zeros(out_n, dtype=complex)
    half = n // 2
    pad[:half] = dcoeff_shifted[:half]
    pad[-(n - half):] = dcoeff_shifted[half:]
    return np.fft.ifft(pad).real * (out_n / n)


def _eval_residual_and_tangent(u: np.ndarray, K: float, omega: float, sign: int, L: Optional[int] = None) -> Dict[str, float]:
    # sign s corresponds to map y' = y + s*K/(2pi)*sin(2pi*x)
    # scalar residual is u+ - 2u + u- - s*a*sin(2pi(theta+u)).
    u = np.asarray(u, dtype=float)
    n = u.size
    if L is None:
        L = n
    theta = np.arange(L, dtype=float) / float(L)
    uu = _spectral_shift(u, 0.0, L)
    up = _spectral_shift(u, omega, L)
    um = _spectral_shift(u, -omega, L)
    du = _spectral_derivative(u, L, 0.0)
    dup = _spectral_derivative(u, L, omega)
    dum = _spectral_derivative(u, L, -omega)

    a = K / (2.0 * np.pi)
    x = theta + uu
    residual = up - 2.0 * uu + um - sign * a * np.sin(2.0 * np.pi * x)

    # derivative of scalar residual. Should match x-component tangent residual.
    derivative_residual = dup - 2.0 * du + dum - sign * K * np.cos(2.0 * np.pi * x) * (1.0 + du)

    x_tan = 1.0 + du
    y_tan = du - dum
    target_x_tan = 1.0 + dup
    target_y_tan = dup - du
    c = np.cos(2.0 * np.pi * x)
    map_x_tan = (1.0 + sign * K * c) * x_tan + y_tan
    map_y_tan = sign * K * c * x_tan + y_tan
    tan_x_res = target_x_tan - map_x_tan
    tan_y_res = target_y_tan - map_y_tan

    # Direct derivative and 2D tangent x residual should be the same up to roundoff.
    return {
        "grid_size": int(L),
        "sign": int(sign),
        "scalar_residual_linf": float(np.max(np.abs(residual))),
        "scalar_residual_rms": float(np.sqrt(np.mean(residual**2))),
        "derivative_residual_linf": float(np.max(np.abs(derivative_residual))),
        "tangent_x_residual_linf": float(np.max(np.abs(tan_x_res))),
        "tangent_y_residual_linf": float(np.max(np.abs(tan_y_res))),
        "tangent_combined_linf": float(max(np.max(np.abs(tan_x_res)), np.max(np.abs(tan_y_res)))),
        "derivative_vs_tangent_x_linf": float(np.max(np.abs(derivative_residual - tan_x_res))),
        "u_linf": float(np.max(np.abs(uu))),
        "du_linf": float(np.max(np.abs(du))),
        "x_tangent_min_abs": float(np.min(np.abs(x_tan))),
        "x_tangent_max_abs": float(np.max(np.abs(x_tan))),
    }


def _spectrum_metrics(u: np.ndarray, K: float, omega: float, sign: int, core_n: int) -> Dict[str, Any]:
    row = _eval_residual_and_tangent(u, K, omega, sign, core_n)
    # Compute spectrum of scalar residual on core grid.
    n = core_n
    theta = np.arange(n, dtype=float) / float(n)
    uu = _spectral_shift(u, 0.0, n)
    up = _spectral_shift(u, omega, n)
    um = _spectral_shift(u, -omega, n)
    a = K / (2.0 * np.pi)
    res = up - 2.0 * uu + um - sign * a * np.sin(2.0 * np.pi * (theta + uu))
    coeff = np.fft.fft(res) / n
    mag = np.abs(coeff)
    k = np.abs(_fft_freq_int(n)).astype(int)
    total_l1 = float(np.sum(mag))
    metrics: Dict[str, Any] = dict(row)
    for frac in [0.25, 0.5, 0.75, 0.9, 0.95]:
        cutoff = int((n // 2) * frac)
        tail = float(np.sum(mag[k >= cutoff]))
        metrics[f"scalar_residual_tail_l1_frac_{frac:.2f}"] = tail
        metrics[f"scalar_residual_tail_ratio_frac_{frac:.2f}"] = tail / total_l1 if total_l1 else 0.0
    # largest modes excluding zero
    order = np.argsort(mag)[::-1]
    top = []
    for idx in order[:12]:
        top.append({"mode": int(_fft_freq_int(n)[idx]), "abs_coeff": float(mag[idx])})
    metrics["scalar_residual_top_modes"] = top
    metrics["scalar_residual_l1_coeff"] = total_l1
    return metrics


@dataclass
class TangentConsistencyConfig:
    npz_path: str
    grid_factors: Tuple[int, ...] = (1, 2, 4)
    force_sign: Optional[int] = None
    out_dir: str = "artifacts/proof_audit/theorem_iii_trackb/phase4g_tangent_consistency"
    force: bool = False


def audit_tangent_consistency(cfg: TangentConsistencyConfig) -> Dict[str, Any]:
    u, meta = _infer_u_from_npz(cfg.npz_path)
    K = meta.get("K")
    omega = meta.get("omega") or GOLDEN_OMEGA
    if K is None:
        raise ValueError(f"Could not infer K from {cfg.npz_path}; pass an npz containing K or using K... filename")
    n = int(u.size)
    signs = [int(cfg.force_sign)] if cfg.force_sign is not None else [1, -1]
    grid_rows = []
    for s in signs:
        for fac in cfg.grid_factors:
            L = int(n * fac)
            grid_rows.append(_eval_residual_and_tangent(u, float(K), float(omega), s, L))
    # Choose sign by smallest scalar residual on native grid.
    native = [r for r in grid_rows if r["grid_size"] == n]
    best_native = min(native, key=lambda r: r["scalar_residual_linf"])
    best_sign = int(best_native["sign"])
    spectrum = _spectrum_metrics(u, float(K), float(omega), best_sign, n)

    # A direct diagnostic decision.
    best_rows_for_sign = [r for r in grid_rows if r["sign"] == best_sign]
    max_scalar_over_grids = max(r["scalar_residual_linf"] for r in best_rows_for_sign)
    max_tangent_over_grids = max(r["tangent_combined_linf"] for r in best_rows_for_sign)
    derivative_consistency = max(r["derivative_vs_tangent_x_linf"] for r in best_rows_for_sign)
    label = "unknown"
    if derivative_consistency > 1e-7:
        label = "formula_or_derivative_mismatch"
    elif max_scalar_over_grids < 1e-8 and max_tangent_over_grids > 1e-4:
        label = "high_frequency_derivative_or_aliasing_suspected"
    elif max_scalar_over_grids < 1e-8 and max_tangent_over_grids <= 1e-4:
        label = "tangent_consistency_good_enough_for_next_prep"
    else:
        label = "seed_residual_too_large_for_interval_prep"

    result: Dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase4g_tangent_consistency_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "npz_path": cfg.npz_path,
        "K": float(K),
        "omega": float(omega),
        "M": n,
        "metadata": meta,
        "best_sign": best_sign,
        "best_native_scalar_residual_linf": best_native["scalar_residual_linf"],
        "max_scalar_residual_linf_over_grids_best_sign": float(max_scalar_over_grids),
        "max_tangent_residual_linf_over_grids_best_sign": float(max_tangent_over_grids),
        "max_derivative_vs_tangent_x_linf_best_sign": float(derivative_consistency),
        "recommendation_label": label,
        "grid_rows": grid_rows,
        "spectrum_metrics_native_best_sign": spectrum,
    }
    return result


def run_phase4g_tangent_consistency(npz_paths: Sequence[str], out_dir: str, grid_factors: Sequence[int] = (1, 2, 4), force_sign: Optional[int] = None, force: bool = False) -> Dict[str, Any]:
    out = Path(out_dir)
    rec_dir = out / "records"
    out.mkdir(parents=True, exist_ok=True)
    rec_dir.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    for p in npz_paths:
        cfg = TangentConsistencyConfig(str(p), tuple(int(x) for x in grid_factors), force_sign, out_dir, force)
        res = audit_tangent_consistency(cfg)
        stem = Path(p).stem
        rec_path = rec_dir / f"{stem}.phase4g_tangent_consistency.json"
        with rec_path.open("w") as f:
            json.dump(res, f, indent=2, sort_keys=True)
        rows.append({
            "npz_path": str(p),
            "record_path": str(rec_path),
            "K": res["K"],
            "M": res["M"],
            "best_sign": res["best_sign"],
            "best_native_scalar_residual_linf": res["best_native_scalar_residual_linf"],
            "max_scalar_residual_linf_over_grids_best_sign": res["max_scalar_residual_linf_over_grids_best_sign"],
            "max_tangent_residual_linf_over_grids_best_sign": res["max_tangent_residual_linf_over_grids_best_sign"],
            "max_derivative_vs_tangent_x_linf_best_sign": res["max_derivative_vs_tangent_x_linf_best_sign"],
            "recommendation_label": res["recommendation_label"],
        })
    rows_sorted = sorted(rows, key=lambda r: (r["max_tangent_residual_linf_over_grids_best_sign"], r["max_scalar_residual_linf_over_grids_best_sign"]))
    summary = {
        "schema": "theorem_iii_trackb_phase4g_summary_v1",
        "diagnostic_only": True,
        "status": "phase4g-tangent-consistency-complete",
        "counts": {"tasks": len(npz_paths), "completed_records": len(rows)},
        "parameters": {"grid_factors": list(grid_factors), "force_sign": force_sign},
        "top_candidates": rows_sorted,
    }
    with (out / "phase4g_tangent_consistency_summary.json").open("w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    return summary
