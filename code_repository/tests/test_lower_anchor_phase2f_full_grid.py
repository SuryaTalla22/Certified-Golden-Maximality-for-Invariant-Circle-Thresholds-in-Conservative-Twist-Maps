from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_closure import build_anchor_closure_audit, load_lower_corridor_bundle
from kam_theorem_suite.audit.lower_anchor_heavy_certificate import (
    HeavyLowerAnchorConfig,
    run_heavy_lower_anchor_certificate,
    write_heavy_lower_anchor_outputs,
)
from kam_theorem_suite.audit.lower_anchor_phase2e_full_grid import (
    build_phase2e_full_grid_plan,
    merge_phase2e_anchor_candidates,
    write_merged_phase2e_anchor_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
LOWER_BUNDLE = ROOT / "artifacts/proof_audit/lower_corridor/lower_corridor_audit.bundle.json"
_GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def _phase2e_zero_builder(**kwargs):
    N = max(kwargs.get("N_values", (16,)))
    return {
        "rho": _GOLDEN,
        "K": 0.0,
        "N": int(N),
        "sigma_used": 1.0e-3,
        "finite_dimensional_success": True,
        "finite_radius": 1.0e-4,
        "finite_eta": 0.0,
        "finite_B_norm": 1.0,
        "finite_lipschitz_bound": 0.1,
        "finite_contraction_bound": 0.01,
        "finite_radii_margin": 9.0e-5,
        "theorem_status": "analytic-torus-bridge-weak",
        "theorem_margin": -1.0,
        "cohomological_inverse_bound": 5.0,
        "cohomological_correction_bound": 0.0,
        "defect_report": {"weighted_l1": 0.0},
        "tail_bound": {"tail_l1": 0.0},
        "source_validation": {"u": [0.0] * int(N), "lambda_value": 0.0},
    }


class LowerAnchorPhase2FFullGridTests(unittest.TestCase):
    def test_full_grid_plan_reaches_near_critical_anchor(self) -> None:
        plan = build_phase2e_full_grid_plan()
        self.assertGreaterEqual(plan.segment_count, 10)
        self.assertLessEqual(plan.segments[0]["K_lo"], 0.265)
        self.assertGreaterEqual(plan.segments[-1]["K_hi"], 0.9716360)
        for a, b in zip(plan.segments, plan.segments[1:]):
            self.assertGreater(float(a["K_hi"]) - float(b["K_lo"]), 0.0)

    def test_chunk_slice_keeps_global_segment_ids_and_is_not_promotable(self) -> None:
        cfg = HeavyLowerAnchorConfig(
            start_K=0.0,
            final_anchor_lo=0.49,
            final_anchor_hi=0.5,
            N_values=(16,),
            segment_start=1,
            segment_stop=2,
            theorem_margin_safety_factor=1.0,
            outward_rounding_tolerance=1e-12,
        )
        report = run_heavy_lower_anchor_certificate(cfg, certificate_builder=_phase2e_zero_builder)
        self.assertEqual(len(report.records), 1)
        self.assertEqual(report.records[0].segment_id, "phase2e_heavy_anchor_segment_001")
        self.assertFalse(report.promotion_allowed)
        self.assertIn("partial_grid_run_not_promotable", report.failure_fields)

    def test_merge_full_synthetic_chunks_can_pass_phase2b_ingestion(self) -> None:
        lower = load_lower_corridor_bundle(LOWER_BUNDLE)
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            cfg0 = HeavyLowerAnchorConfig(
                start_K=0.2649,
                final_anchor_lo=0.9716350,
                final_anchor_hi=0.9716360,
                N_values=(16,),
                segment_start=0,
                segment_stop=5,
                theorem_margin_safety_factor=1.0,
                outward_rounding_tolerance=1e-12,
            )
            cfg1 = HeavyLowerAnchorConfig(
                start_K=0.2649,
                final_anchor_lo=0.9716350,
                final_anchor_hi=0.9716360,
                N_values=(16,),
                segment_start=5,
                segment_stop=None,
                theorem_margin_safety_factor=1.0,
                outward_rounding_tolerance=1e-12,
            )
            rep0 = run_heavy_lower_anchor_certificate(cfg0, certificate_builder=_phase2e_zero_builder)
            rep1 = run_heavy_lower_anchor_certificate(cfg1, certificate_builder=_phase2e_zero_builder)
            out0 = write_heavy_lower_anchor_outputs(rep0, out_dir=td_path / "a", table_dir=td_path / "ta", candidate_name="chunk0.json")
            out1 = write_heavy_lower_anchor_outputs(rep1, out_dir=td_path / "b", table_dir=td_path / "tb", candidate_name="chunk1.json")
            merged = merge_phase2e_anchor_candidates(
                [out0["candidate_path"], out1["candidate_path"]],
                final_anchor=(0.9716350, 0.9716360),
            )
            self.assertTrue(merged["promotion_allowed"])
            self.assertFalse(merged["failure_fields"])
            merged_path = td_path / "merged.json"
            merged_path.write_text(json.dumps(merged))
            segments, candidate_validation, verification, bundle = build_anchor_closure_audit(
                lower,
                anchor_candidate=merged,
                anchor_candidate_path=merged_path,
                final_anchor=(0.9716350, 0.9716360),
            )
            self.assertTrue(candidate_validation.anchor_segments_verified)
            self.assertTrue(verification.final_anchor_reached)
            self.assertFalse(bundle.failure_fields)

    def test_merge_rejects_nonoverlapping_rows(self) -> None:
        row = {
            "segment_id": "a",
            "K_lo": 0.0,
            "K_hi": 0.1,
            "rho": _GOLDEN,
            "N": 16,
            "sigma": 0.001,
            "residual_Y": 0.0,
            "linear_defect_Z": 0.0,
            "tail_bound_T": 0.0,
            "radius_r": 1e-4,
            "radii_margin": 1e-4,
            "small_divisor_min": 1.0,
            "small_divisor_inverse_bound": 1.0,
            "source_module": "test",
            "source_artifact": "test",
            "certified": True,
            "finite_dimensional_only": False,
            "closure_level": "analytic_theorem_closure",
        }
        c1 = {"theorem_facing": True, "diagnostic_only": False, "anchor_segments": [row]}
        row2 = dict(row, segment_id="b", K_lo=0.2, K_hi=0.3)
        c2 = {"theorem_facing": True, "diagnostic_only": False, "anchor_segments": [row2]}
        with tempfile.TemporaryDirectory() as td:
            p1 = Path(td) / "c1.json"; p2 = Path(td) / "c2.json"
            p1.write_text(json.dumps(c1)); p2.write_text(json.dumps(c2))
            merged = merge_phase2e_anchor_candidates([p1, p2], final_anchor=(0.0, 0.3))
            self.assertFalse(merged["promotion_allowed"])
            self.assertIn("merged_anchor_failed_links", merged["failure_fields"])


if __name__ == "__main__":
    unittest.main()
