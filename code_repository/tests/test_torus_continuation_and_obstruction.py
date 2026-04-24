from __future__ import annotations

import math

from kam_theorem_suite.obstruction import (
    build_existence_obstruction_bridge,
    build_periodic_obstruction_report,
)
from kam_theorem_suite.proof_driver import (
    build_existence_obstruction_bridge_report,
    build_torus_continuation_report,
    build_torus_grid_scan_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.torus_continuation import continue_invariant_circle_validations


GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def test_torus_continuation_report_tracks_quality_and_prefix_data():
    fam = HarmonicFamily()
    rep = continue_invariant_circle_validations(GOLDEN, [0.5, 0.7, 0.9], fam, N=64)
    assert len(rep.steps) == 3
    assert rep.all_success
    assert rep.validated_fraction == 1.0
    assert rep.strongest_quality_prefix in {"strong", "moderate", None}
    assert all(step.bridge_quality in {"strong", "moderate", "weak", "failed"} for step in rep.steps)


def test_driver_grid_scan_and_direct_continuation_are_json_ready():
    fam = HarmonicFamily()
    rep1 = build_torus_continuation_report(GOLDEN, [0.5, 0.6, 0.7], fam, N=64)
    rep2 = build_torus_grid_scan_report(GOLDEN, 0.5, 0.7, 3, fam, N=64)
    assert "steps" in rep1 and len(rep1["steps"]) == 3
    assert "validated_fraction" in rep2
    assert rep2["validated_fraction"] >= 0.0


def test_periodic_obstruction_report_exposes_regime_and_trace_bounds():
    fam = HarmonicFamily()
    rep = build_periodic_obstruction_report(3, 5, 0.969, 0.972, fam)
    assert rep.regime in {"elliptic", "hyperbolic", "mixed"}
    assert rep.trace_interval_lo <= rep.trace_interval_hi
    assert rep.certified_crossing_side in {"below-target", "above-target", "mixed"}
    assert "x_iv_bounds" in rep.branch_tube


def test_existence_obstruction_bridge_driver_has_both_sides():
    fam = HarmonicFamily()
    rep = build_existence_obstruction_bridge(
        rho=GOLDEN,
        K_subcritical=0.5,
        K_supercritical_lo=0.969,
        K_supercritical_hi=0.972,
        p=3,
        q=5,
        family=fam,
        N=64,
    )
    d = rep.to_dict()
    assert d["torus_validation"]["success"]
    assert "periodic_obstruction" in d
    assert "bridge_status" in d["relation"]

    d2 = build_existence_obstruction_bridge_report(
        rho=GOLDEN,
        K_subcritical=0.5,
        K_supercritical_lo=0.969,
        K_supercritical_hi=0.972,
        p=3,
        q=5,
        family=fam,
        N=64,
    )
    assert d2["relation"]["subcritical_torus_validated"]
