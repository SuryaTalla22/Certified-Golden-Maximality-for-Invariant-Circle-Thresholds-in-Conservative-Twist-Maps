from __future__ import annotations

from kam_theorem_suite.proof_driver import (
    build_crossing_to_hyperbolic_bridge_report,
    build_hyperbolic_window_report,
    build_supercritical_band_report_driver,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.supercritical_bands import (
    build_crossing_to_hyperbolic_band_bridge,
    build_supercritical_band_report,
    certify_hyperbolic_window,
)


def test_hyperbolic_window_certificate_closes_on_clear_supercritical_window():
    fam = HarmonicFamily()
    cert = certify_hyperbolic_window(3, 5, 1.05, 1.06, fam)
    assert cert.certified_hyperbolic
    assert cert.certified_above_target
    assert cert.regime in {"negative-hyperbolic", "positive-hyperbolic"}
    assert cert.hyperbolicity_margin > 0.0


def test_supercritical_band_report_finds_nonempty_band():
    fam = HarmonicFamily()
    rep = build_supercritical_band_report(3, 5, 1.04, 1.06, fam, initial_subdivisions=2, max_depth=2)
    d = rep.to_dict()
    assert d["status"] in {"certified-full-band", "certified-partial-band"}
    assert d["longest_band_lo"] is not None
    assert d["longest_band_hi"] is not None
    assert d["longest_band_width"] > 0.0


def test_crossing_to_hyperbolic_bridge_reports_both_layers():
    fam = HarmonicFamily()
    bridge = build_crossing_to_hyperbolic_band_bridge(
        3,
        5,
        0.97,
        0.975,
        1.04,
        1.06,
        fam,
        initial_subdivisions=2,
        max_depth=2,
    )
    d = bridge.to_dict()
    assert d["crossing_certificate"]["certification_tier"] in {"interval_newton", "monotone_window"}
    assert d["band_report"]["longest_band_lo"] is not None
    assert d["status"] == "crossing-plus-hyperbolic-band"


def test_driver_layer_exposes_supercritical_reports():
    fam = HarmonicFamily()
    window = build_hyperbolic_window_report(3, 5, 1.05, 1.06, fam)
    band = build_supercritical_band_report_driver(3, 5, 1.04, 1.06, fam, initial_subdivisions=2, max_depth=2)
    bridge = build_crossing_to_hyperbolic_bridge_report(
        3, 5, 0.97, 0.975, 1.04, 1.06, fam, initial_subdivisions=2, max_depth=2
    )
    assert window["certified_hyperbolic"]
    assert band["longest_band_width"] > 0.0
    assert bridge["status"] == "crossing-plus-hyperbolic-band"
