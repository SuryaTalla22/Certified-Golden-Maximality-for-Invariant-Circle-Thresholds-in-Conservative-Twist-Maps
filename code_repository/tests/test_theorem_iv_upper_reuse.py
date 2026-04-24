from __future__ import annotations

from kam_theorem_suite.nonexistence_front import build_golden_nonexistence_front_certificate
from kam_theorem_suite.proof_driver import build_golden_theorem_program_discharge_status_report


def _dummy_obj(payload):
    return type('D', (), {'to_dict': lambda self: payload})()


def test_nonexistence_front_reuses_supplied_upper_certificates(monkeypatch) -> None:
    import kam_theorem_suite.nonexistence_front as nf

    lower = {
        'theorem_status': 'golden-lower-neighborhood-stability-strong',
        'stable_lower_bound': 0.3,
        'stable_window_hi': 0.35,
        'stable_window_width': 0.05,
        'distinct_resolution_signatures': [1, 2],
    }
    upper_bridge = {
        'theorem_status': 'golden-incompatibility-theorem-bridge-strong',
        'certified_upper_lo': 0.5,
        'certified_upper_hi': 0.6,
        'certified_upper_width': 0.1,
        'certified_barrier_lo': 0.7,
        'certified_barrier_hi': 0.8,
        'certified_barrier_width': 0.1,
        'certified_tail_qs': [13, 21],
        'certified_tail_is_suffix': True,
        'supporting_entry_count': 2,
        'support_fraction_floor': 1.0,
        'entry_coverage_floor': 1.0,
        'bridge_margin': 0.1,
        'missing_hypotheses': [],
    }
    upper_support = {
        'theorem_status': 'golden-adaptive-support-core-neighborhood-strong',
        'selected_bridge': upper_bridge,
    }
    upper_tail_aware = {
        'theorem_status': 'golden-adaptive-tail-aware-neighborhood-strong',
        'selected_bridge': upper_bridge,
    }
    upper_tail_stability = {
        'theorem_status': 'golden-adaptive-tail-stability-strong',
        'stable_incompatibility_gap': 0.1,
    }
    upper_profile = {
        'theorem_status': 'golden-incompatibility-bridge-profile-strong',
        'selected_bridge': upper_bridge,
    }

    monkeypatch.setattr(
        nf,
        'build_golden_lower_neighborhood_stability_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('lower should be reused')),
    )
    monkeypatch.setattr(
        nf,
        'build_golden_incompatibility_theorem_bridge_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('upper bridge should be reused')),
    )
    monkeypatch.setattr(
        nf,
        'build_golden_incompatibility_strict_bridge_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('strict bridge should be reused')),
    )
    monkeypatch.setattr(
        nf,
        'build_golden_adaptive_support_core_neighborhood_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('support core should be reused')),
    )
    monkeypatch.setattr(
        nf,
        'build_golden_adaptive_tail_aware_neighborhood_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('tail-aware should be reused')),
    )
    monkeypatch.setattr(
        nf,
        'build_golden_adaptive_tail_stability_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('tail stability should be reused')),
    )
    monkeypatch.setattr(
        nf,
        'build_golden_incompatibility_bridge_profile_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('bridge profile should be reused')),
    )

    cert = build_golden_nonexistence_front_certificate(
        base_K_values=[0.2, 0.25],
        lower_neighborhood_stability_certificate=lower,
        upper_bridge_certificate=upper_bridge,
        upper_bridge_promotion_certificate=upper_bridge,
        upper_support_core_neighborhood_certificate=upper_support,
        upper_tail_aware_neighborhood_certificate=upper_tail_aware,
        upper_tail_stability_certificate=upper_tail_stability,
        upper_bridge_profile_certificate=upper_profile,
    ).to_dict()

    assert cert['lower_side']['theorem_status'] == 'golden-lower-neighborhood-stability-strong'
    assert cert['upper_bridge']['theorem_status'] == 'golden-incompatibility-theorem-bridge-strong'
    assert cert['upper_support_core_neighborhood']['theorem_status'] == 'golden-adaptive-support-core-neighborhood-strong'



def test_support_core_reuses_supplied_baseline_tail_coherence(monkeypatch) -> None:
    import kam_theorem_suite.adaptive_support_core_neighborhood as sc

    baseline = {
        'theorem_status': 'golden-adaptive-tail-coherence-strong',
        'entries': [],
        'supporting_entry_indices': [],
        'clustered_entry_indices': [],
        'successful_entry_indices': [],
    }
    monkeypatch.setattr(
        sc,
        'build_golden_adaptive_tail_coherence_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('baseline coherence should be reused')),
    )
    monkeypatch.setattr(
        sc,
        '_build_golden_incompatibility_strict_bridge_from_coherence_payload',
        lambda *args, **kwargs: _dummy_obj({
            'theorem_status': 'golden-incompatibility-theorem-bridge-strong',
            'bridge_margin': 0.1,
            'support_fraction_floor': 1.0,
            'entry_coverage_floor': 1.0,
            'certified_tail_qs': [13, 21],
            'supporting_entry_count': 2,
        }),
    )

    cert = sc.build_golden_adaptive_support_core_neighborhood_certificate(
        baseline_tail_coherence_certificate=baseline,
        refinement_radius_factors=(),
    ).to_dict()
    assert cert['selected_coherence']['theorem_status'] == 'golden-adaptive-tail-coherence-strong'



def test_tail_aware_reuses_supplied_baseline_and_support_core(monkeypatch) -> None:
    import kam_theorem_suite.adaptive_tail_aware_neighborhood as ta

    baseline = {
        'theorem_status': 'golden-adaptive-tail-coherence-strong',
        'entries': [],
        'support_profile': [],
        'coherence_tail_qs': [13, 21],
    }
    support_core = {
        'theorem_status': 'golden-adaptive-support-core-neighborhood-strong',
        'selected_bridge': {
            'certified_tail_qs': [13, 21],
            'support_fraction_floor': 1.0,
            'supporting_entry_count': 2,
        },
        'selected_center': 0.971635406,
        'selected_atlas_shift_grid': [-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4],
    }
    monkeypatch.setattr(
        ta,
        'build_golden_adaptive_tail_coherence_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('baseline coherence should be reused')),
    )
    monkeypatch.setattr(
        ta,
        'build_golden_adaptive_support_core_neighborhood_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('support core should be reused')),
    )
    monkeypatch.setattr(
        ta,
        '_build_golden_incompatibility_strict_bridge_from_coherence_payload',
        lambda *args, **kwargs: _dummy_obj({
            'theorem_status': 'golden-incompatibility-theorem-bridge-strong',
            'bridge_margin': 0.1,
            'support_fraction_floor': 1.0,
            'entry_coverage_floor': 1.0,
            'certified_tail_qs': [13, 21],
            'supporting_entry_count': 2,
            'certified_tail_is_suffix': True,
        }),
    )

    cert = ta.build_golden_adaptive_tail_aware_neighborhood_certificate(
        baseline_tail_coherence_certificate=baseline,
        support_core_neighborhood_certificate=support_core,
    ).to_dict()
    assert cert['selected_coherence']['theorem_status'] == 'golden-adaptive-tail-coherence-strong'



def test_program_driver_reuses_supplied_theorem_iv_upper_certificates(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    lower = {'theorem_status': 'golden-lower-neighborhood-stability-strong'}
    upper_bridge = {'theorem_status': 'golden-incompatibility-theorem-bridge-strong'}
    support_core = {'theorem_status': 'golden-adaptive-support-core-neighborhood-strong'}
    tail_aware = {'theorem_status': 'golden-adaptive-tail-aware-neighborhood-strong'}
    tail_stability = {'theorem_status': 'golden-adaptive-tail-stability-strong'}
    bridge_profile = {'theorem_status': 'golden-incompatibility-bridge-profile-strong'}
    tail_coherence = {'theorem_status': 'golden-adaptive-tail-coherence-strong'}

    monkeypatch.setattr(pd, 'build_golden_theorem_i_ii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-i-ii-workstream-papergrade-final', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_iii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-iii-final-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_iv_lower_neighborhood_report', lambda **kwargs: (_ for _ in ()).throw(AssertionError('lower should be reused')))

    def _iv(**kwargs):
        assert kwargs['lower_neighborhood_stability_certificate'] is lower
        assert kwargs['upper_tail_coherence_certificate'] is tail_coherence
        assert kwargs['upper_bridge_certificate'] is upper_bridge
        assert kwargs['upper_support_core_neighborhood_certificate'] is support_core
        assert kwargs['upper_tail_aware_neighborhood_certificate'] is tail_aware
        assert kwargs['upper_tail_stability_certificate'] is tail_stability
        assert kwargs['upper_bridge_profile_certificate'] is bridge_profile
        return {'theorem_status': 'golden-theorem-iv-final-strong', 'active_assumptions': []}

    monkeypatch.setattr(pd, 'build_golden_theorem_iv_report', _iv)
    monkeypatch.setattr(pd, 'build_golden_theorem_v_report', lambda **kwargs: {'theorem_status': 'golden-theorem-v-final-strong', 'active_assumptions': []})
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

    report = build_golden_theorem_program_discharge_status_report(
        base_K_values=[0.2, 0.25],
        theorem_iv_lower_neighborhood_certificate=lower,
        theorem_iv_upper_tail_coherence_certificate=tail_coherence,
        theorem_iv_upper_bridge_certificate=upper_bridge,
        theorem_iv_upper_bridge_promotion_certificate=upper_bridge,
        theorem_iv_upper_support_core_neighborhood_certificate=support_core,
        theorem_iv_upper_tail_aware_neighborhood_certificate=tail_aware,
        theorem_iv_upper_tail_stability_certificate=tail_stability,
        theorem_iv_upper_bridge_profile_certificate=bridge_profile,
    )
    assert report['subreports']['theorem_iv_lower_neighborhood'] == lower
