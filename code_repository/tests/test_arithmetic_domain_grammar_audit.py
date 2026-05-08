from __future__ import annotations

import copy
import unittest
from pathlib import Path

from kam_theorem_suite.audit.arithmetic_domain_grammar import (
    GrammarRecord,
    build_default_theorem_vii_support,
    build_domain_exhaustion_audit,
    default_certified_universe,
    extract_generated_domain,
    run_nonvacuous_omitted_tail_study,
    verify_domain_partition,
    verify_no_uncontrolled_records,
)
from kam_theorem_suite.audit.artifact_shell_builder import build_theorem_vii_shell_from_audit
from kam_theorem_suite.audit.proof_bundle_validator import (
    ProofAuditValidationError,
    assert_proof_audit_bundle_valid,
    validate_proof_audit_bundle,
)
from kam_theorem_suite.paper_replay_inputs import build_minimal_theorem_shells, validate_paper_replay_shells


class ArithmeticDomainGrammarAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = default_certified_universe()
        self.support = build_default_theorem_vii_support(self.universe)

    def test_every_generated_record_has_route_and_control_certificate(self) -> None:
        records = extract_generated_domain(self.universe, self.support)
        self.assertGreater(len(records), 0)
        for record in records:
            self.assertTrue(record.route)
            self.assertTrue(record.route_valid, record.to_dict())
            self.assertTrue(record.has_control_certificate, record.to_dict())
            self.assertTrue(record.verified, record.to_dict())
        verification = verify_domain_partition(records)
        self.assertTrue(verification["partition_verified"])
        self.assertEqual(verification["missing_required_ranked_labels"], [])

    def test_default_domain_audit_passes_fail_closed_validator(self) -> None:
        report = build_domain_exhaustion_audit(self.universe, self.support)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["domain_grammar_generated_pre_conclusion"])
        self.assertEqual(report["uncontrolled_count"], 0)
        self.assertTrue(report["failure_fields_empty"])
        self.assertEqual(report["omitted_tail_status"], "vacuous_with_empty_complement")
        self.assertEqual(validate_proof_audit_bundle(report["domain_audit"]), [])
        self.assertTrue(report["domain_audit"]["derived_booleans"]["domain_exhaustion_certified"]["value"])
        self.assertFalse(report["domain_audit"]["derived_booleans"]["domain_exhaustion_certified"]["trusted_as_input"])

    def test_theorem_vii_shell_can_be_built_from_domain_audit(self) -> None:
        report = build_domain_exhaustion_audit(self.universe, self.support)
        shell = build_theorem_vii_shell_from_audit(report["domain_audit"])
        self.assertTrue(shell["proof_audit_verified"])
        self.assertEqual(shell["current_near_top_exhaustion_pending_count"], 0)
        self.assertGreater(shell["current_near_top_exhaustion_margin"], 0.0)
        self.assertIn("domain_grammar_records", shell)

        shells = list(build_minimal_theorem_shells())
        shells[6] = shell
        validate_paper_replay_shells(tuple(shells), require_cached_upstream=False)

    def test_adding_uncontrolled_record_fails(self) -> None:
        records = extract_generated_domain(self.universe, self.support)
        records.append(
            GrammarRecord(
                label="uncontrolled-extra-record",
                cf_pattern="[0;9,*]",
                eta_interval=(0.1, 0.2),
                generation_rule="manual-negative-control",
                route="pruned",
                control_certificate="",
                upper_ceiling=None,
                lower_reference=None,
                margin=None,
                certified=False,
            )
        )
        report = build_domain_exhaustion_audit(self.universe, self.support, records=records)
        self.assertEqual(report["status"], "failed")
        self.assertIn("uncontrolled_generated_records", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["domain_audit"])

    def test_removing_silver_or_bronze_from_ranking_fails(self) -> None:
        support = copy.deepcopy(self.support)
        ranking = support["support_certificates"]["exact_near_top_lagrange_spectrum_ranking_certificate"]
        ranking["ranking_records"] = [row for row in ranking["ranking_records"] if row["class_label"] != "bronze"]
        ranking["theorem_level_ranked_labels"] = ["silver"]
        report = build_domain_exhaustion_audit(self.universe, support)
        self.assertEqual(report["status"], "failed")
        self.assertIn("required_near_top_ranked_label_missing", report["failure_fields"])
        self.assertIn("bronze", report["partition_verification"]["missing_required_ranked_labels"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["domain_audit"])

    def test_nonempty_omitted_labels_without_envelope_control_fail(self) -> None:
        support = copy.deepcopy(self.support)
        omitted = support["support_certificates"]["omitted_class_global_control_certificate"]
        omitted["status"] = "omitted-class-global-control-frontier"
        omitted["omitted_labels"] = ["uncertified-tail-cylinder"]
        omitted["control_records"] = [
            {
                "class_label": "uncertified-tail-cylinder",
                "cf_pattern": "[0;5,*]",
                "control_source": "negative-control-no-envelope-margin",
            }
        ]
        support["omitted_tail_complement_empty"] = False
        report = build_domain_exhaustion_audit(self.universe, support)
        self.assertEqual(report["status"], "failed")
        self.assertIn("uncontrolled_omitted_labels", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["domain_audit"])

    def test_empty_omitted_tail_requires_explicit_empty_complement(self) -> None:
        support = copy.deepcopy(self.support)
        omitted = support["support_certificates"]["omitted_class_global_control_certificate"]
        omitted["status"] = "omitted-class-global-control-frontier"
        omitted["omitted_tail_complement_empty"] = False
        omitted["control_records"] = []
        support["omitted_tail_complement_empty"] = False
        report = build_domain_exhaustion_audit(self.universe, support)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["omitted_tail_status"], "vacuous_without_explicit_empty_complement")
        with self.assertRaises(ProofAuditValidationError):
            assert_proof_audit_bundle_valid(report["domain_audit"])

    def test_empty_failure_lists_alone_do_not_make_domain_audit_valid(self) -> None:
        records: list[GrammarRecord] = []
        report = build_domain_exhaustion_audit(self.universe, self.support, records=records)
        self.assertEqual(report["status"], "failed")
        self.assertIn("no_generated_records", report["failure_fields"])
        with self.assertRaises(ProofAuditValidationError):
            build_theorem_vii_shell_from_audit(report["domain_audit"])

    def test_nonvacuous_omitted_tail_study_is_diagnostic_not_theorem_facing(self) -> None:
        study = run_nonvacuous_omitted_tail_study(self.universe)
        self.assertTrue(study["certified"])
        self.assertFalse(study["theorem_facing"])
        self.assertTrue(study["promotion_required_before_theorem_use"])
        self.assertGreater(study["margin"], 0.0)


if __name__ == "__main__":
    unittest.main()
