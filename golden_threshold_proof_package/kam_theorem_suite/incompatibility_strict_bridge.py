from __future__ import annotations

"""Strict bridge promotion for the upper-side incompatibility front.

Stage 36 introduced a bridge-profile ladder that can certify a strong upper-side
bridge under lighter theorem-facing profiles when the direct strict bridge is
still weak. The next strongest move is to improve the *direct* strict bridge
itself by extracting a strict support core from the adaptive tail-coherence
entries.

This module searches the existing adaptive neighborhood object for a denominator
block and supporting entry subcluster that already satisfy the strict bridge
hypotheses, even when the default tail-coherence pass failed to expose such a
core. The resulting certificate is still derived from the current adaptive
neighborhood package, but it is stronger and more direct than falling back to a
lighter profile ladder.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from .adaptive_tail_coherence import (
    build_golden_adaptive_tail_coherence_certificate,
    _normalize_golden_adaptive_tail_coherence_entry,
    _support_set_for_entry,
    _tail_signature_for_entry,
)
from .golden_aposteriori import golden_inverse
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


def _window_intersection(windows: Iterable[tuple[float, float]]) -> tuple[float | None, float | None]:
    items = [(float(lo), float(hi)) for lo, hi in windows]
    if not items:
        return None, None
    lo = max(lo for lo, _ in items)
    hi = min(hi for _, hi in items)
    if lo > hi:
        return None, None
    return float(lo), float(hi)


def _window_hull(windows: Iterable[tuple[float, float]]) -> tuple[float | None, float | None]:
    items = [(float(lo), float(hi)) for lo, hi in windows]
    if not items:
        return None, None
    return float(min(lo for lo, _ in items)), float(max(hi for _, hi in items))


@dataclass
class StrictBridgeCandidate:
    tail_qs: list[int]
    supporting_entry_indices: list[int]
    upper_lo: float | None
    upper_hi: float | None
    barrier_lo: float | None
    barrier_hi: float | None
    upper_width: float | None
    barrier_width: float | None
    incompatibility_gap: float | None
    gap_to_width_ratio: float | None
    support_fraction_floor: float | None
    entry_coverage_floor: float | None
    tail_is_suffix: bool
    score: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenIncompatibilityStrictBridgeCertificate:
    rho: float
    family_label: str
    source_name: str
    coherence_source_status: str
    certified_upper_lo: float | None
    certified_upper_hi: float | None
    certified_upper_width: float | None
    certified_barrier_lo: float | None
    certified_barrier_hi: float | None
    certified_barrier_width: float | None
    certified_gap: float | None
    gap_to_localization_ratio: float | None
    certified_tail_qs: list[int]
    certified_tail_start_q: int | None
    certified_tail_is_suffix: bool
    supporting_entry_count: int
    support_fraction_floor: float | None
    entry_coverage_floor: float | None
    promoted_entry_indices: list[int]
    candidate_count: int
    strongest_candidate: dict[str, Any]
    missing_hypotheses: list[str]
    bridge_margin: float | None
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _status_rank(status: str) -> int:
    if str(status).endswith('-strong'):
        return 4
    if str(status).endswith('-moderate'):
        return 3
    if str(status).endswith('-weak'):
        return 2
    if str(status).endswith('-fragile'):
        return 1
    return 0


def _candidate_score(
    *,
    support_fraction_floor: float | None,
    entry_coverage_floor: float | None,
    gap_to_width_ratio: float | None,
    gap: float | None,
    tail_len: int,
    entry_count: int,
    tail_is_suffix: bool,
    strong: bool,
) -> tuple[float, ...]:
    return (
        1.0 if strong else 0.0,
        1.0 if tail_is_suffix else 0.0,
        float(support_fraction_floor or 0.0),
        float(entry_coverage_floor or 0.0),
        float(gap_to_width_ratio or 0.0),
        float(gap or 0.0),
        float(tail_len),
        float(entry_count),
    )




def _build_golden_incompatibility_strict_bridge_from_coherence_payload(
    coherence: dict[str, Any],
    *,
    rho: float,
    family_label: str,
    min_cluster_size: int = 2,
    min_tail_members: int = 2,
    min_support_fraction: float = 0.75,
    min_entry_coverage: float = 0.75,
    min_gap_to_width_ratio: float = 1.0,
    require_suffix_tail: bool = False,
    source_name: str = 'strict-bridge-promotion',
    notes_prefix: str | None = None,
) -> GoldenIncompatibilityStrictBridgeCertificate:
    raw_entries = list(coherence.get('entries', []))
    if not raw_entries:
        return GoldenIncompatibilityStrictBridgeCertificate(rho=rho, family_label=family_label, source_name=source_name, coherence_source_status=str(coherence.get('theorem_status', 'unknown')), certified_upper_lo=None, certified_upper_hi=None, certified_upper_width=None, certified_barrier_lo=None, certified_barrier_hi=None, certified_barrier_width=None, certified_gap=None, gap_to_localization_ratio=None, certified_tail_qs=[], certified_tail_start_q=None, certified_tail_is_suffix=False, supporting_entry_count=0, support_fraction_floor=None, entry_coverage_floor=None, promoted_entry_indices=[], candidate_count=0, strongest_candidate={}, missing_hypotheses=['coherence_entries_available'], bridge_margin=None, theorem_status='golden-incompatibility-theorem-bridge-failed', notes=(notes_prefix + ' ' if notes_prefix else '') + 'No adaptive tail-coherence entries were available for strict bridge promotion.')
    entry_objs = [_normalize_golden_adaptive_tail_coherence_entry(entry) for entry in raw_entries]
    clustered = [int(i) for i in coherence.get('clustered_entry_indices', [])]
    successful = [int(i) for i in coherence.get('successful_entry_indices', [])]
    usable = clustered or successful or list(range(len(entry_objs)))
    usable = [i for i in usable if 0 <= i < len(entry_objs)]
    all_generated_qs = sorted({int(q) for i in usable for q in entry_objs[i].generated_qs if int(q) > 0})
    upper_windows = {i: (entry_objs[i].selected_upper_lo, entry_objs[i].selected_upper_hi) for i in usable}
    barrier_windows = {i: (entry_objs[i].selected_barrier_lo, entry_objs[i].selected_barrier_hi) for i in usable}
    support_sets = {i: _support_set_for_entry(entry_objs[i]) for i in usable}
    candidates=[]
    groups={}
    for i in usable:
        sig=_tail_signature_for_entry(entry_objs[i], min_tail_members=min_tail_members)
        if len(sig) >= int(min_tail_members): groups.setdefault(sig, []).append(i)
    for sig, indices in groups.items():
        indices=sorted(set(indices))
        if len(indices) < int(min_cluster_size): continue
        uppers=[]; barriers=[]
        for i in indices:
            ulo,uhi=upper_windows[i]; blo,bhi=barrier_windows[i]
            if ulo is None or uhi is None or blo is None or bhi is None: continue
            uppers.append((float(ulo), float(uhi))); barriers.append((float(blo), float(bhi)))
        if len(uppers) < int(min_cluster_size) or not barriers: continue
        upper_hull=_window_hull(uppers)
        rep_idx=min(indices, key=lambda j: float(entry_objs[j].selected_barrier_lo if entry_objs[j].selected_barrier_lo is not None else 1e99))
        blo=entry_objs[rep_idx].selected_barrier_lo; bhi=entry_objs[rep_idx].selected_barrier_hi
        if upper_hull[0] is None or upper_hull[1] is None or blo is None or bhi is None: continue
        tail=[int(q) for q in sig]
        support_fraction_floor=float(len(indices)/max(1,len(usable)))
        coverages=[float(sum(1 for q in tail if q in support_sets[i]) / len(tail)) for i in indices]
        entry_coverage_floor=min(coverages) if coverages else None
        upper_lo=float(upper_hull[0]); upper_hi=float(upper_hull[1])
        upper_width=float(upper_hi-upper_lo); barrier_width=float(float(bhi)-float(blo))
        gap=float(float(blo)-upper_hi); ratio=float(gap/max(1e-12,upper_width,barrier_width))
        tail_is_suffix=tail == [q for q in all_generated_qs if q >= tail[0]]
        strong=gap>0.0 and ratio>=float(min_gap_to_width_ratio) and support_fraction_floor>=float(min_support_fraction) and (entry_coverage_floor is not None and entry_coverage_floor>=float(min_entry_coverage)) and (not require_suffix_tail or tail_is_suffix)
        candidates.append(StrictBridgeCandidate(tail_qs=tail,supporting_entry_indices=[int(i) for i in indices],upper_lo=upper_lo,upper_hi=upper_hi,barrier_lo=float(blo),barrier_hi=float(bhi),upper_width=upper_width,barrier_width=barrier_width,incompatibility_gap=gap,gap_to_width_ratio=ratio,support_fraction_floor=support_fraction_floor,entry_coverage_floor=float(entry_coverage_floor) if entry_coverage_floor is not None else None,tail_is_suffix=bool(tail_is_suffix),score=_candidate_score(support_fraction_floor=support_fraction_floor,entry_coverage_floor=entry_coverage_floor,gap_to_width_ratio=ratio,gap=gap,tail_len=len(tail),entry_count=len(indices),tail_is_suffix=tail_is_suffix,strong=strong)))
    witness_sets = {i: {int(q) for q in entry_objs[i].witness_qs if int(q) > 0} for i in usable}
    for start in range(len(all_generated_qs)):
        for end in range(start,len(all_generated_qs)):
            tail=all_generated_qs[start:end+1]
            if len(tail) < int(min_tail_members): continue
            supporting_entries=[]; per_entry_coverages=[]; per_q_support=[]
            for i in usable:
                supported=sum(1 for q in tail if q in witness_sets[i]); coverage=float(supported/len(tail))
                if coverage >= float(min_entry_coverage): supporting_entries.append(i); per_entry_coverages.append(coverage)
            if len(supporting_entries) < int(min_cluster_size): continue
            for q in tail: per_q_support.append(float(sum(1 for i in usable if q in witness_sets[i]) / max(1,len(usable))))
            support_fraction_floor=min(per_q_support) if per_q_support else None
            if support_fraction_floor is None or support_fraction_floor < float(min_support_fraction): continue
            uppers=[]; barriers=[]
            for i in supporting_entries:
                ulo,uhi=upper_windows[i]; blo,bhi=barrier_windows[i]
                if ulo is None or uhi is None or blo is None or bhi is None: continue
                uppers.append((float(ulo), float(uhi))); barriers.append((float(blo), float(bhi)))
            upper_lo_i, upper_hi_i = _window_intersection(uppers); barrier_lo_i, barrier_hi_i = _window_intersection(barriers)
            if upper_lo_i is None or upper_hi_i is None or barrier_lo_i is None or barrier_hi_i is None: continue
            upper_width=float(upper_hi_i-upper_lo_i); barrier_width=float(barrier_hi_i-barrier_lo_i)
            gap=float(barrier_lo_i-upper_hi_i); ratio=float(gap/max(1e-12,upper_width,barrier_width))
            entry_coverage_floor=min(per_entry_coverages) if per_entry_coverages else None
            tail_is_suffix=tail == [q for q in all_generated_qs if q >= tail[0]]
            strong=gap>0.0 and ratio>=float(min_gap_to_width_ratio) and (not require_suffix_tail or tail_is_suffix)
            candidates.append(StrictBridgeCandidate(tail_qs=[int(q) for q in tail],supporting_entry_indices=[int(i) for i in supporting_entries],upper_lo=float(upper_lo_i),upper_hi=float(upper_hi_i),barrier_lo=float(barrier_lo_i),barrier_hi=float(barrier_hi_i),upper_width=upper_width,barrier_width=barrier_width,incompatibility_gap=gap,gap_to_width_ratio=ratio,support_fraction_floor=float(support_fraction_floor),entry_coverage_floor=float(entry_coverage_floor) if entry_coverage_floor is not None else None,tail_is_suffix=bool(tail_is_suffix),score=_candidate_score(support_fraction_floor=support_fraction_floor,entry_coverage_floor=entry_coverage_floor,gap_to_width_ratio=ratio,gap=gap,tail_len=len(tail),entry_count=len(supporting_entries),tail_is_suffix=tail_is_suffix,strong=strong)))
    best=max(candidates,key=lambda c:c.score) if candidates else None
    if best is None:
        return GoldenIncompatibilityStrictBridgeCertificate(rho=rho,family_label=family_label,source_name=source_name,coherence_source_status=str(coherence.get('theorem_status','unknown')),certified_upper_lo=None,certified_upper_hi=None,certified_upper_width=None,certified_barrier_lo=None,certified_barrier_hi=None,certified_barrier_width=None,certified_gap=None,gap_to_localization_ratio=None,certified_tail_qs=[],certified_tail_start_q=None,certified_tail_is_suffix=False,supporting_entry_count=0,support_fraction_floor=None,entry_coverage_floor=None,promoted_entry_indices=[],candidate_count=0,strongest_candidate={},missing_hypotheses=['supporting_tail_exists'],bridge_margin=None,theorem_status='golden-incompatibility-theorem-bridge-failed',notes=(notes_prefix + ' ' if notes_prefix else '') + 'The adaptive neighborhood did not yet contain a strict-support denominator block with coherent upper/barrier intersections.')
    missing=[]
    if best.incompatibility_gap is None or best.incompatibility_gap <= 0.0: missing.append('positive_incompatibility_gap')
    if best.gap_to_width_ratio is None or best.gap_to_width_ratio < float(min_gap_to_width_ratio): missing.append('gap_dominates_localization')
    if not best.tail_qs: missing.append('supporting_tail_exists')
    if len(best.supporting_entry_indices) < int(min_cluster_size): missing.append('supporting_cluster_size')
    if best.support_fraction_floor is None or best.support_fraction_floor < float(min_support_fraction): missing.append('tail_support_fraction')
    if best.entry_coverage_floor is None or best.entry_coverage_floor < float(min_entry_coverage): missing.append('tail_entry_coverage_floor')
    if require_suffix_tail and not best.tail_is_suffix: missing.append('suffix_tail')
    margin_candidates=[best.incompatibility_gap,None if best.gap_to_width_ratio is None else float(best.gap_to_width_ratio-float(min_gap_to_width_ratio)),None if best.support_fraction_floor is None else float(best.support_fraction_floor-float(min_support_fraction)),None if best.entry_coverage_floor is None else float(best.entry_coverage_floor-float(min_entry_coverage)),float(len(best.supporting_entry_indices)-int(min_cluster_size)),float(len(best.tail_qs)-int(min_tail_members))]
    if require_suffix_tail: margin_candidates.append(1.0 if best.tail_is_suffix else -1.0)
    finite_margins=[float(x) for x in margin_candidates if x is not None]; bridge_margin=min(finite_margins) if finite_margins else None
    if not missing:
        status='golden-incompatibility-theorem-bridge-strong'; notes=(notes_prefix + ' ' if notes_prefix else '') + 'The direct strict upper bridge can now be promoted from the adaptive neighborhood itself: a strict support core yields a coherent upper envelope, a representative compatible barrier, a quantitative gap, and strict denominator-tail support.'
    elif best.tail_qs and best.incompatibility_gap is not None and best.incompatibility_gap > 0.0:
        status='golden-incompatibility-theorem-bridge-moderate'; notes=(notes_prefix + ' ' if notes_prefix else '') + 'A promoted support core now carries a tail-signature-supported upper/barrier object and positive incompatibility gap, but at least one strict bridge hypothesis remains below threshold.'
    elif best.tail_qs and best.upper_lo is not None:
        status='golden-incompatibility-theorem-bridge-weak'; notes=(notes_prefix + ' ' if notes_prefix else '') + 'The adaptive neighborhood contains a usable promoted support core, but the strict gap or support thresholds are not yet fully met.'
    else:
        status='golden-incompatibility-theorem-bridge-fragile'; notes=(notes_prefix + ' ' if notes_prefix else '') + 'The adaptive neighborhood still localizes the upper object, but no promoted strict support core has stabilized.'
    return GoldenIncompatibilityStrictBridgeCertificate(rho=rho,family_label=family_label,source_name=source_name,coherence_source_status=str(coherence.get('theorem_status','unknown')),certified_upper_lo=best.upper_lo,certified_upper_hi=best.upper_hi,certified_upper_width=best.upper_width,certified_barrier_lo=best.barrier_lo,certified_barrier_hi=best.barrier_hi,certified_barrier_width=best.barrier_width,certified_gap=best.incompatibility_gap,gap_to_localization_ratio=best.gap_to_width_ratio,certified_tail_qs=[int(q) for q in best.tail_qs],certified_tail_start_q=best.tail_qs[0] if best.tail_qs else None,certified_tail_is_suffix=bool(best.tail_is_suffix),supporting_entry_count=len(best.supporting_entry_indices),support_fraction_floor=best.support_fraction_floor,entry_coverage_floor=best.entry_coverage_floor,promoted_entry_indices=[int(i) for i in best.supporting_entry_indices],candidate_count=len(candidates),strongest_candidate=best.to_dict(),missing_hypotheses=missing,bridge_margin=bridge_margin,theorem_status=status,notes=notes)


def build_golden_incompatibility_strict_bridge_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    min_cluster_size: int = 2,
    min_tail_members: int = 2,
    min_support_fraction: float = 0.75,
    min_entry_coverage: float = 0.75,
    min_gap_to_width_ratio: float = 1.0,
    require_suffix_tail: bool = False,
    adaptive_tail_coherence_certificate: Mapping[str, Any] | None = None,
    **coherence_kwargs,
) -> GoldenIncompatibilityStrictBridgeCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    if adaptive_tail_coherence_certificate is not None:
        coherence = dict(adaptive_tail_coherence_certificate)
    else:
        coherence = build_golden_adaptive_tail_coherence_certificate(
            family=family,
            rho=rho,
            min_cluster_size=min_cluster_size,
            min_tail_members=min_tail_members,
            min_q_support_fraction=min(0.5, float(min_support_fraction)),
            min_entry_tail_coverage=min(0.5, float(min_entry_coverage)),
            min_tail_support_fraction=min(0.5, float(min_support_fraction)),
            **coherence_kwargs,
        ).to_dict()
    return _build_golden_incompatibility_strict_bridge_from_coherence_payload(
        coherence,
        rho=rho,
        family_label=_family_label(family),
        min_cluster_size=min_cluster_size,
        min_tail_members=min_tail_members,
        min_support_fraction=min_support_fraction,
        min_entry_coverage=min_entry_coverage,
        min_gap_to_width_ratio=min_gap_to_width_ratio,
        require_suffix_tail=require_suffix_tail,
        source_name='strict-bridge-promotion',
    )



__all__ = [
    'StrictBridgeCandidate',
    'GoldenIncompatibilityStrictBridgeCertificate',
    '_build_golden_incompatibility_strict_bridge_from_coherence_payload',
    'build_golden_incompatibility_strict_bridge_certificate',
]
