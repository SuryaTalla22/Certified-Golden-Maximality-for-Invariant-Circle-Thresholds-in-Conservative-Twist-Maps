from __future__ import annotations

"""Seed transfer across neighboring periodic approximants.

This module pushes the campaign layer beyond parameter-window heuristics.  The
key idea is to turn a *successful* rational approximant into a reusable orbit
profile that can seed nearby approximants on the same arithmetic ladder.

The transfer is intentionally modest and transparent:

* A successful source orbit is converted into a periodic profile capturing
  (i) the lifted shape relative to the rigid rotation ``j p/q`` and
  (ii) the graph-like deviation of the step variable ``r`` from the average
  rotation ``p/q`` as a function of phase.
* For a target approximant ``p'/q'``, two seed-construction methods are tried:
  a lifted-shape interpolation and a graph-step recurrence.
* The resulting candidate seeds are *scored* by the target residual at the
  requested parameter value, and the better seed is surfaced to callers.

This is not a theorem of inter-approximant conjugacy.  It is a proof-oriented
engineering layer that makes neighboring-approximant campaigns much less ad hoc.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable

import numpy as np

from .standard_map import (
    HarmonicFamily,
    orbit_to_states,
    periodic_orbit_residual,
    solve_periodic_orbit,
)


@dataclass
class PeriodicOrbitSeedProfile:
    source_p: int
    source_q: int
    source_K: float
    source_label: str
    source_rotation: float
    phase_anchor: float
    lift_grid: list[float]
    lift_delta: list[float]
    theta_phase_sorted: list[float]
    r_dev_sorted: list[float]
    source_residual_inf: float
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SeedGuessScore:
    method: str
    p: int
    q: int
    K: float
    residual_inf: float
    residual_l2: float
    monotone_theta: bool
    endpoint_mismatch: float
    x0_phase: float
    x_guess: list[float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SeedTransferReport:
    source_label: str
    target_label: str
    target_p: int
    target_q: int
    target_K: float
    candidate_scores: list[dict[str, Any]]
    selected_method: str | None
    selected_residual_inf: float | None
    selected_x_guess: list[float] | None
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _periodic_interp(sample_x: np.ndarray, sample_y: np.ndarray, query_x: np.ndarray) -> np.ndarray:
    sample_x = np.asarray(sample_x, dtype=float)
    sample_y = np.asarray(sample_y, dtype=float)
    query_x = np.mod(np.asarray(query_x, dtype=float), 1.0)
    if sample_x.size == 0:
        return np.zeros_like(query_x)
    order = np.argsort(sample_x)
    xs = sample_x[order]
    ys = sample_y[order]
    xs_ext = np.concatenate([xs, xs[:1] + 1.0])
    ys_ext = np.concatenate([ys, ys[:1]])
    return np.interp(query_x, xs_ext, ys_ext)


def build_seed_profile_from_orbit(
    x: Iterable[float],
    *,
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily | None = None,
    label: str | None = None,
) -> PeriodicOrbitSeedProfile:
    family = family or HarmonicFamily()
    x = np.asarray(list(x), dtype=float)
    if len(x) != int(q):
        raise ValueError('orbit length must equal q')
    theta, r = orbit_to_states(x, p)
    rho = float(p) / float(q)
    phase_anchor = float(np.mod(x[0], 1.0))
    idx = np.arange(int(q), dtype=float)
    lift_grid = idx / float(q)
    lift_delta = x - (x[0] + idx * rho)
    theta_phase = np.mod(np.asarray(theta, dtype=float), 1.0)
    r_dev = np.asarray(r, dtype=float) - rho
    order = np.argsort(theta_phase)
    residual = periodic_orbit_residual(x, int(p), float(K), family)
    notes = (
        'Profile stores both lifted-shape and graph-step deviations relative to the rigid rotation. '
        'It is meant for neighboring-approximant seeding, not as a theorem of orbit conjugacy.'
    )
    return PeriodicOrbitSeedProfile(
        source_p=int(p),
        source_q=int(q),
        source_K=float(K),
        source_label=str(label or f'{p}/{q}'),
        source_rotation=rho,
        phase_anchor=phase_anchor,
        lift_grid=[float(v) for v in lift_grid],
        lift_delta=[float(v) for v in lift_delta],
        theta_phase_sorted=[float(v) for v in theta_phase[order]],
        r_dev_sorted=[float(v) for v in r_dev[order]],
        source_residual_inf=float(np.max(np.abs(residual))),
        notes=notes,
    )


def _seed_by_lift_shape(profile: PeriodicOrbitSeedProfile, *, p: int, q: int) -> np.ndarray:
    rho = float(p) / float(q)
    s = np.arange(int(q), dtype=float) / float(q)
    delta = _periodic_interp(np.asarray(profile.lift_grid), np.asarray(profile.lift_delta), s)
    x = profile.phase_anchor + np.arange(int(q), dtype=float) * rho + delta
    return np.asarray(x, dtype=float)


def _seed_by_graph_step(profile: PeriodicOrbitSeedProfile, *, p: int, q: int) -> np.ndarray:
    rho = float(p) / float(q)
    x = np.empty(int(q), dtype=float)
    x[0] = float(profile.phase_anchor)
    phase_samples = np.asarray(profile.theta_phase_sorted, dtype=float)
    r_dev_samples = np.asarray(profile.r_dev_sorted, dtype=float)
    for j in range(int(q) - 1):
        phase = np.mod(x[j], 1.0)
        r_dev = float(_periodic_interp(phase_samples, r_dev_samples, np.array([phase]))[0])
        x[j + 1] = x[j] + rho + r_dev
    return x


def score_seed_guess(
    x_guess: Iterable[float],
    *,
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily | None = None,
    method: str,
) -> SeedGuessScore:
    family = family or HarmonicFamily()
    x = np.asarray(list(x_guess), dtype=float)
    residual = periodic_orbit_residual(x, int(p), float(K), family)
    dx = np.diff(x)
    endpoint_mismatch = float((x[0] + float(p)) - (x[-1] + (dx[-1] if dx.size else 0.0))) if len(x) > 1 else 0.0
    return SeedGuessScore(
        method=str(method),
        p=int(p),
        q=int(q),
        K=float(K),
        residual_inf=float(np.max(np.abs(residual))),
        residual_l2=float(np.linalg.norm(residual)),
        monotone_theta=bool(np.all(dx > -1e-12)) if dx.size else True,
        endpoint_mismatch=endpoint_mismatch,
        x0_phase=float(np.mod(x[0], 1.0)),
        x_guess=[float(v) for v in x],
    )


def build_seed_transfer_report(
    profile: PeriodicOrbitSeedProfile,
    *,
    target_p: int,
    target_q: int,
    target_K: float,
    family: HarmonicFamily | None = None,
) -> SeedTransferReport:
    family = family or HarmonicFamily()
    candidates = [
        score_seed_guess(
            _seed_by_lift_shape(profile, p=target_p, q=target_q),
            p=target_p,
            q=target_q,
            K=target_K,
            family=family,
            method='lift-shape',
        ),
        score_seed_guess(
            _seed_by_graph_step(profile, p=target_p, q=target_q),
            p=target_p,
            q=target_q,
            K=target_K,
            family=family,
            method='graph-step',
        ),
    ]
    candidates_sorted = sorted(candidates, key=lambda c: (c.residual_inf, c.residual_l2))
    best = candidates_sorted[0] if candidates_sorted else None
    notes = (
        'Two neighboring-approximant seed constructions were scored by the target residual. '
        'The selected seed is the lower-residual candidate, not a certified best seed.'
    )
    return SeedTransferReport(
        source_label=str(profile.source_label),
        target_label=f'{int(target_p)}/{int(target_q)}',
        target_p=int(target_p),
        target_q=int(target_q),
        target_K=float(target_K),
        candidate_scores=[c.to_dict() for c in candidates_sorted],
        selected_method=None if best is None else str(best.method),
        selected_residual_inf=None if best is None else float(best.residual_inf),
        selected_x_guess=None if best is None else list(best.x_guess),
        notes=notes,
    )


def solve_with_transferred_seed(
    profile: PeriodicOrbitSeedProfile,
    *,
    target_p: int,
    target_q: int,
    target_K: float,
    family: HarmonicFamily | None = None,
    tol: float = 1e-13,
    maxfev: int = 20000,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    rep = build_seed_transfer_report(
        profile,
        target_p=target_p,
        target_q=target_q,
        target_K=target_K,
        family=family,
    )
    if rep.selected_x_guess is None:
        return {
            'success': False,
            'message': 'no seed candidate was produced',
            'seed_transfer': rep.to_dict(),
        }
    sol = solve_periodic_orbit(
        p=int(target_p),
        q=int(target_q),
        K=float(target_K),
        family=family,
        x0=np.asarray(rep.selected_x_guess, dtype=float),
        tol=tol,
        maxfev=maxfev,
    )
    sol = dict(sol)
    sol['seed_transfer'] = rep.to_dict()
    return sol


__all__ = [
    'PeriodicOrbitSeedProfile',
    'SeedGuessScore',
    'SeedTransferReport',
    'build_seed_profile_from_orbit',
    'build_seed_transfer_report',
    'score_seed_guess',
    'solve_with_transferred_seed',
]
