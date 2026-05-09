from __future__ import annotations

import csv
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

GOLDEN_OMEGA = (math.sqrt(5.0) - 1.0) / 2.0
TWO_PI = 2.0 * math.pi


def _clean(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        x = float(o)
        return None if (math.isnan(x) or math.isinf(x)) else x
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.complexfloating):
        z = complex(o)
        return {"real": float(z.real), "imag": float(z.imag)}
    return o


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(_clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


def _as_float(x: Any, default: float | None = None) -> float | None:
    try:
        y = float(np.asarray(x).reshape(()))
        return y if math.isfinite(y) else default
    except Exception:
        return default


def freq_grid(M: int) -> np.ndarray:
    return np.fft.fftfreq(int(M), d=1.0 / float(M))


def coeff(values: np.ndarray) -> np.ndarray:
    return np.fft.fft(np.asarray(values, dtype=float)) / float(values.size)


def samples_from_coeff(c: np.ndarray) -> np.ndarray:
    return np.fft.ifft(np.asarray(c) * float(c.size)).real


def coeff_to_size(c_src: np.ndarray, M_dst: int, *, cutoff_mode: int | None = None) -> np.ndarray:
    c_src = np.asarray(c_src, dtype=complex)
    M_src = int(c_src.size)
    M_dst = int(M_dst)
    out = np.zeros(M_dst, dtype=complex)
    max_dst = M_dst // 2
    for idx, k_float in enumerate(freq_grid(M_src)):
        k = int(k_float)
        if k == -M_src // 2 and M_src % 2 == 0 and M_dst != M_src:
            # Drop ambiguous Nyquist coefficient when changing grid size.
            continue
        if cutoff_mode is not None and abs(k) > int(cutoff_mode):
            continue
        if abs(k) > max_dst:
            continue
        out[k % M_dst] = c_src[idx]
    return out


def shift_samples(values: np.ndarray, omega: float, sign: int = +1) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    f = freq_grid(values.size)
    c = coeff(values)
    mult = np.exp(1j * TWO_PI * f * float(omega) * (1 if sign >= 0 else -1))
    return samples_from_coeff(c * mult)


def spectral_derivative(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    f = freq_grid(values.size)
    return samples_from_coeff((1j * TWO_PI * f) * coeff(values))


def weighted_l1(values: np.ndarray, nu: float) -> float:
    values = np.asarray(values, dtype=float)
    f = np.abs(freq_grid(values.size))
    return float(np.sum(np.abs(coeff(values)) * np.exp(math.log(float(nu)) * f)))


def tail_ratio(values: np.ndarray, nu: float, frac: float) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    f = np.abs(freq_grid(values.size))
    vals = np.abs(coeff(values)) * np.exp(math.log(float(nu)) * f)
    total = float(np.sum(vals))
    start = float(frac) * float(np.max(f)) if f.size else 0.0
    mask = f >= start
    tail = float(np.sum(vals[mask])) if np.any(mask) else 0.0
    return {"tail_start_mode": start, "weighted_tail_l1": tail, "weighted_tail_ratio": tail / total if total > 0 else 0.0}


def scalar_residual_lift_aware(u: np.ndarray, K: float, omega: float) -> np.ndarray:
    M = int(u.size)
    theta = np.arange(M, dtype=float) / float(M)
    return shift_samples(u, omega, +1) - 2.0 * u + shift_samples(u, omega, -1) - (float(K) / TWO_PI) * np.sin(TWO_PI * (theta + u))


def standard_map_df_entries(x: np.ndarray, K: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    c = float(K) * np.cos(TWO_PI * np.asarray(x, dtype=float))
    return 1.0 + c, np.ones_like(c), c, np.ones_like(c)


def symplectic_normal_from_tangent(xp: np.ndarray, rp: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    norm2 = xp * xp + rp * rp
    # n = (-r', x') / |t|^2 gives det([t,n]) = 1 pointwise.
    return -rp / norm2, xp / norm2, norm2


def target_frame_auto_reducibility_audit(u: np.ndarray, K: float, omega: float) -> dict[str, Any]:
    """Lift-aware automatic-reducibility diagnostic with the target frame recomputed.

    Phase 4b exposed a second diagnostic issue: shifting the nonlinear normal vector can
    create large determinant defects because the normal is a nonlinear function of the
    tangent and its tail is not represented exactly.  The target frame M(theta+omega)
    should be assembled from the shifted tangent and then re-normalized symplectically.
    This audit compares that target-recomputed frame against the older shifted-normal
    frame so we can separate real tangent defects from frame-normalization artifacts.
    """
    M = int(u.size)
    theta = np.arange(M, dtype=float) / float(M)
    up = spectral_derivative(u)
    u_p = shift_samples(u, omega, +1)
    u_m = shift_samples(u, omega, -1)
    up_p = shift_samples(up, omega, +1)
    up_m = shift_samples(up, omega, -1)

    x = theta + u
    r = float(omega) + u - u_m
    forcing = (float(K) / TWO_PI) * np.sin(TWO_PI * x)

    # Lift-aware embedding residual.
    x_target = theta + float(omega) + u_p
    r_target = float(omega) + u_p - u
    ex = x + r + forcing - x_target
    er = r + forcing - r_target
    scalar = scalar_residual_lift_aware(u, K, omega)

    # Source tangent and target tangent.  The target tangent is obtained by shifting u'
    # and applying the same formulas to W(theta+omega), not by differentiating a lifted x.
    xp = 1.0 + up
    rp = up - up_m
    xp_s = 1.0 + up_p
    rp_s = up_p - up

    nx, nr, norm2 = symplectic_normal_from_tangent(xp, rp)
    # Old shifted-normal target frame, kept only for comparison.
    nx_s_shift = shift_samples(nx, omega, +1)
    nr_s_shift = shift_samples(nr, omega, +1)
    # Corrected target frame: recompute normal from shifted tangent.
    nx_s, nr_s, norm2_s = symplectic_normal_from_tangent(xp_s, rp_s)

    a, b, c, d = standard_map_df_entries(x, K)
    Dtx = a * xp + b * rp
    Dtr = c * xp + d * rp
    Dnx = a * nx + b * nr
    Dnr = c * nx + d * nr

    tangent_res_x = Dtx - xp_s
    tangent_res_r = Dtr - rp_s

    # Corrected target frame inverse.
    A11 = nr_s * Dtx - nx_s * Dtr
    A21 = -rp_s * Dtx + xp_s * Dtr
    A12 = nr_s * Dnx - nx_s * Dnr
    A22 = -rp_s * Dnx + xp_s * Dnr

    # Old shifted-normal inverse for comparison.
    det_shift_old = xp_s * nr_s_shift - rp_s * nx_s_shift
    A11_old = (nr_s_shift * Dtx - nx_s_shift * Dtr) / det_shift_old
    A21_old = (-rp_s * Dtx + xp_s * Dtr) / det_shift_old
    A12_old = (nr_s_shift * Dnx - nx_s_shift * Dnr) / det_shift_old
    A22_old = (-rp_s * Dnx + xp_s * Dnr) / det_shift_old

    det_source = xp * nr - rp * nx
    det_target = xp_s * nr_s - rp_s * nx_s
    det_shifted_normal = det_shift_old

    twist = A12
    twist_avg = float(np.mean(twist))

    return {
        "u": u,
        "scalar_residual": scalar,
        "x_lift_residual": ex,
        "r_lift_residual": er,
        "tangent_residual_x": tangent_res_x,
        "tangent_residual_r": tangent_res_r,
        "A11": A11,
        "A12": A12,
        "A21": A21,
        "A22": A22,
        "A11_old_shifted_normal": A11_old,
        "A12_old_shifted_normal": A12_old,
        "A21_old_shifted_normal": A21_old,
        "A22_old_shifted_normal": A22_old,
        "twist": twist,
        "twist_average": twist_avg,
        "det_source": det_source,
        "det_target": det_target,
        "det_shifted_normal": det_shifted_normal,
        "xp": xp,
        "rp": rp,
        "xp_s": xp_s,
        "rp_s": rp_s,
        "nx": nx,
        "nr": nr,
        "nx_s": nx_s,
        "nr_s": nr_s,
        "norm2": norm2,
        "norm2_s": norm2_s,
    }


def metrics_for_u(u: np.ndarray, K: float, omega: float, nu_grid: Sequence[float], tail_start_fracs: Sequence[float]) -> dict[str, Any]:
    aud = target_frame_auto_reducibility_audit(u, K, omega)
    scalar = np.asarray(aud["scalar_residual"])
    ex = np.asarray(aud["x_lift_residual"])
    er = np.asarray(aud["r_lift_residual"])
    tx = np.asarray(aud["tangent_residual_x"])
    tr = np.asarray(aud["tangent_residual_r"])
    A11 = np.asarray(aud["A11"]); A12 = np.asarray(aud["A12"]); A21 = np.asarray(aud["A21"]); A22 = np.asarray(aud["A22"])
    A11_old = np.asarray(aud["A11_old_shifted_normal"]); A21_old = np.asarray(aud["A21_old_shifted_normal"]); A22_old = np.asarray(aud["A22_old_shifted_normal"])
    twist = np.asarray(aud["twist"])
    det_source = np.asarray(aud["det_source"]); det_target = np.asarray(aud["det_target"]); det_shifted = np.asarray(aud["det_shifted_normal"])
    xp = np.asarray(aud["xp"]); rp = np.asarray(aud["rp"]); nx = np.asarray(aud["nx"]); nr = np.asarray(aud["nr"])
    xp_s = np.asarray(aud["xp_s"]); rp_s = np.asarray(aud["rp_s"]); nx_s = np.asarray(aud["nx_s"]); nr_s = np.asarray(aud["nr_s"])
    norm2 = np.asarray(aud["norm2"]); norm2_s = np.asarray(aud["norm2_s"])

    scalar_metrics = {
        "scalar_residual_linf": float(np.max(np.abs(scalar))),
        "embedding_residual_linf_max_lift_aware": float(max(np.max(np.abs(ex)), np.max(np.abs(er)))),
        "lift_residual_matches_scalar_linf": float(max(np.max(np.abs(ex + scalar)), np.max(np.abs(er + scalar)))),
        "tangent_residual_x_linf": float(np.max(np.abs(tx))),
        "tangent_residual_r_linf": float(np.max(np.abs(tr))),
        "tangent_residual_linf_max": float(max(np.max(np.abs(tx)), np.max(np.abs(tr)))),
        "a11_minus_1_linf": float(np.max(np.abs(A11 - 1.0))),
        "a21_linf": float(np.max(np.abs(A21))),
        "a22_minus_1_linf": float(np.max(np.abs(A22 - 1.0))),
        "upper_triangular_defect_linf_max": float(max(np.max(np.abs(A11 - 1.0)), np.max(np.abs(A21)), np.max(np.abs(A22 - 1.0)))),
        "old_shifted_normal_a11_minus_1_linf": float(np.max(np.abs(A11_old - 1.0))),
        "old_shifted_normal_a21_linf": float(np.max(np.abs(A21_old))),
        "old_shifted_normal_a22_minus_1_linf": float(np.max(np.abs(A22_old - 1.0))),
        "old_shifted_normal_upper_triangular_defect_linf_max": float(max(np.max(np.abs(A11_old - 1.0)), np.max(np.abs(A21_old)), np.max(np.abs(A22_old - 1.0)))),
        "twist_average": float(aud["twist_average"]),
        "twist_min": float(np.min(twist)),
        "twist_max": float(np.max(twist)),
        "twist_centered_linf": float(np.max(np.abs(twist - np.mean(twist)))),
        "source_frame_det_defect_linf": float(np.max(np.abs(det_source - 1.0))),
        "target_frame_det_defect_linf": float(np.max(np.abs(det_target - 1.0))),
        "shifted_normal_target_det_defect_linf": float(np.max(np.abs(det_shifted - 1.0))),
        "source_tangent_norm_min": float(np.sqrt(np.min(norm2))),
        "source_tangent_norm_max": float(np.sqrt(np.max(norm2))),
        "target_tangent_norm_min": float(np.sqrt(np.min(norm2_s))),
        "target_tangent_norm_max": float(np.sqrt(np.max(norm2_s))),
        "source_normal_norm_max": float(np.max(np.sqrt(nx * nx + nr * nr))),
        "target_normal_norm_max": float(np.max(np.sqrt(nx_s * nx_s + nr_s * nr_s))),
        "xprime_min": float(np.min(xp)),
        "xprime_max": float(np.max(xp)),
        "target_xprime_min": float(np.min(xp_s)),
        "target_xprime_max": float(np.max(xp_s)),
        "rprime_linf": float(np.max(np.abs(rp))),
        "target_rprime_linf": float(np.max(np.abs(rp_s))),
    }
    weighted: dict[str, Any] = {}
    for nu in nu_grid:
        nu = float(nu)
        tangent_l1 = max(weighted_l1(tx, nu), weighted_l1(tr, nu))
        tri_l1 = max(weighted_l1(A11 - 1.0, nu), weighted_l1(A21, nu), weighted_l1(A22 - 1.0, nu))
        scalar_l1 = weighted_l1(scalar, nu)
        weighted[f"nu_{nu:.6f}"] = {
            "nu": nu,
            "scalar_residual_l1_nu": scalar_l1,
            "embedding_residual_l1_nu_lift_aware": max(weighted_l1(ex, nu), weighted_l1(er, nu)),
            "tangent_residual_l1_nu": tangent_l1,
            "upper_triangular_defect_l1_nu": tri_l1,
            "a21_l1_nu": weighted_l1(A21, nu),
            "twist_centered_l1_nu": weighted_l1(twist - np.mean(twist), nu),
            "target_det_defect_l1_nu": weighted_l1(det_target - 1.0, nu),
            "shifted_normal_det_defect_l1_nu": weighted_l1(det_shifted - 1.0, nu),
            "tail_ratios": {
                f"frac_{f:.3f}": {
                    "scalar_residual_tail": tail_ratio(scalar, nu, f),
                    "tangent_residual_x_tail": tail_ratio(tx, nu, f),
                    "tangent_residual_r_tail": tail_ratio(tr, nu, f),
                    "a21_tail": tail_ratio(A21, nu, f),
                } for f in tail_start_fracs
            },
        }
    return {"scalar_metrics": scalar_metrics, "weighted_metrics": weighted}


@dataclass(slots=True)
class TargetFrameAuditConfig:
    npz_path: str
    out_dir: str
    oversample_factors: tuple[int, ...] = (1, 2, 4)
    cutoff_fracs: tuple[float, ...] = (1.0, 0.95, 0.90, 0.75, 0.50)
    nu_grid: tuple[float, ...] = (1.002, 1.003, 1.005)
    tail_start_fracs: tuple[float, ...] = (0.50, 0.75, 0.90)
    omega_override: float | None = None
    force: bool = False


def audit_npz_target_frame(cfg: TargetFrameAuditConfig) -> dict[str, Any]:
    t0 = time.time()
    npz_path = Path(cfg.npz_path)
    tag = npz_path.stem
    out_dir = Path(cfg.out_dir)
    record_path = out_dir / "records" / f"{tag}.phase4d_target_frame_audit.json"
    if record_path.exists() and not cfg.force:
        try:
            d = json.loads(record_path.read_text(encoding="utf-8"))
            d["loaded_from_existing_record"] = True
            return d
        except Exception:
            pass
    with np.load(npz_path, allow_pickle=False) as z:
        K = _as_float(z.get("K"), None)
        M_field = int(_as_float(z.get("M"), 0) or 0)
        omega_in = _as_float(z.get("omega"), GOLDEN_OMEGA)
        omega = float(cfg.omega_override if cfg.omega_override is not None else (omega_in if omega_in is not None else GOLDEN_OMEGA))
        u0 = np.asarray(z["u"], dtype=float)
        schema = str(np.asarray(z["schema"]).reshape(()).item()) if "schema" in z else "unknown"
    if K is None:
        raise ValueError(f"Missing K in {npz_path}")
    M0 = int(u0.size)
    if M_field and M_field != M0:
        raise ValueError(f"M mismatch in {npz_path}: field {M_field}, u.size {M0}")

    c0 = coeff(u0)
    max_mode0 = M0 // 2
    cases: dict[str, Any] = {}
    compact_cases: list[dict[str, Any]] = []
    for fac in cfg.oversample_factors:
        L = int(M0) * int(fac)
        if L < M0:
            continue
        for cf in cfg.cutoff_fracs:
            cutoff = int(math.floor(float(cf) * max_mode0))
            if cf >= 0.999:
                cutoff = None
                cf_label = "full"
            else:
                cf_label = f"cut_{cf:.3f}"
            uL = samples_from_coeff(coeff_to_size(c0, L, cutoff_mode=cutoff))
            met = metrics_for_u(uL, float(K), omega, cfg.nu_grid, cfg.tail_start_fracs)
            key = f"L{L}_{cf_label}"
            met["grid_size"] = L
            met["oversample_factor"] = int(fac)
            met["cutoff_frac"] = float(cf)
            met["cutoff_mode"] = cutoff
            cases[key] = met
            sm = met["scalar_metrics"]
            rep = met["weighted_metrics"].get("nu_1.003000") or next(iter(met["weighted_metrics"].values()))
            compact_cases.append({
                "case": key,
                "grid_size": L,
                "oversample_factor": int(fac),
                "cutoff_frac": float(cf),
                "cutoff_mode": cutoff,
                "scalar_residual_linf": sm["scalar_residual_linf"],
                "embedding_residual_linf_max_lift_aware": sm["embedding_residual_linf_max_lift_aware"],
                "lift_residual_matches_scalar_linf": sm["lift_residual_matches_scalar_linf"],
                "tangent_residual_linf_max": sm["tangent_residual_linf_max"],
                "upper_triangular_defect_linf_max": sm["upper_triangular_defect_linf_max"],
                "a11_minus_1_linf": sm["a11_minus_1_linf"],
                "a21_linf": sm["a21_linf"],
                "a22_minus_1_linf": sm["a22_minus_1_linf"],
                "old_shifted_normal_upper_triangular_defect_linf_max": sm["old_shifted_normal_upper_triangular_defect_linf_max"],
                "source_frame_det_defect_linf": sm["source_frame_det_defect_linf"],
                "target_frame_det_defect_linf": sm["target_frame_det_defect_linf"],
                "shifted_normal_target_det_defect_linf": sm["shifted_normal_target_det_defect_linf"],
                "twist_average": sm["twist_average"],
                "twist_min": sm["twist_min"],
                "twist_max": sm["twist_max"],
                "rep_nu": rep.get("nu"),
                "rep_scalar_residual_l1_nu": rep.get("scalar_residual_l1_nu"),
                "rep_tangent_residual_l1_nu": rep.get("tangent_residual_l1_nu"),
                "rep_upper_triangular_defect_l1_nu": rep.get("upper_triangular_defect_l1_nu"),
            })

    full_cases = [r for r in compact_cases if r["cutoff_mode"] is None]
    best_full = min(full_cases, key=lambda r: (r["upper_triangular_defect_linf_max"], r["tangent_residual_linf_max"], r["scalar_residual_linf"])) if full_cases else None
    best_any = min(compact_cases, key=lambda r: (r["upper_triangular_defect_linf_max"], r["tangent_residual_linf_max"], r["scalar_residual_linf"])) if compact_cases else None
    base_case = next((r for r in compact_cases if r["oversample_factor"] == 1 and r["cutoff_mode"] is None), None)

    score = 0
    reasons: list[str] = []
    label = "needs_target_frame_or_refined_seed"
    if base_case and base_case["embedding_residual_linf_max_lift_aware"] < 1e-8:
        score += 1; reasons.append("lift-aware embedding residual is small")
    if best_full and max(best_full["source_frame_det_defect_linf"], best_full["target_frame_det_defect_linf"]) < 1e-12:
        score += 1; reasons.append("recomputed source/target symplectic frame determinant is pointwise normalized")
    if best_full and best_full["upper_triangular_defect_linf_max"] < 1e-6:
        score += 4; reasons.append("full-coefficient triangular defect is below 1e-6")
    elif best_full and best_full["upper_triangular_defect_linf_max"] < 1e-4:
        score += 2; reasons.append("full-coefficient triangular defect is moderate below 1e-4")
    elif best_full and best_full["upper_triangular_defect_linf_max"] < 1e-3:
        score += 1; reasons.append("full-coefficient triangular defect is sub-1e-3 but not interval-ready")
    if best_full and base_case and best_full["upper_triangular_defect_linf_max"] < 0.25 * max(base_case["old_shifted_normal_upper_triangular_defect_linf_max"], 1e-300):
        score += 1; reasons.append("target-frame recomputation substantially improves the old shifted-normal defect")
    if score >= 6:
        label = "ready_for_intervalized_radii_prep"
    elif score >= 4:
        label = "moderate_needs_one_more_precision_or_frame_polish"

    payload: dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase4d_target_frame_audit_v1",
        "phase": "TrackB-Phase4d-target-recomputed-symplectic-frame-audit",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "important_warning": "Double-precision diagnostic only. The target frame is recomputed from the shifted tangent instead of shifting the nonlinear normal vector.",
        "npz_path": str(npz_path),
        "record_path": str(record_path),
        "source_npz_schema": schema,
        "K": float(K),
        "M": M0,
        "omega": omega,
        "oversample_factors": [int(x) for x in cfg.oversample_factors],
        "cutoff_fracs": [float(x) for x in cfg.cutoff_fracs],
        "nu_grid": [float(x) for x in cfg.nu_grid],
        "tail_start_fracs": [float(x) for x in cfg.tail_start_fracs],
        "compact_cases": compact_cases,
        "cases": cases,
        "recommendation": {
            "label": label,
            "score": score,
            "reasons": reasons,
            "base_case": base_case,
            "best_full_case": best_full,
            "best_any_case": best_any,
            "next_phase_hint": "If this leaves sub-1e-3 triangular defect at the final anchor, polish/dealias the seed using the target-frame residual as a diagnostic before intervalization.",
        },
        "elapsed_seconds": float(time.time() - t0),
    }
    write_json(record_path, payload)
    return payload


def _cfg_dict(cfg: TargetFrameAuditConfig) -> dict[str, Any]:
    return asdict(cfg)


def _compact_row(rec: dict[str, Any]) -> dict[str, Any]:
    recm = rec.get("recommendation", {})
    base = recm.get("base_case") or {}
    best_full = recm.get("best_full_case") or {}
    best_any = recm.get("best_any_case") or {}
    return {
        "K": rec.get("K"),
        "M": rec.get("M"),
        "npz_path": rec.get("npz_path"),
        "record_path": rec.get("record_path"),
        "base_scalar_residual_linf": base.get("scalar_residual_linf"),
        "base_embedding_residual_linf_max_lift_aware": base.get("embedding_residual_linf_max_lift_aware"),
        "base_tangent_residual_linf_max": base.get("tangent_residual_linf_max"),
        "base_upper_triangular_defect_linf_max": base.get("upper_triangular_defect_linf_max"),
        "base_old_shifted_normal_upper_triangular_defect_linf_max": base.get("old_shifted_normal_upper_triangular_defect_linf_max"),
        "base_source_frame_det_defect_linf": base.get("source_frame_det_defect_linf"),
        "base_target_frame_det_defect_linf": base.get("target_frame_det_defect_linf"),
        "base_shifted_normal_target_det_defect_linf": base.get("shifted_normal_target_det_defect_linf"),
        "best_full_case": best_full.get("case"),
        "best_full_grid_size": best_full.get("grid_size"),
        "best_full_scalar_residual_linf": best_full.get("scalar_residual_linf"),
        "best_full_tangent_residual_linf_max": best_full.get("tangent_residual_linf_max"),
        "best_full_upper_triangular_defect_linf_max": best_full.get("upper_triangular_defect_linf_max"),
        "best_full_a21_linf": best_full.get("a21_linf"),
        "best_full_source_frame_det_defect_linf": best_full.get("source_frame_det_defect_linf"),
        "best_full_target_frame_det_defect_linf": best_full.get("target_frame_det_defect_linf"),
        "best_any_case": best_any.get("case"),
        "best_any_cutoff_mode": best_any.get("cutoff_mode"),
        "best_any_scalar_residual_linf": best_any.get("scalar_residual_linf"),
        "best_any_tangent_residual_linf_max": best_any.get("tangent_residual_linf_max"),
        "best_any_upper_triangular_defect_linf_max": best_any.get("upper_triangular_defect_linf_max"),
        "twist_average_best_full": best_full.get("twist_average"),
        "recommendation_label": recm.get("label"),
        "recommendation_score": recm.get("score"),
    }


def _task(cfgd: dict[str, Any]) -> dict[str, Any]:
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
        os.environ.setdefault(k, "1")
    return _compact_row(audit_npz_target_frame(TargetFrameAuditConfig(**cfgd)))


def load_npz_list_from_phase3_summary(
    phase3_summary: str | Path,
    *,
    selection: str = "strong",
    anchors: Sequence[float] | None = None,
    resolutions: Sequence[int] | None = None,
    top: int | None = None,
) -> list[str]:
    data = json.loads(Path(phase3_summary).read_text(encoding="utf-8"))
    anchor_set = {round(float(x), 12) for x in anchors} if anchors else None
    res_set = {int(x) for x in resolutions} if resolutions else None
    candidates = list(data.get("ranked_candidates", data.get("records", [])))
    out: list[str] = []
    for row in candidates:
        label = str(row.get("recommendation_label", ""))
        if selection == "strong" and label != "strong_phase3_candidate":
            continue
        K = row.get("K"); M = row.get("M")
        if K is None or M is None:
            continue
        if anchor_set is not None and round(float(K), 12) not in anchor_set:
            continue
        if res_set is not None and int(M) not in res_set:
            continue
        p = row.get("npz_path") or row.get("npz")
        if p:
            out.append(str(p))
        if top is not None and len(out) >= int(top):
            break
    seen = set(); deduped = []
    for p in out:
        if p not in seen:
            deduped.append(p); seen.add(p)
    return deduped


def run_phase4d_target_frame_audit(
    *,
    npz_paths: Sequence[str],
    out_dir: str | Path,
    workers: int = 1,
    oversample_factors: Sequence[int] = (1, 2, 4),
    cutoff_fracs: Sequence[float] = (1.0, 0.95, 0.90, 0.75, 0.50),
    nu_grid: Sequence[float] = (1.002, 1.003, 1.005),
    tail_start_fracs: Sequence[float] = (0.50, 0.75, 0.90),
    omega_override: float | None = None,
    force: bool = False,
) -> dict[str, Any]:
    t0 = time.time()
    out = Path(out_dir)
    (out / "records").mkdir(parents=True, exist_ok=True)
    tasks = [_cfg_dict(TargetFrameAuditConfig(
        npz_path=str(Path(p)), out_dir=str(out),
        oversample_factors=tuple(int(x) for x in oversample_factors),
        cutoff_fracs=tuple(float(x) for x in cutoff_fracs),
        nu_grid=tuple(float(x) for x in nu_grid),
        tail_start_fracs=tuple(float(x) for x in tail_start_fracs),
        omega_override=omega_override, force=bool(force),
    )) for p in npz_paths]
    rows: list[dict[str, Any]] = []
    nw = max(1, min(int(workers), len(tasks))) if tasks else 1
    if nw == 1:
        for cfgd in tasks:
            rows.append(_task(cfgd))
    else:
        with ProcessPoolExecutor(max_workers=nw) as ex:
            futs = [ex.submit(_task, cfgd) for cfgd in tasks]
            for fut in as_completed(futs):
                rows.append(fut.result())
    rows.sort(key=lambda r: (
        r.get("recommendation_score", -1) is None,
        -(r.get("recommendation_score") or 0),
        r.get("best_full_upper_triangular_defect_linf_max") if r.get("best_full_upper_triangular_defect_linf_max") is not None else float("inf"),
    ))
    counts = {"tasks": len(tasks), "completed_records": len(rows), "ready": 0, "moderate": 0, "needs_polish": 0}
    for r in rows:
        lab = str(r.get("recommendation_label", ""))
        if lab.startswith("ready"):
            counts["ready"] += 1
        elif lab.startswith("moderate"):
            counts["moderate"] += 1
        else:
            counts["needs_polish"] += 1
    summary = {
        "schema": "theorem_iii_trackb_phase4d_compact_report_v1",
        "status": "phase4d-target-frame-audit-complete",
        "diagnostic_only": True,
        "counts": counts,
        "parameters": {
            "npz_count": len(tasks),
            "workers_requested": int(workers),
            "workers_used": nw,
            "oversample_factors": [int(x) for x in oversample_factors],
            "cutoff_fracs": [float(x) for x in cutoff_fracs],
            "nu_grid": [float(x) for x in nu_grid],
            "tail_start_fracs": [float(x) for x in tail_start_fracs],
            "omega_override": omega_override,
        },
        "interpretation_hints": {
            "main_decision": "If target-frame recomputation drops determinant/triangular defects to sub-1e-4 or better, proceed to one more high-precision polish/intervalization prep; if not, improve the seed or frame model before intervalization.",
            "primary_fix_checked": "Recompute M(theta+omega)'s symplectic normal from the shifted tangent, instead of shifting the nonlinear normal vector.",
        },
        "top_candidates": rows[: min(60, len(rows))],
        "ranked_candidates": rows,
        "elapsed_seconds": float(time.time() - t0),
    }
    write_json(out / "phase4d_target_frame_summary.json", summary)
    csv_path = out / "phase4d_target_frame_results.csv"
    if rows:
        keys = sorted({k for row in rows for k in row.keys()})
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader(); w.writerows(rows)
    write_json(out / "phase4d_ranked_candidates.json", {"ranked_candidates": rows})
    return summary
