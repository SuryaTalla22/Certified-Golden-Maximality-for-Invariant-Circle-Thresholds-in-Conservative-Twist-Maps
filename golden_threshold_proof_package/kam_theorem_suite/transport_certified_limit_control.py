from __future__ import annotations

"""Transport-certified irrational-limit control.

This layer strengthens the current rational-to-irrational bridge by replacing
raw crossing-window geometry with *transport-refined* root windows extracted
from the local branch certificates themselves.

The key idea is simple.  For each rational approximant, the local crossing
certificate already contains theorem-facing data from a validated branch window:

1. endpoint signed-gap bounds for ``g(K)=|R_{p/q}(K)|-target``,
2. a one-sided derivative enclosure for ``g'`` when available,
3. an optional interval-Newton refinement around the midpoint, and
4. branch-tube continuation diagnostics.

Whenever the derivative is bounded away from zero, the endpoint gap bounds imply
one-sided transport bounds from the endpoints to the root.  Intersecting those
transport bounds with the interval-Newton refinement produces a sharper local
root enclosure than the raw certified window alone.  The current module then
feeds those transport-refined windows through the explicit convergent-family
chain, producing step bounds and a telescoping tail interval that depend on the
branch continuation data themselves rather than only on raw center/width
geometry.

This is still not a final rational-to-irrational theorem.  It *is* a stronger
intermediate object, because every step bound now has a direct provenance in the
local transport information already certified on the branch windows.
"""

from dataclasses import asdict, dataclass
from math import inf, isfinite
from typing import Any, Sequence

from .convergent_family_limit_control import _longest_convergent_chain, _fraction_true


@dataclass
class TransportCertifiedEntry:
    label: str
    p: int
    q: int
    raw_window_lo: float
    raw_window_hi: float
    raw_window_width: float
    transport_window_lo: float | None
    transport_window_hi: float | None
    transport_window_width: float | None
    transport_center: float | None
    transport_improvement: float | None
    derivative_sign: str
    derivative_floor: float | None
    derivative_backed: bool
    interval_newton_success: bool
    endpoint_transport_available: bool
    midpoint_transport_available: bool
    tangent_inclusion_success: bool | None
    interval_tangent_success: bool | None
    interval_tangent_contraction: float | None
    branch_residual_width: float | None
    tube_sup_width: float | None
    slope_center_inf: float | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TransportCertifiedStep:
    grandparent_label: str | None
    parent_label: str
    child_label: str
    grandparent_q: int | None
    parent_q: int
    child_q: int
    parent_transport_width: float | None
    child_transport_width: float | None
    parent_child_overlap_fraction: float | None
    child_nested_in_parent: bool | None
    transport_union_width: float | None
    transport_center_shift: float | None
    transport_step_bound: float | None
    step_bound_ratio_to_previous: float | None
    parent_derivative_floor: float | None
    child_derivative_floor: float | None
    parent_interval_tangent_success: bool | None
    child_interval_tangent_success: bool | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TransportCertifiedLimitCertificate:
    rho_target: float | None
    family_label: str | None
    entry_count: int
    usable_entry_count: int
    chain_labels: list[str]
    chain_qs: list[int]
    chain_ps: list[int]
    chain_length: int
    derivative_backed_fraction: float | None
    endpoint_transport_fraction: float | None
    midpoint_transport_fraction: float | None
    interval_newton_fraction: float | None
    transport_intersection_lo: float | None
    transport_intersection_hi: float | None
    transport_intersection_width: float | None
    last_transport_window_lo: float | None
    last_transport_window_hi: float | None
    last_transport_window_width: float | None
    last_transport_step_bound: float | None
    observed_transport_contraction_ratio: float | None
    telescoping_tail_bound: float | None
    limit_interval_lo: float | None
    limit_interval_hi: float | None
    limit_interval_width: float | None
    transport_overlap_fraction: float | None
    transport_nested_fraction: float | None
    mean_transport_improvement: float | None
    theorem_status: str
    notes: str
    entries: list[TransportCertifiedEntry]
    steps: list[TransportCertifiedStep]

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
            'derivative_backed_fraction': self.derivative_backed_fraction,
            'endpoint_transport_fraction': self.endpoint_transport_fraction,
            'midpoint_transport_fraction': self.midpoint_transport_fraction,
            'interval_newton_fraction': self.interval_newton_fraction,
            'transport_intersection_lo': self.transport_intersection_lo,
            'transport_intersection_hi': self.transport_intersection_hi,
            'transport_intersection_width': self.transport_intersection_width,
            'last_transport_window_lo': self.last_transport_window_lo,
            'last_transport_window_hi': self.last_transport_window_hi,
            'last_transport_window_width': self.last_transport_window_width,
            'last_transport_step_bound': self.last_transport_step_bound,
            'observed_transport_contraction_ratio': self.observed_transport_contraction_ratio,
            'telescoping_tail_bound': self.telescoping_tail_bound,
            'limit_interval_lo': self.limit_interval_lo,
            'limit_interval_hi': self.limit_interval_hi,
            'limit_interval_width': self.limit_interval_width,
            'transport_overlap_fraction': self.transport_overlap_fraction,
            'transport_nested_fraction': self.transport_nested_fraction,
            'mean_transport_improvement': self.mean_transport_improvement,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'entries': [e.to_dict() for e in self.entries],
            'steps': [s.to_dict() for s in self.steps],
        }


def _interval_intersection(
    windows: Sequence[tuple[float, float] | None],
) -> tuple[float | None, float | None, float | None]:
    filtered: list[tuple[float, float]] = []
    for window in windows:
        if window is None:
            continue
        try:
            lo = window[0]
            hi = window[1]
        except (TypeError, IndexError):
            continue
        if lo is None or hi is None:
            continue
        filtered.append((float(lo), float(hi)))
    if not filtered:
        return None, None, None
    lo = max(float(w[0]) for w in filtered)
    hi = min(float(w[1]) for w in filtered)
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _window_overlap(a_lo: float, a_hi: float, b_lo: float, b_hi: float) -> tuple[float, float]:
    width = max(0.0, min(float(a_hi), float(b_hi)) - max(float(a_lo), float(b_lo)))
    denom = max(min(float(a_hi) - float(a_lo), float(b_hi) - float(b_lo)), 1e-15)
    return float(width), float(width / denom)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _crossing_object(entry: dict[str, Any]) -> dict[str, Any]:
    crossing = dict(entry.get('crossing_certificate') or {})
    if not crossing:
        crossing = dict((entry.get('bridge_report') or {}).get('crossing_certificate') or {})
    return crossing


def _signed_gap_side(lo: float | None, hi: float | None) -> str:
    if lo is None or hi is None:
        return 'unknown'
    if float(hi) < 0.0:
        return 'below-target'
    if float(lo) > 0.0:
        return 'above-target'
    return 'mixed'


def _transport_interval_from_endpoint(
    *,
    K: float,
    gap_lo: float | None,
    gap_hi: float | None,
    derivative_sign: str,
    derivative_floor: float | None,
) -> tuple[float | None, float | None]:
    if derivative_floor is None or derivative_floor <= 0.0 or derivative_sign not in {'positive', 'negative'}:
        return None, None
    side = _signed_gap_side(gap_lo, gap_hi)
    if side == 'unknown' or side == 'mixed':
        return None, None
    mag = max(abs(float(gap_lo)), abs(float(gap_hi)))
    delta = float(mag / max(float(derivative_floor), 1e-15))
    K = float(K)
    if derivative_sign == 'positive':
        if side == 'below-target':
            return K, float(K + delta)
        return float(K - delta), K
    # derivative_sign == 'negative'
    if side == 'below-target':
        return float(K - delta), K
    return K, float(K + delta)


def _transport_interval_from_midpoint(
    *,
    K_mid: float | None,
    gap_lo: float | None,
    gap_hi: float | None,
    derivative_floor: float | None,
) -> tuple[float | None, float | None]:
    if K_mid is None or gap_lo is None or gap_hi is None or derivative_floor is None or derivative_floor <= 0.0:
        return None, None
    mag = max(abs(float(gap_lo)), abs(float(gap_hi)))
    delta = float(mag / max(float(derivative_floor), 1e-15))
    K_mid = float(K_mid)
    return float(K_mid - delta), float(K_mid + delta)


def _intersect_many(intervals: Sequence[tuple[float | None, float | None]]) -> tuple[float | None, float | None, float | None]:
    usable = [(float(lo), float(hi)) for lo, hi in intervals if lo is not None and hi is not None]
    return _interval_intersection(usable)


def _extract_transport_entries(ladder: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for entry in ladder.get('approximants', []) or []:
        q = entry.get('q')
        raw_lo = entry.get('crossing_root_window_lo')
        raw_hi = entry.get('crossing_root_window_hi')
        if q in (None, 0) or raw_lo is None or raw_hi is None:
            continue
        raw_lo_f = float(raw_lo)
        raw_hi_f = float(raw_hi)
        raw_w = float(entry.get('crossing_root_window_width', raw_hi_f - raw_lo_f))
        crossing = _crossing_object(entry)
        branch_summary = dict(crossing.get('branch_summary') or {})
        branch_tube = dict(branch_summary.get('branch_tube') or {})
        interval_newton = dict(crossing.get('interval_newton') or {})
        endpoint_left = dict(crossing.get('endpoint_left') or {})
        endpoint_right = dict(crossing.get('endpoint_right') or {})
        midpoint = dict(crossing.get('midpoint') or {})
        gp_lo = _as_float(branch_summary.get('gprime_interval_lo'))
        gp_hi = _as_float(branch_summary.get('gprime_interval_hi'))
        derivative_sign = str(crossing.get('derivative_sign', 'mixed'))
        derivative_floor = None
        if gp_lo is not None and gp_hi is not None and crossing.get('derivative_away_from_zero', False):
            if gp_lo > 0.0 or gp_hi < 0.0:
                derivative_floor = float(min(abs(gp_lo), abs(gp_hi)))
                if derivative_sign == 'mixed':
                    derivative_sign = 'positive' if gp_lo > 0.0 else 'negative'
        left_iv = _transport_interval_from_endpoint(
            K=float(crossing.get('K_lo', raw_lo_f)),
            gap_lo=_as_float(endpoint_left.get('signed_gap_interval_lo')),
            gap_hi=_as_float(endpoint_left.get('signed_gap_interval_hi')),
            derivative_sign=derivative_sign,
            derivative_floor=derivative_floor,
        )
        right_iv = _transport_interval_from_endpoint(
            K=float(crossing.get('K_hi', raw_hi_f)),
            gap_lo=_as_float(endpoint_right.get('signed_gap_interval_lo')),
            gap_hi=_as_float(endpoint_right.get('signed_gap_interval_hi')),
            derivative_sign=derivative_sign,
            derivative_floor=derivative_floor,
        )
        midpoint_iv = _transport_interval_from_midpoint(
            K_mid=_as_float(midpoint.get('K')) if midpoint.get('K') is not None else _as_float((crossing.get('interval_newton') or {}).get('K_mid')),
            gap_lo=_as_float(midpoint.get('signed_gap_interval_lo')),
            gap_hi=_as_float(midpoint.get('signed_gap_interval_hi')),
            derivative_floor=derivative_floor,
        )
        newton_iv = (
            _as_float(interval_newton.get('refined_lo')),
            _as_float(interval_newton.get('refined_hi')),
        ) if bool(interval_newton.get('success', False)) else (None, None)
        trans_lo, trans_hi, trans_w = _intersect_many([
            (raw_lo_f, raw_hi_f),
            left_iv,
            right_iv,
            midpoint_iv,
            newton_iv,
        ])
        if trans_lo is None or trans_hi is None:
            trans_lo, trans_hi, trans_w = raw_lo_f, raw_hi_f, raw_w
        out.append({
            'label': str(entry.get('label', f"{entry.get('p')}/{entry.get('q')}")),
            'p': int(entry.get('p', 0)),
            'q': int(q),
            'raw_lo': raw_lo_f,
            'raw_hi': raw_hi_f,
            'raw_width': raw_w,
            'transport_lo': float(trans_lo),
            'transport_hi': float(trans_hi),
            'transport_width': float(trans_w),
            'transport_center': float(0.5 * (trans_lo + trans_hi)),
            'transport_improvement': float(raw_w - trans_w),
            'derivative_sign': derivative_sign,
            'derivative_floor': derivative_floor,
            'derivative_backed': bool(derivative_floor is not None and derivative_floor > 0.0),
            'interval_newton_success': bool(interval_newton.get('success', False) or crossing.get('certification_tier') == 'interval_newton'),
            'endpoint_transport_available': bool(left_iv[0] is not None and right_iv[0] is not None),
            'midpoint_transport_available': bool(midpoint_iv[0] is not None),
            'tangent_inclusion_success': None if branch_summary.get('tangent_inclusion_success') is None else bool(branch_summary.get('tangent_inclusion_success')),
            'interval_tangent_success': None if branch_tube.get('interval_tangent_success') is None else bool(branch_tube.get('interval_tangent_success')),
            'interval_tangent_contraction': _as_float(branch_tube.get('interval_tangent_contraction')),
            'branch_residual_width': _as_float(branch_tube.get('branch_residual_width')),
            'tube_sup_width': _as_float(branch_tube.get('tube_sup_width')),
            'slope_center_inf': _as_float(branch_tube.get('slope_center_inf')),
            'status': str(crossing.get('certification_tier', entry.get('status', 'unknown'))),
        })
    return sorted(out, key=lambda e: (e['q'], e['p'], e['transport_center']))


def build_transport_certified_limit_certificate(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    contraction_cap: float = 0.9,
    min_overlap_fraction: float = 0.5,
) -> TransportCertifiedLimitCertificate:
    entries = _extract_transport_entries(ladder)
    entry_count = len(list(ladder.get('approximants', []) or []))
    usable = len(entries)
    if usable < 2:
        return TransportCertifiedLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            entry_count=int(entry_count),
            usable_entry_count=int(usable),
            chain_labels=[],
            chain_qs=[],
            chain_ps=[],
            chain_length=0,
            derivative_backed_fraction=None,
            endpoint_transport_fraction=None,
            midpoint_transport_fraction=None,
            interval_newton_fraction=None,
            transport_intersection_lo=None,
            transport_intersection_hi=None,
            transport_intersection_width=None,
            last_transport_window_lo=None,
            last_transport_window_hi=None,
            last_transport_window_width=None,
            last_transport_step_bound=None,
            observed_transport_contraction_ratio=None,
            telescoping_tail_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            transport_overlap_fraction=None,
            transport_nested_fraction=None,
            mean_transport_improvement=None,
            theorem_status='transport-certified-limit-incomplete',
            notes='Not enough certified entries carry usable transport-refined windows.',
            entries=[],
            steps=[],
        )

    chain = _longest_convergent_chain(entries, p_tolerance=p_tolerance)
    chain_labels = [str(e['label']) for e in chain]
    chain_qs = [int(e['q']) for e in chain]
    chain_ps = [int(e['p']) for e in chain]
    if len(chain) < min_chain_length:
        return TransportCertifiedLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            entry_count=int(entry_count),
            usable_entry_count=int(usable),
            chain_labels=chain_labels,
            chain_qs=chain_qs,
            chain_ps=chain_ps,
            chain_length=len(chain),
            derivative_backed_fraction=_fraction_true([bool(e['derivative_backed']) for e in entries]),
            endpoint_transport_fraction=_fraction_true([bool(e['endpoint_transport_available']) for e in entries]),
            midpoint_transport_fraction=_fraction_true([bool(e['midpoint_transport_available']) for e in entries]),
            interval_newton_fraction=_fraction_true([bool(e['interval_newton_success']) for e in entries]),
            transport_intersection_lo=None,
            transport_intersection_hi=None,
            transport_intersection_width=None,
            last_transport_window_lo=float(chain[-1]['transport_lo']),
            last_transport_window_hi=float(chain[-1]['transport_hi']),
            last_transport_window_width=float(chain[-1]['transport_width']),
            last_transport_step_bound=None,
            observed_transport_contraction_ratio=None,
            telescoping_tail_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            transport_overlap_fraction=None,
            transport_nested_fraction=None,
            mean_transport_improvement=None if not entries else float(sum(float(e['transport_improvement']) for e in entries) / len(entries)),
            theorem_status='transport-certified-limit-incomplete',
            notes='A transport-aware tail exists, but it is not yet long enough to support telescoping transport control.',
            entries=[TransportCertifiedEntry(**e).to_dict() for e in []],
            steps=[],
        )

    transport_windows = [(float(e['transport_lo']), float(e['transport_hi'])) for e in chain]
    inter_lo, inter_hi, inter_w = _interval_intersection(transport_windows)
    steps: list[TransportCertifiedStep] = []
    step_bounds: list[float] = []
    overlap_flags: list[bool] = []
    nested_flags: list[bool] = []
    for idx in range(1, len(chain)):
        parent = chain[idx - 1]
        child = chain[idx]
        grandparent = chain[idx - 2] if idx >= 2 else None
        overlap_w, overlap_frac = _window_overlap(parent['transport_lo'], parent['transport_hi'], child['transport_lo'], child['transport_hi'])
        nested = bool(child['transport_lo'] >= parent['transport_lo'] and child['transport_hi'] <= parent['transport_hi'])
        center_shift = abs(float(child['transport_center']) - float(parent['transport_center']))
        union_width = float(max(parent['transport_hi'], child['transport_hi']) - min(parent['transport_lo'], child['transport_lo']))
        ratio = None
        if step_bounds and step_bounds[-1] > 0.0:
            ratio = float(union_width / step_bounds[-1])
        step_bounds.append(union_width)
        overlap_flags.append(bool(overlap_frac >= min_overlap_fraction))
        nested_flags.append(nested)
        steps.append(
            TransportCertifiedStep(
                grandparent_label=None if grandparent is None else str(grandparent['label']),
                parent_label=str(parent['label']),
                child_label=str(child['label']),
                grandparent_q=None if grandparent is None else int(grandparent['q']),
                parent_q=int(parent['q']),
                child_q=int(child['q']),
                parent_transport_width=float(parent['transport_width']),
                child_transport_width=float(child['transport_width']),
                parent_child_overlap_fraction=float(overlap_frac),
                child_nested_in_parent=bool(nested),
                transport_union_width=float(union_width),
                transport_center_shift=float(center_shift),
                transport_step_bound=float(union_width),
                step_bound_ratio_to_previous=ratio,
                parent_derivative_floor=parent['derivative_floor'],
                child_derivative_floor=child['derivative_floor'],
                parent_interval_tangent_success=parent['interval_tangent_success'],
                child_interval_tangent_success=child['interval_tangent_success'],
            )
        )

    ratios = [s.step_bound_ratio_to_previous for s in steps if s.step_bound_ratio_to_previous is not None and isfinite(float(s.step_bound_ratio_to_previous))]
    observed_ratio = None if not ratios else float(min(contraction_cap, max(0.0, sum(float(r) for r in ratios) / len(ratios))))
    telescoping_tail = None
    if observed_ratio is not None and 0.0 <= observed_ratio < 1.0 and step_bounds:
        telescoping_tail = float(step_bounds[-1] * observed_ratio / max(1.0 - observed_ratio, 1e-12))

    last = chain[-1]
    last_lo = float(last['transport_lo'])
    last_hi = float(last['transport_hi'])
    last_w = float(last['transport_width'])
    limit_lo = None
    limit_hi = None
    limit_w = None
    if telescoping_tail is not None:
        base_lo = float(last_lo - telescoping_tail)
        base_hi = float(last_hi + telescoping_tail)
        if inter_lo is not None and inter_hi is not None:
            lo = max(base_lo, float(inter_lo))
            hi = min(base_hi, float(inter_hi))
            if hi >= lo:
                limit_lo, limit_hi = float(lo), float(hi)
            else:
                limit_lo, limit_hi = base_lo, base_hi
        else:
            limit_lo, limit_hi = base_lo, base_hi
        limit_w = float(limit_hi - limit_lo)

    entries_dc = [TransportCertifiedEntry(
        label=str(e['label']),
        p=int(e['p']),
        q=int(e['q']),
        raw_window_lo=float(e['raw_lo']),
        raw_window_hi=float(e['raw_hi']),
        raw_window_width=float(e['raw_width']),
        transport_window_lo=float(e['transport_lo']),
        transport_window_hi=float(e['transport_hi']),
        transport_window_width=float(e['transport_width']),
        transport_center=float(e['transport_center']),
        transport_improvement=float(e['transport_improvement']),
        derivative_sign=str(e['derivative_sign']),
        derivative_floor=e['derivative_floor'],
        derivative_backed=bool(e['derivative_backed']),
        interval_newton_success=bool(e['interval_newton_success']),
        endpoint_transport_available=bool(e['endpoint_transport_available']),
        midpoint_transport_available=bool(e['midpoint_transport_available']),
        tangent_inclusion_success=e['tangent_inclusion_success'],
        interval_tangent_success=e['interval_tangent_success'],
        interval_tangent_contraction=e['interval_tangent_contraction'],
        branch_residual_width=e['branch_residual_width'],
        tube_sup_width=e['tube_sup_width'],
        slope_center_inf=e['slope_center_inf'],
        status=str(e['status']),
    ) for e in entries]

    derivative_fraction = _fraction_true([bool(e['derivative_backed']) for e in chain])
    endpoint_fraction = _fraction_true([bool(e['endpoint_transport_available']) for e in chain])
    midpoint_fraction = _fraction_true([bool(e['midpoint_transport_available']) for e in chain])
    newton_fraction = _fraction_true([bool(e['interval_newton_success']) for e in chain])
    mean_improvement = float(sum(float(e['transport_improvement']) for e in chain) / len(chain)) if chain else None
    overlap_fraction = _fraction_true(overlap_flags)
    nested_fraction = _fraction_true(nested_flags)

    if (
        limit_lo is not None
        and derivative_fraction is not None and derivative_fraction >= 0.75
        and endpoint_fraction is not None and endpoint_fraction >= 0.5
        and observed_ratio is not None and observed_ratio < contraction_cap
        and overlap_fraction is not None and overlap_fraction >= min_overlap_fraction
    ):
        status = 'transport-certified-limit-strong'
        notes = (
            'The convergent-family tail closes using transport-refined windows derived from the local branch certificates themselves: '
            'endpoint signed-gap bounds, one-sided derivative floors, midpoint/interval-Newton refinement, and branch-window continuation data all contribute to the final telescoping interval.'
        )
    elif limit_lo is not None:
        status = 'transport-certified-limit-moderate'
        notes = (
            'A transport-aware convergent tail closes, but the derivative-backed or overlap structure is not yet strong enough to treat the resulting telescoping interval as more than a moderately coordinated bridge object.'
        )
    else:
        status = 'transport-certified-limit-incomplete'
        notes = (
            'Transport-refined local windows were extracted, but they do not yet contract into a stable telescoping irrational-limit interval.'
        )

    return TransportCertifiedLimitCertificate(
        rho_target=None if rho_target is None else float(rho_target),
        family_label=family_label,
        entry_count=int(entry_count),
        usable_entry_count=int(usable),
        chain_labels=chain_labels,
        chain_qs=chain_qs,
        chain_ps=chain_ps,
        chain_length=int(len(chain)),
        derivative_backed_fraction=derivative_fraction,
        endpoint_transport_fraction=endpoint_fraction,
        midpoint_transport_fraction=midpoint_fraction,
        interval_newton_fraction=newton_fraction,
        transport_intersection_lo=inter_lo,
        transport_intersection_hi=inter_hi,
        transport_intersection_width=inter_w,
        last_transport_window_lo=last_lo,
        last_transport_window_hi=last_hi,
        last_transport_window_width=last_w,
        last_transport_step_bound=None if not step_bounds else float(step_bounds[-1]),
        observed_transport_contraction_ratio=observed_ratio,
        telescoping_tail_bound=telescoping_tail,
        limit_interval_lo=limit_lo,
        limit_interval_hi=limit_hi,
        limit_interval_width=limit_w,
        transport_overlap_fraction=overlap_fraction,
        transport_nested_fraction=nested_fraction,
        mean_transport_improvement=mean_improvement,
        theorem_status=status,
        notes=notes,
        entries=entries_dc,
        steps=steps,
    )


__all__ = [
    'TransportCertifiedEntry',
    'TransportCertifiedStep',
    'TransportCertifiedLimitCertificate',
    'build_transport_certified_limit_certificate',
]
