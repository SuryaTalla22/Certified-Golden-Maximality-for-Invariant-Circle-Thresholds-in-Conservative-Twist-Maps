import hashlib
import json
from pathlib import Path

from kam_theorem_suite.lower_param.phase6_final_integration import (
    REQUIRED_FORMAL_FLAGS,
    assemble_phase6_final_integration,
    replay_phase6_final_integration,
)


def write(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")


def test_phase6_assembles_and_replays_final_artifact(tmp_path):
    cert = tmp_path / "cert.json"
    write(cert, {"schema": "cert", "lower_anchor_K": 0.971635})
    h = hashlib.sha256(cert.read_bytes()).hexdigest()
    constants = {
        "K": 0.971635,
        "M": 8192,
        "nu": 1.001,
        "radius": 3e-5,
        "cutoff_spec": "full",
        "tail_start_frac": 0.90,
        "Y_interval_upper": 7e-8,
        "Z_interval_upper": 0.23,
        "Q_interval_upper": 551.0,
        "radii_margin_interval_lower": 2.2e-5,
        "radii_relative_margin_interval_lower": 0.75,
        "radii_lhs_interval_upper": 7.4e-6,
        "small_divisor_min_denominator_lower": 1e-3,
        "cohomology_inverse_linf_resolved_upper": 920.0,
    }
    att = tmp_path / "att.json"
    write(att, {
        "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
        "certificate_sha256": h,
        "theorem_facing": True,
        "promotion_allowed": True,
        "formal_attachment_ok": True,
        "formal_evidence": {k: True for k in REQUIRED_FORMAL_FLAGS},
        "selected_constants": constants,
    })
    p5e = tmp_path / "p5e.json"
    write(p5e, {
        "decision": "PROMOTE",
        "formal_attachment_ok": True,
        "theorem_replay_accepted": True,
        "theorem_facing": True,
        "promotion_allowed": True,
        "failed_formal_attachment_checks": [],
        "negative_controls_passed": True,
        "selected_constants": constants,
    })
    out = tmp_path / "out"
    summary = assemble_phase6_final_integration(
        certificate_path=str(cert),
        promoted_attachment_path=str(att),
        phase5e_summary_path=str(p5e),
        theorem_i_artifact=None,
        theorem_ii_artifact=None,
        theorem_iv_artifact=None,
        required_min_lower_anchor_k=0.971635,
        require_nu=1.001,
        require_radius=3e-5,
        require_cutoff="full",
        require_tail_start=0.90,
        min_relative_margin=0.25,
        max_z=0.5,
        downstream_output_root=str(tmp_path / "regen"),
        out_dir=str(out),
        force=True,
    )
    assert summary["passed"] is True
    final = out / "theorem_iii_trackb_PHASE6_FINAL_LOWER_ANCHOR_CERTIFICATE.json"
    assert final.exists()
    replay = replay_phase6_final_integration(
        final_artifact_path=str(final),
        theorem_i_artifact=None,
        theorem_ii_artifact=None,
        theorem_iv_artifact=None,
        required_min_lower_anchor_k=0.971635,
        require_nu=1.001,
        require_radius=3e-5,
        require_cutoff="full",
        require_tail_start=0.90,
        min_relative_margin=0.25,
        max_z=0.5,
        out_dir=str(tmp_path / "replay"),
        force=True,
    )
    assert replay["passed"] is True


def test_phase6_blocks_unpromoted_attachment(tmp_path):
    cert = tmp_path / "cert.json"
    write(cert, {"lower_anchor_K": 0.971635})
    h = hashlib.sha256(cert.read_bytes()).hexdigest()
    att = tmp_path / "att.json"
    write(att, {
        "certificate_sha256": h,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "formal_evidence": {k: True for k in REQUIRED_FORMAL_FLAGS},
        "selected_constants": {"K": 0.971635, "nu": 1.001, "radius": 3e-5, "cutoff_spec": "full", "tail_start_frac": 0.9, "radii_relative_margin_interval_lower": 0.75, "Z_interval_upper": 0.23, "radii_margin_interval_lower": 1e-5, "Y_interval_upper": 1e-7, "Q_interval_upper": 500.0},
    })
    p5e = tmp_path / "p5e.json"
    write(p5e, {"decision": "REJECT_FAIL_CLOSED", "formal_attachment_ok": False, "theorem_replay_accepted": False, "theorem_facing": False, "promotion_allowed": False, "failed_formal_attachment_checks": ["formal_interval_backend"], "negative_controls_passed": True})
    summary = assemble_phase6_final_integration(
        certificate_path=str(cert), promoted_attachment_path=str(att), phase5e_summary_path=str(p5e),
        theorem_i_artifact=None, theorem_ii_artifact=None, theorem_iv_artifact=None,
        required_min_lower_anchor_k=0.971635, require_nu=1.001, require_radius=3e-5,
        require_cutoff="full", require_tail_start=0.9, min_relative_margin=0.25, max_z=0.5,
        downstream_output_root=str(tmp_path / "regen"), out_dir=str(tmp_path / "out"), force=True)
    assert summary["passed"] is False
    assert summary["failed_checks"]
