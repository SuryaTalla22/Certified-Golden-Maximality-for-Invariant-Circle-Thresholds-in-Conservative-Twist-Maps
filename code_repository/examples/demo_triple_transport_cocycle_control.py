from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.triple_transport_cocycle_control import build_triple_transport_cocycle_limit_certificate

ladder = {
    'approximants': [
        {
            'p': 5, 'q': 8, 'label': '5/8',
            'crossing_root_window_lo': 0.97100, 'crossing_root_window_hi': 0.97128,
            'bridge_report': {'crossing_certificate': {
                'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                'endpoint_left': {'signed_gap_interval_lo': -3.0e-4, 'signed_gap_interval_hi': -1.0e-4},
                'endpoint_right': {'signed_gap_interval_lo': 1.0e-4, 'signed_gap_interval_hi': 2.2e-4},
                'midpoint': {'signed_gap_interval_lo': -1.0e-4, 'signed_gap_interval_hi': 8.0e-5, 'K': 0.97114},
                'interval_newton': {'success': False},
                'branch_summary': {'gprime_interval_lo': 0.7, 'gprime_interval_hi': 1.0, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 3e-4, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.2}},
            }},
        },
        {
            'p': 8, 'q': 13, 'label': '8/13',
            'crossing_root_window_lo': 0.97108, 'crossing_root_window_hi': 0.97124,
            'bridge_report': {'crossing_certificate': {
                'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                'endpoint_left': {'signed_gap_interval_lo': -1.4e-4, 'signed_gap_interval_hi': -6.0e-5},
                'endpoint_right': {'signed_gap_interval_lo': 5.0e-5, 'signed_gap_interval_hi': 1.2e-4},
                'midpoint': {'signed_gap_interval_lo': -4.0e-5, 'signed_gap_interval_hi': 3.0e-5, 'K': 0.97116},
                'interval_newton': {'success': True, 'refined_lo': 0.97112, 'refined_hi': 0.97120},
                'branch_summary': {'gprime_interval_lo': 0.9, 'gprime_interval_hi': 1.2, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 2e-4, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.18}},
            }},
        },
        {
            'p': 13, 'q': 21, 'label': '13/21',
            'crossing_root_window_lo': 0.97112, 'crossing_root_window_hi': 0.97120,
            'bridge_report': {'crossing_certificate': {
                'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                'endpoint_left': {'signed_gap_interval_lo': -7.0e-5, 'signed_gap_interval_hi': -2.0e-5},
                'endpoint_right': {'signed_gap_interval_lo': 2.0e-5, 'signed_gap_interval_hi': 6.0e-5},
                'midpoint': {'signed_gap_interval_lo': -1.5e-5, 'signed_gap_interval_hi': 1.0e-5, 'K': 0.97116},
                'interval_newton': {'success': True, 'refined_lo': 0.971145, 'refined_hi': 0.971185},
                'branch_summary': {'gprime_interval_lo': 1.0, 'gprime_interval_hi': 1.3, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 1e-4, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.15}},
            }},
        },
        {
            'p': 21, 'q': 34, 'label': '21/34',
            'crossing_root_window_lo': 0.97114, 'crossing_root_window_hi': 0.97118,
            'bridge_report': {'crossing_certificate': {
                'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                'endpoint_left': {'signed_gap_interval_lo': -3.0e-5, 'signed_gap_interval_hi': -1.0e-5},
                'endpoint_right': {'signed_gap_interval_lo': 1.0e-5, 'signed_gap_interval_hi': 3.0e-5},
                'midpoint': {'signed_gap_interval_lo': -7.0e-6, 'signed_gap_interval_hi': 6.0e-6, 'K': 0.97116},
                'interval_newton': {'success': True, 'refined_lo': 0.971152, 'refined_hi': 0.971172},
                'branch_summary': {'gprime_interval_lo': 1.1, 'gprime_interval_hi': 1.4, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 7e-5, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.12}},
            }},
        },
        {
            'p': 34, 'q': 55, 'label': '34/55',
            'crossing_root_window_lo': 0.971148, 'crossing_root_window_hi': 0.971170,
            'bridge_report': {'crossing_certificate': {
                'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                'endpoint_left': {'signed_gap_interval_lo': -1.7e-5, 'signed_gap_interval_hi': -0.5e-5},
                'endpoint_right': {'signed_gap_interval_lo': 0.5e-5, 'signed_gap_interval_hi': 1.6e-5},
                'midpoint': {'signed_gap_interval_lo': -4.0e-6, 'signed_gap_interval_hi': 3.0e-6, 'K': 0.971159},
                'interval_newton': {'success': True, 'refined_lo': 0.971153, 'refined_hi': 0.971166},
                'branch_summary': {'gprime_interval_lo': 1.15, 'gprime_interval_hi': 1.45, 'branch_tube': {'branch_residual_width': 1e-8, 'tube_sup_width': 5e-5, 'interval_tangent_success': True, 'interval_tangent_contraction': 0.10}},
            }},
        },
    ]
}

pprint(build_triple_transport_cocycle_limit_certificate(ladder).to_dict())
