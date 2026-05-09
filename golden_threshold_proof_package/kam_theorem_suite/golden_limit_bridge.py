from __future__ import annotations

"""Golden-class rational-to-irrational convergence bridge.

This stage packages the most theorem-facing synthesis currently feasible from
existing infrastructure:

1. a neighborhood-stable *lower* golden object,
2. a convergent-ladder *upper* golden obstruction object,
3. an explicit rational-to-irrational q-tail limit-control certificate for that
   ladder, and
4. a neighborhood-stable upper-tail audit used to check whether the fitted upper
   limit interval is compatible with the localized/supported upper window.

The output is still not the final theorem.  It is, however, the first module in
this bundle that explicitly tries to attach an *error function* to the ladder of
rational approximants and use it to infer a candidate irrational threshold
interval.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .golden_lower_neighborhood_stability import build_golden_lower_neighborhood_stability_certificate
from .golden_supercritical import build_golden_supercritical_obstruction_certificate
from .theorem_v_upper_seed import build_golden_supercritical_obstruction_certificate_from_theorem_iv
from .golden_upper_tail_stability import (
    build_golden_upper_tail_stability_certificate,
    build_golden_upper_tail_stability_certificate_from_theorem_iv,
)
from .irrational_limit_control import build_rational_irrational_convergence_certificate
from .branch_certified_limit_control import build_branch_certified_irrational_limit_certificate
from .nested_subladder_limit_control import build_nested_subladder_limit_certificate
from .convergent_family_limit_control import build_convergent_family_limit_certificate
from .transport_certified_limit_control import build_transport_certified_limit_certificate
from .pairwise_transport_chain_control import build_pairwise_transport_chain_limit_certificate
from .triple_transport_cocycle_control import build_triple_transport_cocycle_limit_certificate
from .global_transport_potential_control import build_global_transport_potential_certificate
from .tail_cauchy_potential_control import build_tail_cauchy_potential_certificate
from .certified_tail_modulus_control import build_certified_tail_modulus_certificate
from .rate_aware_tail_modulus_control import build_rate_aware_tail_modulus_certificate
from .golden_recurrence_rate_control import build_golden_recurrence_rate_certificate
from .transport_slope_weighted_golden_rate_control import build_transport_slope_weighted_golden_rate_certificate
from .edge_class_weighted_golden_rate_control import build_edge_class_weighted_golden_rate_certificate
from .theorem_v_error_control import build_theorem_v_explicit_error_certificate, build_theorem_v_final_error_law_certificate
from .theorem_v_uniform_error_law import build_theorem_v_uniform_error_law_certificate
from .theorem_v_branch_identification import build_theorem_v_branch_identification_certificate
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _interval_intersection(
    a_lo: float | None,
    a_hi: float | None,
    b_lo: float | None,
    b_hi: float | None,
) -> tuple[float | None, float | None, float | None]:
    if a_lo is None or a_hi is None or b_lo is None or b_hi is None:
        return None, None, None
    lo = max(float(a_lo), float(b_lo))
    hi = min(float(a_hi), float(b_hi))
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _coerce_component_dict(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if hasattr(value, "to_dict"):
        try:
            return dict(value.to_dict())
        except Exception:
            pass
    return dict(value)


def build_final_transport_bridge_certificate(
    theorem_v_final_error: Mapping[str, Any],
    *,
    theorem_iv_certificate: Mapping[str, Any] | None = None,
    upper_tail: Mapping[str, Any] | None = None,
    uniform_error_law: Mapping[str, Any] | None = None,
    branch_identification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    theorem_target_interval = theorem_v_final_error.get("theorem_target_interval")
    theorem_target_lo = None
    theorem_target_hi = None
    if isinstance(theorem_target_interval, (list, tuple)) and len(theorem_target_interval) >= 2:
        theorem_target_lo = float(theorem_target_interval[0])
        theorem_target_hi = float(theorem_target_interval[1])
    theorem_target_width = theorem_v_final_error.get("theorem_target_width")
    if theorem_target_width is not None:
        theorem_target_width = float(theorem_target_width)
    uniform_error_law = dict(uniform_error_law or {})
    branch_identification = dict(branch_identification or {})
    final_transport_bridge_locked = bool(
        theorem_target_lo is not None
        and theorem_target_hi is not None
        and (
            theorem_v_final_error.get("final_error_law_certified", False)
            or uniform_error_law.get("final_error_law_certified", False)
            or uniform_error_law.get("transport_ready", False)
        )
    )
    final_transport_bridge_with_identification_lock = bool(
        final_transport_bridge_locked
        and (
            theorem_v_final_error.get("error_law_preserves_gap", False)
            or uniform_error_law.get("gap_preservation_certified", False)
        )
        and (
            branch_identification.get("branch_identification_locked", False)
            or theorem_v_final_error.get("transport_ready", False)
        )
    )
    if final_transport_bridge_with_identification_lock:
        final_transport_bridge_status = "final-transport-bridge-strong"
    elif final_transport_bridge_locked:
        final_transport_bridge_status = "final-transport-bridge-gap-preservation-incomplete"
    elif theorem_target_lo is not None and theorem_target_hi is not None:
        final_transport_bridge_status = "final-transport-bridge-partial"
    else:
        final_transport_bridge_status = "final-transport-bridge-incomplete"
    return {
        "transport_bridge_locked": final_transport_bridge_locked,
        "transport_bridge_with_identification_lock": final_transport_bridge_with_identification_lock,
        "bridge_status": final_transport_bridge_status,
        "theorem_target_interval": None if theorem_target_lo is None or theorem_target_hi is None else [theorem_target_lo, theorem_target_hi],
        "theorem_target_width": theorem_target_width,
        "error_law_source_status": str(theorem_v_final_error.get("theorem_status", "unknown")),
        "uniform_error_law_status": str(uniform_error_law.get("theorem_status", "unknown")),
        "branch_identification_status": str(branch_identification.get("theorem_status", "unknown")),
        "upper_tail_source": "theorem-iv-final-object" if theorem_iv_certificate is not None else str((upper_tail or {}).get("stable_upper_source", "unknown")),
        "notes": (
            "The final transport bridge packages the theorem-facing irrational target interval together with its readiness for downstream identification/discharge consumers."
        ),
    }


@dataclass
class GoldenRationalToIrrationalConvergenceCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    upper_tail_stability: dict[str, Any]
    convergence_control: dict[str, Any]
    branch_certified_control: dict[str, Any]
    nested_subladder_control: dict[str, Any]
    convergent_family_control: dict[str, Any]
    transport_certified_control: dict[str, Any]
    pairwise_transport_control: dict[str, Any]
    triple_transport_cocycle_control: dict[str, Any]
    global_transport_potential_control: dict[str, Any]
    tail_cauchy_potential_control: dict[str, Any]
    certified_tail_modulus_control: dict[str, Any]
    rate_aware_tail_modulus_control: dict[str, Any]
    golden_recurrence_rate_control: dict[str, Any]
    transport_slope_weighted_golden_rate_control: dict[str, Any]
    edge_class_weighted_golden_rate_control: dict[str, Any]
    theorem_v_explicit_error_control: dict[str, Any]
    theorem_v_final_error_control: dict[str, Any]
    theorem_v_uniform_error_law: dict[str, Any]
    theorem_v_branch_identification: dict[str, Any]
    runtime_row_233_377: dict[str, Any]
    runtime_row_377_610: dict[str, Any]
    final_transport_bridge: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_golden_rational_to_irrational_convergence_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    theorem_iv_certificate: Mapping[str, Any] | None = None,
    # lower-side neighborhood audit
    lower_shift_grid: Sequence[float] = (-0.015, 0.0, 0.015),
    lower_resolution_sets: Sequence[Sequence[int]] = ((64, 96, 128), (80, 112, 144)),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    lower_min_cluster_size: int = 2,
    # upper-side golden obstruction / support tail
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    crossing_center: float = 0.971635406,
    crossing_half_width: float = 2.5e-3,
    band_offset: float = 5.5e-2,
    band_width: float = 3.0e-2,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
    atlas_shifts: Sequence[float] = (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4),
    atlas_center_offsets: Sequence[float] = (-1.2e-3, -6.0e-4, 0.0, 6.0e-4, 1.2e-3),
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
    max_rounds: int = 3,
    center_shrink: float = 0.5,
    width_shrink: float = 0.7,
    min_center_spacing: float = 5.0e-5,
    support_fraction_threshold: float = 0.6,
    min_tail_members: int = 2,
    upper_tail_min_cluster_size: int = 2,
    min_stable_tail_members: int = 2,
    # convergence-control layers
    limit_min_members: int = 3,
    model_power: float = 2.0,
    center_drift_tol: float = 5.0e-4,
    branch_limit_min_members: int = 3,
    nested_limit_min_members: int = 3,
    nesting_tolerance: float = 5.0e-5,
    cauchy_multiplier: float = 1.25,
    convergent_min_chain_length: int = 4,
    convergent_p_tolerance: int = 1,
    convergent_contraction_cap: float = 0.9,
    convergent_min_overlap_fraction: float = 0.5,
    transport_min_chain_length: int = 4,
    transport_p_tolerance: int = 1,
    transport_contraction_cap: float = 0.9,
    transport_min_overlap_fraction: float = 0.5,
    pairwise_min_chain_length: int = 4,
    pairwise_p_tolerance: int = 1,
    pairwise_contraction_cap: float = 0.9,
    pairwise_min_overlap_fraction: float = 0.5,
    pairwise_compatibility_multiplier: float = 1.1,
    triple_min_chain_length: int = 4,
    triple_p_tolerance: int = 1,
    triple_contraction_cap: float = 0.9,
    triple_min_overlap_fraction: float = 0.5,
    triple_compatibility_multiplier: float = 1.1,
    triple_cocycle_multiplier: float = 1.05,
    global_potential_min_chain_length: int = 4,
    global_potential_p_tolerance: int = 1,
    global_potential_contraction_cap: float = 0.9,
    global_potential_anchor_multiplier: float = 1.05,
    tail_cauchy_min_chain_length: int = 4,
    tail_cauchy_p_tolerance: int = 1,
    tail_cauchy_contraction_cap: float = 0.9,
    tail_cauchy_anchor_multiplier: float = 1.05,
    tail_cauchy_fallback_share_cap: float = 0.35,
    tail_modulus_total_radius_growth_slack: float = 1.25,
    rate_modulus_exponent_safety_factor: float = 0.9,
    rate_modulus_min_exponent: float = 0.2,
    rate_modulus_max_exponent: float = 4.0,
    golden_recurrence_min_step_exponent: float = 0.05,
    transport_slope_strength_boost: float = 0.25,
    derivative_share_weight: float = 1.0,
    tangent_share_weight: float = 0.8,
    fallback_share_weight: float = 0.3,
    reuse_theorem_iv_upper_seed: bool = True,
    theorem_iv_stage_cache_dir: str | None = None,
    theorem_iv_preferred_shift: float = 0.0,
    lower_side_certificate: Mapping[str, Any] | None = None,
    upper_side_certificate: Mapping[str, Any] | None = None,
    upper_tail_stability_certificate: Mapping[str, Any] | None = None,
    convergence_control_certificate: Mapping[str, Any] | None = None,
    branch_certified_control_certificate: Mapping[str, Any] | None = None,
    nested_subladder_control_certificate: Mapping[str, Any] | None = None,
    convergent_family_control_certificate: Mapping[str, Any] | None = None,
    transport_certified_control_certificate: Mapping[str, Any] | None = None,
    pairwise_transport_control_certificate: Mapping[str, Any] | None = None,
    triple_transport_cocycle_control_certificate: Mapping[str, Any] | None = None,
    global_transport_potential_control_certificate: Mapping[str, Any] | None = None,
    tail_cauchy_potential_control_certificate: Mapping[str, Any] | None = None,
    certified_tail_modulus_control_certificate: Mapping[str, Any] | None = None,
    rate_aware_tail_modulus_control_certificate: Mapping[str, Any] | None = None,
    golden_recurrence_rate_control_certificate: Mapping[str, Any] | None = None,
    transport_slope_weighted_golden_rate_control_certificate: Mapping[str, Any] | None = None,
    edge_class_weighted_golden_rate_control_certificate: Mapping[str, Any] | None = None,
    theorem_v_explicit_error_control_certificate: Mapping[str, Any] | None = None,
    theorem_v_final_error_control_certificate: Mapping[str, Any] | None = None,
    theorem_v_uniform_error_law_certificate: Mapping[str, Any] | None = None,
    theorem_v_branch_identification_certificate: Mapping[str, Any] | None = None,
    runtime_row_233_377_certificate: Mapping[str, Any] | None = None,
    runtime_row_377_610_certificate: Mapping[str, Any] | None = None,
    final_transport_bridge_certificate: Mapping[str, Any] | None = None,
) -> GoldenRationalToIrrationalConvergenceCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)

    lower = _coerce_component_dict(lower_side_certificate)
    if lower is None:
        lower = build_golden_lower_neighborhood_stability_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            shift_grid=lower_shift_grid,
            resolution_sets=lower_resolution_sets,
            sigma_cap=sigma_cap,
            use_multiresolution=use_multiresolution,
            oversample_factor=oversample_factor,
            min_cluster_size=lower_min_cluster_size,
        ).to_dict()

    upper = _coerce_component_dict(upper_side_certificate)
    if upper is None:
        if theorem_iv_certificate is not None and reuse_theorem_iv_upper_seed:
            try:
                upper = build_golden_supercritical_obstruction_certificate_from_theorem_iv(
                    theorem_iv_certificate,
                    preferred_shift=theorem_iv_preferred_shift,
                    stage_cache_dir=theorem_iv_stage_cache_dir,
                    target_residue=target_residue,
                ).to_dict()
            except Exception:
                upper = None
        if upper is None:
            upper = build_golden_supercritical_obstruction_certificate(
                family=family,
                rho=rho,
                n_terms=n_terms,
                keep_last=keep_last,
                min_q=min_q,
                max_q=max_q,
                crossing_center=crossing_center,
                crossing_half_width=crossing_half_width,
                band_offset=band_offset,
                band_width=band_width,
                target_residue=target_residue,
                auto_localize_crossing=auto_localize_crossing,
                initial_subdivisions=initial_subdivisions,
                max_depth=max_depth,
                min_width=min_width,
                refine_upper_ladder=refine_upper_ladder,
                asymptotic_min_members=asymptotic_min_members,
            ).to_dict()

    upper_tail = _coerce_component_dict(upper_tail_stability_certificate)
    if upper_tail is None:
        if theorem_iv_certificate is not None:
            upper_tail = build_golden_upper_tail_stability_certificate_from_theorem_iv(
                theorem_iv_certificate
            ).to_dict()
        else:
            upper_tail = build_golden_upper_tail_stability_certificate(
                family=family,
                rho=rho,
                crossing_center=crossing_center,
                atlas_shifts=atlas_shifts,
                min_cluster_size=upper_tail_min_cluster_size,
                min_stable_tail_members=min_stable_tail_members,
                atlas_center_offsets=atlas_center_offsets,
                crossing_center_offsets=crossing_center_offsets,
                band_offset=band_offset,
                band_offset_slope=0.0,
                crossing_half_width=crossing_half_width,
                band_width=band_width,
                n_terms=n_terms,
                keep_last=keep_last,
                min_q=min_q,
                max_q=max_q,
                target_residue=target_residue,
                auto_localize_crossing=auto_localize_crossing,
                initial_subdivisions=initial_subdivisions,
                max_depth=max_depth,
                min_width=min_width,
                refine_upper_ladder=refine_upper_ladder,
                asymptotic_min_members=asymptotic_min_members,
                max_rounds=max_rounds,
                center_shrink=center_shrink,
                width_shrink=width_shrink,
                min_center_spacing=min_center_spacing,
                support_fraction_threshold=support_fraction_threshold,
                min_tail_members=min_tail_members,
            ).to_dict()

    convergence = _coerce_component_dict(convergence_control_certificate)
    if convergence is None:
        convergence = build_rational_irrational_convergence_certificate(
        upper.get("ladder", {}),
        refined=upper.get("refined", {}),
        asymptotic_audit=upper.get("asymptotic_audit", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_members=limit_min_members,
        model_power=model_power,
        center_drift_tol=center_drift_tol,
    ).to_dict()

    branch_certified = _coerce_component_dict(branch_certified_control_certificate)
    if branch_certified is None:
        branch_certified = build_branch_certified_irrational_limit_certificate(
        upper.get("ladder", {}),
        refined=upper.get("refined", {}),
        asymptotic_audit=upper.get("asymptotic_audit", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_members=branch_limit_min_members,
    ).to_dict()

    nested_subladder = _coerce_component_dict(nested_subladder_control_certificate)
    if nested_subladder is None:
        nested_subladder = build_nested_subladder_limit_certificate(
        upper.get("ladder", {}),
        refined=upper.get("refined", {}),
        asymptotic_audit=upper.get("asymptotic_audit", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_members=nested_limit_min_members,
        nesting_tolerance=nesting_tolerance,
        cauchy_multiplier=cauchy_multiplier,
    ).to_dict()

    convergent_family = _coerce_component_dict(convergent_family_control_certificate)
    if convergent_family is None:
        convergent_family = build_convergent_family_limit_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=convergent_min_chain_length,
        p_tolerance=convergent_p_tolerance,
        nesting_tolerance=nesting_tolerance,
        contraction_cap=convergent_contraction_cap,
        min_overlap_fraction=convergent_min_overlap_fraction,
    ).to_dict()

    transport_certified = _coerce_component_dict(transport_certified_control_certificate)
    if transport_certified is None:
        transport_certified = build_transport_certified_limit_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=transport_min_chain_length,
        p_tolerance=transport_p_tolerance,
        contraction_cap=transport_contraction_cap,
        min_overlap_fraction=transport_min_overlap_fraction,
    ).to_dict()

    pairwise_transport = _coerce_component_dict(pairwise_transport_control_certificate)
    if pairwise_transport is None:
        pairwise_transport = build_pairwise_transport_chain_limit_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=pairwise_min_chain_length,
        p_tolerance=pairwise_p_tolerance,
        contraction_cap=pairwise_contraction_cap,
        min_overlap_fraction=pairwise_min_overlap_fraction,
        compatibility_multiplier=pairwise_compatibility_multiplier,
    ).to_dict()

    triple_transport_cocycle = _coerce_component_dict(triple_transport_cocycle_control_certificate)
    if triple_transport_cocycle is None:
        triple_transport_cocycle = build_triple_transport_cocycle_limit_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=triple_min_chain_length,
        p_tolerance=triple_p_tolerance,
        contraction_cap=triple_contraction_cap,
        min_overlap_fraction=triple_min_overlap_fraction,
        compatibility_multiplier=triple_compatibility_multiplier,
        cocycle_multiplier=triple_cocycle_multiplier,
    ).to_dict()

    global_transport_potential = _coerce_component_dict(global_transport_potential_control_certificate)
    if global_transport_potential is None:
        global_transport_potential = build_global_transport_potential_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=global_potential_min_chain_length,
        p_tolerance=global_potential_p_tolerance,
        contraction_cap=global_potential_contraction_cap,
        anchor_multiplier=global_potential_anchor_multiplier,
    ).to_dict()

    tail_cauchy_potential = _coerce_component_dict(tail_cauchy_potential_control_certificate)
    if tail_cauchy_potential is None:
        tail_cauchy_potential = build_tail_cauchy_potential_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=tail_cauchy_min_chain_length,
        p_tolerance=tail_cauchy_p_tolerance,
        contraction_cap=tail_cauchy_contraction_cap,
        anchor_multiplier=tail_cauchy_anchor_multiplier,
        fallback_share_cap=tail_cauchy_fallback_share_cap,
    ).to_dict()

    certified_tail_modulus = _coerce_component_dict(certified_tail_modulus_control_certificate)
    if certified_tail_modulus is None:
        certified_tail_modulus = build_certified_tail_modulus_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=tail_cauchy_min_chain_length,
        p_tolerance=tail_cauchy_p_tolerance,
        contraction_cap=tail_cauchy_contraction_cap,
        anchor_multiplier=tail_cauchy_anchor_multiplier,
        fallback_share_cap=tail_cauchy_fallback_share_cap,
        total_radius_growth_slack=tail_modulus_total_radius_growth_slack,
    ).to_dict()

    rate_aware_tail_modulus = _coerce_component_dict(rate_aware_tail_modulus_control_certificate)
    if rate_aware_tail_modulus is None:
        rate_aware_tail_modulus = build_rate_aware_tail_modulus_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=tail_cauchy_min_chain_length,
        p_tolerance=tail_cauchy_p_tolerance,
        contraction_cap=tail_cauchy_contraction_cap,
        anchor_multiplier=tail_cauchy_anchor_multiplier,
        fallback_share_cap=tail_cauchy_fallback_share_cap,
        total_radius_growth_slack=tail_modulus_total_radius_growth_slack,
        rate_exponent_safety_factor=rate_modulus_exponent_safety_factor,
        min_rate_exponent=rate_modulus_min_exponent,
        max_rate_exponent=rate_modulus_max_exponent,
    ).to_dict()

    golden_recurrence_rate = _coerce_component_dict(golden_recurrence_rate_control_certificate)
    if golden_recurrence_rate is None:
        golden_recurrence_rate = build_golden_recurrence_rate_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=tail_cauchy_min_chain_length,
        p_tolerance=tail_cauchy_p_tolerance,
        contraction_cap=tail_cauchy_contraction_cap,
        anchor_multiplier=tail_cauchy_anchor_multiplier,
        fallback_share_cap=tail_cauchy_fallback_share_cap,
        total_radius_growth_slack=tail_modulus_total_radius_growth_slack,
        rate_exponent_safety_factor=rate_modulus_exponent_safety_factor,
        min_rate_exponent=rate_modulus_min_exponent,
        max_rate_exponent=rate_modulus_max_exponent,
        min_step_exponent=golden_recurrence_min_step_exponent,
    ).to_dict()

    transport_slope_weighted_golden_rate = _coerce_component_dict(transport_slope_weighted_golden_rate_control_certificate)
    if transport_slope_weighted_golden_rate is None:
        transport_slope_weighted_golden_rate = build_transport_slope_weighted_golden_rate_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=tail_cauchy_min_chain_length,
        p_tolerance=tail_cauchy_p_tolerance,
        contraction_cap=tail_cauchy_contraction_cap,
        anchor_multiplier=tail_cauchy_anchor_multiplier,
        fallback_share_cap=tail_cauchy_fallback_share_cap,
        total_radius_growth_slack=tail_modulus_total_radius_growth_slack,
        rate_exponent_safety_factor=rate_modulus_exponent_safety_factor,
        min_rate_exponent=rate_modulus_min_exponent,
        max_rate_exponent=rate_modulus_max_exponent,
        min_step_exponent=golden_recurrence_min_step_exponent,
        transport_strength_boost=transport_slope_strength_boost,
    ).to_dict()

    edge_class_weighted_golden_rate = _coerce_component_dict(edge_class_weighted_golden_rate_control_certificate)
    if edge_class_weighted_golden_rate is None:
        edge_class_weighted_golden_rate = build_edge_class_weighted_golden_rate_certificate(
        upper.get("ladder", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_chain_length=tail_cauchy_min_chain_length,
        p_tolerance=tail_cauchy_p_tolerance,
        contraction_cap=tail_cauchy_contraction_cap,
        anchor_multiplier=tail_cauchy_anchor_multiplier,
        fallback_share_cap=tail_cauchy_fallback_share_cap,
        total_radius_growth_slack=tail_modulus_total_radius_growth_slack,
        rate_exponent_safety_factor=rate_modulus_exponent_safety_factor,
        min_rate_exponent=rate_modulus_min_exponent,
        max_rate_exponent=rate_modulus_max_exponent,
        min_step_exponent=golden_recurrence_min_step_exponent,
        transport_strength_boost=transport_slope_strength_boost,
        derivative_share_weight=derivative_share_weight,
        tangent_share_weight=tangent_share_weight,
        fallback_share_weight=fallback_share_weight,
    ).to_dict()

    theorem_v_explicit_error = _coerce_component_dict(theorem_v_explicit_error_control_certificate)
    if theorem_v_explicit_error is None:
        theorem_v_explicit_error = build_theorem_v_explicit_error_certificate(
        upper.get("ladder", {}),
        refined=upper.get("refined", {}),
        asymptotic_audit=upper.get("asymptotic_audit", {}),
        rho_target=rho,
        family_label=_family_label(family),
        min_members=limit_min_members,
        nesting_tolerance=nesting_tolerance,
        cauchy_multiplier=cauchy_multiplier,
        min_chain_length=tail_cauchy_min_chain_length,
        p_tolerance=tail_cauchy_p_tolerance,
        contraction_cap=tail_cauchy_contraction_cap,
        min_overlap_fraction=transport_min_overlap_fraction,
        compatibility_multiplier=pairwise_compatibility_multiplier,
        cocycle_multiplier=triple_cocycle_multiplier,
        anchor_multiplier=tail_cauchy_anchor_multiplier,
        fallback_share_cap=tail_cauchy_fallback_share_cap,
        total_radius_growth_slack=tail_modulus_total_radius_growth_slack,
        rate_exponent_safety_factor=rate_modulus_exponent_safety_factor,
        min_rate_exponent=rate_modulus_min_exponent,
        max_rate_exponent=rate_modulus_max_exponent,
        min_step_exponent=golden_recurrence_min_step_exponent,
        transport_strength_boost=transport_slope_strength_boost,
        derivative_share_weight=derivative_share_weight,
        tangent_share_weight=tangent_share_weight,
        fallback_share_weight=fallback_share_weight,
        convergence_control=convergence,
        branch_certified_control=branch_certified,
        nested_subladder_control=nested_subladder,
        convergent_family_control=convergent_family,
        transport_certified_control=transport_certified,
        pairwise_transport_control=pairwise_transport,
        triple_transport_cocycle_control=triple_transport_cocycle,
        global_transport_potential_control=global_transport_potential,
        tail_cauchy_potential_control=tail_cauchy_potential,
        certified_tail_modulus_control=certified_tail_modulus,
        rate_aware_tail_modulus_control=rate_aware_tail_modulus,
        golden_recurrence_rate_control=golden_recurrence_rate,
        transport_slope_weighted_golden_rate_control=transport_slope_weighted_golden_rate,
        edge_class_weighted_golden_rate_control=edge_class_weighted_golden_rate,
    ).to_dict()
    theorem_v_final_error = _coerce_component_dict(theorem_v_final_error_control_certificate)
    if theorem_v_final_error is None:
        theorem_v_final_error = build_theorem_v_final_error_law_certificate(
        explicit_error_certificate=theorem_v_explicit_error,
        reference_lower_bound=lower.get("stable_lower_bound"),
        min_uniform_chain_length=max(3, tail_cauchy_min_chain_length),
    ).to_dict()
    theorem_target_interval = theorem_v_final_error.get("theorem_target_interval")
    theorem_target_lo = None
    theorem_target_hi = None
    if isinstance(theorem_target_interval, (list, tuple)) and len(theorem_target_interval) >= 2:
        theorem_target_lo = float(theorem_target_interval[0])
        theorem_target_hi = float(theorem_target_interval[1])
    theorem_target_width = theorem_v_final_error.get("theorem_target_width")
    if theorem_target_width is not None:
        theorem_target_width = float(theorem_target_width)
    runtime_row_233_377 = _coerce_component_dict(runtime_row_233_377_certificate) or {}
    runtime_row_377_610 = _coerce_component_dict(runtime_row_377_610_certificate) or {}
    theorem_v_uniform_error = _coerce_component_dict(theorem_v_uniform_error_law_certificate)
    if theorem_v_uniform_error is None:
        theorem_v_uniform_error = build_theorem_v_uniform_error_law_certificate(
            explicit_error_certificate=theorem_v_explicit_error,
            final_error_certificate=theorem_v_final_error,
            golden_recurrence_rate_control=golden_recurrence_rate,
            edge_class_weighted_golden_rate_control=edge_class_weighted_golden_rate,
            convergent_family_control=convergent_family,
            runtime_row_certificates=[runtime_row_233_377, runtime_row_377_610],
            min_uniform_chain_length=max(3, tail_cauchy_min_chain_length),
        ).to_dict()
    theorem_v_branch_identification = _coerce_component_dict(theorem_v_branch_identification_certificate)
    if theorem_v_branch_identification is None:
        theorem_v_branch_identification = build_theorem_v_branch_identification_certificate(
            lower_side_certificate=lower,
            upper_tail_certificate=upper_tail,
            final_transport_bridge=theorem_v_final_error,
            theorem_iv_certificate=theorem_iv_certificate,
            convergent_family_control=convergent_family,
            golden_recurrence_rate_control=golden_recurrence_rate,
            explicit_error_certificate=theorem_v_explicit_error,
            uniform_error_law=theorem_v_uniform_error,
            runtime_row_certificates=[runtime_row_233_377, runtime_row_377_610],
        ).to_dict()
    final_transport_bridge = _coerce_component_dict(final_transport_bridge_certificate)
    if final_transport_bridge is None:
        final_transport_bridge = build_final_transport_bridge_certificate(
            theorem_v_final_error,
            theorem_iv_certificate=theorem_iv_certificate,
            upper_tail=upper_tail,
            uniform_error_law=theorem_v_uniform_error,
            branch_identification=theorem_v_branch_identification,
        )

    fit_lo = convergence.get("limit_interval_lo")
    fit_hi = convergence.get("limit_interval_hi")
    branch_lo = branch_certified.get("selected_limit_interval_lo")
    branch_hi = branch_certified.get("selected_limit_interval_hi")
    nested_lo = nested_subladder.get("final_interval_lo")
    nested_hi = nested_subladder.get("final_interval_hi")
    conv_lo = convergent_family.get("limit_interval_lo")
    conv_hi = convergent_family.get("limit_interval_hi")
    transport_lo = transport_certified.get("limit_interval_lo")
    transport_hi = transport_certified.get("limit_interval_hi")
    pairwise_lo = pairwise_transport.get("limit_interval_lo")
    pairwise_hi = pairwise_transport.get("limit_interval_hi")
    triple_lo = triple_transport_cocycle.get("limit_interval_lo")
    triple_hi = triple_transport_cocycle.get("limit_interval_hi")
    global_lo = global_transport_potential.get("selected_limit_interval_lo")
    global_hi = global_transport_potential.get("selected_limit_interval_hi")
    tail_cauchy_lo = tail_cauchy_potential.get("selected_limit_interval_lo")
    tail_cauchy_hi = tail_cauchy_potential.get("selected_limit_interval_hi")
    tail_modulus_lo = certified_tail_modulus.get("selected_limit_interval_lo")
    tail_modulus_hi = certified_tail_modulus.get("selected_limit_interval_hi")
    rate_modulus_lo = rate_aware_tail_modulus.get("modulus_rate_intersection_lo")
    rate_modulus_hi = rate_aware_tail_modulus.get("modulus_rate_intersection_hi")
    golden_rate_lo = golden_recurrence_rate.get("rate_golden_intersection_lo")
    golden_rate_hi = golden_recurrence_rate.get("rate_golden_intersection_hi")
    transport_weighted_golden_lo = transport_slope_weighted_golden_rate.get("weighted_golden_intersection_lo")
    transport_weighted_golden_hi = transport_slope_weighted_golden_rate.get("weighted_golden_intersection_hi")
    edge_class_golden_lo = edge_class_weighted_golden_rate.get("edge_class_transport_intersection_lo")
    edge_class_golden_hi = edge_class_weighted_golden_rate.get("edge_class_transport_intersection_hi")
    tail_lo = upper_tail.get("stable_upper_lo")
    tail_hi = upper_tail.get("stable_upper_hi")
    model_branch_lo, model_branch_hi, model_branch_w = _interval_intersection(fit_lo, fit_hi, branch_lo, branch_hi)
    model_branch_nested_lo, model_branch_nested_hi, model_branch_nested_w = _interval_intersection(model_branch_lo, model_branch_hi, nested_lo, nested_hi)
    model_branch_nested_conv_lo, model_branch_nested_conv_hi, model_branch_nested_conv_w = _interval_intersection(model_branch_nested_lo, model_branch_nested_hi, conv_lo, conv_hi)
    model_branch_nested_conv_transport_lo, model_branch_nested_conv_transport_hi, model_branch_nested_conv_transport_w = _interval_intersection(model_branch_nested_conv_lo, model_branch_nested_conv_hi, transport_lo, transport_hi)
    model_branch_nested_conv_transport_pair_lo, model_branch_nested_conv_transport_pair_hi, model_branch_nested_conv_transport_pair_w = _interval_intersection(model_branch_nested_conv_transport_lo, model_branch_nested_conv_transport_hi, pairwise_lo, pairwise_hi)
    model_branch_nested_conv_transport_pair_triple_lo, model_branch_nested_conv_transport_pair_triple_hi, model_branch_nested_conv_transport_pair_triple_w = _interval_intersection(model_branch_nested_conv_transport_pair_lo, model_branch_nested_conv_transport_pair_hi, triple_lo, triple_hi)
    model_branch_nested_conv_transport_pair_triple_global_lo, model_branch_nested_conv_transport_pair_triple_global_hi, model_branch_nested_conv_transport_pair_triple_global_w = _interval_intersection(model_branch_nested_conv_transport_pair_triple_lo, model_branch_nested_conv_transport_pair_triple_hi, global_lo, global_hi)
    model_branch_nested_conv_transport_pair_triple_global_cauchy_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_hi, model_branch_nested_conv_transport_pair_triple_global_cauchy_w = _interval_intersection(model_branch_nested_conv_transport_pair_triple_global_lo, model_branch_nested_conv_transport_pair_triple_global_hi, tail_cauchy_lo, tail_cauchy_hi)
    model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_hi, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_w = _interval_intersection(model_branch_nested_conv_transport_pair_triple_global_cauchy_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_hi, tail_modulus_lo, tail_modulus_hi)
    model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_hi, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_w = _interval_intersection(model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_hi, rate_modulus_lo, rate_modulus_hi)
    model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_hi, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_w = _interval_intersection(model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_hi, golden_rate_lo, golden_rate_hi)
    model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_hi, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_w = _interval_intersection(model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_hi, transport_weighted_golden_lo, transport_weighted_golden_hi)
    model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_edge_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_edge_hi, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_edge_w = _interval_intersection(model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_hi, edge_class_golden_lo, edge_class_golden_hi)
    compatible_lo, compatible_hi, compatible_w = _interval_intersection(model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_edge_lo, model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_edge_hi, tail_lo, tail_hi)
    lower_bound = lower.get("stable_lower_bound")
    lower_window_hi = lower.get("stable_observed_upper_hint")
    compatible_gap = None if lower_bound is None or compatible_lo is None else float(compatible_lo - float(lower_bound))
    fit_gap = None if lower_bound is None or fit_lo is None else float(fit_lo - float(lower_bound))
    branch_gap = None if lower_bound is None or branch_lo is None else float(branch_lo - float(lower_bound))
    nested_gap = None if lower_bound is None or nested_lo is None else float(nested_lo - float(lower_bound))
    conv_gap = None if lower_bound is None or conv_lo is None else float(conv_lo - float(lower_bound))
    transport_gap = None if lower_bound is None or transport_lo is None else float(transport_lo - float(lower_bound))
    pairwise_gap = None if lower_bound is None or pairwise_lo is None else float(pairwise_lo - float(lower_bound))
    triple_gap = None if lower_bound is None or triple_lo is None else float(triple_lo - float(lower_bound))
    global_gap = None if lower_bound is None or global_lo is None else float(global_lo - float(lower_bound))
    tail_cauchy_gap = None if lower_bound is None or tail_cauchy_lo is None else float(tail_cauchy_lo - float(lower_bound))
    tail_modulus_gap = None if lower_bound is None or tail_modulus_lo is None else float(tail_modulus_lo - float(lower_bound))
    rate_modulus_gap = None if lower_bound is None or rate_modulus_lo is None else float(rate_modulus_lo - float(lower_bound))
    golden_rate_gap = None if lower_bound is None or golden_rate_lo is None else float(golden_rate_lo - float(lower_bound))
    transport_weighted_golden_gap = None if lower_bound is None or transport_weighted_golden_lo is None else float(transport_weighted_golden_lo - float(lower_bound))
    edge_class_golden_gap = None if lower_bound is None or edge_class_golden_lo is None else float(edge_class_golden_lo - float(lower_bound))
    theorem_v_lo = theorem_v_explicit_error.get("compatible_limit_interval_lo")
    theorem_v_hi = theorem_v_explicit_error.get("compatible_limit_interval_hi")
    theorem_v_gap = None if lower_bound is None or theorem_v_lo is None else float(theorem_v_lo - float(lower_bound))
    tail_gap = None if lower_bound is None or tail_lo is None else float(tail_lo - float(lower_bound))
    native_late_suffix_lo = theorem_v_explicit_error.get("late_coherent_suffix_interval_lo")
    native_late_suffix_hi = theorem_v_explicit_error.get("late_coherent_suffix_interval_hi")
    native_late_suffix_length = int(theorem_v_explicit_error.get("late_coherent_suffix_length") or 0)
    native_late_suffix_contracting = bool(theorem_v_explicit_error.get("late_coherent_suffix_contracting", False))
    native_late_suffix_ratio = theorem_v_explicit_error.get("late_coherent_suffix_contraction_ratio")
    native_late_suffix_status = theorem_v_explicit_error.get("late_coherent_suffix_status")
    native_late_suffix_labels = [str(x) for x in theorem_v_explicit_error.get("late_coherent_suffix_labels", [])]
    native_late_suffix_qs = [int(x) for x in theorem_v_explicit_error.get("late_coherent_suffix_qs", [])]
    native_late_suffix_start_q = theorem_v_explicit_error.get("late_coherent_suffix_start_q")
    native_late_suffix_start_label = theorem_v_explicit_error.get("late_coherent_suffix_start_label")
    native_late_suffix_witness_lo, native_late_suffix_witness_hi, native_late_suffix_witness_w = _interval_intersection(
        native_late_suffix_lo,
        native_late_suffix_hi,
        compatible_lo,
        compatible_hi,
    )
    if native_late_suffix_witness_lo is None and native_late_suffix_lo is not None and native_late_suffix_hi is not None:
        native_late_suffix_witness_lo = float(native_late_suffix_lo)
        native_late_suffix_witness_hi = float(native_late_suffix_hi)
        native_late_suffix_witness_w = float(float(native_late_suffix_hi) - float(native_late_suffix_lo))
    native_late_suffix_gap = None if lower_bound is None or native_late_suffix_witness_lo is None else float(native_late_suffix_witness_lo - float(lower_bound))

    relation = {
        "lower_bound": None if lower_bound is None else float(lower_bound),
        "lower_window_hi": None if lower_window_hi is None else float(lower_window_hi),
        "upper_fit_limit_lo": None if fit_lo is None else float(fit_lo),
        "upper_fit_limit_hi": None if fit_hi is None else float(fit_hi),
        "upper_fit_limit_width": convergence.get("limit_interval_width"),
        "branch_certified_upper_lo": None if branch_lo is None else float(branch_lo),
        "branch_certified_upper_hi": None if branch_hi is None else float(branch_hi),
        "branch_certified_upper_width": branch_certified.get("selected_limit_interval_width"),
        "model_branch_compatible_lo": model_branch_lo,
        "model_branch_compatible_hi": model_branch_hi,
        "model_branch_compatible_width": model_branch_w,
        "nested_subladder_upper_lo": None if nested_lo is None else float(nested_lo),
        "nested_subladder_upper_hi": None if nested_hi is None else float(nested_hi),
        "nested_subladder_upper_width": nested_subladder.get("final_interval_width"),
        "model_branch_nested_lo": model_branch_nested_lo,
        "model_branch_nested_hi": model_branch_nested_hi,
        "model_branch_nested_width": model_branch_nested_w,
        "convergent_family_upper_lo": None if conv_lo is None else float(conv_lo),
        "convergent_family_upper_hi": None if conv_hi is None else float(conv_hi),
        "convergent_family_upper_width": convergent_family.get("limit_interval_width"),
        "model_branch_nested_convergent_lo": model_branch_nested_conv_lo,
        "model_branch_nested_convergent_hi": model_branch_nested_conv_hi,
        "model_branch_nested_convergent_width": model_branch_nested_conv_w,
        "transport_certified_upper_lo": None if transport_lo is None else float(transport_lo),
        "transport_certified_upper_hi": None if transport_hi is None else float(transport_hi),
        "transport_certified_upper_width": transport_certified.get("limit_interval_width"),
        "model_branch_nested_convergent_transport_lo": model_branch_nested_conv_transport_lo,
        "model_branch_nested_convergent_transport_hi": model_branch_nested_conv_transport_hi,
        "model_branch_nested_convergent_transport_width": model_branch_nested_conv_transport_w,
        "pairwise_transport_upper_lo": None if pairwise_lo is None else float(pairwise_lo),
        "pairwise_transport_upper_hi": None if pairwise_hi is None else float(pairwise_hi),
        "pairwise_transport_upper_width": pairwise_transport.get("limit_interval_width"),
        "model_branch_nested_convergent_transport_pairwise_lo": model_branch_nested_conv_transport_pair_lo,
        "model_branch_nested_convergent_transport_pairwise_hi": model_branch_nested_conv_transport_pair_hi,
        "model_branch_nested_convergent_transport_pairwise_width": model_branch_nested_conv_transport_pair_w,
        "triple_transport_cocycle_upper_lo": None if triple_lo is None else float(triple_lo),
        "triple_transport_cocycle_upper_hi": None if triple_hi is None else float(triple_hi),
        "triple_transport_cocycle_upper_width": triple_transport_cocycle.get("limit_interval_width"),
        "model_branch_nested_convergent_transport_pairwise_triple_lo": model_branch_nested_conv_transport_pair_triple_lo,
        "model_branch_nested_convergent_transport_pairwise_triple_hi": model_branch_nested_conv_transport_pair_triple_hi,
        "model_branch_nested_convergent_transport_pairwise_triple_width": model_branch_nested_conv_transport_pair_triple_w,
        "global_transport_potential_upper_lo": None if global_lo is None else float(global_lo),
        "global_transport_potential_upper_hi": None if global_hi is None else float(global_hi),
        "global_transport_potential_upper_width": global_transport_potential.get("selected_limit_interval_width"),
        "model_branch_nested_convergent_transport_pairwise_triple_global_lo": model_branch_nested_conv_transport_pair_triple_global_lo,
        "model_branch_nested_convergent_transport_pairwise_triple_global_hi": model_branch_nested_conv_transport_pair_triple_global_hi,
        "model_branch_nested_convergent_transport_pairwise_triple_global_width": model_branch_nested_conv_transport_pair_triple_global_w,
        "tail_cauchy_potential_upper_lo": None if tail_cauchy_lo is None else float(tail_cauchy_lo),
        "tail_cauchy_potential_upper_hi": None if tail_cauchy_hi is None else float(tail_cauchy_hi),
        "tail_cauchy_potential_upper_width": tail_cauchy_potential.get("selected_limit_interval_width"),
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_lo": model_branch_nested_conv_transport_pair_triple_global_cauchy_lo,
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_hi": model_branch_nested_conv_transport_pair_triple_global_cauchy_hi,
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_width": model_branch_nested_conv_transport_pair_triple_global_cauchy_w,
        "certified_tail_modulus_upper_lo": None if tail_modulus_lo is None else float(tail_modulus_lo),
        "certified_tail_modulus_upper_hi": None if tail_modulus_hi is None else float(tail_modulus_hi),
        "certified_tail_modulus_upper_width": certified_tail_modulus.get("selected_limit_interval_width"),
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_modulus_lo": model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_lo,
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_modulus_hi": model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_hi,
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_modulus_width": model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_w,
        "rate_aware_tail_modulus_upper_lo": None if rate_modulus_lo is None else float(rate_modulus_lo),
        "rate_aware_tail_modulus_upper_hi": None if rate_modulus_hi is None else float(rate_modulus_hi),
        "rate_aware_tail_modulus_upper_width": rate_aware_tail_modulus.get("modulus_rate_intersection_width"),
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_modulus_rate_lo": model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_lo,
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_modulus_rate_hi": model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_hi,
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_modulus_rate_width": model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_w,
        "upper_tail_stable_lo": None if tail_lo is None else float(tail_lo),
        "upper_tail_stable_hi": None if tail_hi is None else float(tail_hi),
        "upper_tail_stable_width": upper_tail.get("stable_upper_width"),
        "compatible_upper_lo": compatible_lo,
        "compatible_upper_hi": compatible_hi,
        "compatible_upper_width": compatible_w,
        "gap_to_fit_interval": fit_gap,
        "gap_to_branch_interval": branch_gap,
        "gap_to_nested_interval": nested_gap,
        "gap_to_convergent_interval": conv_gap,
        "gap_to_transport_interval": transport_gap,
        "gap_to_pairwise_transport_interval": pairwise_gap,
        "gap_to_triple_transport_cocycle_interval": triple_gap,
        "gap_to_global_transport_potential_interval": global_gap,
        "gap_to_tail_cauchy_potential_interval": tail_cauchy_gap,
        "gap_to_certified_tail_modulus_interval": tail_modulus_gap,
        "gap_to_rate_aware_tail_modulus_interval": rate_modulus_gap,
        "gap_to_golden_recurrence_rate_interval": golden_rate_gap,
        "gap_to_transport_slope_weighted_golden_rate_interval": transport_weighted_golden_gap,
        "edge_class_weighted_golden_rate_upper_lo": None if edge_class_golden_lo is None else float(edge_class_golden_lo),
        "edge_class_weighted_golden_rate_upper_hi": None if edge_class_golden_hi is None else float(edge_class_golden_hi),
        "edge_class_weighted_golden_rate_upper_width": edge_class_weighted_golden_rate.get("edge_class_transport_intersection_width"),
        "theorem_v_explicit_error_upper_lo": None if theorem_v_lo is None else float(theorem_v_lo),
        "theorem_v_explicit_error_upper_hi": None if theorem_v_hi is None else float(theorem_v_hi),
        "theorem_v_explicit_error_upper_width": theorem_v_explicit_error.get("compatible_limit_interval_width"),
        "native_late_coherent_suffix_witness_lo": native_late_suffix_witness_lo,
        "native_late_coherent_suffix_witness_hi": native_late_suffix_witness_hi,
        "native_late_coherent_suffix_witness_width": native_late_suffix_witness_w,
        "native_late_coherent_suffix_start_q": None if native_late_suffix_start_q is None else int(native_late_suffix_start_q),
        "native_late_coherent_suffix_start_label": None if native_late_suffix_start_label is None else str(native_late_suffix_start_label),
        "native_late_coherent_suffix_length": int(native_late_suffix_length),
        "native_late_coherent_suffix_labels": list(native_late_suffix_labels),
        "native_late_coherent_suffix_qs": list(native_late_suffix_qs),
        "native_late_coherent_suffix_contracting": bool(native_late_suffix_contracting),
        "native_late_coherent_suffix_contraction_ratio": None if native_late_suffix_ratio is None else float(native_late_suffix_ratio),
        "native_late_coherent_suffix_status": None if native_late_suffix_status is None else str(native_late_suffix_status),
        "native_late_coherent_suffix_source": "theorem_v_explicit_error_control.late_coherent_suffix",
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_modulus_rate_golden_transport_edge_lo": model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_edge_lo,
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_modulus_rate_golden_transport_edge_hi": model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_edge_hi,
        "model_branch_nested_convergent_transport_pairwise_triple_global_cauchy_modulus_rate_golden_transport_edge_width": model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_edge_w,
        "gap_to_edge_class_weighted_golden_rate_interval": edge_class_golden_gap,
        "gap_to_theorem_v_explicit_error_interval": theorem_v_gap,
        "gap_to_native_late_coherent_suffix_interval": native_late_suffix_gap,
        "gap_to_tail_interval": tail_gap,
        "gap_to_compatible_upper": compatible_gap,
        "theorem_v_target_interval_lo": theorem_target_lo,
        "theorem_v_target_interval_hi": theorem_target_hi,
        "theorem_v_target_interval_width": theorem_target_width,
        "theorem_v_final_error_law_status": str(theorem_v_final_error.get("theorem_status", "unknown")),
        "theorem_v_uniform_error_law_status": str(theorem_v_uniform_error.get("theorem_status", "unknown")),
        "theorem_v_branch_identification_status": str(theorem_v_branch_identification.get("theorem_status", "unknown")),
        "theorem_v_uniform_error_law_certified": bool(theorem_v_uniform_error.get("final_error_law_certified", False)),
        "theorem_v_branch_identification_locked": bool(theorem_v_branch_identification.get("branch_identification_locked", False)),
        "theorem_v_gap_preservation_margin": theorem_v_final_error.get("gap_preservation_margin"),
        "theorem_v_gap_preservation_certified": theorem_v_final_error.get("error_law_preserves_gap"),
        "final_transport_bridge_status": str(final_transport_bridge.get("bridge_status", "unknown")),
        "selected_tail_qs": [int(x) for x in convergence.get("selected_tail_qs", [])],
        "branch_selected_tail_qs": [int(x) for x in branch_certified.get("selected_tail_qs", [])],
        "nested_chain_thresholds": [int(x) for x in nested_subladder.get("chain_thresholds", [])],
        "convergent_chain_qs": [int(x) for x in convergent_family.get("chain_qs", [])],
        "transport_chain_qs": [int(x) for x in transport_certified.get("chain_qs", [])],
        "pairwise_transport_chain_qs": [int(x) for x in pairwise_transport.get("chain_qs", [])],
        "triple_transport_cocycle_chain_qs": [int(x) for x in triple_transport_cocycle.get("chain_qs", [])],
        "global_transport_potential_chain_qs": [int(x) for x in global_transport_potential.get("chain_qs", [])],
        "tail_cauchy_potential_chain_qs": [int(x) for x in tail_cauchy_potential.get("chain_qs", [])],
        "certified_tail_modulus_chain_qs": [int(x) for x in certified_tail_modulus.get("chain_qs", [])],
        "rate_aware_tail_modulus_chain_qs": [int(x) for x in rate_aware_tail_modulus.get("chain_qs", [])],
        "golden_recurrence_rate_chain_qs": [int(x) for x in golden_recurrence_rate.get("chain_qs", [])],
        "transport_slope_weighted_golden_rate_chain_qs": [int(x) for x in transport_slope_weighted_golden_rate.get("chain_qs", [])],
        "edge_class_weighted_golden_rate_chain_qs": [int(x) for x in edge_class_weighted_golden_rate.get("chain_qs", [])],
        "stable_tail_qs": [int(x) for x in upper_tail.get("stable_tail_qs", [])],
        "convergence_status": str(convergence.get("theorem_status", "unknown")),
        "branch_certified_status": str(branch_certified.get("theorem_status", "unknown")),
        "nested_subladder_status": str(nested_subladder.get("theorem_status", "unknown")),
        "convergent_family_status": str(convergent_family.get("theorem_status", "unknown")),
        "transport_certified_status": str(transport_certified.get("theorem_status", "unknown")),
        "pairwise_transport_status": str(pairwise_transport.get("theorem_status", "unknown")),
        "triple_transport_cocycle_status": str(triple_transport_cocycle.get("theorem_status", "unknown")),
        "global_transport_potential_status": str(global_transport_potential.get("theorem_status", "unknown")),
        "tail_cauchy_potential_status": str(tail_cauchy_potential.get("theorem_status", "unknown")),
        "certified_tail_modulus_status": str(certified_tail_modulus.get("theorem_status", "unknown")),
        "rate_aware_tail_modulus_status": str(rate_aware_tail_modulus.get("theorem_status", "unknown")),
        "golden_recurrence_rate_status": str(golden_recurrence_rate.get("theorem_status", "unknown")),
        "transport_slope_weighted_golden_rate_status": str(transport_slope_weighted_golden_rate.get("theorem_status", "unknown")),
        "edge_class_weighted_golden_rate_status": str(edge_class_weighted_golden_rate.get("theorem_status", "unknown")),
        "theorem_v_explicit_error_status": str(theorem_v_explicit_error.get("theorem_status", "unknown")),
        "upper_tail_status": str(upper_tail.get("theorem_status", "unknown")),
        "upper_tail_inherited_from_theorem_iv": bool(theorem_iv_certificate is not None),
        "upper_tail_source": str(upper_tail.get("stable_upper_source", "unknown")),
        "theorem_iv_status": None if theorem_iv_certificate is None else str(theorem_iv_certificate.get("theorem_status", "unknown")),
        "theorem_iv_contradiction_certified": None if theorem_iv_certificate is None else bool(theorem_iv_certificate.get("nonexistence_contradiction_certified", False)),
        "theorem_iv_open_hypotheses": [] if theorem_iv_certificate is None else [str(x) for x in theorem_iv_certificate.get("open_hypotheses", [])],
        "upper_side_inherited_from_theorem_iv": bool(theorem_iv_certificate is not None and upper.get("selected_upper_source") == "theorem-iv-final-object"),
        "upper_side_source": str(upper.get("selected_upper_source", "unknown")),
        "upper_side_approximant_count": len(list((upper.get("ladder") or {}).get("approximants", []) or [])),
        "lower_status": str(lower.get("theorem_status", "unknown")),
        "runtime_row_233_377_status": str(runtime_row_233_377.get("theorem_status", "unknown")),
        "runtime_row_377_610_status": str(runtime_row_377_610.get("theorem_status", "unknown")),
        "runtime_row_233_377_direct_attempt_proof_ready": bool(runtime_row_233_377.get("direct_attempt_proof_ready", False)),
        "runtime_row_377_610_direct_attempt_proof_ready": bool(runtime_row_377_610.get("direct_attempt_proof_ready", False)),
        "final_error_law_status": str(theorem_v_final_error.get("theorem_status", "unknown")),
        "uniform_error_law_status": str(theorem_v_uniform_error.get("theorem_status", "unknown")),
        "branch_identification_status": str(theorem_v_branch_identification.get("theorem_status", "unknown")),
        "late_suffix_rigidity_ready": bool(theorem_v_uniform_error.get("late_suffix_rigidity_ready", False)),
    }

    strong_intermediate_stack = (
        str(convergence.get("theorem_status")) == "irrational-limit-control-strong"
        and str(branch_certified.get("theorem_status")) == "branch-certified-limit-strong"
        and str(nested_subladder.get("theorem_status")) == "nested-subladder-limit-strong"
        and str(convergent_family.get("theorem_status")) == "convergent-family-limit-strong"
        and str(transport_certified.get("theorem_status")) == "transport-certified-limit-strong"
        and str(pairwise_transport.get("theorem_status")) == "pairwise-transport-chain-strong"
        and str(triple_transport_cocycle.get("theorem_status")) == "triple-transport-cocycle-strong"
        and str(global_transport_potential.get("theorem_status")) == "global-transport-potential-strong"
        and str(tail_cauchy_potential.get("theorem_status")) == "tail-cauchy-potential-strong"
        and str(certified_tail_modulus.get("theorem_status")) == "certified-tail-modulus-strong"
        and str(rate_aware_tail_modulus.get("theorem_status")) == "rate-aware-tail-modulus-strong"
        and str(golden_recurrence_rate.get("theorem_status")) == "golden-recurrence-rate-strong"
        and str(transport_slope_weighted_golden_rate.get("theorem_status")) == "transport-slope-weighted-golden-rate-strong"
        and str(edge_class_weighted_golden_rate.get("theorem_status")) == "edge-class-weighted-golden-rate-strong"
        and str(upper_tail.get("theorem_status", "")).endswith("-strong")
    )
    final_layer_override_strong = bool(
        lower_bound is not None
        and (
            (compatible_lo is not None and float(lower_bound) < float(compatible_lo))
            or (theorem_target_lo is not None and float(lower_bound) < float(theorem_target_lo))
        )
        and str(lower.get("theorem_status", "")).endswith("-strong")
        and str(upper_tail.get("theorem_status", "")).endswith("-strong")
        and str(theorem_v_explicit_error.get("theorem_status", "")).endswith("-strong")
        and bool(theorem_v_uniform_error.get("final_error_law_certified", False))
        and bool(theorem_v_branch_identification.get("branch_identification_locked", False))
        and bool(final_transport_bridge.get("transport_bridge_locked", False))
        and bool(theorem_v_uniform_error.get("late_suffix_rigidity_ready", False))
    )

    if lower_bound is not None and ((compatible_lo is not None and float(lower_bound) < float(compatible_lo)) or (theorem_target_lo is not None and float(lower_bound) < float(theorem_target_lo))):
        if strong_intermediate_stack or final_layer_override_strong:
            status = "golden-rational-to-irrational-convergence-strong"
        else:
            status = "golden-rational-to-irrational-convergence-partial"
        notes = (
            "A neighborhood-stable golden lower object lies below a fourteen-layer compatible upper interval: the fitted q-tail limit-control layer, the non-model-based branch-certified tail envelope, the nested convergent-subladder control, the explicit convergent-family telescoping layer, the transport-certified convergent-family layer, the pairwise continuation-aware transport chain, the three-step cocycle-style transport layer, the ladder-global transport-potential layer, the explicit tail-Cauchy remainder-decomposition layer, the certified start-index tail modulus layer, the denominator-scale rate-aware tail modulus layer, the golden/Fibonacci-normalized recurrence-aware rate layer, the transport-slope weighted golden recurrence layer, and the neighborhood-stable golden upper-tail audit all agree on a surviving upper window. "
            "This is a stronger theorem-facing bridge toward Theorem V than the earlier raw ladder audits. When the runtime-aware uniform error law, late-suffix rigidity witness, and branch-identification layer all lock simultaneously, this compressed final package is allowed to dominate weaker intermediate diagnostics."
        )
    elif model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_lo is not None and lower_bound is not None and float(lower_bound) < float(model_branch_nested_conv_transport_pair_triple_global_cauchy_modulus_rate_golden_transport_lo):
        status = "golden-rational-to-irrational-convergence-fragile"
        notes = (
            "The explicit q-tail fit, the non-model-based branch-certified tail envelope, the nested convergent-subladder control, the convergent-family telescoping layer, the transport-certified convergent-family layer, the pairwise continuation-aware transport chain, the three-step cocycle-style transport layer, the ladder-global transport-potential layer, the explicit tail-Cauchy remainder-decomposition layer, the certified start-index tail modulus layer, the denominator-scale rate-aware tail modulus layer, the golden/Fibonacci-normalized recurrence-aware rate layer, and the transport-slope weighted golden recurrence layer agree on an upper interval above the lower-side golden object, but that overlap is not yet corroborated by the neighborhood-stable upper-tail audit."
        )
    elif fit_lo is not None and branch_lo is not None and nested_lo is not None and conv_lo is not None and transport_lo is not None and pairwise_lo is not None and triple_lo is not None and global_lo is not None and tail_cauchy_lo is not None and tail_modulus_lo is not None and rate_modulus_lo is not None and golden_rate_lo is not None and transport_weighted_golden_lo is not None and lower_bound is not None and float(lower_bound) < min(float(fit_lo), float(branch_lo), float(nested_lo), float(conv_lo), float(transport_lo), float(pairwise_lo), float(triple_lo), float(global_lo), float(tail_cauchy_lo), float(tail_modulus_lo), float(rate_modulus_lo), float(golden_rate_lo), float(transport_weighted_golden_lo)):
        status = "golden-rational-to-irrational-convergence-fragile"
        notes = (
            "The fit layer, branch-certified tail envelope, nested convergent-subladder layer, convergent-family telescoping layer, transport-certified convergent-family layer, pairwise continuation-aware chain, three-step cocycle-style transport layer, ladder-global transport-potential layer, explicit tail-Cauchy remainder-decomposition layer, certified start-index tail modulus layer, denominator-scale rate-aware tail modulus layer, golden/Fibonacci-normalized recurrence-aware rate layer, and transport-slope weighted golden recurrence layer separately separate from the lower-side golden object, but they do not yet produce a stable fourteen-layer compatible interval once the upper-tail audit is imposed."
        )
    else:
        status = "golden-rational-to-irrational-convergence-incomplete"
        notes = (
            "The model-based q-tail layer, the branch-certified tail envelope, the nested convergent-subladder control, the convergent-family telescoping layer, the transport-certified convergent-family layer, the pairwise continuation-aware transport chain, the three-step cocycle-style transport layer, the ladder-global transport-potential layer, the explicit tail-Cauchy remainder-decomposition layer, the certified start-index tail modulus layer, the denominator-scale rate-aware tail modulus layer, the golden/Fibonacci-normalized recurrence-aware rate layer, the transport-slope weighted golden recurrence layer, and the upper-tail stability audit do not yet yield a clean two-sided separation simultaneously."
        )

    return GoldenRationalToIrrationalConvergenceCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        upper_tail_stability=upper_tail,
        convergence_control=convergence,
        branch_certified_control=branch_certified,
        nested_subladder_control=nested_subladder,
        convergent_family_control=convergent_family,
        transport_certified_control=transport_certified,
        pairwise_transport_control=pairwise_transport,
        triple_transport_cocycle_control=triple_transport_cocycle,
        global_transport_potential_control=global_transport_potential,
        tail_cauchy_potential_control=tail_cauchy_potential,
        certified_tail_modulus_control=certified_tail_modulus,
        rate_aware_tail_modulus_control=rate_aware_tail_modulus,
        golden_recurrence_rate_control=golden_recurrence_rate,
        transport_slope_weighted_golden_rate_control=transport_slope_weighted_golden_rate,
        edge_class_weighted_golden_rate_control=edge_class_weighted_golden_rate,
        theorem_v_explicit_error_control=theorem_v_explicit_error,
        theorem_v_final_error_control=theorem_v_final_error,
        theorem_v_uniform_error_law=theorem_v_uniform_error,
        theorem_v_branch_identification=theorem_v_branch_identification,
        runtime_row_233_377=runtime_row_233_377,
        runtime_row_377_610=runtime_row_377_610,
        final_transport_bridge=final_transport_bridge,
        relation=relation,
        theorem_status=status,
        notes=notes,
    )


__all__ = [
    "GoldenRationalToIrrationalConvergenceCertificate",
    "build_final_transport_bridge_certificate",
    "build_golden_rational_to_irrational_convergence_certificate",
]
