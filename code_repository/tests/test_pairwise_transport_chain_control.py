from __future__ import annotations

from kam_theorem_suite.pairwise_transport_chain_control import build_pairwise_transport_chain_limit_certificate
from kam_theorem_suite.proof_driver import build_pairwise_transport_chain_limit_report


def _synthetic_ladder() -> dict:
    return {
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
                    "endpoint_left": {"signed_gap_interval_lo": -2.2e-4, "signed_gap_interval_hi": -1.1e-4},
                    "endpoint_right": {"signed_gap_interval_lo": 1.0e-4, "signed_gap_interval_hi": 2.0e-4},
                    "midpoint": {"signed_gap_interval_lo": -5.0e-5, "signed_gap_interval_hi": 3.0e-5, "K": 0.97114},
                    "interval_newton": {"success": True, "refined_lo": 0.97109, "refined_hi": 0.97119},
                    "branch_summary": {"gprime_interval_lo": 0.75, "gprime_interval_hi": 1.05, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 3.0e-4, "slope_center_inf": 3.8, "interval_tangent_success": True, "interval_tangent_contraction": 0.22}}}},
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
                    "endpoint_left": {"signed_gap_interval_lo": -1.4e-4, "signed_gap_interval_hi": -6.0e-5},
                    "endpoint_right": {"signed_gap_interval_lo": 5.0e-5, "signed_gap_interval_hi": 1.2e-4},
                    "midpoint": {"signed_gap_interval_lo": -4.0e-5, "signed_gap_interval_hi": 3.0e-5, "K": 0.97116},
                    "interval_newton": {"success": True, "refined_lo": 0.97112, "refined_hi": 0.97120},
                    "branch_summary": {"gprime_interval_lo": 0.9, "gprime_interval_hi": 1.2, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 2.0e-4, "slope_center_inf": 3.0, "interval_tangent_success": True, "interval_tangent_contraction": 0.18}}}},
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
                    "endpoint_left": {"signed_gap_interval_lo": -7.0e-5, "signed_gap_interval_hi": -2.0e-5},
                    "endpoint_right": {"signed_gap_interval_lo": 2.0e-5, "signed_gap_interval_hi": 6.0e-5},
                    "midpoint": {"signed_gap_interval_lo": -1.5e-5, "signed_gap_interval_hi": 1.0e-5, "K": 0.97116},
                    "interval_newton": {"success": True, "refined_lo": 0.971145, "refined_hi": 0.971185},
                    "branch_summary": {"gprime_interval_lo": 1.0, "gprime_interval_hi": 1.3, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 1.0e-4, "slope_center_inf": 2.4, "interval_tangent_success": True, "interval_tangent_contraction": 0.15}}}},
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
                    "endpoint_left": {"signed_gap_interval_lo": -3.0e-5, "signed_gap_interval_hi": -1.0e-5},
                    "endpoint_right": {"signed_gap_interval_lo": 1.0e-5, "signed_gap_interval_hi": 3.0e-5},
                    "midpoint": {"signed_gap_interval_lo": -7.0e-6, "signed_gap_interval_hi": 6.0e-6, "K": 0.97116},
                    "interval_newton": {"success": True, "refined_lo": 0.971152, "refined_hi": 0.971172},
                    "branch_summary": {"gprime_interval_lo": 1.1, "gprime_interval_hi": 1.4, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 7.0e-5, "slope_center_inf": 2.0, "interval_tangent_success": True, "interval_tangent_contraction": 0.12}}}},
            },
        ]
    }


def test_pairwise_transport_chain_builds_chain_aware_interval() -> None:
    cert = build_pairwise_transport_chain_limit_certificate(_synthetic_ladder(), min_chain_length=4)
    d = cert.to_dict()
    assert d["theorem_status"].startswith("pairwise-transport-chain-")
    assert d["chain_length"] >= 4
    assert d["pair_count"] >= 3
    assert d["continuation_compatible_fraction"] is not None and d["continuation_compatible_fraction"] > 0.5
    assert d["limit_interval_lo"] is not None
    assert d["limit_interval_hi"] is not None
    assert d["observed_pair_contraction_ratio"] is not None and d["observed_pair_contraction_ratio"] < 1.0


def test_driver_exposes_pairwise_transport_chain_layer() -> None:
    report = build_pairwise_transport_chain_limit_report(_synthetic_ladder(), min_chain_length=4)
    assert report["chain_length"] >= 4
    assert report["theorem_status"].startswith("pairwise-transport-chain-")
