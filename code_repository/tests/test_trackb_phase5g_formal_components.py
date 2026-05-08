from __future__ import annotations
import json
import math
from pathlib import Path

import numpy as np

from kam_theorem_suite.lower_param.phase5g_formal_components import (
    fft_resample_periodic_values,
    small_divisor_scan,
    residual_proof_object,
    generate_phase5g_attachment,
    replay_phase5g_attachment,
)


def test_fft_resample_constant_and_sine():
    M = 32
    x = np.arange(M) / M
    v = 2.0 + 0.25 * np.sin(2 * np.pi * x)
    w = fft_resample_periodic_values(v, 128)
    y = np.arange(128) / 128
    expected = 2.0 + 0.25 * np.sin(2 * np.pi * y)
    assert np.max(np.abs(w - expected)) < 1e-12


def test_small_divisor_golden_positive():
    omega = (math.sqrt(5) - 1) / 2
    obj = small_divisor_scan(omega, cutoff=100, slack=1e-16)
    assert obj["small_divisor_min_denominator_lower"] > 0
    assert obj["cohomology_inverse_linf_resolved_upper"] > 1
    assert obj["small_divisor_min_mode"] >= 1


def test_generate_and_replay_attachment(tmp_path: Path):
    M = 64
    u = np.zeros(M)
    seed = tmp_path / "seed.npz"
    np.savez(seed, u=u, K=0.0, omega=(math.sqrt(5) - 1) / 2)
    cert = tmp_path / "cert.json"
    cert.write_text(json.dumps({"schema": "cert", "lower_anchor_K": 0.971635}, sort_keys=True))
    base = tmp_path / "base.json"
    base.write_text(json.dumps({
        "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "formal_evidence": {},
        "selected_constants": {
            "K": 0.971635,
            "M": 64,
            "nu": 1.001,
            "radius": 3e-5,
            "cutoff_spec": "full",
            "tail_start_frac": 0.9,
            "Z_interval_upper": 0.2,
            "radii_relative_margin_interval_lower": 0.7,
            "cutoff_mode_native_units": 31,
            "residual_l1_nu_total_upper": 1e-8,
        },
    }, sort_keys=True))
    out = tmp_path / "out"
    summary = generate_phase5g_attachment(
        cert, base, seed, None, out, 1.001, 3e-5, "full", 0.9, 2, 1e-13, 1e-14, force=True
    )
    assert summary["component_checks"]["residual_component_ok"]
    assert summary["component_checks"]["small_divisor_component_ok"]
    att = out / "phase5g_formal_interval_attachment_COMPONENTS.json"
    replay = replay_phase5g_attachment(
        cert, att, seed, tmp_path / "replay", 0.971635, 1.001, 3e-5, "full", 0.9, 0.25, 0.5, 1e-13, 1e-14, force=True
    )
    assert replay["passed"]
    assert "outward_rounded_residual_proof" in replay["formal_evidence_true_flags"]
    assert "small_divisor_proof" in replay["formal_evidence_true_flags"]
