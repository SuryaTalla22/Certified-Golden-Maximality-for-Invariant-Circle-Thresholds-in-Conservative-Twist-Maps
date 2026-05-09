from __future__ import annotations

import json
from pathlib import Path

from kam_theorem_suite.lower_param.phase5e_promotion_gate import (
    ATTACHMENT_SCHEMA,
    GateThresholds,
    _sha256_file,
    run_phase5e_promotion_gate,
)


def _cert() -> dict:
    return {
        "schema": "theorem_iii_trackb_phase5d_certificate_scaffold_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "statement": {"lower_anchor_K": 0.971635, "omega": "golden"},
        "selected_candidate": {
            "K": 0.971635,
            "M": 8192,
            "nu": 1.001,
            "cutoff_spec": "full",
            "tail_start_frac": 0.9,
            "radius": 3e-5,
            "Y_interval_upper": 7e-8,
            "Z_interval_upper": 0.23,
            "Q_interval_upper": 551.0,
            "radii_margin_interval_lower": 2.2e-5,
            "radii_relative_margin_interval_lower": 0.75,
            "small_divisor_min_denominator_lower": 1.0e-3,
            "cohomology_inverse_linf_resolved_upper": 920.0,
        },
        "active_assumptions": ["not formal"],
        "open_hypotheses": ["needs formal attachment"],
    }


def test_phase5e_rejects_scaffold_without_formal_attachment(tmp_path: Path) -> None:
    cp = tmp_path / "cert.json"
    cp.write_text(json.dumps(_cert()), encoding="utf-8")
    out = tmp_path / "out"
    summary = run_phase5e_promotion_gate(
        certificate_path=cp,
        out_dir=out,
        thresholds=GateThresholds(require_nu=1.001, require_radius=3e-5, require_cutoff="full", require_tail_start=0.9),
        force=True,
    )
    assert summary["decision"] == "REJECT_FAIL_CLOSED"
    assert summary["fail_closed_passed"] is True
    assert summary["scaffold_replay_ok_for_gate"] is True
    assert summary["formal_attachment_ok"] is False
    assert summary["theorem_facing"] is False
    assert summary["promotion_allowed"] is False
    assert summary["negative_controls_passed"] is True


def test_phase5e_can_promote_only_with_mock_formal_attachment(tmp_path: Path) -> None:
    cp = tmp_path / "cert.json"
    cp.write_text(json.dumps(_cert()), encoding="utf-8")
    att = {
        "schema": ATTACHMENT_SCHEMA,
        "certificate_sha256": _sha256_file(cp),
        "formal_interval_backend": True,
        "independent_replay_passed": True,
        "outward_rounded_residual_proof": True,
        "small_divisor_proof": True,
        "cohomology_inverse_proof": True,
        "frame_reducibility_proof": True,
        "nonlinear_bound_proof": True,
        "tail_bound_proof": True,
        "branch_chart_compatibility_proof": True,
        "final_graph_consumption_proof": True,
        "nu": 1.001,
        "tail_start_frac": 0.9,
        "radius": 3e-5,
        "Y_interval_upper": 8e-8,
        "Z_interval_upper": 0.24,
        "Q_interval_upper": 560.0,
        "radii_margin_interval_lower": 2.0e-5,
        "radii_relative_margin_interval_lower": 0.70,
    }
    ap = tmp_path / "attachment.json"
    ap.write_text(json.dumps(att), encoding="utf-8")
    summary = run_phase5e_promotion_gate(
        certificate_path=cp,
        formal_attachment_path=ap,
        out_dir=tmp_path / "out2",
        thresholds=GateThresholds(require_nu=1.001, require_radius=3e-5, require_cutoff="full", require_tail_start=0.9),
        force=True,
    )
    assert summary["decision"] == "PROMOTE"
    assert summary["theorem_facing"] is True
    assert summary["promotion_allowed"] is True


def test_phase5e_bad_attachment_is_rejected(tmp_path: Path) -> None:
    cp = tmp_path / "cert.json"
    cp.write_text(json.dumps(_cert()), encoding="utf-8")
    ap = tmp_path / "bad_attachment.json"
    ap.write_text(json.dumps({"schema": ATTACHMENT_SCHEMA, "certificate_sha256": "wrong"}), encoding="utf-8")
    summary = run_phase5e_promotion_gate(certificate_path=cp, formal_attachment_path=ap, out_dir=tmp_path / "out", force=True)
    assert summary["decision"] == "REJECT_FAIL_CLOSED"
    assert summary["formal_attachment_ok"] is False
