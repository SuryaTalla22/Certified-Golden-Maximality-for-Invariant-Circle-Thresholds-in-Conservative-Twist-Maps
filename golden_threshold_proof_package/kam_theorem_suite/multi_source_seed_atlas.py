from __future__ import annotations

"""Multi-source seed atlases for neighboring periodic approximants.

This stage upgrades single-source seed transfer into a small continuation atlas.
Instead of reusing only the nearest successful approximant, callers may gather
several nearby seed profiles, transport each one to the target rational, and
then score both individual and blended candidates.

The atlas is intentionally transparent:

* source selection is arithmetic-first (nearest rotation number, then larger q),
* every single-source transported candidate is retained and scored,
* atlas blends are simple and inspectable (weighted average, top-2 mean,
  componentwise median), and
* the selected seed is whichever candidate attains the lowest target residual
  after optional one-step orbit refinement.

This is still a proof-bridge engineering layer.  The theorem content remains in
whatever downstream certificate ultimately accepts or rejects the seeded branch.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence

import numpy as np

from .seed_transfer import score_seed_guess, build_seed_transfer_report
from .seeded_campaigns import SeedBankEntry
from .standard_map import HarmonicFamily, solve_periodic_orbit, periodic_orbit_residual


@dataclass
class AtlasSourceSelection:
    label: str
    p: int
    q: int
    rho: float
    K_center: float
    rho_distance: float
    rank: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AtlasCandidateScore:
    method: str
    source_labels: list[str]
    source_weights: list[float]
    residual_inf: float
    residual_l2: float
    solver_success: bool
    solver_residual_inf: float | None
    solver_residual_l2: float | None
    x_guess: list[float]
    x_refined: list[float] | None
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiSourceSeedAtlasReport:
    target_label: str
    target_p: int
    target_q: int
    target_K: float
    selected_sources: list[dict[str, Any]]
    single_source_transfers: list[dict[str, Any]]
    atlas_candidates: list[dict[str, Any]]
    selected_method: str | None
    selected_source_labels: list[str]
    selected_residual_inf: float | None
    selected_solver_residual_inf: float | None
    selected_x_guess: list[float] | None
    selected_x_refined: list[float] | None
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _target_rho(p: int, q: int) -> float:
    return float(p) / float(q)


def _select_sources(
    seed_bank: Sequence[SeedBankEntry],
    *,
    target_rho: float,
    max_sources: int,
) -> list[tuple[SeedBankEntry, AtlasSourceSelection]]:
    rows: list[tuple[SeedBankEntry, AtlasSourceSelection]] = []
    for entry in seed_bank:
        row = AtlasSourceSelection(
            label=str(entry.label),
            p=int(entry.p),
            q=int(entry.q),
            rho=float(entry.rho),
            K_center=float(entry.K_center),
            rho_distance=abs(float(entry.rho) - float(target_rho)),
            rank=0,
        )
        rows.append((entry, row))
    rows.sort(key=lambda pair: (pair[1].rho_distance, -pair[1].q, abs(pair[1].K_center)))
    kept = rows[: max(0, int(max_sources))]
    out: list[tuple[SeedBankEntry, AtlasSourceSelection]] = []
    for idx, (entry, row) in enumerate(kept):
        row.rank = idx
        out.append((entry, row))
    return out


def _align_guess_to_reference(x: np.ndarray, reference: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    ref = np.asarray(reference, dtype=float)
    if x.shape != ref.shape:
        raise ValueError('candidate/reference shapes must match for atlas blending')
    offset = float(np.median(ref - x))
    shift = float(np.round(offset))
    return x + shift


def _normalize_weights(weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    weights = np.clip(weights, 0.0, np.inf)
    total = float(np.sum(weights))
    if not np.isfinite(total) or total <= 0.0:
        return np.ones_like(weights) / float(len(weights))
    return weights / total


def _blend_candidates(
    aligned_candidates: Sequence[np.ndarray],
    *,
    weights: Sequence[float],
    method: str,
) -> np.ndarray:
    arr = np.stack([np.asarray(c, dtype=float) for c in aligned_candidates], axis=0)
    if method == 'weighted-average':
        w = _normalize_weights(np.asarray(weights, dtype=float))
        return np.tensordot(w, arr, axes=(0, 0))
    if method == 'top2-average':
        arr2 = arr[:2]
        return np.mean(arr2, axis=0)
    if method == 'component-median':
        return np.median(arr, axis=0)
    raise ValueError(f'unknown atlas blend method: {method}')


def _maybe_refine_candidate(
    x_guess: np.ndarray,
    *,
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily,
) -> tuple[bool, np.ndarray | None, float | None, float | None]:
    sol = solve_periodic_orbit(
        p=int(p),
        q=int(q),
        K=float(K),
        family=family,
        x0=np.asarray(x_guess, dtype=float),
    )
    if not sol.get('success', False):
        return False, None, None, None
    x = np.asarray(sol['x'], dtype=float)
    resid = periodic_orbit_residual(x, int(p), float(K), family)
    return True, x, float(np.max(np.abs(resid))), float(np.linalg.norm(resid))


def _score_atlas_candidate(
    x_guess: Iterable[float],
    *,
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily,
    method: str,
    source_labels: Sequence[str],
    source_weights: Sequence[float],
    refine: bool,
    notes: str,
) -> AtlasCandidateScore:
    base = score_seed_guess(
        x_guess,
        p=int(p),
        q=int(q),
        K=float(K),
        family=family,
        method=str(method),
    )
    solver_success = False
    x_refined = None
    solver_resid_inf = None
    solver_resid_l2 = None
    if refine:
        solver_success, x_refined, solver_resid_inf, solver_resid_l2 = _maybe_refine_candidate(
            np.asarray(base.x_guess, dtype=float),
            p=int(p),
            q=int(q),
            K=float(K),
            family=family,
        )
    return AtlasCandidateScore(
        method=str(method),
        source_labels=[str(s) for s in source_labels],
        source_weights=[float(w) for w in source_weights],
        residual_inf=float(base.residual_inf),
        residual_l2=float(base.residual_l2),
        solver_success=bool(solver_success),
        solver_residual_inf=None if solver_resid_inf is None else float(solver_resid_inf),
        solver_residual_l2=None if solver_resid_l2 is None else float(solver_resid_l2),
        x_guess=list(base.x_guess),
        x_refined=None if x_refined is None else [float(v) for v in x_refined],
        notes=str(notes),
    )


def _candidate_sort_key(candidate: AtlasCandidateScore) -> tuple[float, float, float, float]:
    refined = candidate.solver_residual_inf if candidate.solver_residual_inf is not None else np.inf
    return (
        float(refined),
        0.0 if candidate.solver_success else 1.0,
        float(candidate.residual_inf),
        float(candidate.residual_l2),
    )


def build_multi_source_seed_atlas(
    seed_bank: Sequence[SeedBankEntry],
    *,
    target_p: int,
    target_q: int,
    target_K: float,
    family: HarmonicFamily | None = None,
    max_sources: int = 3,
    refine_candidates: bool = True,
    include_component_median: bool = True,
) -> MultiSourceSeedAtlasReport:
    family = family or HarmonicFamily()
    target_p = int(target_p)
    target_q = int(target_q)
    target_K = float(target_K)
    rho = _target_rho(target_p, target_q)
    selected = _select_sources(seed_bank, target_rho=rho, max_sources=max_sources)

    selected_rows = [row.to_dict() for _, row in selected]
    transfers: list[dict[str, Any]] = []
    individual_candidates: list[AtlasCandidateScore] = []
    raw_guesses: list[np.ndarray] = []
    raw_labels: list[str] = []
    raw_weights: list[float] = []

    for entry, row in selected:
        from .seed_transfer import PeriodicOrbitSeedProfile  # local import keeps module light

        profile = PeriodicOrbitSeedProfile(**entry.seed_profile)
        transfer = build_seed_transfer_report(
            profile,
            target_p=target_p,
            target_q=target_q,
            target_K=target_K,
            family=family,
        ).to_dict()
        transfers.append(transfer)
        x_guess = transfer.get('selected_x_guess')
        if x_guess is None:
            continue
        x_arr = np.asarray(x_guess, dtype=float)
        weight = 1.0 / max(row.rho_distance, 1e-9)
        candidate = _score_atlas_candidate(
            x_arr,
            p=target_p,
            q=target_q,
            K=target_K,
            family=family,
            method=f'single:{transfer.get("selected_method") or "unknown"}',
            source_labels=[entry.label],
            source_weights=[weight],
            refine=refine_candidates,
            notes='Single-source transported seed from the atlas source bank.',
        )
        individual_candidates.append(candidate)
        raw_guesses.append(x_arr)
        raw_labels.append(str(entry.label))
        raw_weights.append(float(weight))

    atlas_candidates: list[AtlasCandidateScore] = list(individual_candidates)
    if raw_guesses:
        reference = raw_guesses[0]
        aligned = [_align_guess_to_reference(g, reference) for g in raw_guesses]
        if len(aligned) >= 2:
            blended = _blend_candidates(aligned, weights=raw_weights, method='weighted-average')
            atlas_candidates.append(
                _score_atlas_candidate(
                    blended,
                    p=target_p,
                    q=target_q,
                    K=target_K,
                    family=family,
                    method='atlas:weighted-average',
                    source_labels=raw_labels,
                    source_weights=raw_weights,
                    refine=refine_candidates,
                    notes='Inverse-rho-distance weighted average of aligned transported seeds.',
                )
            )
            top2 = _blend_candidates(aligned[:2], weights=raw_weights[:2], method='top2-average')
            atlas_candidates.append(
                _score_atlas_candidate(
                    top2,
                    p=target_p,
                    q=target_q,
                    K=target_K,
                    family=family,
                    method='atlas:top2-average',
                    source_labels=raw_labels[:2],
                    source_weights=raw_weights[:2],
                    refine=refine_candidates,
                    notes='Simple mean of the two closest aligned transported seeds.',
                )
            )
            if include_component_median and len(aligned) >= 3:
                med = _blend_candidates(aligned, weights=raw_weights, method='component-median')
                atlas_candidates.append(
                    _score_atlas_candidate(
                        med,
                        p=target_p,
                        q=target_q,
                        K=target_K,
                        family=family,
                        method='atlas:component-median',
                        source_labels=raw_labels,
                        source_weights=raw_weights,
                        refine=refine_candidates,
                        notes='Componentwise median of aligned transported seeds.',
                    )
                )

    atlas_candidates.sort(key=_candidate_sort_key)
    best = atlas_candidates[0] if atlas_candidates else None
    notes = (
        'The atlas keeps every single-source candidate and augments them with simple aligned blends. '
        'Selection is by lowest refined residual when a local solve succeeds, otherwise by raw target residual.'
    )
    return MultiSourceSeedAtlasReport(
        target_label=f'{target_p}/{target_q}',
        target_p=target_p,
        target_q=target_q,
        target_K=target_K,
        selected_sources=selected_rows,
        single_source_transfers=transfers,
        atlas_candidates=[c.to_dict() for c in atlas_candidates],
        selected_method=None if best is None else str(best.method),
        selected_source_labels=[] if best is None else list(best.source_labels),
        selected_residual_inf=None if best is None else float(best.residual_inf),
        selected_solver_residual_inf=None if best is None else best.solver_residual_inf,
        selected_x_guess=None if best is None else list(best.x_guess),
        selected_x_refined=None if best is None else best.x_refined,
        notes=notes,
    )


__all__ = [
    'AtlasSourceSelection',
    'AtlasCandidateScore',
    'MultiSourceSeedAtlasReport',
    'build_multi_source_seed_atlas',
]
