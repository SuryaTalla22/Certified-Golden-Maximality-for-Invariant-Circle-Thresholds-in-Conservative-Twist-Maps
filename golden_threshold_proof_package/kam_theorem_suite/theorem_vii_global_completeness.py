from __future__ import annotations

"""Theorem-facing global challenger-completeness packaging for Theorem VII.

This module sits one level above the near-top screened-panel dominance front.
The repository already knows how to build a finite screened challenger panel and
how to show, in good cases, that this current panel is dominated by the golden
class. What remains globally missing is the theorem-grade step proving that the
screened panel is genuinely complete near the top and that omitted non-golden
irrational classes are controlled outside that panel.

The goal here is not to overclaim that theorem. Instead this module packages the
current global burden explicitly, distinguishes support-side global assumptions
from the final completeness assumptions, and records whether the global burden
has reached a theorem-promotion frontier.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .class_exhaustion_screen import (
    build_near_top_threat_set_partition_certificate,
    promote_omitted_class_global_control_certificate,
    promote_screened_panel_global_completeness_certificate,
)

GLOBAL_SUPPORT_ASSUMPTIONS = {
    'exact_near_top_lagrange_spectrum_ranking',
    'theorem_level_pruning_of_dominated_regions',
    'deferred_or_retired_classes_are_globally_dominated',
    'termination_search_promotes_to_theorem_exclusion',
}

GLOBAL_COMPLETENESS_ASSUMPTIONS = {
    'finite_screened_panel_is_globally_complete',
    'omitted_nongolden_irrationals_outside_screened_panel_controlled',
}

_SUPPORT_CERTIFICATE_SPECS = {
    'exact_near_top_lagrange_spectrum_ranking': ('exact_near_top_lagrange_spectrum_ranking_certificate', 'proves_exact_near_top_lagrange_spectrum_ranking'),
    'theorem_level_pruning_of_dominated_regions': ('theorem_level_pruning_certificate', 'proves_theorem_level_pruning_of_dominated_regions'),
    'deferred_or_retired_classes_are_globally_dominated': ('deferred_retired_domination_certificate', 'proves_deferred_or_retired_classes_are_globally_dominated'),
    'termination_search_promotes_to_theorem_exclusion': ('termination_search_exclusion_certificate', 'proves_termination_search_promotes_to_theorem_exclusion'),
    'finite_screened_panel_is_globally_complete': ('screened_panel_global_completeness_certificate', 'screened_panel_globally_complete'),
    'omitted_nongolden_irrationals_outside_screened_panel_controlled': ('omitted_class_global_control_certificate', 'omitted_classes_globally_controlled'),
}


@dataclass
class TheoremVIIGlobalCompletenessHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVIIGlobalCompletenessAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremVIIGlobalCompletenessCertificate:
    family_label: str
    theorem_vii_shell: dict[str, Any]
    current_screened_panel_dominance_certificate: dict[str, Any]
    near_top_threat_set_partition_certificate: dict[str, Any]
    support_certificates: dict[str, Any]
    readiness_summary: dict[str, Any]
    residual_burden_summary: dict[str, Any]
    hypotheses: list[TheoremVIIGlobalCompletenessHypothesisRow]
    assumptions: list[TheoremVIIGlobalCompletenessAssumptionRow]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    local_active_assumptions: list[str]
    upstream_active_assumptions: list[str]
    active_assumptions: list[str]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'family_label': str(self.family_label),
            'theorem_vii_shell': dict(self.theorem_vii_shell),
            'current_screened_panel_dominance_certificate': dict(self.current_screened_panel_dominance_certificate),
            'near_top_threat_set_partition_certificate': dict(self.near_top_threat_set_partition_certificate),
            'support_certificates': {str(k): dict(v) for k, v in self.support_certificates.items()},
            'readiness_summary': dict(self.readiness_summary),
            'residual_burden_summary': dict(self.residual_burden_summary),
            'hypotheses': [row.to_dict() for row in self.hypotheses],
            'assumptions': [row.to_dict() for row in self.assumptions],
            'discharged_hypotheses': [str(x) for x in self.discharged_hypotheses],
            'open_hypotheses': [str(x) for x in self.open_hypotheses],
            'local_active_assumptions': [str(x) for x in self.local_active_assumptions],
            'upstream_active_assumptions': [str(x) for x in self.upstream_active_assumptions],
            'active_assumptions': [str(x) for x in self.active_assumptions],
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


def _coerce_assumption_rows(rows: Sequence[Mapping[str, Any]]) -> list[TheoremVIIGlobalCompletenessAssumptionRow]:
    out: list[TheoremVIIGlobalCompletenessAssumptionRow] = []
    for row in rows:
        out.append(
            TheoremVIIGlobalCompletenessAssumptionRow(
                name=str(row.get('name', 'unknown-assumption')),
                assumed=bool(row.get('assumed', False)),
                source=str(row.get('source', 'Theorem-VII global completeness assumption')),
                note=str(row.get('note', '')),
            )
        )
    return out


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _extract_support_certificates(theorem_vii: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    support_certificates = dict(theorem_vii.get('support_certificates', {}))
    for cert_name, _ in _SUPPORT_CERTIFICATE_SPECS.values():
        if cert_name in theorem_vii and cert_name not in support_certificates:
            raw = theorem_vii.get(cert_name)
            if isinstance(raw, Mapping):
                support_certificates[cert_name] = dict(raw)
    return {str(k): dict(v) for k, v in support_certificates.items() if isinstance(v, Mapping)}


def _augment_support_certificates(
    support_certificates: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    augmented = {str(k): dict(v) for k, v in support_certificates.items()}
    screened_panel_global_completeness_certificate = promote_screened_panel_global_completeness_certificate(
        screened_panel_certificate=augmented.get('screened_panel_global_completeness_certificate', {}),
        arithmetic_ranking_certificate=augmented.get('exact_near_top_lagrange_spectrum_ranking_certificate', {}),
        pruning_region_certificate=augmented.get('theorem_level_pruning_certificate', {}),
        deferred_retired_domination_certificate=augmented.get('deferred_retired_domination_certificate', {}),
        termination_exclusion_promotion_certificate=augmented.get('termination_search_exclusion_certificate', {}),
    )
    near_top_threat_set_partition_certificate = build_near_top_threat_set_partition_certificate(
        screened_panel_certificate=screened_panel_global_completeness_certificate,
        arithmetic_ranking_certificate=augmented.get('exact_near_top_lagrange_spectrum_ranking_certificate', {}),
        pruning_region_certificate=augmented.get('theorem_level_pruning_certificate', {}),
        deferred_retired_domination_certificate=augmented.get('deferred_retired_domination_certificate', {}),
        termination_exclusion_promotion_certificate=augmented.get('termination_search_exclusion_certificate', {}),
    )
    omitted_class_global_control_certificate = promote_omitted_class_global_control_certificate(
        omitted_control_certificate=augmented.get('omitted_class_global_control_certificate', {}),
        partition_certificate=near_top_threat_set_partition_certificate,
        screened_panel_certificate=screened_panel_global_completeness_certificate,
        arithmetic_ranking_certificate=augmented.get('exact_near_top_lagrange_spectrum_ranking_certificate', {}),
        pruning_region_certificate=augmented.get('theorem_level_pruning_certificate', {}),
        deferred_retired_domination_certificate=augmented.get('deferred_retired_domination_certificate', {}),
        termination_exclusion_promotion_certificate=augmented.get('termination_search_exclusion_certificate', {}),
    )
    augmented['screened_panel_global_completeness_certificate'] = screened_panel_global_completeness_certificate
    augmented['near_top_threat_set_partition_certificate'] = near_top_threat_set_partition_certificate
    augmented['omitted_class_global_control_certificate'] = omitted_class_global_control_certificate
    return augmented, near_top_threat_set_partition_certificate


def _certificate_proves(support_certificates: Mapping[str, Mapping[str, Any]], assumption_name: str) -> bool:
    cert_name, proof_key = _SUPPORT_CERTIFICATE_SPECS[assumption_name]
    cert = dict(support_certificates.get(cert_name, {}))
    return bool(cert.get(proof_key, False))


def _discharged_local_active_assumptions(
    local_active_assumptions: Sequence[str],
    support_certificates: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    return [
        str(name) for name in local_active_assumptions
        if not (_SUPPORT_CERTIFICATE_SPECS.get(str(name)) and _certificate_proves(support_certificates, str(name)))
    ]


def _update_assumption_rows(
    assumptions: Sequence[TheoremVIIGlobalCompletenessAssumptionRow],
    support_certificates: Mapping[str, Mapping[str, Any]],
) -> list[TheoremVIIGlobalCompletenessAssumptionRow]:
    updated: list[TheoremVIIGlobalCompletenessAssumptionRow] = []
    for row in assumptions:
        assumed = bool(row.assumed)
        source = row.source
        if row.name in _SUPPORT_CERTIFICATE_SPECS and _certificate_proves(support_certificates, row.name):
            cert_name, _ = _SUPPORT_CERTIFICATE_SPECS[row.name]
            cert = dict(support_certificates.get(cert_name, {}))
            assumed = True
            source = str(cert.get('status', cert_name))
        updated.append(
            TheoremVIIGlobalCompletenessAssumptionRow(
                name=row.name,
                assumed=assumed,
                source=source,
                note=row.note,
            )
        )
    return updated


def _build_readiness_summary(
    *,
    local_front_hypotheses: Sequence[str],
    local_active_assumptions: Sequence[str],
    upstream_active_assumptions: Sequence[str],
    current_screened_panel_dominance_certificate: Mapping[str, Any],
) -> dict[str, Any]:
    local_front_hypotheses = [str(x) for x in local_front_hypotheses]
    local_active_assumptions = [str(x) for x in local_active_assumptions]
    upstream_active_assumptions = [str(x) for x in upstream_active_assumptions]
    support_assumptions = [x for x in local_active_assumptions if x in GLOBAL_SUPPORT_ASSUMPTIONS]
    completion_assumptions = [x for x in local_active_assumptions if x in GLOBAL_COMPLETENESS_ASSUMPTIONS]
    near_top_closed = bool(current_screened_panel_dominance_certificate.get('near_top_frontier_closed', False))
    local_front_ready = near_top_closed and len(local_front_hypotheses) == 0
    support_ready = len(support_assumptions) == 0
    promotion_ready = local_front_ready and support_ready
    full_global_ready = promotion_ready and len(completion_assumptions) == 0

    if not local_front_ready:
        status = 'global-completeness-not-ready'
    elif promotion_ready and not completion_assumptions and not upstream_active_assumptions:
        status = 'global-completeness-theorem-ready'
    elif promotion_ready and not completion_assumptions:
        status = 'global-completeness-locally-ready-with-upstream-burden'
    elif promotion_ready:
        status = 'global-completeness-promotion-frontier'
    elif local_front_ready:
        status = 'global-exhaustion-support-frontier'
    else:
        status = 'global-completeness-not-ready'

    return {
        'status': status,
        'near_top_frontier_closed': near_top_closed,
        'local_front_ready': local_front_ready,
        'support_assumptions': support_assumptions,
        'completion_assumptions': completion_assumptions,
        'support_ready': support_ready,
        'promotion_ready': promotion_ready,
        'full_global_ready': full_global_ready,
        'upstream_active_assumptions': upstream_active_assumptions,
    }


def _build_residual_burden_summary(
    readiness_summary: Mapping[str, Any],
) -> dict[str, Any]:
    status = str(readiness_summary.get('status', 'global-completeness-not-ready'))
    support_assumptions = [str(x) for x in readiness_summary.get('support_assumptions', [])]
    completion_assumptions = [str(x) for x in readiness_summary.get('completion_assumptions', [])]
    upstream_active_assumptions = [str(x) for x in readiness_summary.get('upstream_active_assumptions', [])]

    if status == 'global-completeness-not-ready':
        residual_status = 'global-completeness-not-ready'
    elif status == 'global-exhaustion-support-frontier':
        residual_status = 'global-exhaustion-support-frontier'
    elif completion_assumptions == ['finite_screened_panel_is_globally_complete']:
        residual_status = 'screened-panel-global-completeness-frontier'
    elif completion_assumptions == ['omitted_nongolden_irrationals_outside_screened_panel_controlled']:
        residual_status = 'omitted-class-global-control-frontier'
    elif completion_assumptions:
        residual_status = 'global-completeness-and-omitted-control-frontier'
    elif upstream_active_assumptions:
        residual_status = 'mixed-global-and-upstream-burden'
    else:
        residual_status = 'fully-discharged'

    return {
        'status': residual_status,
        'remaining_global_support_assumptions': support_assumptions,
        'remaining_global_completion_assumptions': completion_assumptions,
        'upstream_theorem_assumptions': upstream_active_assumptions,
        'near_top_frontier_closed': bool(readiness_summary.get('near_top_frontier_closed', False)),
        'promotion_ready': bool(readiness_summary.get('promotion_ready', False)),
        'full_global_ready': bool(readiness_summary.get('full_global_ready', False)),
    }


def _hypothesis_source(support_certificates: Mapping[str, Mapping[str, Any]], assumption_name: str, fallback: str) -> str:
    cert_name, _ = _SUPPORT_CERTIFICATE_SPECS[assumption_name]
    cert = dict(support_certificates.get(cert_name, {}))
    return str(cert.get('status', fallback))


def _build_hypotheses(
    *,
    local_front_hypotheses: Sequence[str],
    local_active_assumptions: Sequence[str],
    upstream_active_assumptions: Sequence[str],
    current_screened_panel_dominance_certificate: Mapping[str, Any],
    readiness_summary: Mapping[str, Any],
    support_certificates: Mapping[str, Mapping[str, Any]],
) -> list[TheoremVIIGlobalCompletenessHypothesisRow]:
    local_active_assumptions = {str(x) for x in local_active_assumptions}
    dominance_margin = _coerce_float(current_screened_panel_dominance_certificate.get('dominance_margin'))
    return [
        TheoremVIIGlobalCompletenessHypothesisRow(
            name='near_top_frontier_closed',
            satisfied=bool(readiness_summary.get('near_top_frontier_closed', False)),
            source='Theorem-VII screened-panel dominance certificate',
            note='The currently screened near-top challenger panel is already dominated, so the remaining burden has moved beyond local near-top challenger survival.',
            margin=dominance_margin,
        ),
        TheoremVIIGlobalCompletenessHypothesisRow(
            name='global_front_isolated',
            satisfied=bool(readiness_summary.get('local_front_ready', False)),
            source='Theorem-VII residual burden split',
            note='All remaining Theorem VII burdens lie on the global completeness side rather than in unresolved local near-top hypotheses.',
            margin=None if len(local_front_hypotheses) == 0 else float(-len(local_front_hypotheses)),
        ),
        TheoremVIIGlobalCompletenessHypothesisRow(
            name='exact_near_top_lagrange_spectrum_ranking_available',
            satisfied='exact_near_top_lagrange_spectrum_ranking' not in local_active_assumptions,
            source=_hypothesis_source(support_certificates, 'exact_near_top_lagrange_spectrum_ranking', 'Theorem-VII assumption ledger'),
            note='The near-top arithmetic ranking needed to certify completeness of the screened panel has been promoted beyond a purely heuristic status.',
            margin=None,
        ),
        TheoremVIIGlobalCompletenessHypothesisRow(
            name='theorem_level_pruning_of_dominated_regions_available',
            satisfied='theorem_level_pruning_of_dominated_regions' not in local_active_assumptions,
            source=_hypothesis_source(support_certificates, 'theorem_level_pruning_of_dominated_regions', 'Theorem-VII assumption ledger'),
            note='The dominated challenger regions used operationally by search are available in theorem-level form.',
            margin=None,
        ),
        TheoremVIIGlobalCompletenessHypothesisRow(
            name='deferred_or_retired_classes_globally_dominated',
            satisfied='deferred_or_retired_classes_are_globally_dominated' not in local_active_assumptions,
            source=_hypothesis_source(support_certificates, 'deferred_or_retired_classes_are_globally_dominated', 'Theorem-VII assumption ledger'),
            note='Classes retired or deferred by the search lifecycle are genuinely dominated globally rather than merely deprioritized computationally.',
            margin=None,
        ),
        TheoremVIIGlobalCompletenessHypothesisRow(
            name='termination_search_promotes_to_theorem_exclusion',
            satisfied='termination_search_promotes_to_theorem_exclusion' not in local_active_assumptions,
            source=_hypothesis_source(support_certificates, 'termination_search_promotes_to_theorem_exclusion', 'Theorem-VII assumption ledger'),
            note='Termination-aware search outcomes have been promoted from workflow decisions to theorem-level exclusions.',
            margin=None,
        ),
        TheoremVIIGlobalCompletenessHypothesisRow(
            name='screened_panel_globally_complete',
            satisfied='finite_screened_panel_is_globally_complete' not in local_active_assumptions,
            source=_hypothesis_source(support_certificates, 'finite_screened_panel_is_globally_complete', 'Theorem-VII assumption ledger'),
            note='The currently screened near-top challenger panel is now known to be globally complete for the relevant near-top competitor spectrum.',
            margin=None,
        ),
        TheoremVIIGlobalCompletenessHypothesisRow(
            name='omitted_classes_globally_controlled',
            satisfied='omitted_nongolden_irrationals_outside_screened_panel_controlled' not in local_active_assumptions,
            source=_hypothesis_source(support_certificates, 'omitted_nongolden_irrationals_outside_screened_panel_controlled', 'Theorem-VII assumption ledger'),
            note='Non-golden irrational classes outside the screened near-top panel are globally controlled.',
            margin=None,
        ),
        TheoremVIIGlobalCompletenessHypothesisRow(
            name='no_upstream_global_dependencies',
            satisfied=len(upstream_active_assumptions) == 0,
            source='Theorem-VII upstream active assumptions',
            note='No upstream theorem-side assumptions remain between the current global challenger package and a theorem-grade exhaustion statement.',
            margin=None if len(upstream_active_assumptions) == 0 else float(-len(upstream_active_assumptions)),
        ),
    ]


def build_golden_theorem_vii_global_completeness_certificate(
    theorem_vii_certificate: Mapping[str, Any],
) -> GoldenTheoremVIIGlobalCompletenessCertificate:
    theorem_vii = dict(theorem_vii_certificate)
    family_label = str(theorem_vii.get('family_label', 'standard-sine'))
    current_screened_panel_dominance_certificate = dict(theorem_vii.get('current_screened_panel_dominance_certificate', {}))
    inherited_residual = dict(theorem_vii.get('residual_burden_summary', {}))
    local_front_hypotheses = [str(x) for x in inherited_residual.get('local_front_hypotheses', [])]
    support_certificates, near_top_threat_set_partition_certificate = _augment_support_certificates(_extract_support_certificates(theorem_vii))
    local_active_assumptions = _discharged_local_active_assumptions(
        theorem_vii.get('local_active_assumptions', []),
        support_certificates,
    )
    upstream_active_assumptions = [str(x) for x in theorem_vii.get('upstream_active_assumptions', [])]
    assumptions = _update_assumption_rows(_coerce_assumption_rows(theorem_vii.get('assumptions', [])), support_certificates)
    active_assumptions = list(upstream_active_assumptions) + list(local_active_assumptions)

    readiness_summary = _build_readiness_summary(
        local_front_hypotheses=local_front_hypotheses,
        local_active_assumptions=local_active_assumptions,
        upstream_active_assumptions=upstream_active_assumptions,
        current_screened_panel_dominance_certificate=current_screened_panel_dominance_certificate,
    )
    residual_burden_summary = _build_residual_burden_summary(readiness_summary)
    hypotheses = _build_hypotheses(
        local_front_hypotheses=local_front_hypotheses,
        local_active_assumptions=local_active_assumptions,
        upstream_active_assumptions=upstream_active_assumptions,
        current_screened_panel_dominance_certificate=current_screened_panel_dominance_certificate,
        readiness_summary=readiness_summary,
        support_certificates=support_certificates,
    )
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]

    residual_status = residual_burden_summary['status']
    if residual_status == 'fully-discharged' and len(active_assumptions) == 0:
        theorem_status = 'golden-theorem-vii-global-completeness-conditional-strong'
    elif residual_status == 'fully-discharged':
        theorem_status = 'golden-theorem-vii-global-completeness-front-complete'
    elif residual_status in {
        'screened-panel-global-completeness-frontier',
        'omitted-class-global-control-frontier',
        'global-completeness-and-omitted-control-frontier',
    }:
        theorem_status = 'golden-theorem-vii-global-completeness-promotion-frontier'
    elif residual_status == 'global-exhaustion-support-frontier':
        theorem_status = 'golden-theorem-vii-global-completeness-support-frontier'
    else:
        theorem_status = 'golden-theorem-vii-global-completeness-conditional-partial'

    notes = (
        'This certificate packages the remaining global Theorem VII burden after the near-top screened-panel frontier. '
        'It distinguishes the support-side arithmetic/pruning promotions from the final completeness claims that the screened panel is globally complete and that omitted non-golden classes are globally controlled. '
        'Support assumptions are now allowed to discharge via explicit certificate provenance rather than only by manual toggles, the screened-panel completeness step is now mediated by an explicit near-top threat-set partition certificate, and the omitted-class tail is now tracked by an explicit omitted-class global-control certificate.'
    )
    if residual_status == 'screened-panel-global-completeness-frontier':
        notes += ' The omitted-class tail is already controlled locally enough that the live blocker is proving the screened panel itself is globally complete.'
    elif residual_status == 'omitted-class-global-control-frontier':
        notes += ' The screened panel is effectively complete; the remaining live blocker is controlling omitted non-golden classes outside that panel.'
    elif residual_status == 'global-completeness-and-omitted-control-frontier':
        notes += ' Both the screened-panel completeness step and the omitted-class global-control step remain active.'
    elif residual_status == 'global-exhaustion-support-frontier':
        notes += ' The global burden has been isolated, but theorem-grade support objects for ranking/pruning/termination promotion are still missing.'

    return GoldenTheoremVIIGlobalCompletenessCertificate(
        family_label=family_label,
        theorem_vii_shell=theorem_vii,
        current_screened_panel_dominance_certificate=current_screened_panel_dominance_certificate,
        near_top_threat_set_partition_certificate=near_top_threat_set_partition_certificate,
        support_certificates=support_certificates,
        readiness_summary=readiness_summary,
        residual_burden_summary=residual_burden_summary,
        hypotheses=hypotheses,
        assumptions=assumptions,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        local_active_assumptions=local_active_assumptions,
        upstream_active_assumptions=upstream_active_assumptions,
        active_assumptions=active_assumptions,
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    'GLOBAL_SUPPORT_ASSUMPTIONS',
    'GLOBAL_COMPLETENESS_ASSUMPTIONS',
    'TheoremVIIGlobalCompletenessHypothesisRow',
    'TheoremVIIGlobalCompletenessAssumptionRow',
    'GoldenTheoremVIIGlobalCompletenessCertificate',
    'build_golden_theorem_vii_global_completeness_certificate',
]
