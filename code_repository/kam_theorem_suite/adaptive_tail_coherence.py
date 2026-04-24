from __future__ import annotations

"""Support-profile adaptive tail coherence certificates.

This stage strengthens the neighborhood-level adaptive upper package by
requiring the *same* upper/barrier object and the supporting denominator tail to
cohere simultaneously.

Stage 32 asked whether a neighborhood of adaptive atlases shared:
- an overlapping upper window,
- an overlapping barrier window, and
- an exact tail intersection.

That exact tail intersection is honest but often too brittle.  The next theorem-
facing move is therefore to work with a denominator-wise support profile:

- track, for each denominator q on the generated union, how many neighboring
  adaptive atlases support q as a witness;
- choose a suffix tail on which support stays uniformly high; and
- then re-intersect the upper/barrier windows only across the entries that
  actually support that tail.

This is still not a finished irrational obstruction theorem.  It is a sharper
bridge object that makes the upper object and its supporting tail cohere at the
same time.
"""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import asdict, dataclass
from inspect import signature
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


def _largest_joint_overlapping_subset(
    indices: Sequence[int],
    upper_windows: Sequence[tuple[float | None, float | None]],
    barrier_windows: Sequence[tuple[float | None, float | None]],
) -> list[int]:
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


@dataclass
class AdaptiveTailCoherenceProfileRow:
    q: int
    witness_support_count: int
    witness_support_fraction: float
    tail_support_count: int
    tail_support_fraction: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenAdaptiveTailCoherenceEntry:
    atlas_shift: float
    crossing_center: float
    theorem_status: str
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_barrier_lo: float | None
    selected_barrier_hi: float | None
    incompatibility_gap: float | None
    witness_qs: list[int]
    exact_tail_qs: list[int]
    generated_qs: list[int]
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenAdaptiveTailCoherenceCertificate:
    rho: float
    family_label: str
    base_crossing_center: float
    atlas_shift_grid: list[float]
    successful_entry_indices: list[int]
    clustered_entry_indices: list[int]
    supporting_entry_indices: list[int]
    coherence_tail_qs: list[int]
    coherence_tail_start_q: int | None
    coherence_tail_support_count: int
    coherence_tail_support_fraction: float | None
    coherence_tail_entry_coverage_floor: float | None
    coherence_tail_is_suffix_of_generated_union: bool
    stable_upper_lo: float | None
    stable_upper_hi: float | None
    stable_upper_width: float | None
    stable_barrier_lo: float | None
    stable_barrier_hi: float | None
    stable_barrier_width: float | None
    stable_incompatibility_gap: float | None
    support_profile: list[AdaptiveTailCoherenceProfileRow]
    entries: list[GoldenAdaptiveTailCoherenceEntry]
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
            'supporting_entry_indices': [int(x) for x in self.supporting_entry_indices],
            'coherence_tail_qs': [int(x) for x in self.coherence_tail_qs],
            'coherence_tail_start_q': self.coherence_tail_start_q,
            'coherence_tail_support_count': int(self.coherence_tail_support_count),
            'coherence_tail_support_fraction': self.coherence_tail_support_fraction,
            'coherence_tail_entry_coverage_floor': self.coherence_tail_entry_coverage_floor,
            'coherence_tail_is_suffix_of_generated_union': bool(self.coherence_tail_is_suffix_of_generated_union),
            'stable_upper_lo': self.stable_upper_lo,
            'stable_upper_hi': self.stable_upper_hi,
            'stable_upper_width': self.stable_upper_width,
            'stable_barrier_lo': self.stable_barrier_lo,
            'stable_barrier_hi': self.stable_barrier_hi,
            'stable_barrier_width': self.stable_barrier_width,
            'stable_incompatibility_gap': self.stable_incompatibility_gap,
            'support_profile': [row.to_dict() for row in self.support_profile],
            'entries': [e.to_dict() for e in self.entries],
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


@dataclass
class GoldenTwoSidedAdaptiveTailCoherenceBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _choose_support_profile_tail(
    generated_union: Sequence[int],
    witness_sets: Sequence[set[int]],
    tail_sets: Sequence[set[int]],
    usable_entry_indices: Sequence[int],
    *,
    min_tail_members: int,
    min_q_support_fraction: float,
    min_entry_tail_coverage: float,
    min_supporting_entries: int,
    upper_windows: Sequence[tuple[float | None, float | None]],
    barrier_windows: Sequence[tuple[float | None, float | None]],
) -> tuple[list[int], list[int], list[AdaptiveTailCoherenceProfileRow], tuple[float | None, float | None], tuple[float | None, float | None]]:
    usable = [int(i) for i in usable_entry_indices]
    generated = sorted({int(q) for q in generated_union if int(q) > 0})
    if not usable or not generated:
        return [], [], [], (None, None), (None, None)

    profile: list[AdaptiveTailCoherenceProfileRow] = []
    denom_to_witness_support: dict[int, list[int]] = {}
    denom_to_tail_support: dict[int, list[int]] = {}
    for q in generated:
        w_idx = [i for i in usable if q in witness_sets[i]]
        t_idx = [i for i in usable if q in tail_sets[i]]
        denom_to_witness_support[q] = w_idx
        denom_to_tail_support[q] = t_idx
        profile.append(
            AdaptiveTailCoherenceProfileRow(
                q=int(q),
                witness_support_count=len(w_idx),
                witness_support_fraction=float(len(w_idx) / len(usable)),
                tail_support_count=len(t_idx),
                tail_support_fraction=float(len(t_idx) / len(usable)),
            )
        )

    best_tail: list[int] = []
    best_supporting_entries: list[int] = []
    best_upper = (None, None)
    best_barrier = (None, None)
    best_score: tuple[float, ...] | None = None

    for start in range(len(generated)):
        support_run_ok = True
        for end in range(start, len(generated)):
            q = generated[end]
            if (len(denom_to_witness_support[q]) / len(usable)) < float(min_q_support_fraction):
                support_run_ok = False
                break
            tail = generated[start:end + 1]
            if len(tail) < int(min_tail_members):
                continue
            supporting_entries: list[int] = []
            coverage_values: list[float] = []
            for i in usable:
                supported = sum(1 for qq in tail if qq in witness_sets[i])
                coverage = float(supported / len(tail))
                if coverage >= float(min_entry_tail_coverage):
                    supporting_entries.append(i)
                    coverage_values.append(coverage)
            if len(supporting_entries) < int(min_supporting_entries):
                continue
            upper = _window_intersection(
                (upper_windows[i] for i in supporting_entries if upper_windows[i][0] is not None and upper_windows[i][1] is not None)
            )
            barrier = _window_intersection(
                (barrier_windows[i] for i in supporting_entries if barrier_windows[i][0] is not None and barrier_windows[i][1] is not None)
            )
            if upper[0] is None or barrier[0] is None:
                continue
            gap = float(barrier[0] - upper[1]) if upper[1] is not None and barrier[0] is not None else float('-inf')
            avg_support = sum(len(denom_to_witness_support[qq]) / len(usable) for qq in tail) / len(tail)
            coverage_floor = min(coverage_values) if coverage_values else 0.0
            is_suffix = 1.0 if end == len(generated) - 1 else 0.0
            score = (
                1.0 if gap > 0.0 else 0.0,
                is_suffix,
                float(len(tail)),
                float(len(supporting_entries)),
                float(avg_support),
                float(coverage_floor),
                float(generated[start]),
            )
            if best_score is None or score > best_score:
                best_score = score
                best_tail = [int(qq) for qq in tail]
                best_supporting_entries = [int(i) for i in supporting_entries]
                best_upper = upper
                best_barrier = barrier

    return best_tail, best_supporting_entries, profile, best_upper, best_barrier





def _window_hull(windows: Iterable[tuple[float, float]]) -> tuple[float | None, float | None]:
    items = [(float(lo), float(hi)) for lo, hi in windows]
    if not items:
        return None, None
    return float(min(lo for lo, _ in items)), float(max(hi for _, hi in items))


def _tail_signature_for_entry(entry: "GoldenAdaptiveTailCoherenceEntry", *, min_tail_members: int) -> tuple[int, ...]:
    exact = tuple(sorted({int(q) for q in entry.exact_tail_qs if int(q) > 0}))
    if len(exact) >= int(min_tail_members):
        return exact
    witness = tuple(sorted({int(q) for q in entry.witness_qs if int(q) > 0}))
    if len(witness) >= int(min_tail_members):
        return witness
    generated = tuple(sorted({int(q) for q in entry.generated_qs if int(q) > 0}))
    if len(generated) >= int(min_tail_members):
        return generated[-int(min_tail_members):]
    return ()


def _support_set_for_entry(entry: "GoldenAdaptiveTailCoherenceEntry") -> set[int]:
    exact = {int(q) for q in entry.exact_tail_qs if int(q) > 0}
    if exact:
        return exact
    witness = {int(q) for q in entry.witness_qs if int(q) > 0}
    if witness:
        return witness
    return {int(q) for q in entry.generated_qs if int(q) > 0}


def _build_signature_support_candidates(
    entry_objs: Sequence["GoldenAdaptiveTailCoherenceEntry"],
    successful_entry_indices: Sequence[int],
    *,
    min_tail_members: int,
    min_cluster_size: int,
) -> list[dict[str, Any]]:
    successful = [int(i) for i in successful_entry_indices if 0 <= int(i) < len(entry_objs)]
    if not successful:
        return []
    generated_union = sorted({int(q) for i in successful for q in entry_objs[i].generated_qs if int(q) > 0})
    groups: dict[tuple[int, ...], list[int]] = {}
    for i in successful:
        sig = _tail_signature_for_entry(entry_objs[i], min_tail_members=min_tail_members)
        if len(sig) >= int(min_tail_members):
            groups.setdefault(sig, []).append(i)
    candidates: list[dict[str, Any]] = []
    for sig, indices in groups.items():
        indices = sorted(set(indices))
        if len(indices) < max(1, int(min_cluster_size)):
            continue
        uppers = [(float(entry_objs[i].selected_upper_lo), float(entry_objs[i].selected_upper_hi)) for i in indices if entry_objs[i].selected_upper_lo is not None and entry_objs[i].selected_upper_hi is not None]
        barriers = [(float(entry_objs[i].selected_barrier_lo), float(entry_objs[i].selected_barrier_hi)) for i in indices if entry_objs[i].selected_barrier_lo is not None and entry_objs[i].selected_barrier_hi is not None]
        if len(uppers) < max(1, int(min_cluster_size)) or not barriers:
            continue
        upper_hull = _window_hull(uppers)
        rep_idx = min(indices, key=lambda j: float(entry_objs[j].selected_barrier_lo if entry_objs[j].selected_barrier_lo is not None else 1e99))
        blo = entry_objs[rep_idx].selected_barrier_lo
        bhi = entry_objs[rep_idx].selected_barrier_hi
        if upper_hull[0] is None or upper_hull[1] is None or blo is None or bhi is None:
            continue
        tail = [int(q) for q in sig]
        support_fraction = float(len(indices) / max(1, len(successful)))
        coverages = [float(sum(1 for q in tail if q in _support_set_for_entry(entry_objs[i])) / len(tail)) for i in indices]
        coverage_floor = min(coverages) if coverages else None
        gap = float(float(blo) - float(upper_hull[1]))
        upper_width = float(float(upper_hull[1]) - float(upper_hull[0]))
        barrier_width = float(float(bhi) - float(blo))
        ratio = float(gap / max(1e-12, upper_width, barrier_width))
        suffix = tail == [q for q in generated_union if q >= tail[0]]
        score = (1.0 if gap > 0 else 0.0, support_fraction, float(coverage_floor or 0.0), 1.0 if suffix else 0.0, float(len(tail)), float(len(indices)), ratio, -float(tail[0]))
        candidates.append({'tail_qs': tail, 'supporting_entry_indices': indices, 'support_fraction': support_fraction, 'entry_coverage_floor': coverage_floor, 'stable_upper': (float(upper_hull[0]), float(upper_hull[1])), 'stable_barrier': (float(blo), float(bhi)), 'stable_gap': gap, 'tail_is_suffix': bool(suffix), 'score': score})
    candidates.sort(key=lambda c: c['score'], reverse=True)
    return candidates



def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _to_int_list(values: Any) -> list[int]:
    if values is None:
        return []
    out: list[int] = []
    for value in values:
        try:
            out.append(int(value))
        except (TypeError, ValueError):
            continue
    return out


def _first_nonempty_int_list(*values: Any) -> list[int]:
    for value in values:
        ints = _to_int_list(value)
        if ints:
            return ints
    return []


def _normalize_golden_adaptive_tail_coherence_entry(
    entry: GoldenAdaptiveTailCoherenceEntry | dict[str, Any]
) -> GoldenAdaptiveTailCoherenceEntry:
    if isinstance(entry, GoldenAdaptiveTailCoherenceEntry):
        return entry

    raw = dict(entry)
    report = dict(raw.get('report') or {})
    atlas = dict(report.get('atlas') or {})
    hyper = dict(report.get('hyperbolic_tail') or atlas.get('hyperbolic_tail') or {})
    tail_transport = dict(
        raw.get('tail_transport_certificate')
        or report.get('tail_transport_certificate')
        or {}
    )
    anchor_tail = dict(tail_transport.get('anchor_tail_summary') or {})

    if tail_transport and 'tail_transport_certificate' not in report:
        report['tail_transport_certificate'] = tail_transport

    witness_qs = _first_nonempty_int_list(
        raw.get('witness_qs'),
        hyper.get('witness_qs'),
        anchor_tail.get('witness_qs'),
        tail_transport.get('anchor_qs'),
    )
    exact_tail_qs = _first_nonempty_int_list(
        raw.get('exact_tail_qs'),
        hyper.get('tail_qs'),
        tail_transport.get('tail_qs'),
    )
    generated_qs = _first_nonempty_int_list(
        raw.get('generated_qs'),
        hyper.get('generated_qs'),
        anchor_tail.get('generated_qs'),
        tail_transport.get('anchor_qs'),
        sorted(set(witness_qs) | set(exact_tail_qs)),
    )

    selected_upper_lo = _to_float_or_none(
        _first_present(
            raw.get('selected_upper_lo'),
            report.get('selected_upper_lo'),
            atlas.get('coherent_upper_lo'),
            tail_transport.get('anchor_upper_lo'),
        )
    )
    selected_upper_hi = _to_float_or_none(
        _first_present(
            raw.get('selected_upper_hi'),
            report.get('selected_upper_hi'),
            atlas.get('coherent_upper_hi'),
            tail_transport.get('anchor_upper_hi'),
        )
    )
    selected_barrier_lo = _to_float_or_none(
        _first_present(
            raw.get('selected_barrier_lo'),
            report.get('selected_barrier_lo'),
            atlas.get('coherent_band_lo'),
        )
    )
    selected_barrier_hi = _to_float_or_none(
        _first_present(
            raw.get('selected_barrier_hi'),
            report.get('selected_barrier_hi'),
            atlas.get('coherent_band_hi'),
        )
    )
    incompatibility_gap = _to_float_or_none(
        _first_present(
            raw.get('incompatibility_gap'),
            report.get('incompatibility_gap'),
            hyper.get('incompatibility_gap'),
            atlas.get('incompatibility_gap'),
            anchor_tail.get('incompatibility_gap'),
        )
    )

    atlas_shift = _to_float_or_none(raw.get('atlas_shift'))
    if atlas_shift is None:
        atlas_shift = 0.0
    crossing_center = _to_float_or_none(raw.get('crossing_center'))
    if crossing_center is None:
        crossing_center = 0.0

    theorem_status = str(
        _first_present(
            raw.get('theorem_status'),
            report.get('theorem_status'),
            hyper.get('theorem_status'),
            tail_transport.get('theorem_status'),
            'unknown',
        )
    )

    return GoldenAdaptiveTailCoherenceEntry(
        atlas_shift=float(atlas_shift),
        crossing_center=float(crossing_center),
        theorem_status=theorem_status,
        selected_upper_lo=selected_upper_lo,
        selected_upper_hi=selected_upper_hi,
        selected_barrier_lo=selected_barrier_lo,
        selected_barrier_hi=selected_barrier_hi,
        incompatibility_gap=incompatibility_gap,
        witness_qs=witness_qs,
        exact_tail_qs=exact_tail_qs,
        generated_qs=generated_qs,
        report=report,
    )

def _filter_kwargs(fn, kwargs: dict[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    return {k: v for k, v in kwargs.items() if k in params}

def build_golden_adaptive_tail_coherence_entry(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    shift: float = 0.0,
    **adaptive_kwargs,
) -> GoldenAdaptiveTailCoherenceEntry:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    report = build_golden_adaptive_incompatibility_certificate(
        family=family,
        rho=rho,
        crossing_center=float(crossing_center) + float(shift),
        **_filter_kwargs(build_golden_adaptive_incompatibility_certificate, adaptive_kwargs),
    ).to_dict()
    atlas = report.get('atlas', {}) or {}
    tail = atlas.get('hyperbolic_tail', {}) or {}
    witness_qs = [int(x) for x in tail.get('witness_qs', [])]
    exact_tail_qs = [int(x) for x in tail.get('tail_qs', [])]
    generated_qs = [int(x) for x in tail.get('generated_qs', [])]
    return GoldenAdaptiveTailCoherenceEntry(
        atlas_shift=float(shift),
        crossing_center=float(crossing_center) + float(shift),
        theorem_status=str(report.get('theorem_status', 'unknown')),
        selected_upper_lo=None if report.get('selected_upper_lo') is None else float(report.get('selected_upper_lo')),
        selected_upper_hi=None if report.get('selected_upper_hi') is None else float(report.get('selected_upper_hi')),
        selected_barrier_lo=None if report.get('selected_barrier_lo') is None else float(report.get('selected_barrier_lo')),
        selected_barrier_hi=None if report.get('selected_barrier_hi') is None else float(report.get('selected_barrier_hi')),
        incompatibility_gap=None if report.get('incompatibility_gap') is None else float(report.get('incompatibility_gap')),
        witness_qs=witness_qs,
        exact_tail_qs=exact_tail_qs,
        generated_qs=generated_qs,
        report=report,
    )


def _build_golden_adaptive_tail_coherence_entry_worker(payload: dict[str, Any]) -> dict[str, Any]:
    family = payload.get('family')
    kwargs = dict(payload.get('kwargs', {}))
    entry = build_golden_adaptive_tail_coherence_entry(family=family, **kwargs)
    return entry.to_dict()


def build_golden_adaptive_tail_coherence_certificate_from_entries(
    entries: Sequence[GoldenAdaptiveTailCoherenceEntry | dict[str, Any]],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_shifts: Sequence[float] = (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4),
    min_cluster_size: int = 2,
    min_tail_members: int = 2,
    min_q_support_fraction: float = 0.6,
    min_entry_tail_coverage: float = 0.75,
    min_tail_support_fraction: float = 0.75,
) -> GoldenAdaptiveTailCoherenceCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    entry_objs: list[GoldenAdaptiveTailCoherenceEntry] = []
    all_generated_qs: set[int] = set()
    for entry in entries:
        e = _normalize_golden_adaptive_tail_coherence_entry(entry)
        entry_objs.append(e)
        all_generated_qs.update(int(q) for q in e.generated_qs)
    successful_entry_indices = [i for i, e in enumerate(entry_objs) if e.selected_upper_lo is not None and e.selected_upper_hi is not None and e.selected_barrier_lo is not None and e.selected_barrier_hi is not None]
    upper_windows = [(e.selected_upper_lo, e.selected_upper_hi) for e in entry_objs]
    barrier_windows = [(e.selected_barrier_lo, e.selected_barrier_hi) for e in entry_objs]
    generated_union = sorted(all_generated_qs)
    support_profile: list[AdaptiveTailCoherenceProfileRow] = []
    if successful_entry_indices:
        support_sets = [_support_set_for_entry(entry_objs[i]) for i in successful_entry_indices]
        exact_tail_sets = [{int(q) for q in entry_objs[i].exact_tail_qs if int(q) > 0} for i in successful_entry_indices]
        denom = max(1, len(successful_entry_indices))
        for q in generated_union:
            witness_support_count = sum(1 for sset in support_sets if int(q) in sset)
            tail_support_count = sum(1 for sset in exact_tail_sets if int(q) in sset)
            support_profile.append(AdaptiveTailCoherenceProfileRow(q=int(q), witness_support_count=int(witness_support_count), witness_support_fraction=float(witness_support_count/denom), tail_support_count=int(tail_support_count), tail_support_fraction=float(tail_support_count/denom)))
    signature_candidates = _build_signature_support_candidates(entry_objs, successful_entry_indices, min_tail_members=min_tail_members, min_cluster_size=min_cluster_size)
    witness_sets = [set(_support_set_for_entry(e)) for e in entry_objs]
    tail_sets = [set(int(q) for q in e.exact_tail_qs if int(q) > 0) for e in entry_objs]
    legacy_supporting=[]; legacy_tail_qs=[]; legacy_upper=(None,None); legacy_barrier=(None,None)
    if successful_entry_indices:
        legacy_tail_qs, legacy_supporting, legacy_profile, legacy_upper, legacy_barrier = _choose_support_profile_tail(generated_union, witness_sets, tail_sets, successful_entry_indices, min_tail_members=min_tail_members, min_q_support_fraction=min_q_support_fraction, min_entry_tail_coverage=min_entry_tail_coverage, min_supporting_entries=max(1, min_cluster_size), upper_windows=upper_windows, barrier_windows=barrier_windows)
        if legacy_profile: support_profile = legacy_profile
    best_candidate = signature_candidates[0] if signature_candidates else None
    clustered_entry_indices = list(successful_entry_indices)
    supporting_entry_indices=[]; coherence_tail_qs=[]; stable_upper=(None,None); stable_barrier=(None,None); stable_gap=None
    coherence_tail_support_fraction=None; coherence_tail_entry_coverage_floor=None; coherence_tail_support_count=0; coherence_tail_is_suffix=False
    if best_candidate is not None:
        clustered_entry_indices=[int(i) for i in best_candidate['supporting_entry_indices']]
        supporting_entry_indices=[int(i) for i in best_candidate['supporting_entry_indices']]
        coherence_tail_qs=[int(q) for q in best_candidate['tail_qs']]
        stable_upper=best_candidate['stable_upper']; stable_barrier=best_candidate['stable_barrier']; stable_gap=float(best_candidate['stable_gap'])
        coherence_tail_support_fraction=float(best_candidate['support_fraction'])
        coherence_tail_entry_coverage_floor=None if best_candidate['entry_coverage_floor'] is None else float(best_candidate['entry_coverage_floor'])
        coherence_tail_support_count=len(supporting_entry_indices); coherence_tail_is_suffix=bool(best_candidate['tail_is_suffix'])
    elif legacy_supporting:
        clustered_entry_indices=list(legacy_supporting); supporting_entry_indices=list(legacy_supporting); coherence_tail_qs=[int(q) for q in legacy_tail_qs]
        stable_upper=legacy_upper; stable_barrier=legacy_barrier; stable_gap=None if stable_upper[1] is None or stable_barrier[0] is None else float(stable_barrier[0]-stable_upper[1])
        coherence_tail_is_suffix=bool(coherence_tail_qs) and coherence_tail_qs == [q for q in generated_union if q >= coherence_tail_qs[0]]
        coherence_tail_support_count=len(supporting_entry_indices)
        coherence_tail_support_fraction=float(len(supporting_entry_indices)/max(1,len(successful_entry_indices)))
        if coherence_tail_qs:
            coverages=[]
            for i in supporting_entry_indices:
                support_set=_support_set_for_entry(entry_objs[i])
                coverages.append(float(sum(1 for q in coherence_tail_qs if q in support_set)/len(coherence_tail_qs)))
            coherence_tail_entry_coverage_floor=min(coverages) if coverages else None
    elif successful_entry_indices:
        clustered_entry_indices=list(successful_entry_indices); supporting_entry_indices=list(successful_entry_indices)
        upper_hull=_window_hull((upper_windows[i] for i in successful_entry_indices if upper_windows[i][0] is not None and upper_windows[i][1] is not None))
        rep_idx=min(successful_entry_indices, key=lambda i: float(entry_objs[i].selected_barrier_lo if entry_objs[i].selected_barrier_lo is not None else 1e99))
        stable_upper=upper_hull
        stable_barrier=(float(entry_objs[rep_idx].selected_barrier_lo) if entry_objs[rep_idx].selected_barrier_lo is not None else None, float(entry_objs[rep_idx].selected_barrier_hi) if entry_objs[rep_idx].selected_barrier_hi is not None else None)
        stable_gap=None if stable_upper[1] is None or stable_barrier[0] is None else float(stable_barrier[0]-stable_upper[1])
    stable_upper_lo, stable_upper_hi = stable_upper; stable_barrier_lo, stable_barrier_hi = stable_barrier
    stable_upper_width=None if stable_upper_lo is None or stable_upper_hi is None else float(stable_upper_hi-stable_upper_lo)
    stable_barrier_width=None if stable_barrier_lo is None or stable_barrier_hi is None else float(stable_barrier_hi-stable_barrier_lo)
    coherence_tail_start_q=coherence_tail_qs[0] if coherence_tail_qs else None
    if stable_upper_lo is None or stable_barrier_lo is None:
        theorem_status='golden-adaptive-tail-coherence-failed'; notes='No coherent adaptive upper/barrier object survived the tail-coherence refinement.'
    elif len(supporting_entry_indices) >= max(1,int(min_cluster_size)) and coherence_tail_qs and coherence_tail_support_fraction is not None and coherence_tail_support_fraction >= float(min_tail_support_fraction) and coherence_tail_entry_coverage_floor is not None and coherence_tail_entry_coverage_floor >= float(min_entry_tail_coverage) and stable_gap is not None and stable_gap > 0.0:
        theorem_status='golden-adaptive-tail-coherence-strong'; notes='A tail-signature support core survives across neighboring adaptive atlases: the same exact high-denominator tail is supported on a neighborhood subcluster, the upper localization envelopes remain compatible, and the representative barrier stays strictly above the whole supported upper envelope.'
    elif coherence_tail_qs and stable_gap is not None and stable_gap > 0.0:
        theorem_status='golden-adaptive-tail-coherence-moderate'; notes='A tail-signature support core with positive envelope gap has been identified, but the neighborhood support fractions are not yet at the strongest threshold.'
    elif coherence_tail_qs:
        theorem_status='golden-adaptive-tail-coherence-weak'; notes='A common exact tail signature is present, but the supported upper/barrier geometry is not yet sharp enough for a strong coherence package.'
    elif clustered_entry_indices:
        theorem_status='golden-adaptive-tail-coherence-fragile'; notes='Neighboring adaptive atlases still share usable upper/barrier data, but no supported exact-tail signature has stabilized.'
    else:
        theorem_status='golden-adaptive-tail-coherence-failed'; notes='No usable adaptive upper/barrier neighborhood survived the coherence refinement.'
    return GoldenAdaptiveTailCoherenceCertificate(rho=float(rho), family_label=_family_label(family), base_crossing_center=float(crossing_center), atlas_shift_grid=[float(x) for x in atlas_shifts], successful_entry_indices=[int(x) for x in successful_entry_indices], clustered_entry_indices=[int(x) for x in clustered_entry_indices], supporting_entry_indices=[int(x) for x in supporting_entry_indices], coherence_tail_qs=[int(x) for x in coherence_tail_qs], coherence_tail_start_q=coherence_tail_start_q, coherence_tail_support_count=int(coherence_tail_support_count), coherence_tail_support_fraction=coherence_tail_support_fraction, coherence_tail_entry_coverage_floor=coherence_tail_entry_coverage_floor, coherence_tail_is_suffix_of_generated_union=bool(coherence_tail_is_suffix), stable_upper_lo=stable_upper_lo, stable_upper_hi=stable_upper_hi, stable_upper_width=stable_upper_width, stable_barrier_lo=stable_barrier_lo, stable_barrier_hi=stable_barrier_hi, stable_barrier_width=stable_barrier_width, stable_incompatibility_gap=stable_gap, support_profile=support_profile, entries=entry_objs, theorem_status=theorem_status, notes=notes)


def build_golden_adaptive_tail_coherence_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_shifts: Sequence[float] = (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4),
    min_cluster_size: int = 2,
    min_tail_members: int = 2,
    min_q_support_fraction: float = 0.6,
    min_entry_tail_coverage: float = 0.75,
    min_tail_support_fraction: float = 0.75,
    n_jobs: int = 1,
    parallelism: str = "serial",
    **adaptive_kwargs,
) -> GoldenAdaptiveTailCoherenceCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    entry_kwargs = dict(rho=rho, crossing_center=crossing_center)
    entry_kwargs.update(adaptive_kwargs)
    entries: list[GoldenAdaptiveTailCoherenceEntry] = []
    if int(n_jobs) > 1 and parallelism in {"thread", "process"} and len(atlas_shifts) > 1:
        executor_cls = ThreadPoolExecutor if parallelism == "thread" else ProcessPoolExecutor
        with executor_cls(max_workers=int(n_jobs)) as ex:
            payloads = [{"family": family, "kwargs": {**entry_kwargs, "shift": float(shift)}} for shift in atlas_shifts]
            for entry_dict in ex.map(_build_golden_adaptive_tail_coherence_entry_worker, payloads):
                entries.append(GoldenAdaptiveTailCoherenceEntry(**entry_dict))
        entries.sort(key=lambda e: e.atlas_shift)
    else:
        for shift in atlas_shifts:
            entries.append(build_golden_adaptive_tail_coherence_entry(family=family, shift=float(shift), **entry_kwargs))
    return build_golden_adaptive_tail_coherence_certificate_from_entries(
        entries,
        family=family,
        rho=rho,
        crossing_center=crossing_center,
        atlas_shifts=atlas_shifts,
        min_cluster_size=min_cluster_size,
        min_tail_members=min_tail_members,
        min_q_support_fraction=min_q_support_fraction,
        min_entry_tail_coverage=min_entry_tail_coverage,
        min_tail_support_fraction=min_tail_support_fraction,
    )


def build_golden_two_sided_adaptive_tail_coherence_bridge_certificate(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    **coherence_kwargs,
) -> GoldenTwoSidedAdaptiveTailCoherenceBridgeCertificate:
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
    upper = build_golden_adaptive_tail_coherence_certificate(family=family, rho=rho, **coherence_kwargs).to_dict()
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
        'coherence_tail_qs': [int(x) for x in upper.get('coherence_tail_qs', [])],
        'supporting_entry_count': len(upper.get('supporting_entry_indices', [])),
        'upper_status': str(upper.get('theorem_status', 'unknown')),
    }
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        status = 'golden-two-sided-adaptive-tail-coherence-strong' if str(upper.get('theorem_status')) == 'golden-adaptive-tail-coherence-strong' else 'golden-two-sided-adaptive-tail-coherence-partial'
        notes = 'Lower golden continuation lies below an adaptive upper object whose supporting tail coheres on the same neighborhood subcluster.'
    else:
        status = 'golden-two-sided-adaptive-tail-coherence-incomplete'
        notes = 'The tail-coherent adaptive upper object did not yet separate cleanly from the lower a-posteriori side.'
    return GoldenTwoSidedAdaptiveTailCoherenceBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=status,
        notes=notes,
    )


__all__ = [
    'AdaptiveTailCoherenceProfileRow',
    'GoldenAdaptiveTailCoherenceEntry',
    'GoldenAdaptiveTailCoherenceCertificate',
    'GoldenTwoSidedAdaptiveTailCoherenceBridgeCertificate',
    'build_golden_adaptive_tail_coherence_entry',
    'build_golden_adaptive_tail_coherence_certificate_from_entries',
    'build_golden_adaptive_tail_coherence_certificate',
    'build_golden_two_sided_adaptive_tail_coherence_bridge_certificate',
]
