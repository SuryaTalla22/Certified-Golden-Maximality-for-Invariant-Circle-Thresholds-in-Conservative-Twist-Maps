from __future__ import annotations

"""Rate-aware certified tail modulus for the convergent-family bridge.

This layer upgrades the start-index tail modulus into an explicit denominator-scale
rate profile.  The previous stage exposed a monotone map from ladder depth to
remaining tail radius.  What was still missing was a quantitative law tying that
radius to the arithmetic scale of the convergents themselves.

The present module extracts a conservative exponent ``alpha`` from the certified
chain, normalizes each tail budget by ``q**alpha``, and builds a rate-aware Cauchy
family

    remaining tail radius <= C / q**alpha.

The result is not yet a theorem-grade convergence rate, but it is the first
bundle layer that presents the irrational-limit bridge as an explicit function of
ladder scale rather than merely of suffix depth.
"""

from dataclasses import asdict, dataclass
from math import isfinite, log
from statistics import mean
from typing import Any

from .certified_tail_modulus_control import build_certified_tail_modulus_certificate
from .transport_certified_limit_control import _interval_intersection


def _pair_interval_intersection(
    lo_a: float | None,
    hi_a: float | None,
    lo_b: float | None,
    hi_b: float | None,
) -> tuple[float | None, float | None, float | None]:
    if lo_a is None or hi_a is None or lo_b is None or hi_b is None:
        return None, None, None
    lo = max(float(lo_a), float(lo_b))
    hi = min(float(hi_a), float(hi_b))
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


@dataclass
class RateAwareTailModulusNode:
    start_index: int
    label: str
    p: int
    q: int
    transport_center: float
    local_radius: float
    actual_tail_modulus_radius: float
    actual_total_cauchy_radius: float
    rate_tail_modulus_radius: float
    rate_total_cauchy_radius: float
    rate_interval_lo: float
    rate_interval_hi: float
    rate_interval_width: float
    q_growth_to_next: float | None
    observed_alpha_to_next: float | None
    edge_normalized_tail_modulus: float
    edge_normalized_triple_reinforced: float
    edge_normalized_pair_anchored: float
    edge_normalized_transport_fallback: float
    edge_normalized_geometric_tail: float
    derivative_backed: bool
    tangent_backed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RateAwareTailModulusCertificate:
    rho_target: float | None
    family_label: str | None
    entry_count: int
    usable_entry_count: int
    chain_labels: list[str]
    chain_qs: list[int]
    chain_ps: list[int]
    chain_length: int
    chosen_rate_exponent: float | None
    rate_exponent_safety_factor: float
    observed_alpha_min: float | None
    observed_alpha_mean: float | None
    observed_alpha_max: float | None
    normalized_tail_constant: float | None
    normalized_triple_constant: float | None
    normalized_pair_constant: float | None
    normalized_fallback_constant: float | None
    normalized_geometric_constant: float | None
    rate_tail_nonincreasing: bool
    edge_normalized_tail_bounded: bool
    classwise_edge_normalized_bounded: bool
    actual_tail_dominated_by_rate: bool
    actual_total_dominated_by_rate: bool
    first_rate_tail_radius: float | None
    last_rate_tail_radius: float | None
    mean_rate_tail_radius: float | None
    first_rate_total_radius: float | None
    last_rate_total_radius: float | None
    mean_rate_total_radius: float | None
    selected_rate_interval_lo: float | None
    selected_rate_interval_hi: float | None
    selected_rate_interval_width: float | None
    modulus_rate_intersection_lo: float | None
    modulus_rate_intersection_hi: float | None
    modulus_rate_intersection_width: float | None
    theorem_status: str
    notes: str
    nodes: list[RateAwareTailModulusNode]

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
            'chosen_rate_exponent': self.chosen_rate_exponent,
            'rate_exponent_safety_factor': float(self.rate_exponent_safety_factor),
            'observed_alpha_min': self.observed_alpha_min,
            'observed_alpha_mean': self.observed_alpha_mean,
            'observed_alpha_max': self.observed_alpha_max,
            'normalized_tail_constant': self.normalized_tail_constant,
            'normalized_triple_constant': self.normalized_triple_constant,
            'normalized_pair_constant': self.normalized_pair_constant,
            'normalized_fallback_constant': self.normalized_fallback_constant,
            'normalized_geometric_constant': self.normalized_geometric_constant,
            'rate_tail_nonincreasing': bool(self.rate_tail_nonincreasing),
            'edge_normalized_tail_bounded': bool(self.edge_normalized_tail_bounded),
            'classwise_edge_normalized_bounded': bool(self.classwise_edge_normalized_bounded),
            'actual_tail_dominated_by_rate': bool(self.actual_tail_dominated_by_rate),
            'actual_total_dominated_by_rate': bool(self.actual_total_dominated_by_rate),
            'first_rate_tail_radius': self.first_rate_tail_radius,
            'last_rate_tail_radius': self.last_rate_tail_radius,
            'mean_rate_tail_radius': self.mean_rate_tail_radius,
            'first_rate_total_radius': self.first_rate_total_radius,
            'last_rate_total_radius': self.last_rate_total_radius,
            'mean_rate_total_radius': self.mean_rate_total_radius,
            'selected_rate_interval_lo': self.selected_rate_interval_lo,
            'selected_rate_interval_hi': self.selected_rate_interval_hi,
            'selected_rate_interval_width': self.selected_rate_interval_width,
            'modulus_rate_intersection_lo': self.modulus_rate_intersection_lo,
            'modulus_rate_intersection_hi': self.modulus_rate_intersection_hi,
            'modulus_rate_intersection_width': self.modulus_rate_intersection_width,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'nodes': [n.to_dict() for n in self.nodes],
        }


def _nonincreasing(values: list[float], tol: float = 1e-15) -> bool:
    return all(float(values[i]) >= float(values[i + 1]) - tol for i in range(len(values) - 1))


def _max_or_none(values: list[float]) -> float | None:
    return None if not values else float(max(values))


def _safe_alpha(radius_a: float, radius_b: float, q_a: int, q_b: int) -> float | None:
    if radius_a <= 0.0 or radius_b <= 0.0 or q_a <= 0 or q_b <= q_a:
        return None
    ratio_r = float(radius_a / radius_b)
    ratio_q = float(q_b / q_a)
    if ratio_r <= 1.0 or ratio_q <= 1.0:
        return None
    alpha = log(ratio_r) / log(ratio_q)
    if not isfinite(alpha) or alpha <= 0.0:
        return None
    return float(alpha)


def build_rate_aware_tail_modulus_certificate(
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
) -> RateAwareTailModulusCertificate:
    base = build_certified_tail_modulus_certificate(
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

    raw_nodes = list(base.get('nodes', []) or [])
    if len(raw_nodes) < 2:
        return RateAwareTailModulusCertificate(
            rho_target=rho_target,
            family_label=family_label,
            entry_count=int(base.get('entry_count', 0) or 0),
            usable_entry_count=int(base.get('usable_entry_count', 0) or 0),
            chain_labels=[str(x) for x in base.get('chain_labels', [])],
            chain_qs=[int(x) for x in base.get('chain_qs', [])],
            chain_ps=[int(x) for x in base.get('chain_ps', [])],
            chain_length=int(base.get('chain_length', 0) or 0),
            chosen_rate_exponent=None,
            rate_exponent_safety_factor=float(rate_exponent_safety_factor),
            observed_alpha_min=None,
            observed_alpha_mean=None,
            observed_alpha_max=None,
            normalized_tail_constant=None,
            normalized_triple_constant=None,
            normalized_pair_constant=None,
            normalized_fallback_constant=None,
            normalized_geometric_constant=None,
            rate_tail_nonincreasing=False,
            edge_normalized_tail_bounded=False,
            classwise_edge_normalized_bounded=False,
            actual_tail_dominated_by_rate=False,
            actual_total_dominated_by_rate=False,
            first_rate_tail_radius=None,
            last_rate_tail_radius=None,
            mean_rate_tail_radius=None,
            first_rate_total_radius=None,
            last_rate_total_radius=None,
            mean_rate_total_radius=None,
            selected_rate_interval_lo=None,
            selected_rate_interval_hi=None,
            selected_rate_interval_width=None,
            modulus_rate_intersection_lo=None,
            modulus_rate_intersection_hi=None,
            modulus_rate_intersection_width=None,
            theorem_status='rate-aware-tail-modulus-incomplete',
            notes='The certified tail modulus did not yet supply enough convergents to estimate a denominator-scale rate profile.',
            nodes=[],
        )

    alphas: list[float] = []
    for a, b in zip(raw_nodes[:-1], raw_nodes[1:]):
        alpha = _safe_alpha(float(a.get('tail_modulus_radius', 0.0) or 0.0), float(b.get('tail_modulus_radius', 0.0) or 0.0), int(a.get('q', 0) or 0), int(b.get('q', 0) or 0))
        if alpha is not None:
            alphas.append(alpha)

    if not alphas:
        return RateAwareTailModulusCertificate(
            rho_target=rho_target,
            family_label=family_label,
            entry_count=int(base.get('entry_count', 0) or 0),
            usable_entry_count=int(base.get('usable_entry_count', 0) or 0),
            chain_labels=[str(x) for x in base.get('chain_labels', [])],
            chain_qs=[int(x) for x in base.get('chain_qs', [])],
            chain_ps=[int(x) for x in base.get('chain_ps', [])],
            chain_length=int(base.get('chain_length', 0) or 0),
            chosen_rate_exponent=None,
            rate_exponent_safety_factor=float(rate_exponent_safety_factor),
            observed_alpha_min=None,
            observed_alpha_mean=None,
            observed_alpha_max=None,
            normalized_tail_constant=None,
            normalized_triple_constant=None,
            normalized_pair_constant=None,
            normalized_fallback_constant=None,
            normalized_geometric_constant=None,
            rate_tail_nonincreasing=False,
            edge_normalized_tail_bounded=False,
            classwise_edge_normalized_bounded=False,
            actual_tail_dominated_by_rate=False,
            actual_total_dominated_by_rate=False,
            first_rate_tail_radius=None,
            last_rate_tail_radius=None,
            mean_rate_tail_radius=None,
            first_rate_total_radius=None,
            last_rate_total_radius=None,
            mean_rate_total_radius=None,
            selected_rate_interval_lo=None,
            selected_rate_interval_hi=None,
            selected_rate_interval_width=None,
            modulus_rate_intersection_lo=None,
            modulus_rate_intersection_hi=None,
            modulus_rate_intersection_width=None,
            theorem_status='rate-aware-tail-modulus-incomplete',
            notes='No positive denominator-scale decay exponent could be extracted from the certified modulus chain.',
            nodes=[],
        )

    observed_alpha_min = float(min(alphas))
    observed_alpha_mean = float(mean(alphas))
    observed_alpha_max = float(max(alphas))
    chosen_alpha = float(max(min_rate_exponent, min(max_rate_exponent, rate_exponent_safety_factor * observed_alpha_min)))

    normalized_tail_constant = 0.0
    normalized_triple_constant = 0.0
    normalized_pair_constant = 0.0
    normalized_fallback_constant = 0.0
    normalized_geometric_constant = 0.0
    for raw in raw_nodes:
        q = int(raw.get('q', 1) or 1)
        scale = float(q ** chosen_alpha)
        normalized_tail_constant = max(normalized_tail_constant, float(raw.get('tail_modulus_radius', 0.0) or 0.0) * scale)
        normalized_triple_constant = max(normalized_triple_constant, float(raw.get('tail_modulus_triple_reinforced', 0.0) or 0.0) * scale)
        normalized_pair_constant = max(normalized_pair_constant, float(raw.get('tail_modulus_pair_anchored', 0.0) or 0.0) * scale)
        normalized_fallback_constant = max(normalized_fallback_constant, float(raw.get('tail_modulus_transport_fallback', 0.0) or 0.0) * scale)
        normalized_geometric_constant = max(normalized_geometric_constant, float(raw.get('tail_modulus_geometric_tail', 0.0) or 0.0) * scale)

    nodes: list[RateAwareTailModulusNode] = []
    rate_tail_radii: list[float] = []
    rate_total_radii: list[float] = []
    rate_intervals: list[tuple[float, float]] = []
    actual_tail_dominated = True
    actual_total_dominated = True
    for idx, raw in enumerate(raw_nodes):
        q = int(raw.get('q', 1) or 1)
        scale = float(q ** chosen_alpha)
        tail_actual = float(raw.get('tail_modulus_radius', 0.0) or 0.0)
        total_actual = float(raw.get('total_cauchy_radius', 0.0) or 0.0)
        local_radius = float(raw.get('local_radius', 0.0) or 0.0)
        rate_tail = float(normalized_tail_constant / max(scale, 1e-15))
        rate_total = float(local_radius + rate_tail)
        center = float(raw.get('transport_center', 0.0) or 0.0)
        lo = float(center - rate_total)
        hi = float(center + rate_total)
        rate_intervals.append((lo, hi))
        actual_tail_dominated = actual_tail_dominated and (tail_actual <= rate_tail + 1e-15)
        actual_total_dominated = actual_total_dominated and (total_actual <= rate_total + 1e-15)
        q_growth = None
        alpha_next = None
        if idx + 1 < len(raw_nodes):
            q_next = int(raw_nodes[idx + 1].get('q', q) or q)
            q_growth = None if q <= 0 else float(q_next / q)
            alpha_next = _safe_alpha(tail_actual, float(raw_nodes[idx + 1].get('tail_modulus_radius', 0.0) or 0.0), q, q_next)
        rate_tail_radii.append(rate_tail)
        rate_total_radii.append(rate_total)
        nodes.append(RateAwareTailModulusNode(
            start_index=int(raw.get('start_index', idx) or idx),
            label=str(raw.get('label')),
            p=int(raw.get('p', 0) or 0),
            q=q,
            transport_center=center,
            local_radius=local_radius,
            actual_tail_modulus_radius=tail_actual,
            actual_total_cauchy_radius=total_actual,
            rate_tail_modulus_radius=rate_tail,
            rate_total_cauchy_radius=rate_total,
            rate_interval_lo=lo,
            rate_interval_hi=hi,
            rate_interval_width=float(hi - lo),
            q_growth_to_next=q_growth,
            observed_alpha_to_next=alpha_next,
            edge_normalized_tail_modulus=float(tail_actual * scale),
            edge_normalized_triple_reinforced=float(raw.get('tail_modulus_triple_reinforced', 0.0) or 0.0) * scale,
            edge_normalized_pair_anchored=float(raw.get('tail_modulus_pair_anchored', 0.0) or 0.0) * scale,
            edge_normalized_transport_fallback=float(raw.get('tail_modulus_transport_fallback', 0.0) or 0.0) * scale,
            edge_normalized_geometric_tail=float(raw.get('tail_modulus_geometric_tail', 0.0) or 0.0) * scale,
            derivative_backed=bool(raw.get('derivative_backed')),
            tangent_backed=bool(raw.get('tangent_backed')),
        ))

    rate_inter_lo, rate_inter_hi, rate_inter_w = _interval_intersection(rate_intervals)
    mod_lo = base.get('selected_limit_interval_lo')
    mod_hi = base.get('selected_limit_interval_hi')
    both_lo, both_hi, both_w = _pair_interval_intersection(rate_inter_lo, rate_inter_hi, mod_lo, mod_hi)

    rate_nonincreasing = _nonincreasing(rate_tail_radii)
    edge_normalized_tail_bounded = all(float(n.edge_normalized_tail_modulus) <= normalized_tail_constant + 1e-12 for n in nodes)
    classwise_edge_normalized_bounded = all(
        max(getattr(n, attr) for n in nodes) <= const + 1e-12
        for attr, const in (
            ('edge_normalized_triple_reinforced', normalized_triple_constant),
            ('edge_normalized_pair_anchored', normalized_pair_constant),
            ('edge_normalized_transport_fallback', normalized_fallback_constant),
            ('edge_normalized_geometric_tail', normalized_geometric_constant),
        )
    )

    strong = (
        str(base.get('theorem_status', '')).startswith('certified-tail-modulus-strong')
        and chosen_alpha >= min_rate_exponent
        and actual_tail_dominated
        and actual_total_dominated
        and rate_nonincreasing
        and edge_normalized_tail_bounded
        and classwise_edge_normalized_bounded
        and both_lo is not None
    )
    partial = both_lo is not None and actual_tail_dominated and rate_nonincreasing
    if strong:
        status = 'rate-aware-tail-modulus-strong'
        notes = (
            'The certified tail modulus has been upgraded to a denominator-scale law. '
            'A conservative exponent was extracted from the certified chain, each tail component admits a bounded q^alpha-normalization, '
            'and the resulting rate-aware Cauchy intervals remain compatible with the underlying certified modulus.'
        )
    elif partial:
        status = 'rate-aware-tail-modulus-partial'
        notes = (
            'A conservative denominator-scale rate profile exists and dominates the certified tail modulus, '
            'but the full set of normalization or compatibility checks is not yet strong enough to treat it as a robust quantitative convergence law.'
        )
    else:
        status = 'rate-aware-tail-modulus-incomplete'
        notes = 'The denominator-scale normalization did not yet produce a usable rate-aware upgrade of the certified tail modulus.'

    return RateAwareTailModulusCertificate(
        rho_target=rho_target,
        family_label=family_label,
        entry_count=int(base.get('entry_count', 0) or 0),
        usable_entry_count=int(base.get('usable_entry_count', 0) or 0),
        chain_labels=[str(x) for x in base.get('chain_labels', [])],
        chain_qs=[int(x) for x in base.get('chain_qs', [])],
        chain_ps=[int(x) for x in base.get('chain_ps', [])],
        chain_length=int(base.get('chain_length', 0) or 0),
        chosen_rate_exponent=chosen_alpha,
        rate_exponent_safety_factor=float(rate_exponent_safety_factor),
        observed_alpha_min=observed_alpha_min,
        observed_alpha_mean=observed_alpha_mean,
        observed_alpha_max=observed_alpha_max,
        normalized_tail_constant=float(normalized_tail_constant),
        normalized_triple_constant=float(normalized_triple_constant),
        normalized_pair_constant=float(normalized_pair_constant),
        normalized_fallback_constant=float(normalized_fallback_constant),
        normalized_geometric_constant=float(normalized_geometric_constant),
        rate_tail_nonincreasing=bool(rate_nonincreasing),
        edge_normalized_tail_bounded=bool(edge_normalized_tail_bounded),
        classwise_edge_normalized_bounded=bool(classwise_edge_normalized_bounded),
        actual_tail_dominated_by_rate=bool(actual_tail_dominated),
        actual_total_dominated_by_rate=bool(actual_total_dominated),
        first_rate_tail_radius=(None if not rate_tail_radii else float(rate_tail_radii[0])),
        last_rate_tail_radius=(None if not rate_tail_radii else float(rate_tail_radii[-1])),
        mean_rate_tail_radius=(None if not rate_tail_radii else float(mean(rate_tail_radii))),
        first_rate_total_radius=(None if not rate_total_radii else float(rate_total_radii[0])),
        last_rate_total_radius=(None if not rate_total_radii else float(rate_total_radii[-1])),
        mean_rate_total_radius=(None if not rate_total_radii else float(mean(rate_total_radii))),
        selected_rate_interval_lo=rate_inter_lo,
        selected_rate_interval_hi=rate_inter_hi,
        selected_rate_interval_width=rate_inter_w,
        modulus_rate_intersection_lo=both_lo,
        modulus_rate_intersection_hi=both_hi,
        modulus_rate_intersection_width=both_w,
        theorem_status=status,
        notes=notes,
        nodes=nodes,
    )


__all__ = [
    'RateAwareTailModulusNode',
    'RateAwareTailModulusCertificate',
    'build_rate_aware_tail_modulus_certificate',
]
