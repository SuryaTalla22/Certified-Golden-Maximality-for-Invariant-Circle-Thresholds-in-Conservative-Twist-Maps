from __future__ import annotations

r"""Proto-envelope / compatibility-to-eta comparison scaffold.

This module is the first explicit bridge from the stage-27 threshold-compatibility
window to the eventual Theorem VI arithmetic-comparison layer.  It does **not**
prove a monotone envelope theorem in :math:`\eta`.  Instead, it packages the
current localized threshold-compatibility window as a local ``(eta, Lambda)``
anchor and, when exploratory panel data are supplied, compares that anchor to a
conservative isotonic envelope built from the existing finite panel.

The design goal is to let the codebase say:

* here is the current threshold-side compatibility window,
* here is the arithmetic ``eta`` window attached to the current class, and
* here is how that local anchor sits relative to the current exploratory
  envelope/panel gap diagnostics.

This remains a theorem-facing scaffold rather than a proof of Theorem VI.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

from .arithmetic_exact import known_constant_type_eta, periodic_class_eta_interval
from .envelope import (
    build_eta_statement_mode_certificate,
    conservative_eta_envelope,
    isotonic_regression,
    panel_gap_summary,
)
from .threshold_compatibility import build_validated_threshold_compatibility_bridge_certificate
from .chart_threshold_linkage import golden_inverse
from .standard_map import HarmonicFamily


GOLDEN_ENDPOINT_ETA = float(known_constant_type_eta(1))


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


def _coerce_float(x: Any) -> float | None:
    if x is None:
        return None
    return float(x)


@dataclass
class EtaThresholdComparisonCertificate:
    rho: float
    family_label: str
    compatibility_bridge_certificate: dict[str, Any]
    eta_source: str
    eta_certificate: dict[str, Any]
    eta_interval: list[float] | None
    eta_center: float | None
    eta_radius: float | None
    threshold_interval: list[float] | None
    threshold_center: float | None
    threshold_radius: float | None
    arithmetic_endpoint: dict[str, float]
    local_envelope_anchor: dict[str, Any]
    eta_relation: dict[str, Any]
    theorem_flags: dict[str, bool]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProtoEnvelopeEtaBridgeCertificate:
    rho: float
    family_label: str
    eta_threshold_comparison_certificate: dict[str, Any]
    exploratory_panel_summary: dict[str, Any]
    anchor_globalization_certificate: dict[str, Any]
    statement_mode_certificate: dict[str, Any]
    proto_envelope_relation: dict[str, Any]
    theorem_flags: dict[str, bool]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _build_eta_certificate(
    *,
    rho: float,
    eta_certificate: Mapping[str, Any] | None = None,
    period: Sequence[int] | None = None,
    preperiod: Sequence[int] | None = None,
    dps: int = 160,
    burn_in_cycles: int = 12,
) -> tuple[str, dict[str, Any]]:
    if eta_certificate is not None:
        return 'precomputed-eta-certificate', dict(eta_certificate)
    if period is not None:
        return (
            'periodic-class-eta-interval',
            periodic_class_eta_interval(
                period=period,
                preperiod=preperiod,
                dps=dps,
                burn_in_cycles=burn_in_cycles,
            ),
        )
    if abs(float(rho) - float(golden_inverse())) <= 1e-9:
        eta = float(GOLDEN_ENDPOINT_ETA)
        return (
            'exact-golden-endpoint',
            {
                'label': 'golden-endpoint',
                'eta_lo': eta,
                'eta_hi': eta,
                'eta_center': eta,
                'method': 'exact-constant-type',
            },
        )
    return (
        'rho-only-no-eta-interval',
        {
            'label': 'unresolved-arithmetic-class',
            'eta_lo': None,
            'eta_hi': None,
            'eta_center': None,
            'method': 'rho-only',
        },
    )


def build_eta_threshold_comparison_certificate(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    eta_certificate: Mapping[str, Any] | None = None,
    period: Sequence[int] | None = None,
    preperiod: Sequence[int] | None = None,
    threshold_bridge_certificate: Mapping[str, Any] | None = None,
    dps: int = 160,
    burn_in_cycles: int = 12,
    **kwargs: Any,
) -> EtaThresholdComparisonCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    if threshold_bridge_certificate is not None:
        bridge = dict(threshold_bridge_certificate)
    else:
        try:
            bridge = build_validated_threshold_compatibility_bridge_certificate(
                family=family,
                family_label=family_label,
                rho=rho,
                **kwargs,
            ).to_dict()
        except Exception as exc:  # pragma: no cover - defensive fallback for heavy upstream failures
            bridge = {
                'theorem_status': 'validated-threshold-compatibility-bridge-unavailable',
                'validated_window': None,
                'certified_center': None,
                'certified_radius': None,
                'notes': f'upstream compatibility bridge failed: {exc}',
            }

    eta_source, eta_data = _build_eta_certificate(
        rho=rho,
        eta_certificate=eta_certificate,
        period=period,
        preperiod=preperiod,
        dps=dps,
        burn_in_cycles=burn_in_cycles,
    )

    eta_lo = _coerce_float(eta_data.get('eta_lo'))
    eta_hi = _coerce_float(eta_data.get('eta_hi'))
    eta_center = _coerce_float(eta_data.get('eta_center'))
    if eta_center is None and eta_lo is not None and eta_hi is not None:
        eta_center = float(0.5 * (eta_lo + eta_hi))
    eta_interval = None if eta_lo is None or eta_hi is None else [float(eta_lo), float(eta_hi)]
    eta_radius = None if eta_lo is None or eta_hi is None else float(0.5 * (eta_hi - eta_lo))

    thresh_center0 = _coerce_float(bridge.get('certified_center'))
    thresh_radius0 = _coerce_float(bridge.get('certified_radius'))
    validated_window = bridge.get('validated_window')
    if validated_window is not None:
        threshold_interval = [float(validated_window[0]), float(validated_window[1])]
        threshold_center = float(0.5 * (threshold_interval[0] + threshold_interval[1]))
        threshold_radius = float(0.5 * (threshold_interval[1] - threshold_interval[0]))
    elif thresh_center0 is not None:
        threshold_center = float(thresh_center0)
        threshold_radius = None if thresh_radius0 is None else float(thresh_radius0)
        if thresh_radius0 is None:
            threshold_interval = [threshold_center, threshold_center]
        else:
            threshold_interval = [threshold_center - threshold_radius, threshold_center + threshold_radius]
    else:
        threshold_interval = None
        threshold_center = None
        threshold_radius = None

    anchor_lower = None if threshold_interval is None else float(threshold_interval[0])
    anchor_upper = None if threshold_interval is None else float(threshold_interval[1])
    anchor_gap = None
    anchor_width = None
    if anchor_lower is not None and anchor_upper is not None:
        anchor_gap = float(anchor_upper - anchor_lower)
        anchor_width = float(anchor_upper - anchor_lower)

    endpoint_hi = float(GOLDEN_ENDPOINT_ETA)
    endpoint_gap = None if eta_hi is None else float(endpoint_hi - eta_hi)
    endpoint_center_gap = None if eta_center is None else float(endpoint_hi - eta_center)
    threshold_width_per_eta_width = None
    if anchor_width is not None and eta_radius not in (None, 0.0):
        threshold_width_per_eta_width = float(anchor_width / (2.0 * eta_radius))
    threshold_width_relative = None
    if anchor_width is not None and threshold_center not in (None, 0.0):
        threshold_width_relative = float(anchor_width / abs(threshold_center))

    eta_relation = {
        'eta_lo': eta_lo,
        'eta_hi': eta_hi,
        'eta_center': eta_center,
        'eta_radius': eta_radius,
        'golden_endpoint_eta': endpoint_hi,
        'eta_gap_to_golden_endpoint': endpoint_gap,
        'eta_center_gap_to_golden_endpoint': endpoint_center_gap,
        'threshold_width_per_eta_width': threshold_width_per_eta_width,
        'threshold_width_relative': threshold_width_relative,
        'threshold_interval_lo': None if threshold_interval is None else float(threshold_interval[0]),
        'threshold_interval_hi': None if threshold_interval is None else float(threshold_interval[1]),
        'threshold_interval_width': anchor_width,
    }
    local_anchor = {
        'eta_interval_lo': eta_lo,
        'eta_interval_hi': eta_hi,
        'eta_center': eta_center,
        'threshold_lower': anchor_lower,
        'threshold_upper': anchor_upper,
        'threshold_center': threshold_center,
        'threshold_gap': anchor_gap,
        'threshold_width': anchor_width,
    }

    flags = {
        'threshold_bridge_available': bool(str(bridge.get('theorem_status', '')).startswith('validated-threshold-compatibility-bridge-')),
        'eta_interval_available': bool(eta_interval is not None),
        'eta_anchor_inside_arithmetic_domain': bool(eta_lo is not None and eta_hi is not None and eta_lo >= -1e-15 and eta_hi <= endpoint_hi + 1e-15),
        'local_envelope_anchor_well_defined': bool(anchor_lower is not None and anchor_upper is not None and anchor_upper >= anchor_lower),
        'positive_threshold_gap': bool(anchor_gap is not None and anchor_gap >= 0.0),
        'golden_endpoint_anchor': bool(endpoint_gap is not None and abs(endpoint_gap) <= 1e-12),
        'subgolden_anchor': bool(endpoint_gap is not None and endpoint_gap > 1e-12),
    }

    strong_ready = (
        flags['threshold_bridge_available']
        and flags['eta_interval_available']
        and flags['eta_anchor_inside_arithmetic_domain']
        and flags['local_envelope_anchor_well_defined']
        and flags['positive_threshold_gap']
        and (flags['golden_endpoint_anchor'] or flags['subgolden_anchor'])
    )

    if strong_ready:
        status = 'eta-threshold-comparison-strong'
        notes = 'The current compatibility window is now packaged as a local (eta, threshold) anchor sitting inside the arithmetic domain and aligned with the golden endpoint.'
    elif flags['threshold_bridge_available'] and flags['eta_interval_available'] and flags['local_envelope_anchor_well_defined']:
        status = 'eta-threshold-comparison-moderate'
        notes = 'The current compatibility window is now expressed as a local (eta, threshold) anchor, but the arithmetic endpoint relation remains only partial.'
    elif flags['threshold_bridge_available']:
        status = 'eta-threshold-comparison-weak'
        notes = 'A threshold-side compatibility bridge is available, but the arithmetic eta anchor remains incomplete.'
    else:
        status = 'eta-threshold-comparison-unavailable'
        notes = 'Neither the threshold-side compatibility bridge nor the arithmetic eta anchor is presently available.'

    return EtaThresholdComparisonCertificate(
        rho=rho,
        family_label=family_label,
        compatibility_bridge_certificate=bridge,
        eta_source=eta_source,
        eta_certificate=eta_data,
        eta_interval=eta_interval,
        eta_center=eta_center,
        eta_radius=eta_radius,
        threshold_interval=threshold_interval,
        threshold_center=threshold_center,
        threshold_radius=threshold_radius,
        arithmetic_endpoint={'eta_star': endpoint_hi, 'eta_domain_lo': 0.0, 'eta_domain_hi': endpoint_hi},
        local_envelope_anchor=local_anchor,
        eta_relation=eta_relation,
        theorem_flags=flags,
        theorem_status=status,
        notes=notes,
    )


def _build_panel_summary(panel_records: Iterable[Mapping[str, Any]] | None) -> dict[str, Any]:
    if panel_records is None:
        return {'available': False, 'summary': {}, 'eta_envelope_rows': [], 'panel_records': [], 'statement_mode_certificate': build_eta_statement_mode_certificate(pd.DataFrame())}
    rows = list(panel_records)
    df = pd.DataFrame(rows)
    if df.empty:
        return {'available': False, 'summary': {}, 'eta_envelope_rows': [], 'panel_records': [], 'statement_mode_certificate': build_eta_statement_mode_certificate(df)}
    env = conservative_eta_envelope(df)
    summary = panel_gap_summary(df)
    statement_mode_certificate = build_eta_statement_mode_certificate(df, top_gap_scale=summary.get('raw_gap'))
    work = df[['eta_approx', 'threshold_lo', 'threshold_hi']].copy()
    work['threshold_center'] = 0.5 * (work['threshold_lo'] + work['threshold_hi'])
    work['eta_bucket'] = work['eta_approx'].astype(float).round(12)
    grouped = work.groupby('eta_bucket', sort=True)
    same_eta_rows = grouped.agg(
        eta_center=('eta_approx', 'mean'),
        threshold_lo_min=('threshold_lo', 'min'),
        threshold_hi_max=('threshold_hi', 'max'),
        count=('eta_approx', 'size'),
    ).reset_index(drop=True)
    same_eta_rows['within_eta_spread'] = same_eta_rows['threshold_hi_max'] - same_eta_rows['threshold_lo_min']
    repeated_eta_buckets = [
        {
            'eta_center': float(row['eta_center']),
            'count': int(row['count']),
            'within_eta_spread': float(row['within_eta_spread']),
        }
        for row in same_eta_rows.to_dict(orient='records')
        if int(row['count']) > 1
    ]
    centers = work.sort_values('eta_approx')['threshold_center'].to_numpy(dtype=float)
    etas = work.sort_values('eta_approx')['eta_approx'].to_numpy(dtype=float)
    iso = isotonic_regression(etas, centers) if len(centers) else []
    monotonicity_defect = None if len(centers) == 0 else float(max(abs(a - b) for a, b in zip(centers, iso)))
    return {
        'available': True,
        'summary': summary,
        'eta_envelope_rows': env.to_dict(orient='records'),
        'panel_records': rows,
        'statement_mode_certificate': statement_mode_certificate,
        'panel_decomposition': {
            'repeated_eta_buckets': repeated_eta_buckets,
            'same_eta_spread_witnesses': same_eta_rows.to_dict(orient='records'),
            'panel_ceiling_witness': {
                'nongolden_max_upper_bound': summary.get('nongolden_max_upper_bound'),
                'golden_lower_bound': summary.get('golden_lower_bound'),
                'raw_gap': summary.get('raw_gap'),
            },
            'monotonicity_defect': monotonicity_defect,
        },
    }


def build_eta_anchor_globalization_certificate(
    eta_threshold_certificate: Mapping[str, Any],
    exploratory_panel_summary: Mapping[str, Any],
) -> dict[str, Any]:
    anchor = dict(eta_threshold_certificate.get('local_envelope_anchor', {}))
    panel_summary = dict(exploratory_panel_summary.get('summary', {}))
    theorem_flags = dict(eta_threshold_certificate.get('theorem_flags', {}))

    anchor_lower = _coerce_float(anchor.get('threshold_lower'))
    anchor_upper = _coerce_float(anchor.get('threshold_upper'))
    anchor_eta_center = _coerce_float(anchor.get('eta_center'))
    nongolden_panel_upper = _coerce_float(panel_summary.get('nongolden_max_upper_bound'))
    anchor_globalization_margin = None if anchor_lower is None or nongolden_panel_upper is None else float(anchor_lower - nongolden_panel_upper)

    transport_locked = bool(theorem_flags.get('threshold_bridge_available', False))
    identification_locked = bool(theorem_flags.get('local_envelope_anchor_well_defined', False))
    panel_available = bool(exploratory_panel_summary.get('available', False))
    panel_gap_positive = bool(_coerce_float(panel_summary.get('raw_gap')) is not None and float(panel_summary.get('raw_gap')) > 0.0)

    if anchor_lower is None or anchor_upper is None or anchor_eta_center is None:
        anchor_scope = 'missing'
        anchor_globalization_status = 'anchor-globalization-unavailable'
        anchor_ready_for_global_envelope = False
        anchor_global_theorem_ready = False
    elif not panel_available:
        anchor_scope = 'local'
        anchor_globalization_status = 'anchor-globalization-local-only'
        anchor_ready_for_global_envelope = identification_locked
        anchor_global_theorem_ready = False
    elif (
        anchor_globalization_margin is not None
        and anchor_globalization_margin > 0.0
        and transport_locked
        and identification_locked
        and panel_gap_positive
    ):
        anchor_scope = 'global-theorem-candidate'
        anchor_globalization_status = 'anchor-globalization-global-certified'
        anchor_ready_for_global_envelope = True
        anchor_global_theorem_ready = True
    elif anchor_globalization_margin is not None and anchor_globalization_margin > 0.0:
        anchor_scope = 'screened-panel'
        anchor_globalization_status = 'anchor-globalization-screened-panel-ready'
        anchor_ready_for_global_envelope = True
        anchor_global_theorem_ready = False
    else:
        anchor_scope = 'screened-panel'
        anchor_globalization_status = 'anchor-globalization-panel-overlap'
        anchor_ready_for_global_envelope = False
        anchor_global_theorem_ready = False

    return {
        'anchor_scope': anchor_scope,
        'anchor_transport_locked': transport_locked,
        'anchor_identification_locked': identification_locked,
        'anchor_ready_for_global_envelope': anchor_ready_for_global_envelope,
        'anchor_global_theorem_ready': anchor_global_theorem_ready,
        'anchor_lower_witness_interval': None if anchor_lower is None or anchor_upper is None else [float(anchor_lower), float(anchor_upper)],
        'anchor_upper_witness_interval': None if anchor_lower is None or anchor_upper is None else [float(anchor_lower), float(anchor_upper)],
        'anchor_mode_compatibility': None if exploratory_panel_summary.get('statement_mode_certificate') is None else str(dict(exploratory_panel_summary.get('statement_mode_certificate', {})).get('candidate_mode', 'unresolved')),
        'anchor_globalization_margin': None if anchor_globalization_margin is None else float(anchor_globalization_margin),
        'anchor_globalization_status': anchor_globalization_status,
    }

def build_proto_envelope_eta_bridge_certificate(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    panel_records: Iterable[Mapping[str, Any]] | None = None,
    eta_threshold_certificate: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ProtoEnvelopeEtaBridgeCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    if eta_threshold_certificate is not None:
        comp = dict(eta_threshold_certificate)
    else:
        comp = build_eta_threshold_comparison_certificate(
            family=family,
            family_label=family_label,
            rho=rho,
            **kwargs,
        ).to_dict()

    panel = _build_panel_summary(panel_records)
    summary = dict(panel.get('summary', {}))
    anchor = dict(comp.get('local_envelope_anchor', {}))

    anchor_lower = _coerce_float(anchor.get('threshold_lower'))
    anchor_upper = _coerce_float(anchor.get('threshold_upper'))
    anchor_eta_center = _coerce_float(anchor.get('eta_center'))

    nongolden_max_upper = _coerce_float(summary.get('nongolden_max_upper_bound'))
    raw_gap = _coerce_float(summary.get('raw_gap'))
    golden_eta = _coerce_float(summary.get('golden_eta'))
    panel_top_gap = None
    if anchor_lower is not None and nongolden_max_upper is not None:
        panel_top_gap = float(anchor_lower - nongolden_max_upper)
    eta_alignment_to_panel_top = None
    if anchor_eta_center is not None and golden_eta is not None:
        eta_alignment_to_panel_top = float(abs(anchor_eta_center - golden_eta))

    relation = {
        'panel_available': bool(panel.get('available', False)),
        'panel_nongolden_max_upper_bound': nongolden_max_upper,
        'panel_raw_gap': raw_gap,
        'anchor_lower_minus_panel_nongolden_upper': panel_top_gap,
        'anchor_eta_center_minus_panel_top_eta': None if anchor_eta_center is None or golden_eta is None else float(anchor_eta_center - golden_eta),
        'anchor_eta_alignment_to_panel_top': eta_alignment_to_panel_top,
        'proto_envelope_lower': anchor_lower,
        'proto_envelope_upper': anchor_upper,
        'proto_envelope_eta_center': anchor_eta_center,
    }

    anchor_globalization_certificate = build_eta_anchor_globalization_certificate(comp, panel)

    flags = {
        'eta_threshold_anchor_available': bool(str(comp.get('theorem_status', '')).startswith('eta-threshold-comparison-')),
        'panel_available': bool(panel.get('available', False)),
        'panel_gap_positive': bool(raw_gap is not None and raw_gap > 0.0),
        'anchor_gap_against_panel_positive': bool(panel_top_gap is not None and panel_top_gap > 0.0),
        'anchor_well_defined': bool(anchor_lower is not None and anchor_upper is not None and anchor_upper >= anchor_lower),
    }

    if flags['eta_threshold_anchor_available'] and flags['panel_available'] and flags['panel_gap_positive'] and flags['anchor_gap_against_panel_positive']:
        status = 'proto-envelope-eta-bridge-strong'
        notes = 'The current eta-threshold anchor now sits above the exploratory nongolden panel ceiling, giving a proto top-gap diagnostic in eta space.'
    elif flags['eta_threshold_anchor_available'] and flags['anchor_well_defined']:
        status = 'proto-envelope-eta-bridge-moderate'
        notes = 'A local eta-threshold anchor is now available and can be compared against exploratory panel envelopes when such data are supplied.'
    elif flags['eta_threshold_anchor_available']:
        status = 'proto-envelope-eta-bridge-weak'
        notes = 'The eta-threshold anchor exists, but the proto-envelope comparison remains only partial.'
    else:
        status = 'proto-envelope-eta-bridge-unavailable'
        notes = 'No eta-threshold anchor is currently available for proto-envelope comparison.'

    statement_mode_certificate = build_eta_statement_mode_certificate(
        panel.get('panel_records', []),
        top_gap_scale=panel_top_gap if panel_top_gap is not None else raw_gap,
    )

    return ProtoEnvelopeEtaBridgeCertificate(
        rho=rho,
        family_label=family_label,
        eta_threshold_comparison_certificate=comp,
        exploratory_panel_summary=panel,
        anchor_globalization_certificate=anchor_globalization_certificate,
        statement_mode_certificate=statement_mode_certificate,
        proto_envelope_relation=relation,
        theorem_flags=flags,
        theorem_status=status,
        notes=notes,
    )
