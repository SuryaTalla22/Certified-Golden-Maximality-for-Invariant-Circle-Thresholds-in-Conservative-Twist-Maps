from __future__ import annotations

"""Parameterized periodic-branch enclosures.

The original suite validated isolated periodic orbits very well, but it did not
provide a reusable object representing a *window* in parameter space along a
tracked periodic branch. This module fills that gap.

The resulting tube is intentionally conservative. It combines:

- continuation to the left and right endpoints of a ``K``-window,
- a midpoint tangent calculation ``dx/dK``,
- optional interval tangent bounds via midpoint-preconditioned Krawczyk, and
- a final hull/inflation step that encloses the branch over the window.

This is not yet a final theorem-level family validator, but it gives the rest of
this bundle a concrete, inspectable object on which residue and derivative
bounds can be evaluated.
"""

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np

from .interval_utils import (
    inflate_interval,
    interval_mag,
    interval_width,
    iv_scalar,
)
from .standard_map import (
    HarmonicFamily,
    continue_periodic_orbit,
    periodic_orbit_derivative_K,
    periodic_orbit_derivative_K_iv,
    periodic_orbit_residual_iv,
    solve_periodic_orbit,
)


@dataclass
class BranchTube:
    p: int
    q: int
    K_lo: float
    K_hi: float
    K_mid: float
    x_mid: np.ndarray
    x_left: np.ndarray
    x_right: np.ndarray
    x_iv: np.ndarray
    branch_residual_width: float
    slope_center_inf: float
    interval_tangent_success: bool
    interval_tangent_contraction: float
    message: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for key in ("x_mid", "x_left", "x_right"):
            d[key] = np.asarray(d[key], dtype=float).tolist()
        d["x_iv_bounds"] = [(float(v.a), float(v.b)) for v in self.x_iv]
        # Backward-compatible aliases used by earlier notebooks.
        d["max_endpoint_radius"] = float(max(abs(float(hi) - float(lo)) for lo, hi in d["x_iv_bounds"]) / 2.0)
        d["tube_sup_width"] = float(max(float(hi) - float(lo) for lo, hi in d["x_iv_bounds"]))
        del d["x_iv"]
        return d


def _solve_or_continue(
    p: int,
    q: int,
    K_target: float,
    family: HarmonicFamily,
    *,
    K_start: float,
    x_start: np.ndarray | None,
) -> dict:
    if x_start is not None:
        cont = continue_periodic_orbit(
            p=p,
            q=q,
            K_target=K_target,
            family=family,
            K_start=K_start,
            x_start=x_start,
            n_steps=max(16, int(abs(K_target - K_start) / 5e-4)),
        )
        if cont["success"]:
            return cont
        retry = solve_periodic_orbit(p=p, q=q, K=K_target, family=family, x0=x_start)
        if retry["success"]:
            return retry
    return continue_periodic_orbit(p=p, q=q, K_target=K_target, family=family, K_start=0.0, n_steps=64)


def build_branch_tube(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    x_guess: np.ndarray | None = None,
    *,
    inflate_rel: float = 5e-10,
    inflate_abs: float = 1e-12,
) -> BranchTube:
    family = family or HarmonicFamily()
    K_lo = float(K_lo)
    K_hi = float(K_hi)
    if K_lo > K_hi:
        K_lo, K_hi = K_hi, K_lo
    K_mid = 0.5 * (K_lo + K_hi)
    half_width = 0.5 * (K_hi - K_lo)

    mid_sol = _solve_or_continue(p, q, K_mid, family, K_start=0.0, x_start=x_guess)
    if not mid_sol["success"]:
        raise RuntimeError(f"Could not solve midpoint orbit at K={K_mid}: {mid_sol['message']}")
    x_mid = np.asarray(mid_sol["x"], dtype=float)

    left_sol = _solve_or_continue(p, q, K_lo, family, K_start=K_mid, x_start=x_mid)
    right_sol = _solve_or_continue(p, q, K_hi, family, K_start=K_mid, x_start=x_mid)
    if not left_sol["success"] or not right_sol["success"]:
        msg = []
        if not left_sol["success"]:
            msg.append(f"left continuation failed: {left_sol['message']}")
        if not right_sol["success"]:
            msg.append(f"right continuation failed: {right_sol['message']}")
        raise RuntimeError("; ".join(msg))

    x_left = np.asarray(left_sol["x"], dtype=float)
    x_right = np.asarray(right_sol["x"], dtype=float)
    slope_center = periodic_orbit_derivative_K(x_mid, p, K_mid, family)
    slope_center_inf = float(np.linalg.norm(slope_center, ord=np.inf))

    # Start from the endpoint hull and then enlarge using the midpoint slope.
    x_iv = np.empty(q, dtype=object)
    for i in range(q):
        lo = min(x_left[i], x_right[i], x_mid[i] - abs(slope_center[i]) * half_width)
        hi = max(x_left[i], x_right[i], x_mid[i] + abs(slope_center[i]) * half_width)
        x_iv[i] = inflate_interval(iv_scalar(lo, hi), rel=inflate_rel, abs_eps=inflate_abs)

    tangent_res = periodic_orbit_derivative_K_iv(x_iv, p, iv_scalar(K_lo, K_hi), family)
    if tangent_res.success:
        # If an interval tangent was proved, widen the tube accordingly.
        for i in range(q):
            mag = interval_mag(tangent_res.x_iv[i])
            lo = min(float(x_iv[i].a), x_mid[i] - mag * half_width)
            hi = max(float(x_iv[i].b), x_mid[i] + mag * half_width)
            x_iv[i] = inflate_interval(iv_scalar(lo, hi), rel=inflate_rel, abs_eps=inflate_abs)

    residual_box = periodic_orbit_residual_iv(x_iv, p, iv_scalar(K_lo, K_hi), family)
    residual_width = float(max(interval_width(v) for v in residual_box))
    msg = "built from midpoint solve + endpoint continuation"
    if tangent_res.success:
        msg += "; interval tangent inclusion succeeded"
    else:
        msg += "; interval tangent inclusion did not close"

    return BranchTube(
        p=p,
        q=q,
        K_lo=K_lo,
        K_hi=K_hi,
        K_mid=K_mid,
        x_mid=x_mid,
        x_left=x_left,
        x_right=x_right,
        x_iv=x_iv,
        branch_residual_width=residual_width,
        slope_center_inf=slope_center_inf,
        interval_tangent_success=bool(tangent_res.success),
        interval_tangent_contraction=float(tangent_res.contraction_bound),
        message=msg,
    )
