from __future__ import annotations

from kam_theorem_suite.theorem_vii_global_exhaustion_support import build_theorem_vii_global_exhaustion_support_certificate
from kam_theorem_suite.theorem_vii_exhaustion_lift import build_golden_theorem_vii_exhaustion_lift_certificate
from kam_theorem_suite.theorem_vii_exhaustion_discharge import build_golden_theorem_vii_exhaustion_discharge_lift_certificate

SCREEN = {'reference_label': 'golden', 'reference_lower_bound': 0.9713628519, 'classes': [
    {'class_label': 'silver', 'preperiod': (), 'period': (2,), 'eta_lo': 0.4142, 'eta_hi': 0.4143, 'pruning_status': 'arithmetic-weaker-only', 'selected_upper_hi': None, 'selected_upper_margin_to_reference': None},
    {'class_label': 'bronze', 'preperiod': (), 'period': (3,), 'eta_lo': 0.3027, 'eta_hi': 0.3028, 'pruning_status': 'dominated', 'selected_upper_hi': 0.9700, 'selected_upper_margin_to_reference': 0.0013},
]}
TERMINATION = {'active_count': 0, 'deferred_count': 0, 'retired_count': 2, 'undecided_count': 0, 'overlapping_count': 0, 'retired_labels': ['silver', 'bronze'], 'rounds': [{'retired_classes': ['silver', 'bronze']}]}
THEOREM_VI = {'family_label': 'standard-sine', 'theorem_status': 'golden-theorem-vi-envelope-lift-screened-one-variable-strong', 'open_hypotheses': [], 'active_assumptions': [], 'near_top_challenger_surface': {'challenger_records': [{'label': 'silver', 'eta_interval': [0.4142, 0.4143], 'status': 'arithmetic-weaker-only'}, {'label': 'bronze', 'eta_interval': [0.3027, 0.3028], 'status': 'dominated-by-golden-threshold-anchor', 'threshold_upper_bound': 0.9700}]}, 'global_nongolden_ceiling_certificate': {'global_ceiling_status': 'stage106-eta-envelope-ceiling-ready', 'global_ceiling_theorem_certified': True}}

def _support():
    return build_theorem_vii_global_exhaustion_support_certificate(screen=SCREEN, termination=TERMINATION, theorem_vi_certificate=THEOREM_VI, reference_lower_bound=0.9713628519)

def test_stage106_support_certificate_discharges_all_vii_assumptions() -> None:
    support = _support()
    assert support['status'] == 'theorem-vii-global-exhaustion-support-certified'
    assert support['all_vii_assumptions_dischargeable'] is True
    assert support['undischarged_vii_assumptions'] == []
    certs = support['support_certificates']
    assert certs['exact_near_top_lagrange_spectrum_ranking_certificate']['proves_exact_near_top_lagrange_spectrum_ranking'] is True
    assert certs['theorem_level_pruning_certificate']['proves_theorem_level_pruning_of_dominated_regions'] is True
    assert certs['screened_panel_global_completeness_certificate']['screened_panel_globally_complete'] is True
    assert certs['deferred_retired_domination_certificate']['proves_deferred_or_retired_classes_are_globally_dominated'] is True
    assert certs['termination_search_exclusion_certificate']['proves_termination_search_promotes_to_theorem_exclusion'] is True
    assert certs['omitted_class_global_control_certificate']['omitted_classes_globally_controlled'] is True

def test_stage106_lift_consumes_support_payload_without_manual_assumptions() -> None:
    cert = build_golden_theorem_vii_exhaustion_lift_certificate(base_K_values=[0.9713628519], theorem_vi_certificate=THEOREM_VI, theorem_vii_global_exhaustion_support_certificate=_support(), reference_lower_bound=0.9713628519, reference_crossing_center=0.9713650136).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vii-exhaustion-lift-conditional-strong'
    assert cert['open_hypotheses'] == []
    assert cert['local_active_assumptions'] == []
    assert cert['active_assumptions'] == []
    assert cert['global_completeness_certificate']['theorem_status'] == 'golden-theorem-vii-global-completeness-conditional-strong'
    assert cert['global_completeness_certificate']['residual_burden_summary']['status'] == 'fully-discharged'

def test_stage106_discharge_preserves_support_and_becomes_papergrade_final() -> None:
    lift = build_golden_theorem_vii_exhaustion_lift_certificate(base_K_values=[0.9713628519], theorem_vi_certificate=THEOREM_VI, theorem_vii_global_exhaustion_support_certificate=_support(), reference_lower_bound=0.9713628519, reference_crossing_center=0.9713650136).to_dict()
    discharge = build_golden_theorem_vii_exhaustion_discharge_lift_certificate(base_K_values=[0.9713628519], theorem_vii_certificate=lift, theorem_vi_certificate=THEOREM_VI, reference_lower_bound=0.9713628519, reference_crossing_center=0.9713650136).to_dict()
    assert discharge['theorem_status'] == 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong'
    assert discharge['theorem_vii_codepath_final'] is True
    assert discharge['theorem_vii_papergrade_final'] is True
    assert discharge['theorem_vii_residual_citation_burden'] == []
    assert discharge['active_assumptions'] == []
