from __future__ import annotations

from kam_theorem_suite.nested_subladder_limit_control import build_nested_subladder_limit_certificate
from kam_theorem_suite.proof_driver import build_nested_subladder_limit_report


def _synthetic_ladder() -> dict:
    return {
        "approximants": [
            {
                "p": 7,
                "q": 8,
                "label": "7/8",
                "crossing_root_window_lo": 0.97100,
                "crossing_root_window_hi": 0.97134,
                "crossing_root_window_width": 0.00034,
                "crossing_center": 0.97117,
                "bridge_report": {
                    "crossing_certificate": {
                        "certification_tier": "monotone_window",
                        "derivative_away_from_zero": True,
                        "interval_newton": {"success": False},
                        "branch_summary": {
                            "gprime_interval_lo": 0.6,
                            "gprime_interval_hi": 0.9,
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
                "crossing_root_window_lo": 0.97109,
                "crossing_root_window_hi": 0.97129,
                "crossing_root_window_width": 0.00020,
                "crossing_center": 0.97119,
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
                "crossing_root_window_lo": 0.97114,
                "crossing_root_window_hi": 0.97126,
                "crossing_root_window_width": 0.00012,
                "crossing_center": 0.97120,
                "bridge_report": {
                    "crossing_certificate": {
                        "certification_tier": "interval_newton",
                        "derivative_away_from_zero": True,
                        "interval_newton": {"success": True},
                        "branch_summary": {
                            "gprime_interval_lo": 1.0,
                            "gprime_interval_hi": 1.3,
                            "tangent_inclusion_success": True,
                            "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 1e-4},
                        },
                    }
                },
            },
            {
                "p": 33,
                "q": 34,
                "label": "33/34",
                "crossing_root_window_lo": 0.97117,
                "crossing_root_window_hi": 0.97123,
                "crossing_root_window_width": 0.00006,
                "crossing_center": 0.97120,
                "bridge_report": {
                    "crossing_certificate": {
                        "certification_tier": "interval_newton",
                        "derivative_away_from_zero": True,
                        "interval_newton": {"success": True},
                        "branch_summary": {
                            "gprime_interval_lo": 1.1,
                            "gprime_interval_hi": 1.4,
                            "tangent_inclusion_success": True,
                            "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 8e-5},
                        },
                    }
                },
            },
        ]
    }


def test_nested_subladder_limit_control_builds_chain() -> None:
    cert = build_nested_subladder_limit_certificate(_synthetic_ladder(), min_members=2)
    d = cert.to_dict()
    assert d["theorem_status"].startswith("nested-subladder-limit-")
    assert d["chain_length"] >= 2
    assert d["final_interval_lo"] is not None
    assert d["final_interval_hi"] is not None
    assert d["final_interval_lo"] <= 0.97120 <= d["final_interval_hi"]


def test_driver_exposes_nested_subladder_layer() -> None:
    report = build_nested_subladder_limit_report(_synthetic_ladder(), min_members=2)
    assert report["chain_length"] >= 2
    assert report["theorem_status"].startswith("nested-subladder-limit-")
