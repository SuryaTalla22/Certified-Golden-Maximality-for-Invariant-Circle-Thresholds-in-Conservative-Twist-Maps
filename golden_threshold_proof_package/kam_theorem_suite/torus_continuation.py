from __future__ import annotations

"""Validated continuation utilities for irrational invariant circles.

This module adds the next natural layer above ``torus_validator``: instead of
solving and validating a single collocation system at one parameter value, it
tracks a family of candidate invariant circles across a parameter grid using
warm starts and summarizes where validation succeeds or fails.

The resulting objects are still honest *proof-bridge* artifacts:
- each successful step is a finite-dimensional radii-polynomial certificate for
  the collocation system at that parameter value;
- the scan as a whole is not claimed to be a theorem about the exact analytic
  threshold, but it gives a reproducible, structured lower-bound search tool.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Sequence

import numpy as np

from .standard_map import HarmonicFamily
from .torus_validator import (
    InvariantCircleValidationResult,
    solve_invariant_circle_graph,
    validate_invariant_circle_graph,
)


@dataclass
class TorusContinuationStep:
    index: int
    K: float
    success: bool
    radius: float
    residual_inf: float
    oversampled_residual_inf: float
    contraction_bound: float
    strip_width_proxy: float | None
    bridge_quality: str
    message: str
    solver_iterations: int
    z: np.ndarray = field(repr=False)
    u: np.ndarray = field(repr=False)

    @classmethod
    def from_validation(cls, index: int, val: InvariantCircleValidationResult) -> "TorusContinuationStep":
        return cls(
            index=int(index),
            K=float(val.K),
            success=bool(val.success),
            radius=float(val.radius),
            residual_inf=float(val.residual_inf),
            oversampled_residual_inf=float(val.oversampled_residual_inf),
            contraction_bound=float(val.contraction_bound),
            strip_width_proxy=(None if val.strip_width_proxy is None else float(val.strip_width_proxy)),
            bridge_quality=str(val.bridge_quality),
            message=str(val.message),
            solver_iterations=int(val.solver_iterations),
            z=np.asarray(val.z, dtype=float),
            u=np.asarray(val.u, dtype=float),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["z"] = np.asarray(self.z, dtype=float).tolist()
        d["u"] = np.asarray(self.u, dtype=float).tolist()
        return d


@dataclass
class TorusContinuationReport:
    rho: float
    N: int
    family_label: str
    K_values: list[float]
    steps: list[TorusContinuationStep]
    all_success: bool
    validated_fraction: float
    last_success_index: int | None
    first_failure_index: int | None
    last_success_K: float | None
    first_failure_K: float | None
    threshold_bracket: tuple[float, float] | None
    quality_threshold_bracket: tuple[float, float] | None
    monotone_success_prefix: bool
    strongest_quality_prefix: str | None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["steps"] = [s.to_dict() for s in self.steps]
        if self.threshold_bracket is not None:
            d["threshold_bracket"] = [float(self.threshold_bracket[0]), float(self.threshold_bracket[1])]
        if self.quality_threshold_bracket is not None:
            d["quality_threshold_bracket"] = [float(self.quality_threshold_bracket[0]), float(self.quality_threshold_bracket[1])]
            d["quality_floor_passed_up_to"] = float(self.quality_threshold_bracket[0])
        else:
            d["quality_floor_passed_up_to"] = None
        if self.threshold_bracket is not None:
            d["last_success_before_failure"] = float(self.threshold_bracket[0])
            d["first_failure_after_success"] = float(self.threshold_bracket[1])
        else:
            d["last_success_before_failure"] = self.last_success_K
            d["first_failure_after_success"] = self.first_failure_K
        return d


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _normalize_K_values(K_values: Iterable[float]) -> list[float]:
    out = [float(k) for k in K_values]
    if len(out) == 0:
        raise ValueError("K_values must be non-empty")
    return out


def continue_invariant_circle_validations(
    rho: float,
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    initial_z0: np.ndarray | None = None,
    restart_on_failure: bool = True,
    reverse_if_descending: bool = False,
) -> TorusContinuationReport:
    """Validate collocation circles across a parameter grid.

    Parameters
    ----------
    rho:
        Irrational rotation number.
    K_values:
        Sequence of parameter values. The function preserves the order provided;
        this matters because successful steps are warm-started from the previous
        one.
    restart_on_failure:
        If true, a failure clears the warm start and lets the next point start
        from the zero graph again. This is useful when the user wants to scan a
        grid rather than require contiguous continuation success.
    reverse_if_descending:
        Convenience flag for notebook use. When true and ``K_values`` is strictly
        descending, the function internally scans from low to high and maps the
        results back to the original order. This keeps warm starts effective
        while preserving the user's requested output order.
    """
    family = family or HarmonicFamily()
    K_grid = _normalize_K_values(K_values)

    descending = len(K_grid) >= 2 and all(K_grid[i + 1] < K_grid[i] for i in range(len(K_grid) - 1))
    order = list(range(len(K_grid)))
    scan_grid = list(K_grid)
    if reverse_if_descending and descending:
        order = list(reversed(order))
        scan_grid = [K_grid[i] for i in order]

    tmp_steps: list[TorusContinuationStep] = [None] * len(K_grid)  # type: ignore[assignment]
    z_warm = None if initial_z0 is None else np.asarray(initial_z0, dtype=float).copy()

    for local_idx, K in enumerate(scan_grid):
        global_idx = order[local_idx]
        solve = solve_invariant_circle_graph(rho, K, family, N=N, z0=z_warm)
        val = validate_invariant_circle_graph(rho, K, family, N=N, solve_result=solve)
        step = TorusContinuationStep.from_validation(global_idx, val)
        tmp_steps[global_idx] = step
        if val.success:
            z_warm = np.asarray(val.z, dtype=float).copy()
        elif restart_on_failure:
            z_warm = None

    steps = [s for s in tmp_steps if s is not None]
    success_flags = [bool(s.success) for s in steps]
    all_success = all(success_flags)
    validated_fraction = float(np.mean(success_flags)) if success_flags else 0.0

    success_indices = [i for i, s in enumerate(steps) if s.success]
    failure_indices = [i for i, s in enumerate(steps) if not s.success]
    last_success_index = max(success_indices) if success_indices else None
    first_failure_index = min(failure_indices) if failure_indices else None
    last_success_K = steps[last_success_index].K if last_success_index is not None else None
    first_failure_K = steps[first_failure_index].K if first_failure_index is not None else None

    # The threshold bracket is meaningful when the successes form a prefix and
    # there is at least one subsequent failure.
    prefix_len = 0
    for ok in success_flags:
        if ok:
            prefix_len += 1
        else:
            break
    monotone_success_prefix = (prefix_len == len(success_flags)) or all(not ok for ok in success_flags[prefix_len:])
    threshold_bracket = None
    if monotone_success_prefix and prefix_len > 0 and prefix_len < len(steps):
        threshold_bracket = (steps[prefix_len - 1].K, steps[prefix_len].K)

    quality_flags = [s.bridge_quality in {"strong", "moderate"} for s in steps]
    qprefix_len = 0
    for ok in quality_flags:
        if ok:
            qprefix_len += 1
        else:
            break
    quality_threshold_bracket = None
    if qprefix_len > 0 and qprefix_len < len(steps):
        quality_threshold_bracket = (steps[qprefix_len - 1].K, steps[qprefix_len].K)
    strongest_quality_prefix = None
    if qprefix_len > 0:
        if all(s.bridge_quality == "strong" for s in steps[:qprefix_len]):
            strongest_quality_prefix = "strong"
        else:
            strongest_quality_prefix = "moderate"

    return TorusContinuationReport(
        rho=float(rho),
        N=int(N),
        family_label=_family_label(family),
        K_values=[float(k) for k in K_grid],
        steps=steps,
        all_success=bool(all_success),
        validated_fraction=float(validated_fraction),
        last_success_index=last_success_index,
        first_failure_index=first_failure_index,
        last_success_K=last_success_K,
        first_failure_K=first_failure_K,
        threshold_bracket=threshold_bracket,
        quality_threshold_bracket=quality_threshold_bracket,
        monotone_success_prefix=bool(monotone_success_prefix),
        strongest_quality_prefix=strongest_quality_prefix,
    )


def scan_torus_validity_on_grid(
    rho: float,
    K_min: float,
    K_max: float,
    n_steps: int,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
) -> TorusContinuationReport:
    """Convenience wrapper for a uniform scan on ``[K_min, K_max]``."""
    if n_steps < 2:
        raise ValueError("n_steps must be at least 2")
    grid = np.linspace(float(K_min), float(K_max), int(n_steps))
    return continue_invariant_circle_validations(rho, grid, family=family, N=N)



@dataclass
class TorusContinuationClosureCertificate:
    rho: float
    N: int
    family_label: str
    all_steps_locally_closed: bool
    continuation_interval: list[float] | None
    continuation_monotonicity_certified: bool
    seed_transfer_stable: bool
    continuation_breakdown_index: int | None
    continuation_closure_status: str
    source_report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_torus_continuation_closure_certificate(report: TorusContinuationReport) -> TorusContinuationClosureCertificate:
    interval = None
    if report.last_success_K is not None:
        hi = report.last_success_K if report.first_failure_K is None else report.first_failure_K
        interval = [float(min(report.K_values)), float(hi)]
    all_local = bool(report.validated_fraction > 0.0 and (report.monotone_success_prefix or report.all_success))
    monotone = bool(report.monotone_success_prefix)
    seed_stable = bool(report.strongest_quality_prefix in {'strong', 'moderate'} or report.validated_fraction >= 0.5)
    if interval is not None and all_local and seed_stable:
        status = 'torus-continuation-closure-strong'
    elif interval is not None:
        status = 'torus-continuation-closure-partial'
    else:
        status = 'torus-continuation-closure-failed'
    return TorusContinuationClosureCertificate(
        rho=float(report.rho),
        N=int(report.N),
        family_label=str(report.family_label),
        all_steps_locally_closed=bool(all_local),
        continuation_interval=interval,
        continuation_monotonicity_certified=bool(monotone),
        seed_transfer_stable=bool(seed_stable),
        continuation_breakdown_index=report.first_failure_index,
        continuation_closure_status=str(status),
        source_report=report.to_dict(),
    )
