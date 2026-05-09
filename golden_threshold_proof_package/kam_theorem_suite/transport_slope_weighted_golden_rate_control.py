from __future__ import annotations

"""Transport-slope weighted golden recurrence rate control.

This layer strengthens the golden/Fibonacci-normalized tail law by allowing the
phi-step decay profile to depend not only on certified tail radii and recurrence
structure, but also on local continuation strength extracted from the transport
certificate.  The guiding principle is conservative: stronger branch transport
support should modestly improve the step decay budget, never replace it.

Concretely, for each adjacent convergent pair we combine:

1. derivative floors from the branch certificates,
2. branch-tube slope-center lower bounds,
3. interval-tangent contraction data, and
4. tangent-inclusion success flags,

into a continuation-strength score in ``[0, 1]``.  The observed phi-step decay
between adjacent certified tail radii is then weighted by that score, yielding a
recurrence-aware tail law that is informed by continuation geometry rather than
by recurrence alone.
"""

from dataclasses import asdict, dataclass
from math import isfinite, log, sqrt
from statistics import mean
from typing import Any

from .certified_tail_modulus_control import build_certified_tail_modulus_certificate
from .golden_recurrence_rate_control import build_golden_recurrence_rate_certificate
from .transport_certified_limit_control import build_transport_certified_limit_certificate

_PHI = 0.5 * (1.0 + sqrt(5.0))


@dataclass
class TransportSlopeWeightedGoldenRateNode:
    start_index: int
    label: str
    p: int
    q: int
    golden_depth: int
    transport_center: float
    local_radius: float
    actual_tail_modulus_radius: float
    actual_total_cauchy_radius: float
    weighted_golden_tail_modulus_radius: float
    weighted_golden_total_cauchy_radius: float
    weighted_interval_lo: float
    weighted_interval_hi: float
    weighted_interval_width: float
    transport_strength_to_next: float | None
    weighted_step_exponent_to_next: float | None
    derivative_floor: float | None
    slope_center_inf: float | None
    interval_tangent_contraction: float | None
    derivative_backed: bool
    tangent_backed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TransportSlopeWeightedGoldenRateCertificate:
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
    transport_strength_min: float | None
    transport_strength_mean: float | None
    transport_strength_max: float | None
    observed_weighted_step_beta_min: float | None
    observed_weighted_step_beta_mean: float | None
    observed_weighted_step_beta_max: float | None
    chosen_weighted_step_exponent: float | None
    weighted_step_exponent_safety_factor: float
    weighted_golden_normalized_tail_constant: float | None
    weighted_tail_nonincreasing: bool
    actual_tail_dominated_by_weighted_rate: bool
    actual_total_dominated_by_weighted_rate: bool
    first_weighted_tail_radius: float | None
    last_weighted_tail_radius: float | None
    mean_weighted_tail_radius: float | None
    selected_weighted_interval_lo: float | None
    selected_weighted_interval_hi: float | None
    selected_weighted_interval_width: float | None
    weighted_golden_intersection_lo: float | None
    weighted_golden_intersection_hi: float | None
    weighted_golden_intersection_width: float | None
    theorem_status: str
    notes: str
    nodes: list[TransportSlopeWeightedGoldenRateNode]

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
            'transport_strength_min': self.transport_strength_min,
            'transport_strength_mean': self.transport_strength_mean,
            'transport_strength_max': self.transport_strength_max,
            'observed_weighted_step_beta_min': self.observed_weighted_step_beta_min,
            'observed_weighted_step_beta_mean': self.observed_weighted_step_beta_mean,
            'observed_weighted_step_beta_max': self.observed_weighted_step_beta_max,
            'chosen_weighted_step_exponent': self.chosen_weighted_step_exponent,
            'weighted_step_exponent_safety_factor': float(self.weighted_step_exponent_safety_factor),
            'weighted_golden_normalized_tail_constant': self.weighted_golden_normalized_tail_constant,
            'weighted_tail_nonincreasing': bool(self.weighted_tail_nonincreasing),
            'actual_tail_dominated_by_weighted_rate': bool(self.actual_tail_dominated_by_weighted_rate),
            'actual_total_dominated_by_weighted_rate': bool(self.actual_total_dominated_by_weighted_rate),
            'first_weighted_tail_radius': self.first_weighted_tail_radius,
            'last_weighted_tail_radius': self.last_weighted_tail_radius,
            'mean_weighted_tail_radius': self.mean_weighted_tail_radius,
            'selected_weighted_interval_lo': self.selected_weighted_interval_lo,
            'selected_weighted_interval_hi': self.selected_weighted_interval_hi,
            'selected_weighted_interval_width': self.selected_weighted_interval_width,
            'weighted_golden_intersection_lo': self.weighted_golden_intersection_lo,
            'weighted_golden_intersection_hi': self.weighted_golden_intersection_hi,
            'weighted_golden_intersection_width': self.weighted_golden_intersection_width,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'nodes': [node.to_dict() for node in self.nodes],
        }


def _pair_interval_intersection(lo_a: float | None, hi_a: float | None, lo_b: float | None, hi_b: float | None) -> tuple[float | None, float | None, float | None]:
    if lo_a is None or hi_a is None or lo_b is None or hi_b is None:
        return None, None, None
    lo = max(float(lo_a), float(lo_b))
    hi = min(float(hi_a), float(hi_b))
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _nonincreasing(values: list[float], tol: float = 1e-15) -> bool:
    return all(float(values[i]) >= float(values[i + 1]) - tol for i in range(len(values) - 1))


def _safe_step_beta(radius_a: float, radius_b: float) -> float | None:
    if radius_a <= 0.0 or radius_b <= 0.0 or radius_b >= radius_a:
        return None
    beta = log(float(radius_a / radius_b)) / log(_PHI)
    if not isfinite(beta) or beta <= 0.0:
        return None
    return float(beta)


def _normalize_positive(value: float | None) -> float:
    if value is None or value <= 0.0 or not isfinite(float(value)):
        return 0.0
    x = float(value)
    return float(x / (1.0 + x))


def _normalize_contraction(value: float | None) -> float:
    if value is None or not isfinite(float(value)):
        return 0.0
    x = float(value)
    return float(max(0.0, min(1.0, 1.0 - x)))


def _node_transport_strength(transport_node: dict[str, Any]) -> float:
    comps: list[float] = []
    comps.append(_normalize_positive(transport_node.get('derivative_floor')))
    comps.append(_normalize_positive(transport_node.get('slope_center_inf')))
    comps.append(_normalize_contraction(transport_node.get('interval_tangent_contraction')))
    if transport_node.get('derivative_backed'):
        comps.append(1.0)
    if transport_node.get('tangent_inclusion_success') or transport_node.get('interval_tangent_success'):
        comps.append(1.0)
    return float(sum(comps) / len(comps)) if comps else 0.0


def build_transport_slope_weighted_golden_rate_certificate(
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
) -> TransportSlopeWeightedGoldenRateCertificate:
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
        return TransportSlopeWeightedGoldenRateCertificate(
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
            transport_strength_min=None,
            transport_strength_mean=None,
            transport_strength_max=None,
            observed_weighted_step_beta_min=None,
            observed_weighted_step_beta_mean=None,
            observed_weighted_step_beta_max=None,
            chosen_weighted_step_exponent=None,
            weighted_step_exponent_safety_factor=float(rate_exponent_safety_factor),
            weighted_golden_normalized_tail_constant=None,
            weighted_tail_nonincreasing=False,
            actual_tail_dominated_by_weighted_rate=False,
            actual_total_dominated_by_weighted_rate=False,
            first_weighted_tail_radius=None,
            last_weighted_tail_radius=None,
            mean_weighted_tail_radius=None,
            selected_weighted_interval_lo=None,
            selected_weighted_interval_hi=None,
            selected_weighted_interval_width=None,
            weighted_golden_intersection_lo=None,
            weighted_golden_intersection_hi=None,
            weighted_golden_intersection_width=None,
            theorem_status='transport-slope-weighted-golden-rate-insufficient',
            notes='Need at least two common certified/transport convergents to build a transport-slope weighted phi-step law.',
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

    node_strengths = [_node_transport_strength(trans_by_q[int(node['q'])]) for node in common_nodes]
    weighted_betas: list[float] = []
    edge_strengths: list[float] = []
    for i in range(len(common_nodes) - 1):
        a = common_nodes[i]
        b = common_nodes[i + 1]
        raw_beta = _safe_step_beta(float(a['tail_modulus_radius']), float(b['tail_modulus_radius']))
        edge_strength = min(node_strengths[i], node_strengths[i + 1])
        edge_strengths.append(edge_strength)
        if raw_beta is None:
            continue
        multiplier = 1.0 + float(transport_strength_boost) * edge_strength
        weighted_betas.append(float(raw_beta * multiplier))

    base_beta = golden.get('chosen_step_exponent')
    chosen_beta = None
    if weighted_betas:
        chosen_beta = min(weighted_betas) * float(rate_exponent_safety_factor)
        if base_beta is not None:
            chosen_beta = max(float(base_beta), float(chosen_beta))
        chosen_beta = max(float(min_step_exponent), float(chosen_beta))
        chosen_beta = min(float(max_rate_exponent), float(chosen_beta))

    if chosen_beta is None:
        return TransportSlopeWeightedGoldenRateCertificate(
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
            transport_strength_min=min(edge_strengths) if edge_strengths else None,
            transport_strength_mean=mean(edge_strengths) if edge_strengths else None,
            transport_strength_max=max(edge_strengths) if edge_strengths else None,
            observed_weighted_step_beta_min=min(weighted_betas) if weighted_betas else None,
            observed_weighted_step_beta_mean=mean(weighted_betas) if weighted_betas else None,
            observed_weighted_step_beta_max=max(weighted_betas) if weighted_betas else None,
            chosen_weighted_step_exponent=None,
            weighted_step_exponent_safety_factor=float(rate_exponent_safety_factor),
            weighted_golden_normalized_tail_constant=None,
            weighted_tail_nonincreasing=False,
            actual_tail_dominated_by_weighted_rate=False,
            actual_total_dominated_by_weighted_rate=False,
            first_weighted_tail_radius=None,
            last_weighted_tail_radius=None,
            mean_weighted_tail_radius=None,
            selected_weighted_interval_lo=None,
            selected_weighted_interval_hi=None,
            selected_weighted_interval_width=None,
            weighted_golden_intersection_lo=None,
            weighted_golden_intersection_hi=None,
            weighted_golden_intersection_width=None,
            theorem_status='transport-slope-weighted-golden-rate-insufficient',
            notes='Observed certified tail radii did not yield a positive transport-slope weighted phi-step decay exponent.',
            nodes=[],
        )

    scales = []
    current_scale = 1.0
    for i in range(len(common_nodes)):
        if i == 0:
            current_scale = 1.0
        else:
            current_scale *= _PHI ** float(chosen_beta)
        scales.append(float(current_scale))

    weighted_constant = max(float(node['tail_modulus_radius']) * scale for node, scale in zip(common_nodes, scales))

    nodes: list[TransportSlopeWeightedGoldenRateNode] = []
    weighted_tail_radii: list[float] = []
    weighted_total_radii: list[float] = []
    selected_lo = None
    selected_hi = None
    actual_tail_dominated = True
    actual_total_dominated = True
    for i, (node, scale) in enumerate(zip(common_nodes, scales)):
        transport_node = trans_by_q[int(node['q'])]
        weighted_tail = float(weighted_constant / scale)
        weighted_total = float(weighted_tail + float(node['local_radius']))
        lo = float(node['transport_center']) - weighted_total
        hi = float(node['transport_center']) + weighted_total
        if selected_lo is None or selected_hi is None:
            selected_lo, selected_hi = lo, hi
        else:
            selected_lo, selected_hi, _ = _pair_interval_intersection(selected_lo, selected_hi, lo, hi)
        actual_tail = float(node['tail_modulus_radius'])
        actual_total = float(node['total_cauchy_radius'])
        actual_tail_dominated &= actual_tail <= weighted_tail + 1e-15
        actual_total_dominated &= actual_total <= weighted_total + 1e-15
        weighted_tail_radii.append(weighted_tail)
        weighted_total_radii.append(weighted_total)
        strength_to_next = edge_strengths[i] if i < len(edge_strengths) else None
        beta_to_next = weighted_betas[i] if i < len(weighted_betas) else None
        nodes.append(
            TransportSlopeWeightedGoldenRateNode(
                start_index=int(node['start_index']),
                label=str(node['label']),
                p=int(node['p']),
                q=int(node['q']),
                golden_depth=int(i),
                transport_center=float(node['transport_center']),
                local_radius=float(node['local_radius']),
                actual_tail_modulus_radius=actual_tail,
                actual_total_cauchy_radius=actual_total,
                weighted_golden_tail_modulus_radius=weighted_tail,
                weighted_golden_total_cauchy_radius=weighted_total,
                weighted_interval_lo=float(lo),
                weighted_interval_hi=float(hi),
                weighted_interval_width=float(hi - lo),
                transport_strength_to_next=None if strength_to_next is None else float(strength_to_next),
                weighted_step_exponent_to_next=None if beta_to_next is None else float(beta_to_next),
                derivative_floor=transport_node.get('derivative_floor'),
                slope_center_inf=transport_node.get('slope_center_inf'),
                interval_tangent_contraction=transport_node.get('interval_tangent_contraction'),
                derivative_backed=bool(transport_node.get('derivative_backed', False)),
                tangent_backed=bool(transport_node.get('tangent_inclusion_success') or transport_node.get('interval_tangent_success')),
            )
        )

    selected_width = None if selected_lo is None or selected_hi is None else float(selected_hi - selected_lo)
    golden_lo = golden.get('rate_golden_intersection_lo')
    golden_hi = golden.get('rate_golden_intersection_hi')
    wgi_lo, wgi_hi, wgi_w = _pair_interval_intersection(selected_lo, selected_hi, golden_lo, golden_hi)

    if (
        selected_lo is not None
        and selected_hi is not None
        and wgi_lo is not None
        and wgi_hi is not None
        and exact_recurrence
        and actual_tail_dominated
        and actual_total_dominated
        and _nonincreasing(weighted_tail_radii)
    ):
        status = 'transport-slope-weighted-golden-rate-strong'
        notes = (
            'The golden/Fibonacci-normalized tail law remains compatible with the earlier recurrence-aware interval after weighting the phi-step decay by conservative continuation strength extracted from derivative floors, branch-tube slope data, and tangent-contraction support.'
        )
    elif selected_lo is not None and selected_hi is not None:
        status = 'transport-slope-weighted-golden-rate-partial'
        notes = (
            'A transport-slope weighted phi-step tail law can be built and yields a common interval, but recurrence, domination, or compatibility with the earlier golden recurrence law are not yet fully strong.'
        )
    else:
        status = 'transport-slope-weighted-golden-rate-incomplete'
        notes = 'The transport-slope weighted recurrence-aware tail law did not yield a stable common interval.'

    return TransportSlopeWeightedGoldenRateCertificate(
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
        transport_strength_min=min(edge_strengths) if edge_strengths else None,
        transport_strength_mean=mean(edge_strengths) if edge_strengths else None,
        transport_strength_max=max(edge_strengths) if edge_strengths else None,
        observed_weighted_step_beta_min=min(weighted_betas) if weighted_betas else None,
        observed_weighted_step_beta_mean=mean(weighted_betas) if weighted_betas else None,
        observed_weighted_step_beta_max=max(weighted_betas) if weighted_betas else None,
        chosen_weighted_step_exponent=float(chosen_beta),
        weighted_step_exponent_safety_factor=float(rate_exponent_safety_factor),
        weighted_golden_normalized_tail_constant=float(weighted_constant),
        weighted_tail_nonincreasing=_nonincreasing(weighted_tail_radii),
        actual_tail_dominated_by_weighted_rate=actual_tail_dominated,
        actual_total_dominated_by_weighted_rate=actual_total_dominated,
        first_weighted_tail_radius=weighted_tail_radii[0] if weighted_tail_radii else None,
        last_weighted_tail_radius=weighted_tail_radii[-1] if weighted_tail_radii else None,
        mean_weighted_tail_radius=mean(weighted_tail_radii) if weighted_tail_radii else None,
        selected_weighted_interval_lo=selected_lo,
        selected_weighted_interval_hi=selected_hi,
        selected_weighted_interval_width=selected_width,
        weighted_golden_intersection_lo=wgi_lo,
        weighted_golden_intersection_hi=wgi_hi,
        weighted_golden_intersection_width=wgi_w,
        theorem_status=status,
        notes=notes,
        nodes=nodes,
    )


__all__ = [
    'TransportSlopeWeightedGoldenRateCertificate',
    'TransportSlopeWeightedGoldenRateNode',
    'build_transport_slope_weighted_golden_rate_certificate',
]
