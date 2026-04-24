from __future__ import annotations

import math

from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import (
    build_refined_rational_upper_ladder_report,
    build_two_sided_irrational_threshold_atlas_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.two_sided_irrational_atlas import build_rational_upper_ladder
from kam_theorem_suite.upper_ladder_refinement import refine_rational_upper_ladder

GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def _specs():
    return [
        ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
        ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
        ApproximantWindowSpec(8, 13, 0.9710, 0.9725, 1.04, 1.06, label="gold-8/13"),
    ]


def test_refined_upper_ladder_builds_clusters_and_best_object():
    fam = HarmonicFamily()
    raw = build_rational_upper_ladder(
        rho=GOLDEN,
        specs=_specs(),
        family=fam,
        initial_subdivisions=2,
        max_depth=2,
    ).to_dict()
    refined = refine_rational_upper_ladder(raw).to_dict()
    assert refined["raw_successful_crossing_count"] >= 1
    assert isinstance(refined["clusters"], list)
    assert refined["status"] in {"refined-upper-ladder", "audited-upper-ladder", "failed"}
    if refined["clusters"]:
        cluster = refined["clusters"][refined["selected_cluster_index"]]
        assert cluster["denominator_consistency_status"] in {"strong", "moderate", "weak", "failed"}
        assert cluster["pairwise_consistency_fraction"] >= 0.0


def test_driver_and_two_sided_report_expose_refined_upper_cluster():
    fam = HarmonicFamily()
    rep = build_refined_rational_upper_ladder_report(
        rho=GOLDEN,
        specs=_specs(),
        family=fam,
        initial_subdivisions=2,
        max_depth=2,
    )
    assert rep["refined_upper_ladder"]["status"] in {"refined-upper-ladder", "audited-upper-ladder", "failed"}

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
    )
    assert "refined_cluster" in atlas["upper_side"]
    assert atlas["relation"]["upper_object_source"] in {"asymptotic-upper-ladder", "refined-upper-ladder", "raw-upper-ladder"}
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
