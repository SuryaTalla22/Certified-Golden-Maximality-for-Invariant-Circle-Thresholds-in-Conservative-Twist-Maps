from __future__ import annotations

from kam_theorem_suite.obstruction_atlas import (
    ApproximantWindowSpec,
    build_multi_approximant_obstruction_atlas,
    compare_atlas_to_reference,
)
from kam_theorem_suite.challenger_pruning import (
    ChallengerSpec,
    build_challenger_pruning_report,
    extract_challengers_from_atlas,
)
from kam_theorem_suite.proof_driver import (
    build_multi_approximant_atlas_report,
    build_atlas_reference_comparison_report,
    build_challenger_pruning_report_driver,
    build_pruning_report_from_atlas,
)
from kam_theorem_suite.standard_map import HarmonicFamily


def test_multi_approximant_obstruction_atlas_builds_structured_summary():
    fam = HarmonicFamily()
    specs = [
        ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
        ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
    ]
    atlas = build_multi_approximant_obstruction_atlas(
        specs,
        fam,
        auto_localize_crossing=True,
        initial_subdivisions=2,
        max_depth=2,
    )
    d = atlas.to_dict()
    assert d["atlas_status"] in {"fully-certified-local-atlas", "partial-certified-local-atlas"}
    assert len(d["approximants"]) == 2
    assert d["approximants"][0]["crossing_certificate"]["certification_tier"] in {"interval_newton", "monotone_window", "incomplete"}


def test_atlas_reference_comparison_detects_dominated_entries():
    fam = HarmonicFamily()
    specs = [
        ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
        ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
    ]
    atlas = build_multi_approximant_obstruction_atlas(
        specs,
        fam,
        auto_localize_crossing=True,
        initial_subdivisions=2,
        max_depth=2,
    )
    comp = compare_atlas_to_reference(atlas, reference_label="gold-ref", reference_crossing_lo=0.9738, reference_crossing_hi=0.9742)
    d = comp.to_dict()
    assert "gold-5/8" in d["dominated_labels"]
    assert d["status"] == "reference-dominates-certified-subset"


def test_challenger_pruning_mixes_threshold_and_arithmetic_only_statuses():
    challengers = [
        ChallengerSpec(preperiod=(), period=(2,), threshold_upper_bound=0.96, label="silver"),
        ChallengerSpec(preperiod=(), period=(3,), threshold_upper_bound=None, label="bronze"),
    ]
    report = build_challenger_pruning_report(challengers, golden_lower_bound=0.9712)
    rows = {r["label"]: r for r in report.to_dict()["records"]}
    assert rows["silver"]["status"] == "dominated"
    assert rows["bronze"]["status"] == "arithmetic-weaker-only"


def test_driver_layer_exposes_atlas_and_pruning_reports():
    fam = HarmonicFamily()
    specs = [
        ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
        ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
    ]
    atlas = build_multi_approximant_atlas_report(
        specs,
        fam,
        auto_localize_crossing=True,
        initial_subdivisions=2,
        max_depth=2,
    )
    comp = build_atlas_reference_comparison_report(
        atlas,
        reference_label="gold-ref",
        reference_crossing_lo=0.9738,
        reference_crossing_hi=0.9742,
    )
    pruning = build_challenger_pruning_report_driver(
        [ChallengerSpec(preperiod=(), period=(2,), threshold_upper_bound=0.96, label="silver")],
        golden_lower_bound=0.9712,
    )
    from_atlas = build_pruning_report_from_atlas(
        atlas,
        class_map={"gold-3/5": ((), (1,)), "gold-5/8": ((), (1,))},
        golden_lower_bound=0.9738,
    )
    assert comp["status"] == "reference-dominates-certified-subset"
    assert pruning["records"][0]["status"] == "dominated"
    assert from_atlas["status"] in {"partially-pruned", "all-listed-challengers-dominated", "no-threshold-pruning-yet"}
    extracted = extract_challengers_from_atlas(atlas, class_map={"gold-3/5": ((), (1,)), "gold-5/8": ((), (1,))})
    assert len(extracted) == 2
