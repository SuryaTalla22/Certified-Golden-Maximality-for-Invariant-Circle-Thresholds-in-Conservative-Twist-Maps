from __future__ import annotations

from kam_theorem_suite.global_transport_potential_control import build_global_transport_potential_certificate
from kam_theorem_suite.proof_driver import build_global_transport_potential_report


def _synthetic_ladder() -> dict:
    return {
        'approximants': [
            {
                'p': 5, 'q': 8, 'label': '5/8',
                'crossing_root_window_lo': 0.97100, 'crossing_root_window_hi': 0.97128,
                'bridge_report': {'crossing_certificate': {
                    'K_lo': 0.97100, 'K_hi': 0.97128,
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'endpoint_left': {'signed_gap_interval_lo': -1.8e-4, 'signed_gap_interval_hi': -0.8e-4},
                    'endpoint_right': {'signed_gap_interval_lo': 0.8e-4, 'signed_gap_interval_hi': 1.9e-4},
                    'midpoint': {'signed_gap_interval_lo': -3.0e-5, 'signed_gap_interval_hi': 2.5e-5, 'K': 0.97114},
                    'interval_newton': {'success': True, 'refined_lo': 0.97110, 'refined_hi': 0.97118},
                    'branch_summary': {'gprime_interval_lo': 0.7, 'gprime_interval_hi': 1.0, 'tangent_inclusion_success': True, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 3.0e-4, 'slope_center_inf': 2.9, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.22}},
                }},
            },
            {
                'p': 8, 'q': 13, 'label': '8/13',
                'crossing_root_window_lo': 0.97108, 'crossing_root_window_hi': 0.97124,
                'bridge_report': {'crossing_certificate': {
                    'K_lo': 0.97108, 'K_hi': 0.97124,
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'endpoint_left': {'signed_gap_interval_lo': -1.2e-4, 'signed_gap_interval_hi': -0.4e-4},
                    'endpoint_right': {'signed_gap_interval_lo': 0.4e-4, 'signed_gap_interval_hi': 1.1e-4},
                    'midpoint': {'signed_gap_interval_lo': -2.0e-5, 'signed_gap_interval_hi': 1.8e-5, 'K': 0.97116},
                    'interval_newton': {'success': True, 'refined_lo': 0.97112, 'refined_hi': 0.97120},
                    'branch_summary': {'gprime_interval_lo': 0.9, 'gprime_interval_hi': 1.2, 'tangent_inclusion_success': True, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 1.8e-4, 'slope_center_inf': 2.6, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.18}},
                }},
            },
            {
                'p': 13, 'q': 21, 'label': '13/21',
                'crossing_root_window_lo': 0.97112, 'crossing_root_window_hi': 0.97120,
                'bridge_report': {'crossing_certificate': {
                    'K_lo': 0.97112, 'K_hi': 0.97120,
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'endpoint_left': {'signed_gap_interval_lo': -7.0e-5, 'signed_gap_interval_hi': -2.0e-5},
                    'endpoint_right': {'signed_gap_interval_lo': 2.0e-5, 'signed_gap_interval_hi': 6.0e-5},
                    'midpoint': {'signed_gap_interval_lo': -1.5e-5, 'signed_gap_interval_hi': 1.0e-5, 'K': 0.97116},
                    'interval_newton': {'success': True, 'refined_lo': 0.971145, 'refined_hi': 0.971185},
                    'branch_summary': {'gprime_interval_lo': 1.0, 'gprime_interval_hi': 1.3, 'tangent_inclusion_success': True, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 1.0e-4, 'slope_center_inf': 2.4, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.15}},
                }},
            },
            {
                'p': 21, 'q': 34, 'label': '21/34',
                'crossing_root_window_lo': 0.97114, 'crossing_root_window_hi': 0.97118,
                'bridge_report': {'crossing_certificate': {
                    'K_lo': 0.97114, 'K_hi': 0.97118,
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'endpoint_left': {'signed_gap_interval_lo': -3.0e-5, 'signed_gap_interval_hi': -1.0e-5},
                    'endpoint_right': {'signed_gap_interval_lo': 1.0e-5, 'signed_gap_interval_hi': 3.0e-5},
                    'midpoint': {'signed_gap_interval_lo': -7.0e-6, 'signed_gap_interval_hi': 6.0e-6, 'K': 0.97116},
                    'interval_newton': {'success': True, 'refined_lo': 0.971152, 'refined_hi': 0.971172},
                    'branch_summary': {'gprime_interval_lo': 1.1, 'gprime_interval_hi': 1.4, 'tangent_inclusion_success': True, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 7.0e-5, 'slope_center_inf': 2.0, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.12}},
                }},
            },
            {
                'p': 34, 'q': 55, 'label': '34/55',
                'crossing_root_window_lo': 0.971148, 'crossing_root_window_hi': 0.971170,
                'bridge_report': {'crossing_certificate': {
                    'K_lo': 0.971148, 'K_hi': 0.971170,
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'endpoint_left': {'signed_gap_interval_lo': -1.7e-5, 'signed_gap_interval_hi': -0.5e-5},
                    'endpoint_right': {'signed_gap_interval_lo': 0.5e-5, 'signed_gap_interval_hi': 1.6e-5},
                    'midpoint': {'signed_gap_interval_lo': -4.0e-6, 'signed_gap_interval_hi': 3.0e-6, 'K': 0.971159},
                    'interval_newton': {'success': True, 'refined_lo': 0.971153, 'refined_hi': 0.971166},
                    'branch_summary': {'gprime_interval_lo': 1.15, 'gprime_interval_hi': 1.45, 'tangent_inclusion_success': True, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 5.0e-5, 'slope_center_inf': 1.8, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.10}},
                }},
            },
        ]
    }


def test_global_transport_potential_builds_ladder_global_interval() -> None:
    cert = build_global_transport_potential_certificate(_synthetic_ladder(), min_chain_length=5)
    d = cert.to_dict()
    assert d['theorem_status'].startswith('global-transport-potential-')
    assert d['chain_length'] >= 5
    assert d['selected_limit_interval_lo'] is not None
    assert d['selected_limit_interval_hi'] is not None
    assert d['observed_monotone_ratio'] is not None and d['observed_monotone_ratio'] < 1.0
    budgets = [n['monotone_forward_edge_budget'] for n in d['nodes'][:-1]]
    assert all(budgets[i] >= budgets[i+1] for i in range(len(budgets)-1))


def test_driver_exposes_global_transport_potential_layer() -> None:
    report = build_global_transport_potential_report(_synthetic_ladder(), min_chain_length=5)
    assert report['chain_length'] >= 5
    assert report['theorem_status'].startswith('global-transport-potential-')
