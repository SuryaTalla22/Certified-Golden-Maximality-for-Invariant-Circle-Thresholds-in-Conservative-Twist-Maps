from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_golden_theorem_vi_envelope_lift_report,
    build_golden_theorem_vi_report,
)
from kam_theorem_suite.theorem_vi_envelope_lift import (
    build_golden_theorem_vi_envelope_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload
    def to_dict(self):
        return dict(self._payload)


def test_theorem_vi_front_complete_when_identification_and_eta_fronts_are_closed(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['validated_true_renormalization_fixed_point_package'],
    }))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'eta-threshold-comparison-strong',
        'theorem_flags': {'golden_endpoint_anchor': True},
        'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
    }))
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {
            'eta_threshold_anchor_available': True,
            'anchor_well_defined': True,
            'anchor_gap_against_panel_positive': True,
        },
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 0.01},
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {
            'golden_anchor_available': True,
            'challenger_records_available': True,
            'all_threshold_bounded_challengers_dominated': True,
            'no_undecided_challengers': True,
            'panel_gap_positive': True,
        },
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 0.01},
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-lift-front-complete'
    assert cert['statement_mode'] == 'unresolved'
    assert cert['open_hypotheses'] == []
    assert cert['upstream_active_assumptions'] == ['validated_true_renormalization_fixed_point_package']
    assert 'one_variable_eta_envelope_law' in cert['local_active_assumptions']



def test_theorem_vi_one_variable_conditional_strong_when_assumptions_are_toggled_on(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'eta-threshold-comparison-strong',
        'theorem_flags': {'golden_endpoint_anchor': True},
        'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
    }))
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {
            'eta_threshold_anchor_available': True,
            'anchor_well_defined': True,
            'anchor_gap_against_panel_positive': True,
        },
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 0.02},
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {
            'golden_anchor_available': True,
            'challenger_records_available': True,
            'all_threshold_bounded_challengers_dominated': True,
            'no_undecided_challengers': True,
            'panel_gap_positive': True,
        },
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 0.02},
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=[0.3],
        assume_one_variable_eta_envelope_law=True,
        assume_strict_golden_top_gap_theorem=True,
        assume_challenger_exhaustion_beyond_current_panel=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong'
    assert cert['statement_mode'] == 'one-variable'
    assert cert['active_assumptions'] == []



def test_theorem_vi_two_variable_conditional_strong_when_corrected_statement_is_toggled_on(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'eta-threshold-comparison-strong',
        'theorem_flags': {'golden_endpoint_anchor': True},
        'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
    }))
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {
            'eta_threshold_anchor_available': True,
            'anchor_well_defined': True,
            'anchor_gap_against_panel_positive': True,
        },
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 0.015},
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {
            'golden_anchor_available': True,
            'challenger_records_available': True,
            'all_threshold_bounded_challengers_dominated': True,
            'no_undecided_challengers': True,
            'panel_gap_positive': True,
        },
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 0.015},
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=[0.3],
        assume_corrected_two_variable_envelope_law=True,
        assume_renormalization_covariate_control_on_class=True,
        assume_strict_golden_top_gap_theorem=True,
        assume_challenger_exhaustion_beyond_current_panel=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-lift-conditional-two-variable-strong'
    assert cert['statement_mode'] == 'two-variable'
    assert cert['active_assumptions'] == []



def test_theorem_vi_stays_partial_when_front_is_not_closed(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-conditional-partial',
        'open_hypotheses': ['theorem_iv_front_complete'],
        'active_assumptions': ['validated_true_renormalization_fixed_point_package'],
    }))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'eta-threshold-comparison-moderate',
        'theorem_flags': {'golden_endpoint_anchor': False},
        'eta_relation': {'eta_gap_to_golden_endpoint': 1.0e-4},
    }))
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-moderate',
        'theorem_flags': {
            'eta_threshold_anchor_available': True,
            'anchor_well_defined': True,
            'anchor_gap_against_panel_positive': False,
        },
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': -0.002},
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-moderate',
        'theorem_flags': {
            'golden_anchor_available': True,
            'challenger_records_available': True,
            'all_threshold_bounded_challengers_dominated': False,
            'no_undecided_challengers': False,
            'panel_gap_positive': False,
        },
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': -0.002},
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=[0.3],
        assume_one_variable_eta_envelope_law=True,
        assume_strict_golden_top_gap_theorem=True,
        assume_challenger_exhaustion_beyond_current_panel=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-lift-conditional-partial'
    assert 'threshold_identification_front_complete' in cert['open_hypotheses']
    assert 'threshold_bounded_near_top_challengers_dominated' in cert['open_hypotheses']
    assert 'no_undecided_near_top_challengers' in cert['open_hypotheses']



def test_driver_exposes_theorem_vi_envelope_reports(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(pd, 'build_golden_theorem_vi_envelope_lift_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'active_assumptions': ['one_variable_eta_envelope_law'],
    }))
    monkeypatch.setattr(pd, 'build_golden_theorem_vi_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'active_assumptions': [],
    }))

    lift_report = build_golden_theorem_vi_envelope_lift_report(base_K_values=[0.3])
    theorem_report = build_golden_theorem_vi_report(base_K_values=[0.3])
    assert lift_report['theorem_status'] == 'golden-theorem-vi-envelope-lift-front-complete'
    assert theorem_report['theorem_status'] == 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong'


def test_theorem_vi_lift_surfaces_local_gap_certificate_and_residual_global_burden(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['validated_true_renormalization_fixed_point_package'],
    }))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'eta-threshold-comparison-strong',
        'theorem_flags': {'golden_endpoint_anchor': True},
        'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
    }))
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {
            'eta_threshold_anchor_available': True,
            'anchor_well_defined': True,
            'anchor_gap_against_panel_positive': True,
        },
        'proto_envelope_relation': {
            'anchor_lower_minus_panel_nongolden_upper': 0.02,
            'panel_nongolden_max_upper_bound': 0.97106,
        },
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {
            'golden_anchor_available': True,
            'challenger_records_available': True,
            'all_threshold_bounded_challengers_dominated': True,
            'no_undecided_challengers': True,
            'panel_gap_positive': True,
        },
        'near_top_relation': {
            'golden_lower_minus_most_dangerous_upper': 0.02,
            'most_dangerous_threshold_upper': 0.97106,
        },
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['current_local_top_gap_certificate']['status'] == 'current-local-top-gap-strong'
    assert cert['residual_burden_summary']['status'] == 'global-theorem-burden-only'
    assert cert['statement_mode_diagnostics']['candidate_mode'] == 'unresolved'
    assert 'settle whether Theorem VI is genuinely one-variable' in cert['statement_mode_diagnostics']['residual_statement_mode_burden']


def test_theorem_vi_locks_one_variable_mode_from_finite_statement_mode_certificates(monkeypatch) -> None:
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
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['statement_mode'] == 'one-variable'
    assert cert['statement_mode_diagnostics']['mode_lock_status'] == 'one-variable-supported'
    assert 'corrected_two_variable_envelope_law' not in cert['local_active_assumptions']


def test_theorem_vi_locks_two_variable_mode_from_finite_statement_mode_certificates(monkeypatch) -> None:
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
    two_variable_mode = {'candidate_mode': 'two-variable', 'mode_lock_status': 'two-variable-supported', 'status': 'statement-mode-certificate-two-variable-supported', 'evidence_margin': 2.0e-4}
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {'eta_threshold_anchor_available': True, 'anchor_well_defined': True, 'anchor_gap_against_panel_positive': True},
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 0.02},
        'statement_mode_certificate': two_variable_mode,
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {'golden_anchor_available': True, 'challenger_records_available': True, 'all_threshold_bounded_challengers_dominated': True, 'no_undecided_challengers': True, 'panel_gap_positive': True},
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 0.02},
        'statement_mode_certificate': two_variable_mode,
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['statement_mode'] == 'two-variable'
    assert cert['statement_mode_diagnostics']['mode_lock_status'] == 'two-variable-supported'
    assert 'one_variable_eta_envelope_law' not in cert['local_active_assumptions']



def test_locked_statement_mode_promotes_strict_top_gap_beyond_raw_gap(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    locked_cert = {
        'candidate_mode': 'one-variable',
        'mode_lock_status': 'one-variable-supported',
        'status': 'statement-mode-certificate-one-variable-supported',
        'evidence_margin': 2.5e-3,
    }

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'golden-threshold-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    }))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'eta-threshold-comparison-strong',
        'theorem_flags': {'golden_endpoint_anchor': True},
        'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
    }))
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {
            'eta_threshold_anchor_available': True,
            'anchor_well_defined': True,
            'anchor_gap_against_panel_positive': True,
        },
        'statement_mode_certificate': dict(locked_cert),
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 0.018},
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {
            'golden_anchor_available': True,
            'challenger_records_available': True,
            'all_threshold_bounded_challengers_dominated': True,
            'no_undecided_challengers': True,
            'panel_gap_positive': True,
        },
        'statement_mode_certificate': dict(locked_cert),
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 0.018},
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(base_K_values=[0.3]).to_dict()
    assert cert['statement_mode'] == 'one-variable'
    assert cert['strict_golden_top_gap_certificate']['screened_panel_strict_top_gap_status'] == 'strict-golden-top-gap-screened-panel-strong'
    assert cert['strict_golden_top_gap_certificate']['local_top_gap_promoted_beyond_raw_gap'] is True
    assert 'strict_golden_top_gap_theorem' not in cert['local_active_assumptions']
    assert 'challenger_exhaustion_beyond_current_panel' in cert['local_active_assumptions']


def test_theorem_vi_reuses_nested_threshold_bridge_from_identification_certificate(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    captured: dict[str, object] = {}

    def _eta_builder(**kwargs):
        captured['eta_kwargs'] = dict(kwargs)
        return _Dummy({
            'theorem_status': 'eta-threshold-comparison-strong',
            'theorem_flags': {'golden_endpoint_anchor': True},
            'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
            'local_envelope_anchor': {'threshold_lower': 0.97109, 'threshold_upper': 0.97111, 'eta_center': 0.3819},
        })

    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', _eta_builder)
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {
            'eta_threshold_anchor_available': True,
            'anchor_well_defined': True,
            'anchor_gap_against_panel_positive': True,
        },
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 0.02},
    }))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {
            'golden_anchor_available': True,
            'challenger_records_available': True,
            'all_threshold_bounded_challengers_dominated': True,
            'no_undecided_challengers': True,
            'panel_gap_positive': True,
        },
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 0.02},
    }))

    cert = build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=[0.3],
        threshold_identification_certificate={
            'theorem_status': 'golden-threshold-identification-theorem-front-complete',
            'open_hypotheses': [],
            'active_assumptions': [],
            'transport_discharge_shell': {
                'threshold_identification_discharge_shell': {
                    'identification_shell': {
                        'threshold_compatibility_bridge': {
                            'theorem_status': 'validated-threshold-compatibility-bridge-strong',
                            'validated_window': [0.97109, 0.97111],
                            'certified_center': 0.97110,
                            'certified_radius': 1.0e-05,
                        },
                    },
                },
            },
        },
    ).to_dict()

    eta_kwargs = captured['eta_kwargs']
    assert isinstance(eta_kwargs, dict)
    assert eta_kwargs['threshold_bridge_certificate']['theorem_status'] == 'validated-threshold-compatibility-bridge-strong'
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-lift-front-complete'


def test_theorem_vi_reuses_nested_eta_proto_and_near_top_when_available() -> None:
    cert = build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=[0.3],
        threshold_identification_certificate={
            'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-front-complete',
            'open_hypotheses': [],
            'active_assumptions': [],
            'eta_threshold_anchor': {
                'theorem_status': 'eta-threshold-comparison-strong',
                'theorem_flags': {'golden_endpoint_anchor': True},
                'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
                'local_envelope_anchor': {'threshold_lower': 0.97109, 'threshold_upper': 0.97111, 'eta_center': 0.3819},
            },
            'proto_envelope_bridge': {
                'theorem_status': 'proto-envelope-eta-bridge-strong',
                'theorem_flags': {
                    'eta_threshold_anchor_available': True,
                    'anchor_well_defined': True,
                    'anchor_gap_against_panel_positive': True,
                },
                'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 0.02},
            },
            'near_top_challenger_surface': {
                'theorem_status': 'near-top-eta-challenger-comparison-strong',
                'theorem_flags': {
                    'golden_anchor_available': True,
                    'challenger_records_available': True,
                    'all_threshold_bounded_challengers_dominated': True,
                    'no_undecided_challengers': True,
                    'panel_gap_positive': True,
                },
                'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 0.02},
            },
        },
    ).to_dict()

    assert cert['eta_threshold_anchor']['theorem_status'] == 'eta-threshold-comparison-strong'
    assert cert['proto_envelope_bridge']['theorem_status'] == 'proto-envelope-eta-bridge-strong'
    assert cert['near_top_challenger_surface']['theorem_status'] == 'near-top-eta-challenger-comparison-strong'
