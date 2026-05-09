from __future__ import annotations

"""Nested subladder irrational-limit control.

This stage strengthens the branch-certified tail envelope by organizing the
high-denominator approximants into a sequence of *nested tail intervals*.

Instead of selecting a single best tail threshold and stopping there, this
module builds the branch-certified tail interval for every admissible q-tail,
then searches for a monotone/nested suffix along the convergent subladders.
The resulting object is still not a full convergence theorem, but it is closer
in spirit to a Cauchy argument: successive higher-q tails should keep the
candidate irrational threshold trapped in a shrinking, compatible family of
intervals.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .branch_certified_limit_control import (
    build_branch_certified_irrational_limit_certificate,
    _extract_branch_certified_entries,
    _source_thresholds,
    _default_thresholds,
)


@dataclass
class NestedSubladderInterval:
    q_threshold: int
    member_qs: list[int]
    member_labels: list[str]
    interval_lo: float
    interval_hi: float
    interval_width: float
    center: float | None
    derivative_backed_fraction: float | None
    interval_newton_fraction: float | None
    pairwise_overlap_fraction: float | None
    theorem_status: str
    nested_with_previous: bool | None
    cauchy_with_previous: bool | None
    center_step_from_previous: float | None
    width_ratio_to_previous: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NestedSubladderLimitCertificate:
    rho_target: float | None
    family_label: str | None
    usable_entry_count: int
    candidate_thresholds: list[int]
    chain_thresholds: list[int]
    chain_length: int
    chain_is_nested: bool
    chain_is_cauchy_like: bool
    final_interval_lo: float | None
    final_interval_hi: float | None
    final_interval_width: float | None
    outer_chain_interval_lo: float | None
    outer_chain_interval_hi: float | None
    outer_chain_interval_width: float | None
    shrink_ratio: float | None
    max_center_step: float | None
    theorem_status: str
    notes: str
    intervals: list[NestedSubladderInterval]

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho_target': self.rho_target,
            'family_label': self.family_label,
            'usable_entry_count': int(self.usable_entry_count),
            'candidate_thresholds': [int(x) for x in self.candidate_thresholds],
            'chain_thresholds': [int(x) for x in self.chain_thresholds],
            'chain_length': int(self.chain_length),
            'chain_is_nested': bool(self.chain_is_nested),
            'chain_is_cauchy_like': bool(self.chain_is_cauchy_like),
            'final_interval_lo': self.final_interval_lo,
            'final_interval_hi': self.final_interval_hi,
            'final_interval_width': self.final_interval_width,
            'outer_chain_interval_lo': self.outer_chain_interval_lo,
            'outer_chain_interval_hi': self.outer_chain_interval_hi,
            'outer_chain_interval_width': self.outer_chain_interval_width,
            'shrink_ratio': self.shrink_ratio,
            'max_center_step': self.max_center_step,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'intervals': [i.to_dict() for i in self.intervals],
        }


def _interval_subset(inner_lo: float, inner_hi: float, outer_lo: float, outer_hi: float, tol: float) -> bool:
    return float(inner_lo) >= float(outer_lo) - tol and float(inner_hi) <= float(outer_hi) + tol


def _interval_intersection(lo_a: float, hi_a: float, lo_b: float, hi_b: float) -> tuple[float, float, float] | None:
    lo = max(float(lo_a), float(lo_b))
    hi = min(float(hi_a), float(hi_b))
    if hi < lo:
        return None
    return float(lo), float(hi), float(hi - lo)


def build_nested_subladder_limit_certificate(
    ladder: dict[str, Any],
    *,
    refined: dict[str, Any] | None = None,
    asymptotic_audit: dict[str, Any] | None = None,
    rho_target: float | None = None,
    family_label: str | None = None,
    q_thresholds: Sequence[int] | None = None,
    min_members: int = 3,
    nesting_tolerance: float = 5e-5,
    cauchy_multiplier: float = 1.25,
) -> NestedSubladderLimitCertificate:
    """Build a nested tail chain from branch-certified tail intervals.

    The chain is assembled by evaluating every admissible q-threshold, building
    the corresponding branch-certified tail envelope, and retaining the longest
    suffix for which consecutive intervals remain compatible in a nested,
    Cauchy-like sense.
    """
    entries = _extract_branch_certified_entries(ladder)
    usable = len(entries)
    if usable < min_members:
        return NestedSubladderLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            usable_entry_count=int(usable),
            candidate_thresholds=[],
            chain_thresholds=[],
            chain_length=0,
            chain_is_nested=False,
            chain_is_cauchy_like=False,
            final_interval_lo=None,
            final_interval_hi=None,
            final_interval_width=None,
            outer_chain_interval_lo=None,
            outer_chain_interval_hi=None,
            outer_chain_interval_width=None,
            shrink_ratio=None,
            max_center_step=None,
            theorem_status='nested-subladder-limit-incomplete',
            notes='Not enough certified branch entries are available to build a nested tail chain.',
            intervals=[],
        )

    thresholds = sorted(set([int(t) for t in (q_thresholds or [])] + _source_thresholds(refined, asymptotic_audit) + _default_thresholds(entries, min_members=min_members)))
    interval_objs: list[NestedSubladderInterval] = []
    prev = None
    for thr in thresholds:
        cert = build_branch_certified_irrational_limit_certificate(
            ladder,
            refined=refined,
            asymptotic_audit=asymptotic_audit,
            rho_target=rho_target,
            family_label=family_label,
            q_thresholds=[thr],
            min_members=min_members,
        ).to_dict()
        lo = cert.get('selected_limit_interval_lo')
        hi = cert.get('selected_limit_interval_hi')
        if lo is None or hi is None:
            continue
        nested = None
        cauchy = None
        center_step = None
        width_ratio = None
        center = cert.get('selected_consensus_center')
        width = cert.get('selected_limit_interval_width')
        if prev is not None:
            nested = _interval_subset(float(lo), float(hi), prev.interval_lo, prev.interval_hi, nesting_tolerance)
            prev_center = prev.center
            if center is not None and prev_center is not None:
                center_step = abs(float(center) - float(prev_center))
                allowed = cauchy_multiplier * max(prev.interval_width, float(width or prev.interval_width))
                cauchy = center_step <= allowed
            else:
                cauchy = False
            if prev.interval_width > 0.0 and width is not None:
                width_ratio = float(width) / float(prev.interval_width)
        obj = NestedSubladderInterval(
            q_threshold=int(thr),
            member_qs=[int(x) for x in cert.get('selected_tail_qs', [])],
            member_labels=[str(x) for x in cert.get('selected_tail_labels', [])],
            interval_lo=float(lo),
            interval_hi=float(hi),
            interval_width=float(width if width is not None else float(hi) - float(lo)),
            center=None if center is None else float(center),
            derivative_backed_fraction=None if cert.get('derivative_backed_fraction') is None else float(cert.get('derivative_backed_fraction')),
            interval_newton_fraction=None if cert.get('interval_newton_fraction') is None else float(cert.get('interval_newton_fraction')),
            pairwise_overlap_fraction=None if cert.get('pairwise_overlap_fraction') is None else float(cert.get('pairwise_overlap_fraction')),
            theorem_status=str(cert.get('theorem_status', 'unknown')),
            nested_with_previous=nested,
            cauchy_with_previous=cauchy,
            center_step_from_previous=center_step,
            width_ratio_to_previous=width_ratio,
        )
        interval_objs.append(obj)
        prev = obj

    if len(interval_objs) < 2:
        return NestedSubladderLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            usable_entry_count=int(usable),
            candidate_thresholds=thresholds,
            chain_thresholds=[int(i.q_threshold) for i in interval_objs],
            chain_length=len(interval_objs),
            chain_is_nested=False,
            chain_is_cauchy_like=False,
            final_interval_lo=interval_objs[-1].interval_lo if interval_objs else None,
            final_interval_hi=interval_objs[-1].interval_hi if interval_objs else None,
            final_interval_width=interval_objs[-1].interval_width if interval_objs else None,
            outer_chain_interval_lo=interval_objs[0].interval_lo if interval_objs else None,
            outer_chain_interval_hi=interval_objs[0].interval_hi if interval_objs else None,
            outer_chain_interval_width=interval_objs[0].interval_width if interval_objs else None,
            shrink_ratio=None,
            max_center_step=None,
            theorem_status='nested-subladder-limit-incomplete',
            notes='Fewer than two admissible tail thresholds produced certified intervals, so no nested subladder chain could be checked.',
            intervals=interval_objs,
        )

    best_chain_start = 0
    best_chain_len = 1
    current_start = 0
    for i in range(1, len(interval_objs)):
        ok = bool(interval_objs[i].nested_with_previous) and bool(interval_objs[i].cauchy_with_previous)
        if ok:
            chain_len = i - current_start + 1
            if chain_len > best_chain_len:
                best_chain_len = chain_len
                best_chain_start = current_start
        else:
            current_start = i
    chain = interval_objs[best_chain_start:best_chain_start + best_chain_len]
    chain_thresholds = [int(i.q_threshold) for i in chain]
    chain_is_nested = all(bool(i.nested_with_previous) for i in chain[1:]) if len(chain) > 1 else False
    chain_is_cauchy = all(bool(i.cauchy_with_previous) for i in chain[1:]) if len(chain) > 1 else False
    inter_lo, inter_hi = chain[0].interval_lo, chain[0].interval_hi
    for item in chain[1:]:
        inter = _interval_intersection(inter_lo, inter_hi, item.interval_lo, item.interval_hi)
        if inter is None:
            inter_lo = inter_hi = None
            break
        inter_lo, inter_hi, _ = inter
    final_width = None if inter_lo is None or inter_hi is None else float(inter_hi - inter_lo)
    outer_width = chain[0].interval_width if chain else None
    shrink_ratio = None if final_width is None or outer_width in (None, 0.0) else float(final_width / outer_width)
    max_center_step = None
    steps = [i.center_step_from_previous for i in chain[1:] if i.center_step_from_previous is not None]
    if steps:
        max_center_step = float(max(steps))

    if len(chain) >= 3 and chain_is_nested and chain_is_cauchy and final_width is not None:
        status = 'nested-subladder-limit-strong'
    elif len(chain) >= 2 and final_width is not None:
        status = 'nested-subladder-limit-moderate'
    else:
        status = 'nested-subladder-limit-weak'

    notes = (
        'This certificate organizes the branch-certified q-tail envelopes into a nested convergent-subladder chain. '
        'It is not yet a proof of rational-to-irrational convergence, but it is closer to a Cauchy-style theorem object: successive higher-q tails keep the candidate irrational threshold trapped inside a shrinking compatible interval family.'
    )
    return NestedSubladderLimitCertificate(
        rho_target=None if rho_target is None else float(rho_target),
        family_label=family_label,
        usable_entry_count=int(usable),
        candidate_thresholds=[int(x) for x in thresholds],
        chain_thresholds=chain_thresholds,
        chain_length=len(chain),
        chain_is_nested=chain_is_nested,
        chain_is_cauchy_like=chain_is_cauchy,
        final_interval_lo=inter_lo,
        final_interval_hi=inter_hi,
        final_interval_width=final_width,
        outer_chain_interval_lo=chain[0].interval_lo if chain else None,
        outer_chain_interval_hi=chain[0].interval_hi if chain else None,
        outer_chain_interval_width=outer_width,
        shrink_ratio=shrink_ratio,
        max_center_step=max_center_step,
        theorem_status=status,
        notes=notes,
        intervals=interval_objs,
    )


__all__ = [
    'NestedSubladderInterval',
    'NestedSubladderLimitCertificate',
    'build_nested_subladder_limit_certificate',
]
