from __future__ import annotations

"""Reusable scalar interval-Newton certificates.

This module isolates the one-dimensional root-refinement logic that previously
lived inside :mod:`crossing_certificate`.  The theorem program needs this in a
branch-generic form so residue crossings, transport equations, and later
threshold-side scalar equations can all use the same certificate format.
"""

from dataclasses import asdict, dataclass
from typing import Any

from .interval_utils import iv_scalar


@dataclass
class ScalarIntervalNewtonCertificate:
    success: bool
    interval_lo: float
    interval_hi: float
    midpoint: float
    g_mid_lo: float | None
    g_mid_hi: float | None
    gprime_lo: float | None
    gprime_hi: float | None
    derivative_sign: str
    derivative_away_from_zero: bool
    newton_image_lo: float | None
    newton_image_hi: float | None
    refined_lo: float | None
    refined_hi: float | None
    strict_subset: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def derivative_sign_from_bounds(lo: float, hi: float) -> tuple[str, bool]:
    lo = float(lo)
    hi = float(hi)
    if lo > 0.0:
        return "positive", True
    if hi < 0.0:
        return "negative", True
    return "mixed", False


def build_scalar_interval_newton_certificate(
    interval_lo: float,
    interval_hi: float,
    *,
    g_mid_lo: float,
    g_mid_hi: float,
    gprime_lo: float,
    gprime_hi: float,
    midpoint: float | None = None,
) -> ScalarIntervalNewtonCertificate:
    interval_lo = float(interval_lo)
    interval_hi = float(interval_hi)
    if interval_lo > interval_hi:
        interval_lo, interval_hi = interval_hi, interval_lo
    midpoint = 0.5 * (interval_lo + interval_hi) if midpoint is None else float(midpoint)

    deriv_sign, one_sided = derivative_sign_from_bounds(gprime_lo, gprime_hi)
    if not one_sided:
        return ScalarIntervalNewtonCertificate(
            success=False,
            interval_lo=interval_lo,
            interval_hi=interval_hi,
            midpoint=midpoint,
            g_mid_lo=float(g_mid_lo),
            g_mid_hi=float(g_mid_hi),
            gprime_lo=float(gprime_lo),
            gprime_hi=float(gprime_hi),
            derivative_sign=deriv_sign,
            derivative_away_from_zero=False,
            newton_image_lo=None,
            newton_image_hi=None,
            refined_lo=None,
            refined_hi=None,
            strict_subset=False,
            message="derivative interval is not one-sided, so scalar interval Newton is not valid",
        )

    I = iv_scalar(interval_lo, interval_hi)
    x_mid = iv_scalar(midpoint)
    g_mid_iv = iv_scalar(float(g_mid_lo), float(g_mid_hi))
    gp_iv = iv_scalar(float(gprime_lo), float(gprime_hi))
    N_iv = x_mid - (g_mid_iv / gp_iv)

    refined_lo = max(float(I.a), float(N_iv.a))
    refined_hi = min(float(I.b), float(N_iv.b))
    nonempty = refined_lo <= refined_hi
    strict_subset = float(N_iv.a) > float(I.a) and float(N_iv.b) < float(I.b) and nonempty
    success = bool(strict_subset)
    msg = (
        "scalar interval Newton image is strictly contained in the window"
        if success
        else "scalar interval Newton image did not close strictly inside the window"
    )

    return ScalarIntervalNewtonCertificate(
        success=success,
        interval_lo=interval_lo,
        interval_hi=interval_hi,
        midpoint=midpoint,
        g_mid_lo=float(g_mid_iv.a),
        g_mid_hi=float(g_mid_iv.b),
        gprime_lo=float(gp_iv.a),
        gprime_hi=float(gp_iv.b),
        derivative_sign=deriv_sign,
        derivative_away_from_zero=True,
        newton_image_lo=float(N_iv.a),
        newton_image_hi=float(N_iv.b),
        refined_lo=(float(refined_lo) if nonempty else None),
        refined_hi=(float(refined_hi) if nonempty else None),
        strict_subset=bool(strict_subset),
        message=msg,
    )
