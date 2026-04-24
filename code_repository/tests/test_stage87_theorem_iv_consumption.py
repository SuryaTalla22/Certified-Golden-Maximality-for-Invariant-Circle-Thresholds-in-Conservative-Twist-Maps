from __future__ import annotations

from kam_theorem_suite.theorem_viii_reduction_lift import build_golden_theorem_viii_reduction_lift_certificate
from kam_theorem_suite.theorem_viii_reduction_discharge import build_golden_theorem_viii_reduction_discharge_lift_certificate


def _final_theorem_v():
    return {
        'theorem_status': 'golden-theorem-v-final-strong',
        'active_assumptions': [],
        'open_hypotheses': [],
        'theorem_target_interval': [0.971095, 0.971105],
        'gap_preservation_margin': 2.0e-6,
        'final_error_law': {'error_law_preserves_gap': True},
    }


def test_stage87_viii_lift_and_discharge_record_final_iv() -> None:
    theorem_iv = {
        'theorem_status': 'golden-theorem-iv-final-strong',
        'analytic_incompatibility_certified': True,
        'open_hypotheses': [],
        'active_assumptions': [],
    }
    theorem_v = _final_theorem_v()
    identification = {'theorem_status': 'golden-threshold-identification-transport-discharge-lift-conditional-strong', 'open_hypotheses': [], 'active_assumptions': []}
    theorem_vi = {'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-conditional-one-variable-strong', 'statement_mode': 'one-variable', 'open_hypotheses': [], 'active_assumptions': []}
    theorem_vii = {'theorem_status': 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong', 'open_hypotheses': [], 'active_assumptions': [], 'reference_lower_bound': 0.97109}
    lift = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.9, 0.95],
        theorem_iv_certificate=theorem_iv,
        theorem_v_certificate=theorem_v,
        threshold_identification_discharge_certificate=identification,
        theorem_vi_envelope_discharge_certificate=theorem_vi,
        theorem_vii_exhaustion_discharge_certificate=theorem_vii,
    ).to_dict()
    assert lift['theorem_iv_final_certified'] is True
    names = {row['name']: row for row in lift['hypotheses']}
    assert names['theorem_iv_final_certified']['satisfied'] is True

    baseline = {
        'rho': 0.618,
        'family_label': 'standard-sine',
        'statement_mode': 'one-variable',
        'assumptions': [],
        'upstream_active_assumptions': [],
        'local_active_assumptions': [],
        'active_assumptions': [],
        'open_hypotheses': [],
        'theorem_status': 'golden-theorem-viii-reduction-lift-front-complete',
        'theorem_iv_shell': theorem_iv,
        'theorem_v_shell': theorem_v,
    }
    vii_discharge = {
        'theorem_status': 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'reference_lower_bound': 0.97109,
        'current_near_top_exhaustion_upper_bound': 0.97106,
        'current_near_top_exhaustion_margin': 3.0e-05,
        'current_near_top_exhaustion_pending_count': 0,
        'current_near_top_exhaustion_source': 'test',
        'current_near_top_exhaustion_status': 'near-top-exhaustion-strong',
        'theorem_vi_discharge_shell': {
            'theorem_status': theorem_vi['theorem_status'],
            'statement_mode': 'one-variable',
            'open_hypotheses': [],
            'active_assumptions': [],
            'threshold_identification_discharge_shell': {
                'theorem_status': identification['theorem_status'],
                'open_hypotheses': [],
                'active_assumptions': [],
                'local_active_assumptions': [],
                'discharged_bridge_native_tail_witness_interval': [0.971095, 0.971105],
                'discharged_bridge_native_tail_witness_width': 1.0e-05,
                'overlap_window': [0.97109, 0.97111],
                'overlap_width': 2.0e-05,
            },
            'discharged_identified_branch_witness_interval': [0.971095, 0.971105],
            'discharged_identified_branch_witness_width': 1.0e-05,
            'current_top_gap_scale': 4.0e-05,
            'current_most_dangerous_challenger_upper': 0.97106,
            'discharged_witness_width_vs_current_top_gap_margin': 3.0e-05,
            'discharged_witness_lower_vs_current_near_top_challenger_upper_margin': 3.5e-05,
            'discharged_witness_geometry_min_margin': 3.0e-05,
            'discharged_witness_geometry_status': 'discharged-witness-geometry-strong',
        },
    }
    discharge = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.9, 0.95],
        baseline_theorem_viii_certificate=baseline,
        theorem_viii_certificate=baseline,
        theorem_vii_exhaustion_discharge_certificate=vii_discharge,
    ).to_dict()
    assert discharge['theorem_iv_final_certified'] is True
    names = {row['name']: row for row in discharge['hypotheses']}
    assert names['theorem_iv_consumed_as_final_theorem']['satisfied'] is True
