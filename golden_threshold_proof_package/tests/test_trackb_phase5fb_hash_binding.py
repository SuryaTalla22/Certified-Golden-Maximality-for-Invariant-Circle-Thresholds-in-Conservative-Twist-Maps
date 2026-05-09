from __future__ import annotations
import json
from pathlib import Path

from kam_theorem_suite.lower_param.phase5fb_hash_binding import (
    bind_certificate_hash,
    replay_hash_binding,
    sha256_file,
)


def test_phase5fb_binds_top_level_hash(tmp_path: Path):
    cert = tmp_path / "cert.json"
    cert.write_text(json.dumps({"schema": "cert", "x": 1}, sort_keys=True), encoding="utf-8")
    attachment = tmp_path / "attachment.json"
    payload = {
        "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "formal_evidence": {
            "formal_interval_backend": False,
            "independent_replay_passed": False,
            "outward_rounded_residual_proof": False,
            "small_divisor_proof": False,
            "cohomology_inverse_proof": False,
            "frame_reducibility_proof": False,
            "nonlinear_bound_proof": False,
            "tail_bound_proof": False,
            "branch_chart_compatibility_proof": False,
            "final_graph_consumption_proof": False,
        },
        "selected_constants": {
            "K": 0.971635,
            "M": 8192,
            "nu": 1.001,
            "radius": 3e-5,
            "cutoff_spec": "full",
            "tail_start_frac": 0.9,
            "Z_interval_upper": 0.2,
            "radii_relative_margin_interval_lower": 0.5,
        },
        "source_hashes": {"certificate_sha256": sha256_file(cert)},
    }
    attachment.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    out = tmp_path / "out"
    summary = bind_certificate_hash(certificate_path=cert, attachment_path=attachment, out_dir=out, force=True)
    bound = json.loads((out / "phase5f_formal_interval_attachment_CANDIDATE_HASH_BOUND.json").read_text())
    assert bound["certificate_sha256"] == sha256_file(cert)
    assert bound["certificate_binding"]["certificate_sha256"] == sha256_file(cert)
    assert summary["top_level_certificate_sha256_written"] is True


def test_phase5fb_replay_passes_hash_binding(tmp_path: Path):
    cert = tmp_path / "cert.json"
    cert.write_text(json.dumps({"schema": "cert", "x": [1, 2, 3]}, sort_keys=True), encoding="utf-8")
    attachment = tmp_path / "attachment.json"
    formal_evidence = {
        "formal_interval_backend": False,
        "independent_replay_passed": False,
        "outward_rounded_residual_proof": False,
        "small_divisor_proof": False,
        "cohomology_inverse_proof": False,
        "frame_reducibility_proof": False,
        "nonlinear_bound_proof": False,
        "tail_bound_proof": False,
        "branch_chart_compatibility_proof": False,
        "final_graph_consumption_proof": False,
    }
    payload = {
        "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "certificate_sha256": sha256_file(cert),
        "certificate_hash": sha256_file(cert),
        "source_hashes": {"certificate_sha256": sha256_file(cert)},
        "certificate_binding": {"certificate_sha256": sha256_file(cert)},
        "formal_evidence": formal_evidence,
        "selected_constants": {
            "K": 0.971635,
            "nu": 1.001,
            "radius": 3e-5,
            "cutoff_spec": "full",
            "tail_start_frac": 0.9,
            "Z_interval_upper": 0.2,
            "radii_relative_margin_interval_lower": 0.5,
        },
    }
    attachment.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    summary = replay_hash_binding(certificate_path=cert, attachment_path=attachment, out_dir=tmp_path / "replay", force=True)
    assert summary["passed"] is True
    assert summary["missing_formal_evidence_flags"] == []
