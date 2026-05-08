from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from kam_theorem_suite.audit.artifact_shell_builder import build_theorem_iv_shell_from_audit
from kam_theorem_suite.audit.proof_bundle_validator import (
    ProofAuditValidationError,
    assert_proof_audit_bundle_valid,
    validate_proof_audit_bundle,
)
from kam_theorem_suite.audit.upper_obstruction_margin import (
    audit_upper_obstruction_from_promotion,
    build_upper_obstruction_audit_bundle,
    build_upper_obstruction_ledger,
)

ROOT = Path(__file__).resolve().parents[1]
PROMOTION = ROOT / "artifacts/final_discharge/stage_cache/theorem_iv_upper_bridge_promotion.json"


class UpperObstructionAuditTests(unittest.TestCase):
    def load_promotion(self) -> dict:
        return json.loads(PROMOTION.read_text())

    def test_upper_obstruction_promotion_recomputes_positive_margin(self) -> None:
        promotion = self.load_promotion()
        ledger = build_upper_obstruction_ledger(promotion)
        self.assertTrue(ledger.upper_window_ordered)
        self.assertTrue(ledger.barrier_window_ordered)
        self.assertTrue(ledger.exported_gap_matches)
        self.assertGreater(ledger.recomputed_gap, 0.0)
        self.assertAlmostEqual(
            ledger.recomputed_gap,
            ledger.barrier_lo - ledger.upper_hi,
            places=14,
        )
        self.assertGreater(ledger.gap_minus_upper_width, 0.0)
        self.assertTrue(ledger.upper_audit_certified)

    def test_upper_obstruction_bundle_passes_fail_closed_validator(self) -> None:
        promotion = self.load_promotion()
        report = audit_upper_obstruction_from_promotion(promotion)
        self.assertEqual(report["status"], "passed")
        bundle = report["upper_audit"]
        failures = validate_proof_audit_bundle(bundle)
        self.assertEqual(failures, [])
        for name in [
            "analytic_incompatibility_certified",
            "supercritical_obstruction_locked",
            "support_geometry_certified",
            "tail_coherence_certified",
            "tail_stability_certified",
        ]:
            self.assertTrue(bundle["derived_booleans"][name]["value"], name)
            self.assertFalse(bundle["derived_booleans"][name]["trusted_as_input"], name)
            self.assertGreater(bundle["derived_booleans"][name]["margin"], 0.0, name)

    def test_theorem_iv_shell_can_be_built_from_upper_audit(self) -> None:
        promotion = self.load_promotion()
        report = audit_upper_obstruction_from_promotion(promotion)
        shell = build_theorem_iv_shell_from_audit(report["upper_audit"])
        self.assertTrue(shell["proof_audit_verified"])
        self.assertTrue(shell["analytic_incompatibility_certified"])
        self.assertTrue(shell["supercritical_obstruction_locked"])
        self.assertGreater(shell["analytic_incompatibility_margin"], 0.0)
        self.assertEqual(shell["upper_obstruction_tail_qs"], [144, 233])

    def test_tampered_upper_endpoint_fails(self) -> None:
        promotion = self.load_promotion()
        tampered = copy.deepcopy(promotion)
        tampered["certified_upper_hi"] = float(tampered["certified_barrier_lo"]) + 0.01
        tampered["certified_upper_width"] = tampered["certified_upper_hi"] - tampered["certified_upper_lo"]
        tampered["certified_gap"] = tampered["certified_barrier_lo"] - tampered["certified_upper_hi"]
        tampered["gap_to_localization_ratio"] = tampered["certified_gap"] / tampered["certified_upper_width"]
        report = audit_upper_obstruction_from_promotion(tampered)
        self.assertEqual(report["status"], "failed")
        self.assertIn("upper_not_below_barrier", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["upper_audit"])

    def test_trusted_boolean_is_rejected_even_with_good_numbers(self) -> None:
        promotion = self.load_promotion()
        bundle = build_upper_obstruction_audit_bundle(build_upper_obstruction_ledger(promotion)).to_dict()
        bundle["derived_booleans"]["analytic_incompatibility_certified"]["trusted_as_input"] = True
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(bundle)

    def test_tail_suffix_false_fails(self) -> None:
        promotion = self.load_promotion()
        tampered = copy.deepcopy(promotion)
        tampered["certified_tail_is_suffix"] = False
        report = audit_upper_obstruction_from_promotion(tampered)
        self.assertEqual(report["status"], "failed")
        self.assertIn("tail_coherence_not_certified", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["upper_audit"])

    def test_exported_gap_mismatch_fails(self) -> None:
        promotion = self.load_promotion()
        tampered = copy.deepcopy(promotion)
        tampered["certified_gap"] = float(tampered["certified_gap"]) + 1.0e-4
        report = audit_upper_obstruction_from_promotion(tampered)
        self.assertEqual(report["status"], "failed")
        self.assertIn("exported_gap_does_not_match_recomputed_gap", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["upper_audit"])


if __name__ == "__main__":
    unittest.main()
