from __future__ import annotations

import math
import unittest

from kam_theorem_suite.audit.lower_anchor_heavy_certificate import (
    HeavyLowerAnchorConfig,
    build_heavy_candidate_json,
    run_heavy_lower_anchor_certificate,
)


_GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def _phase2e_zero_builder(**kwargs):
    N = max(kwargs.get("N_values", (16,)))
    K = float(kwargs.get("K", 0.0))
    return {
        "rho": _GOLDEN,
        "K": 0.0,  # exact zero forcing gives a closed ledger for the test object
        "N": int(N),
        "sigma_used": 1.0e-3,
        "finite_dimensional_success": True,
        "finite_radius": 1.0e-4,
        "finite_eta": 0.0,
        "finite_B_norm": 1.0,
        "finite_lipschitz_bound": 0.1,
        "finite_contraction_bound": 0.01,
        "finite_radii_margin": 9.0e-5,
        "theorem_status": "analytic-torus-bridge-weak",
        "theorem_margin": -1.0,  # Phase-2E direct ledger should supersede this compact old margin.
        "cohomological_inverse_bound": 5.0,
        "cohomological_correction_bound": 0.0,
        "defect_report": {"weighted_l1": 0.0},
        "tail_bound": {"tail_l1": 0.0},
        "source_validation": {"u": [0.0] * int(N), "lambda_value": 0.0},
        "builder_test_K_seen": K,
    }


class HeavyLowerAnchorPhase2EIngestionTests(unittest.TestCase):
    def test_phase2e_direct_radii_ledger_can_promote_without_legacy_status_string(self) -> None:
        cfg = HeavyLowerAnchorConfig(
            start_K=0.0,
            final_anchor_lo=0.49,
            final_anchor_hi=0.5,
            N_values=(16,),
            theorem_margin_safety_factor=1.0,
            outward_rounding_tolerance=1e-12,
        )
        report = run_heavy_lower_anchor_certificate(cfg, certificate_builder=_phase2e_zero_builder)
        self.assertTrue(report.promotion_allowed)
        self.assertTrue(all(r.phase2e_ledger and r.phase2e_ledger["theorem_ready"] for r in report.records))
        self.assertTrue(all(r.closure_level == "analytic_theorem_closure" for r in report.records))
        cand = build_heavy_candidate_json(report, source_artifact="tests/phase2e.json")
        self.assertTrue(cand["theorem_facing"])
        self.assertFalse(cand["diagnostic_only"])
        self.assertGreater(min(row["radii_margin"] for row in cand["anchor_segments"]), 0.0)

    def test_phase2e_direct_radii_ledger_is_fail_closed_when_disabled_or_unavailable(self) -> None:
        cfg = HeavyLowerAnchorConfig(
            start_K=0.0,
            final_anchor_lo=0.49,
            final_anchor_hi=0.5,
            N_values=(16,),
            theorem_margin_safety_factor=1.0,
            outward_rounding_tolerance=1e-12,
            use_phase2e_direct_radii_ledger=False,
        )
        report = run_heavy_lower_anchor_certificate(cfg, certificate_builder=_phase2e_zero_builder)
        self.assertFalse(report.promotion_allowed)
        self.assertTrue(any("analytic_theorem_margin_not_safely_positive" in r.failure_reasons for r in report.records))


if __name__ == "__main__":
    unittest.main()
