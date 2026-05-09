from __future__ import annotations

"""Golden/Fibonacci-normalized tail modulus control.

This layer upgrades the denominator-scale rate law into a recurrence-aware law tied
specifically to the golden convergent family.  Instead of expressing the certified
remaining tail radius only as C / q**alpha, we also express it as a function of
ladder depth along a (nearly) Fibonacci recurrence chain:

    remaining tail radius <= C_phi / phi**(beta * depth),

where ``depth`` is the convergent index within the certified tail and ``phi`` is
the golden ratio.  The point is not that this is already the final theorem, but
that the bridge now depends on the recurrence structure of the actual ladder being
used rather than only on denominator size.
"""

from dataclasses import asdict, dataclass
from math import isfinite, log, sqrt
from statistics import mean
from typing import Any

from .certified_tail_modulus_control import build_certified_tail_modulus_certificate
from .rate_aware_tail_modulus_control import build_rate_aware_tail_modulus_certificate

_PHI = 0.5 * (1.0 + sqrt(5.0))


@dataclass
class GoldenRecurrenceRateNode:
    start_index: int
    label: str
    p: int
    q: int
    golden_depth: int
    transport_center: float
    local_radius: float
    actual_tail_modulus_radius: float
    actual_total_cauchy_radius: float
    golden_tail_modulus_radius: float
    golden_total_cauchy_radius: float
    golden_interval_lo: float
    golden_interval_hi: float
    golden_interval_width: float
    q_ratio_to_next: float | None
    q_ratio_defect_from_phi: float | None
    observed_step_beta_to_next: float | None
    golden_normalized_tail_constant: float
    golden_normalized_triple_constant: float
    golden_normalized_pair_constant: float
    golden_normalized_fallback_constant: float
    golden_normalized_geometric_constant: float
    derivative_backed: bool
    tangent_backed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenRecurrenceRateCertificate:
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
    q_ratio_defect_max: float | None
    q_ratio_defect_mean: float | None
    observed_step_beta_min: float | None
    observed_step_beta_mean: float | None
    observed_step_beta_max: float | None
    chosen_step_exponent: float | None
    step_exponent_safety_factor: float
    golden_normalized_tail_constant: float | None
    golden_normalized_triple_constant: float | None
    golden_normalized_pair_constant: float | None
    golden_normalized_fallback_constant: float | None
    golden_normalized_geometric_constant: float | None
    golden_tail_nonincreasing: bool
    actual_tail_dominated_by_golden_rate: bool
    actual_total_dominated_by_golden_rate: bool
    first_golden_tail_radius: float | None
    last_golden_tail_radius: float | None
    mean_golden_tail_radius: float | None
    selected_golden_interval_lo: float | None
    selected_golden_interval_hi: float | None
    selected_golden_interval_width: float | None
    rate_golden_intersection_lo: float | None
    rate_golden_intersection_hi: float | None
    rate_golden_intersection_width: float | None
    theorem_status: str
    notes: str
    nodes: list[GoldenRecurrenceRateNode]

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
            'q_ratio_defect_max': self.q_ratio_defect_max,
            'q_ratio_defect_mean': self.q_ratio_defect_mean,
            'observed_step_beta_min': self.observed_step_beta_min,
            'observed_step_beta_mean': self.observed_step_beta_mean,
            'observed_step_beta_max': self.observed_step_beta_max,
            'chosen_step_exponent': self.chosen_step_exponent,
            'step_exponent_safety_factor': float(self.step_exponent_safety_factor),
            'golden_normalized_tail_constant': self.golden_normalized_tail_constant,
            'golden_normalized_triple_constant': self.golden_normalized_triple_constant,
            'golden_normalized_pair_constant': self.golden_normalized_pair_constant,
            'golden_normalized_fallback_constant': self.golden_normalized_fallback_constant,
            'golden_normalized_geometric_constant': self.golden_normalized_geometric_constant,
            'golden_tail_nonincreasing': bool(self.golden_tail_nonincreasing),
            'actual_tail_dominated_by_golden_rate': bool(self.actual_tail_dominated_by_golden_rate),
            'actual_total_dominated_by_golden_rate': bool(self.actual_total_dominated_by_golden_rate),
            'first_golden_tail_radius': self.first_golden_tail_radius,
            'last_golden_tail_radius': self.last_golden_tail_radius,
            'mean_golden_tail_radius': self.mean_golden_tail_radius,
            'selected_golden_interval_lo': self.selected_golden_interval_lo,
            'selected_golden_interval_hi': self.selected_golden_interval_hi,
            'selected_golden_interval_width': self.selected_golden_interval_width,
            'rate_golden_intersection_lo': self.rate_golden_intersection_lo,
            'rate_golden_intersection_hi': self.rate_golden_intersection_hi,
            'rate_golden_intersection_width': self.rate_golden_intersection_width,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'nodes': [node.to_dict() for node in self.nodes],
        }




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

def _nonincreasing(values: list[float], tol: float = 1e-15) -> bool:
    return all(float(values[i]) >= float(values[i + 1]) - tol for i in range(len(values) - 1))


def _safe_step_beta(radius_a: float, radius_b: float) -> float | None:
    if radius_a <= 0.0 or radius_b <= 0.0 or radius_b >= radius_a:
        return None
    beta = log(float(radius_a / radius_b)) / log(_PHI)
    if not isfinite(beta) or beta <= 0.0:
        return None
    return float(beta)


def build_golden_recurrence_rate_certificate(
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
) -> GoldenRecurrenceRateCertificate:
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
    rate = build_rate_aware_tail_modulus_certificate(
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

    certified_nodes = list(certified.get('nodes', []) or [])
    rate_nodes = list(rate.get('nodes', []) or [])
    usable = min(len(certified_nodes), len(rate_nodes))
    if usable < 2:
        return GoldenRecurrenceRateCertificate(
            rho_target=rho_target,
            family_label=family_label,
            entry_count=int(certified.get('entry_count', 0) or 0),
            usable_entry_count=usable,
            chain_labels=[str(x) for x in certified.get('chain_labels', [])],
            chain_qs=[int(x) for x in certified.get('chain_qs', [])],
            chain_ps=[int(x) for x in certified.get('chain_ps', [])],
            chain_length=int(certified.get('chain_length', 0) or 0),
            exact_fibonacci_recurrence=False,
            q_recurrence_max_defect=0,
            p_recurrence_max_defect=0,
            q_ratio_defect_max=None,
            q_ratio_defect_mean=None,
            observed_step_beta_min=None,
            observed_step_beta_mean=None,
            observed_step_beta_max=None,
            chosen_step_exponent=None,
            step_exponent_safety_factor=float(rate_exponent_safety_factor),
            golden_normalized_tail_constant=None,
            golden_normalized_triple_constant=None,
            golden_normalized_pair_constant=None,
            golden_normalized_fallback_constant=None,
            golden_normalized_geometric_constant=None,
            golden_tail_nonincreasing=False,
            actual_tail_dominated_by_golden_rate=False,
            actual_total_dominated_by_golden_rate=False,
            first_golden_tail_radius=None,
            last_golden_tail_radius=None,
            mean_golden_tail_radius=None,
            selected_golden_interval_lo=None,
            selected_golden_interval_hi=None,
            selected_golden_interval_width=None,
            rate_golden_intersection_lo=None,
            rate_golden_intersection_hi=None,
            rate_golden_intersection_width=None,
            theorem_status='golden-recurrence-rate-insufficient',
            notes='Need at least two certified convergents to build a golden/Fibonacci-normalized tail law.',
            nodes=[],
        )

    certified_nodes = certified_nodes[:usable]
    rate_nodes = rate_nodes[:usable]
    qs = [int(node['q']) for node in certified_nodes]
    ps = [int(node['p']) for node in certified_nodes]
    labels = [str(node['label']) for node in certified_nodes]

    q_rec_defects: list[int] = []
    p_rec_defects: list[int] = []
    q_ratio_defects: list[float] = []
    observed_betas: list[float] = []
    for i in range(usable - 1):
        q_ratio = float(qs[i + 1] / qs[i]) if qs[i] > 0 else float('nan')
        if isfinite(q_ratio):
            q_ratio_defects.append(abs(q_ratio - _PHI))
        beta = _safe_step_beta(
            float(certified_nodes[i]['tail_modulus_radius']),
            float(certified_nodes[i + 1]['tail_modulus_radius']),
        )
        if beta is not None:
            observed_betas.append(beta)
    for i in range(2, usable):
        q_rec_defects.append(abs(int(qs[i]) - int(qs[i - 1]) - int(qs[i - 2])))
        p_rec_defects.append(abs(int(ps[i]) - int(ps[i - 1]) - int(ps[i - 2])))

    penalty = 1.0 + (max(q_ratio_defects) if q_ratio_defects else 0.0)
    if observed_betas:
        chosen_beta = min(observed_betas) * float(rate_exponent_safety_factor) / penalty
        chosen_beta = max(float(min_step_exponent), chosen_beta)
        chosen_beta = min(float(max_rate_exponent), chosen_beta)
    else:
        chosen_beta = None

    if chosen_beta is None:
        return GoldenRecurrenceRateCertificate(
            rho_target=rho_target,
            family_label=family_label,
            entry_count=int(certified.get('entry_count', 0) or 0),
            usable_entry_count=usable,
            chain_labels=labels,
            chain_qs=qs,
            chain_ps=ps,
            chain_length=usable,
            exact_fibonacci_recurrence=False,
            q_recurrence_max_defect=max(q_rec_defects) if q_rec_defects else 0,
            p_recurrence_max_defect=max(p_rec_defects) if p_rec_defects else 0,
            q_ratio_defect_max=max(q_ratio_defects) if q_ratio_defects else None,
            q_ratio_defect_mean=mean(q_ratio_defects) if q_ratio_defects else None,
            observed_step_beta_min=min(observed_betas) if observed_betas else None,
            observed_step_beta_mean=mean(observed_betas) if observed_betas else None,
            observed_step_beta_max=max(observed_betas) if observed_betas else None,
            chosen_step_exponent=None,
            step_exponent_safety_factor=float(rate_exponent_safety_factor),
            golden_normalized_tail_constant=None,
            golden_normalized_triple_constant=None,
            golden_normalized_pair_constant=None,
            golden_normalized_fallback_constant=None,
            golden_normalized_geometric_constant=None,
            golden_tail_nonincreasing=False,
            actual_tail_dominated_by_golden_rate=False,
            actual_total_dominated_by_golden_rate=False,
            first_golden_tail_radius=None,
            last_golden_tail_radius=None,
            mean_golden_tail_radius=None,
            selected_golden_interval_lo=None,
            selected_golden_interval_hi=None,
            selected_golden_interval_width=None,
            rate_golden_intersection_lo=None,
            rate_golden_intersection_hi=None,
            rate_golden_intersection_width=None,
            theorem_status='golden-recurrence-rate-insufficient',
            notes='Observed tail radii did not yield a positive golden-step decay exponent.',
            nodes=[],
        )

    tail_constants: list[float] = []
    triple_constants: list[float] = []
    pair_constants: list[float] = []
    fallback_constants: list[float] = []
    geometric_constants: list[float] = []
    for i, cert_node in enumerate(certified_nodes):
        scale = _PHI ** (float(chosen_beta) * float(i))
        tail_constants.append(float(cert_node['tail_modulus_radius']) * scale)
        triple_constants.append(float(cert_node['tail_modulus_triple_reinforced']) * scale)
        pair_constants.append(float(cert_node['tail_modulus_pair_anchored']) * scale)
        fallback_constants.append(float(cert_node['tail_modulus_transport_fallback']) * scale)
        geometric_constants.append(float(cert_node['tail_modulus_geometric_tail']) * scale)

    tail_constant = max(tail_constants)
    triple_constant = max(triple_constants)
    pair_constant = max(pair_constants)
    fallback_constant = max(fallback_constants)
    geometric_constant = max(geometric_constants)

    nodes: list[GoldenRecurrenceRateNode] = []
    golden_tail_radii: list[float] = []
    golden_total_radii: list[float] = []
    selected_lo = None
    selected_hi = None
    actual_tail_dominated = True
    actual_total_dominated = True
    for i, (cert_node, rate_node) in enumerate(zip(certified_nodes, rate_nodes)):
        depth = int(i)
        scale = _PHI ** (float(chosen_beta) * float(depth))
        golden_tail = float(tail_constant / scale)
        golden_total = float(golden_tail + float(cert_node['local_radius']))
        lo = float(cert_node['transport_center']) - golden_total
        hi = float(cert_node['transport_center']) + golden_total
        width = float(hi - lo)
        if selected_lo is None or selected_hi is None:
            selected_lo, selected_hi = lo, hi
        else:
            selected_lo, selected_hi, _ = _pair_interval_intersection(selected_lo, selected_hi, lo, hi)
        actual_tail = float(cert_node['tail_modulus_radius'])
        actual_total = float(cert_node['total_cauchy_radius'])
        actual_tail_dominated &= actual_tail <= golden_tail + 1e-15
        actual_total_dominated &= actual_total <= golden_total + 1e-15
        golden_tail_radii.append(golden_tail)
        golden_total_radii.append(golden_total)
        q_ratio = None
        q_ratio_defect = None
        beta_to_next = None
        if i + 1 < usable:
            q_ratio = float(qs[i + 1] / qs[i]) if qs[i] > 0 else None
            q_ratio_defect = None if q_ratio is None else abs(float(q_ratio) - _PHI)
            beta_to_next = _safe_step_beta(actual_tail, float(certified_nodes[i + 1]['tail_modulus_radius']))
        nodes.append(
            GoldenRecurrenceRateNode(
                start_index=int(cert_node['start_index']),
                label=str(cert_node['label']),
                p=int(cert_node['p']),
                q=int(cert_node['q']),
                golden_depth=depth,
                transport_center=float(cert_node['transport_center']),
                local_radius=float(cert_node['local_radius']),
                actual_tail_modulus_radius=actual_tail,
                actual_total_cauchy_radius=actual_total,
                golden_tail_modulus_radius=golden_tail,
                golden_total_cauchy_radius=golden_total,
                golden_interval_lo=lo,
                golden_interval_hi=hi,
                golden_interval_width=width,
                q_ratio_to_next=q_ratio,
                q_ratio_defect_from_phi=q_ratio_defect,
                observed_step_beta_to_next=beta_to_next,
                golden_normalized_tail_constant=float(actual_tail * scale),
                golden_normalized_triple_constant=float(cert_node['tail_modulus_triple_reinforced']) * scale,
                golden_normalized_pair_constant=float(cert_node['tail_modulus_pair_anchored']) * scale,
                golden_normalized_fallback_constant=float(cert_node['tail_modulus_transport_fallback']) * scale,
                golden_normalized_geometric_constant=float(cert_node['tail_modulus_geometric_tail']) * scale,
                derivative_backed=bool(rate_node.get('derivative_backed', False)),
                tangent_backed=bool(rate_node.get('tangent_backed', False)),
            )
        )

    selected_width = None if selected_lo is None or selected_hi is None else float(selected_hi - selected_lo)
    rate_lo = rate.get('modulus_rate_intersection_lo')
    rate_hi = rate.get('modulus_rate_intersection_hi')
    rg_lo, rg_hi, rg_w = _pair_interval_intersection(selected_lo, selected_hi, rate_lo, rate_hi)

    exact_recurrence = (max(q_rec_defects) if q_rec_defects else 0) == 0 and (max(p_rec_defects) if p_rec_defects else 0) == 0
    q_ratio_defect_max = max(q_ratio_defects) if q_ratio_defects else None
    if (
        selected_lo is not None
        and selected_hi is not None
        and rg_lo is not None
        and rg_hi is not None
        and exact_recurrence
        and actual_tail_dominated
        and actual_total_dominated
        and _nonincreasing(golden_tail_radii)
    ):
        status = 'golden-recurrence-rate-strong'
        notes = (
            'The certified tail modulus admits a golden/Fibonacci-normalized remainder law: the convergent chain satisfies the expected recurrence, '
            'the remaining tail budget is dominated by a phi-step rate profile, and that recurrence-aware interval remains compatible with the older q-scale rate-aware modulus interval.'
        )
    elif selected_lo is not None and selected_hi is not None:
        status = 'golden-recurrence-rate-partial'
        notes = (
            'A recurrence-aware phi-step tail law can be fit to the certified convergent family, but either recurrence defects, domination, or compatibility with the q-scale rate law are not yet fully strong.'
        )
    else:
        status = 'golden-recurrence-rate-incomplete'
        notes = 'The recurrence-aware golden/Fibonacci-normalized tail law did not yield a stable common interval.'

    return GoldenRecurrenceRateCertificate(
        rho_target=rho_target,
        family_label=family_label,
        entry_count=int(certified.get('entry_count', 0) or 0),
        usable_entry_count=usable,
        chain_labels=labels,
        chain_qs=qs,
        chain_ps=ps,
        chain_length=usable,
        exact_fibonacci_recurrence=exact_recurrence,
        q_recurrence_max_defect=max(q_rec_defects) if q_rec_defects else 0,
        p_recurrence_max_defect=max(p_rec_defects) if p_rec_defects else 0,
        q_ratio_defect_max=q_ratio_defect_max,
        q_ratio_defect_mean=mean(q_ratio_defects) if q_ratio_defects else None,
        observed_step_beta_min=min(observed_betas) if observed_betas else None,
        observed_step_beta_mean=mean(observed_betas) if observed_betas else None,
        observed_step_beta_max=max(observed_betas) if observed_betas else None,
        chosen_step_exponent=float(chosen_beta),
        step_exponent_safety_factor=float(rate_exponent_safety_factor),
        golden_normalized_tail_constant=float(tail_constant),
        golden_normalized_triple_constant=float(triple_constant),
        golden_normalized_pair_constant=float(pair_constant),
        golden_normalized_fallback_constant=float(fallback_constant),
        golden_normalized_geometric_constant=float(geometric_constant),
        golden_tail_nonincreasing=_nonincreasing(golden_tail_radii),
        actual_tail_dominated_by_golden_rate=actual_tail_dominated,
        actual_total_dominated_by_golden_rate=actual_total_dominated,
        first_golden_tail_radius=golden_tail_radii[0] if golden_tail_radii else None,
        last_golden_tail_radius=golden_tail_radii[-1] if golden_tail_radii else None,
        mean_golden_tail_radius=mean(golden_tail_radii) if golden_tail_radii else None,
        selected_golden_interval_lo=selected_lo,
        selected_golden_interval_hi=selected_hi,
        selected_golden_interval_width=selected_width,
        rate_golden_intersection_lo=rg_lo,
        rate_golden_intersection_hi=rg_hi,
        rate_golden_intersection_width=rg_w,
        theorem_status=status,
        notes=notes,
        nodes=nodes,
    )


__all__ = [
    'GoldenRecurrenceRateCertificate',
    'GoldenRecurrenceRateNode',
    'build_golden_recurrence_rate_certificate',
]
