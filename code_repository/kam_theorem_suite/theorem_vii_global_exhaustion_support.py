from __future__ import annotations
from typing import Any, Mapping, Sequence
from .class_exhaustion_screen import build_near_top_threat_set_partition_certificate
from .theorem_vii_arithmetic_ranking import build_exact_near_top_lagrange_spectrum_ranking_certificate
from .theorem_vii_deferred_domination import build_deferred_retired_global_domination_certificate
from .theorem_vii_omitted_control import build_omitted_nongolden_global_control_certificate
from .theorem_vii_pruning_regions import build_theorem_level_pruning_certificate
from .theorem_vii_screened_panel_completion import build_screened_panel_global_completeness_witness
from .theorem_vii_termination_promotion import build_termination_search_exclusion_promotion_certificate

_STAGE106_ASSUMPTIONS = ['exact_near_top_lagrange_spectrum_ranking','theorem_level_pruning_of_dominated_regions','finite_screened_panel_is_globally_complete','deferred_or_retired_classes_are_globally_dominated','termination_search_promotes_to_theorem_exclusion','omitted_nongolden_irrationals_outside_screened_panel_controlled']

def _screened_labels(screen: Mapping[str, Any]) -> list[str]:
    labels = [str(r.get('class_label', r.get('label', 'unknown'))) for r in screen.get('classes', [])]
    if labels: return labels
    cert = screen.get('screened_panel_global_completeness_certificate', {})
    if isinstance(cert, Mapping): return [str(x) for x in cert.get('screened_panel_labels', [])]
    return []

def _termination_labels(termination: Mapping[str, Any], key: str) -> list[str]:
    labels = [str(x) for x in termination.get(key, [])]
    if not labels and key == 'retired_labels':
        for rr in termination.get('rounds', []) if isinstance(termination.get('rounds', []), list) else []:
            if isinstance(rr, Mapping): labels.extend(str(x) for x in rr.get('retired_classes', []))
    return sorted(set(labels))

def build_theorem_vii_global_exhaustion_support_certificate(*, screen: Mapping[str, Any], termination: Mapping[str, Any] | None = None, theorem_vi_certificate: Mapping[str, Any] | None = None, reference_lower_bound: float | None = None, eta_cut: float | None = None, omitted_labels: Sequence[str] | None = None) -> dict[str, Any]:
    screen = dict(screen); termination = {} if termination is None else dict(termination); theorem_vi_certificate = {} if theorem_vi_certificate is None else dict(theorem_vi_certificate)
    labels = _screened_labels(screen)
    ranking = build_exact_near_top_lagrange_spectrum_ranking_certificate(screen=screen, theorem_vi_certificate=theorem_vi_certificate, screened_labels=labels, eta_cut=eta_cut)
    pruning = build_theorem_level_pruning_certificate(screen=screen, reference_lower_bound=reference_lower_bound)
    screened = build_screened_panel_global_completeness_witness(screen=screen, arithmetic_ranking_certificate=ranking, pruning_region_certificate=pruning)
    deferred = build_deferred_retired_global_domination_certificate(termination=termination, deferred_labels=_termination_labels(termination, 'deferred_labels'), retired_labels=_termination_labels(termination, 'retired_labels'), screened_panel_labels=labels)
    term = build_termination_search_exclusion_promotion_certificate(termination=termination, screened_panel_labels=labels)
    partition = build_near_top_threat_set_partition_certificate(screened_panel_certificate=screened, arithmetic_ranking_certificate=ranking, pruning_region_certificate=pruning, deferred_retired_domination_certificate=deferred, termination_exclusion_promotion_certificate=term)
    omitted = build_omitted_nongolden_global_control_certificate(omitted_labels=omitted_labels or partition.get('ranking_excluded_labels', []) or [], screened_panel_labels=labels, eta_envelope_control_certificate=(theorem_vi_certificate.get('global_nongolden_ceiling_certificate', {}) if isinstance(theorem_vi_certificate, Mapping) else {}))
    support = {'exact_near_top_lagrange_spectrum_ranking_certificate': ranking, 'theorem_level_pruning_certificate': pruning, 'screened_panel_global_completeness_certificate': screened, 'near_top_threat_set_partition_certificate': partition, 'deferred_retired_domination_certificate': deferred, 'termination_search_exclusion_certificate': term, 'omitted_class_global_control_certificate': omitted}
    undischarged = []
    if not ranking.get('proves_exact_near_top_lagrange_spectrum_ranking'): undischarged.append('exact_near_top_lagrange_spectrum_ranking')
    if not pruning.get('proves_theorem_level_pruning_of_dominated_regions'): undischarged.append('theorem_level_pruning_of_dominated_regions')
    if not screened.get('screened_panel_globally_complete'): undischarged.append('finite_screened_panel_is_globally_complete')
    if not deferred.get('proves_deferred_or_retired_classes_are_globally_dominated'): undischarged.append('deferred_or_retired_classes_are_globally_dominated')
    if not term.get('proves_termination_search_promotes_to_theorem_exclusion'): undischarged.append('termination_search_promotes_to_theorem_exclusion')
    if not omitted.get('omitted_classes_globally_controlled'): undischarged.append('omitted_nongolden_irrationals_outside_screened_panel_controlled')
    return {'status': 'theorem-vii-global-exhaustion-support-certified' if not undischarged else 'theorem-vii-global-exhaustion-support-frontier', 'support_certificates': support, 'all_vii_assumptions_dischargeable': not undischarged, 'discharged_vii_assumptions': [x for x in _STAGE106_ASSUMPTIONS if x not in undischarged], 'undischarged_vii_assumptions': undischarged, 'screened_panel_labels': labels, 'notes': 'Stage 106 aggregates exact ranking, pruning, finite-panel completion, deferred/retired domination, termination promotion, and omitted-tail control into one theorem-facing support payload for Theorem VII.'}
