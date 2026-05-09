from __future__ import annotations

"""Bridge-level obstruction diagnostics for near/supercritical periodic branches.

The purpose of this module is not to overclaim a finished nonexistence theorem.
Instead, it packages the strongest obstruction-side information that the current
proof bridge can state cleanly:

- certified residue windows on a rational branch over a K-interval,
- certified sign information for g(K)=|R(K)|-target,
- trace-based classification into elliptic / hyperbolic / mixed regimes, and
- a bridge report combining a validated subcritical irrational torus with a
  supercritical rational obstruction window.

This is the right next layer after the torus validator because it lets notebooks
and scripts talk about *both* sides of the breakup story in a structured way.
"""

from dataclasses import asdict, dataclass
from typing import Any

from .certification import get_residue_and_derivative_iv
from .interval_utils import iv_scalar
from .crossing_certificate import certify_unique_crossing_window
from .proof_driver import build_torus_validation_report
from .standard_map import HarmonicFamily


@dataclass
class PeriodicObstructionReport:
    p: int
    q: int
    K_lo: float
    K_hi: float
    target_residue: float
    residue_interval_lo: float
    residue_interval_hi: float
    abs_residue_interval_lo: float
    abs_residue_interval_hi: float
    g_interval_lo: float
    g_interval_hi: float
    gprime_interval_lo: float
    gprime_interval_hi: float
    trace_interval_lo: float
    trace_interval_hi: float
    trace_abs_lower_bound: float
    regime: str
    certified_hyperbolic: bool
    certified_crossing_side: str
    tangent_inclusion_success: bool
    branch_tube: dict[str, Any]
    crossing_certificate: dict[str, Any] | None
    supercritical_barrier_lo: float | None
    supercritical_barrier_hi: float | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExistenceObstructionBridgeReport:
    rho: float
    K_subcritical: float
    K_supercritical_lo: float
    K_supercritical_hi: float
    p: int
    q: int
    torus_validation: dict[str, Any]
    periodic_obstruction: dict[str, Any]
    relation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _trace_interval_from_residue_interval(res_lo: float, res_hi: float) -> tuple[float, float]:
    # trace = 2 - 4 R
    lo = 2.0 - 4.0 * float(res_hi)
    hi = 2.0 - 4.0 * float(res_lo)
    return float(lo), float(hi)


def _trace_abs_lower_bound(tr_lo: float, tr_hi: float) -> float:
    if tr_lo <= 0.0 <= tr_hi:
        return 0.0
    return min(abs(tr_lo), abs(tr_hi))


def _classify_regime(res_lo: float, res_hi: float) -> tuple[str, bool]:
    # Greene residue regime: elliptic for 0 < R < 1, hyperbolic outside [0, 1].
    if res_hi < 0.0 or res_lo > 1.0:
        return "hyperbolic", True
    if res_lo > 0.0 and res_hi < 1.0:
        return "elliptic", False
    return "mixed", False


def _classify_crossing_side(g_lo: float, g_hi: float) -> str:
    if g_hi < 0.0:
        return "below-target"
    if g_lo > 0.0:
        return "above-target"
    return "mixed"


def build_periodic_obstruction_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    target_residue: float = 0.25,
) -> PeriodicObstructionReport:
    family = family or HarmonicFamily()
    summary = get_residue_and_derivative_iv(
        p=p,
        q=q,
        K_iv=iv_scalar(K_lo, K_hi),
        family=family,
        x_guess=x_guess,
        target_residue=target_residue,
    )
    res_lo = float(summary["residue_interval_lo"])
    res_hi = float(summary["residue_interval_hi"])
    tr_lo, tr_hi = _trace_interval_from_residue_interval(res_lo, res_hi)
    tr_abs_lb = _trace_abs_lower_bound(tr_lo, tr_hi)
    regime, certified_hyp = _classify_regime(res_lo, res_hi)
    side = _classify_crossing_side(float(summary["g_interval_lo"]), float(summary["g_interval_hi"]))
    crossing_cert = certify_unique_crossing_window(
        p=p,
        q=q,
        K_lo=K_lo,
        K_hi=K_hi,
        family=family,
        x_guess=x_guess,
        target_residue=target_residue,
        auto_localize=False,
    )
    return PeriodicObstructionReport(
        p=int(p),
        q=int(q),
        K_lo=float(K_lo),
        K_hi=float(K_hi),
        target_residue=float(target_residue),
        residue_interval_lo=res_lo,
        residue_interval_hi=res_hi,
        abs_residue_interval_lo=float(summary["abs_residue_interval_lo"]),
        abs_residue_interval_hi=float(summary["abs_residue_interval_hi"]),
        g_interval_lo=float(summary["g_interval_lo"]),
        g_interval_hi=float(summary["g_interval_hi"]),
        gprime_interval_lo=float(summary["gprime_interval_lo"]),
        gprime_interval_hi=float(summary["gprime_interval_hi"]),
        trace_interval_lo=tr_lo,
        trace_interval_hi=tr_hi,
        trace_abs_lower_bound=tr_abs_lb,
        regime=regime,
        certified_hyperbolic=bool(certified_hyp),
        certified_crossing_side=side,
        tangent_inclusion_success=bool(summary["tangent_inclusion_success"]),
        branch_tube=dict(summary["branch_tube"]),
        crossing_certificate=crossing_cert.to_dict(),
        supercritical_barrier_lo=crossing_cert.supercritical_barrier_lo,
        supercritical_barrier_hi=crossing_cert.supercritical_barrier_hi,
        message=str(summary["message"]),
    )


def build_existence_obstruction_bridge(
    rho: float,
    K_subcritical: float,
    K_supercritical_lo: float,
    K_supercritical_hi: float,
    p: int,
    q: int,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    target_residue: float = 0.25,
) -> ExistenceObstructionBridgeReport:
    family = family or HarmonicFamily()
    torus = build_torus_validation_report(rho=rho, K=K_subcritical, family=family, N=N)
    obstruction = build_periodic_obstruction_report(
        p=p,
        q=q,
        K_lo=K_supercritical_lo,
        K_hi=K_supercritical_hi,
        family=family,
        target_residue=target_residue,
    ).to_dict()
    crossing_cert = obstruction.get("crossing_certificate") or {}
    relation = {
        "subcritical_torus_validated": bool(torus["success"]),
        "obstruction_crossing_side": obstruction["certified_crossing_side"],
        "certified_hyperbolic": bool(obstruction["certified_hyperbolic"]),
        "crossing_certificate_tier": crossing_cert.get("certification_tier"),
        "supercritical_barrier_window": (
            [obstruction["supercritical_barrier_lo"], obstruction["supercritical_barrier_hi"]]
            if obstruction.get("supercritical_barrier_lo") is not None and obstruction.get("supercritical_barrier_hi") is not None
            else None
        ),
        "bridge_status": (
            "validated-existence plus certified-crossing-and-barrier"
            if torus["success"] and crossing_cert.get("certification_tier") in {"interval_newton", "monotone_window"}
            else "validated-existence plus supercritical-branch-obstruction"
            if torus["success"] and obstruction["certified_crossing_side"] == "above-target"
            else "incomplete"
        ),
        "notes": (
            "Bridge-level statement only: this combines a finite-dimensional irrational-circle "
            "validation below the candidate threshold with a certified rational obstruction window above it."
        ),
    }
    return ExistenceObstructionBridgeReport(
        rho=float(rho),
        K_subcritical=float(K_subcritical),
        K_supercritical_lo=float(K_supercritical_lo),
        K_supercritical_hi=float(K_supercritical_hi),
        p=int(p),
        q=int(q),
        torus_validation=torus,
        periodic_obstruction=obstruction,
        relation=relation,
    )
