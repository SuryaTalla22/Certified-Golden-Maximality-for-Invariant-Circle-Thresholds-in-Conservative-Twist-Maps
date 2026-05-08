from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_phase2k_rescue_execution import (
    build_merged_rescued_candidate,
    collect_successful_rescue_rows,
    execute_rescue_variants,
    row_is_theorem_ready,
)


def ready_row(segment_id: str, lo: float, hi: float, margin: float = 1.0e-8) -> dict:
    r = 1.0e-6
    y = 1.0e-8
    z = 1.0e-3
    # Choose T so recomputed margin is the requested value.
    t = r - (y + z * r + margin)
    return {
        "segment_id": segment_id,
        "K_lo": lo,
        "K_hi": hi,
        "K_mid": 0.5 * (lo + hi),
        "rho": 0.6180339887498949,
        "N": 64,
        "sigma": 0.001,
        "residual_Y": y,
        "linear_defect_Z": z,
        "tail_bound_T": t,
        "radius_r": r,
        "radii_margin": margin,
        "small_divisor_min": 0.1,
        "small_divisor_inverse_bound": 10.0,
        "closure_level": "analytic_theorem_closure",
        "certified": True,
        "theorem_ready": True,
        "finite_dimensional_only": False,
        "source_module": "unit_test",
        "source_artifact": "unit_test.json",
    }


class Phase2KRescueExecutionTests(unittest.TestCase):
    def test_row_is_theorem_ready_recomputes_margin(self) -> None:
        row = ready_row("s", 0.0, 1.0)
        self.assertTrue(row_is_theorem_ready(row))
        row["tail_bound_T"] = 2.0
        self.assertFalse(row_is_theorem_ready(row))

    def test_collect_successful_rescue_rows_and_parent_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rescue = root / "rescue"
            rescue.mkdir()
            atlas = {
                "failed_rows": [{"segment_id": "parent", "K_lo": 1.0, "K_hi": 3.0}],
                "rescue_variants": [
                    {"variant_id": "a", "parent_segment_id": "parent", "candidate_name": "a_candidate.json", "command": []},
                    {"variant_id": "b", "parent_segment_id": "parent", "candidate_name": "b_candidate.json", "command": []},
                ],
            }
            atlas_path = root / "atlas.json"
            atlas_path.write_text(json.dumps(atlas))
            (rescue / "a_candidate.json").write_text(json.dumps({"anchor_segments": [ready_row("parent_phase2j_sub00", 1.0, 2.1)]}))
            (rescue / "b_candidate.json").write_text(json.dumps({"anchor_segments": [ready_row("parent_phase2j_sub01", 2.0, 3.0)]}))
            rows, coverages = collect_successful_rescue_rows(atlas_path=atlas_path, rescue_dir=rescue)
            self.assertEqual(len(rows), 2)
            self.assertEqual(len(coverages), 1)
            self.assertTrue(coverages[0].coverage_complete)
            self.assertEqual(coverages[0].gaps, tuple())

    def test_build_merged_candidate_stays_fail_closed_when_parent_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rescue = root / "rescue"
            rescue.mkdir()
            atlas = {
                "failed_rows": [{"segment_id": "parent", "K_lo": 1.0, "K_hi": 3.0}],
                "rescue_variants": [
                    {"variant_id": "a", "parent_segment_id": "parent", "candidate_name": "a_candidate.json", "command": []},
                ],
            }
            atlas_path = root / "atlas.json"
            atlas_path.write_text(json.dumps(atlas))
            prefix = root / "prefix.json"
            prefix.write_text(json.dumps({"anchor_segments": [ready_row("prefix", 0.0, 1.1)]}))
            (rescue / "a_candidate.json").write_text(json.dumps({"anchor_segments": [ready_row("parent_phase2j_sub00", 1.0, 2.0)]}))
            merged, coverages = build_merged_rescued_candidate(
                atlas_path=atlas_path,
                rescue_dir=rescue,
                prefix_candidate_paths=[prefix],
                final_anchor=(2.9, 3.0),
            )
            self.assertFalse(merged["promotion_allowed"])
            self.assertIn("phase2k_unrescued_parent_segments", merged["failure_fields"])
            self.assertFalse(coverages[0].coverage_complete)

    def test_execute_variants_summarizes_existing_without_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rescue = root / "rescue"
            rescue.mkdir()
            atlas = {
                "rescue_variants": [
                    {"variant_id": "a", "parent_segment_id": "p", "rescue_segment_id": "p_sub", "candidate_name": "a_candidate.json", "command": ["python", "-c", "raise SystemExit(99)"]},
                ]
            }
            atlas_path = root / "atlas.json"
            atlas_path.write_text(json.dumps(atlas))
            (rescue / "a_candidate.json").write_text(json.dumps({"anchor_segments": [ready_row("p_sub", 1.0, 2.0)]}))
            executions = execute_rescue_variants(atlas_path=atlas_path, repo_root=root, rescue_dir=rescue, log_dir=root / "logs")
            self.assertEqual(len(executions), 1)
            self.assertTrue(executions[0].skipped_existing)
            self.assertFalse(executions[0].attempted)
            self.assertEqual(executions[0].theorem_ready_row_count, 1)


if __name__ == "__main__":
    unittest.main()
