from __future__ import annotations

from kam_theorem_suite.envelope import (
    build_eta_global_envelope_certificate,
    build_eta_mode_obstruction_certificate,
    build_eta_mode_reduction_certificate,
    build_strict_golden_top_gap_theorem_candidate,
)
from kam_theorem_suite.theorem_vi_envelope_lift import build_golden_theorem_vi_envelope_lift_certificate
from kam_theorem_suite.theorem_vi_envelope_discharge import build_golden_theorem_vi_envelope_discharge_lift_certificate
from kam_theorem_suite import proof_driver


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage85_one_variable_reduction_can_be_theorem_certified() -> None:
    statement_mode_certificate = {
        'candidate_mode': 'one-variable',
        'mode_lock_status': 'one-variable-supported',
        'status': 'statement-mode-certificate-one-variable-supported',
        'evidence_margin': 1.5e-4,
    }
    obstruction = build_eta_mode_obstruction_certificate(statement_mode_certificate)
    reduction = build_eta_mode_reduction_certificate(
        statement_mode_certificate,
        mode_obstruction_certificate=obstruction,
        current_local_top_gap_status='current-local-top-gap-strong',
        anchor_globalization_certificate={
            'anchor_ready_for_global_envelope': True,
            'anchor_transport_locked': True,
            'anchor_identification_locked': True,
            'anchor_globalization_status': 'anchor-globalization-global-certified',
        },
        global_nongolden_ceiling_certificate={
            'global_ceiling_status': 'global-ceiling-strong',
            'global_gap_margin': 5.3e-4,
            'global_ceiling_theorem_certified': True,
        },
    )
    envelope = build_eta_global_envelope_certificate(
        golden_lower_witness=0.97163,
        nongolden_global_upper_ceiling=0.97110,
        mode_reduction_certificate=reduction,
        ceiling_decomposition={
            'global_ceiling_status': 'global-ceiling-strong',
            'global_gap_margin': 5.3e-4,
            'global_ceiling_theorem_certified': True,
        },
        theorem_mode='one-variable',
    )
    candidate = build_strict_golden_top_gap_theorem_candidate(envelope)

    assert reduction['theorem_mode'] == 'one-variable'
    assert reduction['reduction_certified'] is True
    assert reduction['theorem_mode_status'] == 'one-variable-reduction-certified-globalized'
    assert envelope['theorem_status'] == 'global-envelope-theorem-one-variable-certified'
    assert candidate['global_strict_top_gap_status'] == 'strict-golden-top-gap-theorem-one-variable-certified'


def test_stage85_lift_can_close_to_global_one_variable_strong(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'eta-threshold-comparison-strong',
        'theorem_flags': {
            'golden_endpoint_anchor': True,
            'threshold_bridge_available': True,
            'local_envelope_anchor_well_defined': True,
        },
        'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
        'local_envelope_anchor': {'threshold_lower': 0.97163, 'threshold_upper': 0.97165, 'eta_center': 0.4472},
    }))
    one_variable_mode = {'candidate_mode': 'one-variable', 'mode_lock_status': 'one-variable-supported', 'status': 'statement-mode-certificate-one-variable-supported', 'evidence_margin': 1.0e-4}
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {'eta_threshold_anchor_available': True, 'anchor_well_defined': True, 'anchor_gap_against_panel_positive': True},
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 0.02, 'panel_nongolden_max_upper_bound': 0.97110},
        'statement_mode_certificate': one_variable_mode,
        'anchor_globalization_certificate': {
            'anchor_ready_for_global_envelope': True,
            'anchor_transport_locked': True,
            'anchor_identification_locked': True,
            'anchor_globalization_status': 'anchor-globalization-global-certified',
        },
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {'golden_anchor_available': True, 'challenger_records_available': True, 'all_threshold_bounded_challengers_dominated': True, 'no_undecided_challengers': True, 'panel_gap_positive': True},
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 0.02, 'most_dangerous_threshold_upper': 0.97110},
        'statement_mode_certificate': one_variable_mode,
        'global_nongolden_ceiling_certificate': {
            'global_nongolden_upper_ceiling': 0.97110,
            'golden_lower_witness': 0.97163,
            'global_gap_margin': 5.3e-4,
            'global_ceiling_status': 'global-ceiling-strong',
            'global_ceiling_theorem_certified': True,
            'remaining_burden': 'none',
        },
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-lift-global-one-variable-strong'
    assert cert['statement_mode'] == 'one-variable'
    assert cert['active_assumptions'] == []
    assert cert['mode_reduction_certificate']['reduction_certified'] is True
    assert cert['strict_golden_top_gap_theorem_candidate']['global_strict_top_gap_certified'] is True


def test_stage85_discharge_and_driver_surface_global_closure(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_discharge as tved

    theorem_vi = {
        'theorem_status': 'golden-theorem-vi-envelope-lift-global-one-variable-strong',
        'statement_mode': 'one-variable',
        'statement_mode_diagnostics': {'candidate_mode': 'one-variable', 'mode_lock_status': 'one-variable-supported', 'theorem_statement_mode': 'one-variable', 'theorem_mode_certified': True},
        'mode_reduction_certificate': {'theorem_mode': 'one-variable', 'theorem_mode_status': 'one-variable-reduction-certified-globalized', 'reduction_certified': True},
        'mode_obstruction_certificate': {'one_variable_obstruction_certified': False},
        'near_top_challenger_surface': {'theorem_flags': {'all_threshold_bounded_challengers_dominated': True, 'no_undecided_challengers': True}, 'near_top_relation': {'most_dangerous_threshold_upper': 0.97110, 'golden_lower_minus_most_dangerous_upper': 5.3e-4}},
        'proto_envelope_bridge': {'proto_envelope_relation': {'panel_nongolden_max_upper_bound': 0.97110, 'anchor_lower_minus_panel_nongolden_upper': 5.3e-4}},
        'open_hypotheses': [],
        'local_active_assumptions': [],
        'assumptions': [],
        'global_nongolden_ceiling_certificate': {
            'global_nongolden_upper_ceiling': 0.97110,
            'golden_lower_witness': 0.97163,
            'global_gap_margin': 5.3e-4,
            'global_ceiling_status': 'global-ceiling-strong',
            'global_ceiling_theorem_certified': True,
            'remaining_burden': 'none',
        },
        'global_envelope_certificate': {
            'theorem_status': 'global-envelope-theorem-one-variable-certified',
        },
        'strict_golden_top_gap_theorem_candidate': {
            'global_strict_top_gap_status': 'strict-golden-top-gap-theorem-one-variable-certified',
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
    assert cert['residual_burden_summary']['status'] == 'theorem-vi-globally-discharged'

    summary = proof_driver._summarize_theorem_status_entry('theorem_vi', cert)
    assert summary['theorem_mode_certified'] is True
    assert summary['global_ceiling_certified'] is True
