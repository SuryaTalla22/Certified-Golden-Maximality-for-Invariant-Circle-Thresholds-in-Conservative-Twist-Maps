from __future__ import annotations

import copy
import unittest
from pathlib import Path

from kam_theorem_suite.audit.artifact_shell_builder import build_theorem_v_shell_from_audit
from kam_theorem_suite.audit.proof_bundle_validator import (
    ProofAuditValidationError,
    assert_proof_audit_bundle_valid,
    validate_proof_audit_bundle,
)
from kam_theorem_suite.audit.transport_budget import (
    audit_transport_budget,
    build_default_transport_input_payload,
    build_transport_budget_audit_bundle,
    build_transport_budget_ledger,
    run_margin_amplification_study,
)

ROOT = Path(__file__).resolve().parents[1]


class TransportBudgetAuditTests(unittest.TestCase):
    def test_default_transport_budget_recomputes_and_passes(self) -> None:
        payload = build_default_transport_input_payload()
        ledger = build_transport_budget_ledger(payload)
        self.assertTrue(ledger.target_interval_ordered)
        self.assertTrue(ledger.target_width_matches)
        self.assertTrue(ledger.total_matches_components)
        self.assertTrue(ledger.remaining_matches)
        self.assertTrue(ledger.margin_ratio_matches)
        self.assertGreater(ledger.remaining_margin, 0.0)
        self.assertGreater(ledger.margin_ratio, 1.0)
        self.assertTrue(ledger.ledger_certified)

    def test_transport_budget_bundle_passes_fail_closed_validator(self) -> None:
        report = audit_transport_budget(build_default_transport_input_payload())
        self.assertEqual(report["status"], "passed")
        bundle = report["transport_audit"]
        failures = validate_proof_audit_bundle(bundle)
        self.assertEqual(failures, [])
        for name in [
            "transport_component_budget_nonnegative",
            "transport_budget_ledger_complete",
            "transport_target_interval_certified",
            "compressed_contract_budget_exposed",
            "transport_gap_preservation_certified",
        ]:
            self.assertTrue(bundle["derived_booleans"][name]["value"], name)
            self.assertFalse(bundle["derived_booleans"][name]["trusted_as_input"], name)
            self.assertGreater(bundle["derived_booleans"][name]["margin"], 0.0, name)

    def test_theorem_v_shell_can_be_built_from_transport_audit(self) -> None:
        report = audit_transport_budget(build_default_transport_input_payload())
        shell = build_theorem_v_shell_from_audit(report["transport_audit"])
        self.assertTrue(shell["proof_audit_verified"])
        self.assertEqual(shell["theorem_status"], "golden-theorem-v-compressed-contract-strong")
        budget = shell["compressed_contract"]["uniform_majorant"]["budget"]
        self.assertGreater(budget["remaining_margin"], 0.0)
        self.assertGreater(budget["margin_ratio"], 1.0)
        self.assertFalse(shell["compressed_contract"]["raw_shell_consumed"])

    def test_budget_exceeding_gap_fails(self) -> None:
        payload = build_default_transport_input_payload()
        payload["available_gap"] = 1.0e-7
        report = audit_transport_budget(payload)
        self.assertEqual(report["status"], "failed")
        self.assertIn("transport_budget_exceeds_available_gap", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["transport_audit"])

    def test_trusted_gap_boolean_is_rejected(self) -> None:
        bundle = build_transport_budget_audit_bundle(build_transport_budget_ledger(build_default_transport_input_payload())).to_dict()
        bundle["derived_booleans"]["transport_gap_preservation_certified"]["trusted_as_input"] = True
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(bundle)

    def test_target_width_mismatch_fails(self) -> None:
        payload = build_default_transport_input_payload()
        payload["target_width"] = 1.0e-2
        report = audit_transport_budget(payload)
        self.assertEqual(report["status"], "failed")
        self.assertIn("target_width_export_mismatch", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["transport_audit"])

    def test_raw_shell_consumed_fails(self) -> None:
        payload = build_default_transport_input_payload()
        payload["raw_shell_consumed"] = True
        report = audit_transport_budget(payload)
        self.assertEqual(report["status"], "failed")
        self.assertIn("raw_shell_consumed", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["transport_audit"])

    def test_perturbed_component_sum_fails_validator(self) -> None:
        bundle = build_transport_budget_audit_bundle(build_transport_budget_ledger(build_default_transport_input_payload())).to_dict()
        bundle["derived_inequalities"]["total_matches_component_sum"]["lhs_value"] = 1.0
        # Keep the old stored margin to make sure the validator recomputes and notices.
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(bundle)

    def test_margin_amplification_study_is_diagnostic_and_improves_best(self) -> None:
        ledger = build_transport_budget_ledger(build_default_transport_input_payload())
        study = run_margin_amplification_study(ledger)
        self.assertFalse(study["theorem_facing"])
        self.assertGreater(study["best_remaining_margin"], study["baseline_remaining_margin"])
        self.assertIn("combined_aggressive", {row["strategy"] for row in study["rows"]})


if __name__ == "__main__":
    unittest.main()
