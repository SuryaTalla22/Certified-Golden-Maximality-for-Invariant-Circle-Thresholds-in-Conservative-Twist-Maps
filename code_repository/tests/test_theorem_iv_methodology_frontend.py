from __future__ import annotations

import numpy as np

from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.theorem_iv_methodology import (
    get_theorem_iv_methodology_profile,
    predict_theorem_iv_crossing_center,
)
import kam_theorem_suite.adaptive_incompatibility as ai


class _DummyReport:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


class _DummyAdaptive:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_theorem_iv_methodology_profiles_scale_with_q():
    low = get_theorem_iv_methodology_profile(13, 21)
    high = get_theorem_iv_methodology_profile(89, 144)
    ultra = get_theorem_iv_methodology_profile(144, 233)
    assert low.dps < high.dps <= ultra.dps
    assert low.targeted_center_margin > high.targeted_center_margin > ultra.targeted_center_margin
    assert high.targeted_points >= low.targeted_points


def test_predictive_center_uses_previous_entry_q_inverse_squared_fit():
    spec = ApproximantWindowSpec(89, 144, 0.9685, 0.9735, 1.02, 1.05, label='gold-89/144')
    previous = [
        {'q': 21, 'crossing_root_window_lo': 0.9698, 'crossing_root_window_hi': 0.9700},
        {'q': 34, 'crossing_root_window_lo': 0.9710, 'crossing_root_window_hi': 0.9712},
        {'q': 55, 'crossing_root_window_lo': 0.9685, 'crossing_root_window_hi': 0.9687},
    ]
    pred = predict_theorem_iv_crossing_center(spec, previous_entry_dicts=previous)
    assert pred['source'] == 'q^-2 extrapolation from previous entries'
    assert spec.crossing_K_lo <= pred['predictive_center'] <= spec.crossing_K_hi


def test_entry_certificate_uses_methodology_frontend_success(monkeypatch):
    spec = ApproximantWindowSpec(55, 89, 0.9685, 0.9735, 1.02, 1.05, label='gold-55/89')

    def fake_methodology(*args, **kwargs):
        return {
            'success': True,
            'proof_ready': True,
            'status': 'theorem_mode_local',
            'K_lo': 0.9691,
            'K_hi': 0.9692,
            'method': 'newton_local',
            'x_seed': [0.1, 0.2, 0.3],
            'scan_rows': [{'K': 0.96915}],
        }

    def fail_adaptive(*args, **kwargs):
        raise AssertionError('adaptive_localize_residue_crossing should not be called after proof-ready methodology success')

    def fake_band_report(*args, **kwargs):
        return _DummyReport({
            'accepted_windows': [],
            'rejected_windows': [],
            'longest_band_lo': None,
            'longest_band_hi': None,
            'status': 'no-certified-band',
        })

    monkeypatch.setattr(ai, 'methodology_localize_theorem_iv_crossing', fake_methodology)
    monkeypatch.setattr(ai, 'adaptive_localize_residue_crossing', fail_adaptive)
    monkeypatch.setattr(ai, 'build_supercritical_band_report', fake_band_report)

    entry = ai.build_adaptive_incompatibility_entry_certificate(spec, family=HarmonicFamily())
    assert entry.localized_crossing_source == 'methodology-theorem-window'
    assert entry.crossing_root_window_lo == 0.9691
    assert entry.crossing_root_window_hi == 0.9692
    assert entry.adaptive_crossing['status'] == 'theorem_mode_local'


def test_entry_certificate_uses_methodology_frontend_failure_to_narrow_and_seed(monkeypatch):
    spec = ApproximantWindowSpec(89, 144, 0.9685, 0.9735, 1.02, 1.05, label='gold-89/144')
    observed = {}

    def fake_methodology(*args, **kwargs):
        return {
            'success': False,
            'proof_ready': False,
            'status': 'fallback-required',
            'K_lo': 0.9690,
            'K_hi': 0.9693,
            'x_seed': [1.0, 2.0, 3.0],
            'scan_rows': [{'K': 0.9691}],
        }

    def fake_adaptive(*args, **kwargs):
        observed['K_lo'] = kwargs['K_lo'] if 'K_lo' in kwargs else args[2]
        observed['K_hi'] = kwargs['K_hi'] if 'K_hi' in kwargs else args[3]
        observed['initial_x_guess'] = kwargs.get('initial_x_guess')
        return _DummyAdaptive({
            'status': 'incomplete',
            'best_window': {},
            'windows': [],
            'analyzed_windows': 0,
            'successful_window_count': 0,
            'monotone_window_count': 0,
            'interval_newton_window_count': 0,
            'message': 'fallback adaptive path',
        })

    def fake_band_report(*args, **kwargs):
        observed['band_x_guess'] = kwargs.get('x_guess')
        return _DummyReport({
            'accepted_windows': [],
            'rejected_windows': [],
            'longest_band_lo': None,
            'longest_band_hi': None,
            'status': 'no-certified-band',
        })

    monkeypatch.setattr(ai, 'methodology_localize_theorem_iv_crossing', fake_methodology)
    monkeypatch.setattr(ai, 'adaptive_localize_residue_crossing', fake_adaptive)
    monkeypatch.setattr(ai, 'build_supercritical_band_report', fake_band_report)

    entry = ai.build_adaptive_incompatibility_entry_certificate(spec, family=HarmonicFamily())
    assert abs(observed['K_lo'] - 0.9690) < 1e-12
    assert abs(observed['K_hi'] - 0.9693) < 1e-12
    assert observed['initial_x_guess'] == [1.0, 2.0, 3.0]
    assert observed['band_x_guess'] == [1.0, 2.0, 3.0]
    assert entry.adaptive_crossing['methodology_frontend']['status'] == 'fallback-required'


def test_sequential_atlas_passes_previous_entries_into_methodology(monkeypatch):
    specs = [
        ApproximantWindowSpec(13, 21, 0.9685, 0.9735, 1.02, 1.05, label='gold-13/21'),
        ApproximantWindowSpec(21, 34, 0.9685, 0.9735, 1.02, 1.05, label='gold-21/34'),
        ApproximantWindowSpec(34, 55, 0.9685, 0.9735, 1.02, 1.05, label='gold-34/55'),
    ]
    seen_lengths = []

    def fake_entry(spec, family=None, **kwargs):
        seen_lengths.append(len(kwargs.get('previous_entry_dicts') or []))
        return ai.AdaptiveIncompatibilityAtlasEntry(
            p=spec.p, q=spec.q, label=spec.normalized_label(),
            crossing_window_input_lo=spec.crossing_K_lo, crossing_window_input_hi=spec.crossing_K_hi,
            band_search_lo=spec.band_search_lo, band_search_hi=spec.band_search_hi,
            adaptive_crossing={'status': 'theorem_mode_local', 'best_window': {'K_lo': spec.crossing_K_lo, 'K_hi': spec.crossing_K_hi}},
            localized_crossing_source='methodology-theorem-window',
            crossing_root_window_lo=spec.crossing_K_lo, crossing_root_window_hi=spec.crossing_K_hi,
            crossing_root_window_width=spec.crossing_K_hi - spec.crossing_K_lo,
            band_report={'accepted_windows': [], 'rejected_windows': [], 'longest_band_lo': None, 'longest_band_hi': None},
            hyperbolic_band_lo=None, hyperbolic_band_hi=None, hyperbolic_band_width=None,
            gap_from_crossing_to_band=None, status='adaptive-crossing-only', notes='stub',
        )

    monkeypatch.setattr(ai, 'build_adaptive_incompatibility_entry_certificate', fake_entry)
    ai.build_adaptive_incompatibility_atlas_certificate(specs, family=HarmonicFamily(), n_jobs=1)
    assert seen_lengths == [0, 1, 2]
