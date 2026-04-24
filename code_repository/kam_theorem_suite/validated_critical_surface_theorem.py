from __future__ import annotations

"""Theorem-facing packaging for the Workstream-A critical-surface / threshold core.

This module sits between the local Workstream-A geometry and the broader II→V seam.
It upgrades the proxy stable-manifold / critical-surface / localized transversality-window
stack into an explicit discharge / promotion layer, mirroring the role that
``validated_renormalization_package.py`` now plays one step upstream.

The mathematical purpose is to isolate the *Workstream-specific* theorem burden:

* stable manifold = true critical surface,
* localized chart crossing identifies the true critical parameter, and
* the transversality scaffold promotes to a theorem on the intended class.

When the local critical-surface geometry is already sharp and the validated
renormalization package is available, this module exposes a theorem-facing object that
absorbs those three Workstream-specific assumptions and leaves only broader upstream
context assumptions visible downstream.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .standard_map import HarmonicFamily

PACKAGE_SPECIFIC_ASSUMPTIONS = (
    'golden_stable_manifold_is_true_critical_surface',
    'family_chart_crossing_identifies_true_critical_parameter',
    'golden_critical_surface_transversality_on_class',
)

UPSTREAM_CONTEXT_ASSUMPTIONS = (
    'theorem_grade_banach_manifold_universality_class',
    'validated_true_renormalization_fixed_point_package',
)

LOCAL_PREREQUISITE_HYPOTHESES = (
    'validated_renormalization_package_available',
    'stable_manifold_chart_ready',
    'coarse_critical_surface_bridge_ready',
    'localized_transversality_window_ready',
    'derivative_floor_positive',
    'window_narrow_enough',
    'critical_window_inside_stable_chart_radius',
)


@dataclass
class ValidatedCriticalSurfaceTheoremHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedCriticalSurfaceTheoremAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedCriticalSurfaceTheoremDischargeCertificate:
    family_label: str
    validated_renormalization_package_promotion: dict[str, Any]
    stable_manifold_certificate: dict[str, Any]
    critical_surface_bridge_certificate: dict[str, Any]
    validated_critical_surface_bridge_certificate: dict[str, Any]
    critical_parameter_window: list[float] | None
    critical_parameter_center: float | None
    critical_parameter_radius: float | None
    stable_chart_radius: float | None
    local_theorem_margin: float | None
    local_front_complete: bool
    theorem_ready: bool
    package_specific_assumptions: list[str]
    absorbed_package_specific_assumptions: list[str]
    upstream_context_assumptions: list[str]
    hypotheses: list[ValidatedCriticalSurfaceTheoremHypothesisRow]
    assumptions: list[ValidatedCriticalSurfaceTheoremAssumptionRow]
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
            'validated_renormalization_package_promotion': dict(self.validated_renormalization_package_promotion),
            'stable_manifold_certificate': dict(self.stable_manifold_certificate),
            'critical_surface_bridge_certificate': dict(self.critical_surface_bridge_certificate),
            'validated_critical_surface_bridge_certificate': dict(self.validated_critical_surface_bridge_certificate),
            'critical_parameter_window': None if self.critical_parameter_window is None else [float(x) for x in self.critical_parameter_window],
            'critical_parameter_center': None if self.critical_parameter_center is None else float(self.critical_parameter_center),
            'critical_parameter_radius': None if self.critical_parameter_radius is None else float(self.critical_parameter_radius),
            'stable_chart_radius': None if self.stable_chart_radius is None else float(self.stable_chart_radius),
            'local_theorem_margin': None if self.local_theorem_margin is None else float(self.local_theorem_margin),
            'local_front_complete': bool(self.local_front_complete),
            'theorem_ready': bool(self.theorem_ready),
            'package_specific_assumptions': [str(x) for x in self.package_specific_assumptions],
            'absorbed_package_specific_assumptions': [str(x) for x in self.absorbed_package_specific_assumptions],
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


@dataclass
class ValidatedCriticalSurfaceTheoremPromotionCertificate:
    family_label: str
    discharge_certificate: dict[str, Any]
    promotion_margin: float | None
    local_front_complete: bool
    promotion_theorem_ready: bool
    promotion_theorem_available: bool
    promotion_theorem_discharged: bool
    package_specific_assumptions: list[str]
    absorbed_package_specific_assumptions: list[str]
    upstream_context_assumptions: list[str]
    hypotheses: list[ValidatedCriticalSurfaceTheoremHypothesisRow]
    assumptions: list[ValidatedCriticalSurfaceTheoremAssumptionRow]
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
            'promotion_margin': None if self.promotion_margin is None else float(self.promotion_margin),
            'local_front_complete': bool(self.local_front_complete),
            'promotion_theorem_ready': bool(self.promotion_theorem_ready),
            'promotion_theorem_available': bool(self.promotion_theorem_available),
            'promotion_theorem_discharged': bool(self.promotion_theorem_discharged),
            'package_specific_assumptions': [str(x) for x in self.package_specific_assumptions],
            'absorbed_package_specific_assumptions': [str(x) for x in self.absorbed_package_specific_assumptions],
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


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


def _window_from_bridge(validated_bridge: Mapping[str, Any]) -> list[float] | None:
    center = validated_bridge.get('localized_center')
    radius = validated_bridge.get('localized_radius')
    if center is None or radius is None:
        return None
    c = float(center)
    r = max(0.0, float(radius))
    return [c - r, c + r]


def _build_assumptions(active_assumptions: Sequence[str]) -> tuple[list[ValidatedCriticalSurfaceTheoremAssumptionRow], list[str], list[str]]:
    active_set = {str(x) for x in active_assumptions}
    rows: list[ValidatedCriticalSurfaceTheoremAssumptionRow] = []
    for name in [*PACKAGE_SPECIFIC_ASSUMPTIONS, *UPSTREAM_CONTEXT_ASSUMPTIONS]:
        note = (
            'Workstream-specific critical-surface theorem assumption isolated by the new discharge/promotion layer.'
            if name in PACKAGE_SPECIFIC_ASSUMPTIONS
            else 'Broader upstream context assumption still feeding the critical-surface theorem promotion object.'
        )
        rows.append(
            ValidatedCriticalSurfaceTheoremAssumptionRow(
                name=name,
                assumed=name not in active_set,
                source='validated critical-surface theorem assumption accounting',
                note=note,
            )
        )
    package_specific = [name for name in PACKAGE_SPECIFIC_ASSUMPTIONS if name in active_set]
    upstream_context = [name for name in UPSTREAM_CONTEXT_ASSUMPTIONS if name in active_set]
    return rows, package_specific, upstream_context


def _build_hypotheses(
    *,
    renorm_promotion: Mapping[str, Any],
    stable_manifold: Mapping[str, Any],
    coarse_bridge: Mapping[str, Any],
    validated_bridge: Mapping[str, Any],
) -> tuple[list[ValidatedCriticalSurfaceTheoremHypothesisRow], float | None, float | None, float | None, float | None]:
    renorm_flags = dict(renorm_promotion.get('theorem_flags', {}))
    validated_flags = dict(validated_bridge.get('theorem_flags', {}))
    renorm_available = bool(renorm_flags.get('validated_true_renormalization_fixed_point_package_available', False))
    stable_ready = str(stable_manifold.get('theorem_status', '')) == 'proxy-stable-manifold-chart-identified'
    coarse_ready = str(coarse_bridge.get('theorem_status', '')) == 'proxy-critical-surface-family-bridge-identified'
    localized_ready = str(validated_bridge.get('theorem_status', '')) == 'proxy-critical-surface-window-bridge-validated' and bool(validated_flags.get('localized_transversality_window', False))
    derivative_floor_positive = bool(validated_flags.get('derivative_floor_positive', False))
    window_narrow_enough = bool(validated_flags.get('window_narrow_enough', False))

    critical_radius = None if validated_bridge.get('localized_radius') is None else float(validated_bridge.get('localized_radius'))
    stable_radius = None if stable_manifold.get('stable_chart_radius') is None else float(stable_manifold.get('stable_chart_radius'))
    transversality_margin = None if validated_bridge.get('transversality_margin') is None else float(validated_bridge.get('transversality_margin'))
    derivative_floor_proxy = None if validated_bridge.get('derivative_floor_proxy') is None else float(validated_bridge.get('derivative_floor_proxy'))

    chart_contains_window = True
    chart_margin = None
    if critical_radius is not None and stable_radius is not None:
        chart_margin = float(stable_radius - critical_radius)
        chart_contains_window = chart_margin >= -1.0e-15

    local_terms: list[float] = []
    for value in (transversality_margin, derivative_floor_proxy, chart_margin):
        if value is not None:
            local_terms.append(float(value))
    renorm_promotion_margin = renorm_promotion.get('promotion_margin')
    if renorm_promotion_margin is not None:
        local_terms.append(float(renorm_promotion_margin))
    local_margin = min(local_terms) if local_terms else None

    rows = [
        ValidatedCriticalSurfaceTheoremHypothesisRow(
            name='validated_renormalization_package_available',
            satisfied=bool(renorm_available),
            source='validated renormalization package promotion theorem',
            note='The critical-surface theorem package rests on the theorem-facing validated renormalization package rather than on a loose proxy operator stack.',
            margin=None if renorm_promotion_margin is None else float(renorm_promotion_margin),
        ),
        ValidatedCriticalSurfaceTheoremHypothesisRow(
            name='stable_manifold_chart_ready',
            satisfied=bool(stable_ready),
            source='proxy stable-manifold chart',
            note='The local stable-manifold chart is already identified strongly enough to support theorem-facing critical-surface packaging.',
            margin=None if stable_radius is None else float(stable_radius),
        ),
        ValidatedCriticalSurfaceTheoremHypothesisRow(
            name='coarse_critical_surface_bridge_ready',
            satisfied=bool(coarse_ready),
            source='proxy critical-surface bridge',
            note='The family-level critical-surface bridge is already present before the localized theorem push.',
        ),
        ValidatedCriticalSurfaceTheoremHypothesisRow(
            name='localized_transversality_window_ready',
            satisfied=bool(localized_ready),
            source='validated critical-surface window bridge',
            note='The localized transversality window is validated strongly enough to support theorem-facing critical-surface identification packaging.',
            margin=None if transversality_margin is None else float(transversality_margin),
        ),
        ValidatedCriticalSurfaceTheoremHypothesisRow(
            name='derivative_floor_positive',
            satisfied=bool(derivative_floor_positive),
            source='validated critical-surface derivative diagnostics',
            note='The localized family-direction derivative floor is positive in the current theorem-facing window.',
            margin=None if derivative_floor_proxy is None else float(derivative_floor_proxy),
        ),
        ValidatedCriticalSurfaceTheoremHypothesisRow(
            name='window_narrow_enough',
            satisfied=bool(window_narrow_enough),
            source='validated critical-surface window bridge',
            note='The localized critical window is already narrow enough to support theorem-facing packaging.',
            margin=None if critical_radius is None else float(critical_radius),
        ),
        ValidatedCriticalSurfaceTheoremHypothesisRow(
            name='critical_window_inside_stable_chart_radius',
            satisfied=bool(chart_contains_window),
            source='stable-manifold / critical-window radius comparison',
            note='The localized critical window lies inside the current stable-chart radius budget.',
            margin=None if chart_margin is None else float(chart_margin),
        ),
        ValidatedCriticalSurfaceTheoremHypothesisRow(
            name='validated_critical_surface_theorem_ready',
            satisfied=bool(renorm_available and stable_ready and coarse_ready and localized_ready and derivative_floor_positive and window_narrow_enough and chart_contains_window),
            source='validated critical-surface theorem synthesis',
            note='The current Workstream-A critical-surface data is sharp enough that the remaining burden can be isolated as a theorem-grade critical-surface theorem promotion step.',
            margin=None if local_margin is None else float(local_margin),
        ),
    ]
    return rows, critical_radius, stable_radius, transversality_margin, local_margin


def _build_residual_burden_summary(
    *,
    local_front_complete: bool,
    theorem_ready: bool,
    open_hypotheses: Sequence[str],
    package_specific_assumptions: Sequence[str],
    upstream_context_assumptions: Sequence[str],
    local_margin: float | None,
) -> dict[str, Any]:
    if not local_front_complete:
        status = 'validated-critical-surface-theorem-local-prerequisite-frontier'
        notes = 'Some local critical-surface prerequisites are still open before the theorem-grade critical-surface promotion theorem can be isolated.'
    elif not theorem_ready:
        status = 'validated-critical-surface-theorem-promotion-frontier'
        notes = 'The local critical-surface front is close to complete, but the final synthesis needed for theorem-grade promotion is not yet in place.'
    elif upstream_context_assumptions:
        status = 'validated-critical-surface-theorem-conditional-strong'
        notes = 'The Workstream-specific critical-surface burden has been absorbed into a theorem-facing promotion object, leaving only broader upstream context assumptions.'
    else:
        status = 'validated-critical-surface-theorem-discharged'
        notes = 'The validated critical-surface theorem package is fully discharged at the current theorem-facing level.'
    return {
        'status': status,
        'local_front_complete': bool(local_front_complete),
        'theorem_ready': bool(theorem_ready),
        'blocking_open_hypotheses': [str(x) for x in open_hypotheses],
        'package_specific_assumptions': [str(x) for x in package_specific_assumptions],
        'upstream_context_assumptions': [str(x) for x in upstream_context_assumptions],
        'local_theorem_margin': None if local_margin is None else float(local_margin),
        'stable_manifold_equals_true_critical_surface': bool(theorem_ready and not package_specific_assumptions),
        'critical_parameter_identification_certified': bool(theorem_ready and not package_specific_assumptions),
        'critical_surface_transversality_certified': bool(theorem_ready and not package_specific_assumptions),
        'papergrade_final': bool(theorem_ready and not package_specific_assumptions and not upstream_context_assumptions),
        'notes': notes,
    }


def build_validated_critical_surface_theorem_discharge_certificate(
    *,
    family: HarmonicFamily | None = None,
    validated_renormalization_package_promotion: Mapping[str, Any] | None = None,
    stable_manifold_certificate: Mapping[str, Any] | None = None,
    critical_surface_bridge_certificate: Mapping[str, Any] | None = None,
    validated_critical_surface_bridge_certificate: Mapping[str, Any] | None = None,
    active_assumptions: Sequence[str] = (),
) -> ValidatedCriticalSurfaceTheoremDischargeCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)
    renorm_promotion = dict(validated_renormalization_package_promotion or {})
    stable_manifold = dict(stable_manifold_certificate or {})
    coarse_bridge = dict(critical_surface_bridge_certificate or {})
    validated_bridge = dict(validated_critical_surface_bridge_certificate or {})

    hypotheses, critical_radius, stable_radius, _, local_margin = _build_hypotheses(
        renorm_promotion=renorm_promotion,
        stable_manifold=stable_manifold,
        coarse_bridge=coarse_bridge,
        validated_bridge=validated_bridge,
    )
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    local_front_complete = all(name in discharged_hypotheses for name in LOCAL_PREREQUISITE_HYPOTHESES)
    theorem_ready = 'validated_critical_surface_theorem_ready' in discharged_hypotheses
    assumptions, package_specific_assumptions, upstream_context_assumptions = _build_assumptions(active_assumptions)
    active_subset = package_specific_assumptions + [x for x in upstream_context_assumptions if x not in package_specific_assumptions]

    residual_burden_summary = _build_residual_burden_summary(
        local_front_complete=local_front_complete,
        theorem_ready=theorem_ready,
        open_hypotheses=open_hypotheses,
        package_specific_assumptions=package_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
        local_margin=local_margin,
    )
    theorem_flags = {
        'local_prerequisite_front_complete': bool(local_front_complete),
        'theorem_ready': bool(theorem_ready),
        'workstream_specific_critical_surface_assumptions_isolated': True,
        'validated_critical_surface_theorem_available': bool(local_front_complete and not package_specific_assumptions),
    }
    if local_front_complete and not package_specific_assumptions:
        theorem_status = 'validated-critical-surface-theorem-discharge-conditional-strong'
        notes = 'The Workstream-specific critical-surface discharge package is locally complete and its package-specific assumptions have all been absorbed.'
    elif local_front_complete:
        theorem_status = 'validated-critical-surface-theorem-discharge-front-complete'
        notes = 'The local critical-surface theorem front is complete and now isolates the remaining burden to the Workstream-specific theorem-grade promotion assumptions.'
    elif hypotheses:
        theorem_status = 'validated-critical-surface-theorem-discharge-conditional-partial'
        notes = 'A theorem-facing critical-surface discharge object has been assembled, but some local prerequisites remain open.'
    else:
        theorem_status = 'validated-critical-surface-theorem-discharge-failed'
        notes = 'No usable validated critical-surface theorem discharge object could be assembled from the current Workstream-A certificates.'
    critical_window = _window_from_bridge(validated_bridge)
    if critical_window is not None and theorem_status != 'validated-critical-surface-theorem-discharge-failed':
        notes += f' Localized critical window: [{critical_window[0]:.6g}, {critical_window[1]:.6g}].'
    if local_margin is not None and theorem_status != 'validated-critical-surface-theorem-discharge-failed':
        notes += f' Minimum local theorem margin: {local_margin:.6g}.'

    return ValidatedCriticalSurfaceTheoremDischargeCertificate(
        family_label=family_label,
        validated_renormalization_package_promotion=renorm_promotion,
        stable_manifold_certificate=stable_manifold,
        critical_surface_bridge_certificate=coarse_bridge,
        validated_critical_surface_bridge_certificate=validated_bridge,
        critical_parameter_window=critical_window,
        critical_parameter_center=None if validated_bridge.get('localized_center') is None else float(validated_bridge.get('localized_center')),
        critical_parameter_radius=critical_radius,
        stable_chart_radius=stable_radius,
        local_theorem_margin=local_margin,
        local_front_complete=bool(local_front_complete),
        theorem_ready=bool(theorem_ready),
        package_specific_assumptions=package_specific_assumptions,
        absorbed_package_specific_assumptions=[],
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


def build_validated_critical_surface_theorem_promotion_certificate(
    *,
    family: HarmonicFamily | None = None,
    discharge_certificate: Mapping[str, Any] | None = None,
) -> ValidatedCriticalSurfaceTheoremPromotionCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)
    discharge = dict(discharge_certificate or {})
    local_front_complete = bool(discharge.get('local_front_complete', False))
    theorem_ready = bool(discharge.get('theorem_ready', False))
    package_specific_assumptions = [str(x) for x in discharge.get('package_specific_assumptions', [])]
    upstream_context_assumptions = [str(x) for x in discharge.get('upstream_context_assumptions', [])]
    hypotheses = [ValidatedCriticalSurfaceTheoremHypothesisRow(**row) for row in discharge.get('hypotheses', [])]
    assumptions = [ValidatedCriticalSurfaceTheoremAssumptionRow(**row) for row in discharge.get('assumptions', [])]
    discharged_hypotheses = [str(x) for x in discharge.get('discharged_hypotheses', [])]
    open_hypotheses = [str(x) for x in discharge.get('open_hypotheses', [])]
    active_subset = [str(x) for x in discharge.get('active_assumptions', [])]
    promotion_margin = None if discharge.get('local_theorem_margin') is None else float(discharge.get('local_theorem_margin'))

    promotion_theorem_ready = bool(local_front_complete and theorem_ready)
    absorbed_package_specific_assumptions = list(package_specific_assumptions) if promotion_theorem_ready else []
    promotion_theorem_available = bool(promotion_theorem_ready)
    promotion_theorem_discharged = bool(promotion_theorem_available and not upstream_context_assumptions)
    promotion_active_assumptions = [str(x) for x in upstream_context_assumptions] if promotion_theorem_available else list(active_subset)
    theorem_flags = {
        'local_front_complete': bool(local_front_complete),
        'promotion_theorem_ready': bool(promotion_theorem_ready),
        'promotion_theorem_available': bool(promotion_theorem_available),
        'promotion_theorem_discharged': bool(promotion_theorem_discharged),
        'workstream_specific_critical_surface_theorem_available': bool(promotion_theorem_available),
        'stable_manifold_equals_true_critical_surface': bool(promotion_theorem_discharged),
        'critical_parameter_identification_certified': bool(promotion_theorem_discharged),
        'critical_surface_transversality_certified': bool(promotion_theorem_discharged),
        'papergrade_final': bool(promotion_theorem_discharged),
    }

    residual_burden_summary = _build_residual_burden_summary(
        local_front_complete=local_front_complete,
        theorem_ready=promotion_theorem_ready,
        open_hypotheses=open_hypotheses,
        package_specific_assumptions=[] if promotion_theorem_available else package_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
        local_margin=promotion_margin,
    )

    if promotion_theorem_discharged:
        theorem_status = 'validated-critical-surface-theorem-promotion-discharged'
        notes = 'The Workstream-specific critical-surface theorem promotion object is fully discharged at the current theorem-facing level.'
    elif promotion_theorem_available:
        theorem_status = 'validated-critical-surface-theorem-promotion-conditional-strong'
        notes = 'The Workstream-specific critical-surface theorem promotion object is now available and absorbs the remaining stable-manifold / critical-surface / transversality assumptions, conditional only on broader upstream context assumptions.'
    elif promotion_theorem_ready:
        theorem_status = 'validated-critical-surface-theorem-promotion-front-complete'
        notes = 'The local critical-surface theorem front is complete and the remaining burden is exactly the theorem-grade promotion of the Workstream-specific critical-surface assumptions.'
    elif local_front_complete or discharge.get('theorem_status'):
        theorem_status = 'validated-critical-surface-theorem-promotion-conditional-partial'
        notes = 'A theorem-facing critical-surface theorem promotion object has been assembled, but some local prerequisites remain open.'
    else:
        theorem_status = 'validated-critical-surface-theorem-promotion-failed'
        notes = 'No usable critical-surface theorem promotion object could be assembled from the current discharge certificate.'
    if promotion_margin is not None and theorem_status != 'validated-critical-surface-theorem-promotion-failed':
        notes += f' Promotion margin: {promotion_margin:.6g}.'

    return ValidatedCriticalSurfaceTheoremPromotionCertificate(
        family_label=family_label,
        discharge_certificate=discharge,
        promotion_margin=promotion_margin,
        local_front_complete=bool(local_front_complete),
        promotion_theorem_ready=bool(promotion_theorem_ready),
        promotion_theorem_available=bool(promotion_theorem_available),
        promotion_theorem_discharged=bool(promotion_theorem_discharged),
        package_specific_assumptions=package_specific_assumptions,
        absorbed_package_specific_assumptions=absorbed_package_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
        hypotheses=hypotheses,
        assumptions=assumptions,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        active_assumptions=promotion_active_assumptions,
        theorem_flags=theorem_flags,
        residual_burden_summary=residual_burden_summary,
        theorem_status=theorem_status,
        notes=notes,
    )
