from __future__ import annotations

"""Localized transversality-window package for the critical-surface bridge.

This module tightens the stage-24 family-transversality bridge into a more
localized window object. It does *not* prove a rigorous critical-surface
transversality theorem for the true renormalization operator. Instead it adds:

* recursive localization of a codimension-one sign-changing family window,
* a denser unstable-coordinate evaluation layer on that window,
* slope and slope-variation diagnostics giving a derivative lower-bound proxy,
* machine-readable window admissibility and localization margins.

The goal is to replace
    "a family path appears to cross the stable-manifold chart"
by
    "there is a localized family window with endpoint sign separation,
     monotonicity diagnostics, and a positive derivative floor proxy".
"""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .critical_surface import (
    _augmented_chart_vector,
    _crossing_interval,
    _perturb_family_along_path,
    build_critical_surface_bridge_certificate,
    build_family_transversality_certificate,
)
from .renormalization_class import build_renormalization_class_certificate
from .stable_manifold import build_stable_manifold_chart_certificate
from .standard_map import HarmonicFamily


@dataclass
class TransversalityWindowSample:
    parameter: float
    unstable_coordinate_scalar: float
    stable_coordinate_norm: float
    admissible_near_chart: bool
    on_manifold_proxy: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TransversalityWindowCertificate:
    family_label: str
    path_parameters: dict[str, float]
    supporting_certificates: dict[str, Any]
    initial_window: list[float] | None
    localized_window: list[float] | None
    critical_parameter_estimate: float
    endpoint_unstable_values: list[float]
    center_unstable_value: float
    window_radius: float | None
    sample_count_used: int
    maximum_refinement_depth_reached: int
    derivative_samples: list[float]
    derivative_floor_proxy: float
    derivative_variation_proxy: float
    transversality_margin: float
    stable_localization_margin: float
    window_samples: list[dict[str, Any]]
    theorem_flags: dict[str, bool]
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedCriticalSurfaceBridgeCertificate:
    family_label: str
    path_parameters: dict[str, float]
    transversality_window_certificate: dict[str, Any]
    coarse_bridge_certificate: dict[str, Any]
    localized_center: float
    localized_radius: float | None
    derivative_floor_proxy: float
    transversality_margin: float
    theorem_flags: dict[str, bool]
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _path_evaluator(
    family: HarmonicFamily,
    chart_cert,
    parameter: float,
    *,
    anchor_amplitude_slope: float,
    anchor_phase_slope: float,
    second_mode_slope: float,
    higher_mode_slope: float,
    manifold_tolerance_factor: float,
) -> TransversalityWindowSample:
    Pinv = np.asarray(chart_cert.inverse_coordinate_change_matrix, dtype=float)
    stable_dim = int(chart_cert.stable_dimension)
    unstable_dim = int(chart_cert.unstable_dimension)
    fam_t = _perturb_family_along_path(
        family,
        float(parameter),
        anchor_amplitude_slope=anchor_amplitude_slope,
        anchor_phase_slope=anchor_phase_slope,
        second_mode_slope=second_mode_slope,
        higher_mode_slope=higher_mode_slope,
    )
    vec = _augmented_chart_vector(fam_t, float(parameter))
    local = Pinv @ vec
    stable = local[:stable_dim]
    unstable = local[stable_dim:stable_dim + unstable_dim]
    stable_norm = float(np.linalg.norm(stable, ord=np.inf)) if stable.size else 0.0
    if unstable_dim == 1:
        unstable_scalar = float(unstable[0])
    else:
        unstable_scalar = float(np.linalg.norm(unstable, ord=np.inf))
    admissible = bool(build_renormalization_class_certificate(fam_t, family_label='window_sample').admissible_near_chart)
    on_manifold = bool(abs(unstable_scalar) <= manifold_tolerance_factor * float(chart_cert.unstable_chart_radius + 1e-12))
    return TransversalityWindowSample(
        parameter=float(parameter),
        unstable_coordinate_scalar=float(unstable_scalar),
        stable_coordinate_norm=float(stable_norm),
        admissible_near_chart=admissible,
        on_manifold_proxy=on_manifold,
    )



def _window_sign_change(
    family: HarmonicFamily,
    chart_cert,
    *,
    lo: float,
    hi: float,
    anchor_amplitude_slope: float,
    anchor_phase_slope: float,
    second_mode_slope: float,
    higher_mode_slope: float,
    manifold_tolerance_factor: float,
) -> tuple[bool, TransversalityWindowSample, TransversalityWindowSample]:
    left = _path_evaluator(
        family,
        chart_cert,
        float(lo),
        anchor_amplitude_slope=anchor_amplitude_slope,
        anchor_phase_slope=anchor_phase_slope,
        second_mode_slope=second_mode_slope,
        higher_mode_slope=higher_mode_slope,
        manifold_tolerance_factor=manifold_tolerance_factor,
    )
    right = _path_evaluator(
        family,
        chart_cert,
        float(hi),
        anchor_amplitude_slope=anchor_amplitude_slope,
        anchor_phase_slope=anchor_phase_slope,
        second_mode_slope=second_mode_slope,
        higher_mode_slope=higher_mode_slope,
        manifold_tolerance_factor=manifold_tolerance_factor,
    )
    u0 = float(left.unstable_coordinate_scalar)
    u1 = float(right.unstable_coordinate_scalar)
    sign_change = bool(u0 == 0.0 or u1 == 0.0 or u0 * u1 <= 0.0)
    return sign_change, left, right



def _refine_window(
    family: HarmonicFamily,
    chart_cert,
    *,
    initial_window: list[float] | None,
    anchor_amplitude_slope: float,
    anchor_phase_slope: float,
    second_mode_slope: float,
    higher_mode_slope: float,
    manifold_tolerance_factor: float,
    max_depth: int,
    target_radius: float,
) -> tuple[list[float] | None, int]:
    if initial_window is None:
        return None, 0
    lo = float(initial_window[0])
    hi = float(initial_window[1])
    depth = 0
    for depth in range(1, int(max_depth) + 1):
        width = hi - lo
        if width <= 2.0 * float(target_radius):
            return [float(lo), float(hi)], depth
        mid = 0.5 * (lo + hi)
        left_change, _, _ = _window_sign_change(
            family,
            chart_cert,
            lo=lo,
            hi=mid,
            anchor_amplitude_slope=anchor_amplitude_slope,
            anchor_phase_slope=anchor_phase_slope,
            second_mode_slope=second_mode_slope,
            higher_mode_slope=higher_mode_slope,
            manifold_tolerance_factor=manifold_tolerance_factor,
        )
        right_change, _, _ = _window_sign_change(
            family,
            chart_cert,
            lo=mid,
            hi=hi,
            anchor_amplitude_slope=anchor_amplitude_slope,
            anchor_phase_slope=anchor_phase_slope,
            second_mode_slope=second_mode_slope,
            higher_mode_slope=higher_mode_slope,
            manifold_tolerance_factor=manifold_tolerance_factor,
        )
        if left_change and not right_change:
            hi = mid
        elif right_change and not left_change:
            lo = mid
        elif left_change and right_change:
            # Keep the narrower half with the smaller endpoint magnitude.
            _, l0, l1 = _window_sign_change(
                family,
                chart_cert,
                lo=lo,
                hi=mid,
                anchor_amplitude_slope=anchor_amplitude_slope,
                anchor_phase_slope=anchor_phase_slope,
                second_mode_slope=second_mode_slope,
                higher_mode_slope=higher_mode_slope,
                manifold_tolerance_factor=manifold_tolerance_factor,
            )
            _, r0, r1 = _window_sign_change(
                family,
                chart_cert,
                lo=mid,
                hi=hi,
                anchor_amplitude_slope=anchor_amplitude_slope,
                anchor_phase_slope=anchor_phase_slope,
                second_mode_slope=second_mode_slope,
                higher_mode_slope=higher_mode_slope,
                manifold_tolerance_factor=manifold_tolerance_factor,
            )
            left_score = max(abs(l0.unstable_coordinate_scalar), abs(l1.unstable_coordinate_scalar))
            right_score = max(abs(r0.unstable_coordinate_scalar), abs(r1.unstable_coordinate_scalar))
            if left_score <= right_score:
                hi = mid
            else:
                lo = mid
        else:
            break
    return [float(lo), float(hi)], depth



def _window_samples(
    family: HarmonicFamily,
    chart_cert,
    *,
    window: list[float],
    dense_sample_count: int,
    anchor_amplitude_slope: float,
    anchor_phase_slope: float,
    second_mode_slope: float,
    higher_mode_slope: float,
    manifold_tolerance_factor: float,
) -> tuple[list[TransversalityWindowSample], np.ndarray, np.ndarray, np.ndarray]:
    lo, hi = float(window[0]), float(window[1])
    params = np.linspace(lo, hi, int(max(5, dense_sample_count)), dtype=float)
    samples = [
        _path_evaluator(
            family,
            chart_cert,
            float(t),
            anchor_amplitude_slope=anchor_amplitude_slope,
            anchor_phase_slope=anchor_phase_slope,
            second_mode_slope=second_mode_slope,
            higher_mode_slope=higher_mode_slope,
            manifold_tolerance_factor=manifold_tolerance_factor,
        )
        for t in params
    ]
    unstable = np.asarray([float(s.unstable_coordinate_scalar) for s in samples], dtype=float)
    stable = np.asarray([float(s.stable_coordinate_norm) for s in samples], dtype=float)
    return samples, params, unstable, stable



def _derivative_diagnostics(parameters: np.ndarray, unstable_values: np.ndarray) -> tuple[list[float], float, float, bool]:
    if len(parameters) < 3:
        return [], 0.0, 0.0, False
    deriv = np.gradient(unstable_values, parameters)
    deriv_samples = [float(x) for x in deriv.tolist()]
    signs = np.sign(deriv)
    nonzero = np.abs(deriv) > 1e-12
    monotone = bool(np.all(signs[nonzero] >= 0.0) or np.all(signs[nonzero] <= 0.0)) if np.any(nonzero) else False
    floor = float(np.min(np.abs(deriv[nonzero]))) if np.any(nonzero) else 0.0
    variation = float(np.max(deriv) - np.min(deriv)) if len(deriv) else 0.0
    return deriv_samples, floor, variation, monotone



def build_transversality_window_certificate(
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
    max_refinement_depth: int = 5,
    target_window_radius: float = 0.006,
    dense_sample_count: int = 21,
) -> TransversalityWindowCertificate:
    trans = build_family_transversality_certificate(
        family,
        family_label=family_label,
        parameter_center=parameter_center,
        parameter_radius=parameter_radius,
        sample_count=sample_count,
        anchor_amplitude_slope=anchor_amplitude_slope,
        anchor_phase_slope=anchor_phase_slope,
        second_mode_slope=second_mode_slope,
        higher_mode_slope=higher_mode_slope,
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
        transversality_floor=transversality_floor,
        manifold_tolerance_factor=manifold_tolerance_factor,
        stable_localization_factor=stable_localization_factor,
    )
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
    localized = _refine_window(
        family,
        chart,
        initial_window=trans.selected_crossing_interval,
        anchor_amplitude_slope=anchor_amplitude_slope,
        anchor_phase_slope=anchor_phase_slope,
        second_mode_slope=second_mode_slope,
        higher_mode_slope=higher_mode_slope,
        manifold_tolerance_factor=manifold_tolerance_factor,
        max_depth=max_refinement_depth,
        target_radius=target_window_radius,
    )
    window, depth = localized
    if window is None:
        critical_est = float(trans.critical_parameter_estimate)
        window = [critical_est - float(target_window_radius), critical_est + float(target_window_radius)]
    samples, params, unstable, stable = _window_samples(
        family,
        chart,
        window=window,
        dense_sample_count=dense_sample_count,
        anchor_amplitude_slope=anchor_amplitude_slope,
        anchor_phase_slope=anchor_phase_slope,
        second_mode_slope=second_mode_slope,
        higher_mode_slope=higher_mode_slope,
        manifold_tolerance_factor=manifold_tolerance_factor,
    )
    dense_interval, critical_est = _crossing_interval(params, unstable)
    if dense_interval is not None:
        window = dense_interval
        samples, params, unstable, stable = _window_samples(
            family,
            chart,
            window=window,
            dense_sample_count=dense_sample_count,
            anchor_amplitude_slope=anchor_amplitude_slope,
            anchor_phase_slope=anchor_phase_slope,
            second_mode_slope=second_mode_slope,
            higher_mode_slope=higher_mode_slope,
            manifold_tolerance_factor=manifold_tolerance_factor,
        )
    deriv_samples, deriv_floor, deriv_variation, monotone = _derivative_diagnostics(params, unstable)
    center_idx = int(np.argmin(np.abs(params - float(critical_est))))
    center_unstable = float(unstable[center_idx])
    width = float(window[1] - window[0])
    radius = 0.5 * width
    stable_center = float(stable[center_idx]) if len(stable) else 0.0
    stable_disp = float(np.max(np.abs(stable - stable_center))) if len(stable) else 0.0
    stable_margin = float(
        stable_localization_factor * (chart.stable_chart_radius + radius + 1e-12) - stable_disp
    )
    trans_margin = float(deriv_floor - float(transversality_floor))
    flags = {
        'coarse_crossing_identified': bool(trans.theorem_flags['sign_change_detected']),
        'localized_window_identified': bool(window is not None),
        'endpoint_sign_change': bool(unstable[0] == 0.0 or unstable[-1] == 0.0 or unstable[0] * unstable[-1] <= 0.0),
        'monotone_unstable_coordinate_on_window': bool(monotone),
        'derivative_floor_positive': bool(deriv_floor >= transversality_floor),
        'window_narrow_enough': bool(radius <= target_window_radius + 1e-12),
        'chart_admissible_on_window': bool(all(s.admissible_near_chart for s in samples)),
        'stable_coordinates_localized_on_window': bool(stable_margin >= 0.0),
        'center_close_to_surface_proxy': bool(abs(center_unstable) <= max(abs(unstable[0]), abs(unstable[-1]), 1e-12)),
    }
    status = (
        'proxy-transversality-window-validated'
        if all(flags.values())
        else 'proxy-transversality-window-mixed'
    )
    return TransversalityWindowCertificate(
        family_label=str(family_label),
        path_parameters={
            'parameter_center': float(parameter_center),
            'parameter_radius': float(parameter_radius),
            'sample_count': int(max(3, sample_count)),
            'max_refinement_depth': int(max_refinement_depth),
            'target_window_radius': float(target_window_radius),
            'dense_sample_count': int(max(5, dense_sample_count)),
            'anchor_amplitude_slope': float(anchor_amplitude_slope),
            'anchor_phase_slope': float(anchor_phase_slope),
            'second_mode_slope': float(second_mode_slope),
            'higher_mode_slope': float(higher_mode_slope),
            'transversality_floor': float(transversality_floor),
        },
        supporting_certificates={
            'family_transversality': trans.to_dict(),
            'stable_manifold_chart': chart.to_dict(),
        },
        initial_window=None if trans.selected_crossing_interval is None else [float(x) for x in trans.selected_crossing_interval],
        localized_window=[float(x) for x in window] if window is not None else None,
        critical_parameter_estimate=float(critical_est),
        endpoint_unstable_values=[float(unstable[0]), float(unstable[-1])],
        center_unstable_value=float(center_unstable),
        window_radius=float(radius) if window is not None else None,
        sample_count_used=int(len(samples)),
        maximum_refinement_depth_reached=int(depth),
        derivative_samples=deriv_samples,
        derivative_floor_proxy=float(deriv_floor),
        derivative_variation_proxy=float(deriv_variation),
        transversality_margin=float(trans_margin),
        stable_localization_margin=float(stable_margin),
        window_samples=[s.to_dict() for s in samples],
        theorem_flags=flags,
        theorem_status=status,
    )



def build_validated_critical_surface_bridge_certificate(
    family: HarmonicFamily,
    *,
    family_label: str = 'harmonic_family',
    **kwargs: Any,
) -> ValidatedCriticalSurfaceBridgeCertificate:
    coarse = build_critical_surface_bridge_certificate(
        family,
        family_label=family_label,
        **kwargs,
    )
    window = build_transversality_window_certificate(
        family,
        family_label=family_label,
        **kwargs,
    )
    flags = {
        'coarse_bridge_usable': bool(coarse.theorem_flags['chart_bridge_usable']),
        'localized_transversality_window': bool(window.theorem_flags['localized_window_identified']),
        'endpoint_sign_change': bool(window.theorem_flags['endpoint_sign_change']),
        'derivative_floor_positive': bool(window.theorem_flags['derivative_floor_positive']),
        'window_narrow_enough': bool(window.theorem_flags['window_narrow_enough']),
    }
    status = (
        'proxy-critical-surface-window-bridge-validated'
        if all(flags.values())
        else 'proxy-critical-surface-window-bridge-mixed'
    )
    return ValidatedCriticalSurfaceBridgeCertificate(
        family_label=str(family_label),
        path_parameters=dict(window.path_parameters),
        transversality_window_certificate=window.to_dict(),
        coarse_bridge_certificate=coarse.to_dict(),
        localized_center=float(window.critical_parameter_estimate),
        localized_radius=float(window.window_radius) if window.window_radius is not None else None,
        derivative_floor_proxy=float(window.derivative_floor_proxy),
        transversality_margin=float(window.transversality_margin),
        theorem_flags=flags,
        theorem_status=status,
    )
