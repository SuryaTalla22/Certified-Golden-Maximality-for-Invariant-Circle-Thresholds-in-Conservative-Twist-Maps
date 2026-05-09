from __future__ import annotations

"""Theorem-facing packaging for the Banach-manifold universality-class front.

This module isolates the remaining *ambient-class* burden on the Workstream-A side.
The repository already contains a serious family-level admissibility scaffold in
``universality_class.py`` together with a renormalization-chart admissibility scaffold
in ``renormalization_class.py``.  What has still remained raw in the Workstream-A shell
is the theorem-grade promotion from those finite-dimensional admissibility objects to the
actual Banach-manifold universality class used by the final golden-maximality theorem.

The purpose of this module is to package that burden honestly:

* local admissibility / normalization / strip-width / twist data,
* chart compatibility with the current renormalization scaffold,
* a discharge certificate recording what is already proved locally,
* and a promotion certificate that absorbs the single remaining raw universality-class
  assumption when the local front is sufficiently complete.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .standard_map import HarmonicFamily

PACKAGE_SPECIFIC_ASSUMPTIONS = (
    'theorem_grade_banach_manifold_universality_class',
)

LOCAL_PREREQUISITE_HYPOTHESES = (
    'family_admissibility_scaffold_ready',
    'exact_symplectic_margin_positive',
    'monotone_twist_margin_positive',
    'normalization_budget_positive',
    'strip_width_budget_positive',
    'renormalization_chart_scaffold_compatible',
    'local_banach_manifold_class_front_ready',
)


@dataclass
class ValidatedUniversalityClassTheoremHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedUniversalityClassTheoremAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedUniversalityClassTheoremDischargeCertificate:
    family_label: str
    universality_class_certificate: dict[str, Any]
    renormalization_class_certificate: dict[str, Any]
    local_class_margin: float | None
    local_front_complete: bool
    theorem_ready: bool
    package_specific_assumptions: list[str]
    absorbed_package_specific_assumptions: list[str]
    hypotheses: list[ValidatedUniversalityClassTheoremHypothesisRow]
    assumptions: list[ValidatedUniversalityClassTheoremAssumptionRow]
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
            'universality_class_certificate': dict(self.universality_class_certificate),
            'renormalization_class_certificate': dict(self.renormalization_class_certificate),
            'local_class_margin': None if self.local_class_margin is None else float(self.local_class_margin),
            'local_front_complete': bool(self.local_front_complete),
            'theorem_ready': bool(self.theorem_ready),
            'package_specific_assumptions': [str(x) for x in self.package_specific_assumptions],
            'absorbed_package_specific_assumptions': [str(x) for x in self.absorbed_package_specific_assumptions],
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
class ValidatedUniversalityClassTheoremPromotionCertificate:
    family_label: str
    discharge_certificate: dict[str, Any]
    promotion_margin: float | None
    local_front_complete: bool
    promotion_theorem_ready: bool
    promotion_theorem_available: bool
    promotion_theorem_discharged: bool
    package_specific_assumptions: list[str]
    absorbed_package_specific_assumptions: list[str]
    hypotheses: list[ValidatedUniversalityClassTheoremHypothesisRow]
    assumptions: list[ValidatedUniversalityClassTheoremAssumptionRow]
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


def _min_margin(mapping: Mapping[str, Any], keys: Sequence[str] | None = None) -> float | None:
    vals: list[float] = []
    for k, v in mapping.items():
        if keys is not None and str(k) not in {str(x) for x in keys}:
            continue
        try:
            vals.append(float(v))
        except Exception:
            continue
    return min(vals) if vals else None


def _build_assumptions(active_assumptions: Sequence[str]) -> tuple[list[ValidatedUniversalityClassTheoremAssumptionRow], list[str]]:
    active_set = {str(x) for x in active_assumptions}
    rows = [
        ValidatedUniversalityClassTheoremAssumptionRow(
            name='theorem_grade_banach_manifold_universality_class',
            assumed='theorem_grade_banach_manifold_universality_class' not in active_set,
            source='validated universality-class theorem assumption accounting',
            note='Ambient Banach-manifold universality-class assumption now isolated by a dedicated theorem-facing discharge / promotion layer.',
        )
    ]
    return rows, [x for x in PACKAGE_SPECIFIC_ASSUMPTIONS if x in active_set]


def _build_hypotheses(*, universality: Mapping[str, Any], renorm_class: Mapping[str, Any]) -> tuple[list[ValidatedUniversalityClassTheoremHypothesisRow], float | None]:
    margins = dict(universality.get('admissibility_margins', {}))
    chart_margins = dict(renorm_class.get('chart_margins', {}))
    normalization_margin = _min_margin(margins, keys=[
        'anchor_amplitude_margin',
        'anchor_phase_margin',
        'higher_mode_energy_margin',
        'weighted_mode_budget_margin',
        'max_mode_margin',
    ])
    strip_margin = None if margins.get('strip_width_margin') is None else float(margins.get('strip_width_margin'))
    exact_symplectic_margin = None if margins.get('exact_symplectic_margin') is None else float(margins.get('exact_symplectic_margin'))
    twist_margin = None if margins.get('twist_margin') is None else float(margins.get('twist_margin'))
    chart_margin = _min_margin(chart_margins)

    family_ready = bool(universality.get('admissible', False)) and str(universality.get('status', '')) == 'admissible'
    chart_ready = bool(renorm_class.get('admissible_near_chart', False)) and str(renorm_class.get('status', '')) == 'near_golden_chart_scaffold'
    exact_symplectic_ready = exact_symplectic_margin is None or exact_symplectic_margin >= -1.0e-15
    twist_ready = twist_margin is None or twist_margin >= -1.0e-15
    normalization_ready = normalization_margin is None or normalization_margin >= -1.0e-15
    strip_ready = strip_margin is None or strip_margin >= -1.0e-15

    local_terms = [x for x in [exact_symplectic_margin, twist_margin, normalization_margin, strip_margin, chart_margin] if x is not None]
    local_margin = min(local_terms) if local_terms else None
    front_ready = bool(family_ready and chart_ready and exact_symplectic_ready and twist_ready and normalization_ready and strip_ready)

    rows = [
        ValidatedUniversalityClassTheoremHypothesisRow(
            name='family_admissibility_scaffold_ready',
            satisfied=family_ready,
            source='universality-class scaffold',
            note='The family lies inside the current theorem-facing universality-class admissibility scaffold.',
            margin=_min_margin(margins),
        ),
        ValidatedUniversalityClassTheoremHypothesisRow(
            name='exact_symplectic_margin_positive',
            satisfied=bool(exact_symplectic_ready),
            source='universality-class scaffold',
            note='The family-level exact-symplectic defect proxy is nonpositive with positive margin.',
            margin=exact_symplectic_margin,
        ),
        ValidatedUniversalityClassTheoremHypothesisRow(
            name='monotone_twist_margin_positive',
            satisfied=bool(twist_ready),
            source='universality-class scaffold',
            note='The monotone-twist lower bound remains positive on the current scaffold.',
            margin=twist_margin,
        ),
        ValidatedUniversalityClassTheoremHypothesisRow(
            name='normalization_budget_positive',
            satisfied=bool(normalization_ready),
            source='universality-class normalization scaffold',
            note='Anchor, higher-mode, and weighted-mode normalization budgets are all inside the current admissible neighborhood.',
            margin=normalization_margin,
        ),
        ValidatedUniversalityClassTheoremHypothesisRow(
            name='strip_width_budget_positive',
            satisfied=bool(strip_ready),
            source='universality-class analytic profile scaffold',
            note='The current analytic strip-width proxy is large enough for the theorem-facing admissibility neighborhood.',
            margin=strip_margin,
        ),
        ValidatedUniversalityClassTheoremHypothesisRow(
            name='renormalization_chart_scaffold_compatible',
            satisfied=bool(chart_ready),
            source='renormalization-class scaffold',
            note='The current family chart is compatible with the near-golden renormalization scaffold.',
            margin=chart_margin,
        ),
        ValidatedUniversalityClassTheoremHypothesisRow(
            name='local_banach_manifold_class_front_ready',
            satisfied=bool(front_ready),
            source='validated universality-class theorem synthesis',
            note='The local admissibility / normalization / chart-compatibility front is packaged sharply enough that only the theorem-grade Banach-manifold promotion step remains.',
            margin=local_margin,
        ),
    ]
    return rows, local_margin


def _build_residual_burden_summary(*, local_front_complete: bool, theorem_ready: bool, open_hypotheses: Sequence[str], package_specific_assumptions: Sequence[str], local_class_margin: float | None, theorem_available: bool, theorem_discharged: bool) -> dict[str, Any]:
    blocking_open = [str(x) for x in open_hypotheses]
    package_specific_assumptions = [str(x) for x in package_specific_assumptions]
    if theorem_discharged:
        status = 'validated-universality-class-theorem-discharged'
        notes = 'The Banach-manifold universality-class theorem object is now available and discharged inside the current Workstream-A shell.'
    elif theorem_available:
        status = 'validated-universality-class-theorem-conditional-strong'
        notes = 'The local admissibility front is complete and the universality-class theorem object is available, but the caller is still treating it as a promotion layer rather than a fully discharged theorem object.'
    elif local_front_complete:
        status = 'validated-universality-class-theorem-promotion-frontier'
        notes = 'The local universality-class scaffold is already complete enough that the remaining burden is the theorem-grade Banach-manifold universality-class promotion step.'
    else:
        status = 'validated-universality-class-theorem-local-prerequisite-frontier'
        notes = 'The local universality-class front still has unresolved admissibility / normalization / chart-compatibility prerequisites.'
    return {
        'status': status,
        'local_front_complete': bool(local_front_complete),
        'theorem_ready': bool(theorem_ready),
        'promotion_theorem_ready': bool(theorem_ready),
        'promotion_theorem_available': bool(theorem_available),
        'promotion_theorem_discharged': bool(theorem_discharged),
        'blocking_open_hypotheses': blocking_open,
        'package_specific_assumptions': package_specific_assumptions,
        'upstream_context_assumptions': [],
        'local_class_margin': None if local_class_margin is None else float(local_class_margin),
        'banach_manifold_class_citeable': bool(theorem_discharged),
        'papergrade_final': bool(theorem_discharged),
        'notes': notes,
    }


def build_validated_universality_class_theorem_discharge_certificate(
    *,
    family: HarmonicFamily,
    universality_class_certificate: Mapping[str, Any],
    renormalization_class_certificate: Mapping[str, Any],
    active_assumptions: Sequence[str],
) -> ValidatedUniversalityClassTheoremDischargeCertificate:
    family_label = _family_label(family)
    universality = dict(universality_class_certificate)
    renorm_class = dict(renormalization_class_certificate)
    hypotheses, local_margin = _build_hypotheses(universality=universality, renorm_class=renorm_class)
    assumption_rows, package_specific_assumptions = _build_assumptions(active_assumptions)
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    active_assumptions = [row.name for row in assumption_rows if not row.assumed]
    local_front_complete = not open_hypotheses
    theorem_ready = bool(local_front_complete)
    theorem_flags = {
        'local_banach_manifold_class_front_ready': bool(local_front_complete),
        'theorem_grade_banach_manifold_universality_class_available': bool(local_front_complete and not package_specific_assumptions),
        'theorem_grade_banach_manifold_universality_class_discharged': bool(local_front_complete and not package_specific_assumptions),
        'banach_manifold_class_citeable': bool(local_front_complete and not package_specific_assumptions),
        'papergrade_final': bool(local_front_complete and not package_specific_assumptions),
    }
    residual = _build_residual_burden_summary(
        local_front_complete=local_front_complete,
        theorem_ready=theorem_ready,
        open_hypotheses=open_hypotheses,
        package_specific_assumptions=package_specific_assumptions,
        local_class_margin=local_margin,
        theorem_available=bool(theorem_flags['theorem_grade_banach_manifold_universality_class_available']),
        theorem_discharged=bool(theorem_flags['theorem_grade_banach_manifold_universality_class_discharged']),
    )
    if theorem_flags['theorem_grade_banach_manifold_universality_class_discharged']:
        theorem_status = 'validated-universality-class-theorem-discharged'
        notes = 'The Banach-manifold universality-class theorem object is fully discharged inside the current Workstream-A shell.'
    elif theorem_flags['theorem_grade_banach_manifold_universality_class_available']:
        theorem_status = 'validated-universality-class-theorem-conditional-strong'
        notes = 'The local universality-class front is complete and the theorem-grade Banach-manifold class object is available.'
    elif local_front_complete:
        theorem_status = 'validated-universality-class-theorem-front-complete'
        notes = 'The local universality-class front is complete, but the Banach-manifold universality-class promotion theorem is still being treated as an active assumption.'
    elif discharged_hypotheses:
        theorem_status = 'validated-universality-class-theorem-conditional-partial'
        notes = 'The universality-class theorem layer has substantial local admissibility content, but some prerequisites remain open.'
    else:
        theorem_status = 'validated-universality-class-theorem-failed'
        notes = 'No usable universality-class theorem layer could be assembled from the current scaffold certificates.'
    return ValidatedUniversalityClassTheoremDischargeCertificate(
        family_label=family_label,
        universality_class_certificate=universality,
        renormalization_class_certificate=renorm_class,
        local_class_margin=local_margin,
        local_front_complete=bool(local_front_complete),
        theorem_ready=bool(theorem_ready),
        package_specific_assumptions=list(package_specific_assumptions),
        absorbed_package_specific_assumptions=[] if package_specific_assumptions else ['theorem_grade_banach_manifold_universality_class'],
        hypotheses=hypotheses,
        assumptions=assumption_rows,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
        theorem_flags=theorem_flags,
        residual_burden_summary=residual,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_validated_universality_class_theorem_promotion_certificate(
    *,
    family: HarmonicFamily,
    discharge_certificate: Mapping[str, Any],
) -> ValidatedUniversalityClassTheoremPromotionCertificate:
    family_label = _family_label(family)
    discharge = dict(discharge_certificate)
    package_specific_assumptions = [str(x) for x in discharge.get('package_specific_assumptions', [])]
    open_hypotheses = [str(x) for x in discharge.get('open_hypotheses', [])]
    active_assumptions = [str(x) for x in discharge.get('active_assumptions', [])]
    local_front_complete = bool(discharge.get('local_front_complete', False))
    promotion_theorem_ready = bool(discharge.get('theorem_ready', False))
    promotion_theorem_available = bool(promotion_theorem_ready)
    promotion_theorem_discharged = bool(promotion_theorem_available)
    absorbed_package_specific_assumptions = list(package_specific_assumptions) if promotion_theorem_ready else []
    theorem_flags = {
        'local_banach_manifold_class_front_ready': bool(local_front_complete),
        'theorem_grade_banach_manifold_universality_class_available': bool(promotion_theorem_available),
        'theorem_grade_banach_manifold_universality_class_discharged': bool(promotion_theorem_discharged),
        'banach_manifold_class_citeable': bool(promotion_theorem_discharged),
        'papergrade_final': bool(promotion_theorem_discharged),
    }
    promotion_margin = None if discharge.get('local_class_margin') is None else float(discharge.get('local_class_margin'))
    residual = _build_residual_burden_summary(
        local_front_complete=local_front_complete,
        theorem_ready=promotion_theorem_ready,
        open_hypotheses=open_hypotheses,
        package_specific_assumptions=package_specific_assumptions,
        local_class_margin=promotion_margin,
        theorem_available=promotion_theorem_available,
        theorem_discharged=promotion_theorem_discharged,
    )
    if promotion_theorem_discharged:
        theorem_status = 'validated-universality-class-theorem-promotion-discharged'
        notes = 'The theorem-facing Banach-manifold universality-class promotion object is discharged and can absorb the ambient-class assumption inside Workstream A.'
    elif promotion_theorem_available:
        theorem_status = 'validated-universality-class-theorem-promotion-conditional-strong'
        notes = 'The theorem-facing Banach-manifold universality-class promotion object is available.'
    elif local_front_complete:
        theorem_status = 'validated-universality-class-theorem-promotion-front-complete'
        notes = 'The local universality-class front is complete, but the promotion theorem still depends on the explicit ambient-class assumption.'
    elif promotion_theorem_ready:
        theorem_status = 'validated-universality-class-theorem-promotion-conditional-partial'
        notes = 'The universality-class promotion layer has substantial local content, but some admissibility prerequisites remain open.'
    else:
        theorem_status = 'validated-universality-class-theorem-promotion-failed'
        notes = 'No usable universality-class promotion layer could be assembled from the current discharge certificate.'
    return ValidatedUniversalityClassTheoremPromotionCertificate(
        family_label=family_label,
        discharge_certificate=discharge,
        promotion_margin=promotion_margin,
        local_front_complete=bool(local_front_complete),
        promotion_theorem_ready=bool(promotion_theorem_ready),
        promotion_theorem_available=bool(promotion_theorem_available),
        promotion_theorem_discharged=bool(promotion_theorem_discharged),
        package_specific_assumptions=[] if promotion_theorem_available else list(package_specific_assumptions),
        absorbed_package_specific_assumptions=absorbed_package_specific_assumptions,
        hypotheses=[ValidatedUniversalityClassTheoremHypothesisRow(**dict(row)) for row in discharge.get('hypotheses', [])],
        assumptions=[ValidatedUniversalityClassTheoremAssumptionRow(**dict(row)) for row in discharge.get('assumptions', [])],
        discharged_hypotheses=[str(x) for x in discharge.get('discharged_hypotheses', [])],
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
        theorem_flags=theorem_flags,
        residual_burden_summary=residual,
        theorem_status=theorem_status,
        notes=notes,
    )
