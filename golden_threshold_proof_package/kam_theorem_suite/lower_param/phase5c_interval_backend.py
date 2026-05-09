"""
Track B Phase 5C: outward-rounded interval-backend scaffold for Theorem III.

This module intentionally sits between Phase 5B's component-inflated diagnostics and a
future theorem-facing proof object.  It uses IEEE-754 nextafter outward rounding and
conservative scalar inflations to produce interval-shaped records for the selected
near-critical golden anchor.  It is not a replacement for a full arbitrary-precision /
formal interval arithmetic backend, but it is designed so the quantities and schemas can
be promoted with minimal changes once the arithmetic layer is upgraded.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import concurrent.futures as cf
import itertools
import json
import math
import os
import re

import numpy as np

TAU = 2.0 * math.pi
GOLDEN_OMEGA = (math.sqrt(5.0) - 1.0) / 2.0


def _jsonable(x: Any) -> Any:
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    return x


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(_jsonable(payload), f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def _fmt_float_token(x: float) -> str:
    if not np.isfinite(x):
        return str(x).replace("-", "m").replace("+", "p").replace(".", "p")
    s = f"{x:.12g}"
    s = s.replace("-", "m").replace("+", "p").replace(".", "p")
    s = s.replace("e", "e")
    return s


def _safe_float(v: Any, default: float) -> float:
    try:
        a = np.asarray(v)
        if a.shape == ():
            return float(a)
        return float(a.ravel()[0])
    except Exception:
        return default


def _load_npz_seed(npz_path: str) -> Tuple[np.ndarray, float, float, Dict[str, Any]]:
    p = Path(npz_path)
    with np.load(p, allow_pickle=False) as z:
        keys = set(z.files)
        u = None
        for k in ("u", "u_values", "u_grid", "embedding_u", "u_theta", "values"):
            if k in keys:
                u = np.asarray(z[k], dtype=float).reshape(-1)
                break
        if u is None:
            # Some earlier overlays store x rather than u.  If x is present, subtract the grid lift.
            for k in ("x", "x_values", "embedding_x"):
                if k in keys:
                    x = np.asarray(z[k], dtype=float).reshape(-1)
                    t = np.arange(x.size, dtype=float) / float(x.size)
                    u = x - t
                    # Remove integer/lift drift from the mean if needed.
                    u = u - np.round(np.mean(u))
                    break
        if u is None:
            raise KeyError(f"Could not find a usable u/x array in {npz_path}; keys={sorted(keys)}")
        K = GOLDEN_OMEGA
        for k in ("K", "k", "parameter_K", "K_value"):
            if k in keys:
                K = _safe_float(z[k], K)
                break
        # If K was not present, parse from filename K0p9716350000...
        if abs(K - GOLDEN_OMEGA) < 1e-15:
            m = re.search(r"K(\d+)p(\d+)", p.name)
            if m:
                K = float(f"{m.group(1)}.{m.group(2)}")
        omega = GOLDEN_OMEGA
        for k in ("omega", "rho", "rotation", "rotation_number"):
            if k in keys:
                omega = _safe_float(z[k], omega)
                break
        meta = {"npz_keys": sorted(keys)}
    if not np.all(np.isfinite(u)):
        raise ValueError(f"Seed has nonfinite u values: {npz_path}")
    return u.astype(float), float(K), float(omega), meta


def _freqs(M: int) -> np.ndarray:
    return np.fft.fftfreq(M, d=1.0 / M)


def _fft_coeff(v: np.ndarray) -> np.ndarray:
    return np.fft.fft(np.asarray(v, dtype=float)) / float(v.size)


def _from_coeff(c: np.ndarray) -> np.ndarray:
    return np.fft.ifft(c * float(c.size)).real


def _shift_values(v: np.ndarray, alpha: float) -> np.ndarray:
    M = int(v.size)
    k = _freqs(M)
    return np.fft.ifft(np.fft.fft(v) * np.exp(1j * TAU * k * alpha)).real


def _derivative_values(v: np.ndarray) -> np.ndarray:
    M = int(v.size)
    k = _freqs(M)
    return np.fft.ifft(np.fft.fft(v) * (1j * TAU * k)).real


def _resample(v: np.ndarray, L: int) -> np.ndarray:
    v = np.asarray(v, dtype=float).reshape(-1)
    M = v.size
    if L == M:
        return v.copy()
    c = np.fft.fft(v) / float(M)
    cshift = np.fft.fftshift(c)
    if L < M:
        # Bandlimited truncation around zero.
        start = (M - L) // 2
        cnew_shift = cshift[start:start + L]
    else:
        pad = L - M
        left = pad // 2
        right = pad - left
        cnew_shift = np.pad(cshift, (left, right), mode="constant")
    cnew = np.fft.ifftshift(cnew_shift)
    return np.fft.ifft(cnew * float(L)).real


def _weighted_l1_from_values(v: np.ndarray, nu: float, cutoff_mode: Optional[int] = None) -> Tuple[float, float, float]:
    M = int(v.size)
    k = _freqs(M).astype(int)
    coeff = _fft_coeff(v)
    weights = np.power(float(nu), np.abs(k))
    absw = np.abs(coeff) * weights
    if cutoff_mode is None:
        core_mask = np.ones(M, dtype=bool)
    else:
        core_mask = np.abs(k) <= int(cutoff_mode)
    core = float(np.sum(absw[core_mask]))
    tail = float(np.sum(absw[~core_mask]))
    return core + tail, core, tail


def _weighted_derivative_l1_from_values(v: np.ndarray, nu: float, cutoff_mode: Optional[int] = None) -> Tuple[float, float, float]:
    M = int(v.size)
    k = _freqs(M).astype(int)
    coeff = _fft_coeff(v)
    weights = np.power(float(nu), np.abs(k)) * (TAU * np.abs(k))
    absw = np.abs(coeff) * weights
    if cutoff_mode is None:
        core_mask = np.ones(M, dtype=bool)
    else:
        core_mask = np.abs(k) <= int(cutoff_mode)
    core = float(np.sum(absw[core_mask]))
    tail = float(np.sum(absw[~core_mask]))
    return core + tail, core, tail


def _scalar_residual(u: np.ndarray, K: float, omega: float) -> np.ndarray:
    M = int(u.size)
    t = np.arange(M, dtype=float) / float(M)
    return _shift_values(u, omega) - 2.0 * u + _shift_values(u, -omega) - (K / TAU) * np.sin(TAU * (t + u))


def _embedding_geometry(u: np.ndarray, K: float, omega: float) -> Dict[str, float]:
    M = int(u.size)
    t = np.arange(M, dtype=float) / float(M)
    up = _derivative_values(u)
    up_minus = _shift_values(up, -omega)
    x = t + u
    tx = 1.0 + up
    ty = up - up_minus
    norm2 = tx * tx + ty * ty
    # Symplectic normal with det([T,N]) = 1.
    nx = -ty / norm2
    ny = tx / norm2

    tx_p = _shift_values(tx, omega)
    ty_p = _shift_values(ty, omega)
    norm2_p = tx_p * tx_p + ty_p * ty_p
    nx_p = -ty_p / norm2_p
    ny_p = tx_p / norm2_p

    c = K * np.cos(TAU * x)
    # DF = [[1+c,1],[c,1]]
    v1x = (1.0 + c) * tx + ty
    v1y = c * tx + ty
    v2x = (1.0 + c) * nx + ny
    v2y = c * nx + ny

    # Since target frame determinant is 1, inverse is [[ny_p,-nx_p],[-ty_p,tx_p]].
    a11 = ny_p * v1x - nx_p * v1y
    a21 = -ty_p * v1x + tx_p * v1y
    a12 = ny_p * v2x - nx_p * v2y
    a22 = -ty_p * v2x + tx_p * v2y

    det_source = tx * ny - ty * nx
    det_target = tx_p * ny_p - ty_p * nx_p
    S = a12
    tangent_residual = np.maximum(np.abs(a11 - 1.0), np.maximum(np.abs(a21), np.abs(a22 - 1.0)))
    upper_defect = np.maximum.reduce([np.abs(a11 - 1.0), np.abs(a21), np.abs(a22 - 1.0)])
    return {
        "a11_minus_1_linf": float(np.max(np.abs(a11 - 1.0))),
        "a21_linf": float(np.max(np.abs(a21))),
        "a22_minus_1_linf": float(np.max(np.abs(a22 - 1.0))),
        "upper_triangular_defect_linf_max": float(np.max(upper_defect)),
        "tangent_residual_linf": float(np.max(tangent_residual)),
        "source_frame_det_defect_linf": float(np.max(np.abs(det_source - 1.0))),
        "target_frame_det_defect_linf": float(np.max(np.abs(det_target - 1.0))),
        "frame_tangent_norm_max": float(np.max(np.sqrt(norm2))),
        "frame_tangent_norm_min": float(np.min(np.sqrt(norm2))),
        "twist_average": float(np.mean(S)),
        "twist_min": float(np.min(S)),
        "twist_max": float(np.max(S)),
    }


def _parse_cutoff(spec: str, M: int) -> Tuple[str, Optional[int]]:
    spec = str(spec)
    if spec == "full":
        return spec, M // 2 - 1
    if spec.startswith("frac:"):
        frac = float(spec.split(":", 1)[1])
        return spec, int(math.floor(frac * (M // 2 - 1)))
    if spec.startswith("mode:"):
        return spec, int(spec.split(":", 1)[1])
    return spec, int(spec)


def _small_divisor_bounds(cutoff: int, omega: float, slack: float) -> Dict[str, float]:
    ks = np.arange(1, int(cutoff) + 1, dtype=float)
    den = np.abs(np.exp(1j * TAU * ks * omega) - 1.0)
    idx = int(np.argmin(den))
    raw = float(den[idx])
    # Outward-ish lower via nextafter and slack.  Diophantine fallback for golden class.
    lowered = max(0.0, float(np.nextafter(raw, 0.0)) - float(slack))
    # Conservative golden fallback: ||k omega|| >= 1/(sqrt(5)*(k+1)); 2 sin(pi x) >= 4x for x <= 1/2.
    kmax = float(cutoff)
    dio = 4.0 / (math.sqrt(5.0) * (kmax + 1.0))
    combined_lower = max(min(lowered, raw), min(lowered, dio) if lowered > 0 else dio * 0.5)
    if combined_lower <= 0:
        combined_lower = max(dio * 0.25, 1e-300)
    return {
        "small_divisor_min_denominator_raw": raw,
        "small_divisor_min_denominator_lower": float(np.nextafter(combined_lower, 0.0)),
        "small_divisor_min_mode": int(ks[idx]),
        "cohomology_inverse_linf_resolved_upper": float(np.nextafter(1.0 / combined_lower, math.inf)),
        "golden_diophantine_fallback_lower_at_cutoff": float(dio),
    }


def _upper(x: float, rel: float = 0.0, abs_slack: float = 0.0) -> float:
    y = abs(float(x)) * (1.0 + float(rel)) + float(abs_slack)
    return float(np.nextafter(y, math.inf))


def _lower(x: float, rel: float = 0.0, abs_slack: float = 0.0) -> float:
    y = float(x) * (1.0 - float(rel)) - float(abs_slack)
    return float(np.nextafter(y, -math.inf))


@dataclass(frozen=True)
class Phase5CConfig:
    npz_path: str
    nu: float
    cutoff_spec: str
    tail_start_frac: float
    grid_factor: int
    radius: float
    interval_inflation: float
    rounding_slack: float
    small_divisor_slack: float
    residual_slack: float
    tail_safety: float
    q_scale: float
    z_inflation: float
    q_inflation: float
    out_dir: str


def audit_one_phase5c(cfg: Phase5CConfig) -> Dict[str, Any]:
    u0, K, omega, meta = _load_npz_seed(cfg.npz_path)
    M_native = int(u0.size)
    L = int(M_native * cfg.grid_factor)
    u = _resample(u0, L)
    cutoff_label, cutoff_native = _parse_cutoff(cfg.cutoff_spec, M_native)
    cutoff_grid = min(int(cutoff_native * cfg.grid_factor), L // 2 - 1)

    R = _scalar_residual(u, K, omega)
    dR = _derivative_values(R)
    geom = _embedding_geometry(u, K, omega)
    res_total, res_core, res_tail = _weighted_l1_from_values(R, cfg.nu, cutoff_grid)
    dres_total, dres_core, dres_tail = _weighted_derivative_l1_from_values(R, cfg.nu, cutoff_grid)
    sd = _small_divisor_bounds(cutoff_native, omega, cfg.small_divisor_slack)
    inv = sd["cohomology_inverse_linf_resolved_upper"]

    scalar_linf = float(np.max(np.abs(R)))
    deriv_linf = float(np.max(np.abs(dR)))
    residual_l1_upper = _upper(res_total, cfg.interval_inflation, cfg.residual_slack)
    residual_tail_upper = _upper(res_tail * cfg.tail_safety, cfg.interval_inflation, cfg.residual_slack)
    derivative_l1_upper = _upper(dres_total, cfg.interval_inflation, cfg.residual_slack)
    derivative_tail_upper = _upper(dres_tail * cfg.tail_safety, cfg.interval_inflation, cfg.residual_slack)

    # Match the Phase 5B scale but make the bound explicit: residual is first converted
    # through the resolved cohomology inverse and q_scale, then inflated outward.
    Y_raw = inv * scalar_linf * cfg.q_scale + residual_tail_upper
    Y = _upper(Y_raw, cfg.interval_inflation, cfg.rounding_slack)
    upper_defect = max(geom["a11_minus_1_linf"], geom["a21_linf"], geom["a22_minus_1_linf"])
    Z_raw = inv * upper_defect
    Z = _upper(Z_raw, cfg.z_inflation + cfg.interval_inflation, cfg.rounding_slack)
    # Nonlinear proxy: q_scale controls the scale inherited from Phase 5B.  Frame and tail
    # make the bound react to the actual seed instead of being purely fixed.
    frame_factor = max(1.0, geom["frame_tangent_norm_max"] / 10.0)
    Q_raw = 1.0e4 * cfg.q_scale * frame_factor + 10.0 * derivative_tail_upper
    Q = _upper(Q_raw, cfg.q_inflation + cfg.interval_inflation, cfg.rounding_slack)
    r = float(cfg.radius)
    lhs = _upper(Y + Z * r + Q * r * r, 0.0, cfg.rounding_slack)
    margin_lower = _lower(r - lhs, 0.0, cfg.rounding_slack)
    relative_margin_lower = margin_lower / r if r > 0 else float("nan")

    # Simple outward intervals for the main scalars.
    payload: Dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase5c_interval_backend_record_v1",
        "status": "phase5c-outward-rounded-backend-record",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "important_warning": "IEEE-754 nextafter outward-rounded backend scaffold; not yet an independently verified formal interval proof.",
        "npz_path": cfg.npz_path,
        "npz_meta": meta,
        "K": K,
        "omega": omega,
        "M": M_native,
        "grid_size": L,
        "grid_factor": cfg.grid_factor,
        "nu": cfg.nu,
        "cutoff_spec": cutoff_label,
        "cutoff_mode_native_units": int(cutoff_native),
        "cutoff_mode_grid_units": int(cutoff_grid),
        "tail_start_frac": cfg.tail_start_frac,
        "radius": r,
        "interval_inflation": cfg.interval_inflation,
        "z_inflation": cfg.z_inflation,
        "q_inflation": cfg.q_inflation,
        "rounding_slack": cfg.rounding_slack,
        "small_divisor_slack": cfg.small_divisor_slack,
        "tail_safety": cfg.tail_safety,
        "q_scale": cfg.q_scale,
        "scalar_residual_linf": scalar_linf,
        "scalar_residual_linf_interval": [_lower(scalar_linf, 0.0, cfg.residual_slack), _upper(scalar_linf, 0.0, cfg.residual_slack)],
        "derivative_residual_linf": deriv_linf,
        "derivative_residual_linf_interval": [_lower(deriv_linf, 0.0, cfg.residual_slack), _upper(deriv_linf, 0.0, cfg.residual_slack)],
        "residual_l1_nu_total_raw": res_total,
        "residual_l1_nu_core_raw": res_core,
        "residual_l1_nu_tail_raw": res_tail,
        "residual_l1_nu_total_upper": residual_l1_upper,
        "tail_residual_component_upper": residual_tail_upper,
        "derivative_l1_nu_total_raw": dres_total,
        "derivative_l1_nu_core_raw": dres_core,
        "derivative_l1_nu_tail_raw": dres_tail,
        "derivative_l1_nu_total_upper": derivative_l1_upper,
        "tail_derivative_component_upper": derivative_tail_upper,
        **sd,
        **geom,
        "Y_raw_backend": Y_raw,
        "Y_interval_upper": Y,
        "Z_raw_backend": Z_raw,
        "Z_interval_upper": Z,
        "Q_raw_backend": Q_raw,
        "Q_interval_upper": Q,
        "radii_lhs_interval_upper": lhs,
        "radii_margin_interval_lower": margin_lower,
        "radii_relative_margin_interval_lower": relative_margin_lower,
        "any_positive_interval_margin": bool(margin_lower > 0.0),
        "dominant_interval_term": "Zr_interval" if Z * r >= max(Y, Q * r * r) else ("Y_interval" if Y >= Q * r * r else "Qr2_interval"),
        "recommended_next": "phase5d_certificate_assembly" if margin_lower > 0.0 and Z < 0.5 else "tighten_interval_backend_or_frame_Z",
        "acceptance_thresholds": {
            "Z_interval_upper_target": 0.5,
            "relative_margin_lower_target": 0.25,
            "radius_target": r,
        },
    }
    score = 0
    if margin_lower > 0.0:
        score += 2
    if relative_margin_lower > 0.5:
        score += 1
    if Z < 0.3:
        score += 1
    if cfg.nu <= 1.0015:
        score += 1
    payload["recommendation_score"] = score
    payload["recommendation_label"] = "backend_ready_candidate" if score >= 4 else ("backend_marginal_candidate" if margin_lower > 0 else "backend_failed_candidate")

    rec_stem = f"K{_fmt_float_token(K)}_M{M_native}_nu{_fmt_float_token(cfg.nu)}_{cutoff_label.replace(':','').replace('.','p')}_tail{_fmt_float_token(cfg.tail_start_frac)}_g{cfg.grid_factor}_r{_fmt_float_token(r)}"
    rec_path = Path(cfg.out_dir) / "records" / f"{rec_stem}.phase5c_interval_backend.json"
    payload["record_path"] = str(rec_path)
    _write_json(rec_path, payload)
    return _compact_row(payload)


def _compact_row(p: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "K", "M", "nu", "cutoff_spec", "cutoff_mode_native_units", "tail_start_frac", "grid_factor", "grid_size", "radius",
        "scalar_residual_linf", "derivative_residual_linf", "residual_l1_nu_total_upper", "tail_residual_component_upper",
        "small_divisor_min_denominator_lower", "small_divisor_min_mode", "cohomology_inverse_linf_resolved_upper",
        "a11_minus_1_linf", "a21_linf", "a22_minus_1_linf", "upper_triangular_defect_linf_max",
        "source_frame_det_defect_linf", "target_frame_det_defect_linf", "twist_average", "twist_min", "twist_max",
        "Y_interval_upper", "Z_interval_upper", "Q_interval_upper", "radii_lhs_interval_upper", "radii_margin_interval_lower",
        "radii_relative_margin_interval_lower", "dominant_interval_term", "any_positive_interval_margin", "recommendation_label", "recommendation_score", "record_path", "npz_path",
    ]
    return {k: p.get(k) for k in keys if k in p}


def run_phase5c_interval_backend(
    npz_paths: Sequence[str],
    nu_grid: Sequence[float],
    cutoffs: Sequence[str],
    tail_start_fracs: Sequence[float],
    grid_factors: Sequence[int],
    radii: Sequence[float],
    interval_inflation: float,
    rounding_slack: float,
    small_divisor_slack: float,
    residual_slack: float,
    tail_safety: float,
    q_scale: float,
    z_inflation: float,
    q_inflation: float,
    workers: int,
    out_dir: str,
    force: bool = False,
) -> Dict[str, Any]:
    out = Path(out_dir)
    if force and out.exists():
        import shutil
        shutil.rmtree(out)
    (out / "records").mkdir(parents=True, exist_ok=True)
    cfgs: List[Phase5CConfig] = []
    for npz, nu, cutoff, tail, gf, r in itertools.product(npz_paths, nu_grid, cutoffs, tail_start_fracs, grid_factors, radii):
        cfgs.append(Phase5CConfig(
            npz_path=str(npz), nu=float(nu), cutoff_spec=str(cutoff), tail_start_frac=float(tail),
            grid_factor=int(gf), radius=float(r), interval_inflation=float(interval_inflation),
            rounding_slack=float(rounding_slack), small_divisor_slack=float(small_divisor_slack),
            residual_slack=float(residual_slack), tail_safety=float(tail_safety), q_scale=float(q_scale),
            z_inflation=float(z_inflation), q_inflation=float(q_inflation), out_dir=str(out),
        ))
    if workers and workers > 1 and len(cfgs) > 1:
        try:
            with cf.ProcessPoolExecutor(max_workers=int(workers)) as ex:
                rows = list(ex.map(audit_one_phase5c, cfgs))
        except BaseException as exc:
            # Phase 5C has a small task grid but can allocate large FFT work
            # arrays per task.  If the process pool is rejected by local
            # resource limits, fall back to serial execution.
            print(f"[phase5c] parallel execution failed ({type(exc).__name__}: {exc}); falling back to serial execution", flush=True)
            rows = [audit_one_phase5c(c) for c in cfgs]
    else:
        rows = [audit_one_phase5c(c) for c in cfgs]
    rows_sorted = sorted(rows, key=lambda d: (d.get("recommendation_score", 0), d.get("radii_margin_interval_lower", -1e300)), reverse=True)
    summary = {
        "schema": "theorem_iii_trackb_phase5c_interval_backend_summary_v1",
        "status": "phase5c-interval-backend-complete",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "important_warning": "Uses nextafter outward rounding and conservative inflations, but is not yet an independently verified formal proof.",
        "parameters": {
            "npz_count": len(npz_paths), "nu_grid": list(map(float, nu_grid)), "cutoffs": list(cutoffs),
            "tail_start_fracs": list(map(float, tail_start_fracs)), "grid_factors": list(map(int, grid_factors)),
            "radii": list(map(float, radii)), "interval_inflation": interval_inflation, "z_inflation": z_inflation,
            "q_inflation": q_inflation, "rounding_slack": rounding_slack, "small_divisor_slack": small_divisor_slack,
            "residual_slack": residual_slack, "tail_safety": tail_safety, "q_scale": q_scale,
            "workers_requested": workers, "tasks": len(cfgs),
        },
        "counts": {
            "tasks": len(cfgs),
            "completed_records": len(rows),
            "backend_ready_candidate": sum(1 for r in rows if r.get("recommendation_label") == "backend_ready_candidate"),
            "backend_marginal_candidate": sum(1 for r in rows if r.get("recommendation_label") == "backend_marginal_candidate"),
            "backend_failed_candidate": sum(1 for r in rows if r.get("recommendation_label") == "backend_failed_candidate"),
        },
        "top_candidates": rows_sorted[:50],
    }
    _write_json(out / "phase5c_interval_backend_summary.json", summary)
    _write_json(out / "phase5c_ranked_candidates.json", {"rows": rows_sorted})
    # CSV for quick grep.
    import csv
    csv_path = out / "phase5c_interval_backend_results.csv"
    if rows_sorted:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows_sorted[0].keys()))
            writer.writeheader()
            for row in rows_sorted:
                writer.writerow(row)
    return summary
