from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.proof_driver import build_theorem_v_explicit_error_report


if __name__ == '__main__':
    ladder = {
        'approximants': [
            {
                'p': 5, 'q': 8, 'label': '5/8',
                'crossing_root_window_lo': 0.97100, 'crossing_root_window_hi': 0.97128,
                'bridge_report': {'crossing_certificate': {
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'interval_newton': {'success': True},
                    'branch_summary': {
                        'gprime_interval_lo': 0.7, 'gprime_interval_hi': 1.0,
                        'tangent_inclusion_success': True,
                        'branch_tube': {
                            'branch_residual_width': 1e-8,
                            'tube_sup_width': 3e-4,
                            'slope_center_inf': 2.9,
                            'interval_tangent_success': True,
                            'interval_tangent_contraction': 0.22,
                        },
                    },
                }},
            },
            {
                'p': 8, 'q': 13, 'label': '8/13',
                'crossing_root_window_lo': 0.97108, 'crossing_root_window_hi': 0.97124,
                'bridge_report': {'crossing_certificate': {
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'interval_newton': {'success': True},
                    'branch_summary': {
                        'gprime_interval_lo': 0.9, 'gprime_interval_hi': 1.2,
                        'tangent_inclusion_success': True,
                        'branch_tube': {
                            'branch_residual_width': 1e-8,
                            'tube_sup_width': 1.8e-4,
                            'slope_center_inf': 2.6,
                            'interval_tangent_success': True,
                            'interval_tangent_contraction': 0.18,
                        },
                    },
                }},
            },
            {
                'p': 13, 'q': 21, 'label': '13/21',
                'crossing_root_window_lo': 0.97112, 'crossing_root_window_hi': 0.97120,
                'bridge_report': {'crossing_certificate': {
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'interval_newton': {'success': True},
                    'branch_summary': {
                        'gprime_interval_lo': 1.0, 'gprime_interval_hi': 1.3,
                        'tangent_inclusion_success': True,
                        'branch_tube': {
                            'branch_residual_width': 1e-8,
                            'tube_sup_width': 1e-4,
                            'slope_center_inf': 2.4,
                            'interval_tangent_success': True,
                            'interval_tangent_contraction': 0.15,
                        },
                    },
                }},
            },
            {
                'p': 21, 'q': 34, 'label': '21/34',
                'crossing_root_window_lo': 0.97114, 'crossing_root_window_hi': 0.97118,
                'bridge_report': {'crossing_certificate': {
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'interval_newton': {'success': True},
                    'branch_summary': {
                        'gprime_interval_lo': 1.1, 'gprime_interval_hi': 1.4,
                        'tangent_inclusion_success': True,
                        'branch_tube': {
                            'branch_residual_width': 1e-8,
                            'tube_sup_width': 7e-5,
                            'slope_center_inf': 2.0,
                            'interval_tangent_success': True,
                            'interval_tangent_contraction': 0.12,
                        },
                    },
                }},
            },
            {
                'p': 34, 'q': 55, 'label': '34/55',
                'crossing_root_window_lo': 0.971148, 'crossing_root_window_hi': 0.971170,
                'bridge_report': {'crossing_certificate': {
                    'derivative_sign': 'positive', 'derivative_away_from_zero': True,
                    'interval_newton': {'success': True},
                    'branch_summary': {
                        'gprime_interval_lo': 1.15, 'gprime_interval_hi': 1.45,
                        'tangent_inclusion_success': True,
                        'branch_tube': {
                            'branch_residual_width': 1e-8,
                            'tube_sup_width': 5e-5,
                            'slope_center_inf': 1.8,
                            'interval_tangent_success': True,
                            'interval_tangent_contraction': 0.10,
                        },
                    },
                }},
            },
        ]
    }

    report = build_theorem_v_explicit_error_report(ladder, min_chain_length=5)
    pprint({
        'status': report['theorem_status'],
        'compatible_limit_interval': (
            report['compatible_limit_interval_lo'],
            report['compatible_limit_interval_hi'],
        ),
        'q_power_model_source': report['q_power_model_source'],
        'chosen_q_power_exponent': report['chosen_q_power_exponent'],
        'chain_qs': report['chain_qs'],
    })
