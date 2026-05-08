from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_closure import (
    LowerAnchorClosureError,
    anchor_candidate_template,
    build_anchor_closure_audit,
    build_synthetic_anchor_candidate_for_tests,
    load_lower_corridor_bundle,
    segment_from_candidate_row,
    write_anchor_closure_outputs,
)
from kam_theorem_suite.audit.proof_payload_validator import validate_lower_corridor_payload

ROOT = Path(__file__).resolve().parents[1]
LOWER_BUNDLE = ROOT / "artifacts/proof_audit/lower_corridor/lower_corridor_audit.bundle.json"


class Phase2BLowerAnchorClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lower = load_lower_corridor_bundle(LOWER_BUNDLE)

    def test_no_candidate_fails_closed_without_claiming_final_anchor(self) -> None:
        segments, candidate_validation, verification, bundle = build_anchor_closure_audit(self.lower)
        self.assertFalse(candidate_validation.candidate_present)
        self.assertFalse(verification.final_anchor_reached)
        self.assertIn("anchor_candidate_missing", bundle.failure_fields)
        failures = validate_lower_corridor_payload(bundle, require_final_anchor=True, allow_known_lower_gap=True)
        # The known lower-gap allowance removes only the final-anchor failures; a
        # missing candidate remains documented in the Phase-2B bundle but does
        # not create stale positive theorem Booleans.
        self.assertFalse(bundle.derived_booleans["final_anchor_reached"].value)
        self.assertTrue(all(f.code != "segment-margin-mismatch" for f in failures))

    def test_synthetic_theorem_shaped_candidate_passes_in_temp_only(self) -> None:
        candidate = build_synthetic_anchor_candidate_for_tests()
        segments, candidate_validation, verification, bundle = build_anchor_closure_audit(
            self.lower,
            anchor_candidate=candidate,
            anchor_candidate_path="tests/synthetic_lower_anchor_candidate.json",
        )
        self.assertTrue(candidate_validation.candidate_present)
        self.assertTrue(candidate_validation.anchor_chain_linked_to_existing_corridor)
        self.assertTrue(verification.final_anchor_reached)
        self.assertTrue(verification.lower_chain_verified)
        self.assertEqual(bundle.failure_fields, [])
        self.assertEqual(validate_lower_corridor_payload(bundle, require_final_anchor=True), [])
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report = write_anchor_closure_outputs(
                segments=segments,
                candidate_validation=candidate_validation,
                verification=verification,
                bundle=bundle,
                out_json=tmp_path / "audit.json",
                out_bundle=tmp_path / "audit.bundle.json",
                out_csv=tmp_path / "segments.csv",
                out_tex=tmp_path / "segments.tex",
            )
            self.assertEqual(report["status"], "passed")
            self.assertTrue((tmp_path / "audit.bundle.json").exists())
            self.assertTrue((tmp_path / "segments.csv").exists())

    def test_candidate_starting_after_existing_corridor_is_rejected(self) -> None:
        candidate = build_synthetic_anchor_candidate_for_tests(start=0.90)
        _segments, candidate_validation, verification, bundle = build_anchor_closure_audit(
            self.lower,
            anchor_candidate=candidate,
            anchor_candidate_path="tests/gapped_candidate.json",
        )
        self.assertFalse(candidate_validation.anchor_chain_linked_to_existing_corridor)
        self.assertIn("anchor_failed_links", bundle.failure_fields)
        self.assertFalse(verification.lower_chain_verified)
        self.assertTrue(validate_lower_corridor_payload(bundle, require_final_anchor=True))

    def test_diagnostic_candidate_is_rejected_even_if_numerically_shaped(self) -> None:
        candidate = build_synthetic_anchor_candidate_for_tests(diagnostic_only=True)
        _segments, candidate_validation, verification, bundle = build_anchor_closure_audit(
            self.lower,
            anchor_candidate=candidate,
            anchor_candidate_path="tests/diagnostic_candidate.json",
        )
        self.assertTrue(candidate_validation.candidate_diagnostic_only)
        self.assertIn("anchor_candidate_diagnostic_only", bundle.failure_fields)
        self.assertFalse(bundle.derived_booleans["lower_anchor_closure_candidate_verified"].value)
        self.assertTrue(validate_lower_corridor_payload(bundle, require_final_anchor=True))

    def test_stale_candidate_margin_is_rejected_at_ingestion(self) -> None:
        candidate = build_synthetic_anchor_candidate_for_tests()
        bad = copy.deepcopy(candidate["anchor_segments"][0])
        bad["radii_margin"] = float(bad["radii_margin"]) + 1.0e-3
        with self.assertRaises(LowerAnchorClosureError):
            segment_from_candidate_row(bad, source_artifact="tests/bad_margin.json")

    def test_template_is_diagnostic_and_not_theorem_facing(self) -> None:
        template = anchor_candidate_template()
        self.assertFalse(template["theorem_facing"])
        self.assertTrue(template["diagnostic_only"])
        self.assertIn("anchor_segments", template)
        self.assertFalse(template["anchor_segments"][0]["certified"])


if __name__ == "__main__":
    unittest.main()
