from __future__ import annotations

from kam_theorem_suite.branch_tube import build_branch_tube
from kam_theorem_suite.proof_driver import build_crossing_window_report
from kam_theorem_suite.standard_map import HarmonicFamily


def test_branch_tube_builds_for_small_window():
    fam = HarmonicFamily()
    tube = build_branch_tube(3, 5, 0.95, 0.951, fam)
    assert tube.branch_residual_width >= 0.0
    assert tube.K_lo < tube.K_hi
    assert len(tube.x_mid) == 5


def test_crossing_window_report_has_g_interval():
    fam = HarmonicFamily()
    report = build_crossing_window_report(3, 5, 0.969, 0.972, fam)
    summary = report.summary
    assert summary["success"]
    assert summary["g_interval_lo"] <= summary["g_interval_hi"]
    assert "branch_tube" in summary
