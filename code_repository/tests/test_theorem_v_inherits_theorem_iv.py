from __future__ import annotations

import json
from pathlib import Path

from kam_theorem_suite.golden_limit_bridge import build_golden_rational_to_irrational_convergence_certificate
from kam_theorem_suite.golden_upper_tail_stability import (
    build_golden_upper_tail_stability_certificate_from_theorem_iv,
)
from kam_theorem_suite.proof_driver import build_golden_theorem_program_discharge_status_report
from kam_theorem_suite.theorem_v_transport_lift import build_golden_theorem_v_transport_lift_certificate


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def _real_theorem_iv_artifact() -> dict:
    artifact = Path(__file__).resolve().parents[1] / 'artifacts' / 'final_discharge' / 'stage_cache' / 'theorem_iv.json'
    with artifact.open() as handle:
        return json.load(handle)


def _minimal_theorem_iv() -> dict:
    return {
        'rho': 0.6180339887498949,
        'family_label': 'standard-sine',
        'theorem_status': 'golden-theorem-iv-final-strong',
        'nonexistence_contradiction_certified': True,
        'open_hypotheses': [],
        'nonexistence_front': {
            'upper_bridge': {
                'theorem_status': 'golden-incompatibility-theorem-bridge-strong',
                'certified_upper_lo': 0.9702729059999999,
                'certified_upper_hi': 0.9717820875185549,
                'certified_upper_width': 0.0015091815185549473,
                'certified_barrier_lo': 1.0366258097576748,
                'certified_barrier_hi': 1.0367050853686908,
                'certified_tail_qs': [144, 233],
                'certified_tail_start_q': 144,
                'certified_tail_is_suffix': True,
                'support_fraction_floor': 1.0,
                'supporting_entry_count': 5,
            },
            'upper_tail_stability': {
                'theorem_status': 'golden-adaptive-tail-stability-strong',
                'base_crossing_center': 0.971635406,
                'atlas_shift_grid': [-0.0006, -0.0003, 0.0, 0.0003, 0.0006],
                'successful_entry_indices': [0, 1, 2, 3, 4],
                'clustered_entry_indices': [0, 1, 2, 3, 4],
                'stable_tail_qs': [144, 233],
                'stable_tail_start_q': 144,
                'stable_tail_support_count': 5,
                'stable_tail_support_fraction': 1.0,
                'stable_tail_is_suffix_of_generated_union': True,
                'stable_q_union': [21, 34, 55, 89, 144, 233],
                'stable_q_intersection': [144, 233],
                'stable_upper_lo': 0.9702729059999999,
                'stable_upper_hi': 0.9717820875185549,
                'stable_upper_width': 0.0015091815185549473,
                'stable_barrier_lo': 1.0366258097576748,
                'stable_barrier_hi': 1.0367050853686908,
                'entries': [
                    {
                        'atlas_shift': 0.0,
                        'crossing_center': 0.971635406,
                        'theorem_status': 'golden-adaptive-incompatibility-strong',
                        'selected_upper_lo': 0.9702729059999999,
                        'selected_upper_hi': 0.9717820875185549,
                        'selected_upper_width': 0.0015091815185549473,
                        'stable_tail_qs': [144, 233],
                        'stable_tail_start_q': 144,
                        'generated_qs': [21, 34, 55, 89, 144, 233],
                        'witness_qs': [34, 55, 89, 144, 233],
                        'tail_is_suffix_of_generated': True,
                        'fully_certified_count': 5,
                    }
                ],
            },
        },
    }


def _dummy_upper_obstruction():
    return {
        'ladder': {
            'approximants': [
                {'p': 5, 'q': 8, 'label': 'g-5/8', 'crossing_root_window_lo': 0.97100, 'crossing_root_window_hi': 0.97128, 'crossing_center': 0.97114, 'bridge_report': {'crossing_certificate': {'certification_tier': 'monotone_window', 'derivative_away_from_zero': True, 'interval_newton': {'success': False}, 'branch_summary': {'gprime_interval_lo': 0.7, 'gprime_interval_hi': 1.0, 'tangent_inclusion_success': True, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 3e-4}}}}},
                {'p': 8, 'q': 13, 'label': 'g-8/13', 'crossing_root_window_lo': 0.97108, 'crossing_root_window_hi': 0.97124, 'crossing_center': 0.97116, 'bridge_report': {'crossing_certificate': {'certification_tier': 'interval_newton', 'derivative_away_from_zero': True, 'interval_newton': {'success': True}, 'branch_summary': {'gprime_interval_lo': 0.9, 'gprime_interval_hi': 1.2, 'tangent_inclusion_success': True, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 2e-4}}}}},
                {'p': 13, 'q': 21, 'label': 'g-13/21', 'crossing_root_window_lo': 0.97112, 'crossing_root_window_hi': 0.97120, 'crossing_center': 0.97116, 'bridge_report': {'crossing_certificate': {'certification_tier': 'interval_newton', 'derivative_away_from_zero': True, 'interval_newton': {'success': True}, 'branch_summary': {'gprime_interval_lo': 1.0, 'gprime_interval_hi': 1.3, 'tangent_inclusion_success': True, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 1e-4}}}}},
                {'p': 21, 'q': 34, 'label': 'g-21/34', 'crossing_root_window_lo': 0.97114, 'crossing_root_window_hi': 0.97118, 'crossing_center': 0.97116, 'bridge_report': {'crossing_certificate': {'certification_tier': 'interval_newton', 'derivative_away_from_zero': True, 'interval_newton': {'success': True}, 'branch_summary': {'gprime_interval_lo': 1.1, 'gprime_interval_hi': 1.4, 'tangent_inclusion_success': True, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 7e-5}}}}},
            ]
        },
        'refined': {'selected_cluster_member_qs': [8, 13, 21, 34]},
        'asymptotic_audit': {'audited_upper_source_threshold': 13},
        'theorem_status': 'golden-supercritical-obstruction-moderate',
    }


def test_theorem_iv_adapter_uses_real_cached_artifact() -> None:
    cert = build_golden_upper_tail_stability_certificate_from_theorem_iv(_real_theorem_iv_artifact()).to_dict()
    assert cert['theorem_status'] == 'golden-supercritical-tail-stability-strong'
    assert cert['stable_upper_source'] == 'theorem-iv-final-object'
    assert cert['stable_tail_qs'] == [144, 233]
    assert cert['stable_tail_start_q'] == 144
    assert len(cert['entries']) >= 1


def test_golden_limit_bridge_inherits_theorem_iv_upper_tail(monkeypatch) -> None:
    import kam_theorem_suite.golden_limit_bridge as glb

    monkeypatch.setattr(
        glb,
        'build_golden_lower_neighborhood_stability_certificate',
        lambda **kwargs: _Dummy(
            {
                'stable_lower_bound': 0.96,
                'stable_observed_upper_hint': 0.965,
                'theorem_status': 'golden-lower-neighborhood-stability-strong',
            }
        ),
    )
    monkeypatch.setattr(
        glb,
        'build_golden_supercritical_obstruction_certificate',
        lambda **kwargs: _Dummy(_dummy_upper_obstruction()),
    )
    monkeypatch.setattr(
        glb,
        'build_golden_upper_tail_stability_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('legacy upper-tail builder should not run when theorem IV is supplied')),
    )
    monkeypatch.setattr(glb, 'build_rational_irrational_convergence_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'irrational-limit-control-strong'}))
    monkeypatch.setattr(glb, 'build_branch_certified_irrational_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'branch-certified-limit-strong'}))
    monkeypatch.setattr(glb, 'build_nested_subladder_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'nested-subladder-limit-strong'}))
    monkeypatch.setattr(glb, 'build_convergent_family_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'convergent-family-limit-strong'}))
    monkeypatch.setattr(glb, 'build_transport_certified_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'transport-certified-limit-strong'}))
    monkeypatch.setattr(glb, 'build_pairwise_transport_chain_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'pairwise-transport-chain-strong'}))
    monkeypatch.setattr(glb, 'build_triple_transport_cocycle_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'triple-transport-cocycle-strong'}))
    monkeypatch.setattr(glb, 'build_global_transport_potential_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'global-transport-potential-strong'}))
    monkeypatch.setattr(glb, 'build_tail_cauchy_potential_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'tail-cauchy-potential-strong'}))
    monkeypatch.setattr(glb, 'build_certified_tail_modulus_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'certified-tail-modulus-strong'}))
    monkeypatch.setattr(glb, 'build_rate_aware_tail_modulus_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'rate-aware-tail-modulus-strong'}))
    monkeypatch.setattr(glb, 'build_golden_recurrence_rate_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'golden-recurrence-rate-strong'}))
    monkeypatch.setattr(glb, 'build_transport_slope_weighted_golden_rate_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'transport-slope-weighted-golden-rate-strong'}))
    monkeypatch.setattr(glb, 'build_edge_class_weighted_golden_rate_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'edge-class-weighted-golden-rate-strong'}))
    monkeypatch.setattr(glb, 'build_theorem_v_explicit_error_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'theorem-v-explicit-error-law-strong'}))
    monkeypatch.setattr(glb, 'build_theorem_v_final_error_law_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'theorem-v-final-error-law-strong'}))

    cert = build_golden_rational_to_irrational_convergence_certificate(
        base_K_values=[0.4, 0.5, 0.6],
        theorem_iv_certificate=_minimal_theorem_iv(),
    ).to_dict()
    relation = cert['relation']
    assert relation['upper_tail_inherited_from_theorem_iv'] is True
    assert relation['upper_tail_source'] == 'theorem-iv-final-object'
    assert relation['theorem_iv_status'] == 'golden-theorem-iv-final-strong'
    assert relation['theorem_iv_contradiction_certified'] is True
    assert cert['upper_tail_stability']['stable_tail_qs'] == [144, 233]


def test_theorem_v_transport_lift_marks_inherited_theorem_iv_source(monkeypatch) -> None:
    import kam_theorem_suite.theorem_v_transport_lift as tvtl

    monkeypatch.setattr(
        tvtl,
        'build_golden_rational_to_irrational_convergence_certificate',
        lambda **kwargs: _Dummy(
            {
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
                    'upper_tail_inherited_from_theorem_iv': True,
                    'upper_tail_source': 'theorem-iv-final-object',
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
                'theorem_v_final_error_control': {},
                'final_transport_bridge': {},
            }
        ),
    )
    cert = build_golden_theorem_v_transport_lift_certificate(base_K_values=[0.3]).to_dict()
    row = next(h for h in cert['hypotheses'] if h['name'] == 'upper_tail_stability_closed')
    assert row['source'] == 'theorem-iv.final-upper-package'
    assert 'Theorem-IV' in row['note']


def test_proof_driver_passes_theorem_iv_into_theorem_v(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    theorem_iv_obj = {'theorem_status': 'golden-theorem-iv-final-strong', 'active_assumptions': []}

    monkeypatch.setattr(pd, 'build_golden_theorem_i_ii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-i-ii-workstream-papergrade-final', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_iii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-iii-final-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_iv_lower_neighborhood_report', lambda **kwargs: {'theorem_status': 'golden-lower-neighborhood-stability-strong'})
    monkeypatch.setattr(pd, 'build_golden_theorem_iv_report', lambda **kwargs: theorem_iv_obj)

    def _theorem_v(**kwargs):
        assert kwargs['theorem_iv_certificate'] is theorem_iv_obj
        return {'theorem_status': 'golden-theorem-v-final-strong', 'active_assumptions': []}

    monkeypatch.setattr(pd, 'build_golden_theorem_v_report', _theorem_v)
    monkeypatch.setattr(pd, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {'theorem_status': 'golden-theorem-ii-to-v-identification-final-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_ii_to_v_identification_discharge_report', lambda **kwargs: {'theorem_status': 'golden-theorem-ii-to-v-identification-discharge-final-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_ii_to_v_identification_transport_discharge_report', lambda **kwargs: {'theorem_status': 'golden-theorem-v-identification-transport-discharge-final-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_ii_to_v_identification_theorem_report', lambda **kwargs: {'theorem_status': 'golden-theorem-ii-to-v-identification-theorem-final-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_vi_report', lambda **kwargs: {'theorem_status': 'golden-theorem-vi-envelope-lift-global-one-variable-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_vi_discharge_report', lambda **kwargs: {'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-global-one-variable-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_vii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-vii-exhaustion-lift-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_vii_discharge_report', lambda **kwargs: {'theorem_status': 'golden-theorem-vii-exhaustion-discharge-final-strong', 'active_assumptions': [], 'papergrade_final': True})
    monkeypatch.setattr(pd, 'build_golden_theorem_viii_report', lambda **kwargs: {'theorem_status': 'golden-universal-theorem-codepath-strong', 'active_assumptions': [], 'current_reduction_geometry_summary': {'available': True, 'status': 'current-reduction-geometry-strong', 'source': 'test', 'minimum_certified_margin': 0.1}})
    monkeypatch.setattr(pd, 'build_golden_theorem_viii_discharge_report', lambda **kwargs: {'theorem_status': 'golden-universal-theorem-final-strong', 'active_assumptions': [], 'final_certificate_ready_for_code_path': True, 'final_certificate_ready_for_paper': True, 'remaining_true_mathematical_burden': [], 'remaining_workstream_paper_grade_burden': [], 'remaining_exhaustion_paper_grade_burden': [], 'current_reduction_geometry_summary': {'available': True, 'status': 'current-reduction-geometry-strong', 'source': 'test', 'minimum_certified_margin': 0.1}})

    report = build_golden_theorem_program_discharge_status_report(base_K_values=[0.2, 0.25])
    assert report['subreports']['theorem_iv']['theorem_status'] == 'golden-theorem-iv-final-strong'
