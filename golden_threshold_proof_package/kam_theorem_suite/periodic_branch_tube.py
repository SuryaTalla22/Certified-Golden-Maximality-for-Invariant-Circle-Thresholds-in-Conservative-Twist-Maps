from __future__ import annotations

"""Proof-facing wrappers for parameterized periodic-branch tubes.

The original :mod:`branch_tube` module already built a conservative enclosure for
one branch window.  This module repackages that object with certificate metadata
and subdivision helpers so downstream crossing code can work window-by-window in
an adaptive way.
"""

from dataclasses import asdict, dataclass
from typing import Any

from .branch_tube import BranchTube, build_branch_tube
from .standard_map import HarmonicFamily


@dataclass
class PeriodicBranchTubeCertificate:
    p: int
    q: int
    K_lo: float
    K_hi: float
    width: float
    branch_tube: dict[str, Any]
    branch_residual_width: float
    slope_center_inf: float
    interval_tangent_success: bool
    interval_tangent_contraction: float
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KWindow:
    K_lo: float
    K_hi: float
    depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_periodic_branch_tube_certificate(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    x_guess=None,
) -> PeriodicBranchTubeCertificate:
    family = family or HarmonicFamily()
    tube: BranchTube = build_branch_tube(p=p, q=q, K_lo=K_lo, K_hi=K_hi, family=family, x_guess=x_guess)
    return PeriodicBranchTubeCertificate(
        p=int(p),
        q=int(q),
        K_lo=float(min(K_lo, K_hi)),
        K_hi=float(max(K_lo, K_hi)),
        width=float(abs(K_hi - K_lo)),
        branch_tube=tube.to_dict(),
        branch_residual_width=float(tube.branch_residual_width),
        slope_center_inf=float(tube.slope_center_inf),
        interval_tangent_success=bool(tube.interval_tangent_success),
        interval_tangent_contraction=float(tube.interval_tangent_contraction),
        message=str(tube.message),
    )


def subdivide_k_window(K_lo: float, K_hi: float, *, n_pieces: int = 2, depth: int = 0) -> list[KWindow]:
    K_lo = float(K_lo)
    K_hi = float(K_hi)
    if K_lo > K_hi:
        K_lo, K_hi = K_hi, K_lo
    n_pieces = max(2, int(n_pieces))
    grid = [K_lo + (K_hi - K_lo) * (i / n_pieces) for i in range(n_pieces + 1)]
    return [KWindow(float(a), float(b), depth=depth) for a, b in zip(grid[:-1], grid[1:])]
