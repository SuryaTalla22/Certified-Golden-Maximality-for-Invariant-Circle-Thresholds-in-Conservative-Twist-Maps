from __future__ import annotations

"""Tail-Cauchy potential control with explicit remainder decomposition.

This layer upgrades the ladder-global transport potential by attaching an
explicit decomposition of the tail remainder budget by *edge class*.

The previous global potential layer already aggregated pairwise and triple
constraints into a single suffix potential.  What it did not expose was where
that suffix budget came from.  Here we keep the same continuation-style tail
object but refine it into theorem-facing components:

1. ``triple-reinforced`` edge budgets coming from edges supported by overlapping
   triple cocycle constraints,
2. ``pair-anchored`` edge budgets coming from edges supported only by pairwise
   continuation anchors,
3. ``transport-fallback`` budgets for edges that are still controlled only by
   local transport geometry, and
4. a ``geometric-tail`` remainder representing the extrapolated unseen tail
   beyond the last certified edge.

For every node in the convergent tail we report the suffix contribution from
these edge classes separately.  The resulting interval is therefore not merely a
single global tail bound: it is a *Tail-Cauchy functional* whose radius comes
with a precise decomposition of its continuation remainder.

This still does not prove the full rational-to-irrational convergence theorem.
It does, however, provide a stronger theorem-facing bridge because the final
limit interval now carries an explicit audit trail for the remainder budget.
"""

from dataclasses import asdict, dataclass
from math import isfinite
from statistics import mean
from typing import Any

from .convergent_family_limit_control import _fraction_true, _longest_convergent_chain
from .global_transport_potential_control import _build_anchor_interval, _edge_budget, _map_pair_steps, _map_triple_steps
from .pairwise_transport_chain_control import _local_radius, build_pairwise_transport_chain_limit_certificate
from .transport_certified_limit_control import _extract_transport_entries, _interval_intersection
from .triple_transport_cocycle_control import build_triple_transport_cocycle_limit_certificate

_EDGE_CLASSES = ('triple-reinforced', 'pair-anchored', 'transport-fallback')


@dataclass
class TailCauchyPotentialNode:
    label: str
    p: int
    q: int
    transport_center: float
    transport_lo: float
    transport_hi: float
    transport_width: float
    local_radius: float
    forward_edge_class: str | None
    forward_edge_budget: float | None
    monotone_forward_edge_budget: float | None
    suffix_triple_reinforced_budget: float
    suffix_pair_anchored_budget: float
    suffix_transport_fallback_budget: float
    suffix_geometric_tail_budget: float
    suffix_total_budget: float
    cauchy_radius: float
    cauchy_interval_lo: float
    cauchy_interval_hi: float
    cauchy_interval_width: float
    cauchy_interval_ratio_to_previous: float | None
    derivative_backed: bool
    tangent_backed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TailCauchyPotentialCertificate:
    rho_target: float | None
    family_label: str | None
    entry_count: int
    usable_entry_count: int
    chain_labels: list[str]
    chain_qs: list[int]
    chain_ps: list[int]
    chain_length: int
    edge_count: int
    derivative_backed_fraction: float | None
    tangent_backed_fraction: float | None
    pair_anchor_fraction: float | None
    triple_anchor_fraction: float | None
    triple_reinforced_edge_count: int
    pair_anchored_edge_count: int
    transport_fallback_edge_count: int
    full_tail_triple_reinforced_budget: float | None
    full_tail_pair_anchored_budget: float | None
    full_tail_transport_fallback_budget: float | None
    full_tail_geometric_budget: float | None
    full_tail_budget: float | None
    full_tail_triple_reinforced_share: float | None
    full_tail_pair_anchored_share: float | None
    full_tail_transport_fallback_share: float | None
    full_tail_geometric_share: float | None
    first_node_local_radius: float | None
    max_local_radius: float | None
    mean_local_radius: float | None
    raw_edge_budget_mean: float | None
    monotone_edge_budget_mean: float | None
    observed_monotone_ratio: float | None
    suffix_budget_nonincreasing: bool
    global_cauchy_intersection_lo: float | None
    global_cauchy_intersection_hi: float | None
    global_cauchy_intersection_width: float | None
    last_node_interval_lo: float | None
    last_node_interval_hi: float | None
    last_node_interval_width: float | None
    selected_limit_interval_lo: float | None
    selected_limit_interval_hi: float | None
    selected_limit_interval_width: float | None
    theorem_status: str
    notes: str
    nodes: list[TailCauchyPotentialNode]

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
            'edge_count': int(self.edge_count),
            'derivative_backed_fraction': self.derivative_backed_fraction,
            'tangent_backed_fraction': self.tangent_backed_fraction,
            'pair_anchor_fraction': self.pair_anchor_fraction,
            'triple_anchor_fraction': self.triple_anchor_fraction,
            'triple_reinforced_edge_count': int(self.triple_reinforced_edge_count),
            'pair_anchored_edge_count': int(self.pair_anchored_edge_count),
            'transport_fallback_edge_count': int(self.transport_fallback_edge_count),
            'full_tail_triple_reinforced_budget': self.full_tail_triple_reinforced_budget,
            'full_tail_pair_anchored_budget': self.full_tail_pair_anchored_budget,
            'full_tail_transport_fallback_budget': self.full_tail_transport_fallback_budget,
            'full_tail_geometric_budget': self.full_tail_geometric_budget,
            'full_tail_budget': self.full_tail_budget,
            'full_tail_triple_reinforced_share': self.full_tail_triple_reinforced_share,
            'full_tail_pair_anchored_share': self.full_tail_pair_anchored_share,
            'full_tail_transport_fallback_share': self.full_tail_transport_fallback_share,
            'full_tail_geometric_share': self.full_tail_geometric_share,
            'first_node_local_radius': self.first_node_local_radius,
            'max_local_radius': self.max_local_radius,
            'mean_local_radius': self.mean_local_radius,
            'raw_edge_budget_mean': self.raw_edge_budget_mean,
            'monotone_edge_budget_mean': self.monotone_edge_budget_mean,
            'observed_monotone_ratio': self.observed_monotone_ratio,
            'suffix_budget_nonincreasing': bool(self.suffix_budget_nonincreasing),
            'global_cauchy_intersection_lo': self.global_cauchy_intersection_lo,
            'global_cauchy_intersection_hi': self.global_cauchy_intersection_hi,
            'global_cauchy_intersection_width': self.global_cauchy_intersection_width,
            'last_node_interval_lo': self.last_node_interval_lo,
            'last_node_interval_hi': self.last_node_interval_hi,
            'last_node_interval_width': self.last_node_interval_width,
            'selected_limit_interval_lo': self.selected_limit_interval_lo,
            'selected_limit_interval_hi': self.selected_limit_interval_hi,
            'selected_limit_interval_width': self.selected_limit_interval_width,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'nodes': [n.to_dict() for n in self.nodes],
        }


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if isfinite(out) else None


def _empty_certificate(*, rho_target: float | None, family_label: str | None, entry_count: int, usable_entry_count: int,
                       chain_labels: list[str], chain_qs: list[int], chain_ps: list[int], chain_length: int,
                       edge_count: int, notes: str) -> TailCauchyPotentialCertificate:
    return TailCauchyPotentialCertificate(
        rho_target=rho_target,
        family_label=family_label,
        entry_count=int(entry_count),
        usable_entry_count=int(usable_entry_count),
        chain_labels=chain_labels,
        chain_qs=chain_qs,
        chain_ps=chain_ps,
        chain_length=int(chain_length),
        edge_count=int(edge_count),
        derivative_backed_fraction=None,
        tangent_backed_fraction=None,
        pair_anchor_fraction=None,
        triple_anchor_fraction=None,
        triple_reinforced_edge_count=0,
        pair_anchored_edge_count=0,
        transport_fallback_edge_count=0,
        full_tail_triple_reinforced_budget=None,
        full_tail_pair_anchored_budget=None,
        full_tail_transport_fallback_budget=None,
        full_tail_geometric_budget=None,
        full_tail_budget=None,
        full_tail_triple_reinforced_share=None,
        full_tail_pair_anchored_share=None,
        full_tail_transport_fallback_share=None,
        full_tail_geometric_share=None,
        first_node_local_radius=None,
        max_local_radius=None,
        mean_local_radius=None,
        raw_edge_budget_mean=None,
        monotone_edge_budget_mean=None,
        observed_monotone_ratio=None,
        suffix_budget_nonincreasing=False,
        global_cauchy_intersection_lo=None,
        global_cauchy_intersection_hi=None,
        global_cauchy_intersection_width=None,
        last_node_interval_lo=None,
        last_node_interval_hi=None,
        last_node_interval_width=None,
        selected_limit_interval_lo=None,
        selected_limit_interval_hi=None,
        selected_limit_interval_width=None,
        theorem_status='tail-cauchy-potential-incomplete',
        notes=notes,
        nodes=[],
    )


def _edge_class(pair_anchor_count: int, triple_anchor_count: int) -> str:
    if triple_anchor_count > 0:
        return 'triple-reinforced'
    if pair_anchor_count > 0:
        return 'pair-anchored'
    return 'transport-fallback'


def _share(part: float | None, whole: float | None) -> float | None:
    if part is None or whole is None or whole <= 0.0:
        return None
    return float(part / whole)


def build_tail_cauchy_potential_certificate(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    anchor_multiplier: float = 1.05,
    fallback_share_cap: float = 0.35,
) -> TailCauchyPotentialCertificate:
    entries = _extract_transport_entries(ladder)
    entry_count = len(list(ladder.get('approximants', []) or []))
    usable = len(entries)
    rho_target = None if rho_target is None else float(rho_target)
    if usable < 2:
        return _empty_certificate(
            rho_target=rho_target,
            family_label=family_label,
            entry_count=entry_count,
            usable_entry_count=usable,
            chain_labels=[],
            chain_qs=[],
            chain_ps=[],
            chain_length=0,
            edge_count=0,
            notes='Not enough transport-refined entries are available to build a tail-Cauchy potential.',
        )

    chain = _longest_convergent_chain(entries, p_tolerance=p_tolerance)
    chain_labels = [str(e['label']) for e in chain]
    chain_qs = [int(e['q']) for e in chain]
    chain_ps = [int(e['p']) for e in chain]
    if len(chain) < min_chain_length:
        return _empty_certificate(
            rho_target=rho_target,
            family_label=family_label,
            entry_count=entry_count,
            usable_entry_count=usable,
            chain_labels=chain_labels,
            chain_qs=chain_qs,
            chain_ps=chain_ps,
            chain_length=len(chain),
            edge_count=max(0, len(chain) - 1),
            notes='A transport-refined convergent tail exists, but it is not yet long enough to support a Tail-Cauchy potential.',
        )

    pair_cert = build_pairwise_transport_chain_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
    ).to_dict()
    triple_cert = build_triple_transport_cocycle_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
    ).to_dict()

    pair_map = _map_pair_steps(pair_cert)
    triple_map = _map_triple_steps(triple_cert)

    edge_raw_budgets: list[float] = []
    edge_classes: list[str] = []
    pair_anchor_flags: list[bool] = []
    triple_anchor_flags: list[bool] = []
    edge_infos: list[dict[str, Any]] = []

    for left, right in zip(chain[:-1], chain[1:]):
        key = (str(left['label']), str(right['label']))
        pair_step = pair_map.get(key)
        triples = triple_map.get(key, [])
        anchor_lo, anchor_hi, anchor_w, pair_anchor_count, triple_anchor_count = _build_anchor_interval(
            pair_step,
            triples,
            left_label=key[0],
            right_label=key[1],
        )
        budget = _edge_budget(
            left,
            right,
            pair_step=pair_step,
            anchor_interval=(anchor_lo, anchor_hi, anchor_w),
            anchor_multiplier=anchor_multiplier,
        )
        edge_raw_budgets.append(float(budget))
        edge_cls = _edge_class(pair_anchor_count, triple_anchor_count)
        edge_classes.append(edge_cls)
        pair_anchor_flags.append(pair_anchor_count > 0)
        triple_anchor_flags.append(triple_anchor_count > 0)
        edge_infos.append(
            {
                'pair_anchor_count': int(pair_anchor_count),
                'triple_anchor_count': int(triple_anchor_count),
                'edge_class': edge_cls,
            }
        )

    monotone_edge_budgets = list(edge_raw_budgets)
    for i in range(len(monotone_edge_budgets) - 2, -1, -1):
        monotone_edge_budgets[i] = max(float(monotone_edge_budgets[i]), float(monotone_edge_budgets[i + 1]))

    ratio_candidates: list[float] = []
    for a, b in zip(monotone_edge_budgets[:-1], monotone_edge_budgets[1:]):
        if a > 0.0 and b >= 0.0:
            ratio_candidates.append(float(b / a))
    observed_ratio = min(float(contraction_cap), max(ratio_candidates)) if ratio_candidates else float(contraction_cap)
    if observed_ratio >= 1.0:
        observed_ratio = min(float(contraction_cap), 0.99)
    last_edge = float(monotone_edge_budgets[-1]) if monotone_edge_budgets else 0.0
    geometric_tail_extension = float(last_edge * observed_ratio / max(1.0 - observed_ratio, 1e-12)) if monotone_edge_budgets else 0.0

    running = {cls: 0.0 for cls in _EDGE_CLASSES}
    suffix_class_budgets: list[dict[str, float]] = [dict(running) for _ in chain]
    for idx in range(len(chain) - 2, -1, -1):
        cls = edge_classes[idx]
        running[cls] += float(monotone_edge_budgets[idx])
        suffix_class_budgets[idx] = dict(running)
    if chain:
        suffix_class_budgets[-1] = {cls: 0.0 for cls in _EDGE_CLASSES}

    node_intervals: list[tuple[float, float]] = []
    nodes: list[TailCauchyPotentialNode] = []
    previous_width: float | None = None
    derivative_flags: list[bool] = []
    tangent_flags: list[bool] = []
    local_radii: list[float] = []
    suffix_totals: list[float] = []

    for idx, entry in enumerate(chain):
        center = float(entry['transport_center'])
        local_radius = float(_local_radius(entry))
        local_radii.append(local_radius)
        suffix = suffix_class_budgets[idx]
        suffix_total = float(sum(suffix.values()) + geometric_tail_extension)
        suffix_totals.append(suffix_total)
        cauchy_radius = float(local_radius + suffix_total)
        lo = float(center - cauchy_radius)
        hi = float(center + cauchy_radius)
        width = float(hi - lo)
        node_intervals.append((lo, hi))
        interval_ratio = None if previous_width in (None, 0.0) else float(width / max(previous_width, 1e-15))
        previous_width = width
        derivative_backed = bool(entry.get('derivative_backed'))
        tangent_backed = bool(entry.get('tangent_inclusion_success')) or bool(entry.get('interval_tangent_success'))
        derivative_flags.append(derivative_backed)
        tangent_flags.append(tangent_backed)
        nodes.append(
            TailCauchyPotentialNode(
                label=str(entry['label']),
                p=int(entry['p']),
                q=int(entry['q']),
                transport_center=center,
                transport_lo=float(entry['transport_lo']),
                transport_hi=float(entry['transport_hi']),
                transport_width=float(entry['transport_width']),
                local_radius=local_radius,
                forward_edge_class=None if idx >= len(edge_classes) else str(edge_classes[idx]),
                forward_edge_budget=None if idx >= len(edge_raw_budgets) else float(edge_raw_budgets[idx]),
                monotone_forward_edge_budget=None if idx >= len(monotone_edge_budgets) else float(monotone_edge_budgets[idx]),
                suffix_triple_reinforced_budget=float(suffix['triple-reinforced']),
                suffix_pair_anchored_budget=float(suffix['pair-anchored']),
                suffix_transport_fallback_budget=float(suffix['transport-fallback']),
                suffix_geometric_tail_budget=float(geometric_tail_extension),
                suffix_total_budget=suffix_total,
                cauchy_radius=cauchy_radius,
                cauchy_interval_lo=lo,
                cauchy_interval_hi=hi,
                cauchy_interval_width=width,
                cauchy_interval_ratio_to_previous=interval_ratio,
                derivative_backed=derivative_backed,
                tangent_backed=tangent_backed,
            )
        )

    global_lo, global_hi, global_w = _interval_intersection(node_intervals)
    last_node = nodes[-1]
    first_suffix = suffix_class_budgets[0] if suffix_class_budgets else {cls: 0.0 for cls in _EDGE_CLASSES}
    full_tail_budget = float(sum(first_suffix.values()) + geometric_tail_extension) if nodes else None
    fallback_share = _share(first_suffix['transport-fallback'], full_tail_budget)
    suffix_budget_nonincreasing = all(suffix_totals[i] >= suffix_totals[i + 1] - 1e-15 for i in range(len(suffix_totals) - 1))

    pair_fraction = _fraction_true(pair_anchor_flags)
    triple_fraction = _fraction_true(triple_anchor_flags)
    triple_count = sum(1 for cls in edge_classes if cls == 'triple-reinforced')
    pair_count = sum(1 for cls in edge_classes if cls == 'pair-anchored')
    fallback_count = sum(1 for cls in edge_classes if cls == 'transport-fallback')

    strong_support = (
        global_lo is not None
        and global_hi is not None
        and (pair_fraction or 0.0) >= 0.75
        and (triple_fraction or 0.0) >= 0.5
        and observed_ratio < 1.0
        and suffix_budget_nonincreasing
        and ((fallback_share or 0.0) <= float(fallback_share_cap))
    )
    partial_support = global_lo is not None and global_hi is not None and suffix_budget_nonincreasing

    if strong_support:
        status = 'tail-cauchy-potential-strong'
        notes = (
            'A Tail-Cauchy potential was built from the convergent-family tail. '
            'The final remainder radius is decomposed explicitly into triple-reinforced, pair-anchored, transport-fallback, and geometric-tail contributions, '
            'and the resulting node-wise Cauchy intervals intersect nontrivially.'
        )
    elif partial_support:
        status = 'tail-cauchy-potential-partial'
        notes = (
            'A Tail-Cauchy potential exists and its suffix budgets are explicitly decomposed by edge class, '
            'but the support fractions or fallback share are not yet strong enough to treat the resulting interval as a robust continuation-style bound.'
        )
    else:
        status = 'tail-cauchy-potential-incomplete'
        notes = 'The edge-class remainder decomposition does not yet yield a nonempty global Tail-Cauchy interval.'

    return TailCauchyPotentialCertificate(
        rho_target=rho_target,
        family_label=family_label,
        entry_count=int(entry_count),
        usable_entry_count=int(usable),
        chain_labels=chain_labels,
        chain_qs=chain_qs,
        chain_ps=chain_ps,
        chain_length=len(chain),
        edge_count=max(0, len(chain) - 1),
        derivative_backed_fraction=_fraction_true(derivative_flags),
        tangent_backed_fraction=_fraction_true(tangent_flags),
        pair_anchor_fraction=pair_fraction,
        triple_anchor_fraction=triple_fraction,
        triple_reinforced_edge_count=int(triple_count),
        pair_anchored_edge_count=int(pair_count),
        transport_fallback_edge_count=int(fallback_count),
        full_tail_triple_reinforced_budget=float(first_suffix['triple-reinforced']),
        full_tail_pair_anchored_budget=float(first_suffix['pair-anchored']),
        full_tail_transport_fallback_budget=float(first_suffix['transport-fallback']),
        full_tail_geometric_budget=float(geometric_tail_extension),
        full_tail_budget=full_tail_budget,
        full_tail_triple_reinforced_share=_share(first_suffix['triple-reinforced'], full_tail_budget),
        full_tail_pair_anchored_share=_share(first_suffix['pair-anchored'], full_tail_budget),
        full_tail_transport_fallback_share=fallback_share,
        full_tail_geometric_share=_share(geometric_tail_extension, full_tail_budget),
        first_node_local_radius=(None if not local_radii else float(local_radii[0])),
        max_local_radius=(None if not local_radii else float(max(local_radii))),
        mean_local_radius=(None if not local_radii else float(mean(local_radii))),
        raw_edge_budget_mean=(None if not edge_raw_budgets else float(mean(edge_raw_budgets))),
        monotone_edge_budget_mean=(None if not monotone_edge_budgets else float(mean(monotone_edge_budgets))),
        observed_monotone_ratio=float(observed_ratio),
        suffix_budget_nonincreasing=bool(suffix_budget_nonincreasing),
        global_cauchy_intersection_lo=global_lo,
        global_cauchy_intersection_hi=global_hi,
        global_cauchy_intersection_width=global_w,
        last_node_interval_lo=float(last_node.cauchy_interval_lo),
        last_node_interval_hi=float(last_node.cauchy_interval_hi),
        last_node_interval_width=float(last_node.cauchy_interval_width),
        selected_limit_interval_lo=global_lo,
        selected_limit_interval_hi=global_hi,
        selected_limit_interval_width=global_w,
        theorem_status=status,
        notes=notes,
        nodes=nodes,
    )


__all__ = [
    'TailCauchyPotentialNode',
    'TailCauchyPotentialCertificate',
    'build_tail_cauchy_potential_certificate',
]
