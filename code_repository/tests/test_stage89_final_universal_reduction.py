from __future__ import annotations

from kam_theorem_suite.theorem_viii_reduction_lift import build_golden_theorem_viii_reduction_lift_certificate
from kam_theorem_suite.theorem_viii_reduction_discharge import build_golden_theorem_viii_reduction_discharge_lift_certificate


def _final_inputs(*, workstream_papergrade: bool = True, vii_papergrade: bool = True):
    theorem_iii = {
        'theorem_iii_final_status': 'golden-theorem-iii-final-strong',
        'certified_below_threshold_interval': [0.20, 0.29],
        'residual_theorem_iii_burden': [],
    }
    theorem_iv = {'theorem_status': 'golden-theorem-iv-final-strong', 'active_assumptions': []}
    theorem_v = {
        'theorem_status': 'golden-theorem-v-final-strong',
        'active_assumptions': [],
        'theorem_target_interval': [0.97, 0.971],
        'final_error_law': {'error_law_preserves_gap': True},
    }
    identification = {
        'theorem_status': 'golden-identification-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
        'overlap_window': [0.20, 0.21],
        'overlap_width': 0.01,
    }
    theorem_vi = {
        'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-global-one-variable-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'statement_mode': 'one-variable',
        'residual_burden_summary': {'status': 'theorem-vi-globally-discharged'},
        'current_top_gap_scale': 0.01,
        'current_most_dangerous_challenger_upper': 0.19,
        'discharged_identified_branch_witness_interval': [0.201, 0.205],
        'discharged_identified_branch_witness_width': 0.004,
        'discharged_identified_branch_witness_source': 'test',
        'discharged_identified_branch_witness_status': 'witness-ready',
    }
    theorem_vii = {
        'theorem_status': 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [] if vii_papergrade else ['citation-cleanup'],
        'theorem_vii_codepath_final': True,
        'theorem_vii_papergrade_final': vii_papergrade,
        'theorem_vii_residual_citation_burden': [] if vii_papergrade else ['theorem-vii-papergrade-cleanup'],
        'reference_lower_bound': 0.20,
        'current_near_top_exhaustion_upper_bound': 0.185,
        'current_near_top_exhaustion_margin': 0.015,
        'current_near_top_exhaustion_pending_count': 0,
        'current_near_top_exhaustion_status': 'near-top-exhaustion-strong',
        'residual_burden_summary': {'status': 'theorem-vii-papergrade-cleanup' if not vii_papergrade else 'global-exhaustion-discharged'},
    }
    theorem_vi_discharge = {
        'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-global-one-variable-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'residual_global_active_assumptions': [],
        'current_top_gap_scale': 0.01,
        'current_most_dangerous_challenger_upper': 0.19,
        'discharged_identified_branch_witness_interval': [0.201, 0.205],
        'discharged_identified_branch_witness_width': 0.004,
        'discharged_identified_branch_witness_source': 'test',
        'discharged_identified_branch_witness_status': 'witness-ready',
        'discharged_witness_width_vs_current_top_gap_margin': 0.006,
        'discharged_witness_lower_vs_current_near_top_challenger_upper_margin': 0.011,
        'discharged_witness_geometry_min_margin': 0.006,
        'discharged_witness_geometry_status': 'discharged-witness-geometry-strong',
        'residual_burden_summary': {'status': 'theorem-vi-globally-discharged'},
        'threshold_identification_discharge_shell': {
            'theorem_status': 'golden-identification-discharge-front-complete',
            'open_hypotheses': [],
            'active_assumptions': [],
            'local_active_assumptions': [],
            'overlap_window': [0.20, 0.21],
            'overlap_width': 0.01,
        },
    }
    workstream = {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'active_assumptions': [] if workstream_papergrade else ['proxy-cleanup'],
        'residual_burden_summary': {
            'status': 'workstream-discharged' if workstream_papergrade else 'workstream-proxy-caveat',
            'promotion_theorem_discharged': workstream_papergrade,
        },
    }
    return theorem_iii, theorem_iv, theorem_v, identification, theorem_vi, theorem_vii, theorem_vi_discharge, workstream


def test_stage89_final_universal_reduction_strong() -> None:
    theorem_iii, theorem_iv, theorem_v, identification, theorem_vi, theorem_vii, theorem_vi_discharge, workstream = _final_inputs()
    lift = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.2, 0.25],
        theorem_iii_certificate=theorem_iii,
        theorem_iv_certificate=theorem_iv,
        theorem_v_certificate=theorem_v,
        threshold_identification_certificate=identification,
        theorem_vi_certificate=theorem_vi,
        theorem_vii_certificate=theorem_vii,
        theorem_i_ii_workstream_certificate=workstream,
        assume_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality=True,
        assume_gl2z_orbit_uniqueness_and_normalization_closed=True,
        assume_final_universality_class_matches_reduction_statement=True,
    ).to_dict()
    assert lift['final_universal_implication_ready'] is True
    assert lift['theorem_status'] == 'golden-theorem-viii-reduction-lift-final-universal-ready'

    cert = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.2, 0.25],
        baseline_theorem_viii_certificate=lift,
        theorem_viii_certificate=lift,
        theorem_vii_exhaustion_discharge_certificate=theorem_vii,
        theorem_vi_envelope_discharge_certificate=theorem_vi_discharge,
        threshold_identification_discharge_certificate=theorem_vi_discharge['threshold_identification_discharge_shell'],
        theorem_i_ii_workstream_certificate=workstream,
    ).to_dict()
    assert cert['all_upstream_theorems_consumed'] is True
    assert cert['golden_maximality_conclusion_certified'] is True
    assert cert['final_certificate_ready_for_code_path'] is True
    assert cert['final_certificate_ready_for_paper'] is True
    assert cert['remaining_true_mathematical_burden'] == []
    assert cert['theorem_status'] == 'golden-universal-theorem-final-strong'


def test_stage89_workstream_caveat_split() -> None:
    theorem_iii, theorem_iv, theorem_v, identification, theorem_vi, theorem_vii, theorem_vi_discharge, workstream = _final_inputs(workstream_papergrade=False)
    lift = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.2, 0.25],
        theorem_iii_certificate=theorem_iii,
        theorem_iv_certificate=theorem_iv,
        theorem_v_certificate=theorem_v,
        threshold_identification_certificate=identification,
        theorem_vi_certificate=theorem_vi,
        theorem_vii_certificate=theorem_vii,
        theorem_i_ii_workstream_certificate=workstream,
        assume_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality=True,
        assume_gl2z_orbit_uniqueness_and_normalization_closed=True,
        assume_final_universality_class_matches_reduction_statement=True,
    ).to_dict()
    assert lift['theorem_status'] == 'golden-theorem-viii-reduction-lift-workstream-caveat-only'

    cert = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.2, 0.25],
        baseline_theorem_viii_certificate=lift,
        theorem_viii_certificate=lift,
        theorem_vii_exhaustion_discharge_certificate=theorem_vii,
        theorem_vi_envelope_discharge_certificate=theorem_vi_discharge,
        threshold_identification_discharge_certificate=theorem_vi_discharge['threshold_identification_discharge_shell'],
        theorem_i_ii_workstream_certificate=workstream,
    ).to_dict()
    assert cert['final_certificate_ready_for_code_path'] is True
    assert cert['final_certificate_ready_for_paper'] is False
    assert cert['remaining_true_mathematical_burden'] == []
    assert cert['remaining_workstream_paper_grade_burden'] != []
    assert cert['theorem_status'] == 'golden-universal-theorem-workstream-caveat-only'


def test_stage89_vii_papergrade_split() -> None:
    theorem_iii, theorem_iv, theorem_v, identification, theorem_vi, theorem_vii, theorem_vi_discharge, workstream = _final_inputs(vii_papergrade=False)
    lift = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.2, 0.25],
        theorem_iii_certificate=theorem_iii,
        theorem_iv_certificate=theorem_iv,
        theorem_v_certificate=theorem_v,
        threshold_identification_certificate=identification,
        theorem_vi_certificate=theorem_vi,
        theorem_vii_certificate=theorem_vii,
        theorem_i_ii_workstream_certificate=workstream,
        assume_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality=True,
        assume_gl2z_orbit_uniqueness_and_normalization_closed=True,
        assume_final_universality_class_matches_reduction_statement=True,
    ).to_dict()
    assert lift['theorem_status'] == 'golden-theorem-viii-reduction-lift-exhaustion-citation-incomplete'

    cert = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.2, 0.25],
        baseline_theorem_viii_certificate=lift,
        theorem_viii_certificate=lift,
        theorem_vii_exhaustion_discharge_certificate=theorem_vii,
        theorem_vi_envelope_discharge_certificate=theorem_vi_discharge,
        threshold_identification_discharge_certificate=theorem_vi_discharge['threshold_identification_discharge_shell'],
        theorem_i_ii_workstream_certificate=workstream,
    ).to_dict()
    assert cert['final_certificate_ready_for_code_path'] is True
    assert cert['final_certificate_ready_for_paper'] is False
    assert cert['remaining_exhaustion_paper_grade_burden'] != []
    assert cert['theorem_status'] == 'golden-universal-theorem-exhaustion-citation-incomplete'
