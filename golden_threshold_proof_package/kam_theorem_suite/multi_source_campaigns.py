from __future__ import annotations

"""Campaigns driven by multi-source continuation atlases.

This module extends seed-aware campaigns by replacing the nearest-neighbor seed
policy with a small multi-source seed atlas.  Later approximants can therefore
be started from a blended continuation guess assembled from several nearby
successful branches.
"""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .class_campaigns import ArithmeticClassSpec, build_class_ladder_report
from .challenger_pruning import ChallengerSpec, build_challenger_pruning_report
from .seed_transfer import build_seed_profile_from_orbit
from .seeded_campaigns import SeedBankEntry
from .multi_source_seed_atlas import build_multi_source_seed_atlas
from .standard_map import HarmonicFamily, solve_periodic_orbit
from .supercritical_bands import build_crossing_to_hyperbolic_band_bridge


@dataclass
class AtlasCampaignAttempt:
    p: int
    q: int
    label: str
    attempt_index: int
    predicted_center: float
    crossing_half_width: float
    crossing_window_lo: float
    crossing_window_hi: float
    predictor_method: str
    atlas_used: bool
    atlas_selected_method: str | None
    atlas_selected_source_labels: list[str]
    atlas_selected_residual_inf: float | None
    atlas_report: dict[str, Any] | None
    bridge_status: str
    crossing_certification_tier: str
    crossing_root_window_lo: float | None
    crossing_root_window_hi: float | None
    crossing_root_center: float | None
    first_supercritical_gap: float | None
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d['status'] = d['bridge_status']
        d['root_window_lo'] = d['crossing_root_window_lo']
        d['root_window_hi'] = d['crossing_root_window_hi']
        return d


@dataclass
class AtlasApproximantEntry:
    p: int
    q: int
    label: str
    order_index: int
    rho_error: float
    final_status: str
    attempts: list[dict[str, Any]]
    accepted_attempt_index: int | None
    accepted_center: float | None
    final_crossing_root_window_lo: float | None
    final_crossing_root_window_hi: float | None
    final_crossing_root_center: float | None
    final_supercritical_gap: float | None
    atlas_selected_method: str | None
    atlas_selected_source_labels: list[str]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d['status'] = d['final_status']
        d['root_window_lo'] = d['final_crossing_root_window_lo']
        d['root_window_hi'] = d['final_crossing_root_window_hi']
        return d


@dataclass
class MultiSourceClassCampaignReport:
    class_label: str
    ladder: dict[str, Any]
    reference_crossing_center: float
    reference_lower_bound: float
    initial_crossing_half_width: float
    widening_factor: float
    max_attempts_per_approximant: int
    max_sources: int
    entries: list[dict[str, Any]]
    seed_bank: list[dict[str, Any]]
    atlas_use_count: int
    atlas_blend_use_count: int
    certified_crossing_count: int
    certified_band_bridge_count: int
    crossing_envelope_lo: float | None
    crossing_envelope_hi: float | None
    pruning_against_reference: dict[str, Any]
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiSourceCampaignComparisonReport:
    class_label: str
    seeded_campaign: dict[str, Any]
    atlas_campaign: dict[str, Any]
    seeded_certified_crossing_count: int
    atlas_certified_crossing_count: int
    seeded_seed_reuse_count: int
    atlas_use_count: int
    atlas_blend_use_count: int
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiSourceMultiClassCampaignReport:
    reference_label: str
    reference_lower_bound: float
    class_campaigns: list[dict[str, Any]]
    total_atlas_use_count: int
    total_atlas_blend_use_count: int
    dominated_classes: list[str]
    overlapping_classes: list[str]
    undecided_classes: list[str]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _center_from_root_window(lo: float | None, hi: float | None) -> float | None:
    if lo is None or hi is None:
        return None
    return 0.5 * (float(lo) + float(hi))


def _prediction_from_history(history: list[dict[str, float]], *, q: int, fallback_center: float) -> tuple[float, str]:
    q = int(q)
    fallback_center = float(fallback_center)
    if not history:
        return fallback_center, 'reference-center'
    if len(history) == 1:
        return float(history[-1]['center']), 'last-success'
    xs = np.array([1.0 / (float(h['q']) ** 2) for h in history], dtype=float)
    ys = np.array([float(h['center']) for h in history], dtype=float)
    w = np.array([float(h['q']) for h in history], dtype=float)
    A = np.column_stack([np.ones_like(xs), xs])
    Aw = A * w[:, None]
    yw = ys * w
    coeffs, *_ = np.linalg.lstsq(Aw, yw, rcond=None)
    a, b = coeffs
    pred = float(a + b * (1.0 / (q ** 2)))
    if not np.isfinite(pred):
        return float(history[-1]['center']), 'last-success-fallback'
    pred = float(np.clip(pred, fallback_center - 0.03, fallback_center + 0.03))
    return pred, 'q^-2-fit'


def _solve_root_orbit(*, p: int, q: int, K_center: float, family: HarmonicFamily, x_guess) -> np.ndarray | None:
    sol = solve_periodic_orbit(
        p=int(p),
        q=int(q),
        K=float(K_center),
        family=family,
        x0=None if x_guess is None else np.asarray(x_guess, dtype=float),
    )
    if not sol.get('success', False):
        return None
    return np.asarray(sol['x'], dtype=float)


def build_multi_source_class_campaign(
    spec: ArithmeticClassSpec,
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily | None = None,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    initial_crossing_half_width: float = 2.5e-3,
    widening_factor: float = 1.8,
    max_attempts_per_approximant: int = 3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = True,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    max_sources: int = 3,
    refine_candidates: bool = True,
) -> MultiSourceClassCampaignReport:
    family = family or HarmonicFamily()
    ladder = build_class_ladder_report(
        spec,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
    ).to_dict()

    seed_bank: list[SeedBankEntry] = []
    predictor_history: list[dict[str, float]] = []
    entries: list[dict[str, Any]] = []
    atlas_use_count = 0
    atlas_blend_use_count = 0

    for order_index, approx in enumerate(ladder['approximants']):
        p = int(approx['p'])
        q = int(approx['q'])
        label = str(approx['label'])
        predicted_center, predictor_method = _prediction_from_history(
            predictor_history, q=q, fallback_center=reference_crossing_center
        )
        current_half_width = float(initial_crossing_half_width)
        attempts: list[dict[str, Any]] = []
        accepted_attempt: AtlasCampaignAttempt | None = None

        for attempt_index in range(max_attempts_per_approximant):
            center = float(predicted_center)
            crossing_lo = center - current_half_width
            crossing_hi = center + current_half_width
            atlas_report = None
            x_guess = None
            atlas_selected_method = None
            atlas_selected_source_labels: list[str] = []
            atlas_selected_residual_inf = None
            if seed_bank:
                atlas_report = build_multi_source_seed_atlas(
                    seed_bank,
                    target_p=p,
                    target_q=q,
                    target_K=center,
                    family=family,
                    max_sources=max_sources,
                    refine_candidates=refine_candidates,
                ).to_dict()
                x_guess = atlas_report.get('selected_x_guess')
                atlas_selected_method = atlas_report.get('selected_method')
                atlas_selected_source_labels = list(atlas_report.get('selected_source_labels', []))
                atlas_selected_residual_inf = atlas_report.get('selected_residual_inf')
                if x_guess is not None:
                    x_guess = np.asarray(x_guess, dtype=float)
                    atlas_use_count += 1
                    if atlas_selected_method and atlas_selected_method.startswith('atlas:'):
                        atlas_blend_use_count += 1

            rep = build_crossing_to_hyperbolic_band_bridge(
                p=p,
                q=q,
                crossing_K_lo=crossing_lo,
                crossing_K_hi=crossing_hi,
                band_search_lo=float(center + band_offset_lo),
                band_search_hi=float(center + band_offset_hi),
                family=family,
                target_residue=target_residue,
                auto_localize_crossing=auto_localize_crossing,
                initial_subdivisions=initial_subdivisions,
                max_depth=max_depth,
                min_width=min_width,
                x_guess=x_guess,
            ).to_dict()
            crossing = dict(rep.get('crossing_certificate', {}))
            root_lo = crossing.get('certified_root_window_lo')
            root_hi = crossing.get('certified_root_window_hi')
            root_center = _center_from_root_window(root_lo, root_hi)
            attempt = AtlasCampaignAttempt(
                p=p,
                q=q,
                label=label,
                attempt_index=attempt_index,
                predicted_center=center,
                crossing_half_width=current_half_width,
                crossing_window_lo=crossing_lo,
                crossing_window_hi=crossing_hi,
                predictor_method=predictor_method,
                atlas_used=bool(x_guess is not None),
                atlas_selected_method=None if atlas_selected_method is None else str(atlas_selected_method),
                atlas_selected_source_labels=atlas_selected_source_labels,
                atlas_selected_residual_inf=None if atlas_selected_residual_inf is None else float(atlas_selected_residual_inf),
                atlas_report=atlas_report,
                bridge_status=str(rep.get('status', 'unknown')),
                crossing_certification_tier=str(crossing.get('certification_tier', crossing.get('status', 'unknown'))),
                crossing_root_window_lo=None if root_lo is None else float(root_lo),
                crossing_root_window_hi=None if root_hi is None else float(root_hi),
                crossing_root_center=None if root_center is None else float(root_center),
                first_supercritical_gap=None if rep.get('first_supercritical_gap') is None else float(rep['first_supercritical_gap']),
                report=rep,
            )
            attempts.append(attempt.to_dict())
            if attempt.bridge_status in {'crossing-plus-hyperbolic-band', 'crossing-only'}:
                accepted_attempt = attempt
                break
            current_half_width *= float(widening_factor)

        if accepted_attempt is not None and accepted_attempt.crossing_root_center is not None:
            predictor_history.append({'q': float(q), 'center': float(accepted_attempt.crossing_root_center)})
            seed_guess = None
            if accepted_attempt.atlas_report is not None:
                if accepted_attempt.atlas_report.get('selected_x_refined') is not None:
                    seed_guess = accepted_attempt.atlas_report['selected_x_refined']
                else:
                    seed_guess = accepted_attempt.atlas_report.get('selected_x_guess')
            root_orbit = _solve_root_orbit(
                p=p,
                q=q,
                K_center=float(accepted_attempt.crossing_root_center),
                family=family,
                x_guess=seed_guess,
            )
            if root_orbit is not None:
                profile = build_seed_profile_from_orbit(
                    root_orbit,
                    p=p,
                    q=q,
                    K=float(accepted_attempt.crossing_root_center),
                    family=family,
                    label=label,
                )
                seed_bank.append(
                    SeedBankEntry(
                        label=label,
                        p=p,
                        q=q,
                        rho=float(p) / float(q),
                        K_center=float(accepted_attempt.crossing_root_center),
                        source_method='multi-source-root',
                        seed_profile=profile.to_dict(),
                    )
                )

        entry = AtlasApproximantEntry(
            p=p,
            q=q,
            label=label,
            order_index=order_index,
            rho_error=float(approx['rho_error']),
            final_status='failed' if accepted_attempt is None else accepted_attempt.bridge_status,
            attempts=attempts,
            accepted_attempt_index=None if accepted_attempt is None else int(accepted_attempt.attempt_index),
            accepted_center=None if accepted_attempt is None else float(accepted_attempt.predicted_center),
            final_crossing_root_window_lo=None if accepted_attempt is None else accepted_attempt.crossing_root_window_lo,
            final_crossing_root_window_hi=None if accepted_attempt is None else accepted_attempt.crossing_root_window_hi,
            final_crossing_root_center=None if accepted_attempt is None else accepted_attempt.crossing_root_center,
            final_supercritical_gap=None if accepted_attempt is None else accepted_attempt.first_supercritical_gap,
            atlas_selected_method=None if accepted_attempt is None else accepted_attempt.atlas_selected_method,
            atlas_selected_source_labels=[] if accepted_attempt is None else list(accepted_attempt.atlas_selected_source_labels),
            notes='Multi-source atlas campaign entry. The atlas influences only the initial periodic solve.',
        )
        entries.append(entry.to_dict())

    root_los = [e['final_crossing_root_window_lo'] for e in entries if e['final_crossing_root_window_lo'] is not None]
    root_his = [e['final_crossing_root_window_hi'] for e in entries if e['final_crossing_root_window_hi'] is not None]
    challengers = [
        ChallengerSpec(
            preperiod=tuple(spec.preperiod),
            period=tuple(spec.period),
            threshold_lower_bound=None if e['final_crossing_root_window_lo'] is None else float(e['final_crossing_root_window_lo']),
            threshold_upper_bound=None if e['final_crossing_root_window_hi'] is None else float(e['final_crossing_root_window_hi']),
            label=e['label'],
        )
        for e in entries
    ]
    pruning = build_challenger_pruning_report(
        golden_lower_bound=float(reference_lower_bound),
        challengers=challengers,
    ).to_dict()
    notes = (
        'This campaign replaces nearest-neighbor seed reuse with a small multi-source continuation atlas. '
        'Several nearby successful approximants may jointly seed the next branch.'
    )
    return MultiSourceClassCampaignReport(
        class_label=str(ladder['class_label']),
        ladder=ladder,
        reference_crossing_center=float(reference_crossing_center),
        reference_lower_bound=float(reference_lower_bound),
        initial_crossing_half_width=float(initial_crossing_half_width),
        widening_factor=float(widening_factor),
        max_attempts_per_approximant=int(max_attempts_per_approximant),
        max_sources=int(max_sources),
        entries=entries,
        seed_bank=[s.to_dict() for s in seed_bank],
        atlas_use_count=int(atlas_use_count),
        atlas_blend_use_count=int(atlas_blend_use_count),
        certified_crossing_count=sum(1 for e in entries if e['final_crossing_root_window_hi'] is not None),
        certified_band_bridge_count=sum(1 for e in entries if e['final_status'] == 'crossing-plus-hyperbolic-band'),
        crossing_envelope_lo=None if not root_los else float(min(root_los)),
        crossing_envelope_hi=None if not root_his else float(max(root_his)),
        pruning_against_reference=pruning,
        status='multi-source-campaign-complete' if entries else 'empty',
        notes=notes,
    )


def build_multi_source_campaign_comparison(
    spec: ArithmeticClassSpec,
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> MultiSourceCampaignComparisonReport:
    family = family or HarmonicFamily()
    from .seeded_campaigns import build_seeded_class_campaign

    seeded_kwargs = dict(kwargs)
    seeded_kwargs.pop('max_sources', None)
    seeded_kwargs.pop('refine_candidates', None)
    seeded = build_seeded_class_campaign(
        spec,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        family=family,
        **seeded_kwargs,
    ).to_dict()
    atlas = build_multi_source_class_campaign(
        spec,
        reference_crossing_center=reference_crossing_center,
        reference_lower_bound=reference_lower_bound,
        family=family,
        **kwargs,
    ).to_dict()
    notes = (
        'This comparison report is intended for notebook- and script-level sanity checks. '
        'It contrasts single-source seeded campaigns with the multi-source atlas policy on the same arithmetic class.'
    )
    return MultiSourceCampaignComparisonReport(
        class_label=str(spec.label or spec.period),
        seeded_campaign=seeded,
        atlas_campaign=atlas,
        seeded_certified_crossing_count=int(seeded.get('certified_crossing_count', 0)),
        atlas_certified_crossing_count=int(atlas.get('certified_crossing_count', 0)),
        seeded_seed_reuse_count=int(seeded.get('seed_reuse_count', 0)),
        atlas_use_count=int(atlas.get('atlas_use_count', 0)),
        atlas_blend_use_count=int(atlas.get('atlas_blend_use_count', 0)),
        notes=notes,
    )


def build_multi_source_multi_class_campaign(
    specs: list[ArithmeticClassSpec],
    *,
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily | None = None,
    **kwargs,
) -> MultiSourceMultiClassCampaignReport:
    family = family or HarmonicFamily()
    campaigns = [
        build_multi_source_class_campaign(
            spec,
            reference_crossing_center=reference_crossing_center,
            reference_lower_bound=reference_lower_bound,
            family=family,
            **kwargs,
        ).to_dict()
        for spec in specs
    ]
    dominated: list[str] = []
    overlapping: list[str] = []
    undecided: list[str] = []
    for rep in campaigns:
        pruning = rep.get('pruning_against_reference', {})
        statuses = pruning.get('challenger_statuses', [])
        class_statuses = {row.get('status') for row in statuses}
        if class_statuses and class_statuses <= {'dominated'}:
            dominated.append(rep['class_label'])
        elif 'overlapping' in class_statuses:
            overlapping.append(rep['class_label'])
        else:
            undecided.append(rep['class_label'])
    notes = (
        'Multi-class multi-source campaigns use local continuation atlases rather than a single predecessor seed. '
        'They remain challenger-search scaffolds, not a finished exhaustion theorem.'
    )
    return MultiSourceMultiClassCampaignReport(
        reference_label='reference',
        reference_lower_bound=float(reference_lower_bound),
        class_campaigns=campaigns,
        total_atlas_use_count=int(sum(rep.get('atlas_use_count', 0) for rep in campaigns)),
        total_atlas_blend_use_count=int(sum(rep.get('atlas_blend_use_count', 0) for rep in campaigns)),
        dominated_classes=dominated,
        overlapping_classes=overlapping,
        undecided_classes=undecided,
        notes=notes,
    )


__all__ = [
    'AtlasCampaignAttempt',
    'AtlasApproximantEntry',
    'MultiSourceClassCampaignReport',
    'MultiSourceCampaignComparisonReport',
    'MultiSourceMultiClassCampaignReport',
    'build_multi_source_class_campaign',
    'build_multi_source_campaign_comparison',
    'build_multi_source_multi_class_campaign',
]
