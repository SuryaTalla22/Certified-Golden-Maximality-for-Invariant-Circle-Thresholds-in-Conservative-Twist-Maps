from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_golden_theorem_v_report,
    build_golden_theorem_v_transport_lift_report,
)
from kam_theorem_suite.theorem_v_transport_lift import (
    build_golden_theorem_v_transport_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload
    def to_dict(self):
        return dict(self._payload)


def test_transport_lift_front_only_when_convergence_front_is_strong(monkeypatch) -> None:
    import kam_theorem_suite.theorem_v_transport_lift as tvtl

    monkeypatch.setattr(tvtl, 'build_golden_rational_to_irrational_convergence_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-rational-to-irrational-convergence-strong',
        'relation': {
            'gap_to_compatible_upper': 0.012,
            'convergence_status': 'irrational-limit-control-strong',
            'branch_certified_status': 'branch-certified-limit-strong',
            'nested_subladder_status': 'nested-subladder-limit-strong',
            'convergent_family_status': 'convergent-family-limit-strong',
            'transport_certified_status': 'transport-certified-limit-strong',
            'pairwise_transport_status': 'pairwise-transport-chain-strong',
            'triple_transport_cocycle_status': 'triple-transport-cocycle-strong',
            'global_transport_potential_status': 'global-transport-potential-strong',
            'tail_cauchy_potential_status': 'tail-cauchy-potential-strong',
            'certified_tail_modulus_status': 'certified-tail-modulus-strong',
            'rate_aware_tail_modulus_status': 'rate-aware-tail-modulus-strong',
            'golden_recurrence_rate_status': 'golden-recurrence-rate-strong',
            'transport_slope_weighted_golden_rate_status': 'transport-slope-weighted-golden-rate-strong',
            'edge_class_weighted_golden_rate_status': 'edge-class-weighted-golden-rate-strong',
            'upper_tail_status': 'golden-supercritical-tail-stability-strong',
            'lower_status': 'golden-lower-neighborhood-stability-strong',
            'native_late_coherent_suffix_witness_width': 9.0e-5,
            'native_late_coherent_suffix_length': 4,
            'native_late_coherent_suffix_contracting': True,
            'native_late_coherent_suffix_contraction_ratio': 2.4,
        },
        'theorem_v_explicit_error_control': {
            'theorem_status': 'theorem-v-explicit-error-law-strong',
            'compatible_interval_nonempty': True,
            'monotone_error_law_nonincreasing': True,
            'active_bounds_dominate_compatible_errors': True,
            'active_bounds_dominate_certificate_totals': True,
            'compatible_limit_interval_width': 2.5e-4,
        },
    }))
    cert = build_golden_theorem_v_transport_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-v-transport-lift-front-only'
    assert cert['open_hypotheses'] == []
    assert set(cert['active_assumptions']) == {
        'validated_function_space_continuation_transport',
        'unique_branch_continuation_to_true_irrational_threshold',
        'uniform_error_law_preserves_golden_gap',
    }


def test_transport_lift_conditional_strong_when_assumptions_are_toggled_on(monkeypatch) -> None:
    import kam_theorem_suite.theorem_v_transport_lift as tvtl

    monkeypatch.setattr(tvtl, 'build_golden_rational_to_irrational_convergence_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-rational-to-irrational-convergence-strong',
        'relation': {
            'gap_to_compatible_upper': 0.02,
            'convergence_status': 'irrational-limit-control-strong',
            'branch_certified_status': 'branch-certified-limit-strong',
            'nested_subladder_status': 'nested-subladder-limit-strong',
            'convergent_family_status': 'convergent-family-limit-strong',
            'transport_certified_status': 'transport-certified-limit-strong',
            'pairwise_transport_status': 'pairwise-transport-chain-strong',
            'triple_transport_cocycle_status': 'triple-transport-cocycle-strong',
            'global_transport_potential_status': 'global-transport-potential-strong',
            'tail_cauchy_potential_status': 'tail-cauchy-potential-strong',
            'certified_tail_modulus_status': 'certified-tail-modulus-strong',
            'rate_aware_tail_modulus_status': 'rate-aware-tail-modulus-strong',
            'golden_recurrence_rate_status': 'golden-recurrence-rate-strong',
            'transport_slope_weighted_golden_rate_status': 'transport-slope-weighted-golden-rate-strong',
            'edge_class_weighted_golden_rate_status': 'edge-class-weighted-golden-rate-strong',
            'upper_tail_status': 'golden-supercritical-tail-stability-strong',
            'lower_status': 'golden-lower-neighborhood-stability-strong',
            'native_late_coherent_suffix_witness_width': 8.0e-5,
            'native_late_coherent_suffix_length': 4,
            'native_late_coherent_suffix_contracting': True,
            'native_late_coherent_suffix_contraction_ratio': 2.8,
        },
        'theorem_v_explicit_error_control': {
            'theorem_status': 'theorem-v-explicit-error-law-strong',
            'compatible_interval_nonempty': True,
            'monotone_error_law_nonincreasing': True,
            'active_bounds_dominate_compatible_errors': True,
            'active_bounds_dominate_certificate_totals': True,
            'compatible_limit_interval_width': 2.0e-4,
        },
    }))
    cert = build_golden_theorem_v_transport_lift_certificate(
        base_K_values=[0.3],
        assume_validated_function_space_continuation_transport=True,
        assume_unique_branch_continuation_to_true_irrational_threshold=True,
        assume_uniform_error_law_preserves_golden_gap=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-v-transport-lift-conditional-strong'
    assert cert['active_assumptions'] == []


def test_transport_lift_stays_partial_when_front_is_not_closed(monkeypatch) -> None:
    import kam_theorem_suite.theorem_v_transport_lift as tvtl

    monkeypatch.setattr(tvtl, 'build_golden_rational_to_irrational_convergence_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-rational-to-irrational-convergence-partial',
        'relation': {
            'gap_to_compatible_upper': 0.002,
            'convergence_status': 'irrational-limit-control-strong',
            'branch_certified_status': 'branch-certified-limit-strong',
            'nested_subladder_status': 'nested-subladder-limit-strong',
            'convergent_family_status': 'convergent-family-limit-strong',
            'transport_certified_status': 'transport-certified-limit-strong',
            'pairwise_transport_status': 'pairwise-transport-chain-strong',
            'triple_transport_cocycle_status': 'triple-transport-cocycle-strong',
            'global_transport_potential_status': 'global-transport-potential-strong',
            'tail_cauchy_potential_status': 'tail-cauchy-potential-strong',
            'certified_tail_modulus_status': 'certified-tail-modulus-strong',
            'rate_aware_tail_modulus_status': 'rate-aware-tail-modulus-strong',
            'golden_recurrence_rate_status': 'golden-recurrence-rate-strong',
            'transport_slope_weighted_golden_rate_status': 'transport-slope-weighted-golden-rate-strong',
            'edge_class_weighted_golden_rate_status': 'edge-class-weighted-golden-rate-strong',
            'upper_tail_status': 'golden-supercritical-tail-stability-strong',
            'lower_status': 'golden-lower-neighborhood-stability-strong',
        },
        'theorem_v_explicit_error_control': {
            'theorem_status': 'theorem-v-explicit-error-law-moderate',
            'compatible_interval_nonempty': False,
            'monotone_error_law_nonincreasing': True,
            'active_bounds_dominate_compatible_errors': False,
            'active_bounds_dominate_certificate_totals': True,
            'compatible_limit_interval_width': None,
        },
    }))
    cert = build_golden_theorem_v_transport_lift_certificate(
        base_K_values=[0.3],
        assume_validated_function_space_continuation_transport=True,
        assume_unique_branch_continuation_to_true_irrational_threshold=True,
        assume_uniform_error_law_preserves_golden_gap=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-v-transport-lift-conditional-partial'
    assert 'explicit_error_interval_nonempty' in cert['open_hypotheses']
    assert 'active_bounds_dominate_errors' in cert['open_hypotheses']


def test_driver_exposes_transport_lift_and_theorem_v_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_theorem_v_transport_lift_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-v-transport-lift-front-only',
        'active_assumptions': ['validated_function_space_continuation_transport'],
    }))
    monkeypatch.setattr(pd, 'build_golden_theorem_v_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-v-transport-lift-conditional-strong',
        'active_assumptions': [],
    }))

    lift_report = build_golden_theorem_v_transport_lift_report(base_K_values=[0.3])
    theorem_report = build_golden_theorem_v_report(base_K_values=[0.3])
    assert lift_report['theorem_status'] == 'golden-theorem-v-transport-lift-front-only'
    assert theorem_report['theorem_status'] == 'golden-theorem-v-transport-lift-conditional-strong'
