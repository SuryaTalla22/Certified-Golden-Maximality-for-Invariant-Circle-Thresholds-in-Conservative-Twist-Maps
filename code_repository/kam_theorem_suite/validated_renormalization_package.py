from __future__ import annotations

"""Theorem-facing packaging for the renormalization fixed-point core.

This module upgrades the Workstream-A operator/fixed-point/splitting/stable-manifold
stack from a loose collection of proxy certificates into an explicit discharge /
promotion layer.

It still does *not* claim to prove the true Banach-manifold renormalization theorem.
What it does provide is the next theorem-facing object the repository needs:

* a local discharge certificate recording when the proxy renormalization package is
  completely assembled,
* a promotion theorem object isolating the remaining theorem-grade assumptions,
* machine-readable margins that make the current local front explicit, and
* a clean way for Workstream A to replace the combined assumption
  ``validated_true_renormalization_fixed_point_package`` by a theorem object.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .standard_map import HarmonicFamily
from .renormalization_class import build_renormalization_class_certificate
from .renormalization import build_renormalization_operator_certificate
from .renormalization_fixed_point import build_renormalization_fixed_point_certificate
from .fixed_point_enclosure import build_fixed_point_enclosure_certificate
from .spectral_splitting import build_spectral_splitting_certificate
from .stable_manifold import build_stable_manifold_chart_certificate

PACKAGE_SPECIFIC_ASSUMPTIONS = (
    'true_renormalization_operator_validated_on_banach_class',
    'validated_golden_fixed_point_and_enclosure',
    'validated_codom_one_splitting_and_local_stable_manifold',
)

UPSTREAM_CONTEXT_ASSUMPTIONS = (
    'theorem_grade_banach_manifold_universality_class',
)


@dataclass
class ValidatedRenormalizationPackageHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedRenormalizationPackageAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedRenormalizationPackageDischargeCertificate:
    family_label: str
    renormalization_class_certificate: dict[str, Any]
    renormalization_operator_certificate: dict[str, Any]
    fixed_point_certificate: dict[str, Any]
    fixed_point_enclosure_certificate: dict[str, Any]
    spectral_splitting_certificate: dict[str, Any]
    stable_manifold_certificate: dict[str, Any]
    local_package_margin: float | None
    local_front_complete: bool
    package_ready: bool
    package_specific_assumptions: list[str]
    upstream_context_assumptions: list[str]
    hypotheses: list[ValidatedRenormalizationPackageHypothesisRow]
    assumptions: list[ValidatedRenormalizationPackageAssumptionRow]
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
            'renormalization_class_certificate': dict(self.renormalization_class_certificate),
            'renormalization_operator_certificate': dict(self.renormalization_operator_certificate),
            'fixed_point_certificate': dict(self.fixed_point_certificate),
            'fixed_point_enclosure_certificate': dict(self.fixed_point_enclosure_certificate),
            'spectral_splitting_certificate': dict(self.spectral_splitting_certificate),
            'stable_manifold_certificate': dict(self.stable_manifold_certificate),
            'local_package_margin': None if self.local_package_margin is None else float(self.local_package_margin),
            'local_front_complete': bool(self.local_front_complete),
            'package_ready': bool(self.package_ready),
            'package_specific_assumptions': [str(x) for x in self.package_specific_assumptions],
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
class ValidatedRenormalizationPackagePromotionCertificate:
    family_label: str
    discharge_certificate: dict[str, Any]
    promotion_margin: float | None
    local_front_complete: bool
    promotion_theorem_ready: bool
    promotion_theorem_available: bool
    promotion_theorem_discharged: bool
    package_specific_assumptions: list[str]
    upstream_context_assumptions: list[str]
    hypotheses: list[ValidatedRenormalizationPackageHypothesisRow]
    assumptions: list[ValidatedRenormalizationPackageAssumptionRow]
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


def _build_assumptions(active_assumptions: Sequence[str]) -> tuple[list[ValidatedRenormalizationPackageAssumptionRow], list[str], list[str]]:
    active_set = {str(x) for x in active_assumptions}
    rows: list[ValidatedRenormalizationPackageAssumptionRow] = []
    for name in [*PACKAGE_SPECIFIC_ASSUMPTIONS, *UPSTREAM_CONTEXT_ASSUMPTIONS]:
        note = (
            'Validated renormalization-package assumption isolated by the new discharge/promotion layer.'
            if name in PACKAGE_SPECIFIC_ASSUMPTIONS
            else 'Broader Workstream-A context assumption still feeding the validated renormalization-package promotion theorem.'
        )
        rows.append(
            ValidatedRenormalizationPackageAssumptionRow(
                name=name,
                assumed=name not in active_set,
                source='validated renormalization package assumption accounting',
                note=note,
            )
        )
    package_specific = [name for name in PACKAGE_SPECIFIC_ASSUMPTIONS if name in active_set]
    upstream_context = [name for name in UPSTREAM_CONTEXT_ASSUMPTIONS if name in active_set]
    return rows, package_specific, upstream_context


def _build_local_hypotheses(
    *,
    renorm_class: Mapping[str, Any],
    renorm_operator: Mapping[str, Any],
    fixed_point: Mapping[str, Any],
    enclosure: Mapping[str, Any],
    splitting: Mapping[str, Any],
    stable_manifold: Mapping[str, Any],
) -> tuple[list[ValidatedRenormalizationPackageHypothesisRow], float | None]:
    operator_ratios = dict(renorm_operator.get('contraction_metrics', {}))
    fixed_point_ratio = fixed_point.get('contraction_ratio_estimate')
    invariance_margin = enclosure.get('invariance_margin')
    domination_margin = splitting.get('domination_margin')
    stable_radius = stable_manifold.get('stable_chart_radius')
    graph_contraction = stable_manifold.get('graph_transform_contraction')
    manifold_flags = dict(stable_manifold.get('manifold_flags', {}))
    graph_contracting = bool(manifold_flags.get('dominated_graph_transform', False)) if graph_contraction is None else float(graph_contraction) < 1.0
    local_terms: list[float] = []
    if operator_ratios.get('chart_radius_ratio') is not None:
        local_terms.append(float(1.0 - float(operator_ratios['chart_radius_ratio'])))
    if fixed_point_ratio is not None:
        local_terms.append(float(1.0 - float(fixed_point_ratio)))
    if invariance_margin is not None:
        local_terms.append(float(invariance_margin))
    if domination_margin is not None:
        local_terms.append(float(domination_margin))
    if stable_radius is not None:
        local_terms.append(float(stable_radius))
    if graph_contraction is not None:
        local_terms.append(float(1.0 - float(graph_contraction)))
    local_margin = min(local_terms) if local_terms else None

    rows = [
        ValidatedRenormalizationPackageHypothesisRow(
            name='renormalization_chart_scaffold_admissible',
            satisfied=bool(renorm_class.get('admissible_near_chart', False)) and str(renorm_class.get('status', '')) == 'near_golden_chart_scaffold',
            source='renormalization-class scaffold',
            note='The family is chart-admissible near the current golden renormalization scaffold.',
            margin=None if renorm_class.get('chart_margins') is None else min(float(v) for v in dict(renorm_class.get('chart_margins', {})).values()),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='proxy_operator_stable_chart_identified',
            satisfied=str(renorm_operator.get('operator_status', '')) == 'proxy-renormalization-operator-stable-chart',
            source='proxy renormalization operator',
            note='The proxy renormalization operator preserves normalization and contracts the chart profile on the current family.',
            margin=None if operator_ratios.get('chart_radius_ratio') is None else float(1.0 - float(operator_ratios['chart_radius_ratio'])),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='proxy_fixed_point_iteration_contracting',
            satisfied=str(fixed_point.get('theorem_status', '')) == 'proxy-fixed-point-iteration-contracting',
            source='proxy fixed-point iteration',
            note='The proxy renormalization iteration contracts toward a candidate golden fixed point.',
            margin=None if fixed_point_ratio is None else float(1.0 - float(fixed_point_ratio)),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='proxy_fixed_point_enclosure_validated',
            satisfied=str(enclosure.get('theorem_status', '')) == 'proxy-fixed-point-enclosure-validated',
            source='proxy fixed-point enclosure',
            note='The proxy fixed-point candidate carries a validated enclosure with positive invariance margin.',
            margin=None if invariance_margin is None else float(invariance_margin),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='proxy_spectral_splitting_identified',
            satisfied=str(splitting.get('theorem_status', '')) == 'proxy-spectral-splitting-identified',
            source='proxy spectral splitting',
            note='A codimension-one dominated splitting proxy has been identified near the candidate fixed point.',
            margin=None if domination_margin is None else float(domination_margin),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='proxy_stable_manifold_chart_identified',
            satisfied=str(stable_manifold.get('theorem_status', '')) == 'proxy-stable-manifold-chart-identified',
            source='proxy stable-manifold chart',
            note='The local stable-manifold chart scaffold is fully closed at the proxy level.',
            margin=None if stable_radius is None else float(stable_radius),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='proxy_graph_transform_contracting',
            satisfied=bool(graph_contracting),
            source='proxy stable-manifold graph transform',
            note='The graph-transform proxy is genuinely contracting, so the stable-manifold scaffold is not merely formal.',
            margin=None if graph_contraction is None else float(1.0 - float(graph_contraction)),
        ),
    ]
    return rows, local_margin


def _build_discharge_residual_burden_summary(
    *,
    local_front_complete: bool,
    package_ready: bool,
    open_hypotheses: Sequence[str],
    package_specific_assumptions: Sequence[str],
    upstream_context_assumptions: Sequence[str],
    local_package_margin: float | None,
) -> dict[str, Any]:
    blocking_open = [str(x) for x in open_hypotheses]
    package_specific_assumptions = [str(x) for x in package_specific_assumptions]
    upstream_context_assumptions = [str(x) for x in upstream_context_assumptions]
    if local_front_complete and not package_specific_assumptions:
        status = 'validated-renormalization-package-discharge-ready'
        notes = 'The proxy operator/fixed-point/enclosure/splitting/stable-manifold front is locally packaged, and the package-specific promotion assumptions have been absorbed.'
    elif local_front_complete:
        status = 'validated-renormalization-package-promotion-frontier'
        notes = 'The local renormalization fixed-point core is packaged, so the remaining Workstream-A burden is the theorem-grade validated renormalization package itself.'
    elif package_ready:
        status = 'validated-renormalization-package-isolation-frontier'
        notes = 'The local renormalization core margins are encouraging, but some front hypotheses still prevent the validated package theorem from being isolated sharply.'
    else:
        status = 'renormalization-package-local-prerequisite-frontier'
        notes = 'The operator/fixed-point/splitting/stable-manifold core still has local proxy prerequisites open, so the validated renormalization package is not yet isolated cleanly.'
    return {
        'status': status,
        'local_front_complete': bool(local_front_complete),
        'package_ready': bool(package_ready),
        'blocking_open_hypotheses': blocking_open,
        'package_specific_assumptions': package_specific_assumptions,
        'upstream_context_assumptions': upstream_context_assumptions,
        'local_package_margin': None if local_package_margin is None else float(local_package_margin),
        'true_fixed_point_package_certified': bool(local_front_complete and not package_specific_assumptions),
        'spectral_splitting_citeable': bool(local_front_complete and not package_specific_assumptions),
        'stable_manifold_citeable': bool(local_front_complete and not package_specific_assumptions),
        'papergrade_final': bool(local_front_complete and not package_specific_assumptions and not upstream_context_assumptions),
        'notes': notes,
    }


def build_validated_renormalization_package_discharge_certificate(
    *,
    family: HarmonicFamily | None = None,
    renormalization_class_certificate: Mapping[str, Any] | None = None,
    renormalization_operator_certificate: Mapping[str, Any] | None = None,
    fixed_point_certificate: Mapping[str, Any] | None = None,
    fixed_point_enclosure_certificate: Mapping[str, Any] | None = None,
    spectral_splitting_certificate: Mapping[str, Any] | None = None,
    stable_manifold_certificate: Mapping[str, Any] | None = None,
    active_assumptions: Sequence[str] = (),
) -> ValidatedRenormalizationPackageDischargeCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)
    renorm_class = dict(renormalization_class_certificate or build_renormalization_class_certificate(family, family_label=family_label).to_dict())
    renorm_operator = dict(renormalization_operator_certificate or build_renormalization_operator_certificate(family, family_label=family_label).to_dict())
    fixed_point = dict(fixed_point_certificate or build_renormalization_fixed_point_certificate(family, family_label=family_label).to_dict())
    enclosure = dict(fixed_point_enclosure_certificate or build_fixed_point_enclosure_certificate(family, family_label=family_label).to_dict())
    splitting = dict(spectral_splitting_certificate or build_spectral_splitting_certificate(family, family_label=family_label).to_dict())
    stable_manifold = dict(stable_manifold_certificate or build_stable_manifold_chart_certificate(family, family_label=family_label).to_dict())

    hypotheses, local_margin = _build_local_hypotheses(
        renorm_class=renorm_class,
        renorm_operator=renorm_operator,
        fixed_point=fixed_point,
        enclosure=enclosure,
        splitting=splitting,
        stable_manifold=stable_manifold,
    )
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    local_front_complete = not open_hypotheses
    package_ready = bool(local_front_complete)
    assumptions, package_specific_assumptions, upstream_context_assumptions = _build_assumptions(active_assumptions)
    active_subset = [*package_specific_assumptions, *[x for x in upstream_context_assumptions if x not in package_specific_assumptions]]
    theorem_flags = {
        'local_front_complete': bool(local_front_complete),
        'package_ready': bool(package_ready),
        'validated_operator_proxy_ready': 'proxy_operator_stable_chart_identified' in discharged_hypotheses,
        'validated_fixed_point_proxy_ready': 'proxy_fixed_point_iteration_contracting' in discharged_hypotheses and 'proxy_fixed_point_enclosure_validated' in discharged_hypotheses,
        'validated_splitting_proxy_ready': 'proxy_spectral_splitting_identified' in discharged_hypotheses and 'proxy_stable_manifold_chart_identified' in discharged_hypotheses,
    }
    residual_burden_summary = _build_discharge_residual_burden_summary(
        local_front_complete=local_front_complete,
        package_ready=package_ready,
        open_hypotheses=open_hypotheses,
        package_specific_assumptions=package_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
        local_package_margin=local_margin,
    )
    if local_front_complete:
        theorem_status = 'validated-renormalization-package-discharge-front-complete'
        notes = 'The operator/fixed-point/enclosure/splitting/stable-manifold core is packaged cleanly enough that the remaining burden can be localized as a theorem-grade validated renormalization package.'
    elif discharged_hypotheses:
        theorem_status = 'validated-renormalization-package-discharge-conditional-partial'
        notes = 'A theorem-facing validated renormalization-package discharge object has been assembled, but some local proxy prerequisites remain open.'
    else:
        theorem_status = 'validated-renormalization-package-discharge-failed'
        notes = 'No usable validated renormalization-package discharge object could be assembled from the current certificates.'
    if local_margin is not None and theorem_status != 'validated-renormalization-package-discharge-failed':
        notes += f' Local package margin: {local_margin:.6g}.'
    return ValidatedRenormalizationPackageDischargeCertificate(
        family_label=family_label,
        renormalization_class_certificate=renorm_class,
        renormalization_operator_certificate=renorm_operator,
        fixed_point_certificate=fixed_point,
        fixed_point_enclosure_certificate=enclosure,
        spectral_splitting_certificate=splitting,
        stable_manifold_certificate=stable_manifold,
        local_package_margin=local_margin,
        local_front_complete=bool(local_front_complete),
        package_ready=bool(package_ready),
        package_specific_assumptions=package_specific_assumptions,
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


def _build_promotion_hypotheses(
    *,
    local_front_complete: bool,
    promotion_theorem_ready: bool,
    promotion_theorem_available: bool,
    promotion_theorem_discharged: bool,
    promotion_margin: float | None,
    package_specific_assumptions: Sequence[str],
    upstream_context_assumptions: Sequence[str],
) -> list[ValidatedRenormalizationPackageHypothesisRow]:
    return [
        ValidatedRenormalizationPackageHypothesisRow(
            name='validated_renormalization_package_discharge_front_complete',
            satisfied=bool(local_front_complete),
            source='validated renormalization package discharge certificate',
            note='The operator/fixed-point/enclosure/splitting/stable-manifold core is locally packaged with no remaining proxy-front hypotheses open.',
            margin=None if promotion_margin is None else float(promotion_margin),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='validated_renormalization_package_promotion_theorem_ready',
            satisfied=bool(promotion_theorem_ready),
            source='validated renormalization package promotion synthesis',
            note='The local proxy renormalization package is packaged sharply enough that the remaining burden can be promoted into a theorem-facing validated renormalization package statement.',
            margin=None if promotion_margin is None else float(promotion_margin),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='validated_renormalization_package_promotion_theorem_available',
            satisfied=bool(promotion_theorem_available),
            source='validated renormalization package promotion theorem',
            note='The package-specific renormalization assumptions have been absorbed, so the repository now exposes the theorem-facing validated renormalization package object.',
            margin=None if promotion_margin is None else float(promotion_margin),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='validated_renormalization_package_promotion_theorem_discharged',
            satisfied=bool(promotion_theorem_discharged),
            source='validated renormalization package promotion theorem',
            note='Both the validated renormalization package and its broader Workstream context assumptions are discharged at the current theorem-facing level.',
            margin=None if promotion_margin is None else float(promotion_margin),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='package_specific_assumptions_absorbed_by_promotion_theorem',
            satisfied=not package_specific_assumptions,
            source='promotion theorem assumption accounting',
            note='The promotion theorem no longer leaves package-specific renormalization assumptions exposed downstream.',
            margin=float(len(PACKAGE_SPECIFIC_ASSUMPTIONS) - len(list(package_specific_assumptions))),
        ),
        ValidatedRenormalizationPackageHypothesisRow(
            name='upstream_context_assumptions_absorbed',
            satisfied=not upstream_context_assumptions,
            source='promotion theorem assumption accounting',
            note='The broader Workstream-A context assumptions have also been absorbed, so the renormalization package theorem is fully discharged rather than only conditionally strong.',
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
    package_specific_assumptions: Sequence[str],
    upstream_context_assumptions: Sequence[str],
    promotion_margin: float | None,
) -> dict[str, Any]:
    blocking_open = [str(x) for x in open_hypotheses]
    package_specific_assumptions = [str(x) for x in package_specific_assumptions]
    upstream_context_assumptions = [str(x) for x in upstream_context_assumptions]
    if promotion_theorem_discharged:
        status = 'validated-renormalization-package-discharged'
        notes = 'The Workstream-A side now carries a fully discharged theorem-facing validated renormalization package object.'
    elif promotion_theorem_available:
        status = 'validated-renormalization-package-conditional-strong'
        notes = 'The Workstream-A side now carries the theorem-facing validated renormalization package object, conditional only on the broader universality-class context.'
    elif promotion_theorem_ready:
        status = 'validated-renormalization-package-frontier'
        notes = 'The local discharge prerequisites are packaged, so the remaining Workstream-A burden is precisely the theorem-grade validated renormalization package.'
    elif local_front_complete:
        status = 'validated-renormalization-package-promotion-isolation-frontier'
        notes = 'The local discharge object is front-complete, but the promotion theorem is not yet isolated sharply enough to count as the sole remaining renormalization-package burden.'
    else:
        status = 'validated-renormalization-package-local-prerequisite-frontier'
        notes = 'The operator/fixed-point/splitting/stable-manifold core still has local prerequisites open before the validated renormalization package can be promoted.'
    return {
        'status': status,
        'local_front_complete': bool(local_front_complete),
        'promotion_theorem_ready': bool(promotion_theorem_ready),
        'promotion_theorem_available': bool(promotion_theorem_available),
        'promotion_theorem_discharged': bool(promotion_theorem_discharged),
        'blocking_open_hypotheses': blocking_open,
        'package_specific_assumptions': package_specific_assumptions,
        'upstream_context_assumptions': upstream_context_assumptions,
        'promotion_margin': None if promotion_margin is None else float(promotion_margin),
        'true_fixed_point_package_certified': bool(promotion_theorem_discharged),
        'spectral_splitting_citeable': bool(promotion_theorem_discharged),
        'stable_manifold_citeable': bool(promotion_theorem_discharged),
        'papergrade_final': bool(promotion_theorem_discharged),
        'notes': notes,
    }


def build_validated_renormalization_package_promotion_certificate(
    *,
    family: HarmonicFamily | None = None,
    discharge_certificate: Mapping[str, Any] | None = None,
    renormalization_class_certificate: Mapping[str, Any] | None = None,
    renormalization_operator_certificate: Mapping[str, Any] | None = None,
    fixed_point_certificate: Mapping[str, Any] | None = None,
    fixed_point_enclosure_certificate: Mapping[str, Any] | None = None,
    spectral_splitting_certificate: Mapping[str, Any] | None = None,
    stable_manifold_certificate: Mapping[str, Any] | None = None,
    active_assumptions: Sequence[str] = (),
) -> ValidatedRenormalizationPackagePromotionCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)
    if discharge_certificate is not None:
        discharge_cert = dict(discharge_certificate)
    else:
        discharge_cert = build_validated_renormalization_package_discharge_certificate(
            family=family,
            renormalization_class_certificate=renormalization_class_certificate,
            renormalization_operator_certificate=renormalization_operator_certificate,
            fixed_point_certificate=fixed_point_certificate,
            fixed_point_enclosure_certificate=fixed_point_enclosure_certificate,
            spectral_splitting_certificate=spectral_splitting_certificate,
            stable_manifold_certificate=stable_manifold_certificate,
            active_assumptions=active_assumptions,
        ).to_dict()

    promotion_margin = None if discharge_cert.get('local_package_margin') is None else float(discharge_cert.get('local_package_margin'))
    local_front_complete = bool(discharge_cert.get('local_front_complete', False))
    promotion_theorem_ready = bool(discharge_cert.get('package_ready', False))
    package_specific_assumptions = [str(x) for x in discharge_cert.get('package_specific_assumptions', [])]
    upstream_context_assumptions = [str(x) for x in discharge_cert.get('upstream_context_assumptions', [])]
    promotion_theorem_available = bool(local_front_complete and not package_specific_assumptions)
    promotion_theorem_discharged = bool(promotion_theorem_available and not upstream_context_assumptions)

    assumptions, _, _ = _build_assumptions([*package_specific_assumptions, *upstream_context_assumptions])
    active_subset = [str(x) for x in package_specific_assumptions] + [str(x) for x in upstream_context_assumptions if str(x) not in package_specific_assumptions]
    hypotheses = _build_promotion_hypotheses(
        local_front_complete=local_front_complete,
        promotion_theorem_ready=promotion_theorem_ready,
        promotion_theorem_available=promotion_theorem_available,
        promotion_theorem_discharged=promotion_theorem_discharged,
        promotion_margin=promotion_margin,
        package_specific_assumptions=package_specific_assumptions,
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
        package_specific_assumptions=package_specific_assumptions,
        upstream_context_assumptions=upstream_context_assumptions,
        promotion_margin=promotion_margin,
    )
    theorem_flags = {
        'local_front_complete': bool(local_front_complete),
        'promotion_theorem_ready': bool(promotion_theorem_ready),
        'promotion_theorem_available': bool(promotion_theorem_available),
        'validated_true_renormalization_fixed_point_package_available': bool(promotion_theorem_available),
        'promotion_theorem_discharged': bool(promotion_theorem_discharged),
        'true_fixed_point_package_certified': bool(promotion_theorem_discharged),
        'spectral_splitting_citeable': bool(promotion_theorem_discharged),
        'stable_manifold_citeable': bool(promotion_theorem_discharged),
        'papergrade_final': bool(promotion_theorem_discharged),
    }
    if promotion_theorem_discharged:
        theorem_status = 'validated-renormalization-package-promotion-theorem-discharged'
        notes = 'The theorem-facing validated renormalization package is fully discharged at the current theorem-facing level.'
    elif promotion_theorem_available:
        theorem_status = 'validated-renormalization-package-promotion-theorem-conditional-strong'
        notes = 'The Workstream-A side now exposes the theorem-facing validated renormalization package, conditional only on the broader universality-class context assumptions.'
    elif promotion_theorem_ready:
        theorem_status = 'validated-renormalization-package-promotion-theorem-front-complete'
        notes = 'The local renormalization core is packaged strongly enough that the remaining burden is exactly the theorem-grade validated renormalization package.'
    elif local_front_complete or discharge_cert.get('theorem_status'):
        theorem_status = 'validated-renormalization-package-promotion-theorem-conditional-partial'
        notes = 'A theorem-facing validated renormalization package object has been assembled, but the local discharge package is not yet strong enough to isolate it as the sole remaining burden.'
    else:
        theorem_status = 'validated-renormalization-package-promotion-theorem-failed'
        notes = 'No usable theorem-facing validated renormalization package object could be assembled from the current discharge certificate.'
    if promotion_margin is not None and theorem_status != 'validated-renormalization-package-promotion-theorem-failed':
        notes += f' Promotion margin: {promotion_margin:.6g}.'
    return ValidatedRenormalizationPackagePromotionCertificate(
        family_label=family_label,
        discharge_certificate=discharge_cert,
        promotion_margin=promotion_margin,
        local_front_complete=bool(local_front_complete),
        promotion_theorem_ready=bool(promotion_theorem_ready),
        promotion_theorem_available=bool(promotion_theorem_available),
        promotion_theorem_discharged=bool(promotion_theorem_discharged),
        package_specific_assumptions=package_specific_assumptions,
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
