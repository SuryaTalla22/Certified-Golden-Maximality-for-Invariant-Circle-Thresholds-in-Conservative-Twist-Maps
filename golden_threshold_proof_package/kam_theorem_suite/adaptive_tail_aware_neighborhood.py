from __future__ import annotations

"""Tail-aware adaptive neighborhood refinement for the upper obstruction front.

Stage 38 improved the adaptive neighborhood by recentering and densifying around
promising entries.  The next strongest move is to make that refinement *tail
aware*: pick refined neighborhoods not just by crossing centers, but by whether
those neighborhoods are likely to preserve a multi-denominator support block.

This module therefore:
- starts from the baseline adaptive tail-coherence object,
- optionally seeds from the stage-38 support-core neighborhood,
- identifies promising denominator blocks/suffixes from the support profile,
- recenters neighborhoods on the entries that support those blocks, and
- reruns strict bridge promotion on the refined neighborhoods.

The output is still not a finished irrational nonexistence theorem.  It is a
sharper upper-side construction that searches directly for neighborhoods in
which strict tail support can survive.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .adaptive_tail_coherence import build_golden_adaptive_tail_coherence_certificate
from .adaptive_support_core_neighborhood import (
    build_golden_adaptive_support_core_neighborhood_certificate,
)
from .golden_aposteriori import golden_inverse
from .incompatibility_strict_bridge import (
    _build_golden_incompatibility_strict_bridge_from_coherence_payload,
)
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


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


def _base_radius(atlas_shifts: Sequence[float]) -> float:
    vals = sorted({abs(float(x)) for x in atlas_shifts})
    vals = [x for x in vals if x > 0.0]
    return float(min(vals)) if vals else 4.0e-4


def _tail_dense_shift_grid(radius: float, *, points: int = 7) -> list[float]:
    r = abs(float(radius))
    if points <= 1:
        return [0.0]
    half = points // 2
    raw = [i / max(1, half) for i in range(-half, half + 1)]
    if len(raw) > points:
        raw = raw[:points]
    return [float(r * x) for x in raw]


def _coherence_builder_kwargs(kwargs: Mapping[str, Any]) -> dict[str, Any]:
    blocked = {'adaptive_tail_coherence_certificate', 'baseline_tail_coherence_certificate', 'support_core_neighborhood_certificate'}
    return {k: v for k, v in kwargs.items() if k not in blocked}


@dataclass
class TailAwareNeighborhoodCandidateSummary:
    source_label: str
    target_tail_qs: list[int]
    target_support_fraction: float | None
    target_entry_count: int
    crossing_center: float
    atlas_shift_grid: list[float]
    coherence_status: str
    bridge_status: str
    bridge_margin: float | None
    support_fraction_floor: float | None
    entry_coverage_floor: float | None
    realized_tail_qs: list[int]
    supporting_entry_count: int
    score: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenAdaptiveTailAwareNeighborhoodCertificate:
    rho: float
    family_label: str
    baseline_center: float
    baseline_atlas_shift_grid: list[float]
    selected_source_label: str
    selected_target_tail_qs: list[int]
    selected_center: float
    selected_atlas_shift_grid: list[float]
    candidate_summaries: list[TailAwareNeighborhoodCandidateSummary]
    selected_coherence: dict[str, Any]
    selected_bridge: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho': float(self.rho),
            'family_label': str(self.family_label),
            'baseline_center': float(self.baseline_center),
            'baseline_atlas_shift_grid': [float(x) for x in self.baseline_atlas_shift_grid],
            'selected_source_label': str(self.selected_source_label),
            'selected_target_tail_qs': [int(x) for x in self.selected_target_tail_qs],
            'selected_center': float(self.selected_center),
            'selected_atlas_shift_grid': [float(x) for x in self.selected_atlas_shift_grid],
            'candidate_summaries': [c.to_dict() for c in self.candidate_summaries],
            'selected_coherence': dict(self.selected_coherence),
            'selected_bridge': dict(self.selected_bridge),
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


def _candidate_score(bridge: dict[str, Any], coherence: dict[str, Any], target_tail_qs: Sequence[int]) -> tuple[float, ...]:
    realized_tail = [int(x) for x in bridge.get('certified_tail_qs', []) or []]
    return (
        float(_status_rank(str(bridge.get('theorem_status', '')))),
        1.0 if bool(bridge.get('certified_tail_is_suffix', False)) else 0.0,
        float(len(realized_tail)),
        float(len(target_tail_qs)),
        float(bridge.get('support_fraction_floor') if bridge.get('support_fraction_floor') is not None else 0.0),
        float(bridge.get('entry_coverage_floor') if bridge.get('entry_coverage_floor') is not None else 0.0),
        float(bridge.get('supporting_entry_count', 0)),
        float(bridge.get('bridge_margin') if bridge.get('bridge_margin') is not None else -1e9),
        float(_status_rank(str(coherence.get('theorem_status', '')))),
    )


def _build_target_tail_candidates(
    baseline: dict[str, Any],
    *,
    crossing_center: float,
    atlas_shifts: Sequence[float],
    min_tail_members: int,
    min_entry_coverage: float,
    max_tail_candidates: int,
    radius_factors: Sequence[float],
) -> list[tuple[str, list[int], float, list[float], float | None, int]]:
    entries = list(baseline.get('entries', []))
    generated_qs = sorted({int(row.get('q')) for row in baseline.get('support_profile', []) if int(row.get('q', 0)) > 0})
    if not generated_qs or not entries:
        return []
    witness_sets = []
    exact_tail_sets = []
    centers = []
    for entry in entries:
        witness_sets.append({int(q) for q in entry.get('witness_qs', []) if int(q) > 0})
        exact_tail_sets.append({int(q) for q in entry.get('exact_tail_qs', []) if int(q) > 0})
        centers.append(float(entry.get('crossing_center', crossing_center)))

    block_specs: list[tuple[tuple[float, ...], list[int], list[int], float]] = []
    seen_blocks: set[tuple[int, ...]] = set()
    for tail_set in exact_tail_sets:
        block = sorted(q for q in tail_set if q > 0)
        if len(block) < int(min_tail_members):
            continue
        sig = tuple(block)
        if sig in seen_blocks:
            continue
        seen_blocks.add(sig)
        supporting_entries = [i for i, other in enumerate(exact_tail_sets) if set(block).issubset(other or witness_sets[i])]
        if not supporting_entries:
            continue
        avg_q_support = float(sum(sum(1 for other in exact_tail_sets if q in (other or set())) for q in block) / (len(block) * max(1, len(entries))))
        score = (avg_q_support, avg_q_support, float(len(block)), float(len(supporting_entries)), 1.0, -float(block[0]))
        block_specs.append((score, [int(q) for q in block], supporting_entries, avg_q_support))

    n = len(generated_qs)
    for start in range(n):
        for end in range(start + min_tail_members - 1, n):
            block = generated_qs[start:end + 1]
            support_fracs = []
            supporting_entries: list[int] = []
            for i, witness in enumerate(witness_sets):
                covered = sum(1 for q in block if q in witness)
                frac = float(covered / len(block))
                if frac >= float(min(0.5, min_entry_coverage)):
                    supporting_entries.append(i)
                support_fracs.append(frac)
            if not supporting_entries:
                continue
            q_supports = []
            for q in block:
                q_supports.append(sum(1 for witness in witness_sets if q in witness) / max(1, len(witness_sets)))
            avg_q_support = float(sum(q_supports) / len(q_supports))
            min_q_support = float(min(q_supports))
            suffix_bonus = 1.0 if end == n - 1 else 0.0
            score = (
                avg_q_support,
                min_q_support,
                float(len(block)),
                float(len(supporting_entries)),
                suffix_bonus,
                -float(block[0]),
            )
            block_specs.append((score, [int(q) for q in block], supporting_entries, avg_q_support))

    block_specs.sort(reverse=True, key=lambda x: x[0])
    chosen = block_specs[: max(1, int(max_tail_candidates))]
    specs: list[tuple[str, list[int], float, list[float], float | None, int]] = []
    base_radius = _base_radius(atlas_shifts)
    seen: set[tuple[float, tuple[float, ...], tuple[int, ...]]] = set()
    for _, block, supporting_entries, avg_q_support in chosen:
        block_centers = [centers[i] for i in supporting_entries]
        if not block_centers:
            continue
        center = float(sum(block_centers) / len(block_centers))
        span = max(block_centers) - min(block_centers) if len(block_centers) >= 2 else 0.0
        for factor in radius_factors:
            radius = max(base_radius * float(factor), 0.5 * span + 0.25 * base_radius)
            grid = _tail_dense_shift_grid(radius)
            sig = (round(center, 12), tuple(round(float(x), 12) for x in grid), tuple(block))
            if sig in seen:
                continue
            seen.add(sig)
            label = f"tail-block-{block[0]}-{block[-1]}-x{factor:g}"
            specs.append((label, [int(q) for q in block], center, [float(x) for x in grid], avg_q_support, len(supporting_entries)))
    return specs


def build_golden_adaptive_tail_aware_neighborhood_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_shifts: Sequence[float] = (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4),
    refinement_radius_factors: Sequence[float] = (1.5, 1.0, 0.5),
    max_tail_candidates: int = 4,
    min_cluster_size: int = 2,
    min_tail_members: int = 2,
    min_support_fraction: float = 0.75,
    min_entry_coverage: float = 0.75,
    min_gap_to_width_ratio: float = 1.0,
    require_suffix_tail: bool = False,
    seed_from_support_core: bool = True,
    baseline_tail_coherence_certificate: Mapping[str, Any] | None = None,
    support_core_neighborhood_certificate: Mapping[str, Any] | None = None,
    **coherence_kwargs,
) -> GoldenAdaptiveTailAwareNeighborhoodCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    family_label = _family_label(family)

    if baseline_tail_coherence_certificate is not None:
        baseline = dict(baseline_tail_coherence_certificate)
    else:
        baseline = build_golden_adaptive_tail_coherence_certificate(
            family=family,
            rho=rho,
            crossing_center=crossing_center,
            atlas_shifts=atlas_shifts,
            min_cluster_size=min_cluster_size,
            min_tail_members=min_tail_members,
            min_q_support_fraction=min(0.5, float(min_support_fraction)),
            min_entry_tail_coverage=min(0.5, float(min_entry_coverage)),
            min_tail_support_fraction=min(0.5, float(min_support_fraction)),
            **_coherence_builder_kwargs(coherence_kwargs),
        ).to_dict()
    baseline_bridge = _build_golden_incompatibility_strict_bridge_from_coherence_payload(
        baseline,
        rho=rho,
        family_label=family_label,
        min_cluster_size=min_cluster_size,
        min_tail_members=min_tail_members,
        min_support_fraction=min_support_fraction,
        min_entry_coverage=min_entry_coverage,
        min_gap_to_width_ratio=min_gap_to_width_ratio,
        require_suffix_tail=require_suffix_tail,
        source_name='tail-aware-neighborhood',
        notes_prefix='Baseline tail-aware neighborhood.',
    ).to_dict()

    candidate_specs: list[tuple[str, list[int], float, list[float], float | None, int]] = [
        ('baseline', [int(x) for x in baseline_bridge.get('certified_tail_qs', []) or baseline.get('coherence_tail_qs', [])], float(crossing_center), [float(x) for x in atlas_shifts], None, 0)
    ]

    if seed_from_support_core:
        if support_core_neighborhood_certificate is not None:
            support_core = dict(support_core_neighborhood_certificate)
        else:
            support_core = build_golden_adaptive_support_core_neighborhood_certificate(
                family=family,
                rho=rho,
                crossing_center=crossing_center,
                atlas_shifts=atlas_shifts,
                refinement_radius_factors=tuple(refinement_radius_factors),
                min_cluster_size=min_cluster_size,
                min_tail_members=min_tail_members,
                min_support_fraction=min_support_fraction,
                min_entry_coverage=min_entry_coverage,
                min_gap_to_width_ratio=min_gap_to_width_ratio,
                require_suffix_tail=require_suffix_tail,
                baseline_tail_coherence_certificate=baseline,
                **_coherence_builder_kwargs(coherence_kwargs),
            ).to_dict()
        support_core_selected_bridge = dict((support_core.get('selected_bridge', {}) or {}))
        support_core_selected_coherence = dict((support_core.get('selected_coherence', {}) or {}))
        support_core_status = str(support_core_selected_bridge.get('theorem_status', 'unknown'))
        support_core_support = int(support_core_selected_bridge.get('supporting_entry_count', 0))
        support_core_fraction = support_core_selected_bridge.get('support_fraction_floor')
        support_core_coverage = support_core_selected_bridge.get('entry_coverage_floor')
        candidate_specs.append((
            'support-core-selected',
            [int(x) for x in support_core_selected_bridge.get('certified_tail_qs', [])],
            float(support_core.get('selected_center', crossing_center)),
            [float(x) for x in support_core.get('selected_atlas_shift_grid', list(atlas_shifts))],
            support_core_fraction,
            support_core_support,
        ))
        if (
            _status_rank(support_core_status) >= 4
            and support_core_support >= int(min_cluster_size)
            and (support_core_fraction is None or float(support_core_fraction) >= float(min_support_fraction))
            and (support_core_coverage is None or float(support_core_coverage) >= float(min_entry_coverage))
        ):
            baseline_tail_qs = [int(x) for x in baseline_bridge.get('certified_tail_qs', []) or baseline.get('coherence_tail_qs', [])]
            return GoldenAdaptiveTailAwareNeighborhoodCertificate(
                rho=float(rho),
                family_label=family_label,
                baseline_center=float(crossing_center),
                baseline_atlas_shift_grid=[float(x) for x in atlas_shifts],
                selected_source_label='support-core-selected',
                selected_target_tail_qs=[int(x) for x in support_core_selected_bridge.get('certified_tail_qs', [])],
                selected_center=float(support_core.get('selected_center', crossing_center)),
                selected_atlas_shift_grid=[float(x) for x in support_core.get('selected_atlas_shift_grid', list(atlas_shifts))],
                candidate_summaries=[
                    TailAwareNeighborhoodCandidateSummary(
                        source_label='baseline',
                        target_tail_qs=baseline_tail_qs,
                        target_support_fraction=None,
                        target_entry_count=0,
                        crossing_center=float(crossing_center),
                        atlas_shift_grid=[float(x) for x in atlas_shifts],
                        coherence_status=str(baseline.get('theorem_status', 'unknown')),
                        bridge_status=str(baseline_bridge.get('theorem_status', 'unknown')),
                        bridge_margin=None if baseline_bridge.get('bridge_margin') is None else float(baseline_bridge.get('bridge_margin')),
                        support_fraction_floor=None if baseline_bridge.get('support_fraction_floor') is None else float(baseline_bridge.get('support_fraction_floor')),
                        entry_coverage_floor=None if baseline_bridge.get('entry_coverage_floor') is None else float(baseline_bridge.get('entry_coverage_floor')),
                        realized_tail_qs=[int(x) for x in baseline_bridge.get('certified_tail_qs', [])],
                        supporting_entry_count=int(baseline_bridge.get('supporting_entry_count', 0)),
                        score=_candidate_score(baseline_bridge, baseline, baseline_tail_qs),
                    ),
                    TailAwareNeighborhoodCandidateSummary(
                        source_label='support-core-selected',
                        target_tail_qs=[int(x) for x in support_core_selected_bridge.get('certified_tail_qs', [])],
                        target_support_fraction=None if support_core_fraction is None else float(support_core_fraction),
                        target_entry_count=support_core_support,
                        crossing_center=float(support_core.get('selected_center', crossing_center)),
                        atlas_shift_grid=[float(x) for x in support_core.get('selected_atlas_shift_grid', list(atlas_shifts))],
                        coherence_status=str(support_core_selected_coherence.get('theorem_status', 'unknown')),
                        bridge_status=support_core_status,
                        bridge_margin=None if support_core_selected_bridge.get('bridge_margin') is None else float(support_core_selected_bridge.get('bridge_margin')),
                        support_fraction_floor=None if support_core_fraction is None else float(support_core_fraction),
                        entry_coverage_floor=None if support_core_coverage is None else float(support_core_coverage),
                        realized_tail_qs=[int(x) for x in support_core_selected_bridge.get('certified_tail_qs', [])],
                        supporting_entry_count=support_core_support,
                        score=_candidate_score(
                            support_core_selected_bridge,
                            support_core_selected_coherence,
                            support_core_selected_bridge.get('certified_tail_qs', []),
                        ),
                    ),
                ],
                selected_coherence=support_core_selected_coherence,
                selected_bridge=support_core_selected_bridge,
                theorem_status='golden-adaptive-tail-aware-neighborhood-strong',
                notes='The support-core neighborhood already carries a strong strict bridge, so no additional tail-aware refinement is required.',
            )

    candidate_specs.extend(_build_target_tail_candidates(
        baseline,
        crossing_center=float(crossing_center),
        atlas_shifts=atlas_shifts,
        min_tail_members=min_tail_members,
        min_entry_coverage=min_entry_coverage,
        max_tail_candidates=max_tail_candidates,
        radius_factors=refinement_radius_factors,
    ))

    seen: set[tuple[float, tuple[float, ...], tuple[int, ...]]] = set()
    candidate_summaries: list[TailAwareNeighborhoodCandidateSummary] = []

    selected_coherence = baseline
    selected_bridge = baseline_bridge
    selected_label = 'baseline'
    selected_target_tail = [int(x) for x in candidate_specs[0][1]]
    selected_center = float(crossing_center)
    selected_grid = [float(x) for x in atlas_shifts]
    best_score = _candidate_score(baseline_bridge, baseline, selected_target_tail)

    for idx, (label, target_tail_qs, center, grid, target_support, target_entries) in enumerate(candidate_specs):
        sig = (round(float(center), 12), tuple(round(float(x), 12) for x in grid), tuple(int(x) for x in target_tail_qs))
        if sig in seen:
            continue
        seen.add(sig)
        if idx == 0:
            coherence = baseline
            bridge = baseline_bridge
        else:
            coherence = build_golden_adaptive_tail_coherence_certificate(
                family=family,
                rho=rho,
                crossing_center=center,
                atlas_shifts=grid,
                min_cluster_size=min_cluster_size,
                min_tail_members=min_tail_members,
                min_q_support_fraction=min(0.5, float(min_support_fraction)),
                min_entry_tail_coverage=min(0.5, float(min_entry_coverage)),
                min_tail_support_fraction=min(0.5, float(min_support_fraction)),
                **coherence_kwargs,
            ).to_dict()
            bridge = _build_golden_incompatibility_strict_bridge_from_coherence_payload(
                coherence,
                rho=rho,
                family_label=family_label,
                min_cluster_size=min_cluster_size,
                min_tail_members=min_tail_members,
                min_support_fraction=min_support_fraction,
                min_entry_coverage=min_entry_coverage,
                min_gap_to_width_ratio=min_gap_to_width_ratio,
                require_suffix_tail=require_suffix_tail,
                source_name='tail-aware-neighborhood',
                notes_prefix='Tail-aware refined neighborhood.',
            ).to_dict()
        score = _candidate_score(bridge, coherence, target_tail_qs)
        candidate_summaries.append(TailAwareNeighborhoodCandidateSummary(
            source_label=str(label),
            target_tail_qs=[int(x) for x in target_tail_qs],
            target_support_fraction=None if target_support is None else float(target_support),
            target_entry_count=int(target_entries),
            crossing_center=float(center),
            atlas_shift_grid=[float(x) for x in grid],
            coherence_status=str(coherence.get('theorem_status', 'unknown')),
            bridge_status=str(bridge.get('theorem_status', 'unknown')),
            bridge_margin=None if bridge.get('bridge_margin') is None else float(bridge.get('bridge_margin')),
            support_fraction_floor=None if bridge.get('support_fraction_floor') is None else float(bridge.get('support_fraction_floor')),
            entry_coverage_floor=None if bridge.get('entry_coverage_floor') is None else float(bridge.get('entry_coverage_floor')),
            realized_tail_qs=[int(x) for x in bridge.get('certified_tail_qs', [])],
            supporting_entry_count=int(bridge.get('supporting_entry_count', 0)),
            score=score,
        ))
        if (score > best_score or (score == best_score and idx != 0 and len([int(x) for x in bridge.get('certified_tail_qs', [])]) >= len(selected_target_tail) and str(label).startswith('tail-block-'))):
            best_score = score
            selected_coherence = coherence
            selected_bridge = bridge
            selected_label = str(label)
            selected_target_tail = [int(x) for x in target_tail_qs]
            selected_center = float(center)
            selected_grid = [float(x) for x in grid]

    selected_status = str(selected_bridge.get('theorem_status', 'unknown'))
    if _status_rank(selected_status) >= 4:
        theorem_status = 'golden-adaptive-tail-aware-neighborhood-strong'
        notes = 'A tail-aware refined neighborhood preserves a multi-denominator support block strongly enough to close the strict upper bridge.'
    elif _status_rank(selected_status) == 3:
        theorem_status = 'golden-adaptive-tail-aware-neighborhood-moderate'
        notes = 'Tail-aware neighborhood refinement improves the support block and bridge margins, but the strongest strict thresholds are not all closed.'
    elif _status_rank(selected_status) == 2:
        theorem_status = 'golden-adaptive-tail-aware-neighborhood-weak'
        notes = 'Tail-aware refinement exposes a better support block than the baseline neighborhood, but the strict bridge is still only partially closed.'
    elif _status_rank(selected_status) == 1:
        theorem_status = 'golden-adaptive-tail-aware-neighborhood-fragile'
        notes = 'Tail-aware refinement still localizes the upper object, but no strict multi-denominator support block stabilizes.'
    else:
        theorem_status = 'golden-adaptive-tail-aware-neighborhood-failed'
        notes = 'No tail-aware refined neighborhood produced a usable strict support block.'

    return GoldenAdaptiveTailAwareNeighborhoodCertificate(
        rho=float(rho),
        family_label=family_label,
        baseline_center=float(crossing_center),
        baseline_atlas_shift_grid=[float(x) for x in atlas_shifts],
        selected_source_label=selected_label,
        selected_target_tail_qs=selected_target_tail,
        selected_center=selected_center,
        selected_atlas_shift_grid=selected_grid,
        candidate_summaries=candidate_summaries,
        selected_coherence=selected_coherence,
        selected_bridge=selected_bridge,
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    'TailAwareNeighborhoodCandidateSummary',
    'GoldenAdaptiveTailAwareNeighborhoodCertificate',
    'build_golden_adaptive_tail_aware_neighborhood_certificate',
]
