from __future__ import annotations

"""Explicit Theorem V error-law packaging.

This module is meant to *compress* the long rational-to-irrational bridge stack
into one theorem-facing object.

The earlier stages in this bundle produced a sequence of increasingly structured
limit intervals and tail-modulus certificates:

* fit-based q-tail envelopes,
* branch-certified windows,
* nested subladder consistency,
* convergent-family transport control,
* pairwise / triple transport compatibility,
* global transport potentials,
* tail-Cauchy moduli,
* rate-aware tail laws,
* golden-recurrence laws, and
* edge-class-weighted golden recurrence laws.

That layering is valuable, but it still leaves Theorem V spread across many
objects.  The goal here is to collapse the strongest currently available data
into a *single explicit error package* with two outputs:

1. a compatible irrational-threshold interval obtained from the intersection of
   the strongest available theorem-facing limit layers; and
2. a per-convergent error law of the form

       |K_{p_n/q_n} - K_*| <= E(q_n),

   where ``K_*`` is any value inside the compatible interval.

This is still not the final theorem, because the compatible interval is built
from the existing certified bridge layers rather than from a finished
continuation theorem in function space.  It is, however, the strongest compact
Theorem-V object currently supported by the codebase.
"""

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Iterable, Mapping, Sequence

from .branch_certified_limit_control import build_branch_certified_irrational_limit_certificate
from .certified_tail_modulus_control import build_certified_tail_modulus_certificate
from .convergent_family_limit_control import build_convergent_family_limit_certificate
from .edge_class_weighted_golden_rate_control import build_edge_class_weighted_golden_rate_certificate
from .global_transport_potential_control import build_global_transport_potential_certificate
from .golden_recurrence_rate_control import build_golden_recurrence_rate_certificate
from .irrational_limit_control import build_rational_irrational_convergence_certificate
from .nested_subladder_limit_control import build_nested_subladder_limit_certificate
from .pairwise_transport_chain_control import build_pairwise_transport_chain_limit_certificate
from .rate_aware_tail_modulus_control import build_rate_aware_tail_modulus_certificate
from .tail_cauchy_potential_control import build_tail_cauchy_potential_certificate
from .transport_certified_limit_control import build_transport_certified_limit_certificate
from .transport_slope_weighted_golden_rate_control import build_transport_slope_weighted_golden_rate_certificate
from .triple_transport_cocycle_control import build_triple_transport_cocycle_limit_certificate


@dataclass
class TheoremVExplicitErrorNode:
    start_index: int
    label: str
    p: int
    q: int
    transport_center: float
    local_radius: float
    local_interval_lo: float
    local_interval_hi: float
    certificate_tail_radius: float | None
    certificate_total_radius: float | None
    certificate_interval_lo: float | None
    certificate_interval_hi: float | None
    compatible_error_radius: float | None
    q_power_tail_radius: float
    raw_total_error_radius: float
    monotone_total_error_radius: float
    raw_interval_lo: float
    raw_interval_hi: float
    monotone_interval_lo: float
    monotone_interval_hi: float
    dominates_compatible_error: bool | None
    dominates_certificate_total_radius: bool | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVExplicitErrorCertificate:
    rho_target: float | None
    family_label: str | None
    chain_labels: list[str]
    chain_qs: list[int]
    chain_ps: list[int]
    chain_length: int
    compatible_layer_names: list[str]
    compatible_layer_count: int
    compatible_limit_interval_lo: float | None
    compatible_limit_interval_hi: float | None
    compatible_limit_interval_width: float | None
    chosen_q_power_exponent: float | None
    q_power_anchor_q: int | None
    q_power_anchor_tail_constant: float | None
    q_power_model_source: str
    q_power_tail_dominates_certificate_tail: bool
    compatible_interval_nonempty: bool
    raw_error_law_nonincreasing: bool
    monotone_error_law_nonincreasing: bool
    active_bounds_dominate_compatible_errors: bool
    active_bounds_dominate_certificate_totals: bool
    first_raw_total_error_radius: float | None
    last_raw_total_error_radius: float | None
    first_monotone_total_error_radius: float | None
    last_monotone_total_error_radius: float | None
    late_coherent_suffix_start_index: int | None
    late_coherent_suffix_start_q: int | None
    late_coherent_suffix_start_label: str | None
    late_coherent_suffix_length: int
    late_coherent_suffix_labels: list[str]
    late_coherent_suffix_qs: list[int]
    late_coherent_suffix_interval_lo: float | None
    late_coherent_suffix_interval_hi: float | None
    late_coherent_suffix_interval_width: float | None
    late_coherent_suffix_first_raw_total_error_radius: float | None
    late_coherent_suffix_last_raw_total_error_radius: float | None
    late_coherent_suffix_contraction_ratio: float | None
    late_coherent_suffix_raw_error_law_nonincreasing: bool
    late_coherent_suffix_contracting: bool
    late_coherent_suffix_status: str
    theorem_status: str
    notes: str
    layer_intervals: dict[str, dict[str, float | None]]
    nodes: list[TheoremVExplicitErrorNode]

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho_target': self.rho_target,
            'family_label': self.family_label,
            'chain_labels': [str(x) for x in self.chain_labels],
            'chain_qs': [int(x) for x in self.chain_qs],
            'chain_ps': [int(x) for x in self.chain_ps],
            'chain_length': int(self.chain_length),
            'compatible_layer_names': [str(x) for x in self.compatible_layer_names],
            'compatible_layer_count': int(self.compatible_layer_count),
            'compatible_limit_interval_lo': self.compatible_limit_interval_lo,
            'compatible_limit_interval_hi': self.compatible_limit_interval_hi,
            'compatible_limit_interval_width': self.compatible_limit_interval_width,
            'chosen_q_power_exponent': self.chosen_q_power_exponent,
            'q_power_anchor_q': self.q_power_anchor_q,
            'q_power_anchor_tail_constant': self.q_power_anchor_tail_constant,
            'q_power_model_source': str(self.q_power_model_source),
            'q_power_tail_dominates_certificate_tail': bool(self.q_power_tail_dominates_certificate_tail),
            'compatible_interval_nonempty': bool(self.compatible_interval_nonempty),
            'raw_error_law_nonincreasing': bool(self.raw_error_law_nonincreasing),
            'monotone_error_law_nonincreasing': bool(self.monotone_error_law_nonincreasing),
            'active_bounds_dominate_compatible_errors': bool(self.active_bounds_dominate_compatible_errors),
            'active_bounds_dominate_certificate_totals': bool(self.active_bounds_dominate_certificate_totals),
            'first_raw_total_error_radius': self.first_raw_total_error_radius,
            'last_raw_total_error_radius': self.last_raw_total_error_radius,
            'first_monotone_total_error_radius': self.first_monotone_total_error_radius,
            'last_monotone_total_error_radius': self.last_monotone_total_error_radius,
            'late_coherent_suffix_start_index': self.late_coherent_suffix_start_index,
            'late_coherent_suffix_start_q': self.late_coherent_suffix_start_q,
            'late_coherent_suffix_start_label': self.late_coherent_suffix_start_label,
            'late_coherent_suffix_length': int(self.late_coherent_suffix_length),
            'late_coherent_suffix_labels': [str(x) for x in self.late_coherent_suffix_labels],
            'late_coherent_suffix_qs': [int(x) for x in self.late_coherent_suffix_qs],
            'late_coherent_suffix_interval_lo': self.late_coherent_suffix_interval_lo,
            'late_coherent_suffix_interval_hi': self.late_coherent_suffix_interval_hi,
            'late_coherent_suffix_interval_width': self.late_coherent_suffix_interval_width,
            'late_coherent_suffix_first_raw_total_error_radius': self.late_coherent_suffix_first_raw_total_error_radius,
            'late_coherent_suffix_last_raw_total_error_radius': self.late_coherent_suffix_last_raw_total_error_radius,
            'late_coherent_suffix_contraction_ratio': self.late_coherent_suffix_contraction_ratio,
            'late_coherent_suffix_raw_error_law_nonincreasing': bool(self.late_coherent_suffix_raw_error_law_nonincreasing),
            'late_coherent_suffix_contracting': bool(self.late_coherent_suffix_contracting),
            'late_coherent_suffix_status': str(self.late_coherent_suffix_status),
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'layer_intervals': {str(k): dict(v) for k, v in self.layer_intervals.items()},
            'nodes': [node.to_dict() for node in self.nodes],
        }


_INTERVAL_KEYS: dict[str, tuple[str, str]] = {
    'fit_q_tail': ('limit_interval_lo', 'limit_interval_hi'),
    'branch_certified': ('selected_limit_interval_lo', 'selected_limit_interval_hi'),
    'nested_subladder': ('final_interval_lo', 'final_interval_hi'),
    'convergent_family': ('limit_interval_lo', 'limit_interval_hi'),
    'transport_certified': ('limit_interval_lo', 'limit_interval_hi'),
    'pairwise_transport': ('limit_interval_lo', 'limit_interval_hi'),
    'triple_transport_cocycle': ('limit_interval_lo', 'limit_interval_hi'),
    'global_transport_potential': ('selected_limit_interval_lo', 'selected_limit_interval_hi'),
    'tail_cauchy_potential': ('selected_limit_interval_lo', 'selected_limit_interval_hi'),
    'certified_tail_modulus': ('selected_limit_interval_lo', 'selected_limit_interval_hi'),
    'rate_aware_tail_modulus': ('modulus_rate_intersection_lo', 'modulus_rate_intersection_hi'),
    'golden_recurrence_rate': ('rate_golden_intersection_lo', 'rate_golden_intersection_hi'),
    'transport_slope_weighted_golden_rate': ('weighted_golden_intersection_lo', 'weighted_golden_intersection_hi'),
    'edge_class_weighted_golden_rate': ('edge_class_transport_intersection_lo', 'edge_class_transport_intersection_hi'),
}


def _nonincreasing(values: Sequence[float], tol: float = 1e-15) -> bool:
    return all(float(values[i]) >= float(values[i + 1]) - tol for i in range(len(values) - 1))


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except Exception:
        return None
    return out if isfinite(out) else None




def _is_strong_status(payload: Mapping[str, Any] | None) -> bool:
    return str((payload or {}).get('theorem_status', '')).endswith('-strong')

def _interval_intersection(
    a_lo: float | None,
    a_hi: float | None,
    b_lo: float | None,
    b_hi: float | None,
) -> tuple[float | None, float | None, float | None]:
    if a_lo is None or a_hi is None or b_lo is None or b_hi is None:
        return None, None, None
    lo = max(float(a_lo), float(b_lo))
    hi = min(float(a_hi), float(b_hi))
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _extract_interval(payload: Mapping[str, Any] | None, lo_key: str, hi_key: str) -> tuple[float | None, float | None, float | None]:
    if not payload:
        return None, None, None
    lo = _safe_float(payload.get(lo_key))
    hi = _safe_float(payload.get(hi_key))
    if lo is None or hi is None:
        return None, None, None
    if hi < lo:
        return None, None, None
    return lo, hi, float(hi - lo)


def _extract_layer_intervals(layer_payloads: Mapping[str, Mapping[str, Any] | None]) -> tuple[dict[str, dict[str, float | None]], list[str], tuple[float | None, float | None, float | None]]:
    intervals: dict[str, dict[str, float | None]] = {}
    compatible_layers: list[str] = []
    current_lo: float | None = None
    current_hi: float | None = None
    current_w: float | None = None

    for name, payload in layer_payloads.items():
        lo_key, hi_key = _INTERVAL_KEYS[name]
        lo, hi, width = _extract_interval(payload, lo_key, hi_key)
        intervals[name] = {'lo': lo, 'hi': hi, 'width': width}
        if lo is None or hi is None:
            continue
        if current_lo is None or current_hi is None:
            current_lo, current_hi, current_w = lo, hi, width
            compatible_layers.append(name)
            continue
        new_lo, new_hi, new_w = _interval_intersection(current_lo, current_hi, lo, hi)
        if new_lo is not None and new_hi is not None:
            current_lo, current_hi, current_w = new_lo, new_hi, new_w
            compatible_layers.append(name)

    return intervals, compatible_layers, (current_lo, current_hi, current_w)


def _select_preferred_nodes(
    edge_class_weighted: Mapping[str, Any] | None,
    transport_slope_weighted: Mapping[str, Any] | None,
    golden_recurrence: Mapping[str, Any] | None,
    rate_aware: Mapping[str, Any] | None,
) -> tuple[list[dict[str, Any]], str]:
    for source_name, payload in (
        ('edge_class_weighted_golden_rate', edge_class_weighted),
        ('transport_slope_weighted_golden_rate', transport_slope_weighted),
        ('golden_recurrence_rate', golden_recurrence),
        ('rate_aware_tail_modulus', rate_aware),
    ):
        nodes = list((payload or {}).get('nodes') or [])
        if nodes:
            return [dict(node) for node in nodes], source_name
    return [], 'none'


def _select_exponent_source(
    edge_class_weighted: Mapping[str, Any] | None,
    transport_slope_weighted: Mapping[str, Any] | None,
    golden_recurrence: Mapping[str, Any] | None,
    rate_aware: Mapping[str, Any] | None,
) -> tuple[float | None, str]:
    choices = [
        (_safe_float((edge_class_weighted or {}).get('chosen_edge_class_step_exponent')), 'edge_class_weighted_golden_rate'),
        (_safe_float((transport_slope_weighted or {}).get('chosen_weighted_step_exponent')), 'transport_slope_weighted_golden_rate'),
        (_safe_float((golden_recurrence or {}).get('chosen_step_exponent')), 'golden_recurrence_rate'),
        (_safe_float((rate_aware or {}).get('chosen_rate_exponent')), 'rate_aware_tail_modulus'),
    ]
    for exponent, label in choices:
        if exponent is not None and exponent > 0.0:
            return float(exponent), label
    return None, 'constant-fallback'


def _q_power_tail_model(nodes: Sequence[Mapping[str, Any]], exponent: float | None) -> tuple[int | None, float | None, list[float], bool]:
    if not nodes:
        return None, None, [], False
    qs = [int(node.get('q', 0)) for node in nodes]
    if any(q <= 0 for q in qs):
        return None, None, [], False
    anchor_q = int(min(qs))
    beta = float(exponent) if exponent is not None and exponent > 0.0 else 0.0

    observed_tail: list[float] = []
    for node in nodes:
        tail = _safe_float(node.get('edge_class_weighted_tail_radius'))
        if tail is None:
            tail = _safe_float(node.get('weighted_golden_tail_modulus_radius'))
        if tail is None:
            tail = _safe_float(node.get('golden_tail_modulus_radius'))
        if tail is None:
            tail = _safe_float(node.get('rate_tail_modulus_radius'))
        if tail is None:
            tail = _safe_float(node.get('actual_tail_modulus_radius'))
        observed_tail.append(max(float(tail or 0.0), 0.0))

    if beta > 0.0:
        constants = [tail * (int(node.get('q', anchor_q)) / anchor_q) ** beta for tail, node in zip(observed_tail, nodes)]
        anchor_constant = max(constants) if constants else max(observed_tail, default=0.0)
    else:
        anchor_constant = max(observed_tail, default=0.0)

    predicted = [float(anchor_constant * (anchor_q / int(node.get('q', anchor_q))) ** beta) if beta > 0.0 else float(anchor_constant) for node in nodes]
    dominates = all(pred + 1e-15 >= obs for pred, obs in zip(predicted, observed_tail))
    return anchor_q, float(anchor_constant), predicted, bool(dominates)


def _compatible_error_radius(local_lo: float, local_hi: float, target_lo: float | None, target_hi: float | None) -> float | None:
    if target_lo is None or target_hi is None:
        return None
    return float(max(abs(float(local_lo) - float(target_hi)), abs(float(local_hi) - float(target_lo))))



def _multi_interval_intersection(intervals: Sequence[tuple[float | None, float | None]]) -> tuple[float | None, float | None, float | None]:
    usable = [(float(lo), float(hi)) for lo, hi in intervals if lo is not None and hi is not None]
    if not usable:
        return None, None, None
    lo = max(lo for lo, _ in usable)
    hi = min(hi for _, hi in usable)
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _raw_suffix_contracting(widths: Sequence[float], tol: float = 1e-15) -> bool:
    if len(widths) < 2:
        return False
    if _nonincreasing(widths, tol=tol):
        return True
    return len(widths) >= 3 and float(widths[-1]) <= 0.8 * min(float(x) for x in widths[:-1]) + tol


def _select_late_coherent_suffix(
    nodes: Sequence[TheoremVExplicitErrorNode],
    compatible_lo: float | None,
    compatible_hi: float | None,
    *,
    min_suffix_len: int = 3,
) -> dict[str, Any]:
    candidates: list[tuple[int, float, int, dict[str, Any]]] = []
    for start in range(len(nodes)):
        suffix = list(nodes[start:])
        if len(suffix) < max(2, int(min_suffix_len)):
            continue
        raw_intervals = [(node.raw_interval_lo, node.raw_interval_hi) for node in suffix]
        intervals = [(compatible_lo, compatible_hi)] + raw_intervals if compatible_lo is not None and compatible_hi is not None else raw_intervals
        witness_lo, witness_hi, witness_width = _multi_interval_intersection(intervals)
        if witness_lo is None or witness_hi is None:
            continue
        raw_widths = [float(node.raw_total_error_radius) * 2.0 for node in suffix]
        raw_nonincreasing = _nonincreasing(raw_widths)
        contracting = _raw_suffix_contracting(raw_widths)
        contraction_ratio = None
        if raw_widths and raw_widths[-1] > 0.0:
            contraction_ratio = float(max(raw_widths[:-1]) / raw_widths[-1]) if len(raw_widths) >= 2 else 1.0
        payload = {
            'start_index': int(suffix[0].start_index),
            'start_q': int(suffix[0].q),
            'start_label': str(suffix[0].label),
            'length': int(len(suffix)),
            'labels': [str(node.label) for node in suffix],
            'qs': [int(node.q) for node in suffix],
            'interval_lo': float(witness_lo),
            'interval_hi': float(witness_hi),
            'interval_width': float(witness_width),
            'first_raw_total_error_radius': float(raw_widths[0] * 0.5),
            'last_raw_total_error_radius': float(raw_widths[-1] * 0.5),
            'contraction_ratio': contraction_ratio,
            'raw_error_law_nonincreasing': bool(raw_nonincreasing),
            'contracting': bool(contracting),
        }
        # Prefer contracting suffixes, then smaller witness intervals, then deeper starts.
        candidates.append((0 if contracting else 1, float(witness_width), -int(suffix[0].start_index), payload))

    if not candidates:
        return {
            'start_index': None,
            'start_q': None,
            'start_label': None,
            'length': 0,
            'labels': [],
            'qs': [],
            'interval_lo': None,
            'interval_hi': None,
            'interval_width': None,
            'first_raw_total_error_radius': None,
            'last_raw_total_error_radius': None,
            'contraction_ratio': None,
            'raw_error_law_nonincreasing': False,
            'contracting': False,
            'status': 'late-coherent-suffix-missing',
        }

    payload = sorted(candidates, key=lambda row: (row[0], row[1], row[2]))[0][3]
    payload['status'] = 'late-coherent-suffix-strong' if payload['contracting'] else 'late-coherent-suffix-partial'
    return payload


def build_theorem_v_explicit_error_certificate(
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
    # optional precomputed layers to avoid recomputation in higher-level bridges
    convergence_control: Mapping[str, Any] | None = None,
    branch_certified_control: Mapping[str, Any] | None = None,
    nested_subladder_control: Mapping[str, Any] | None = None,
    convergent_family_control: Mapping[str, Any] | None = None,
    transport_certified_control: Mapping[str, Any] | None = None,
    pairwise_transport_control: Mapping[str, Any] | None = None,
    triple_transport_cocycle_control: Mapping[str, Any] | None = None,
    global_transport_potential_control: Mapping[str, Any] | None = None,
    tail_cauchy_potential_control: Mapping[str, Any] | None = None,
    certified_tail_modulus_control: Mapping[str, Any] | None = None,
    rate_aware_tail_modulus_control: Mapping[str, Any] | None = None,
    golden_recurrence_rate_control: Mapping[str, Any] | None = None,
    transport_slope_weighted_golden_rate_control: Mapping[str, Any] | None = None,
    edge_class_weighted_golden_rate_control: Mapping[str, Any] | None = None,
) -> TheoremVExplicitErrorCertificate:
    refined = dict(refined or {})
    asymptotic_audit = dict(asymptotic_audit or {})

    convergence = dict(convergence_control or build_rational_irrational_convergence_certificate(
        ladder,
        refined=refined,
        asymptotic_audit=asymptotic_audit,
        rho_target=rho_target,
        family_label=family_label,
        min_members=min_members,
    ).to_dict())
    branch_certified = dict(branch_certified_control or build_branch_certified_irrational_limit_certificate(
        ladder,
        refined=refined,
        asymptotic_audit=asymptotic_audit,
        rho_target=rho_target,
        family_label=family_label,
        min_members=min_members,
    ).to_dict())
    nested_subladder = dict(nested_subladder_control or build_nested_subladder_limit_certificate(
        ladder,
        refined=refined,
        asymptotic_audit=asymptotic_audit,
        rho_target=rho_target,
        family_label=family_label,
        min_members=min_members,
        nesting_tolerance=nesting_tolerance,
        cauchy_multiplier=cauchy_multiplier,
    ).to_dict())
    convergent_family = dict(convergent_family_control or build_convergent_family_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        nesting_tolerance=nesting_tolerance,
        contraction_cap=contraction_cap,
        min_overlap_fraction=min_overlap_fraction,
    ).to_dict())
    transport_certified = dict(transport_certified_control or build_transport_certified_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        min_overlap_fraction=min_overlap_fraction,
    ).to_dict())
    pairwise_transport = dict(pairwise_transport_control or build_pairwise_transport_chain_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        min_overlap_fraction=min_overlap_fraction,
        compatibility_multiplier=compatibility_multiplier,
    ).to_dict())
    triple_transport_cocycle = dict(triple_transport_cocycle_control or build_triple_transport_cocycle_limit_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        min_overlap_fraction=min_overlap_fraction,
        compatibility_multiplier=compatibility_multiplier,
        cocycle_multiplier=cocycle_multiplier,
    ).to_dict())
    global_transport_potential = dict(global_transport_potential_control or build_global_transport_potential_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
    ).to_dict())
    tail_cauchy_potential = dict(tail_cauchy_potential_control or build_tail_cauchy_potential_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
    ).to_dict())
    certified_tail_modulus = dict(certified_tail_modulus_control or build_certified_tail_modulus_certificate(
        ladder,
        rho_target=rho_target,
        family_label=family_label,
        min_chain_length=min_chain_length,
        p_tolerance=p_tolerance,
        contraction_cap=contraction_cap,
        anchor_multiplier=anchor_multiplier,
        fallback_share_cap=fallback_share_cap,
        total_radius_growth_slack=total_radius_growth_slack,
    ).to_dict())
    rate_aware_tail_modulus = dict(rate_aware_tail_modulus_control or build_rate_aware_tail_modulus_certificate(
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
    ).to_dict())
    golden_recurrence_rate = dict(golden_recurrence_rate_control or build_golden_recurrence_rate_certificate(
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
    ).to_dict())
    transport_slope_weighted_golden_rate = dict(transport_slope_weighted_golden_rate_control or build_transport_slope_weighted_golden_rate_certificate(
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
    ).to_dict())
    edge_class_weighted = dict(edge_class_weighted_golden_rate_control or build_edge_class_weighted_golden_rate_certificate(
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
    ).to_dict())

    layer_payloads: dict[str, Mapping[str, Any] | None] = {
        'fit_q_tail': convergence,
        'branch_certified': branch_certified,
        'nested_subladder': nested_subladder,
        'convergent_family': convergent_family,
        'transport_certified': transport_certified,
        'pairwise_transport': pairwise_transport,
        'triple_transport_cocycle': triple_transport_cocycle,
        'global_transport_potential': global_transport_potential,
        'tail_cauchy_potential': tail_cauchy_potential,
        'certified_tail_modulus': certified_tail_modulus,
        'rate_aware_tail_modulus': rate_aware_tail_modulus,
        'golden_recurrence_rate': golden_recurrence_rate,
        'transport_slope_weighted_golden_rate': transport_slope_weighted_golden_rate,
        'edge_class_weighted_golden_rate': edge_class_weighted,
    }
    layer_intervals, compatible_layers, compatible_interval = _extract_layer_intervals(layer_payloads)
    compatible_lo, compatible_hi, compatible_width = compatible_interval

    preferred_nodes, q_model_source = _select_preferred_nodes(
        edge_class_weighted,
        transport_slope_weighted_golden_rate,
        golden_recurrence_rate,
        rate_aware_tail_modulus,
    )
    exponent, exponent_source = _select_exponent_source(
        edge_class_weighted,
        transport_slope_weighted_golden_rate,
        golden_recurrence_rate,
        rate_aware_tail_modulus,
    )
    anchor_q, anchor_constant, q_power_tail_radii, q_power_tail_dominates_certificate_tail = _q_power_tail_model(preferred_nodes, exponent)

    raw_nodes: list[TheoremVExplicitErrorNode] = []
    raw_total_radii: list[float] = []
    compatible_error_flags: list[bool] = []
    certificate_total_flags: list[bool] = []

    for idx, node in enumerate(preferred_nodes):
        center = float(_safe_float(node.get('transport_center')) or 0.0)
        local_radius = float(max(_safe_float(node.get('local_radius')) or 0.0, 0.0))
        local_lo = float(center - local_radius)
        local_hi = float(center + local_radius)

        certificate_tail_radius = _safe_float(node.get('edge_class_weighted_tail_radius'))
        if certificate_tail_radius is None:
            certificate_tail_radius = _safe_float(node.get('weighted_golden_tail_modulus_radius'))
        if certificate_tail_radius is None:
            certificate_tail_radius = _safe_float(node.get('golden_tail_modulus_radius'))
        if certificate_tail_radius is None:
            certificate_tail_radius = _safe_float(node.get('rate_tail_modulus_radius'))
        if certificate_tail_radius is None:
            certificate_tail_radius = _safe_float(node.get('actual_tail_modulus_radius'))

        certificate_total_radius = _safe_float(node.get('edge_class_weighted_total_cauchy_radius'))
        if certificate_total_radius is None:
            certificate_total_radius = _safe_float(node.get('weighted_golden_total_cauchy_radius'))
        if certificate_total_radius is None:
            certificate_total_radius = _safe_float(node.get('golden_total_cauchy_radius'))
        if certificate_total_radius is None:
            certificate_total_radius = _safe_float(node.get('rate_total_cauchy_radius'))
        if certificate_total_radius is None:
            certificate_total_radius = local_radius + float(certificate_tail_radius or 0.0)

        certificate_interval_lo = None if certificate_total_radius is None else float(center - certificate_total_radius)
        certificate_interval_hi = None if certificate_total_radius is None else float(center + certificate_total_radius)

        compatible_error = _compatible_error_radius(local_lo, local_hi, compatible_lo, compatible_hi)
        q_tail = float(q_power_tail_radii[idx]) if idx < len(q_power_tail_radii) else float(max(certificate_tail_radius or 0.0, 0.0))
        raw_total = max(
            float(local_radius + q_tail),
            float(compatible_error or 0.0),
            float(certificate_total_radius or 0.0),
        )
        raw_total_radii.append(float(raw_total))

        dominates_compatible_error = None if compatible_error is None else bool(raw_total + 1e-15 >= compatible_error)
        dominates_certificate_total = None if certificate_total_radius is None else bool(raw_total + 1e-15 >= certificate_total_radius)
        compatible_error_flags.append(True if dominates_compatible_error is None else dominates_compatible_error)
        certificate_total_flags.append(True if dominates_certificate_total is None else dominates_certificate_total)

        raw_nodes.append(
            TheoremVExplicitErrorNode(
                start_index=int(node.get('start_index', idx)),
                label=str(node.get('label', f"{node.get('p', 0)}/{node.get('q', 0)}")),
                p=int(node.get('p', 0)),
                q=int(node.get('q', 0)),
                transport_center=center,
                local_radius=local_radius,
                local_interval_lo=local_lo,
                local_interval_hi=local_hi,
                certificate_tail_radius=certificate_tail_radius,
                certificate_total_radius=certificate_total_radius,
                certificate_interval_lo=certificate_interval_lo,
                certificate_interval_hi=certificate_interval_hi,
                compatible_error_radius=compatible_error,
                q_power_tail_radius=q_tail,
                raw_total_error_radius=float(raw_total),
                monotone_total_error_radius=float(raw_total),
                raw_interval_lo=float(center - raw_total),
                raw_interval_hi=float(center + raw_total),
                monotone_interval_lo=float(center - raw_total),
                monotone_interval_hi=float(center + raw_total),
                dominates_compatible_error=dominates_compatible_error,
                dominates_certificate_total_radius=dominates_certificate_total,
            )
        )

    monotone_radii = list(raw_total_radii)
    for i in range(len(monotone_radii) - 2, -1, -1):
        monotone_radii[i] = max(monotone_radii[i], monotone_radii[i + 1])
    for node, radius in zip(raw_nodes, monotone_radii):
        node.monotone_total_error_radius = float(radius)
        node.monotone_interval_lo = float(node.transport_center - radius)
        node.monotone_interval_hi = float(node.transport_center + radius)

    raw_nonincreasing = _nonincreasing(raw_total_radii) if raw_total_radii else False
    monotone_nonincreasing = _nonincreasing(monotone_radii) if monotone_radii else False
    compatible_interval_nonempty = compatible_lo is not None and compatible_hi is not None
    active_dominate_compatible = bool(compatible_error_flags) and all(compatible_error_flags)
    active_dominate_certificate = bool(certificate_total_flags) and all(certificate_total_flags)
    late_coherent_suffix = _select_late_coherent_suffix(raw_nodes, compatible_lo, compatible_hi, min_suffix_len=max(3, min_chain_length // 2))

    chain_length = len(raw_nodes)
    if chain_length >= max(min_chain_length, 4) and compatible_interval_nonempty and monotone_nonincreasing and active_dominate_compatible and active_dominate_certificate:
        theorem_status = 'theorem-v-explicit-error-law-strong'
    elif chain_length >= 3 and compatible_interval_nonempty and active_dominate_compatible:
        theorem_status = 'theorem-v-explicit-error-law-moderate'
    elif chain_length >= 2:
        theorem_status = 'theorem-v-explicit-error-law-partial'
    else:
        theorem_status = 'theorem-v-explicit-error-law-insufficient'

    notes = (
        'Compatible interval built from the strongest currently available rational-to-irrational '
        'limit layers. The q-power tail law is a conservative compression of the existing chain '\
        'certificates rather than a final continuation theorem.'
    )
    if exponent is None:
        notes += ' No positive q-power exponent was available, so the tail law fell back to a constant envelope.'
    else:
        notes += f' The q-power exponent was taken from {exponent_source}.'
    if late_coherent_suffix['interval_width'] is not None:
        notes += (
            f" The best late coherent suffix starts at q={late_coherent_suffix['start_q']} with width "
            f"{float(late_coherent_suffix['interval_width']):.6g}."
        )

    return TheoremVExplicitErrorCertificate(
        rho_target=rho_target,
        family_label=family_label,
        chain_labels=[node.label for node in raw_nodes],
        chain_qs=[int(node.q) for node in raw_nodes],
        chain_ps=[int(node.p) for node in raw_nodes],
        chain_length=int(chain_length),
        compatible_layer_names=compatible_layers,
        compatible_layer_count=int(len(compatible_layers)),
        compatible_limit_interval_lo=compatible_lo,
        compatible_limit_interval_hi=compatible_hi,
        compatible_limit_interval_width=compatible_width,
        chosen_q_power_exponent=exponent,
        q_power_anchor_q=anchor_q,
        q_power_anchor_tail_constant=anchor_constant,
        q_power_model_source=q_model_source if q_model_source != 'none' else exponent_source,
        q_power_tail_dominates_certificate_tail=bool(q_power_tail_dominates_certificate_tail),
        compatible_interval_nonempty=bool(compatible_interval_nonempty),
        raw_error_law_nonincreasing=bool(raw_nonincreasing),
        monotone_error_law_nonincreasing=bool(monotone_nonincreasing),
        active_bounds_dominate_compatible_errors=bool(active_dominate_compatible),
        active_bounds_dominate_certificate_totals=bool(active_dominate_certificate),
        first_raw_total_error_radius=None if not raw_total_radii else float(raw_total_radii[0]),
        last_raw_total_error_radius=None if not raw_total_radii else float(raw_total_radii[-1]),
        first_monotone_total_error_radius=None if not monotone_radii else float(monotone_radii[0]),
        last_monotone_total_error_radius=None if not monotone_radii else float(monotone_radii[-1]),
        late_coherent_suffix_start_index=late_coherent_suffix['start_index'],
        late_coherent_suffix_start_q=late_coherent_suffix['start_q'],
        late_coherent_suffix_start_label=late_coherent_suffix['start_label'],
        late_coherent_suffix_length=int(late_coherent_suffix['length']),
        late_coherent_suffix_labels=list(late_coherent_suffix['labels']),
        late_coherent_suffix_qs=[int(x) for x in late_coherent_suffix['qs']],
        late_coherent_suffix_interval_lo=late_coherent_suffix['interval_lo'],
        late_coherent_suffix_interval_hi=late_coherent_suffix['interval_hi'],
        late_coherent_suffix_interval_width=late_coherent_suffix['interval_width'],
        late_coherent_suffix_first_raw_total_error_radius=late_coherent_suffix['first_raw_total_error_radius'],
        late_coherent_suffix_last_raw_total_error_radius=late_coherent_suffix['last_raw_total_error_radius'],
        late_coherent_suffix_contraction_ratio=late_coherent_suffix['contraction_ratio'],
        late_coherent_suffix_raw_error_law_nonincreasing=bool(late_coherent_suffix['raw_error_law_nonincreasing']),
        late_coherent_suffix_contracting=bool(late_coherent_suffix['contracting']),
        late_coherent_suffix_status=str(late_coherent_suffix['status']),
        theorem_status=theorem_status,
        notes=notes,
        layer_intervals=layer_intervals,
        nodes=raw_nodes,
    )



@dataclass
class TheoremVFinalErrorLawCertificate:
    rho_target: float | None
    family_label: str | None
    theorem_target_interval: list[float] | None
    theorem_target_width: float | None
    transport_limit_interval: list[float] | None
    error_law_function_label: str
    error_law_monotone: bool
    error_law_uniform_on_family: bool
    error_law_preserves_gap: bool | None
    gap_preservation_margin: float | None
    continuation_ready: bool
    transport_ready: bool
    final_error_law_certified: bool
    residual_error_law_burden: list[str]
    theorem_status: str
    notes: str
    explicit_error_shell: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho_target': self.rho_target,
            'family_label': self.family_label,
            'theorem_target_interval': None if self.theorem_target_interval is None else [float(x) for x in self.theorem_target_interval],
            'theorem_target_width': self.theorem_target_width,
            'transport_limit_interval': None if self.transport_limit_interval is None else [float(x) for x in self.transport_limit_interval],
            'error_law_function_label': str(self.error_law_function_label),
            'error_law_monotone': bool(self.error_law_monotone),
            'error_law_uniform_on_family': bool(self.error_law_uniform_on_family),
            'error_law_preserves_gap': None if self.error_law_preserves_gap is None else bool(self.error_law_preserves_gap),
            'gap_preservation_margin': self.gap_preservation_margin,
            'continuation_ready': bool(self.continuation_ready),
            'transport_ready': bool(self.transport_ready),
            'final_error_law_certified': bool(self.final_error_law_certified),
            'residual_error_law_burden': [str(x) for x in self.residual_error_law_burden],
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'explicit_error_shell': dict(self.explicit_error_shell),
        }


def build_theorem_v_final_error_law_certificate(
    ladder: dict[str, Any] | None = None,
    *,
    explicit_error_certificate: Mapping[str, Any] | None = None,
    reference_lower_bound: float | None = None,
    min_uniform_chain_length: int = 4,
    max_target_width_for_transport_readiness: float = 5.0e-4,
    **explicit_error_kwargs: Any,
) -> TheoremVFinalErrorLawCertificate:
    """Promote the explicit Theorem-V error package to a final theorem-facing law.

    This does not claim to finish the mathematical proof; it packages the current
    strongest error object as a single law with explicit transport/gap semantics
    so downstream theorem shells can consume it directly.
    """
    if explicit_error_certificate is None:
        if ladder is None:
            raise ValueError('Either ladder or explicit_error_certificate must be provided.')
        explicit = build_theorem_v_explicit_error_certificate(ladder, **explicit_error_kwargs).to_dict()
    else:
        explicit = dict(explicit_error_certificate)

    compatible_lo = _safe_float(explicit.get('compatible_limit_interval_lo'))
    compatible_hi = _safe_float(explicit.get('compatible_limit_interval_hi'))
    compatible_interval = None if compatible_lo is None or compatible_hi is None or compatible_hi < compatible_lo else [float(compatible_lo), float(compatible_hi)]
    late_lo = _safe_float(explicit.get('late_coherent_suffix_interval_lo'))
    late_hi = _safe_float(explicit.get('late_coherent_suffix_interval_hi'))
    late_interval = None if late_lo is None or late_hi is None or late_hi < late_lo else [float(late_lo), float(late_hi)]
    late_status = str(explicit.get('late_coherent_suffix_status', ''))
    late_ratio = _safe_float(explicit.get('late_coherent_suffix_contraction_ratio'))
    late_contracting = bool(explicit.get('late_coherent_suffix_contracting', False))
    chain_length = int(explicit.get('chain_length') or 0)
    late_length = int(explicit.get('late_coherent_suffix_length') or 0)

    late_suffix_rigidity_ready = bool(
        late_interval is not None
        and late_length >= max(3, min_uniform_chain_length - 1)
        and _is_strong_status(explicit)
        and (('strong' in late_status) or late_contracting or (late_ratio is not None and late_ratio <= 1.1))
        and (late_hi - late_lo) <= max(20.0 * float(max_target_width_for_transport_readiness), 5.0e-5)
    )

    use_late_interval = late_interval is not None and (
        (late_length >= min_uniform_chain_length and 'strong' in late_status) or late_suffix_rigidity_ready
    )
    theorem_target_interval = late_interval if use_late_interval else compatible_interval
    theorem_target_width = None if theorem_target_interval is None else float(theorem_target_interval[1] - theorem_target_interval[0])

    error_law_monotone = bool(explicit.get('monotone_error_law_nonincreasing', False))
    error_law_uniform_on_family = (
        chain_length >= min_uniform_chain_length
        and late_length >= min_uniform_chain_length - 1
        and (('strong' in late_status) or late_suffix_rigidity_ready)
        and bool(explicit.get('active_bounds_dominate_compatible_errors', False))
        and bool(explicit.get('active_bounds_dominate_certificate_totals', False))
    )
    continuation_ready = bool(explicit.get('compatible_interval_nonempty', False)) and error_law_monotone
    transport_ready = continuation_ready and error_law_uniform_on_family and theorem_target_width is not None and theorem_target_width <= float(max_target_width_for_transport_readiness)

    gap_preservation_margin = None
    error_law_preserves_gap = None
    if reference_lower_bound is not None and theorem_target_interval is not None:
        gap_preservation_margin = float(theorem_target_interval[0] - float(reference_lower_bound))
        error_law_preserves_gap = bool(gap_preservation_margin > 0.0)

    residual: list[str] = []
    if not continuation_ready:
        residual.append('continuation-target-interval-not-ready')
    if not error_law_monotone:
        residual.append('monotone-error-law-missing')
    if not error_law_uniform_on_family:
        residual.append('family-uniform-error-law-missing')
    if not transport_ready:
        residual.append('transport-target-interval-not-ready')
    if error_law_preserves_gap is False:
        residual.append('gap-preservation-not-certified')

    final_error_law_certified = continuation_ready and transport_ready and (error_law_preserves_gap is not False)
    if final_error_law_certified and error_law_preserves_gap is True:
        theorem_status = 'theorem-v-final-error-law-strong'
    elif final_error_law_certified:
        theorem_status = 'theorem-v-final-error-law-gap-agnostic-strong'
    elif continuation_ready and transport_ready:
        theorem_status = 'theorem-v-final-error-law-gap-preservation-incomplete'
    elif continuation_ready:
        theorem_status = 'theorem-v-final-error-law-partial'
    else:
        theorem_status = 'theorem-v-final-error-law-incomplete'

    notes = (
        'The current explicit Theorem-V error package has been promoted to a single theorem-facing error law object. '
        'The preferred target interval is taken from the native late coherent suffix when that witness is strong enough or rigid enough in the runtime-aware sense; '
        'otherwise the full compatible irrational interval is used.'
    )
    if theorem_target_width is not None:
        notes += f' Target interval width: {float(theorem_target_width):.6g}.'
    if gap_preservation_margin is not None:
        notes += f' Gap-preservation margin against the supplied lower reference: {float(gap_preservation_margin):.6g}.'

    return TheoremVFinalErrorLawCertificate(
        rho_target=_safe_float(explicit.get('rho_target')),
        family_label=None if explicit.get('family_label') is None else str(explicit.get('family_label')),
        theorem_target_interval=theorem_target_interval,
        theorem_target_width=theorem_target_width,
        transport_limit_interval=compatible_interval,
        error_law_function_label='late-coherent-suffix-q-tail-envelope' if use_late_interval else 'compatible-q-tail-envelope',
        error_law_monotone=bool(error_law_monotone),
        error_law_uniform_on_family=bool(error_law_uniform_on_family),
        error_law_preserves_gap=error_law_preserves_gap,
        gap_preservation_margin=gap_preservation_margin,
        continuation_ready=bool(continuation_ready),
        transport_ready=bool(transport_ready),
        final_error_law_certified=bool(final_error_law_certified),
        residual_error_law_burden=residual,
        theorem_status=theorem_status,
        notes=notes,
        explicit_error_shell=explicit,
    )


__all__ = [
    'TheoremVExplicitErrorNode',
    'TheoremVExplicitErrorCertificate',
    'TheoremVFinalErrorLawCertificate',
    'build_theorem_v_explicit_error_certificate',
    'build_theorem_v_final_error_law_certificate',
]
