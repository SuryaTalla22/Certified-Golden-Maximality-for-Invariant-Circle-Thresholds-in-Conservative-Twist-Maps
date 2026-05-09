from __future__ import annotations

import csv
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
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


def _freq_grid(M: int) -> np.ndarray:
    return np.fft.fftfreq(int(M), d=1.0 / float(M))


def _coeff(values: np.ndarray) -> np.ndarray:
    return np.fft.fft(np.asarray(values, dtype=float)) / float(values.size)


def _samples_from_coeff(coeff: np.ndarray) -> np.ndarray:
    return np.fft.ifft(np.asarray(coeff) * float(coeff.size)).real


def _weighted_l1_from_coeff(c: np.ndarray, abs_freq: np.ndarray, nu: float) -> float:
    return float(np.sum(np.abs(c) * np.exp(math.log(float(nu)) * abs_freq)))


def _weighted_l1_samples(values: np.ndarray, freq: np.ndarray, nu: float) -> float:
    return _weighted_l1_from_coeff(_coeff(values), np.abs(freq), nu)


def _spectral_derivative(values: np.ndarray, freq: np.ndarray) -> np.ndarray:
    c = _coeff(values)
    dc = (1j * TWO_PI * np.asarray(freq, dtype=float)) * c
    return _samples_from_coeff(dc)


def _shift(values: np.ndarray, freq: np.ndarray, omega: float, sign: int = +1) -> np.ndarray:
    c = _coeff(values)
    mult = np.exp(1j * TWO_PI * np.asarray(freq, dtype=float) * float(omega) * (1 if sign >= 0 else -1))
    return _samples_from_coeff(c * mult)


def _tail_ratio_samples(values: np.ndarray, freq: np.ndarray, nu: float, frac: float) -> dict[str, float]:
    c = _coeff(values)
    af = np.abs(freq)
    vals = np.abs(c) * np.exp(math.log(float(nu)) * af)
    total = float(np.sum(vals))
    start = float(frac) * float(np.max(af)) if af.size else 0.0
    mask = af >= start
    tail = float(np.sum(vals[mask])) if np.any(mask) else 0.0
    return {"tail_start_mode": start, "weighted_tail_l1": tail, "weighted_tail_ratio": tail / total if total > 0.0 else 0.0}


def standard_map_df_entries(x: np.ndarray, K: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # F(x,r)=(x+r+K/(2pi)sin(2pi x), r+K/(2pi)sin(2pi x))
    c = float(K) * np.cos(TWO_PI * np.asarray(x, dtype=float))
    return 1.0 + c, np.ones_like(c), c, np.ones_like(c)


def scalar_residual_from_u(u: np.ndarray, K: float, omega: float, freq: np.ndarray) -> np.ndarray:
    theta = np.arange(u.size, dtype=float) / float(u.size)
    return _shift(u, freq, omega, +1) - 2.0 * u + _shift(u, freq, omega, -1) - (float(K) / TWO_PI) * np.sin(TWO_PI * (theta + u))


def embedding_residuals(x: np.ndarray, r: np.ndarray, K: float, omega: float, freq: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    fx = x + r + (float(K) / TWO_PI) * np.sin(TWO_PI * x)
    fr = r + (float(K) / TWO_PI) * np.sin(TWO_PI * x)
    return fx - _shift(x, freq, omega, +1), fr - _shift(r, freq, omega, +1)


def automatic_reducibility_samples(u: np.ndarray, K: float, omega: float, freq: np.ndarray) -> dict[str, np.ndarray | float]:
    M = u.size
    theta = np.arange(M, dtype=float) / float(M)
    x = theta + u
    x_minus = theta - float(omega) + _shift(u, freq, omega, -1)
    r = x - x_minus

    xp = 1.0 + _spectral_derivative(u, freq)
    rp = _spectral_derivative(r, freq)
    norm2 = xp * xp + rp * rp
    # Symplectic normal n=(-r',x')/||W'||^2. Then det([t,n])=1.
    nx = -rp / norm2
    nr = xp / norm2

    # Shifted frame at theta+omega.
    xp_s = _shift(xp, freq, omega, +1)
    rp_s = _shift(rp, freq, omega, +1)
    nx_s = _shift(nx, freq, omega, +1)
    nr_s = _shift(nr, freq, omega, +1)

    a, b, c, d = standard_map_df_entries(x, K)
    # Apply DF to tangent and normal.
    Dtx = a * xp + b * rp
    Dtr = c * xp + d * rp
    Dnx = a * nx + b * nr
    Dnr = c * nx + d * nr

    # Since det shifted frame is 1, inverse is [[nr_s,-nx_s],[-rp_s,xp_s]].
    A11 = nr_s * Dtx - nx_s * Dtr
    A21 = -rp_s * Dtx + xp_s * Dtr
    A12 = nr_s * Dnx - nx_s * Dnr
    A22 = -rp_s * Dnx + xp_s * Dnr

    det_frame = xp * nr - rp * nx
    det_shifted = xp_s * nr_s - rp_s * nx_s
    symplectic_defect = det_frame - 1.0
    shifted_symplectic_defect = det_shifted - 1.0
    twist = A12
    twist_avg = float(np.mean(twist))
    return {
        "x": x, "r": r,
        "xp": xp, "rp": rp, "nx": nx, "nr": nr,
        "norm2": norm2,
        "A11": A11, "A12": A12, "A21": A21, "A22": A22,
        "det_frame": det_frame, "det_shifted": det_shifted,
        "symplectic_defect": symplectic_defect,
        "shifted_symplectic_defect": shifted_symplectic_defect,
        "twist": twist,
        "twist_average": twist_avg,
        "res_scalar": scalar_residual_from_u(u, K, omega, freq),
    }


@dataclass(slots=True)
class AutoReducibilityAuditConfig:
    npz_path: str
    out_dir: str
    nu_grid: tuple[float, ...] = (1.002, 1.003, 1.005)
    tail_start_fracs: tuple[float, ...] = (0.50, 0.75, 0.90)
    omega_override: float | None = None
    force: bool = False
    y_safety_factor: float = 8.0
    z_safety_factor: float = 8.0
    q_safety_factor: float = 8.0


def audit_npz_auto_reducibility(cfg: AutoReducibilityAuditConfig) -> dict[str, Any]:
    t0 = time.time()
    npz_path = Path(cfg.npz_path)
    tag = npz_path.stem
    out_dir = Path(cfg.out_dir)
    record_path = out_dir / "records" / f"{tag}.phase4_auto_reducibility_audit.json"
    if record_path.exists() and not cfg.force:
        try:
            d = json.loads(record_path.read_text(encoding="utf-8"))
            d["loaded_from_existing_record"] = True
            return d
        except Exception:
            pass

    with np.load(npz_path, allow_pickle=False) as z:
        K = _as_float(z.get("K"), None)
        M_npz = int(_as_float(z.get("M"), 0) or 0)
        omega_in = _as_float(z.get("omega"), GOLDEN_OMEGA)
        omega = float(cfg.omega_override if cfg.omega_override is not None else (omega_in if omega_in is not None else GOLDEN_OMEGA))
        u = np.asarray(z["u"], dtype=float)
        freq = np.asarray(z["freq"], dtype=float) if "freq" in z else _freq_grid(u.size)
        schema = str(np.asarray(z["schema"]).reshape(()).item()) if "schema" in z else "unknown"
    if K is None:
        raise ValueError(f"Missing K in {npz_path}")
    M = int(u.size)
    if M_npz and M_npz != M:
        raise ValueError(f"M mismatch in {npz_path}: field {M_npz}, u.size {M}")
    max_mode = int(np.max(np.abs(freq))) if freq.size else M // 2
    ar = automatic_reducibility_samples(u, float(K), omega, freq)
    x = np.asarray(ar["x"]); r = np.asarray(ar["r"])
    ex, er = embedding_residuals(x, r, float(K), omega, freq)
    res_scalar = np.asarray(ar["res_scalar"])

    A11 = np.asarray(ar["A11"]); A12 = np.asarray(ar["A12"]); A21 = np.asarray(ar["A21"]); A22 = np.asarray(ar["A22"])
    twist = np.asarray(ar["twist"])
    twist_avg = float(ar["twist_average"])
    S_centered = twist - twist_avg
    xp = np.asarray(ar["xp"]); rp = np.asarray(ar["rp"]); nx = np.asarray(ar["nx"]); nr = np.asarray(ar["nr"])
    norm2 = np.asarray(ar["norm2"])
    det_def = np.asarray(ar["symplectic_defect"])
    det_shift_def = np.asarray(ar["shifted_symplectic_defect"])

    scalar_metrics = {
        "x_residual_linf": float(np.max(np.abs(ex))),
        "r_residual_linf": float(np.max(np.abs(er))),
        "embedding_residual_linf_max": float(max(np.max(np.abs(ex)), np.max(np.abs(er)))),
        "scalar_residual_linf": float(np.max(np.abs(res_scalar))),
        "a11_minus_1_linf": float(np.max(np.abs(A11 - 1.0))),
        "a21_linf": float(np.max(np.abs(A21))),
        "a22_minus_1_linf": float(np.max(np.abs(A22 - 1.0))),
        "upper_triangular_defect_linf_max": float(max(np.max(np.abs(A11 - 1.0)), np.max(np.abs(A21)), np.max(np.abs(A22 - 1.0)))),
        "twist_average": twist_avg,
        "twist_abs_average": abs(twist_avg),
        "twist_min": float(np.min(twist)),
        "twist_max": float(np.max(twist)),
        "twist_std": float(np.std(twist)),
        "twist_centered_linf": float(np.max(np.abs(S_centered))),
        "frame_tangent_norm_min": float(np.sqrt(np.min(norm2))),
        "frame_tangent_norm_max": float(np.sqrt(np.max(norm2))),
        "frame_normal_norm_max": float(np.max(np.sqrt(nx * nx + nr * nr))),
        "frame_det_defect_linf": float(np.max(np.abs(det_def))),
        "shifted_frame_det_defect_linf": float(np.max(np.abs(det_shift_def))),
        "xprime_min": float(np.min(xp)),
        "xprime_max": float(np.max(xp)),
        "rprime_linf": float(np.max(np.abs(rp))),
    }

    weighted: dict[str, Any] = {}
    for nu in cfg.nu_grid:
        nu = float(nu)
        residual_l1 = max(_weighted_l1_samples(ex, freq, nu), _weighted_l1_samples(er, freq, nu), _weighted_l1_samples(res_scalar, freq, nu))
        a11d = _weighted_l1_samples(A11 - 1.0, freq, nu)
        a21d = _weighted_l1_samples(A21, freq, nu)
        a22d = _weighted_l1_samples(A22 - 1.0, freq, nu)
        s_cent = _weighted_l1_samples(S_centered, freq, nu)
        detd = max(_weighted_l1_samples(det_def, freq, nu), _weighted_l1_samples(det_shift_def, freq, nu))
        # Conservative diagnostic proxies: real theorem phase must derive these constants with intervals.
        Y_proxy = cfg.y_safety_factor * residual_l1
        Z_proxy = cfg.z_safety_factor * (a11d + a21d + a22d + detd)
        # Nonlinear proxy includes frame size, forcing curvature scale, and twist fluctuation.
        frame_size = float(max(np.max(np.sqrt(xp*xp + rp*rp)), np.max(np.sqrt(nx*nx + nr*nr))))
        Q_proxy = cfg.q_safety_factor * (abs(float(K)) * TWO_PI * (1.0 + frame_size) ** 2 + s_cent + 1.0)
        r_candidate = max(10.0 * Y_proxy, 1e-14)
        lhs = Y_proxy + Z_proxy * r_candidate + Q_proxy * r_candidate * r_candidate
        margin = r_candidate - lhs
        tails = {
            f"frac_{f:.3f}": {
                "a21_tail": _tail_ratio_samples(A21, freq, nu, f),
                "a11_minus_1_tail": _tail_ratio_samples(A11 - 1.0, freq, nu, f),
                "a22_minus_1_tail": _tail_ratio_samples(A22 - 1.0, freq, nu, f),
                "residual_tail": _tail_ratio_samples(res_scalar, freq, nu, f),
            }
            for f in cfg.tail_start_fracs
        }
        weighted[f"nu_{nu:.6f}"] = {
            "nu": nu,
            "embedding_residual_l1_nu_proxy": residual_l1,
            "a11_minus_1_l1_nu": a11d,
            "a21_l1_nu": a21d,
            "a22_minus_1_l1_nu": a22d,
            "twist_centered_l1_nu": s_cent,
            "frame_det_defect_l1_nu": detd,
            "Y_proxy": Y_proxy,
            "Z_proxy": Z_proxy,
            "Q_proxy": Q_proxy,
            "r_candidate_proxy": r_candidate,
            "radii_lhs_proxy": lhs,
            "radii_margin_proxy": margin,
            "radii_proxy_positive_margin": bool(margin > 0.0),
            "tail_ratios": tails,
        }

    rep = weighted.get("nu_1.003000") or weighted.get("nu_1.005000") or next(iter(weighted.values()), {})
    score = 0
    reasons: list[str] = []
    if scalar_metrics["embedding_residual_linf_max"] < 1e-9:
        score += 2; reasons.append("embedding_residual_linf_max<1e-9")
    elif scalar_metrics["embedding_residual_linf_max"] < 1e-7:
        score += 1; reasons.append("embedding_residual_linf_max<1e-7")
    if scalar_metrics["upper_triangular_defect_linf_max"] < 1e-8:
        score += 2; reasons.append("upper_triangular_defect_linf_max<1e-8")
    elif scalar_metrics["upper_triangular_defect_linf_max"] < 1e-6:
        score += 1; reasons.append("upper_triangular_defect_linf_max<1e-6")
    if scalar_metrics["twist_abs_average"] > 1e-3:
        score += 1; reasons.append("twist_average bounded away from 0 diagnostically")
    if bool(rep.get("radii_proxy_positive_margin", False)):
        score += 1; reasons.append("diagnostic radii proxy positive")
    label = "strong_phase4_candidate" if score >= 5 else ("moderate_phase4_candidate" if score >= 3 else "weak_or_needs_auto_reducibility_improvement")

    payload: dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase4_auto_reducibility_audit_v1",
        "phase": "TrackB-Phase4-automatic-reducibility-radii-proxy-audit",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "important_warning": "Double-precision diagnostic only. This does not prove automatic reducibility, radii bounds, or Theorem III.",
        "npz_path": str(npz_path),
        "record_path": str(record_path),
        "source_npz_schema": schema,
        "K": K,
        "M": M,
        "max_mode": max_mode,
        "omega": omega,
        "nu_grid": [float(x) for x in cfg.nu_grid],
        "tail_start_fracs": [float(x) for x in cfg.tail_start_fracs],
        "scalar_metrics": scalar_metrics,
        "weighted_auto_reducibility_norms": weighted,
        "recommendation": {
            "label": label,
            "score": score,
            "reasons": reasons,
            "representative_nu_used": rep.get("nu") if isinstance(rep, dict) else None,
            "representative_Y_proxy": rep.get("Y_proxy") if isinstance(rep, dict) else None,
            "representative_Z_proxy": rep.get("Z_proxy") if isinstance(rep, dict) else None,
            "representative_Q_proxy": rep.get("Q_proxy") if isinstance(rep, dict) else None,
            "representative_radii_margin_proxy": rep.get("radii_margin_proxy") if isinstance(rep, dict) else None,
            "next_phase_hint": "If strong at the final anchor, intervalize Fourier arithmetic and exactify golden small-divisor/reducibility constants.",
        },
        "elapsed_seconds": float(time.time() - t0),
    }
    write_json(record_path, payload)
    return payload


def _cfg_dict(cfg: AutoReducibilityAuditConfig) -> dict[str, Any]:
    return asdict(cfg)


def _compact_row(rec: dict[str, Any]) -> dict[str, Any]:
    weighted = rec.get("weighted_auto_reducibility_norms", {})
    rep = weighted.get("nu_1.003000") or weighted.get("nu_1.005000") or next(iter(weighted.values()), {})
    sm = rec.get("scalar_metrics", {})
    return {
        "K": rec.get("K"),
        "M": rec.get("M"),
        "npz_path": rec.get("npz_path"),
        "record_path": rec.get("record_path"),
        "embedding_residual_linf_max": sm.get("embedding_residual_linf_max"),
        "scalar_residual_linf": sm.get("scalar_residual_linf"),
        "upper_triangular_defect_linf_max": sm.get("upper_triangular_defect_linf_max"),
        "a11_minus_1_linf": sm.get("a11_minus_1_linf"),
        "a21_linf": sm.get("a21_linf"),
        "a22_minus_1_linf": sm.get("a22_minus_1_linf"),
        "twist_average": sm.get("twist_average"),
        "twist_min": sm.get("twist_min"),
        "twist_max": sm.get("twist_max"),
        "twist_centered_linf": sm.get("twist_centered_linf"),
        "frame_tangent_norm_min": sm.get("frame_tangent_norm_min"),
        "frame_tangent_norm_max": sm.get("frame_tangent_norm_max"),
        "frame_normal_norm_max": sm.get("frame_normal_norm_max"),
        "frame_det_defect_linf": sm.get("frame_det_defect_linf"),
        "rep_nu": rep.get("nu") if isinstance(rep, dict) else None,
        "rep_embedding_residual_l1_nu_proxy": rep.get("embedding_residual_l1_nu_proxy") if isinstance(rep, dict) else None,
        "rep_a21_l1_nu": rep.get("a21_l1_nu") if isinstance(rep, dict) else None,
        "rep_Z_proxy": rep.get("Z_proxy") if isinstance(rep, dict) else None,
        "rep_Q_proxy": rep.get("Q_proxy") if isinstance(rep, dict) else None,
        "rep_radii_margin_proxy": rep.get("radii_margin_proxy") if isinstance(rep, dict) else None,
        "rep_radii_proxy_positive_margin": rep.get("radii_proxy_positive_margin") if isinstance(rep, dict) else None,
        "recommendation_label": rec.get("recommendation", {}).get("label"),
        "recommendation_score": rec.get("recommendation", {}).get("score"),
    }


def _task(cfgd: dict[str, Any]) -> dict[str, Any]:
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
        os.environ.setdefault(k, "1")
    return _compact_row(audit_npz_auto_reducibility(AutoReducibilityAuditConfig(**cfgd)))


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


def run_phase4_auto_reducibility_audit(
    *,
    npz_paths: Sequence[str],
    out_dir: str | Path,
    workers: int = 1,
    nu_grid: Sequence[float] = (1.002, 1.003, 1.005),
    tail_start_fracs: Sequence[float] = (0.50, 0.75, 0.90),
    omega_override: float | None = None,
    force: bool = False,
    y_safety_factor: float = 8.0,
    z_safety_factor: float = 8.0,
    q_safety_factor: float = 8.0,
) -> dict[str, Any]:
    t0 = time.time()
    out = Path(out_dir)
    (out / "records").mkdir(parents=True, exist_ok=True)
    tasks = [_cfg_dict(AutoReducibilityAuditConfig(
        npz_path=str(Path(p)), out_dir=str(out),
        nu_grid=tuple(float(x) for x in nu_grid),
        tail_start_fracs=tuple(float(x) for x in tail_start_fracs),
        omega_override=omega_override, force=bool(force),
        y_safety_factor=float(y_safety_factor), z_safety_factor=float(z_safety_factor), q_safety_factor=float(q_safety_factor),
    )) for p in npz_paths]
    rows: list[dict[str, Any]] = []
    nw = max(1, min(int(workers), len(tasks))) if tasks else 1
    if nw == 1:
        for td in tasks:
            rows.append(_task(td))
    else:
        with ProcessPoolExecutor(max_workers=nw) as ex:
            futs = [ex.submit(_task, td) for td in tasks]
            for fut in as_completed(futs):
                row = fut.result()
                rows.append(row)
                print(f"[phase4] K={row.get('K')} M={row.get('M')} tri={row.get('upper_triangular_defect_linf_max')} twist={row.get('twist_average')} label={row.get('recommendation_label')}", flush=True)
    rows.sort(key=lambda r: (float(r.get("K") or 0.0), int(r.get("M") or 0)))
    def rank_key(r: dict[str, Any]) -> tuple[float, float, float, float]:
        label_bonus = {"strong_phase4_candidate": 0.0, "moderate_phase4_candidate": 1.0}.get(str(r.get("recommendation_label")), 2.0)
        # Prefer final-target/high-M, low defect.
        return (label_bonus, -float(r.get("M") or 0), float(r.get("upper_triangular_defect_linf_max") or 1e300), float(r.get("embedding_residual_linf_max") or 1e300))
    ranked = sorted(rows, key=rank_key)
    summary: dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase4_auto_reducibility_summary_v1",
        "phase": "TrackB-Phase4-automatic-reducibility-radii-proxy-audit",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "status": "phase4-auto-reducibility-audit-complete" if rows else "no-npz-inputs",
        "parameters": {"npz_count": len(npz_paths), "workers_requested": int(workers), "workers_used": int(nw), "nu_grid": [float(x) for x in nu_grid], "tail_start_fracs": [float(x) for x in tail_start_fracs], "omega_override": omega_override, "y_safety_factor": y_safety_factor, "z_safety_factor": z_safety_factor, "q_safety_factor": q_safety_factor},
        "counts": {"tasks": len(tasks), "completed_records": len(rows), "strong": sum(r.get("recommendation_label") == "strong_phase4_candidate" for r in rows), "moderate": sum(r.get("recommendation_label") == "moderate_phase4_candidate" for r in rows), "weak": sum(r.get("recommendation_label") == "weak_or_needs_auto_reducibility_improvement" for r in rows)},
        "ranked_candidates": ranked,
        "best_12_candidates": ranked[:12],
        "records": rows,
        "elapsed_seconds": float(time.time() - t0),
    }
    write_json(out / "phase4_auto_reducibility_summary.json", summary)
    write_json(out / "phase4_ranked_candidates.json", {"schema": "theorem_iii_trackb_phase4_ranked_candidates_v1", "candidates": ranked})
    csv_path = out / "phase4_auto_reducibility_results.csv"
    fields = [
        "K", "M", "embedding_residual_linf_max", "scalar_residual_linf", "upper_triangular_defect_linf_max", "a11_minus_1_linf", "a21_linf", "a22_minus_1_linf", "twist_average", "twist_min", "twist_max", "twist_centered_linf", "frame_tangent_norm_min", "frame_tangent_norm_max", "frame_normal_norm_max", "frame_det_defect_linf", "rep_nu", "rep_embedding_residual_l1_nu_proxy", "rep_a21_l1_nu", "rep_Z_proxy", "rep_Q_proxy", "rep_radii_margin_proxy", "rep_radii_proxy_positive_margin", "recommendation_label", "recommendation_score", "npz_path", "record_path",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})
    summary["csv"] = str(csv_path)
    return summary
