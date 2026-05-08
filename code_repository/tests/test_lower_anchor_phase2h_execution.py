from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from kam_theorem_suite.audit.lower_anchor_phase2h_execution import build_phase2h_execution_status, candidate_paths_for_merge, recompute_margin, row_is_theorem_ready, write_phase2h_missing_segment_script

def _ready_row(segment_id: str, lo: float, hi: float) -> dict:
    return {"segment_id": segment_id, "K_lo": lo, "K_hi": hi, "K_mid": 0.5*(lo+hi), "certified": True, "finite_dimensional_only": False, "closure_level": "analytic_theorem_closure", "residual_Y": 1e-10, "linear_defect_Z": 1e-6, "tail_bound_T": 1e-10, "radius_r": 1e-8, "radii_margin": 9.7e-9, "failure_reasons": []}

class Phase2HExecutionTests(unittest.TestCase):
    def test_margin_and_readiness_are_recomputed(self):
        row = _ready_row("s0", 0.0, 1.0)
        self.assertGreater(recompute_margin(row), 0.0)
        self.assertTrue(row_is_theorem_ready(row))
        row["radii_margin"] = -1.0
        self.assertTrue(row_is_theorem_ready(row))
        row["tail_bound_T"] = 1.0
        self.assertFalse(row_is_theorem_ready(row))

    def test_status_detects_missing_segments_and_writes_script(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = root / "plan.json"
            plan.write_text(json.dumps({"segments": [{"index": 0, "segment_id": "s0", "K_lo": 0.0, "K_hi": 0.5, "K_mid": 0.25}, {"index": 1, "segment_id": "s1", "K_lo": 0.5, "K_hi": 1.0, "K_mid": 0.75}]}))
            lower = root / "lower"; refine = lower / "phase2g_refinements"; lower.mkdir(parents=True)
            (lower / "lower_anchor_phase2f_chunk_000_candidate.json").write_text(json.dumps({"anchor_segments": [_ready_row("s0", 0.0, 0.5)]}))
            status = build_phase2h_execution_status(plan_path=plan, lower_dir=lower, refinement_dir=refine, final_anchor=(0.9, 1.0))
            self.assertEqual(status.ready_segment_count, 1)
            self.assertEqual(status.missing_segment_count, 1)
            self.assertFalse(status.promotion_allowed)
            script = root / "run_missing.sh"
            write_phase2h_missing_segment_script(status=status, out_path=script)
            text = script.read_text()
            self.assertIn("--segment-id s1", text)
            self.assertNotIn("--segment-id s0", text)
            self.assertEqual(len(candidate_paths_for_merge(status=status, lower_dir=lower, refinement_dir=refine)), 1)

if __name__ == "__main__":
    unittest.main()
