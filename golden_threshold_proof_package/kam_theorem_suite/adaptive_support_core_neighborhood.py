from __future__ import annotations

"""Refined adaptive neighborhood search for strict support cores.

The stage-37 strict bridge promotion can only use the support core already
visible in one adaptive tail-coherence run.  The next strongest move is to
improve the *neighborhood construction itself*: recenter and densify the atlas
around promising entries, then rerun the strict bridge promotion on those
refined neighborhoods.

This module performs that search and returns the strongest refined strict bridge
currently available.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .adaptive_tail_coherence import build_golden_adaptive_tail_coherence_certificate
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
    if vals:
        return float(min(vals))
    return 4.0e-4


def _dense_shift_grid(radius: float) -> list[float]:
    r = abs(float(radius))
    return [-r, -0.5 * r, 0.0, 0.5 * r, r]


def _coherence_builder_kwargs(kwargs: Mapping[str, Any]) -> dict[str, Any]:
    blocked = {'adaptive_tail_coherence_certificate', 'baseline_tail_coherence_certificate', 'support_core_neighborhood_certificate'}
    return {k: v for k, v in kwargs.items() if k not in blocked}


@dataclass
class NeighborhoodCandidateSummary:
    source_label: str
    crossing_center: float
    atlas_shift_grid: list[float]
    coherence_status: str
    bridge_status: str
    bridge_margin: float | None
    support_fraction_floor: float | None
    entry_coverage_floor: float | None
    tail_qs: list[int]
    supporting_entry_count: int
    score: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenAdaptiveSupportCoreNeighborhoodCertificate:
    rho: float
    family_label: str
    baseline_center: float
    baseline_atlas_shift_grid: list[float]
    selected_source_label: str
    selected_center: float
    selected_atlas_shift_grid: list[float]
    candidate_summaries: list[NeighborhoodCandidateSummary]
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
            'selected_center': float(self.selected_center),
            'selected_atlas_shift_grid': [float(x) for x in self.selected_atlas_shift_grid],
            'candidate_summaries': [c.to_dict() for c in self.candidate_summaries],
            'selected_coherence': dict(self.selected_coherence),
            'selected_bridge': dict(self.selected_bridge),
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


def _candidate_score(bridge: dict[str, Any], coherence: dict[str, Any]) -> tuple[float, ...]:
    return (
        float(_status_rank(str(bridge.get('theorem_status', '')))),
        float(bridge.get('bridge_margin') if bridge.get('bridge_margin') is not None else -1e9),
        float(bridge.get('support_fraction_floor') if bridge.get('support_fraction_floor') is not None else 0.0),
        float(bridge.get('entry_coverage_floor') if bridge.get('entry_coverage_floor') is not None else 0.0),
        float(len(bridge.get('certified_tail_qs', []) or [])),
        float(bridge.get('supporting_entry_count', 0)),
        float(_status_rank(str(coherence.get('theorem_status', '')))),
    )


def build_golden_adaptive_support_core_neighborhood_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_shifts: Sequence[float] = (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4),
    refinement_radius_factors: Sequence[float] = (1.0, 0.5),
    min_cluster_size: int = 2,
    min_tail_members: int = 2,
    min_support_fraction: float = 0.75,
    min_entry_coverage: float = 0.75,
    min_gap_to_width_ratio: float = 1.0,
    require_suffix_tail: bool = False,
    baseline_tail_coherence_certificate: Mapping[str, Any] | None = None,
    **coherence_kwargs,
) -> GoldenAdaptiveSupportCoreNeighborhoodCertificate:
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
        source_name='strict-support-neighborhood',
        notes_prefix='Baseline adaptive neighborhood.',
    ).to_dict()
    baseline_status = str(baseline_bridge.get('theorem_status', 'unknown'))
    baseline_support = int(baseline_bridge.get('supporting_entry_count', 0))
    baseline_fraction = baseline_bridge.get('support_fraction_floor')
    baseline_coverage = baseline_bridge.get('entry_coverage_floor')
    if (
        _status_rank(baseline_status) >= 4
        and baseline_support >= int(min_cluster_size)
        and (baseline_fraction is None or float(baseline_fraction) >= float(min_support_fraction))
        and (baseline_coverage is None or float(baseline_coverage) >= float(min_entry_coverage))
    ):
        return GoldenAdaptiveSupportCoreNeighborhoodCertificate(
            rho=float(rho),
            family_label=family_label,
            baseline_center=float(crossing_center),
            baseline_atlas_shift_grid=[float(x) for x in atlas_shifts],
            selected_source_label='baseline',
            selected_center=float(crossing_center),
            selected_atlas_shift_grid=[float(x) for x in atlas_shifts],
            candidate_summaries=[
                NeighborhoodCandidateSummary(
                    source_label='baseline',
                    crossing_center=float(crossing_center),
                    atlas_shift_grid=[float(x) for x in atlas_shifts],
                    coherence_status=str(baseline.get('theorem_status', 'unknown')),
                    bridge_status=baseline_status,
                    bridge_margin=None if baseline_bridge.get('bridge_margin') is None else float(baseline_bridge.get('bridge_margin')),
                    support_fraction_floor=None if baseline_fraction is None else float(baseline_fraction),
                    entry_coverage_floor=None if baseline_coverage is None else float(baseline_coverage),
                    tail_qs=[int(x) for x in baseline_bridge.get('certified_tail_qs', [])],
                    supporting_entry_count=baseline_support,
                    score=_candidate_score(baseline_bridge, baseline),
                )
            ],
            selected_coherence=baseline,
            selected_bridge=baseline_bridge,
            theorem_status='golden-adaptive-support-core-neighborhood-strong',
            notes='The baseline adaptive neighborhood already carries a strong strict bridge, so no additional support-core refinement is required.',
        )

    candidate_specs: list[tuple[str, float, list[float]]] = [('baseline', float(crossing_center), [float(x) for x in atlas_shifts])]
    seen = {(round(float(crossing_center), 12), tuple(round(float(x), 12) for x in atlas_shifts))}
    entries = list(baseline.get('entries', []))
    prioritized_indices = []
    for key in ('supporting_entry_indices', 'clustered_entry_indices', 'successful_entry_indices'):
        prioritized_indices.extend(int(i) for i in baseline.get(key, []) if 0 <= int(i) < len(entries))
    ordered_indices = []
    for i in prioritized_indices:
        if i not in ordered_indices:
            ordered_indices.append(i)
    centers = [float(crossing_center)]
    for i in ordered_indices:
        ctr = entries[i].get('crossing_center')
        if ctr is not None:
            centers.append(float(ctr))
    signature_groups: dict[tuple[int, ...], list[float]] = {}
    for entry in entries:
        tail_qs = tuple(int(q) for q in entry.get('exact_tail_qs', []) if int(q) > 0)
        ctr = entry.get('crossing_center')
        if len(tail_qs) < int(min_tail_members) or ctr is None:
            continue
        signature_groups.setdefault(tail_qs, []).append(float(ctr))
    for ctrs in signature_groups.values():
        if ctrs:
            centers.append(float(sum(ctrs) / len(ctrs)))
    base_radius = _base_radius(atlas_shifts)
    for center in centers:
        for factor in refinement_radius_factors:
            grid = _dense_shift_grid(base_radius * float(factor))
            sig = (round(float(center), 12), tuple(round(float(x), 12) for x in grid))
            if sig in seen:
                continue
            seen.add(sig)
            label = 'refined-supporting' if center != float(crossing_center) else f'refined-baseline-{factor:g}'
            candidate_specs.append((label, float(center), grid))

    candidate_summaries: list[NeighborhoodCandidateSummary] = []
    selected_coherence = baseline
    selected_bridge = baseline_bridge
    selected_label = 'baseline'
    selected_center = float(crossing_center)
    selected_grid = [float(x) for x in atlas_shifts]
    best_score = _candidate_score(baseline_bridge, baseline)

    # Skip re-evaluating the exact baseline spec.
    for label, center, grid in candidate_specs[1:]:
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
            source_name='strict-support-neighborhood',
            notes_prefix='Refined adaptive neighborhood.',
        ).to_dict()
        score = _candidate_score(bridge, coherence)
        candidate_summaries.append(NeighborhoodCandidateSummary(
            source_label=label,
            crossing_center=float(center),
            atlas_shift_grid=[float(x) for x in grid],
            coherence_status=str(coherence.get('theorem_status', 'unknown')),
            bridge_status=str(bridge.get('theorem_status', 'unknown')),
            bridge_margin=None if bridge.get('bridge_margin') is None else float(bridge.get('bridge_margin')),
            support_fraction_floor=None if bridge.get('support_fraction_floor') is None else float(bridge.get('support_fraction_floor')),
            entry_coverage_floor=None if bridge.get('entry_coverage_floor') is None else float(bridge.get('entry_coverage_floor')),
            tail_qs=[int(x) for x in bridge.get('certified_tail_qs', [])],
            supporting_entry_count=int(bridge.get('supporting_entry_count', 0)),
            score=score,
        ))
        if score > best_score:
            best_score = score
            selected_coherence = coherence
            selected_bridge = bridge
            selected_label = label
            selected_center = float(center)
            selected_grid = [float(x) for x in grid]

    selected_status = str(selected_bridge.get('theorem_status', 'unknown'))
    if _status_rank(selected_status) >= 4:
        theorem_status = 'golden-adaptive-support-core-neighborhood-strong'
        notes = 'A recentered and densified adaptive neighborhood exposes a strict support core strong enough to close the upper bridge.'
    elif _status_rank(selected_status) == 3:
        theorem_status = 'golden-adaptive-support-core-neighborhood-moderate'
        notes = 'Neighborhood refinement improves the strict support core, but one or more strict bridge margins remain below the strongest threshold.'
    elif _status_rank(selected_status) == 2:
        theorem_status = 'golden-adaptive-support-core-neighborhood-weak'
        notes = 'Neighborhood refinement finds a better support core than the baseline adaptive neighborhood, but the strict bridge is still only partially closed.'
    elif _status_rank(selected_status) == 1:
        theorem_status = 'golden-adaptive-support-core-neighborhood-fragile'
        notes = 'A refined neighborhood still localizes the upper object, but no strict support core stabilizes.'
    else:
        theorem_status = 'golden-adaptive-support-core-neighborhood-failed'
        notes = 'Neighborhood refinement did not expose a usable strict support core.'

    return GoldenAdaptiveSupportCoreNeighborhoodCertificate(
        rho=rho,
        family_label=family_label,
        baseline_center=float(crossing_center),
        baseline_atlas_shift_grid=[float(x) for x in atlas_shifts],
        selected_source_label=selected_label,
        selected_center=selected_center,
        selected_atlas_shift_grid=selected_grid,
        candidate_summaries=candidate_summaries,
        selected_coherence=selected_coherence,
        selected_bridge=selected_bridge,
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    'NeighborhoodCandidateSummary',
    'GoldenAdaptiveSupportCoreNeighborhoodCertificate',
    'build_golden_adaptive_support_core_neighborhood_certificate',
]
