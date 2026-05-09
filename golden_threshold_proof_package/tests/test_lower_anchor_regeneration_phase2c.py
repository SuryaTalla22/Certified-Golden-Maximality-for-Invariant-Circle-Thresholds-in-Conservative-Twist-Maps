from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_closure import build_anchor_closure_audit, load_lower_corridor_bundle
from kam_theorem_suite.audit.lower_anchor_regeneration import (
    LowerAnchorRegenerationConfig,
    LowerAnchorValidationRecord,
    build_candidate_json,
    build_mock_regeneration_report,
    build_overlapping_grid,
    write_regeneration_outputs,
)
from kam_theorem_suite.audit.proof_payload_validator import validate_lower_corridor_payload

ROOT = Path(__file__).resolve().parents[1]
LOWER_BUNDLE = ROOT / "artifacts/proof_audit/lower_corridor/lower_corridor_audit.bundle.json"


def _record(idx: int, *, theorem_ready: bool = False, analytic_margin: float | None = None) -> dict:
    K_lo = 0.265 + idx * 0.36
    K_hi = 0.625 + idx * 0.36
    return LowerAnchorValidationRecord(
        segment_id=f"mock_{idx}",
        K_lo=K_lo,
        K_hi=K_hi,
        K_mid=0.5 * (K_lo + K_hi),
        N=16,
        finite_success=True,
        eta=1.0e-14,
        B_norm=10.0,
        lipschitz_bound=2.0,
        radius_r=1.0e-8,
        finite_radii_margin=9.999e-9,
        contraction_bound=2.0e-7,
        residual_inf=1.0e-14,
        residual_l2=1.0e-13,
        oversampled_residual_inf=1.0e-12,
        fourier_tail_l2=1.0e-10,
        bridge_quality="weak",
        solver_iterations=4,
        elapsed_seconds=0.01,
        analytic_probe_attempted=analytic_margin is not None,
        analytic_theorem_status="analytic-torus-bridge-strong" if theorem_ready else "analytic-torus-bridge-weak",
        analytic_theorem_margin=analytic_margin,
        closure_level="analytic_theorem_closure" if theorem_ready else "finite_dimensional_collocation_only",
        theorem_ready=theorem_ready,
        failure_reasons=[] if theorem_ready else ["not_theorem_ready"],
    ).to_dict()


class Phase2CLowerAnchorRegenerationTests(unittest.TestCase):
    def test_grid_reaches_anchor_and_overlaps(self) -> None:
        grid = build_overlapping_grid(start_K=0.265, final_anchor_hi=0.971636, n_segments=4, overlap=1e-6)
        self.assertEqual(len(grid), 4)
        self.assertLessEqual(grid[0][0], 0.265)
        self.assertGreaterEqual(grid[-1][1], 0.971636)
        for a, b in zip(grid, grid[1:]):
            self.assertGreater(a[1] - b[0], 0.0)

    def test_mock_finite_candidate_is_diagnostic_and_not_promotable(self) -> None:
        cfg = LowerAnchorRegenerationConfig(n_segments=2)
        report = build_mock_regeneration_report([_record(0), _record(1)], cfg)
        self.assertFalse(report.theorem_facing)
        self.assertTrue(report.diagnostic_only)
        self.assertFalse(report.promotion_allowed)
        self.assertIn("analytic_theorem_closure_not_established_for_all_segments", report.failure_fields)
        cand = build_candidate_json(report, source_artifact="tests/mock_candidate.json")
        self.assertTrue(cand["diagnostic_only"])
        self.assertFalse(cand["theorem_facing"])

    def test_diagnostic_candidate_is_rejected_by_phase2b_ingestion(self) -> None:
        lower = load_lower_corridor_bundle(LOWER_BUNDLE)
        cfg = LowerAnchorRegenerationConfig(n_segments=2)
        report = build_mock_regeneration_report([_record(0), _record(1)], cfg)
        cand = build_candidate_json(report, source_artifact="tests/mock_candidate.json")
        _segments, candidate_validation, verification, bundle = build_anchor_closure_audit(
            lower,
            anchor_candidate=cand,
            anchor_candidate_path="tests/mock_candidate.json",
        )
        self.assertTrue(candidate_validation.candidate_diagnostic_only)
        self.assertIn("anchor_candidate_diagnostic_only", bundle.failure_fields)
        self.assertFalse(verification.lower_chain_verified)
        self.assertTrue(validate_lower_corridor_payload(bundle, require_final_anchor=True))

    def test_theorem_ready_mock_can_be_shaped_but_requires_explicit_positive_analytic_margins(self) -> None:
        cfg = LowerAnchorRegenerationConfig(n_segments=2)
        report = build_mock_regeneration_report([_record(0, theorem_ready=True, analytic_margin=1e-6), _record(1, theorem_ready=True, analytic_margin=2e-6)], cfg)
        self.assertTrue(report.theorem_facing)
        self.assertTrue(report.promotion_allowed)
        cand = build_candidate_json(report, source_artifact="tests/mock_ready_candidate.json")
        self.assertTrue(cand["theorem_facing"])
        self.assertFalse(cand["diagnostic_only"])

    def test_outputs_are_written(self) -> None:
        cfg = LowerAnchorRegenerationConfig(n_segments=2)
        report = build_mock_regeneration_report([_record(0), _record(1)], cfg)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary = write_regeneration_outputs(report, out_dir=tmp_path / "artifacts", table_dir=tmp_path / "tables", fig_dir=None)
            self.assertTrue(Path(summary["candidate_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).exists())
            self.assertTrue(Path(summary["csv_path"]).exists())
            self.assertTrue(Path(summary["tex_path"]).exists())


if __name__ == "__main__":
    unittest.main()
