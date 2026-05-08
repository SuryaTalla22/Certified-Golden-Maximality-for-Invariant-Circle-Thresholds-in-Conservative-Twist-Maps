from __future__ import annotations

import json
from pathlib import Path

from kam_theorem_suite.lower_param.phase5i_nonlinear_tail import (
    decimal_margin,
    ensure_formal_evidence,
    find_backend_record,
    raw_sha256,
)


def test_decimal_margin_positive():
    d = decimal_margin(7.1e-8, 0.23, 551.0, 3e-5)
    assert d["positive_recomputed_margin"] is True
    assert "recomputed_margin_decimal" in d


def test_find_backend_record_exact_config():
    summary = {
        "top_candidates": [
            {
                "K": 0.971635,
                "M": 8192,
                "nu": 1.001,
                "radius": 3e-5,
                "cutoff_spec": "full",
                "tail_start_frac": 0.9,
                "Y_interval_upper": 7e-8,
                "Z_interval_upper": 0.23,
                "Q_interval_upper": 551.0,
                "radii_margin_interval_lower": 2e-5,
                "radii_relative_margin_interval_lower": 0.75,
                "tail_residual_component_upper": 4e-10,
            }
        ]
    }
    r = find_backend_record(
        summary,
        require_nu=1.001,
        require_radius=3e-5,
        require_cutoff="full",
        require_tail_start=0.9,
        min_relative_margin=0.25,
        max_z=0.5,
    )
    assert r["cutoff_spec"] == "full"


def test_formal_evidence_literal_true_only():
    a = {"formal_evidence": {"nonlinear_bound_proof": "true", "tail_bound_proof": True}}
    fe = ensure_formal_evidence(a)
    assert fe["nonlinear_bound_proof"] is False
    assert fe["tail_bound_proof"] is True
    assert fe["formal_interval_backend"] is False


def test_raw_sha256(tmp_path: Path):
    p = tmp_path / "x.json"
    p.write_bytes(b"abc")
    assert raw_sha256(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_phase5i_json_sanitizer_converts_optional_nan():
    from kam_theorem_suite.lower_param.phase5i_nonlinear_tail import sanitize_json_value, count_nonfinite_json_values
    obj = {"good": 1.0, "bad": float("nan"), "nested": [float("inf"), -float("inf"), 2.0]}
    assert count_nonfinite_json_values(obj) == 3
    clean = sanitize_json_value(obj)
    assert clean == {"good": 1.0, "bad": None, "nested": [None, None, 2.0]}
