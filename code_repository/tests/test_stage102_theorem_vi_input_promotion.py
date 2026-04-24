from __future__ import annotations

from kam_theorem_suite.theorem_vi_envelope_lift import build_golden_theorem_vi_envelope_lift_certificate


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage102_refreshes_stale_eta_anchor_and_promotes_campaign_near_top(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    captured = {}

    identification = {
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
        'threshold_compatibility_bridge': {
            'theorem_status': 'validated-threshold-compatibility-bridge-strong',
            'validated_window': [0.97163, 0.97165],
            'certified_center': 0.97164,
            'certified_radius': 1.0e-5,
        },
        'eta_threshold_anchor': {
            'theorem_status': 'eta-threshold-comparison-moderate',
            'theorem_flags': {
                'threshold_bridge_available': True,
                'eta_interval_available': True,
                'local_envelope_anchor_well_defined': True,
                'positive_threshold_gap': True,
                'golden_endpoint_anchor': False,
            },
        },
        'proto_envelope_bridge': {
            'theorem_status': 'proto-envelope-eta-bridge-weak',
            'theorem_flags': {'panel_available': False, 'anchor_well_defined': True},
            'proto_envelope_relation': {'panel_nongolden_max_upper_bound': None},
        },
        'near_top_challenger_surface': {
            'theorem_status': 'near-top-eta-challenger-comparison-seed-only',
            'theorem_flags': {
                'golden_anchor_available': True,
                'challenger_records_available': False,
                'at_least_one_threshold_bounded_challenger': False,
            },
        },
    }

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(identification))

    def fake_eta(**kwargs):
        captured['eta_kwargs'] = dict(kwargs)
        return _Dummy({
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
                'threshold_lower': 0.97163,
                'threshold_upper': 0.97165,
                'threshold_center': 0.97164,
                'eta_center': 0.4472135955,
            },
            'threshold_interval': [0.97163, 0.97165],
        })

    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', fake_eta)

    monkeypatch.setattr(tvel, 'build_multi_class_campaign', lambda *args, **kwargs: _Dummy({
        'reference_label': 'golden',
        'reference_lower_bound': 0.97163,
        'class_campaigns': [{'class_label': 'silver'}],
        'dominated_classes': ['silver'],
        'overlapping_classes': [],
        'undecided_classes': [],
    }))

    monkeypatch.setattr(tvel, 'build_campaign_driven_eta_challenger_comparison_certificate', lambda *args, **kwargs: _Dummy({
        'near_top_certificate': {
            'theorem_status': 'near-top-eta-challenger-comparison-strong',
            'theorem_flags': {
                'golden_anchor_available': True,
                'challenger_records_available': True,
                'at_least_one_threshold_bounded_challenger': True,
                'all_threshold_bounded_challengers_dominated': True,
                'no_undecided_challengers': True,
                'panel_gap_positive': True,
            },
            'challenger_records': [{'label': 'silver', 'threshold_upper_bound': 0.97110}],
            'panel_records': [
                {'label': 'golden-anchor', 'eta_approx': 0.4472135955, 'threshold_lo': 0.97163, 'threshold_hi': 0.97165, 'is_golden': True},
                {'label': 'silver', 'eta_approx': 0.3535533906, 'threshold_lo': 0.97100, 'threshold_hi': 0.97110, 'is_golden': False},
            ],
            'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 5.3e-4, 'most_dangerous_threshold_upper': 0.97110},
            'global_nongolden_ceiling_certificate': {
                'global_nongolden_upper_ceiling': 0.97110,
                'golden_lower_witness': 0.97163,
                'global_gap_margin': 5.3e-4,
                'global_ceiling_status': 'global-ceiling-strong',
                'global_ceiling_theorem_certified': True,
            },
            'statement_mode_certificate': {
                'candidate_mode': 'one-variable',
                'mode_lock_status': 'one-variable-supported',
                'status': 'statement-mode-certificate-one-variable-supported',
                'evidence_margin': 5.3e-4,
            },
        }
    }))

    def fake_proto(**kwargs):
        captured['proto_kwargs'] = dict(kwargs)
        return _Dummy({
            'theorem_status': 'proto-envelope-eta-bridge-strong',
            'theorem_flags': {
                'eta_threshold_anchor_available': True,
                'panel_available': True,
                'panel_gap_positive': True,
                'anchor_gap_against_panel_positive': True,
                'anchor_well_defined': True,
            },
            'proto_envelope_relation': {
                'anchor_lower_minus_panel_nongolden_upper': 5.3e-4,
                'panel_nongolden_max_upper_bound': 0.97110,
            },
            'statement_mode_certificate': {
                'candidate_mode': 'one-variable',
                'mode_lock_status': 'one-variable-supported',
                'status': 'statement-mode-certificate-one-variable-supported',
                'evidence_margin': 5.3e-4,
            },
            'anchor_globalization_certificate': {
                'anchor_ready_for_global_envelope': True,
                'anchor_transport_locked': True,
                'anchor_identification_locked': True,
                'anchor_globalization_status': 'anchor-globalization-global-certified',
            },
        })

    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', fake_proto)

    cert = build_golden_theorem_vi_envelope_lift_certificate(base_K_values=[0.3], auto_build_screened_near_top_panel=False, challenger_campaign_report={'seed': 'fixture'}).to_dict()
    assert cert['eta_threshold_anchor']['theorem_status'] == 'eta-threshold-comparison-strong'
    assert cert['near_top_challenger_surface']['theorem_status'] == 'near-top-eta-challenger-comparison-strong'
    assert cert['theorem_status'] in {
        'golden-theorem-vi-envelope-lift-front-complete',
        'golden-theorem-vi-envelope-lift-global-one-variable-strong',
    }
    assert captured['eta_kwargs']['threshold_bridge_certificate']['theorem_status'] == 'validated-threshold-compatibility-bridge-strong'
    assert len(captured['proto_kwargs']['panel_records']) == 2


def test_stage102_keeps_explicit_near_top_certificate_when_already_strong(monkeypatch) -> None:
    import kam_theorem_suite.theorem_vi_envelope_lift as tvel

    identification = {
        'theorem_status': 'golden-threshold-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    }
    near_top = {
        'theorem_status': 'near-top-eta-challenger-comparison-strong',
        'theorem_flags': {
            'golden_anchor_available': True,
            'challenger_records_available': True,
            'at_least_one_threshold_bounded_challenger': True,
            'all_threshold_bounded_challengers_dominated': True,
            'no_undecided_challengers': True,
            'panel_gap_positive': True,
        },
        'challenger_records': [{'label': 'silver', 'threshold_upper_bound': 0.97110}],
        'panel_records': [{'label': 'silver', 'eta_approx': 0.35, 'threshold_lo': 0.9710, 'threshold_hi': 0.9711, 'is_golden': False}],
        'near_top_relation': {'golden_lower_minus_most_dangerous_upper': 5.3e-4, 'most_dangerous_threshold_upper': 0.97110},
        'global_nongolden_ceiling_certificate': {'global_ceiling_status': 'global-ceiling-strong', 'global_gap_margin': 5.3e-4, 'global_ceiling_theorem_certified': True, 'golden_lower_witness': 0.97163, 'global_nongolden_upper_ceiling': 0.97110},
        'statement_mode_certificate': {'candidate_mode': 'one-variable', 'mode_lock_status': 'one-variable-supported', 'status': 'statement-mode-certificate-one-variable-supported', 'evidence_margin': 5.3e-4},
    }
    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(identification))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'eta-threshold-comparison-strong',
        'theorem_flags': {'threshold_bridge_available': True, 'eta_interval_available': True, 'eta_anchor_inside_arithmetic_domain': True, 'local_envelope_anchor_well_defined': True, 'positive_threshold_gap': True, 'golden_endpoint_anchor': True},
        'eta_relation': {'eta_gap_to_golden_endpoint': 0.0},
        'local_envelope_anchor': {'threshold_lower': 0.97163, 'threshold_upper': 0.97165, 'threshold_center': 0.97164, 'eta_center': 0.4472135955},
        'threshold_interval': [0.97163, 0.97165],
    }))
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy({
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {'eta_threshold_anchor_available': True, 'panel_available': True, 'panel_gap_positive': True, 'anchor_gap_against_panel_positive': True, 'anchor_well_defined': True},
        'proto_envelope_relation': {'anchor_lower_minus_panel_nongolden_upper': 5.3e-4, 'panel_nongolden_max_upper_bound': 0.97110},
        'statement_mode_certificate': {'candidate_mode': 'one-variable', 'mode_lock_status': 'one-variable-supported', 'status': 'statement-mode-certificate-one-variable-supported', 'evidence_margin': 5.3e-4},
        'anchor_globalization_certificate': {'anchor_ready_for_global_envelope': True, 'anchor_transport_locked': True, 'anchor_identification_locked': True, 'anchor_globalization_status': 'anchor-globalization-global-certified'},
    }))

    calls = {'campaign': 0}
    monkeypatch.setattr(tvel, 'build_campaign_driven_eta_challenger_comparison_certificate', lambda *args, **kwargs: calls.__setitem__('campaign', calls['campaign'] + 1))

    cert = build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=[0.3],
        near_top_certificate=near_top,
    ).to_dict()
    assert cert['near_top_challenger_surface']['theorem_status'] == 'near-top-eta-challenger-comparison-strong'
    assert calls['campaign'] == 0
