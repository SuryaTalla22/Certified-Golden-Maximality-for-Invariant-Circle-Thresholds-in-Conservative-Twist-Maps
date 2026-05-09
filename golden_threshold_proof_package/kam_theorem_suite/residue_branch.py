from __future__ import annotations

"""Branch-generic residue crossing analysis and adaptive localization.

This module is the main stage-30 hardening step for the rational branch side of
Theorems IV and V.  It lifts the existing single-window crossing logic into an
adaptive, reusable proof object that can analyze a broad parameter window,
subdivide it, and return the best certified crossing subwindow it finds.
"""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .certification import (
    get_residue_and_derivative_iv,
    validate_periodic_orbit,
    _recenter_orbit_guess,
)
from .interval_newton_scalar import (
    ScalarIntervalNewtonCertificate,
    build_scalar_interval_newton_certificate,
    derivative_sign_from_bounds,
)
from .periodic_branch_tube import KWindow, build_periodic_branch_tube_certificate, subdivide_k_window
from .standard_map import HarmonicFamily
from .interval_utils import iv_scalar


@dataclass
class ResidueEndpointCertificate:
    K: float
    success: bool
    side: str
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
class ResidueBranchWindowCertificate:
    p: int
    q: int
    K_lo: float
    K_hi: float
    depth: int
    target_residue: float
    branch_tube: dict[str, Any]
    g_interval_lo: float
    g_interval_hi: float
    gprime_interval_lo: float
    gprime_interval_hi: float
    derivative_sign: str
    derivative_away_from_zero: bool
    strict_sign_change: bool
    monotone_unique_crossing: bool
    endpoint_left: dict[str, Any]
    endpoint_mid: dict[str, Any]
    endpoint_right: dict[str, Any]
    interval_newton: dict[str, Any]
    status: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AdaptiveResidueCrossingCertificate:
    p: int
    q: int
    K_lo: float
    K_hi: float
    target_residue: float
    analyzed_windows: int
    max_depth_reached: int
    best_window: dict[str, Any] | None
    successful_window_count: int
    monotone_window_count: int
    interval_newton_window_count: int
    status: str
    windows: list[dict[str, Any]]
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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


def build_residue_endpoint_certificate(
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    K_anchor: float | None = None,
    target_residue: float = 0.25,
) -> ResidueEndpointCertificate:
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
        return ResidueEndpointCertificate(
            K=float(K),
            success=False,
            side="unknown",
            residue_interval_lo=None,
            residue_interval_hi=None,
            abs_residue_interval_lo=None,
            abs_residue_interval_hi=None,
            signed_gap_interval_lo=None,
            signed_gap_interval_hi=None,
            message=f"endpoint solve failed: {sol['message']}",
        )

    val = validate_periodic_orbit(p=p, q=q, K=float(K), family=family, x_star=np.asarray(sol["x"], dtype=float))
    abs_lo = val.abs_residue_interval_lo if val.success else None
    abs_hi = val.abs_residue_interval_hi if val.success else None
    gap_lo, gap_hi = _signed_gap_bounds(abs_lo, abs_hi, target_residue)
    return ResidueEndpointCertificate(
        K=float(K),
        success=bool(val.success),
        side=_endpoint_side(abs_lo, abs_hi, target_residue),
        residue_interval_lo=(None if val.residue_interval_lo is None else float(val.residue_interval_lo)),
        residue_interval_hi=(None if val.residue_interval_hi is None else float(val.residue_interval_hi)),
        abs_residue_interval_lo=(None if abs_lo is None else float(abs_lo)),
        abs_residue_interval_hi=(None if abs_hi is None else float(abs_hi)),
        signed_gap_interval_lo=(None if gap_lo is None else float(gap_lo)),
        signed_gap_interval_hi=(None if gap_hi is None else float(gap_hi)),
        message=str(val.message),
    )


def analyze_residue_branch_window(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    target_residue: float = 0.25,
    depth: int = 0,
) -> ResidueBranchWindowCertificate:
    family = family or HarmonicFamily()
    if K_lo > K_hi:
        K_lo, K_hi = K_hi, K_lo

    tube_cert = build_periodic_branch_tube_certificate(p=p, q=q, K_lo=K_lo, K_hi=K_hi, family=family, x_guess=x_guess)
    summary = get_residue_and_derivative_iv(
        p=p,
        q=q,
        K_iv=iv_scalar(K_lo, K_hi),
        family=family,
        x_guess=np.asarray(tube_cert.branch_tube["x_mid"], dtype=float),
        target_residue=target_residue,
    )

    left = build_residue_endpoint_certificate(
        p=p, q=q, K=K_lo, family=family,
        x_guess=np.asarray(tube_cert.branch_tube["x_left"], dtype=float), K_anchor=0.5 * (K_lo + K_hi),
        target_residue=target_residue,
    )
    mid = build_residue_endpoint_certificate(
        p=p, q=q, K=0.5 * (K_lo + K_hi), family=family,
        x_guess=np.asarray(tube_cert.branch_tube["x_mid"], dtype=float), K_anchor=0.5 * (K_lo + K_hi),
        target_residue=target_residue,
    )
    right = build_residue_endpoint_certificate(
        p=p, q=q, K=K_hi, family=family,
        x_guess=np.asarray(tube_cert.branch_tube["x_right"], dtype=float), K_anchor=0.5 * (K_lo + K_hi),
        target_residue=target_residue,
    )

    gp_lo = float(summary["gprime_interval_lo"])
    gp_hi = float(summary["gprime_interval_hi"])
    deriv_sign, deriv_one_sided = derivative_sign_from_bounds(gp_lo, gp_hi)
    strict_sign_change = bool(left.success and right.success and {left.side, right.side} == {"below-target", "above-target"})
    monotone_unique = bool(strict_sign_change and deriv_one_sided)

    if mid.success and mid.signed_gap_interval_lo is not None and mid.signed_gap_interval_hi is not None:
        newton = build_scalar_interval_newton_certificate(
            K_lo, K_hi,
            midpoint=0.5 * (K_lo + K_hi),
            g_mid_lo=float(mid.signed_gap_interval_lo),
            g_mid_hi=float(mid.signed_gap_interval_hi),
            gprime_lo=gp_lo,
            gprime_hi=gp_hi,
        )
    else:
        newton = ScalarIntervalNewtonCertificate(
            success=False,
            interval_lo=float(K_lo),
            interval_hi=float(K_hi),
            midpoint=0.5 * (K_lo + K_hi),
            g_mid_lo=None,
            g_mid_hi=None,
            gprime_lo=float(gp_lo),
            gprime_hi=float(gp_hi),
            derivative_sign=deriv_sign,
            derivative_away_from_zero=bool(deriv_one_sided),
            newton_image_lo=None,
            newton_image_hi=None,
            refined_lo=None,
            refined_hi=None,
            strict_subset=False,
            message="midpoint validation did not produce a signed gap interval",
        )

    status = "incomplete"
    parts: list[str] = []
    if monotone_unique:
        status = "monotone_window"
        parts.append("validated endpoints lie on opposite sides of the target and g' has a definite sign")
    if newton.success:
        status = "interval_newton"
        parts.append("scalar interval Newton closed a strict subwindow")
    if not parts:
        if not strict_sign_change:
            parts.append("endpoint sign change was not certified")
        if not deriv_one_sided:
            parts.append("branch derivative interval crosses zero")
    return ResidueBranchWindowCertificate(
        p=int(p),
        q=int(q),
        K_lo=float(K_lo),
        K_hi=float(K_hi),
        depth=int(depth),
        target_residue=float(target_residue),
        branch_tube=dict(tube_cert.to_dict()),
        g_interval_lo=float(summary["g_interval_lo"]),
        g_interval_hi=float(summary["g_interval_hi"]),
        gprime_interval_lo=gp_lo,
        gprime_interval_hi=gp_hi,
        derivative_sign=deriv_sign,
        derivative_away_from_zero=bool(deriv_one_sided),
        strict_sign_change=bool(strict_sign_change),
        monotone_unique_crossing=bool(monotone_unique),
        endpoint_left=left.to_dict(),
        endpoint_mid=mid.to_dict(),
        endpoint_right=right.to_dict(),
        interval_newton=newton.to_dict(),
        status=status,
        message="; ".join(parts),
    )


def _candidate_rank(cert: ResidueBranchWindowCertificate) -> tuple[int, float]:
    tier = 2 if cert.status == "interval_newton" else (1 if cert.status == "monotone_window" else 0)
    width = float(cert.K_hi - cert.K_lo)
    return tier, -width


def _should_subdivide(cert: ResidueBranchWindowCertificate) -> bool:
    left = cert.endpoint_left.get("side")
    mid = cert.endpoint_mid.get("side")
    right = cert.endpoint_right.get("side")
    if cert.strict_sign_change:
        return True
    if {left, mid} == {"below-target", "above-target"}:
        return True
    if {mid, right} == {"below-target", "above-target"}:
        return True
    if "mixed" in {left, mid, right} or "unknown" in {left, mid, right}:
        return True
    return False


def adaptive_localize_residue_crossing(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    max_depth: int = 6,
    min_width: float = 1e-5,
    n_pieces: int = 2,
    use_seed_propagation: bool = True,
    initial_x_guess=None,
) -> AdaptiveResidueCrossingCertificate:
    family = family or HarmonicFamily()
    queue: list[dict[str, Any]] = [{"window": KWindow(float(K_lo), float(K_hi), depth=0), "x_guess": initial_x_guess}]
    windows: list[ResidueBranchWindowCertificate] = []
    best: ResidueBranchWindowCertificate | None = None
    max_depth_reached = 0

    while queue:
        payload = queue.pop(0)
        current = payload["window"]
        x_guess = payload.get("x_guess")
        max_depth_reached = max(max_depth_reached, int(current.depth))
        cert = analyze_residue_branch_window(
            p=p, q=q, K_lo=current.K_lo, K_hi=current.K_hi, family=family,
            x_guess=x_guess, target_residue=target_residue, depth=current.depth,
        )
        windows.append(cert)

        if best is None or _candidate_rank(cert) > _candidate_rank(best):
            best = cert
        elif best is not None and _candidate_rank(cert) == _candidate_rank(best):
            if (cert.K_hi - cert.K_lo) < (best.K_hi - best.K_lo):
                best = cert

        width = float(current.K_hi - current.K_lo)
        if current.depth >= int(max_depth) or width <= float(min_width):
            continue
        if cert.status == "interval_newton" and width <= 4.0 * float(min_width):
            continue
        if _should_subdivide(cert):
            children = subdivide_k_window(current.K_lo, current.K_hi, n_pieces=n_pieces, depth=current.depth + 1)
            branch = cert.branch_tube or {}
            left_seed = np.asarray(branch.get("x_left"), dtype=float) if branch.get("x_left") is not None else None
            mid_seed = np.asarray(branch.get("x_mid"), dtype=float) if branch.get("x_mid") is not None else None
            right_seed = np.asarray(branch.get("x_right"), dtype=float) if branch.get("x_right") is not None else None
            child_payloads: list[dict[str, Any]] = []
            for idx, child in enumerate(children):
                seed = None
                if use_seed_propagation:
                    frac = (idx + 0.5) / max(len(children), 1)
                    if frac <= 0.34 and left_seed is not None:
                        seed = left_seed
                    elif frac >= 0.66 and right_seed is not None:
                        seed = right_seed
                    else:
                        seed = mid_seed if mid_seed is not None else (left_seed if left_seed is not None else right_seed)
                child_payloads.append({"window": child, "x_guess": seed})
            queue.extend(child_payloads)

    interval_newton_count = sum(1 for c in windows if c.status == "interval_newton")
    monotone_count = sum(1 for c in windows if c.status in {"interval_newton", "monotone_window"})
    success_count = sum(1 for c in windows if c.status != "incomplete")
    if best is None:
        status = "failed"
        msg = "no residue-branch windows were analyzed"
        best_dict = None
    else:
        status = best.status
        msg = (
            "adaptive localization found a strict interval-Newton crossing subwindow"
            if best.status == "interval_newton"
            else (
                "adaptive localization found a monotone unique-crossing window"
                if best.status == "monotone_window"
                else "adaptive localization did not obtain a theorem-like crossing certificate"
            )
        )
        best_dict = best.to_dict()

    return AdaptiveResidueCrossingCertificate(
        p=int(p),
        q=int(q),
        K_lo=float(min(K_lo, K_hi)),
        K_hi=float(max(K_lo, K_hi)),
        target_residue=float(target_residue),
        analyzed_windows=len(windows),
        max_depth_reached=int(max_depth_reached),
        best_window=best_dict,
        successful_window_count=int(success_count),
        monotone_window_count=int(monotone_count),
        interval_newton_window_count=int(interval_newton_count),
        status=status,
        windows=[w.to_dict() for w in windows],
        message=msg,
    )
