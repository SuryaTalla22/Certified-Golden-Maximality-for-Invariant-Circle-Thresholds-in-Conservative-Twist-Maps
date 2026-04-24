from __future__ import annotations

from types import SimpleNamespace

from kam_theorem_suite.proof_driver import (
    build_golden_theorem_i_ii_report,
    build_golden_theorem_i_ii_workstream_lift_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.theorem_i_ii_workstream_lift import (
    build_golden_theorem_i_ii_workstream_lift_certificate,
)


class _FakeCert:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)



def _base_payloads(strong_stable: bool = True):
    return {
        'universality': {
            'admissible': True,
            'status': 'admissible',
            'admissibility_margins': {'a': 0.3, 'b': 0.2},
        },
        'renorm_class': {
            'admissible_near_chart': True,
            'status': 'near_golden_chart_scaffold',
            'chart_margins': {'a': 0.2, 'b': 0.1},
        },
        'renorm_operator': {
            'operator_status': 'proxy-renormalization-operator-stable-chart',
            'contraction_metrics': {'chart_radius_ratio': 0.7},
        },
        'fixed_point': {
            'theorem_status': 'proxy-fixed-point-iteration-contracting',
            'contraction_ratio_estimate': 0.6,
        },
        'enclosure': {
            'theorem_status': 'proxy-fixed-point-enclosure-validated',
            'invariance_margin': 0.05,
        },
        'splitting': {
            'theorem_status': 'proxy-spectral-splitting-identified',
            'domination_margin': 0.11,
        },
        'stable_manifold': {
            'theorem_status': 'proxy-stable-manifold-chart-identified' if strong_stable else 'proxy-stable-manifold-chart-mixed',
            'stable_chart_radius': 0.03,
            'graph_transform_contraction': 0.81 if strong_stable else 1.03,
        },
        'coarse_bridge': {
            'theorem_status': 'proxy-critical-surface-family-bridge-identified',
            'critical_surface_gap': 0.04,
        },
        'validated_bridge': {
            'theorem_status': 'proxy-critical-surface-window-bridge-validated',
            'theorem_flags': {
                'localized_transversality_window': True,
                'derivative_floor_positive': True,
                'window_narrow_enough': True,
            },
            'localized_center': 1.0,
            'localized_radius': 0.02,
            'transversality_margin': 0.07,
            'derivative_floor_proxy': 0.05,
        },
    }



def _patch_all(monkeypatch, strong_stable: bool = True):
    from kam_theorem_suite import theorem_i_ii_workstream_lift as mod

    payloads = _base_payloads(strong_stable=strong_stable)
    monkeypatch.setattr(mod, 'build_universality_class_certificate', lambda *a, **k: _FakeCert(payloads['universality']))
    monkeypatch.setattr(mod, 'build_renormalization_class_certificate', lambda *a, **k: _FakeCert(payloads['renorm_class']))
    monkeypatch.setattr(mod, 'build_renormalization_operator_certificate', lambda *a, **k: _FakeCert(payloads['renorm_operator']))
    monkeypatch.setattr(mod, 'build_renormalization_fixed_point_certificate', lambda *a, **k: _FakeCert(payloads['fixed_point']))
    monkeypatch.setattr(mod, 'build_fixed_point_enclosure_certificate', lambda *a, **k: _FakeCert(payloads['enclosure']))
    monkeypatch.setattr(mod, 'build_spectral_splitting_certificate', lambda *a, **k: _FakeCert(payloads['splitting']))
    monkeypatch.setattr(mod, 'build_stable_manifold_chart_certificate', lambda *a, **k: _FakeCert(payloads['stable_manifold']))
    monkeypatch.setattr(mod, 'build_critical_surface_bridge_certificate', lambda *a, **k: _FakeCert(payloads['coarse_bridge']))
    monkeypatch.setattr(mod, 'build_validated_critical_surface_bridge_certificate', lambda *a, **k: _FakeCert(payloads['validated_bridge']))



def test_theorem_i_ii_workstream_smoke_default_family():
    cert = build_golden_theorem_i_ii_workstream_lift_certificate(family=HarmonicFamily()).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-i-ii-workstream-lift-conditional-strong'
    assert cert['open_hypotheses'] == []
    assert cert['active_assumptions'] == []
    assert cert['validated_renormalization_package_promotion']['theorem_status'] == 'validated-renormalization-package-promotion-theorem-discharged'
    assert cert['critical_surface_threshold_identification_promotion']['theorem_status'] == 'critical-surface-threshold-promotion-theorem-discharged'
    assert 'hypotheses' in cert
    assert 'assumptions' in cert



def test_theorem_i_ii_workstream_front_complete(monkeypatch):
    _patch_all(monkeypatch, strong_stable=True)
    cert = build_golden_theorem_i_ii_workstream_lift_certificate(family=HarmonicFamily()).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-i-ii-workstream-lift-conditional-strong'
    assert cert['open_hypotheses'] == []
    assert cert['active_assumptions'] == []
    assert cert['validated_universality_class_theorem_promotion']['theorem_status'] == 'validated-universality-class-theorem-promotion-discharged'
    assert cert['validated_renormalization_package_promotion']['theorem_status'] == 'validated-renormalization-package-promotion-theorem-discharged'
    assert cert['validated_critical_surface_theorem_promotion']['theorem_status'] == 'validated-critical-surface-theorem-promotion-discharged'



def test_theorem_i_ii_workstream_conditional_strong(monkeypatch):
    _patch_all(monkeypatch, strong_stable=True)
    cert = build_golden_theorem_i_ii_workstream_lift_certificate(
        family=HarmonicFamily(),
        assume_theorem_grade_banach_manifold_universality_class=True,
        assume_validated_true_renormalization_fixed_point_package=True,
        assume_golden_stable_manifold_is_true_critical_surface=True,
        assume_family_chart_crossing_identifies_true_critical_parameter=True,
        assume_golden_critical_surface_transversality_on_class=True,
    ).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-i-ii-workstream-lift-conditional-strong'
    assert cert['active_assumptions'] == []
    assert cert['validated_renormalization_package_promotion']['theorem_status'] == 'validated-renormalization-package-promotion-theorem-discharged'
    assert cert['validated_critical_surface_theorem_promotion']['theorem_status'] == 'validated-critical-surface-theorem-promotion-discharged'



def test_theorem_i_ii_workstream_partial_if_stable_chart_open(monkeypatch):
    _patch_all(monkeypatch, strong_stable=False)
    cert = build_golden_theorem_i_ii_workstream_lift_certificate(family=HarmonicFamily()).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-i-ii-workstream-lift-conditional-partial'
    assert 'theorem_ii_proxy_stable_manifold_chart_identified' in cert['open_hypotheses']



def test_theorem_i_ii_workstream_reports_roundtrip(monkeypatch):
    _patch_all(monkeypatch, strong_stable=True)
    rep = build_golden_theorem_i_ii_workstream_lift_report(family=HarmonicFamily())
    rep2 = build_golden_theorem_i_ii_report(family=HarmonicFamily())
    assert rep['theorem_status'] == 'golden-theorem-i-ii-workstream-lift-conditional-strong'
    assert rep2['theorem_status'] == 'golden-theorem-i-ii-workstream-lift-conditional-strong'


def test_theorem_i_ii_workstream_auto_promotes_validated_critical_surface_theorem(monkeypatch):
    _patch_all(monkeypatch, strong_stable=True)
    cert = build_golden_theorem_i_ii_workstream_lift_certificate(family=HarmonicFamily()).to_dict()
    summary = cert['critical_surface_identification_summary']
    residual = cert['residual_burden_summary']
    assert summary['threshold_identification_ready'] is True
    validated_cs_promotion = cert['validated_critical_surface_theorem_promotion']
    assert cert['validated_universality_class_theorem_promotion']['theorem_status'] == 'validated-universality-class-theorem-promotion-discharged'
    assert validated_cs_promotion['theorem_status'] == 'validated-critical-surface-theorem-promotion-discharged'
    assert validated_cs_promotion['theorem_flags']['workstream_specific_critical_surface_theorem_available'] is True
    assert validated_cs_promotion['absorbed_package_specific_assumptions'] == [
        'golden_stable_manifold_is_true_critical_surface',
        'family_chart_crossing_identifies_true_critical_parameter',
        'golden_critical_surface_transversality_on_class',
    ]
    assert cert['critical_surface_threshold_identification_discharge']['theorem_status'] == 'critical-surface-threshold-identification-discharge-conditional-strong'
    assert cert['critical_surface_threshold_identification_promotion']['theorem_status'] == 'critical-surface-threshold-promotion-theorem-discharged'
    assert cert['active_assumptions'] == []
    assert residual['status'] == 'critical-surface-threshold-promotion-theorem-discharged'
    assert residual['promotion_theorem_available'] is True
    assert residual['upstream_context_assumptions'] == []


def test_theorem_i_ii_workstream_auto_promotes_validated_renormalization_package(monkeypatch):
    _patch_all(monkeypatch, strong_stable=True)
    cert = build_golden_theorem_i_ii_workstream_lift_certificate(family=HarmonicFamily()).to_dict()
    renorm_promotion = cert['validated_renormalization_package_promotion']
    assert cert['validated_universality_class_theorem_promotion']['theorem_flags']['theorem_grade_banach_manifold_universality_class_available'] is True
    assert renorm_promotion['theorem_flags']['validated_true_renormalization_fixed_point_package_available'] is True
    assert renorm_promotion['residual_burden_summary']['status'] == 'validated-renormalization-package-discharged'
    assert 'validated_true_renormalization_fixed_point_package' not in cert['active_assumptions']
    assert cert['residual_burden_summary']['status'] == 'critical-surface-threshold-promotion-theorem-discharged'


def test_default_workstream_now_auto_closes_through_stable_radius_promotion():
    cert = build_golden_theorem_i_ii_workstream_lift_certificate(family=HarmonicFamily()).to_dict()
    stable = cert['stable_manifold_certificate']
    renorm = cert['validated_renormalization_package_promotion']
    critical_surface = cert['validated_critical_surface_theorem_promotion']
    threshold = cert['critical_surface_threshold_identification_promotion']
    assert stable['theorem_status'] == 'proxy-stable-manifold-chart-identified'
    assert stable['stable_chart_radius'] > cert['validated_critical_surface_bridge_certificate']['localized_radius']
    assert renorm['theorem_status'] == 'validated-renormalization-package-promotion-theorem-discharged'
    assert critical_surface['theorem_status'] == 'validated-critical-surface-theorem-promotion-discharged'
    assert threshold['theorem_status'] == 'critical-surface-threshold-promotion-theorem-discharged'
    assert cert['residual_burden_summary']['status'] == 'critical-surface-threshold-promotion-theorem-discharged'
