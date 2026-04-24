from __future__ import annotations

import math

from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import (
    build_rational_upper_ladder_report,
    build_two_sided_irrational_threshold_atlas_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.two_sided_irrational_atlas import (
    build_rational_upper_ladder,
    build_two_sided_irrational_threshold_atlas,
)

GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def _specs():
    return [
        ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
        ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
    ]


def test_rational_upper_ladder_builds_and_summarizes_crossings():
    fam = HarmonicFamily()
    rep = build_rational_upper_ladder(
        rho=GOLDEN,
        specs=_specs(),
        family=fam,
        initial_subdivisions=2,
        max_depth=2,
    )
    d = rep.to_dict()
    assert len(d["approximants"]) == 2
    assert d["successful_crossing_count"] >= 1
    assert d["ladder_quality"] in {"strong", "moderate", "weak", "failed"}
    if d["successful_crossing_count"] >= 1:
        assert d["best_crossing_lower_bound"] is not None
        assert d["best_crossing_upper_bound"] is not None


def test_two_sided_irrational_threshold_atlas_has_both_layers():
    fam = HarmonicFamily()
    rep = build_two_sided_irrational_threshold_atlas(
        rho=GOLDEN,
        K_values=[0.5, 0.6, 0.7],
        specs=_specs(),
        family=fam,
        N_values=(32, 48, 64),
        quality_floor="weak",
        initial_subdivisions=2,
        max_depth=2,
    )
    d = rep.to_dict()
    assert "lower_side" in d and "upper_side" in d and "relation" in d
    assert d["relation"]["status"] in {
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
    assert d["lower_side"]["stable_prefix_len"] >= 1
    assert d["upper_side"]["successful_crossing_count"] >= 1


def test_driver_layer_exposes_two_sided_reports():
    fam = HarmonicFamily()
    ladder = build_rational_upper_ladder_report(
        rho=GOLDEN,
        specs=_specs(),
        family=fam,
        initial_subdivisions=2,
        max_depth=2,
    )
    atlas = build_two_sided_irrational_threshold_atlas_report(
        rho=GOLDEN,
        K_values=[0.5, 0.6, 0.7],
        specs=_specs(),
        family=fam,
        N_values=(32, 48, 64),
        quality_floor="weak",
        initial_subdivisions=2,
        max_depth=2,
    )
    assert ladder["successful_crossing_count"] >= 1
    assert atlas["relation"]["ladder_quality"] in {"strong", "moderate", "weak", "failed"}
    assert atlas["relation"]["lower_bound_K"] is not None
