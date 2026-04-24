from __future__ import annotations

from kam_theorem_suite.theorem_vi_envelope_lift import (
    _build_screened_near_top_dominance_certificate,
    _choose_vi_screened_threshold_bound,
    build_golden_theorem_vi_envelope_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage103_prefers_trusted_interior_window_over_edge_attained_candidate() -> None:
    lo, hi, report = _choose_vi_screened_threshold_bound(
        [
            {
                'label': 'silver 12/5',
                'q': 5,
                'K_lo': 0.9738650132533114,
                'K_hi': 0.9738650136001021,
                'width': 3.4e-10,
                'edge_attained': True,
                'trust_status': 'edge-attained-window',
            },
            {
                'label': 'bronze 8/3',
                'q': 3,
                'K_lo': 0.9688650136001022,
                'K_hi': 0.9688650139468930,
                'width': 3.4e-10,
                'edge_attained': False,
                'trust_status': 'trusted-interior-window',
            },
        ]
    )
    assert lo == 0.9688650136001022
    assert hi == 0.9688650139468930
    assert report['trusted_threshold_bound'] is True
    assert report['selected_label'] == 'bronze 8/3'
    assert report['exploratory_threshold_upper_bound'] == 0.9738650136001021


def test_stage103_dominance_certificate_tracks_deferred_exploratory_classes() -> None:
    cert = _build_screened_near_top_dominance_certificate(
        {
            'challenger_records': [
                {
                    'label': 'bronze',
                    'threshold_upper_bound': 0.9688650139468930,
                    'status': 'dominated-by-golden-threshold-anchor',
                    'provenance': {
                        'source': 'theorem-vi-screened-rational-panel',
                        'screening_status': 'trusted-threshold-upper-bound',
                    },
                },
                {
                    'label': 'silver',
                    'threshold_upper_bound': None,
                    'status': 'arithmetic-weaker-only',
                    'provenance': {
                        'source': 'theorem-vi-screened-rational-panel',
                        'screening_status': 'edge-attained-exploratory-only',
                        'exploratory_threshold_upper_bound': 0.9738650136001021,
                        'exploratory_ceiling_attained_by': 'silver 12/5',
                        'residual_burden': 'edge attained',
                    },
                },
            ],
            'near_top_relation': {
                'golden_lower_minus_most_dangerous_upper': 0.0024978379618663,
            },
        }
    )
    assert cert['status'] == 'screened-near-top-dominance-positive-gap'
    assert cert['local_dominance_certified_over_trusted_panel'] is True
    assert cert['trusted_ceiling_attained_by'] == 'bronze'
    assert cert['deferred_exploratory_records'][0]['label'] == 'silver'


def test_stage103_front_completes_vi_when_only_deferred_class_is_exploratory(monkeypatch) -> None:
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
            'threshold_lower': 0.9713628519087594,
            'threshold_upper': 0.9713671752914450,
            'threshold_center': 0.9713650136001022,
            'eta_center': 0.4472135955,
        },
        'threshold_interval': [0.9713628519087594, 0.9713671752914450],
    }
    proto = {
        'theorem_status': 'proto-envelope-eta-bridge-strong',
        'theorem_flags': {
            'eta_threshold_anchor_available': True,
            'panel_available': True,
            'panel_gap_positive': True,
            'anchor_gap_against_panel_positive': True,
            'anchor_well_defined': True,
        },
        'proto_envelope_relation': {
            'anchor_lower_minus_panel_nongolden_upper': 0.0024978379618663,
            'panel_nongolden_max_upper_bound': 0.9688650139468930,
        },
        'statement_mode_certificate': {
            'candidate_mode': 'one-variable',
            'mode_lock_status': 'one-variable-supported',
            'status': 'statement-mode-certificate-one-variable-supported',
            'evidence_margin': 8.6e-11,
        },
        'anchor_globalization_certificate': {
            'anchor_ready_for_global_envelope': False,
            'anchor_transport_locked': True,
            'anchor_identification_locked': True,
            'anchor_globalization_status': 'anchor-globalization-panel-overlap',
        },
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
        'challenger_records': [
            {
                'label': 'bronze',
                'threshold_upper_bound': 0.9688650139468930,
                'status': 'dominated-by-golden-threshold-anchor',
                'provenance': {'source': 'theorem-vi-screened-rational-panel', 'screening_status': 'trusted-threshold-upper-bound'},
            },
            {
                'label': 'silver',
                'threshold_upper_bound': None,
                'status': 'arithmetic-weaker-only',
                'provenance': {
                    'source': 'theorem-vi-screened-rational-panel',
                    'screening_status': 'edge-attained-exploratory-only',
                    'exploratory_threshold_upper_bound': 0.9738650136001021,
                    'exploratory_ceiling_attained_by': 'silver 12/5',
                },
            },
        ],
        'panel_records': [
            {'label': 'golden-anchor', 'eta_approx': 0.4472135955, 'threshold_lo': 0.9713628519087594, 'threshold_hi': 0.9713671752914450, 'is_golden': True},
            {'label': 'bronze', 'eta_approx': 0.2773500981, 'threshold_lo': 0.9688650136001022, 'threshold_hi': 0.9688650139468930, 'is_golden': False},
        ],
        'near_top_relation': {
            'golden_lower_minus_most_dangerous_upper': 0.0024978379618663,
            'most_dangerous_threshold_upper': 0.9688650139468930,
        },
        'global_nongolden_ceiling_certificate': {
            'global_nongolden_upper_ceiling': 0.9738650136001021,
            'golden_lower_witness': 0.9713628519087594,
            'global_gap_margin': -0.0025021616913427636,
            'global_ceiling_status': 'global-ceiling-partial',
            'global_ceiling_theorem_certified': False,
        },
        'statement_mode_certificate': {
            'candidate_mode': 'one-variable',
            'mode_lock_status': 'one-variable-supported',
            'status': 'statement-mode-certificate-one-variable-supported',
            'evidence_margin': 8.6e-11,
        },
    }

    monkeypatch.setattr(tvel, 'build_golden_theorem_ii_to_v_identification_certificate', lambda **kwargs: _Dummy(identification))
    monkeypatch.setattr(tvel, 'build_eta_threshold_comparison_certificate', lambda **kwargs: _Dummy(eta_anchor))
    monkeypatch.setattr(tvel, 'build_proto_envelope_eta_bridge_certificate', lambda **kwargs: _Dummy(proto))

    cert = build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=[0.3],
        near_top_certificate=near_top,
    ).to_dict()
    assert cert['open_hypotheses'] == []
    assert cert['screened_near_top_dominance_certificate']['deferred_exploratory_records'][0]['label'] == 'silver'
    assert cert['current_local_top_gap_certificate']['status'] in {
        'current-local-top-gap-partial',
        'current-local-top-gap-strong',
    }
    assert cert['theorem_status'] in {
        'golden-theorem-vi-envelope-lift-front-complete',
        'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
    }
