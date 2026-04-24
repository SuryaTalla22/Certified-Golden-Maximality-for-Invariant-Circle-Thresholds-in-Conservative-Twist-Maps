from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.branch_certified_limit_control import (
    build_branch_certified_irrational_limit_certificate,
)

ladder = {
    "approximants": [
        {
            "p": 7,
            "q": 8,
            "label": "7/8",
            "crossing_root_window_lo": 0.97105,
            "crossing_root_window_hi": 0.97135,
            "bridge_report": {
                "crossing_certificate": {
                    "certification_tier": "monotone_window",
                    "derivative_away_from_zero": True,
                    "interval_newton": {"success": False},
                    "branch_summary": {
                        "gprime_interval_lo": 0.8,
                        "gprime_interval_hi": 1.1,
                        "tangent_inclusion_success": True,
                        "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 4e-4},
                    },
                }
            },
        },
        {
            "p": 12,
            "q": 13,
            "label": "12/13",
            "crossing_root_window_lo": 0.97112,
            "crossing_root_window_hi": 0.97130,
            "bridge_report": {
                "crossing_certificate": {
                    "certification_tier": "interval_newton",
                    "derivative_away_from_zero": True,
                    "interval_newton": {"success": True},
                    "branch_summary": {
                        "gprime_interval_lo": 0.9,
                        "gprime_interval_hi": 1.2,
                        "tangent_inclusion_success": True,
                        "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 2e-4},
                    },
                }
            },
        },
        {
            "p": 20,
            "q": 21,
            "label": "20/21",
            "crossing_root_window_lo": 0.97116,
            "crossing_root_window_hi": 0.97128,
            "bridge_report": {
                "crossing_certificate": {
                    "certification_tier": "interval_newton",
                    "derivative_away_from_zero": True,
                    "interval_newton": {"success": True},
                    "branch_summary": {
                        "gprime_interval_lo": 1.0,
                        "gprime_interval_hi": 1.25,
                        "tangent_inclusion_success": True,
                        "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 1e-4},
                    },
                }
            },
        },
    ]
}

cert = build_branch_certified_irrational_limit_certificate(ladder, min_members=2)
pprint(cert.to_dict())
