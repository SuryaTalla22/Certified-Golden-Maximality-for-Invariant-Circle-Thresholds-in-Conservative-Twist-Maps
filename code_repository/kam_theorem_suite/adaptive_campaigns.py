
from __future__ import annotations

"""Adaptive arithmetic-class campaign builders.

This module pushes the campaign layer beyond fixed reference-centered windows.
The earlier class-campaign workflow assigned every approximant the same search
center. Here, successful local certificates seed later approximants through a
conservative predictor in ``1/q^2`` together with widening-on-failure retries.

This remains a proof bridge rather than a theorem about asymptotic scaling. The
predictor is a campaign policy; the mathematical content remains in the local
crossing and hyperbolic-band certificates that each attempt invokes.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np

from .challenger_pruning import ChallengerSpec, build_challenger_pruning_report
from .class_campaigns import ArithmeticClassSpec, build_class_ladder_report
from .standard_map import HarmonicFamily
from .supercritical_bands import build_crossing_to_hyperbolic_band_bridge


@dataclass
class AdaptiveCampaignAttempt:
    p: int
    q: int
    label: str
    attempt_index: int
    predictor_method: str
    predicted_center: float
    crossing_half_width: float
    crossing_window_lo: float
    crossing_window_hi: float
    reference_center: float
    bridge_status: str
    crossing_certification_tier: str
    crossing_root_window_lo: float | None
    crossing_root_window_hi: float | None
    crossing_root_center: float | None
    first_supercritical_gap: float | None
    used_reference_blend: bool
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d['status'] = d['bridge_status']
        d['root_window_lo'] = d['crossing_root_window_lo']
        d['root_window_hi'] = d['crossing_root_window_hi']
        return d


@dataclass
class AdaptiveApproximantCampaignEntry:
    p: int
    q: int
    label: str
    order_index: int
    rho_error: float
    final_status: str
    attempts: list[dict[str, Any]]
    accepted_attempt_index: int | None
    accepted_predictor_method: str | None
    accepted_center: float | None
    final_crossing_root_window_lo: float | None
    final_crossing_root_window_hi: float | None
    final_crossing_root_center: float | None
    final_supercritical_gap: float | None
    threshold_lower_bound: float | None
    threshold_upper_bound: float | None
    notes: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d['status'] = d['final_status']
        d['root_window_lo'] = d['final_crossing_root_window_lo']
        d['root_window_hi'] = d['final_crossing_root_window_hi']
        return d


@dataclass
class AdaptiveClassCampaignReport:
    class_label: str
    ladder: dict[str, Any]
    reference_crossing_center: float
    reference_lower_bound: float
    predictor_mode: str
    initial_crossing_half_width: float
    widening_factor: float
    max_attempts_per_approximant: int
    entries: list[dict[str, Any]]
    certified_crossing_count: int
    certified_band_bridge_count: int
    failed_entry_count: int
    crossing_envelope_lo: float | None
    crossing_envelope_hi: float | None
    crossing_envelope_width: float | None
    predictor_history: list[dict[str, float]]
    pruning_against_reference: dict[str, Any]
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AdaptiveMultiClassCampaignReport:
    reference_label: str
    reference_lower_bound: float
    predictor_mode: str
    class_campaigns: list[dict[str, Any]]
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


def _candidate_center(predicted_center: float, reference_center: float, attempt_index: int) -> tuple[float, bool]:
    predicted_center = float(predicted_center)
    reference_center = float(reference_center)
    if attempt_index <= 0:
        return predicted_center, False
    alpha = min(1.0, 0.45 * attempt_index)
    center = float((1.0 - alpha) * predicted_center + alpha * reference_center)
    return center, True


def _attempt_bridge(
    *,
    p: int,
    q: int,
    label: str,
    attempt_index: int,
    predictor_method: str,
    predicted_center: float,
    crossing_half_width: float,
    reference_center: float,
    band_offset_lo: float,
    band_offset_hi: float,
    family: HarmonicFamily,
    target_residue: float,
    auto_localize_crossing: bool,
    initial_subdivisions: int,
    max_depth: int,
    min_width: float,
) -> AdaptiveCampaignAttempt:
    center, blended = _candidate_center(predicted_center, reference_center, attempt_index)
    crossing_lo = float(center - crossing_half_width)
    crossing_hi = float(center + crossing_half_width)
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
    ).to_dict()
    crossing = dict(rep.get('crossing_certificate', {}))
    root_lo = crossing.get('certified_root_window_lo')
    root_hi = crossing.get('certified_root_window_hi')
    root_center = _center_from_root_window(root_lo, root_hi)
    return AdaptiveCampaignAttempt(
        p=int(p),
        q=int(q),
        label=str(label),
        attempt_index=int(attempt_index),
        predictor_method=str(predictor_method),
        predicted_center=float(center),
        crossing_half_width=float(crossing_half_width),
        crossing_window_lo=crossing_lo,
        crossing_window_hi=crossing_hi,
        reference_center=float(reference_center),
        bridge_status=str(rep.get('status', 'unknown')),
        crossing_certification_tier=str(crossing.get('certification_tier', crossing.get('status', 'unknown'))),
        crossing_root_window_lo=None if root_lo is None else float(root_lo),
        crossing_root_window_hi=None if root_hi is None else float(root_hi),
        crossing_root_center=None if root_center is None else float(root_center),
        first_supercritical_gap=None if rep.get('first_supercritical_gap') is None else float(rep['first_supercritical_gap']),
        used_reference_blend=bool(blended),
        report=rep,
    )


def _attempt_succeeded(attempt: AdaptiveCampaignAttempt) -> bool:
    return attempt.crossing_root_window_lo is not None and attempt.crossing_root_window_hi is not None


def build_adaptive_class_campaign(
    spec: ArithmeticClassSpec,
    *,
    reference_lower_bound: float,
    reference_crossing_center: float,
    family: HarmonicFamily | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = True,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    initial_crossing_half_width: float = 2.5e-3,
    widening_factor: float = 1.75,
    max_attempts_per_approximant: int = 3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    predictor_mode: str = 'q^-2-fit',
) -> AdaptiveClassCampaignReport:
    family = family or HarmonicFamily()
    ladder = build_class_ladder_report(
        spec,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
    ).to_dict()
    approximants = sorted(list(ladder.get('approximants', [])), key=lambda a: (int(a.get('q', 0)), int(a.get('order_index', 0))))

    history: list[dict[str, float]] = []
    entries: list[dict[str, Any]] = []
    crossing_los: list[float] = []
    crossing_his: list[float] = []
    certified_crossing_count = 0
    certified_band_bridge_count = 0
    failed_count = 0

    for appr in approximants:
        p = int(appr['p'])
        q = int(appr['q'])
        label = str(appr.get('label', f'{p}/{q}'))
        predicted_center, predictor_method = _prediction_from_history(history, q=q, fallback_center=reference_crossing_center)

        attempts: list[dict[str, Any]] = []
        accepted: AdaptiveCampaignAttempt | None = None
        for attempt_index in range(max_attempts_per_approximant):
            width = float(initial_crossing_half_width * (widening_factor ** attempt_index))
            attempt = _attempt_bridge(
                p=p,
                q=q,
                label=label,
                attempt_index=attempt_index,
                predictor_method=predictor_method,
                predicted_center=predicted_center,
                crossing_half_width=width,
                reference_center=reference_crossing_center,
                band_offset_lo=band_offset_lo,
                band_offset_hi=band_offset_hi,
                family=family,
                target_residue=target_residue,
                auto_localize_crossing=auto_localize_crossing,
                initial_subdivisions=initial_subdivisions,
                max_depth=max_depth,
                min_width=min_width,
            )
            attempts.append(attempt.to_dict())
            if _attempt_succeeded(attempt):
                accepted = attempt
                break

        if accepted is not None:
            center = float(accepted.crossing_root_center)
            history.append({'q': float(q), 'center': center})
            crossing_los.append(float(accepted.crossing_root_window_lo))
            crossing_his.append(float(accepted.crossing_root_window_hi))
            certified_crossing_count += 1
            if accepted.bridge_status == 'crossing-plus-band':
                certified_band_bridge_count += 1
            final_status = str(accepted.bridge_status)
            threshold_lo = float(accepted.crossing_root_window_lo)
            threshold_hi = float(accepted.crossing_root_window_hi)
            accepted_idx = int(accepted.attempt_index)
            accepted_method = str(accepted.predictor_method)
            accepted_center = float(accepted.predicted_center)
            final_center = float(accepted.crossing_root_center)
            final_gap = None if accepted.first_supercritical_gap is None else float(accepted.first_supercritical_gap)
            notes = 'Accepted on an adaptive window chosen from successful-history prediction and widening-on-failure.'
        else:
            failed_count += 1
            final_status = 'failed-to-certify-crossing'
            threshold_lo = None
            threshold_hi = None
            accepted_idx = None
            accepted_method = None
            accepted_center = None
            final_center = None
            final_gap = None
            notes = 'No local crossing certificate closed within the attempted adaptive windows.'

        entries.append(
            AdaptiveApproximantCampaignEntry(
                p=p,
                q=q,
                label=label,
                order_index=int(appr.get('order_index', 0)),
                rho_error=float(appr.get('rho_error', float('nan'))),
                final_status=final_status,
                attempts=attempts,
                accepted_attempt_index=accepted_idx,
                accepted_predictor_method=accepted_method,
                accepted_center=accepted_center,
                final_crossing_root_window_lo=threshold_lo,
                final_crossing_root_window_hi=threshold_hi,
                final_crossing_root_center=final_center,
                final_supercritical_gap=final_gap,
                threshold_lower_bound=threshold_lo,
                threshold_upper_bound=threshold_hi,
                notes=notes,
            ).to_dict()
        )

    challengers = [
        ChallengerSpec(
            preperiod=tuple(spec.preperiod),
            period=tuple(spec.period),
            threshold_lower_bound=e.get('threshold_lower_bound'),
            threshold_upper_bound=e.get('threshold_upper_bound'),
            label=str(e.get('label')),
        )
        for e in entries
    ]
    pruning = build_challenger_pruning_report(challengers, golden_lower_bound=reference_lower_bound).to_dict()

    env_lo = min(crossing_los) if crossing_los else None
    env_hi = max(crossing_his) if crossing_his else None
    env_width = None if env_lo is None or env_hi is None else float(env_hi - env_lo)
    if certified_crossing_count == len(entries) and entries:
        status = 'fully-adaptive-certified-campaign'
    elif certified_crossing_count > 0:
        status = 'partially-adaptive-certified-campaign'
    else:
        status = 'adaptive-campaign-needs-manual-followup'

    notes = (
        'Adaptive campaign windows are policy objects rather than theorems: successful approximants seed later windows through a conservative '
        'q^-2 predictor and widening-on-failure fallback, while every accepted result still comes from the local certified bridge routines.'
    )
    return AdaptiveClassCampaignReport(
        class_label=spec.normalized_label(),
        ladder=ladder,
        reference_crossing_center=float(reference_crossing_center),
        reference_lower_bound=float(reference_lower_bound),
        predictor_mode=str(predictor_mode),
        initial_crossing_half_width=float(initial_crossing_half_width),
        widening_factor=float(widening_factor),
        max_attempts_per_approximant=int(max_attempts_per_approximant),
        entries=entries,
        certified_crossing_count=int(certified_crossing_count),
        certified_band_bridge_count=int(certified_band_bridge_count),
        failed_entry_count=int(failed_count),
        crossing_envelope_lo=None if env_lo is None else float(env_lo),
        crossing_envelope_hi=None if env_hi is None else float(env_hi),
        crossing_envelope_width=None if env_width is None else float(env_width),
        predictor_history=[{'q': float(h['q']), 'center': float(h['center'])} for h in history],
        pruning_against_reference=pruning,
        status=status,
        notes=notes,
    )


def build_adaptive_multi_class_campaign(
    classes: Sequence[ArithmeticClassSpec],
    *,
    reference_label: str,
    reference_lower_bound: float,
    reference_crossing_center: float,
    family: HarmonicFamily | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = True,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    initial_crossing_half_width: float = 2.5e-3,
    widening_factor: float = 1.75,
    max_attempts_per_approximant: int = 3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    predictor_mode: str = 'q^-2-fit',
) -> AdaptiveMultiClassCampaignReport:
    family = family or HarmonicFamily()
    class_reports: list[dict[str, Any]] = []
    dominated: list[str] = []
    overlapping: list[str] = []
    undecided: list[str] = []

    for spec in classes:
        rep = build_adaptive_class_campaign(
            spec,
            reference_lower_bound=reference_lower_bound,
            reference_crossing_center=reference_crossing_center,
            family=family,
            target_residue=target_residue,
            auto_localize_crossing=auto_localize_crossing,
            initial_subdivisions=initial_subdivisions,
            max_depth=max_depth,
            min_width=min_width,
            max_q=max_q,
            n_terms=n_terms,
            q_min=q_min,
            keep_last=keep_last,
            initial_crossing_half_width=initial_crossing_half_width,
            widening_factor=widening_factor,
            max_attempts_per_approximant=max_attempts_per_approximant,
            band_offset_lo=band_offset_lo,
            band_offset_hi=band_offset_hi,
            predictor_mode=predictor_mode,
        ).to_dict()
        class_reports.append(rep)
        pruning = rep.get('pruning_against_reference', {})
        label = str(rep.get('class_label'))
        if pruning.get('dominated_count', 0) > 0 and pruning.get('overlapping_count', 0) == 0:
            dominated.append(label)
        elif pruning.get('overlapping_count', 0) > 0:
            overlapping.append(label)
        else:
            undecided.append(label)

    notes = (
        'This multi-class adaptive campaign scales the new predictor-driven workflow across several arithmetic classes. '
        'It remains a campaign/exhaustion scaffold rather than a final irrational challenger theorem.'
    )
    return AdaptiveMultiClassCampaignReport(
        reference_label=str(reference_label),
        reference_lower_bound=float(reference_lower_bound),
        predictor_mode=str(predictor_mode),
        class_campaigns=class_reports,
        dominated_classes=dominated,
        overlapping_classes=overlapping,
        undecided_classes=undecided,
        notes=notes,
    )


__all__ = [
    'AdaptiveCampaignAttempt',
    'AdaptiveApproximantCampaignEntry',
    'AdaptiveClassCampaignReport',
    'AdaptiveMultiClassCampaignReport',
    'build_adaptive_class_campaign',
    'build_adaptive_multi_class_campaign',
]
