from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from kam_theorem_suite.audit.lower_anchor_phase2n import (
    Phase2NScore,
    atomic_write_json,
    resample_periodic_samples,
    score_key,
    summarize_attempts,
)


def test_resample_periodic_samples_preserves_mean_and_length():
    x = np.sin(2.0 * np.pi * np.arange(16) / 16.0)
    y = resample_periodic_samples(x, 32)
    assert len(y) == 32
    assert abs(float(np.mean(y))) < 1e-12


def test_phase2n_score_prioritizes_theorem_margin():
    bad = Phase2NScore(False, -1.0, 1.0, 1.0, 1.0, 1.0, None, None, 1024, 1e-4)
    better = Phase2NScore(False, -0.1, 1.0, 1.0, 1.0, 1.0, None, None, 512, 1e-4)
    ready = Phase2NScore(True, 1e-9, 1.0, 1.0, 1.0, 1.0, None, None, 128, 1e-4)
    assert score_key(better) > score_key(bad)
    assert score_key(ready) > score_key(better)


def test_summarize_attempts_selects_best_by_phase2e_margin():
    attempts = [
        {
            "schema": "phase2n_single_N_attempt_v1",
            "status": "phase2n-diagnostic-single-N",
            "_path": "a.json",
            "config": {"segment_id": "s", "K_mid": 0.96, "oversample_factor": 64, "sigma_cap": 1e-4},
            "score": {"theorem_ready": False, "radii_margin": -3.0, "residual_Y": 1.0, "linear_Z": 1.0, "radius_r": 1.0, "tail_T": 1.0, "selected_N": 1024, "sigma": 1e-4, "failure_reasons": ["x"]},
        },
        {
            "schema": "phase2n_single_N_attempt_v1",
            "status": "phase2n-diagnostic-single-N",
            "_path": "b.json",
            "config": {"segment_id": "s", "K_mid": 0.96, "oversample_factor": 64, "sigma_cap": 1e-4},
            "score": {"theorem_ready": False, "radii_margin": -1.0, "residual_Y": 1.0, "linear_Z": 1.0, "radius_r": 1.0, "tail_T": 1.0, "selected_N": 512, "sigma": 1e-4, "failure_reasons": []},
        },
    ]
    summary = summarize_attempts(attempts)
    assert summary["best"]["path"] == "b.json"
    assert summary["attempt_count"] == 2
