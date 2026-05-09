from __future__ import annotations

import json
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_phase2q_chain import (
    Phase2QConfig,
    assemble_phase2q_chain,
    build_phase2q_candidate,
)


def _candidate(path: Path, *, seg_id: str, lo: float, hi: float, margin: float = 1e-6) -> Path:
    data = {
        "schema": "phase2p_modewise_tail_candidate_v1",
        "theorem_facing": True,
        "promotion_allowed": True,
        "closure_level": "phase2p_modewise_tail_closure",
        "failure_fields": [],
        "anchor_segments": [
            {
                "segment_id": seg_id,
                "K_lo": lo,
                "K_hi": hi,
                "K_mid": 0.5 * (lo + hi),
                "theorem_ready": True,
            }
        ],
        "selected_phase2p_row": {
            "segment_id": seg_id,
            "theorem_ready": True,
            "radii_margin": margin,
            "tail_T": 2e-7,
            "allowable_tail_max": 8e-7,
            "sigma": 1e-6,
            "tail_cutoff": 2048,
            "model_name": "strict_modewise_tail_test",
            "failure_reasons": [],
        },
    }
    path.write_text(json.dumps(data))
    return path


def test_phase2q_closes_two_overlapping_segments(tmp_path: Path) -> None:
    p0 = _candidate(tmp_path / "c0.json", seg_id="c0", lo=0.0, hi=1.0)
    p1 = _candidate(tmp_path / "c1.json", seg_id="c1", lo=0.9999999, hi=2.0)
    cfg = Phase2QConfig(expected_start=0.0, expected_end=2.0, expected_regime_i_hi=0.0)
    result = assemble_phase2q_chain([p0, p1], cfg)
    assert result.theorem_facing is True
    assert result.promotion_allowed is True
    assert result.failure_fields == []
    assert result.min_overlap is not None and result.min_overlap > 0
    cand = build_phase2q_candidate(result)
    assert cand["closure_level"] == "phase2q_collar_chain_closure"
    assert cand["derived_booleans"]["chain_theorem_ready"] is True


def test_phase2q_rejects_gap(tmp_path: Path) -> None:
    p0 = _candidate(tmp_path / "c0.json", seg_id="c0", lo=0.0, hi=1.0)
    p1 = _candidate(tmp_path / "c1.json", seg_id="c1", lo=1.01, hi=2.0)
    result = assemble_phase2q_chain([p0, p1], Phase2QConfig(overlap_tolerance=1e-10))
    assert result.theorem_facing is False
    assert any("positive_gap" in f for f in result.failure_fields)


def test_phase2q_rejects_nonpromotable_segment(tmp_path: Path) -> None:
    p = _candidate(tmp_path / "bad.json", seg_id="bad", lo=0.0, hi=1.0)
    data = json.loads(p.read_text())
    data["promotion_allowed"] = False
    p.write_text(json.dumps(data))
    result = assemble_phase2q_chain([p], Phase2QConfig())
    assert result.theorem_facing is False
    assert any("candidate_not_promotion_allowed" in f for f in result.failure_fields)


def test_phase2q_rejects_tail_slack_failure(tmp_path: Path) -> None:
    p = _candidate(tmp_path / "bad_tail.json", seg_id="bad_tail", lo=0.0, hi=1.0)
    data = json.loads(p.read_text())
    data["selected_phase2p_row"]["tail_T"] = 9e-7
    data["selected_phase2p_row"]["allowable_tail_max"] = 8e-7
    p.write_text(json.dumps(data))
    result = assemble_phase2q_chain([p], Phase2QConfig())
    assert result.theorem_facing is False
    assert any("tail_bound_not_below_allowable_tail_max" in f for f in result.failure_fields)
