from __future__ import annotations
from kam_theorem_suite.supercritical_bands import build_supercritical_band_report
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.hyperbolicity_certifier import certify_sustained_hyperbolic_tail

def test_supercritical_band_report_returns_early_on_methodology_success(monkeypatch):
    def fake_methodology(*args, **kwargs):
        return {'proof_ready': True, 'certificate': {'K_lo': 1.01, 'K_hi': 1.02, 'width': 0.01, 'regime': 'negative-hyperbolic', 'residue_interval_lo': -0.4, 'residue_interval_hi': -0.3, 'abs_residue_interval_lo': 0.3, 'abs_residue_interval_hi': 0.4, 'trace_abs_lower_bound': 3.2, 'hyperbolicity_margin': 1.2, 'g_interval_lo': 0.05, 'g_interval_hi': 0.15, 'gprime_interval_lo': 1.0, 'gprime_interval_hi': 2.0, 'certified_hyperbolic': True, 'certified_above_target': True, 'certification_tier': 'theorem_mode_local_band', 'message': 'mock band'}}
    def fail_if_called(*args, **kwargs):
        raise AssertionError('wide recursive interval band scan should not run after local methodology success')
    monkeypatch.setattr('kam_theorem_suite.supercritical_bands.methodology_localize_hyperbolic_band', fake_methodology)
    monkeypatch.setattr('kam_theorem_suite.supercritical_bands.certify_hyperbolic_window', fail_if_called)
    d = build_supercritical_band_report(p=13, q=21, K_lo=1.0, K_hi=1.05, family=HarmonicFamily(), use_methodology_frontend=True).to_dict()
    assert d['status'] == 'certified-local-band'
    assert d['certified_band_count'] == 1
    assert abs(d['best_band']['width'] - 0.01) < 1e-12

def test_hyperbolic_tail_accepts_theorem_mode_local_crossings():
    d = certify_sustained_hyperbolic_tail([
        {'q': 21, 'label': 'q=21', 'crossing_certificate': {'certification_tier': 'theorem_mode_local'}, 'crossing_root_window_lo': 0.97, 'crossing_root_window_hi': 0.971, 'hyperbolic_band_lo': 1.01, 'hyperbolic_band_hi': 1.02, 'gap_from_crossing_to_band': 0.039},
        {'q': 34, 'label': 'q=34', 'crossing_certificate': {'certification_tier': 'theorem_mode_local'}, 'crossing_root_window_lo': 0.971, 'crossing_root_window_hi': 0.972, 'hyperbolic_band_lo': 1.011, 'hyperbolic_band_hi': 1.021, 'gap_from_crossing_to_band': 0.039},
    ], min_tail_members=2).to_dict()
    assert d['tail_member_count'] == 2
