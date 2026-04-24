
from __future__ import annotations

from kam_theorem_suite.nonexistence_front import build_golden_nonexistence_front_certificate
from kam_theorem_suite.proof_driver import build_golden_theorem_program_discharge_status_report


def test_nonexistence_front_reuses_supplied_lower_certificate(monkeypatch) -> None:
    import kam_theorem_suite.nonexistence_front as nf

    supplied = {
        'theorem_status': 'golden-lower-neighborhood-stability-strong',
        'stable_lower_bound': 0.3,
        'stable_window_hi': 0.4,
        'stable_window_width': 0.1,
        'clustered_entry_indices': [0, 1],
        'entries': [],
    }

    monkeypatch.setattr(
        nf,
        'build_golden_lower_neighborhood_stability_certificate',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('lower certificate should be reused')),
    )
    monkeypatch.setattr(
        nf,
        'build_golden_incompatibility_theorem_bridge_certificate',
        lambda **kwargs: type('D', (), {'to_dict': lambda self: {
            'theorem_status': 'golden-incompatibility-theorem-bridge-strong',
            'certified_upper_lo': 0.5,
            'certified_upper_hi': 0.6,
            'tail_member_count': 2,
            'positive_window_separation': True,
            'support_geometry_certified': True,
            'tail_coherence_certified': True,
            'tail_stability_certified': True,
            'supercritical_obstruction_locked': True,
            'strict_bridge_certified': True,
            'residual_burden': [],
        }})(),
    )

    cert = build_golden_nonexistence_front_certificate(
        base_K_values=[0.3],
        lower_neighborhood_stability_certificate=supplied,
    ).to_dict()
    assert cert['lower_side']['theorem_status'] == 'golden-lower-neighborhood-stability-strong'


def test_program_driver_reuses_supplied_theorem_iv_lower_certificate(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    supplied = {'theorem_status': 'golden-lower-neighborhood-stability-strong'}
    monkeypatch.setattr(pd, 'build_golden_theorem_i_ii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-i-ii-workstream-papergrade-final', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_iii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-iii-final-strong', 'active_assumptions': []})
    monkeypatch.setattr(pd, 'build_golden_theorem_iv_lower_neighborhood_report', lambda **kwargs: (_ for _ in ()).throw(AssertionError('driver should reuse supplied theorem_iv lower certificate')))

    def _iv(**kwargs):
        assert kwargs['lower_neighborhood_stability_certificate'] is supplied
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
        theorem_iv_lower_neighborhood_certificate=supplied,
    )
    assert report['subreports']['theorem_iv_lower_neighborhood'] == supplied
