from __future__ import annotations

"""Fixed-point enclosure bridge for the proxy renormalization workflow.

This module upgrades the stage-21 fixed-point iteration scaffold into a more
explicit theorem-facing enclosure object.  It still does *not* claim a fully
rigorous interval-Newton proof of the renormalization fixed point.  Instead, it
packages the current ingredients in the correct shape:

* a candidate center obtained from the proxy operator iteration,
* a local chart defect at that center,
* a contraction bound from the chart linearization,
* a Banach-style invariant-ball radius estimate, and
* machine-readable enclosure margins for downstream spectral work.

The point is to replace "there is an iteration history" by "there is a concrete
candidate fixed-point neighborhood with an explicit radius and margin".
"""

from dataclasses import asdict, dataclass
from typing import Any

from .standard_map import HarmonicFamily
from .renormalization_fixed_point import build_renormalization_fixed_point_certificate
from .linearization_bounds import build_linearization_bounds_certificate
from .renormalization_class import build_renormalization_class_certificate


@dataclass
class FixedPointEnclosureCertificate:
    family_label: str
    candidate_family_harmonics: list[tuple[float, int, float]]
    candidate_chart_profile: dict[str, Any]
    contraction_bound: float
    contraction_margin: float
    local_defect: float
    enclosure_radius: float
    invariance_margin: float
    coordinate_enclosure: dict[str, dict[str, float]]
    supporting_certificates: dict[str, Any]
    enclosure_flags: dict[str, bool]
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def build_fixed_point_enclosure_certificate(
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
    radius_safety_factor: float = 1.1,
) -> FixedPointEnclosureCertificate:
    fp = build_renormalization_fixed_point_certificate(
        family,
        family_label=family_label,
        iterations=iterations,
        stable_damping=stable_damping,
        phase_damping=phase_damping,
        mode_penalty_power=mode_penalty_power,
        anchor_target_amplitude=anchor_target_amplitude,
    )
    candidate = HarmonicFamily(harmonics=list(fp.candidate_family_harmonics))
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
    chart = build_renormalization_class_certificate(candidate, family_label=f'{family_label}_candidate')

    contraction_bound = float(min(max(lin.stable_radius_upper_bound, 0.0), 0.999999))
    contraction_margin = float(1.0 - contraction_bound)
    local_defect = float(fp.final_fixed_point_defect)
    if contraction_margin <= 1e-12:
        enclosure_radius = float('inf')
        invariance_margin = float('-inf')
    else:
        base_radius = local_defect / contraction_margin
        enclosure_radius = float(max(0.0, radius_safety_factor * base_radius))
        invariance_margin = float(enclosure_radius * contraction_margin - local_defect)

    coords = dict(fp.final_chart_profile['chart_coordinates'])
    coordinate_enclosure = {
        key: {
            'center': float(val),
            'radius': float(enclosure_radius),
            'lower': float(val - enclosure_radius),
            'upper': float(val + enclosure_radius),
        }
        for key, val in coords.items()
        if key != 'strip_complexity'
    }

    flags = {
        'iteration_contracting': bool(fp.defect_history_nonincreasing and fp.radius_history_nonincreasing),
        'chart_contracting': bool(contraction_margin > 0.0),
        'enclosure_positive_radius': bool(enclosure_radius >= 0.0),
        'invariance_margin_positive': bool(invariance_margin >= -1e-12),
        'candidate_admissible_near_chart': bool(chart.admissible_near_chart),
    }
    status = (
        'proxy-fixed-point-enclosure-validated'
        if all(flags.values())
        else 'proxy-fixed-point-enclosure-mixed'
    )
    return FixedPointEnclosureCertificate(
        family_label=str(family_label),
        candidate_family_harmonics=list(fp.candidate_family_harmonics),
        candidate_chart_profile=dict(fp.final_chart_profile),
        contraction_bound=float(contraction_bound),
        contraction_margin=float(contraction_margin),
        local_defect=float(local_defect),
        enclosure_radius=float(enclosure_radius),
        invariance_margin=float(invariance_margin),
        coordinate_enclosure=coordinate_enclosure,
        supporting_certificates={
            'fixed_point_iteration': fp.to_dict(),
            'linearization_bounds': lin.to_dict(),
            'renormalization_class': chart.to_dict(),
        },
        enclosure_flags=flags,
        theorem_status=status,
    )
