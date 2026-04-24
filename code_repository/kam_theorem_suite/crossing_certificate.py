from __future__ import annotations

"""Theorem-like scalar crossing certificates on validated periodic windows.

This module strengthens the earlier bridge from two directions:

1. it upgrades endpoint information from raw scans to *validated endpoint
   residue certificates* using the periodic-orbit Krawczyk machinery already
   present in :mod:`certification`;
2. it packages a monotonicity-plus-interval-Newton argument for the scalar
   crossing function

       g(K) = |R_{p/q}(K)| - target,

   over a parameter window.

The point is not to claim a finished universal nonexistence theorem. The point
is to turn the current residue/branch infrastructure into a reusable,
inspectable proof object saying:

- the endpoints are on opposite sides of the target residue level;
- ``g'(K)`` has a certified one-sided sign over the entire window; and
- optionally, interval Newton refines the unique root to a smaller certified
  subwindow.

That is the strongest theorem-like local statement the current bundle can make
honestly about a rational residue crossing.
"""

from dataclasses import asdict, dataclass
from typing import Any

import mpmath as mp
import numpy as np

from .branch_tube import build_branch_tube
from .interval_newton_scalar import build_scalar_interval_newton_certificate
from .residue_branch import adaptive_localize_residue_crossing
from .certification import (
    _recenter_orbit_guess,
    get_residue_and_derivative_iv,
    propose_local_crossing_window,
    scan_branch_for_crossing,
    validate_periodic_orbit,
)
from .interval_utils import iv_scalar
from .standard_map import HarmonicFamily


@dataclass
class EndpointResidueCertificate:
    p: int
    q: int
    K: float
    target_residue: float
    success: bool
    side: str
    unique_orbit: bool
    validation_status: str
    radius: float
    residual_inf: float
    residual_l2: float
    residue_interval_lo: float | None
    residue_interval_hi: float | None
    abs_residue_interval_lo: float | None
    abs_residue_interval_hi: float | None
    signed_gap_interval_lo: float | None
    signed_gap_interval_hi: float | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MidpointNewtonCertificate:
    success: bool
    K_mid: float
    I_lo: float
    I_hi: float
    g_mid_lo: float | None
    g_mid_hi: float | None
    gprime_lo: float | None
    gprime_hi: float | None
    newton_image_lo: float | None
    newton_image_hi: float | None
    refined_lo: float | None
    refined_hi: float | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UniqueCrossingCertificate:
    p: int
    q: int
    K_lo: float
    K_hi: float
    target_residue: float
    localization_scan_used: bool
    endpoint_left: dict[str, Any]
    endpoint_right: dict[str, Any]
    midpoint: dict[str, Any]
    branch_summary: dict[str, Any]
    derivative_sign: str
    derivative_away_from_zero: bool
    strict_sign_change: bool
    monotone_unique_crossing: bool
    interval_newton: dict[str, Any]
    certified_root_window_lo: float | None
    certified_root_window_hi: float | None
    supercritical_barrier_lo: float | None
    supercritical_barrier_hi: float | None
    supercritical_barrier_side: str | None
    certification_tier: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = d["certification_tier"]
        d["root_window_lo"] = d["certified_root_window_lo"]
        d["root_window_hi"] = d["certified_root_window_hi"]
        return d


def _endpoint_side(abs_lo: float | None, abs_hi: float | None, target_residue: float) -> str:
    if abs_lo is None or abs_hi is None:
        return "unknown"
    if float(abs_hi) < float(target_residue):
        return "below-target"
    if float(abs_lo) > float(target_residue):
        return "above-target"
    return "mixed"


def _signed_gap_bounds(abs_lo: float | None, abs_hi: float | None, target_residue: float) -> tuple[float | None, float | None]:
    if abs_lo is None or abs_hi is None:
        return None, None
    return float(abs_lo) - float(target_residue), float(abs_hi) - float(target_residue)


def build_endpoint_residue_certificate(
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess: np.ndarray | None = None,
    K_anchor: float | None = None,
    target_residue: float = 0.25,
) -> EndpointResidueCertificate:
    """Validate one endpoint and classify its residue side relative to ``target``."""
    family = family or HarmonicFamily()
    sol = _recenter_orbit_guess(
        p=p,
        q=q,
        K=float(K),
        family=family,
        x_guess=None if x_guess is None else np.asarray(x_guess, dtype=float),
        K_anchor=K_anchor,
    )
    if not sol["success"]:
        return EndpointResidueCertificate(
            p=int(p),
            q=int(q),
            K=float(K),
            target_residue=float(target_residue),
            success=False,
            side="unknown",
            unique_orbit=False,
            validation_status="failed",
            radius=float("nan"),
            residual_inf=float(sol.get("residual_inf", float("nan"))),
            residual_l2=float(sol.get("residual_l2", float("nan"))),
            residue_interval_lo=None,
            residue_interval_hi=None,
            abs_residue_interval_lo=None,
            abs_residue_interval_hi=None,
            signed_gap_interval_lo=None,
            signed_gap_interval_hi=None,
            message=f"endpoint solve failed: {sol['message']}",
        )

    val = validate_periodic_orbit(
        p=p,
        q=q,
        K=float(K),
        family=family,
        x_star=np.asarray(sol["x"], dtype=float),
    )
    abs_lo = val.abs_residue_interval_lo if val.success else None
    abs_hi = val.abs_residue_interval_hi if val.success else None
    side = _endpoint_side(abs_lo, abs_hi, target_residue)
    gap_lo, gap_hi = _signed_gap_bounds(abs_lo, abs_hi, target_residue)
    return EndpointResidueCertificate(
        p=int(p),
        q=int(q),
        K=float(K),
        target_residue=float(target_residue),
        success=bool(val.success),
        side=side,
        unique_orbit=bool(val.unique),
        validation_status=str(val.status),
        radius=float(val.radius),
        residual_inf=float(val.residual_inf),
        residual_l2=float(val.residual_l2),
        residue_interval_lo=None if val.residue_interval_lo is None else float(val.residue_interval_lo),
        residue_interval_hi=None if val.residue_interval_hi is None else float(val.residue_interval_hi),
        abs_residue_interval_lo=None if abs_lo is None else float(abs_lo),
        abs_residue_interval_hi=None if abs_hi is None else float(abs_hi),
        signed_gap_interval_lo=None if gap_lo is None else float(gap_lo),
        signed_gap_interval_hi=None if gap_hi is None else float(gap_hi),
        message=str(val.message),
    )


def _derivative_sign(gp_lo: float, gp_hi: float) -> tuple[str, bool]:
    if gp_lo > 0.0:
        return "positive", True
    if gp_hi < 0.0:
        return "negative", True
    return "mixed", False


def _strict_sign_change(left_side: str, right_side: str) -> bool:
    return {left_side, right_side} == {"below-target", "above-target"}


def _interval_newton_from_midpoint(
    K_lo: float,
    K_hi: float,
    g_mid_lo: float,
    g_mid_hi: float,
    gp_lo: float,
    gp_hi: float,
) -> MidpointNewtonCertificate:
    cert = build_scalar_interval_newton_certificate(
        K_lo,
        K_hi,
        g_mid_lo=g_mid_lo,
        g_mid_hi=g_mid_hi,
        gprime_lo=gp_lo,
        gprime_hi=gp_hi,
    )
    return MidpointNewtonCertificate(
        success=bool(cert.success),
        K_mid=float(cert.midpoint),
        I_lo=float(cert.interval_lo),
        I_hi=float(cert.interval_hi),
        g_mid_lo=cert.g_mid_lo,
        g_mid_hi=cert.g_mid_hi,
        gprime_lo=cert.gprime_lo,
        gprime_hi=cert.gprime_hi,
        newton_image_lo=cert.newton_image_lo,
        newton_image_hi=cert.newton_image_hi,
        refined_lo=cert.refined_lo,
        refined_hi=cert.refined_hi,
        message=str(cert.message),
    )


def certify_unique_crossing_window(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess: np.ndarray | None = None,
    target_residue: float = 0.25,
    auto_localize: bool = False,
    localization_grid: int = 121,
    K_seed: float = 0.0,
    adaptive_refine: bool = True,
    adaptive_max_depth: int = 6,
    adaptive_min_width: float = 1e-5,
) -> UniqueCrossingCertificate:
    """Certify a unique transverse crossing on a rational window when possible.

    The strongest route is:
    1. validated endpoint residues lie strictly on opposite sides of the target;
    2. the branch-level derivative interval for ``g(K)`` has a definite sign;
    3. scalar interval Newton at the midpoint gives a smaller certified root box.

    When step 3 fails but 1--2 succeed, the function still returns a theorem-like
    monotonicity certificate for a unique transverse crossing on the full window.
    """
    family = family or HarmonicFamily()
    localization_scan_used = False
    if auto_localize:
        rows = scan_branch_for_crossing(
            p=p,
            q=q,
            family=family,
            target_residue=target_residue,
            K_min=float(K_lo),
            K_max=float(K_hi),
            n_grid=int(localization_grid),
            K_seed=float(K_seed),
        )
        local = propose_local_crossing_window(rows, target_residue=target_residue)
        if local is not None:
            K_lo = float(local["K_lo"])
            K_hi = float(local["K_hi"])
            localization_scan_used = True

    if K_lo > K_hi:
        K_lo, K_hi = K_hi, K_lo
    tube = build_branch_tube(p=p, q=q, K_lo=K_lo, K_hi=K_hi, family=family, x_guess=x_guess)
    summary = get_residue_and_derivative_iv(
        p=p,
        q=q,
        K_iv=iv_scalar(K_lo, K_hi),
        family=family,
        x_guess=tube.x_mid,
        target_residue=target_residue,
    )

    left = build_endpoint_residue_certificate(
        p=p,
        q=q,
        K=K_lo,
        family=family,
        x_guess=tube.x_left,
        K_anchor=tube.K_mid,
        target_residue=target_residue,
    )
    right = build_endpoint_residue_certificate(
        p=p,
        q=q,
        K=K_hi,
        family=family,
        x_guess=tube.x_right,
        K_anchor=tube.K_mid,
        target_residue=target_residue,
    )
    midpoint = build_endpoint_residue_certificate(
        p=p,
        q=q,
        K=tube.K_mid,
        family=family,
        x_guess=tube.x_mid,
        K_anchor=tube.K_mid,
        target_residue=target_residue,
    )

    gp_lo = float(summary["gprime_interval_lo"])
    gp_hi = float(summary["gprime_interval_hi"])
    deriv_sign, deriv_one_sided = _derivative_sign(gp_lo, gp_hi)
    sign_change = left.success and right.success and _strict_sign_change(left.side, right.side)
    monotone_unique = bool(sign_change and deriv_one_sided)

    if midpoint.success and midpoint.signed_gap_interval_lo is not None and midpoint.signed_gap_interval_hi is not None:
        newton = _interval_newton_from_midpoint(
            K_lo=K_lo,
            K_hi=K_hi,
            g_mid_lo=float(midpoint.signed_gap_interval_lo),
            g_mid_hi=float(midpoint.signed_gap_interval_hi),
            gp_lo=gp_lo,
            gp_hi=gp_hi,
        )
    else:
        newton = MidpointNewtonCertificate(
            success=False,
            K_mid=tube.K_mid,
            I_lo=K_lo,
            I_hi=K_hi,
            g_mid_lo=None,
            g_mid_hi=None,
            gprime_lo=gp_lo,
            gprime_hi=gp_hi,
            newton_image_lo=None,
            newton_image_hi=None,
            refined_lo=None,
            refined_hi=None,
            message="midpoint orbit validation did not produce a signed gap interval",
        )

    certified_lo = None
    certified_hi = None
    tier = "incomplete"
    message_parts = []
    if monotone_unique:
        certified_lo, certified_hi = float(K_lo), float(K_hi)
        tier = "monotone_window"
        message_parts.append("validated endpoints lie on opposite sides of the target and g' has a definite sign")
    else:
        if not sign_change:
            message_parts.append("endpoint sign change was not certified")
        if not deriv_one_sided:
            message_parts.append("branch derivative interval crosses zero")

    if newton.success:
        certified_lo = float(newton.refined_lo)
        certified_hi = float(newton.refined_hi)
        tier = "interval_newton"
        message_parts.append("scalar interval Newton shrank the unique crossing to a strict subwindow")

    if adaptive_refine and tier != "interval_newton":
        adaptive = adaptive_localize_residue_crossing(
            p=p, q=q, K_lo=K_lo, K_hi=K_hi, family=family,
            target_residue=target_residue, max_depth=adaptive_max_depth, min_width=adaptive_min_width,
        )
        best = adaptive.best_window
        if isinstance(best, dict) and best.get("status") in {"interval_newton", "monotone_window"}:
            best_lo = float(best.get("K_lo", K_lo))
            best_hi = float(best.get("K_hi", K_hi))
            best_newton = best.get("interval_newton", {}) if isinstance(best.get("interval_newton", {}), dict) else {}
            better = False
            if best.get("status") == "interval_newton" and tier != "interval_newton":
                better = True
            elif best.get("status") == tier and (best_hi - best_lo) < ((certified_hi or K_hi) - (certified_lo or K_lo)):
                better = True
            elif best.get("status") == "monotone_window" and tier == "incomplete":
                better = True
            if better:
                if best_newton and best_newton.get("success") and best_newton.get("refined_lo") is not None and best_newton.get("refined_hi") is not None:
                    certified_lo = float(best_newton.get("refined_lo"))
                    certified_hi = float(best_newton.get("refined_hi"))
                else:
                    certified_lo, certified_hi = best_lo, best_hi
                tier = str(best.get("status"))
                message_parts.append(f"adaptive residue-branch localization improved the crossing window after analyzing {adaptive.analyzed_windows} subwindows")
                midpoint = best.get("endpoint_mid", midpoint)
                derivative_sign = best.get("derivative_sign", deriv_sign)
                deriv_sign = str(derivative_sign)
                deriv_one_sided = bool(best.get("derivative_away_from_zero", deriv_one_sided))
                sign_change = bool(best.get("strict_sign_change", sign_change))
                monotone_unique = bool(best.get("monotone_unique_crossing", monotone_unique))
                if best_newton and best_newton.get("success"):
                    newton = MidpointNewtonCertificate(
                        success=True,
                        K_mid=float(best_newton.get("midpoint", 0.5*(best_lo+best_hi))),
                        I_lo=best_lo,
                        I_hi=best_hi,
                        g_mid_lo=best_newton.get("g_mid_lo"),
                        g_mid_hi=best_newton.get("g_mid_hi"),
                        gprime_lo=best_newton.get("gprime_lo"),
                        gprime_hi=best_newton.get("gprime_hi"),
                        newton_image_lo=best_newton.get("newton_image_lo"),
                        newton_image_hi=best_newton.get("newton_image_hi"),
                        refined_lo=best_newton.get("refined_lo"),
                        refined_hi=best_newton.get("refined_hi"),
                        message=str(best_newton.get("message", "adaptive scalar interval Newton succeeded")),
                    )

    barrier_lo = None
    barrier_hi = None
    barrier_side = None
    if certified_lo is not None and certified_hi is not None and monotone_unique:
        if deriv_sign == "positive":
            if right.side == "above-target":
                barrier_lo, barrier_hi = float(certified_hi), float(K_hi)
                barrier_side = "above-target"
            elif right.side == "below-target":
                barrier_lo, barrier_hi = float(certified_hi), float(K_hi)
                barrier_side = "below-target"
        elif deriv_sign == "negative":
            if right.side == "above-target":
                barrier_lo, barrier_hi = float(certified_hi), float(K_hi)
                barrier_side = "above-target"
            elif right.side == "below-target":
                barrier_lo, barrier_hi = float(certified_hi), float(K_hi)
                barrier_side = "below-target"

    message = "; ".join(message_parts) if message_parts else "no theorem-like crossing certificate was obtained"
    return UniqueCrossingCertificate(
        p=int(p),
        q=int(q),
        K_lo=float(K_lo),
        K_hi=float(K_hi),
        target_residue=float(target_residue),
        localization_scan_used=bool(localization_scan_used),
        endpoint_left=left.to_dict(),
        endpoint_right=right.to_dict(),
        midpoint=(midpoint if isinstance(midpoint, dict) else midpoint.to_dict()),
        branch_summary=dict(summary),
        derivative_sign=deriv_sign,
        derivative_away_from_zero=bool(deriv_one_sided),
        strict_sign_change=bool(sign_change),
        monotone_unique_crossing=bool(monotone_unique),
        interval_newton=newton.to_dict(),
        certified_root_window_lo=certified_lo,
        certified_root_window_hi=certified_hi,
        supercritical_barrier_lo=barrier_lo,
        supercritical_barrier_hi=barrier_hi,
        supercritical_barrier_side=barrier_side,
        certification_tier=tier,
        message=message,
    )
