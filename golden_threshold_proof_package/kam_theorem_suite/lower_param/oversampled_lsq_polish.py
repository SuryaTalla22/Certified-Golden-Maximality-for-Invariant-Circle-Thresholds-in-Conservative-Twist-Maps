from __future__ import annotations

import csv
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from scipy.sparse.linalg import LinearOperator, lsmr

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


def freq_grid(M: int) -> np.ndarray:
    return np.fft.fftfreq(int(M), d=1.0 / float(M))


def coeff(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    return np.fft.fft(values) / float(values.size)


def samples_from_coeff(c: np.ndarray) -> np.ndarray:
    c = np.asarray(c, dtype=complex)
    return np.fft.ifft(c * float(c.size)).real


def coeff_to_size(c_src: np.ndarray, M_dst: int, *, cutoff_mode: int | None = None) -> np.ndarray:
    c_src = np.asarray(c_src, dtype=complex)
    M_src = int(c_src.size)
    M_dst = int(M_dst)
    out = np.zeros(M_dst, dtype=complex)
    max_dst = M_dst // 2
    for idx, k_float in enumerate(freq_grid(M_src)):
        k = int(k_float)
        if k == -M_src // 2 and M_src % 2 == 0 and M_dst != M_src:
            # Ambiguous Nyquist mode when changing size.
            continue
        if cutoff_mode is not None and abs(k) > int(cutoff_mode):
            continue
        if abs(k) > max_dst:
            continue
        out[k % M_dst] = c_src[idx]
    return out


def resample_periodic(values: np.ndarray, M_dst: int, *, cutoff_mode: int | None = None) -> np.ndarray:
    return samples_from_coeff(coeff_to_size(coeff(values), int(M_dst), cutoff_mode=cutoff_mode))


def parse_float_from_npz_value(v: Any, default: float | None = None) -> float | None:
    try:
        x = float(np.asarray(v).reshape(()))
        return x if math.isfinite(x) else default
    except Exception:
        return default


def load_seed_npz(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    z = np.load(path, allow_pickle=True)
    if "u" not in z:
        raise ValueError(f"{path} does not contain array 'u'")
    u = np.asarray(z["u"], dtype=float)
    K = parse_float_from_npz_value(z.get("K"), None)
    omega = parse_float_from_npz_value(z.get("omega"), GOLDEN_OMEGA)
    if K is None:
        name = path.name
        if name.startswith("K"):
            K = float(name.split("_", 1)[0][1:].replace("p", "."))
        else:
            raise ValueError(f"Could not read K from {path}")
    return {"path": str(path), "u": u, "K": float(K), "omega": float(omega or GOLDEN_OMEGA)}


class OversampledLeastSquaresResidual:
    """Oversampled least-squares residual for band-limited scalar invariance.

    Unknown: M real samples of the periodic correction u.
    Equation: evaluate residual on L=oversample*M points without projecting the
    nonlinear residual back to M modes.  Newton corrections are computed by LSMR
    on the overdetermined linearized system, with one small gauge row preserving
    the phase of the input seed.

    This is diagnostic only.  It is intended to polish a seed so that the
    derivative-level/automatic-reducibility diagnostics are not dominated by
    residual aliasing.
    """

    def __init__(
        self,
        M: int,
        K: float,
        omega: float = GOLDEN_OMEGA,
        oversample: int = 2,
        cutoff_mode: int | None = None,
        gauge_index: int = 0,
        gauge_weight: float = 1.0,
        gauge_value: float = 0.0,
    ):
        self.M = int(M)
        self.K = float(K)
        self.omega = float(omega)
        self.oversample = int(max(1, oversample))
        self.L = int(self.M * self.oversample)
        self.cutoff_mode = cutoff_mode
        self.gauge_index = int(gauge_index) % self.M
        self.gauge_weight = float(gauge_weight)
        self.gauge_value = float(gauge_value)
        self.theta_core = np.arange(self.M, dtype=float) / float(self.M)
        self.theta = np.arange(self.L, dtype=float) / float(self.L)
        self.freq_core = freq_grid(self.M)
        self.freq = freq_grid(self.L)
        self.shift_plus = np.exp(1j * TWO_PI * self.freq * self.omega)
        self.shift_minus = np.conjugate(self.shift_plus)

    def lift_to_L(self, u_core: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        c_core = coeff(np.asarray(u_core, dtype=float))
        c_L = coeff_to_size(c_core, self.L, cutoff_mode=self.cutoff_mode)
        return samples_from_coeff(c_L), c_L

    def project_L_to_core_samples(self, values_L: np.ndarray) -> np.ndarray:
        c_L = coeff(np.asarray(values_L, dtype=float))
        c_core = coeff_to_size(c_L, self.M)
        return samples_from_coeff(c_core)

    def shift_L_coeff(self, c_L: np.ndarray, sign: int) -> np.ndarray:
        mult = self.shift_plus if sign >= 0 else self.shift_minus
        return samples_from_coeff(np.asarray(c_L, dtype=complex) * mult)

    def residual_L_only(self, u_core: np.ndarray) -> np.ndarray:
        u_L, c_L = self.lift_to_L(u_core)
        up = self.shift_L_coeff(c_L, +1)
        um = self.shift_L_coeff(c_L, -1)
        x = self.theta + u_L
        return up - 2.0 * u_L + um - (self.K / TWO_PI) * np.sin(TWO_PI * x)

    def residual_augmented(self, u_core: np.ndarray) -> np.ndarray:
        r = self.residual_L_only(u_core)
        if self.gauge_weight > 0:
            g = self.gauge_weight * (float(u_core[self.gauge_index]) - self.gauge_value)
            return np.concatenate([r, np.array([g], dtype=float)])
        return r

    def residual_core(self, u_core: np.ndarray) -> np.ndarray:
        M = self.M
        theta = self.theta_core
        f = self.freq_core
        c = coeff(np.asarray(u_core, dtype=float))
        up = samples_from_coeff(c * np.exp(1j * TWO_PI * f * self.omega))
        um = samples_from_coeff(c * np.exp(-1j * TWO_PI * f * self.omega))
        return up - 2.0 * u_core + um - (self.K / TWO_PI) * np.sin(TWO_PI * (theta + u_core))

    def residual_projected(self, u_core: np.ndarray) -> np.ndarray:
        return self.project_L_to_core_samples(self.residual_L_only(u_core))

    def _apply_A_L(self, y_L: np.ndarray, diag_L: np.ndarray, sign_adjoint: bool = False) -> np.ndarray:
        c = coeff(np.asarray(y_L, dtype=float))
        if not sign_adjoint:
            sp = self.shift_plus
            sm = self.shift_minus
        else:
            # Adjoint of shift +omega is shift -omega, and vice versa.
            sp = self.shift_minus
            sm = self.shift_plus
        return samples_from_coeff(c * sp) + samples_from_coeff(c * sm) + diag_L * y_L

    def linop_augmented(self, u_core: np.ndarray) -> LinearOperator:
        u_L, _ = self.lift_to_L(u_core)
        diag = -2.0 - self.K * np.cos(TWO_PI * (self.theta + u_L))
        M = self.M
        L = self.L
        gw = self.gauge_weight
        gi = self.gauge_index

        def matvec(delta_core: np.ndarray) -> np.ndarray:
            delta_core = np.asarray(delta_core, dtype=float)
            d_L, _ = self.lift_to_L(delta_core)
            y_L = self._apply_A_L(d_L, diag, sign_adjoint=False)
            if gw > 0:
                return np.concatenate([y_L, np.array([gw * float(delta_core[gi])], dtype=float)])
            return y_L

        def rmatvec(y_aug: np.ndarray) -> np.ndarray:
            y_aug = np.asarray(y_aug, dtype=float)
            y_L = y_aug[:L]
            # Approximate Euclidean adjoint: apply formal L-grid adjoint, then
            # project back to the M core band.  The L/M scaling compensates for
            # different unnormalized sample inner products.
            z_L = self._apply_A_L(y_L, diag, sign_adjoint=True)
            z_core = self.project_L_to_core_samples(z_L) * (float(L) / float(M))
            if gw > 0 and y_aug.size > L:
                z_core = z_core.copy()
                z_core[gi] += gw * float(y_aug[L])
            return z_core

        return LinearOperator((L + (1 if gw > 0 else 0), M), matvec=matvec, rmatvec=rmatvec, dtype=float)


def linf(v: np.ndarray) -> float:
    return float(np.max(np.abs(np.asarray(v, dtype=float))))


def weighted_l1(values: np.ndarray, nu: float) -> float:
    values = np.asarray(values, dtype=float)
    f = np.abs(freq_grid(values.size))
    return float(np.sum(np.abs(coeff(values)) * np.exp(math.log(float(nu)) * f)))


@dataclass(slots=True)
class LSQPolishConfig:
    input_npz: str
    M_out: int
    oversample: int = 2
    cutoff_mode: int | None = None
    max_newton: int = 8
    accept_oversampled_linf: float = 1e-10
    accept_projected_linf: float = 1e-10
    accept_core_linf: float = 1e-8
    lsmr_atol: float = 1e-12
    lsmr_btol: float = 1e-12
    lsmr_maxiter: int = 1000
    lsmr_conlim: float = 1e12
    damping_min: float = 1e-7
    gauge_index: int = 0
    gauge_weight: float = 1.0
    omega_override: float | None = None
    nu: float = 1.003


@dataclass(slots=True)
class LSQStep:
    iteration: int
    oversampled_linf: float
    projected_linf: float
    core_linf: float
    lsmr_istop: int | None
    lsmr_itn: int | None
    lsmr_normr: float | None
    correction_linf: float | None
    damping: float | None
    accepted: bool


@dataclass(slots=True)
class LSQPolishResult:
    config: LSQPolishConfig
    K: float
    omega: float
    M_in: int
    M_out: int
    converged_oversampled: bool
    solve_status: str
    oversampled_residual_linf: float
    projected_residual_linf: float
    core_residual_linf: float
    weighted_projected_residual_l1_nu: float
    weighted_core_residual_l1_nu: float
    weighted_u_l1_nu: float
    elapsed_seconds: float
    step_records: list[LSQStep] = field(default_factory=list)
    output_npz: str | None = None
    record_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(schema="theorem_iii_trackb_phase4f_lsq_polish_v1", diagnostic_only=True, theorem_facing=False, promotion_allowed=False)
        return d


def k_tag(K: float) -> str:
    return f"K{float(K):.10f}".replace(".", "p")


def infer_parent_M(path: str | Path, default: int) -> int:
    name = Path(path).name
    marker = "_fromM"
    if marker in name:
        try:
            return int(name.split(marker, 1)[1].split(".", 1)[0].split("_", 1)[0])
        except Exception:
            pass
    return int(default)


def polish_one(cfg: LSQPolishConfig, out_dir: str | Path) -> LSQPolishResult:
    t0 = time.time()
    seed = load_seed_npz(cfg.input_npz)
    u0 = np.asarray(seed["u"], dtype=float)
    K = float(seed["K"])
    omega = float(cfg.omega_override if cfg.omega_override is not None else seed["omega"])
    M_in = int(u0.size)
    M_out = int(cfg.M_out)
    u = resample_periodic(u0, M_out, cutoff_mode=cfg.cutoff_mode)
    gauge_value = float(u[int(cfg.gauge_index) % M_out])
    op = OversampledLeastSquaresResidual(
        M_out,
        K,
        omega=omega,
        oversample=cfg.oversample,
        cutoff_mode=cfg.cutoff_mode,
        gauge_index=cfg.gauge_index,
        gauge_weight=cfg.gauge_weight,
        gauge_value=gauge_value,
    )
    steps: list[LSQStep] = []
    status = "not-started"
    best = math.inf
    for it in range(int(cfg.max_newton)):
        rL = op.residual_L_only(u)
        rproj = op.residual_projected(u)
        rcore = op.residual_core(u)
        o_linf = linf(rL)
        p_linf = linf(rproj)
        c_linf = linf(rcore)
        if o_linf <= cfg.accept_oversampled_linf and p_linf <= cfg.accept_projected_linf and c_linf <= cfg.accept_core_linf:
            steps.append(LSQStep(it, o_linf, p_linf, c_linf, None, None, None, 0.0, 0.0, True))
            status = "converged-oversampled"
            break
        A = op.linop_augmented(u)
        b = -op.residual_augmented(u)
        sol = lsmr(A, b, atol=cfg.lsmr_atol, btol=cfg.lsmr_btol, conlim=cfg.lsmr_conlim, maxiter=cfg.lsmr_maxiter)
        delta = np.asarray(sol[0], dtype=float)
        istop = int(sol[1])
        itn = int(sol[2])
        normr = float(sol[3])
        d_linf = linf(delta)
        alpha = 1.0
        accepted = False
        chosen = None
        # Primary line-search objective is oversampled residual; projected/core are recorded.
        while alpha >= cfg.damping_min:
            trial = u + alpha * delta
            trL = op.residual_L_only(trial)
            score = linf(trL)
            if score < o_linf or score < best:
                u = trial
                best = score
                accepted = True
                chosen = alpha
                break
            alpha *= 0.5
        steps.append(LSQStep(it, o_linf, p_linf, c_linf, istop, itn, normr, d_linf, chosen, accepted))
        if not accepted:
            status = "line-search-failed"
            break
        if d_linf * float(chosen or 0.0) <= 1e-14:
            status = "stalled-small-step"
            break
    else:
        status = "max-newton-reached"

    rL = op.residual_L_only(u)
    rproj = op.residual_projected(u)
    rcore = op.residual_core(u)
    o_linf = linf(rL)
    p_linf = linf(rproj)
    c_linf = linf(rcore)
    conv = bool(o_linf <= cfg.accept_oversampled_linf and p_linf <= cfg.accept_projected_linf and c_linf <= cfg.accept_core_linf)
    if conv:
        status = "converged-oversampled"

    out_dir = Path(out_dir)
    emb_dir = out_dir / "embeddings"
    rec_dir = out_dir / "records"
    emb_dir.mkdir(parents=True, exist_ok=True)
    rec_dir.mkdir(parents=True, exist_ok=True)
    parent_M = infer_parent_M(cfg.input_npz, M_in)
    cut = "full" if cfg.cutoff_mode is None else f"cut{int(cfg.cutoff_mode)}"
    stem = f"{k_tag(K)}_M{M_out}_lsqdealias{int(cfg.oversample)}_{cut}_fromM{parent_M}"
    npz_path = emb_dir / f"{stem}.npz"
    theta = np.arange(M_out, dtype=float) / float(M_out)
    c = coeff(u)
    f = freq_grid(M_out)
    um = samples_from_coeff(c * np.exp(-1j * TWO_PI * f * omega))
    x = theta + u
    r = omega + u - um
    np.savez_compressed(
        npz_path,
        schema="theorem_iii_trackb_phase4f_lsq_polished_embedding_npz_v1",
        diagnostic_only=True,
        theorem_facing=False,
        K=float(K),
        M=int(M_out),
        omega=float(omega),
        theta=theta,
        u=u,
        x=x,
        r=r,
        residual=rcore,
        oversampled_residual_linf=float(o_linf),
        projected_residual_linf=float(p_linf),
        core_residual_linf=float(c_linf),
        u_coeff=coeff(u),
        residual_coeff=coeff(rcore),
        freq=f,
    )

    result = LSQPolishResult(
        config=cfg,
        K=K,
        omega=omega,
        M_in=M_in,
        M_out=M_out,
        converged_oversampled=conv,
        solve_status=status,
        oversampled_residual_linf=float(o_linf),
        projected_residual_linf=float(p_linf),
        core_residual_linf=float(c_linf),
        weighted_projected_residual_l1_nu=weighted_l1(rproj, cfg.nu),
        weighted_core_residual_l1_nu=weighted_l1(rcore, cfg.nu),
        weighted_u_l1_nu=weighted_l1(u, cfg.nu),
        elapsed_seconds=float(time.time() - t0),
        step_records=steps,
        output_npz=str(npz_path),
    )
    rec_path = rec_dir / f"{stem}.phase4f_lsq_polish.json"
    result.record_path = str(rec_path)
    write_json(rec_path, result.to_dict())
    return result


def run_many(configs: Sequence[LSQPolishConfig], out_dir: str | Path, workers: int = 1) -> list[LSQPolishResult]:
    workers = max(1, min(int(workers), len(configs) or 1))
    if workers == 1:
        return [polish_one(c, out_dir) for c in configs]
    results: list[LSQPolishResult] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(polish_one, c, out_dir) for c in configs]
        for fut in as_completed(futs):
            results.append(fut.result())
    results.sort(key=lambda r: (r.K, r.M_out, r.config.oversample, str(r.config.cutoff_mode)))
    return results


def write_outputs(results: Sequence[LSQPolishResult], out_dir: str | Path, parameters: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in results:
        rows.append({
            "K": r.K,
            "M_in": r.M_in,
            "M_out": r.M_out,
            "oversample": r.config.oversample,
            "cutoff_mode": r.config.cutoff_mode,
            "converged_oversampled": r.converged_oversampled,
            "solve_status": r.solve_status,
            "oversampled_residual_linf": r.oversampled_residual_linf,
            "projected_residual_linf": r.projected_residual_linf,
            "core_residual_linf": r.core_residual_linf,
            "weighted_projected_residual_l1_nu": r.weighted_projected_residual_l1_nu,
            "weighted_core_residual_l1_nu": r.weighted_core_residual_l1_nu,
            "weighted_u_l1_nu": r.weighted_u_l1_nu,
            "elapsed_seconds": r.elapsed_seconds,
            "output_npz": r.output_npz,
            "record_path": r.record_path,
        })
    csv_path = out_dir / "phase4f_lsq_polish_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    ranked = sorted(rows, key=lambda x: (float(x["oversampled_residual_linf"]), float(x["core_residual_linf"])))
    summary = {
        "schema": "theorem_iii_trackb_phase4f_lsq_polish_summary_v1",
        "status": "phase4f-lsq-polish-complete",
        "diagnostic_only": True,
        "parameters": parameters,
        "counts": {
            "tasks": len(results),
            "completed_records": len(results),
            "converged_oversampled": sum(1 for r in results if r.converged_oversampled),
            "not_converged_oversampled": sum(1 for r in results if not r.converged_oversampled),
        },
        "top_candidates": ranked[:50],
        "results_csv": str(csv_path),
    }
    write_json(out_dir / "phase4f_lsq_polish_summary.json", summary)
    write_json(out_dir / "phase4f_ranked_candidates.json", {"top_candidates": ranked})
    return summary
