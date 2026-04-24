from __future__ import annotations

from kam_theorem_suite.interval_newton_scalar import build_scalar_interval_newton_certificate
from kam_theorem_suite.periodic_branch_tube import build_periodic_branch_tube_certificate
from kam_theorem_suite.proof_driver import (
    build_adaptive_residue_crossing_report,
    build_periodic_branch_tube_report,
    build_residue_branch_window_report,
)
from kam_theorem_suite.residue_branch import adaptive_localize_residue_crossing, analyze_residue_branch_window
from kam_theorem_suite.crossing_certificate import certify_unique_crossing_window
from kam_theorem_suite.standard_map import HarmonicFamily


def test_scalar_interval_newton_certificate_closes_simple_root():
    cert = build_scalar_interval_newton_certificate(
        0.0,
        1.0,
        midpoint=0.5,
        g_mid_lo=-0.1,
        g_mid_hi=0.1,
        gprime_lo=1.0,
        gprime_hi=1.2,
    )
    assert cert.derivative_away_from_zero
    assert cert.success
    assert cert.refined_lo is not None and cert.refined_hi is not None
    assert cert.refined_lo <= 0.5 <= cert.refined_hi


def test_periodic_branch_tube_certificate_and_driver_are_json_ready():
    fam = HarmonicFamily()
    cert = build_periodic_branch_tube_certificate(3, 5, 0.9738, 0.9742, fam)
    rep = build_periodic_branch_tube_report(3, 5, 0.9738, 0.9742, fam)
    assert cert.width > 0.0
    assert cert.interval_tangent_contraction >= 0.0
    assert rep["branch_tube"]["tube_sup_width"] >= 0.0


def test_residue_branch_window_report_matches_crossing_window_structure():
    fam = HarmonicFamily()
    rep = build_residue_branch_window_report(3, 5, 0.9738, 0.9742, fam)
    assert rep["status"] in {"interval_newton", "monotone_window", "incomplete"}
    assert rep["g_interval_lo"] <= rep["g_interval_hi"]
    assert rep["gprime_interval_lo"] <= rep["gprime_interval_hi"]


def test_adaptive_residue_crossing_localizes_on_broad_window():
    fam = HarmonicFamily()
    cert = adaptive_localize_residue_crossing(3, 5, 0.95, 0.99, fam, max_depth=5, min_width=5e-4)
    assert cert.analyzed_windows >= 3
    assert cert.status == "interval_newton"
    assert cert.best_window is not None
    assert cert.best_window["interval_newton"]["success"]
    assert cert.best_window["interval_newton"]["refined_lo"] < cert.best_window["interval_newton"]["refined_hi"]


def test_crossing_certificate_uses_adaptive_refinement_on_broad_window():
    fam = HarmonicFamily()
    cert = certify_unique_crossing_window(
        3, 5, 0.95, 0.99, fam,
        adaptive_refine=True,
        adaptive_max_depth=5,
        adaptive_min_width=5e-4,
    )
    assert cert.certification_tier == "interval_newton"
    assert cert.certified_root_window_lo is not None
    assert cert.certified_root_window_hi is not None
    assert cert.certified_root_window_hi - cert.certified_root_window_lo < 5e-4


def test_adaptive_driver_report_returns_best_window():
    fam = HarmonicFamily()
    rep = build_adaptive_residue_crossing_report(3, 5, 0.95, 0.99, fam, max_depth=5, min_width=5e-4)
    assert rep["status"] == "interval_newton"
    assert rep["best_window"] is not None
    assert rep["best_window"]["interval_newton"]["success"]
