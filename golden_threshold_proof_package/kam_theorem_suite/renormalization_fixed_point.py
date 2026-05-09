from __future__ import annotations

"""Fixed-point iteration scaffolding for the proxy renormalization operator.

This is the first concrete fixed-point surface in the repository's
renormalization workstream.  It iterates the proxy operator, records chart
radii and defects, and packages a candidate fixed-point scaffold for later
validated Newton / radii-polynomial work.
"""

from dataclasses import asdict, dataclass
from typing import Any

import math

from .standard_map import HarmonicFamily
from .renormalization import (
    build_renormalization_operator_certificate,
    apply_proxy_renormalization_operator,
)
from .renormalization_class import build_renormalization_chart_profile


@dataclass
class FixedPointIterationNode:
    iteration: int
    chart_radius_proxy: float
    stable_direction_proxy: float
    unstable_direction_proxy: float
    anchor_phase_abs: float
    fixed_point_defect: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RenormalizationFixedPointCertificate:
    family_label: str
    operator_parameters: dict[str, float]
    nodes: list[dict[str, Any]]
    candidate_family_harmonics: list[tuple[float, int, float]]
    final_chart_profile: dict[str, Any]
    defect_history_nonincreasing: bool
    radius_history_nonincreasing: bool
    final_fixed_point_defect: float
    contraction_ratio_estimate: float | None
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def _chart_defect(a: HarmonicFamily, b: HarmonicFamily) -> float:
    pa = build_renormalization_chart_profile(a)
    pb = build_renormalization_chart_profile(b)
    va = pa.chart_coordinates
    vb = pb.chart_coordinates
    diffs = [
        float(vb['anchor_amplitude_shift'] - va['anchor_amplitude_shift']),
        float(vb['anchor_phase_shift'] - va['anchor_phase_shift']),
        float(vb['higher_mode_energy'] - va['higher_mode_energy']),
        float(vb['weighted_mode_l1'] - va['weighted_mode_l1']),
    ]
    return float(math.sqrt(sum(d * d for d in diffs)))



def build_renormalization_fixed_point_certificate(
    family: HarmonicFamily,
    *,
    family_label: str = 'harmonic_family',
    iterations: int = 6,
    stable_damping: float = 0.6,
    phase_damping: float = 0.5,
    mode_penalty_power: float = 1.0,
    anchor_target_amplitude: float = 1.0,
) -> RenormalizationFixedPointCertificate:
    current = family
    prev_defect: float | None = None
    nodes: list[dict[str, Any]] = []
    defects: list[float] = []
    radii: list[float] = []

    for it in range(int(max(1, iterations))):
        cert = build_renormalization_operator_certificate(
            current,
            family_label=f'{family_label}_iter{it}',
            stable_damping=stable_damping,
            phase_damping=phase_damping,
            mode_penalty_power=mode_penalty_power,
            anchor_target_amplitude=anchor_target_amplitude,
        )
        nxt = HarmonicFamily(harmonics=list(cert.proxy_output_family['harmonics']))
        defect = _chart_defect(current, nxt)
        profile = build_renormalization_chart_profile(nxt)
        defects.append(float(defect))
        radii.append(float(profile.chart_radius_proxy))
        nodes.append(
            FixedPointIterationNode(
                iteration=it + 1,
                chart_radius_proxy=float(profile.chart_radius_proxy),
                stable_direction_proxy=float(profile.stable_direction_proxy),
                unstable_direction_proxy=float(profile.unstable_direction_proxy),
                anchor_phase_abs=float(abs(profile.chart_coordinates['anchor_phase_shift'])),
                fixed_point_defect=float(defect),
            ).to_dict()
        )
        current = nxt
        prev_defect = defect

    defect_noninc = all(defects[i + 1] <= defects[i] + 1e-12 for i in range(len(defects) - 1)) if len(defects) > 1 else True
    radius_noninc = all(radii[i + 1] <= radii[i] + 1e-12 for i in range(len(radii) - 1)) if len(radii) > 1 else True
    contraction_ratio = None
    if len(defects) >= 2 and defects[-2] > 0.0:
        contraction_ratio = float(defects[-1] / defects[-2])

    final_profile = build_renormalization_chart_profile(current)
    status = (
        'proxy-fixed-point-iteration-contracting'
        if defect_noninc and radius_noninc and (contraction_ratio is None or contraction_ratio <= 1.0 + 1e-12)
        else 'proxy-fixed-point-iteration-mixed'
    )
    return RenormalizationFixedPointCertificate(
        family_label=str(family_label),
        operator_parameters={
            'iterations': int(max(1, iterations)),
            'stable_damping': float(stable_damping),
            'phase_damping': float(phase_damping),
            'mode_penalty_power': float(mode_penalty_power),
            'anchor_target_amplitude': float(anchor_target_amplitude),
        },
        nodes=nodes,
        candidate_family_harmonics=list(current.harmonics),
        final_chart_profile=final_profile.to_dict(),
        defect_history_nonincreasing=bool(defect_noninc),
        radius_history_nonincreasing=bool(radius_noninc),
        final_fixed_point_defect=float(defects[-1] if defects else 0.0),
        contraction_ratio_estimate=contraction_ratio,
        theorem_status=status,
    )
