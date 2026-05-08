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
from scipy.sparse.linalg import LinearOperator, gmres

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
        # Fallback: parse from file name K0p9716350000...
        name = path.name
        if name.startswith("K"):
            K = float(name.split("_", 1)[0][1:].replace("p", "."))
        else:
            raise ValueError(f"Could not read K from {path}")
    return {"path": str(path), "u": u, "K": float(K), "omega": float(omega or GOLDEN_OMEGA)}


class DealiasedProjectedResidual:
    """Projected invariance residual with oversampled nonlinear evaluation.

    Variable: real samples of a band-limited periodic correction u on M core nodes.
    Residual: evaluate the nonlinear standard-sine invariance equation on L = oversample*M
    nodes, project the residual back to the M core Fourier modes, then return M core samples.

    This is not a proof object.  It is a diagnostic seed-polishing tool designed to reduce
    aliasing-driven tangent/automatic-reducibility defects before intervalization.
    """

    def __init__(self, M: int, K: float, omega: float = GOLDEN_OMEGA, oversample: int = 4, pin: int = 0, cutoff_mode: int | None = None):
        self.M = int(M)
        self.K = float(K)
        self.omega = float(omega)
        self.oversample = int(max(1, oversample))
        self.L = int(self.M * self.oversample)
        self.pin = int(pin) % self.M
        self.cutoff_mode = cutoff_mode
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

    def project_L_to_core(self, values_L: np.ndarray) -> np.ndarray:
        c_L = coeff(np.asarray(values_L, dtype=float))
        c_core = coeff_to_size(c_L, self.M)
        return samples_from_coeff(c_core)

    def shift_L_coeff(self, c_L: np.ndarray, sign: int) -> np.ndarray:
        mult = self.shift_plus if sign >= 0 else self.shift_minus
        return samples_from_coeff(np.asarray(c_L, dtype=complex) * mult)

    def residual_L(self, u_core: np.ndarray) -> np.ndarray:
        u_L, c_L = self.lift_to_L(u_core)
        up = self.shift_L_coeff(c_L, +1)
        um = self.shift_L_coeff(c_L, -1)
        x = self.theta + u_L
        return up - 2.0 * u_L + um - (self.K / TWO_PI) * np.sin(TWO_PI * x)

    def residual_projected(self, u_core: np.ndarray, *, pin: bool = True) -> np.ndarray:
        r = self.project_L_to_core(self.residual_L(u_core))
        if pin:
            r = r.copy()
            r[self.pin] = float(u_core[self.pin])
        return r

    def linop(self, u_core: np.ndarray) -> LinearOperator:
        u_L, c_L = self.lift_to_L(u_core)
        diag = -2.0 - self.K * np.cos(TWO_PI * (self.theta + u_L))

        def mv(delta_core: np.ndarray) -> np.ndarray:
            delta_core = np.asarray(delta_core, dtype=float)
            d_L, dc_L = self.lift_to_L(delta_core)
            y_L = self.shift_L_coeff(dc_L, +1) + self.shift_L_coeff(dc_L, -1) + diag * d_L
            y = self.project_L_to_core(y_L)
            y[self.pin] = delta_core[self.pin]
            return y

        return LinearOperator((self.M, self.M), matvec=mv, dtype=float)

    def scalar_residual_core(self, u_core: np.ndarray) -> np.ndarray:
        # Conventional core-grid residual, for comparison with previous phases.
        M = self.M
        theta = self.theta_core
        f = self.freq_core
        c = coeff(np.asarray(u_core, dtype=float))
        up = samples_from_coeff(c * np.exp(1j * TWO_PI * f * self.omega))
        um = samples_from_coeff(c * np.exp(-1j * TWO_PI * f * self.omega))
        return up - 2.0 * u_core + um - (self.K / TWO_PI) * np.sin(TWO_PI * (theta + u_core))


def _gmres(A: LinearOperator, b: np.ndarray, *, rtol: float, atol: float, restart: int, maxiter: int) -> tuple[np.ndarray, int]:
    try:
        x, info = gmres(A, b, rtol=rtol, atol=atol, restart=restart, maxiter=maxiter)
    except TypeError:
        x, info = gmres(A, b, tol=rtol, restart=restart, maxiter=maxiter)
    return np.asarray(x, dtype=float), int(info)


@dataclass(slots=True)
class PolishConfig:
    input_npz: str
    M_out: int
    oversample: int = 4
    cutoff_mode: int | None = None
    max_newton: int = 16
    newton_tol: float = 1e-12
    accept_projected_linf: float = 1e-10
    accept_core_linf: float = 1e-8
    gmres_rtol: float = 1e-12
    gmres_atol: float = 1e-14
    gmres_restart: int = 220
    gmres_maxiter: int = 2200
    damping_min: float = 1e-6
    pin_index: int = 0
    omega_override: float | None = None
    nu: float = 1.003


@dataclass(slots=True)
class PolishStep:
    iteration: int
    projected_linf: float
    core_linf: float
    oversampled_linf: float
    gmres_info: int | None
    correction_linf: float | None
    damping: float | None
    accepted: bool


@dataclass(slots=True)
class PolishResult:
    config: PolishConfig
    K: float
    omega: float
    M_in: int
    M_out: int
    converged_projected: bool
    solve_status: str
    projected_residual_linf: float
    core_residual_linf: float
    oversampled_residual_linf: float
    weighted_u_l1_nu: float
    weighted_projected_residual_l1_nu: float
    elapsed_seconds: float
    output_npz: str | None
    record_path: str | None
    steps: list[PolishStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(
            schema="theorem_iii_trackb_phase4e_dealiased_polish_v1",
            diagnostic_only=True,
            theorem_facing=False,
            promotion_allowed=False,
            warning="Double-precision dealiased seed polish only; not interval/theorem-facing.",
        )
        return d


def weighted_l1_samples(values: np.ndarray, nu: float) -> float:
    values = np.asarray(values, dtype=float)
    f = np.abs(freq_grid(values.size))
    return float(np.sum(np.abs(coeff(values)) * np.exp(math.log(float(nu)) * f)))


def save_polished_npz(path: str | Path, u: np.ndarray, K: float, omega: float, op: DealiasedProjectedResidual, cfg: PolishConfig) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    theta = op.theta_core
    c = coeff(u)
    f = op.freq_core
    u_m = samples_from_coeff(c * np.exp(-1j * TWO_PI * f * omega))
    x = theta + u
    r = omega + u - u_m
    scalar = op.scalar_residual_core(u)
    projected = op.residual_projected(u, pin=False)
    oversampled = op.residual_L(u)
    np.savez_compressed(
        path,
        schema="theorem_iii_trackb_phase4e_dealiased_embedding_npz_v1",
        diagnostic_only=True,
        theorem_facing=False,
        K=float(K),
        M=int(op.M),
        omega=float(omega),
        theta=theta,
        u=u,
        x=x,
        r=r,
        residual=scalar,
        projected_residual=projected,
        oversampled_residual=oversampled,
        u_coeff=coeff(u),
        residual_coeff=coeff(scalar),
        projected_residual_coeff=coeff(projected),
        freq=op.freq_core,
        oversample=int(op.oversample),
        source_npz=str(cfg.input_npz),
    )
    return str(path)


def polish_one(cfg: PolishConfig, *, out_dir: str | Path, force: bool = False) -> dict[str, Any]:
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
        os.environ.setdefault(k, "1")
    t0 = time.time()
    seed = load_seed_npz(cfg.input_npz)
    u_in = np.asarray(seed["u"], dtype=float)
    K = float(seed["K"])
    omega = float(cfg.omega_override if cfg.omega_override is not None else seed["omega"])
    M_in = int(u_in.size)
    M_out = int(cfg.M_out)
    tag = f"K{K:.10f}_M{M_out}_dealias{cfg.oversample}_fromM{M_in}".replace(".", "p")
    out = Path(out_dir)
    record_path = out / "records" / f"{tag}.phase4e_dealiased_polish.json"
    npz_path = out / "embeddings" / f"{tag}.npz"
    if record_path.exists() and npz_path.exists() and not force:
        d = json.loads(record_path.read_text())
        d["loaded_from_existing_record"] = True
        return d

    u = resample_periodic(u_in, M_out, cutoff_mode=cfg.cutoff_mode)
    op = DealiasedProjectedResidual(M_out, K, omega, oversample=cfg.oversample, pin=cfg.pin_index, cutoff_mode=None)

    steps: list[PolishStep] = []
    status = "not-started"
    for it in range(int(cfg.max_newton)):
        rp = op.residual_projected(u, pin=True)
        rproj = op.residual_projected(u, pin=False)
        rcore = op.scalar_residual_core(u)
        rover = op.residual_L(u)
        pl = float(np.max(np.abs(rp)))
        cl = float(np.max(np.abs(rcore)))
        ol = float(np.max(np.abs(rover)))
        if pl <= cfg.newton_tol:
            steps.append(PolishStep(it, pl, cl, ol, None, 0.0, 0.0, True))
            status = "converged-projected"
            break
        delta, info = _gmres(op.linop(u), -rp, rtol=cfg.gmres_rtol, atol=cfg.gmres_atol, restart=cfg.gmres_restart, maxiter=cfg.gmres_maxiter)
        dl = float(np.max(np.abs(delta)))
        alpha = 1.0
        accepted = False
        chosen = None
        while alpha >= cfg.damping_min:
            trial = u + alpha * delta
            tpl = float(np.max(np.abs(op.residual_projected(trial, pin=True))))
            if tpl < pl:
                u = trial
                accepted = True
                chosen = alpha
                break
            alpha *= 0.5
        steps.append(PolishStep(it, pl, cl, ol, info, dl, chosen, accepted))
        if not accepted:
            status = f"failed-damping-at-iteration-{it}"
            break
        if dl * float(chosen or 0.0) <= max(1e-15, 0.1 * cfg.newton_tol):
            status = "stalled-small-correction"
            break
    else:
        status = "max-newton-reached"

    rproj_final = op.residual_projected(u, pin=False)
    rcore_final = op.scalar_residual_core(u)
    rover_final = op.residual_L(u)
    projected_linf = float(np.max(np.abs(rproj_final)))
    core_linf = float(np.max(np.abs(rcore_final)))
    over_linf = float(np.max(np.abs(rover_final)))
    converged = bool(projected_linf <= cfg.accept_projected_linf and core_linf <= cfg.accept_core_linf)
    if converged and status not in {"converged-projected"}:
        status = "accepted-after-final-check"
    output_npz = save_polished_npz(npz_path, u, K, omega, op, cfg)
    result = PolishResult(
        config=cfg,
        K=K,
        omega=omega,
        M_in=M_in,
        M_out=M_out,
        converged_projected=converged,
        solve_status=status,
        projected_residual_linf=projected_linf,
        core_residual_linf=core_linf,
        oversampled_residual_linf=over_linf,
        weighted_u_l1_nu=weighted_l1_samples(u, cfg.nu),
        weighted_projected_residual_l1_nu=weighted_l1_samples(rproj_final, cfg.nu),
        elapsed_seconds=float(time.time() - t0),
        output_npz=output_npz,
        record_path=str(record_path),
        steps=steps,
    )
    d = result.to_dict()
    write_json(record_path, d)
    return d


def _task(cfgd: dict[str, Any], out_dir: str, force: bool) -> dict[str, Any]:
    return polish_one(PolishConfig(**cfgd), out_dir=out_dir, force=force)


def run_phase4e_dealiased_polish(
    *,
    npz_paths: Sequence[str | Path],
    M_outs: Sequence[int],
    out_dir: str | Path,
    workers: int = 1,
    oversample: int = 4,
    cutoff_mode: int | None = None,
    max_newton: int = 16,
    newton_tol: float = 1e-12,
    accept_projected_linf: float = 1e-10,
    accept_core_linf: float = 1e-8,
    gmres_rtol: float = 1e-12,
    gmres_atol: float = 1e-14,
    gmres_restart: int = 220,
    gmres_maxiter: int = 2200,
    damping_min: float = 1e-6,
    nu: float = 1.003,
    omega_override: float | None = None,
    force: bool = False,
) -> dict[str, Any]:
    t0 = time.time()
    out = Path(out_dir)
    (out / "records").mkdir(parents=True, exist_ok=True)
    (out / "embeddings").mkdir(parents=True, exist_ok=True)
    tasks: list[dict[str, Any]] = []
    for p in npz_paths:
        for M in M_outs:
            tasks.append(asdict(PolishConfig(
                input_npz=str(p),
                M_out=int(M),
                oversample=int(oversample),
                cutoff_mode=cutoff_mode,
                max_newton=int(max_newton),
                newton_tol=float(newton_tol),
                accept_projected_linf=float(accept_projected_linf),
                accept_core_linf=float(accept_core_linf),
                gmres_rtol=float(gmres_rtol),
                gmres_atol=float(gmres_atol),
                gmres_restart=int(gmres_restart),
                gmres_maxiter=int(gmres_maxiter),
                damping_min=float(damping_min),
                omega_override=omega_override,
                nu=float(nu),
            )))
    rows: list[dict[str, Any]] = []
    nw = max(1, min(int(workers), len(tasks))) if tasks else 1
    if nw == 1:
        for td in tasks:
            rows.append(_task(td, str(out), force))
    else:
        with ProcessPoolExecutor(max_workers=nw) as ex:
            futs = [ex.submit(_task, td, str(out), force) for td in tasks]
            for fut in as_completed(futs):
                row = fut.result()
                rows.append(row)
                print(f"[phase4e] K={row.get('K')} M_out={row.get('M_out')} status={row.get('solve_status')} proj={row.get('projected_residual_linf')} core={row.get('core_residual_linf')}", flush=True)
    rows.sort(key=lambda r: (float(r.get("K", 0.0)), int(r.get("M_out", 0))))
    ranked = sorted(rows, key=lambda r: (not bool(r.get("converged_projected")), float(r.get("projected_residual_linf") or 1e300), float(r.get("core_residual_linf") or 1e300)))
    summary = {
        "schema": "theorem_iii_trackb_phase4e_dealiased_polish_summary_v1",
        "status": "phase4e-dealiased-polish-complete" if rows else "no-tasks",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "interpretation_hints": {
            "main_decision": "Run Phase 4d target-frame audit on the polished npz outputs.  If tangent/triangular defects drop materially, proceed to intervalization prep; otherwise improve frame model or use higher precision arithmetic.",
            "warning": "This is double-precision dealiased Newton polishing, not a theorem-facing proof certificate.",
        },
        "parameters": {
            "npz_count": len(list(npz_paths)),
            "M_outs": [int(x) for x in M_outs],
            "workers_requested": workers,
            "workers_used": nw,
            "oversample": oversample,
            "cutoff_mode": cutoff_mode,
            "max_newton": max_newton,
            "newton_tol": newton_tol,
            "accept_projected_linf": accept_projected_linf,
            "accept_core_linf": accept_core_linf,
            "gmres_rtol": gmres_rtol,
            "gmres_atol": gmres_atol,
            "gmres_restart": gmres_restart,
            "gmres_maxiter": gmres_maxiter,
            "damping_min": damping_min,
            "nu": nu,
            "omega_override": omega_override,
        },
        "counts": {
            "tasks": len(tasks),
            "completed_records": len(rows),
            "converged_projected": sum(bool(r.get("converged_projected")) for r in rows),
            "not_converged_projected": sum(not bool(r.get("converged_projected")) for r in rows),
        },
        "top_candidates": [
            {
                "K": r.get("K"),
                "M_in": r.get("M_in"),
                "M_out": r.get("M_out"),
                "converged_projected": r.get("converged_projected"),
                "solve_status": r.get("solve_status"),
                "projected_residual_linf": r.get("projected_residual_linf"),
                "core_residual_linf": r.get("core_residual_linf"),
                "oversampled_residual_linf": r.get("oversampled_residual_linf"),
                "weighted_projected_residual_l1_nu": r.get("weighted_projected_residual_l1_nu"),
                "weighted_u_l1_nu": r.get("weighted_u_l1_nu"),
                "output_npz": r.get("output_npz"),
                "record_path": r.get("record_path"),
            }
            for r in ranked[:40]
        ],
        "elapsed_seconds": float(time.time() - t0),
        "records": rows,
    }
    write_json(out / "phase4e_dealiased_polish_summary.json", summary)
    write_json(out / "phase4e_ranked_candidates.json", {"top_candidates": summary["top_candidates"]})
    with open(out / "phase4e_dealiased_polish_results.csv", "w", newline="", encoding="utf-8") as f:
        fields = ["K", "M_in", "M_out", "converged_projected", "solve_status", "projected_residual_linf", "core_residual_linf", "oversampled_residual_linf", "weighted_projected_residual_l1_nu", "weighted_u_l1_nu", "output_npz", "record_path", "elapsed_seconds"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})
    return summary


def summarize_phase4e(summary_path: str | Path, top: int = 20) -> dict[str, Any]:
    s = json.loads(Path(summary_path).read_text())
    rows = s.get("records", [])
    ranked = sorted(rows, key=lambda r: (not bool(r.get("converged_projected")), float(r.get("projected_residual_linf") or 1e300), float(r.get("core_residual_linf") or 1e300)))
    return {
        "schema": "theorem_iii_trackb_phase4e_compact_report_v1",
        "status": s.get("status"),
        "diagnostic_only": True,
        "parameters": s.get("parameters", {}),
        "counts": s.get("counts", {}),
        "top_candidates": [
            {
                "K": r.get("K"),
                "M_in": r.get("M_in"),
                "M_out": r.get("M_out"),
                "converged_projected": r.get("converged_projected"),
                "solve_status": r.get("solve_status"),
                "projected_residual_linf": r.get("projected_residual_linf"),
                "core_residual_linf": r.get("core_residual_linf"),
                "oversampled_residual_linf": r.get("oversampled_residual_linf"),
                "weighted_projected_residual_l1_nu": r.get("weighted_projected_residual_l1_nu"),
                "weighted_u_l1_nu": r.get("weighted_u_l1_nu"),
                "output_npz": r.get("output_npz"),
                "record_path": r.get("record_path"),
            }
            for r in ranked[: int(top)]
        ],
    }
