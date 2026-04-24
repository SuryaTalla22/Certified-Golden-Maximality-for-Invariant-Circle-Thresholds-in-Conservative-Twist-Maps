from __future__ import annotations

"""Edge-class decomposed transport-slope weighted golden rate control.

This layer refines the transport-slope weighted golden/Fibonacci recurrence law
by *splitting* the phi-step tail budget into three explicit edge classes:

1. derivative-driven continuation support,
2. tangent-driven continuation support, and
3. fallback recurrence support.

The purpose is not to claim a final theorem, but to make the weighted
recurrence-aware tail law more auditable and more theorem-facing.  Instead of a
single blended continuation-strength score, each adjacent convergent step now
carries classwise shares and classwise beta contributions.  Those shares are
then accumulated into suffix budgets, so every node on the certified tail comes
with an explicit decomposition of its weighted golden tail radius.
"""

from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from statistics import mean
from typing import Any

from .certified_tail_modulus_control import build_certified_tail_modulus_certificate
from .golden_recurrence_rate_control import build_golden_recurrence_rate_certificate
from .transport_certified_limit_control import build_transport_certified_limit_certificate
from .transport_slope_weighted_golden_rate_control import (
    _nonincreasing,
    _normalize_contraction,
    _normalize_positive,
    _pair_interval_intersection,
    _safe_step_beta,
)

_PHI = 0.5 * (1.0 + sqrt(5.0))


@dataclass
class EdgeClassWeightedGoldenRateNode:
    start_index: int
    label: str
    p: int
    q: int
    golden_depth: int
    transport_center: float
    local_radius: float
    actual_tail_modulus_radius: float
    edge_class_weighted_tail_radius: float
    edge_class_weighted_total_cauchy_radius: float
    derivative_tail_radius: float
    tangent_tail_radius: float
    fallback_tail_radius: float
    derivative_share: float
    tangent_share: float
    fallback_share: float
    derivative_interval_lo: float
    derivative_interval_hi: float
    tangent_interval_lo: float
    tangent_interval_hi: float
    fallback_interval_lo: float
    fallback_interval_hi: float
    weighted_interval_lo: float
    weighted_interval_hi: float
    weighted_interval_width: float
    derivative_strength_to_next: float | None
    tangent_strength_to_next: float | None
    fallback_strength_to_next: float | None
    derivative_beta_contrib_to_next: float | None
    tangent_beta_contrib_to_next: float | None
    fallback_beta_contrib_to_next: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EdgeClassWeightedGoldenRateCertificate:
    rho_target: float | None
    family_label: str | None
    entry_count: int
    usable_entry_count: int
    chain_labels: list[str]
    chain_qs: list[int]
    chain_ps: list[int]
    chain_length: int
    exact_fibonacci_recurrence: bool
    q_recurrence_max_defect: int
    p_recurrence_max_defect: int
    derivative_strength_mean: float | None
    tangent_strength_mean: float | None
    fallback_strength_mean: float | None
    derivative_beta_contrib_min: float | None
    derivative_beta_contrib_mean: float | None
    derivative_beta_contrib_max: float | None
    tangent_beta_contrib_min: float | None
    tangent_beta_contrib_mean: float | None
    tangent_beta_contrib_max: float | None
    fallback_beta_contrib_min: float | None
    fallback_beta_contrib_mean: float | None
    fallback_beta_contrib_max: float | None
    chosen_edge_class_step_exponent: float | None
    edge_class_step_exponent_safety_factor: float
    edge_class_weighted_golden_tail_constant: float | None
    derivative_tail_constant: float | None
    tangent_tail_constant: float | None
    fallback_tail_constant: float | None
    edge_class_tail_nonincreasing: bool
    classwise_tail_nonincreasing: bool
    actual_tail_dominated_by_edge_class_rate: bool
    first_edge_class_tail_radius: float | None
    last_edge_class_tail_radius: float | None
    mean_edge_class_tail_radius: float | None
    derivative_share_mean: float | None
    tangent_share_mean: float | None
    fallback_share_mean: float | None
    selected_edge_class_interval_lo: float | None
    selected_edge_class_interval_hi: float | None
    selected_edge_class_interval_width: float | None
    edge_class_transport_intersection_lo: float | None
    edge_class_transport_intersection_hi: float | None
    edge_class_transport_intersection_width: float | None
    theorem_status: str
    notes: str
    nodes: list[EdgeClassWeightedGoldenRateNode]

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho_target': self.rho_target,
            'family_label': self.family_label,
            'entry_count': int(self.entry_count),
            'usable_entry_count': int(self.usable_entry_count),
            'chain_labels': [str(x) for x in self.chain_labels],
            'chain_qs': [int(x) for x in self.chain_qs],
            'chain_ps': [int(x) for x in self.chain_ps],
            'chain_length': int(self.chain_length),
            'exact_fibonacci_recurrence': bool(self.exact_fibonacci_recurrence),
            'q_recurrence_max_defect': int(self.q_recurrence_max_defect),
            'p_recurrence_max_defect': int(self.p_recurrence_max_defect),
            'derivative_strength_mean': self.derivative_strength_mean,
            'tangent_strength_mean': self.tangent_strength_mean,
            'fallback_strength_mean': self.fallback_strength_mean,
            'derivative_beta_contrib_min': self.derivative_beta_contrib_min,
            'derivative_beta_contrib_mean': self.derivative_beta_contrib_mean,
            'derivative_beta_contrib_max': self.derivative_beta_contrib_max,
            'tangent_beta_contrib_min': self.tangent_beta_contrib_min,
            'tangent_beta_contrib_mean': self.tangent_beta_contrib_mean,
            'tangent_beta_contrib_max': self.tangent_beta_contrib_max,
            'fallback_beta_contrib_min': self.fallback_beta_contrib_min,
            'fallback_beta_contrib_mean': self.fallback_beta_contrib_mean,
            'fallback_beta_contrib_max': self.fallback_beta_contrib_max,
            'chosen_edge_class_step_exponent': self.chosen_edge_class_step_exponent,
            'edge_class_step_exponent_safety_factor': float(self.edge_class_step_exponent_safety_factor),
            'edge_class_weighted_golden_tail_constant': self.edge_class_weighted_golden_tail_constant,
            'derivative_tail_constant': self.derivative_tail_constant,
            'tangent_tail_constant': self.tangent_tail_constant,
            'fallback_tail_constant': self.fallback_tail_constant,
            'edge_class_tail_nonincreasing': bool(self.edge_class_tail_nonincreasing),
            'classwise_tail_nonincreasing': bool(self.classwise_tail_nonincreasing),
            'actual_tail_dominated_by_edge_class_rate': bool(self.actual_tail_dominated_by_edge_class_rate),
            'first_edge_class_tail_radius': self.first_edge_class_tail_radius,
            'last_edge_class_tail_radius': self.last_edge_class_tail_radius,
            'mean_edge_class_tail_radius': self.mean_edge_class_tail_radius,
            'derivative_share_mean': self.derivative_share_mean,
            'tangent_share_mean': self.tangent_share_mean,
            'fallback_share_mean': self.fallback_share_mean,
            'selected_edge_class_interval_lo': self.selected_edge_class_interval_lo,
            'selected_edge_class_interval_hi': self.selected_edge_class_interval_hi,
            'selected_edge_class_interval_width': self.selected_edge_class_interval_width,
            'edge_class_transport_intersection_lo': self.edge_class_transport_intersection_lo,
            'edge_class_transport_intersection_hi': self.edge_class_transport_intersection_hi,
            'edge_class_transport_intersection_width': self.edge_class_transport_intersection_width,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'nodes': [node.to_dict() for node in self.nodes],
        }


def _clamp_unit(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def _edge_strengths(transport_node: dict[str, Any]) -> tuple[float, float, float]:
    derivative_floor = _normalize_positive(transport_node.get('derivative_floor'))
    derivative_flag = 1.0 if transport_node.get('derivative_backed') else 0.0
    derivative_strength = 0.65 * derivative_floor + 0.35 * derivative_flag

    slope_strength = _normalize_positive(transport_node.get('slope_center_inf'))
    contraction_strength = _normalize_contraction(transport_node.get('interval_tangent_contraction'))
    tangent_flag = 1.0 if (transport_node.get('tangent_inclusion_success') or transport_node.get('interval_tangent_success')) else 0.0
    tangent_strength = 0.4 * slope_strength + 0.4 * contraction_strength + 0.2 * tangent_flag

    derivative_strength = _clamp_unit(derivative_strength)
    tangent_strength = _clamp_unit(tangent_strength)
    fallback_strength = _clamp_unit(max(0.0, 1.0 - max(derivative_strength, tangent_strength)))

    total = derivative_strength + tangent_strength + fallback_strength
    if total <= 1e-15:
        return 0.0, 0.0, 1.0
    return (
        float(derivative_strength / total),
        float(tangent_strength / total),
        float(fallback_strength / total),
    )


def build_edge_class_weighted_golden_rate_certificate(
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
) -> EdgeClassWeightedGoldenRateCertificate:
    certified = build_certified_tail_modulus_certificate(
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
    golden = build_golden_recurrence_rate_certificate(
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
    transport = build_transport_certified_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
    ).to_dict()

    cert_nodes = list(certified.get('nodes', []) or [])
    trans_by_q = {int(node['q']): dict(node) for node in (transport.get('entries', []) or []) if node.get('q') is not None}
    common_nodes = [dict(node) for node in cert_nodes if int(node['q']) in trans_by_q]
    if len(common_nodes) < 2:
        return EdgeClassWeightedGoldenRateCertificate(
            rho_target=rho_target,
            family_label=family_label,
            entry_count=int(certified.get('entry_count', 0) or 0),
            usable_entry_count=len(common_nodes),
            chain_labels=[str(node['label']) for node in common_nodes],
            chain_qs=[int(node['q']) for node in common_nodes],
            chain_ps=[int(node['p']) for node in common_nodes],
            chain_length=len(common_nodes),
            exact_fibonacci_recurrence=False,
            q_recurrence_max_defect=0,
            p_recurrence_max_defect=0,
            derivative_strength_mean=None,
            tangent_strength_mean=None,
            fallback_strength_mean=None,
            derivative_beta_contrib_min=None,
            derivative_beta_contrib_mean=None,
            derivative_beta_contrib_max=None,
            tangent_beta_contrib_min=None,
            tangent_beta_contrib_mean=None,
            tangent_beta_contrib_max=None,
            fallback_beta_contrib_min=None,
            fallback_beta_contrib_mean=None,
            fallback_beta_contrib_max=None,
            chosen_edge_class_step_exponent=None,
            edge_class_step_exponent_safety_factor=float(rate_exponent_safety_factor),
            edge_class_weighted_golden_tail_constant=None,
            derivative_tail_constant=None,
            tangent_tail_constant=None,
            fallback_tail_constant=None,
            edge_class_tail_nonincreasing=False,
            classwise_tail_nonincreasing=False,
            actual_tail_dominated_by_edge_class_rate=False,
            first_edge_class_tail_radius=None,
            last_edge_class_tail_radius=None,
            mean_edge_class_tail_radius=None,
            derivative_share_mean=None,
            tangent_share_mean=None,
            fallback_share_mean=None,
            selected_edge_class_interval_lo=None,
            selected_edge_class_interval_hi=None,
            selected_edge_class_interval_width=None,
            edge_class_transport_intersection_lo=None,
            edge_class_transport_intersection_hi=None,
            edge_class_transport_intersection_width=None,
            theorem_status='edge-class-weighted-golden-rate-insufficient',
            notes='Need at least two common certified/transport convergents to build an edge-class decomposed weighted golden recurrence law.',
            nodes=[],
        )

    qs = [int(node['q']) for node in common_nodes]
    ps = [int(node['p']) for node in common_nodes]
    labels = [str(node['label']) for node in common_nodes]
    q_rec_defects: list[int] = []
    p_rec_defects: list[int] = []
    for i in range(2, len(common_nodes)):
        q_rec_defects.append(abs(qs[i] - qs[i - 1] - qs[i - 2]))
        p_rec_defects.append(abs(ps[i] - ps[i - 1] - ps[i - 2]))
    exact_recurrence = (max(q_rec_defects) if q_rec_defects else 0) == 0 and (max(p_rec_defects) if p_rec_defects else 0) == 0

    edge_deriv_shares: list[float] = []
    edge_tangent_shares: list[float] = []
    edge_fallback_shares: list[float] = []
    derivative_contribs: list[float] = []
    tangent_contribs: list[float] = []
    fallback_contribs: list[float] = []
    total_weighted_betas: list[float] = []

    for i in range(len(common_nodes) - 1):
        a = common_nodes[i]
        b = common_nodes[i + 1]
        raw_beta = _safe_step_beta(float(a['tail_modulus_radius']), float(b['tail_modulus_radius']))
        ta = trans_by_q[int(a['q'])]
        tb = trans_by_q[int(b['q'])]
        da, ta_share, fa = _edge_strengths(ta)
        db, tb_share, fb = _edge_strengths(tb)
        deriv_share = 0.5 * (da + db)
        tangent_share = 0.5 * (ta_share + tb_share)
        fallback_share = 0.5 * (fa + fb)
        share_total = deriv_share + tangent_share + fallback_share
        if share_total <= 1e-15:
            deriv_share, tangent_share, fallback_share = 0.0, 0.0, 1.0
        else:
            deriv_share /= share_total
            tangent_share /= share_total
            fallback_share /= share_total
        edge_deriv_shares.append(float(deriv_share))
        edge_tangent_shares.append(float(tangent_share))
        edge_fallback_shares.append(float(fallback_share))
        if raw_beta is None:
            continue
        derivative_contrib = float(raw_beta * transport_strength_boost * derivative_share_weight * deriv_share)
        tangent_contrib = float(raw_beta * transport_strength_boost * tangent_share_weight * tangent_share)
        fallback_contrib = float(raw_beta * transport_strength_boost * fallback_share_weight * fallback_share)
        weighted_beta = float(raw_beta + derivative_contrib + tangent_contrib + fallback_contrib)
        derivative_contribs.append(derivative_contrib)
        tangent_contribs.append(tangent_contrib)
        fallback_contribs.append(fallback_contrib)
        total_weighted_betas.append(weighted_beta)

    base_beta = golden.get('chosen_step_exponent')
    chosen_beta = None
    if total_weighted_betas:
        chosen_beta = min(total_weighted_betas) * float(rate_exponent_safety_factor)
        if base_beta is not None:
            chosen_beta = max(float(base_beta), float(chosen_beta))
        chosen_beta = max(float(min_step_exponent), float(chosen_beta))
        chosen_beta = min(float(max_rate_exponent), float(chosen_beta))

    if chosen_beta is None:
        return EdgeClassWeightedGoldenRateCertificate(
            rho_target=rho_target,
            family_label=family_label,
            entry_count=int(certified.get('entry_count', 0) or 0),
            usable_entry_count=len(common_nodes),
            chain_labels=labels,
            chain_qs=qs,
            chain_ps=ps,
            chain_length=len(common_nodes),
            exact_fibonacci_recurrence=exact_recurrence,
            q_recurrence_max_defect=max(q_rec_defects) if q_rec_defects else 0,
            p_recurrence_max_defect=max(p_rec_defects) if p_rec_defects else 0,
            derivative_strength_mean=mean(edge_deriv_shares) if edge_deriv_shares else None,
            tangent_strength_mean=mean(edge_tangent_shares) if edge_tangent_shares else None,
            fallback_strength_mean=mean(edge_fallback_shares) if edge_fallback_shares else None,
            derivative_beta_contrib_min=min(derivative_contribs) if derivative_contribs else None,
            derivative_beta_contrib_mean=mean(derivative_contribs) if derivative_contribs else None,
            derivative_beta_contrib_max=max(derivative_contribs) if derivative_contribs else None,
            tangent_beta_contrib_min=min(tangent_contribs) if tangent_contribs else None,
            tangent_beta_contrib_mean=mean(tangent_contribs) if tangent_contribs else None,
            tangent_beta_contrib_max=max(tangent_contribs) if tangent_contribs else None,
            fallback_beta_contrib_min=min(fallback_contribs) if fallback_contribs else None,
            fallback_beta_contrib_mean=mean(fallback_contribs) if fallback_contribs else None,
            fallback_beta_contrib_max=max(fallback_contribs) if fallback_contribs else None,
            chosen_edge_class_step_exponent=None,
            edge_class_step_exponent_safety_factor=float(rate_exponent_safety_factor),
            edge_class_weighted_golden_tail_constant=None,
            derivative_tail_constant=None,
            tangent_tail_constant=None,
            fallback_tail_constant=None,
            edge_class_tail_nonincreasing=False,
            classwise_tail_nonincreasing=False,
            actual_tail_dominated_by_edge_class_rate=False,
            first_edge_class_tail_radius=None,
            last_edge_class_tail_radius=None,
            mean_edge_class_tail_radius=None,
            derivative_share_mean=mean(edge_deriv_shares) if edge_deriv_shares else None,
            tangent_share_mean=mean(edge_tangent_shares) if edge_tangent_shares else None,
            fallback_share_mean=mean(edge_fallback_shares) if edge_fallback_shares else None,
            selected_edge_class_interval_lo=None,
            selected_edge_class_interval_hi=None,
            selected_edge_class_interval_width=None,
            edge_class_transport_intersection_lo=None,
            edge_class_transport_intersection_hi=None,
            edge_class_transport_intersection_width=None,
            theorem_status='edge-class-weighted-golden-rate-insufficient',
            notes='Observed certified tail radii did not yield a positive edge-class weighted phi-step decay exponent.',
            nodes=[],
        )

    scales: list[float] = []
    current_scale = 1.0
    for i in range(len(common_nodes)):
        if i == 0:
            current_scale = 1.0
        else:
            current_scale *= _PHI ** float(chosen_beta)
        scales.append(float(current_scale))

    total_constant = max(float(node['tail_modulus_radius']) * scale for node, scale in zip(common_nodes, scales))

    suffix_deriv_share: list[float] = []
    suffix_tangent_share: list[float] = []
    suffix_fallback_share: list[float] = []
    for i in range(len(common_nodes)):
        if i >= len(edge_deriv_shares):
            if edge_deriv_shares:
                d_share = edge_deriv_shares[-1]
                t_share = edge_tangent_shares[-1]
                f_share = edge_fallback_shares[-1]
            else:
                d_share, t_share, f_share = 0.0, 0.0, 1.0
        else:
            d_share = mean(edge_deriv_shares[i:])
            t_share = mean(edge_tangent_shares[i:])
            f_share = mean(edge_fallback_shares[i:])
            s = d_share + t_share + f_share
            if s > 1e-15:
                d_share, t_share, f_share = d_share / s, t_share / s, f_share / s
        suffix_deriv_share.append(float(d_share))
        suffix_tangent_share.append(float(t_share))
        suffix_fallback_share.append(float(f_share))

    derivative_constant = max(total_constant * share for share in suffix_deriv_share)
    tangent_constant = max(total_constant * share for share in suffix_tangent_share)
    fallback_constant = max(total_constant * share for share in suffix_fallback_share)

    nodes: list[EdgeClassWeightedGoldenRateNode] = []
    total_tail_radii: list[float] = []
    derivative_tail_radii: list[float] = []
    tangent_tail_radii: list[float] = []
    fallback_tail_radii: list[float] = []
    selected_lo = None
    selected_hi = None
    actual_tail_dominated = True
    for i, (node, scale) in enumerate(zip(common_nodes, scales)):
        center = float(node['transport_center'])
        local_radius = float(node['local_radius'])
        d_share = suffix_deriv_share[i]
        t_share = suffix_tangent_share[i]
        f_share = suffix_fallback_share[i]
        total_tail = float(total_constant / scale)
        derivative_tail = float(total_tail * d_share)
        tangent_tail = float(total_tail * t_share)
        fallback_tail = float(total_tail * f_share)
        total_radius = float(total_tail + local_radius)
        lo = center - total_radius
        hi = center + total_radius
        if selected_lo is None or selected_hi is None:
            selected_lo, selected_hi = lo, hi
        else:
            selected_lo, selected_hi, _ = _pair_interval_intersection(selected_lo, selected_hi, lo, hi)
        actual_tail = float(node['tail_modulus_radius'])
        actual_tail_dominated &= actual_tail <= total_tail + 1e-15
        derivative_lo = center - (local_radius + derivative_tail)
        derivative_hi = center + (local_radius + derivative_tail)
        tangent_lo = center - (local_radius + tangent_tail)
        tangent_hi = center + (local_radius + tangent_tail)
        fallback_lo = center - (local_radius + fallback_tail)
        fallback_hi = center + (local_radius + fallback_tail)
        total_tail_radii.append(total_tail)
        derivative_tail_radii.append(derivative_tail)
        tangent_tail_radii.append(tangent_tail)
        fallback_tail_radii.append(fallback_tail)
        nodes.append(
            EdgeClassWeightedGoldenRateNode(
                start_index=int(node['start_index']),
                label=str(node['label']),
                p=int(node['p']),
                q=int(node['q']),
                golden_depth=int(i),
                transport_center=center,
                local_radius=local_radius,
                actual_tail_modulus_radius=actual_tail,
                edge_class_weighted_tail_radius=total_tail,
                edge_class_weighted_total_cauchy_radius=total_radius,
                derivative_tail_radius=derivative_tail,
                tangent_tail_radius=tangent_tail,
                fallback_tail_radius=fallback_tail,
                derivative_share=d_share,
                tangent_share=t_share,
                fallback_share=f_share,
                derivative_interval_lo=derivative_lo,
                derivative_interval_hi=derivative_hi,
                tangent_interval_lo=tangent_lo,
                tangent_interval_hi=tangent_hi,
                fallback_interval_lo=fallback_lo,
                fallback_interval_hi=fallback_hi,
                weighted_interval_lo=lo,
                weighted_interval_hi=hi,
                weighted_interval_width=float(hi - lo),
                derivative_strength_to_next=edge_deriv_shares[i] if i < len(edge_deriv_shares) else None,
                tangent_strength_to_next=edge_tangent_shares[i] if i < len(edge_tangent_shares) else None,
                fallback_strength_to_next=edge_fallback_shares[i] if i < len(edge_fallback_shares) else None,
                derivative_beta_contrib_to_next=derivative_contribs[i] if i < len(derivative_contribs) else None,
                tangent_beta_contrib_to_next=tangent_contribs[i] if i < len(tangent_contribs) else None,
                fallback_beta_contrib_to_next=fallback_contribs[i] if i < len(fallback_contribs) else None,
            )
        )

    selected_width = None if selected_lo is None or selected_hi is None else float(selected_hi - selected_lo)
    weighted_lo = golden.get('rate_golden_intersection_lo')
    weighted_hi = golden.get('rate_golden_intersection_hi')
    egt_lo, egt_hi, egt_w = _pair_interval_intersection(selected_lo, selected_hi, weighted_lo, weighted_hi)

    classwise_tail_nonincreasing = (
        _nonincreasing(derivative_tail_radii)
        and _nonincreasing(tangent_tail_radii)
        and _nonincreasing(fallback_tail_radii)
    )

    if (
        selected_lo is not None
        and selected_hi is not None
        and egt_lo is not None
        and egt_hi is not None
        and exact_recurrence
        and actual_tail_dominated
        and _nonincreasing(total_tail_radii)
        and classwise_tail_nonincreasing
    ):
        status = 'edge-class-weighted-golden-rate-strong'
        notes = (
            'The transport-slope weighted golden recurrence law admits an explicit edge-class decomposition into derivative-driven, tangent-driven, and fallback recurrence budgets, and this decomposed law remains compatible with the earlier recurrence-aware interval.'
        )
    elif selected_lo is not None and selected_hi is not None:
        status = 'edge-class-weighted-golden-rate-partial'
        notes = (
            'An edge-class decomposed weighted golden recurrence law can be built and yields a common interval, but recurrence, domination, monotonicity, or compatibility with the earlier recurrence-aware interval are not yet fully strong.'
        )
    else:
        status = 'edge-class-weighted-golden-rate-incomplete'
        notes = 'The edge-class decomposed weighted golden recurrence law did not yield a stable common interval.'

    return EdgeClassWeightedGoldenRateCertificate(
        rho_target=rho_target,
        family_label=family_label,
        entry_count=int(certified.get('entry_count', 0) or 0),
        usable_entry_count=len(common_nodes),
        chain_labels=labels,
        chain_qs=qs,
        chain_ps=ps,
        chain_length=len(common_nodes),
        exact_fibonacci_recurrence=exact_recurrence,
        q_recurrence_max_defect=max(q_rec_defects) if q_rec_defects else 0,
        p_recurrence_max_defect=max(p_rec_defects) if p_rec_defects else 0,
        derivative_strength_mean=mean(edge_deriv_shares) if edge_deriv_shares else None,
        tangent_strength_mean=mean(edge_tangent_shares) if edge_tangent_shares else None,
        fallback_strength_mean=mean(edge_fallback_shares) if edge_fallback_shares else None,
        derivative_beta_contrib_min=min(derivative_contribs) if derivative_contribs else None,
        derivative_beta_contrib_mean=mean(derivative_contribs) if derivative_contribs else None,
        derivative_beta_contrib_max=max(derivative_contribs) if derivative_contribs else None,
        tangent_beta_contrib_min=min(tangent_contribs) if tangent_contribs else None,
        tangent_beta_contrib_mean=mean(tangent_contribs) if tangent_contribs else None,
        tangent_beta_contrib_max=max(tangent_contribs) if tangent_contribs else None,
        fallback_beta_contrib_min=min(fallback_contribs) if fallback_contribs else None,
        fallback_beta_contrib_mean=mean(fallback_contribs) if fallback_contribs else None,
        fallback_beta_contrib_max=max(fallback_contribs) if fallback_contribs else None,
        chosen_edge_class_step_exponent=float(chosen_beta),
        edge_class_step_exponent_safety_factor=float(rate_exponent_safety_factor),
        edge_class_weighted_golden_tail_constant=float(total_constant),
        derivative_tail_constant=float(derivative_constant),
        tangent_tail_constant=float(tangent_constant),
        fallback_tail_constant=float(fallback_constant),
        edge_class_tail_nonincreasing=_nonincreasing(total_tail_radii),
        classwise_tail_nonincreasing=classwise_tail_nonincreasing,
        actual_tail_dominated_by_edge_class_rate=actual_tail_dominated,
        first_edge_class_tail_radius=total_tail_radii[0] if total_tail_radii else None,
        last_edge_class_tail_radius=total_tail_radii[-1] if total_tail_radii else None,
        mean_edge_class_tail_radius=mean(total_tail_radii) if total_tail_radii else None,
        derivative_share_mean=mean(suffix_deriv_share) if suffix_deriv_share else None,
        tangent_share_mean=mean(suffix_tangent_share) if suffix_tangent_share else None,
        fallback_share_mean=mean(suffix_fallback_share) if suffix_fallback_share else None,
        selected_edge_class_interval_lo=selected_lo,
        selected_edge_class_interval_hi=selected_hi,
        selected_edge_class_interval_width=selected_width,
        edge_class_transport_intersection_lo=egt_lo,
        edge_class_transport_intersection_hi=egt_hi,
        edge_class_transport_intersection_width=egt_w,
        theorem_status=status,
        notes=notes,
        nodes=nodes,
    )


__all__ = [
    'EdgeClassWeightedGoldenRateCertificate',
    'EdgeClassWeightedGoldenRateNode',
    'build_edge_class_weighted_golden_rate_certificate',
]
