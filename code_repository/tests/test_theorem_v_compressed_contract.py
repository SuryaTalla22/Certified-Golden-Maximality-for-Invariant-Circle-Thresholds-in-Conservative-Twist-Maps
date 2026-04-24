from __future__ import annotations

from kam_theorem_suite.theorem_v_compressed_contract import build_theorem_v_compressed_contract_certificate
from kam_theorem_suite.theorem_v_lower_compatibility import build_theorem_v_lower_compatibility_certificate
from kam_theorem_suite.theorem_v_transport_lift import build_golden_theorem_v_compressed_lift_certificate


def _theorem_v_shell() -> dict:
    return {
        'theorem_status': 'golden-theorem-v-final-strong',
        'theorem_target_interval': [0.9713628, 0.9713671],
        'theorem_target_width': 4.3e-06,
        'gap_preservation_margin': 0.001,
        'assumptions': [
            {'name': 'validated_function_space_continuation_transport', 'assumed': True},
            {'name': 'unique_branch_continuation_to_true_irrational_threshold', 'assumed': True},
        ],
        'convergence_front': {
            'relation': {'lower_status': 'golden-lower-neighborhood-stability-strong', 'lower_bound': 0.2},
            'branch_certified_control': {'theorem_status': 'branch-certified-limit-weak'},
            'convergent_family_control': {'theorem_status': 'convergent-family-limit-incomplete'},
            'global_transport_potential_control': {'theorem_status': 'global-transport-potential-partial'},
            'certified_tail_modulus_control': {'theorem_status': 'certified-tail-modulus-partial'},
            'theorem_v_uniform_error_law': {'theorem_status': 'theorem-v-uniform-error-law-strong', 'final_error_law_certified': True, 'gap_preservation_certified': True},
            'theorem_v_branch_identification': {'theorem_status': 'theorem-v-branch-identification-partial', 'branch_identification_locked': True},
            'theorem_v_final_error_control': {'theorem_target_interval': [0.9713628, 0.9713671], 'error_law_preserves_gap': True},
        },
        'final_transport_bridge': {
            'bridge_status': 'final-transport-bridge-strong',
            'transport_bridge_locked': True,
            'transport_bridge_with_identification_lock': True,
            'upper_tail_source': 'theorem-iv-final-object',
            'uniform_error_law_status': 'theorem-v-uniform-error-law-strong',
            'branch_identification_status': 'theorem-v-branch-identification-partial',
            'theorem_target_interval': [0.9713628, 0.9713671],
        },
    }


def test_lower_compatibility_strong_with_overlapping_interval():
    cert = build_theorem_v_lower_compatibility_certificate(
        {'theorem_status': 'golden-theorem-iii-infinite-dimensional-closure-incomplete'},
        {'final_transport_bridge': {'theorem_target_interval': [0.25, 0.3]}, 'relation': {'lower_bound': 0.2}}
    ).to_dict()
    assert cert['lower_compatibility_certified'] is True
    assert cert['theorem_status'] == 'theorem-v-lower-compatibility-strong'


def test_compressed_contract_is_strong_when_minimal_contract_holds():
    cert = build_theorem_v_compressed_contract_certificate(
        theorem_v_certificate=_theorem_v_shell(),
        theorem_iii_certificate={'theorem_status': 'golden-theorem-iii-infinite-dimensional-closure-incomplete'},
        theorem_iv_certificate={'theorem_status': 'golden-theorem-iv-final-strong', 'analytic_incompatibility_certified': True},
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-v-compressed-contract-strong'
    assert cert['transport_lock']['locked'] is True
    assert cert['uniform_majorant']['certified'] is True
    assert cert['branch_identity']['sufficient_for_downstream'] is True
    assert cert['formal_assumptions_remaining'] == []


def test_compressed_lift_wraps_transport_shell():
    wrapped = build_golden_theorem_v_compressed_lift_certificate(
        base_K_values=[0.2],
        theorem_v_certificate=_theorem_v_shell(),
        theorem_iii_certificate={'theorem_status': 'golden-theorem-iii-infinite-dimensional-closure-incomplete'},
        theorem_iv_certificate={'theorem_status': 'golden-theorem-iv-final-strong', 'analytic_incompatibility_certified': True},
    )
    assert wrapped['compressed_contract']['theorem_status'] == 'golden-theorem-v-compressed-contract-strong'
