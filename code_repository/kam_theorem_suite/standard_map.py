from __future__ import annotations

"""Standard-map and generalized harmonic-family helpers.

This version hardens the original bridge-suite implementation in three ways:

1. it supports both scalar and interval ``K`` values consistently;
2. it adds second-derivative force information needed for rigorous residue
   derivative bounds along a periodic branch; and
3. it separates pointwise tangent calculations from interval enclosures so
   downstream certification code can distinguish theorem-grade inclusions from
   midpoint-based diagnostics.
"""

from dataclasses import dataclass, field
from typing import Any, List, Sequence, Tuple

import mpmath as mp
import numpy as np
from scipy.optimize import root

from .interval_utils import (
    IntervalLinearSolveResult,
    iv_eye,
    iv_matmul,
    iv_matvec,
    iv_scalar,
    point_mat_to_iv,
    solve_linear_interval_fixed_point,
)

Interval = Any


@dataclass
class HarmonicFamily:
    """Generalized standard-map forcing.

    The map is written in lift form as

        r' = r + K * force(theta)
        theta' = theta + r'

    with

        force(theta) = sum_j amp_j/(2*pi*mode_j) * sin(2*pi*mode_j*theta + phase_j).

    The default choice ``[(1.0, 1, 0.0)]`` is the standard map convention used
    in the original suite, so existing notebooks continue to work.
    """

    harmonics: List[Tuple[float, int, float]] = field(default_factory=lambda: [(1.0, 1, 0.0)])

    def force(self, theta: np.ndarray | float):
        theta = np.asarray(theta, dtype=float)
        out = np.zeros_like(theta, dtype=float)
        for amp, mode, phase in self.harmonics:
            out = out + (amp / (2.0 * np.pi * mode)) * np.sin(2.0 * np.pi * mode * theta + phase)
        return out

    def dforce(self, theta: np.ndarray | float):
        theta = np.asarray(theta, dtype=float)
        out = np.zeros_like(theta, dtype=float)
        for amp, mode, phase in self.harmonics:
            out = out + amp * np.cos(2.0 * np.pi * mode * theta + phase)
        return out

    def ddforce(self, theta: np.ndarray | float):
        theta = np.asarray(theta, dtype=float)
        out = np.zeros_like(theta, dtype=float)
        for amp, mode, phase in self.harmonics:
            out = out - amp * (2.0 * np.pi * mode) * np.sin(2.0 * np.pi * mode * theta + phase)
        return out

    def force_iv(self, theta: Interval):
        out = iv_scalar(0.0)
        for amp, mode, phase in self.harmonics:
            amp_iv = iv_scalar(float(amp))
            freq_iv = iv_scalar(float(2 * np.pi * mode))
            phase_iv = iv_scalar(float(phase))
            out = out + (amp_iv / freq_iv) * mp.iv.sin(freq_iv * theta + phase_iv)
        return out

    def dforce_iv(self, theta: Interval):
        out = iv_scalar(0.0)
        for amp, mode, phase in self.harmonics:
            amp_iv = iv_scalar(float(amp))
            freq_iv = iv_scalar(float(2 * np.pi * mode))
            phase_iv = iv_scalar(float(phase))
            out = out + amp_iv * mp.iv.cos(freq_iv * theta + phase_iv)
        return out

    def ddforce_iv(self, theta: Interval):
        out = iv_scalar(0.0)
        for amp, mode, phase in self.harmonics:
            amp_iv = iv_scalar(float(amp))
            freq_iv = iv_scalar(float(2 * np.pi * mode))
            phase_iv = iv_scalar(float(phase))
            out = out - amp_iv * freq_iv * mp.iv.sin(freq_iv * theta + phase_iv)
        return out


def initial_orbit_guess(p: int, q: int) -> np.ndarray:
    return np.arange(q, dtype=float) * (p / q)


def _as_generic_array(x: Sequence[Any]) -> np.ndarray:
    arr = np.asarray(x)
    if arr.dtype == object:
        return arr.astype(object)
    return np.asarray(x, dtype=float)


def orbit_to_states(x: Sequence[Any], p: int) -> tuple[np.ndarray, np.ndarray]:
    """Return theta and r values for a lifted periodic orbit.

    The original implementation always cast to float, which broke interval use.
    This version preserves object/interval dtype when necessary.
    """
    x_arr = _as_generic_array(x)
    q = len(x_arr)
    theta = np.empty(q, dtype=object if x_arr.dtype == object else float)
    theta[:] = x_arr
    theta_next = np.empty(q, dtype=object if x_arr.dtype == object else float)
    for i in range(q - 1):
        theta_next[i] = theta[i + 1]
    theta_next[-1] = theta[0] + p
    r = np.empty(q, dtype=object if x_arr.dtype == object else float)
    for i in range(q):
        r[i] = theta_next[i] - theta[i]
    return theta, r


def periodic_orbit_residual(x: np.ndarray, p: int, K: float, family: HarmonicFamily | None = None) -> np.ndarray:
    family = family or HarmonicFamily()
    q = len(x)
    xp = np.empty(q, dtype=float)
    xm = np.empty(q, dtype=float)
    xp[:-1] = x[1:]
    xp[-1] = x[0] + p
    xm[1:] = x[:-1]
    xm[0] = x[-1] - p
    return xp - 2.0 * x + xm - K * family.force(x)


def periodic_orbit_residual_iv(X: np.ndarray, p: int, K: float | Interval, family: HarmonicFamily | None = None) -> np.ndarray:
    family = family or HarmonicFamily()
    K_iv = iv_scalar(K)
    q = len(X)
    out = np.empty(q, dtype=object)
    for i in range(q):
        xp = X[(i + 1) % q] + (p if i == q - 1 else 0)
        xm = X[(i - 1) % q] - (p if i == 0 else 0)
        out[i] = xp - 2 * X[i] + xm - K_iv * family.force_iv(X[i])
    return out


def periodic_orbit_jacobian(x: np.ndarray, p: int, K: float, family: HarmonicFamily | None = None) -> np.ndarray:
    family = family or HarmonicFamily()
    q = len(x)
    J = np.zeros((q, q), dtype=float)
    diag = -2.0 - K * family.dforce(x)
    idx = np.arange(q)
    J[idx, idx] = diag
    J[idx[:-1], idx[1:]] = 1.0
    J[idx[1:], idx[:-1]] = 1.0
    J[0, -1] = 1.0
    J[-1, 0] = 1.0
    return J


def periodic_orbit_jacobian_iv(X: np.ndarray, p: int, K: float | Interval, family: HarmonicFamily | None = None) -> np.ndarray:
    family = family or HarmonicFamily()
    K_iv = iv_scalar(K)
    q = len(X)
    J = np.empty((q, q), dtype=object)
    zero = iv_scalar(0.0)
    one = iv_scalar(1.0)
    two = iv_scalar(2.0)
    for i in range(q):
        for j in range(q):
            J[i, j] = zero
    for i in range(q):
        J[i, i] = -two - K_iv * family.dforce_iv(X[i])
        J[i, (i + 1) % q] = J[i, (i + 1) % q] + one
        J[i, (i - 1) % q] = J[i, (i - 1) % q] + one
    return J


def periodic_orbit_partial_K(x: np.ndarray, family: HarmonicFamily | None = None) -> np.ndarray:
    family = family or HarmonicFamily()
    return family.force(np.asarray(x, dtype=float))


def periodic_orbit_partial_K_iv(X: np.ndarray, family: HarmonicFamily | None = None) -> np.ndarray:
    family = family or HarmonicFamily()
    return np.array([family.force_iv(th) for th in X], dtype=object)




def _cyclic_tridiagonal_components(x: np.ndarray, K: float, family: HarmonicFamily) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    q = len(x)
    diag = -2.0 - K * family.dforce(x)
    off = np.ones(max(q - 1, 0), dtype=float)
    return diag, off.copy(), off.copy()


def _tridiagonal_solve(lower: np.ndarray, diag: np.ndarray, upper: np.ndarray, rhs: np.ndarray) -> np.ndarray:
    q = len(diag)
    rhs = np.asarray(rhs, dtype=float)
    if q == 1:
        return np.asarray([rhs[0] / diag[0]], dtype=float)
    cprime = np.zeros(q - 1, dtype=float)
    dprime = np.zeros(q, dtype=float)
    denom = float(diag[0])
    cprime[0] = float(upper[0]) / denom
    dprime[0] = rhs[0] / denom
    for i in range(1, q - 1):
        denom = float(diag[i]) - float(lower[i - 1]) * cprime[i - 1]
        cprime[i] = float(upper[i]) / denom
        dprime[i] = (rhs[i] - float(lower[i - 1]) * dprime[i - 1]) / denom
    denom = float(diag[-1]) - float(lower[-1]) * cprime[-1]
    dprime[-1] = (rhs[-1] - float(lower[-1]) * dprime[-2]) / denom
    x = np.zeros(q, dtype=float)
    x[-1] = dprime[-1]
    for i in range(q - 2, -1, -1):
        x[i] = dprime[i] - cprime[i] * x[i + 1]
    return x


def _solve_cyclic_tridiagonal(lower: np.ndarray, diag: np.ndarray, upper: np.ndarray, rhs: np.ndarray) -> np.ndarray:
    """Solve a cyclic tridiagonal linear system via Sherman--Morrison.

    The matrix has diagonals ``diag``, subdiagonal ``lower``, superdiagonal
    ``upper``, and corner entries ``A[0,-1]=upper[-1]`` and
    ``A[-1,0]=lower[0]``.
    """
    q = len(diag)
    rhs = np.asarray(rhs, dtype=float)
    if q == 1:
        return np.asarray([rhs[0] / diag[0]], dtype=float)
    if q == 2:
        A = np.array([[diag[0], upper[0] + lower[0]], [upper[0] + lower[0], diag[1]]], dtype=float)
        return np.linalg.solve(A, rhs)

    alpha = float(upper[-1])
    beta = float(lower[0])
    gamma = -float(diag[0]) if abs(float(diag[0])) > 1e-14 else -1.0

    diag_t = np.asarray(diag, dtype=float).copy()
    diag_t[0] -= gamma
    diag_t[-1] -= (alpha * beta) / gamma

    lower_t = np.asarray(lower, dtype=float).copy()
    upper_t = np.asarray(upper, dtype=float).copy()

    y = _tridiagonal_solve(lower_t, diag_t, upper_t, rhs)
    u = np.zeros(q, dtype=float)
    u[0] = gamma
    u[-1] = beta
    z = _tridiagonal_solve(lower_t, diag_t, upper_t, u)

    denom = 1.0 + z[0] + (alpha / gamma) * z[-1]
    if abs(denom) < 1e-18:
        A = np.zeros((q, q), dtype=float)
        idx = np.arange(q)
        A[idx, idx] = diag
        A[idx[:-1], idx[1:]] = upper[:-1]
        A[idx[1:], idx[:-1]] = lower[1:]
        A[0, -1] = alpha
        A[-1, 0] = beta
        return np.linalg.solve(A, rhs)
    fact = (y[0] + (alpha / gamma) * y[-1]) / denom
    return y - fact * z


def _periodic_orbit_newton_structured(
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily,
    x0: np.ndarray,
    *,
    tol: float = 1e-13,
    max_iter: int = 40,
) -> dict:
    x = np.asarray(x0, dtype=float).copy()
    if x.shape != (q,):
        x = np.resize(x, q).astype(float)
    residual = periodic_orbit_residual(x, p, K, family)
    residual_inf = float(np.max(np.abs(residual)))
    if residual_inf < tol:
        return {
            "success": True,
            "message": "structured-newton converged immediately",
            "x": x,
            "residual_inf": residual_inf,
            "residual_l2": float(np.linalg.norm(residual)),
            "nfev": 1,
            "solver": "structured-newton",
            "iterations": 0,
        }

    for it in range(1, max_iter + 1):
        diag, lower, upper = _cyclic_tridiagonal_components(x, K, family)
        try:
            if q <= 16:
                step = np.linalg.solve(periodic_orbit_jacobian(x, p, K, family), -residual)
            else:
                step = _solve_cyclic_tridiagonal(lower, diag, upper, -residual)
            if not np.all(np.isfinite(step)):
                raise FloatingPointError("non-finite Newton step")
        except Exception as exc:
            return {
                "success": False,
                "message": f"structured-newton linear solve failed: {exc}",
                "x": x,
                "residual_inf": residual_inf,
                "residual_l2": float(np.linalg.norm(residual)),
                "nfev": it,
                "solver": "structured-newton",
                "iterations": it - 1,
            }

        step_inf = float(np.max(np.abs(step)))
        alpha = 1.0
        accepted = False
        best_x = x
        best_residual = residual
        best_residual_inf = residual_inf
        for _ in range(8):
            trial_x = x + alpha * step
            trial_residual = periodic_orbit_residual(trial_x, p, K, family)
            trial_inf = float(np.max(np.abs(trial_residual)))
            if trial_inf <= residual_inf * (1.0 - 1e-4 * alpha) or trial_inf < tol:
                best_x = trial_x
                best_residual = trial_residual
                best_residual_inf = trial_inf
                accepted = True
                break
            if trial_inf < best_residual_inf:
                best_x = trial_x
                best_residual = trial_residual
                best_residual_inf = trial_inf
            alpha *= 0.5

        x = best_x
        residual = best_residual
        residual_inf = best_residual_inf
        if residual_inf < tol or step_inf * alpha < max(tol * 0.1, 1e-15):
            return {
                "success": residual_inf < max(tol, 1e-12),
                "message": "structured-newton converged" if residual_inf < max(tol, 1e-12) else "structured-newton stalled near tolerance",
                "x": x,
                "residual_inf": residual_inf,
                "residual_l2": float(np.linalg.norm(residual)),
                "nfev": it + 1,
                "solver": "structured-newton",
                "iterations": it,
            }
        if not accepted and residual_inf > 1e2:
            break

    return {
        "success": residual_inf < max(tol, 1e-10),
        "message": "structured-newton reached iteration limit",
        "x": x,
        "residual_inf": residual_inf,
        "residual_l2": float(np.linalg.norm(residual)),
        "nfev": max_iter + 1,
        "solver": "structured-newton",
        "iterations": max_iter,
    }


def _mp_force(theta: Any, family: HarmonicFamily) -> Any:
    out = mp.mpf('0')
    for amp, mode, phase in family.harmonics:
        out += (mp.mpf(str(amp)) / (2 * mp.pi * int(mode))) * mp.sin(2 * mp.pi * int(mode) * theta + mp.mpf(str(phase)))
    return out


def _mp_dforce(theta: Any, family: HarmonicFamily) -> Any:
    out = mp.mpf('0')
    for amp, mode, phase in family.harmonics:
        out += mp.mpf(str(amp)) * mp.cos(2 * mp.pi * int(mode) * theta + mp.mpf(str(phase)))
    return out


def _mp_periodic_orbit_residual(x: list[Any], p: int, K: float, family: HarmonicFamily) -> list[Any]:
    q = len(x)
    K_mp = mp.mpf(str(K))
    out = []
    for i in range(q):
        xp = x[(i + 1) % q] + (p if i == q - 1 else 0)
        xm = x[(i - 1) % q] - (p if i == 0 else 0)
        out.append(xp - 2 * x[i] + xm - K_mp * _mp_force(x[i], family))
    return out


def _mp_solve_cyclic_tridiagonal(diag: list[Any], rhs: list[Any], K: float, x: list[Any], family: HarmonicFamily) -> list[Any]:
    q = len(diag)
    if q == 1:
        return [rhs[0] / diag[0]]
    if q == 2:
        a00 = diag[0]
        a01 = mp.mpf('2.0')
        a10 = mp.mpf('2.0')
        a11 = diag[1]
        det = a00 * a11 - a01 * a10
        return [(rhs[0] * a11 - a01 * rhs[1]) / det, (a00 * rhs[1] - rhs[0] * a10) / det]
    lower = [mp.mpf('1.0')] * (q - 1)
    upper = [mp.mpf('1.0')] * (q - 1)
    alpha = mp.mpf('1.0')
    beta = mp.mpf('1.0')
    gamma = -diag[0] if abs(diag[0]) > mp.mpf('1e-40') else mp.mpf('-1.0')
    d = list(diag)
    d[0] -= gamma
    d[-1] -= alpha * beta / gamma

    def tri_solve(dv, b):
        c = [mp.mpf('0.0')] * (q - 1)
        dprime = [mp.mpf('0.0')] * q
        c[0] = upper[0] / dv[0]
        dprime[0] = b[0] / dv[0]
        for i in range(1, q - 1):
            denom = dv[i] - lower[i - 1] * c[i - 1]
            c[i] = upper[i] / denom
            dprime[i] = (b[i] - lower[i - 1] * dprime[i - 1]) / denom
        denom = dv[-1] - lower[-1] * c[-1]
        dprime[-1] = (b[-1] - lower[-1] * dprime[-2]) / denom
        xout = [mp.mpf('0.0')] * q
        xout[-1] = dprime[-1]
        for i in range(q - 2, -1, -1):
            xout[i] = dprime[i] - c[i] * xout[i + 1] if i < q - 1 else dprime[i]
        return xout

    y = tri_solve(d, rhs)
    u = [mp.mpf('0.0')] * q
    u[0] = gamma
    u[-1] = beta
    z = tri_solve(d, u)
    denom = 1 + z[0] + alpha * z[-1] / gamma
    fact = (y[0] + alpha * y[-1] / gamma) / denom
    return [yy - fact * zz for yy, zz in zip(y, z)]


def _solve_periodic_orbit_high_precision(
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily,
    x0: np.ndarray,
    *,
    dps: int = 160,
    max_iter: int = 20,
) -> dict:
    with mp.workdps(int(dps)):
        x = [mp.mpf(str(v)) for v in np.asarray(x0, dtype=float)]
        for it in range(1, max_iter + 1):
            residual = _mp_periodic_orbit_residual(x, p, K, family)
            residual_inf = max(abs(v) for v in residual)
            if residual_inf < mp.mpf('1e-40'):
                x_float = np.array([float(v) for v in x], dtype=float)
                res_float = periodic_orbit_residual(x_float, p, K, family)
                return {
                    "success": True,
                    "message": f"high-precision-newton converged at {dps} dps",
                    "x": x_float,
                    "residual_inf": float(np.max(np.abs(res_float))),
                    "residual_l2": float(np.linalg.norm(res_float)),
                    "nfev": it,
                    "solver": "high-precision-newton",
                    "iterations": it,
                    "dps": int(dps),
                }
            diag = [mp.mpf('-2.0') - mp.mpf(str(K)) * _mp_dforce(xx, family) for xx in x]
            step = _mp_solve_cyclic_tridiagonal(diag, [-v for v in residual], K, x, family)
            alpha = mp.mpf('1.0')
            cur_inf = residual_inf
            accepted = False
            for _ in range(8):
                trial = [xx + alpha * dx for xx, dx in zip(x, step)]
                trial_res = _mp_periodic_orbit_residual(trial, p, K, family)
                trial_inf = max(abs(v) for v in trial_res)
                if trial_inf < cur_inf:
                    x = trial
                    accepted = True
                    break
                alpha *= mp.mpf('0.5')
            if not accepted:
                break
        x_float = np.array([float(v) for v in x], dtype=float)
        res_float = periodic_orbit_residual(x_float, p, K, family)
        return {
            "success": float(np.max(np.abs(res_float))) < 1e-10,
            "message": f"high-precision-newton stopped at {dps} dps",
            "x": x_float,
            "residual_inf": float(np.max(np.abs(res_float))),
            "residual_l2": float(np.linalg.norm(res_float)),
            "nfev": max_iter,
            "solver": "high-precision-newton",
            "iterations": max_iter,
            "dps": int(dps),
        }

def periodic_orbit_derivative_K(
    x: np.ndarray,
    p: int,
    K: float,
    family: HarmonicFamily | None = None,
) -> np.ndarray:
    family = family or HarmonicFamily()
    J = periodic_orbit_jacobian(np.asarray(x, dtype=float), p, K, family)
    rhs = periodic_orbit_partial_K(np.asarray(x, dtype=float), family)
    return np.linalg.solve(J, rhs)


def periodic_orbit_derivative_K_iv(
    x_iv: np.ndarray,
    p: int,
    K: float | Interval,
    family: HarmonicFamily | None = None,
) -> IntervalLinearSolveResult:
    """Validated enclosure for ``dx/dK`` using the implicit function theorem."""
    family = family or HarmonicFamily()
    Df_x = periodic_orbit_jacobian_iv(x_iv, p, K, family)
    rhs = periodic_orbit_partial_K_iv(x_iv, family)
    return solve_linear_interval_fixed_point(Df_x, rhs)


def solve_periodic_orbit(
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily | None = None,
    x0: np.ndarray | None = None,
    tol: float = 1e-13,
    maxfev: int = 20000,
) -> dict:
    family = family or HarmonicFamily()
    x0 = initial_orbit_guess(p, q) if x0 is None else np.asarray(x0, dtype=float)

    def fun(x):
        return periodic_orbit_residual(x, p, K, family)

    def jac(x):
        return periodic_orbit_jacobian(x, p, K, family)

    sol = root(fun, x0, jac=jac, method="hybr", options={"maxfev": maxfev, "xtol": tol})
    x = np.asarray(sol.x, dtype=float)
    res = fun(x)
    return {
        "success": bool(sol.success),
        "message": str(sol.message),
        "x": x,
        "residual_inf": float(np.max(np.abs(res))),
        "residual_l2": float(np.linalg.norm(res)),
        "nfev": int(sol.nfev),
    }


def continue_periodic_orbit(
    p: int,
    q: int,
    K_target: float,
    family: HarmonicFamily | None = None,
    K_start: float = 0.0,
    n_steps: int = 48,
    max_refine: int = 8,
    min_step: float = 1e-5,
    x_start: np.ndarray | None = None,
) -> dict:
    family = family or HarmonicFamily()
    x_curr = initial_orbit_guess(p, q) if x_start is None else np.asarray(x_start, dtype=float)
    start = solve_periodic_orbit(p, q, K_start, family, x0=x_curr)
    if not start["success"]:
        return start
    x_curr = start["x"]
    if abs(K_target - K_start) < 1e-15:
        return start

    direction = 1.0 if K_target >= K_start else -1.0
    total = abs(K_target - K_start)
    step = max(total / max(n_steps, 1), min_step)
    step = min(step, total)
    K_curr = float(K_start)
    last = start
    refinements = 0

    while direction * (K_target - K_curr) > 1e-15:
        K_next = K_curr + direction * min(step, abs(K_target - K_curr))
        sol = solve_periodic_orbit(p, q, float(K_next), family, x0=x_curr)
        if sol["success"]:
            x_curr = sol["x"]
            K_curr = float(K_next)
            last = sol
            if refinements > 0:
                refinements -= 1
            step = min(step * 1.25, total)
        else:
            step *= 0.5
            refinements += 1
            if step < min_step or refinements > max_refine * 8:
                msg = (
                    f"continuation failed near K={K_next:.9f}; "
                    f"last successful K={K_curr:.9f}; "
                    f"residual={sol['residual_inf']:.3e}"
                )
                return {**sol, "message": msg}
    return last


def monodromy_step_matrix(theta: float, K: float, family: HarmonicFamily | None = None) -> np.ndarray:
    family = family or HarmonicFamily()
    a = K * family.dforce(np.array([theta], dtype=float))[0]
    return np.array([[1.0 + a, 1.0], [a, 1.0]], dtype=float)


def monodromy_step_matrix_iv(theta: Interval, K: float | Interval, family: HarmonicFamily | None = None) -> np.ndarray:
    family = family or HarmonicFamily()
    one = iv_scalar(1.0)
    K_iv = iv_scalar(K)
    a = K_iv * family.dforce_iv(theta)
    return np.array([[one + a, one], [a, one]], dtype=object)


def monodromy_matrix(x: np.ndarray, p: int, K: float, family: HarmonicFamily | None = None) -> np.ndarray:
    family = family or HarmonicFamily()
    theta, _ = orbit_to_states(x, p)
    M = np.eye(2)
    for th in theta:
        M = monodromy_step_matrix(float(th), K, family) @ M
    return M


def monodromy_interval_from_orbit_box(X: np.ndarray, p: int, K: float | Interval, family: HarmonicFamily | None = None):
    family = family or HarmonicFamily()
    M = iv_eye(2)
    for th in X:
        J = monodromy_step_matrix_iv(th, K, family)
        M = iv_matmul(J, M)
    return M


def greene_residue(x: np.ndarray, p: int, K: float, family: HarmonicFamily | None = None) -> float:
    M = monodromy_matrix(x, p, K, family)
    return float((2.0 - np.trace(M)) / 4.0)


def greene_residue_iv(X: np.ndarray, p: int, K: float | Interval, family: HarmonicFamily | None = None):
    M = monodromy_interval_from_orbit_box(X, p, K, family)
    tr = M[0, 0] + M[1, 1]
    return (iv_scalar(2.0) - tr) / 4


def residue_derivative(
    x: np.ndarray,
    p: int,
    K: float,
    family: HarmonicFamily | None = None,
) -> float:
    family = family or HarmonicFamily()
    theta, _ = orbit_to_states(x, p)
    dx_dK = periodic_orbit_derivative_K(np.asarray(x, dtype=float), p, K, family)

    J_list = [monodromy_step_matrix(float(th), K, family) for th in theta]
    dJ_list = []
    for th, dth in zip(theta, dx_dK):
        da = family.dforce(np.array([th], dtype=float))[0] + K * family.ddforce(np.array([th], dtype=float))[0] * dth
        dJ_list.append(np.array([[da, 0.0], [da, 0.0]], dtype=float))

    prefix = [np.eye(2)]
    for J in J_list:
        prefix.append(J @ prefix[-1])

    dM = np.zeros((2, 2), dtype=float)
    suffix = np.eye(2)
    for i in reversed(range(len(J_list))):
        dM = dM + suffix @ dJ_list[i] @ prefix[i]
        suffix = suffix @ J_list[i]

    return float(-0.25 * np.trace(dM))


def residue_derivative_iv(
    x_iv: np.ndarray,
    p: int,
    K: float | Interval,
    family: HarmonicFamily | None = None,
):
    family = family or HarmonicFamily()
    K_iv = iv_scalar(K)
    dx_res = periodic_orbit_derivative_K_iv(x_iv, p, K_iv, family)
    dx_dK_iv = dx_res.x_iv

    J_list = [monodromy_step_matrix_iv(th, K_iv, family) for th in x_iv]
    dJ_list = []
    for th, dth in zip(x_iv, dx_dK_iv):
        da = family.dforce_iv(th) + K_iv * family.ddforce_iv(th) * dth
        zero = iv_scalar(0.0)
        dJ_list.append(np.array([[da, zero], [da, zero]], dtype=object))

    prefix = [iv_eye(2)]
    for J in J_list:
        prefix.append(iv_matmul(J, prefix[-1]))

    dM = np.empty((2, 2), dtype=object)
    for i in range(2):
        for j in range(2):
            dM[i, j] = iv_scalar(0.0)

    suffix = iv_eye(2)
    for i in reversed(range(len(J_list))):
        dM = dM + iv_matmul(iv_matmul(suffix, dJ_list[i]), prefix[i])
        suffix = iv_matmul(suffix, J_list[i])

    tr_dM = dM[0, 0] + dM[1, 1]
    return -0.25 * tr_dM, dx_res
