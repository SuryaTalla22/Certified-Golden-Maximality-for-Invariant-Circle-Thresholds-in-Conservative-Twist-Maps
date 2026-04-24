
from __future__ import annotations

from kam_theorem_suite.theorem_vi_envelope_lift import (
    _build_current_local_top_gap_certificate,
    _build_screened_near_top_dominance_certificate,
    build_golden_theorem_vi_envelope_lift_certificate,
)


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_stage104_local_gap_witness_promotes_screened_domination_without_numeric_gap() -> None:
    screened = _build_screened_near_top_dominance_certificate(
        {
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
                    },
                },
            ],
            'near_top_relation': {
                'golden_lower_minus_most_dangerous_upper': None,
                'most_dangerous_threshold_upper': None,
            },
        }
    )
    cert = _build_current_local_top_gap_certificate(
        proto={
            'theorem_flags': {},
            'proto_envelope_relation': {
                'anchor_lower_minus_panel_nongolden_upper': None,
                'panel_nongolden_max_upper_bound': None,
            },
        },
        near_top={
            'theorem_flags': {
                'all_threshold_bounded_challengers_dominated': True,
                'no_undecided_challengers': True,
                'panel_gap_positive': False,
            },
            'near_top_relation': {
                'golden_lower_minus_most_dangerous_upper': None,
                'most_dangerous_threshold_upper': None,
            },
        },
        screened_near_top_dominance_certificate=screened,
    )
    assert cert['status'] == 'current-local-top-gap-screened-domination-positive'
    assert cert['exploratory_top_gap_positive'] is True
    assert cert['screened_domination_positive_without_numeric_gap'] is True
    assert cert['local_geometry_supports_top_gap_promotion'] is True



def test_stage104_front_completes_gap_hypothesis_with_screened_gap_witness() -> None:
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
    }
    proto = {
        'theorem_status': 'proto-envelope-eta-bridge-moderate',
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
    }
    near_top = {
        'theorem_status': 'near-top-eta-challenger-comparison-weak',
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
                'label': 'near-golden-12',
                'threshold_upper_bound': None,
                'status': 'arithmetic-weaker-only',
                'provenance': {
                    'source': 'theorem-vi-screened-rational-panel',
                    'screening_status': 'edge-attained-exploratory-only',
                    'exploratory_threshold_upper_bound': 0.9738650136001021,
                    'exploratory_ceiling_attained_by': '7/5',
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
                    'exploratory_ceiling_attained_by': '12/5',
                },
            },
        ],
        'near_top_relation': {
            'golden_lower_minus_most_dangerous_upper': None,
            'most_dangerous_threshold_upper': None,
        },
    }

    screened = _build_screened_near_top_dominance_certificate(near_top)
    current_local = _build_current_local_top_gap_certificate(
        proto=proto,
        near_top=near_top,
        screened_near_top_dominance_certificate=screened,
    )
    hypotheses = build_golden_theorem_vi_envelope_lift_certificate.__globals__['_build_hypotheses'](
        identification,
        eta_anchor,
        proto,
        near_top,
        current_local_top_gap_certificate=current_local,
    )
    hyp = {row.name: row for row in hypotheses}

    assert current_local['status'] == 'current-local-top-gap-screened-domination-positive'
    assert current_local['exploratory_top_gap_positive'] is True
    assert hyp['exploratory_top_gap_positive'].satisfied is True
    assert hyp['threshold_identification_front_complete'].satisfied is True
    assert hyp['eta_threshold_anchor_strong'].satisfied is True
    assert hyp['proto_envelope_anchor_available'].satisfied is True
    assert hyp['near_top_challenger_surface_available'].satisfied is True
