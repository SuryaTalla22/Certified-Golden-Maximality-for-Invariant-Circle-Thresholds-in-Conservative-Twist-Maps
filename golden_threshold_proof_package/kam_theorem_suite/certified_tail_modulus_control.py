from __future__ import annotations

"""Certified tail modulus for the convergent-family bridge.

This layer turns the Tail-Cauchy potential into an explicit *modulus of
remaining tail uncertainty* indexed by the starting ladder element.

The previous stage already produced, for each convergent in the certified tail,
a Cauchy interval together with a decomposition of the remaining suffix budget
by edge class.  What it did not yet expose as a first-class theorem-facing
object was the modulus itself:

* for each start index ``i`` in the convergent chain,
* how large can the unseen tail contribution still be,
* how is that tail radius decomposed by edge class, and
* does this modulus improve monotonically as the start index moves deeper into
  the ladder?

The result is a start-index-to-radius map that is closer in spirit to a true
Cauchy modulus.  It does not prove the full convergence theorem, but it makes
explicit that the bridge now carries a nonincreasing tail-control function
rather than only a single global interval.
"""

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any

from .tail_cauchy_potential_control import build_tail_cauchy_potential_certificate
from .transport_certified_limit_control import _interval_intersection


@dataclass
class CertifiedTailModulusNode:
    start_index: int
    label: str
    p: int
    q: int
    remaining_edge_count: int
    transport_center: float
    local_radius: float
    tail_modulus_triple_reinforced: float
    tail_modulus_pair_anchored: float
    tail_modulus_transport_fallback: float
    tail_modulus_geometric_tail: float
    tail_modulus_radius: float
    total_cauchy_radius: float
    tail_modulus_ratio_to_previous: float | None
    total_cauchy_ratio_to_previous: float | None
    modulus_interval_lo: float
    modulus_interval_hi: float
    modulus_interval_width: float
    derivative_backed: bool
    tangent_backed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CertifiedTailModulusCertificate:
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
    modulus_nonincreasing: bool
    total_cauchy_nonincreasing: bool
    classwise_modulus_nonincreasing: bool
    tail_modulus_observed_ratio: float | None
    total_cauchy_observed_ratio: float | None
    first_tail_modulus_radius: float | None
    last_tail_modulus_radius: float | None
    mean_tail_modulus_radius: float | None
    first_total_cauchy_radius: float | None
    last_total_cauchy_radius: float | None
    mean_total_cauchy_radius: float | None
    full_tail_triple_reinforced_budget: float | None
    full_tail_pair_anchored_budget: float | None
    full_tail_transport_fallback_budget: float | None
    full_tail_geometric_budget: float | None
    full_tail_budget: float | None
    suffix_modulus_intersection_lo: float | None
    suffix_modulus_intersection_hi: float | None
    suffix_modulus_intersection_width: float | None
    selected_limit_interval_lo: float | None
    selected_limit_interval_hi: float | None
    selected_limit_interval_width: float | None
    theorem_status: str
    notes: str
    nodes: list[CertifiedTailModulusNode]

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
            'modulus_nonincreasing': bool(self.modulus_nonincreasing),
            'total_cauchy_nonincreasing': bool(self.total_cauchy_nonincreasing),
            'classwise_modulus_nonincreasing': bool(self.classwise_modulus_nonincreasing),
            'tail_modulus_observed_ratio': self.tail_modulus_observed_ratio,
            'total_cauchy_observed_ratio': self.total_cauchy_observed_ratio,
            'first_tail_modulus_radius': self.first_tail_modulus_radius,
            'last_tail_modulus_radius': self.last_tail_modulus_radius,
            'mean_tail_modulus_radius': self.mean_tail_modulus_radius,
            'first_total_cauchy_radius': self.first_total_cauchy_radius,
            'last_total_cauchy_radius': self.last_total_cauchy_radius,
            'mean_total_cauchy_radius': self.mean_total_cauchy_radius,
            'full_tail_triple_reinforced_budget': self.full_tail_triple_reinforced_budget,
            'full_tail_pair_anchored_budget': self.full_tail_pair_anchored_budget,
            'full_tail_transport_fallback_budget': self.full_tail_transport_fallback_budget,
            'full_tail_geometric_budget': self.full_tail_geometric_budget,
            'full_tail_budget': self.full_tail_budget,
            'suffix_modulus_intersection_lo': self.suffix_modulus_intersection_lo,
            'suffix_modulus_intersection_hi': self.suffix_modulus_intersection_hi,
            'suffix_modulus_intersection_width': self.suffix_modulus_intersection_width,
            'selected_limit_interval_lo': self.selected_limit_interval_lo,
            'selected_limit_interval_hi': self.selected_limit_interval_hi,
            'selected_limit_interval_width': self.selected_limit_interval_width,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'nodes': [n.to_dict() for n in self.nodes],
        }


def _frac_true(vals: list[bool]) -> float | None:
    return None if not vals else float(sum(1 for v in vals if v) / len(vals))


def _nonincreasing(values: list[float], tol: float = 1e-15) -> bool:
    return all(float(values[i]) >= float(values[i + 1]) - tol for i in range(len(values) - 1))


def _observed_ratio(values: list[float]) -> float | None:
    ratios: list[float] = []
    for a, b in zip(values[:-1], values[1:]):
        if a > 0.0 and b >= 0.0:
            ratios.append(float(b / a))
    return None if not ratios else float(max(ratios))


def build_certified_tail_modulus_certificate(
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
) -> CertifiedTailModulusCertificate:
    tail = build_tail_cauchy_potential_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
    ).to_dict()

    nodes_in = list(tail.get('nodes', []) or [])
    if not nodes_in:
        return CertifiedTailModulusCertificate(
            rho_target=rho_target,
            family_label=family_label,
            entry_count=int(tail.get('entry_count', 0) or 0),
            usable_entry_count=int(tail.get('usable_entry_count', 0) or 0),
            chain_labels=[str(x) for x in tail.get('chain_labels', [])],
            chain_qs=[int(x) for x in tail.get('chain_qs', [])],
            chain_ps=[int(x) for x in tail.get('chain_ps', [])],
            chain_length=int(tail.get('chain_length', 0) or 0),
            edge_count=int(tail.get('edge_count', 0) or 0),
            derivative_backed_fraction=None,
            tangent_backed_fraction=None,
            modulus_nonincreasing=False,
            total_cauchy_nonincreasing=False,
            classwise_modulus_nonincreasing=False,
            tail_modulus_observed_ratio=None,
            total_cauchy_observed_ratio=None,
            first_tail_modulus_radius=None,
            last_tail_modulus_radius=None,
            mean_tail_modulus_radius=None,
            first_total_cauchy_radius=None,
            last_total_cauchy_radius=None,
            mean_total_cauchy_radius=None,
            full_tail_triple_reinforced_budget=tail.get('full_tail_triple_reinforced_budget'),
            full_tail_pair_anchored_budget=tail.get('full_tail_pair_anchored_budget'),
            full_tail_transport_fallback_budget=tail.get('full_tail_transport_fallback_budget'),
            full_tail_geometric_budget=tail.get('full_tail_geometric_budget'),
            full_tail_budget=tail.get('full_tail_budget'),
            suffix_modulus_intersection_lo=None,
            suffix_modulus_intersection_hi=None,
            suffix_modulus_intersection_width=None,
            selected_limit_interval_lo=tail.get('selected_limit_interval_lo'),
            selected_limit_interval_hi=tail.get('selected_limit_interval_hi'),
            selected_limit_interval_width=tail.get('selected_limit_interval_width'),
            theorem_status='certified-tail-modulus-incomplete',
            notes='The Tail-Cauchy layer did not yet produce a usable node chain, so no certified modulus could be extracted.',
            nodes=[],
        )

    nodes: list[CertifiedTailModulusNode] = []
    modulus_radii: list[float] = []
    cauchy_radii: list[float] = []
    derivative_flags: list[bool] = []
    tangent_flags: list[bool] = []
    previous_modulus: float | None = None
    previous_cauchy: float | None = None
    modulus_intervals: list[tuple[float, float]] = []
    triple_vals: list[float] = []
    pair_vals: list[float] = []
    fallback_vals: list[float] = []
    geometric_vals: list[float] = []

    for idx, raw in enumerate(nodes_in):
        triple = float(raw.get('suffix_triple_reinforced_budget', 0.0) or 0.0)
        pair = float(raw.get('suffix_pair_anchored_budget', 0.0) or 0.0)
        fallback = float(raw.get('suffix_transport_fallback_budget', 0.0) or 0.0)
        geometric = float(raw.get('suffix_geometric_tail_budget', 0.0) or 0.0)
        modulus = float(triple + pair + fallback + geometric)
        cauchy = float(raw.get('cauchy_radius', 0.0) or 0.0)
        lo = float(raw.get('cauchy_interval_lo'))
        hi = float(raw.get('cauchy_interval_hi'))
        width = float(raw.get('cauchy_interval_width'))
        modulus_intervals.append((lo, hi))
        modulus_ratio = None if previous_modulus in (None, 0.0) else float(modulus / max(previous_modulus, 1e-15))
        cauchy_ratio = None if previous_cauchy in (None, 0.0) else float(cauchy / max(previous_cauchy, 1e-15))
        previous_modulus = modulus
        previous_cauchy = cauchy
        modulus_radii.append(modulus)
        cauchy_radii.append(cauchy)
        triple_vals.append(triple)
        pair_vals.append(pair)
        fallback_vals.append(fallback)
        geometric_vals.append(geometric)
        derivative_backed = bool(raw.get('derivative_backed'))
        tangent_backed = bool(raw.get('tangent_backed'))
        derivative_flags.append(derivative_backed)
        tangent_flags.append(tangent_backed)
        nodes.append(
            CertifiedTailModulusNode(
                start_index=idx,
                label=str(raw.get('label')),
                p=int(raw.get('p')),
                q=int(raw.get('q')),
                remaining_edge_count=max(0, len(nodes_in) - idx - 1),
                transport_center=float(raw.get('transport_center')),
                local_radius=float(raw.get('local_radius', 0.0) or 0.0),
                tail_modulus_triple_reinforced=triple,
                tail_modulus_pair_anchored=pair,
                tail_modulus_transport_fallback=fallback,
                tail_modulus_geometric_tail=geometric,
                tail_modulus_radius=modulus,
                total_cauchy_radius=cauchy,
                tail_modulus_ratio_to_previous=modulus_ratio,
                total_cauchy_ratio_to_previous=cauchy_ratio,
                modulus_interval_lo=lo,
                modulus_interval_hi=hi,
                modulus_interval_width=width,
                derivative_backed=derivative_backed,
                tangent_backed=tangent_backed,
            )
        )

    inter_lo, inter_hi, inter_w = _interval_intersection(modulus_intervals)
    modulus_nonincreasing = _nonincreasing(modulus_radii)
    classwise_nonincreasing = all(
        _nonincreasing(vals)
        for vals in (triple_vals, pair_vals, fallback_vals, geometric_vals)
    )
    # allow some slack because local radii may fluctuate mildly even when the tail modulus tightens.
    total_cauchy_nonincreasing = all(
        float(cauchy_radii[i + 1]) <= float(cauchy_radii[i]) * float(total_radius_growth_slack) + 1e-15
        for i in range(len(cauchy_radii) - 1)
    )

    strong = (
        str(tail.get('theorem_status', '')).startswith('tail-cauchy-potential-strong')
        and inter_lo is not None
        and modulus_nonincreasing
        and classwise_nonincreasing
        and total_cauchy_nonincreasing
        and ((_observed_ratio(modulus_radii) or 0.0) < 1.0)
    )
    partial = inter_lo is not None and modulus_nonincreasing

    if strong:
        status = 'certified-tail-modulus-strong'
        notes = (
            'An explicit start-index-to-radius certified tail modulus was extracted from the Tail-Cauchy layer. '
            'The remaining-tail radius tightens monotonically along the convergent chain, its classwise components are themselves monotone, '
            'and the resulting modulus intervals intersect nontrivially.'
        )
    elif partial:
        status = 'certified-tail-modulus-partial'
        notes = (
            'A start-index-to-radius tail modulus exists and is monotone, but the full set of classwise or total-radius regularity checks is not yet strong enough '
            'to treat it as a robust continuation-style modulus.'
        )
    else:
        status = 'certified-tail-modulus-incomplete'
        notes = 'The extracted start-index tail radii do not yet form a usable certified modulus.'

    return CertifiedTailModulusCertificate(
        rho_target=rho_target,
        family_label=family_label,
        entry_count=int(tail.get('entry_count', 0) or 0),
        usable_entry_count=int(tail.get('usable_entry_count', 0) or 0),
        chain_labels=[str(x) for x in tail.get('chain_labels', [])],
        chain_qs=[int(x) for x in tail.get('chain_qs', [])],
        chain_ps=[int(x) for x in tail.get('chain_ps', [])],
        chain_length=int(tail.get('chain_length', 0) or 0),
        edge_count=int(tail.get('edge_count', 0) or 0),
        derivative_backed_fraction=_frac_true(derivative_flags),
        tangent_backed_fraction=_frac_true(tangent_flags),
        modulus_nonincreasing=bool(modulus_nonincreasing),
        total_cauchy_nonincreasing=bool(total_cauchy_nonincreasing),
        classwise_modulus_nonincreasing=bool(classwise_nonincreasing),
        tail_modulus_observed_ratio=_observed_ratio(modulus_radii),
        total_cauchy_observed_ratio=_observed_ratio(cauchy_radii),
        first_tail_modulus_radius=(None if not modulus_radii else float(modulus_radii[0])),
        last_tail_modulus_radius=(None if not modulus_radii else float(modulus_radii[-1])),
        mean_tail_modulus_radius=(None if not modulus_radii else float(mean(modulus_radii))),
        first_total_cauchy_radius=(None if not cauchy_radii else float(cauchy_radii[0])),
        last_total_cauchy_radius=(None if not cauchy_radii else float(cauchy_radii[-1])),
        mean_total_cauchy_radius=(None if not cauchy_radii else float(mean(cauchy_radii))),
        full_tail_triple_reinforced_budget=tail.get('full_tail_triple_reinforced_budget'),
        full_tail_pair_anchored_budget=tail.get('full_tail_pair_anchored_budget'),
        full_tail_transport_fallback_budget=tail.get('full_tail_transport_fallback_budget'),
        full_tail_geometric_budget=tail.get('full_tail_geometric_budget'),
        full_tail_budget=tail.get('full_tail_budget'),
        suffix_modulus_intersection_lo=inter_lo,
        suffix_modulus_intersection_hi=inter_hi,
        suffix_modulus_intersection_width=inter_w,
        selected_limit_interval_lo=inter_lo,
        selected_limit_interval_hi=inter_hi,
        selected_limit_interval_width=inter_w,
        theorem_status=status,
        notes=notes,
        nodes=nodes,
    )


__all__ = [
    'CertifiedTailModulusNode',
    'CertifiedTailModulusCertificate',
    'build_certified_tail_modulus_certificate',
]
