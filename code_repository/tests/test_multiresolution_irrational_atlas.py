from __future__ import annotations

import math
import numpy as np

from kam_theorem_suite.irrational_existence_atlas import (
    build_multiresolution_existence_vs_crossing_bridge,
    continue_invariant_circle_multiresolution,
    resample_graph_samples,
    validate_invariant_circle_multiresolution,
)
from kam_theorem_suite.proof_driver import (
    build_multiresolution_existence_crossing_bridge_report,
    build_multiresolution_torus_continuation_report,
    build_multiresolution_torus_validation_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily

GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def test_resample_graph_samples_preserves_trigonometric_profile_reasonably():
    theta = np.arange(32, dtype=float) / 32.0
    u = 0.05 * np.sin(2.0 * np.pi * theta) + 0.01 * np.sin(4.0 * np.pi * theta)
    up = resample_graph_samples(u, 96)
    back = resample_graph_samples(up, 32)
    assert np.linalg.norm(back - u, ord=np.inf) < 1e-10


def test_multiresolution_validation_report_succeeds_for_subcritical_case():
    fam = HarmonicFamily()
    rep = validate_invariant_circle_multiresolution(GOLDEN, 0.5, fam, N_values=(32, 48, 64))
    assert rep.success_count >= 2
    assert rep.finest_success_N in {32, 48, 64}
    assert rep.atlas_quality in {"strong", "moderate", "weak"}
    assert len(rep.comparisons) == 2


def test_multiresolution_continuation_report_tracks_stable_prefix():
    fam = HarmonicFamily()
    rep = continue_invariant_circle_multiresolution(GOLDEN, [0.5, 0.7, 0.9], fam, N_values=(32, 48, 64), quality_floor="weak")
    assert len(rep.steps) == 3
    assert rep.stable_prefix_len >= 1
    assert rep.steps[0].atlas_quality in {"strong", "moderate", "weak", "failed"}


def test_multiresolution_driver_reports_are_json_ready():
    fam = HarmonicFamily()
    rep1 = build_multiresolution_torus_validation_report(GOLDEN, 0.5, fam, N_values=(32, 48, 64))
    rep2 = build_multiresolution_torus_continuation_report(GOLDEN, [0.5, 0.6, 0.7], fam, N_values=(32, 48, 64), quality_floor="weak")
    assert rep1["atlas_quality"] in {"strong", "moderate", "weak", "failed"}
    assert "steps" in rep2 and len(rep2["steps"]) == 3


def test_multiresolution_bridge_contains_both_existence_and_crossing_sides():
    fam = HarmonicFamily()
    bridge = build_multiresolution_existence_vs_crossing_bridge(
        rho=GOLDEN, K_values=[0.5, 0.6, 0.7], N_values=(32, 48, 64), p=3, q=5,
        crossing_K_lo=0.969, crossing_K_hi=0.972, family=fam, quality_floor="weak",
    ).to_dict()
    assert "multiresolution_continuation" in bridge
    assert "crossing_window" in bridge
    d2 = build_multiresolution_existence_crossing_bridge_report(
        rho=GOLDEN, K_values=[0.5, 0.6, 0.7], p=3, q=5,
        crossing_K_lo=0.969, crossing_K_hi=0.972, family=fam,
        N_values=(32, 48, 64), quality_floor="weak",
    )
    assert d2["relation"]["stable_prefix_len"] >= 1
