from __future__ import annotations

from kam_theorem_suite.theorem_v_seed_prediction import (
    decide_runtime_aware_row_attempt,
    predict_future_golden_row_seed,
)
from kam_theorem_suite.theorem_v_row_refinement import build_runtime_aware_theorem_v_row_certificate
from kam_theorem_suite.theorem_v_uniform_error_law import build_theorem_v_uniform_error_law_certificate
from kam_theorem_suite.theorem_v_branch_identification import build_theorem_v_branch_identification_certificate


def _ladder():
    return {
        'approximants': [
            {'p': 55, 'q': 89, 'label': 'gold-55/89', 'crossing_center': 0.9714393, 'crossing_root_window_lo': 0.9714373, 'crossing_root_window_hi': 0.9714413},
            {'p': 89, 'q': 144, 'label': 'gold-89/144', 'crossing_center': 0.9712393, 'crossing_root_window_lo': 0.9710, 'crossing_root_window_hi': 0.9715},
            {'p': 144, 'q': 233, 'label': 'gold-144/233', 'crossing_center': 0.9713393, 'crossing_root_window_lo': 0.9711, 'crossing_root_window_hi': 0.9716},
        ]
    }


def test_seed_prediction_prefers_transport_for_377_610() -> None:
    seed = predict_future_golden_row_seed(
        _ladder(),
        p=377,
        q=610,
        theorem_target_interval=[0.9713628, 0.9713671],
    ).to_dict()
    assert seed['q'] == 610
    assert seed['estimated_runtime_hours'] > 0.0
    assert seed['direct_attempt_recommended'] is False
    decision = decide_runtime_aware_row_attempt(seed, budget_hours=18.0, allow_direct_refinement=True, hard_q_cap=400).to_dict()
    assert decision['attempt_direct_refinement'] is False
    assert decision['decision'] in {'skip-direct-attempt-q-cap', 'skip-direct-attempt-not-recommended'}


def test_runtime_aware_row_certificate_skips_direct_attempt_by_default() -> None:
    cert = build_runtime_aware_theorem_v_row_certificate(
        _ladder(),
        p=233,
        q=377,
        theorem_target_interval=[0.9713628, 0.9713671],
        allow_direct_refinement=False,
    ).to_dict()
    assert cert['theorem_status'] == 'runtime-aware-row-skipped'
    assert cert['direct_attempt_performed'] is False
    assert cert['selected_window_width'] > 0.0


def test_uniform_error_law_and_branch_identification_layers_compile_a_strong_shell() -> None:
    explicit = {
        'chain_length': 6,
        'late_coherent_suffix_length': 4,
        'monotone_error_law_nonincreasing': True,
        'active_bounds_dominate_compatible_errors': True,
        'active_bounds_dominate_certificate_totals': True,
    }
    final_error = {
        'theorem_target_interval': [0.9713628, 0.9713671],
        'transport_limit_interval': [0.97130, 0.97138],
        'error_law_preserves_gap': True,
        'gap_preservation_margin': 1e-4,
    }
    uniform = build_theorem_v_uniform_error_law_certificate(
        explicit_error_certificate=explicit,
        final_error_certificate=final_error,
        golden_recurrence_rate_control={'theorem_status': 'golden-recurrence-rate-strong'},
        edge_class_weighted_golden_rate_control={'theorem_status': 'edge-class-weighted-golden-rate-strong'},
        convergent_family_control={'theorem_status': 'convergent-family-limit-strong'},
        runtime_row_certificates=[],
    ).to_dict()
    assert uniform['final_error_law_certified'] is True
    branch = build_theorem_v_branch_identification_certificate(
        lower_side_certificate={'stable_lower_bound': 0.97},
        upper_tail_certificate={'stable_upper_hi': 0.972},
        final_transport_bridge={'theorem_target_interval': [0.9713628, 0.9713671], 'transport_bridge_locked': True, 'upper_tail_source': 'theorem-iv-final-object'},
        theorem_iv_certificate={'theorem_status': 'golden-theorem-iv-final-strong'},
        convergent_family_control={'theorem_status': 'convergent-family-limit-strong'},
        golden_recurrence_rate_control={'exact_fibonacci_recurrence': True},
        runtime_row_certificates=[],
    ).to_dict()
    assert branch['branch_identification_locked'] is True
