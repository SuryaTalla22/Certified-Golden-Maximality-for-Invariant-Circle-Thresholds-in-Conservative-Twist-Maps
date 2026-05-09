from __future__ import annotations

import csv
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np


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
    return o


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(_clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


@dataclass(slots=True)
class TailAuditConfig:
    npz_path: str
    out_dir: str
    nu_grid: tuple[float, ...] = (1.002, 1.003, 1.005, 1.008, 1.010, 1.012, 1.015)
    tail_start_fracs: tuple[float, ...] = (0.25, 0.50, 0.75, 0.85, 0.90)
    fit_min_frac: float = 0.08
    fit_max_frac: float = 0.70
    coefficient_floor_rel: float = 1e-14
    coefficient_floor_abs: float = 1e-300
    shell_count: int = 24
    force: bool = False


def _as_float(x: Any, default: float | None = None) -> float | None:
    try:
        y = float(np.asarray(x).reshape(()))
        return y if math.isfinite(y) else default
    except Exception:
        return default


def _as_bool(x: Any, default: bool = False) -> bool:
    try:
        if isinstance(x, np.ndarray):
            return bool(x.reshape(()).item())
        return bool(x)
    except Exception:
        return default


def _normalized_coeff_from_samples(values: np.ndarray) -> np.ndarray:
    return np.fft.fft(np.asarray(values, dtype=float)) / float(values.size)


def _freq_grid(M: int) -> np.ndarray:
    return np.fft.fftfreq(int(M), d=1.0 / float(M))


def _weighted_l1(coeff: np.ndarray, abs_freq: np.ndarray, nu: float) -> float:
    log_nu = math.log(float(nu))
    # The mode counts here are modest; direct exp is safe for the requested nu/M range.
    return float(np.sum(np.abs(coeff) * np.exp(log_nu * abs_freq)))


def _plain_l1(coeff: np.ndarray) -> float:
    return float(np.sum(np.abs(coeff)))


def _l2_coeff(coeff: np.ndarray) -> float:
    return float(math.sqrt(np.sum(np.abs(coeff) ** 2)))


def _tail_stats(coeff: np.ndarray, abs_freq: np.ndarray, tail_start_fracs: Sequence[float]) -> dict[str, Any]:
    mag = np.abs(coeff)
    total_l1 = float(np.sum(mag))
    kmax = float(np.max(abs_freq)) if abs_freq.size else 0.0
    out: dict[str, Any] = {}
    for frac in tail_start_fracs:
        start = max(0.0, float(frac) * kmax)
        mask = abs_freq >= start
        l1 = float(np.sum(mag[mask]))
        linf = float(np.max(mag[mask])) if np.any(mask) else 0.0
        count = int(np.sum(mask))
        out[f"frac_{frac:.3f}"] = {
            "tail_start_mode": start,
            "tail_count": count,
            "tail_l1": l1,
            "tail_linf": linf,
            "tail_l1_ratio": (l1 / total_l1) if total_l1 > 0.0 else 0.0,
        }
    return out


def _tail_stats_for_nu(coeff: np.ndarray, abs_freq: np.ndarray, tail_start_fracs: Sequence[float], nu: float) -> dict[str, Any]:
    weights = np.exp(math.log(float(nu)) * abs_freq)
    wmag = np.abs(coeff) * weights
    total_l1 = float(np.sum(wmag))
    kmax = float(np.max(abs_freq)) if abs_freq.size else 0.0
    out: dict[str, Any] = {}
    for frac in tail_start_fracs:
        start = max(0.0, float(frac) * kmax)
        mask = abs_freq >= start
        l1 = float(np.sum(wmag[mask]))
        linf = float(np.max(wmag[mask])) if np.any(mask) else 0.0
        out[f"frac_{frac:.3f}"] = {
            "tail_start_mode": start,
            "weighted_tail_l1": l1,
            "weighted_tail_linf": linf,
            "weighted_tail_l1_ratio": (l1 / total_l1) if total_l1 > 0.0 else 0.0,
        }
    return out


def _fit_decay(coeff: np.ndarray, abs_freq: np.ndarray, fit_min_frac: float, fit_max_frac: float, floor_rel: float, floor_abs: float) -> dict[str, Any]:
    mag = np.abs(coeff)
    kmax = float(np.max(abs_freq)) if abs_freq.size else 0.0
    maxmag = float(np.max(mag)) if mag.size else 0.0
    floor = max(float(floor_abs), maxmag * float(floor_rel))
    mask = (abs_freq >= float(fit_min_frac) * kmax) & (abs_freq <= float(fit_max_frac) * kmax) & (mag > floor)
    n = int(np.sum(mask))
    if n < 8:
        return {
            "fit_available": False,
            "fit_points": n,
            "fit_reason": "fewer-than-8-usable-coefficients",
            "estimated_strip_width": None,
            "estimated_nu_from_decay": None,
            "slope": None,
            "intercept": None,
            "r2": None,
            "floor_used": floor,
        }
    x = abs_freq[mask].astype(float)
    y = np.log(mag[mask].astype(float))
    slope, intercept = np.polyfit(x, y, 1)
    yhat = slope * x + intercept
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else None
    strip = float(-slope) if slope < 0.0 and math.isfinite(float(slope)) else None
    nu = float(math.exp(strip)) if strip is not None and strip < 50.0 else None
    return {
        "fit_available": strip is not None,
        "fit_points": n,
        "estimated_strip_width": strip,
        "estimated_nu_from_decay": nu,
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": r2,
        "fit_min_mode": float(np.min(x)),
        "fit_max_mode": float(np.max(x)),
        "floor_used": floor,
    }


def _mode_shells(coeff: np.ndarray, abs_freq: np.ndarray, shell_count: int) -> list[dict[str, Any]]:
    mag = np.abs(coeff)
    kmax = int(np.max(abs_freq)) if abs_freq.size else 0
    if kmax <= 0:
        return []
    edges = np.linspace(0, kmax, int(shell_count) + 1)
    out: list[dict[str, Any]] = []
    for i in range(int(shell_count)):
        lo = float(edges[i])
        hi = float(edges[i + 1])
        if i == 0:
            mask = (abs_freq >= lo) & (abs_freq <= hi)
        else:
            mask = (abs_freq > lo) & (abs_freq <= hi)
        if not np.any(mask):
            continue
        vals = mag[mask]
        out.append({
            "shell_index": i,
            "mode_lo": lo,
            "mode_hi": hi,
            "count": int(vals.size),
            "l1": float(np.sum(vals)),
            "linf": float(np.max(vals)),
            "median": float(np.median(vals)),
            "mean_log10_abs": float(np.mean(np.log10(np.maximum(vals, 1e-300)))),
        })
    return out


def _geometric_envelopes(coeff: np.ndarray, abs_freq: np.ndarray, fit: dict[str, Any], tail_start_fracs: Sequence[float]) -> dict[str, Any]:
    """Return diagnostic exponential envelope constants.

    If |c_k| <= C exp(-alpha |k|) on the observed tail, then a continuation
    tail beyond kmax would be roughly 2 C exp(-alpha (kmax+1))/(1-exp(-alpha)).
    This is NOT yet a rigorous theorem tail, because it only fits/majorizes the
    observed finite coefficients. Phase 3/4 must replace it with interval-safe
    majorants.
    """
    mag = np.abs(coeff)
    kmax = float(np.max(abs_freq)) if abs_freq.size else 0.0
    alpha = fit.get("estimated_strip_width")
    if alpha is None or not math.isfinite(float(alpha)) or float(alpha) <= 0.0:
        return {"available": False, "reason": "no-positive-decay-fit"}
    alpha = float(alpha)
    out: dict[str, Any] = {"available": True, "alpha": alpha, "kmax": kmax, "by_tail_start": {}}
    for frac in tail_start_fracs:
        start = float(frac) * kmax
        mask = abs_freq >= start
        if not np.any(mask):
            continue
        C = float(np.max(mag[mask] * np.exp(alpha * abs_freq[mask])))
        rho = math.exp(-alpha)
        beyond_kmax_l1_two_sided = float(2.0 * C * math.exp(-alpha * (kmax + 1.0)) / max(1e-300, 1.0 - rho))
        observed_tail_l1 = float(np.sum(mag[mask]))
        out["by_tail_start"][f"frac_{frac:.3f}"] = {
            "tail_start_mode": start,
            "C_observed_majorant": C,
            "rho": rho,
            "observed_tail_l1": observed_tail_l1,
            "diagnostic_beyond_kmax_l1_two_sided": beyond_kmax_l1_two_sided,
        }
    return out


def _monotonicity(coeff: np.ndarray, abs_freq: np.ndarray) -> dict[str, Any]:
    # Collapse +/- modes by max magnitude at integer |k|.
    mag = np.abs(coeff)
    kmax = int(np.max(abs_freq)) if abs_freq.size else 0
    radial = np.zeros(kmax + 1, dtype=float)
    for k in range(kmax + 1):
        mask = abs_freq == float(k)
        if np.any(mask):
            radial[k] = float(np.max(mag[mask]))
    # Find earliest index after which radial envelope is nonincreasing, up to tiny floors.
    floor = max(float(np.max(radial)) * 1e-14, 1e-300) if radial.size else 1e-300
    best = None
    for start in range(1, kmax + 1):
        vals = np.maximum(radial[start:], floor)
        if vals.size <= 2:
            best = start
            break
        if bool(np.all(vals[1:] <= vals[:-1] * (1.0 + 1e-10))):
            best = start
            break
    increases = []
    for k in range(1, kmax):
        if radial[k + 1] > radial[k] * (1.0 + 1e-8) and radial[k + 1] > floor:
            increases.append({"k": k, "c_k": float(radial[k]), "c_next": float(radial[k + 1]), "ratio": float(radial[k + 1] / max(radial[k], 1e-300))})
            if len(increases) >= 20:
                break
    return {
        "eventually_nonincreasing_from_mode": best,
        "first_20_significant_increases": increases,
        "significant_increase_count_capped": len(increases),
        "floor_used": floor,
    }


def _recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    residual_linf = payload.get("residual_linf")
    residual_l1_best = None
    for nu_s, row in payload.get("weighted_norms", {}).items():
        try:
            v = float(row.get("residual_l1_nu"))
            if residual_l1_best is None or v < residual_l1_best:
                residual_l1_best = v
        except Exception:
            pass
    fit_strip = payload.get("u_decay_fit", {}).get("estimated_strip_width")
    half_nu = math.exp(0.5 * float(fit_strip)) if fit_strip is not None and float(fit_strip) > 0 else None
    quarter_nu = math.exp(0.25 * float(fit_strip)) if fit_strip is not None and float(fit_strip) > 0 else None
    tail_075 = payload.get("u_tail_stats_plain", {}).get("frac_0.750", {}).get("tail_l1_ratio")
    score = 0
    reasons = []
    try:
        if float(residual_linf) < 1e-10:
            score += 2; reasons.append("residual_linf<1e-10")
        elif float(residual_linf) < 1e-8:
            score += 1; reasons.append("residual_linf<1e-8")
        else:
            reasons.append("residual_linf-not-small")
    except Exception:
        reasons.append("missing-residual_linf")
    try:
        if float(tail_075) < 1e-3:
            score += 2; reasons.append("plain-tail-after-75pct<1e-3")
        elif float(tail_075) < 1e-2:
            score += 1; reasons.append("plain-tail-after-75pct<1e-2")
        else:
            reasons.append("plain-tail-after-75pct-large")
    except Exception:
        reasons.append("missing-tail-075")
    try:
        if half_nu is not None and half_nu >= 1.005:
            score += 2; reasons.append("half-decay-nu>=1.005")
        elif half_nu is not None and half_nu >= 1.002:
            score += 1; reasons.append("half-decay-nu>=1.002")
        else:
            reasons.append("decay-fit-gives-small-safe-nu")
    except Exception:
        reasons.append("missing-decay-fit")
    if score >= 5:
        label = "strong_phase2_candidate"
    elif score >= 3:
        label = "moderate_phase2_candidate"
    else:
        label = "weak_or_needs_higher_resolution"
    return {
        "label": label,
        "score": score,
        "reasons": reasons,
        "recommended_conservative_nu_quarter_fit": quarter_nu,
        "recommended_conservative_nu_half_fit": half_nu,
        "note": "Diagnostic only. These recommendations do not certify a theorem-facing tail bound.",
    }


def audit_npz(cfg: TailAuditConfig) -> dict[str, Any]:
    t0 = time.time()
    npz_path = Path(cfg.npz_path)
    tag = npz_path.stem
    out_dir = Path(cfg.out_dir)
    record_path = out_dir / "records" / f"{tag}.phase2_tail_audit.json"
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
        omega = _as_float(z.get("omega"), None)
        u = np.asarray(z["u"], dtype=float)
        residual_samples = np.asarray(z["residual"], dtype=float) if "residual" in z else None
        freq = np.asarray(z["freq"], dtype=float) if "freq" in z else _freq_grid(u.size)
        u_coeff_saved = np.asarray(z["u_coeff"]) if "u_coeff" in z else None
        residual_coeff_saved = np.asarray(z["residual_coeff"]) if "residual_coeff" in z else None
        schema = str(np.asarray(z["schema"]).reshape(()).item()) if "schema" in z else "unknown"
        diagnostic_only_in = _as_bool(z.get("diagnostic_only"), True)
        theorem_facing_in = _as_bool(z.get("theorem_facing"), False)

    M = int(u.size)
    if M_npz and M_npz != M:
        raise ValueError(f"M mismatch in {npz_path}: M field {M_npz}, u.size {M}")
    abs_freq = np.abs(freq)
    u_coeff = _normalized_coeff_from_samples(u)
    if u_coeff_saved is not None:
        coeff_mismatch = float(np.max(np.abs(u_coeff - u_coeff_saved)))
    else:
        coeff_mismatch = None
    if residual_samples is not None:
        residual_coeff = _normalized_coeff_from_samples(residual_samples)
        residual_linf = float(np.max(np.abs(residual_samples)))
        residual_l2 = float(np.linalg.norm(residual_samples) / math.sqrt(residual_samples.size))
    elif residual_coeff_saved is not None:
        residual_coeff = residual_coeff_saved
        residual_linf = None
        residual_l2 = None
    else:
        residual_coeff = np.zeros_like(u_coeff)
        residual_linf = None
        residual_l2 = None
    if residual_coeff_saved is not None and residual_samples is not None:
        residual_coeff_mismatch = float(np.max(np.abs(residual_coeff - residual_coeff_saved)))
    else:
        residual_coeff_mismatch = None

    weighted: dict[str, Any] = {}
    for nu in cfg.nu_grid:
        weighted[f"nu_{float(nu):.6f}"] = {
            "nu": float(nu),
            "u_l1_nu": _weighted_l1(u_coeff, abs_freq, float(nu)),
            "residual_l1_nu": _weighted_l1(residual_coeff, abs_freq, float(nu)),
            "u_weighted_tail_stats": _tail_stats_for_nu(u_coeff, abs_freq, cfg.tail_start_fracs, float(nu)),
            "residual_weighted_tail_stats": _tail_stats_for_nu(residual_coeff, abs_freq, cfg.tail_start_fracs, float(nu)),
        }

    u_fit = _fit_decay(u_coeff, abs_freq, cfg.fit_min_frac, cfg.fit_max_frac, cfg.coefficient_floor_rel, cfg.coefficient_floor_abs)
    residual_fit = _fit_decay(residual_coeff, abs_freq, cfg.fit_min_frac, cfg.fit_max_frac, cfg.coefficient_floor_rel, cfg.coefficient_floor_abs)

    payload: dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase2_fourier_tail_audit_v1",
        "phase": "TrackB-Phase2-Fourier-tail-audit",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "npz_path": str(npz_path),
        "record_path": str(record_path),
        "source_npz_schema": schema,
        "source_npz_diagnostic_only": diagnostic_only_in,
        "source_npz_theorem_facing": theorem_facing_in,
        "K": K,
        "M": M,
        "omega": omega,
        "nu_grid": [float(x) for x in cfg.nu_grid],
        "tail_start_fracs": [float(x) for x in cfg.tail_start_fracs],
        "fit_min_frac": float(cfg.fit_min_frac),
        "fit_max_frac": float(cfg.fit_max_frac),
        "coefficient_checks": {
            "u_coeff_recomputed_vs_saved_linf": coeff_mismatch,
            "residual_coeff_recomputed_vs_saved_linf": residual_coeff_mismatch,
        },
        "sample_norms": {
            "max_abs_u": float(np.max(np.abs(u))),
            "mean_u": float(np.mean(u)),
            "u_sample_linf": float(np.max(np.abs(u))),
            "u_sample_l2": float(np.linalg.norm(u) / math.sqrt(u.size)),
            "residual_linf": residual_linf,
            "residual_l2": residual_l2,
        },
        "coefficient_norms_plain": {
            "u_l1": _plain_l1(u_coeff),
            "u_l2": _l2_coeff(u_coeff),
            "u_linf": float(np.max(np.abs(u_coeff))),
            "residual_l1": _plain_l1(residual_coeff),
            "residual_l2": _l2_coeff(residual_coeff),
            "residual_linf_coeff": float(np.max(np.abs(residual_coeff))),
        },
        "residual_linf": residual_linf,
        "weighted_norms": weighted,
        "u_tail_stats_plain": _tail_stats(u_coeff, abs_freq, cfg.tail_start_fracs),
        "residual_tail_stats_plain": _tail_stats(residual_coeff, abs_freq, cfg.tail_start_fracs),
        "u_decay_fit": u_fit,
        "residual_decay_fit": residual_fit,
        "u_geometric_envelope_diagnostic": _geometric_envelopes(u_coeff, abs_freq, u_fit, cfg.tail_start_fracs),
        "residual_geometric_envelope_diagnostic": _geometric_envelopes(residual_coeff, abs_freq, residual_fit, cfg.tail_start_fracs),
        "u_eventual_monotonicity": _monotonicity(u_coeff, abs_freq),
        "u_mode_shells": _mode_shells(u_coeff, abs_freq, cfg.shell_count),
        "residual_mode_shells": _mode_shells(residual_coeff, abs_freq, cfg.shell_count),
        "elapsed_seconds": float(time.time() - t0),
    }
    payload["recommendation"] = _recommendation(payload)
    write_json(record_path, payload)
    return payload


def _cfg_dict(cfg: TailAuditConfig) -> dict[str, Any]:
    d = asdict(cfg)
    d["nu_grid"] = tuple(float(x) for x in cfg.nu_grid)
    d["tail_start_fracs"] = tuple(float(x) for x in cfg.tail_start_fracs)
    return d


def _task(cfgd: dict[str, Any]) -> dict[str, Any]:
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
        os.environ.setdefault(k, "1")
    cfg = TailAuditConfig(**cfgd)
    rec = audit_npz(cfg)
    return _compact_row(rec)


def _compact_row(rec: dict[str, Any]) -> dict[str, Any]:
    # Choose a representative nu if present.
    weighted = rec.get("weighted_norms", {})
    rep = weighted.get("nu_1.005000") or weighted.get("nu_1.008000") or next(iter(weighted.values()), {})
    rep_tail = rep.get("u_weighted_tail_stats", {}).get("frac_0.750", {}) if isinstance(rep, dict) else {}
    return {
        "npz_path": rec.get("npz_path"),
        "record_path": rec.get("record_path"),
        "K": rec.get("K"),
        "M": rec.get("M"),
        "residual_linf": rec.get("residual_linf"),
        "u_l1": rec.get("coefficient_norms_plain", {}).get("u_l1"),
        "u_tail_075_ratio_plain": rec.get("u_tail_stats_plain", {}).get("frac_0.750", {}).get("tail_l1_ratio"),
        "u_tail_090_ratio_plain": rec.get("u_tail_stats_plain", {}).get("frac_0.900", {}).get("tail_l1_ratio"),
        "u_decay_strip": rec.get("u_decay_fit", {}).get("estimated_strip_width"),
        "u_decay_nu": rec.get("u_decay_fit", {}).get("estimated_nu_from_decay"),
        "u_decay_r2": rec.get("u_decay_fit", {}).get("r2"),
        "recommended_nu_quarter_fit": rec.get("recommendation", {}).get("recommended_conservative_nu_quarter_fit"),
        "recommended_nu_half_fit": rec.get("recommendation", {}).get("recommended_conservative_nu_half_fit"),
        "recommendation_label": rec.get("recommendation", {}).get("label"),
        "recommendation_score": rec.get("recommendation", {}).get("score"),
        "rep_nu": rep.get("nu") if isinstance(rep, dict) else None,
        "rep_u_l1_nu": rep.get("u_l1_nu") if isinstance(rep, dict) else None,
        "rep_residual_l1_nu": rep.get("residual_l1_nu") if isinstance(rep, dict) else None,
        "rep_u_tail_075_weighted_ratio": rep_tail.get("weighted_tail_l1_ratio"),
    }


def load_npz_list_from_phase1_summary(
    phase1_summary: str | Path,
    *,
    selection: str = "converged",
    anchors: Sequence[float] | None = None,
    resolutions: Sequence[int] | None = None,
) -> list[str]:
    data = json.loads(Path(phase1_summary).read_text(encoding="utf-8"))
    anchor_set = {round(float(x), 12) for x in anchors} if anchors else None
    res_set = {int(x) for x in resolutions} if resolutions else None

    paths: list[str] = []
    if selection == "best_by_anchor":
        candidates = list(data.get("best_by_anchor", {}).values())
    else:
        candidates = list(data.get("records", []))

    for row in candidates:
        cfg = row.get("config", row)
        K = cfg.get("K_target", row.get("K_target"))
        M = cfg.get("M", row.get("M"))
        if K is None or M is None:
            continue
        if anchor_set is not None and round(float(K), 12) not in anchor_set:
            continue
        if res_set is not None and int(M) not in res_set:
            continue
        if selection == "converged" and not bool(row.get("converged")):
            continue
        p = row.get("output_npz") or row.get("npz")
        if p:
            paths.append(str(p))
    # Preserve order, remove duplicates.
    seen = set()
    out = []
    for p in paths:
        if p not in seen:
            out.append(p); seen.add(p)
    return out


def run_phase2_tail_audit(
    *,
    npz_paths: Sequence[str],
    out_dir: str | Path,
    workers: int = 1,
    nu_grid: Sequence[float] = (1.002, 1.003, 1.005, 1.008, 1.010, 1.012, 1.015),
    tail_start_fracs: Sequence[float] = (0.25, 0.50, 0.75, 0.85, 0.90),
    fit_min_frac: float = 0.08,
    fit_max_frac: float = 0.70,
    coefficient_floor_rel: float = 1e-14,
    shell_count: int = 24,
    force: bool = False,
) -> dict[str, Any]:
    t0 = time.time()
    out = Path(out_dir)
    (out / "records").mkdir(parents=True, exist_ok=True)
    paths = [str(Path(p)) for p in npz_paths]
    tasks = [
        _cfg_dict(TailAuditConfig(
            npz_path=p,
            out_dir=str(out),
            nu_grid=tuple(float(x) for x in nu_grid),
            tail_start_fracs=tuple(float(x) for x in tail_start_fracs),
            fit_min_frac=float(fit_min_frac),
            fit_max_frac=float(fit_max_frac),
            coefficient_floor_rel=float(coefficient_floor_rel),
            shell_count=int(shell_count),
            force=bool(force),
        ))
        for p in paths
    ]
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
                print(f"[phase2] K={row.get('K')} M={row.get('M')} residual_linf={row.get('residual_linf')} label={row.get('recommendation_label')} strip={row.get('u_decay_strip')}", flush=True)
    rows.sort(key=lambda r: (float(r.get("K") or 0.0), int(r.get("M") or 0)))

    # Rank candidates: prioritize target/final high resolution, small residual, and reasonable decay.
    def rank_key(r: dict[str, Any]) -> tuple[float, float, float, float]:
        label_bonus = {"strong_phase2_candidate": 0.0, "moderate_phase2_candidate": 1.0}.get(str(r.get("recommendation_label")), 2.0)
        # Larger M is better for proof seeding: sort by negative M after label.
        return (
            label_bonus,
            -float(r.get("M") or 0),
            float(r.get("residual_linf") or 1e300),
            -float(r.get("u_decay_strip") or 0.0),
        )
    ranked = sorted(rows, key=rank_key)
    by_anchor: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        key = f"{float(r.get('K') or 0.0):.10f}"
        by_anchor.setdefault(key, []).append(r)

    summary: dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase2_tail_audit_summary_v1",
        "phase": "TrackB-Phase2-Fourier-tail-audit",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "status": "phase2-tail-audit-complete" if rows else "no-npz-inputs",
        "parameters": {
            "npz_count": len(paths),
            "workers_requested": int(workers),
            "workers_used": int(nw),
            "nu_grid": [float(x) for x in nu_grid],
            "tail_start_fracs": [float(x) for x in tail_start_fracs],
            "fit_min_frac": float(fit_min_frac),
            "fit_max_frac": float(fit_max_frac),
            "coefficient_floor_rel": float(coefficient_floor_rel),
            "shell_count": int(shell_count),
        },
        "counts": {
            "tasks": len(tasks),
            "completed_records": len(rows),
            "strong": sum(r.get("recommendation_label") == "strong_phase2_candidate" for r in rows),
            "moderate": sum(r.get("recommendation_label") == "moderate_phase2_candidate" for r in rows),
            "weak": sum(r.get("recommendation_label") == "weak_or_needs_higher_resolution" for r in rows),
        },
        "ranked_candidates": ranked,
        "best_12_candidates": ranked[:12],
        "by_anchor": by_anchor,
        "elapsed_seconds": float(time.time() - t0),
        "records": rows,
    }
    write_json(out / "phase2_tail_audit_summary.json", summary)
    write_json(out / "phase2_ranked_candidates.json", {"schema": "theorem_iii_trackb_phase2_ranked_candidates_v1", "candidates": ranked})
    csv_path = out / "phase2_tail_audit_results.csv"
    fields = [
        "K", "M", "residual_linf", "u_l1", "u_tail_075_ratio_plain", "u_tail_090_ratio_plain",
        "u_decay_strip", "u_decay_nu", "u_decay_r2", "recommended_nu_quarter_fit",
        "recommended_nu_half_fit", "recommendation_label", "recommendation_score", "rep_nu",
        "rep_u_l1_nu", "rep_residual_l1_nu", "rep_u_tail_075_weighted_ratio", "npz_path", "record_path",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})
    summary["csv"] = str(csv_path)
    return summary
