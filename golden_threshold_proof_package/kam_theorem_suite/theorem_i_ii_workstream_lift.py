from __future__ import annotations

"""Conditional theorem packaging for Workstream A / Theorems I-II.

The repository now contains a real Workstream-A scaffold:

* theorem-facing universality-class admissibility,
* renormalization-chart admissibility,
* a proxy renormalization operator,
* proxy fixed-point iteration and enclosure,
* proxy spectral splitting,
* a proxy stable-manifold chart, and
* a localized critical-surface/transversality window bridge.

What is still missing is the final lift from these proxy objects to the theorem-grade
Banach-manifold / true-operator / true-critical-surface statements required by the
full proof program.  This module packages that situation honestly.  It does not
claim to prove Theorems I or II; instead it records which Workstream-A front
hypotheses are already discharged and which remaining assumptions would promote the
current scaffold into a conditional Theorem-I/II-style statement.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping

from .critical_surface import build_critical_surface_bridge_certificate
from .critical_surface_threshold_identification import (
    build_critical_surface_threshold_identification_discharge_certificate,
    build_critical_surface_threshold_identification_promotion_certificate,
)
from .validated_universality_class_theorem import (
    build_validated_universality_class_theorem_discharge_certificate,
    build_validated_universality_class_theorem_promotion_certificate,
)
from .validated_critical_surface_theorem import (
    build_validated_critical_surface_theorem_discharge_certificate,
    build_validated_critical_surface_theorem_promotion_certificate,
)
from .validated_renormalization_package import (
    build_validated_renormalization_package_discharge_certificate,
    build_validated_renormalization_package_promotion_certificate,
)
from .fixed_point_enclosure import build_fixed_point_enclosure_certificate
from .renormalization import build_renormalization_operator_certificate
from .renormalization_class import build_renormalization_class_certificate
from .renormalization_fixed_point import build_renormalization_fixed_point_certificate
from .spectral_splitting import build_spectral_splitting_certificate
from .stable_manifold import build_stable_manifold_chart_certificate
from .standard_map import HarmonicFamily
from .transversality_window import build_validated_critical_surface_bridge_certificate
from .universality_class import build_universality_class_certificate



def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'



def _filter_kwargs(fn, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    has_var_keyword = any(p.kind == p.VAR_KEYWORD for p in params.values())
    if has_var_keyword:
        return dict(kwargs)
    return {k: v for k, v in kwargs.items() if k in params}



def _status_rank(status: str) -> int:
    status = str(status)
    if any(token in status for token in ('validated', 'identified', 'stable-chart', 'contracting', 'admissible')):
        return 4
    if any(token in status for token in ('scaffold', 'mixed')):
        return 2
    return 0



def _min_margin(mapping: Mapping[str, Any], keys: list[str] | None = None) -> float | None:
    if not mapping:
        return None
    vals: list[float] = []
    for k, v in mapping.items():
        if keys is not None and str(k) not in keys:
            continue
        try:
            vals.append(float(v))
        except Exception:
            continue
    return min(vals) if vals else None



@dataclass
class TheoremIIWorkstreamHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremIIWorkstreamAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkstreamCriticalSurfaceIdentificationSummary:
    stable_manifold_chart_ready: bool
    coarse_critical_surface_bridge_ready: bool
    localized_transversality_window_ready: bool
    derivative_floor_positive: bool
    window_narrow_enough: bool
    critical_parameter_radius: float | None
    stable_chart_radius: float | None
    transversality_margin: float | None
    derivative_floor_proxy: float | None
    local_identification_margin: float | None
    threshold_identification_ready: bool
    residual_burden_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremIAndIIWorkstreamLiftCertificate:
    family_label: str
    universality_class_certificate: dict[str, Any]
    renormalization_class_certificate: dict[str, Any]
    renormalization_operator_certificate: dict[str, Any]
    fixed_point_certificate: dict[str, Any]
    fixed_point_enclosure_certificate: dict[str, Any]
    spectral_splitting_certificate: dict[str, Any]
    stable_manifold_certificate: dict[str, Any]
    critical_surface_bridge_certificate: dict[str, Any]
    validated_critical_surface_bridge_certificate: dict[str, Any]
    validated_universality_class_theorem_discharge: dict[str, Any]
    validated_universality_class_theorem_promotion: dict[str, Any]
    validated_renormalization_package_discharge: dict[str, Any]
    validated_renormalization_package_promotion: dict[str, Any]
    validated_critical_surface_theorem_discharge: dict[str, Any]
    validated_critical_surface_theorem_promotion: dict[str, Any]
    critical_parameter_window: list[float] | None
    critical_parameter_center: float | None
    critical_parameter_radius: float | None
    critical_surface_identification_summary: dict[str, Any]
    critical_surface_threshold_identification_discharge: dict[str, Any]
    critical_surface_threshold_identification_promotion: dict[str, Any]
    residual_burden_summary: dict[str, Any]
    hypotheses: list[TheoremIIWorkstreamHypothesisRow]
    assumptions: list[TheoremIIWorkstreamAssumptionRow]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    active_assumptions: list[str]
    workstream_codepath_strong: bool
    workstream_papergrade_strong: bool
    workstream_residual_caveat: list[str]
    workstream_consumption_summary: dict[str, Any]
    papergrade_theorem_status: str
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'family_label': str(self.family_label),
            'universality_class_certificate': dict(self.universality_class_certificate),
            'renormalization_class_certificate': dict(self.renormalization_class_certificate),
            'renormalization_operator_certificate': dict(self.renormalization_operator_certificate),
            'fixed_point_certificate': dict(self.fixed_point_certificate),
            'fixed_point_enclosure_certificate': dict(self.fixed_point_enclosure_certificate),
            'spectral_splitting_certificate': dict(self.spectral_splitting_certificate),
            'stable_manifold_certificate': dict(self.stable_manifold_certificate),
            'critical_surface_bridge_certificate': dict(self.critical_surface_bridge_certificate),
            'validated_critical_surface_bridge_certificate': dict(self.validated_critical_surface_bridge_certificate),
            'validated_universality_class_theorem_discharge': dict(self.validated_universality_class_theorem_discharge),
            'validated_universality_class_theorem_promotion': dict(self.validated_universality_class_theorem_promotion),
            'validated_renormalization_package_discharge': dict(self.validated_renormalization_package_discharge),
            'validated_renormalization_package_promotion': dict(self.validated_renormalization_package_promotion),
            'validated_critical_surface_theorem_discharge': dict(self.validated_critical_surface_theorem_discharge),
            'validated_critical_surface_theorem_promotion': dict(self.validated_critical_surface_theorem_promotion),
            'critical_parameter_window': None if self.critical_parameter_window is None else [float(x) for x in self.critical_parameter_window],
            'critical_parameter_center': None if self.critical_parameter_center is None else float(self.critical_parameter_center),
            'critical_parameter_radius': None if self.critical_parameter_radius is None else float(self.critical_parameter_radius),
            'critical_surface_identification_summary': dict(self.critical_surface_identification_summary),
            'critical_surface_threshold_identification_discharge': dict(self.critical_surface_threshold_identification_discharge),
            'critical_surface_threshold_identification_promotion': dict(self.critical_surface_threshold_identification_promotion),
            'residual_burden_summary': dict(self.residual_burden_summary),
            'hypotheses': [row.to_dict() for row in self.hypotheses],
            'assumptions': [row.to_dict() for row in self.assumptions],
            'discharged_hypotheses': [str(x) for x in self.discharged_hypotheses],
            'open_hypotheses': [str(x) for x in self.open_hypotheses],
            'active_assumptions': [str(x) for x in self.active_assumptions],
            'workstream_codepath_strong': bool(self.workstream_codepath_strong),
            'workstream_papergrade_strong': bool(self.workstream_papergrade_strong),
            'workstream_residual_caveat': [str(x) for x in self.workstream_residual_caveat],
            'workstream_consumption_summary': dict(self.workstream_consumption_summary),
            'papergrade_theorem_status': str(self.papergrade_theorem_status),
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }



def _default_assumptions() -> list[TheoremIIWorkstreamAssumptionRow]:
    return [
        TheoremIIWorkstreamAssumptionRow(
            name='theorem_grade_banach_manifold_universality_class',
            assumed=False,
            source='Theorem-I/II workstream lift assumption',
            note='Upgrade the current family-level admissibility scaffold into the final Banach-manifold universality class used by the universal theorem.',
        ),
        TheoremIIWorkstreamAssumptionRow(
            name='validated_true_renormalization_fixed_point_package',
            assumed=False,
            source='Theorem-I/II workstream lift assumption',
            note='Promote the proxy renormalization operator, fixed-point iteration, enclosure, splitting, and stable-manifold scaffold to the true validated renormalization fixed-point package.',
        ),
        TheoremIIWorkstreamAssumptionRow(
            name='golden_stable_manifold_is_true_critical_surface',
            assumed=False,
            source='Theorem-I/II workstream lift assumption',
            note='Identify the validated golden stable-manifold package with the actual critical surface separating persistence from obstruction.',
        ),
        TheoremIIWorkstreamAssumptionRow(
            name='family_chart_crossing_identifies_true_critical_parameter',
            assumed=False,
            source='Theorem-I/II workstream lift assumption',
            note='Upgrade the localized chart crossing / transversality window from a proxy compatibility object to the true family critical parameter.',
        ),
        TheoremIIWorkstreamAssumptionRow(
            name='golden_critical_surface_transversality_on_class',
            assumed=False,
            source='Theorem-I/II workstream lift assumption',
            note='Extend the present transversality window scaffold to a theorem-level transversality statement across the renormalization-stable class.',
        ),
    ]



def _build_assumptions(
    *,
    assume_theorem_grade_banach_manifold_universality_class: bool,
    assume_validated_true_renormalization_fixed_point_package: bool,
    assume_golden_stable_manifold_is_true_critical_surface: bool,
    assume_family_chart_crossing_identifies_true_critical_parameter: bool,
    assume_golden_critical_surface_transversality_on_class: bool,
) -> list[TheoremIIWorkstreamAssumptionRow]:
    assumption_map = {
        'theorem_grade_banach_manifold_universality_class': bool(assume_theorem_grade_banach_manifold_universality_class),
        'validated_true_renormalization_fixed_point_package': bool(assume_validated_true_renormalization_fixed_point_package),
        'golden_stable_manifold_is_true_critical_surface': bool(assume_golden_stable_manifold_is_true_critical_surface),
        'family_chart_crossing_identifies_true_critical_parameter': bool(assume_family_chart_crossing_identifies_true_critical_parameter),
        'golden_critical_surface_transversality_on_class': bool(assume_golden_critical_surface_transversality_on_class),
    }
    rows: list[TheoremIIWorkstreamAssumptionRow] = []
    for row in _default_assumptions():
        rows.append(
            TheoremIIWorkstreamAssumptionRow(
                name=row.name,
                assumed=bool(assumption_map.get(row.name, False)),
                source=row.source,
                note=row.note,
            )
        )
    return rows





def _promote_validated_universality_class_theorem_assumption(
    assumptions: list[TheoremIIWorkstreamAssumptionRow],
    promotion_certificate: Mapping[str, Any],
) -> list[TheoremIIWorkstreamAssumptionRow]:
    if not bool((promotion_certificate.get('theorem_flags') or {}).get('theorem_grade_banach_manifold_universality_class_available', False)):
        return assumptions
    promoted: list[TheoremIIWorkstreamAssumptionRow] = []
    for row in assumptions:
        if row.name == 'theorem_grade_banach_manifold_universality_class':
            promoted.append(
                TheoremIIWorkstreamAssumptionRow(
                    name=row.name,
                    assumed=True,
                    source='validated universality-class theorem promotion',
                    note='This ambient-class assumption is now absorbed by the theorem-facing validated universality-class theorem promotion object.',
                )
            )
        else:
            promoted.append(row)
    return promoted


def _promote_validated_renormalization_package_assumption(
    assumptions: list[TheoremIIWorkstreamAssumptionRow],
    promotion_certificate: Mapping[str, Any],
) -> list[TheoremIIWorkstreamAssumptionRow]:
    if not bool((promotion_certificate.get('theorem_flags') or {}).get('validated_true_renormalization_fixed_point_package_available', False)):
        return assumptions
    promoted: list[TheoremIIWorkstreamAssumptionRow] = []
    for row in assumptions:
        if row.name == 'validated_true_renormalization_fixed_point_package':
            promoted.append(
                TheoremIIWorkstreamAssumptionRow(
                    name=row.name,
                    assumed=True,
                    source='validated renormalization package promotion theorem',
                    note='This combined Workstream-A assumption is now absorbed by the theorem-facing validated renormalization package promotion object.',
                )
            )
        else:
            promoted.append(row)
    return promoted




def _promote_validated_critical_surface_theorem_assumptions(
    assumptions: list[TheoremIIWorkstreamAssumptionRow],
    promotion_certificate: Mapping[str, Any],
) -> list[TheoremIIWorkstreamAssumptionRow]:
    if not bool((promotion_certificate.get('theorem_flags') or {}).get('workstream_specific_critical_surface_theorem_available', False)):
        return assumptions
    promoted_names = {
        'golden_stable_manifold_is_true_critical_surface',
        'family_chart_crossing_identifies_true_critical_parameter',
        'golden_critical_surface_transversality_on_class',
    }
    promoted: list[TheoremIIWorkstreamAssumptionRow] = []
    for row in assumptions:
        if row.name in promoted_names:
            promoted.append(
                TheoremIIWorkstreamAssumptionRow(
                    name=row.name,
                    assumed=True,
                    source='validated critical-surface theorem promotion',
                    note='This Workstream-specific critical-surface assumption is now absorbed by the theorem-facing validated critical-surface theorem promotion object.',
                )
            )
        else:
            promoted.append(row)
    return promoted

def _build_critical_surface_identification_summary(
    *,
    stable_manifold: Mapping[str, Any],
    coarse_bridge: Mapping[str, Any],
    validated_bridge: Mapping[str, Any],
    open_hypotheses: list[str],
    active_assumptions: list[str],
) -> WorkstreamCriticalSurfaceIdentificationSummary:
    validated_flags = dict(validated_bridge.get('theorem_flags', {}))
    stable_ready = str(stable_manifold.get('theorem_status', '')) == 'proxy-stable-manifold-chart-identified'
    coarse_ready = str(coarse_bridge.get('theorem_status', '')) == 'proxy-critical-surface-family-bridge-identified'
    localized_ready = str(validated_bridge.get('theorem_status', '')) == 'proxy-critical-surface-window-bridge-validated' and bool(validated_flags.get('localized_transversality_window', False))
    derivative_floor_positive = bool(validated_flags.get('derivative_floor_positive', False))
    window_narrow_enough = bool(validated_flags.get('window_narrow_enough', False))

    critical_radius = None if validated_bridge.get('localized_radius') is None else float(validated_bridge.get('localized_radius'))
    stable_radius = None if stable_manifold.get('stable_chart_radius') is None else float(stable_manifold.get('stable_chart_radius'))
    transversality_margin = None if validated_bridge.get('transversality_margin') is None else float(validated_bridge.get('transversality_margin'))
    derivative_floor_proxy = None if validated_bridge.get('derivative_floor_proxy') is None else float(validated_bridge.get('derivative_floor_proxy'))

    local_margin_terms = []
    for value in (transversality_margin, derivative_floor_proxy):
        if value is not None:
            local_margin_terms.append(float(value))
    if stable_radius is not None and critical_radius is not None:
        local_margin_terms.append(float(stable_radius - critical_radius))
    local_identification_margin = min(local_margin_terms) if local_margin_terms else None

    threshold_identification_ready = bool(
        stable_ready
        and coarse_ready
        and localized_ready
        and derivative_floor_positive
        and window_narrow_enough
        and (local_identification_margin is None or local_identification_margin >= -1.0e-15)
    )

    if threshold_identification_ready and any(name in active_assumptions for name in (
        'golden_stable_manifold_is_true_critical_surface',
        'family_chart_crossing_identifies_true_critical_parameter',
        'golden_critical_surface_transversality_on_class',
    )):
        residual_status = 'critical-surface-threshold-identification-frontier'
        notes = (
            'The proxy stable-manifold / critical-surface / transversality-window front is locally sharp enough that the remaining Workstream-A burden now sits in the theorem-grade identification of the true critical surface and true critical parameter.'
        )
    elif 'theorem_ii_proxy_stable_manifold_chart_identified' in open_hypotheses:
        residual_status = 'stable-manifold-chart-frontier'
        notes = 'The current Workstream-A bottleneck still sits at the proxy stable-manifold chart.'
    elif 'theorem_ii_proxy_critical_surface_bridge_identified' in open_hypotheses:
        residual_status = 'critical-surface-bridge-frontier'
        notes = 'The coarse critical-surface bridge has not yet closed, so the Workstream-A bottleneck remains upstream of threshold identification.'
    elif 'theorem_ii_proxy_transversality_window_validated' in open_hypotheses:
        residual_status = 'localized-transversality-window-frontier'
        notes = 'The localized transversality window is not yet validated tightly enough to support theorem-grade critical-parameter identification.'
    elif 'validated_true_renormalization_fixed_point_package' in active_assumptions:
        residual_status = 'renormalization-fixed-point-package-frontier'
        notes = 'The Workstream-A bottleneck remains the validated renormalization fixed-point / splitting / stable-manifold package.'
    elif 'theorem_grade_banach_manifold_universality_class' in active_assumptions:
        residual_status = 'banach-manifold-universality-frontier'
        notes = 'The Workstream-A bottleneck is still the final Banach-manifold universality-class theorem.'
    elif threshold_identification_ready:
        residual_status = 'workstream-ready-for-identification'
        notes = 'The local Workstream-A geometry is sharp enough that only theorem-grade identification packaging remains.'
    else:
        residual_status = 'mixed-workstream-frontier'
        notes = 'The current Workstream-A burden is spread across multiple proxy fronts rather than isolated in one critical-surface identification hinge.'

    return WorkstreamCriticalSurfaceIdentificationSummary(
        stable_manifold_chart_ready=bool(stable_ready),
        coarse_critical_surface_bridge_ready=bool(coarse_ready),
        localized_transversality_window_ready=bool(localized_ready),
        derivative_floor_positive=bool(derivative_floor_positive),
        window_narrow_enough=bool(window_narrow_enough),
        critical_parameter_radius=critical_radius,
        stable_chart_radius=stable_radius,
        transversality_margin=transversality_margin,
        derivative_floor_proxy=derivative_floor_proxy,
        local_identification_margin=None if local_identification_margin is None else float(local_identification_margin),
        threshold_identification_ready=bool(threshold_identification_ready),
        residual_burden_status=str(residual_status),
        notes=str(notes),
    )


def _build_residual_burden_summary(
    *,
    critical_surface_identification_summary: WorkstreamCriticalSurfaceIdentificationSummary,
    validated_universality_class_theorem_discharge: Mapping[str, Any],
    validated_universality_class_theorem_promotion: Mapping[str, Any],
    validated_renormalization_package_discharge: Mapping[str, Any],
    validated_renormalization_package_promotion: Mapping[str, Any],
    validated_critical_surface_theorem_discharge: Mapping[str, Any],
    validated_critical_surface_theorem_promotion: Mapping[str, Any],
    critical_surface_threshold_identification_discharge: Mapping[str, Any],
    critical_surface_threshold_identification_promotion: Mapping[str, Any],
    open_hypotheses: list[str],
    active_assumptions: list[str],
) -> dict[str, Any]:
    universality_summary = dict(validated_universality_class_theorem_promotion.get('residual_burden_summary', {}))
    if universality_summary and str(universality_summary.get('status', '')) not in {'validated-universality-class-theorem-conditional-strong', 'validated-universality-class-theorem-discharged'}:
        return {
            'status': None if universality_summary.get('status') is None else str(universality_summary.get('status')),
            'local_geometry_ready': bool(universality_summary.get('local_front_complete', False)),
            'promotion_ready': bool(universality_summary.get('theorem_ready', False) or universality_summary.get('promotion_theorem_ready', False)),
            'promotion_theorem_available': bool(validated_universality_class_theorem_promotion.get('promotion_theorem_available', False)),
            'promotion_theorem_discharged': bool(validated_universality_class_theorem_promotion.get('promotion_theorem_discharged', False)),
            'local_front_complete': bool(universality_summary.get('local_front_complete', False)),
            'blocking_open_hypotheses': [str(x) for x in universality_summary.get('blocking_open_hypotheses', [])],
            'blocking_assumptions': [str(x) for x in universality_summary.get('package_specific_assumptions', [])],
            'upstream_context_assumptions': [str(x) for x in universality_summary.get('upstream_context_assumptions', [])],
            'minimum_local_identification_margin': None if universality_summary.get('local_class_margin') is None else float(universality_summary.get('local_class_margin')),
            'notes': str(universality_summary.get('notes', critical_surface_identification_summary.notes)),
        }
    renorm_promotion_summary = dict(validated_renormalization_package_promotion.get('residual_burden_summary', {}))
    if renorm_promotion_summary and str(renorm_promotion_summary.get('status', '')) not in {'validated-renormalization-package-conditional-strong', 'validated-renormalization-package-discharged'}:
        return {
            'status': None if renorm_promotion_summary.get('status') is None else str(renorm_promotion_summary.get('status')),
            'local_geometry_ready': bool(renorm_promotion_summary.get('local_front_complete', False)),
            'promotion_ready': bool(renorm_promotion_summary.get('promotion_theorem_ready', False)),
            'promotion_theorem_available': bool(renorm_promotion_summary.get('promotion_theorem_available', False)),
            'promotion_theorem_discharged': bool(renorm_promotion_summary.get('promotion_theorem_discharged', False)),
            'local_front_complete': bool(renorm_promotion_summary.get('local_front_complete', False)),
            'blocking_open_hypotheses': [str(x) for x in renorm_promotion_summary.get('blocking_open_hypotheses', [])],
            'blocking_assumptions': [str(x) for x in renorm_promotion_summary.get('package_specific_assumptions', [])],
            'upstream_context_assumptions': [str(x) for x in renorm_promotion_summary.get('upstream_context_assumptions', [])],
            'minimum_local_identification_margin': None if renorm_promotion_summary.get('promotion_margin') is None else float(renorm_promotion_summary.get('promotion_margin')),
            'notes': str(renorm_promotion_summary.get('notes', critical_surface_identification_summary.notes)),
        }
    validated_critical_surface_summary = dict(validated_critical_surface_theorem_promotion.get('residual_burden_summary', {}))
    if validated_critical_surface_summary and str(validated_critical_surface_summary.get('status', '')) not in {'validated-critical-surface-theorem-conditional-strong', 'validated-critical-surface-theorem-discharged'}:
        return {
            'status': None if validated_critical_surface_summary.get('status') is None else str(validated_critical_surface_summary.get('status')),
            'local_geometry_ready': bool(validated_critical_surface_summary.get('local_front_complete', False)),
            'promotion_ready': bool(validated_critical_surface_summary.get('theorem_ready', False) or validated_critical_surface_summary.get('promotion_theorem_ready', False)),
            'promotion_theorem_available': bool(validated_critical_surface_theorem_promotion.get('promotion_theorem_available', False)),
            'promotion_theorem_discharged': bool(validated_critical_surface_theorem_promotion.get('promotion_theorem_discharged', False)),
            'local_front_complete': bool(validated_critical_surface_summary.get('local_front_complete', False)),
            'blocking_open_hypotheses': [str(x) for x in validated_critical_surface_summary.get('blocking_open_hypotheses', [])],
            'blocking_assumptions': [str(x) for x in validated_critical_surface_summary.get('package_specific_assumptions', [])],
            'upstream_context_assumptions': [str(x) for x in validated_critical_surface_summary.get('upstream_context_assumptions', [])],
            'minimum_local_identification_margin': None if validated_critical_surface_summary.get('local_theorem_margin') is None else float(validated_critical_surface_summary.get('local_theorem_margin')),
            'notes': str(validated_critical_surface_summary.get('notes', critical_surface_identification_summary.notes)),
        }
    promotion_summary = dict(critical_surface_threshold_identification_promotion.get('residual_burden_summary', {}))
    if promotion_summary:
        return {
            'status': None if promotion_summary.get('status') is None else str(promotion_summary.get('status')),
            'local_geometry_ready': bool(critical_surface_identification_summary.threshold_identification_ready),
            'promotion_ready': bool(promotion_summary.get('promotion_theorem_ready', False)),
            'promotion_theorem_available': bool(promotion_summary.get('promotion_theorem_available', False)),
            'promotion_theorem_discharged': bool(promotion_summary.get('promotion_theorem_discharged', False)),
            'local_front_complete': bool(promotion_summary.get('local_front_complete', False)),
            'blocking_open_hypotheses': [str(x) for x in promotion_summary.get('blocking_open_hypotheses', [])],
            'blocking_assumptions': [str(x) for x in promotion_summary.get('identification_specific_assumptions', [])],
            'upstream_context_assumptions': [str(x) for x in promotion_summary.get('upstream_context_assumptions', [])],
            'minimum_local_identification_margin': None if promotion_summary.get('promotion_margin') is None else float(promotion_summary.get('promotion_margin')),
            'notes': str(promotion_summary.get('notes', critical_surface_identification_summary.notes)),
        }
    discharge_summary = dict(critical_surface_threshold_identification_discharge.get('residual_burden_summary', {}))
    if discharge_summary:
        return {
            'status': None if discharge_summary.get('status') is None else str(discharge_summary.get('status')),
            'local_geometry_ready': bool(critical_surface_identification_summary.threshold_identification_ready),
            'promotion_ready': bool(discharge_summary.get('promotion_ready', False)),
            'promotion_theorem_available': False,
            'promotion_theorem_discharged': False,
            'local_front_complete': bool(discharge_summary.get('local_front_complete', False)),
            'blocking_open_hypotheses': [str(x) for x in discharge_summary.get('blocking_open_hypotheses', [])],
            'blocking_assumptions': [str(x) for x in discharge_summary.get('identification_specific_assumptions', [])],
            'upstream_context_assumptions': [str(x) for x in discharge_summary.get('upstream_context_assumptions', [])],
            'minimum_local_identification_margin': None if discharge_summary.get('local_identification_margin') is None else float(discharge_summary.get('local_identification_margin')),
            'notes': str(discharge_summary.get('notes', critical_surface_identification_summary.notes)),
        }
    status = str(critical_surface_identification_summary.residual_burden_status)
    blocking_assumptions = [
        name for name in active_assumptions
        if name in {
            'theorem_grade_banach_manifold_universality_class',
            'validated_true_renormalization_fixed_point_package',
            'golden_stable_manifold_is_true_critical_surface',
            'family_chart_crossing_identifies_true_critical_parameter',
            'golden_critical_surface_transversality_on_class',
        }
    ]
    return {
        'status': status,
        'local_geometry_ready': bool(critical_surface_identification_summary.threshold_identification_ready),
        'promotion_ready': bool(critical_surface_identification_summary.threshold_identification_ready),
        'promotion_theorem_available': False,
        'promotion_theorem_discharged': False,
        'local_front_complete': bool(critical_surface_identification_summary.threshold_identification_ready),
        'blocking_open_hypotheses': [str(x) for x in open_hypotheses],
        'blocking_assumptions': [str(x) for x in blocking_assumptions],
        'upstream_context_assumptions': [],
        'minimum_local_identification_margin': None if critical_surface_identification_summary.local_identification_margin is None else float(critical_surface_identification_summary.local_identification_margin),
        'notes': str(critical_surface_identification_summary.notes),
    }



def _build_hypotheses(
    *,
    universality: Mapping[str, Any],
    renorm_class: Mapping[str, Any],
    renorm_operator: Mapping[str, Any],
    fixed_point: Mapping[str, Any],
    enclosure: Mapping[str, Any],
    splitting: Mapping[str, Any],
    stable_manifold: Mapping[str, Any],
    coarse_bridge: Mapping[str, Any],
    validated_bridge: Mapping[str, Any],
) -> list[TheoremIIWorkstreamHypothesisRow]:
    operator_ratios = dict(renorm_operator.get('contraction_metrics', {}))
    fixed_point_ratio = fixed_point.get('contraction_ratio_estimate')
    validated_flags = dict(validated_bridge.get('theorem_flags', {}))
    critical_radius = validated_bridge.get('localized_radius')

    return [
        TheoremIIWorkstreamHypothesisRow(
            name='theorem_i_universality_class_scaffold_admissible',
            satisfied=bool(universality.get('admissible', False)) and str(universality.get('status', '')) == 'admissible',
            source='universality-class scaffold',
            note='The current family lies inside the theorem-facing universality-class admissibility scaffold.',
            margin=_min_margin(dict(universality.get('admissibility_margins', {}))),
        ),
        TheoremIIWorkstreamHypothesisRow(
            name='theorem_i_renormalization_chart_scaffold_admissible',
            satisfied=bool(renorm_class.get('admissible_near_chart', False)) and str(renorm_class.get('status', '')) == 'near_golden_chart_scaffold',
            source='renormalization-class scaffold',
            note='The family is chart-admissible near the current golden renormalization scaffold.',
            margin=_min_margin(dict(renorm_class.get('chart_margins', {}))),
        ),
        TheoremIIWorkstreamHypothesisRow(
            name='theorem_ii_proxy_operator_stable',
            satisfied=str(renorm_operator.get('operator_status', '')) == 'proxy-renormalization-operator-stable-chart',
            source='proxy renormalization operator',
            note='The proxy renormalization operator preserves normalization and does not expand the chart profile on the current family.',
            margin=None if operator_ratios.get('chart_radius_ratio') is None else float(1.0 - float(operator_ratios['chart_radius_ratio'])),
        ),
        TheoremIIWorkstreamHypothesisRow(
            name='theorem_ii_proxy_fixed_point_iteration_contracting',
            satisfied=str(fixed_point.get('theorem_status', '')) == 'proxy-fixed-point-iteration-contracting',
            source='proxy fixed-point iteration',
            note='The proxy fixed-point iteration contracts at the chart level and produces a candidate golden fixed-point scaffold.',
            margin=None if fixed_point_ratio is None else float(1.0 - float(fixed_point_ratio)),
        ),
        TheoremIIWorkstreamHypothesisRow(
            name='theorem_ii_proxy_fixed_point_enclosure_validated',
            satisfied=str(enclosure.get('theorem_status', '')) == 'proxy-fixed-point-enclosure-validated',
            source='proxy fixed-point enclosure',
            note='The proxy fixed-point candidate has a validated enclosure with nonnegative invariance margin.',
            margin=None if enclosure.get('invariance_margin') is None else float(enclosure['invariance_margin']),
        ),
        TheoremIIWorkstreamHypothesisRow(
            name='theorem_ii_proxy_spectral_splitting_identified',
            satisfied=str(splitting.get('theorem_status', '')) == 'proxy-spectral-splitting-identified',
            source='proxy spectral splitting',
            note='A codimension-one dominated splitting proxy has been identified near the candidate golden fixed point.',
            margin=None if splitting.get('domination_margin') is None else float(splitting['domination_margin']),
        ),
        TheoremIIWorkstreamHypothesisRow(
            name='theorem_ii_proxy_stable_manifold_chart_identified',
            satisfied=str(stable_manifold.get('theorem_status', '')) == 'proxy-stable-manifold-chart-identified',
            source='proxy stable-manifold chart',
            note='The current stable-manifold chart package is fully closed at the proxy level.',
            margin=None if stable_manifold.get('stable_chart_radius') is None else float(stable_manifold['stable_chart_radius']),
        ),
        TheoremIIWorkstreamHypothesisRow(
            name='theorem_ii_proxy_critical_surface_bridge_identified',
            satisfied=str(coarse_bridge.get('theorem_status', '')) == 'proxy-critical-surface-family-bridge-identified',
            source='proxy critical-surface bridge',
            note='The family path supports a usable proxy critical-surface bridge at the coarse chart level.',
            margin=None if coarse_bridge.get('critical_surface_gap') is None else float(coarse_bridge['critical_surface_gap']),
        ),
        TheoremIIWorkstreamHypothesisRow(
            name='theorem_ii_proxy_transversality_window_validated',
            satisfied=str(validated_bridge.get('theorem_status', '')) == 'proxy-critical-surface-window-bridge-validated' and bool(validated_flags.get('localized_transversality_window', False)),
            source='validated transversality window',
            note='The proxy critical-surface bridge has been sharpened into a localized transversality window suitable for theorem packaging.',
            margin=None if critical_radius is None else float(critical_radius),
        ),
    ]





def _build_workstream_consumption_summary(
    *,
    open_hypotheses: Sequence[str],
    active_assumptions: Sequence[str],
    validated_universality_class_theorem_promotion: Mapping[str, Any],
    validated_renormalization_package_promotion: Mapping[str, Any],
    validated_critical_surface_theorem_promotion: Mapping[str, Any],
    critical_surface_threshold_identification_promotion: Mapping[str, Any],
    residual_burden_summary: Mapping[str, Any],
) -> dict[str, Any]:
    universality_flags = dict(validated_universality_class_theorem_promotion.get('theorem_flags', {}))
    renorm_flags = dict(validated_renormalization_package_promotion.get('theorem_flags', {}))
    critical_flags = dict(validated_critical_surface_theorem_promotion.get('theorem_flags', {}))
    ident_residual = dict(critical_surface_threshold_identification_promotion.get('residual_burden_summary', {}))

    codepath_strong = len(list(open_hypotheses)) == 0 and len(list(active_assumptions)) == 0
    universality_final = bool(universality_flags.get('papergrade_final') or universality_flags.get('banach_manifold_class_citeable'))
    renorm_final = bool(renorm_flags.get('papergrade_final') or (
        renorm_flags.get('true_fixed_point_package_certified') and renorm_flags.get('spectral_splitting_citeable') and renorm_flags.get('stable_manifold_citeable')
    ))
    critical_final = bool(critical_flags.get('papergrade_final') or (
        critical_flags.get('stable_manifold_equals_true_critical_surface') and critical_flags.get('critical_parameter_identification_certified') and critical_flags.get('critical_surface_transversality_certified')
    ))
    identification_final = bool(
        critical_surface_threshold_identification_promotion.get('promotion_theorem_discharged', False)
        or ident_residual.get('promotion_theorem_discharged', False)
    )
    papergrade_strong = bool(codepath_strong and universality_final and renorm_final and critical_final and identification_final)
    residual_caveat: list[str] = []
    if not papergrade_strong:
        if not universality_final:
            residual_caveat.append('workstream-universality-class-papergrade-incomplete')
        if not renorm_final:
            residual_caveat.append('workstream-renormalization-package-papergrade-incomplete')
        if not critical_final:
            residual_caveat.append('workstream-critical-surface-papergrade-incomplete')
        if not identification_final:
            residual_caveat.append('workstream-threshold-identification-papergrade-incomplete')
        residual_status = str(residual_burden_summary.get('status', ''))
        if residual_status and residual_status not in residual_caveat:
            residual_caveat.append(residual_status)
        if len(list(active_assumptions)) > 0 and 'workstream-active-assumptions-remain' not in residual_caveat:
            residual_caveat.append('workstream-active-assumptions-remain')
        if len(list(open_hypotheses)) > 0 and 'workstream-open-hypotheses-remain' not in residual_caveat:
            residual_caveat.append('workstream-open-hypotheses-remain')
    if papergrade_strong:
        papergrade_status = 'golden-theorem-i-ii-workstream-papergrade-final'
    elif codepath_strong:
        papergrade_status = 'golden-theorem-i-ii-workstream-papergrade-partial'
    else:
        papergrade_status = 'golden-theorem-i-ii-workstream-front-incomplete'
    return {
        'codepath_strong': bool(codepath_strong),
        'papergrade_strong': bool(papergrade_strong),
        'universality_class_citeable': bool(universality_final),
        'renormalization_package_citeable': bool(renorm_final),
        'critical_surface_theorem_citeable': bool(critical_final),
        'threshold_identification_citeable': bool(identification_final),
        'residual_caveat': residual_caveat,
        'papergrade_theorem_status': papergrade_status,
    }

def build_golden_theorem_i_ii_workstream_lift_certificate(
    family: HarmonicFamily | None = None,
    *,
    assume_theorem_grade_banach_manifold_universality_class: bool = False,
    assume_validated_true_renormalization_fixed_point_package: bool = False,
    assume_golden_stable_manifold_is_true_critical_surface: bool = False,
    assume_family_chart_crossing_identifies_true_critical_parameter: bool = False,
    assume_golden_critical_surface_transversality_on_class: bool = False,
    universality_certificate: Mapping[str, Any] | None = None,
    renormalization_class_certificate: Mapping[str, Any] | None = None,
    renormalization_operator_certificate: Mapping[str, Any] | None = None,
    fixed_point_certificate: Mapping[str, Any] | None = None,
    fixed_point_enclosure_certificate: Mapping[str, Any] | None = None,
    spectral_splitting_certificate: Mapping[str, Any] | None = None,
    stable_manifold_certificate: Mapping[str, Any] | None = None,
    critical_surface_bridge_certificate: Mapping[str, Any] | None = None,
    validated_critical_surface_bridge_certificate: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> GoldenTheoremIAndIIWorkstreamLiftCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)

    if universality_certificate is not None:
        universality = dict(universality_certificate)
    else:
        universality = build_universality_class_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_universality_class_certificate, kwargs),
        ).to_dict()

    if renormalization_class_certificate is not None:
        renorm_class = dict(renormalization_class_certificate)
    else:
        renorm_class = build_renormalization_class_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_renormalization_class_certificate, kwargs),
        ).to_dict()

    if renormalization_operator_certificate is not None:
        renorm_operator = dict(renormalization_operator_certificate)
    else:
        renorm_operator = build_renormalization_operator_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_renormalization_operator_certificate, kwargs),
        ).to_dict()

    if fixed_point_certificate is not None:
        fixed_point = dict(fixed_point_certificate)
    else:
        fixed_point = build_renormalization_fixed_point_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_renormalization_fixed_point_certificate, kwargs),
        ).to_dict()

    if fixed_point_enclosure_certificate is not None:
        enclosure = dict(fixed_point_enclosure_certificate)
    else:
        enclosure = build_fixed_point_enclosure_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_fixed_point_enclosure_certificate, kwargs),
        ).to_dict()

    if spectral_splitting_certificate is not None:
        splitting = dict(spectral_splitting_certificate)
    else:
        splitting = build_spectral_splitting_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_spectral_splitting_certificate, kwargs),
        ).to_dict()

    if stable_manifold_certificate is not None:
        stable_manifold = dict(stable_manifold_certificate)
    else:
        stable_manifold = build_stable_manifold_chart_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_stable_manifold_chart_certificate, kwargs),
        ).to_dict()

    if critical_surface_bridge_certificate is not None:
        coarse_bridge = dict(critical_surface_bridge_certificate)
    else:
        coarse_bridge = build_critical_surface_bridge_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_critical_surface_bridge_certificate, kwargs),
        ).to_dict()

    if validated_critical_surface_bridge_certificate is not None:
        validated_bridge = dict(validated_critical_surface_bridge_certificate)
    else:
        validated_bridge = build_validated_critical_surface_bridge_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_validated_critical_surface_bridge_certificate, kwargs),
        ).to_dict()

    hypotheses = _build_hypotheses(
        universality=universality,
        renorm_class=renorm_class,
        renorm_operator=renorm_operator,
        fixed_point=fixed_point,
        enclosure=enclosure,
        splitting=splitting,
        stable_manifold=stable_manifold,
        coarse_bridge=coarse_bridge,
        validated_bridge=validated_bridge,
    )
    assumptions = _build_assumptions(
        assume_theorem_grade_banach_manifold_universality_class=assume_theorem_grade_banach_manifold_universality_class,
        assume_validated_true_renormalization_fixed_point_package=assume_validated_true_renormalization_fixed_point_package,
        assume_golden_stable_manifold_is_true_critical_surface=assume_golden_stable_manifold_is_true_critical_surface,
        assume_family_chart_crossing_identifies_true_critical_parameter=assume_family_chart_crossing_identifies_true_critical_parameter,
        assume_golden_critical_surface_transversality_on_class=assume_golden_critical_surface_transversality_on_class,
    )

    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    provisional_active_assumptions = [row.name for row in assumptions if not row.assumed]
    validated_universality_class_theorem_discharge = build_validated_universality_class_theorem_discharge_certificate(
        family=family,
        universality_class_certificate=universality,
        renormalization_class_certificate=renorm_class,
        active_assumptions=provisional_active_assumptions,
    ).to_dict()
    validated_universality_class_theorem_promotion = build_validated_universality_class_theorem_promotion_certificate(
        family=family,
        discharge_certificate=validated_universality_class_theorem_discharge,
    ).to_dict()
    assumptions = _promote_validated_universality_class_theorem_assumption(
        assumptions,
        validated_universality_class_theorem_promotion,
    )
    provisional_active_assumptions = [row.name for row in assumptions if not row.assumed]
    validated_renormalization_package_discharge = build_validated_renormalization_package_discharge_certificate(
        family=family,
        renormalization_class_certificate=renorm_class,
        renormalization_operator_certificate=renorm_operator,
        fixed_point_certificate=fixed_point,
        fixed_point_enclosure_certificate=enclosure,
        spectral_splitting_certificate=splitting,
        stable_manifold_certificate=stable_manifold,
        active_assumptions=provisional_active_assumptions,
    ).to_dict()
    validated_renormalization_package_promotion = build_validated_renormalization_package_promotion_certificate(
        family=family,
        discharge_certificate=validated_renormalization_package_discharge,
    ).to_dict()
    assumptions = _promote_validated_renormalization_package_assumption(
        assumptions,
        validated_renormalization_package_promotion,
    )
    provisional_active_assumptions = [row.name for row in assumptions if not row.assumed]
    validated_critical_surface_theorem_discharge = build_validated_critical_surface_theorem_discharge_certificate(
        family=family,
        validated_renormalization_package_promotion=validated_renormalization_package_promotion,
        stable_manifold_certificate=stable_manifold,
        critical_surface_bridge_certificate=coarse_bridge,
        validated_critical_surface_bridge_certificate=validated_bridge,
        active_assumptions=provisional_active_assumptions,
    ).to_dict()
    validated_critical_surface_theorem_promotion = build_validated_critical_surface_theorem_promotion_certificate(
        family=family,
        discharge_certificate=validated_critical_surface_theorem_discharge,
    ).to_dict()
    assumptions = _promote_validated_critical_surface_theorem_assumptions(
        assumptions,
        validated_critical_surface_theorem_promotion,
    )
    active_assumptions = [row.name for row in assumptions if not row.assumed]
    critical_surface_identification_summary = _build_critical_surface_identification_summary(
        stable_manifold=stable_manifold,
        coarse_bridge=coarse_bridge,
        validated_bridge=validated_bridge,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
    )
    critical_surface_threshold_identification_discharge = build_critical_surface_threshold_identification_discharge_certificate(
        family=family,
        stable_manifold_certificate=stable_manifold,
        critical_surface_bridge_certificate=coarse_bridge,
        validated_critical_surface_bridge_certificate=validated_bridge,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
    ).to_dict()
    critical_surface_threshold_identification_promotion = build_critical_surface_threshold_identification_promotion_certificate(
        family=family,
        discharge_certificate=critical_surface_threshold_identification_discharge,
    ).to_dict()
    residual_burden_summary = _build_residual_burden_summary(
        critical_surface_identification_summary=critical_surface_identification_summary,
        validated_universality_class_theorem_discharge=validated_universality_class_theorem_discharge,
        validated_universality_class_theorem_promotion=validated_universality_class_theorem_promotion,
        validated_renormalization_package_discharge=validated_renormalization_package_discharge,
        validated_renormalization_package_promotion=validated_renormalization_package_promotion,
        validated_critical_surface_theorem_discharge=validated_critical_surface_theorem_discharge,
        validated_critical_surface_theorem_promotion=validated_critical_surface_theorem_promotion,
        critical_surface_threshold_identification_discharge=critical_surface_threshold_identification_discharge,
        critical_surface_threshold_identification_promotion=critical_surface_threshold_identification_promotion,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
    )
    workstream_consumption_summary = _build_workstream_consumption_summary(
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
        validated_universality_class_theorem_promotion=validated_universality_class_theorem_promotion,
        validated_renormalization_package_promotion=validated_renormalization_package_promotion,
        validated_critical_surface_theorem_promotion=validated_critical_surface_theorem_promotion,
        critical_surface_threshold_identification_promotion=critical_surface_threshold_identification_promotion,
        residual_burden_summary=residual_burden_summary,
    )

    component_statuses = [
        str(universality.get('status', '')),
        str(renorm_class.get('status', '')),
        str(renorm_operator.get('operator_status', '')),
        str(fixed_point.get('theorem_status', '')),
        str(enclosure.get('theorem_status', '')),
        str(splitting.get('theorem_status', '')),
        str(stable_manifold.get('theorem_status', '')),
        str(coarse_bridge.get('theorem_status', '')),
        str(validated_bridge.get('theorem_status', '')),
    ]
    strongest_rank = max((_status_rank(s) for s in component_statuses), default=0)
    satisfied_count = len(discharged_hypotheses)
    total_count = len(hypotheses)

    crit_center = validated_bridge.get('localized_center')
    crit_radius = validated_bridge.get('localized_radius')
    crit_window = None
    if crit_center is not None and crit_radius is not None:
        crit_window = [float(crit_center) - float(crit_radius), float(crit_center) + float(crit_radius)]

    if not open_hypotheses and not active_assumptions:
        theorem_status = 'golden-theorem-i-ii-workstream-lift-conditional-strong'
        notes = (
            'The current Workstream-A front is fully closed at the proxy level and all remaining theorem-grade lifts are assumed. '
            'This is the repository\'s strongest conditional Theorem-I/II-style statement.'
        )
    elif not open_hypotheses:
        theorem_status = 'golden-theorem-i-ii-workstream-lift-front-complete'
        notes = (
            'The current Workstream-A front is fully packaged at the proxy level, but the remaining universality / true-operator / '
            'true-critical-surface assumptions are still active. This is a front-complete Theorem-I/II shell rather than a finished theorem.'
        )
    elif strongest_rank >= 2 or satisfied_count > 0:
        theorem_status = 'golden-theorem-i-ii-workstream-lift-conditional-partial'
        notes = (
            'The repository now has an explicit theorem-facing Workstream-A package, but some proxy front components remain open. '
            'The shell isolates exactly which scaffold pieces still fail before only the theorem-grade lifts remain.'
        )
    else:
        theorem_status = 'golden-theorem-i-ii-workstream-lift-failed'
        notes = 'No usable Workstream-A theorem shell was assembled from the current certificates.'

    if theorem_status != 'golden-theorem-i-ii-workstream-lift-failed':
        notes += f' Front closure count: {satisfied_count}/{total_count}.'
        if crit_window is not None:
            notes += f' Localized critical window width: {float(crit_window[1]) - float(crit_window[0]):.6g}.'
        if critical_surface_identification_summary.threshold_identification_ready:
            notes += ' The local stable-manifold / critical-surface / transversality-window geometry is now sharp enough to support a focused critical-surface-to-threshold identification push.'

    return GoldenTheoremIAndIIWorkstreamLiftCertificate(
        family_label=family_label,
        universality_class_certificate=universality,
        renormalization_class_certificate=renorm_class,
        renormalization_operator_certificate=renorm_operator,
        fixed_point_certificate=fixed_point,
        fixed_point_enclosure_certificate=enclosure,
        spectral_splitting_certificate=splitting,
        stable_manifold_certificate=stable_manifold,
        critical_surface_bridge_certificate=coarse_bridge,
        validated_critical_surface_bridge_certificate=validated_bridge,
        validated_universality_class_theorem_discharge=validated_universality_class_theorem_discharge,
        validated_universality_class_theorem_promotion=validated_universality_class_theorem_promotion,
        validated_renormalization_package_discharge=validated_renormalization_package_discharge,
        validated_renormalization_package_promotion=validated_renormalization_package_promotion,
        validated_critical_surface_theorem_discharge=validated_critical_surface_theorem_discharge,
        validated_critical_surface_theorem_promotion=validated_critical_surface_theorem_promotion,
        critical_parameter_window=crit_window,
        critical_parameter_center=None if crit_center is None else float(crit_center),
        critical_parameter_radius=None if crit_radius is None else float(crit_radius),
        critical_surface_identification_summary=critical_surface_identification_summary.to_dict(),
        critical_surface_threshold_identification_discharge=critical_surface_threshold_identification_discharge,
        critical_surface_threshold_identification_promotion=critical_surface_threshold_identification_promotion,
        residual_burden_summary=residual_burden_summary,
        hypotheses=hypotheses,
        assumptions=assumptions,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
        workstream_codepath_strong=bool(workstream_consumption_summary['codepath_strong']),
        workstream_papergrade_strong=bool(workstream_consumption_summary['papergrade_strong']),
        workstream_residual_caveat=[str(x) for x in workstream_consumption_summary['residual_caveat']],
        workstream_consumption_summary=workstream_consumption_summary,
        papergrade_theorem_status=str(workstream_consumption_summary['papergrade_theorem_status']),
        theorem_status=theorem_status,
        notes=notes,
    )



def build_golden_theorem_i_ii_certificate(
    family: HarmonicFamily | None = None,
    **kwargs: Any,
) -> GoldenTheoremIAndIIWorkstreamLiftCertificate:
    return build_golden_theorem_i_ii_workstream_lift_certificate(
        family=family,
        **kwargs,
    )
