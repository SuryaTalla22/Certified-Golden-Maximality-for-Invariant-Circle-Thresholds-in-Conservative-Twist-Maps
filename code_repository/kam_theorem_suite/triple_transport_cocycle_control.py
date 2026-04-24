from __future__ import annotations

"""Three-step continuation / cocycle-style transport control.

This module strengthens the pairwise continuation chain by adding an explicit
*three-step* coherence layer across consecutive grandparent/parent/child
convergents.

The pairwise layer checks whether adjacent entries behave like compatible
continuation steps.  The present layer asks for more: whether those adjacent
steps are themselves compatible with the *direct* grandparent-to-child transfer
information.  In other words, the tail should not merely be pairwise coherent;
it should behave like a discrete cocycle along the convergent family.

Concretely, for every triple ``(a,b,c)`` in a convergent-family tail the module
builds

1. a parent/child transfer interval ``I_ab``;
2. a child/grandchild transfer interval ``I_bc``; and
3. a direct grandparent/child transfer interval ``I_ac``.

It then intersects those intervals with the local transport windows and records
whether the resulting triple-support interval is nonempty.  A second,
step-budget diagnostic compares the direct grandparent-to-child transport budget
against the sum of the two adjacent pair budgets.  When both pass, the triple is
counted as cocycle compatible.

This is still not a theorem.  It is, however, a stronger theorem-facing object
than the pairwise chain because it begins to enforce consistency of the transfer
mechanism across overlapping triples rather than only across adjacent pairs.
"""

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from .convergent_family_limit_control import _fraction_true, _longest_convergent_chain
from .pairwise_transport_chain_control import _local_radius, _pair_interval
from .transport_certified_limit_control import _extract_transport_entries, _interval_intersection, _window_overlap


@dataclass
class TripleTransportCocycleStep:
    grandparent_label: str
    parent_label: str
    child_label: str
    grandparent_q: int
    parent_q: int
    child_q: int
    pair_interval_ab_lo: float | None
    pair_interval_ab_hi: float | None
    pair_interval_ab_width: float | None
    pair_interval_bc_lo: float | None
    pair_interval_bc_hi: float | None
    pair_interval_bc_width: float | None
    direct_interval_ac_lo: float | None
    direct_interval_ac_hi: float | None
    direct_interval_ac_width: float | None
    pair_chain_overlap_lo: float | None
    pair_chain_overlap_hi: float | None
    pair_chain_overlap_width: float | None
    triple_interval_lo: float | None
    triple_interval_hi: float | None
    triple_interval_width: float | None
    pair_chain_overlap_fraction: float | None
    direct_overlap_fraction: float | None
    cocycle_budget: float
    adjacent_budget_sum: float
    direct_step_bound: float
    cocycle_margin: float
    derivative_backed_triplet: bool
    tangent_backed_triplet: bool
    cocycle_compatible: bool
    triple_interval_ratio_to_previous: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TripleTransportCocycleLimitCertificate:
    rho_target: float | None
    family_label: str | None
    entry_count: int
    usable_entry_count: int
    chain_labels: list[str]
    chain_qs: list[int]
    chain_ps: list[int]
    chain_length: int
    triple_count: int
    derivative_backed_triplet_fraction: float | None
    tangent_backed_triplet_fraction: float | None
    pair_chain_overlap_fraction: float | None
    direct_overlap_fraction: float | None
    cocycle_compatible_fraction: float | None
    mean_cocycle_margin: float | None
    triple_chain_intersection_lo: float | None
    triple_chain_intersection_hi: float | None
    triple_chain_intersection_width: float | None
    last_triple_interval_lo: float | None
    last_triple_interval_hi: float | None
    last_triple_interval_width: float | None
    observed_triple_contraction_ratio: float | None
    telescoping_triple_tail_bound: float | None
    limit_interval_lo: float | None
    limit_interval_hi: float | None
    limit_interval_width: float | None
    theorem_status: str
    notes: str
    steps: list[TripleTransportCocycleStep]

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
            'triple_count': int(self.triple_count),
            'derivative_backed_triplet_fraction': self.derivative_backed_triplet_fraction,
            'tangent_backed_triplet_fraction': self.tangent_backed_triplet_fraction,
            'pair_chain_overlap_fraction': self.pair_chain_overlap_fraction,
            'direct_overlap_fraction': self.direct_overlap_fraction,
            'cocycle_compatible_fraction': self.cocycle_compatible_fraction,
            'mean_cocycle_margin': self.mean_cocycle_margin,
            'triple_chain_intersection_lo': self.triple_chain_intersection_lo,
            'triple_chain_intersection_hi': self.triple_chain_intersection_hi,
            'triple_chain_intersection_width': self.triple_chain_intersection_width,
            'last_triple_interval_lo': self.last_triple_interval_lo,
            'last_triple_interval_hi': self.last_triple_interval_hi,
            'last_triple_interval_width': self.last_triple_interval_width,
            'observed_triple_contraction_ratio': self.observed_triple_contraction_ratio,
            'telescoping_triple_tail_bound': self.telescoping_triple_tail_bound,
            'limit_interval_lo': self.limit_interval_lo,
            'limit_interval_hi': self.limit_interval_hi,
            'limit_interval_width': self.limit_interval_width,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'steps': [s.to_dict() for s in self.steps],
        }


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if isfinite(out) else None


def _support_fraction(base: tuple[float | None, float | None, float | None], other: tuple[float | None, float | None, float | None]) -> float | None:
    if base[0] is None or base[1] is None or other[0] is None or other[1] is None:
        return None
    _, frac = _window_overlap(float(base[0]), float(base[1]), float(other[0]), float(other[1]))
    return frac


def build_triple_transport_cocycle_limit_certificate(
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
) -> TripleTransportCocycleLimitCertificate:
    entries = _extract_transport_entries(ladder)
    entry_count = len(list(ladder.get('approximants', []) or []))
    usable = len(entries)
    if usable < 3:
        return TripleTransportCocycleLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            entry_count=int(entry_count),
            usable_entry_count=int(usable),
            chain_labels=[],
            chain_qs=[],
            chain_ps=[],
            chain_length=0,
            triple_count=0,
            derivative_backed_triplet_fraction=None,
            tangent_backed_triplet_fraction=None,
            pair_chain_overlap_fraction=None,
            direct_overlap_fraction=None,
            cocycle_compatible_fraction=None,
            mean_cocycle_margin=None,
            triple_chain_intersection_lo=None,
            triple_chain_intersection_hi=None,
            triple_chain_intersection_width=None,
            last_triple_interval_lo=None,
            last_triple_interval_hi=None,
            last_triple_interval_width=None,
            observed_triple_contraction_ratio=None,
            telescoping_triple_tail_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            theorem_status='triple-transport-cocycle-incomplete',
            notes='Not enough transport-refined entries are available to build a three-step cocycle chain.',
            steps=[],
        )

    chain = _longest_convergent_chain(entries, p_tolerance=p_tolerance)
    chain_labels = [str(e['label']) for e in chain]
    chain_qs = [int(e['q']) for e in chain]
    chain_ps = [int(e['p']) for e in chain]
    if len(chain) < min_chain_length:
        return TripleTransportCocycleLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            entry_count=int(entry_count),
            usable_entry_count=int(usable),
            chain_labels=chain_labels,
            chain_qs=chain_qs,
            chain_ps=chain_ps,
            chain_length=len(chain),
            triple_count=max(0, len(chain) - 2),
            derivative_backed_triplet_fraction=None,
            tangent_backed_triplet_fraction=None,
            pair_chain_overlap_fraction=None,
            direct_overlap_fraction=None,
            cocycle_compatible_fraction=None,
            mean_cocycle_margin=None,
            triple_chain_intersection_lo=None,
            triple_chain_intersection_hi=None,
            triple_chain_intersection_width=None,
            last_triple_interval_lo=None,
            last_triple_interval_hi=None,
            last_triple_interval_width=None,
            observed_triple_contraction_ratio=None,
            telescoping_triple_tail_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            theorem_status='triple-transport-cocycle-incomplete',
            notes='A convergent-family tail exists, but it is not yet long enough to support a three-step cocycle check.',
            steps=[],
        )

    steps: list[TripleTransportCocycleStep] = []
    triple_intervals: list[tuple[float, float]] = []
    triple_widths: list[float] = []
    derivative_flags: list[bool] = []
    tangent_flags: list[bool] = []
    pair_overlap_flags: list[bool] = []
    direct_overlap_flags: list[bool] = []
    cocycle_flags: list[bool] = []
    margins: list[float] = []

    prev_width: float | None = None
    for idx in range(2, len(chain)):
        a = chain[idx - 2]
        b = chain[idx - 1]
        c = chain[idx]

        ra = _local_radius(a)
        rb = _local_radius(b)
        rc = _local_radius(c)
        allowed_ab = compatibility_multiplier * (ra + rb)
        allowed_bc = compatibility_multiplier * (rb + rc)
        adjacent_budget_sum = float(allowed_ab + allowed_bc)
        cocycle_budget = float(cocycle_multiplier * adjacent_budget_sum)
        allowed_ac = max(
            compatibility_multiplier * (ra + rc),
            cocycle_budget,
        )

        pair_ab = _pair_interval(a, b, allowed_ab)
        pair_bc = _pair_interval(b, c, allowed_bc)
        direct_ac = _pair_interval(a, c, allowed_ac)
        pair_windows = []
        if pair_ab[0] is not None and pair_ab[1] is not None:
            pair_windows.append((float(pair_ab[0]), float(pair_ab[1])))
        if pair_bc[0] is not None and pair_bc[1] is not None:
            pair_windows.append((float(pair_bc[0]), float(pair_bc[1])))
        pair_chain = _interval_intersection(pair_windows)
        usable_windows = []
        for lo, hi in [
            (pair_chain[0], pair_chain[1]),
            (direct_ac[0], direct_ac[1]),
            (_safe_float(a.get('transport_lo')), _safe_float(a.get('transport_hi'))),
            (_safe_float(b.get('transport_lo')), _safe_float(b.get('transport_hi'))),
            (_safe_float(c.get('transport_lo')), _safe_float(c.get('transport_hi'))),
        ]:
            if lo is not None and hi is not None:
                usable_windows.append((float(lo), float(hi)))
        triple = _interval_intersection(usable_windows)

        direct_step_bound = abs(float(c['transport_center']) - float(a['transport_center'])) + ra + rc
        cocycle_margin = float(cocycle_budget - direct_step_bound)

        derivative_backed = bool(a.get('derivative_backed') and b.get('derivative_backed') and c.get('derivative_backed'))
        tangent_backed = bool(
            a.get('interval_tangent_success') and b.get('interval_tangent_success') and c.get('interval_tangent_success')
        )
        pair_frac = _support_fraction(pair_chain, direct_ac)
        direct_frac = _support_fraction(direct_ac, triple)
        pair_overlap_ok = bool(pair_frac is not None and pair_frac >= min_overlap_fraction)
        direct_overlap_ok = bool(direct_frac is not None and direct_frac >= min_overlap_fraction)
        triple_ok = bool(triple[0] is not None and triple[1] is not None)
        cocycle_ok = bool(triple_ok and pair_overlap_ok and direct_overlap_ok and cocycle_margin >= 0.0)

        triple_width = triple[2]
        ratio = None
        if prev_width not in (None, 0.0) and triple_width not in (None,):
            ratio = float(triple_width / max(prev_width, 1e-15))
        if triple_width is not None:
            prev_width = float(triple_width)
            triple_widths.append(float(triple_width))
        if triple[0] is not None and triple[1] is not None:
            triple_intervals.append((float(triple[0]), float(triple[1])))

        derivative_flags.append(derivative_backed)
        tangent_flags.append(tangent_backed)
        pair_overlap_flags.append(pair_overlap_ok)
        direct_overlap_flags.append(direct_overlap_ok)
        cocycle_flags.append(cocycle_ok)
        margins.append(cocycle_margin)

        steps.append(
            TripleTransportCocycleStep(
                grandparent_label=str(a['label']),
                parent_label=str(b['label']),
                child_label=str(c['label']),
                grandparent_q=int(a['q']),
                parent_q=int(b['q']),
                child_q=int(c['q']),
                pair_interval_ab_lo=pair_ab[0],
                pair_interval_ab_hi=pair_ab[1],
                pair_interval_ab_width=pair_ab[2],
                pair_interval_bc_lo=pair_bc[0],
                pair_interval_bc_hi=pair_bc[1],
                pair_interval_bc_width=pair_bc[2],
                direct_interval_ac_lo=direct_ac[0],
                direct_interval_ac_hi=direct_ac[1],
                direct_interval_ac_width=direct_ac[2],
                pair_chain_overlap_lo=pair_chain[0],
                pair_chain_overlap_hi=pair_chain[1],
                pair_chain_overlap_width=pair_chain[2],
                triple_interval_lo=triple[0],
                triple_interval_hi=triple[1],
                triple_interval_width=triple[2],
                pair_chain_overlap_fraction=pair_frac,
                direct_overlap_fraction=direct_frac,
                cocycle_budget=cocycle_budget,
                adjacent_budget_sum=adjacent_budget_sum,
                direct_step_bound=direct_step_bound,
                cocycle_margin=cocycle_margin,
                derivative_backed_triplet=derivative_backed,
                tangent_backed_triplet=tangent_backed,
                cocycle_compatible=cocycle_ok,
                triple_interval_ratio_to_previous=ratio,
            )
        )

    intersection = _interval_intersection(triple_intervals)
    last = steps[-1] if steps else None
    contraction_ratios = [
        float(step.triple_interval_ratio_to_previous)
        for step in steps
        if step.triple_interval_ratio_to_previous is not None and isfinite(float(step.triple_interval_ratio_to_previous))
    ]
    observed_contraction = None
    if contraction_ratios:
        observed_contraction = min(float(sum(contraction_ratios) / len(contraction_ratios)), float(contraction_cap))
    telescoping_tail = None
    if last is not None and last.triple_interval_width is not None and observed_contraction is not None and observed_contraction < 1.0:
        telescoping_tail = float(last.triple_interval_width * observed_contraction / max(1.0 - observed_contraction, 1e-15))
        limit_lo = float(last.triple_interval_lo - telescoping_tail) if last.triple_interval_lo is not None else None
        limit_hi = float(last.triple_interval_hi + telescoping_tail) if last.triple_interval_hi is not None else None
        limit_w = None if limit_lo is None or limit_hi is None else float(limit_hi - limit_lo)
    else:
        limit_lo = limit_hi = limit_w = None

    cocycle_fraction = _fraction_true(cocycle_flags)
    if (
        intersection[0] is not None
        and limit_lo is not None
        and cocycle_fraction is not None
        and cocycle_fraction >= min_overlap_fraction
        and (observed_contraction is None or observed_contraction < 1.0)
    ):
        status = 'triple-transport-cocycle-strong' if (
            observed_contraction is not None and observed_contraction <= contraction_cap and _fraction_true(derivative_flags) is not None
        ) else 'triple-transport-cocycle-moderate'
        notes = (
            'A three-step grandparent/parent/child continuation chain is available. '
            'Adjacent pair-transfer intervals and the direct grandparent-to-child transport interval admit a nonempty cocycle support across the tail, producing a stronger structural irrational-limit container than the pairwise chain alone.'
        )
    elif triple_intervals:
        status = 'triple-transport-cocycle-fragile'
        notes = (
            'Three-step transfer intervals can be formed on the tail, but the cocycle-support intersection is not yet strong enough across the full chain to behave like a stable theorem-facing container.'
        )
    else:
        status = 'triple-transport-cocycle-incomplete'
        notes = 'The current ladder does not yet support a usable three-step cocycle transport chain.'

    return TripleTransportCocycleLimitCertificate(
        rho_target=None if rho_target is None else float(rho_target),
        family_label=family_label,
        entry_count=int(entry_count),
        usable_entry_count=int(usable),
        chain_labels=chain_labels,
        chain_qs=chain_qs,
        chain_ps=chain_ps,
        chain_length=len(chain),
        triple_count=len(steps),
        derivative_backed_triplet_fraction=_fraction_true(derivative_flags),
        tangent_backed_triplet_fraction=_fraction_true(tangent_flags),
        pair_chain_overlap_fraction=_fraction_true(pair_overlap_flags),
        direct_overlap_fraction=_fraction_true(direct_overlap_flags),
        cocycle_compatible_fraction=cocycle_fraction,
        mean_cocycle_margin=None if not margins else float(sum(margins) / len(margins)),
        triple_chain_intersection_lo=intersection[0],
        triple_chain_intersection_hi=intersection[1],
        triple_chain_intersection_width=intersection[2],
        last_triple_interval_lo=None if last is None else last.triple_interval_lo,
        last_triple_interval_hi=None if last is None else last.triple_interval_hi,
        last_triple_interval_width=None if last is None else last.triple_interval_width,
        observed_triple_contraction_ratio=observed_contraction,
        telescoping_triple_tail_bound=telescoping_tail,
        limit_interval_lo=limit_lo,
        limit_interval_hi=limit_hi,
        limit_interval_width=limit_w,
        theorem_status=status,
        notes=notes,
        steps=steps,
    )


__all__ = ['TripleTransportCocycleLimitCertificate', 'TripleTransportCocycleStep', 'build_triple_transport_cocycle_limit_certificate']
