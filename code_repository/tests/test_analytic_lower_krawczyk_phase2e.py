from __future__ import annotations

import math
import unittest

from kam_theorem_suite.analytic_lower_krawczyk import (
    build_analytic_lower_radii_ledger,
    build_modewise_divisor_ledger,
    choose_best_phase2e_ledger,
    exact_small_divisor_gap,
)


_GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def _perfect_zero_certificate(N: int = 16) -> dict:
    return {
        "rho": _GOLDEN,
        "K": 0.0,
        "N": N,
        "sigma_used": 1.0e-3,
        "finite_radius": 1.0e-4,
        "finite_radii_margin": 9.0e-5,
        "finite_B_norm": 1.0,
        "finite_lipschitz_bound": 0.1,
        "finite_contraction_bound": 0.01,
        "theorem_margin": 9.0e-5,
        "cohomological_inverse_bound": 5.0,
        "defect_report": {"weighted_l1": 0.0},
        "tail_bound": {"tail_l1": 0.0},
        "source_validation": {
            "u": [0.0] * N,
            "lambda_value": 0.0,
        },
    }


class AnalyticLowerKrawczykPhase2ETests(unittest.TestCase):
    def test_exact_small_divisor_gap_is_positive_for_golden_modes(self) -> None:
        vals = [exact_small_divisor_gap(_GOLDEN, k) for k in range(1, 20)]
        self.assertTrue(all(v > 0.0 for v in vals))
        self.assertLess(min(vals), max(vals))

    def test_modewise_divisor_ledger_has_positive_gaps(self) -> None:
        ledger = build_modewise_divisor_ledger(32, rho=_GOLDEN, sigma=1e-3)
        self.assertTrue(ledger.certified)
        self.assertGreater(ledger.min_gap, 0.0)
        self.assertGreater(ledger.max_inverse_multiplier, 1.0)
        self.assertEqual(ledger.zero_mode_policy.startswith("zero Fourier mode"), True)

    def test_perfect_zero_source_closes_direct_radii_ledger(self) -> None:
        ledger = build_analytic_lower_radii_ledger(_perfect_zero_certificate())
        self.assertTrue(ledger.modewise_residual_available)
        self.assertTrue(ledger.theorem_ready)
        self.assertEqual(ledger.failure_reasons, tuple())
        self.assertGreater(ledger.radii_margin, 0.0)
        terms = ledger.to_candidate_terms()
        self.assertTrue(terms["theorem_ready"])
        self.assertFalse(terms["finite_dimensional_only"])
        self.assertGreater(terms["small_divisor_min"], 0.0)

    def test_missing_samples_are_fail_closed_not_silent_promotion(self) -> None:
        cert = _perfect_zero_certificate()
        cert.pop("source_validation")
        ledger = build_analytic_lower_radii_ledger(cert)
        self.assertFalse(ledger.modewise_residual_available)
        self.assertFalse(ledger.theorem_ready)
        self.assertIn("modewise_residual_coefficients_unavailable", ledger.failure_reasons)

    def test_best_ledger_prefers_positive_margin_and_higher_resolution(self) -> None:
        strong = build_analytic_lower_radii_ledger(_perfect_zero_certificate(16))
        stronger = build_analytic_lower_radii_ledger(_perfect_zero_certificate(32))
        best = choose_best_phase2e_ledger([strong, stronger])
        self.assertEqual(best.N, 32)


if __name__ == "__main__":
    unittest.main()
