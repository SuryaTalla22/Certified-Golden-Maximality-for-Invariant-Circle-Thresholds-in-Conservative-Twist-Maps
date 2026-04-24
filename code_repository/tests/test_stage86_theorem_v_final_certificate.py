from __future__ import annotations

from kam_theorem_suite.theorem_v_transport_lift import build_golden_theorem_v_transport_lift_certificate


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def _final_front(*, gap_preserved: bool = True):
    return {
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
            'late_coherent_suffix_status': 'late-coherent-suffix-strong',
            'late_coherent_suffix_length': 4,
        },
        'theorem_v_final_error_control': {
            'theorem_status': 'theorem-v-final-error-law-strong' if gap_preserved else 'theorem-v-final-error-law-gap-preservation-incomplete',
            'theorem_target_interval': [0.971095, 0.971105],
            'theorem_target_width': 1.0e-5,
            'final_error_law_certified': True,
            'continuation_ready': True,
            'transport_ready': True,
            'error_law_preserves_gap': gap_preserved,
            'gap_preservation_margin': 2.0e-6 if gap_preserved else -1.0e-6,
        },
        'final_transport_bridge': {
            'transport_bridge_locked': True,
            'transport_bridge_with_identification_lock': True,
            'bridge_status': 'final-transport-bridge-strong' if gap_preserved else 'final-transport-bridge-gap-preservation-incomplete',
        },
    }


def test_stage86_transport_lift_closes_to_final_strong(monkeypatch) -> None:
    import kam_theorem_suite.theorem_v_transport_lift as tvtl

    monkeypatch.setattr(tvtl, 'build_golden_rational_to_irrational_convergence_certificate', lambda **kwargs: _Dummy(_final_front(gap_preserved=True)))
    cert = build_golden_theorem_v_transport_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-v-final-strong'
    assert cert['theorem_v_final_status'] == 'final-strong'
    assert cert['active_assumptions'] == []
    assert cert['theorem_target_interval'] == [0.971095, 0.971105]
    assert cert['gap_preservation_margin'] == 2.0e-6


def test_stage86_transport_lift_detects_gap_preservation_incomplete(monkeypatch) -> None:
    import kam_theorem_suite.theorem_v_transport_lift as tvtl

    monkeypatch.setattr(tvtl, 'build_golden_rational_to_irrational_convergence_certificate', lambda **kwargs: _Dummy(_final_front(gap_preserved=False)))
    cert = build_golden_theorem_v_transport_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-v-gap-preservation-incomplete'
    assert cert['theorem_v_final_status'] == 'gap-preservation-incomplete'
    assert cert['active_assumptions'] == ['uniform_error_law_preserves_golden_gap']
