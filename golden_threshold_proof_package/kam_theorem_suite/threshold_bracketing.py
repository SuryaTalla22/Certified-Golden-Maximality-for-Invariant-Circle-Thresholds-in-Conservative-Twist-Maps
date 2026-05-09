from __future__ import annotations

"""Bridge-level threshold corridor reports.

This module combines the strongest *implemented* lower-bound and upper-bound
objects in the current suite:

- a continuation report for finite-dimensional irrational-circle validation, and
- a theorem-like unique-crossing certificate for a rational approximant.

The output is deliberately named a *corridor* rather than a proof of the true
irrational threshold. It packages the exact data one would want to inspect while
working toward a sharper existence/breakup theorem: where the irrational side is
validated, where the rational approximant crosses the chosen residue level, and
whether a clean gap is already visible between the two.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable

import numpy as np

from .crossing_certificate import certify_unique_crossing_window
from .standard_map import HarmonicFamily
from .torus_continuation import TorusContinuationReport, continue_invariant_circle_validations


@dataclass
class ThresholdCorridorReport:
    rho: float
    p: int
    q: int
    quality_floor: str
    lower_bound_K: float | None
    lower_bound_source: str
    rational_root_window_lo: float | None
    rational_root_window_hi: float | None
    rational_barrier_lo: float | None
    rational_barrier_hi: float | None
    lower_vs_rational_gap: float | None
    status: str
    torus_continuation: dict[str, Any]
    crossing_certificate: dict[str, Any]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_QUALITY_ORDER = {"failed": 0, "weak": 1, "moderate": 2, "strong": 3}


def _quality_ok(label: str, floor: str) -> bool:
    return _QUALITY_ORDER.get(label, -1) >= _QUALITY_ORDER.get(floor, -1)


def _extract_lower_bound(report: TorusContinuationReport, quality_floor: str) -> tuple[float | None, str]:
    good = [step for step in report.steps if step.success and _quality_ok(step.bridge_quality, quality_floor)]
    if not good:
        return None, "none"
    return float(max(step.K for step in good)), f"torus-continuation-{quality_floor}"


def build_threshold_corridor_report(
    rho: float,
    K_values: Iterable[float],
    p: int,
    q: int,
    crossing_K_lo: float,
    crossing_K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    quality_floor: str = "moderate",
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
) -> ThresholdCorridorReport:
    family = family or HarmonicFamily()
    K_values = [float(k) for k in K_values]
    if quality_floor not in _QUALITY_ORDER:
        raise ValueError(f"unknown quality floor: {quality_floor}")

    torus = continue_invariant_circle_validations(rho=rho, K_values=K_values, family=family, N=N)
    crossing = certify_unique_crossing_window(
        p=p,
        q=q,
        K_lo=float(crossing_K_lo),
        K_hi=float(crossing_K_hi),
        family=family,
        target_residue=target_residue,
        auto_localize=auto_localize_crossing,
    )

    lower_bound_K, lower_source = _extract_lower_bound(torus, quality_floor=quality_floor)
    root_lo = crossing.certified_root_window_lo
    root_hi = crossing.certified_root_window_hi
    barrier_lo = crossing.supercritical_barrier_lo
    barrier_hi = crossing.supercritical_barrier_hi

    gap = None
    status = "incomplete"
    if lower_bound_K is not None and root_lo is not None:
        gap = float(root_lo - lower_bound_K)
        if gap > 0.0:
            status = "separated-corridor"
        else:
            status = "overlapping-corridor"
    elif lower_bound_K is not None:
        status = "lower-bound-only"
    elif root_lo is not None:
        status = "rational-crossing-only"

    notes = (
        "Bridge-level threshold corridor only. The lower endpoint comes from finite-dimensional "
        f"irrational validation at quality floor '{quality_floor}', while the upper object comes from "
        "a rational crossing certificate. This is not yet a theorem identifying the exact irrational threshold."
    )

    return ThresholdCorridorReport(
        rho=float(rho),
        p=int(p),
        q=int(q),
        quality_floor=str(quality_floor),
        lower_bound_K=lower_bound_K,
        lower_bound_source=lower_source,
        rational_root_window_lo=root_lo,
        rational_root_window_hi=root_hi,
        rational_barrier_lo=barrier_lo,
        rational_barrier_hi=barrier_hi,
        lower_vs_rational_gap=gap,
        status=status,
        torus_continuation=torus.to_dict(),
        crossing_certificate=crossing.to_dict(),
        notes=notes,
    )
