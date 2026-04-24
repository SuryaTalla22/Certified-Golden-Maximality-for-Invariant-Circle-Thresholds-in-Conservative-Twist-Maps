from __future__ import annotations

"""Ladder-global transport-potential control.

This module upgrades the triple transport cocycle layer from a collection of
local triple intersections into a *single tail functional* built across the
whole convergent ladder.

The previous stages already supplied:

1. transport-refined local root windows,
2. pairwise continuation-aware transfer intervals, and
3. triple cocycle-style coherence checks on overlapping triples.

What they did not yet do was aggregate those local constraints into one global
object.  Here we do exactly that.

For a convergent-family tail we first build an effective edge budget for each
adjacent pair.  That budget starts from the pairwise continuation certificate and
is then *reinforced* by all overlapping triple constraints touching that edge.
The reinforced edge budgets are projected to a monotone nonincreasing tail
profile, producing a ladder-global transport potential.  Each convergent then
induces a candidate limit interval obtained by enlarging its local transport
center by the suffix potential still available beyond that point.  Intersecting
those node-wise potential intervals produces a single candidate irrational-limit
interval.

This is still not the final rational-to-irrational convergence theorem.  It is,
however, the strongest bridge object in the current bundle because it converts
all overlapping local continuation evidence into one coherent tail potential
rather than intersecting the constraints one pair or one triple at a time.
"""

from dataclasses import asdict, dataclass
from math import isfinite
from statistics import mean
from typing import Any, Sequence

from .convergent_family_limit_control import _fraction_true, _longest_convergent_chain
from .pairwise_transport_chain_control import _local_radius, build_pairwise_transport_chain_limit_certificate
from .transport_certified_limit_control import _extract_transport_entries, _interval_intersection
from .triple_transport_cocycle_control import build_triple_transport_cocycle_limit_certificate


@dataclass
class GlobalTransportPotentialNode:
    label: str
    p: int
    q: int
    transport_center: float
    transport_lo: float
    transport_hi: float
    transport_width: float
    local_radius: float
    forward_edge_budget: float | None
    monotone_forward_edge_budget: float | None
    suffix_transport_budget: float
    potential_radius: float
    potential_interval_lo: float
    potential_interval_hi: float
    potential_interval_width: float
    pair_anchor_count: int
    triple_anchor_count: int
    derivative_backed: bool
    tangent_backed: bool
    potential_interval_ratio_to_previous: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GlobalTransportPotentialCertificate:
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
    mean_supporting_triples_per_edge: float | None
    raw_edge_budget_mean: float | None
    monotone_edge_budget_mean: float | None
    observed_monotone_ratio: float | None
    geometric_tail_extension: float | None
    global_intersection_lo: float | None
    global_intersection_hi: float | None
    global_intersection_width: float | None
    last_node_interval_lo: float | None
    last_node_interval_hi: float | None
    last_node_interval_width: float | None
    selected_limit_interval_lo: float | None
    selected_limit_interval_hi: float | None
    selected_limit_interval_width: float | None
    theorem_status: str
    notes: str
    nodes: list[GlobalTransportPotentialNode]

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
            'mean_supporting_triples_per_edge': self.mean_supporting_triples_per_edge,
            'raw_edge_budget_mean': self.raw_edge_budget_mean,
            'monotone_edge_budget_mean': self.monotone_edge_budget_mean,
            'observed_monotone_ratio': self.observed_monotone_ratio,
            'geometric_tail_extension': self.geometric_tail_extension,
            'global_intersection_lo': self.global_intersection_lo,
            'global_intersection_hi': self.global_intersection_hi,
            'global_intersection_width': self.global_intersection_width,
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


def _map_pair_steps(cert: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for step in cert.get('steps', []) or []:
        key = (str(step.get('parent_label')), str(step.get('child_label')))
        out[key] = dict(step)
    return out


def _map_triple_steps(cert: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for step in cert.get('steps', []) or []:
        gp = str(step.get('grandparent_label'))
        parent = str(step.get('parent_label'))
        child = str(step.get('child_label'))
        out.setdefault((gp, parent), []).append(dict(step))
        out.setdefault((parent, child), []).append(dict(step))
    return out


def _interval_width(interval: tuple[float | None, float | None, float | None]) -> float | None:
    return None if interval[2] is None else float(interval[2])


def _build_anchor_interval(
    pair_step: dict[str, Any] | None,
    triple_steps: Sequence[dict[str, Any]],
    *,
    left_label: str,
    right_label: str,
) -> tuple[float | None, float | None, float | None, int, int]:
    windows: list[tuple[float, float]] = []
    pair_count = 0
    triple_count = 0
    if pair_step is not None:
        lo = _safe_float(pair_step.get('pair_interval_lo'))
        hi = _safe_float(pair_step.get('pair_interval_hi'))
        if lo is not None and hi is not None:
            windows.append((lo, hi))
            pair_count += 1
    for step in triple_steps:
        parent = str(step.get('parent_label'))
        child = str(step.get('child_label'))
        gp = str(step.get('grandparent_label'))
        if (parent, child) == (left_label, right_label):
            lo = _safe_float(step.get('pair_interval_bc_lo'))
            hi = _safe_float(step.get('pair_interval_bc_hi'))
        elif (gp, parent) == (left_label, right_label):
            lo = _safe_float(step.get('pair_interval_ab_lo'))
            hi = _safe_float(step.get('pair_interval_ab_hi'))
        else:
            lo = hi = None
        if lo is not None and hi is not None:
            windows.append((lo, hi))
            triple_count += 1
        tri_lo = _safe_float(step.get('triple_interval_lo'))
        tri_hi = _safe_float(step.get('triple_interval_hi'))
        if tri_lo is not None and tri_hi is not None:
            windows.append((tri_lo, tri_hi))
            triple_count += 1
    lo, hi, width = _interval_intersection(windows)
    return lo, hi, width, pair_count, triple_count


def _edge_budget(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    pair_step: dict[str, Any] | None,
    anchor_interval: tuple[float | None, float | None, float | None],
    anchor_multiplier: float,
) -> float:
    left_center = float(left['transport_center'])
    right_center = float(right['transport_center'])
    left_radius = _local_radius(left)
    right_radius = _local_radius(right)
    fallback = abs(right_center - left_center) + left_radius + right_radius
    base = _safe_float(None if pair_step is None else pair_step.get('pair_step_bound'))
    base_budget = fallback if base is None else min(fallback, float(base))
    a_lo, a_hi, a_w = anchor_interval
    if a_lo is None or a_hi is None or a_w is None:
        return float(base_budget)
    anchor_center = 0.5 * (float(a_lo) + float(a_hi))
    anchor_budget = max(abs(left_center - anchor_center), abs(right_center - anchor_center)) + 0.5 * float(a_w)
    return float(min(base_budget, anchor_multiplier * anchor_budget))


def build_global_transport_potential_certificate(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    anchor_multiplier: float = 1.05,
) -> GlobalTransportPotentialCertificate:
    entries = _extract_transport_entries(ladder)
    entry_count = len(list(ladder.get('approximants', []) or []))
    usable = len(entries)
    if usable < 2:
        return GlobalTransportPotentialCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            entry_count=int(entry_count),
            usable_entry_count=int(usable),
            chain_labels=[],
            chain_qs=[],
            chain_ps=[],
            chain_length=0,
            edge_count=0,
            derivative_backed_fraction=None,
            tangent_backed_fraction=None,
            pair_anchor_fraction=None,
            triple_anchor_fraction=None,
            mean_supporting_triples_per_edge=None,
            raw_edge_budget_mean=None,
            monotone_edge_budget_mean=None,
            observed_monotone_ratio=None,
            geometric_tail_extension=None,
            global_intersection_lo=None,
            global_intersection_hi=None,
            global_intersection_width=None,
            last_node_interval_lo=None,
            last_node_interval_hi=None,
            last_node_interval_width=None,
            selected_limit_interval_lo=None,
            selected_limit_interval_hi=None,
            selected_limit_interval_width=None,
            theorem_status='global-transport-potential-incomplete',
            notes='Not enough transport-refined entries are available to build a ladder-global transport potential.',
            nodes=[],
        )

    chain = _longest_convergent_chain(entries, p_tolerance=p_tolerance)
    chain_labels = [str(e['label']) for e in chain]
    chain_qs = [int(e['q']) for e in chain]
    chain_ps = [int(e['p']) for e in chain]
    if len(chain) < min_chain_length:
        return GlobalTransportPotentialCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            entry_count=int(entry_count),
            usable_entry_count=int(usable),
            chain_labels=chain_labels,
            chain_qs=chain_qs,
            chain_ps=chain_ps,
            chain_length=len(chain),
            edge_count=max(0, len(chain) - 1),
            derivative_backed_fraction=None,
            tangent_backed_fraction=None,
            pair_anchor_fraction=None,
            triple_anchor_fraction=None,
            mean_supporting_triples_per_edge=None,
            raw_edge_budget_mean=None,
            monotone_edge_budget_mean=None,
            observed_monotone_ratio=None,
            geometric_tail_extension=None,
            global_intersection_lo=None,
            global_intersection_hi=None,
            global_intersection_width=None,
            last_node_interval_lo=None,
            last_node_interval_hi=None,
            last_node_interval_width=None,
            selected_limit_interval_lo=None,
            selected_limit_interval_hi=None,
            selected_limit_interval_width=None,
            theorem_status='global-transport-potential-incomplete',
            notes='A transport-refined convergent tail exists, but it is not yet long enough to support a ladder-global transport potential.',
            nodes=[],
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
    pair_anchor_flags: list[bool] = []
    triple_anchor_flags: list[bool] = []
    triple_support_counts: list[int] = []
    edge_info: list[dict[str, Any]] = []

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
        pair_anchor_flags.append(pair_anchor_count > 0)
        triple_anchor_flags.append(triple_anchor_count > 0)
        triple_support_counts.append(int(triple_anchor_count))
        edge_info.append(
            {
                'key': key,
                'pair_step': pair_step,
                'triple_steps': triples,
                'anchor_lo': anchor_lo,
                'anchor_hi': anchor_hi,
                'anchor_width': anchor_w,
                'pair_anchor_count': pair_anchor_count,
                'triple_anchor_count': triple_anchor_count,
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

    suffix_budgets = [0.0 for _ in chain]
    running = float(geometric_tail_extension)
    suffix_budgets[-1] = running
    for i in range(len(chain) - 2, -1, -1):
        running += float(monotone_edge_budgets[i])
        suffix_budgets[i] = float(running)

    node_intervals: list[tuple[float, float]] = []
    nodes: list[GlobalTransportPotentialNode] = []
    previous_width: float | None = None
    derivative_flags: list[bool] = []
    tangent_flags: list[bool] = []

    for idx, entry in enumerate(chain):
        center = float(entry['transport_center'])
        local_radius = float(_local_radius(entry))
        potential_radius = float(local_radius + suffix_budgets[idx])
        lo = float(center - potential_radius)
        hi = float(center + potential_radius)
        width = float(hi - lo)
        node_intervals.append((lo, hi))
        interval_ratio = None if previous_width in (None, 0.0) else float(width / max(previous_width, 1e-15))
        previous_width = width
        derivative_backed = bool(entry.get('derivative_backed'))
        tangent_backed = bool(entry.get('tangent_inclusion_success')) or bool(entry.get('interval_tangent_success'))
        derivative_flags.append(derivative_backed)
        tangent_flags.append(tangent_backed)
        nodes.append(
            GlobalTransportPotentialNode(
                label=str(entry['label']),
                p=int(entry['p']),
                q=int(entry['q']),
                transport_center=center,
                transport_lo=float(entry['transport_lo']),
                transport_hi=float(entry['transport_hi']),
                transport_width=float(entry['transport_width']),
                local_radius=local_radius,
                forward_edge_budget=None if idx >= len(edge_raw_budgets) else float(edge_raw_budgets[idx]),
                monotone_forward_edge_budget=None if idx >= len(monotone_edge_budgets) else float(monotone_edge_budgets[idx]),
                suffix_transport_budget=float(suffix_budgets[idx]),
                potential_radius=potential_radius,
                potential_interval_lo=lo,
                potential_interval_hi=hi,
                potential_interval_width=width,
                pair_anchor_count=0 if idx >= len(edge_info) else int(edge_info[idx]['pair_anchor_count']),
                triple_anchor_count=0 if idx >= len(edge_info) else int(edge_info[idx]['triple_anchor_count']),
                derivative_backed=derivative_backed,
                tangent_backed=tangent_backed,
                potential_interval_ratio_to_previous=interval_ratio,
            )
        )

    global_lo, global_hi, global_w = _interval_intersection(node_intervals)
    last_node = nodes[-1]

    pair_fraction = _fraction_true(pair_anchor_flags)
    triple_fraction = _fraction_true(triple_anchor_flags)
    strong_support = (
        global_lo is not None
        and global_hi is not None
        and (pair_fraction or 0.0) >= 0.75
        and (triple_fraction or 0.0) >= 0.5
        and observed_ratio < 1.0
    )
    partial_support = global_lo is not None and global_hi is not None

    if strong_support:
        status = 'global-transport-potential-strong'
        notes = (
            'A ladder-global transport potential was built from the convergent-family tail. '
            'Pairwise continuation budgets and overlapping triple constraints were aggregated into monotone edge budgets, '
            'yielding a single suffix transport potential whose node-wise intervals intersect nontrivially.'
        )
    elif partial_support:
        status = 'global-transport-potential-partial'
        notes = (
            'A ladder-global transport potential exists and produces a nonempty tail intersection, '
            'but the pair/triple support fractions are not yet strong enough to treat the resulting interval as a robust continuation-style bound.'
        )
    else:
        status = 'global-transport-potential-incomplete'
        notes = (
            'The pairwise and triple transport data do not yet aggregate into a nonempty ladder-global potential interval.'
        )

    return GlobalTransportPotentialCertificate(
        rho_target=None if rho_target is None else float(rho_target),
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
        mean_supporting_triples_per_edge=(None if not triple_support_counts else float(mean(triple_support_counts))),
        raw_edge_budget_mean=(None if not edge_raw_budgets else float(mean(edge_raw_budgets))),
        monotone_edge_budget_mean=(None if not monotone_edge_budgets else float(mean(monotone_edge_budgets))),
        observed_monotone_ratio=float(observed_ratio),
        geometric_tail_extension=float(geometric_tail_extension),
        global_intersection_lo=global_lo,
        global_intersection_hi=global_hi,
        global_intersection_width=global_w,
        last_node_interval_lo=float(last_node.potential_interval_lo),
        last_node_interval_hi=float(last_node.potential_interval_hi),
        last_node_interval_width=float(last_node.potential_interval_width),
        selected_limit_interval_lo=global_lo,
        selected_limit_interval_hi=global_hi,
        selected_limit_interval_width=global_w,
        theorem_status=status,
        notes=notes,
        nodes=nodes,
    )


__all__ = [
    'GlobalTransportPotentialNode',
    'GlobalTransportPotentialCertificate',
    'build_global_transport_potential_certificate',
]
