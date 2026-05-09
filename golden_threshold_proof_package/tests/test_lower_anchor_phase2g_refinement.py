from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_phase2g_refinement import (
    build_phase2g_refinement_plan,
    classify_segment,
    recompute_radii_margin,
    write_phase2g_refinement_outputs,
)


def _ready_row(segment_id: str, lo: float, hi: float) -> dict:
    return {
        "segment_id": segment_id,
        "K_lo": lo,
        "K_hi": hi,
        "K_mid": 0.5 * (lo + hi),
        "rho": 0.618,
        "N": 64,
        "residual_Y": 1.0e-8,
        "linear_defect_Z": 0.01,
        "tail_bound_T": 1.0e-8,
        "radius_r": 1.0e-4,
        "radii_margin": 9.897e-5,
        "certified": True,
        "theorem_ready": True,
        "finite_success": True,
        "finite_dimensional_only": False,
        "closure_level": "analytic_theorem_closure",
    }


class Phase2GRefinementTests(unittest.TestCase):
    def test_margin_recomputed_from_raw_terms(self) -> None:
        row = _ready_row("s", 0.0, 0.1)
        margin = recompute_radii_margin(row)
        self.assertIsNotNone(margin)
        self.assertGreater(margin, 0.0)
        diag = classify_segment(row)
        self.assertEqual(diag.failure_type, "ready")
        self.assertTrue(diag.theorem_ready)

    def test_analytic_margin_failure_is_subdivided_and_escalated(self) -> None:
        row = _ready_row("bad", 0.9714, 0.971636)
        row.update({
            "residual_Y": 8.0e-5,
            "tail_bound_T": 4.0e-5,
            "radii_margin": -2.1e-5,
            "theorem_ready": False,
            "certified": False,
            "failure_reasons": ["analytic_radii_margin_not_safely_positive"],
        })
        plan = build_phase2g_refinement_plan({"anchor_segments": [row]}, near_critical_subdivisions=4)
        self.assertTrue(plan.actionable)
        self.assertEqual(plan.first_blocker["failure_type"], "analytic_margin_failure")
        self.assertEqual(len(plan.refinement_segments), 4)
        self.assertTrue(all(512 in seg.recommended_N_values for seg in plan.refinement_segments))
        self.assertTrue(all(seg.recommended_oversample_factor >= 16 for seg in plan.refinement_segments))

    def test_nonoverlap_bridge_is_proposed_after_ready_rows(self) -> None:
        a = _ready_row("a", 0.0, 0.1)
        b = _ready_row("b", 0.2, 0.3)
        plan = build_phase2g_refinement_plan({"anchor_segments": [a, b]}, final_anchor=(0.0, 0.3))
        self.assertTrue(plan.actionable)
        self.assertEqual(plan.first_blocker["kind"], "link")
        self.assertEqual(plan.refinement_segments[0].source_failure, "nonpositive_overlap")
        self.assertLess(plan.refinement_segments[0].K_lo, plan.refinement_segments[0].K_hi)

    def test_missing_final_anchor_uses_remaining_full_grid_plan(self) -> None:
        row = _ready_row("a", 0.265, 0.5)
        full_plan = {
            "segments": [
                {"segment_id": "p0", "K_lo": 0.265, "K_hi": 0.5, "K_mid": 0.38},
                {"segment_id": "p1", "K_lo": 0.4999999, "K_hi": 0.971636, "K_mid": 0.735},
            ]
        }
        plan = build_phase2g_refinement_plan({"anchor_segments": [row]}, plan=full_plan, final_anchor=(0.971635, 0.971636))
        self.assertTrue(plan.actionable)
        self.assertEqual(plan.first_blocker["failure_type"], "final_anchor_not_reached")
        self.assertEqual(plan.refinement_segments[0].source_failure, "final_anchor_not_reached")
        self.assertGreaterEqual(plan.refinement_segments[0].K_hi, 0.971636)

    def test_write_outputs_includes_shell_commands(self) -> None:
        row = _ready_row("bad", 0.970, 0.971636)
        row.update({"tail_bound_T": 2e-4, "radii_margin": -1e-4, "theorem_ready": False, "certified": False})
        plan = build_phase2g_refinement_plan({"anchor_segments": [row]})
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            summary = write_phase2g_refinement_outputs(
                plan,
                out_json=td_path / "plan.json",
                out_csv=td_path / "segments.csv",
                out_shell=td_path / "run.sh",
            )
            self.assertTrue(Path(summary["plan_path"]).exists())
            self.assertTrue(Path(summary["csv_path"]).exists())
            shell = Path(summary["shell_path"]).read_text()
            self.assertIn("run_lower_anchor_phase2g_segment.py", shell)
            data = json.loads(Path(summary["plan_path"]).read_text())
            self.assertTrue(data["actionable"])


if __name__ == "__main__":
    unittest.main()
