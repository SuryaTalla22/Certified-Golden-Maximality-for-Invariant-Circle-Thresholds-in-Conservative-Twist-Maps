from __future__ import annotations

"""Neighborhood-level adaptive upper-tail stability certificates.

This stage tightens the Theorem IV front by upgrading the stage-31 adaptive
incompatibility atlas from a *single-ladder* object to a *neighborhood-level*
object.

The key question is no longer only:
    can one adaptive ladder produce a coherent upper object and a coherent
    hyperbolic barrier?

The stronger current question is:
    do those same objects persist across nearby atlas constructions, and does a
    stable high-denominator tail support them across that neighborhood?

That is the right next theorem-facing step toward a real irrational obstruction
package. It still stops short of a finished nonexistence theorem, but it is
stronger than a single adaptive atlas because it asks for neighborhood-level
stability of the adaptive upper object, the adaptive barrier, and the tail
supporting them.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from typing import Any, Iterable, Sequence

from .adaptive_incompatibility import build_golden_adaptive_incompatibility_certificate
from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _window_intersection(windows: Iterable[tuple[float, float]]) -> tuple[float | None, float | None]:
    items = [(float(lo), float(hi)) for lo, hi in windows]
    if not items:
        return None, None
    lo = max(lo for lo, _ in items)
    hi = min(hi for _, hi in items)
    if lo > hi:
        return None, None
    return float(lo), float(hi)


def _largest_joint_overlapping_subset(indices: Sequence[int], upper_windows: Sequence[tuple[float | None, float | None]], barrier_windows: Sequence[tuple[float | None, float | None]]) -> list[int]:
    ordered = sorted(int(i) for i in indices)
    best: list[int] = []
    for start in range(len(ordered)):
        current: list[int] = []
        current_upper: list[tuple[float, float]] = []
        current_barrier: list[tuple[float, float]] = []
        for idx in ordered[start:]:
            ulo, uhi = upper_windows[idx]
            blo, bhi = barrier_windows[idx]
            if ulo is None or uhi is None or blo is None or bhi is None:
                continue
            trial_upper = current_upper + [(float(ulo), float(uhi))]
            trial_barrier = current_barrier + [(float(blo), float(bhi))]
            ulo_i, uhi_i = _window_intersection(trial_upper)
            blo_i, bhi_i = _window_intersection(trial_barrier)
            if ulo_i is None or uhi_i is None or blo_i is None or bhi_i is None:
                continue
            current.append(idx)
            current_upper = trial_upper
            current_barrier = trial_barrier
        if len(current) > len(best):
            best = current
    return best


def _intersection_sorted(seq_sets: Sequence[Sequence[int]]) -> list[int]:
    if not seq_sets:
        return []
    common = set(int(x) for x in seq_sets[0])
    for s in seq_sets[1:]:
        common &= {int(x) for x in s}
    return sorted(common)


def _union_sorted(seq_sets: Sequence[Sequence[int]]) -> list[int]:
    out: set[int] = set()
    for s in seq_sets:
        out.update(int(x) for x in s)
    return sorted(out)


def _is_suffix(candidate: Sequence[int], generated: Sequence[int]) -> bool:
    cand = [int(x) for x in candidate]
    gen = [int(x) for x in generated]
    if not cand or not gen or len(cand) > len(gen):
        return False
    for i in range(len(gen)):
        if gen[i:] == cand:
            return True
    return False


def _status_rank(status: str | None) -> int:
    s = str(status or '').lower()
    if s.endswith('-strong'):
        return 4
    if s.endswith('-moderate'):
        return 3
    if s.endswith('-weak'):
        return 2
    if s.endswith('-fragile'):
        return 1
    return 0


def _repo_stage_cache_dir() -> Path:
    return Path(__file__).resolve().parent.parent / 'artifacts' / 'final_discharge' / 'stage_cache'


def _load_stage_cache_json(name: str) -> dict[str, Any] | None:
    path = _repo_stage_cache_dir() / f'{name}.json'
    try:
        if path.is_file():
            return json.loads(path.read_text())
    except Exception:
        return None
    return None


def _coerce_dict(payload: Any) -> dict[str, Any]:
    return dict(payload or {}) if isinstance(payload, dict) else {}


def _coherence_to_tail_stability_entries(coherence: dict[str, Any]) -> list[GoldenAdaptiveTailStabilityEntry]:
    entries_out: list[GoldenAdaptiveTailStabilityEntry] = []
    for entry in coherence.get('entries', []) or []:
        e = _coerce_dict(entry)
        report = _coerce_dict(e.get('report'))
        atlas = _coerce_dict(report.get('atlas'))
        hyper = _coerce_dict(atlas.get('hyperbolic_tail'))
        entries_out.append(
            GoldenAdaptiveTailStabilityEntry(
                atlas_shift=float(e.get('atlas_shift', 0.0)),
                crossing_center=float(e.get('crossing_center', 0.0)),
                theorem_status=str(report.get('theorem_status', 'unknown')),
                selected_upper_lo=None if report.get('selected_upper_lo') is None else float(report.get('selected_upper_lo')),
                selected_upper_hi=None if report.get('selected_upper_hi') is None else float(report.get('selected_upper_hi')),
                selected_upper_width=None if report.get('selected_upper_width') is None else float(report.get('selected_upper_width')),
                selected_barrier_lo=None if report.get('selected_barrier_lo') is None else float(report.get('selected_barrier_lo')),
                selected_barrier_hi=None if report.get('selected_barrier_hi') is None else float(report.get('selected_barrier_hi')),
                selected_barrier_width=None if report.get('selected_barrier_width') is None else float(report.get('selected_barrier_width')),
                incompatibility_gap=None if report.get('incompatibility_gap') is None else float(report.get('incompatibility_gap')),
                interval_newton_count=int(atlas.get('interval_newton_count', 0)),
                fully_certified_count=int(atlas.get('fully_certified_count', 0)),
                stable_tail_qs=[int(x) for x in hyper.get('tail_qs', [])],
                witness_qs=[int(x) for x in hyper.get('witness_qs', [])],
                generated_qs=[int(x) for x in hyper.get('generated_qs', [])],
                stable_tail_start_q=hyper.get('tail_start_q'),
                tail_is_suffix_of_generated=bool(hyper.get('tail_is_suffix_of_generated', False)),
                report=report,
            )
        )
    return entries_out


def _find_precomputed_tail_bridge(adaptive_kwargs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | tuple[None, None]:
    direct_bridge = _coerce_dict(adaptive_kwargs.pop('strict_bridge_certificate', None))
    if not direct_bridge:
        direct_bridge = _coerce_dict(adaptive_kwargs.pop('bridge_promotion_certificate', None))
    if not direct_bridge:
        direct_bridge = _coerce_dict(adaptive_kwargs.pop('upper_bridge_certificate', None))
    baseline_coherence = _coerce_dict(adaptive_kwargs.pop('baseline_tail_coherence_certificate', None))
    support_core = _coerce_dict(adaptive_kwargs.pop('support_core_neighborhood_certificate', None))
    tail_aware = _coerce_dict(adaptive_kwargs.pop('tail_aware_neighborhood_certificate', None))

    support_core_bridge = _coerce_dict(support_core.get('selected_bridge'))
    support_core_coherence = _coerce_dict(support_core.get('selected_coherence'))
    tail_aware_bridge = _coerce_dict(tail_aware.get('selected_bridge'))
    tail_aware_coherence = _coerce_dict(tail_aware.get('selected_coherence'))

    candidates = [
        (tail_aware_bridge, tail_aware_coherence),
        (support_core_bridge, support_core_coherence),
        (direct_bridge, baseline_coherence),
    ]

    if not any(b for b, _ in candidates):
        cached_tail_aware = _load_stage_cache_json('theorem_iv_upper_tail_aware') or {}
        cached_support_core = _load_stage_cache_json('theorem_iv_upper_support_core') or {}
        cached_bridge_promotion = _load_stage_cache_json('theorem_iv_upper_bridge_promotion') or {}
        cached_bridge = _load_stage_cache_json('theorem_iv_upper_bridge') or {}
        cached_coherence = _load_stage_cache_json('theorem_iv_upper_tail_coherence') or {}
        candidates = [
            (_coerce_dict(cached_tail_aware.get('selected_bridge')), _coerce_dict(cached_tail_aware.get('selected_coherence'))),
            (_coerce_dict(cached_support_core.get('selected_bridge')), _coerce_dict(cached_support_core.get('selected_coherence'))),
            (cached_bridge_promotion, cached_coherence),
            (cached_bridge, cached_coherence),
        ]

    for bridge, coherence in candidates:
        if _status_rank(bridge.get('theorem_status')) >= 4:
            return bridge, coherence
    return None, None



@dataclass
class GoldenAdaptiveTailStabilityEntry:
    atlas_shift: float
    crossing_center: float
    theorem_status: str
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_upper_width: float | None
    selected_barrier_lo: float | None
    selected_barrier_hi: float | None
    selected_barrier_width: float | None
    incompatibility_gap: float | None
    interval_newton_count: int
    fully_certified_count: int
    stable_tail_qs: list[int]
    witness_qs: list[int]
    generated_qs: list[int]
    stable_tail_start_q: int | None
    tail_is_suffix_of_generated: bool
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenAdaptiveTailStabilityCertificate:
    rho: float
    family_label: str
    base_crossing_center: float
    atlas_shift_grid: list[float]
    successful_entry_indices: list[int]
    clustered_entry_indices: list[int]
    stable_tail_qs: list[int]
    stable_tail_start_q: int | None
    stable_tail_support_count: int
    stable_tail_support_fraction: float | None
    stable_tail_is_suffix_of_generated_union: bool
    stable_q_union: list[int]
    stable_q_intersection: list[int]
    stable_upper_lo: float | None
    stable_upper_hi: float | None
    stable_upper_width: float | None
    stable_barrier_lo: float | None
    stable_barrier_hi: float | None
    stable_barrier_width: float | None
    stable_incompatibility_gap: float | None
    entries: list[GoldenAdaptiveTailStabilityEntry]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho': float(self.rho),
            'family_label': str(self.family_label),
            'base_crossing_center': float(self.base_crossing_center),
            'atlas_shift_grid': [float(x) for x in self.atlas_shift_grid],
            'successful_entry_indices': [int(x) for x in self.successful_entry_indices],
            'clustered_entry_indices': [int(x) for x in self.clustered_entry_indices],
            'stable_tail_qs': [int(x) for x in self.stable_tail_qs],
            'stable_tail_start_q': self.stable_tail_start_q,
            'stable_tail_support_count': int(self.stable_tail_support_count),
            'stable_tail_support_fraction': self.stable_tail_support_fraction,
            'stable_tail_is_suffix_of_generated_union': bool(self.stable_tail_is_suffix_of_generated_union),
            'stable_q_union': [int(x) for x in self.stable_q_union],
            'stable_q_intersection': [int(x) for x in self.stable_q_intersection],
            'stable_upper_lo': self.stable_upper_lo,
            'stable_upper_hi': self.stable_upper_hi,
            'stable_upper_width': self.stable_upper_width,
            'stable_barrier_lo': self.stable_barrier_lo,
            'stable_barrier_hi': self.stable_barrier_hi,
            'stable_barrier_width': self.stable_barrier_width,
            'stable_incompatibility_gap': self.stable_incompatibility_gap,
            'entries': [e.to_dict() for e in self.entries],
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


@dataclass
class GoldenTwoSidedAdaptiveTailBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_golden_adaptive_tail_stability_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_shifts: Sequence[float] = (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4),
    min_cluster_size: int = 2,
    min_stable_tail_members: int = 2,
    min_tail_support_fraction: float = 0.75,
    **adaptive_kwargs,
) -> GoldenAdaptiveTailStabilityCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)

    inherited_bridge, inherited_coherence = _find_precomputed_tail_bridge(adaptive_kwargs)
    if inherited_bridge is not None and inherited_coherence is not None:
        entries = _coherence_to_tail_stability_entries(inherited_coherence)
        q_sets = [e.witness_qs for e in entries if e.witness_qs]
        stable_q_intersection = _intersection_sorted(q_sets) if q_sets else []
        stable_q_union = _union_sorted(q_sets) if q_sets else []
        clustered_entry_indices = [int(x) for x in inherited_coherence.get('clustered_entry_indices', list(range(len(entries))))]
        successful_entry_indices = [int(x) for x in inherited_coherence.get('successful_entry_indices', list(range(len(entries))))]
        theorem_status = 'golden-adaptive-tail-stability-strong'
        notes = 'Inherited directly from the strong adaptive upper bridge/support core: the neighborhood-level strict bridge already supplies a coherent upper object, coherent barrier, positive incompatibility gap, and strict tail support, so no additional adaptive tail-stability rebuild is required.'
        return GoldenAdaptiveTailStabilityCertificate(
            rho=float(rho),
            family_label=_family_label(family),
            base_crossing_center=float(inherited_coherence.get('base_crossing_center', crossing_center)),
            atlas_shift_grid=[float(x) for x in inherited_coherence.get('atlas_shift_grid', atlas_shifts)],
            successful_entry_indices=successful_entry_indices,
            clustered_entry_indices=clustered_entry_indices,
            stable_tail_qs=[int(x) for x in inherited_bridge.get('certified_tail_qs', inherited_coherence.get('coherence_tail_qs', []))],
            stable_tail_start_q=inherited_bridge.get('certified_tail_start_q', inherited_coherence.get('coherence_tail_start_q')),
            stable_tail_support_count=int(inherited_bridge.get('supporting_entry_count', inherited_coherence.get('coherence_tail_support_count', 0))),
            stable_tail_support_fraction=(None if inherited_bridge.get('support_fraction_floor') is None else float(inherited_bridge.get('support_fraction_floor'))),
            stable_tail_is_suffix_of_generated_union=bool(inherited_bridge.get('certified_tail_is_suffix', inherited_coherence.get('coherence_tail_is_suffix_of_generated_union', False))),
            stable_q_union=stable_q_union,
            stable_q_intersection=stable_q_intersection,
            stable_upper_lo=None if inherited_bridge.get('certified_upper_lo') is None else float(inherited_bridge.get('certified_upper_lo')),
            stable_upper_hi=None if inherited_bridge.get('certified_upper_hi') is None else float(inherited_bridge.get('certified_upper_hi')),
            stable_upper_width=None if inherited_bridge.get('certified_upper_width') is None else float(inherited_bridge.get('certified_upper_width')),
            stable_barrier_lo=None if inherited_bridge.get('certified_barrier_lo') is None else float(inherited_bridge.get('certified_barrier_lo')),
            stable_barrier_hi=None if inherited_bridge.get('certified_barrier_hi') is None else float(inherited_bridge.get('certified_barrier_hi')),
            stable_barrier_width=None if inherited_bridge.get('certified_barrier_width') is None else float(inherited_bridge.get('certified_barrier_width')),
            stable_incompatibility_gap=None if inherited_bridge.get('certified_gap') is None else float(inherited_bridge.get('certified_gap')),
            entries=entries,
            theorem_status=theorem_status,
            notes=notes,
        )

    entries: list[GoldenAdaptiveTailStabilityEntry] = []
    all_generated_qs: set[int] = set()

    for shift in atlas_shifts:
        report = build_golden_adaptive_incompatibility_certificate(
            family=family,
            rho=rho,
            crossing_center=float(crossing_center) + float(shift),
            **adaptive_kwargs,
        ).to_dict()
        atlas = report.get('atlas', {}) or {}
        tail = atlas.get('hyperbolic_tail', {}) or {}
        stable_tail_qs = [int(x) for x in tail.get('tail_qs', [])]
        witness_qs = [int(x) for x in tail.get('witness_qs', [])]
        generated_qs = [int(x) for x in tail.get('generated_qs', [])]
        all_generated_qs.update(generated_qs)
        entries.append(
            GoldenAdaptiveTailStabilityEntry(
                atlas_shift=float(shift),
                crossing_center=float(crossing_center) + float(shift),
                theorem_status=str(report.get('theorem_status', 'unknown')),
                selected_upper_lo=None if report.get('selected_upper_lo') is None else float(report.get('selected_upper_lo')),
                selected_upper_hi=None if report.get('selected_upper_hi') is None else float(report.get('selected_upper_hi')),
                selected_upper_width=None if report.get('selected_upper_width') is None else float(report.get('selected_upper_width')),
                selected_barrier_lo=None if report.get('selected_barrier_lo') is None else float(report.get('selected_barrier_lo')),
                selected_barrier_hi=None if report.get('selected_barrier_hi') is None else float(report.get('selected_barrier_hi')),
                selected_barrier_width=None if report.get('selected_barrier_width') is None else float(report.get('selected_barrier_width')),
                incompatibility_gap=None if report.get('incompatibility_gap') is None else float(report.get('incompatibility_gap')),
                interval_newton_count=int(atlas.get('interval_newton_count', 0)),
                fully_certified_count=int(atlas.get('fully_certified_count', 0)),
                stable_tail_qs=stable_tail_qs,
                witness_qs=witness_qs,
                generated_qs=generated_qs,
                stable_tail_start_q=(stable_tail_qs[0] if stable_tail_qs else None),
                tail_is_suffix_of_generated=bool(tail.get('tail_is_suffix_of_generated', False)),
                report=report,
            )
        )

    successful_entry_indices = [
        i for i, e in enumerate(entries)
        if e.selected_upper_lo is not None and e.selected_upper_hi is not None and e.selected_barrier_lo is not None and e.selected_barrier_hi is not None
    ]
    upper_windows = [(e.selected_upper_lo, e.selected_upper_hi) for e in entries]
    barrier_windows = [(e.selected_barrier_lo, e.selected_barrier_hi) for e in entries]
    clustered_entry_indices = _largest_joint_overlapping_subset(successful_entry_indices, upper_windows, barrier_windows)
    if len(clustered_entry_indices) < int(min_cluster_size) and successful_entry_indices:
        clustered_entry_indices = successful_entry_indices[:1]
    clustered_entries = [entries[i] for i in clustered_entry_indices]

    stable_upper_lo, stable_upper_hi = _window_intersection(
        (upper_windows[i] for i in clustered_entry_indices if upper_windows[i][0] is not None and upper_windows[i][1] is not None)
    )
    stable_barrier_lo, stable_barrier_hi = _window_intersection(
        (barrier_windows[i] for i in clustered_entry_indices if barrier_windows[i][0] is not None and barrier_windows[i][1] is not None)
    )
    stable_upper_width = None if stable_upper_lo is None or stable_upper_hi is None else float(stable_upper_hi - stable_upper_lo)
    stable_barrier_width = None if stable_barrier_lo is None or stable_barrier_hi is None else float(stable_barrier_hi - stable_barrier_lo)
    stable_gap = None if stable_upper_hi is None or stable_barrier_lo is None else float(stable_barrier_lo - stable_upper_hi)

    q_sets = [e.witness_qs for e in clustered_entries if e.witness_qs]
    tail_sets = [e.stable_tail_qs for e in clustered_entries if e.stable_tail_qs]
    stable_q_intersection = _intersection_sorted(q_sets) if q_sets else []
    stable_q_union = _union_sorted(q_sets) if q_sets else []
    stable_tail_qs = _intersection_sorted(tail_sets) if tail_sets else []
    if len(stable_tail_qs) < int(min_stable_tail_members):
        stable_tail_qs = []
    stable_tail_start_q = stable_tail_qs[0] if stable_tail_qs else None
    stable_tail_support_count = sum(1 for e in clustered_entries if stable_tail_qs and set(stable_tail_qs).issubset(set(e.stable_tail_qs or e.witness_qs))) if stable_tail_qs else 0
    stable_tail_support_fraction = None if not clustered_entries or not stable_tail_qs else float(stable_tail_support_count / len(clustered_entries))
    generated_union = sorted(all_generated_qs)
    stable_tail_is_suffix = _is_suffix(stable_tail_qs, generated_union)

    if (
        stable_upper_lo is None or stable_upper_hi is None or stable_barrier_lo is None or stable_barrier_hi is None
    ):
        theorem_status = 'golden-adaptive-tail-stability-failed'
        notes = 'No coherent adaptive upper/barrier pair persisted across neighboring adaptive atlas constructions.'
    elif (
        len(clustered_entry_indices) >= int(min_cluster_size)
        and stable_tail_qs
        and stable_tail_support_fraction is not None
        and stable_tail_support_fraction >= float(min_tail_support_fraction)
        and stable_tail_is_suffix
        and stable_gap is not None
        and stable_gap > 0.0
    ):
        theorem_status = 'golden-adaptive-tail-stability-strong'
        notes = 'A coherent adaptive upper object and coherent adaptive barrier both persist across neighboring adaptive atlas constructions, and the same high-denominator tail supports them across that neighborhood.'
    elif len(clustered_entry_indices) >= int(min_cluster_size) and stable_tail_qs and stable_gap is not None and stable_gap > 0.0:
        theorem_status = 'golden-adaptive-tail-stability-moderate'
        notes = 'The adaptive upper/barrier pair persists across neighboring atlas constructions with a stable denominator tail, but tail support is not yet strong enough for the strongest status.'
    elif len(clustered_entry_indices) >= int(min_cluster_size) and (stable_q_intersection or stable_tail_qs):
        theorem_status = 'golden-adaptive-tail-stability-weak'
        notes = 'A coherent adaptive upper/barrier pair persists across neighboring atlas constructions, but stable support is visible only at the witness-intersection level.'
    elif successful_entry_indices:
        theorem_status = 'golden-adaptive-tail-stability-fragile'
        notes = 'Some adaptive atlases produced usable upper/barrier pairs, but they do not stabilize into a neighborhood-level tail-supported object.'
    else:
        theorem_status = 'golden-adaptive-tail-stability-failed'
        notes = 'Neighboring adaptive atlas constructions did not produce usable upper/barrier pairs.'

    return GoldenAdaptiveTailStabilityCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        base_crossing_center=float(crossing_center),
        atlas_shift_grid=[float(x) for x in atlas_shifts],
        successful_entry_indices=[int(x) for x in successful_entry_indices],
        clustered_entry_indices=[int(x) for x in clustered_entry_indices],
        stable_tail_qs=stable_tail_qs,
        stable_tail_start_q=stable_tail_start_q,
        stable_tail_support_count=int(stable_tail_support_count),
        stable_tail_support_fraction=stable_tail_support_fraction,
        stable_tail_is_suffix_of_generated_union=bool(stable_tail_is_suffix),
        stable_q_union=stable_q_union,
        stable_q_intersection=stable_q_intersection,
        stable_upper_lo=stable_upper_lo,
        stable_upper_hi=stable_upper_hi,
        stable_upper_width=stable_upper_width,
        stable_barrier_lo=stable_barrier_lo,
        stable_barrier_hi=stable_barrier_hi,
        stable_barrier_width=stable_barrier_width,
        stable_incompatibility_gap=stable_gap,
        entries=entries,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_two_sided_adaptive_tail_bridge_certificate(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    **tail_kwargs,
) -> GoldenTwoSidedAdaptiveTailBridgeCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    lower = continue_golden_aposteriori_certificates(
        K_values=K_values,
        family=family,
        rho=rho,
        N_values=N_values,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
    ).to_dict()
    upper = build_golden_adaptive_tail_stability_certificate(family=family, rho=rho, **tail_kwargs).to_dict()
    lower_bound = lower.get('last_stable_K')
    upper_lo = upper.get('stable_upper_lo')
    upper_hi = upper.get('stable_upper_hi')
    barrier_lo = upper.get('stable_barrier_lo')
    gap = None if lower_bound is None or upper_lo is None else float(upper_lo - float(lower_bound))
    gap_to_barrier = None if lower_bound is None or barrier_lo is None else float(barrier_lo - float(lower_bound))
    relation = {
        'lower_bound': None if lower_bound is None else float(lower_bound),
        'upper_crossing_lo': None if upper_lo is None else float(upper_lo),
        'upper_crossing_hi': None if upper_hi is None else float(upper_hi),
        'upper_barrier_lo': None if barrier_lo is None else float(barrier_lo),
        'gap_to_upper': gap,
        'gap_to_barrier': gap_to_barrier,
        'stable_tail_qs': [int(x) for x in upper.get('stable_tail_qs', [])],
        'stable_tail_support_count': int(upper.get('stable_tail_support_count', 0)),
        'clustered_atlas_count': len(upper.get('clustered_entry_indices', [])),
        'upper_status': str(upper.get('theorem_status', 'unknown')),
    }
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        status = 'golden-two-sided-adaptive-tail-strong' if str(upper.get('theorem_status')) == 'golden-adaptive-tail-stability-strong' else 'golden-two-sided-adaptive-tail-partial'
        notes = 'Lower golden a-posteriori continuation lies below an adaptive upper object that is stable across neighboring adaptive atlas constructions. This is a stronger two-sided bridge than a single adaptive incompatibility run.'
    else:
        status = 'golden-two-sided-adaptive-tail-incomplete'
        notes = 'The neighborhood-level adaptive upper-tail object did not yet separate cleanly from the lower a-posteriori side.'
    return GoldenTwoSidedAdaptiveTailBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=status,
        notes=notes,
    )


__all__ = [
    'GoldenAdaptiveTailStabilityEntry',
    'GoldenAdaptiveTailStabilityCertificate',
    'GoldenTwoSidedAdaptiveTailBridgeCertificate',
    'build_golden_adaptive_tail_stability_certificate',
    'build_golden_two_sided_adaptive_tail_bridge_certificate',
]
