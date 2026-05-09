from __future__ import annotations

"""Pairwise chain-aware transport control.

This module strengthens the transport-certified irrational-limit bridge by
making the tail explicitly *pairwise continuation aware* across adjacent
convergents.

The previous transport-certified layer sharpened each local crossing window
using endpoint gaps, derivative floors, midpoint data, interval-Newton
refinement, and branch-window diagnostics.  What it did not yet do was check
whether *adjacent* convergents behave like compatible continuation steps rather
than merely individually sharp local objects.

The present module therefore introduces a pairwise chain test.

For every adjacent parent/child pair in a convergent-family tail it builds a
continuation budget from:

1. the transport-refined local widths,
2. branch residual widths transported through derivative floors,
3. branch-tube sup widths, and
4. interval tangent-contraction diagnostics when available.

Those budgets are then used to form pairwise transfer intervals and explicit
compatibility margins.  The final candidate irrational-limit interval is built
from the intersection of the pairwise transfer chain together with the final
transport window, so the output depends not only on per-entry local
certificates but also on explicit parent/child transfer consistency along the
ladder itself.
"""

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Sequence

from .convergent_family_limit_control import _longest_convergent_chain, _fraction_true
from .transport_certified_limit_control import _extract_transport_entries, _interval_intersection, _window_overlap


@dataclass
class PairwiseTransportChainStep:
    grandparent_label: str | None
    parent_label: str
    child_label: str
    grandparent_q: int | None
    parent_q: int
    child_q: int
    parent_local_radius: float
    child_local_radius: float
    allowed_center_shift: float
    observed_center_shift: float
    compatibility_margin: float
    raw_overlap_fraction: float
    child_nested_in_parent: bool
    derivative_backed_pair: bool
    tangent_backed_pair: bool
    continuation_compatible: bool
    pair_interval_lo: float | None
    pair_interval_hi: float | None
    pair_interval_width: float | None
    pair_interval_ratio_to_previous: float | None
    pair_step_bound: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PairwiseTransportChainLimitCertificate:
    rho_target: float | None
    family_label: str | None
    entry_count: int
    usable_entry_count: int
    chain_labels: list[str]
    chain_qs: list[int]
    chain_ps: list[int]
    chain_length: int
    pair_count: int
    derivative_backed_pair_fraction: float | None
    tangent_backed_pair_fraction: float | None
    continuation_compatible_fraction: float | None
    raw_overlap_fraction: float | None
    raw_nested_fraction: float | None
    pair_chain_intersection_lo: float | None
    pair_chain_intersection_hi: float | None
    pair_chain_intersection_width: float | None
    last_pair_interval_lo: float | None
    last_pair_interval_hi: float | None
    last_pair_interval_width: float | None
    last_pair_step_bound: float | None
    observed_pair_contraction_ratio: float | None
    telescoping_pair_tail_bound: float | None
    limit_interval_lo: float | None
    limit_interval_hi: float | None
    limit_interval_width: float | None
    mean_compatibility_margin: float | None
    theorem_status: str
    notes: str
    steps: list[PairwiseTransportChainStep]

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
            'pair_count': int(self.pair_count),
            'derivative_backed_pair_fraction': self.derivative_backed_pair_fraction,
            'tangent_backed_pair_fraction': self.tangent_backed_pair_fraction,
            'continuation_compatible_fraction': self.continuation_compatible_fraction,
            'raw_overlap_fraction': self.raw_overlap_fraction,
            'raw_nested_fraction': self.raw_nested_fraction,
            'pair_chain_intersection_lo': self.pair_chain_intersection_lo,
            'pair_chain_intersection_hi': self.pair_chain_intersection_hi,
            'pair_chain_intersection_width': self.pair_chain_intersection_width,
            'last_pair_interval_lo': self.last_pair_interval_lo,
            'last_pair_interval_hi': self.last_pair_interval_hi,
            'last_pair_interval_width': self.last_pair_interval_width,
            'last_pair_step_bound': self.last_pair_step_bound,
            'observed_pair_contraction_ratio': self.observed_pair_contraction_ratio,
            'telescoping_pair_tail_bound': self.telescoping_pair_tail_bound,
            'limit_interval_lo': self.limit_interval_lo,
            'limit_interval_hi': self.limit_interval_hi,
            'limit_interval_width': self.limit_interval_width,
            'mean_compatibility_margin': self.mean_compatibility_margin,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'steps': [s.to_dict() for s in self.steps],
        }


def _local_radius(entry: dict[str, Any]) -> float:
    width_half = 0.5 * float(entry.get('transport_width', 0.0) or 0.0)
    derivative_floor = entry.get('derivative_floor')
    residual = entry.get('branch_residual_width')
    transported_residual = 0.0
    if derivative_floor not in (None, 0.0) and residual is not None:
        transported_residual = float(residual) / max(float(derivative_floor), 1e-15)
    tube_sup = float(entry.get('tube_sup_width', 0.0) or 0.0)
    contraction = entry.get('interval_tangent_contraction')
    tangent_factor = 1.0
    if contraction is not None and isfinite(float(contraction)):
        tangent_factor = max(0.0, min(1.5, float(contraction)))
    tangent_term = tube_sup * max(tangent_factor, 0.25)
    return float(width_half + transported_residual + tangent_term)


def _pair_interval(parent: dict[str, Any], child: dict[str, Any], allowed_shift: float) -> tuple[float | None, float | None, float | None]:
    parent_center = float(parent['transport_center'])
    child_center = float(child['transport_center'])
    parent_radius = allowed_shift - _local_radius(child)
    child_radius = allowed_shift - _local_radius(parent)
    # expanded transport windows expressing parent->child and child->parent transfer allowances
    a = (
        float(parent['transport_lo']) - max(_local_radius(child), 0.0),
        float(parent['transport_hi']) + max(_local_radius(child), 0.0),
    )
    b = (
        float(child['transport_lo']) - max(_local_radius(parent), 0.0),
        float(child['transport_hi']) + max(_local_radius(parent), 0.0),
    )
    c = (
        parent_center - max(parent_radius, 0.0),
        parent_center + max(parent_radius, 0.0),
    )
    d = (
        child_center - max(child_radius, 0.0),
        child_center + max(child_radius, 0.0),
    )
    return _interval_intersection([a, b, c, d])


def build_pairwise_transport_chain_limit_certificate(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    min_overlap_fraction: float = 0.5,
    compatibility_multiplier: float = 1.1,
) -> PairwiseTransportChainLimitCertificate:
    entries = _extract_transport_entries(ladder)
    entry_count = len(list(ladder.get('approximants', []) or []))
    usable = len(entries)
    if usable < 2:
        return PairwiseTransportChainLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            entry_count=int(entry_count),
            usable_entry_count=int(usable),
            chain_labels=[],
            chain_qs=[],
            chain_ps=[],
            chain_length=0,
            pair_count=0,
            derivative_backed_pair_fraction=None,
            tangent_backed_pair_fraction=None,
            continuation_compatible_fraction=None,
            raw_overlap_fraction=None,
            raw_nested_fraction=None,
            pair_chain_intersection_lo=None,
            pair_chain_intersection_hi=None,
            pair_chain_intersection_width=None,
            last_pair_interval_lo=None,
            last_pair_interval_hi=None,
            last_pair_interval_width=None,
            last_pair_step_bound=None,
            observed_pair_contraction_ratio=None,
            telescoping_pair_tail_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            mean_compatibility_margin=None,
            theorem_status='pairwise-transport-chain-incomplete',
            notes='Not enough transport-refined entries are available to build a pairwise continuation chain.',
            steps=[],
        )

    chain = _longest_convergent_chain(entries, p_tolerance=p_tolerance)
    chain_labels = [str(e['label']) for e in chain]
    chain_qs = [int(e['q']) for e in chain]
    chain_ps = [int(e['p']) for e in chain]
    if len(chain) < min_chain_length:
        return PairwiseTransportChainLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            entry_count=int(entry_count),
            usable_entry_count=int(usable),
            chain_labels=chain_labels,
            chain_qs=chain_qs,
            chain_ps=chain_ps,
            chain_length=len(chain),
            pair_count=max(0, len(chain)-1),
            derivative_backed_pair_fraction=None,
            tangent_backed_pair_fraction=None,
            continuation_compatible_fraction=None,
            raw_overlap_fraction=None,
            raw_nested_fraction=None,
            pair_chain_intersection_lo=None,
            pair_chain_intersection_hi=None,
            pair_chain_intersection_width=None,
            last_pair_interval_lo=None,
            last_pair_interval_hi=None,
            last_pair_interval_width=None,
            last_pair_step_bound=None,
            observed_pair_contraction_ratio=None,
            telescoping_pair_tail_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            mean_compatibility_margin=None,
            theorem_status='pairwise-transport-chain-incomplete',
            notes='A transport-refined convergent tail exists, but it is not yet long enough to support pairwise continuation control.',
            steps=[],
        )

    step_objs: list[PairwiseTransportChainStep] = []
    pair_intervals: list[tuple[float, float]] = []
    pair_widths: list[float] = []
    derivative_pair_flags: list[bool] = []
    tangent_pair_flags: list[bool] = []
    continuation_flags: list[bool] = []
    overlap_flags: list[bool] = []
    nested_flags: list[bool] = []
    compatibility_margins: list[float] = []
    prev_width: float | None = None

    for idx in range(1, len(chain)):
        parent = chain[idx - 1]
        child = chain[idx]
        grandparent = chain[idx - 2] if idx >= 2 else None
        parent_radius = _local_radius(parent)
        child_radius = _local_radius(child)
        center_shift = abs(float(child['transport_center']) - float(parent['transport_center']))
        allowed_shift = float((parent_radius + child_radius) * max(float(compatibility_multiplier), 1.0))
        compatibility_margin = float(allowed_shift - center_shift)
        derivative_pair = bool(parent.get('derivative_backed')) and bool(child.get('derivative_backed'))
        tangent_pair = bool(parent.get('interval_tangent_success')) and bool(child.get('interval_tangent_success'))
        cont_ok = bool(compatibility_margin >= 0.0)
        overlap_w, overlap_frac = _window_overlap(parent['transport_lo'], parent['transport_hi'], child['transport_lo'], child['transport_hi'])
        nested = bool(float(child['transport_lo']) >= float(parent['transport_lo']) and float(child['transport_hi']) <= float(parent['transport_hi']))
        pair_lo, pair_hi, pair_w = _pair_interval(parent, child, allowed_shift)
        if pair_lo is not None and pair_hi is not None:
            pair_intervals.append((float(pair_lo), float(pair_hi)))
            pair_widths.append(float(pair_w))
        ratio = None
        if prev_width is not None and prev_width > 0.0 and pair_w is not None:
            ratio = float(pair_w / prev_width)
        if pair_w is not None:
            prev_width = float(pair_w)
        derivative_pair_flags.append(derivative_pair)
        tangent_pair_flags.append(tangent_pair)
        continuation_flags.append(cont_ok and pair_lo is not None)
        overlap_flags.append(bool(overlap_frac >= min_overlap_fraction))
        nested_flags.append(nested)
        compatibility_margins.append(compatibility_margin)
        step_objs.append(PairwiseTransportChainStep(
            grandparent_label=None if grandparent is None else str(grandparent['label']),
            parent_label=str(parent['label']),
            child_label=str(child['label']),
            grandparent_q=None if grandparent is None else int(grandparent['q']),
            parent_q=int(parent['q']),
            child_q=int(child['q']),
            parent_local_radius=float(parent_radius),
            child_local_radius=float(child_radius),
            allowed_center_shift=float(allowed_shift),
            observed_center_shift=float(center_shift),
            compatibility_margin=float(compatibility_margin),
            raw_overlap_fraction=float(overlap_frac),
            child_nested_in_parent=bool(nested),
            derivative_backed_pair=derivative_pair,
            tangent_backed_pair=tangent_pair,
            continuation_compatible=bool(cont_ok and pair_lo is not None),
            pair_interval_lo=None if pair_lo is None else float(pair_lo),
            pair_interval_hi=None if pair_hi is None else float(pair_hi),
            pair_interval_width=None if pair_w is None else float(pair_w),
            pair_interval_ratio_to_previous=ratio,
            pair_step_bound=None if pair_w is None else float(pair_w + max(center_shift - min(parent_radius, child_radius), 0.0)),
        ))

    pair_inter_lo, pair_inter_hi, pair_inter_w = _interval_intersection(pair_intervals)
    ratios = [s.pair_interval_ratio_to_previous for s in step_objs if s.pair_interval_ratio_to_previous is not None and isfinite(float(s.pair_interval_ratio_to_previous))]
    observed_ratio = None if not ratios else float(min(float(contraction_cap), max(0.0, sum(float(r) for r in ratios) / len(ratios))))
    last = chain[-1]
    last_lo = float(last['transport_lo'])
    last_hi = float(last['transport_hi'])
    last_width = float(last['transport_width'])
    last_pair_width = None if not pair_widths else float(pair_widths[-1])
    telescoping_tail = None
    if observed_ratio is not None and 0.0 <= observed_ratio < 1.0 and last_pair_width is not None:
        telescoping_tail = float(last_pair_width * observed_ratio / max(1.0 - observed_ratio, 1e-12))

    limit_lo = limit_hi = limit_w = None
    if telescoping_tail is not None:
        base_lo = float(last_lo - telescoping_tail)
        base_hi = float(last_hi + telescoping_tail)
        if pair_inter_lo is not None and pair_inter_hi is not None:
            lo = max(base_lo, float(pair_inter_lo))
            hi = min(base_hi, float(pair_inter_hi))
            if hi >= lo:
                limit_lo, limit_hi = float(lo), float(hi)
            else:
                limit_lo, limit_hi = base_lo, base_hi
        else:
            limit_lo, limit_hi = base_lo, base_hi
        limit_w = float(limit_hi - limit_lo)

    derivative_fraction = _fraction_true(derivative_pair_flags)
    tangent_fraction = _fraction_true(tangent_pair_flags)
    continuation_fraction = _fraction_true(continuation_flags)
    raw_overlap_fraction = _fraction_true(overlap_flags)
    raw_nested_fraction = _fraction_true(nested_flags)
    mean_margin = None if not compatibility_margins else float(sum(compatibility_margins) / len(compatibility_margins))

    if (
        limit_lo is not None
        and continuation_fraction is not None and continuation_fraction >= 0.75
        and derivative_fraction is not None and derivative_fraction >= 0.75
        and tangent_fraction is not None and tangent_fraction >= 0.5
        and raw_overlap_fraction is not None and raw_overlap_fraction >= min_overlap_fraction
        and observed_ratio is not None and observed_ratio < contraction_cap
    ):
        status = 'pairwise-transport-chain-strong'
        notes = (
            'Adjacent convergents behave like a continuation-consistent chain: transport-refined windows, branch residual transport through derivative floors, branch-tube widths, and tangent diagnostics together yield nonempty pairwise transfer intervals whose widths contract along the tail.'
        )
    elif limit_lo is not None:
        status = 'pairwise-transport-chain-moderate'
        notes = (
            'A pairwise continuation chain closes and yields a telescoping irrational-limit interval, but the derivative-backed, tangent-backed, or overlap structure is not yet uniformly strong enough for a stronger claim.'
        )
    else:
        status = 'pairwise-transport-chain-incomplete'
        notes = (
            'Transport-refined local windows exist, but adjacent convergents do not yet form a stable pairwise continuation chain with a shrinking tail interval.'
        )

    return PairwiseTransportChainLimitCertificate(
        rho_target=None if rho_target is None else float(rho_target),
        family_label=family_label,
        entry_count=int(entry_count),
        usable_entry_count=int(usable),
        chain_labels=chain_labels,
        chain_qs=chain_qs,
        chain_ps=chain_ps,
        chain_length=int(len(chain)),
        pair_count=int(max(0, len(chain)-1)),
        derivative_backed_pair_fraction=derivative_fraction,
        tangent_backed_pair_fraction=tangent_fraction,
        continuation_compatible_fraction=continuation_fraction,
        raw_overlap_fraction=raw_overlap_fraction,
        raw_nested_fraction=raw_nested_fraction,
        pair_chain_intersection_lo=pair_inter_lo,
        pair_chain_intersection_hi=pair_inter_hi,
        pair_chain_intersection_width=pair_inter_w,
        last_pair_interval_lo=None if not step_objs else step_objs[-1].pair_interval_lo,
        last_pair_interval_hi=None if not step_objs else step_objs[-1].pair_interval_hi,
        last_pair_interval_width=last_pair_width,
        last_pair_step_bound=None if not step_objs else step_objs[-1].pair_step_bound,
        observed_pair_contraction_ratio=observed_ratio,
        telescoping_pair_tail_bound=telescoping_tail,
        limit_interval_lo=limit_lo,
        limit_interval_hi=limit_hi,
        limit_interval_width=limit_w,
        mean_compatibility_margin=mean_margin,
        theorem_status=status,
        notes=notes,
        steps=step_objs,
    )


__all__ = [
    'PairwiseTransportChainStep',
    'PairwiseTransportChainLimitCertificate',
    'build_pairwise_transport_chain_limit_certificate',
]
