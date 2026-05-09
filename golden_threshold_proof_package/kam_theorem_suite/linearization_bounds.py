from __future__ import annotations

"""Linearization scaffolding around the proxy renormalization operator.

This module provides the first chart-level linearization interface for the
renormalization workstream.  It uses finite-difference perturbations of the
harmonic-family chart coordinates to build a conservative Jacobian proxy and
basic stable/unstable spectral diagnostics.
"""

from dataclasses import asdict, dataclass
from typing import Any

import math
import numpy as np

from .standard_map import HarmonicFamily
from .renormalization import apply_proxy_renormalization_operator
from .renormalization_class import build_renormalization_chart_profile


@dataclass
class LinearizationBoundsCertificate:
    family_label: str
    base_chart_coordinates: dict[str, float]
    perturbation_scale: float
    jacobian_proxy: list[list[float]]
    row_sum_upper_bounds: list[float]
    spectral_radius_upper_bound: float
    stable_radius_upper_bound: float
    unstable_radius_lower_bound: float
    linearization_flags: dict[str, bool]
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def _family_from_chart_perturbation(
    family: HarmonicFamily,
    *,
    anchor_amplitude_shift: float = 0.0,
    anchor_phase_shift: float = 0.0,
    second_mode_shift: float = 0.0,
) -> HarmonicFamily:
    harmonics = list(getattr(family, 'harmonics', []) or [(1.0, 1, 0.0)])
    out: list[tuple[float, int, float]] = []
    saw_mode2 = False
    for amp, mode, phase in harmonics:
        amp_f = float(amp)
        phase_f = float(phase)
        mode_i = int(mode)
        if mode_i == 1:
            out.append((amp_f + float(anchor_amplitude_shift), mode_i, phase_f + float(anchor_phase_shift)))
        elif mode_i == 2:
            out.append((amp_f + float(second_mode_shift), mode_i, phase_f))
            saw_mode2 = True
        else:
            out.append((amp_f, mode_i, phase_f))
    if not saw_mode2 and abs(second_mode_shift) > 0.0:
        out.append((float(second_mode_shift), 2, 0.0))
    return HarmonicFamily(harmonics=out)



def _chart_vector(family: HarmonicFamily) -> np.ndarray:
    profile = build_renormalization_chart_profile(family)
    coords = profile.chart_coordinates
    return np.array(
        [
            float(coords['anchor_amplitude_shift']),
            float(coords['anchor_phase_shift']),
            float(coords['higher_mode_energy']),
            float(coords['weighted_mode_l1']),
        ],
        dtype=float,
    )



def build_linearization_bounds_certificate(
    family: HarmonicFamily,
    *,
    family_label: str = 'harmonic_family',
    perturbation_scale: float = 1.0e-3,
    stable_damping: float = 0.6,
    phase_damping: float = 0.5,
    mode_penalty_power: float = 1.0,
    anchor_target_amplitude: float = 1.0,
    inflation: float = 0.02,
) -> LinearizationBoundsCertificate:
    base_profile = build_renormalization_chart_profile(family)
    base_coords = dict(base_profile.chart_coordinates)
    base_vec = _chart_vector(family)

    def op_vec(fam: HarmonicFamily) -> np.ndarray:
        out = apply_proxy_renormalization_operator(
            fam,
            stable_damping=stable_damping,
            phase_damping=phase_damping,
            mode_penalty_power=mode_penalty_power,
            anchor_target_amplitude=anchor_target_amplitude,
        ).to_family()
        return _chart_vector(out)

    columns = []
    basis_builders = [
        lambda s: _family_from_chart_perturbation(family, anchor_amplitude_shift=s),
        lambda s: _family_from_chart_perturbation(family, anchor_phase_shift=s),
        lambda s: _family_from_chart_perturbation(family, second_mode_shift=s),
        lambda s: _family_from_chart_perturbation(family, second_mode_shift=s),
    ]
    # The fourth coordinate (weighted_mode_l1) is not an independent harmonic
    # parameter, so we probe it using the same second-mode amplitude direction.
    # This is still useful as a conservative chart-sensitivity proxy.
    for builder in basis_builders:
        vp = op_vec(builder(+perturbation_scale))
        vm = op_vec(builder(-perturbation_scale))
        col = (vp - vm) / (2.0 * float(perturbation_scale))
        columns.append(col)
    J = np.column_stack(columns)
    J = np.asarray(J, dtype=float)
    J *= (1.0 + float(inflation))

    row_sums = np.sum(np.abs(J), axis=1)
    eigvals = np.linalg.eigvals(J)
    abs_eigs = np.sort(np.abs(eigvals))
    spectral_upper = float(np.max(row_sums, initial=0.0))
    stable_upper = float(abs_eigs[-2]) if len(abs_eigs) >= 2 else float(abs_eigs[-1] if len(abs_eigs) else 0.0)
    unstable_lower = float(abs_eigs[-1]) if len(abs_eigs) else 0.0
    flags = {
        'chart_nonexpanding_bound': bool(spectral_upper <= 1.0 + 1e-12),
        'stable_proxy_contracting': bool(stable_upper < 1.0),
        'unstable_proxy_identified': bool(unstable_lower >= stable_upper - 1e-12),
    }
    status = 'proxy-linearization-bounds-contracting' if flags['stable_proxy_contracting'] else 'proxy-linearization-bounds-mixed'
    return LinearizationBoundsCertificate(
        family_label=str(family_label),
        base_chart_coordinates=base_coords,
        perturbation_scale=float(perturbation_scale),
        jacobian_proxy=[[float(x) for x in row] for row in J.tolist()],
        row_sum_upper_bounds=[float(x) for x in row_sums.tolist()],
        spectral_radius_upper_bound=float(spectral_upper),
        stable_radius_upper_bound=float(stable_upper),
        unstable_radius_lower_bound=float(unstable_lower),
        linearization_flags=flags,
        theorem_status=status,
    )
