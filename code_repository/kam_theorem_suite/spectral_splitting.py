from __future__ import annotations

"""Spectral-splitting bridge for the proxy renormalization workflow.

This module packages the first explicit stable/unstable splitting diagnostics on
 top of the stage-21 renormalization skeleton.  It remains a *proxy* package:
 the true theorem will require validated interval linear algebra around the real
 renormalization operator.  Here we do the next strongest honest thing:

* linearize the proxy operator near the candidate fixed point,
* augment the internal chart dynamics by a family-transverse direction proxy,
* expose the resulting stable/unstable cluster diagnostics, and
* emit a machine-readable splitting certificate with gap and domination data.
"""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .standard_map import HarmonicFamily
from .fixed_point_enclosure import build_fixed_point_enclosure_certificate
from .linearization_bounds import build_linearization_bounds_certificate
from .renormalization_class import build_renormalization_chart_profile


@dataclass
class SpectralSplittingCertificate:
    family_label: str
    candidate_family_harmonics: list[tuple[float, int, float]]
    base_jacobian_proxy: list[list[float]]
    augmented_jacobian_proxy: list[list[float]]
    transverse_multiplier: float
    eigenvalue_moduli: list[float]
    stable_moduli: list[float]
    unstable_moduli: list[float]
    stable_dimension: int
    unstable_dimension: int
    stable_spectral_radius: float
    unstable_spectral_floor: float
    spectral_gap_ratio: float
    domination_margin: float
    vector_condition_number: float
    supporting_certificates: dict[str, Any]
    splitting_flags: dict[str, bool]
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def build_spectral_splitting_certificate(
    family: HarmonicFamily,
    *,
    family_label: str = 'harmonic_family',
    iterations: int = 6,
    stable_damping: float = 0.6,
    phase_damping: float = 0.5,
    mode_penalty_power: float = 1.0,
    anchor_target_amplitude: float = 1.0,
    perturbation_scale: float = 1.0e-3,
    inflation: float = 0.05,
    transverse_growth_floor: float = 1.02,
) -> SpectralSplittingCertificate:
    enclosure = build_fixed_point_enclosure_certificate(
        family,
        family_label=family_label,
        iterations=iterations,
        stable_damping=stable_damping,
        phase_damping=phase_damping,
        mode_penalty_power=mode_penalty_power,
        anchor_target_amplitude=anchor_target_amplitude,
        perturbation_scale=perturbation_scale,
        inflation=inflation,
    )
    candidate = HarmonicFamily(harmonics=list(enclosure.candidate_family_harmonics))
    lin = build_linearization_bounds_certificate(
        candidate,
        family_label=f'{family_label}_candidate',
        perturbation_scale=perturbation_scale,
        stable_damping=stable_damping,
        phase_damping=phase_damping,
        mode_penalty_power=mode_penalty_power,
        anchor_target_amplitude=anchor_target_amplitude,
        inflation=inflation,
    )
    chart = build_renormalization_chart_profile(candidate)

    J = np.asarray(lin.jacobian_proxy, dtype=float)
    transverse_multiplier = float(max(transverse_growth_floor, 1.0 + 20.0 * chart.transversality_proxy))
    Aug = np.zeros((J.shape[0] + 1, J.shape[1] + 1), dtype=float)
    Aug[:-1, :-1] = J
    Aug[-1, -1] = transverse_multiplier

    eigvals, eigvecs = np.linalg.eig(Aug)
    moduli = np.sort(np.abs(eigvals))
    stable_moduli = [float(x) for x in moduli if x < 1.0 - 1e-12]
    unstable_moduli = [float(x) for x in moduli if x > 1.0 + 1e-12]
    stable_radius = float(max(stable_moduli) if stable_moduli else 0.0)
    unstable_floor = float(min(unstable_moduli) if unstable_moduli else 0.0)
    gap_ratio = float(unstable_floor / max(stable_radius, 1e-12)) if unstable_moduli else 0.0
    domination_margin = float(unstable_floor - stable_radius) if unstable_moduli else float(-stable_radius)
    try:
        cond = float(np.linalg.cond(eigvecs))
    except np.linalg.LinAlgError:
        cond = float('inf')

    flags = {
        'enclosure_validated': bool(enclosure.theorem_status == 'proxy-fixed-point-enclosure-validated'),
        'one_dimensional_unstable': bool(len(unstable_moduli) == 1),
        'stable_cluster_contracting': bool(stable_radius < 1.0),
        'spectral_gap_identified': bool(gap_ratio > 1.0 + 1e-12),
        'dominated_splitting_proxy': bool(domination_margin > 0.0),
        'eigenbasis_reasonable': bool(cond < 1.0e6),
    }
    status = (
        'proxy-spectral-splitting-identified'
        if all(flags.values())
        else 'proxy-spectral-splitting-mixed'
    )
    return SpectralSplittingCertificate(
        family_label=str(family_label),
        candidate_family_harmonics=list(enclosure.candidate_family_harmonics),
        base_jacobian_proxy=[[float(x) for x in row] for row in J.tolist()],
        augmented_jacobian_proxy=[[float(x) for x in row] for row in Aug.tolist()],
        transverse_multiplier=float(transverse_multiplier),
        eigenvalue_moduli=[float(x) for x in moduli.tolist()],
        stable_moduli=stable_moduli,
        unstable_moduli=unstable_moduli,
        stable_dimension=int(len(stable_moduli)),
        unstable_dimension=int(len(unstable_moduli)),
        stable_spectral_radius=float(stable_radius),
        unstable_spectral_floor=float(unstable_floor),
        spectral_gap_ratio=float(gap_ratio),
        domination_margin=float(domination_margin),
        vector_condition_number=float(cond),
        supporting_certificates={
            'fixed_point_enclosure': enclosure.to_dict(),
            'linearization_bounds': lin.to_dict(),
            'chart_profile': chart.to_dict(),
        },
        splitting_flags=flags,
        theorem_status=status,
    )
