from __future__ import annotations

import math

from kam_theorem_suite.proof_driver import build_analytic_torus_validation_report
from kam_theorem_suite.torus_validator import build_analytic_invariant_circle_certificate
from kam_theorem_suite.standard_map import HarmonicFamily


GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def test_analytic_torus_certificate_smoke() -> None:
    fam = HarmonicFamily()
    cert = build_analytic_invariant_circle_certificate(GOLDEN, 0.3, fam, N=64, sigma_cap=0.02)
    d = cert.to_dict()
    assert d['finite_dimensional_success'] is True
    assert d['small_divisor_audit']['min_exact_gap'] > 0.0
    assert d['cohomological_inverse_bound'] > 0.0
    assert d['defect_report']['weighted_l1'] >= 0.0
    assert d['theorem_status'] in {
        'analytic-torus-bridge-strong',
        'analytic-torus-bridge-moderate',
        'analytic-torus-bridge-weak',
    }


def test_proof_driver_analytic_torus_report_smoke() -> None:
    fam = HarmonicFamily()
    report = build_analytic_torus_validation_report(GOLDEN, 0.3, fam, N=64, sigma_cap=0.02)
    assert report['finite_dimensional_success'] is True
    assert report['strip_profile']['weighted_l1'] > 0.0
    assert report['small_divisor_audit']['cutoff'] >= 1
