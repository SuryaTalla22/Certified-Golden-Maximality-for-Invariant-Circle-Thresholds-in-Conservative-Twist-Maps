from __future__ import annotations

import math

from kam_theorem_suite.asymptotic_upper_ladder_audit import audit_refined_upper_ladder_asymptotics
from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import (
    build_asymptotic_upper_ladder_audit_report,
    build_two_sided_irrational_threshold_atlas_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.two_sided_irrational_atlas import build_rational_upper_ladder

GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def _fake_ladder() -> dict:
    return {
        "ladder_quality": "moderate",
        "best_crossing_lower_bound": 0.9710,
        "best_crossing_upper_bound": 0.9718,
        "approximants": [
            {"p": 3, "q": 5, "label": "3/5", "crossing_root_window_lo": 0.9710, "crossing_root_window_hi": 0.9724},
            {"p": 5, "q": 8, "label": "5/8", "crossing_root_window_lo": 0.9711, "crossing_root_window_hi": 0.9719},
            {"p": 8, "q": 13, "label": "8/13", "crossing_root_window_lo": 0.97115, "crossing_root_window_hi": 0.97175},
            {"p": 13, "q": 21, "label": "13/21", "crossing_root_window_lo": 0.97118, "crossing_root_window_hi": 0.97170},
        ],
    }



def test_asymptotic_audit_detects_stable_tail_on_fake_ladder():
    rep = audit_refined_upper_ladder_asymptotics(_fake_ladder(), center_drift_tol=5e-4).to_dict()
    assert rep["usable_slice_count"] >= 2
    assert rep["status"] in {
        "asymptotically-stable-upper-ladder",
        "asymptotically-audited-upper-ladder",
        "audited-but-unsettled-upper-ladder",
        "drifting-upper-ladder",
    }
    if rep["status"].startswith("asymptotically"):
        assert rep["audited_upper_lo"] is not None
        assert rep["audited_upper_hi"] is not None



def _specs():
    return [
        ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
        ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
        ApproximantWindowSpec(8, 13, 0.9710, 0.9725, 1.04, 1.06, label="gold-8/13"),
    ]



def test_driver_exposes_asymptotic_audit_layer():
    fam = HarmonicFamily()
    rep = build_asymptotic_upper_ladder_audit_report(
        rho=GOLDEN,
        specs=_specs(),
        family=fam,
        initial_subdivisions=2,
        max_depth=2,
    )
    assert "asymptotic_upper_ladder_audit" in rep
    audit = rep["asymptotic_upper_ladder_audit"]
    assert audit["status"] in {
        "asymptotically-stable-upper-ladder",
        "asymptotically-audited-upper-ladder",
        "audited-but-unsettled-upper-ladder",
        "drifting-upper-ladder",
        "audit-no-usable-slices",
        "insufficient-asymptotic-data",
    }



def test_two_sided_report_can_use_asymptotic_upper_source():
    fam = HarmonicFamily()
    atlas = build_two_sided_irrational_threshold_atlas_report(
        rho=GOLDEN,
        K_values=[0.5, 0.6, 0.7],
        specs=_specs(),
        family=fam,
        N_values=(32, 48, 64),
        quality_floor="weak",
        initial_subdivisions=2,
        max_depth=2,
        refine_upper_ladder=True,
        audit_upper_ladder_asymptotics=True,
    )
    assert "asymptotic_audit" in atlas["upper_side"]
    assert atlas["relation"]["upper_object_source"] in {
        "asymptotic-upper-ladder",
        "refined-upper-ladder",
        "raw-upper-ladder",
    }
    assert atlas["relation"]["status"] in {
        "two-sided-asymptotic-corridor",
        "two-sided-refined-corridor",
        "two-sided-clustered-corridor",
        "two-sided-corridor-with-band",
        "two-sided-corridor",
        "overlapping-two-sided-evidence",
        "lower-side-only",
        "upper-side-only",
        "incomplete",
    }
