from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_closure import build_anchor_closure_audit, load_lower_corridor_bundle
from kam_theorem_suite.audit.lower_anchor_heavy_certificate import (
    HeavyLowerAnchorConfig,
    build_adaptive_near_anchor_grid,
    build_heavy_candidate_json,
    build_modewise_golden_small_divisor_summary,
    refine_grid_by_margins,
    run_heavy_lower_anchor_certificate,
    write_heavy_lower_anchor_outputs,
)
from kam_theorem_suite.audit.proof_payload_validator import validate_lower_corridor_payload

ROOT = Path(__file__).resolve().parents[1]
LOWER_BUNDLE = ROOT / "artifacts/proof_audit/lower_corridor/lower_corridor_audit.bundle.json"


class _MockCert:
    def __init__(self, *, margin: float, status: str = "analytic-torus-bridge-strong", N: int = 64):
        self.payload = {
            "N": N,
            "finite_dimensional_success": True,
            "finite_radius": 1.0e-6,
            "finite_eta": 1.0e-12,
            "finite_B_norm": 10.0,
            "finite_lipschitz_bound": 2.0,
            "finite_radii_margin": 9.9999e-7,
            "theorem_status": status,
            "theorem_margin": margin,
            "cohomological_correction_bound": 1.0e-8,
            "tail_bound": {"tail_l1": 1.0e-12},
            "cohomological_inverse_bound": 10.0,
            "weighted_residual_l1": 1.0e-10,
            "relative_correction_to_graph": 1.0e-5,
        }

    def to_dict(self) -> dict:
        return dict(self.payload)


def _builder_success(**kwargs):
    return _MockCert(margin=5.0e-7, N=max(kwargs.get("N_values", (64,))))


def _builder_failure(**kwargs):
    return _MockCert(margin=-1.0e-6, status="analytic-torus-bridge-weak", N=max(kwargs.get("N_values", (64,))))


class HeavyLowerAnchorCertificateTests(unittest.TestCase):
    def test_adaptive_grid_reaches_anchor_and_refines_near_critical_region(self) -> None:
        grid = build_adaptive_near_anchor_grid(start_K=0.265, final_anchor_hi=0.971636, overlap=1e-7)
        self.assertGreaterEqual(len(grid), 8)
        self.assertLessEqual(grid[0][0], 0.265)
        self.assertGreaterEqual(grid[-1][1], 0.971636)
        self.assertLess(grid[-1][1] - grid[-1][0], grid[0][1] - grid[0][0])
        for a, b in zip(grid, grid[1:]):
            self.assertGreater(a[1] - b[0], 0.0)

    def test_margin_refinement_bisects_weak_segments(self) -> None:
        grid = [(0.0, 1.0, 0.5), (1.0, 2.0, 1.5)]
        refined = refine_grid_by_margins(grid, {0.5: -1.0, 1.5: 1.0}, threshold=0.0, levels=1, overlap=1e-6)
        self.assertEqual(len(refined), 3)
        self.assertAlmostEqual(refined[0][2], 0.25)
        self.assertAlmostEqual(refined[1][2], 0.75)
        self.assertAlmostEqual(refined[2][2], 1.5)

    def test_modewise_small_divisor_summary_is_positive(self) -> None:
        summary = build_modewise_golden_small_divisor_summary(16)
        self.assertTrue(summary.certified)
        self.assertGreater(summary.min_exact_gap, 0.0)
        self.assertGreater(summary.max_inverse_multiplier, 0.0)
        self.assertEqual(summary.lower_bound_failures, tuple())

    def test_successful_mock_generates_promotable_phase2b_shaped_candidate(self) -> None:
        cfg = HeavyLowerAnchorConfig(max_segments=2, N_values=(16, 32), theorem_margin_safety_factor=1.0, outward_rounding_tolerance=1e-12)
        report = run_heavy_lower_anchor_certificate(cfg, certificate_builder=_builder_success)
        self.assertFalse(report.promotion_allowed)  # max_segments intentionally does not reach the final anchor
        cfg_full = HeavyLowerAnchorConfig(N_values=(16, 32), theorem_margin_safety_factor=1.0, outward_rounding_tolerance=1e-12)
        report_full = run_heavy_lower_anchor_certificate(cfg_full, certificate_builder=_builder_success)
        self.assertTrue(report_full.promotion_allowed)
        cand = build_heavy_candidate_json(report_full, source_artifact="tests/heavy_candidate.json")
        self.assertTrue(cand["theorem_facing"])
        self.assertFalse(cand["diagnostic_only"])
        for row in cand["anchor_segments"]:
            self.assertFalse(row["finite_dimensional_only"])
            self.assertGreater(row["radii_margin"], 0.0)

    def test_failed_mock_remains_diagnostic_and_phase2b_rejects_it(self) -> None:
        cfg = HeavyLowerAnchorConfig(N_values=(16, 32), theorem_margin_safety_factor=1.0, outward_rounding_tolerance=1e-12)
        report = run_heavy_lower_anchor_certificate(cfg, certificate_builder=_builder_failure)
        self.assertFalse(report.promotion_allowed)
        cand = build_heavy_candidate_json(report, source_artifact="tests/heavy_candidate.json")
        self.assertTrue(cand["diagnostic_only"])
        lower = load_lower_corridor_bundle(LOWER_BUNDLE)
        _segments, candidate_validation, verification, bundle = build_anchor_closure_audit(
            lower,
            anchor_candidate=cand,
            anchor_candidate_path="tests/heavy_candidate.json",
        )
        self.assertTrue(candidate_validation.candidate_diagnostic_only)
        self.assertFalse(verification.lower_chain_verified)
        self.assertIn("anchor_candidate_diagnostic_only", bundle.failure_fields)
        self.assertTrue(validate_lower_corridor_payload(bundle, require_final_anchor=True))

    def test_outputs_are_written(self) -> None:
        cfg = HeavyLowerAnchorConfig(max_segments=1, dry_run=True)
        report = run_heavy_lower_anchor_certificate(cfg)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary = write_heavy_lower_anchor_outputs(report, out_dir=tmp_path / "artifacts", table_dir=tmp_path / "tables")
            self.assertTrue(Path(summary["candidate_path"]).exists())
            self.assertTrue(Path(summary["report_path"]).exists())
            self.assertTrue(Path(summary["csv_path"]).exists())
            self.assertTrue(Path(summary["tex_path"]).exists())


if __name__ == "__main__":
    unittest.main()
