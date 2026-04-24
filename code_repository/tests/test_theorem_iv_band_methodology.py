from __future__ import annotations
import numpy as np
from kam_theorem_suite.golden_supercritical import generate_golden_convergent_specs
from kam_theorem_suite.theorem_iv_band_methodology import methodology_localize_hyperbolic_band, predict_theorem_iv_band_center, get_theorem_iv_band_profile
from kam_theorem_suite.standard_map import HarmonicFamily

def test_predict_band_center_uses_previous_band_centers():
    spec = generate_golden_convergent_specs(keep_last=1)[0]
    previous = [
        {'q': 21, 'band_report': {'best_band': {'K_lo': 1.01, 'K_hi': 1.03}}},
        {'q': 34, 'band_report': {'best_band': {'K_lo': 1.011, 'K_hi': 1.031}}},
    ]
    pred = predict_theorem_iv_band_center(spec, previous_entry_dicts=previous)
    assert pred['predictive_center'] >= float(spec.band_search_lo)
    assert pred['predictive_center'] <= float(spec.band_search_hi)

def test_methodology_localize_hyperbolic_band_success(monkeypatch):
    spec = generate_golden_convergent_specs(keep_last=1)[0]
    family = HarmonicFamily()
    def fake_validated_branch_state(*, K, **kwargs):
        residue = -0.32 - 5.0 * (float(K) - 1.0)
        return {'success': True, 'candidate': True, 'strict': True, 'x': np.array([float(K), residue]), 'residue_center': residue, 'abs_residue_interval_lo': abs(residue), 'abs_residue_interval_hi': abs(residue), 'message': 'mock strict validation'}
    monkeypatch.setattr('kam_theorem_suite.theorem_iv_band_methodology.validated_branch_state', fake_validated_branch_state)
    out = methodology_localize_hyperbolic_band(spec, family=family, target_residue=0.25, crossing_root_hi=float(spec.crossing_K_hi), previous_entry_dicts=[], profile=get_theorem_iv_band_profile(spec.p, spec.q))
    assert out['proof_ready'] is True
    assert out['status'] == 'theorem_mode_local_band'
    assert out['certificate']['certification_tier'] == 'theorem_mode_local_band'
