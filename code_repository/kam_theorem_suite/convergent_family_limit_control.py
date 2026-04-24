from __future__ import annotations

"""Convergent-family irrational-limit control.

This module is the strongest convergence-facing layer in the current bridge.

Earlier stages used:
1. a fitted q-tail model,
2. a non-model-based branch-certified tail envelope, and
3. a nested suffix chain over q-thresholds.

The purpose of this module is different: it tries to use the *actual convergent
family structure* of the ladder, rather than generic high-q suffixes.  In the
golden setting this means looking for a contiguous tail whose denominators obey
a Fibonacci-style recurrence and whose numerators are compatible with the same
parent/child rule.

Once such a chain is found, the module builds stepwise compatibility bounds
between consecutive certified root windows and derives a telescoping remainder
bound from the observed contraction of those step bounds.  The result is still
not a full theorem, but it is the first limit-control layer in the bundle that
leans explicitly on parent/child convergent structure rather than just on
high-denominator consensus.
"""

from dataclasses import asdict, dataclass
from math import inf, isfinite
from typing import Any, Sequence

from .branch_certified_limit_control import _extract_branch_certified_entries


@dataclass
class ConvergentFamilyStep:
    grandparent_label: str | None
    parent_label: str
    child_label: str
    grandparent_q: int | None
    parent_q: int
    child_q: int
    q_recurrence_ok: bool
    p_recurrence_residual: int | None
    determinant_parent_child: int | None
    center_shift: float
    overlap_width: float
    overlap_fraction: float
    child_nested_in_parent: bool
    step_bound: float
    width_ratio: float | None
    step_bound_ratio_to_previous: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConvergentFamilyLimitCertificate:
    rho_target: float | None
    family_label: str | None
    usable_entry_count: int
    chain_labels: list[str]
    chain_qs: list[int]
    chain_ps: list[int]
    chain_length: int
    q_recurrence_fraction: float | None
    p_recurrence_fraction: float | None
    parent_child_overlap_fraction: float | None
    parent_child_nested_fraction: float | None
    chain_intersection_lo: float | None
    chain_intersection_hi: float | None
    chain_intersection_width: float | None
    last_window_lo: float | None
    last_window_hi: float | None
    last_window_width: float | None
    last_step_bound: float | None
    observed_contraction_ratio: float | None
    telescoping_tail_bound: float | None
    limit_interval_lo: float | None
    limit_interval_hi: float | None
    limit_interval_width: float | None
    theorem_status: str
    notes: str
    steps: list[ConvergentFamilyStep]

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho_target': self.rho_target,
            'family_label': self.family_label,
            'usable_entry_count': int(self.usable_entry_count),
            'chain_labels': [str(x) for x in self.chain_labels],
            'chain_qs': [int(x) for x in self.chain_qs],
            'chain_ps': [int(x) for x in self.chain_ps],
            'chain_length': int(self.chain_length),
            'q_recurrence_fraction': self.q_recurrence_fraction,
            'p_recurrence_fraction': self.p_recurrence_fraction,
            'parent_child_overlap_fraction': self.parent_child_overlap_fraction,
            'parent_child_nested_fraction': self.parent_child_nested_fraction,
            'chain_intersection_lo': self.chain_intersection_lo,
            'chain_intersection_hi': self.chain_intersection_hi,
            'chain_intersection_width': self.chain_intersection_width,
            'last_window_lo': self.last_window_lo,
            'last_window_hi': self.last_window_hi,
            'last_window_width': self.last_window_width,
            'last_step_bound': self.last_step_bound,
            'observed_contraction_ratio': self.observed_contraction_ratio,
            'telescoping_tail_bound': self.telescoping_tail_bound,
            'limit_interval_lo': self.limit_interval_lo,
            'limit_interval_hi': self.limit_interval_hi,
            'limit_interval_width': self.limit_interval_width,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
            'steps': [s.to_dict() for s in self.steps],
        }


def _interval_intersection(windows: Sequence[tuple[float, float]]) -> tuple[float | None, float | None, float | None]:
    if not windows:
        return None, None, None
    lo = max(float(w[0]) for w in windows)
    hi = min(float(w[1]) for w in windows)
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _window_overlap(a_lo: float, a_hi: float, b_lo: float, b_hi: float) -> tuple[float, float]:
    width = max(0.0, min(float(a_hi), float(b_hi)) - max(float(a_lo), float(b_lo)))
    denom = max(min(float(a_hi) - float(a_lo), float(b_hi) - float(b_lo)), 1e-15)
    return float(width), float(width / denom)


def _is_chain_step(a: dict[str, Any], b: dict[str, Any], c: dict[str, Any], *, p_tolerance: int) -> bool:
    q_ok = int(c['q']) == int(a['q']) + int(b['q'])
    p_resid = abs(int(c['p']) - (int(a['p']) + int(b['p'])))
    return bool(q_ok and p_resid <= int(p_tolerance))


def _longest_convergent_chain(entries: Sequence[dict[str, Any]], *, p_tolerance: int) -> list[dict[str, Any]]:
    if len(entries) <= 2:
        return list(entries)
    best: list[dict[str, Any]] = []
    n = len(entries)
    for i in range(n - 1):
        for j in range(i + 1, n):
            chain = [entries[i], entries[j]]
            last_index = j
            while True:
                found = None
                for k in range(last_index + 1, n):
                    if _is_chain_step(chain[-2], chain[-1], entries[k], p_tolerance=p_tolerance):
                        found = k
                        break
                if found is None:
                    break
                chain.append(entries[found])
                last_index = found
            if len(chain) > len(best):
                best = chain
    return best or list(entries[:2])


def _fraction_true(values: Sequence[bool | None]) -> float | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return float(sum(bool(v) for v in vals) / len(vals))


def build_convergent_family_limit_certificate(
    ladder: dict[str, Any],
    *,
    rho_target: float | None = None,
    family_label: str | None = None,
    min_chain_length: int = 4,
    p_tolerance: int = 1,
    nesting_tolerance: float = 5e-5,
    contraction_cap: float = 0.9,
    min_overlap_fraction: float = 0.5,
) -> ConvergentFamilyLimitCertificate:
    """Build a convergent-family limit certificate from a certified ladder.

    The certificate searches for the longest contiguous ladder subsequence whose
    denominators obey a convergent-family recurrence.  Consecutive windows are
    then checked for overlap/nestedness, and the observed step-bound contraction
    is used to derive a telescoping remainder bound from the final certified
    window.
    """
    entries = _extract_branch_certified_entries(ladder)
    usable = len(entries)
    if usable < 2:
        return ConvergentFamilyLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            usable_entry_count=int(usable),
            chain_labels=[],
            chain_qs=[],
            chain_ps=[],
            chain_length=0,
            q_recurrence_fraction=None,
            p_recurrence_fraction=None,
            parent_child_overlap_fraction=None,
            parent_child_nested_fraction=None,
            chain_intersection_lo=None,
            chain_intersection_hi=None,
            chain_intersection_width=None,
            last_window_lo=None,
            last_window_hi=None,
            last_window_width=None,
            last_step_bound=None,
            observed_contraction_ratio=None,
            telescoping_tail_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            theorem_status='convergent-family-limit-incomplete',
            notes='Not enough certified branch entries are available to identify a convergent-family tail.',
            steps=[],
        )

    chain = _longest_convergent_chain(entries, p_tolerance=p_tolerance)
    chain_labels = [str(e['label']) for e in chain]
    chain_qs = [int(e['q']) for e in chain]
    chain_ps = [int(e['p']) for e in chain]

    if len(chain) < min_chain_length:
        last = chain[-1] if chain else None
        return ConvergentFamilyLimitCertificate(
            rho_target=None if rho_target is None else float(rho_target),
            family_label=family_label,
            usable_entry_count=int(usable),
            chain_labels=chain_labels,
            chain_qs=chain_qs,
            chain_ps=chain_ps,
            chain_length=len(chain),
            q_recurrence_fraction=None,
            p_recurrence_fraction=None,
            parent_child_overlap_fraction=None,
            parent_child_nested_fraction=None,
            chain_intersection_lo=None,
            chain_intersection_hi=None,
            chain_intersection_width=None,
            last_window_lo=None if last is None else float(last['lo']),
            last_window_hi=None if last is None else float(last['hi']),
            last_window_width=None if last is None else float(last['width']),
            last_step_bound=None,
            observed_contraction_ratio=None,
            telescoping_tail_bound=None,
            limit_interval_lo=None,
            limit_interval_hi=None,
            limit_interval_width=None,
            theorem_status='convergent-family-limit-incomplete',
            notes='A certified tail exists, but it is not yet long enough to support a convergent-family telescoping bound.',
            steps=[],
        )

    steps: list[ConvergentFamilyStep] = []
    step_bounds: list[float] = []
    q_ok_flags: list[bool] = []
    p_ok_flags: list[bool] = []
    overlap_flags: list[bool] = []
    nested_flags: list[bool] = []

    for idx in range(1, len(chain)):
        parent = chain[idx - 1]
        child = chain[idx]
        gp = chain[idx - 2] if idx >= 2 else None
        q_ok = False
        p_residual = None
        if gp is not None:
            q_ok = int(child['q']) == int(parent['q']) + int(gp['q'])
            p_residual = abs(int(child['p']) - (int(parent['p']) + int(gp['p'])))
            q_ok_flags.append(bool(q_ok))
            p_ok_flags.append(bool(p_residual <= int(p_tolerance)))
        overlap_width, overlap_fraction = _window_overlap(parent['lo'], parent['hi'], child['lo'], child['hi'])
        nested = float(child['lo']) >= float(parent['lo']) - nesting_tolerance and float(child['hi']) <= float(parent['hi']) + nesting_tolerance
        center_shift = abs(float(child['center']) - float(parent['center']))
        step_bound = float(center_shift + 0.5 * (float(parent['width']) + float(child['width'])))
        step_bound_ratio = None
        if step_bounds and step_bounds[-1] > 0.0:
            step_bound_ratio = float(step_bound / step_bounds[-1])
        step_bounds.append(step_bound)
        overlap_flags.append(overlap_fraction >= min_overlap_fraction)
        nested_flags.append(nested)
        det = int(parent['p']) * int(child['q']) - int(parent['q']) * int(child['p'])
        steps.append(
            ConvergentFamilyStep(
                grandparent_label=None if gp is None else str(gp['label']),
                parent_label=str(parent['label']),
                child_label=str(child['label']),
                grandparent_q=None if gp is None else int(gp['q']),
                parent_q=int(parent['q']),
                child_q=int(child['q']),
                q_recurrence_ok=bool(q_ok) if gp is not None else False,
                p_recurrence_residual=p_residual,
                determinant_parent_child=int(det),
                center_shift=float(center_shift),
                overlap_width=float(overlap_width),
                overlap_fraction=float(overlap_fraction),
                child_nested_in_parent=bool(nested),
                step_bound=float(step_bound),
                width_ratio=None if float(parent['width']) <= 0.0 else float(float(child['width']) / float(parent['width'])),
                step_bound_ratio_to_previous=step_bound_ratio,
            )
        )

    ratios = [s.step_bound_ratio_to_previous for s in steps if s.step_bound_ratio_to_previous is not None and isfinite(float(s.step_bound_ratio_to_previous))]
    observed_ratio = None if not ratios else float(max(float(r) for r in ratios))
    telescoping_tail = None
    if observed_ratio is not None and 0.0 <= float(observed_ratio) < 1.0 and step_bounds:
        telescoping_tail = float(step_bounds[-1] * float(observed_ratio) / max(1.0 - float(observed_ratio), 1e-12))

    windows = [(float(e['lo']), float(e['hi'])) for e in chain]
    chain_inter_lo, chain_inter_hi, chain_inter_w = _interval_intersection(windows)
    last = chain[-1]
    last_lo = float(last['lo'])
    last_hi = float(last['hi'])
    last_w = float(last['width'])

    limit_lo = None
    limit_hi = None
    limit_w = None
    if telescoping_tail is not None:
        limit_lo = float(last_lo - telescoping_tail)
        limit_hi = float(last_hi + telescoping_tail)
        if chain_inter_lo is not None and chain_inter_hi is not None:
            limit_lo = max(float(limit_lo), float(chain_inter_lo))
            limit_hi = min(float(limit_hi), float(chain_inter_hi))
        if limit_hi >= limit_lo:
            limit_w = float(limit_hi - limit_lo)
        else:
            limit_lo = None
            limit_hi = None
            limit_w = None

    q_frac = _fraction_true(q_ok_flags)
    p_frac = _fraction_true(p_ok_flags)
    overlap_frac = _fraction_true(overlap_flags)
    nested_frac = _fraction_true(nested_flags)

    if (
        limit_lo is not None
        and observed_ratio is not None
        and observed_ratio < contraction_cap
        and q_frac is not None and q_frac >= 1.0
        and p_frac is not None and p_frac >= 1.0
        and overlap_frac is not None and overlap_frac >= 1.0
    ):
        status = 'convergent-family-limit-strong'
        notes = (
            'A genuine convergent-family tail was detected: the selected high-q subsequence satisfies the parent/child recurrence, consecutive certified crossing windows remain overlap-compatible, and the observed step bounds contract strongly enough to yield a telescoping remainder bound from the last certified convergent window.'
        )
    elif len(chain) >= min_chain_length and telescoping_tail is not None and q_frac is not None and q_frac >= 0.75:
        status = 'convergent-family-limit-partial'
        notes = (
            'A substantial convergent-like tail was detected and supports a telescoping remainder bound, but the chain is not yet fully exact or uniformly overlap-compatible at every parent/child step.'
        )
    else:
        status = 'convergent-family-limit-incomplete'
        notes = (
            'The certified ladder does not yet exhibit a sufficiently rigid convergent-family tail with usable telescoping control.'
        )

    return ConvergentFamilyLimitCertificate(
        rho_target=None if rho_target is None else float(rho_target),
        family_label=family_label,
        usable_entry_count=int(usable),
        chain_labels=chain_labels,
        chain_qs=chain_qs,
        chain_ps=chain_ps,
        chain_length=len(chain),
        q_recurrence_fraction=q_frac,
        p_recurrence_fraction=p_frac,
        parent_child_overlap_fraction=overlap_frac,
        parent_child_nested_fraction=nested_frac,
        chain_intersection_lo=chain_inter_lo,
        chain_intersection_hi=chain_inter_hi,
        chain_intersection_width=chain_inter_w,
        last_window_lo=last_lo,
        last_window_hi=last_hi,
        last_window_width=last_w,
        last_step_bound=None if not step_bounds else float(step_bounds[-1]),
        observed_contraction_ratio=observed_ratio,
        telescoping_tail_bound=telescoping_tail,
        limit_interval_lo=limit_lo,
        limit_interval_hi=limit_hi,
        limit_interval_width=limit_w,
        theorem_status=status,
        notes=notes,
        steps=steps,
    )


__all__ = [
    'ConvergentFamilyStep',
    'ConvergentFamilyLimitCertificate',
    'build_convergent_family_limit_certificate',
]
