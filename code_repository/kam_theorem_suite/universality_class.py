from __future__ import annotations

"""Workstream-A scaffolding for theorem-grade family admissibility.

This module does *not* claim to prove the universality-class theorem.  Instead,
it creates the missing theorem-facing infrastructure that the rest of the codebase
can target: normalized family descriptors, analytic family norms, explicit
admissibility checks, and machine-readable certificates.

The current repository is still centered on finite-dimensional harmonic-family
experiments.  The purpose of this module is to make those families look more
like theorem objects:

* exact-symplectic and twist properties are recorded explicitly,
* normalization is separated from raw harmonic parameters,
* family-level analytic budgets are computed in a reusable format,
* admissibility decisions are emitted with margins rather than just booleans.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import math
import numpy as np

from .standard_map import HarmonicFamily


@dataclass
class FamilyAnalyticProfile:
    harmonic_count: int
    max_mode: int
    amplitude_l1: float
    amplitude_l2: float
    weighted_mode_l1: float
    weighted_mode_l2: float
    anchor_amplitude: float
    anchor_phase: float
    higher_mode_energy: float
    force_sup_bound: float
    dforce_sup_bound: float
    ddforce_sup_bound: float
    strip_width_proxy: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FamilyNormalizationProfile:
    anchor_amplitude: float
    anchor_phase: float
    amplitude_anchor_error: float
    phase_anchor_error: float
    higher_mode_energy: float
    weighted_mode_l1: float
    normalization_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UniversalityClassCertificate:
    family_label: str
    exact_symplectic_defect: float
    monotone_twist_lower_bound: float
    analytic_profile: dict[str, Any]
    normalization_profile: dict[str, Any]
    admissibility_margins: dict[str, float]
    admissibility_flags: dict[str, bool]
    admissible: bool
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _harmonic_arrays(family: HarmonicFamily) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    harmonics = list(getattr(family, 'harmonics', []) or [])
    if not harmonics:
        return np.array([1.0], dtype=float), np.array([1], dtype=int), np.array([0.0], dtype=float)
    amps = np.array([float(h[0]) for h in harmonics], dtype=float)
    modes = np.array([int(h[1]) for h in harmonics], dtype=int)
    phases = np.array([float(h[2]) for h in harmonics], dtype=float)
    return amps, modes, phases


def _safe_strip_proxy(max_mode: int, cap: float = 0.25) -> float:
    # Finite trigonometric polynomials are entire, but downstream theorem-facing
    # code still needs a finite strip scale.  We expose a conservative proxy that
    # decays with spectral complexity and is capped to remain numerically sane.
    return float(min(cap, max(0.02, 1.0 / max(4, 2 * int(max_mode)))))


def build_family_analytic_profile(family: HarmonicFamily) -> FamilyAnalyticProfile:
    amps, modes, phases = _harmonic_arrays(family)
    abs_amps = np.abs(amps)
    weighted = abs_amps * modes
    higher_mask = modes != 1
    higher_mode_energy = float(np.sqrt(np.sum(abs_amps[higher_mask] ** 2))) if np.any(higher_mask) else 0.0
    force_sup = float(np.sum(abs_amps / (2.0 * np.pi * modes)))
    dforce_sup = float(np.sum(abs_amps))
    ddforce_sup = float(np.sum(abs_amps * (2.0 * np.pi * modes)))

    anchor_candidates = np.flatnonzero(modes == 1)
    if len(anchor_candidates):
        idx = int(anchor_candidates[0])
        anchor_amplitude = float(amps[idx])
        anchor_phase = float(phases[idx])
    else:
        anchor_amplitude = 0.0
        anchor_phase = 0.0

    return FamilyAnalyticProfile(
        harmonic_count=int(len(amps)),
        max_mode=int(np.max(modes, initial=1)),
        amplitude_l1=float(np.sum(abs_amps)),
        amplitude_l2=float(np.sqrt(np.sum(abs_amps**2))),
        weighted_mode_l1=float(np.sum(weighted)),
        weighted_mode_l2=float(np.sqrt(np.sum(weighted**2))),
        anchor_amplitude=float(anchor_amplitude),
        anchor_phase=float(anchor_phase),
        higher_mode_energy=float(higher_mode_energy),
        force_sup_bound=float(force_sup),
        dforce_sup_bound=float(dforce_sup),
        ddforce_sup_bound=float(ddforce_sup),
        strip_width_proxy=_safe_strip_proxy(int(np.max(modes, initial=1))),
    )


def build_family_normalization_profile(
    family: HarmonicFamily,
    *,
    target_anchor_amplitude: float = 1.0,
    target_anchor_phase: float = 0.0,
) -> FamilyNormalizationProfile:
    analytic = build_family_analytic_profile(family)
    amp_err = abs(float(analytic.anchor_amplitude) - float(target_anchor_amplitude))
    phase_err = abs(float(analytic.anchor_phase) - float(target_anchor_phase))
    norm_score = math.sqrt(
        amp_err**2 + phase_err**2 + float(analytic.higher_mode_energy) ** 2 + 0.05 * float(analytic.weighted_mode_l1) ** 2
    )
    return FamilyNormalizationProfile(
        anchor_amplitude=float(analytic.anchor_amplitude),
        anchor_phase=float(analytic.anchor_phase),
        amplitude_anchor_error=float(amp_err),
        phase_anchor_error=float(phase_err),
        higher_mode_energy=float(analytic.higher_mode_energy),
        weighted_mode_l1=float(analytic.weighted_mode_l1),
        normalization_score=float(norm_score),
    )


def build_universality_class_certificate(
    family: HarmonicFamily,
    *,
    family_label: str = 'harmonic_family',
    amplitude_anchor_tol: float = 0.35,
    phase_anchor_tol: float = 0.5,
    higher_mode_energy_tol: float = 0.5,
    weighted_mode_budget: float = 3.0,
    max_mode_allowed: int = 8,
    min_strip_width_proxy: float = 0.03,
) -> UniversalityClassCertificate:
    analytic = build_family_analytic_profile(family)
    norm = build_family_normalization_profile(family)

    exact_symplectic_defect = 0.0  # by construction for the current lift-form family wrapper
    monotone_twist_lower_bound = 1.0  # d(theta')/dr = 1 for this family model

    margins = {
        'exact_symplectic_margin': float(1e-12 - exact_symplectic_defect),
        'twist_margin': float(monotone_twist_lower_bound),
        'anchor_amplitude_margin': float(amplitude_anchor_tol - norm.amplitude_anchor_error),
        'anchor_phase_margin': float(phase_anchor_tol - norm.phase_anchor_error),
        'higher_mode_energy_margin': float(higher_mode_energy_tol - analytic.higher_mode_energy),
        'weighted_mode_budget_margin': float(weighted_mode_budget - analytic.weighted_mode_l1),
        'max_mode_margin': float(max_mode_allowed - analytic.max_mode),
        'strip_width_margin': float(analytic.strip_width_proxy - min_strip_width_proxy),
    }
    flags = {k.replace('_margin', ''): (v >= 0.0) for k, v in margins.items()}
    admissible = bool(all(flags.values()))
    status = 'admissible' if admissible else 'outside_admissible_neighborhood'
    return UniversalityClassCertificate(
        family_label=str(family_label),
        exact_symplectic_defect=float(exact_symplectic_defect),
        monotone_twist_lower_bound=float(monotone_twist_lower_bound),
        analytic_profile=analytic.to_dict(),
        normalization_profile=norm.to_dict(),
        admissibility_margins=margins,
        admissibility_flags=flags,
        admissible=admissible,
        status=status,
    )
