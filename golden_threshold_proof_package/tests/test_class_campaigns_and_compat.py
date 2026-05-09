from __future__ import annotations

from pathlib import Path

from kam_theorem_suite.branch_tube import build_branch_tube
from kam_theorem_suite.class_campaigns import (
    ArithmeticClassSpec,
    build_campaign_window_specs,
    build_class_ladder_report,
    generate_eventually_periodic_convergents,
)
from kam_theorem_suite.notebook_tools import bootstrap_project_root
from kam_theorem_suite.proof_driver import build_torus_continuation_report


def test_branch_tube_backward_compatible_aliases_exist():
    tube = build_branch_tube(3, 5, 0.9708, 0.9710)
    d = tube.to_dict()
    assert "max_endpoint_radius" in d
    assert "tube_sup_width" in d
    assert d["max_endpoint_radius"] >= 0.0
    assert d["tube_sup_width"] >= 0.0


def test_torus_continuation_backward_compatible_alias_exists():
    rep = build_torus_continuation_report((5 ** 0.5 - 1.0) / 2.0, [0.90, 0.93, 0.96], N=32)
    assert "quality_floor_passed_up_to" in rep
    assert "last_success_before_failure" in rep
    assert "first_failure_after_success" in rep


def test_eventually_periodic_ladder_generation_and_window_specs():
    spec = ArithmeticClassSpec(preperiod=(), period=(2,), label="silver")
    fracs = generate_eventually_periodic_convergents(preperiod=spec.preperiod, period=spec.period, max_q=30, keep_last=4)
    assert fracs
    assert all(f.denominator <= 30 for f in fracs)
    ladder = build_class_ladder_report(spec, max_q=30, keep_last=4, q_min=2)
    assert ladder.class_label == "silver"
    assert len(ladder.approximants) > 0
    specs = build_campaign_window_specs(spec, reference_crossing_center=0.9713, max_q=30, keep_last=3, q_min=2)
    assert len(specs) > 0
    assert specs[0].crossing_K_lo < specs[0].crossing_K_hi
    assert specs[0].band_search_lo < specs[0].band_search_hi


def test_bootstrap_project_root_from_notebooks_dir():
    root = Path(__file__).resolve().parents[1]
    nb_dir = root / "notebooks"
    detected = bootstrap_project_root(nb_dir)
    assert Path(detected).resolve() == root.resolve()


def test_small_class_campaign_report_smoke():
    from kam_theorem_suite.proof_driver import build_class_atlas_campaign_report
    spec = ArithmeticClassSpec(preperiod=(), period=(2,), label="silver")
    rep = build_class_atlas_campaign_report(
        spec,
        reference_lower_bound=0.97122,
        reference_crossing_center=0.9713,
        max_q=8,
        keep_last=1,
        q_min=2,
        auto_localize_crossing=True,
        min_width=1e-3,
    )
    assert rep["class_label"] == "silver"
    assert "atlas" in rep and "pruning_against_reference" in rep
