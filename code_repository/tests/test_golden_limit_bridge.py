from __future__ import annotations

from kam_theorem_suite.golden_limit_bridge import build_golden_rational_to_irrational_convergence_certificate
from kam_theorem_suite.proof_driver import build_golden_rational_to_irrational_convergence_report


def _dummy(payload):
    class _D:
        def __init__(self, data):
            self._data = data
        def to_dict(self):
            return dict(self._data)
    return _D(payload)


def test_golden_limit_bridge_uses_new_convergence_layer(monkeypatch) -> None:
    import kam_theorem_suite.golden_limit_bridge as glb

    monkeypatch.setattr(
        glb,
        "build_golden_lower_neighborhood_stability_certificate",
        lambda **kwargs: _dummy(
            {
                "stable_lower_bound": 0.96,
                "stable_observed_upper_hint": 0.965,
                "theorem_status": "golden-lower-neighborhood-stability-strong",
            }
        ),
    )
    monkeypatch.setattr(
        glb,
        "build_golden_supercritical_obstruction_certificate",
        lambda **kwargs: _dummy(
            {
                "ladder": {
                    "approximants": [
                        {"p": 5, "q": 8, "label": "g-5/8", "crossing_root_window_lo": 0.97100, "crossing_root_window_hi": 0.97128, "crossing_center": 0.97114, "bridge_report": {"crossing_certificate": {"certification_tier": "monotone_window", "derivative_away_from_zero": True, "interval_newton": {"success": False}, "branch_summary": {"gprime_interval_lo": 0.7, "gprime_interval_hi": 1.0, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 3e-4}}}}},
                        {"p": 8, "q": 13, "label": "g-8/13", "crossing_root_window_lo": 0.97108, "crossing_root_window_hi": 0.97124, "crossing_center": 0.97116, "bridge_report": {"crossing_certificate": {"certification_tier": "interval_newton", "derivative_away_from_zero": True, "interval_newton": {"success": True}, "branch_summary": {"gprime_interval_lo": 0.9, "gprime_interval_hi": 1.2, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 2e-4}}}}},
                        {"p": 13, "q": 21, "label": "g-13/21", "crossing_root_window_lo": 0.97112, "crossing_root_window_hi": 0.97120, "crossing_center": 0.97116, "bridge_report": {"crossing_certificate": {"certification_tier": "interval_newton", "derivative_away_from_zero": True, "interval_newton": {"success": True}, "branch_summary": {"gprime_interval_lo": 1.0, "gprime_interval_hi": 1.3, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 1e-4}}}}},
                        {"p": 21, "q": 34, "label": "g-21/34", "crossing_root_window_lo": 0.97114, "crossing_root_window_hi": 0.97118, "crossing_center": 0.97116, "bridge_report": {"crossing_certificate": {"certification_tier": "interval_newton", "derivative_away_from_zero": True, "interval_newton": {"success": True}, "branch_summary": {"gprime_interval_lo": 1.1, "gprime_interval_hi": 1.4, "tangent_inclusion_success": True, "branch_tube": {"branch_residual_width": 1e-8, "tube_sup_width": 7e-5}}}}},
                    ]
                },
                "refined": {"selected_cluster_member_qs": [8, 13, 21, 34]},
                "asymptotic_audit": {"audited_upper_source_threshold": 13},
                "theorem_status": "golden-supercritical-obstruction-moderate",
            }
        ),
    )
    monkeypatch.setattr(
        glb,
        "build_golden_upper_tail_stability_certificate",
        lambda **kwargs: _dummy(
            {
                "stable_upper_lo": 0.97115,
                "stable_upper_hi": 0.97130,
                "stable_upper_width": 0.00015,
                "stable_tail_qs": [13, 21],
                "theorem_status": "golden-supercritical-tail-stability-strong",
            }
        ),
    )

    cert = build_golden_rational_to_irrational_convergence_certificate(base_K_values=[0.4, 0.5, 0.6])
    d = cert.to_dict()
    assert d["convergence_control"]["theorem_status"].startswith("irrational-limit-control-")
    assert d["branch_certified_control"]["theorem_status"].startswith("branch-certified-limit-")
    assert d["nested_subladder_control"]["theorem_status"].startswith("nested-subladder-limit-")
    assert d["convergent_family_control"]["theorem_status"].startswith("convergent-family-limit-")
    assert d["transport_certified_control"]["theorem_status"].startswith("transport-certified-limit-")
    assert d["pairwise_transport_control"]["theorem_status"].startswith("pairwise-transport-chain-")
    assert d["triple_transport_cocycle_control"]["theorem_status"].startswith("triple-transport-cocycle-")
    assert d["global_transport_potential_control"]["theorem_status"].startswith("global-transport-potential-")
    assert d["tail_cauchy_potential_control"]["theorem_status"].startswith("tail-cauchy-potential-")
    assert d["certified_tail_modulus_control"]["theorem_status"].startswith("certified-tail-modulus-")
    assert d["rate_aware_tail_modulus_control"]["theorem_status"].startswith("rate-aware-tail-modulus-")
    assert d["golden_recurrence_rate_control"]["theorem_status"].startswith("golden-recurrence-rate-")
    assert d["transport_slope_weighted_golden_rate_control"]["theorem_status"].startswith("transport-slope-weighted-golden-rate-")
    assert d["edge_class_weighted_golden_rate_control"]["theorem_status"].startswith("edge-class-weighted-golden-rate-")
    assert d["theorem_v_explicit_error_control"]["theorem_status"].startswith("theorem-v-explicit-error-law-")
    assert d["relation"]["gap_to_fit_interval"] is not None
    assert d["relation"]["gap_to_branch_interval"] is not None
    assert d["relation"]["gap_to_global_transport_potential_interval"] is not None
    assert d["relation"]["gap_to_tail_cauchy_potential_interval"] is not None
    assert d["relation"]["gap_to_certified_tail_modulus_interval"] is not None
    assert d["relation"]["gap_to_rate_aware_tail_modulus_interval"] is not None
    assert d["relation"]["gap_to_golden_recurrence_rate_interval"] is not None
    assert d["relation"]["gap_to_transport_slope_weighted_golden_rate_interval"] is not None
    assert d["relation"]["gap_to_edge_class_weighted_golden_rate_interval"] is not None
    assert d["relation"]["gap_to_theorem_v_explicit_error_interval"] is not None
    assert d["relation"]["native_late_coherent_suffix_witness_lo"] is not None
    assert d["relation"]["native_late_coherent_suffix_witness_hi"] is not None
    assert d["relation"]["native_late_coherent_suffix_witness_width"] is not None
    assert d["relation"]["native_late_coherent_suffix_length"] >= 3
    assert d["relation"]["native_late_coherent_suffix_contracting"] is True
    assert d["relation"]["gap_to_native_late_coherent_suffix_interval"] is not None
    assert d["theorem_status"].startswith("golden-rational-to-irrational-convergence-")


def test_driver_layer_exposes_golden_limit_bridge(monkeypatch) -> None:
    import kam_theorem_suite.proof_driver as pd

    monkeypatch.setattr(
        pd,
        "build_golden_rational_to_irrational_convergence_certificate",
        lambda **kwargs: _dummy(
            {
                "relation": {"gap_to_fit_interval": 0.01},
                "theorem_status": "golden-rational-to-irrational-convergence-partial",
            }
        ),
    )
    report = build_golden_rational_to_irrational_convergence_report(base_K_values=[0.4, 0.5, 0.6])
    assert report["relation"]["gap_to_fit_interval"] == 0.01
    assert report["theorem_status"] == "golden-rational-to-irrational-convergence-partial"
