from __future__ import annotations

"""Interval-arithmetic helpers used by the proof-oriented certification code.

The original suite duplicated several interval helpers inside ``certification.py``.
This module centralizes those operations and adds a lightweight validated solver
for linear systems of the form ``A x = b`` where ``A`` and ``b`` are represented
by interval enclosures.

The solver is intentionally modest: it uses midpoint preconditioning and a
Krawczyk/fixed-point enclosure iteration. When the contraction test is weak the
function returns ``success=False`` together with a conservative box. This keeps
failure modes explicit instead of silently returning over-optimistic intervals.
"""

from dataclasses import dataclass
from typing import Any, Iterable

import mpmath as mp
import numpy as np

Interval = Any


@dataclass
class IntervalLinearSolveResult:
    success: bool
    x_iv: np.ndarray
    message: str
    contraction_bound: float
    iterations: int


def iv_scalar(lo: float | mp.mpf | Interval, hi: float | mp.mpf | None = None):
    if hi is None:
        if hasattr(lo, "a") and hasattr(lo, "b"):
            return lo
        return mp.iv.mpf([float(lo), float(lo)])
    return mp.iv.mpf([float(lo), float(hi)])


def point_vec_to_iv(x: Iterable[float]) -> np.ndarray:
    return np.array([iv_scalar(v) for v in x], dtype=object)


def point_mat_to_iv(A: np.ndarray) -> np.ndarray:
    out = np.empty_like(A, dtype=object)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            out[i, j] = iv_scalar(A[i, j])
    return out


def iv_vec(center: np.ndarray, radius: float | np.ndarray) -> np.ndarray:
    center = np.asarray(center, dtype=float)
    if np.isscalar(radius):
        radius = np.full_like(center, float(radius), dtype=float)
    radius = np.asarray(radius, dtype=float)
    return np.array([iv_scalar(c - r, c + r) for c, r in zip(center, radius)], dtype=object)


def interval_mid(x: Interval) -> float:
    return 0.5 * (float(x.a) + float(x.b))


def interval_rad(x: Interval) -> float:
    return 0.5 * (float(x.b) - float(x.a))


def interval_width(x: Interval) -> float:
    return float(x.b) - float(x.a)


def interval_mag(x: Interval) -> float:
    return max(abs(float(x.a)), abs(float(x.b)))


def midpoint_vec(X: np.ndarray) -> np.ndarray:
    return np.array([interval_mid(x) for x in X], dtype=float)


def midpoint_mat(A: np.ndarray) -> np.ndarray:
    out = np.empty(A.shape, dtype=float)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            out[i, j] = interval_mid(A[i, j])
    return out


def iv_eye(n: int) -> np.ndarray:
    out = np.empty((n, n), dtype=object)
    for i in range(n):
        for j in range(n):
            out[i, j] = iv_scalar(1.0 if i == j else 0.0)
    return out


def iv_zeros(shape: tuple[int, ...]) -> np.ndarray:
    out = np.empty(shape, dtype=object)
    for idx in np.ndindex(shape):
        out[idx] = iv_scalar(0.0)
    return out


def interval_hull(a: Interval, b: Interval):
    return iv_scalar(min(float(a.a), float(b.a)), max(float(a.b), float(b.b)))


def hull_vec(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.array([interval_hull(a, b) for a, b in zip(A, B)], dtype=object)


def inflate_interval(x: Interval, rel: float = 1e-12, abs_eps: float = 1e-30):
    mid = interval_mid(x)
    rad = interval_rad(x)
    extra = max(abs_eps, rel * max(1.0, abs(mid), rad))
    return iv_scalar(mid - rad - extra, mid + rad + extra)


def inflate_vec(X: np.ndarray, rel: float = 1e-12, abs_eps: float = 1e-30) -> np.ndarray:
    return np.array([inflate_interval(x, rel=rel, abs_eps=abs_eps) for x in X], dtype=object)


def subset_interval(a: Interval, b: Interval, strict: bool = False) -> bool:
    if strict:
        return float(a.a) > float(b.a) and float(a.b) < float(b.b)
    return float(a.a) >= float(b.a) and float(a.b) <= float(b.b)


def vec_subset(A: np.ndarray, B: np.ndarray, strict: bool = False) -> bool:
    return all(subset_interval(a, b, strict=strict) for a, b in zip(A, B))


def iv_matmul(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    m, n = A.shape
    n2, p = B.shape
    if n != n2:
        raise ValueError("shape mismatch in iv_matmul")
    out = np.empty((m, p), dtype=object)
    for i in range(m):
        for j in range(p):
            s = iv_scalar(0.0)
            for k in range(n):
                s = s + A[i, k] * B[k, j]
            out[i, j] = s
    return out


def iv_matvec(A: np.ndarray, x: np.ndarray) -> np.ndarray:
    m, n = A.shape
    if n != len(x):
        raise ValueError("shape mismatch in iv_matvec")
    out = np.empty(m, dtype=object)
    for i in range(m):
        s = iv_scalar(0.0)
        for k in range(n):
            s = s + A[i, k] * x[k]
        out[i] = s
    return out


def point_mat_iv_matmul(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return iv_matmul(point_mat_to_iv(np.asarray(A, dtype=float)), B)


def point_mat_iv_vecmul(A: np.ndarray, x: np.ndarray) -> np.ndarray:
    return iv_matvec(point_mat_to_iv(np.asarray(A, dtype=float)), x)


def mag_matrix(A: np.ndarray) -> np.ndarray:
    out = np.empty(A.shape, dtype=float)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            out[i, j] = interval_mag(A[i, j])
    return out


def mag_vec(x: np.ndarray) -> np.ndarray:
    return np.array([interval_mag(v) for v in x], dtype=float)


def solve_linear_interval_fixed_point(
    A_iv: np.ndarray,
    b_iv: np.ndarray,
    *,
    max_iter: int = 40,
    inflation_rel: float = 1e-12,
    inflation_abs: float = 1e-30,
) -> IntervalLinearSolveResult:
    """Validated enclosure for ``A x = b`` using midpoint preconditioning.

    The method computes a midpoint preconditioner ``C = mid(A)^{-1}``, forms the
    affine Krawczyk-style map

        y = z + R y,    z = C (b - A x0),   R = I - C A,

    around the midpoint solution ``x0 = C mid(b)`` and then iterates a box for
    ``y`` until inclusion is achieved. When the iteration does not contract the
    function still returns the final conservative box, but flags ``success`` as
    false.
    """

    A_mid = midpoint_mat(A_iv)
    b_mid = midpoint_vec(b_iv)
    try:
        C = np.linalg.inv(A_mid)
    except np.linalg.LinAlgError:
        n = len(b_mid)
        return IntervalLinearSolveResult(
            success=False,
            x_iv=iv_vec(np.zeros(n), np.full(n, np.inf)),
            message="midpoint matrix singular",
            contraction_bound=float("inf"),
            iterations=0,
        )

    x0 = C @ b_mid
    x0_iv = point_vec_to_iv(x0)
    C_iv = point_mat_to_iv(C)
    z = point_mat_iv_vecmul(C, b_iv - iv_matvec(A_iv, x0_iv))
    R = iv_eye(A_iv.shape[0]) - point_mat_iv_matmul(C, A_iv)
    R_mag = mag_matrix(R)
    contraction = float(np.linalg.norm(R_mag, ord=np.inf))

    Y = inflate_vec(z, rel=inflation_rel, abs_eps=inflation_abs)
    for it in range(1, max_iter + 1):
        new_Y = z + iv_matvec(R, Y)
        if vec_subset(new_Y, Y, strict=False):
            X = x0_iv + Y
            return IntervalLinearSolveResult(
                success=True,
                x_iv=X,
                message="interval fixed-point inclusion succeeded",
                contraction_bound=contraction,
                iterations=it,
            )
        Y = inflate_vec(hull_vec(Y, new_Y), rel=inflation_rel, abs_eps=inflation_abs)

    X = x0_iv + Y
    msg = "interval fixed-point iteration did not prove inclusion"
    if contraction >= 1.0:
        msg += f" (contraction bound={contraction:.3e} >= 1)"
    return IntervalLinearSolveResult(
        success=False,
        x_iv=X,
        message=msg,
        contraction_bound=contraction,
        iterations=max_iter,
    )
