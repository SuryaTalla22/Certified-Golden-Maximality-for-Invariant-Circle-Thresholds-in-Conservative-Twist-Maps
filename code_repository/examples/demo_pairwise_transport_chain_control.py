from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.pairwise_transport_chain_control import build_pairwise_transport_chain_limit_certificate

ladder = {
    "approximants": [
        {
            "p": 5,
            "q": 8,
            "label": "5/8",
            "crossing_root_window_lo": 0.97100,
            "crossing_root_window_hi": 0.97128,
            "bridge_report": {"crossing_certificate": {
                "K_lo": 0.97100,
                "K_hi": 0.97128,
                "derivative_sign": "positive",
                "derivative_away_from_zero": True,
                "interval_newton": {"success": True, "refined_lo": 0.97109, "refined_hi": 0.97119},
                "branch_summary": {"gprime_interval_lo": 0.75, "gprime_interval_hi": 1.05, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 3e-4, "interval_tangent_success": True, "interval_tangent_contraction": 0.22}}}},
        },
        {
            "p": 8,
            "q": 13,
            "label": "8/13",
            "crossing_root_window_lo": 0.97108,
            "crossing_root_window_hi": 0.97124,
            "bridge_report": {"crossing_certificate": {
                "K_lo": 0.97108,
                "K_hi": 0.97124,
                "derivative_sign": "positive",
                "derivative_away_from_zero": True,
                "interval_newton": {"success": True, "refined_lo": 0.97112, "refined_hi": 0.97120},
                "branch_summary": {"gprime_interval_lo": 0.9, "gprime_interval_hi": 1.2, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 2e-4, "interval_tangent_success": True, "interval_tangent_contraction": 0.18}}}},
        },
        {
            "p": 13,
            "q": 21,
            "label": "13/21",
            "crossing_root_window_lo": 0.97112,
            "crossing_root_window_hi": 0.97120,
            "bridge_report": {"crossing_certificate": {
                "K_lo": 0.97112,
                "K_hi": 0.97120,
                "derivative_sign": "positive",
                "derivative_away_from_zero": True,
                "interval_newton": {"success": True, "refined_lo": 0.971145, "refined_hi": 0.971185},
                "branch_summary": {"gprime_interval_lo": 1.0, "gprime_interval_hi": 1.3, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 1e-4, "interval_tangent_success": True, "interval_tangent_contraction": 0.15}}}},
        },
        {
            "p": 21,
            "q": 34,
            "label": "21/34",
            "crossing_root_window_lo": 0.97114,
            "crossing_root_window_hi": 0.97118,
            "bridge_report": {"crossing_certificate": {
                "K_lo": 0.97114,
                "K_hi": 0.97118,
                "derivative_sign": "positive",
                "derivative_away_from_zero": True,
                "interval_newton": {"success": True, "refined_lo": 0.971152, "refined_hi": 0.971172},
                "branch_summary": {"gprime_interval_lo": 1.1, "gprime_interval_hi": 1.4, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 7e-5, "interval_tangent_success": True, "interval_tangent_contraction": 0.12}}}},
        },
    ]
}

cert = build_pairwise_transport_chain_limit_certificate(ladder, min_chain_length=4)
pprint(cert.to_dict())
