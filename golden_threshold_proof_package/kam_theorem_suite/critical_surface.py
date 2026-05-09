from __future__ import annotations

"""Critical-surface / family-transversality bridge for Workstream A.

This module is the next theorem-facing step after the stable-manifold chart
scaffold.  It does *not* prove the golden critical-surface theorem.  Instead,
it builds the right bridge object for that later theorem:

* a one-parameter family path through the renormalization chart,
* local coordinates relative to the proxy stable-manifold chart,
* a codimension-one unstable-coordinate crossing diagnostic, and
* a machine-readable transversality certificate.

The intended use is to replace
    "there is a stable-manifold chart"
by
    "this one-parameter family appears to cross that chart transversely on a
     localized parameter window".
"""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .standard_map import HarmonicFamily
from .renormalization_class import (
    build_renormalization_chart_profile,
    build_renormalization_class_certificate,
)
from .stable_manifold import build_stable_manifold_chart_certificate


@dataclass
class CriticalSurfaceSample:
    parameter: float
    family_harmonics: list[tuple[float, int, float]]
    chart_coordinates: dict[str, float]
    stable_coordinates: list[float]
    unstable_coordinates: list[float]
    stable_coordinate_norm: float
    unstable_coordinate_scalar: float
    distance_to_stable_chart: float
    chart_radius_proxy: float
    admissible_near_chart: bool
    on_manifold_proxy: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FamilyTransversalityCertificate:
    family_label: str
    path_parameters: dict[str, float]
    stable_manifold_certificate: dict[str, Any]
    samples: list[dict[str, Any]]
    selected_crossing_interval: list[float] | None
    critical_parameter_estimate: float
    unstable_coordinate_derivative: float
    transversality_margin: float
    endpoint_unstable_values: list[float]
    minimal_unstable_gap: float
    supporting_chart_radius: float
    theorem_flags: dict[str, bool]
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CriticalSurfaceBridgeCertificate:
    family_label: str
    base_family_harmonics: list[tuple[float, int, float]]
    path_parameters: dict[str, float]
    transversality_certificate: dict[str, Any]
    critical_window_center: float
    critical_window_radius: float | None
    critical_surface_gap: float
    theorem_flags: dict[str, bool]
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def _perturb_family_along_path(
    family: HarmonicFamily,
    parameter: float,
    *,
    anchor_amplitude_slope: float,
    anchor_phase_slope: float,
    second_mode_slope: float,
    higher_mode_slope: float,
) -> HarmonicFamily:
    harmonics = list(getattr(family, 'harmonics', []) or [(1.0, 1, 0.0)])
    out: list[tuple[float, int, float]] = []
    saw_mode2 = False
    for amp, mode, phase in harmonics:
        amp_f = float(amp)
        phase_f = float(phase)
        mode_i = int(mode)
        if mode_i == 1:
            out.append((amp_f + float(parameter) * float(anchor_amplitude_slope), mode_i, phase_f + float(parameter) * float(anchor_phase_slope)))
        elif mode_i == 2:
            out.append((amp_f + float(parameter) * float(second_mode_slope), mode_i, phase_f))
            saw_mode2 = True
        else:
            out.append((amp_f + float(parameter) * float(higher_mode_slope) / float(mode_i), mode_i, phase_f))
    if not saw_mode2 and abs(second_mode_slope) > 0.0:
        out.append((float(parameter) * float(second_mode_slope), 2, 0.0))
    return HarmonicFamily(harmonics=out)



def _augmented_chart_vector(family: HarmonicFamily, parameter: float) -> np.ndarray:
    profile = build_renormalization_chart_profile(family)
    coords = profile.chart_coordinates
    return np.array(
        [
            float(coords['anchor_amplitude_shift']),
            float(coords['anchor_phase_shift']),
            float(coords['higher_mode_energy']),
            float(coords['weighted_mode_l1']),
            float(parameter),
        ],
        dtype=float,
    )



def _build_samples(
    family: HarmonicFamily,
    chart_cert,
    *,
    parameter_center: float,
    parameter_radius: float,
    sample_count: int,
    anchor_amplitude_slope: float,
    anchor_phase_slope: float,
    second_mode_slope: float,
    higher_mode_slope: float,
    manifold_tolerance_factor: float,
) -> tuple[list[CriticalSurfaceSample], np.ndarray, np.ndarray]:
    Pinv = np.asarray(chart_cert.inverse_coordinate_change_matrix, dtype=float)
    stable_dim = int(chart_cert.stable_dimension)
    unstable_dim = int(chart_cert.unstable_dimension)

    parameters = np.linspace(
        float(parameter_center) - float(parameter_radius),
        float(parameter_center) + float(parameter_radius),
        int(max(3, sample_count)),
        dtype=float,
    )
    samples: list[CriticalSurfaceSample] = []
    unstable_scalars: list[float] = []
    stable_norms: list[float] = []
    for t in parameters:
        fam_t = _perturb_family_along_path(
            family,
            float(t),
            anchor_amplitude_slope=anchor_amplitude_slope,
            anchor_phase_slope=anchor_phase_slope,
            second_mode_slope=second_mode_slope,
            higher_mode_slope=higher_mode_slope,
        )
        profile = build_renormalization_chart_profile(fam_t)
        vec = _augmented_chart_vector(fam_t, float(t))
        local = Pinv @ vec
        stable = local[:stable_dim]
        unstable = local[stable_dim:stable_dim + unstable_dim]
        stable_norm = float(np.linalg.norm(stable, ord=np.inf)) if stable.size else 0.0
        if unstable_dim == 1:
            unstable_scalar = float(unstable[0])
        else:
            unstable_scalar = float(np.linalg.norm(unstable, ord=np.inf))
        dist_to_chart = float(abs(unstable_scalar))
        on_chart = bool(dist_to_chart <= manifold_tolerance_factor * float(chart_cert.unstable_chart_radius + 1.0e-12))
        admissible = bool(build_renormalization_class_certificate(fam_t, family_label='path_sample').admissible_near_chart)
        sample = CriticalSurfaceSample(
            parameter=float(t),
            family_harmonics=list(fam_t.harmonics),
            chart_coordinates=dict(profile.chart_coordinates),
            stable_coordinates=[float(x) for x in stable.tolist()],
            unstable_coordinates=[float(x) for x in np.atleast_1d(unstable).tolist()],
            stable_coordinate_norm=float(stable_norm),
            unstable_coordinate_scalar=float(unstable_scalar),
            distance_to_stable_chart=float(dist_to_chart),
            chart_radius_proxy=float(profile.chart_radius_proxy),
            admissible_near_chart=admissible,
            on_manifold_proxy=on_chart,
        )
        samples.append(sample)
        unstable_scalars.append(unstable_scalar)
        stable_norms.append(stable_norm)
    return samples, np.asarray(parameters, dtype=float), np.asarray(unstable_scalars, dtype=float)



def _crossing_interval(parameters: np.ndarray, unstable_values: np.ndarray) -> tuple[list[float] | None, float]:
    for i in range(len(parameters) - 1):
        u0 = float(unstable_values[i])
        u1 = float(unstable_values[i + 1])
        if u0 == 0.0:
            return [float(parameters[i]), float(parameters[i])], float(parameters[i])
        if u0 * u1 <= 0.0:
            p0 = float(parameters[i])
            p1 = float(parameters[i + 1])
            if abs(u1 - u0) > 1.0e-15:
                alpha = -u0 / (u1 - u0)
                est = float(p0 + alpha * (p1 - p0))
            else:
                est = float(0.5 * (p0 + p1))
            return [float(p0), float(p1)], est
    idx = int(np.argmin(np.abs(unstable_values)))
    return None, float(parameters[idx])



def _derivative_estimate(parameters: np.ndarray, unstable_values: np.ndarray, critical_parameter_estimate: float) -> float:
    idx = int(np.argmin(np.abs(parameters - float(critical_parameter_estimate))))
    if 0 < idx < len(parameters) - 1:
        dp = float(parameters[idx + 1] - parameters[idx - 1])
        if abs(dp) > 0.0:
            return float((unstable_values[idx + 1] - unstable_values[idx - 1]) / dp)
    if idx < len(parameters) - 1:
        dp = float(parameters[idx + 1] - parameters[idx])
        if abs(dp) > 0.0:
            return float((unstable_values[idx + 1] - unstable_values[idx]) / dp)
    if idx > 0:
        dp = float(parameters[idx] - parameters[idx - 1])
        if abs(dp) > 0.0:
            return float((unstable_values[idx] - unstable_values[idx - 1]) / dp)
    return 0.0



def build_family_transversality_certificate(
    family: HarmonicFamily,
    *,
    family_label: str = 'harmonic_family',
    parameter_center: float = 0.0,
    parameter_radius: float = 0.1,
    sample_count: int = 9,
    anchor_amplitude_slope: float = -0.75,
    anchor_phase_slope: float = 0.2,
    second_mode_slope: float = 0.08,
    higher_mode_slope: float = 0.03,
    iterations: int = 6,
    stable_damping: float = 0.6,
    phase_damping: float = 0.5,
    mode_penalty_power: float = 1.0,
    anchor_target_amplitude: float = 1.0,
    perturbation_scale: float = 1.0e-3,
    inflation: float = 0.05,
    transverse_growth_floor: float = 1.02,
    stable_radius_fraction: float = 0.75,
    max_graph_slope: float = 0.95,
    transversality_floor: float = 0.25,
    manifold_tolerance_factor: float = 1.25,
    stable_localization_factor: float = 2.0,
) -> FamilyTransversalityCertificate:
    chart = build_stable_manifold_chart_certificate(
        family,
        family_label=family_label,
        iterations=iterations,
        stable_damping=stable_damping,
        phase_damping=phase_damping,
        mode_penalty_power=mode_penalty_power,
        anchor_target_amplitude=anchor_target_amplitude,
        perturbation_scale=perturbation_scale,
        inflation=inflation,
        transverse_growth_floor=transverse_growth_floor,
        stable_radius_fraction=stable_radius_fraction,
        max_graph_slope=max_graph_slope,
    )
    samples, parameters, unstable_values = _build_samples(
        family,
        chart,
        parameter_center=parameter_center,
        parameter_radius=parameter_radius,
        sample_count=sample_count,
        anchor_amplitude_slope=anchor_amplitude_slope,
        anchor_phase_slope=anchor_phase_slope,
        second_mode_slope=second_mode_slope,
        higher_mode_slope=higher_mode_slope,
        manifold_tolerance_factor=manifold_tolerance_factor,
    )
    interval, critical_est = _crossing_interval(parameters, unstable_values)
    deriv = _derivative_estimate(parameters, unstable_values, critical_est)
    trans_margin = float(abs(deriv) - float(transversality_floor))
    min_gap = float(np.min(np.abs(unstable_values))) if len(unstable_values) else 0.0
    stable_norms = [float(s.stable_coordinate_norm) for s in samples]
    center_idx = int(np.argmin(np.abs(parameters - float(critical_est))))
    center_stable = np.asarray(samples[center_idx].stable_coordinates, dtype=float) if samples else np.zeros((0,), dtype=float)
    stable_disp = []
    for s in samples:
        vec = np.asarray(s.stable_coordinates, dtype=float)
        stable_disp.append(float(np.linalg.norm(vec - center_stable, ord=np.inf)) if vec.size else 0.0)

    flags = {
        'stable_manifold_chart_identified': bool(chart.manifold_flags['enclosure_validated'] and chart.manifold_flags['stable_block_contracting'] and chart.manifold_flags['unstable_block_expanding']),
        'codim_one_unstable': bool(chart.unstable_dimension == 1),
        'sign_change_detected': bool(interval is not None),
        'transverse_crossing_detected': bool(abs(deriv) >= transversality_floor),
        'stable_coordinates_localized': bool(max(stable_disp, default=0.0) <= stable_localization_factor * float(parameter_radius + chart.stable_chart_radius + 1.0e-12)),
        'chart_admissible_along_path': bool(all(s.admissible_near_chart for s in samples)),
        'critical_window_bracketed': bool(interval is not None),
    }
    status = (
        'proxy-critical-surface-crossing-identified'
        if all(flags.values())
        else 'proxy-critical-surface-crossing-mixed'
    )

    return FamilyTransversalityCertificate(
        family_label=str(family_label),
        path_parameters={
            'parameter_center': float(parameter_center),
            'parameter_radius': float(parameter_radius),
            'sample_count': int(max(3, sample_count)),
            'anchor_amplitude_slope': float(anchor_amplitude_slope),
            'anchor_phase_slope': float(anchor_phase_slope),
            'second_mode_slope': float(second_mode_slope),
            'higher_mode_slope': float(higher_mode_slope),
            'transversality_floor': float(transversality_floor),
        },
        stable_manifold_certificate=chart.to_dict(),
        samples=[s.to_dict() for s in samples],
        selected_crossing_interval=interval,
        critical_parameter_estimate=float(critical_est),
        unstable_coordinate_derivative=float(deriv),
        transversality_margin=float(trans_margin),
        endpoint_unstable_values=[float(unstable_values[0]), float(unstable_values[-1])] if len(unstable_values) else [0.0, 0.0],
        minimal_unstable_gap=float(min_gap),
        supporting_chart_radius=float(chart.stable_chart_radius),
        theorem_flags=flags,
        theorem_status=status,
    )



def build_critical_surface_bridge_certificate(
    family: HarmonicFamily,
    *,
    family_label: str = 'harmonic_family',
    **kwargs: Any,
) -> CriticalSurfaceBridgeCertificate:
    trans = build_family_transversality_certificate(
        family,
        family_label=family_label,
        **kwargs,
    )
    interval = trans.selected_crossing_interval
    radius = None if interval is None else 0.5 * float(interval[1] - interval[0])
    gap = float(trans.minimal_unstable_gap)
    flags = {
        'transverse_crossing_identified': bool(trans.theorem_flags['transverse_crossing_detected']),
        'critical_window_localized': bool(interval is not None),
        'codim_one_surface_proxy': bool(trans.theorem_flags['codim_one_unstable']),
        'chart_bridge_usable': bool(trans.theorem_flags['stable_manifold_chart_identified'] and trans.theorem_flags['chart_admissible_along_path']),
    }
    status = (
        'proxy-critical-surface-family-bridge-identified'
        if all(flags.values())
        else 'proxy-critical-surface-family-bridge-mixed'
    )
    return CriticalSurfaceBridgeCertificate(
        family_label=str(family_label),
        base_family_harmonics=list(getattr(family, 'harmonics', []) or []),
        path_parameters=dict(trans.path_parameters),
        transversality_certificate=trans.to_dict(),
        critical_window_center=float(trans.critical_parameter_estimate),
        critical_window_radius=None if radius is None else float(radius),
        critical_surface_gap=gap,
        theorem_flags=flags,
        theorem_status=status,
    )
