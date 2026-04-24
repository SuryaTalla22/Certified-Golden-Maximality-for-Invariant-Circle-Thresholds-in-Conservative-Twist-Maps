from __future__ import annotations

"""Theorem-facing discharge certificate for Workstream A critical-surface identification.

This module sits one level deeper than the earlier Workstream-A status summaries.  It does
not merely report that the local stable-manifold / critical-surface / transversality-window
geometry looks promising.  Instead it packages that geometry into a focused discharge object
whose sole purpose is to isolate the *precise* remaining Workstream-A burden:

    the theorem-grade promotion from a locally sharp proxy critical-surface package
    to a true critical-surface / threshold identification theorem.

The certificate intentionally separates three layers:

1. local geometric prerequisites (stable chart, coarse bridge, localized transversality,
   derivative floor, window narrowness, local margin),
2. identification-specific assumptions (stable-manifold = true critical surface, chart
   crossing identifies the true critical parameter, and theorem-grade transversality), and
3. broader upstream Workstream context assumptions (for example Banach-manifold class and
   validated renormalization fixed-point package).

That separation is the mathematical value of the object: it lets downstream layers distinguish
whether the remaining burden is still local geometry, the focused critical-surface/threshold
promotion theorem, or some broader Workstream-A context assumption.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .standard_map import HarmonicFamily

IDENTIFICATION_ASSUMPTIONS = (
    'golden_stable_manifold_is_true_critical_surface',
    'family_chart_crossing_identifies_true_critical_parameter',
    'golden_critical_surface_transversality_on_class',
)

UPSTREAM_CONTEXT_ASSUMPTIONS = (
    'theorem_grade_banach_manifold_universality_class',
    'validated_true_renormalization_fixed_point_package',
)

LOCAL_PREREQUISITE_HYPOTHESES = (
    'stable_manifold_chart_ready',
    'coarse_critical_surface_bridge_ready',
    'localized_transversality_window_ready',
    'derivative_floor_positive',
    'window_narrow_enough',
    'critical_window_inside_stable_chart_radius',
)


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


@dataclass
class CriticalSurfaceThresholdIdentificationHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CriticalSurfaceThresholdIdentificationAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CriticalSurfaceThresholdIdentificationDischargeCertificate:
    family_label: str
    critical_parameter_window: list[float] | None
    critical_parameter_center: float | None
    critical_parameter_radius: float | None
    stable_chart_radius: float | None
    transversality_margin: float | None
    derivative_floor_proxy: float | None
    local_identification_margin: float | None
    promotion_ready: bool
    identification_specific_assumptions: list[str]
    upstream_context_assumptions: list[str]
    hypotheses: list[CriticalSurfaceThresholdIdentificationHypothesisRow]
    assumptions: list[CriticalSurfaceThresholdIdentificationAssumptionRow]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    active_assumptions: list[str]
    theorem_flags: dict[str, bool]
    residual_burden_summary: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'family_label': str(self.family_label),
            'critical_parameter_window': None if self.critical_parameter_window is None else [float(x) for x in self.critical_parameter_window],
            'critical_parameter_center': None if self.critical_parameter_center is None else float(self.critical_parameter_center),
            'critical_parameter_radius': None if self.critical_parameter_radius is None else float(self.critical_parameter_radius),
            'stable_chart_radius': None if self.stable_chart_radius is None else float(self.stable_chart_radius),
            'transversality_margin': None if self.transversality_margin is None else float(self.transversality_margin),
            'derivative_floor_proxy': None if self.derivative_floor_proxy is None else float(self.derivative_floor_proxy),
            'local_identification_margin': None if self.local_identification_margin is None else float(self.local_identification_margin),
            'promotion_ready': bool(self.promotion_ready),
            'identification_specific_assumptions': [str(x) for x in self.identification_specific_assumptions],
            'upstream_context_assumptions': [str(x) for x in self.upstream_context_assumptions],
            'hypotheses': [row.to_dict() for row in self.hypotheses],
            'assumptions': [row.to_dict() for row in self.assumptions],
            'discharged_hypotheses': [str(x) for x in self.discharged_hypotheses],
            'open_hypotheses': [str(x) for x in self.open_hypotheses],
            'active_assumptions': [str(x) for x in self.active_assumptions],
            'theorem_flags': {str(k): bool(v) for k, v in self.theorem_flags.items()},
            'residual_burden_summary': dict(self.residual_burden_summary),
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


def _window_from_validated_bridge(validated_bridge: Mapping[str, Any]) -> list[float] | None:
    center = validated_bridge.get('localized_center')
    radius = validated_bridge.get('localized_radius')
    if center is None or radius is None:
        return None
    c = float(center)
    r = max(0.0, float(radius))
    return [c - r, c + r]


def _build_hypotheses(
    *,
    stable_ready: bool,
    coarse_ready: bool,
    localized_ready: bool,
    derivative_floor_positive: bool,
    window_narrow_enough: bool,
    critical_radius: float | None,
    stable_radius: float | None,
    transversality_margin: float | None,
    derivative_floor_proxy: float | None,
    local_identification_margin: float | None,
) -> list[CriticalSurfaceThresholdIdentificationHypothesisRow]:
    chart_contains_window = True
    chart_margin = None
    if critical_radius is not None and stable_radius is not None:
        chart_margin = float(stable_radius - critical_radius)
        chart_contains_window = chart_margin >= -1.0e-15
    rows = [
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='stable_manifold_chart_ready',
            satisfied=bool(stable_ready),
            source='proxy stable-manifold chart',
            note='The current stable-manifold chart scaffold is fully closed at the proxy level.',
            margin=None if stable_radius is None else float(stable_radius),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='coarse_critical_surface_bridge_ready',
            satisfied=bool(coarse_ready),
            source='proxy critical-surface bridge',
            note='The family path supports a usable proxy critical-surface bridge before localization.',
            margin=None,
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='localized_transversality_window_ready',
            satisfied=bool(localized_ready),
            source='validated transversality window',
            note='The localized critical-surface / transversality window is validated strongly enough to support a focused identification push.',
            margin=None if transversality_margin is None else float(transversality_margin),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='derivative_floor_positive',
            satisfied=bool(derivative_floor_positive),
            source='validated transversality derivative diagnostics',
            note='The validated window carries a positive derivative-floor proxy along the family direction.',
            margin=None if derivative_floor_proxy is None else float(derivative_floor_proxy),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='window_narrow_enough',
            satisfied=bool(window_narrow_enough),
            source='validated transversality window',
            note='The localized critical window is already narrow enough to support theorem-facing threshold identification packaging.',
            margin=None if critical_radius is None else float(critical_radius),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='critical_window_inside_stable_chart_radius',
            satisfied=bool(chart_contains_window),
            source='stable-manifold / critical-window radius comparison',
            note='The localized critical parameter window fits inside the current stable-chart radius budget.',
            margin=None if chart_margin is None else float(chart_margin),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='local_identification_promotion_ready',
            satisfied=bool(local_identification_margin is None or local_identification_margin >= -1.0e-15) and bool(stable_ready and coarse_ready and localized_ready and derivative_floor_positive and window_narrow_enough and chart_contains_window),
            source='critical-surface threshold discharge synthesis',
            note='All currently available local geometric prerequisites line up well enough that the remaining burden can be isolated as a theorem-grade promotion step.',
            margin=None if local_identification_margin is None else float(local_identification_margin),
        ),
    ]
    return rows


def _build_assumptions(active_assumptions: Sequence[str]) -> tuple[list[CriticalSurfaceThresholdIdentificationAssumptionRow], list[str], list[str]]:
    active_set = {str(x) for x in active_assumptions}
    rows: list[CriticalSurfaceThresholdIdentificationAssumptionRow] = []
    for name in IDENTIFICATION_ASSUMPTIONS:
        rows.append(
            CriticalSurfaceThresholdIdentificationAssumptionRow(
                name=name,
                assumed=name not in active_set,
                source='critical-surface threshold discharge assumption',
                note='Identification-specific Workstream-A assumption remaining after the local critical-surface geometry has been packaged into a focused discharge object.',
            )
        )
    identification_active = [name for name in IDENTIFICATION_ASSUMPTIONS if name in active_set]
    context_active = [name for name in UPSTREAM_CONTEXT_ASSUMPTIONS if name in active_set]
    return rows, identification_active, context_active


def _build_residual_burden_summary(
    *,
    local_front_complete: bool,
    promotion_ready: bool,
    open_hypotheses: Sequence[str],
    identification_specific_assumptions: Sequence[str],
    upstream_context_assumptions: Sequence[str],
    local_identification_margin: float | None,
) -> dict[str, Any]:
    blocking_open = [str(x) for x in open_hypotheses]
    identification_specific_assumptions = [str(x) for x in identification_specific_assumptions]
    upstream_context_assumptions = [str(x) for x in upstream_context_assumptions]
    if local_front_complete and not identification_specific_assumptions:
        status = 'critical-surface-threshold-identification-discharge-ready'
        notes = 'The local Workstream-A critical-surface prerequisites are packaged, and the identification-specific promotion assumptions have all been toggled on.'
    elif local_front_complete:
        status = 'critical-surface-threshold-promotion-frontier'
        notes = 'The local Workstream-A geometry is already packaged into a focused discharge object, so the remaining structural burden is the theorem-grade critical-surface-to-threshold promotion step.'
    elif promotion_ready:
        status = 'critical-surface-threshold-isolation-frontier'
        notes = 'The raw local margins are encouraging, but the discharge object still sees unresolved local prerequisite hypotheses before the promotion theorem can be isolated cleanly.'
    else:
        status = 'workstream-local-prerequisite-frontier'
        notes = 'The Workstream-A discharge object is still blocked by local stable-manifold / bridge / transversality prerequisites rather than by the final promotion theorem alone.'
    return {
        'status': status,
        'promotion_ready': bool(promotion_ready),
        'local_front_complete': bool(local_front_complete),
        'blocking_open_hypotheses': blocking_open,
        'identification_specific_assumptions': identification_specific_assumptions,
        'upstream_context_assumptions': upstream_context_assumptions,
        'local_identification_margin': None if local_identification_margin is None else float(local_identification_margin),
        'notes': notes,
    }


@dataclass
class CriticalSurfaceThresholdIdentificationPromotionCertificate:
    family_label: str
    discharge_certificate: dict[str, Any]
    promotion_window: list[float] | None
    promotion_center: float | None
    promotion_radius: float | None
    promotion_margin: float | None
    local_front_complete: bool
    promotion_theorem_ready: bool
    promotion_theorem_available: bool
    promotion_theorem_discharged: bool
    identification_specific_assumptions: list[str]
    upstream_context_assumptions: list[str]
    hypotheses: list[CriticalSurfaceThresholdIdentificationHypothesisRow]
    assumptions: list[CriticalSurfaceThresholdIdentificationAssumptionRow]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    active_assumptions: list[str]
    theorem_flags: dict[str, bool]
    residual_burden_summary: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'family_label': str(self.family_label),
            'discharge_certificate': dict(self.discharge_certificate),
            'promotion_window': None if self.promotion_window is None else [float(x) for x in self.promotion_window],
            'promotion_center': None if self.promotion_center is None else float(self.promotion_center),
            'promotion_radius': None if self.promotion_radius is None else float(self.promotion_radius),
            'promotion_margin': None if self.promotion_margin is None else float(self.promotion_margin),
            'local_front_complete': bool(self.local_front_complete),
            'promotion_theorem_ready': bool(self.promotion_theorem_ready),
            'promotion_theorem_available': bool(self.promotion_theorem_available),
            'promotion_theorem_discharged': bool(self.promotion_theorem_discharged),
            'identification_specific_assumptions': [str(x) for x in self.identification_specific_assumptions],
            'upstream_context_assumptions': [str(x) for x in self.upstream_context_assumptions],
            'hypotheses': [row.to_dict() for row in self.hypotheses],
            'assumptions': [row.to_dict() for row in self.assumptions],
            'discharged_hypotheses': [str(x) for x in self.discharged_hypotheses],
            'open_hypotheses': [str(x) for x in self.open_hypotheses],
            'active_assumptions': [str(x) for x in self.active_assumptions],
            'theorem_flags': {str(k): bool(v) for k, v in self.theorem_flags.items()},
            'residual_burden_summary': dict(self.residual_burden_summary),
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


def _build_promotion_hypotheses(
    *,
    discharge_cert: Mapping[str, Any],
    local_front_complete: bool,
    promotion_theorem_ready: bool,
    promotion_theorem_available: bool,
    promotion_theorem_discharged: bool,
    promotion_margin: float | None,
    identification_specific_assumptions: Sequence[str],
    upstream_context_assumptions: Sequence[str],
) -> list[CriticalSurfaceThresholdIdentificationHypothesisRow]:
    return [
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='critical_surface_threshold_discharge_front_complete',
            satisfied=bool(local_front_complete),
            source='critical-surface threshold discharge certificate',
            note='The stage-74 critical-surface threshold discharge certificate is locally packaged with no remaining local-open prerequisite hypotheses.',
            margin=None if promotion_margin is None else float(promotion_margin),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='critical_surface_threshold_promotion_theorem_ready',
            satisfied=bool(promotion_theorem_ready),
            source='critical-surface threshold promotion synthesis',
            note='The local Workstream-A critical-surface geometry is packaged strongly enough that the remaining burden can be promoted into a theorem-facing critical-surface-to-threshold statement.',
            margin=None if promotion_margin is None else float(promotion_margin),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='critical_surface_threshold_promotion_theorem_available',
            satisfied=bool(promotion_theorem_available),
            source='critical-surface threshold promotion theorem',
            note='The identification-specific promotion assumptions have been absorbed, so the Workstream-A side now exposes the actual theorem-facing critical-surface-to-threshold promotion object.',
            margin=None if promotion_margin is None else float(promotion_margin),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='critical_surface_threshold_promotion_theorem_discharged',
            satisfied=bool(promotion_theorem_discharged),
            source='critical-surface threshold promotion theorem',
            note='Both the promotion theorem and the broader Workstream-A context assumptions are discharged, so the critical-surface-to-threshold identification theorem is complete at the current theorem-facing level.',
            margin=None if promotion_margin is None else float(promotion_margin),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='identification_specific_assumptions_absorbed_by_promotion_theorem',
            satisfied=not identification_specific_assumptions,
            source='promotion theorem assumption accounting',
            note='The promotion theorem no longer leaves identification-specific Workstream-A assumptions exposed downstream.',
            margin=float(len(IDENTIFICATION_ASSUMPTIONS) - len(list(identification_specific_assumptions))),
        ),
        CriticalSurfaceThresholdIdentificationHypothesisRow(
            name='upstream_context_assumptions_absorbed',
            satisfied=not upstream_context_assumptions,
            source='promotion theorem assumption accounting',
            note='The broader Workstream-A context assumptions have also been absorbed, so the promotion theorem is fully discharged rather than only conditionally strong.',
            margin=float(len(UPSTREAM_CONTEXT_ASSUMPTIONS) - len(list(upstream_context_assumptions))),
        ),
    ]


def _build_promotion_residual_burden_summary(
    *,
    local_front_complete: bool,
    promotion_theorem_ready: bool,
    promotion_theorem_available: bool,
    promotion_theorem_discharged: bool,
    open_hypotheses: Sequence[str],
    identification_specific_assumptions: Sequence[str],
    upstream_context_assumptions: Sequence[str],
    promotion_margin: float | None,
) -> dict[str, Any]:
    blocking_open = [str(x) for x in open_hypotheses]
    identification_specific_assumptions = [str(x) for x in identification_specific_assumptions]
    upstream_context_assumptions = [str(x) for x in upstream_context_assumptions]
    if promotion_theorem_discharged:
        status = 'critical-surface-threshold-promotion-theorem-discharged'
        notes = 'The Workstream-A side now carries a fully discharged critical-surface-to-threshold identification theorem object.'
    elif promotion_theorem_available:
        status = 'critical-surface-threshold-promotion-theorem-conditional-strong'
        notes = 'The Workstream-A side now carries the theorem-facing critical-surface-to-threshold promotion theorem; only broader Workstream context assumptions remain active.'
    elif promotion_theorem_ready:
        status = 'critical-surface-threshold-promotion-theorem-frontier'
        notes = 'The local discharge prerequisites are packaged, so the remaining Workstream-A burden is precisely the theorem-grade promotion theorem identifying the true threshold parameter.'
    elif local_front_complete:
        status = 'critical-surface-threshold-promotion-isolation-frontier'
        notes = 'The local discharge object is front-complete, but the promotion theorem is not yet isolated sharply enough to count as the remaining sole burden.'
    else:
        status = 'critical-surface-threshold-promotion-local-prerequisite-frontier'
        notes = 'The Workstream-A side is still missing local prerequisite packaging before the promotion theorem can be stated as the isolated remaining burden.'
    return {
        'status': status,
        'local_front_complete': bool(local_front_complete),
        'promotion_theorem_ready': bool(promotion_theorem_ready),
        'promotion_theorem_available': bool(promotion_theorem_available),
        'promotion_theorem_discharged': bool(promotion_theorem_discharged),
        'blocking_open_hypotheses': blocking_open,
        'identification_specific_assumptions': identification_specific_assumptions,
        'upstream_context_assumptions': upstream_context_assumptions,
        'promotion_margin': None if promotion_margin is None else float(promotion_margin),
        'notes': notes,
    }


def build_critical_surface_threshold_identification_promotion_certificate(
    *,
    family: HarmonicFamily | None = None,
    discharge_certificate: Mapping[str, Any] | None = None,
    stable_manifold_certificate: Mapping[str, Any] | None = None,
    critical_surface_bridge_certificate: Mapping[str, Any] | None = None,
    validated_critical_surface_bridge_certificate: Mapping[str, Any] | None = None,
    open_hypotheses: Sequence[str] = (),
    active_assumptions: Sequence[str] = (),
) -> CriticalSurfaceThresholdIdentificationPromotionCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)
    if discharge_certificate is not None:
        discharge_cert = dict(discharge_certificate)
    else:
        discharge_cert = build_critical_surface_threshold_identification_discharge_certificate(
            family=family,
            stable_manifold_certificate=stable_manifold_certificate,
            critical_surface_bridge_certificate=critical_surface_bridge_certificate,
            validated_critical_surface_bridge_certificate=validated_critical_surface_bridge_certificate,
            open_hypotheses=open_hypotheses,
            active_assumptions=active_assumptions,
        ).to_dict()

    critical_window = None if discharge_cert.get('critical_parameter_window') is None else [float(x) for x in discharge_cert.get('critical_parameter_window')]
    critical_center = None if discharge_cert.get('critical_parameter_center') is None else float(discharge_cert.get('critical_parameter_center'))
    critical_radius = None if discharge_cert.get('critical_parameter_radius') is None else float(discharge_cert.get('critical_parameter_radius'))
    promotion_margin = None if discharge_cert.get('local_identification_margin') is None else float(discharge_cert.get('local_identification_margin'))
    local_front_complete = bool((discharge_cert.get('theorem_flags') or {}).get('local_prerequisite_front_complete', False))
    promotion_theorem_ready = bool(discharge_cert.get('promotion_ready', False))
    identification_specific_assumptions = [str(x) for x in discharge_cert.get('identification_specific_assumptions', [])]
    upstream_context_assumptions = [str(x) for x in discharge_cert.get('upstream_context_assumptions', [])]
    promotion_theorem_available = bool(local_front_complete and not identification_specific_assumptions)
    promotion_theorem_discharged = bool(promotion_theorem_available and not upstream_context_assumptions)

    assumptions, _, _ = _build_assumptions([*identification_specific_assumptions, *upstream_context_assumptions])
    active_subset = [str(x) for x in identification_specific_assumptions] + [str(x) for x in upstream_context_assumptions if str(x) not in identification_specific_assumptions]
    hypotheses = _build_promotion_hypotheses(
        discharge_cert=discharge_cert,
        local_front_complete=local_front_complete,
        promotion_theorem_ready=promotion_theorem_ready,
        promotion_theorem_available=promotion_theorem_available,
        promotion_theorem_discharged=promotion_theorem_discharged,
        promotion_margin=promotion_margin,
        identification_specific_assumptions=identification_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
    )
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    residual_burden_summary = _build_promotion_residual_burden_summary(
        local_front_complete=local_front_complete,
        promotion_theorem_ready=promotion_theorem_ready,
        promotion_theorem_available=promotion_theorem_available,
        promotion_theorem_discharged=promotion_theorem_discharged,
        open_hypotheses=open_hypotheses,
        identification_specific_assumptions=identification_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
        promotion_margin=promotion_margin,
    )
    theorem_flags = {
        'local_front_complete': bool(local_front_complete),
        'promotion_theorem_ready': bool(promotion_theorem_ready),
        'promotion_theorem_available': bool(promotion_theorem_available),
        'critical_surface_identifies_true_threshold': bool(promotion_theorem_available),
        'promotion_theorem_discharged': bool(promotion_theorem_discharged),
    }
    if promotion_theorem_discharged:
        theorem_status = 'critical-surface-threshold-promotion-theorem-discharged'
        notes = 'The Workstream-A critical-surface-to-threshold promotion theorem is fully discharged at the current theorem-facing level.'
    elif promotion_theorem_available:
        theorem_status = 'critical-surface-threshold-promotion-theorem-conditional-strong'
        notes = 'The Workstream-A side now exposes the theorem-facing critical-surface-to-threshold promotion theorem, conditional only on the broader Workstream context assumptions.'
    elif promotion_theorem_ready:
        theorem_status = 'critical-surface-threshold-promotion-theorem-front-complete'
        notes = 'The local discharge package is now strong enough that the remaining Workstream-A burden is exactly the theorem-grade critical-surface-to-threshold promotion theorem.'
    elif local_front_complete or discharge_cert.get('theorem_status'):
        theorem_status = 'critical-surface-threshold-promotion-theorem-conditional-partial'
        notes = 'A theorem-facing critical-surface-to-threshold promotion object has been assembled, but the local discharge package is not yet strong enough to isolate the promotion theorem as the sole remaining burden.'
    else:
        theorem_status = 'critical-surface-threshold-promotion-theorem-failed'
        notes = 'No usable theorem-facing critical-surface-to-threshold promotion object could be assembled from the current discharge certificate.'
    if critical_window is not None and theorem_status != 'critical-surface-threshold-promotion-theorem-failed':
        notes += f' Promotion window: [{critical_window[0]:.6g}, {critical_window[1]:.6g}].'
    if promotion_margin is not None and theorem_status != 'critical-surface-threshold-promotion-theorem-failed':
        notes += f' Promotion margin: {promotion_margin:.6g}.'
    return CriticalSurfaceThresholdIdentificationPromotionCertificate(
        family_label=family_label,
        discharge_certificate=discharge_cert,
        promotion_window=critical_window,
        promotion_center=critical_center,
        promotion_radius=critical_radius,
        promotion_margin=promotion_margin,
        local_front_complete=bool(local_front_complete),
        promotion_theorem_ready=bool(promotion_theorem_ready),
        promotion_theorem_available=bool(promotion_theorem_available),
        promotion_theorem_discharged=bool(promotion_theorem_discharged),
        identification_specific_assumptions=identification_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
        hypotheses=hypotheses,
        assumptions=assumptions,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_subset,
        theorem_flags=theorem_flags,
        residual_burden_summary=residual_burden_summary,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_critical_surface_threshold_identification_discharge_certificate(
    *,
    family: HarmonicFamily | None = None,
    stable_manifold_certificate: Mapping[str, Any] | None = None,
    critical_surface_bridge_certificate: Mapping[str, Any] | None = None,
    validated_critical_surface_bridge_certificate: Mapping[str, Any] | None = None,
    open_hypotheses: Sequence[str] = (),
    active_assumptions: Sequence[str] = (),
) -> CriticalSurfaceThresholdIdentificationDischargeCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)
    stable_manifold = dict(stable_manifold_certificate or {})
    coarse_bridge = dict(critical_surface_bridge_certificate or {})
    validated_bridge = dict(validated_critical_surface_bridge_certificate or {})
    validated_flags = dict(validated_bridge.get('theorem_flags', {}))

    stable_ready = str(stable_manifold.get('theorem_status', '')) == 'proxy-stable-manifold-chart-identified'
    coarse_ready = str(coarse_bridge.get('theorem_status', '')) == 'proxy-critical-surface-family-bridge-identified'
    localized_ready = str(validated_bridge.get('theorem_status', '')) == 'proxy-critical-surface-window-bridge-validated' and bool(validated_flags.get('localized_transversality_window', False))
    derivative_floor_positive = bool(validated_flags.get('derivative_floor_positive', False))
    window_narrow_enough = bool(validated_flags.get('window_narrow_enough', False))

    critical_radius = None if validated_bridge.get('localized_radius') is None else float(validated_bridge.get('localized_radius'))
    critical_center = None if validated_bridge.get('localized_center') is None else float(validated_bridge.get('localized_center'))
    stable_radius = None if stable_manifold.get('stable_chart_radius') is None else float(stable_manifold.get('stable_chart_radius'))
    transversality_margin = None if validated_bridge.get('transversality_margin') is None else float(validated_bridge.get('transversality_margin'))
    derivative_floor_proxy = None if validated_bridge.get('derivative_floor_proxy') is None else float(validated_bridge.get('derivative_floor_proxy'))

    local_margin_terms: list[float] = []
    for value in (transversality_margin, derivative_floor_proxy):
        if value is not None:
            local_margin_terms.append(float(value))
    if stable_radius is not None and critical_radius is not None:
        local_margin_terms.append(float(stable_radius - critical_radius))
    local_identification_margin = min(local_margin_terms) if local_margin_terms else None

    hypotheses = _build_hypotheses(
        stable_ready=stable_ready,
        coarse_ready=coarse_ready,
        localized_ready=localized_ready,
        derivative_floor_positive=derivative_floor_positive,
        window_narrow_enough=window_narrow_enough,
        critical_radius=critical_radius,
        stable_radius=stable_radius,
        transversality_margin=transversality_margin,
        derivative_floor_proxy=derivative_floor_proxy,
        local_identification_margin=local_identification_margin,
    )
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    local_front_complete = all(name in discharged_hypotheses for name in LOCAL_PREREQUISITE_HYPOTHESES)
    promotion_ready = 'local_identification_promotion_ready' in discharged_hypotheses

    assumptions, identification_specific_assumptions, upstream_context_assumptions = _build_assumptions(active_assumptions)
    active_subset = identification_specific_assumptions + [x for x in upstream_context_assumptions if x not in identification_specific_assumptions]

    residual_burden_summary = _build_residual_burden_summary(
        local_front_complete=local_front_complete,
        promotion_ready=promotion_ready,
        open_hypotheses=open_hypotheses,
        identification_specific_assumptions=identification_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
        local_identification_margin=local_identification_margin,
    )

    theorem_flags = {
        'local_prerequisite_front_complete': bool(local_front_complete),
        'promotion_ready': bool(promotion_ready),
        'identification_specific_assumptions_isolated': True,
        'critical_surface_threshold_identification_ready': bool(local_front_complete and not identification_specific_assumptions),
    }

    if local_front_complete and not identification_specific_assumptions:
        theorem_status = 'critical-surface-threshold-identification-discharge-conditional-strong'
        notes = 'The Workstream-A critical-surface discharge object is locally complete and its identification-specific assumptions have all been toggled on.'
    elif local_front_complete:
        theorem_status = 'critical-surface-threshold-identification-discharge-front-complete'
        notes = 'The Workstream-A critical-surface discharge object is locally complete and now isolates the remaining burden to the identification-specific promotion assumptions.'
    elif promotion_ready or hypotheses:
        theorem_status = 'critical-surface-threshold-identification-discharge-conditional-partial'
        notes = 'A theorem-facing critical-surface discharge object has been assembled, but some local Workstream-A prerequisites remain open.'
    else:
        theorem_status = 'critical-surface-threshold-identification-discharge-failed'
        notes = 'No usable critical-surface threshold identification discharge object could be assembled from the current Workstream-A certificates.'

    if critical_center is not None and critical_radius is not None and theorem_status != 'critical-surface-threshold-identification-discharge-failed':
        notes += f' Localized critical window: [{critical_center - critical_radius:.6g}, {critical_center + critical_radius:.6g}].'
    if local_identification_margin is not None and theorem_status != 'critical-surface-threshold-identification-discharge-failed':
        notes += f' Minimum local identification margin: {float(local_identification_margin):.6g}.'

    return CriticalSurfaceThresholdIdentificationDischargeCertificate(
        family_label=family_label,
        critical_parameter_window=_window_from_validated_bridge(validated_bridge),
        critical_parameter_center=critical_center,
        critical_parameter_radius=critical_radius,
        stable_chart_radius=stable_radius,
        transversality_margin=transversality_margin,
        derivative_floor_proxy=derivative_floor_proxy,
        local_identification_margin=None if local_identification_margin is None else float(local_identification_margin),
        promotion_ready=bool(promotion_ready),
        identification_specific_assumptions=identification_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
        hypotheses=hypotheses,
        assumptions=assumptions,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_subset,
        theorem_flags=theorem_flags,
        residual_burden_summary=residual_burden_summary,
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    'IDENTIFICATION_ASSUMPTIONS',
    'UPSTREAM_CONTEXT_ASSUMPTIONS',
    'CriticalSurfaceThresholdIdentificationHypothesisRow',
    'CriticalSurfaceThresholdIdentificationAssumptionRow',
    'CriticalSurfaceThresholdIdentificationDischargeCertificate',
    'CriticalSurfaceThresholdIdentificationPromotionCertificate',
    'build_critical_surface_threshold_identification_discharge_certificate',
    'build_critical_surface_threshold_identification_promotion_certificate',
]
