from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import itertools
import math
import time

import numpy as np
from scipy.sparse.linalg import LinearOperator, lsmr

from .phase4i_common import (
    ensure_dir,
    highpass_values,
    interp_adjoint_values,
    interp_values,
    linearized_residual_adjoint_on_grid,
    linearized_residual_apply_on_grid,
    load_seed,
    lowpass_values,
    l1_nu,
    derivative_l1_nu,
    scalar_residual_on_grid_from_core,
    sanitize_float_tag,
    save_seed_npz,
    spectral_derivative,
    write_json,
    csv_write,
)


@dataclass
class H1PolishJob:
    npz_path: str
    M_out: int
    oversample: int
    cutoff_mode: Optional[int]
    lambda_h1: float
    eta_high: float
    out_dir: str
    omega_override: Optional[float] = None
    max_newton: int = 8
    lsmr_atol: float = 1e-12
    lsmr_btol: float = 1e-12
    lsmr_maxiter: int = 900
    lsmr_conlim: float = 1e12
    damping_min: float = 1e-7
    accept_scalar_linf: float = 1e-8
    accept_derivative_linf: float = 5e-5
    nu: float = 1.003
    force: bool = False


def _tag(job: H1PolishJob) -> str:
    cutoff = "full" if job.cutoff_mode is None else f"cut{job.cutoff_mode}"
    lam = str(job.lambda_h1).replace('.', 'p').replace('-', 'm')
    eta = f"{job.eta_high:.0e}".replace('-', 'm').replace('+', '').replace('.', 'p')
    src = Path(job.npz_path).stem
    return f"{src}_M{job.M_out}_os{job.oversample}_{cutoff}_h1{lam}_eta{eta}"


def _record_path(job: H1PolishJob) -> Path:
    return Path(job.out_dir) / "records" / (_tag(job) + ".phase4i_h1_polish.json")


def _output_npz_path(job: H1PolishJob) -> Path:
    return Path(job.out_dir) / "embeddings" / (_tag(job) + ".npz")


def _residual_metrics(u: np.ndarray, K: float, omega: float, oversample: int, nu: float) -> Dict[str, float]:
    M = len(u)
    L = int(M * oversample)
    Rn = scalar_residual_on_grid_from_core(u, K, omega, M)
    Ro = scalar_residual_on_grid_from_core(u, K, omega, L)
    dRo = spectral_derivative(Ro)
    return {
        "native_scalar_residual_linf": float(np.max(np.abs(Rn))),
        "oversampled_scalar_residual_linf": float(np.max(np.abs(Ro))),
        "oversampled_derivative_residual_linf": float(np.max(np.abs(dRo))),
        "weighted_native_residual_l1_nu": float(l1_nu(Rn, nu)),
        "weighted_oversampled_residual_l1_nu": float(l1_nu(Ro, nu)),
        "weighted_oversampled_derivative_residual_l1_nu": float(derivative_l1_nu(Ro, nu)),
    }


def _make_operator(
    u: np.ndarray,
    K: float,
    omega: float,
    L: int,
    lambda_h1: float,
    eta_high: float,
    cutoff_mode: Optional[int],
) -> Tuple[LinearOperator, np.ndarray, Dict[str, int]]:
    M = len(u)
    uL = interp_values(u, L)
    R = scalar_residual_on_grid_from_core(u, K, omega, L)
    DR = spectral_derivative(R)
    HP = highpass_values(u, cutoff_mode) if eta_high > 0 and cutoff_mode is not None else np.zeros(M)
    # Last row is a homogeneous gauge row pinning delta[0] = 0.
    blocks = {
        "residual_start": 0,
        "h1_start": L,
        "high_start": 2 * L,
        "gauge_start": 2 * L + (M if eta_high > 0 and cutoff_mode is not None else 0),
    }
    high_len = M if eta_high > 0 and cutoff_mode is not None else 0
    nrows = 2 * L + high_len + 1
    F = np.zeros(nrows, dtype=float)
    F[0:L] = R
    F[L:2 * L] = float(lambda_h1) * DR
    if high_len:
        F[2 * L:2 * L + M] = float(eta_high) * HP
    F[-1] = 0.0

    def matvec(delta: np.ndarray) -> np.ndarray:
        delta = np.asarray(delta, dtype=float)
        dL = interp_values(delta, L)
        JR = linearized_residual_apply_on_grid(dL, uL, K, omega)
        out = np.zeros(nrows, dtype=float)
        out[0:L] = JR
        out[L:2 * L] = float(lambda_h1) * spectral_derivative(JR)
        if high_len:
            out[2 * L:2 * L + M] = float(eta_high) * highpass_values(delta, cutoff_mode)
        out[-1] = delta[0]
        return out

    def rmatvec(y: np.ndarray) -> np.ndarray:
        y = np.asarray(y, dtype=float)
        y0 = y[0:L]
        y1 = y[L:2 * L]
        zL = y0 - float(lambda_h1) * spectral_derivative(y1)
        adjL = linearized_residual_adjoint_on_grid(zL, uL, K, omega)
        out = interp_adjoint_values(adjL, M)
        if high_len:
            yh = y[2 * L:2 * L + M]
            out += float(eta_high) * highpass_values(yh, cutoff_mode)
        out[0] += y[-1]
        return out

    A = LinearOperator((nrows, M), matvec=matvec, rmatvec=rmatvec, dtype=float)
    return A, F, blocks


def _merit(u: np.ndarray, K: float, omega: float, oversample: int, lambda_h1: float) -> float:
    L = len(u) * oversample
    R = scalar_residual_on_grid_from_core(u, K, omega, L)
    dR = spectral_derivative(R)
    return float(np.linalg.norm(R) + abs(lambda_h1) * np.linalg.norm(dR))


def _resample_seed_to_M(u: np.ndarray, M_out: int) -> np.ndarray:
    if len(u) == M_out:
        return u.copy()
    return interp_values(u, M_out)


def run_one_h1_polish(job: H1PolishJob) -> Dict[str, Any]:
    rec_path = _record_path(job)
    out_npz = _output_npz_path(job)
    if rec_path.exists() and out_npz.exists() and not job.force:
        import json
        with open(rec_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    seed = load_seed(job.npz_path, omega_override=job.omega_override)
    u = _resample_seed_to_M(seed.u, int(job.M_out))
    if job.cutoff_mode is not None:
        u = lowpass_values(u, job.cutoff_mode)
    K = seed.K
    omega = seed.omega
    M = len(u)
    L = int(M * job.oversample)
    start = time.time()
    before = _residual_metrics(u, K, omega, job.oversample, job.nu)
    history: List[Dict[str, Any]] = []
    solve_status = "not-started"

    for it in range(int(job.max_newton)):
        A, F, _ = _make_operator(u, K, omega, L, job.lambda_h1, job.eta_high, job.cutoff_mode)
        base_merit = _merit(u, K, omega, job.oversample, job.lambda_h1)
        try:
            sol = lsmr(
                A,
                -F,
                atol=job.lsmr_atol,
                btol=job.lsmr_btol,
                maxiter=job.lsmr_maxiter,
                conlim=job.lsmr_conlim,
            )
            delta = np.asarray(sol[0], dtype=float)
            lsmr_istop = int(sol[1])
            lsmr_itn = int(sol[2])
            lsmr_normr = float(sol[3])
        except Exception as exc:
            solve_status = f"lsmr-error:{type(exc).__name__}"
            history.append({"iteration": it, "status": solve_status, "error": str(exc)})
            break

        accepted = False
        alpha = 1.0
        best_u = u.copy()
        best_merit = base_merit
        while alpha >= float(job.damping_min):
            cand = u + alpha * delta
            if job.cutoff_mode is not None:
                cand = lowpass_values(cand, job.cutoff_mode)
            mer = _merit(cand, K, omega, job.oversample, job.lambda_h1)
            if math.isfinite(mer) and mer < best_merit:
                best_merit = mer
                best_u = cand
                accepted = True
                break
            alpha *= 0.5
        u = best_u
        met = _residual_metrics(u, K, omega, job.oversample, job.nu)
        history.append({
            "iteration": it,
            "accepted": bool(accepted),
            "alpha": float(alpha),
            "base_merit": float(base_merit),
            "new_merit": float(best_merit),
            "lsmr_istop": lsmr_istop,
            "lsmr_itn": lsmr_itn,
            "lsmr_normr": lsmr_normr,
            **met,
        })
        if (
            met["oversampled_scalar_residual_linf"] <= job.accept_scalar_linf
            and met["oversampled_derivative_residual_linf"] <= job.accept_derivative_linf
        ):
            solve_status = "accepted-h1-thresholds"
            break
        if not accepted:
            solve_status = "line-search-stalled"
            break
    else:
        solve_status = "max-newton-reached"

    after = _residual_metrics(u, K, omega, job.oversample, job.nu)
    converged_h1 = bool(
        after["oversampled_scalar_residual_linf"] <= job.accept_scalar_linf
        and after["oversampled_derivative_residual_linf"] <= job.accept_derivative_linf
    )
    if converged_h1:
        solve_status = "converged-h1"
    md = {
        "phase": "4i_h1_polish",
        "diagnostic_only": True,
        "source_seed": job.npz_path,
        "M_out": job.M_out,
        "oversample": job.oversample,
        "cutoff_mode": job.cutoff_mode,
        "lambda_h1": job.lambda_h1,
        "eta_high": job.eta_high,
        "solve_status": solve_status,
    }
    save_seed_npz(out_npz, u, K, omega, job.npz_path, md)
    elapsed = time.time() - start
    record = {
        "schema": "theorem_iii_trackb_phase4i_h1_polish_record_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "npz_path": job.npz_path,
        "output_npz": str(out_npz),
        "K": float(K),
        "M_in": int(seed.M),
        "M_out": int(M),
        "oversample": int(job.oversample),
        "cutoff_mode": None if job.cutoff_mode is None else int(job.cutoff_mode),
        "lambda_h1": float(job.lambda_h1),
        "eta_high": float(job.eta_high),
        "solve_status": solve_status,
        "converged_h1": converged_h1,
        "elapsed_seconds": float(elapsed),
        "before": before,
        "after": after,
        "history": history,
    }
    write_json(rec_path, record)
    return record


def compact_row(record: Dict[str, Any], out_dir: str) -> Dict[str, Any]:
    after = record.get("after", {})
    before = record.get("before", {})
    return {
        "K": record.get("K"),
        "M_in": record.get("M_in"),
        "M_out": record.get("M_out"),
        "oversample": record.get("oversample"),
        "cutoff_mode": record.get("cutoff_mode"),
        "lambda_h1": record.get("lambda_h1"),
        "eta_high": record.get("eta_high"),
        "solve_status": record.get("solve_status"),
        "converged_h1": record.get("converged_h1"),
        "before_scalar_linf": before.get("oversampled_scalar_residual_linf"),
        "after_scalar_linf": after.get("oversampled_scalar_residual_linf"),
        "before_derivative_linf": before.get("oversampled_derivative_residual_linf"),
        "after_derivative_linf": after.get("oversampled_derivative_residual_linf"),
        "after_native_scalar_linf": after.get("native_scalar_residual_linf"),
        "weighted_after_residual_l1_nu": after.get("weighted_oversampled_residual_l1_nu"),
        "weighted_after_derivative_l1_nu": after.get("weighted_oversampled_derivative_residual_l1_nu"),
        "output_npz": record.get("output_npz"),
        "record_path": str(_record_path(H1PolishJob(npz_path=record.get("npz_path"), M_out=record.get("M_out"), oversample=record.get("oversample"), cutoff_mode=record.get("cutoff_mode"), lambda_h1=record.get("lambda_h1"), eta_high=record.get("eta_high"), out_dir=out_dir))),
    }


def parse_cutoffs(cutoff_specs: Sequence[str], M: Optional[int] = None) -> List[Optional[int]]:
    out: List[Optional[int]] = []
    for spec in cutoff_specs:
        s = str(spec).strip().lower()
        if not s:
            continue
        if s == "full" or s == "none":
            out.append(None)
        elif s.startswith("frac:"):
            if M is None:
                raise ValueError("frac cutoffs require M")
            frac = float(s.split(":", 1)[1])
            out.append(int(math.floor(frac * (M // 2))))
        else:
            out.append(int(float(s)))
    # de-duplicate preserving order
    seen = set()
    final = []
    for x in out:
        key = -1 if x is None else int(x)
        if key not in seen:
            final.append(x)
            seen.add(key)
    return final


def run_phase4i_h1_polish(
    npz_paths: Sequence[str],
    M_outs: Sequence[int],
    oversamples: Sequence[int],
    cutoff_specs: Sequence[str],
    lambda_h1_values: Sequence[float],
    eta_high_values: Sequence[float],
    out_dir: str,
    workers: int = 1,
    omega_override: Optional[float] = None,
    max_newton: int = 8,
    lsmr_atol: float = 1e-12,
    lsmr_btol: float = 1e-12,
    lsmr_maxiter: int = 900,
    lsmr_conlim: float = 1e12,
    damping_min: float = 1e-7,
    accept_scalar_linf: float = 1e-8,
    accept_derivative_linf: float = 5e-5,
    nu: float = 1.003,
    force: bool = False,
) -> Dict[str, Any]:
    ensure_dir(Path(out_dir) / "records")
    ensure_dir(Path(out_dir) / "embeddings")
    jobs: List[H1PolishJob] = []
    for p in npz_paths:
        # For frac cutoffs, use each requested M_out.
        for M_out, osamp in itertools.product(M_outs, oversamples):
            cutoffs = parse_cutoffs(cutoff_specs, M=int(M_out))
            for cutoff, lam, eta in itertools.product(cutoffs, lambda_h1_values, eta_high_values):
                jobs.append(H1PolishJob(
                    npz_path=str(p), M_out=int(M_out), oversample=int(osamp), cutoff_mode=cutoff,
                    lambda_h1=float(lam), eta_high=float(eta), out_dir=out_dir,
                    omega_override=omega_override, max_newton=max_newton, lsmr_atol=lsmr_atol,
                    lsmr_btol=lsmr_btol, lsmr_maxiter=lsmr_maxiter, lsmr_conlim=lsmr_conlim,
                    damping_min=damping_min, accept_scalar_linf=accept_scalar_linf,
                    accept_derivative_linf=accept_derivative_linf, nu=nu, force=force,
                ))
    if workers and workers > 1 and len(jobs) > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=min(int(workers), len(jobs))) as ex:
            records = list(ex.map(run_one_h1_polish, jobs))
    else:
        records = [run_one_h1_polish(j) for j in jobs]
    rows = [compact_row(r, out_dir) for r in records]
    rows.sort(key=lambda r: (
        r.get("after_derivative_linf") if r.get("after_derivative_linf") is not None else math.inf,
        r.get("after_scalar_linf") if r.get("after_scalar_linf") is not None else math.inf,
    ))
    summary = {
        "schema": "theorem_iii_trackb_phase4i_h1_polish_summary_v1",
        "status": "phase4i-h1-polish-complete",
        "diagnostic_only": True,
        "counts": {
            "tasks": len(jobs),
            "completed_records": len(records),
            "converged_h1": int(sum(1 for r in records if r.get("converged_h1"))),
            "not_converged_h1": int(sum(1 for r in records if not r.get("converged_h1"))),
        },
        "parameters": {
            "M_outs": list(map(int, M_outs)),
            "oversamples": list(map(int, oversamples)),
            "cutoff_specs": list(cutoff_specs),
            "lambda_h1_values": list(map(float, lambda_h1_values)),
            "eta_high_values": list(map(float, eta_high_values)),
            "workers_requested": int(workers),
            "workers_used": min(int(workers), len(jobs)) if workers else 1,
            "max_newton": int(max_newton),
            "lsmr_maxiter": int(lsmr_maxiter),
            "accept_scalar_linf": float(accept_scalar_linf),
            "accept_derivative_linf": float(accept_derivative_linf),
        },
        "top_candidates": rows,
    }
    write_json(Path(out_dir) / "phase4i_h1_polish_summary.json", summary)
    csv_write(Path(out_dir) / "phase4i_h1_polish_results.csv", rows)
    return summary
