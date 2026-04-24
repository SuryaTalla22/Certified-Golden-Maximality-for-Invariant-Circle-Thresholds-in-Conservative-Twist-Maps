from __future__ import annotations

from kam_theorem_suite.theorem_viii_reduction_lift import build_golden_theorem_viii_reduction_lift_certificate
from kam_theorem_suite.theorem_viii_reduction_discharge import build_golden_theorem_viii_reduction_discharge_lift_certificate


def test_stage88_theorem_viii_lift_consumes_final_iii() -> None:
    theorem_iii = {
        'theorem_iii_final_status': 'golden-theorem-iii-final-strong',
        'certified_below_threshold_interval': [0.2, 0.29],
        'residual_theorem_iii_burden': [],
    }
    theorem_iv = {'theorem_status': 'golden-theorem-iv-final-strong', 'active_assumptions': []}
    theorem_v = {'theorem_status': 'golden-theorem-v-final-strong', 'active_assumptions': [], 'theorem_target_interval': [0.97, 0.971], 'final_error_law': {'error_law_preserves_gap': True}}
    identification = {'theorem_status': 'golden-identification-front-complete', 'open_hypotheses': [], 'active_assumptions': []}
    theorem_vi = {'theorem_status': 'golden-theorem-vi-front-complete', 'open_hypotheses': [], 'active_assumptions': [], 'statement_mode': 'one-variable'}
    theorem_vii = {'theorem_status': 'golden-theorem-vii-front-complete', 'open_hypotheses': [], 'active_assumptions': [], 'reference_lower_bound': 0.2}
    cert = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.2, 0.25],
        theorem_iii_certificate=theorem_iii,
        theorem_iv_certificate=theorem_iv,
        theorem_v_certificate=theorem_v,
        threshold_identification_certificate=identification,
        theorem_vi_certificate=theorem_vi,
        theorem_vii_certificate=theorem_vii,
        assume_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality=True,
        assume_gl2z_orbit_uniqueness_and_normalization_closed=True,
        assume_final_universality_class_matches_reduction_statement=True,
    ).to_dict()
    assert cert['theorem_iii_final_certified'] is True
    assert cert['theorem_iii_lower_interval'] == [0.2, 0.29]


def test_stage88_theorem_viii_discharge_consumes_final_iii() -> None:
    theorem_viii = {
        'theorem_status': 'golden-theorem-viii-reduction-lift-front-complete',
        'statement_mode': 'one-variable',
        'theorem_iii_shell': {'theorem_iii_final_status': 'golden-theorem-iii-final-strong', 'certified_below_threshold_interval': [0.2, 0.29]},
        'theorem_iv_shell': {'theorem_status': 'golden-theorem-iv-final-strong'},
        'theorem_v_shell': {'theorem_status': 'golden-theorem-v-final-strong', 'theorem_target_interval': [0.97, 0.971], 'final_error_law': {'error_law_preserves_gap': True}},
        'threshold_identification_shell': {'theorem_status': 'golden-identification-front-complete'},
        'theorem_vi_shell': {'theorem_status': 'golden-theorem-vi-front-complete', 'statement_mode': 'one-variable'},
        'theorem_vii_shell': {'theorem_status': 'golden-theorem-vii-front-complete'},
        'open_hypotheses': [],
        'active_assumptions': [],
    }
    theorem_vi_discharge = {'active_assumptions': [], 'residual_global_active_assumptions': [], 'threshold_identification_discharge_shell': {}, 'current_top_gap_scale': 0.01, 'current_most_dangerous_challenger_upper': 0.19}
    theorem_vii_discharge = {'active_assumptions': [], 'residual_non_global_hinges': []}
    cert = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.2, 0.25],
        baseline_theorem_viii_certificate=theorem_viii,
        theorem_viii_certificate=theorem_viii,
        theorem_vi_envelope_discharge_certificate=theorem_vi_discharge,
        theorem_vii_exhaustion_discharge_certificate=theorem_vii_discharge,
    ).to_dict()
    assert cert['theorem_iii_final_certified'] is True
