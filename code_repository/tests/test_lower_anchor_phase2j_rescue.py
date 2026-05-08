from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_phase2j_failure_atlas import (
    build_failure_atlas,
    build_failure_row,
    classify_failure,
    recompute_terms,
    row_is_failed,
    write_failure_atlas_outputs,
)
from kam_theorem_suite.audit.lower_anchor_phase2j_rescue_profiles import (
    build_profile_for_failure,
    infer_k_regime,
    subdivide_segment,
)
from kam_theorem_suite.audit.lower_anchor_phase2j_adaptive_rescue import summarize_rescue_directory


def _row(segment_id: str = "s", *, K_lo=0.9, K_hi=0.95, ready=False, margin_negative=True):
    r = 1.0e-4
    y = 8.0e-5 if margin_negative else 1.0e-5
    z = 0.1
    t = 5.0e-5 if margin_negative else 1.0e-5
    margin = r - (y + z * r + t)
    return {
        "segment_id": segment_id,
        "K_lo": K_lo,
        "K_hi": K_hi,
        "K_mid": 0.5 * (K_lo + K_hi),
        "N": 128,
        "sigma": 0.001,
        "residual_Y": y,
        "linear_defect_Z": z,
        "tail_bound_T": t,
        "radius_r": r,
        "radii_margin": margin,
        "certified": bool(ready),
        "finite_dimensional_only": not ready,
        "theorem_ready": bool(ready),
        "closure_level": "analytic_theorem_closure" if ready else "phase2e_direct_radii_attempt_not_closed",
        "failure_reasons": [] if ready else ["analytic_radii_margin_not_safely_positive"],
        "small_divisor_min": 0.01,
        "small_divisor_inverse_bound": 100.0,
    }


class Phase2JRescueTests(unittest.TestCase):
    def test_recompute_terms_and_failure_classification(self):
        row = _row()
        y, z, zr, t, r, margin = recompute_terms(row)
        self.assertAlmostEqual(margin, row["radii_margin"])
        self.assertTrue(row_is_failed(row))
        dominant, ftype, rescue = classify_failure(row)
        self.assertIn(dominant, {"residual_Y", "linear_defect_Zr", "tail_bound_T"})
        self.assertEqual(ftype, "analytic_margin_failure")
        self.assertIn("rerun", rescue)

    def test_profile_is_near_critical_adaptive(self):
        row = _row(K_lo=0.97157, K_hi=0.971636)
        self.assertEqual(infer_k_regime(row["K_mid"]), "endpoint")
        failure = build_failure_row(row)
        profile = failure.profile
        self.assertGreaterEqual(max(profile.n_values), 1024)
        self.assertGreaterEqual(profile.split_count, 6)
        subs = subdivide_segment(failure.to_dict(), profile)
        self.assertEqual(len(subs), profile.split_count)
        self.assertLessEqual(subs[0]["K_lo"], row["K_lo"])
        self.assertGreaterEqual(subs[-1]["K_hi"], row["K_hi"])

    def test_build_failure_atlas_and_scripts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cand = root / "candidate.json"
            cand.write_text(json.dumps({"anchor_segments": [_row("ready", ready=True, margin_negative=False), _row("bad", ready=False, margin_negative=True)]}))
            atlas = build_failure_atlas(cand, max_variants_per_parent=3)
            self.assertEqual(atlas.total_segment_count, 2)
            self.assertEqual(atlas.failed_segment_count, 1)
            self.assertEqual(atlas.theorem_ready_count, 1)
            self.assertGreater(len(atlas.rescue_variants), 0)
            out = write_failure_atlas_outputs(
                atlas,
                out_json=root / "atlas.json",
                out_csv=root / "atlas.csv",
                script_out=root / "run.sh",
                dry_run_script_out=root / "dry.sh",
            )
            self.assertTrue(Path(out["atlas_path"]).exists())
            self.assertTrue(Path(out["script_path"]).read_text().startswith("#!/usr/bin/env bash"))
            self.assertIn("--dry-run", Path(out["dry_run_script_path"]).read_text())

    def test_rescue_directory_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            atlas = root / "atlas.json"
            atlas.write_text(json.dumps({"failed_segment_count": 1, "rescue_variants": [{"variant_id": "v"}]}))
            rescue = root / "rescue"
            rescue.mkdir()
            row = _row("r0", ready=True, margin_negative=False)
            (rescue / "r0_candidate.json").write_text(json.dumps({"anchor_segments": [row]}))
            summary = summarize_rescue_directory(atlas_path=atlas, rescue_dir=rescue)
            self.assertEqual(summary.rescue_candidate_count, 1)
            self.assertEqual(summary.theorem_ready_rescue_candidate_count, 1)
            self.assertEqual(len(summary.best_candidate_paths), 1)


if __name__ == "__main__":
    unittest.main()
