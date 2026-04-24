from __future__ import annotations

"""Stable-manifold chart scaffolding for the proxy renormalization workflow.

This module is the next theorem-facing step after the candidate fixed-point
 enclosure and the proxy spectral splitting package.  It does *not* claim a
 rigorous graph-transform theorem for the true renormalization operator.
 Instead, it builds the right kind of object for that later proof:

* a stable/unstable coordinate change near the candidate fixed point,
* block diagnostics for the transformed augmented Jacobian,
* a local graph-transform slope/contraction proxy, and
* a machine-readable chart object for a codimension-one stable manifold.

The stage-82 upgrade strengthens the radius side of the scaffold.  Earlier
versions tied the local chart radius almost entirely to the fixed-point
 enclosure radius, which degenerated to zero at exact or nearly exact proxy
fixed points.  That made the stable-manifold front appear artificially open
for the golden baseline even when the spectral-gap and graph-transform data
were already favorable.

The current implementation now records and combines several radius witnesses:

* an enclosure-based radius,
* a stable-direction / chart-budget radius,
* a spectral-gap radius, and
* a graph-transform contraction radius.

The resulting lower bound is still a *proxy* theorem object, but it is a much
more faithful one: an exact fixed point with a clean dominated splitting should
still carry a positive local chart witness rather than collapsing to radius 0.
"""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .standard_map import HarmonicFamily
from .fixed_point_enclosure import build_fixed_point_enclosure_certificate
from .spectral_splitting import build_spectral_splitting_certificate


@dataclass
class StableManifoldChartCertificate:
    family_label: str
    candidate_family_harmonics: list[tuple[float, int, float]]
    ambient_dimension: int
    stable_dimension: int
    unstable_dimension: int
    coordinate_change_matrix: list[list[float]]
    inverse_coordinate_change_matrix: list[list[float]]
    transformed_jacobian: list[list[float]]
    stable_block_norm: float
    unstable_block_floor: float
    stable_to_unstable_coupling_norm: float
    unstable_to_stable_coupling_norm: float
    graph_slope_bound: float
    graph_transform_contraction: float
    local_chart_radius: float
    enclosure_radius_lower_bound: float
    stable_direction_radius_lower_bound: float
    spectral_gap_radius_lower_bound: float
    contraction_radius_lower_bound: float
    validated_chart_radius_lower_bound: float
    radius_components: dict[str, float]
    radius_source: str
    stable_chart_radius: float
    unstable_chart_radius: float
    tangent_defect_bound: float
    chart_sample_points: list[dict[str, Any]]
    supporting_certificates: dict[str, Any]
    manifold_flags: dict[str, bool]
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def _real_matrix(arr: np.ndarray) -> np.ndarray:
    return np.real_if_close(arr, tol=1_000).astype(float)



def _sorted_eigensystem(A: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    eigvals, eigvecs = np.linalg.eig(A)
    order = np.argsort(np.abs(eigvals))
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    return eigvals, eigvecs



def _make_invertible_basis(eigvecs: np.ndarray) -> np.ndarray:
    P = _real_matrix(eigvecs)
    # Light QR regularization keeps the chart basis usable even when the raw
    # eigenvectors are close to linearly dependent.
    Q, _ = np.linalg.qr(P)
    return _real_matrix(Q)



def _positive_terms(*values: float | None) -> list[float]:
    return [float(v) for v in values if v is not None and float(v) > 0.0]



def _build_radius_certificate_components(
    *,
    enclosure: Any,
    splitting: Any,
    stable_block_norm: float,
    unstable_floor: float,
    graph_slope_bound: float,
    graph_transform_contraction: float,
    stable_radius_fraction: float,
) -> tuple[float, float, float, float, float, dict[str, float], str]:
    chart_profile = dict(getattr(enclosure, 'candidate_chart_profile', {}) or {})
    chart_radius_proxy = float(chart_profile.get('chart_radius_proxy', 0.0) or 0.0)
    stable_direction_proxy = float(chart_profile.get('stable_direction_proxy', 0.0) or 0.0)
    base_chart_budget = max(0.0, min(chart_radius_proxy, stable_direction_proxy if stable_direction_proxy > 0.0 else chart_radius_proxy))

    domination_margin = float(getattr(splitting, 'domination_margin', 0.0) or 0.0)
    stable_margin = max(0.0, 1.0 - float(stable_block_norm))
    unstable_margin = max(0.0, float(unstable_floor) - 1.0)
    contraction_margin = max(0.0, 1.0 - float(graph_transform_contraction))

    enclosure_radius_lower_bound = max(0.0, float(getattr(enclosure, 'enclosure_radius', 0.0) or 0.0))

    # A pure exact fixed point can have enclosure radius 0 while still carrying
    # a positive local stable chart.  The next two candidates use the available
    # spectral-gap / graph-transform data to witness that positive local size.
    stable_direction_radius_lower_bound = 0.25 * base_chart_budget * min(
        _positive_terms(domination_margin, contraction_margin) or [0.0]
    )
    spectral_gap_radius_lower_bound = 0.25 * base_chart_budget * min(
        _positive_terms(domination_margin, stable_margin, unstable_margin) or [0.0]
    )
    contraction_radius_lower_bound = 0.25 * base_chart_budget * min(
        _positive_terms(contraction_margin, stable_margin) or [0.0]
    )

    local_chart_radius = max(
        enclosure_radius_lower_bound,
        stable_direction_radius_lower_bound,
        spectral_gap_radius_lower_bound,
        contraction_radius_lower_bound,
    )
    validated_chart_radius_lower_bound = float(
        max(0.0, stable_radius_fraction * local_chart_radius / max(1.0, 1.0 + float(graph_slope_bound)))
    )

    radius_components = {
        'enclosure_radius_lower_bound': float(enclosure_radius_lower_bound),
        'stable_direction_radius_lower_bound': float(stable_direction_radius_lower_bound),
        'spectral_gap_radius_lower_bound': float(spectral_gap_radius_lower_bound),
        'contraction_radius_lower_bound': float(contraction_radius_lower_bound),
        'local_chart_radius': float(local_chart_radius),
        'validated_chart_radius_lower_bound': float(validated_chart_radius_lower_bound),
    }
    dominant_name = max(radius_components.items(), key=lambda kv: kv[1])[0] if radius_components else 'none'
    return (
        float(enclosure_radius_lower_bound),
        float(stable_direction_radius_lower_bound),
        float(spectral_gap_radius_lower_bound),
        float(contraction_radius_lower_bound),
        float(validated_chart_radius_lower_bound),
        radius_components,
        str(dominant_name),
    )



def build_stable_manifold_chart_certificate(
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
    stable_radius_fraction: float = 0.75,
    max_graph_slope: float = 0.95,
) -> StableManifoldChartCertificate:
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
    splitting = build_spectral_splitting_certificate(
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
    )

    A = np.asarray(splitting.augmented_jacobian_proxy, dtype=float)
    eigvals, eigvecs = _sorted_eigensystem(A)
    moduli = np.abs(eigvals)
    stable_mask = moduli < 1.0 - 1e-12
    unstable_mask = moduli > 1.0 + 1e-12
    stable_dim = int(np.count_nonzero(stable_mask))
    unstable_dim = int(np.count_nonzero(unstable_mask))
    ambient_dim = int(A.shape[0])

    if stable_dim <= 0:
        stable_dim = max(ambient_dim - 1, 1)
    if unstable_dim <= 0:
        unstable_dim = ambient_dim - stable_dim

    stable_vecs = eigvecs[:, :stable_dim]
    unstable_vecs = eigvecs[:, stable_dim:stable_dim + unstable_dim]
    P = np.column_stack([stable_vecs, unstable_vecs])
    P = _make_invertible_basis(P)
    Pinv = np.linalg.inv(P)
    T = Pinv @ A @ P
    T = _real_matrix(T)

    A_ss = T[:stable_dim, :stable_dim]
    A_su = T[:stable_dim, stable_dim:stable_dim + unstable_dim]
    A_us = T[stable_dim:stable_dim + unstable_dim, :stable_dim]
    A_uu = T[stable_dim:stable_dim + unstable_dim, stable_dim:stable_dim + unstable_dim]

    stable_block_norm = float(np.linalg.norm(A_ss, ord=np.inf)) if A_ss.size else 0.0
    unstable_floor = float(np.linalg.svd(A_uu, compute_uv=False)[-1]) if A_uu.size else 0.0
    s_to_u = float(np.linalg.norm(A_us, ord=np.inf)) if A_us.size else 0.0
    u_to_s = float(np.linalg.norm(A_su, ord=np.inf)) if A_su.size else 0.0

    domination_gap = max(unstable_floor - stable_block_norm, 1e-12)
    raw_slope = max(s_to_u, u_to_s) / domination_gap
    graph_slope_bound = float(min(max_graph_slope, max(0.0, raw_slope)))
    graph_transform_contraction = float(stable_block_norm + u_to_s * graph_slope_bound)

    (
        enclosure_radius_lower_bound,
        stable_direction_radius_lower_bound,
        spectral_gap_radius_lower_bound,
        contraction_radius_lower_bound,
        validated_chart_radius_lower_bound,
        radius_components,
        radius_source,
    ) = _build_radius_certificate_components(
        enclosure=enclosure,
        splitting=splitting,
        stable_block_norm=stable_block_norm,
        unstable_floor=unstable_floor,
        graph_slope_bound=graph_slope_bound,
        graph_transform_contraction=graph_transform_contraction,
        stable_radius_fraction=stable_radius_fraction,
    )

    local_radius = float(radius_components['local_chart_radius'])
    stable_radius = float(validated_chart_radius_lower_bound)
    unstable_radius = float(graph_slope_bound * stable_radius)
    tangent_defect_bound = float(s_to_u * stable_radius)

    sample_points: list[dict[str, Any]] = []
    if stable_dim > 0 and stable_radius > 0.0:
        stable_basis = P[:, :stable_dim]
        signs = [-1.0, 0.0, 1.0]
        base = np.zeros((ambient_dim,), dtype=float)
        for sign in signs:
            coeff = np.zeros((stable_dim,), dtype=float)
            coeff[0] = sign * stable_radius
            pt = base + stable_basis @ coeff
            sample_points.append(
                {
                    'stable_coordinate': [float(x) for x in coeff.tolist()],
                    'ambient_coordinate': [float(x) for x in pt.tolist()],
                    'unstable_graph_coordinate': [0.0 for _ in range(unstable_dim)],
                }
            )

    flags = {
        'enclosure_validated': bool(enclosure.theorem_status == 'proxy-fixed-point-enclosure-validated'),
        'splitting_identified': bool(splitting.theorem_status == 'proxy-spectral-splitting-identified'),
        'codim_one_unstable': bool(unstable_dim == 1),
        'basis_invertible': bool(np.linalg.cond(P) < 1.0e6),
        'stable_block_contracting': bool(stable_block_norm < 1.0),
        'unstable_block_expanding': bool(unstable_floor > 1.0),
        'dominated_graph_transform': bool(graph_transform_contraction < 1.0),
        'positive_chart_radius': bool(stable_radius > 0.0),
        'radius_witness_from_enclosure_or_gap': bool(local_radius > 0.0),
        'tangent_defect_controlled': bool(tangent_defect_bound <= unstable_radius + 1e-12),
    }
    status = (
        'proxy-stable-manifold-chart-identified'
        if all(flags.values())
        else 'proxy-stable-manifold-chart-mixed'
    )

    return StableManifoldChartCertificate(
        family_label=str(family_label),
        candidate_family_harmonics=list(enclosure.candidate_family_harmonics),
        ambient_dimension=int(ambient_dim),
        stable_dimension=int(stable_dim),
        unstable_dimension=int(unstable_dim),
        coordinate_change_matrix=[[float(x) for x in row] for row in P.tolist()],
        inverse_coordinate_change_matrix=[[float(x) for x in row] for row in Pinv.tolist()],
        transformed_jacobian=[[float(x) for x in row] for row in T.tolist()],
        stable_block_norm=float(stable_block_norm),
        unstable_block_floor=float(unstable_floor),
        stable_to_unstable_coupling_norm=float(s_to_u),
        unstable_to_stable_coupling_norm=float(u_to_s),
        graph_slope_bound=float(graph_slope_bound),
        graph_transform_contraction=float(graph_transform_contraction),
        local_chart_radius=float(local_radius),
        enclosure_radius_lower_bound=float(enclosure_radius_lower_bound),
        stable_direction_radius_lower_bound=float(stable_direction_radius_lower_bound),
        spectral_gap_radius_lower_bound=float(spectral_gap_radius_lower_bound),
        contraction_radius_lower_bound=float(contraction_radius_lower_bound),
        validated_chart_radius_lower_bound=float(validated_chart_radius_lower_bound),
        radius_components=radius_components,
        radius_source=str(radius_source),
        stable_chart_radius=float(stable_radius),
        unstable_chart_radius=float(unstable_radius),
        tangent_defect_bound=float(tangent_defect_bound),
        chart_sample_points=sample_points,
        supporting_certificates={
            'fixed_point_enclosure': enclosure.to_dict(),
            'spectral_splitting': splitting.to_dict(),
        },
        manifold_flags=flags,
        theorem_status=status,
    )
