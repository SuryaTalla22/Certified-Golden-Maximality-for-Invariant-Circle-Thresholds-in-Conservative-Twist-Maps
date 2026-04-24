from __future__ import annotations

"""Irrational invariant-circle solver and a-posteriori validator.

This module adds the missing *existence-side* infrastructure that the enhanced
proof bridge did not yet contain. The implementation is intentionally honest
about what it validates:

- it solves a Fourier-collocation graph equation for an invariant circle of a
  standard-map-type family with irrational rotation number ``rho``;
- it applies a Newton--Kantorovich/radii-polynomial style argument to the
  resulting finite-dimensional nonlinear system; and
- it supplements the discrete proof object with oversampled residual and Fourier
  tail diagnostics that help the user judge how well the collocation solution is
  approximating the infinite-dimensional analytic problem.

This is not presented as a finished analytic KAM theorem for the full invariant
circle problem. It *is* a serious proof-bridge component: it yields a validated
ball for the discrete collocation system and exports the constants needed for a
future infinite-dimensional a-posteriori argument.
"""

from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Any, Sequence

import numpy as np

from .interval_utils import interval_mag, iv_scalar
from .standard_map import HarmonicFamily
from .analytic_norms import (
    AnalyticStripProfile,
    TheoremNormProfile,
    build_analytic_strip_profile,
    build_theorem_norm_profile_from_strip_profile,
    choose_safe_sigma,
)
from .fourier_bounds import (
    FourierTailBound,
    FourierTailClosureCertificate,
    build_fourier_tail_closure_certificate,
    certify_fourier_tail_bound_from_coeffs,
)
from .small_divisors import (
    SmallDivisorAudit,
    SmallDivisorClosureCertificate,
    build_small_divisor_audit,
    build_small_divisor_closure_certificate,
)
from .invariance_defect import (
    InvarianceDefectReport,
    InvarianceDefectClosureCertificate,
    build_invariance_defect_report,
    build_invariance_defect_closure_certificate,
)


@dataclass
class InvariantCircleSolveResult:
    rho: float
    K: float
    N: int
    success: bool
    iterations: int
    residual_inf: float
    residual_l2: float
    lambda_value: float
    mean_u: float
    damping_steps: int
    message: str
    u: np.ndarray = field(repr=False)
    z: np.ndarray = field(repr=False)
    history: list[float] = field(default_factory=list, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["u"] = np.asarray(self.u, dtype=float).tolist()
        d["z"] = np.asarray(self.z, dtype=float).tolist()
        return d


@dataclass
class InvariantCircleValidationResult:
    rho: float
    K: float
    N: int
    success: bool
    message: str
    radius: float
    eta: float
    B_norm: float
    lipschitz_bound: float
    contraction_bound: float
    residual_inf: float
    residual_l2: float
    lambda_value: float
    mean_u: float
    oversampled_residual_inf: float
    fourier_tail_l1: float
    fourier_tail_l2: float
    strip_width_proxy: float | None
    solver_iterations: int
    solver_history: list[float]
    bridge_quality: str
    u: np.ndarray = field(repr=False)
    z: np.ndarray = field(repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["u"] = np.asarray(self.u, dtype=float).tolist()
        d["z"] = np.asarray(self.z, dtype=float).tolist()
        return d


@dataclass
class AnalyticInvariantCircleCertificate:
    rho: float
    K: float
    N: int
    theorem_status: str
    message: str
    finite_dimensional_success: bool
    bridge_quality: str
    sigma_used: float
    sigma_cap: float
    strip_width_proxy: float | None
    strip_profile: AnalyticStripProfile
    defect_report: InvarianceDefectReport
    tail_bound: FourierTailBound
    small_divisor_audit: SmallDivisorAudit
    finite_radius: float
    finite_eta: float
    finite_B_norm: float
    finite_lipschitz_bound: float
    finite_contraction_bound: float
    finite_radii_margin: float | None
    cohomological_inverse_bound: float
    cohomological_correction_bound: float
    theorem_margin: float | None
    source_validation: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "K": float(self.K),
            "N": int(self.N),
            "theorem_status": str(self.theorem_status),
            "message": str(self.message),
            "finite_dimensional_success": bool(self.finite_dimensional_success),
            "bridge_quality": str(self.bridge_quality),
            "sigma_used": float(self.sigma_used),
            "sigma_cap": float(self.sigma_cap),
            "strip_width_proxy": self.strip_width_proxy,
            "strip_profile": self.strip_profile.to_dict(),
            "defect_report": self.defect_report.to_dict(),
            "tail_bound": self.tail_bound.to_dict(),
            "small_divisor_audit": self.small_divisor_audit.to_dict(),
            "finite_radius": float(self.finite_radius),
            "finite_eta": float(self.finite_eta),
            "finite_B_norm": float(self.finite_B_norm),
            "finite_lipschitz_bound": float(self.finite_lipschitz_bound),
            "finite_contraction_bound": float(self.finite_contraction_bound),
            "finite_radii_margin": self.finite_radii_margin,
            "cohomological_inverse_bound": float(self.cohomological_inverse_bound),
            "cohomological_correction_bound": float(self.cohomological_correction_bound),
            "theorem_margin": self.theorem_margin,
            "source_validation": dict(self.source_validation),
        }




@dataclass
class InfiniteDimensionalClosureWitness:
    rho: float
    K: float
    N: int
    resolved_mode_validation_certified: bool
    analytic_strip_norm_certified: bool
    tail_closure_certified: bool
    small_divisor_closure_certified: bool
    invariance_defect_closure_certified: bool
    newton_kantorovich_margin: float | None
    closure_margin: float | None
    closure_status: str
    residual_tail_split: dict[str, float]
    theorem_norm_profile: TheoremNormProfile
    tail_closure: FourierTailClosureCertificate
    small_divisor_closure: SmallDivisorClosureCertificate
    defect_closure: InvarianceDefectClosureCertificate
    source_certificate: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho': float(self.rho),
            'K': float(self.K),
            'N': int(self.N),
            'resolved_mode_validation_certified': bool(self.resolved_mode_validation_certified),
            'analytic_strip_norm_certified': bool(self.analytic_strip_norm_certified),
            'tail_closure_certified': bool(self.tail_closure_certified),
            'small_divisor_closure_certified': bool(self.small_divisor_closure_certified),
            'invariance_defect_closure_certified': bool(self.invariance_defect_closure_certified),
            'newton_kantorovich_margin': None if self.newton_kantorovich_margin is None else float(self.newton_kantorovich_margin),
            'closure_margin': None if self.closure_margin is None else float(self.closure_margin),
            'closure_status': str(self.closure_status),
            'residual_tail_split': {k: float(v) for k, v in self.residual_tail_split.items()},
            'theorem_norm_profile': self.theorem_norm_profile.to_dict(),
            'tail_closure': self.tail_closure.to_dict(),
            'small_divisor_closure': self.small_divisor_closure.to_dict(),
            'defect_closure': self.defect_closure.to_dict(),
            'source_certificate': dict(self.source_certificate),
        }


def _closure_field(obj: Any, name: str, default: Any = None) -> Any:
    if hasattr(obj, name):
        return getattr(obj, name)
    if isinstance(obj, dict):
        return obj.get(name, default)
    if hasattr(obj, 'to_dict'):
        try:
            d = obj.to_dict()
            if isinstance(d, dict):
                return d.get(name, default)
        except Exception:
            pass
    return default


def build_infinite_dimensional_closure_witness(
    certificate: AnalyticInvariantCircleCertificate,
    *,
    tail_threshold: float = 1.0e-4,
    inverse_bound_threshold: float = 10.0,
    defect_threshold: float = 1.0e-5,
) -> InfiniteDimensionalClosureWitness:
    theorem_norm_profile = build_theorem_norm_profile_from_strip_profile(certificate.strip_profile)
    tail_closure_raw = build_fourier_tail_closure_certificate(certificate.tail_bound, threshold=tail_threshold)
    defect_closure_raw = build_invariance_defect_closure_certificate(certificate.defect_report, defect_threshold=defect_threshold)
    resolved_mode_validation_certified = bool(certificate.finite_dimensional_success and certificate.finite_contraction_bound < 1.0)
    analytic_strip_norm_certified = bool(theorem_norm_profile.norm_translation_certified and theorem_norm_profile.analytic_norm > 0.0)
    nk_margin = certificate.theorem_margin
    defect_combined = _closure_field(defect_closure_raw, 'combined_theorem_defect')
    small_divisor_closure_raw = build_small_divisor_closure_certificate(certificate.small_divisor_audit, inverse_bound_threshold=inverse_bound_threshold, effective_defect=defect_combined, finite_margin=nk_margin, strip_loss_sigma=certificate.sigma_used)
    margins = [
        nk_margin,
        _closure_field(tail_closure_raw, 'tail_closure_margin'),
        _closure_field(small_divisor_closure_raw, 'small_divisor_closure_margin'),
        (defect_threshold - defect_combined) if defect_combined is not None and np.isfinite(defect_combined) else None,
    ]
    margins = [float(m) for m in margins if m is not None]
    closure_margin = None if not margins else float(min(margins))
    all_closed = bool(
        resolved_mode_validation_certified
        and analytic_strip_norm_certified
        and bool(_closure_field(tail_closure_raw, 'tail_ready_for_theorem', False))
        and bool(_closure_field(small_divisor_closure_raw, 'small_divisor_ready_for_theorem', False))
        and bool(_closure_field(defect_closure_raw, 'defect_ready_for_closure', False))
        and nk_margin is not None and nk_margin > 0.0
    )
    if all_closed:
        status = 'infinite-dimensional-closure-strong'
    elif resolved_mode_validation_certified:
        status = 'infinite-dimensional-closure-partial'
    else:
        status = 'infinite-dimensional-closure-failed'
    tail_closure = tail_closure_raw if isinstance(tail_closure_raw, FourierTailClosureCertificate) else FourierTailClosureCertificate(certificate.sigma_used, certificate.N, bool(_closure_field(tail_closure_raw, 'tail_sum_certified', False)), 'patched', _closure_field(tail_closure_raw, 'tail_closure_margin'), bool(_closure_field(tail_closure_raw, 'tail_ready_for_theorem', False)), dict(tail_closure_raw.to_dict() if hasattr(tail_closure_raw, 'to_dict') else {}), str(_closure_field(tail_closure_raw, 'theorem_status', 'fourier-tail-closure-partial')) )
    small_divisor_closure = small_divisor_closure_raw if isinstance(small_divisor_closure_raw, SmallDivisorClosureCertificate) else SmallDivisorClosureCertificate(certificate.rho, max(1, certificate.N // 2), bool(_closure_field(small_divisor_closure_raw, 'divisor_tail_law_certified', False)), _closure_field(small_divisor_closure_raw, 'small_divisor_closure_margin'), bool(_closure_field(small_divisor_closure_raw, 'small_divisor_ready_for_theorem', False)), str(_closure_field(small_divisor_closure_raw, 'theorem_status', 'small-divisor-closure-partial')), dict(small_divisor_closure_raw.to_dict() if hasattr(small_divisor_closure_raw, 'to_dict') else {}))
    defect_closure = defect_closure_raw if isinstance(defect_closure_raw, InvarianceDefectClosureCertificate) else InvarianceDefectClosureCertificate(certificate.rho, certificate.K, certificate.sigma_used, 0.0, 0.0, float(defect_combined or 0.0), bool(_closure_field(defect_closure_raw, 'defect_ready_for_closure', False)), str(_closure_field(defect_closure_raw, 'theorem_status', 'invariance-defect-closure-partial')), dict(defect_closure_raw.to_dict() if hasattr(defect_closure_raw, 'to_dict') else {}))
    return InfiniteDimensionalClosureWitness(
        rho=float(certificate.rho),
        K=float(certificate.K),
        N=int(certificate.N),
        resolved_mode_validation_certified=bool(resolved_mode_validation_certified),
        analytic_strip_norm_certified=bool(analytic_strip_norm_certified),
        tail_closure_certified=bool(_closure_field(tail_closure_raw, 'tail_ready_for_theorem', False)),
        small_divisor_closure_certified=bool(_closure_field(small_divisor_closure_raw, 'small_divisor_ready_for_theorem', False)),
        invariance_defect_closure_certified=bool(_closure_field(defect_closure_raw, 'defect_ready_for_closure', False)),
        newton_kantorovich_margin=None if nk_margin is None else float(nk_margin),
        closure_margin=None if closure_margin is None else float(closure_margin),
        closure_status=str(status),
        residual_tail_split={
            'tail_l1': float(certificate.tail_bound.tail_l1 or 0.0),
            'tail_l2': float(certificate.tail_bound.tail_l2 or 0.0),
            'tail_sup': float(certificate.tail_bound.tail_sup or 0.0),
        },
        theorem_norm_profile=theorem_norm_profile,
        tail_closure=tail_closure,
        small_divisor_closure=small_divisor_closure,
        defect_closure=defect_closure,
        source_certificate=certificate.to_dict(),
    )


@lru_cache(maxsize=64)
def _spectral_shift_matrix_cached(N: int, rho_round: float) -> np.ndarray:
    k = np.fft.fftfreq(N, d=1.0 / N)
    eye = np.eye(N)
    cols = []
    phase = np.exp(2j * np.pi * k * rho_round)
    for j in range(N):
        cols.append(np.fft.ifft(np.fft.fft(eye[:, j]) * phase).real)
    return np.column_stack(cols)


@lru_cache(maxsize=64)
def _theta_grid_cached(N: int) -> np.ndarray:
    return np.arange(N, dtype=float) / float(N)


@lru_cache(maxsize=64)
def _ones_cached(N: int) -> np.ndarray:
    return np.ones(N, dtype=float)


@lru_cache(maxsize=64)
def _mean_row_cached(N: int) -> np.ndarray:
    return np.ones((1, N), dtype=float) / float(N)


@lru_cache(maxsize=64)
def _spectral_wavenumbers_cached(N: int) -> np.ndarray:
    return np.fft.fftfreq(N, d=1.0 / N)


@lru_cache(maxsize=64)
def _shift_pair(N: int, rho_round: float) -> tuple[np.ndarray, np.ndarray]:
    return (
        _spectral_shift_matrix_cached(N, rho_round),
        _spectral_shift_matrix_cached(N, -rho_round),
    )


def theta_grid(N: int) -> np.ndarray:
    return _theta_grid_cached(int(N)).copy()


def spectral_coefficients_from_samples(u: np.ndarray) -> np.ndarray:
    u = np.asarray(u, dtype=float)
    return np.fft.fft(u) / len(u)


def evaluate_trig_interpolant_from_coeffs(coeffs: np.ndarray, theta: np.ndarray) -> np.ndarray:
    coeffs = np.asarray(coeffs, dtype=complex)
    N = len(coeffs)
    k = _spectral_wavenumbers_cached(N)
    theta = np.asarray(theta, dtype=float)
    expo = np.exp(2j * np.pi * np.outer(theta, k))
    vals = expo @ coeffs
    return np.real_if_close(vals, tol=1000).astype(float)


def evaluate_trig_interpolant(u: np.ndarray, theta: np.ndarray) -> np.ndarray:
    coeffs = spectral_coefficients_from_samples(np.asarray(u, dtype=float))
    return evaluate_trig_interpolant_from_coeffs(coeffs, theta)


def spectral_shift(u: np.ndarray, rho: float) -> np.ndarray:
    u = np.asarray(u, dtype=float)
    coeffs = np.fft.fft(u)
    k = _spectral_wavenumbers_cached(len(u))
    return np.fft.ifft(coeffs * np.exp(2j * np.pi * k * float(rho))).real


def invariant_circle_operator(
    u: np.ndarray,
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    lambda_value: float = 0.0,
) -> np.ndarray:
    family = family or HarmonicFamily()
    u = np.asarray(u, dtype=float)
    theta = theta_grid(len(u))
    return (
        spectral_shift(u, rho)
        + spectral_shift(u, -rho)
        - 2.0 * u
        - float(K) * family.force(theta + u)
        - float(lambda_value)
    )


def augmented_invariant_circle_operator(
    z: np.ndarray,
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
) -> np.ndarray:
    family = family or HarmonicFamily()
    z = np.asarray(z, dtype=float)
    N = len(z) - 1
    u = z[:N]
    lam = float(z[N])
    top = invariant_circle_operator(u, rho, K, family, lambda_value=lam)
    bottom = np.array([np.mean(u)], dtype=float)
    return np.concatenate([top, bottom])


def linearized_augmented_operator_matrix(
    u: np.ndarray,
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
) -> np.ndarray:
    family = family or HarmonicFamily()
    u = np.asarray(u, dtype=float)
    N = len(u)
    S_p, S_m = _shift_pair(N, float(rho))
    theta = theta_grid(N)
    top_left = S_p + S_m - 2.0 * np.eye(N) - float(K) * np.diag(family.dforce(theta + u))
    top_right = -_ones_cached(N).reshape(N, 1)
    bottom_left = _mean_row_cached(N)
    bottom_right = np.zeros((1, 1), dtype=float)
    return np.block([[top_left, top_right], [bottom_left, bottom_right]])


def solve_invariant_circle_graph(
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    u0: np.ndarray | None = None,
    z0: np.ndarray | None = None,
    max_newton: int = 15,
    tol: float = 1e-12,
    line_search_floor: float = 2.0**-12,
) -> InvariantCircleSolveResult:
    family = family or HarmonicFamily()
    N = int(N)
    if z0 is not None:
        z = np.asarray(z0, dtype=float).copy()
        if len(z) != N + 1:
            raise ValueError("z0 must have length N+1")
    else:
        u_init = np.zeros(N, dtype=float) if u0 is None else np.asarray(u0, dtype=float).copy()
        if len(u_init) != N:
            raise ValueError("u0 must have length N")
        u_init -= np.mean(u_init)
        z = np.concatenate([u_init, np.array([0.0])])

    damping_steps = 0
    history: list[float] = []
    success = False
    message = "maximum Newton iterations reached"

    for it in range(1, max_newton + 1):
        G = augmented_invariant_circle_operator(z, rho, K, family)
        res_inf = float(np.linalg.norm(G, ord=np.inf))
        history.append(res_inf)
        if res_inf < tol:
            success = True
            message = "Newton solve converged"
            break

        J = linearized_augmented_operator_matrix(z[:-1], rho, K, family)
        try:
            delta = np.linalg.solve(J, -G)
        except np.linalg.LinAlgError:
            message = "linearized operator singular during Newton solve"
            break

        alpha = 1.0
        z_trial = z + delta
        trial_res = float(np.linalg.norm(augmented_invariant_circle_operator(z_trial, rho, K, family), ord=np.inf))
        while trial_res > (1.0 - 1e-4 * alpha) * res_inf and alpha > line_search_floor:
            alpha *= 0.5
            damping_steps += 1
            z_trial = z + alpha * delta
            trial_res = float(np.linalg.norm(augmented_invariant_circle_operator(z_trial, rho, K, family), ord=np.inf))
        z = z_trial
        z[:-1] -= np.mean(z[:-1])

    G = augmented_invariant_circle_operator(z, rho, K, family)
    res_inf = float(np.linalg.norm(G, ord=np.inf))
    res_l2 = float(np.linalg.norm(G))
    return InvariantCircleSolveResult(
        rho=float(rho),
        K=float(K),
        N=N,
        success=bool(success),
        iterations=it if 'it' in locals() else 0,
        residual_inf=res_inf,
        residual_l2=res_l2,
        lambda_value=float(z[-1]),
        mean_u=float(np.mean(z[:-1])),
        damping_steps=int(damping_steps),
        message=message,
        u=np.asarray(z[:-1], dtype=float),
        z=np.asarray(z, dtype=float),
        history=history,
    )


def second_derivative_bound_on_ball(
    u: np.ndarray,
    K: float,
    radius: float,
    family: HarmonicFamily | None = None,
) -> float:
    family = family or HarmonicFamily()
    u = np.asarray(u, dtype=float)
    theta = theta_grid(len(u))
    mags = []
    r = abs(float(radius))
    for th, ui in zip(theta, u):
        arg_iv = iv_scalar(float(th + ui - r), float(th + ui + r))
        mags.append(interval_mag(family.ddforce_iv(arg_iv)))
    return abs(float(K)) * float(max(mags) if mags else 0.0)


def fourier_tail_metrics(u: np.ndarray, frac: float = 0.15) -> tuple[float, float, float | None]:
    coeffs = spectral_coefficients_from_samples(np.asarray(u, dtype=float))
    N = len(coeffs)
    k = np.fft.fftfreq(N, d=1.0 / N)
    abs_coeffs = np.abs(coeffs)
    nz = np.where(np.abs(k) > 0)[0]
    if len(nz) == 0:
        return 0.0, 0.0, None
    cutoff = max(1, int(np.ceil(frac * len(nz))))
    order = nz[np.argsort(np.abs(k[nz]))]
    tail = order[-cutoff:]
    tail_l1 = float(np.sum(abs_coeffs[tail]))
    tail_l2 = float(np.sqrt(np.sum(abs_coeffs[tail] ** 2)))

    # Crude strip-width proxy from the log-decay of the high modes.
    mags = abs_coeffs[order]
    modes = np.abs(k[order]).astype(float)
    valid = (mags > 1e-30) & (modes > 0)
    if np.count_nonzero(valid) < 4:
        return tail_l1, tail_l2, None
    tail_idx = np.where(valid)[0][-max(4, cutoff):]
    x = modes[tail_idx]
    y = np.log(mags[tail_idx])
    try:
        slope, _ = np.polyfit(x, y, deg=1)
    except np.linalg.LinAlgError:
        return tail_l1, tail_l2, None
    sigma = max(0.0, -float(slope) / (2.0 * np.pi))
    return tail_l1, tail_l2, sigma


def oversampled_residual_inf(
    u: np.ndarray,
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    lambda_value: float = 0.0,
    oversample_factor: int = 4,
) -> float:
    family = family or HarmonicFamily()
    u = np.asarray(u, dtype=float)
    coeffs = spectral_coefficients_from_samples(u)
    M = max(oversample_factor * len(u), len(u))
    theta = np.arange(M, dtype=float) / float(M)
    u_theta = evaluate_trig_interpolant_from_coeffs(coeffs, theta)
    u_plus = evaluate_trig_interpolant_from_coeffs(coeffs, (theta + float(rho)) % 1.0)
    u_minus = evaluate_trig_interpolant_from_coeffs(coeffs, (theta - float(rho)) % 1.0)
    resid = u_plus + u_minus - 2.0 * u_theta - float(K) * family.force(theta + u_theta) - float(lambda_value)
    return float(np.linalg.norm(resid, ord=np.inf))


def _search_validated_radius(
    u: np.ndarray,
    G_normed: float,
    B_norm: float,
    K: float,
    family: HarmonicFamily,
    *,
    r_min: float,
    r_max: float,
    n_grid: int = 80,
    selection_mode: str = 'best_margin',
    q_soft: float = 0.7,
) -> tuple[bool, float, float, float]:
    """Search for a radii-polynomial enclosure.

    We use the standard sufficient condition

        eta + 0.5 * B * L(r) * r^2 < r,

    together with the local uniqueness bound ``B * L(r) * r < 1``.  Here
    ``eta = ||A F(x*)||_∞`` and ``B = ||A||_∞`` with ``A = DF(x*)^{-1}``.

    The theorem-facing default scans all admissible radii on the geometric
    grid and keeps the one with the best certified margin instead of the
    first admissible radius.
    """
    if not np.isfinite(r_min) or not np.isfinite(r_max):
        return False, float('nan'), float('nan'), float('nan')
    if r_min <= 0:
        r_min = 1e-18
    if r_max <= r_min:
        r_max = max(10.0 * r_min, 1e-12)
    grid = np.geomspace(r_min, r_max, num=max(8, int(n_grid)))
    admissible=[]
    for r in grid:
        Lr = second_derivative_bound_on_ball(u, K, r, family)
        p_r = G_normed + 0.5 * B_norm * Lr * r * r - r
        q_r = B_norm * Lr * r
        if p_r < 0.0 and q_r < 1.0:
            margin = float(-p_r)
            admissible.append((float(r), float(Lr), float(q_r), margin))
            if selection_mode == 'first':
                break
    if not admissible:
        return False, float('nan'), float('nan'), float('nan')
    if selection_mode == 'first':
        r, Lr, q_r, _ = admissible[0]
        return True, r, Lr, q_r
    r, Lr, q_r, _ = max(admissible, key=lambda item: (item[3], max(0.0, float(q_soft)-item[2]), item[0]))
    return True, r, Lr, q_r


def classify_torus_bridge_quality(
    *,
    success: bool,
    oversampled_residual_inf: float,
    contraction_bound: float,
    fourier_tail_l2: float,
) -> str:
    if not success:
        return "failed"
    if oversampled_residual_inf <= 1e-8 and contraction_bound <= 0.25 and fourier_tail_l2 <= 1e-8:
        return "strong"
    if oversampled_residual_inf <= 1e-5 and contraction_bound <= 0.5 and fourier_tail_l2 <= 1e-5:
        return "moderate"
    return "weak"


def validate_invariant_circle_graph(
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    solve_result: InvariantCircleSolveResult | None = None,
    u0: np.ndarray | None = None,
    z0: np.ndarray | None = None,
    oversample_factor: int = 4,
    radius_search_factor: float = 1e6,
) -> InvariantCircleValidationResult:
    family = family or HarmonicFamily()
    if solve_result is None:
        solve_result = solve_invariant_circle_graph(rho, K, family, N=N, u0=u0, z0=z0)
    z = np.asarray(solve_result.z, dtype=float)
    u = np.asarray(solve_result.u, dtype=float)
    G = augmented_invariant_circle_operator(z, rho, K, family)
    J = linearized_augmented_operator_matrix(u, rho, K, family)

    try:
        A = np.linalg.inv(J)
    except np.linalg.LinAlgError:
        return InvariantCircleValidationResult(
            rho=float(rho),
            K=float(K),
            N=int(N),
            success=False,
            message="linearized augmented operator singular at candidate solution",
            radius=float("nan"),
            eta=float("nan"),
            B_norm=float("nan"),
            lipschitz_bound=float("nan"),
            contraction_bound=float("nan"),
            residual_inf=float(np.linalg.norm(G, ord=np.inf)),
            residual_l2=float(np.linalg.norm(G)),
            lambda_value=float(z[-1]),
            mean_u=float(np.mean(u)),
            oversampled_residual_inf=float("nan"),
            fourier_tail_l1=float("nan"),
            fourier_tail_l2=float("nan"),
            strip_width_proxy=None,
            solver_iterations=int(solve_result.iterations),
            solver_history=list(solve_result.history),
            bridge_quality="failed",
            u=u,
            z=z,
        )

    eta = float(np.linalg.norm(A @ G, ord=np.inf))
    B_norm = float(np.linalg.norm(A, ord=np.inf))
    success, radius, Lr, contraction = _search_validated_radius(
        u,
        eta,
        B_norm,
        K,
        family,
        r_min=max(1.1 * max(eta, 1e-18), 1e-16),
        r_max=max(radius_search_factor * max(eta, 1e-18), 1e-8),
    )
    over_res = oversampled_residual_inf(u, rho, K, family, lambda_value=z[-1], oversample_factor=oversample_factor)
    tail_l1, tail_l2, sigma = fourier_tail_metrics(u)

    if success:
        msg = (
            "validated finite-dimensional collocation circle via radii-polynomial "
            "bound for the augmented graph equation"
        )
    else:
        msg = (
            "Newton solve succeeded, but the current radii-polynomial search did not "
            "close a validated ball"
        )
    bridge_quality = classify_torus_bridge_quality(
        success=bool(success),
        oversampled_residual_inf=float(over_res),
        contraction_bound=float(contraction),
        fourier_tail_l2=float(tail_l2),
    )

    return InvariantCircleValidationResult(
        rho=float(rho),
        K=float(K),
        N=int(N),
        success=bool(success),
        message=msg,
        radius=float(radius),
        eta=float(eta),
        B_norm=float(B_norm),
        lipschitz_bound=float(Lr),
        contraction_bound=float(contraction),
        residual_inf=float(np.linalg.norm(G, ord=np.inf)),
        residual_l2=float(np.linalg.norm(G)),
        lambda_value=float(z[-1]),
        mean_u=float(np.mean(u)),
        oversampled_residual_inf=float(over_res),
        fourier_tail_l1=float(tail_l1),
        fourier_tail_l2=float(tail_l2),
        strip_width_proxy=sigma,
        solver_iterations=int(solve_result.iterations),
        solver_history=list(solve_result.history),
        bridge_quality=bridge_quality,
        u=u,
        z=z,
    )



def _finite_radii_margin(val: InvariantCircleValidationResult) -> float | None:
    if not (np.isfinite(val.radius) and np.isfinite(val.eta) and np.isfinite(val.B_norm) and np.isfinite(val.lipschitz_bound)):
        return None
    return float(val.radius - (val.eta + 0.5 * val.B_norm * val.lipschitz_bound * val.radius * val.radius))


def _theorem_sigma_candidates(*, strip_width_proxy: float | None, sigma_cap: float, floor: float = 1.0e-4) -> list[float]:
    upper=float(sigma_cap)
    if strip_width_proxy is not None and np.isfinite(strip_width_proxy) and strip_width_proxy > 0.0:
        upper=min(upper,float(strip_width_proxy))
    upper=max(float(floor),upper)
    anchors=[float(floor),3.0e-4,1.0e-3,3.0e-3,5.0e-3,1.0e-2,2.0e-2,choose_safe_sigma(strip_width_proxy=strip_width_proxy,sigma_cap=sigma_cap),upper]
    if upper>floor*1.001:
        anchors.extend(np.geomspace(float(floor),float(upper),num=7).tolist())
    out=[]
    for sigma in sorted({float(x) for x in anchors if np.isfinite(x)}):
        if floor-1e-18 <= sigma <= upper+1e-18:
            out.append(float(sigma))
    return out or [float(min(max(floor, sigma_cap*0.25), sigma_cap))]


def _evaluate_sigma_candidate(*, u: np.ndarray, rho: float, K: float, family: HarmonicFamily, lambda_value: float, sigma: float, coeffs: np.ndarray, strip_width_proxy: float | None, N: int, oversample_factor: int, small_divisor_audit: SmallDivisorAudit, finite_margin: float | None):
    strip_profile = build_analytic_strip_profile(np.asarray(u, dtype=float), sigma=float(sigma))
    defect_report = build_invariance_defect_report(np.asarray(u, dtype=float), float(rho), float(K), family, lambda_value=float(lambda_value), sigma=float(sigma), oversample_factor=max(4, int(oversample_factor)))
    tail_bound = certify_fourier_tail_bound_from_coeffs(coeffs, sigma_used=float(sigma), strip_width_proxy=strip_width_proxy, tail_start_mode=max(1, int(N//2 + 1)))
    inv=float(small_divisor_audit.cohomological_inverse_bound)
    correction=float(defect_report.weighted_l1*inv)
    tail_term=0.0 if tail_bound.tail_l1 is None else float(tail_bound.tail_l1*inv)
    theorem_margin=None if finite_margin is None else float(finite_margin-correction-tail_term)
    tail_penalty=float('inf') if tail_bound.tail_l1 is None else float(tail_bound.tail_l1)
    score=(-float('inf'),-float('inf'),-float('inf'),-float(sigma)) if theorem_margin is None or not np.isfinite(theorem_margin) else (1.0 if theorem_margin>0.0 else 0.0,float(theorem_margin),-float(defect_report.weighted_l1+tail_penalty),-float(sigma))
    return score, strip_profile, defect_report, tail_bound, correction, theorem_margin


def _classify_analytic_torus_theorem_status(
    *,
    finite_success: bool,
    bridge_quality: str,
    theorem_margin: float | None,
    weighted_residual_l1: float,
    tail_l1: float | None,
) -> tuple[str, str]:
    if not finite_success:
        return (
            "analytic-torus-failed",
            "no validated finite-dimensional ball was available for the invariant graph equation",
        )
    tail_val = float('inf') if tail_l1 is None else float(tail_l1)
    margin_ok = theorem_margin is not None and theorem_margin > 0.0
    if bridge_quality in {"strong", "moderate"} and margin_ok and weighted_residual_l1 <= 1e-6 and tail_val <= 1e-6:
        return (
            "analytic-torus-bridge-strong",
            "validated collocation ball plus analytic-strip defect, tail, and small-divisor bounds close in a strong lower-side theorem-facing regime",
        )
    if bridge_quality in {"strong", "moderate"} and margin_ok and weighted_residual_l1 <= 1e-4:
        return (
            "analytic-torus-bridge-moderate",
            "validated collocation ball plus explicit analytic-strip constants give a moderate a-posteriori lower-side bridge",
        )
    return (
        "analytic-torus-bridge-weak",
        "validated finite-dimensional circle available, but the analytic-strip correction/tail bridge remains too weak for a stronger theorem-facing claim",
    )


def build_analytic_invariant_circle_certificate(
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    sigma_cap: float = 0.04,
    oversample_factor: int = 8,
    solve_result: InvariantCircleSolveResult | None = None,
    u0: np.ndarray | None = None,
    z0: np.ndarray | None = None,
) -> AnalyticInvariantCircleCertificate:
    family = family or HarmonicFamily()
    val = validate_invariant_circle_graph(rho=float(rho), K=float(K), family=family, N=int(N), solve_result=solve_result, u0=u0, z0=z0, oversample_factor=max(4, int(oversample_factor)))
    coeffs = spectral_coefficients_from_samples(np.asarray(val.u, dtype=float))
    small_divisor_audit = build_small_divisor_audit(float(rho), max(1, int(val.N // 2)), label='exact-small-divisor-audit')
    finite_margin = _finite_radii_margin(val)
    best=None
    for sigma in _theorem_sigma_candidates(strip_width_proxy=val.strip_width_proxy, sigma_cap=sigma_cap):
        payload = _evaluate_sigma_candidate(u=np.asarray(val.u, dtype=float), rho=float(rho), K=float(K), family=family, lambda_value=float(val.lambda_value), sigma=float(sigma), coeffs=coeffs, strip_width_proxy=val.strip_width_proxy, N=int(val.N), oversample_factor=max(4, int(oversample_factor)), small_divisor_audit=small_divisor_audit, finite_margin=finite_margin)
        if best is None or payload[0] > best[0]:
            best = payload
    _, strip_profile, defect_report, tail_bound, correction, theorem_margin = best
    sigma_used=float(defect_report.sigma)
    theorem_status, message = _classify_analytic_torus_theorem_status(finite_success=bool(val.success), bridge_quality=str(val.bridge_quality), theorem_margin=theorem_margin, weighted_residual_l1=float(defect_report.weighted_l1), tail_l1=tail_bound.tail_l1)
    return AnalyticInvariantCircleCertificate(rho=float(rho), K=float(K), N=int(val.N), theorem_status=str(theorem_status), message=str(message), finite_dimensional_success=bool(val.success), bridge_quality=str(val.bridge_quality), sigma_used=float(sigma_used), sigma_cap=float(sigma_cap), strip_width_proxy=(None if val.strip_width_proxy is None else float(val.strip_width_proxy)), strip_profile=strip_profile, defect_report=defect_report, tail_bound=tail_bound, small_divisor_audit=small_divisor_audit, finite_radius=float(val.radius), finite_eta=float(val.eta), finite_B_norm=float(val.B_norm), finite_lipschitz_bound=float(val.lipschitz_bound), finite_contraction_bound=float(val.contraction_bound), finite_radii_margin=(None if finite_margin is None else float(finite_margin)), cohomological_inverse_bound=float(small_divisor_audit.cohomological_inverse_bound), cohomological_correction_bound=float(correction), theorem_margin=(None if theorem_margin is None else float(theorem_margin)), source_validation=val.to_dict())


def build_theorem_optimized_analytic_invariant_circle_certificate(rho: float, K: float, family: HarmonicFamily | None = None, *, N_values: Sequence[int] = (64, 96, 128), sigma_cap: float = 0.04, oversample_factor: int = 8) -> AnalyticInvariantCircleCertificate:
    family = family or HarmonicFamily()
    candidates=[]
    for N in sorted({int(x) for x in N_values if int(x)>0}):
        cert = build_analytic_invariant_circle_certificate(rho=float(rho), K=float(K), family=family, N=int(N), sigma_cap=sigma_cap, oversample_factor=oversample_factor)
        score=(1.0 if cert.theorem_margin is not None and cert.theorem_margin>0.0 else 0.0, float('-inf') if cert.theorem_margin is None else float(cert.theorem_margin), float('-inf') if cert.finite_radii_margin is None else float(cert.finite_radii_margin), -float(cert.cohomological_inverse_bound))
        candidates.append((score, cert))
        if cert.theorem_margin is not None and cert.theorem_margin>0.0 and cert.finite_dimensional_success:
            return cert
    return max(candidates, key=lambda item: item[0])[1]

def build_existence_vs_crossing_bridge(
    rho: float,
    K: float,
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    target_residue: float = 0.25,
):
    """Convenience bridge object tying the irrational existence side to a
    rational crossing window.

    The function intentionally imports the crossing machinery lazily so the
    torus validator remains usable on its own.
    """
    family = family or HarmonicFamily()
    from .certification import get_residue_and_derivative_iv

    torus = validate_invariant_circle_graph(rho, K, family, N=N)
    crossing = get_residue_and_derivative_iv(
        p=p,
        q=q,
        K_iv=iv_scalar(K_lo, K_hi),
        family=family,
        x_guess=None,
        target_residue=target_residue,
    )
    relation = {
        "K_vs_window": "inside" if K_lo <= K <= K_hi else ("below" if K < K_lo else "above"),
        "torus_validated": bool(torus.success),
        "crossing_success": bool(crossing.get("success", False)),
    }
    if crossing.get("success", False):
        g_lo = float(crossing["g_interval_lo"])
        g_hi = float(crossing["g_interval_hi"])
        relation["g_sign"] = "negative" if g_hi < 0 else ("positive" if g_lo > 0 else "mixed")
    return {
        "torus_validation": torus.to_dict(),
        "crossing_window": crossing,
        "relation": relation,
    }
