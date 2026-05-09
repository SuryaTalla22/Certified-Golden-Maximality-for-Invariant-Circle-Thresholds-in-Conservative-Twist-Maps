from __future__ import annotations
import json
from pathlib import Path
import numpy as np

from kam_theorem_suite.lower_param.phase5h_cohomology_frame_components import (
    cohomology_inverse_proof_object,
    frame_reducibility_proof_object,
    generate_phase5h_attachment,
    replay_phase5h_attachment,
)


def _write_json(p: Path, obj):
    p.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")


def test_cohomology_inverse_object_positive(tmp_path: Path):
    M = 64
    seed = tmp_path / "seed.npz"
    np.savez(seed, u=np.zeros(M), K=0.0, omega=(5**0.5 - 1) / 2)
    selected = {"cutoff_mode_native_units": 31, "cohomology_inverse_linf_resolved_upper": 1000.0, "small_divisor_min_denominator_lower": 1e-3}
    obj = cohomology_inverse_proof_object(seed, selected, {"formal_component_evidence": {}}, small_divisor_slack=1e-16)
    assert obj["component_ok"]
    assert obj["small_divisor_min_denominator_lower"] > 0
    assert obj["cohomology_inverse_linf_resolved_upper"] > 0


def test_frame_reducibility_object_ok():
    selected = {
        "Z_interval_upper": 0.2,
        "a21_linf": 1e-4,
        "upper_triangular_defect_linf_max": 1e-4,
        "a11_minus_1_linf": 1e-6,
        "a22_minus_1_linf": 1e-6,
        "source_frame_det_defect_linf": 1e-15,
        "target_frame_det_defect_linf": 1e-15,
        "twist_average": 1.0,
        "radius": 3e-5,
        "radii_relative_margin_interval_lower": 0.75,
    }
    obj = frame_reducibility_proof_object(selected, max_z=0.5)
    assert obj["component_ok"]
    assert obj["Z_interval_upper"] < 0.5


def test_generate_and_replay_phase5h(tmp_path: Path):
    M = 64
    seed = tmp_path / "seed.npz"
    np.savez(seed, u=np.zeros(M), K=0.0, omega=(5**0.5 - 1) / 2)
    cert = tmp_path / "cert.json"
    _write_json(cert, {"schema": "cert", "lower_anchor_K": 0.971635})
    selected = {
        "K": 0.971635,
        "M": M,
        "nu": 1.001,
        "radius": 3e-5,
        "cutoff_spec": "full",
        "tail_start_frac": 0.9,
        "cutoff_mode_native_units": 31,
        "small_divisor_min_denominator_lower": 1e-3,
        "cohomology_inverse_linf_resolved_upper": 1000.0,
        "Z_interval_upper": 0.2,
        "a21_linf": 1e-4,
        "upper_triangular_defect_linf_max": 1e-4,
        "a11_minus_1_linf": 1e-6,
        "a22_minus_1_linf": 1e-6,
        "source_frame_det_defect_linf": 1e-15,
        "target_frame_det_defect_linf": 1e-15,
        "twist_average": 1.0,
        "radii_relative_margin_interval_lower": 0.75,
    }
    base = tmp_path / "base.json"
    _write_json(base, {
        "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "formal_evidence": {
            "outward_rounded_residual_proof": True,
            "small_divisor_proof": True,
        },
        "formal_component_evidence": {
            "small_divisor_proof": {"small_divisor_min_denominator_lower": 1e-3}
        },
        "selected_constants": selected,
    })
    out = tmp_path / "out"
    summary = generate_phase5h_attachment(cert, base, seed, None, out, 1.001, 3e-5, "full", 0.9, 0.25, 0.5, force=True)
    assert summary["overall_component_passed"]
    att = out / "phase5h_formal_interval_attachment_COMPONENTS.json"
    replay = replay_phase5h_attachment(cert, att, seed, tmp_path / "replay", 0.971635, 1.001, 3e-5, "full", 0.9, 0.25, 0.5, force=True)
    assert replay["passed"]
    assert "cohomology_inverse_proof" in replay["formal_evidence_true_flags"]
    assert "frame_reducibility_proof" in replay["formal_evidence_true_flags"]
