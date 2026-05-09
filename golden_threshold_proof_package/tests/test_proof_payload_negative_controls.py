from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from kam_theorem_suite.audit.proof_payload_validator import (
    recompute_interval_inequality,
    require_derived_boolean,
    validate_arithmetic_domain_payload,
    validate_gl2z_normalization_payload,
    validate_layer_payload,
    validate_transport_budget_payload,
    validate_upper_obstruction_payload,
    verify_no_trusted_final_booleans,
    verify_payload_hash_and_content,
)
from kam_theorem_suite.paper_replay_inputs import (
    PaperReplayValidationError,
    build_minimal_theorem_shells,
    validate_paper_replay_shells,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "artifacts/proof_audit"


def load_bundle(rel: str) -> dict:
    return json.loads((AUDIT / rel).read_text())


class Phase8ProofPayloadNegativeControls(unittest.TestCase):
    def test_upper_analytic_incompatibility_true_but_negative_margin_fails(self) -> None:
        bundle = load_bundle("upper_obstruction/upper_obstruction_audit.bundle.json")
        tampered = copy.deepcopy(bundle)
        # Preserve all status Booleans while moving the raw upper endpoint past the barrier.
        tampered["raw_interval_fields"]["certified_upper_interval"]["hi"] = (
            tampered["raw_interval_fields"]["certified_barrier_interval"]["lo"] + 1.0e-3
        )
        failures = validate_upper_obstruction_payload(tampered)
        codes = {f.code for f in failures}
        self.assertIn("upper-not-below-barrier", codes)
        self.assertIn("inequality-raw-lhs-mismatch", codes)

    def test_transport_gap_preservation_true_but_budget_exceeds_gap_fails(self) -> None:
        bundle = load_bundle("transport_budget/transport_budget_audit.bundle.json")
        tampered = copy.deepcopy(bundle)
        tampered["raw_symbolic_fields"]["ledger"]["total_charged"] = 2.0e-5
        tampered["raw_interval_fields"]["total_charged_interval"]["lo"] = 1.9e-5
        tampered["raw_interval_fields"]["total_charged_interval"]["hi"] = 2.1e-5
        failures = validate_transport_budget_payload(tampered)
        codes = {f.code for f in failures}
        self.assertIn("transport-budget-exceeds-gap", codes)
        self.assertIn("inequality-raw-lhs-mismatch", codes)

    def test_direct_lower_anchor_true_but_tampered_radii_lhs_fails(self) -> None:
        bundle = load_bundle("lower_corridor/lower_corridor_audit.bundle.json")
        tampered = copy.deepcopy(bundle)
        tampered["raw_symbolic_fields"]["selected_constants"]["radii_lhs_interval_upper"] = 1.0
        failures = validate_layer_payload(tampered, allow_known_lower_gap=False, require_lower_final_anchor=True)
        codes = {f.code for f in failures}
        self.assertIn("inequality-raw-lhs-mismatch", codes)
        self.assertIn("inequality-raw-margin-mismatch", codes)

    def test_domain_exhaustion_true_but_uncontrolled_record_fails(self) -> None:
        bundle = load_bundle("arithmetic_domain/arithmetic_domain_audit.bundle.json")
        tampered = copy.deepcopy(bundle)
        record = copy.deepcopy(tampered["raw_symbolic_fields"]["domain_records"][0])
        record.update({"label": "uncontrolled.synthetic", "verified": False, "route_valid": False, "has_control_certificate": False})
        tampered["raw_symbolic_fields"]["domain_records"].append(record)
        failures = validate_arithmetic_domain_payload(tampered)
        codes = {f.code for f in failures}
        self.assertIn("uncontrolled-domain-record", codes)
        self.assertIn("domain-boolean-contradicts-records", codes)

    def test_gl2z_normalization_true_but_duplicate_golden_representative_fails(self) -> None:
        bundle = load_bundle("gl2z_normalization/gl2z_normalization_audit.bundle.json")
        tampered = copy.deepcopy(bundle)
        tampered["raw_symbolic_fields"]["unique_representative_verification"]["duplicate_golden_representative_count"] = 1
        tampered["raw_symbolic_fields"]["unique_representative_verification"]["accepted_distinct_representative_count"] = 2
        failures = validate_gl2z_normalization_payload(tampered)
        codes = {f.code for f in failures}
        self.assertIn("duplicate-golden-representative", codes)
        self.assertIn("wrong-accepted-representative-count", codes)

    def test_preserved_status_strings_but_perturbed_raw_endpoint_fails(self) -> None:
        bundle = load_bundle("upper_obstruction/upper_obstruction_audit.bundle.json")
        self.assertTrue(bundle["derived_booleans"]["analytic_incompatibility_certified"]["value"])
        tampered = copy.deepcopy(bundle)
        tampered["raw_interval_fields"]["certified_barrier_interval"]["lo"] += 1.0e-2
        failures = validate_upper_obstruction_payload(tampered)
        self.assertTrue(any(f.code == "inequality-raw-rhs-mismatch" for f in failures))

    def test_removed_source_field_used_by_derived_inequality_fails(self) -> None:
        bundle = load_bundle("upper_obstruction/upper_obstruction_audit.bundle.json")
        tampered = copy.deepcopy(bundle)
        del tampered["raw_interval_fields"]["certified_upper_interval"]
        failures = validate_upper_obstruction_payload(tampered)
        codes = {f.code for f in failures}
        self.assertIn("unknown-source-field", codes)
        self.assertIn("missing-upper-intervals", codes)

    def test_diagnostic_artifact_with_same_endpoint_numbers_is_rejected(self) -> None:
        bundle = load_bundle("upper_obstruction/upper_obstruction_audit.bundle.json")
        tampered = copy.deepcopy(bundle)
        tampered["raw_interval_fields"]["certified_upper_interval"]["diagnostic_only"] = True
        failures = validate_upper_obstruction_payload(tampered)
        self.assertTrue(any(f.code == "diagnostic-theorem-interval" for f in failures))

    def test_core_phase8_primitives_accept_good_upper_payload(self) -> None:
        bundle = load_bundle("upper_obstruction/upper_obstruction_audit.bundle.json")
        require_derived_boolean(bundle, "analytic_incompatibility_certified")
        self.assertTrue(recompute_interval_inequality(bundle, "obstruction_separation"))
        verify_no_trusted_final_booleans(bundle)
        content = verify_payload_hash_and_content(bundle)
        self.assertEqual(content["theorem_layer"], "IV")
        self.assertEqual(len(content["sha256"]), 64)

    def test_final_replay_requires_embedded_payloads_in_proof_audit_mode(self) -> None:
        shells = build_minimal_theorem_shells()
        with self.assertRaises(PaperReplayValidationError):
            validate_paper_replay_shells(shells, require_proof_audit_payloads=True)

    def test_trusted_boolean_rejected_by_phase8_primitive(self) -> None:
        bundle = load_bundle("transport_budget/transport_budget_audit.bundle.json")
        tampered = copy.deepcopy(bundle)
        tampered["derived_booleans"]["transport_gap_preservation_certified"]["trusted_as_input"] = True
        with self.assertRaises(ValueError):
            verify_no_trusted_final_booleans(tampered)


if __name__ == "__main__":
    unittest.main()
