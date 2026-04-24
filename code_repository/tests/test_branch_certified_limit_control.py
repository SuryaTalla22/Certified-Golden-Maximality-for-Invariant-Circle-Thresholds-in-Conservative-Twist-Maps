from __future__ import annotations

from kam_theorem_suite.branch_certified_limit_control import build_branch_certified_irrational_limit_certificate
from kam_theorem_suite.proof_driver import build_branch_certified_irrational_limit_report


def _synthetic_ladder() -> dict:
    return {
        "approximants": [
            {
                "p": 7,
                "q": 8,
                "label": "7/8",
                "crossing_root_window_lo": 0.97100,
                "crossing_root_window_hi": 0.97136,
                "crossing_root_window_width": 0.00036,
                "crossing_center": 0.97118,
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
                "crossing_root_window_lo": 0.97110,
                "crossing_root_window_hi": 0.97130,
                "crossing_root_window_width": 0.00020,
                "crossing_center": 0.97120,
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
                "crossing_root_window_width": 0.00012,
                "crossing_center": 0.97122,
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
        ]
    }


def test_branch_certified_limit_control_builds_tail_interval() -> None:
    cert = build_branch_certified_irrational_limit_certificate(_synthetic_ladder(), min_members=2)
    d = cert.to_dict()
    assert d["theorem_status"].startswith("branch-certified-limit-")
    assert d["selected_tail_member_count"] >= 2
    assert d["selected_limit_interval_lo"] is not None
    assert d["selected_limit_interval_hi"] is not None
    assert d["selected_limit_interval_lo"] <= 0.97122 <= d["selected_limit_interval_hi"]
    assert d["derivative_backed_fraction"] is not None and d["derivative_backed_fraction"] > 0.0


def test_driver_exposes_branch_certified_limit_layer() -> None:
    report = build_branch_certified_irrational_limit_report(_synthetic_ladder(), min_members=2)
    assert report["selected_tail_member_count"] >= 2
    assert report["theorem_status"].startswith("branch-certified-limit-")
