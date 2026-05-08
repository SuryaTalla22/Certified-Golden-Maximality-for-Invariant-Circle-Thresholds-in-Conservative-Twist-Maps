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


def _normalized_coeff_from_samples(values: np.ndarray) -> np.ndarray:
    return np.fft.fft(np.asarray(values, dtype=float)) / float(values.size)


def _freq_grid(M: int) -> np.ndarray:
    return np.fft.fftfreq(int(M), d=1.0 / float(M))


def _dist_to_integer(x: np.ndarray | float) -> np.ndarray | float:
    return np.abs(np.asarray(x) - np.round(np.asarray(x)))


def _weighted_l1(coeff: np.ndarray, abs_freq: np.ndarray, nu: float) -> float:
    return float(np.sum(np.abs(coeff) * np.exp(math.log(float(nu)) * abs_freq)))


def small_divisor_table(max_mode: int, omega: float = GOLDEN_OMEGA) -> dict[str, Any]:
    """Double-precision diagnostic small-divisor table for k=1..max_mode.

    The theorem-facing phase must replace this with an exact/interval continued-
    fraction proof. This phase intentionally exports only diagnostics.
    """
    max_mode = int(max_mode)
    ks = np.arange(1, max_mode + 1, dtype=float)
    phases = ks * float(omega)
    dist = _dist_to_integer(phases)
    denom = np.abs(np.exp(1j * TWO_PI * phases) - 1.0)
    inv = 1.0 / np.maximum(denom, 1e-300)
    k_dist = ks * dist
    k_denom = ks * denom
    min_idx = int(np.argmin(denom))
    max_inv_idx = int(np.argmax(inv))
    worst_order = np.argsort(denom)[: min(20, max_mode)]
    worst = []
    for idx in worst_order:
        worst.append({
            "k": int(ks[idx]),
            "dist_to_integer": float(dist[idx]),
            "denominator_abs_exp_minus_1": float(denom[idx]),
            "inverse_abs": float(inv[idx]),
            "k_times_dist": float(k_dist[idx]),
            "k_times_denominator": float(k_denom[idx]),
        })
    # Conservative but nonrigorous golden Diophantine diagnostic. For the golden
    # rotation, k ||k omega|| has limiting worst value 1/sqrt(5). The theorem
    # phase should prove a rational lower constant. Here we record a deliberately
    # below-limit candidate constant for later proof.
    diagnostic_c = 0.40
    tail_inverse_slope = 1.0 / (4.0 * diagnostic_c)
    return {
        "max_mode": max_mode,
        "omega": float(omega),
        "min_denominator": float(denom[min_idx]),
        "min_denominator_mode": int(ks[min_idx]),
        "max_inverse": float(inv[max_inv_idx]),
        "max_inverse_mode": int(ks[max_inv_idx]),
        "min_k_times_dist": float(np.min(k_dist)),
        "min_k_times_dist_mode": int(ks[int(np.argmin(k_dist))]),
        "min_k_times_denominator": float(np.min(k_denom)),
        "worst_modes_by_denominator": worst,
        "golden_diagnostic_diophantine_constant_c": diagnostic_c,
        "diagnostic_tail_inverse_bound_form": "|inv_k| <= k/(4c) for c=0.40, not theorem-facing",
        "diagnostic_tail_inverse_slope": tail_inverse_slope,
        "diagnostic_tail_inverse_at_max_mode_plus_one": float(tail_inverse_slope * (max_mode + 1)),
    }


def _inverse_multipliers(freq: np.ndarray, omega: float) -> np.ndarray:
    phases = np.asarray(freq, dtype=float) * float(omega)
    denom = np.exp(1j * TWO_PI * phases) - 1.0
    inv = np.zeros_like(denom, dtype=complex)
    mask = np.asarray(freq) != 0
    inv[mask] = 1.0 / denom[mask]
    inv[~mask] = 0.0
    return inv


@dataclass(slots=True)
class SmallDivisorAuditConfig:
    npz_path: str
    out_dir: str
    nu_grid: tuple[float, ...] = (1.002, 1.003, 1.005, 1.008)
    tail_start_fracs: tuple[float, ...] = (0.50, 0.75, 0.85, 0.90)
    omega_override: float | None = None
    force: bool = False


def _weighted_tail_ratio(coeff: np.ndarray, abs_freq: np.ndarray, nu: float, frac: float) -> dict[str, float]:
    weights = np.exp(math.log(float(nu)) * abs_freq)
    vals = np.abs(coeff) * weights
    total = float(np.sum(vals))
    start = float(frac) * float(np.max(abs_freq)) if abs_freq.size else 0.0
    mask = abs_freq >= start
    tail = float(np.sum(vals[mask])) if np.any(mask) else 0.0
    return {
        "tail_start_mode": start,
        "weighted_tail_l1": tail,
        "weighted_tail_ratio": tail / total if total > 0.0 else 0.0,
    }


def audit_npz_small_divisor(cfg: SmallDivisorAuditConfig) -> dict[str, Any]:
    t0 = time.time()
    npz_path = Path(cfg.npz_path)
    tag = npz_path.stem
    out_dir = Path(cfg.out_dir)
    record_path = out_dir / "records" / f"{tag}.phase3_small_divisor_audit.json"
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
        residual_samples = np.asarray(z["residual"], dtype=float) if "residual" in z else None
        freq = np.asarray(z["freq"], dtype=float) if "freq" in z else _freq_grid(u.size)
        residual_coeff_saved = np.asarray(z["residual_coeff"]) if "residual_coeff" in z else None
        schema = str(np.asarray(z["schema"]).reshape(()).item()) if "schema" in z else "unknown"

    M = int(u.size)
    if M_npz and M_npz != M:
        raise ValueError(f"M mismatch in {npz_path}: M field {M_npz}, u.size {M}")
    abs_freq = np.abs(freq)
    max_mode = int(np.max(abs_freq)) if abs_freq.size else M // 2
    u_coeff = _normalized_coeff_from_samples(u)
    if residual_samples is not None:
        residual_coeff = _normalized_coeff_from_samples(residual_samples)
        residual_linf = float(np.max(np.abs(residual_samples)))
    elif residual_coeff_saved is not None:
        residual_coeff = residual_coeff_saved
        residual_linf = None
    else:
        residual_coeff = np.zeros_like(u_coeff)
        residual_linf = None

    inv = _inverse_multipliers(freq, omega)
    nonzero = freq != 0
    correction_coeff = residual_coeff * inv
    zero_mode_residual_abs = float(abs(residual_coeff[~nonzero][0])) if np.any(~nonzero) else 0.0
    finite_max_inverse = float(np.max(np.abs(inv[nonzero]))) if np.any(nonzero) else 0.0
    finite_max_inverse_mode = int(abs_freq[nonzero][int(np.argmax(np.abs(inv[nonzero])))]) if np.any(nonzero) else 0
    sd = small_divisor_table(max_mode, omega)

    weighted: dict[str, Any] = {}
    for nu in cfg.nu_grid:
        nu = float(nu)
        tail_res = {f"frac_{f:.3f}": _weighted_tail_ratio(residual_coeff, abs_freq, nu, f) for f in cfg.tail_start_fracs}
        tail_corr = {f"frac_{f:.3f}": _weighted_tail_ratio(correction_coeff, abs_freq, nu, f) for f in cfg.tail_start_fracs}
        weighted[f"nu_{nu:.6f}"] = {
            "nu": nu,
            "u_l1_nu": _weighted_l1(u_coeff, abs_freq, nu),
            "residual_l1_nu": _weighted_l1(residual_coeff, abs_freq, nu),
            "cohomology_correction_l1_nu": _weighted_l1(correction_coeff, abs_freq, nu),
            "correction_to_u_l1_nu_ratio": _weighted_l1(correction_coeff, abs_freq, nu) / max(_weighted_l1(u_coeff, abs_freq, nu), 1e-300),
            "residual_tail_ratios": tail_res,
            "correction_tail_ratios": tail_corr,
        }

    # Rank risk using a representative nu if available.
    rep = weighted.get("nu_1.003000") or weighted.get("nu_1.005000") or next(iter(weighted.values()), {})
    rep_corr = rep.get("cohomology_correction_l1_nu") if isinstance(rep, dict) else None
    rep_res = rep.get("residual_l1_nu") if isinstance(rep, dict) else None
    score = 0
    reasons: list[str] = []
    if residual_linf is not None and residual_linf < 1e-10:
        score += 2; reasons.append("residual_linf<1e-10")
    elif residual_linf is not None and residual_linf < 1e-8:
        score += 1; reasons.append("residual_linf<1e-8")
    else:
        reasons.append("residual_linf-not-small-or-missing")
    if rep_corr is not None and float(rep_corr) < 1e-8:
        score += 2; reasons.append("rep_cohomology_correction_l1_nu<1e-8")
    elif rep_corr is not None and float(rep_corr) < 1e-6:
        score += 1; reasons.append("rep_cohomology_correction_l1_nu<1e-6")
    else:
        reasons.append("cohomology-correction-large-or-missing")
    if zero_mode_residual_abs < 1e-12:
        score += 1; reasons.append("zero_mode_residual_abs<1e-12")
    if finite_max_inverse < 500.0:
        score += 1; reasons.append("finite_max_inverse<500")
    label = "strong_phase3_candidate" if score >= 5 else ("moderate_phase3_candidate" if score >= 3 else "weak_or_needs_seed_improvement")

    payload: dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase3_small_divisor_audit_v1",
        "phase": "TrackB-Phase3-small-divisor-cohomology-audit",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "npz_path": str(npz_path),
        "record_path": str(record_path),
        "source_npz_schema": schema,
        "K": K,
        "M": M,
        "max_mode": max_mode,
        "omega": omega,
        "nu_grid": [float(x) for x in cfg.nu_grid],
        "tail_start_fracs": [float(x) for x in cfg.tail_start_fracs],
        "residual_linf": residual_linf,
        "zero_mode_residual_abs": zero_mode_residual_abs,
        "finite_resolved_cohomology": {
            "max_inverse": finite_max_inverse,
            "max_inverse_mode": finite_max_inverse_mode,
            "note": "finite double-precision diagnostic multiplier bound; theorem phase must intervalize/exactify",
        },
        "small_divisor_diagnostics": sd,
        "weighted_cohomology_norms": weighted,
        "recommendation": {
            "label": label,
            "score": score,
            "reasons": reasons,
            "representative_nu_used": rep.get("nu") if isinstance(rep, dict) else None,
            "representative_residual_l1_nu": rep_res,
            "representative_correction_l1_nu": rep_corr,
            "note": "Diagnostic only. Phase 4 must validate automatic reducibility/radii bounds with outward rounding.",
        },
        "elapsed_seconds": float(time.time() - t0),
    }
    write_json(record_path, payload)
    return payload


def _cfg_dict(cfg: SmallDivisorAuditConfig) -> dict[str, Any]:
    d = asdict(cfg)
    d["nu_grid"] = tuple(float(x) for x in cfg.nu_grid)
    d["tail_start_fracs"] = tuple(float(x) for x in cfg.tail_start_fracs)
    return d


def _compact_row(rec: dict[str, Any]) -> dict[str, Any]:
    weighted = rec.get("weighted_cohomology_norms", {})
    rep = weighted.get("nu_1.003000") or weighted.get("nu_1.005000") or next(iter(weighted.values()), {})
    corr_tail = rep.get("correction_tail_ratios", {}).get("frac_0.750", {}) if isinstance(rep, dict) else {}
    return {
        "K": rec.get("K"),
        "M": rec.get("M"),
        "npz_path": rec.get("npz_path"),
        "record_path": rec.get("record_path"),
        "residual_linf": rec.get("residual_linf"),
        "zero_mode_residual_abs": rec.get("zero_mode_residual_abs"),
        "max_mode": rec.get("max_mode"),
        "small_divisor_min_denominator": rec.get("small_divisor_diagnostics", {}).get("min_denominator"),
        "small_divisor_min_mode": rec.get("small_divisor_diagnostics", {}).get("min_denominator_mode"),
        "finite_max_inverse": rec.get("finite_resolved_cohomology", {}).get("max_inverse"),
        "finite_max_inverse_mode": rec.get("finite_resolved_cohomology", {}).get("max_inverse_mode"),
        "rep_nu": rep.get("nu") if isinstance(rep, dict) else None,
        "rep_u_l1_nu": rep.get("u_l1_nu") if isinstance(rep, dict) else None,
        "rep_residual_l1_nu": rep.get("residual_l1_nu") if isinstance(rep, dict) else None,
        "rep_cohomology_correction_l1_nu": rep.get("cohomology_correction_l1_nu") if isinstance(rep, dict) else None,
        "rep_correction_to_u_ratio": rep.get("correction_to_u_l1_nu_ratio") if isinstance(rep, dict) else None,
        "rep_correction_tail_075_weighted_ratio": corr_tail.get("weighted_tail_ratio"),
        "recommendation_label": rec.get("recommendation", {}).get("label"),
        "recommendation_score": rec.get("recommendation", {}).get("score"),
    }


def _task(cfgd: dict[str, Any]) -> dict[str, Any]:
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
        os.environ.setdefault(k, "1")
    return _compact_row(audit_npz_small_divisor(SmallDivisorAuditConfig(**cfgd)))


def load_npz_list_from_phase2_summary(
    phase2_summary: str | Path,
    *,
    selection: str = "strong",
    anchors: Sequence[float] | None = None,
    resolutions: Sequence[int] | None = None,
    top: int | None = None,
) -> list[str]:
    data = json.loads(Path(phase2_summary).read_text(encoding="utf-8"))
    anchor_set = {round(float(x), 12) for x in anchors} if anchors else None
    res_set = {int(x) for x in resolutions} if resolutions else None
    candidates = list(data.get("ranked_candidates", data.get("records", [])))
    out: list[str] = []
    for row in candidates:
        label = str(row.get("recommendation_label", ""))
        if selection == "strong" and label != "strong_phase2_candidate":
            continue
        if selection == "all":
            pass
        K = row.get("K")
        M = row.get("M")
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


def run_phase3_small_divisor_audit(
    *,
    npz_paths: Sequence[str],
    out_dir: str | Path,
    workers: int = 1,
    nu_grid: Sequence[float] = (1.002, 1.003, 1.005, 1.008),
    tail_start_fracs: Sequence[float] = (0.50, 0.75, 0.85, 0.90),
    omega_override: float | None = None,
    force: bool = False,
) -> dict[str, Any]:
    t0 = time.time()
    out = Path(out_dir)
    (out / "records").mkdir(parents=True, exist_ok=True)
    tasks = [
        _cfg_dict(SmallDivisorAuditConfig(
            npz_path=str(Path(p)),
            out_dir=str(out),
            nu_grid=tuple(float(x) for x in nu_grid),
            tail_start_fracs=tuple(float(x) for x in tail_start_fracs),
            omega_override=omega_override,
            force=bool(force),
        ))
        for p in npz_paths
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
                print(f"[phase3] K={row.get('K')} M={row.get('M')} invmax={row.get('finite_max_inverse')} corr={row.get('rep_cohomology_correction_l1_nu')} label={row.get('recommendation_label')}", flush=True)
    rows.sort(key=lambda r: (float(r.get("K") or 0.0), int(r.get("M") or 0)))

    def rank_key(r: dict[str, Any]) -> tuple[float, float, float, float]:
        label_bonus = {"strong_phase3_candidate": 0.0, "moderate_phase3_candidate": 1.0}.get(str(r.get("recommendation_label")), 2.0)
        return (
            label_bonus,
            -float(r.get("M") or 0),
            float(r.get("rep_cohomology_correction_l1_nu") or 1e300),
            float(r.get("residual_linf") or 1e300),
        )
    ranked = sorted(rows, key=rank_key)
    summary: dict[str, Any] = {
        "schema": "theorem_iii_trackb_phase3_small_divisor_audit_summary_v1",
        "phase": "TrackB-Phase3-small-divisor-cohomology-audit",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "status": "phase3-small-divisor-audit-complete" if rows else "no-npz-inputs",
        "parameters": {
            "npz_count": len(npz_paths),
            "workers_requested": int(workers),
            "workers_used": int(nw),
            "nu_grid": [float(x) for x in nu_grid],
            "tail_start_fracs": [float(x) for x in tail_start_fracs],
            "omega_override": omega_override,
        },
        "counts": {
            "tasks": len(tasks),
            "completed_records": len(rows),
            "strong": sum(r.get("recommendation_label") == "strong_phase3_candidate" for r in rows),
            "moderate": sum(r.get("recommendation_label") == "moderate_phase3_candidate" for r in rows),
            "weak": sum(r.get("recommendation_label") == "weak_or_needs_seed_improvement" for r in rows),
        },
        "ranked_candidates": ranked,
        "best_12_candidates": ranked[:12],
        "records": rows,
        "elapsed_seconds": float(time.time() - t0),
    }
    write_json(out / "phase3_small_divisor_summary.json", summary)
    write_json(out / "phase3_ranked_candidates.json", {"schema": "theorem_iii_trackb_phase3_ranked_candidates_v1", "candidates": ranked})
    csv_path = out / "phase3_small_divisor_results.csv"
    fields = [
        "K", "M", "residual_linf", "zero_mode_residual_abs", "max_mode",
        "small_divisor_min_denominator", "small_divisor_min_mode", "finite_max_inverse",
        "finite_max_inverse_mode", "rep_nu", "rep_u_l1_nu", "rep_residual_l1_nu",
        "rep_cohomology_correction_l1_nu", "rep_correction_to_u_ratio",
        "rep_correction_tail_075_weighted_ratio", "recommendation_label", "recommendation_score",
        "npz_path", "record_path",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})
    summary["csv"] = str(csv_path)
    return summary
