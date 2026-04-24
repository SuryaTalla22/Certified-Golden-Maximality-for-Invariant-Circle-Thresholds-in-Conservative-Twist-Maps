from __future__ import annotations

from kam_theorem_suite.envelope import build_eta_mode_reduction_certificate
from kam_theorem_suite.theorem_vi_envelope_lift import (
    _build_strict_golden_top_gap_certificate,
    build_golden_theorem_vi_envelope_lift_certificate,
)
from kam_theorem_suite.theorem_vi_envelope_discharge import (
    _build_current_local_top_gap_certificate as build_discharge_local_gap_certificate,
    _build_strict_golden_top_gap_certificate as build_discharge_strict_gap_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage105_mode_reduction_certifies_one_variable_on_screened_panel() -> None:
    cert = {
        'candidate_mode': 'one-variable',
        'mode_lock_status': 'one-variable-supported',
        'status': 'statement-mode-certificate-one-variable-supported',
        'evidence_margin': 1.25e-4,
    }
    reduction = build_eta_mode_reduction_certificate(
        cert,
        current_local_top_gap_status='current-local-top-gap-screened-domination-positive',
        anchor_globalization_certificate={
            'anchor_ready_for_global_envelope': True,
            'anchor_transport_locked': True,
            'anchor_identification_locked': True,
            'anchor_globalization_status': 'anchor-globalization-global-certified',
        },
        global_nongolden_ceiling_certificate={
            'global_ceiling_status': 'global-ceiling-partial',
            'global_ceiling_theorem_certified': False,
            'global_gap_margin': None,
        },
    )
    assert reduction['theorem_mode'] == 'one-variable'
    assert reduction['reduction_certified'] is True
    assert reduction['theorem_mode_status'] == 'one-variable-reduction-certified-screened-panel'
    assert 'Theorem VII' in reduction['remaining_burden']



def test_stage105_strict_gap_promotes_screened_domination_without_numeric_gap() -> None:
    cert = _build_strict_golden_top_gap_certificate(
        statement_mode_diagnostics={
            'candidate_mode': 'one-variable',
            'theorem_statement_mode': 'one-variable',
            'theorem_mode_certified': True,
            'mode_lock_status': 'one-variable-supported',
        },
        current_local_top_gap_certificate={
            'top_gap_scale': None,
            'status': 'current-local-top-gap-screened-domination-positive',
            'local_geometry_supports_top_gap_promotion': True,
            'all_threshold_bounded_challengers_dominated': True,
            'no_undecided_near_top_challengers': True,
        },
        global_nongolden_ceiling_certificate={'global_ceiling_status': 'global-ceiling-partial'},
        global_envelope_certificate={'theorem_status': 'eta-global-envelope-front-complete'},
        strict_golden_top_gap_theorem_candidate={'global_strict_top_gap_certified': False},
    )
    assert cert['screened_panel_strict_top_gap_status'] == 'strict-golden-top-gap-screened-domination-certified'
    assert cert['screened_panel_strict_top_gap_certified'] is True
    assert cert['local_top_gap_promoted_beyond_raw_gap'] is True



def test_stage105_promotes_theorem_vi_to_screened_one_variable_strong(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    identification = {
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    }
    eta_anchor = {
        'theorem_status': 'eta-threshold-comparison-strong',
        'theorem_flags': {
            'threshold_bridge_available': True,
            'eta_interval_available': True,
            'eta_anchor_inside_arithmetic_domain': True,
            'local_envelope_anchor_well_defined': True,
            'positive_threshold_gap': True,
            'golden_endpoint_anchor': True,
        },
        'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
        'local_envelope_anchor': {
            'threshold_lower': 0.9713628519,
            'threshold_upper': 0.9713671753,
            'threshold_center': 0.9713650136,
            'eta_center': 0.4472135955,
        },
        'threshold_interval': [0.9713628519, 0.9713671753],
    }
    proto = {
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {
            'eta_threshold_anchor_available': True,
            'panel_available': True,
            'panel_gap_positive': False,
            'anchor_gap_against_panel_positive': False,
            'anchor_well_defined': True,
        },
        'proto_envelope_relation': {
            'anchor_lower_minus_panel_nongolden_upper': None,
            'panel_nongolden_max_upper_bound': None,
        },
        'statement_mode_certificate': {
            'candidate_mode': 'one-variable',
            'mode_lock_status': 'one-variable-supported',
            'status': 'statement-mode-certificate-one-variable-supported',
            'evidence_margin': 2.0e-4,
        },
        'anchor_globalization_certificate': {
            'anchor_ready_for_global_envelope': True,
            'anchor_transport_locked': True,
            'anchor_identification_locked': True,
            'anchor_globalization_status': 'anchor-globalization-global-certified',
        },
    }
    near_top = {
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {
            'golden_anchor_available': True,
            'challenger_records_available': True,
            'at_least_one_threshold_bounded_challenger': False,
            'all_threshold_bounded_challengers_dominated': True,
            'no_undecided_challengers': True,
            'panel_gap_positive': False,
        },
        'challenger_records': [
            {
                'label': 'silver',
                'threshold_upper_bound': None,
                'status': 'arithmetic-weaker-only',
                'provenance': {
                    'source': 'theorem-vi-screened-rational-panel',
                    'screening_status': 'edge-attained-exploratory-only',
                    'exploratory_threshold_upper_bound': 0.9738650136001021,
                    'exploratory_ceiling_attained_by': '12/5',
                    'residual_burden': 'exploratory-only',
                },
            },
        ],
        'panel_records': [],
        'near_top_relation': {
            'golden_lower_minus_most_dangerous_upper': None,
            'most_dangerous_threshold_upper': None,
        },
        'statement_mode_certificate': {
            'candidate_mode': 'one-variable',
            'mode_lock_status': 'one-variable-supported',
            'status': 'statement-mode-certificate-one-variable-supported',
            'evidence_margin': 2.0e-4,
        },
    }

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(identification))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy(eta_anchor))
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy(proto))
    monkeypatch.setattr(tvel, 'build_near_top_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy(near_top))

    cert = build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=[0.3],
        auto_build_screened_near_top_panel=False,
        challenger_specs=[],
    ).to_dict()

    assert cert['statement_mode'] == 'one-variable'
    assert cert['mode_reduction_certificate']['theorem_mode_status'] == 'one-variable-reduction-certified-screened-panel'
    assert cert['strict_golden_top_gap_certificate']['screened_panel_strict_top_gap_certified'] is True
    assert cert['theorem_status'] == 'golden-theorem-vi-envelope-lift-screened-one-variable-strong'
    assert cert['open_hypotheses'] == []
    assert cert['local_active_assumptions'] == ['challenger_exhaustion_beyond_current_panel']
    assert cert['residual_burden_summary']['theorem_vii_handoff_active'] is True
    assert cert['residual_burden_summary']['theorem_vii_handoff_labels'] == ['silver']



def test_stage105_discharge_promotes_inherited_screened_domination_gap() -> None:
    theorem_vi = {
        'current_local_top_gap_certificate': {
            'status': 'current-local-top-gap-screened-domination-positive',
        },
        'near_top_challenger_surface': {
            'theorem_flags': {
                'all_threshold_bounded_challengers_dominated': True,
                'no_undecided_challengers': True,
            }
        },
    }
    local_gap = build_discharge_local_gap_certificate(
        theorem_vi,
        current_top_gap_scale=None,
        current_most_dangerous_challenger_upper=None,
        discharged_identified_branch_witness_interval=[0.9713628519, 0.9713671753],
        discharged_identified_branch_witness_width=4.3234e-6,
        discharged_witness_width_vs_current_top_gap_margin=None,
        discharged_witness_lower_vs_current_near_top_challenger_upper_margin=None,
        discharged_witness_geometry_status='discharged-witness-geometry-unresolved',
    )
    assert local_gap['status'] == 'current-local-top-gap-screened-domination-positive'
    strict_gap = build_discharge_strict_gap_certificate(
        statement_mode_diagnostics={
            'candidate_mode': 'one-variable',
            'theorem_statement_mode': 'one-variable',
            'theorem_mode_certified': True,
            'mode_lock_status': 'one-variable-supported',
        },
        current_local_top_gap_certificate=local_gap,
        global_nongolden_ceiling_certificate={'global_ceiling_status': 'global-ceiling-partial'},
        global_envelope_certificate={'theorem_status': 'eta-global-envelope-front-complete'},
        global_strict_golden_top_gap_certificate={'global_strict_top_gap_certified': False},
    )
    assert strict_gap['screened_panel_strict_top_gap_status'] == 'strict-golden-top-gap-discharged-screened-domination-certified'
    assert strict_gap['screened_panel_strict_top_gap_certified'] is True
