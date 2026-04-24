from __future__ import annotations

from kam_theorem_suite.transport_locked_threshold_uniqueness import (
    build_transport_locked_threshold_uniqueness_certificate,
)


def _theorem_v_shell(*, pairwise_status='pairwise-transport-chain-strong', triple_status='triple-transport-cocycle-strong', upper_tail_status='golden-upper-tail-stability-strong', explicit_tail=6.0e-6, pair_tail=6.0e-6, triple_tail=7.0e-6):
    return {
        'family_label': 'standard-sine',
        'convergence_front': {
            'relation': {
                'lower_bound': 0.99990,
                'lower_window_hi': 1.00000,
                'upper_tail_status': upper_tail_status,
                'transport_chain_qs': [13, 21, 34, 55],
                'pairwise_transport_chain_qs': [13, 21, 34, 55],
                'triple_transport_cocycle_chain_qs': [13, 21, 34, 55],
                'native_late_coherent_suffix_witness_lo': 1.000174,
                'native_late_coherent_suffix_witness_hi': 1.000186,
                'native_late_coherent_suffix_witness_width': 1.2e-5,
                'native_late_coherent_suffix_length': 4,
                'native_late_coherent_suffix_labels': ['g-13/21', 'g-21/34', 'g-34/55', 'g-55/89'],
                'native_late_coherent_suffix_qs': [21, 34, 55, 89],
                'native_late_coherent_suffix_contracting': True,
                'native_late_coherent_suffix_contraction_ratio': 2.5,
                'native_late_coherent_suffix_source': 'theorem_v_explicit_error_control.late_coherent_suffix',
            },
            'transport_certified_control': {
                'theorem_status': 'transport-certified-limit-strong',
                'limit_interval_lo': 1.00012,
                'limit_interval_hi': 1.00024,
                'telescoping_tail_bound': 5.0e-6,
                'last_transport_step_bound': 4.0e-6,
                'derivative_backed_fraction': 0.75,
                'endpoint_transport_fraction': 0.9,
            },
            'pairwise_transport_control': {
                'theorem_status': pairwise_status,
                'limit_interval_lo': 1.00014,
                'limit_interval_hi': 1.00022,
                'pair_chain_intersection_lo': 1.00015,
                'pair_chain_intersection_hi': 1.00021,
                'pair_chain_intersection_width': 6.0e-5,
                'last_pair_interval_width': 6.0e-5,
                'telescoping_pair_tail_bound': pair_tail,
            },
            'triple_transport_cocycle_control': {
                'theorem_status': triple_status,
                'limit_interval_lo': 1.000145,
                'limit_interval_hi': 1.000215,
                'triple_chain_intersection_lo': 1.000155,
                'triple_chain_intersection_hi': 1.000205,
                'triple_chain_intersection_width': 5.0e-5,
                'last_triple_interval_width': 5.0e-5,
                'telescoping_triple_tail_bound': triple_tail,
            },
            'global_transport_potential_control': {
                'theorem_status': 'global-transport-potential-strong',
                'selected_limit_interval_lo': 1.000160,
                'selected_limit_interval_hi': 1.000200,
            },
            'tail_cauchy_potential_control': {
                'theorem_status': 'tail-cauchy-potential-strong',
                'selected_limit_interval_lo': 1.000164,
                'selected_limit_interval_hi': 1.000196,
            },
            'certified_tail_modulus_control': {
                'theorem_status': 'certified-tail-modulus-strong',
                'selected_limit_interval_lo': 1.000168,
                'selected_limit_interval_hi': 1.000192,
            },
            'rate_aware_tail_modulus_control': {
                'theorem_status': 'rate-aware-tail-modulus-strong',
                'modulus_rate_intersection_lo': 1.000171,
                'modulus_rate_intersection_hi': 1.000189,
            },
            'theorem_v_explicit_error_control': {
                'theorem_status': 'theorem-v-explicit-error-law-strong',
                'compatible_limit_interval_lo': 1.000174,
                'compatible_limit_interval_hi': 1.000186,
                'last_monotone_total_error_radius': explicit_tail,
                'last_raw_total_error_radius': explicit_tail,
            },
        },
    }


def test_transport_locked_threshold_uniqueness_strong():
    cert = build_transport_locked_threshold_uniqueness_certificate(
        theorem_v_certificate=_theorem_v_shell(),
        transport_interval=[1.00010, 1.00030],
        identified_window=[1.00011, 1.00029],
        locked_window=[1.00011, 1.00029],
    ).to_dict()
    assert cert['theorem_status'] == 'transport-locked-threshold-uniqueness-conditional-strong'
    assert cert['eventual_branch_coherence'] is True
    assert cert['uniqueness_margin'] > 0.0
    assert cert['threshold_identification_ready'] is True
    assert cert['threshold_identification_interval'] is not None
    names = {row['name']: row for row in cert['hypotheses']}
    assert names['locked_window_beats_residual_tail_budget']['satisfied'] is True
    assert names['transport_locked_witness_identifies_threshold_branch']['satisfied'] is True


def test_transport_locked_threshold_uniqueness_not_strong_when_coherence_breaks():
    cert = build_transport_locked_threshold_uniqueness_certificate(
        theorem_v_certificate=_theorem_v_shell(pairwise_status='pairwise-transport-chain-incomplete', triple_status='triple-transport-cocycle-incomplete'),
        transport_interval=[1.00010, 1.00030],
        identified_window=[1.00011, 1.00029],
        locked_window=[1.00011, 1.00029],
    ).to_dict()
    assert cert['theorem_status'] in {
        'transport-locked-threshold-uniqueness-front-complete',
        'transport-locked-threshold-uniqueness-partial',
    }
    assert cert['eventual_branch_coherence'] is False


def test_transport_locked_threshold_uniqueness_not_strong_when_tail_budget_too_large():
    cert = build_transport_locked_threshold_uniqueness_certificate(
        theorem_v_certificate=_theorem_v_shell(explicit_tail=8.0e-5, pair_tail=8.0e-5, triple_tail=8.0e-5),
        transport_interval=[1.00010, 1.00030],
        identified_window=[1.00011, 1.00029],
        locked_window=[1.00011, 1.00029],
    ).to_dict()
    assert cert['theorem_status'] == 'transport-locked-threshold-uniqueness-front-complete'
    assert cert['threshold_identification_ready'] is False
    assert cert['residual_identification_obstruction'] == 'locked_window_not_yet_small_relative_to_tail_budget'
    names = {row['name']: row for row in cert['hypotheses']}
    assert names['locked_window_beats_residual_tail_budget']['satisfied'] is False
    assert names['transport_locked_witness_identifies_threshold_branch']['satisfied'] is False


def test_transport_locked_threshold_uniqueness_accepts_late_tail_suffix_contraction():
    shell = _theorem_v_shell()
    # Introduce one coarse-layer wobble that breaks global monotonicity but leaves
    # a genuinely contracting late suffix.
    shell['convergence_front']['pairwise_transport_control'].update({
        'pair_chain_intersection_lo': 1.000150,
        'pair_chain_intersection_hi': 1.000200,
        'pair_chain_intersection_width': 5.0e-5,
        'last_pair_interval_width': 5.0e-5,
    })
    shell['convergence_front']['triple_transport_cocycle_control'].update({
        'triple_chain_intersection_lo': 1.000149,
        'triple_chain_intersection_hi': 1.000209,
        'triple_chain_intersection_width': 6.0e-5,
        'last_triple_interval_width': 6.0e-5,
    })
    shell['convergence_front']['global_transport_potential_control'].update({
        'selected_limit_interval_lo': 1.000164,
        'selected_limit_interval_hi': 1.000194,
        'selected_limit_interval_width': 3.0e-5,
    })
    shell['convergence_front']['tail_cauchy_potential_control'].update({
        'selected_limit_interval_lo': 1.000168,
        'selected_limit_interval_hi': 1.000190,
        'selected_limit_interval_width': 2.2e-5,
    })
    shell['convergence_front']['certified_tail_modulus_control'].update({
        'selected_limit_interval_lo': 1.000171,
        'selected_limit_interval_hi': 1.000187,
        'selected_limit_interval_width': 1.6e-5,
    })
    shell['convergence_front']['rate_aware_tail_modulus_control'].update({
        'modulus_rate_intersection_lo': 1.000173,
        'modulus_rate_intersection_hi': 1.000185,
        'modulus_rate_intersection_width': 1.2e-5,
    })
    shell['convergence_front']['theorem_v_explicit_error_control'].update({
        'compatible_limit_interval_lo': 1.000174,
        'compatible_limit_interval_hi': 1.000184,
        'compatible_limit_interval_width': 1.0e-5,
    })

    cert = build_transport_locked_threshold_uniqueness_certificate(
        theorem_v_certificate=shell,
        transport_interval=[1.00010, 1.00030],
        identified_window=[1.00011, 1.00029],
        locked_window=[1.00011, 1.00029],
    ).to_dict()
    assert cert['eventual_nesting'] is False
    assert cert['late_tail_contracting'] is True
    assert cert['theorem_status'] == 'transport-locked-threshold-uniqueness-conditional-strong'
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['eventual_nesting_or_contraction']['satisfied'] is True



def test_transport_locked_threshold_uniqueness_uses_late_suffix_witness_when_coarse_interval_misses():
    shell = _theorem_v_shell()
    # Make the earliest transport-certified interval miss the late coherent chain by
    # a tiny amount. The late suffix still locks to a unique branch via the deeper
    # transport/pairwise/triple/global/tail witnesses.
    shell['convergence_front']['transport_certified_control'].update({
        'limit_interval_lo': 1.000120,
        'limit_interval_hi': 1.000170,
    })
    shell['convergence_front']['pairwise_transport_control'].update({
        'pair_chain_intersection_lo': 1.000171,
        'pair_chain_intersection_hi': 1.000205,
        'pair_chain_intersection_width': 3.4e-5,
        'last_pair_interval_width': 3.4e-5,
    })
    shell['convergence_front']['triple_transport_cocycle_control'].update({
        'triple_chain_intersection_lo': 1.000173,
        'triple_chain_intersection_hi': 1.000201,
        'triple_chain_intersection_width': 2.8e-5,
        'last_triple_interval_width': 2.8e-5,
    })
    shell['convergence_front']['global_transport_potential_control'].update({
        'selected_limit_interval_lo': 1.000176,
        'selected_limit_interval_hi': 1.000196,
        'selected_limit_interval_width': 2.0e-5,
    })
    shell['convergence_front']['tail_cauchy_potential_control'].update({
        'selected_limit_interval_lo': 1.000178,
        'selected_limit_interval_hi': 1.000194,
        'selected_limit_interval_width': 1.6e-5,
    })
    shell['convergence_front']['certified_tail_modulus_control'].update({
        'selected_limit_interval_lo': 1.000180,
        'selected_limit_interval_hi': 1.000192,
        'selected_limit_interval_width': 1.2e-5,
    })
    shell['convergence_front']['rate_aware_tail_modulus_control'].update({
        'modulus_rate_intersection_lo': 1.000181,
        'modulus_rate_intersection_hi': 1.000191,
        'modulus_rate_intersection_width': 1.0e-5,
    })
    shell['convergence_front']['theorem_v_explicit_error_control'].update({
        'compatible_limit_interval_lo': 1.000182,
        'compatible_limit_interval_hi': 1.000190,
        'compatible_limit_interval_width': 8.0e-6,
        'last_monotone_total_error_radius': 3.0e-7,
        'last_raw_total_error_radius': 3.0e-7,
    })

    cert = build_transport_locked_threshold_uniqueness_certificate(
        theorem_v_certificate=shell,
        transport_interval=[1.00016, 1.00021],
        identified_window=[1.000165, 1.000205],
        locked_window=[1.000165, 1.000205],
    ).to_dict()
    assert cert['branch_witness_interval'] is not None
    assert 'transport_certified_control' not in cert['witness_source_names']
    assert cert['theorem_status'] == 'transport-locked-threshold-uniqueness-conditional-strong'


def test_transport_locked_threshold_uniqueness_prefers_relation_level_tail_witness():
    shell = _theorem_v_shell()
    shell['convergence_front']['relation'].update({
        'native_late_coherent_suffix_witness_lo': 1.000176,
        'native_late_coherent_suffix_witness_hi': 1.000188,
        'native_late_coherent_suffix_witness_width': 1.2e-5,
        'native_late_coherent_suffix_length': 4,
        'native_late_coherent_suffix_contracting': True,
        'native_late_coherent_suffix_contraction_ratio': 3.0,
        'native_late_coherent_suffix_source': 'golden_limit_bridge.native_late_coherent_suffix_witness',
    })
    shell['convergence_front']['theorem_v_explicit_error_control'].pop('late_coherent_suffix_interval_lo', None)
    shell['convergence_front']['theorem_v_explicit_error_control'].pop('late_coherent_suffix_interval_hi', None)
    shell['convergence_front']['theorem_v_explicit_error_control'].pop('late_coherent_suffix_labels', None)
    shell['convergence_front']['theorem_v_explicit_error_control'].pop('late_coherent_suffix_contracting', None)
    shell['convergence_front']['theorem_v_explicit_error_control'].pop('late_coherent_suffix_contraction_ratio', None)

    cert = build_transport_locked_threshold_uniqueness_certificate(
        theorem_v_certificate=shell,
        transport_interval=[1.00010, 1.00030],
        identified_window=[1.00011, 1.00029],
        locked_window=[1.00011, 1.00029],
    ).to_dict()
    assert 'golden_limit_bridge.native_late_coherent_suffix_witness' in cert['witness_source_names']
    assert cert['contraction_ratio'] == 3.0
    assert cert['theorem_status'] == 'transport-locked-threshold-uniqueness-conditional-strong'
