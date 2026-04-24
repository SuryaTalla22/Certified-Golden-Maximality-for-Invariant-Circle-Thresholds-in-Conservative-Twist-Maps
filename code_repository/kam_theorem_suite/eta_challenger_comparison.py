from __future__ import annotations

"""Near-top multi-class ``(eta, Lambda)`` challenger comparison scaffold.

This module is the next proof-facing move after the stage-28 single-anchor
``eta`` comparison layer.  The existing code can already package one localized
``(eta, threshold)`` anchor and compare it against an exploratory finite panel.
What it still lacked was a structured way to attach *several* near-top
challenger classes to that same axis and ask:

* which challengers already sit below the golden lower anchor,
* which challengers still overlap the golden anchor window,
* which challengers are only arithmetically separated so far, and
* what the current near-top proto-envelope looks like when the classes are
  sorted by their arithmetic ``eta`` location.

This remains a theorem-facing scaffold.  It does **not** prove Theorem VI or
Theorem VII.  Its value is that it turns the current single-anchor pipeline
into a reproducible multi-class comparison layer that can consume:

* a validated golden ``(eta, threshold)`` anchor,
* challenger classes specified arithmetically,
* explicit challenger threshold intervals when they exist, and/or
* automated multi-class campaign reports from the existing atlas/pruning stack.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

import pandas as pd

from .arithmetic import class_label
from .arithmetic_exact import periodic_class_eta_interval
from .class_campaigns import ArithmeticClassSpec
from .envelope import build_eta_statement_mode_certificate, panel_gap_summary
from .eta_comparison import GOLDEN_ENDPOINT_ETA, build_eta_threshold_comparison_certificate


ETA_GOLDEN_TOL = 1e-12
THRESHOLD_GAP_TOL = 1e-12


def _coerce_float(x: Any) -> float | None:
    if x is None:
        return None
    return float(x)


@dataclass(frozen=True)
class EtaChallengerSpec:
    """Specification for a challenger class or precomputed challenger anchor."""

    preperiod: tuple[int, ...] = ()
    period: tuple[int, ...] = ()
    label: str | None = None
    threshold_lower_bound: float | None = None
    threshold_upper_bound: float | None = None
    eta_threshold_certificate: Mapping[str, Any] | None = None
    eta_certificate: Mapping[str, Any] | None = None
    threshold_bridge_certificate: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized_label(self) -> str:
        if self.label:
            return str(self.label)
        if self.period:
            return class_label(period=self.period, preperiod=self.preperiod)
        return 'challenger'


@dataclass
class EtaChallengerRecord:
    label: str
    preperiod: tuple[int, ...]
    period: tuple[int, ...]
    rho: float | None
    eta_source: str
    eta_certificate: dict[str, Any]
    eta_interval: list[float] | None
    eta_center: float | None
    eta_radius: float | None
    threshold_source: str
    threshold_interval: list[float] | None
    threshold_center: float | None
    threshold_radius: float | None
    threshold_lower_bound: float | None
    threshold_upper_bound: float | None
    comparison_to_golden: dict[str, Any]
    status: str
    reason: str
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NearTopEtaChallengerComparisonCertificate:
    family_label: str
    golden_anchor_certificate: dict[str, Any]
    challenger_records: list[dict[str, Any]]
    panel_records: list[dict[str, Any]]
    exploratory_panel_summary: dict[str, Any]
    statement_mode_certificate: dict[str, Any]
    challenger_ceiling_decomposition_certificate: dict[str, Any]
    global_nongolden_ceiling_certificate: dict[str, Any]
    near_top_relation: dict[str, Any]
    theorem_flags: dict[str, bool]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CampaignDrivenEtaChallengerComparisonCertificate:
    family_label: str
    source_campaign_report: dict[str, Any]
    near_top_certificate: dict[str, Any]
    theorem_flags: dict[str, bool]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _extract_eta_interval(data: Mapping[str, Any]) -> tuple[list[float] | None, float | None, float | None]:
    lo = _coerce_float(data.get('eta_lo'))
    hi = _coerce_float(data.get('eta_hi'))
    ctr = _coerce_float(data.get('eta_center'))
    if ctr is None and lo is not None and hi is not None:
        ctr = 0.5 * (lo + hi)
    if lo is None or hi is None:
        return None, ctr, None
    return [float(lo), float(hi)], float(ctr), float(0.5 * (hi - lo)) if ctr is not None else float(0.5 * (hi - lo))


def _extract_threshold_interval(data: Mapping[str, Any]) -> tuple[list[float] | None, float | None, float | None, float | None, float | None]:
    interval = data.get('threshold_interval')
    if interval is not None:
        lo = float(interval[0])
        hi = float(interval[1])
        ctr = 0.5 * (lo + hi)
        rad = 0.5 * (hi - lo)
        return [lo, hi], ctr, rad, lo, hi

    vwin = data.get('validated_window')
    if vwin is not None:
        lo = float(vwin[0])
        hi = float(vwin[1])
        ctr = 0.5 * (lo + hi)
        rad = 0.5 * (hi - lo)
        return [lo, hi], ctr, rad, lo, hi

    lo = _coerce_float(data.get('threshold_lower_bound'))
    hi = _coerce_float(data.get('threshold_upper_bound'))
    if lo is not None and hi is not None:
        ctr = 0.5 * (lo + hi)
        rad = 0.5 * (hi - lo)
        return [float(lo), float(hi)], float(ctr), float(rad), float(lo), float(hi)
    if lo is not None:
        return [float(lo), float(lo)], float(lo), 0.0, float(lo), float(lo)
    if hi is not None:
        return [float(hi), float(hi)], float(hi), 0.0, float(hi), float(hi)
    return None, None, None, None, None


def _sort_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(rec: dict[str, Any]) -> tuple[float, float, float, str]:
        eta_hi = rec.get('eta_interval', [None, None])[1] if rec.get('eta_interval') is not None else None
        upper = rec.get('threshold_upper_bound')
        center = rec.get('eta_center')
        return (
            -1e9 if eta_hi is None else -float(eta_hi),
            -1e9 if upper is None else -float(upper),
            -1e9 if center is None else -float(center),
            str(rec.get('label', '')),
        )
    return sorted(records, key=key)


def build_eta_challenger_record(
    spec: EtaChallengerSpec,
    *,
    golden_lower_bound: float,
    golden_eta_lo: float,
    golden_eta_hi: float,
    dps: int = 160,
    burn_in_cycles: int = 12,
) -> EtaChallengerRecord:
    label = spec.normalized_label()
    provenance: dict[str, Any] = dict(spec.metadata)

    if spec.eta_threshold_certificate is not None:
        payload = dict(spec.eta_threshold_certificate)
        eta_interval = payload.get('eta_interval')
        eta_center = _coerce_float(payload.get('eta_center'))
        eta_radius = _coerce_float(payload.get('eta_radius'))
        if eta_interval is None:
            eta_interval, eta_center, eta_radius = _extract_eta_interval(payload.get('eta_certificate', {}))
        threshold_interval = payload.get('threshold_interval')
        threshold_center = _coerce_float(payload.get('threshold_center'))
        threshold_radius = _coerce_float(payload.get('threshold_radius'))
        thr_lo = None if threshold_interval is None else float(threshold_interval[0])
        thr_hi = None if threshold_interval is None else float(threshold_interval[1])
        if threshold_interval is None:
            threshold_interval, threshold_center, threshold_radius, thr_lo, thr_hi = _extract_threshold_interval(payload)
        eta_source = str(payload.get('eta_source', 'precomputed-eta-threshold-certificate'))
        eta_certificate = dict(payload.get('eta_certificate', {}))
        threshold_source = 'precomputed-eta-threshold-certificate'
        rho = _coerce_float(payload.get('rho'))
        preperiod = tuple(spec.preperiod)
        period = tuple(spec.period)
        provenance['source_payload'] = 'eta-threshold-certificate'
    else:
        if spec.eta_certificate is not None:
            eta_certificate = dict(spec.eta_certificate)
            eta_source = 'precomputed-eta-certificate'
        elif spec.period:
            eta_certificate = periodic_class_eta_interval(
                period=spec.period,
                preperiod=spec.preperiod,
                dps=dps,
                burn_in_cycles=burn_in_cycles,
            )
            eta_source = 'periodic-class-eta-interval'
        else:
            eta_certificate = {'eta_lo': None, 'eta_hi': None, 'eta_center': None, 'rho': None, 'method': 'missing-period-data'}
            eta_source = 'missing-period-data'
        eta_interval, eta_center, eta_radius = _extract_eta_interval(eta_certificate)
        rho = _coerce_float(eta_certificate.get('rho'))
        threshold_payload: dict[str, Any] = {}
        threshold_source = 'explicit-threshold-bounds'
        if spec.threshold_bridge_certificate is not None:
            threshold_payload.update(spec.threshold_bridge_certificate)
            threshold_source = 'precomputed-threshold-bridge-certificate'
        if spec.threshold_lower_bound is not None:
            threshold_payload['threshold_lower_bound'] = float(spec.threshold_lower_bound)
        if spec.threshold_upper_bound is not None:
            threshold_payload['threshold_upper_bound'] = float(spec.threshold_upper_bound)
        threshold_interval, threshold_center, threshold_radius, thr_lo, thr_hi = _extract_threshold_interval(threshold_payload)
        preperiod = tuple(spec.preperiod)
        period = tuple(spec.period)

    eta_lo = None if eta_interval is None else float(eta_interval[0])
    eta_hi = None if eta_interval is None else float(eta_interval[1])
    gap_eta_endpoint = None if eta_hi is None else float(GOLDEN_ENDPOINT_ETA - eta_hi)
    gap_eta_to_golden_hi = None if eta_hi is None else float(golden_eta_hi - eta_hi)
    gap_eta_center = None if eta_center is None else float(((golden_eta_lo + golden_eta_hi) * 0.5) - eta_center)
    threshold_gap_to_golden = None if thr_hi is None else float(golden_lower_bound - thr_hi)

    if thr_hi is not None:
        if thr_hi < golden_lower_bound - THRESHOLD_GAP_TOL:
            status = 'dominated-by-golden-threshold-anchor'
            reason = 'challenger threshold upper bound lies strictly below the trusted golden lower anchor'
        else:
            status = 'overlaps-golden-threshold-anchor'
            reason = 'challenger threshold upper bound still reaches the trusted golden lower anchor'
    elif eta_hi is not None and eta_hi < golden_eta_hi - ETA_GOLDEN_TOL:
        status = 'arithmetic-weaker-only'
        reason = 'challenger eta interval lies strictly below the golden eta endpoint, but no threshold upper bound is attached yet'
    else:
        status = 'undecided'
        reason = 'current eta/threshold data do not yet separate this challenger from the golden anchor'

    comparison = {
        'golden_lower_bound': float(golden_lower_bound),
        'golden_eta_lo': float(golden_eta_lo),
        'golden_eta_hi': float(golden_eta_hi),
        'eta_gap_to_golden_endpoint': gap_eta_endpoint,
        'eta_gap_to_golden_hi': gap_eta_to_golden_hi,
        'eta_center_gap_to_golden_center': gap_eta_center,
        'threshold_gap_to_golden_lower': threshold_gap_to_golden,
        'eta_below_golden': bool(eta_hi is not None and eta_hi < golden_eta_hi - ETA_GOLDEN_TOL),
        'threshold_dominated': bool(threshold_gap_to_golden is not None and threshold_gap_to_golden > THRESHOLD_GAP_TOL),
    }

    return EtaChallengerRecord(
        label=label,
        preperiod=preperiod,
        period=period,
        rho=rho,
        eta_source=eta_source,
        eta_certificate=eta_certificate,
        eta_interval=eta_interval,
        eta_center=eta_center,
        eta_radius=eta_radius,
        threshold_source=threshold_source,
        threshold_interval=threshold_interval,
        threshold_center=threshold_center,
        threshold_radius=threshold_radius,
        threshold_lower_bound=thr_lo,
        threshold_upper_bound=thr_hi,
        comparison_to_golden=comparison,
        status=status,
        reason=reason,
        provenance=provenance,
    )


def build_eta_challenger_record_from_campaign(
    campaign_report: Mapping[str, Any],
    *,
    golden_lower_bound: float,
    golden_eta_lo: float,
    golden_eta_hi: float,
) -> EtaChallengerRecord:
    ladder = dict(campaign_report.get('ladder', {}))
    pruning = dict(campaign_report.get('pruning_against_reference', {}))
    records = list(pruning.get('records', []))
    upper_candidates = [(float(rec['threshold_upper_bound']), str(rec.get('label', ''))) for rec in records if rec.get('threshold_upper_bound') is not None]
    lower_candidates = [(float(rec['threshold_lower_bound']), str(rec.get('label', ''))) for rec in records if rec.get('threshold_lower_bound') is not None]

    thr_hi = None if not upper_candidates else max(upper_candidates, key=lambda t: t[0])[0]
    worst_label = None if not upper_candidates else max(upper_candidates, key=lambda t: t[0])[1]
    thr_lo = None if not lower_candidates else min(lower_candidates, key=lambda t: t[0])[0]

    spec = EtaChallengerSpec(
        preperiod=tuple(ladder.get('preperiod', ())),
        period=tuple(ladder.get('period', ())),
        label=str(campaign_report.get('class_label', 'campaign-class')),
        eta_certificate={
            'rho': ladder.get('rho'),
            'eta_lo': ladder.get('eta_lo'),
            'eta_hi': ladder.get('eta_hi'),
            'eta_center': ladder.get('eta_center'),
            'method': ladder.get('arithmetic_method', 'campaign-ladder'),
        },
        threshold_lower_bound=thr_lo,
        threshold_upper_bound=thr_hi,
        metadata={
            'source_campaign_status': pruning.get('status'),
            'source_campaign_notes': campaign_report.get('notes'),
            'most_dangerous_approximant': worst_label,
            'approximant_record_count': len(records),
            'dominated_count': pruning.get('dominated_count'),
            'overlapping_count': pruning.get('overlapping_count'),
            'arithmetic_only_count': pruning.get('arithmetic_only_count'),
            'undecided_count': pruning.get('undecided_count'),
        },
    )
    rec = build_eta_challenger_record(
        spec,
        golden_lower_bound=golden_lower_bound,
        golden_eta_lo=golden_eta_lo,
        golden_eta_hi=golden_eta_hi,
    )
    rec.threshold_source = 'campaign-atlas-supremum'
    rec.provenance['campaign_label'] = str(campaign_report.get('class_label', 'campaign-class'))
    return rec


def build_near_top_eta_challenger_comparison_certificate(
    challenger_specs: Sequence[EtaChallengerSpec] | None = None,
    *,
    golden_eta_threshold_certificate: Mapping[str, Any] | None = None,
    family=None,
    family_label: str | None = None,
    rho: float | None = None,
    dps: int = 160,
    burn_in_cycles: int = 12,
    max_records: int | None = None,
    **kwargs: Any,
) -> NearTopEtaChallengerComparisonCertificate:
    if golden_eta_threshold_certificate is not None:
        golden = dict(golden_eta_threshold_certificate)
    else:
        golden = build_eta_threshold_comparison_certificate(
            family=family,
            family_label=family_label,
            rho=rho,
            dps=dps,
            burn_in_cycles=burn_in_cycles,
            **kwargs,
        ).to_dict()

    family_label = str(family_label or golden.get('family_label', 'harmonic_family'))
    golden_anchor = dict(golden.get('local_envelope_anchor', {}))
    golden_eta_interval = golden.get('eta_interval')
    golden_threshold_interval = golden.get('threshold_interval')
    golden_eta_lo = None if golden_eta_interval is None else float(golden_eta_interval[0])
    golden_eta_hi = None if golden_eta_interval is None else float(golden_eta_interval[1])
    golden_lower = None if golden_threshold_interval is None else float(golden_threshold_interval[0])
    golden_upper = None if golden_threshold_interval is None else float(golden_threshold_interval[1])

    records: list[dict[str, Any]] = []
    for spec in challenger_specs or ():
        if golden_lower is None or golden_eta_lo is None or golden_eta_hi is None:
            rec = EtaChallengerRecord(
                label=spec.normalized_label(),
                preperiod=tuple(spec.preperiod),
                period=tuple(spec.period),
                rho=None,
                eta_source='unavailable-because-golden-anchor-missing',
                eta_certificate={},
                eta_interval=None,
                eta_center=None,
                eta_radius=None,
                threshold_source='unavailable-because-golden-anchor-missing',
                threshold_interval=None,
                threshold_center=None,
                threshold_radius=None,
                threshold_lower_bound=None,
                threshold_upper_bound=None,
                comparison_to_golden={},
                status='unavailable',
                reason='golden anchor is incomplete, so challenger comparison cannot be formed',
                provenance=dict(spec.metadata),
            )
        else:
            rec = build_eta_challenger_record(
                spec,
                golden_lower_bound=golden_lower,
                golden_eta_lo=golden_eta_lo,
                golden_eta_hi=golden_eta_hi,
                dps=dps,
                burn_in_cycles=burn_in_cycles,
            )
        records.append(rec.to_dict())

    records = _sort_records(records)
    if max_records is not None and max_records > 0:
        records = records[: int(max_records)]

    panel_records: list[dict[str, Any]] = []
    if golden_eta_interval is not None and golden_threshold_interval is not None:
        panel_records.append(
            {
                'label': 'golden-anchor',
                'eta_approx': float(0.5 * (golden_eta_interval[0] + golden_eta_interval[1])),
                'threshold_lo': float(golden_threshold_interval[0]),
                'threshold_hi': float(golden_threshold_interval[1]),
                'is_golden': True,
            }
        )
    for rec in records:
        if rec.get('eta_center') is None or rec.get('threshold_upper_bound') is None:
            continue
        lo = rec.get('threshold_lower_bound')
        hi = rec.get('threshold_upper_bound')
        panel_records.append(
            {
                'label': rec['label'],
                'eta_approx': float(rec['eta_center']),
                'threshold_lo': float(hi if lo is None else lo),
                'threshold_hi': float(hi),
                'is_golden': False,
            }
        )

    if len(panel_records) >= 2 and any(not row['is_golden'] for row in panel_records):
        try:
            panel_summary = {'available': True, 'summary': panel_gap_summary(pd.DataFrame(panel_records)), 'panel_records': panel_records}
        except Exception as exc:  # pragma: no cover - defensive fallback
            panel_summary = {'available': False, 'summary': {}, 'panel_records': panel_records, 'error': str(exc)}
    else:
        panel_summary = {'available': False, 'summary': {}, 'panel_records': panel_records}

    dominated = [r['label'] for r in records if r['status'] == 'dominated-by-golden-threshold-anchor']
    overlapping = [r['label'] for r in records if r['status'] == 'overlaps-golden-threshold-anchor']
    arithmetic_only = [r['label'] for r in records if r['status'] == 'arithmetic-weaker-only']
    undecided = [r['label'] for r in records if r['status'] == 'undecided']

    most_dangerous_upper = None
    most_dangerous_label = None
    for rec in records:
        upper = rec.get('threshold_upper_bound')
        if upper is None:
            continue
        if most_dangerous_upper is None or float(upper) > most_dangerous_upper:
            most_dangerous_upper = float(upper)
            most_dangerous_label = str(rec['label'])

    eta_nearest_gap = None
    eta_nearest_label = None
    eta_nearest_hi = None
    for rec in records:
        interval = rec.get('eta_interval')
        if interval is None:
            continue
        hi = float(interval[1])
        if eta_nearest_hi is None or hi > eta_nearest_hi:
            eta_nearest_hi = hi
            eta_nearest_gap = float(GOLDEN_ENDPOINT_ETA - hi)
            eta_nearest_label = str(rec['label'])

    panel_gap = _coerce_float(panel_summary.get('summary', {}).get('raw_gap'))
    anchor_gap_against_nongolden = None if golden_lower is None or most_dangerous_upper is None else float(golden_lower - most_dangerous_upper)

    statement_mode_certificate = build_eta_statement_mode_certificate(
        panel_records,
        top_gap_scale=anchor_gap_against_nongolden if anchor_gap_against_nongolden is not None else panel_gap,
    )

    threshold_bounded_records = [rec for rec in records if rec.get('threshold_upper_bound') is not None]
    arithmetic_only_without_threshold = [rec['label'] for rec in records if rec['status'] == 'arithmetic-weaker-only' and rec.get('threshold_upper_bound') is None]
    overlapping_threshold_records = [rec for rec in records if rec['label'] in overlapping and rec.get('threshold_upper_bound') is not None]
    undecided_threshold_records = [rec for rec in records if rec['label'] in undecided and rec.get('threshold_upper_bound') is not None]
    overlapping_upper = None if not overlapping_threshold_records else max(float(rec['threshold_upper_bound']) for rec in overlapping_threshold_records)
    undecided_upper = None if not undecided_threshold_records else max(float(rec['threshold_upper_bound']) for rec in undecided_threshold_records)
    explicit_panel_upper_ceiling = None if not threshold_bounded_records else max(float(rec['threshold_upper_bound']) for rec in threshold_bounded_records)
    global_upper_candidates = [x for x in (explicit_panel_upper_ceiling, overlapping_upper, undecided_upper) if x is not None]
    global_nongolden_upper_ceiling = None if not global_upper_candidates else float(max(global_upper_candidates))
    global_margin = None if global_nongolden_upper_ceiling is None or golden_lower is None else float(golden_lower - global_nongolden_upper_ceiling)
    tail_control_available = len(arithmetic_only_without_threshold) == 0 and len(overlapping) == 0 and len(undecided) == 0
    if global_nongolden_upper_ceiling is None:
        global_ceiling_status = 'global-ceiling-unavailable'
    elif tail_control_available:
        global_ceiling_status = 'global-ceiling-strong'
    else:
        global_ceiling_status = 'global-ceiling-partial'

    challenger_ceiling_decomposition_certificate = {
        'explicit_panel_upper_ceiling': explicit_panel_upper_ceiling,
        'overlapping_upper_ceiling': overlapping_upper,
        'undecided_upper_ceiling': undecided_upper,
        'arithmetic_only_without_threshold_labels': arithmetic_only_without_threshold,
        'global_nongolden_upper_ceiling': global_nongolden_upper_ceiling,
        'ceiling_attained_by': most_dangerous_label,
        'dominance_partition_complete': len(overlapping) == 0 and len(undecided) == 0,
        'all_near_top_classes_accounted_for': len(records) == len(dominated) + len(overlapping) + len(arithmetic_only) + len(undecided),
        'tail_control_available': tail_control_available,
        'tail_control_margin': global_margin,
        'global_ceiling_status': global_ceiling_status,
    }
    global_nongolden_ceiling_certificate = {
        'global_nongolden_upper_ceiling': global_nongolden_upper_ceiling,
        'golden_lower_witness': golden_lower,
        'global_gap_margin': global_margin,
        'global_ceiling_status': global_ceiling_status,
        'tail_control_available': tail_control_available,
        'global_ceiling_theorem_certified': bool(
            global_ceiling_status == 'global-ceiling-strong'
            and global_margin is not None
            and global_margin > 0.0
            and golden_eta_interval is not None
            and golden_threshold_interval is not None
        ),
        'remaining_burden': (
            'none' if global_ceiling_status == 'global-ceiling-strong' else
            'finish the omitted-class / overlapping-class ceiling control so the nongolden ceiling becomes genuinely global'
        ),
    }

    relation = {
        'golden_eta_interval': None if golden_eta_interval is None else [float(golden_eta_interval[0]), float(golden_eta_interval[1])],
        'golden_threshold_interval': None if golden_threshold_interval is None else [float(golden_threshold_interval[0]), float(golden_threshold_interval[1])],
        'dominated_labels': dominated,
        'overlapping_labels': overlapping,
        'arithmetic_only_labels': arithmetic_only,
        'undecided_labels': undecided,
        'most_dangerous_threshold_upper': most_dangerous_upper,
        'most_dangerous_threshold_label': most_dangerous_label,
        'golden_lower_minus_most_dangerous_upper': anchor_gap_against_nongolden,
        'eta_nearest_challenger_label': eta_nearest_label,
        'eta_nearest_challenger_hi': eta_nearest_hi,
        'golden_endpoint_minus_eta_nearest_challenger': eta_nearest_gap,
        'panel_gap': panel_gap,
        'challenger_count': len(records),
    }

    flags = {
        'golden_anchor_available': bool(str(golden.get('theorem_status', '')).startswith('eta-threshold-comparison-')) and golden_eta_interval is not None and golden_threshold_interval is not None,
        'challenger_records_available': bool(records),
        'at_least_one_threshold_bounded_challenger': bool(any(r.get('threshold_upper_bound') is not None for r in records)),
        'all_threshold_bounded_challengers_dominated': bool(records) and all(r['status'] != 'overlaps-golden-threshold-anchor' for r in records if r.get('threshold_upper_bound') is not None),
        'no_undecided_challengers': len(undecided) == 0,
        'panel_gap_positive': bool(panel_gap is not None and panel_gap > 0.0),
    }

    if flags['golden_anchor_available'] and flags['challenger_records_available'] and flags['at_least_one_threshold_bounded_challenger'] and flags['all_threshold_bounded_challengers_dominated'] and flags['no_undecided_challengers']:
        status = 'near-top-eta-challenger-comparison-strong'
        notes = 'The current golden eta-threshold anchor has been lifted to a multi-class near-top comparison in which every threshold-bounded challenger is dominated and the remaining classes are only arithmetically weaker.'
    elif flags['golden_anchor_available'] and flags['challenger_records_available'] and flags['at_least_one_threshold_bounded_challenger']:
        status = 'near-top-eta-challenger-comparison-moderate'
        notes = 'A genuine multi-class eta-threshold challenger surface now exists, but at least one near-top challenger still overlaps the golden anchor or remains unresolved.'
    elif flags['golden_anchor_available'] and flags['challenger_records_available']:
        status = 'near-top-eta-challenger-comparison-weak'
        notes = 'The challenger classes are organized on the eta axis relative to the golden anchor, but threshold-side domination remains mostly unavailable.'
    elif flags['golden_anchor_available']:
        status = 'near-top-eta-challenger-comparison-seed-only'
        notes = 'The golden eta-threshold anchor is available, but no challenger records were supplied.'
    else:
        status = 'near-top-eta-challenger-comparison-unavailable'
        notes = 'The golden eta-threshold anchor is not available, so the multi-class comparison cannot yet be formed.'

    return NearTopEtaChallengerComparisonCertificate(
        family_label=family_label,
        golden_anchor_certificate=golden,
        challenger_records=records,
        panel_records=panel_records,
        exploratory_panel_summary=panel_summary,
        statement_mode_certificate=statement_mode_certificate,
        challenger_ceiling_decomposition_certificate=challenger_ceiling_decomposition_certificate,
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
        near_top_relation=relation,
        theorem_flags=flags,
        theorem_status=status,
        notes=notes,
    )


def build_campaign_driven_eta_challenger_comparison_certificate(
    multi_class_campaign_report: Mapping[str, Any],
    *,
    golden_eta_threshold_certificate: Mapping[str, Any],
    family_label: str | None = None,
    max_records: int | None = None,
) -> CampaignDrivenEtaChallengerComparisonCertificate:
    campaign = dict(multi_class_campaign_report)
    golden = dict(golden_eta_threshold_certificate)
    golden_eta_interval = golden.get('eta_interval')
    golden_threshold_interval = golden.get('threshold_interval')
    if golden_eta_interval is None or golden_threshold_interval is None:
        near = build_near_top_eta_challenger_comparison_certificate(
            challenger_specs=[],
            golden_eta_threshold_certificate=golden,
            family_label=family_label,
        ).to_dict()
        status = 'campaign-driven-eta-challenger-comparison-unavailable'
        notes = 'The source campaign report is present, but the golden eta-threshold anchor is incomplete.'
        flags = {'campaign_report_available': True, 'golden_anchor_available': False, 'campaign_classes_lifted': False}
        return CampaignDrivenEtaChallengerComparisonCertificate(
            family_label=str(family_label or golden.get('family_label', 'harmonic_family')),
            source_campaign_report=campaign,
            near_top_certificate=near,
            theorem_flags=flags,
            theorem_status=status,
            notes=notes,
        )

    golden_eta_lo = float(golden_eta_interval[0])
    golden_eta_hi = float(golden_eta_interval[1])
    golden_lower = float(golden_threshold_interval[0])
    records = [
        build_eta_challenger_record_from_campaign(
            rep,
            golden_lower_bound=golden_lower,
            golden_eta_lo=golden_eta_lo,
            golden_eta_hi=golden_eta_hi,
        )
        for rep in campaign.get('class_campaigns', [])
    ]
    specs = [
        EtaChallengerSpec(
            preperiod=tuple(rec.preperiod),
            period=tuple(rec.period),
            label=rec.label,
            eta_certificate=rec.eta_certificate,
            threshold_lower_bound=rec.threshold_lower_bound,
            threshold_upper_bound=rec.threshold_upper_bound,
            metadata=rec.provenance,
        )
        for rec in records
    ]
    near = build_near_top_eta_challenger_comparison_certificate(
        specs,
        golden_eta_threshold_certificate=golden,
        family_label=family_label or golden.get('family_label'),
        max_records=max_records,
    ).to_dict()

    flags = {
        'campaign_report_available': True,
        'golden_anchor_available': True,
        'campaign_classes_lifted': bool(records),
        'campaign_contains_overlapping_classes': bool(campaign.get('overlapping_classes')),
    }
    if near['theorem_status'].startswith('near-top-eta-challenger-comparison-strong'):
        status = 'campaign-driven-eta-challenger-comparison-strong'
        notes = 'The existing multi-class campaign has been lifted onto the eta-threshold axis and currently supports a clean dominated-vs-arithmetic-only split against the golden anchor.'
    elif near['theorem_status'].startswith('near-top-eta-challenger-comparison-'):
        status = 'campaign-driven-eta-challenger-comparison-moderate'
        notes = 'The existing multi-class campaign now feeds a near-top eta-threshold comparison layer, but at least one campaign class still overlaps or remains unresolved.'
    else:
        status = 'campaign-driven-eta-challenger-comparison-unavailable'
        notes = 'The source campaign exists, but it could not be lifted into a usable eta-threshold challenger surface.'

    return CampaignDrivenEtaChallengerComparisonCertificate(
        family_label=str(family_label or golden.get('family_label', 'harmonic_family')),
        source_campaign_report=campaign,
        near_top_certificate=near,
        theorem_flags=flags,
        theorem_status=status,
        notes=notes,
    )


__all__ = [
    'EtaChallengerSpec',
    'EtaChallengerRecord',
    'NearTopEtaChallengerComparisonCertificate',
    'CampaignDrivenEtaChallengerComparisonCertificate',
    'build_eta_challenger_record',
    'build_eta_challenger_record_from_campaign',
    'build_near_top_eta_challenger_comparison_certificate',
    'build_campaign_driven_eta_challenger_comparison_certificate',
]
