from __future__ import annotations

import math

from kam_theorem_suite.crossing_certificate import (
    build_endpoint_residue_certificate,
    certify_unique_crossing_window,
)
from kam_theorem_suite.proof_driver import (
    build_endpoint_residue_report,
    build_threshold_corridor_report_driver,
    build_unique_crossing_certificate_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.threshold_bracketing import build_threshold_corridor_report

GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def test_endpoint_residue_certificates_detect_below_and_above_target():
    fam = HarmonicFamily()
    left = build_endpoint_residue_certificate(3, 5, 0.9738, fam)
    right = build_endpoint_residue_certificate(3, 5, 0.9742, fam)
    assert left.success and right.success
    assert left.side == "below-target"
    assert right.side == "above-target"


def test_unique_crossing_certificate_closes_local_interval_newton_window():
    fam = HarmonicFamily()
    cert = certify_unique_crossing_window(3, 5, 0.9738, 0.9742, fam)
    assert cert.strict_sign_change
    assert cert.derivative_away_from_zero
    assert cert.monotone_unique_crossing
    assert cert.interval_newton["success"] if isinstance(cert.interval_newton, dict) else cert.interval_newton.success
    assert cert.certification_tier == "interval_newton"
    assert cert.certified_root_window_lo is not None
    assert cert.certified_root_window_hi is not None
    assert cert.certified_root_window_lo < cert.certified_root_window_hi


def test_threshold_corridor_report_is_json_ready_and_separated():
    fam = HarmonicFamily()
    rep = build_threshold_corridor_report(
        GOLDEN,
        [0.5, 0.6, 0.7],
        3,
        5,
        0.9738,
        0.9742,
        fam,
        N=64,
    )
    d = rep.to_dict()
    assert d["status"] in {"separated-corridor", "overlapping-corridor", "lower-bound-only", "rational-crossing-only"}
    assert d["crossing_certificate"]["certification_tier"] in {"interval_newton", "monotone_window", "incomplete"}
    assert d["lower_bound_K"] is not None
    assert d["rational_root_window_lo"] is not None


def test_driver_reports_cover_new_crossing_and_corridor_layers():
    fam = HarmonicFamily()
    endpoint = build_endpoint_residue_report(3, 5, 0.9738, fam)
    crossing = build_unique_crossing_certificate_report(3, 5, 0.9738, 0.9742, fam)
    corridor = build_threshold_corridor_report_driver(
        GOLDEN,
        [0.5, 0.6, 0.7],
        3,
        5,
        0.9738,
        0.9742,
        fam,
        N=64,
    )
    assert endpoint["side"] == "below-target"
    assert crossing["strict_sign_change"]
    assert corridor["crossing_certificate"]["strict_sign_change"]
