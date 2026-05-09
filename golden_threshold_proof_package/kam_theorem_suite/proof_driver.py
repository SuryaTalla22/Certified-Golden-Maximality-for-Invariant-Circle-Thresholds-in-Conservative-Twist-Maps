from __future__ import annotations

"""High-level orchestration helpers for the enhanced proof bridge.

This is deliberately lightweight: it turns the lower-level arithmetic, branch,
and residue-certification routines into a small set of reusable entry points
that can be called from notebooks, scripts, or future proof-search tooling.
"""

from dataclasses import dataclass, asdict
from typing import Any, Mapping, Sequence

from .arithmetic import approximate_eta_from_periodic_cf, class_label, periodic_cf_to_float
from .arithmetic_exact import cycle_eta_estimates
from .branch_tube import build_branch_tube
from .certification import get_residue_and_derivative_iv
from .standard_map import HarmonicFamily
from .interval_utils import iv_scalar
from .torus_validator import (
    validate_invariant_circle_graph,
    build_analytic_invariant_circle_certificate,
    build_existence_vs_crossing_bridge,
)
from .torus_continuation import continue_invariant_circle_validations, scan_torus_validity_on_grid
from .irrational_existence_atlas import (
    validate_invariant_circle_multiresolution,
    continue_invariant_circle_multiresolution,
    build_multiresolution_existence_vs_crossing_bridge,
)
from .crossing_certificate import build_endpoint_residue_certificate, certify_unique_crossing_window
from .threshold_bracketing import build_threshold_corridor_report
from .supercritical_bands import (
    certify_hyperbolic_window,
    build_supercritical_band_report,
    build_crossing_to_hyperbolic_band_bridge,
)
from .obstruction_atlas import (
    ApproximantWindowSpec,
    build_multi_approximant_obstruction_atlas,
    compare_atlas_to_reference,
)
from .challenger_pruning import (
    ChallengerSpec,
    build_challenger_pruning_report,
    extract_challengers_from_atlas,
)
from .class_campaigns import (
    ArithmeticClassSpec,
    build_class_ladder_report,
    build_class_atlas_campaign,
    build_multi_class_campaign,
)
from .adaptive_campaigns import (
    build_adaptive_class_campaign,
    build_adaptive_multi_class_campaign,
)
from .seed_transfer import build_seed_profile_from_orbit, build_seed_transfer_report
from .seeded_campaigns import (
    build_seeded_class_campaign,
    build_seeded_multi_class_campaign,
)
from .multi_source_seed_atlas import build_multi_source_seed_atlas
from .multi_source_campaigns import (
    build_multi_source_class_campaign,
    build_multi_source_campaign_comparison,
    build_multi_source_multi_class_campaign,
)
from .two_sided_irrational_atlas import (
    build_rational_upper_ladder,
    build_two_sided_irrational_threshold_atlas,
)
from .upper_ladder_refinement import refine_rational_upper_ladder
from .asymptotic_upper_ladder_audit import audit_refined_upper_ladder_asymptotics
from .class_exhaustion_screen import build_class_exhaustion_screen
from .challenger_search_loop import build_adaptive_class_exhaustion_search
from .evidence_weighted_search import build_evidence_weighted_class_exhaustion_search
from .termination_aware_search import build_termination_aware_class_exhaustion_search
from .golden_aposteriori import (
    build_golden_aposteriori_certificate,
    build_golden_theorem_iii_certificate,
    continue_golden_aposteriori_certificates,
)
from .golden_supercritical import (
    build_golden_supercritical_obstruction_certificate,
    build_golden_two_sided_bridge_certificate,
)
from .golden_supercritical_continuation import (
    build_golden_supercritical_continuation_certificate,
    build_golden_two_sided_continuation_bridge_certificate,
)
from .golden_supercritical_localization import (
    build_golden_supercritical_localization_certificate,
    build_golden_two_sided_localization_bridge_certificate,
)
from .golden_supercritical_localization_atlas import (
    build_golden_supercritical_localization_atlas_certificate,
    build_golden_two_sided_localization_atlas_bridge_certificate,
)
from .golden_upper_support_audit import (
    build_golden_upper_support_audit_certificate,
    build_golden_two_sided_support_audit_bridge_certificate,
)
from .golden_upper_tail_stability import (
    build_golden_upper_tail_stability_certificate,
    build_golden_two_sided_tail_stability_bridge_certificate,
)
from .golden_lower_neighborhood_stability import (
    build_golden_lower_neighborhood_stability_certificate,
    build_golden_two_sided_neighborhood_tail_bridge_certificate,
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
from .theorem_v_error_control import build_theorem_v_explicit_error_certificate
from .golden_limit_bridge import build_golden_rational_to_irrational_convergence_certificate
from .theorem_v_transport_lift import (
    build_golden_theorem_v_transport_lift_certificate,
    build_golden_theorem_v_certificate,
    build_golden_theorem_v_compressed_lift_certificate,
)
from .theorem_v_batched import (
    build_golden_rational_to_irrational_convergence_certificate_batched,
    build_golden_theorem_v_certificate_batched,
)
from .renormalization_class import build_renormalization_class_certificate
from .universality_class import build_universality_class_certificate
from .renormalization import build_renormalization_operator_certificate
from .renormalization_fixed_point import build_renormalization_fixed_point_certificate
from .linearization_bounds import build_linearization_bounds_certificate
from .fixed_point_enclosure import build_fixed_point_enclosure_certificate
from .spectral_splitting import build_spectral_splitting_certificate
from .stable_manifold import build_stable_manifold_chart_certificate
from .critical_surface import (
    build_family_transversality_certificate,
    build_critical_surface_bridge_certificate,
)
from .transversality_window import (
    build_transversality_window_certificate,
    build_validated_critical_surface_bridge_certificate,
)
from .chart_threshold_linkage import (
    build_chart_threshold_linkage_certificate,
    build_golden_chart_threshold_bridge_certificate,
)
from .threshold_compatibility import (
    build_threshold_compatibility_window_certificate,
    build_validated_threshold_compatibility_bridge_certificate,
)
from .threshold_identification_lift import (
    build_golden_threshold_identification_lift_certificate,
    build_golden_theorem_ii_to_v_identification_certificate,
)
from .threshold_identification_discharge import (
    build_golden_threshold_identification_discharge_certificate,
    build_golden_theorem_ii_to_v_identification_discharge_certificate,
)
from .threshold_identification_transport_discharge import (
    build_golden_threshold_identification_transport_discharge_certificate,
    build_golden_theorem_ii_to_v_identification_transport_discharge_certificate,
)
from .threshold_identification_localized_implication import (
    build_golden_threshold_identification_localized_implication_certificate,
    build_golden_theorem_ii_to_v_identification_theorem_certificate,
)
from .transport_locked_threshold_uniqueness import (
    build_transport_locked_threshold_uniqueness_certificate,
)
from .theorem_vi_envelope_discharge import (
    build_golden_theorem_vi_envelope_discharge_lift_certificate,
    build_golden_theorem_vi_discharge_certificate,
)
from .theorem_vii_exhaustion_discharge import (
    build_golden_theorem_vii_exhaustion_discharge_lift_certificate,
    build_golden_theorem_vii_discharge_certificate,
)
from .theorem_i_ii_workstream_lift import (
    build_golden_theorem_i_ii_workstream_lift_certificate,
    build_golden_theorem_i_ii_certificate,
)
from .validated_critical_surface_theorem import (
    build_validated_critical_surface_theorem_discharge_certificate,
    build_validated_critical_surface_theorem_promotion_certificate,
)
from .validated_universality_class_theorem import (
    build_validated_universality_class_theorem_discharge_certificate,
    build_validated_universality_class_theorem_promotion_certificate,
)
from .validated_renormalization_package import (
    build_validated_renormalization_package_discharge_certificate,
    build_validated_renormalization_package_promotion_certificate,
)
from .eta_comparison import (
    build_eta_threshold_comparison_certificate,
    build_proto_envelope_eta_bridge_certificate,
)
from .eta_challenger_comparison import (
    EtaChallengerSpec,
    build_near_top_eta_challenger_comparison_certificate,
    build_campaign_driven_eta_challenger_comparison_certificate,
)
from .theorem_vi_envelope_lift import (
    build_golden_theorem_vi_envelope_lift_certificate,
    build_golden_theorem_vi_certificate,
)
from .theorem_vii_exhaustion_lift import (
    build_golden_theorem_vii_exhaustion_lift_certificate,
    build_golden_theorem_vii_certificate,
)
from .theorem_vii_global_completeness import (
    build_golden_theorem_vii_global_completeness_certificate,
)
from .theorem_viii_reduction_lift import (
    build_golden_theorem_viii_reduction_lift_certificate,
    build_golden_theorem_viii_certificate,
)
from .theorem_viii_reduction_discharge import (
    build_golden_theorem_viii_reduction_discharge_lift_certificate,
    build_golden_theorem_viii_discharge_certificate,
)
from .periodic_branch_tube import build_periodic_branch_tube_certificate
from .residue_branch import analyze_residue_branch_window, adaptive_localize_residue_crossing
from .adaptive_incompatibility import (
    build_adaptive_incompatibility_atlas_certificate,
    build_golden_adaptive_incompatibility_certificate,
)
from .adaptive_tail_stability import (
    build_golden_adaptive_tail_stability_certificate,
    build_golden_two_sided_adaptive_tail_bridge_certificate,
)
from .adaptive_tail_coherence import (
    build_golden_adaptive_tail_coherence_certificate,
    build_golden_two_sided_adaptive_tail_coherence_bridge_certificate,
)
from .incompatibility_theorem_bridge import (
    build_golden_incompatibility_theorem_bridge_certificate,
    build_golden_two_sided_incompatibility_theorem_bridge_certificate,
)
from .incompatibility_bridge_profile import (
    build_golden_incompatibility_bridge_profile_certificate,
)
from .incompatibility_strict_bridge import (
    build_golden_incompatibility_strict_bridge_certificate,
)
from .adaptive_support_core_neighborhood import (
    build_golden_adaptive_support_core_neighborhood_certificate,
)
from .adaptive_tail_aware_neighborhood import (
    build_golden_adaptive_tail_aware_neighborhood_certificate,
)
from .nonexistence_front import (
    build_golden_nonexistence_front_certificate,
)
from .theorem_iv_analytic_lift import (
    build_golden_analytic_incompatibility_lift_certificate,
    build_golden_theorem_iv_certificate,
)
from .theorem_iv_obstruction import (
    build_periodic_ladder_incompatibility_certificate,
    build_golden_irrational_incompatibility_certificate,
    build_golden_two_sided_incompatibility_bridge_certificate,
)


@dataclass
class PeriodicClassReport:
    label: str
    rho: float
    eta_approx: float
    eta_cycle: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CrossingWindowReport:
    p: int
    q: int
    K_lo: float
    K_hi: float
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_periodic_class_report(period: Sequence[int], preperiod: Sequence[int] | None = None) -> PeriodicClassReport:
    pre = tuple(preperiod or ())
    eta_cycle = None
    if not pre:
        eta_cycle = cycle_eta_estimates(period)
    return PeriodicClassReport(
        label=class_label(period=period, preperiod=preperiod),
        rho=periodic_cf_to_float(period=period, preperiod=preperiod),
        eta_approx=approximate_eta_from_periodic_cf(period=period, preperiod=preperiod),
        eta_cycle=eta_cycle,
    )


def build_crossing_window_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    x_guess=None,
    target_residue: float = 0.25,
) -> CrossingWindowReport:
    family = family or HarmonicFamily()
    summary = get_residue_and_derivative_iv(
        p=p,
        q=q,
        K_iv=iv_scalar(K_lo, K_hi),
        family=family,
        x_guess=x_guess,
        target_residue=target_residue,
    )
    return CrossingWindowReport(p=p, q=q, K_lo=K_lo, K_hi=K_hi, summary=summary)


def build_periodic_branch_tube_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    x_guess=None,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_periodic_branch_tube_certificate(
        p=p, q=q, K_lo=K_lo, K_hi=K_hi, family=family, x_guess=x_guess
    ).to_dict()


def build_residue_branch_window_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    target_residue: float = 0.25,
    depth: int = 0,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return analyze_residue_branch_window(
        p=p, q=q, K_lo=K_lo, K_hi=K_hi, family=family, x_guess=x_guess, target_residue=target_residue, depth=depth
    ).to_dict()


def build_adaptive_residue_crossing_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    max_depth: int = 6,
    min_width: float = 1e-5,
    n_pieces: int = 2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return adaptive_localize_residue_crossing(
        p=p, q=q, K_lo=K_lo, K_hi=K_hi, family=family, target_residue=target_residue,
        max_depth=max_depth, min_width=min_width, n_pieces=n_pieces
    ).to_dict()


def build_branch_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    x_guess=None,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    tube = build_branch_tube(p=p, q=q, K_lo=K_lo, K_hi=K_hi, family=family, x_guess=x_guess)
    return tube.to_dict()


def build_analytic_torus_validation_report(
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    sigma_cap: float = 0.04,
    oversample_factor: int = 8,
    u0=None,
    z0=None,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_analytic_invariant_circle_certificate(
        rho=rho, K=K, family=family, N=N, sigma_cap=sigma_cap, oversample_factor=oversample_factor, u0=u0, z0=z0
    ).to_dict()


def build_torus_validation_report(
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    u0=None,
    z0=None,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return validate_invariant_circle_graph(rho=rho, K=K, family=family, N=N, u0=u0, z0=z0).to_dict()


def build_existence_crossing_bridge_report(
    rho: float,
    K: float,
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    target_residue: float = 0.25,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_existence_vs_crossing_bridge(
        rho=rho,
        K=K,
        p=p,
        q=q,
        K_lo=K_lo,
        K_hi=K_hi,
        family=family,
        N=N,
        target_residue=target_residue,
    )


def build_torus_continuation_report(
    rho: float,
    K_values,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    initial_z0=None,
    restart_on_failure: bool = True,
    reverse_if_descending: bool = False,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    report = continue_invariant_circle_validations(
        rho=rho,
        K_values=K_values,
        family=family,
        N=N,
        initial_z0=initial_z0,
        restart_on_failure=restart_on_failure,
        reverse_if_descending=reverse_if_descending,
    )
    return report.to_dict()


def build_golden_aposteriori_certificate_report(
    K: float,
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N: int = 128,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_aposteriori_certificate(
        K=K,
        family=family,
        rho=rho,
        N=N,
        N_values=N_values,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
    ).to_dict()


def build_golden_aposteriori_continuation_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return continue_golden_aposteriori_certificates(
        K_values=K_values,
        family=family,
        rho=rho,
        N_values=N_values,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
    ).to_dict()




def build_golden_supercritical_obstruction_report(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
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
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_supercritical_obstruction_certificate(
        family=family, rho=rho, n_terms=n_terms, keep_last=keep_last, min_q=min_q, max_q=max_q,
        crossing_center=crossing_center, crossing_half_width=crossing_half_width, band_offset=band_offset, band_width=band_width,
        target_residue=target_residue, auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions, max_depth=max_depth, min_width=min_width,
        refine_upper_ladder=refine_upper_ladder, asymptotic_min_members=asymptotic_min_members,
    ).to_dict()


def build_golden_two_sided_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
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
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_bridge_certificate(
        K_values=K_values, family=family, rho=rho, N_values=N_values, sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution, oversample_factor=oversample_factor,
        n_terms=n_terms, keep_last=keep_last, min_q=min_q, max_q=max_q,
        crossing_center=crossing_center, crossing_half_width=crossing_half_width, band_offset=band_offset, band_width=band_width,
        target_residue=target_residue, auto_localize_crossing=auto_localize_crossing, initial_subdivisions=initial_subdivisions,
        max_depth=max_depth, min_width=min_width, refine_upper_ladder=refine_upper_ladder, asymptotic_min_members=asymptotic_min_members,
    ).to_dict()


def build_golden_supercritical_continuation_report(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_supercritical_continuation_certificate(
        family=family, rho=rho, crossing_center=crossing_center, crossing_center_offsets=crossing_center_offsets,
        band_offset=band_offset, band_offset_slope=band_offset_slope, crossing_half_width=crossing_half_width,
        band_width=band_width, n_terms=n_terms, keep_last=keep_last, min_q=min_q, max_q=max_q,
        target_residue=target_residue, auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions, max_depth=max_depth, min_width=min_width,
        refine_upper_ladder=refine_upper_ladder, asymptotic_min_members=asymptotic_min_members,
    ).to_dict()


def build_golden_two_sided_continuation_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    crossing_center: float = 0.971635406,
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_continuation_bridge_certificate(
        K_values=K_values, family=family, rho=rho, N_values=N_values, sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution, oversample_factor=oversample_factor,
        crossing_center=crossing_center, crossing_center_offsets=crossing_center_offsets,
        band_offset=band_offset, band_offset_slope=band_offset_slope, crossing_half_width=crossing_half_width, band_width=band_width,
        n_terms=n_terms, keep_last=keep_last, min_q=min_q, max_q=max_q, target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing, initial_subdivisions=initial_subdivisions, max_depth=max_depth,
        min_width=min_width, refine_upper_ladder=refine_upper_ladder, asymptotic_min_members=asymptotic_min_members,
    ).to_dict()

def build_multiresolution_torus_validation_report(
    rho: float,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    N_values: Sequence[int] = (64, 96, 128),
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return validate_invariant_circle_multiresolution(
        rho=rho, K=K, family=family, N_values=N_values
    ).to_dict()


def build_multiresolution_torus_continuation_report(
    rho: float,
    K_values,
    family: HarmonicFamily | None = None,
    *,
    N_values: Sequence[int] = (64, 96, 128),
    quality_floor: str = "moderate",
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return continue_invariant_circle_multiresolution(
        rho=rho, K_values=K_values, family=family, N_values=N_values, quality_floor=quality_floor
    ).to_dict()


def build_multiresolution_existence_crossing_bridge_report(
    rho: float,
    K_values,
    p: int,
    q: int,
    crossing_K_lo: float,
    crossing_K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    N_values: Sequence[int] = (64, 96, 128),
    quality_floor: str = "moderate",
    target_residue: float = 0.25,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_multiresolution_existence_vs_crossing_bridge(
        rho=rho, K_values=K_values, N_values=N_values, p=p, q=q,
        crossing_K_lo=crossing_K_lo, crossing_K_hi=crossing_K_hi,
        family=family, quality_floor=quality_floor, target_residue=target_residue,
    ).to_dict()


def build_torus_grid_scan_report(
    rho: float,
    K_min: float,
    K_max: float,
    n_steps: int,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    report = scan_torus_validity_on_grid(
        rho=rho, K_min=K_min, K_max=K_max, n_steps=n_steps, family=family, N=N
    )
    return report.to_dict()


def build_periodic_obstruction_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    target_residue: float = 0.25,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    from .obstruction import build_periodic_obstruction_report as _build

    return _build(
        p=p,
        q=q,
        K_lo=K_lo,
        K_hi=K_hi,
        family=family,
        x_guess=x_guess,
        target_residue=target_residue,
    ).to_dict()


def build_existence_obstruction_bridge_report(
    rho: float,
    K_subcritical: float,
    K_supercritical_lo: float,
    K_supercritical_hi: float,
    p: int,
    q: int,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    target_residue: float = 0.25,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    from .obstruction import build_existence_obstruction_bridge as _build

    return _build(
        rho=rho,
        K_subcritical=K_subcritical,
        K_supercritical_lo=K_supercritical_lo,
        K_supercritical_hi=K_supercritical_hi,
        p=p,
        q=q,
        family=family,
        N=N,
        target_residue=target_residue,
    ).to_dict()


def build_periodic_ladder_incompatibility_report(
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    min_tail_members: int = 2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_periodic_ladder_incompatibility_certificate(
        specs=specs,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        min_tail_members=min_tail_members,
    ).to_dict()


def build_adaptive_incompatibility_atlas_report(
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_adaptive_incompatibility_atlas_certificate(specs, family=family, **kwargs).to_dict()


def build_golden_adaptive_incompatibility_report(
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_adaptive_incompatibility_certificate(family=family, **kwargs).to_dict()


def build_golden_adaptive_tail_stability_report(
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_adaptive_tail_stability_certificate(family=family, **kwargs).to_dict()


def build_golden_two_sided_adaptive_tail_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_adaptive_tail_bridge_certificate(K_values=K_values, family=family, **kwargs).to_dict()


def build_golden_adaptive_tail_coherence_report(
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_adaptive_tail_coherence_certificate(family=family, **kwargs).to_dict()


def build_golden_two_sided_adaptive_tail_coherence_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_adaptive_tail_coherence_bridge_certificate(K_values=K_values, family=family, **kwargs).to_dict()


def build_golden_incompatibility_theorem_bridge_report(
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_incompatibility_theorem_bridge_certificate(family=family, **kwargs).to_dict()


def build_golden_incompatibility_bridge_profile_report(
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_incompatibility_bridge_profile_certificate(family=family, **kwargs).to_dict()


def build_golden_incompatibility_strict_bridge_report(
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_incompatibility_strict_bridge_certificate(family=family, **kwargs).to_dict()


def build_golden_adaptive_support_core_neighborhood_report(
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_adaptive_support_core_neighborhood_certificate(family=family, **kwargs).to_dict()


def build_golden_adaptive_tail_aware_neighborhood_report(
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_adaptive_tail_aware_neighborhood_certificate(family=family, **kwargs).to_dict()


def build_golden_nonexistence_front_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_nonexistence_front_certificate(base_K_values=base_K_values, family=family, **kwargs).to_dict()


def build_golden_analytic_incompatibility_lift_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_analytic_incompatibility_lift_certificate(base_K_values=base_K_values, family=family, **kwargs).to_dict()


def build_golden_theorem_iii_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_iii_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_theorem_iv_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_iv_certificate(base_K_values=base_K_values, family=family, **kwargs).to_dict()


def build_golden_two_sided_incompatibility_theorem_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_incompatibility_theorem_bridge_certificate(K_values=K_values, family=family, **kwargs).to_dict()


def build_golden_irrational_incompatibility_report(
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_irrational_incompatibility_certificate(family=family, **kwargs).to_dict()


def build_golden_two_sided_incompatibility_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_incompatibility_bridge_certificate(
        K_values=K_values,
        family=family,
        **kwargs,
    ).to_dict()


def build_endpoint_residue_report(
    p: int,
    q: int,
    K: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    K_anchor: float | None = None,
    target_residue: float = 0.25,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_endpoint_residue_certificate(
        p=p,
        q=q,
        K=K,
        family=family,
        x_guess=x_guess,
        K_anchor=K_anchor,
        target_residue=target_residue,
    ).to_dict()


def build_unique_crossing_certificate_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    target_residue: float = 0.25,
    auto_localize: bool = False,
    localization_grid: int = 121,
    K_seed: float = 0.0,
    adaptive_refine: bool = True,
    adaptive_max_depth: int = 6,
    adaptive_min_width: float = 1e-5,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return certify_unique_crossing_window(
        p=p,
        q=q,
        K_lo=K_lo,
        K_hi=K_hi,
        family=family,
        x_guess=x_guess,
        target_residue=target_residue,
        auto_localize=auto_localize,
        localization_grid=localization_grid,
        K_seed=K_seed,
        adaptive_refine=adaptive_refine,
        adaptive_max_depth=adaptive_max_depth,
        adaptive_min_width=adaptive_min_width,
    ).to_dict()


def build_threshold_corridor_report_driver(
    rho: float,
    K_values,
    p: int,
    q: int,
    crossing_K_lo: float,
    crossing_K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    N: int = 128,
    quality_floor: str = "moderate",
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_threshold_corridor_report(
        rho=rho,
        K_values=K_values,
        p=p,
        q=q,
        crossing_K_lo=crossing_K_lo,
        crossing_K_hi=crossing_K_hi,
        family=family,
        N=N,
        quality_floor=quality_floor,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
    ).to_dict()



def build_hyperbolic_window_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return certify_hyperbolic_window(
        p=p,
        q=q,
        K_lo=K_lo,
        K_hi=K_hi,
        family=family,
        target_residue=target_residue,
    ).to_dict()


def build_supercritical_band_report_driver(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_supercritical_band_report(
        p=p,
        q=q,
        K_lo=K_lo,
        K_hi=K_hi,
        family=family,
        target_residue=target_residue,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()


def build_crossing_to_hyperbolic_bridge_report(
    p: int,
    q: int,
    crossing_K_lo: float,
    crossing_K_hi: float,
    band_search_lo: float,
    band_search_hi: float,
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_crossing_to_hyperbolic_band_bridge(
        p=p,
        q=q,
        crossing_K_lo=crossing_K_lo,
        crossing_K_hi=crossing_K_hi,
        band_search_lo=band_search_lo,
        band_search_hi=band_search_hi,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()



def build_multi_approximant_atlas_report(
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_multi_approximant_obstruction_atlas(
        specs=specs,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()


def build_atlas_reference_comparison_report(
    atlas: dict[str, Any],
    *,
    reference_label: str,
    reference_crossing_lo: float,
    reference_crossing_hi: float,
) -> dict[str, Any]:
    return compare_atlas_to_reference(
        atlas=atlas,
        reference_label=reference_label,
        reference_crossing_lo=reference_crossing_lo,
        reference_crossing_hi=reference_crossing_hi,
    ).to_dict()


def build_challenger_pruning_report_driver(
    challengers: Sequence[ChallengerSpec],
    *,
    golden_lower_bound: float,
    dps: int = 160,
    burn_in_cycles: int = 12,
    eta_reference_golden: float = 1.0 / (5.0 ** 0.5),
) -> dict[str, Any]:
    return build_challenger_pruning_report(
        challengers=challengers,
        golden_lower_bound=golden_lower_bound,
        dps=dps,
        burn_in_cycles=burn_in_cycles,
        eta_reference_golden=eta_reference_golden,
    ).to_dict()


def build_pruning_report_from_atlas(
    atlas: dict[str, Any],
    *,
    class_map: dict[str, tuple[tuple[int, ...], tuple[int, ...]]],
    golden_lower_bound: float,
    dps: int = 160,
    burn_in_cycles: int = 12,
    eta_reference_golden: float = 1.0 / (5.0 ** 0.5),
) -> dict[str, Any]:
    challengers = extract_challengers_from_atlas(atlas, class_map=class_map)
    return build_challenger_pruning_report(
        challengers=challengers,
        golden_lower_bound=golden_lower_bound,
        dps=dps,
        burn_in_cycles=burn_in_cycles,
        eta_reference_golden=eta_reference_golden,
    ).to_dict()


def build_class_ladder_report_driver(
    spec: ArithmeticClassSpec,
    *,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    dps: int = 160,
    burn_in_cycles: int = 12,
) -> dict[str, Any]:
    return build_class_ladder_report(
        spec,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
        dps=dps,
        burn_in_cycles=burn_in_cycles,
    ).to_dict()


def build_class_atlas_campaign_report(
    spec: ArithmeticClassSpec,
    *,
    reference_lower_bound: float,
    reference_crossing_center: float,
    family: HarmonicFamily | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = True,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    crossing_half_width: float = 2.5e-3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_class_atlas_campaign(
        spec,
        reference_lower_bound=reference_lower_bound,
        reference_crossing_center=reference_crossing_center,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
        crossing_half_width=crossing_half_width,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
    ).to_dict()


def build_multi_class_campaign_report(
    classes: Sequence[ArithmeticClassSpec],
    *,
    reference_label: str,
    reference_lower_bound: float,
    reference_crossing_center: float,
    family: HarmonicFamily | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = True,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    crossing_half_width: float = 2.5e-3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_multi_class_campaign(
        classes,
        reference_label=reference_label,
        reference_lower_bound=reference_lower_bound,
        reference_crossing_center=reference_crossing_center,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
        crossing_half_width=crossing_half_width,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
    ).to_dict()



def build_adaptive_class_campaign_report(
    spec: ArithmeticClassSpec,
    *,
    reference_lower_bound: float,
    reference_crossing_center: float,
    family: HarmonicFamily | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = True,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    initial_crossing_half_width: float = 2.5e-3,
    widening_factor: float = 1.75,
    max_attempts_per_approximant: int = 3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_adaptive_class_campaign(
        spec,
        reference_lower_bound=reference_lower_bound,
        reference_crossing_center=reference_crossing_center,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
        initial_crossing_half_width=initial_crossing_half_width,
        widening_factor=widening_factor,
        max_attempts_per_approximant=max_attempts_per_approximant,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
    ).to_dict()


def build_adaptive_multi_class_campaign_report(
    classes: Sequence[ArithmeticClassSpec],
    *,
    reference_label: str,
    reference_lower_bound: float,
    reference_crossing_center: float,
    family: HarmonicFamily | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = True,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    initial_crossing_half_width: float = 2.5e-3,
    widening_factor: float = 1.75,
    max_attempts_per_approximant: int = 3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_adaptive_multi_class_campaign(
        classes,
        reference_label=reference_label,
        reference_lower_bound=reference_lower_bound,
        reference_crossing_center=reference_crossing_center,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
        initial_crossing_half_width=initial_crossing_half_width,
        widening_factor=widening_factor,
        max_attempts_per_approximant=max_attempts_per_approximant,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
    ).to_dict()


def build_seed_transfer_report_driver(
    source_x,
    *,
    source_p: int,
    source_q: int,
    source_K: float,
    target_p: int,
    target_q: int,
    target_K: float,
    family: HarmonicFamily | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    profile = build_seed_profile_from_orbit(
        source_x,
        p=source_p,
        q=source_q,
        K=source_K,
        family=family,
        label=label,
    )
    return build_seed_transfer_report(
        profile,
        target_p=target_p,
        target_q=target_q,
        target_K=target_K,
        family=family,
    ).to_dict()


def build_seeded_class_campaign_report(
    spec: ArithmeticClassSpec,
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_seeded_class_campaign(
        spec,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        family=family,
        **kwargs,
    ).to_dict()


def build_seeded_multi_class_campaign_report(
    specs: list[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_seeded_multi_class_campaign(
        specs,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        family=family,
        **kwargs,
    ).to_dict()



def build_multi_source_seed_atlas_report_driver(
    seed_bank,
    *,
    target_p: int,
    target_q: int,
    target_K: float,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_multi_source_seed_atlas(
        seed_bank,
        target_p=target_p,
        target_q=target_q,
        target_K=target_K,
        family=family,
        **kwargs,
    ).to_dict()


def build_multi_source_class_campaign_report(
    spec: ArithmeticClassSpec,
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_multi_source_class_campaign(
        spec,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        family=family,
        **kwargs,
    ).to_dict()


def build_multi_source_campaign_comparison_report(
    spec: ArithmeticClassSpec,
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_multi_source_campaign_comparison(
        spec,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        family=family,
        **kwargs,
    ).to_dict()


def build_multi_source_multi_class_campaign_report(
    specs: list[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_multi_source_multi_class_campaign(
        specs,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        family=family,
        **kwargs,
    ).to_dict()





def build_refined_rational_upper_ladder_report(
    rho: float,
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    base_tol: float = 2.5e-4,
    q2_scale: float = 0.1,
    min_subset: int = 2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    raw = build_rational_upper_ladder(
        rho=rho,
        specs=specs,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()
    refined = refine_rational_upper_ladder(
        raw, base_tol=base_tol, q2_scale=q2_scale, min_subset=min_subset
    ).to_dict()
    return {
        "rho": float(rho),
        "family_label": type(family).__name__,
        "raw_upper_ladder": raw,
        "refined_upper_ladder": refined,
        "status": refined.get("status", "unknown"),
    }

def build_asymptotic_upper_ladder_audit_report(
    rho: float,
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    q_thresholds: Sequence[int] | None = None,
    min_members: int = 2,
    base_tol: float = 2.5e-4,
    q2_scale: float = 0.1,
    min_subset: int = 2,
    center_drift_tol: float = 5e-4,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    raw = build_rational_upper_ladder(
        rho=rho,
        specs=specs,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()
    refined = refine_rational_upper_ladder(
        raw, base_tol=base_tol, q2_scale=q2_scale, min_subset=min_subset
    ).to_dict()
    audit = audit_refined_upper_ladder_asymptotics(
        raw,
        q_thresholds=q_thresholds,
        min_members=min_members,
        base_tol=base_tol,
        q2_scale=q2_scale,
        min_subset=min_subset,
        center_drift_tol=center_drift_tol,
    ).to_dict()
    return {
        "rho": float(rho),
        "family_label": type(family).__name__,
        "raw_upper_ladder": raw,
        "refined_upper_ladder": refined,
        "asymptotic_upper_ladder_audit": audit,
        "status": audit.get("status", refined.get("status", "unknown")),
    }


def build_rational_upper_ladder_report(
    rho: float,
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_rational_upper_ladder(
        rho=rho,
        specs=specs,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()


def build_two_sided_irrational_threshold_atlas_report(
    rho: float,
    K_values,
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    N_values: Sequence[int] = (64, 96, 128),
    quality_floor: str = "moderate",
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    refinement_base_tol: float = 2.5e-4,
    refinement_q2_scale: float = 0.1,
    refinement_min_subset: int = 2,
    audit_upper_ladder_asymptotics: bool = True,
    asymptotic_min_members: int = 2,
    asymptotic_center_drift_tol: float = 5e-4,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_two_sided_irrational_threshold_atlas(
        rho=rho,
        K_values=K_values,
        specs=specs,
        family=family,
        N_values=N_values,
        quality_floor=quality_floor,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        refine_upper_ladder=refine_upper_ladder,
        refinement_base_tol=refinement_base_tol,
        refinement_q2_scale=refinement_q2_scale,
        refinement_min_subset=refinement_min_subset,
        audit_upper_ladder_asymptotics=audit_upper_ladder_asymptotics,
        asymptotic_min_members=asymptotic_min_members,
        asymptotic_center_drift_tol=asymptotic_center_drift_tol,
    ).to_dict()


def build_class_exhaustion_screen_report(
    specs: Sequence[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    reference_label: str = "golden",
    family: HarmonicFamily | None = None,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    crossing_half_width: float = 2.5e-3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refinement_base_tol: float = 2.5e-4,
    refinement_q2_scale: float = 0.1,
    refinement_min_subset: int = 2,
    asymptotic_min_members: int = 2,
    asymptotic_center_drift_tol: float = 5e-4,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_class_exhaustion_screen(
        specs,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        reference_label=reference_label,
        family=family,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
        crossing_half_width=crossing_half_width,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        refinement_base_tol=refinement_base_tol,
        refinement_q2_scale=refinement_q2_scale,
        refinement_min_subset=refinement_min_subset,
        asymptotic_min_members=asymptotic_min_members,
        asymptotic_center_drift_tol=asymptotic_center_drift_tol,
    ).to_dict()


def build_adaptive_class_exhaustion_search_report(
    specs: Sequence[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    reference_label: str = "golden",
    family: HarmonicFamily | None = None,
    rounds: int = 3,
    per_round_budget: int = 2,
    initial_max_q: int = 89,
    max_q_step: int = 55,
    initial_n_terms: int = 96,
    n_terms_step: int = 24,
    q_min: int = 8,
    initial_keep_last: int | None = 4,
    keep_last_step: int = 1,
    initial_crossing_half_width: float = 2.5e-3,
    width_growth: float = 1.35,
    width_cap: float = 1.2e-2,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refinement_base_tol: float = 2.5e-4,
    refinement_q2_scale: float = 0.1,
    refinement_min_subset: int = 2,
    asymptotic_min_members: int = 2,
    asymptotic_member_cap: int = 5,
    asymptotic_center_drift_tol: float = 5e-4,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_adaptive_class_exhaustion_search(
        specs,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        reference_label=reference_label,
        family=family,
        rounds=rounds,
        per_round_budget=per_round_budget,
        initial_max_q=initial_max_q,
        max_q_step=max_q_step,
        initial_n_terms=initial_n_terms,
        n_terms_step=n_terms_step,
        q_min=q_min,
        initial_keep_last=initial_keep_last,
        keep_last_step=keep_last_step,
        initial_crossing_half_width=initial_crossing_half_width,
        width_growth=width_growth,
        width_cap=width_cap,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        refinement_base_tol=refinement_base_tol,
        refinement_q2_scale=refinement_q2_scale,
        refinement_min_subset=refinement_min_subset,
        asymptotic_min_members=asymptotic_min_members,
        asymptotic_member_cap=asymptotic_member_cap,
        asymptotic_center_drift_tol=asymptotic_center_drift_tol,
    ).to_dict()

def build_evidence_weighted_class_exhaustion_search_report(
    specs: Sequence[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    reference_label: str = "golden",
    family: HarmonicFamily | None = None,
    rounds: int = 4,
    per_round_budget: int = 2,
    initial_max_q: int = 89,
    max_q_step: int = 55,
    initial_n_terms: int = 96,
    n_terms_step: int = 24,
    q_min: int = 8,
    initial_keep_last: int | None = 4,
    keep_last_step: int = 1,
    initial_crossing_half_width: float = 2.5e-3,
    width_growth: float = 1.30,
    width_cap: float = 1.2e-2,
    productive_q_multiplier: float = 1.6,
    sparse_width_multiplier: float = 1.25,
    stagnation_width_multiplier: float = 1.10,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refinement_base_tol: float = 2.5e-4,
    refinement_q2_scale: float = 0.1,
    refinement_min_subset: int = 2,
    asymptotic_min_members: int = 2,
    asymptotic_member_cap: int = 5,
    asymptotic_center_drift_tol: float = 5e-4,
    upper_improvement_tol: float = 2.5e-5,
    width_improvement_tol: float = 2.5e-5,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_evidence_weighted_class_exhaustion_search(
        specs,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        reference_label=reference_label,
        family=family,
        rounds=rounds,
        per_round_budget=per_round_budget,
        initial_max_q=initial_max_q,
        max_q_step=max_q_step,
        initial_n_terms=initial_n_terms,
        n_terms_step=n_terms_step,
        q_min=q_min,
        initial_keep_last=initial_keep_last,
        keep_last_step=keep_last_step,
        initial_crossing_half_width=initial_crossing_half_width,
        width_growth=width_growth,
        width_cap=width_cap,
        productive_q_multiplier=productive_q_multiplier,
        sparse_width_multiplier=sparse_width_multiplier,
        stagnation_width_multiplier=stagnation_width_multiplier,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        refinement_base_tol=refinement_base_tol,
        refinement_q2_scale=refinement_q2_scale,
        refinement_min_subset=refinement_min_subset,
        asymptotic_min_members=asymptotic_min_members,
        asymptotic_member_cap=asymptotic_member_cap,
        asymptotic_center_drift_tol=asymptotic_center_drift_tol,
        upper_improvement_tol=upper_improvement_tol,
        width_improvement_tol=width_improvement_tol,
    ).to_dict()



def build_termination_aware_class_exhaustion_search_report(
    specs: Sequence[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    reference_label: str = "golden",
    family: HarmonicFamily | None = None,
    rounds: int = 4,
    per_round_budget: int = 2,
    deferred_probe_budget: int = 1,
    deferred_probe_every: int = 2,
    initial_max_q: int = 89,
    max_q_step: int = 55,
    initial_n_terms: int = 96,
    n_terms_step: int = 24,
    q_min: int = 8,
    initial_keep_last: int | None = 4,
    keep_last_step: int = 1,
    initial_crossing_half_width: float = 2.5e-3,
    width_growth: float = 1.30,
    width_cap: float = 1.2e-2,
    productive_q_multiplier: float = 1.6,
    sparse_width_multiplier: float = 1.25,
    stagnation_width_multiplier: float = 1.10,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refinement_base_tol: float = 2.5e-4,
    refinement_q2_scale: float = 0.1,
    refinement_min_subset: int = 2,
    asymptotic_min_members: int = 2,
    asymptotic_member_cap: int = 5,
    asymptotic_center_drift_tol: float = 5e-4,
    upper_improvement_tol: float = 2.5e-5,
    width_improvement_tol: float = 2.5e-5,
    retire_dominated: bool = True,
    arithmetic_deferral_rounds: int = 2,
    arithmetic_wasted_escalations: int = 1,
    no_upper_deferral_rounds: int = 3,
    stagnation_deferral_rounds: int = 2,
    stagnation_wasted_escalations: int = 2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_termination_aware_class_exhaustion_search(
        specs,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        reference_label=reference_label,
        family=family,
        rounds=rounds,
        per_round_budget=per_round_budget,
        deferred_probe_budget=deferred_probe_budget,
        deferred_probe_every=deferred_probe_every,
        initial_max_q=initial_max_q,
        max_q_step=max_q_step,
        initial_n_terms=initial_n_terms,
        n_terms_step=n_terms_step,
        q_min=q_min,
        initial_keep_last=initial_keep_last,
        keep_last_step=keep_last_step,
        initial_crossing_half_width=initial_crossing_half_width,
        width_growth=width_growth,
        width_cap=width_cap,
        productive_q_multiplier=productive_q_multiplier,
        sparse_width_multiplier=sparse_width_multiplier,
        stagnation_width_multiplier=stagnation_width_multiplier,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        refinement_base_tol=refinement_base_tol,
        refinement_q2_scale=refinement_q2_scale,
        refinement_min_subset=refinement_min_subset,
        asymptotic_min_members=asymptotic_min_members,
        asymptotic_member_cap=asymptotic_member_cap,
        asymptotic_center_drift_tol=asymptotic_center_drift_tol,
        upper_improvement_tol=upper_improvement_tol,
        width_improvement_tol=width_improvement_tol,
        retire_dominated=retire_dominated,
        arithmetic_deferral_rounds=arithmetic_deferral_rounds,
        arithmetic_wasted_escalations=arithmetic_wasted_escalations,
        no_upper_deferral_rounds=no_upper_deferral_rounds,
        stagnation_deferral_rounds=stagnation_deferral_rounds,
        stagnation_wasted_escalations=stagnation_wasted_escalations,
    ).to_dict()



def build_golden_supercritical_localization_report(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
    max_rounds: int = 3,
    center_shrink: float = 0.5,
    width_shrink: float = 0.7,
    min_center_spacing: float = 5.0e-5,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_supercritical_localization_certificate(
        family=family,
        rho=rho,
        crossing_center=crossing_center,
        crossing_center_offsets=crossing_center_offsets,
        band_offset=band_offset,
        band_offset_slope=band_offset_slope,
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
    ).to_dict()


def build_golden_two_sided_localization_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    crossing_center: float = 0.971635406,
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
    max_rounds: int = 3,
    center_shrink: float = 0.5,
    width_shrink: float = 0.7,
    min_center_spacing: float = 5.0e-5,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_localization_bridge_certificate(
        K_values=K_values,
        family=family,
        rho=rho,
        N_values=N_values,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
        crossing_center=crossing_center,
        crossing_center_offsets=crossing_center_offsets,
        band_offset=band_offset,
        band_offset_slope=band_offset_slope,
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
    ).to_dict()



def build_golden_supercritical_localization_atlas_report(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_center_offsets: Sequence[float] = (-1.2e-3, -6.0e-4, 0.0, 6.0e-4, 1.2e-3),
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
    max_rounds: int = 3,
    center_shrink: float = 0.5,
    width_shrink: float = 0.7,
    min_center_spacing: float = 5.0e-5,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_supercritical_localization_atlas_certificate(
        family=family,
        rho=rho,
        crossing_center=crossing_center,
        atlas_center_offsets=atlas_center_offsets,
        crossing_center_offsets=crossing_center_offsets,
        band_offset=band_offset,
        band_offset_slope=band_offset_slope,
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
    ).to_dict()


def build_golden_two_sided_localization_atlas_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    crossing_center: float = 0.971635406,
    atlas_center_offsets: Sequence[float] = (-1.2e-3, -6.0e-4, 0.0, 6.0e-4, 1.2e-3),
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
    max_rounds: int = 3,
    center_shrink: float = 0.5,
    width_shrink: float = 0.7,
    min_center_spacing: float = 5.0e-5,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_localization_atlas_bridge_certificate(
        K_values=K_values,
        family=family,
        rho=rho,
        N_values=N_values,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
        crossing_center=crossing_center,
        atlas_center_offsets=atlas_center_offsets,
        crossing_center_offsets=crossing_center_offsets,
        band_offset=band_offset,
        band_offset_slope=band_offset_slope,
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
    ).to_dict()



def build_golden_upper_support_audit_report(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_center_offsets: Sequence[float] = (-1.2e-3, -6.0e-4, 0.0, 6.0e-4, 1.2e-3),
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
    max_rounds: int = 3,
    center_shrink: float = 0.5,
    width_shrink: float = 0.7,
    min_center_spacing: float = 5.0e-5,
    support_fraction_threshold: float = 0.6,
    min_tail_members: int = 2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_upper_support_audit_certificate(
        family=family,
        rho=rho,
        crossing_center=crossing_center,
        atlas_center_offsets=atlas_center_offsets,
        crossing_center_offsets=crossing_center_offsets,
        band_offset=band_offset,
        band_offset_slope=band_offset_slope,
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


def build_golden_two_sided_support_audit_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    crossing_center: float = 0.971635406,
    atlas_center_offsets: Sequence[float] = (-1.2e-3, -6.0e-4, 0.0, 6.0e-4, 1.2e-3),
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
    max_rounds: int = 3,
    center_shrink: float = 0.5,
    width_shrink: float = 0.7,
    min_center_spacing: float = 5.0e-5,
    support_fraction_threshold: float = 0.6,
    min_tail_members: int = 2,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_support_audit_bridge_certificate(
        K_values=K_values,
        family=family,
        rho=rho,
        N_values=N_values,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
        crossing_center=crossing_center,
        atlas_center_offsets=atlas_center_offsets,
        crossing_center_offsets=crossing_center_offsets,
        band_offset=band_offset,
        band_offset_slope=band_offset_slope,
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


def build_golden_upper_tail_stability_report(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_shifts: Sequence[float] = (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4),
    min_cluster_size: int = 2,
    min_stable_tail_members: int = 2,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_upper_tail_stability_certificate(
        family=family,
        rho=rho,
        crossing_center=crossing_center,
        atlas_shifts=atlas_shifts,
        min_cluster_size=min_cluster_size,
        min_stable_tail_members=min_stable_tail_members,
        **kwargs,
    ).to_dict()


def build_golden_two_sided_tail_stability_bridge_report(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    crossing_center: float = 0.971635406,
    atlas_shifts: Sequence[float] = (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4),
    min_cluster_size: int = 2,
    min_stable_tail_members: int = 2,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_tail_stability_bridge_certificate(
        K_values=K_values,
        family=family,
        rho=rho,
        N_values=N_values,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
        crossing_center=crossing_center,
        atlas_shifts=atlas_shifts,
        min_cluster_size=min_cluster_size,
        min_stable_tail_members=min_stable_tail_members,
        **kwargs,
    ).to_dict()


def build_golden_lower_neighborhood_stability_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_lower_neighborhood_stability_certificate(
        base_K_values=base_K_values, family=family, rho=rho, **kwargs
    ).to_dict()


def build_golden_theorem_iv_lower_neighborhood_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    lower_shift_grid: Sequence[float] = (-0.015, 0.0, 0.015),
    lower_resolution_sets: Sequence[Sequence[int]] = ((64, 96, 128), (80, 112, 144)),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    lower_min_cluster_size: int = 2,
) -> dict[str, Any]:
    """Build the exact broader lower-neighborhood object consumed by Theorem IV.

    This is intentionally separate from Theorem III so callers can materialize and
    cache the *same* lower certificate that Theorem IV would otherwise rebuild.
    Reusing this object preserves rigor because the theorem inputs are unchanged.
    """
    family = family or HarmonicFamily()
    return build_golden_lower_neighborhood_stability_certificate(
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


def build_golden_two_sided_neighborhood_tail_bridge_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_two_sided_neighborhood_tail_bridge_certificate(
        base_K_values=base_K_values, family=family, rho=rho, **kwargs
    ).to_dict()


def build_rational_irrational_convergence_report(
    ladder: dict[str, Any],
    *,
    refined: dict[str, Any] | None = None,
    asymptotic_audit: dict[str, Any] | None = None,
    rho_target: float | None = None,
    family_label: str | None = None,
    q_thresholds: Sequence[int] | None = None,
    min_members: int = 3,
    model_power: float = 2.0,
    center_drift_tol: float = 5.0e-4,
) -> dict[str, Any]:
    return build_rational_irrational_convergence_certificate(
        ladder,
        refined=refined,
        asymptotic_audit=asymptotic_audit,
        rho_target=rho_target,
        family_label=family_label,
        q_thresholds=q_thresholds,
        min_members=min_members,
        model_power=model_power,
        center_drift_tol=center_drift_tol,
    ).to_dict()



def build_branch_certified_irrational_limit_report(
    ladder: dict[str, Any],
    *,
    refined: dict[str, Any] | None = None,
    asymptotic_audit: dict[str, Any] | None = None,
    rho_target: float | None = None,
    family_label: str | None = None,
    q_thresholds: Sequence[int] | None = None,
    min_members: int = 3,
) -> dict[str, Any]:
    return build_branch_certified_irrational_limit_certificate(
        ladder,
        refined=refined,
        asymptotic_audit=asymptotic_audit,
        rho_target=rho_target,
        family_label=family_label,
        q_thresholds=q_thresholds,
        min_members=min_members,
    ).to_dict()


def build_convergent_family_limit_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    nesting_tolerance: float = 5.0e-5,
    contraction_cap: float = 0.9,
    min_overlap_fraction: float = 0.5,
) -> dict[str, Any]:
    return build_convergent_family_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        nesting_tolerance=nesting_tolerance,
        contraction_cap=contraction_cap,
        min_overlap_fraction=min_overlap_fraction,
    ).to_dict()



def build_transport_certified_limit_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    min_overlap_fraction: float = 0.5,
) -> dict[str, Any]:
    return build_transport_certified_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        min_overlap_fraction=min_overlap_fraction,
    ).to_dict()


def build_pairwise_transport_chain_limit_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    min_overlap_fraction: float = 0.5,
    compatibility_multiplier: float = 1.1,
) -> dict[str, Any]:
    return build_pairwise_transport_chain_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        min_overlap_fraction=min_overlap_fraction,
        compatibility_multiplier=compatibility_multiplier,
    ).to_dict()


def build_triple_transport_cocycle_limit_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    min_overlap_fraction: float = 0.5,
    compatibility_multiplier: float = 1.1,
    cocycle_multiplier: float = 1.05,
) -> dict[str, Any]:
    return build_triple_transport_cocycle_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        min_overlap_fraction=min_overlap_fraction,
        compatibility_multiplier=compatibility_multiplier,
        cocycle_multiplier=cocycle_multiplier,
    ).to_dict()


def build_global_transport_potential_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    anchor_multiplier: float = 1.05,
) -> dict[str, Any]:
    return build_global_transport_potential_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
    ).to_dict()


def build_tail_cauchy_potential_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    anchor_multiplier: float = 1.05,
    fallback_share_cap: float = 0.35,
) -> dict[str, Any]:
    return build_tail_cauchy_potential_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
    ).to_dict()


def build_certified_tail_modulus_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    anchor_multiplier: float = 1.05,
    fallback_share_cap: float = 0.35,
    total_radius_growth_slack: float = 1.25,
) -> dict[str, Any]:
    return build_certified_tail_modulus_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
        total_radius_growth_slack=total_radius_growth_slack,
    ).to_dict()

def build_rate_aware_tail_modulus_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    anchor_multiplier: float = 1.05,
    fallback_share_cap: float = 0.35,
    total_radius_growth_slack: float = 1.25,
    rate_exponent_safety_factor: float = 0.9,
    min_rate_exponent: float = 0.2,
    max_rate_exponent: float = 4.0,
) -> dict[str, Any]:
    return build_rate_aware_tail_modulus_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
        total_radius_growth_slack=total_radius_growth_slack,
        rate_exponent_safety_factor=rate_exponent_safety_factor,
        min_rate_exponent=min_rate_exponent,
        max_rate_exponent=max_rate_exponent,
    ).to_dict()



def build_golden_recurrence_rate_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    anchor_multiplier: float = 1.05,
    fallback_share_cap: float = 0.35,
    total_radius_growth_slack: float = 1.25,
    rate_exponent_safety_factor: float = 0.9,
    min_rate_exponent: float = 0.2,
    max_rate_exponent: float = 4.0,
    min_step_exponent: float = 0.05,
) -> dict[str, Any]:
    return build_golden_recurrence_rate_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
        total_radius_growth_slack=total_radius_growth_slack,
        rate_exponent_safety_factor=rate_exponent_safety_factor,
        min_rate_exponent=min_rate_exponent,
        max_rate_exponent=max_rate_exponent,
        min_step_exponent=min_step_exponent,
    ).to_dict()




def build_transport_slope_weighted_golden_rate_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    anchor_multiplier: float = 1.05,
    fallback_share_cap: float = 0.35,
    total_radius_growth_slack: float = 1.25,
    rate_exponent_safety_factor: float = 0.9,
    min_rate_exponent: float = 0.2,
    max_rate_exponent: float = 4.0,
    min_step_exponent: float = 0.05,
    transport_strength_boost: float = 0.25,
) -> dict[str, Any]:
    return build_transport_slope_weighted_golden_rate_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
        total_radius_growth_slack=total_radius_growth_slack,
        rate_exponent_safety_factor=rate_exponent_safety_factor,
        min_rate_exponent=min_rate_exponent,
        max_rate_exponent=max_rate_exponent,
        min_step_exponent=min_step_exponent,
        transport_strength_boost=transport_strength_boost,
    ).to_dict()



def build_edge_class_weighted_golden_rate_report(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    anchor_multiplier: float = 1.05,
    fallback_share_cap: float = 0.35,
    total_radius_growth_slack: float = 1.25,
    rate_exponent_safety_factor: float = 0.9,
    min_rate_exponent: float = 0.2,
    max_rate_exponent: float = 4.0,
    min_step_exponent: float = 0.05,
    transport_strength_boost: float = 0.25,
    derivative_share_weight: float = 1.0,
    tangent_share_weight: float = 0.8,
    fallback_share_weight: float = 0.3,
) -> dict[str, Any]:
    return build_edge_class_weighted_golden_rate_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
        total_radius_growth_slack=total_radius_growth_slack,
        rate_exponent_safety_factor=rate_exponent_safety_factor,
        min_rate_exponent=min_rate_exponent,
        max_rate_exponent=max_rate_exponent,
        min_step_exponent=min_step_exponent,
        transport_strength_boost=transport_strength_boost,
        derivative_share_weight=derivative_share_weight,
        tangent_share_weight=tangent_share_weight,
        fallback_share_weight=fallback_share_weight,
    ).to_dict()




def build_theorem_v_explicit_error_report(
    ladder: dict[str, Any],
    *,
    refined: dict[str, Any] | None = None,
    asymptotic_audit: dict[str, Any] | None = None,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_members: int = 3,
    nesting_tolerance: float = 5.0e-5,
    cauchy_multiplier: float = 1.25,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    min_overlap_fraction: float = 0.5,
    compatibility_multiplier: float = 1.1,
    cocycle_multiplier: float = 1.05,
    anchor_multiplier: float = 1.05,
    fallback_share_cap: float = 0.35,
    total_radius_growth_slack: float = 1.25,
    rate_exponent_safety_factor: float = 0.9,
    min_rate_exponent: float = 0.2,
    max_rate_exponent: float = 4.0,
    min_step_exponent: float = 0.05,
    transport_strength_boost: float = 0.25,
    derivative_share_weight: float = 1.0,
    tangent_share_weight: float = 0.8,
    fallback_share_weight: float = 0.3,
) -> dict[str, Any]:
    return build_theorem_v_explicit_error_certificate(
        ladder,
        refined=refined,
        asymptotic_audit=asymptotic_audit,
        rho_target=rho_target,
        family_label=family_label,
        min_members=min_members,
        nesting_tolerance=nesting_tolerance,
        cauchy_multiplier=cauchy_multiplier,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        min_overlap_fraction=min_overlap_fraction,
        compatibility_multiplier=compatibility_multiplier,
        cocycle_multiplier=cocycle_multiplier,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
        total_radius_growth_slack=total_radius_growth_slack,
        rate_exponent_safety_factor=rate_exponent_safety_factor,
        min_rate_exponent=min_rate_exponent,
        max_rate_exponent=max_rate_exponent,
        min_step_exponent=min_step_exponent,
        transport_strength_boost=transport_strength_boost,
        derivative_share_weight=derivative_share_weight,
        tangent_share_weight=tangent_share_weight,
        fallback_share_weight=fallback_share_weight,
    ).to_dict()


def build_nested_subladder_limit_report(
    ladder: dict[str, Any],
    *,
    refined: dict[str, Any] | None = None,
    asymptotic_audit: dict[str, Any] | None = None,
    rho_target: float | None = None,
    family_label: str | None = None,
    q_thresholds: Sequence[int] | None = None,
    min_members: int = 3,
    nesting_tolerance: float = 5.0e-5,
    cauchy_multiplier: float = 1.25,
) -> dict[str, Any]:
    return build_nested_subladder_limit_certificate(
        ladder,
        refined=refined,
        asymptotic_audit=asymptotic_audit,
        rho_target=rho_target,
        family_label=family_label,
        q_thresholds=q_thresholds,
        min_members=min_members,
        nesting_tolerance=nesting_tolerance,
        cauchy_multiplier=cauchy_multiplier,
    ).to_dict()

def build_golden_rational_to_irrational_convergence_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_rational_to_irrational_convergence_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()



def build_golden_theorem_v_transport_lift_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_v_transport_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()



def build_golden_theorem_v_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_v_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_theorem_v_compressed_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_v_compressed_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    )


def build_golden_theorem_v_batched_front_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_rational_to_irrational_convergence_certificate_batched(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    )


def build_golden_theorem_v_batched_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_v_certificate_batched(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    )


def build_golden_threshold_identification_lift_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_threshold_identification_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()



def build_golden_theorem_ii_to_v_identification_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_ii_to_v_identification_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_threshold_identification_discharge_lift_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_threshold_identification_discharge_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()



def build_golden_theorem_ii_to_v_identification_discharge_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_ii_to_v_identification_discharge_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_threshold_identification_transport_discharge_lift_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_threshold_identification_transport_discharge_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_theorem_ii_to_v_identification_transport_discharge_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_ii_to_v_identification_transport_discharge_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_threshold_identification_localized_implication_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_threshold_identification_localized_implication_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_theorem_ii_to_v_identification_theorem_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_ii_to_v_identification_theorem_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()



def build_transport_locked_threshold_uniqueness_report(
    theorem_v_certificate: Mapping[str, Any],
    **kwargs,
) -> dict[str, Any]:
    return build_transport_locked_threshold_uniqueness_certificate(
        theorem_v_certificate=theorem_v_certificate,
        **kwargs,
    ).to_dict()



def build_renormalization_operator_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str = 'harmonic_family',
    stable_damping: float = 0.6,
    phase_damping: float = 0.5,
    mode_penalty_power: float = 1.0,
    anchor_target_amplitude: float = 1.0,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_renormalization_operator_certificate(
        family,
        family_label=family_label,
        stable_damping=stable_damping,
        phase_damping=phase_damping,
        mode_penalty_power=mode_penalty_power,
        anchor_target_amplitude=anchor_target_amplitude,
    ).to_dict()


def build_renormalization_fixed_point_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str = 'harmonic_family',
    iterations: int = 6,
    stable_damping: float = 0.6,
    phase_damping: float = 0.5,
    mode_penalty_power: float = 1.0,
    anchor_target_amplitude: float = 1.0,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_renormalization_fixed_point_certificate(
        family,
        family_label=family_label,
        iterations=iterations,
        stable_damping=stable_damping,
        phase_damping=phase_damping,
        mode_penalty_power=mode_penalty_power,
        anchor_target_amplitude=anchor_target_amplitude,
    ).to_dict()


def build_linearization_bounds_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str = 'harmonic_family',
    perturbation_scale: float = 1.0e-3,
    stable_damping: float = 0.6,
    phase_damping: float = 0.5,
    mode_penalty_power: float = 1.0,
    anchor_target_amplitude: float = 1.0,
    inflation: float = 0.02,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_linearization_bounds_certificate(
        family,
        family_label=family_label,
        perturbation_scale=perturbation_scale,
        stable_damping=stable_damping,
        phase_damping=phase_damping,
        mode_penalty_power=mode_penalty_power,
        anchor_target_amplitude=anchor_target_amplitude,
        inflation=inflation,
    ).to_dict()



def build_fixed_point_enclosure_report(
    family: HarmonicFamily | None = None,
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
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_fixed_point_enclosure_certificate(
        family,
        family_label=family_label,
        iterations=iterations,
        stable_damping=stable_damping,
        phase_damping=phase_damping,
        mode_penalty_power=mode_penalty_power,
        anchor_target_amplitude=anchor_target_amplitude,
        perturbation_scale=perturbation_scale,
        inflation=inflation,
        radius_safety_factor=radius_safety_factor,
    ).to_dict()


def build_spectral_splitting_report(
    family: HarmonicFamily | None = None,
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
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_spectral_splitting_certificate(
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
    ).to_dict()



def build_stable_manifold_chart_report(
    family: HarmonicFamily | None = None,
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
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_stable_manifold_chart_certificate(
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
    ).to_dict()

def build_family_transversality_report(
    family: HarmonicFamily,
    *,
    family_label: str = "harmonic_family",
    **kwargs: Any,
) -> dict[str, Any]:
    return build_family_transversality_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_critical_surface_bridge_report(
    family: HarmonicFamily,
    *,
    family_label: str = "harmonic_family",
    **kwargs: Any,
) -> dict[str, Any]:
    return build_critical_surface_bridge_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_transversality_window_report(
    family: HarmonicFamily,
    *,
    family_label: str = "harmonic_family",
    **kwargs: Any,
) -> dict[str, Any]:
    return build_transversality_window_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_validated_critical_surface_bridge_report(
    family: HarmonicFamily,
    *,
    family_label: str = "harmonic_family",
    **kwargs: Any,
) -> dict[str, Any]:
    return build_validated_critical_surface_bridge_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_chart_threshold_linkage_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_chart_threshold_linkage_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_golden_chart_threshold_bridge_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_golden_chart_threshold_bridge_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_threshold_compatibility_window_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_threshold_compatibility_window_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_validated_threshold_compatibility_bridge_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_validated_threshold_compatibility_bridge_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_eta_threshold_comparison_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_eta_threshold_comparison_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_proto_envelope_eta_bridge_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_proto_envelope_eta_bridge_certificate(
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_near_top_eta_challenger_comparison_report(
    challenger_specs: Sequence[EtaChallengerSpec] | None = None,
    *,
    family: HarmonicFamily | None = None,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_near_top_eta_challenger_comparison_certificate(
        challenger_specs,
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_campaign_driven_eta_challenger_comparison_report(
    multi_class_campaign_report: dict[str, Any],
    *,
    golden_eta_threshold_certificate: dict[str, Any],
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_campaign_driven_eta_challenger_comparison_certificate(
        multi_class_campaign_report,
        golden_eta_threshold_certificate=golden_eta_threshold_certificate,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_golden_theorem_vi_envelope_lift_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()



def build_golden_theorem_vi_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_golden_theorem_vi_certificate(
        base_K_values=base_K_values,
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_golden_theorem_vi_envelope_discharge_lift_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_golden_theorem_vi_envelope_discharge_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()



def build_golden_theorem_vi_discharge_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_golden_theorem_vi_discharge_certificate(
        base_K_values=base_K_values,
        family=family,
        family_label=family_label,
        **kwargs,
    ).to_dict()


def build_golden_theorem_vii_exhaustion_lift_report(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_vii_exhaustion_lift_certificate(
        base_K_values=base_K_values,
        challenger_specs=challenger_specs,
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_theorem_vii_report(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_vii_certificate(
        base_K_values=base_K_values,
        challenger_specs=challenger_specs,
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_theorem_vii_global_completeness_report(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    theorem_vii = build_golden_theorem_vii_certificate(
        base_K_values=base_K_values,
        challenger_specs=challenger_specs,
        family=family,
        **kwargs,
    ).to_dict()
    return build_golden_theorem_vii_global_completeness_certificate(theorem_vii).to_dict()


def build_golden_theorem_vii_exhaustion_discharge_lift_report(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_vii_exhaustion_discharge_lift_certificate(
        base_K_values=base_K_values,
        challenger_specs=challenger_specs,
        family=family,
        **kwargs,
    ).to_dict()



def build_golden_theorem_vii_discharge_report(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_vii_discharge_certificate(
        base_K_values=base_K_values,
        challenger_specs=challenger_specs,
        family=family,
        **kwargs,
    ).to_dict()






def _count_report_items(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (str, bytes)):
        return 1 if value else 0
    try:
        return len(value)  # type: ignore[arg-type]
    except Exception:
        return 1



def _normalize_report_item_label(item: Any) -> str | None:
    if item is None:
        return None
    if isinstance(item, bytes):
        try:
            label = item.decode()
        except Exception:
            label = repr(item)
        return label or None
    if isinstance(item, str):
        return item or None
    if isinstance(item, Mapping):
        for key in ('name', 'label', 'hypothesis', 'assumption', 'id', 'title', 'item', 'value'):
            value = item.get(key)
            if value:
                return str(value)
        return repr(dict(item))
    return str(item)



def _normalize_report_item_labels(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, Mapping)):
        label = _normalize_report_item_label(value)
        return [] if label is None else [label]
    try:
        iterator = iter(value)
    except Exception:
        label = _normalize_report_item_label(value)
        return [] if label is None else [label]
    labels: list[str] = []
    for item in iterator:
        label = _normalize_report_item_label(item)
        if label:
            labels.append(label)
    return labels



def _summarize_theorem_status_entry(name: str, report: Mapping[str, Any]) -> dict[str, Any]:
    theorem_status = report.get('theorem_status')
    statement_mode = report.get('statement_mode')
    open_hypotheses = _normalize_report_item_labels(report.get('open_hypotheses'))
    active_assumptions = _normalize_report_item_labels(report.get('active_assumptions'))
    open_hypothesis_count = len(open_hypotheses)
    active_assumption_count = len(active_assumptions)
    residual_burden = dict(report.get('residual_burden_summary', {}))
    statement_mode_diagnostics = dict(report.get('statement_mode_diagnostics', {}))
    strict_top_gap = dict(report.get('strict_golden_top_gap_certificate', {}))
    return {
        'name': name,
        'theorem_status': None if theorem_status is None else str(theorem_status),
        'statement_mode': None if statement_mode is None else str(statement_mode),
        'theorem_statement_mode': None if statement_mode_diagnostics.get('theorem_statement_mode') is None else str(statement_mode_diagnostics.get('theorem_statement_mode')),
        'theorem_mode_certified': bool(statement_mode_diagnostics.get('theorem_mode_certified', False)),
        'statement_mode_lock_status': None if statement_mode_diagnostics.get('mode_lock_status') is None else str(statement_mode_diagnostics.get('mode_lock_status')),
        'open_hypothesis_count': open_hypothesis_count,
        'active_assumption_count': active_assumption_count,
        'open_hypotheses': open_hypotheses,
        'active_assumptions': active_assumptions,
        'residual_burden_status': None if residual_burden.get('status') is None else str(residual_burden.get('status')),
        'global_ceiling_status': None if residual_burden.get('global_ceiling_status') is None else str(residual_burden.get('global_ceiling_status')),
        'global_ceiling_certified': bool(residual_burden.get('global_ceiling_certified', False)),
        'global_top_gap_status': None if strict_top_gap.get('global_strict_top_gap_status') is None else str(strict_top_gap.get('global_strict_top_gap_status')),
    }



def _theorem_status_is_resolved(theorem_status: Any) -> bool:
    if theorem_status is None:
        return False
    status = str(theorem_status).lower()
    return 'strong' in status or 'front-complete' in status or 'discharged' in status



def _select_structural_bottleneck(theorem_status_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    best_score: tuple[int, int, int] | None = None
    for row in theorem_status_rows:
        theorem_status = row.get('theorem_status')
        unresolved_score = 0 if _theorem_status_is_resolved(theorem_status) else 1
        open_count = int(row.get('open_hypothesis_count') or 0)
        active_count = int(row.get('active_assumption_count') or 0)
        open_hypotheses = _normalize_report_item_labels(row.get('open_hypotheses'))
        active_assumptions = _normalize_report_item_labels(row.get('active_assumptions'))
        score = (unresolved_score, open_count + active_count, open_count)
        if score == (0, 0, 0):
            continue
        if best is None or score > best_score:
            best = {
                'name': None if row.get('name') is None else str(row['name']),
                'theorem_status': None if theorem_status is None else str(theorem_status),
                'statement_mode': None if row.get('statement_mode') is None else str(row['statement_mode']),
                'statement_mode_lock_status': None if row.get('statement_mode_lock_status') is None else str(row.get('statement_mode_lock_status')),
                'open_hypothesis_count': open_count,
                'active_assumption_count': active_count,
                'open_hypotheses': open_hypotheses,
                'active_assumptions': active_assumptions,
                'residual_burden_status': None if row.get('residual_burden_status') is None else str(row.get('residual_burden_status')),
                'resolved': _theorem_status_is_resolved(theorem_status),
            }
            best_score = score
    if best is None:
        best = {
            'name': None,
            'theorem_status': None,
            'statement_mode': None,
            'statement_mode_lock_status': None,
            'open_hypothesis_count': 0,
            'active_assumption_count': 0,
            'open_hypotheses': [],
            'active_assumptions': [],
            'residual_burden_status': None,
            'resolved': True,
        }
    return best



def _build_theorem_program_bottleneck_summary(
    theorem_status_rows: Sequence[Mapping[str, Any]],
    current_reduction_geometry_summary: Mapping[str, Any],
) -> dict[str, Any]:
    structural = _select_structural_bottleneck(theorem_status_rows)
    local_margin_raw = current_reduction_geometry_summary.get('minimum_certified_margin')
    local_margin = None if local_margin_raw is None else float(local_margin_raw)
    geometry_available = bool(current_reduction_geometry_summary.get('available'))
    geometry_status = None if current_reduction_geometry_summary.get('status') is None else str(current_reduction_geometry_summary['status'])
    geometry_strong = bool(geometry_status) and 'strong' in geometry_status.lower()
    geometry_blocked = (not geometry_available) or (not geometry_strong) or (local_margin is not None and local_margin <= 0.0)

    structural_has_bottleneck = (
        structural.get('name') is not None
        and (
            not bool(structural.get('resolved'))
            or int(structural.get('open_hypothesis_count') or 0) > 0
            or int(structural.get('active_assumption_count') or 0) > 0
        )
    )
    structural_is_only_viii_shell = (
        structural.get('name') == 'Theorem VIII'
        and int(structural.get('open_hypothesis_count') or 0) == 0
        and int(structural.get('active_assumption_count') or 0) == 0
    )
    if geometry_blocked and structural_is_only_viii_shell:
        structural_has_bottleneck = False

    if geometry_blocked and structural_has_bottleneck:
        kind = 'mixed'
        name = f"{structural['name']} + current reduction geometry"
        reason = 'Both the theorem-status frontier and the current local reduction geometry remain active blockers.'
    elif geometry_blocked:
        kind = 'local-geometric'
        name = 'Current reduction geometry'
        reason = 'The current local reduction geometry is not yet strong enough to support the final reduction.'
    elif structural_has_bottleneck:
        kind = 'theorem-structural'
        name = structural['name']
        reason = 'The main blocker remains an unresolved theorem-stage burden rather than the current local reduction geometry.'
    else:
        kind = 'none'
        name = None
        reason = 'No active bottleneck was detected in the theorem-status table or the current reduction geometry summary.'

    return {
        'kind': kind,
        'name': name,
        'reason': reason,
        'smallest_certified_local_margin': local_margin,
        'current_reduction_geometry_available': geometry_available,
        'current_reduction_geometry_status': geometry_status,
        'structural_frontier_name': structural.get('name'),
        'structural_frontier_theorem_status': structural.get('theorem_status'),
        'structural_frontier_statement_mode': structural.get('statement_mode'),
        'structural_frontier_open_hypothesis_count': int(structural.get('open_hypothesis_count') or 0),
        'structural_frontier_active_assumption_count': int(structural.get('active_assumption_count') or 0),
        'structural_frontier_open_hypotheses': list(structural.get('open_hypotheses') or []),
        'structural_frontier_active_assumptions': list(structural.get('active_assumptions') or []),
        'structural_frontier_residual_burden_status': None if structural.get('residual_burden_status') is None else str(structural.get('residual_burden_status')),
        'structural_frontier_resolved': bool(structural.get('resolved')),
    }


_THEOREM_PROGRAM_NEXT_MOVE_MAP: dict[str, tuple[str, str]] = {
    'Theorems I-II': (
        'Workstream A discharge',
        'Replace the remaining proxy renormalization / stable-manifold scaffolding by validated Workstream A theorem objects and feed that discharge back into the II→V seam.',
    ),
    'Theorem IV': (
        'Analytic incompatibility promotion',
        'Promote the current nonexistence front into the final analytic incompatibility theorem so the obstruction corridor closes as a genuine irrational nonexistence theorem.',
    ),
    'Theorem V': (
        'Validated transport closure',
        'Collapse the transport corridor into the final validated continuation/transport theorem with the explicit error law needed downstream.',
    ),
    'Identification seam': (
        'Threshold-identification discharge',
        'Discharge the remaining II→V linkage burden so the renormalization-side critical parameter and the threshold-side irrational branch are genuinely identified.',
    ),
    'Theorem VI': (
        'Envelope / top-gap theorem',
        'Prove the strict golden envelope / top-gap theorem in the current statement mode so the arithmetic comparison side becomes theorem-grade.',
    ),
    'Theorem VII': (
        'Near-top challenger exhaustion',
        'Close the near-top challenger exhaustion burden so the final reduction no longer depends on screened-panel completeness assumptions.',
    ),
    'Theorem VIII': (
        'Final reduction discharge',
        'Convert the remaining final reduction shell into a fully discharged theorem by eliminating its last inherited burdens.',
    ),
}



def _frontier_contains_any(labels: Sequence[str], *needles: str) -> bool:
    lowered = [label.lower() for label in labels]
    for needle in needles:
        needle_lower = needle.lower()
        for label in lowered:
            if needle_lower in label:
                return True
    return False



def _build_frontier_specific_next_move(
    structural_name: str | None,
    *,
    statement_mode: str | None,
    open_hypotheses: Sequence[str],
    active_assumptions: Sequence[str],
    residual_burden_status: str | None = None,
) -> tuple[str | None, str, str, str]:
    all_labels = list(open_hypotheses) + list(active_assumptions)
    generic_label, generic_action = _THEOREM_PROGRAM_NEXT_MOVE_MAP.get(
        structural_name or '',
        (
            'Structural discharge',
            'Discharge the current structural frontier theorem so the proof graph advances at its main unresolved theorem interface.',
        ),
    )
    target = structural_name
    action = generic_action
    rationale = f'The current decisive blocker is structural: {generic_label.lower()} remains more urgent than additional local-geometry tightening.'

    if structural_name == 'Theorem VI':
        if _frontier_contains_any(open_hypotheses, 'strict_golden_top_gap'):
            target = 'Theorem VI strict golden top gap'
            action = 'Prove the strict golden top-gap inequality in the current statement mode so the envelope theorem gains the decisive golden-over-challenger separation it still lacks.'
            rationale = 'The Theorem VI frontier is currently concentrated in the explicit open hypothesis strict_golden_top_gap, so closing that gap dominates more generic envelope-side refinement.'
        elif _frontier_contains_any(all_labels, 'statement_mode', 'settle_statement_mode') or (statement_mode is None) or ('unresolved' in statement_mode.lower()):
            target = 'Theorem VI statement mode'
            action = 'Settle the final Theorem VI statement mode by deciding whether the envelope theorem closes in one-variable form or requires the corrected two-variable formulation, then discharge the matching envelope law.'
            rationale = 'The Theorem VI frontier still depends on unresolved statement-mode structure, so clarifying the correct theorem statement is more urgent than pushing a generic envelope argument.'
        elif _frontier_contains_any(all_labels, 'eta_envelope', 'envelope_law'):
            mode = 'current statement mode' if statement_mode is None else f'{statement_mode} statement mode'
            target = 'Theorem VI envelope law'
            action = f'Prove the missing envelope law in the {mode} so the arithmetic comparison side becomes theorem-grade before asking for the final strict golden top gap.'
            rationale = 'The Theorem VI burden is presently carried by the envelope-law side rather than by challenger exhaustion or final reduction bookkeeping.'
    elif structural_name == 'Identification seam':
        if residual_burden_status == 'transport-locked-local-uniqueness-frontier' or _frontier_contains_any(active_assumptions, 'unique_true_threshold_branch_inside_transport_locked_window'):
            target = 'Identification seam transport-locked uniqueness'
            action = 'Discharge transport-locked threshold uniqueness so the II→V identification seam no longer depends on a local uniqueness hinge inside the locked window.'
            rationale = 'The identification frontier is still pinned to the transport-locked uniqueness assumption, so resolving that hinge is the most leverage-rich seam move.'
        elif residual_burden_status in {'critical-surface-threshold-promotion-theorem-frontier', 'critical-surface-threshold-promotion-frontier'}:
            target = 'Identification seam critical-surface/threshold promotion theorem'
            action = 'Promote the Workstream-fed critical-surface discharge package into the actual theorem-grade statement identifying the same threshold branch recovered from the lower/upper threshold corridor, and feed that promoted object directly through the seam.'
            rationale = 'The seam is no longer mainly blocked by local uniqueness or generic Workstream bookkeeping; it is now blocked by the actual critical-surface-to-threshold promotion theorem.'
        elif residual_burden_status in {'critical-surface-threshold-promotion-theorem-available', 'critical-surface-threshold-promotion-theorem-conditional-strong', 'critical-surface-threshold-promotion-theorem-discharged'}:
            target = 'Identification seam localized compatibility implication'
            action = 'Exploit the promoted Workstream theorem object to discharge the remaining localized compatibility-to-true-threshold implication, since the upstream structural promotion theorem is now already available.'
            rationale = 'The upstream critical-surface-to-threshold theorem object is already available, so the remaining seam burden is downstream/local rather than structural.'
        elif residual_burden_status in {'localized-compatibility-implication-local-frontier', 'localized-compatibility-implication-upstream-frontier'}:
            target = 'Identification seam localized compatibility implication'
            action = 'Promote the transport-locked threshold-branch witness into the final localized compatibility implication theorem, so the II→V seam is discharged rather than merely transport-ready.'
            rationale = 'The seam is now beyond transport-locking and Workstream promotion; the remaining burden is the final local implication from the locked branch witness to the true threshold object.'
        elif residual_burden_status in {'critical-surface-threshold-identification-frontier', 'mixed-local-and-upstream-identification-burden'} or _frontier_contains_any(open_hypotheses, 'critical_surface_identifies_threshold', 'identifies_threshold'):
            target = 'Identification seam critical-surface/threshold identification'
            action = 'Prove that the renormalization-side critical surface identifies the same threshold branch recovered from the lower/upper threshold corridor.'
            rationale = 'The transport-locked local hinge is now packaged sharply enough that the remaining identification burden sits in the actual critical-surface-to-threshold identification theorem.'
    elif structural_name == 'Theorem VII':
        if _frontier_contains_any(open_hypotheses, 'all_near_top_challengers_dominated', 'near_top_challengers_dominated') or residual_burden_status == 'near-top-frontier-still-open':
            target = 'Theorem VII near-top challenger dominance'
            action = 'Prove that every currently dangerous near-top challenger class is dominated by the golden class, turning the screened near-top panel into a theorem-grade dominance statement.'
            rationale = 'The Theorem VII frontier is still concentrated in the screened near-top dominance question rather than in the omitted/global challenger tail.'
        elif residual_burden_status == 'global-exhaustion-support-frontier':
            target = 'Theorem VII global ranking / pruning support'
            action = 'Promote the remaining global ranking, pruning, deferred-class domination, and termination-exclusion support objects into theorem-grade ingredients so the global completeness burden is isolated cleanly.'
            rationale = 'The near-top screened panel is already isolated, but the global challenger-exhaustion side still lacks theorem-grade support objects for ranking and pruning.'
        elif residual_burden_status in {'global-screened-panel-completeness-frontier', 'screened-panel-global-completeness-frontier'} or _frontier_contains_any(active_assumptions, 'finite_screened_panel_is_globally_complete', 'globally_complete'):
            target = 'Theorem VII global screened-panel completeness'
            action = 'Upgrade the global screened-panel completeness assumption into a theorem-grade exhaustion argument so the final reduction no longer depends on hoped-for global panel completeness.'
            rationale = 'The currently screened near-top panel is already dominated, so the remaining Theorem VII burden now sits in showing that the screened panel is genuinely globally complete.'
        elif residual_burden_status == 'omitted-class-global-control-frontier':
            target = 'Theorem VII omitted-class global control'
            action = 'Prove the omitted-class global-control theorem so non-golden irrationals outside the screened panel can no longer threaten the golden lower bound.'
            rationale = 'The screened panel itself is effectively complete; the remaining Theorem VII burden is the global control of omitted non-golden classes outside that panel.'
        elif residual_burden_status == 'global-completeness-and-omitted-control-frontier':
            target = 'Theorem VII global completeness + omitted-class control'
            action = 'Split the remaining global Theorem VII burden into a screened-panel completeness theorem and an omitted-class control theorem, then discharge both pieces so the non-golden world is exhausted globally.'
            rationale = 'The near-top panel is already dominated, but both sides of the remaining global completeness problem are still active.'
    elif structural_name == 'Theorems I-II':
        if residual_burden_status in {'validated-universality-class-theorem-frontier', 'validated-universality-class-theorem-promotion-frontier', 'validated-universality-class-theorem-local-prerequisite-frontier'}:
            target = 'Theorems I-II validated universality-class theorem'
            action = 'Promote the local admissibility / normalization / chart-compatibility discharge object into the theorem-grade Banach-manifold universality-class theorem, so the Workstream-A shell no longer depends on the ambient-class assumption.'
            rationale = 'The remaining Workstream-A burden is now concentrated at the ambient Banach-manifold class layer, so absorbing that assumption is the sharpest structural move before returning to downstream seam work.'
        elif residual_burden_status in {'validated-renormalization-package-frontier', 'validated-renormalization-package-promotion-frontier', 'validated-renormalization-package-local-prerequisite-frontier', 'validated-renormalization-package-promotion-isolation-frontier'}:
            target = 'Theorems I-II validated renormalization package theorem'
            action = 'Promote the new operator/fixed-point/enclosure/splitting/stable-manifold discharge object into the theorem-grade validated renormalization package, so the Workstream-A core no longer depends on the combined proxy package assumption.'
            rationale = 'The Workstream-A bottleneck is now localized at the theorem-facing validated renormalization package rather than being spread diffusely across operator and fixed-point scaffolding.'
        elif residual_burden_status in {'validated-critical-surface-theorem-promotion-frontier', 'validated-critical-surface-theorem-local-prerequisite-frontier'}:
            target = 'Theorems I-II validated critical-surface theorem'
            action = 'Promote the new stable-manifold / critical-surface / localized-transversality discharge object into the theorem-facing validated critical-surface theorem, so the Workstream-specific critical-surface assumptions are absorbed before the final critical-surface-to-threshold promotion step.'
            rationale = 'The renormalization package is already localized well enough that the next structural gain is to absorb the Workstream-specific critical-surface assumptions into their own theorem object rather than leaving them as raw assumptions under the threshold-identification shell.'
        elif residual_burden_status in {'critical-surface-threshold-promotion-theorem-frontier', 'critical-surface-threshold-promotion-frontier'}:
            target = 'Theorems I-II critical-surface/threshold promotion theorem'
            action = 'Turn the new Workstream-A critical-surface discharge certificate into the theorem-grade promotion theorem identifying the true threshold parameter, and feed that promoted object directly into the II→V seam.'
            rationale = 'The Workstream-A frontier is now localized more sharply than before: the local prerequisites are packaged, and the next structural gain is to promote that discharge object into the actual critical-surface-to-threshold theorem.'
        elif residual_burden_status in {'critical-surface-threshold-promotion-theorem-conditional-strong', 'critical-surface-threshold-promotion-theorem-discharged'}:
            target = 'Theorem VII global screened-panel completeness'
            action = 'With the Workstream-A promotion theorem object now available, shift the main effort to theorem-grade global challenger exhaustion so the final reduction no longer depends on screened-panel completeness assumptions.'
            rationale = 'The immediate Workstream-A structural promotion step is now conditionally available, so the highest-leverage remaining burden shifts to the global challenger-exhaustion side.'
        elif residual_burden_status == 'critical-surface-threshold-identification-frontier':
            target = 'Theorems I-II critical surface / threshold identification'
            action = 'Promote the locally sharp stable-manifold / critical-surface / transversality-window scaffold into the theorem-grade critical-surface-to-threshold identification theorem and feed that discharge directly into the II→V seam.'
            rationale = 'The local Workstream-A geometry is already sharp enough that the remaining structural burden now sits in the theorem-grade critical-surface / threshold identification step rather than in generic operator bookkeeping.'
        elif _frontier_contains_any(open_hypotheses, 'validated_operator', 'operator'):
            target = 'Theorems I-II validated renormalization operator'
            action = 'Validate the true renormalization operator on the final Banach-manifold class so the Workstream A scaffold starts from theorem objects rather than proxy coordinates.'
            rationale = 'The Workstream A frontier is still visibly attached to operator validation, so replacing the proxy renormalization operator is the sharpest structural move.'
        elif _frontier_contains_any(open_hypotheses, 'fixed_point'):
            target = 'Theorems I-II golden fixed point'
            action = 'Validate the golden renormalization fixed point and its enclosure in the final theorem norm structure so the downstream splitting and stable-manifold claims rest on a theorem-grade anchor.'
            rationale = 'The Workstream A burden is currently concentrated in the fixed-point package rather than merely in downstream shell bookkeeping.'
        elif _frontier_contains_any(active_assumptions, 'stable_manifold'):
            target = 'Theorems I-II stable manifold / critical surface'
            action = 'Promote the remaining stable-manifold / critical-surface scaffolding into a validated theorem object and feed that discharge directly back into the II→V seam.'
            rationale = 'The Workstream A frontier is presently dominated by the stable-manifold / critical-surface side of the renormalization package.'
    elif structural_name == 'Theorem V':
        if _frontier_contains_any(active_assumptions, 'validated_transport_theorem', 'continuation', 'transport_theorem'):
            target = 'Theorem V validated continuation/transport theorem'
            action = 'Collapse the current transport corridor into the final validated continuation/transport theorem with the explicit error law required by the II→V identification seam.'
            rationale = 'The Theorem V burden is still carried by the final continuation/transport theorem rather than by additional bridge packaging.'
    elif structural_name == 'Theorem VIII':
        if all_labels:
            target = 'Theorem VIII inherited burden discharge'
            action = 'Discharge the last inherited VIII-side burden explicitly so the final reduction theorem stops depending on residual upstream assumptions.'
            rationale = 'The final reduction remains structurally blocked by a specific inherited burden rather than by missing local geometry alone.'

    return target, action, rationale, generic_label



def _build_theorem_program_recommended_next_move_summary(
    bottleneck_summary: Mapping[str, Any],
) -> dict[str, Any]:
    kind = None if bottleneck_summary.get('kind') is None else str(bottleneck_summary['kind'])
    name = None if bottleneck_summary.get('name') is None else str(bottleneck_summary['name'])
    structural_name = None if bottleneck_summary.get('structural_frontier_name') is None else str(bottleneck_summary['structural_frontier_name'])
    local_margin_raw = bottleneck_summary.get('smallest_certified_local_margin')
    local_margin = None if local_margin_raw is None else float(local_margin_raw)
    geometry_status = None if bottleneck_summary.get('current_reduction_geometry_status') is None else str(bottleneck_summary['current_reduction_geometry_status'])
    structural_statement_mode = None if bottleneck_summary.get('structural_frontier_statement_mode') is None else str(bottleneck_summary['structural_frontier_statement_mode'])
    structural_open_hypotheses = _normalize_report_item_labels(bottleneck_summary.get('structural_frontier_open_hypotheses'))
    structural_active_assumptions = _normalize_report_item_labels(bottleneck_summary.get('structural_frontier_active_assumptions'))
    structural_residual_burden_status = None if bottleneck_summary.get('structural_frontier_residual_burden_status') is None else str(bottleneck_summary.get('structural_frontier_residual_burden_status'))

    if kind == 'local-geometric':
        action_kind = 'tighten-local-reduction-geometry'
        target = 'Current reduction geometry'
        action = (
            'Tighten the localized VIII reduction geometry: shrink the discharged witness interval, improve witness-vs-gap separation, '
            'and push the current minimum certified local margin positive and decisively away from zero.'
        )
        rationale = 'The theorem stack is locally geometry-limited at the final reduction interface rather than primarily blocked by an upstream theorem shell.'
    elif kind == 'theorem-structural':
        action_kind = 'discharge-structural-frontier'
        target, action, rationale, _ = _build_frontier_specific_next_move(
            structural_name,
            statement_mode=structural_statement_mode,
            open_hypotheses=structural_open_hypotheses,
            active_assumptions=structural_active_assumptions,
            residual_burden_status=structural_residual_burden_status,
        )
    elif kind == 'mixed':
        action_kind = 'paired-structural-and-local'
        target = name
        structural_target, structural_action, structural_rationale, _ = _build_frontier_specific_next_move(
            structural_name,
            statement_mode=structural_statement_mode,
            open_hypotheses=structural_open_hypotheses,
            active_assumptions=structural_active_assumptions,
            residual_burden_status=structural_residual_burden_status,
        )
        action = (
            f'{structural_action} In parallel, keep tightening the current VIII reduction geometry so the localized witness margin remains positive while the structural frontier is discharged.'
        )
        rationale = f'{structural_rationale} At the same time, the current reduction geometry is still active enough that the local VIII margins must be protected during the structural discharge.'
    else:
        action_kind = 'maintain-and-escalate'
        target = None
        action = 'No active bottleneck is visible in the current status summary; maintain the present local geometry and escalate the strongest remaining theorem package into a full paper-grade discharge.'
        rationale = 'The top-level status report is not currently showing a single decisive active blocker.'

    return {
        'kind': action_kind,
        'target': target,
        'action': action,
        'rationale': rationale,
        'current_bottleneck_kind': kind,
        'current_bottleneck_name': name,
        'current_reduction_geometry_status': geometry_status,
        'current_smallest_certified_local_margin': local_margin,
        'structural_frontier_statement_mode': structural_statement_mode,
        'structural_frontier_open_hypotheses': structural_open_hypotheses,
        'structural_frontier_active_assumptions': structural_active_assumptions,
        'structural_frontier_residual_burden_status': structural_residual_burden_status,
    }



def _assemble_golden_theorem_program_status_report(
    *,
    theorem_i_ii: Mapping[str, Any],
    theorem_iv: Mapping[str, Any],
    theorem_v: Mapping[str, Any],
    identification: Mapping[str, Any],
    theorem_vi: Mapping[str, Any],
    theorem_vii: Mapping[str, Any],
    theorem_viii: Mapping[str, Any],
    discharge_aware: bool,
) -> dict[str, Any]:
    current_reduction_geometry_summary = theorem_viii.get('current_reduction_geometry_summary')
    if not isinstance(current_reduction_geometry_summary, Mapping):
        current_reduction_geometry_summary = extract_theorem_viii_current_reduction_geometry_summary(
            theorem_viii,
            report_kind='theorem-viii-discharge-report' if discharge_aware else 'theorem-viii-report',
            discharge_aware=discharge_aware,
        )
    else:
        current_reduction_geometry_summary = dict(current_reduction_geometry_summary)

    theorem_status_summary = {
        'theorem_i_ii': _summarize_theorem_status_entry('Theorems I-II', theorem_i_ii),
        'theorem_iv': _summarize_theorem_status_entry('Theorem IV', theorem_iv),
        'theorem_v': _summarize_theorem_status_entry('Theorem V', theorem_v),
        'identification_seam': _summarize_theorem_status_entry('Identification seam', identification),
        'theorem_vi': _summarize_theorem_status_entry('Theorem VI', theorem_vi),
        'theorem_vii': _summarize_theorem_status_entry('Theorem VII', theorem_vii),
        'theorem_viii': _summarize_theorem_status_entry('Theorem VIII', theorem_viii),
    }
    theorem_status_rows = list(theorem_status_summary.values())
    bottleneck_summary = _build_theorem_program_bottleneck_summary(
        theorem_status_rows,
        current_reduction_geometry_summary,
    )
    recommended_next_move = _build_theorem_program_recommended_next_move_summary(
        bottleneck_summary,
    )
    implementation_summary = {
        'discharge_aware': discharge_aware,
        'overall_theorem_status': theorem_status_summary['theorem_viii']['theorem_status'],
        'overall_statement_mode': theorem_status_summary['theorem_viii']['statement_mode'],
        'current_reduction_geometry_available': bool(current_reduction_geometry_summary.get('available')),
        'current_reduction_geometry_status': None if current_reduction_geometry_summary.get('status') is None else str(current_reduction_geometry_summary['status']),
        'current_reduction_geometry_minimum_certified_margin': None if current_reduction_geometry_summary.get('minimum_certified_margin') is None else float(current_reduction_geometry_summary['minimum_certified_margin']),
        'current_reduction_geometry_source': None if current_reduction_geometry_summary.get('source') is None else str(current_reduction_geometry_summary['source']),
        'theorem_viii_final_status': None if theorem_viii.get('theorem_status') is None else str(theorem_viii.get('theorem_status')),
        'final_universal_theorem_ready_for_code_path': bool(theorem_viii.get('final_certificate_ready_for_code_path', False)),
        'final_universal_theorem_ready_for_paper': bool(theorem_viii.get('final_certificate_ready_for_paper', False)),
        'true_mathematical_burden_remaining': [str(x) for x in theorem_viii.get('remaining_true_mathematical_burden', [])],
        'paper_grade_burden_remaining': sorted({*[str(x) for x in theorem_viii.get('remaining_workstream_paper_grade_burden', [])], *[str(x) for x in theorem_viii.get('remaining_exhaustion_paper_grade_burden', [])]}),
        'workstream_residual_caveat': [str(x) for x in theorem_viii.get('remaining_workstream_paper_grade_burden', [])],
        'bottleneck_kind': bottleneck_summary['kind'],
        'bottleneck_name': bottleneck_summary['name'],
        'bottleneck_reason': bottleneck_summary['reason'],
        'smallest_certified_local_margin': bottleneck_summary['smallest_certified_local_margin'],
        'recommended_next_move_kind': recommended_next_move['kind'],
        'recommended_next_move_target': recommended_next_move['target'],
        'recommended_next_move_action': recommended_next_move['action'],
        'recommended_next_move_rationale': recommended_next_move['rationale'],
    }
    return {
        'report_kind': 'golden-theorem-program-discharge-status-report' if discharge_aware else 'golden-theorem-program-status-report',
        'discharge_aware': discharge_aware,
        'theorem_status_summary': theorem_status_summary,
        'theorem_status_rows': theorem_status_rows,
        'current_reduction_geometry_summary': current_reduction_geometry_summary,
        'current_reduction_geometry_available': implementation_summary['current_reduction_geometry_available'],
        'current_reduction_geometry_status': implementation_summary['current_reduction_geometry_status'],
        'current_reduction_geometry_minimum_certified_margin': implementation_summary['current_reduction_geometry_minimum_certified_margin'],
        'bottleneck_summary': bottleneck_summary,
        'current_bottleneck_kind': bottleneck_summary['kind'],
        'current_bottleneck_name': bottleneck_summary['name'],
        'current_bottleneck_reason': bottleneck_summary['reason'],
        'current_smallest_certified_local_margin': bottleneck_summary['smallest_certified_local_margin'],
        'recommended_next_move': recommended_next_move,
        'recommended_next_move_kind': recommended_next_move['kind'],
        'recommended_next_move_target': recommended_next_move['target'],
        'recommended_next_move_action': recommended_next_move['action'],
        'recommended_next_move_rationale': recommended_next_move['rationale'],
        'implementation_summary': implementation_summary,
        'subreports': {
            'theorem_i_ii': dict(theorem_i_ii),
            'theorem_iv': dict(theorem_iv),
            'theorem_v': dict(theorem_v),
            'identification_seam': dict(identification),
            'theorem_vi': dict(theorem_vi),
            'theorem_vii': dict(theorem_vii),
            'theorem_viii': dict(theorem_viii),
        },
    }


def build_golden_theorem_program_status_report_from_subreports(
    *,
    theorem_i_ii: Mapping[str, Any],
    theorem_iv: Mapping[str, Any],
    theorem_v: Mapping[str, Any],
    identification: Mapping[str, Any],
    theorem_vi: Mapping[str, Any],
    theorem_vii: Mapping[str, Any],
    theorem_viii: Mapping[str, Any],
    discharge_aware: bool = False,
) -> dict[str, Any]:
    return _assemble_golden_theorem_program_status_report(
        theorem_i_ii=theorem_i_ii,
        theorem_iv=theorem_iv,
        theorem_v=theorem_v,
        identification=identification,
        theorem_vi=theorem_vi,
        theorem_vii=theorem_vii,
        theorem_viii=theorem_viii,
        discharge_aware=discharge_aware,
    )


def _build_golden_theorem_program_status_report(
    *,
    base_K_values: Sequence[float],
    family: HarmonicFamily | None,
    challenger_specs: Sequence[ArithmeticClassSpec] | None,
    discharge_aware: bool,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()

    # Build the shared upstream theorem objects once, then feed them forward.
    # This avoids the very expensive repeated reconstruction of the lower/transport/
    # identification stack that otherwise occurs when VI, VII, and VIII are built
    # independently on the live default path.
    theorem_i_ii = build_golden_theorem_i_ii_report(family=family, **kwargs)
    theorem_iii = build_golden_theorem_iii_report(base_K_values=base_K_values, family=family, **kwargs)
    theorem_iv_lower_neighborhood_certificate = kwargs.get('theorem_iv_lower_neighborhood_certificate')
    if theorem_iv_lower_neighborhood_certificate is None:
        theorem_iv_lower_neighborhood_certificate = build_golden_theorem_iv_lower_neighborhood_report(
            base_K_values=base_K_values,
            family=family,
            rho=kwargs.get('rho'),
            lower_shift_grid=kwargs.get('lower_shift_grid', (-0.015, 0.0, 0.015)),
            lower_resolution_sets=kwargs.get('lower_resolution_sets', ((64, 96, 128), (80, 112, 144))),
            sigma_cap=kwargs.get('sigma_cap', 0.04),
            use_multiresolution=kwargs.get('use_multiresolution', True),
            oversample_factor=kwargs.get('oversample_factor', 8),
            lower_min_cluster_size=kwargs.get('lower_min_cluster_size', 2),
        )
    theorem_iv_upper_tail_coherence_certificate = kwargs.get('theorem_iv_upper_tail_coherence_certificate')
    theorem_iv_upper_bridge_certificate = kwargs.get('theorem_iv_upper_bridge_certificate')
    theorem_iv_upper_bridge_promotion_certificate = kwargs.get('theorem_iv_upper_bridge_promotion_certificate')
    theorem_iv_upper_support_core_neighborhood_certificate = kwargs.get('theorem_iv_upper_support_core_neighborhood_certificate')
    theorem_iv_upper_tail_aware_neighborhood_certificate = kwargs.get('theorem_iv_upper_tail_aware_neighborhood_certificate')
    theorem_iv_upper_tail_stability_certificate = kwargs.get('theorem_iv_upper_tail_stability_certificate')
    theorem_iv_upper_bridge_profile_certificate = kwargs.get('theorem_iv_upper_bridge_profile_certificate')
    theorem_iv = build_golden_theorem_iv_report(
        base_K_values=base_K_values,
        family=family,
        lower_neighborhood_stability_certificate=theorem_iv_lower_neighborhood_certificate,
        upper_tail_coherence_certificate=theorem_iv_upper_tail_coherence_certificate,
        upper_bridge_certificate=theorem_iv_upper_bridge_certificate,
        upper_bridge_promotion_certificate=theorem_iv_upper_bridge_promotion_certificate,
        upper_support_core_neighborhood_certificate=theorem_iv_upper_support_core_neighborhood_certificate,
        upper_tail_aware_neighborhood_certificate=theorem_iv_upper_tail_aware_neighborhood_certificate,
        upper_tail_stability_certificate=theorem_iv_upper_tail_stability_certificate,
        upper_bridge_profile_certificate=theorem_iv_upper_bridge_profile_certificate,
        **kwargs,
    )
    theorem_v_raw = build_golden_theorem_v_report(
        base_K_values=base_K_values,
        family=family,
        theorem_iv_certificate=theorem_iv,
        **kwargs,
    )
    theorem_v = build_golden_theorem_v_compressed_report(
        base_K_values=base_K_values,
        family=family,
        theorem_iii_certificate=theorem_iii,
        theorem_iv_certificate=theorem_iv,
        theorem_v_certificate=theorem_v_raw,
        **kwargs,
    )

    identification_shell = build_golden_theorem_ii_to_v_identification_report(
        base_K_values=base_K_values,
        family=family,
        theorem_iii_certificate=theorem_iii,
        theorem_iv_certificate=theorem_iv,
        theorem_v_certificate=theorem_v_raw,
        theorem_v_compressed_certificate=theorem_v,
        **kwargs,
    )

    if discharge_aware:
        identification_discharge = build_golden_theorem_ii_to_v_identification_discharge_report(
            base_K_values=base_K_values,
            family=family,
            theorem_i_ii_certificate=theorem_i_ii,
            theorem_ii_to_v_identification_certificate=identification_shell,
            **kwargs,
        )
        identification_transport_discharge = build_golden_theorem_ii_to_v_identification_transport_discharge_report(
            base_K_values=base_K_values,
            family=family,
            theorem_v_certificate=theorem_v_raw,
            threshold_identification_discharge_certificate=identification_discharge,
            **kwargs,
        )
        identification = build_golden_theorem_ii_to_v_identification_theorem_report(
            base_K_values=base_K_values,
            family=family,
            threshold_identification_transport_discharge_certificate=identification_transport_discharge,
            **kwargs,
        )
        theorem_vi_base = build_golden_theorem_vi_report(
            base_K_values=base_K_values,
            family=family,
            threshold_identification_certificate=identification,
            **kwargs,
        )
        theorem_vi = build_golden_theorem_vi_discharge_report(
            base_K_values=base_K_values,
            family=family,
            theorem_vi_certificate=theorem_vi_base,
            threshold_identification_transport_discharge_certificate=identification_transport_discharge,
            **kwargs,
        )
        theorem_vii_base = build_golden_theorem_vii_report(
            base_K_values=base_K_values,
            challenger_specs=challenger_specs,
            family=family,
            theorem_vi_envelope_discharge_certificate=theorem_vi,
            **kwargs,
        )
        theorem_vii = build_golden_theorem_vii_discharge_report(
            base_K_values=base_K_values,
            challenger_specs=challenger_specs,
            family=family,
            theorem_vii_certificate=theorem_vii_base,
            theorem_vi_envelope_discharge_certificate=theorem_vi,
            **kwargs,
        )
        theorem_viii_base = build_golden_theorem_viii_report(
            base_K_values=base_K_values,
            family=family,
            theorem_iii_certificate=theorem_iii,
            theorem_iv_certificate=theorem_iv,
            theorem_v_certificate=theorem_v,
            threshold_identification_certificate=identification,
            theorem_vi_certificate=theorem_vi_base,
            theorem_vii_certificate=theorem_vii_base,
            theorem_i_ii_workstream_certificate=theorem_i_ii,
            **kwargs,
        )
        theorem_viii = build_golden_theorem_viii_discharge_report(
            base_K_values=base_K_values,
            family=family,
            baseline_theorem_viii_certificate=theorem_viii_base,
            theorem_vii_exhaustion_discharge_certificate=theorem_vii,
            theorem_vi_envelope_discharge_certificate=theorem_vi,
            threshold_identification_discharge_certificate=identification_discharge,
            theorem_i_ii_workstream_certificate=theorem_i_ii,
            **kwargs,
        )
        report_kind = 'golden-theorem-program-discharge-status-report'
    else:
        identification = identification_shell
        theorem_vi = build_golden_theorem_vi_report(
            base_K_values=base_K_values,
            family=family,
            threshold_identification_certificate=identification,
            **kwargs,
        )
        theorem_vii = build_golden_theorem_vii_report(
            base_K_values=base_K_values,
            challenger_specs=challenger_specs,
            family=family,
            theorem_vi_certificate=theorem_vi,
            **kwargs,
        )
        theorem_viii = build_golden_theorem_viii_report(
            base_K_values=base_K_values,
            family=family,
            theorem_iii_certificate=theorem_iii,
            theorem_iv_certificate=theorem_iv,
            theorem_v_certificate=theorem_v,
            threshold_identification_certificate=identification,
            theorem_vi_certificate=theorem_vi,
            theorem_vii_certificate=theorem_vii,
            theorem_i_ii_workstream_certificate=theorem_i_ii,
            **kwargs,
        )
        report_kind = 'golden-theorem-program-status-report'

    current_reduction_geometry_summary = theorem_viii.get('current_reduction_geometry_summary')
    if not isinstance(current_reduction_geometry_summary, Mapping):
        current_reduction_geometry_summary = extract_theorem_viii_current_reduction_geometry_summary(
            theorem_viii,
            report_kind='theorem-viii-discharge-report' if discharge_aware else 'theorem-viii-report',
            discharge_aware=discharge_aware,
        )
    else:
        current_reduction_geometry_summary = dict(current_reduction_geometry_summary)

    theorem_status_summary = {
        'theorem_i_ii': _summarize_theorem_status_entry('Theorems I-II', theorem_i_ii),
        'theorem_iv': _summarize_theorem_status_entry('Theorem IV', theorem_iv),
        'theorem_v': _summarize_theorem_status_entry('Theorem V', theorem_v),
        'identification_seam': _summarize_theorem_status_entry('Identification seam', identification),
        'theorem_vi': _summarize_theorem_status_entry('Theorem VI', theorem_vi),
        'theorem_vii': _summarize_theorem_status_entry('Theorem VII', theorem_vii),
        'theorem_viii': _summarize_theorem_status_entry('Theorem VIII', theorem_viii),
    }
    theorem_status_rows = list(theorem_status_summary.values())
    bottleneck_summary = _build_theorem_program_bottleneck_summary(
        theorem_status_rows,
        current_reduction_geometry_summary,
    )
    recommended_next_move = _build_theorem_program_recommended_next_move_summary(
        bottleneck_summary,
    )
    implementation_summary = {
        'discharge_aware': discharge_aware,
        'overall_theorem_status': theorem_status_summary['theorem_viii']['theorem_status'],
        'overall_statement_mode': theorem_status_summary['theorem_viii']['statement_mode'],
        'current_reduction_geometry_available': bool(current_reduction_geometry_summary.get('available')),
        'current_reduction_geometry_status': None if current_reduction_geometry_summary.get('status') is None else str(current_reduction_geometry_summary['status']),
        'current_reduction_geometry_minimum_certified_margin': None if current_reduction_geometry_summary.get('minimum_certified_margin') is None else float(current_reduction_geometry_summary['minimum_certified_margin']),
        'current_reduction_geometry_source': None if current_reduction_geometry_summary.get('source') is None else str(current_reduction_geometry_summary['source']),
        'theorem_viii_final_status': None if theorem_viii.get('theorem_status') is None else str(theorem_viii.get('theorem_status')),
        'final_universal_theorem_ready_for_code_path': bool(theorem_viii.get('final_certificate_ready_for_code_path', False)),
        'final_universal_theorem_ready_for_paper': bool(theorem_viii.get('final_certificate_ready_for_paper', False)),
        'true_mathematical_burden_remaining': [str(x) for x in theorem_viii.get('remaining_true_mathematical_burden', [])],
        'paper_grade_burden_remaining': sorted({*[str(x) for x in theorem_viii.get('remaining_workstream_paper_grade_burden', [])], *[str(x) for x in theorem_viii.get('remaining_exhaustion_paper_grade_burden', [])]}),
        'workstream_residual_caveat': [str(x) for x in theorem_viii.get('remaining_workstream_paper_grade_burden', [])],
        'bottleneck_kind': bottleneck_summary['kind'],
        'bottleneck_name': bottleneck_summary['name'],
        'bottleneck_reason': bottleneck_summary['reason'],
        'smallest_certified_local_margin': bottleneck_summary['smallest_certified_local_margin'],
        'recommended_next_move_kind': recommended_next_move['kind'],
        'recommended_next_move_target': recommended_next_move['target'],
        'recommended_next_move_action': recommended_next_move['action'],
        'recommended_next_move_rationale': recommended_next_move['rationale'],
    }
    return {
        'report_kind': report_kind,
        'discharge_aware': discharge_aware,
        'theorem_status_summary': theorem_status_summary,
        'theorem_status_rows': theorem_status_rows,
        'current_reduction_geometry_summary': current_reduction_geometry_summary,
        'current_reduction_geometry_available': implementation_summary['current_reduction_geometry_available'],
        'current_reduction_geometry_status': implementation_summary['current_reduction_geometry_status'],
        'current_reduction_geometry_minimum_certified_margin': implementation_summary['current_reduction_geometry_minimum_certified_margin'],
        'bottleneck_summary': bottleneck_summary,
        'current_bottleneck_kind': bottleneck_summary['kind'],
        'current_bottleneck_name': bottleneck_summary['name'],
        'current_bottleneck_reason': bottleneck_summary['reason'],
        'current_smallest_certified_local_margin': bottleneck_summary['smallest_certified_local_margin'],
        'recommended_next_move': recommended_next_move,
        'recommended_next_move_kind': recommended_next_move['kind'],
        'recommended_next_move_target': recommended_next_move['target'],
        'recommended_next_move_action': recommended_next_move['action'],
        'recommended_next_move_rationale': recommended_next_move['rationale'],
        'implementation_summary': implementation_summary,
        'subreports': {
            'theorem_i_ii': theorem_i_ii,
            'theorem_iv_lower_neighborhood': theorem_iv_lower_neighborhood_certificate,
            'theorem_iv': theorem_iv,
            'theorem_v': theorem_v,
            'identification_seam': identification,
            'theorem_vi': theorem_vi,
            'theorem_vii': theorem_vii,
            'theorem_viii': theorem_viii,
        },
    }



def build_golden_theorem_program_status_report(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _build_golden_theorem_program_status_report(
        base_K_values=base_K_values,
        challenger_specs=challenger_specs,
        family=family,
        discharge_aware=False,
        **kwargs,
    )



def build_golden_theorem_program_discharge_status_report(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _build_golden_theorem_program_status_report(
        base_K_values=base_K_values,
        challenger_specs=challenger_specs,
        family=family,
        discharge_aware=True,
        **kwargs,
    )



def build_golden_implementation_status_report(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_golden_theorem_program_status_report(
        base_K_values=base_K_values,
        challenger_specs=challenger_specs,
        family=family,
        **kwargs,
    )



def build_golden_implementation_discharge_status_report(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_golden_theorem_program_discharge_status_report(
        base_K_values=base_K_values,
        challenger_specs=challenger_specs,
        family=family,
        **kwargs,
    )

def extract_theorem_viii_current_reduction_geometry_summary(report: Mapping[str, Any], *, report_kind: str | None = None, discharge_aware: bool | None = None) -> dict[str, Any]:
    """Normalize the VIII local reduction-geometry fields into one report-level object."""

    kind = report_kind
    if kind is None:
        theorem_status = str(report.get('theorem_status', ''))
        if 'discharge' in theorem_status:
            kind = 'theorem-viii-reduction-discharge'
        else:
            kind = 'theorem-viii-reduction'
    discharge_flag = bool(discharge_aware) if discharge_aware is not None else ('discharge' in str(kind))
    status = report.get('current_reduction_geometry_status')
    if status is None:
        status = 'current-reduction-geometry-missing'
    source = report.get('current_reduction_geometry_source')
    if source is None:
        source = 'unavailable'
    pending_count_raw = report.get('current_reduction_geometry_pending_count', 0)
    try:
        pending_count = int(pending_count_raw)
    except Exception:
        pending_count = 0
    minimum_margin = report.get('current_reduction_geometry_min_margin')
    return {
        'available': bool(status != 'current-reduction-geometry-missing'),
        'status': str(status),
        'source': str(source),
        'minimum_certified_margin': None if minimum_margin is None else float(minimum_margin),
        'witness_vs_overlap_margin': None if report.get('current_reduction_geometry_witness_vs_overlap_margin') is None else float(report['current_reduction_geometry_witness_vs_overlap_margin']),
        'top_gap_scale': None if report.get('current_reduction_geometry_top_gap_scale') is None else float(report['current_reduction_geometry_top_gap_scale']),
        'challenger_upper_bound': None if report.get('current_reduction_geometry_challenger_upper_bound') is None else float(report['current_reduction_geometry_challenger_upper_bound']),
        'exhaustion_upper_bound': None if report.get('current_reduction_geometry_exhaustion_upper_bound') is None else float(report['current_reduction_geometry_exhaustion_upper_bound']),
        'witness_width_vs_top_gap_margin': None if report.get('current_reduction_geometry_witness_width_vs_top_gap_margin') is None else float(report['current_reduction_geometry_witness_width_vs_top_gap_margin']),
        'witness_lower_vs_challenger_upper_margin': None if report.get('current_reduction_geometry_witness_lower_vs_challenger_upper_margin') is None else float(report['current_reduction_geometry_witness_lower_vs_challenger_upper_margin']),
        'pending_count': pending_count,
        'theorem_status': None if report.get('theorem_status') is None else str(report['theorem_status']),
        'statement_mode': None if report.get('statement_mode') is None else str(report['statement_mode']),
        'report_kind': str(kind),
        'discharge_aware': discharge_flag,
    }


def _attach_theorem_viii_current_reduction_geometry_summary(report: Mapping[str, Any], *, report_kind: str, discharge_aware: bool) -> dict[str, Any]:
    augmented = dict(report)
    augmented['current_reduction_geometry_summary'] = extract_theorem_viii_current_reduction_geometry_summary(
        report,
        report_kind=report_kind,
        discharge_aware=discharge_aware,
    )
    return augmented


def build_golden_theorem_viii_reduction_lift_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    report = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()
    return _attach_theorem_viii_current_reduction_geometry_summary(
        report,
        report_kind='theorem-viii-reduction-lift-report',
        discharge_aware=False,
    )


def build_golden_theorem_viii_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    report = build_golden_theorem_viii_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()
    return _attach_theorem_viii_current_reduction_geometry_summary(
        report,
        report_kind='theorem-viii-report',
        discharge_aware=False,
    )


def build_golden_theorem_viii_reduction_discharge_lift_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    report = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()
    return _attach_theorem_viii_current_reduction_geometry_summary(
        report,
        report_kind='theorem-viii-reduction-discharge-lift-report',
        discharge_aware=True,
    )


def build_golden_theorem_viii_discharge_report(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    report = build_golden_theorem_viii_discharge_certificate(
        base_K_values=base_K_values,
        family=family,
        **kwargs,
    ).to_dict()
    return _attach_theorem_viii_current_reduction_geometry_summary(
        report,
        report_kind='theorem-viii-discharge-report',
        discharge_aware=True,
    )






def build_validated_universality_class_theorem_discharge_report(
    *,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    return build_validated_universality_class_theorem_discharge_certificate(
        family=family or HarmonicFamily(),
        **kwargs,
    ).to_dict()


def build_validated_universality_class_theorem_promotion_report(
    *,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    return build_validated_universality_class_theorem_promotion_certificate(
        family=family or HarmonicFamily(),
        **kwargs,
    ).to_dict()


def build_validated_critical_surface_theorem_discharge_report(
    *,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    return build_validated_critical_surface_theorem_discharge_certificate(
        family=family or HarmonicFamily(),
        **kwargs,
    ).to_dict()


def build_validated_critical_surface_theorem_promotion_report(
    *,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> dict[str, Any]:
    return build_validated_critical_surface_theorem_promotion_certificate(
        family=family or HarmonicFamily(),
        **kwargs,
    ).to_dict()

def build_validated_renormalization_package_discharge_report(
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_validated_renormalization_package_discharge_certificate(
        family=family,
        **kwargs,
    ).to_dict()


def build_validated_renormalization_package_promotion_report(
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_validated_renormalization_package_promotion_certificate(
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_theorem_i_ii_workstream_lift_report(
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_i_ii_workstream_lift_certificate(
        family=family,
        **kwargs,
    ).to_dict()


def build_golden_theorem_i_ii_report(
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_golden_theorem_i_ii_certificate(
        family=family,
        **kwargs,
    ).to_dict()


def build_universality_class_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str = 'harmonic_family',
    amplitude_anchor_tol: float = 0.35,
    phase_anchor_tol: float = 0.5,
    higher_mode_energy_tol: float = 0.5,
    weighted_mode_budget: float = 3.0,
    max_mode_allowed: int = 8,
    min_strip_width_proxy: float = 0.03,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_universality_class_certificate(
        family,
        family_label=family_label,
        amplitude_anchor_tol=amplitude_anchor_tol,
        phase_anchor_tol=phase_anchor_tol,
        higher_mode_energy_tol=higher_mode_energy_tol,
        weighted_mode_budget=weighted_mode_budget,
        max_mode_allowed=max_mode_allowed,
        min_strip_width_proxy=min_strip_width_proxy,
    ).to_dict()


def build_renormalization_class_report(
    family: HarmonicFamily | None = None,
    *,
    family_label: str = 'harmonic_family',
    chart_radius_tol: float = 0.9,
    stable_budget: float = 0.6,
    unstable_budget: float = 0.4,
    transversality_floor: float = 1e-3,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    return build_renormalization_class_certificate(
        family,
        family_label=family_label,
        chart_radius_tol=chart_radius_tol,
        stable_budget=stable_budget,
        unstable_budget=unstable_budget,
        transversality_floor=transversality_floor,
    ).to_dict()
