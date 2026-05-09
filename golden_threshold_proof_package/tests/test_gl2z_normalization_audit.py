from __future__ import annotations

import copy
import unittest

from kam_theorem_suite.audit.artifact_shell_builder import build_theorem_viii_gl2z_shell_from_audit
from kam_theorem_suite.audit.gl2z_normalization_audit import (
    GL2ZCandidate,
    build_gl2z_normalization_audit,
    default_Dnorm,
    enumerate_representative_candidates,
    verify_no_analytic_conjugacy_claim,
    verify_unique_golden_representative,
)
from kam_theorem_suite.audit.proof_bundle_validator import (
    ProofAuditValidationError,
    assert_proof_audit_bundle_valid,
    validate_proof_audit_bundle,
)
from kam_theorem_suite.audit.arithmetic_domain_grammar import default_certified_universe


class GL2ZNormalizationAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = default_certified_universe()

    def test_default_gl2z_audit_passes_fail_closed_validator(self) -> None:
        report = build_gl2z_normalization_audit(self.universe, bound=2)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["certified"])
        self.assertFalse(report["analytic_conjugacy_claimed"])
        self.assertTrue(report["golden_orbit_representative_unique_in_Dnorm"])
        self.assertEqual(report["accepted_distinct_representative_count"], 1)
        self.assertEqual(report["accepted_distinct_nongolden_count"], 0)
        self.assertEqual(report["duplicate_golden_representative_count"], 0)
        self.assertEqual(validate_proof_audit_bundle(report["gl2z_audit"]), [])
        for name in [
            "representative_selection_convention_certified",
            "golden_orbit_representative_unique_in_Dnorm",
            "no_analytic_conjugacy_claim_used",
            "gl2z_normalization_certified",
        ]:
            boolean = report["gl2z_audit"]["derived_booleans"][name]
            self.assertTrue(boolean["value"], name)
            self.assertFalse(boolean["trusted_as_input"], name)
            self.assertGreater(boolean["margin"], 0.0, name)

    def test_enumerated_candidates_have_gl2z_determinant(self) -> None:
        candidates = enumerate_representative_candidates(default_Dnorm(self.universe), bound=2)
        self.assertGreater(len(candidates), 0)
        for row in candidates:
            a, b, c, d = row["matrix"]
            self.assertIn(a * d - b * c, (-1, 1))
        verification = verify_unique_golden_representative(candidates, default_Dnorm(self.universe))
        self.assertTrue(verification["certified"])
        self.assertEqual(verification["accepted_distinct_representative_count"], 1)

    def test_changing_representative_convention_fails(self) -> None:
        universe = copy.deepcopy(self.universe)
        universe.setdefault("normalization", {})["convention"] = "unreduced-projective-orbit-all-representatives"
        universe["normalization"]["representative_rule"] = "unreduced-projective-orbit-all-representatives"
        report = build_gl2z_normalization_audit(universe, bound=2)
        self.assertEqual(report["status"], "failed")
        self.assertIn("representative_rule_not_certified_positive_reduced_cf", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["gl2z_audit"])

    def test_duplicating_distinct_golden_representative_fails(self) -> None:
        candidates = enumerate_representative_candidates(default_Dnorm(self.universe), bound=2)
        duplicate = GL2ZCandidate(
            matrix=(1, 1, 0, 1),
            determinant=1,
            representative_value=0.7,
            in_numeric_domain=True,
            accepted_by_Dnorm=True,
            canonical_golden=False,
            representative_label="bad-accepted-nongolden-duplicate",
            source="negative-control",
        ).to_dict()
        report = build_gl2z_normalization_audit(self.universe, candidates=candidates + [duplicate], bound=2)
        self.assertEqual(report["status"], "failed")
        self.assertIn("nongolden_representative_accepted_in_Dnorm", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["gl2z_audit"])

    def test_claiming_analytic_conjugacy_outside_dnorm_fails(self) -> None:
        universe = copy.deepcopy(self.universe)
        universe.setdefault("normalization", {})["analytic_conjugacy_claimed"] = True
        universe["normalization"]["claimed_analytic_conjugacy_outside_Dnorm"] = True
        check = verify_no_analytic_conjugacy_claim(universe)
        self.assertFalse(check["certified"])
        self.assertIn("analytic_conjugacy_claimed", check["failure_fields"])
        self.assertIn("analytic_conjugacy_claimed_outside_Dnorm", check["failure_fields"])
        report = build_gl2z_normalization_audit(universe, bound=2)
        self.assertEqual(report["status"], "failed")
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["gl2z_audit"])

    def test_final_reduction_shell_requires_no_analytic_conjugacy_claim(self) -> None:
        report = build_gl2z_normalization_audit(self.universe, bound=2)
        shell = build_theorem_viii_gl2z_shell_from_audit(report["gl2z_audit"])
        self.assertTrue(shell["proof_audit_verified"])
        self.assertEqual(shell["normalization_type"], "representative_selection")
        self.assertFalse(shell["analytic_conjugacy_claimed"])
        self.assertTrue(shell["proves_gl2z_orbit_uniqueness_and_normalization_closed"])

        bad = copy.deepcopy(report["gl2z_audit"])
        bad["shell_payload"]["analytic_conjugacy_claimed"] = True
        with self.assertRaises(ProofAuditValidationError):
            build_theorem_viii_gl2z_shell_from_audit(bad)

    def test_status_string_without_raw_dependencies_fails(self) -> None:
        report = build_gl2z_normalization_audit(self.universe, bound=2)
        bad = copy.deepcopy(report["gl2z_audit"])
        bad["derived_booleans"]["gl2z_normalization_certified"]["derived_from"] = []
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(bad)


if __name__ == "__main__":
    unittest.main()
