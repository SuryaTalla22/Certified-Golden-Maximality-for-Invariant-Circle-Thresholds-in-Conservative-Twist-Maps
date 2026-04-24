from __future__ import annotations

from kam_theorem_suite.theorem_vi_envelope_lift import build_golden_theorem_vi_envelope_lift_certificate
from kam_theorem_suite.theorem_vi_envelope_discharge import build_golden_theorem_vi_envelope_discharge_lift_certificate
from kam_theorem_suite.theorem_vii_exhaustion_discharge import build_golden_theorem_vii_exhaustion_discharge_lift_certificate
from kam_theorem_suite import proof_driver


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage84_lift_exposes_theorem_mode_separately_from_diagnostic_mode(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'eta-threshold-comparison-strong',
        'theorem_flags': {'golden_endpoint_anchor': True},
        'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
    }))
    one_variable_mode = {'candidate_mode': 'one-variable', 'mode_lock_status': 'one-variable-supported', 'status': 'statement-mode-certificate-one-variable-supported', 'evidence_margin': 1.0e-4}
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {'eta_threshold_anchor_available': True, 'anchor_well_defined': True, 'anchor_gap_against_panel_positive': True},
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 0.02},
        'statement_mode_certificate': one_variable_mode,
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {'golden_anchor_available': True, 'challenger_records_available': True, 'all_threshold_bounded_challengers_dominated': True, 'no_undecided_challengers': True, 'panel_gap_positive': True},
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 0.02},
        'statement_mode_certificate': one_variable_mode,
        'global_nongolden_ceiling_certificate': {
            'global_nongolden_upper_ceiling': 0.9711,
            'golden_lower_witness': 0.97163,
            'global_gap_margin': 5.3e-4,
            'global_ceiling_status': 'global-ceiling-strong',
            'remaining_burden': 'none',
        },
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['statement_mode'] == 'one-variable'
    assert cert['statement_mode_diagnostics']['diagnostic_statement_mode'] == 'one-variable'
    assert cert['statement_mode_diagnostics']['theorem_statement_mode'] == 'unresolved'
    assert cert['mode_reduction_certificate']['theorem_mode_status'] == 'one-variable-diagnostic-support-only'
    assert cert['strict_golden_top_gap_theorem_candidate']['global_strict_top_gap_status'] == 'strict-golden-top-gap-globalization-incomplete'


def test_stage84_discharge_promotes_global_vi_status_when_global_gap_is_certified(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_discharge as tved

    theorem_vi = {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'statement_mode_diagnostics': {'candidate_mode': 'one-variable', 'mode_lock_status': 'assumption-forced-one-variable'},
        'mode_reduction_certificate': {'theorem_mode': 'one-variable', 'theorem_mode_status': 'assumption-forced-one-variable', 'reduction_certified': True},
        'mode_obstruction_certificate': {'one_variable_obstruction_certified': False},
        'near_top_challenger_surface': {'theorem_flags': {'all_threshold_bounded_challengers_dominated': True, 'no_undecided_challengers': True}, 'near_top_relation': {'most_dangerous_threshold_upper': 0.97110, 'golden_lower_minus_most_dangerous_upper': 5.3e-4}},
        'open_hypotheses': [],
        'local_active_assumptions': [],
        'assumptions': [],
        'global_nongolden_ceiling_certificate': {
            'global_nongolden_upper_ceiling': 0.97110,
            'golden_lower_witness': 0.97163,
            'global_gap_margin': 5.3e-4,
            'global_ceiling_status': 'global-ceiling-strong',
            'remaining_burden': 'none',
        },
        'global_envelope_certificate': {
            'theorem_status': 'global-envelope-candidate-one-variable-strong',
        },
        'strict_golden_top_gap_theorem_candidate': {
            'global_strict_top_gap_status': 'strict-golden-top-gap-global-one-variable-certified',
            'global_strict_top_gap_certified': True,
            'global_strict_top_gap_margin': 5.3e-4,
        },
    }
    discharge = {
        'theorem_status': 'golden-theorem-ii-to-v-identification-transport-discharge-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'discharged_bridge_native_tail_witness_interval': [0.9715, 0.97155],
        'discharged_bridge_native_tail_witness_width': 5.0e-5,
        'bridge_native_tail_witness_source': 'fixture',
        'bridge_native_tail_witness_status': 'transport-locked-strong',
    }
    monkeypatch.setattr(tved, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy(theorem_vi))
    monkeypatch.setattr(tved, 'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate', lambda **kwargs: _Dummy(discharge))

    cert = build_golden_theorem_vi_envelope_discharge_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-discharge-lift-global-one-variable-strong'
    assert cert['strict_golden_top_gap_certificate']['global_strict_top_gap_certified'] is True


def test_stage84_vii_prefers_vi_global_ceiling_summary(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vii_exhaustion_discharge as tviid

    theorem_vii = {
        'family_label': 'standard-sine',
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete',
        'open_hypotheses': [],
        'local_active_assumptions': [],
        'assumptions': [],
        'reference_lower_bound': 0.97163,
    }
    vi_discharge = {
        'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-global-one-variable-strong',
        'active_assumptions': [],
        'global_nongolden_ceiling_certificate': {
            'global_nongolden_upper_ceiling': 0.97110,
            'global_gap_margin': 5.3e-4,
            'global_ceiling_status': 'global-ceiling-strong',
        },
    }
    monkeypatch.setattr(tviid, 'build_golden_theorem_vii_certificate', lambda **kwargs: _Dummy(theorem_vii))
    monkeypatch.setattr(tviid, 'build_golden_theorem_vi_discharge_certificate', lambda **kwargs: _Dummy(vi_discharge))
    monkeypatch.setattr(tviid, 'build_golden_theorem_vii_global_completeness_certificate', lambda prelim: _Dummy({'residual_burden_summary': prelim['residual_burden_summary']}))

    cert = build_golden_theorem_vii_exhaustion_discharge_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['current_near_top_exhaustion_source'] == 'theorem_vi_discharge.global_nongolden_ceiling_certificate'
    assert cert['current_near_top_exhaustion_status'] == 'global-ceiling-strong'


def test_stage84_proof_driver_surfaces_global_vi_fields(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {'theorem_status': 'golden-theorem-v-transport-lift-front-complete', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {'theorem_status': 'golden-theorem-ii-to-v-identification-lift-front-complete', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'statement_mode': 'one-variable',
        'statement_mode_diagnostics': {'mode_lock_status': 'one-variable-supported', 'theorem_statement_mode': 'unresolved'},
        'strict_golden_top_gap_certificate': {'global_strict_top_gap_status': 'strict-golden-top-gap-globalization-incomplete'},
        'open_hypotheses': [],
        'active_assumptions': [],
        'residual_burden_summary': {'status': 'global-theorem-burden-only', 'global_ceiling_status': 'global-ceiling-strong'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-viii-reduction-lift-front-complete', 'statement_mode': 'one-variable', 'open_hypotheses': [], 'active_assumptions': []})

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['theorem_status_summary']['theorem_vi']['global_ceiling_status'] == 'global-ceiling-strong'
    assert report['theorem_status_summary']['theorem_vi']['global_top_gap_status'] == 'strict-golden-top-gap-globalization-incomplete'
