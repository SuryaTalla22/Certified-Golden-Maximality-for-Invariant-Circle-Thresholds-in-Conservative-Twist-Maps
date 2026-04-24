from pprint import pprint

from kam_theorem_suite.convergent_family_limit_control import build_convergent_family_limit_certificate

ladder = {
    "approximants": [
        {"p": 5, "q": 8, "label": "5/8", "crossing_root_window_lo": 0.97100, "crossing_root_window_hi": 0.97128, "crossing_center": 0.97114,
         "bridge_report": {"crossing_certificate": {"certification_tier": "monotone_window", "derivative_away_from_zero": True, "interval_newton": {"success": False}, "branch_summary": {"gprime_interval_lo": 0.7, "gprime_interval_hi": 1.0, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 3e-4}}}}},
        {"p": 8, "q": 13, "label": "8/13", "crossing_root_window_lo": 0.97108, "crossing_root_window_hi": 0.97124, "crossing_center": 0.97116,
         "bridge_report": {"crossing_certificate": {"certification_tier": "interval_newton", "derivative_away_from_zero": True, "interval_newton": {"success": True}, "branch_summary": {"gprime_interval_lo": 0.9, "gprime_interval_hi": 1.2, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 2e-4}}}}},
        {"p": 13, "q": 21, "label": "13/21", "crossing_root_window_lo": 0.97112, "crossing_root_window_hi": 0.97120, "crossing_center": 0.97116,
         "bridge_report": {"crossing_certificate": {"certification_tier": "interval_newton", "derivative_away_from_zero": True, "interval_newton": {"success": True}, "branch_summary": {"gprime_interval_lo": 1.0, "gprime_interval_hi": 1.3, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 1e-4}}}}},
        {"p": 21, "q": 34, "label": "21/34", "crossing_root_window_lo": 0.97114, "crossing_root_window_hi": 0.97118, "crossing_center": 0.97116,
         "bridge_report": {"crossing_certificate": {"certification_tier": "interval_newton", "derivative_away_from_zero": True, "interval_newton": {"success": True}, "branch_summary": {"gprime_interval_lo": 1.1, "gprime_interval_hi": 1.4, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 7e-5}}}}},
    ]
}

pprint(build_convergent_family_limit_certificate(ladder, min_chain_length=4).to_dict())
