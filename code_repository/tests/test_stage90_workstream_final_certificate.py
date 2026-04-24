from __future__ import annotations

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.theorem_i_ii_workstream_lift import build_golden_theorem_i_ii_workstream_lift_certificate


def test_stage90_workstream_final_certificate() -> None:
    cert = build_golden_theorem_i_ii_workstream_lift_certificate(family=HarmonicFamily()).to_dict()
    assert cert['workstream_codepath_strong'] is True
    assert cert['workstream_papergrade_strong'] is True
    assert cert['papergrade_theorem_status'] == 'golden-theorem-i-ii-workstream-papergrade-final'
    assert cert['workstream_residual_caveat'] == []
    assert cert['workstream_consumption_summary']['universality_class_citeable'] is True
    assert cert['workstream_consumption_summary']['renormalization_package_citeable'] is True
    assert cert['workstream_consumption_summary']['critical_surface_theorem_citeable'] is True
    assert cert['workstream_consumption_summary']['threshold_identification_citeable'] is True
