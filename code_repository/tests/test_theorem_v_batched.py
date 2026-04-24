from __future__ import annotations

import json
from pathlib import Path

from kam_theorem_suite.proof_driver import build_golden_theorem_v_batched_report
from kam_theorem_suite.theorem_v_batched import (
    build_golden_rational_to_irrational_convergence_certificate_batched,
)


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


def _upper_seed_payload() -> dict:
    return {
        'ladder': {
            'approximants': [
                {'p': 13, 'q': 21, 'label': 'g-13/21', 'crossing_root_window_lo': 0.97112, 'crossing_root_window_hi': 0.97120, 'crossing_center': 0.97116},
                {'p': 21, 'q': 34, 'label': 'g-21/34', 'crossing_root_window_lo': 0.97114, 'crossing_root_window_hi': 0.97118, 'crossing_center': 0.97116},
                {'p': 34, 'q': 55, 'label': 'g-34/55', 'crossing_root_window_lo': 0.97121, 'crossing_root_window_hi': 0.97123, 'crossing_center': 0.97122},
                {'p': 55, 'q': 89, 'label': 'g-55/89', 'crossing_root_window_lo': 0.97143, 'crossing_root_window_hi': 0.97144, 'crossing_center': 0.971435},
                {'p': 89, 'q': 144, 'label': 'g-89/144', 'crossing_root_window_lo': 0.97150, 'crossing_root_window_hi': 0.97154, 'crossing_center': 0.97152},
                {'p': 144, 'q': 233, 'label': 'g-144/233', 'crossing_root_window_lo': 0.97160, 'crossing_root_window_hi': 0.97164, 'crossing_center': 0.97162},
            ],
        },
        'refined': {'selected_cluster_member_qs': [21, 34, 55, 89, 144, 233]},
        'asymptotic_audit': {'audited_upper_source_threshold': 144, 'status': 'asymptotic-upper-audit-strong'},
        'selected_upper_source': 'theorem-iv-final-object',
        'theorem_status': 'golden-supercritical-obstruction-strong',
    }


def _front_payload() -> dict:
    return {
        'theorem_status': 'golden-rational-to-irrational-convergence-strong',
        'relation': {
            'upper_side_inherited_from_theorem_iv': True,
            'upper_tail_inherited_from_theorem_iv': True,
            'upper_side_source': 'theorem-iv-final-object',
            'upper_tail_source': 'theorem-iv-final-object',
        },
        'lower_neighborhood': {'theorem_status': 'golden-lower-neighborhood-stability-strong'},
        'upper_side_obstruction': {'theorem_status': 'golden-supercritical-obstruction-strong'},
        'upper_tail_stability': {'theorem_status': 'golden-supercritical-tail-stability-strong'},
        'convergence_control': {'theorem_status': 'irrational-limit-control-strong'},
        'branch_certified_limit_control': {'theorem_status': 'branch-certified-limit-strong'},
        'nested_subladder_limit_control': {'theorem_status': 'nested-subladder-limit-strong'},
        'convergent_family_limit_control': {'theorem_status': 'convergent-family-limit-strong'},
        'transport_certified_limit_control': {'theorem_status': 'transport-certified-limit-strong'},
        'pairwise_transport_chain_control': {'theorem_status': 'pairwise-transport-chain-strong'},
        'triple_transport_cocycle_control': {'theorem_status': 'triple-transport-cocycle-strong'},
        'global_transport_potential_control': {'theorem_status': 'global-transport-potential-strong'},
        'tail_cauchy_potential_control': {'theorem_status': 'tail-cauchy-potential-strong'},
        'certified_tail_modulus_control': {'theorem_status': 'certified-tail-modulus-strong'},
        'rate_aware_tail_modulus_control': {'theorem_status': 'rate-aware-tail-modulus-strong'},
        'golden_recurrence_rate_control': {'theorem_status': 'golden-recurrence-rate-strong'},
        'transport_slope_weighted_golden_rate_control': {'theorem_status': 'transport-slope-weighted-golden-rate-strong'},
        'edge_class_weighted_golden_rate_control': {'theorem_status': 'edge-class-weighted-golden-rate-strong'},
        'theorem_v_explicit_error_control': {'theorem_status': 'theorem-v-explicit-error-law-strong'},
        'theorem_v_final_error_control': {'theorem_status': 'theorem-v-final-error-law-strong'},
        'theorem_v_uniform_error_law': {'theorem_status': 'theorem-v-uniform-error-law-strong'},
        'theorem_v_branch_identification': {'theorem_status': 'theorem-v-branch-identification-strong'},
        'runtime_row_233_377': {'theorem_status': 'runtime-aware-row-skipped'},
        'runtime_row_377_610': {'theorem_status': 'runtime-aware-row-skipped'},
        'final_transport_bridge': {'theorem_status': 'theorem-v-final-transport-bridge-strong'},
    }


def _monkeypatch_lightweight_batched_pipeline(monkeypatch) -> None:
    import kam_theorem_suite.theorem_v_batched as tvb

    monkeypatch.setattr(
        tvb,
        'build_golden_lower_neighborhood_stability_certificate',
        lambda **kwargs: _Dummy({'stable_lower_bound': 0.96, 'stable_observed_upper_hint': 0.965, 'theorem_status': 'golden-lower-neighborhood-stability-strong'}),
    )
    monkeypatch.setattr(
        tvb,
        'build_golden_supercritical_obstruction_certificate_from_theorem_iv',
        lambda *args, **kwargs: _Dummy(_upper_seed_payload()),
    )
    monkeypatch.setattr(
        tvb,
        'build_golden_upper_tail_stability_certificate_from_theorem_iv',
        lambda *args, **kwargs: _Dummy({'theorem_status': 'golden-supercritical-tail-stability-strong', 'stable_upper_source': 'theorem-iv-final-object', 'stable_tail_qs': [144, 233]}),
    )
    monkeypatch.setattr(tvb, 'build_rational_irrational_convergence_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'irrational-limit-control-strong'}))
    monkeypatch.setattr(tvb, 'build_branch_certified_irrational_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'branch-certified-limit-strong'}))
    monkeypatch.setattr(tvb, 'build_nested_subladder_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'nested-subladder-limit-strong'}))
    monkeypatch.setattr(tvb, 'build_convergent_family_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'convergent-family-limit-strong'}))
    monkeypatch.setattr(tvb, 'build_transport_certified_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'transport-certified-limit-strong'}))
    monkeypatch.setattr(tvb, 'build_pairwise_transport_chain_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'pairwise-transport-chain-strong'}))
    monkeypatch.setattr(tvb, 'build_triple_transport_cocycle_limit_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'triple-transport-cocycle-strong'}))
    monkeypatch.setattr(tvb, 'build_global_transport_potential_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'global-transport-potential-strong'}))
    monkeypatch.setattr(tvb, 'build_tail_cauchy_potential_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'tail-cauchy-potential-strong'}))
    monkeypatch.setattr(tvb, 'build_certified_tail_modulus_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'certified-tail-modulus-strong'}))
    monkeypatch.setattr(tvb, 'build_rate_aware_tail_modulus_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'rate-aware-tail-modulus-strong'}))
    monkeypatch.setattr(tvb, 'build_golden_recurrence_rate_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'golden-recurrence-rate-strong'}))
    monkeypatch.setattr(tvb, 'build_transport_slope_weighted_golden_rate_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'transport-slope-weighted-golden-rate-strong'}))
    monkeypatch.setattr(tvb, 'build_edge_class_weighted_golden_rate_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'edge-class-weighted-golden-rate-strong'}))
    monkeypatch.setattr(tvb, 'build_theorem_v_explicit_error_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'theorem-v-explicit-error-law-strong'}))
    monkeypatch.setattr(tvb, 'build_theorem_v_final_error_law_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'theorem-v-final-error-law-strong', 'theorem_target_interval': [0.97136, 0.971367], 'theorem_target_width': 7e-06, 'final_error_law_certified': True, 'error_law_preserves_gap': True}))
    monkeypatch.setattr(tvb, 'build_runtime_aware_theorem_v_row_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'runtime-aware-row-skipped', 'label': f"gold-{kwargs.get('p',0)}/{kwargs.get('q',0)}", 'q': kwargs.get('q',0), 'direct_attempt_proof_ready': False}))
    monkeypatch.setattr(tvb, 'build_theorem_v_uniform_error_law_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'theorem-v-uniform-error-law-strong', 'final_error_law_certified': True, 'gap_preservation_certified': True, 'transport_ready': True}))
    monkeypatch.setattr(tvb, 'build_theorem_v_branch_identification_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'theorem-v-branch-identification-strong', 'branch_identification_locked': True}))
    monkeypatch.setattr(tvb, 'build_final_transport_bridge_certificate', lambda *args, **kwargs: _Dummy({'theorem_status': 'theorem-v-final-transport-bridge-strong', 'bridge_status': 'final-transport-bridge-strong', 'transport_bridge_locked': True}))
    monkeypatch.setattr(tvb, 'build_golden_rational_to_irrational_convergence_certificate', lambda *args, **kwargs: _Dummy(_front_payload()))
    monkeypatch.setattr(
        tvb,
        'build_golden_theorem_v_transport_lift_certificate',
        lambda *args, **kwargs: _Dummy({'theorem_status': 'golden-theorem-v-transport-lift-strong', 'convergence_front': dict(kwargs.get('convergence_front_certificate') or _front_payload())}),
    )


def test_batched_front_inherits_theorem_iv_and_records_stage_timings(monkeypatch, tmp_path) -> None:
    _monkeypatch_lightweight_batched_pipeline(monkeypatch)
    bundle = build_golden_rational_to_irrational_convergence_certificate_batched(
        base_K_values=[0.2, 0.25],
        theorem_iv_certificate=_real_theorem_iv_artifact(),
        use_cache=False,
        force_rebuild=True,
        stage_cache_dir=tmp_path,
    )
    cert = bundle['certificate']
    relation = cert['relation']
    assert relation['upper_side_inherited_from_theorem_iv'] is True
    assert relation['upper_tail_inherited_from_theorem_iv'] is True
    assert 'theorem_v_upper_seed' in bundle['stage_timings']
    assert 'theorem_v_convergence' in bundle['stage_timings']
    assert 'theorem_v_runtime_row_233_377' in bundle['stage_timings']
    assert 'theorem_v_uniform_error_law' in bundle['stage_timings']
    assert 'theorem_v_branch_identification' in bundle['stage_timings']
    assert 'theorem_v_front' in bundle['stage_timings']
    assert Path(bundle['stage_cache_dir']).exists()


def test_batched_front_skips_legacy_upper_obstruction_builder_when_theorem_iv_is_supplied(monkeypatch, tmp_path) -> None:
    import kam_theorem_suite.theorem_v_batched as tvb

    _monkeypatch_lightweight_batched_pipeline(monkeypatch)
    monkeypatch.setattr(
        tvb,
        'build_golden_supercritical_obstruction_certificate',
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError('legacy upper obstruction builder should not run when theorem IV is supplied')
        ),
    )
    cert = build_golden_rational_to_irrational_convergence_certificate_batched(
        base_K_values=[0.2, 0.25],
        theorem_iv_certificate=_minimal_theorem_iv(),
        use_cache=False,
        force_rebuild=True,
        stage_cache_dir=tmp_path,
    )['certificate']
    assert cert['relation']['upper_side_inherited_from_theorem_iv'] is True


def test_batched_report_threads_stage_timings_and_inherited_upper_side(monkeypatch, tmp_path) -> None:
    _monkeypatch_lightweight_batched_pipeline(monkeypatch)
    bundle = build_golden_theorem_v_batched_report(
        base_K_values=[0.2, 0.25],
        theorem_iv_certificate=_real_theorem_iv_artifact(),
        use_cache=False,
        force_rebuild=True,
        stage_cache_dir=tmp_path,
    )
    assert 'certificate' in bundle
    assert 'stage_timings' in bundle
    cert = bundle['certificate']
    assert cert['convergence_front']['relation']['upper_side_inherited_from_theorem_iv'] is True
    assert 'theorem_v_lift' in bundle['stage_timings']
