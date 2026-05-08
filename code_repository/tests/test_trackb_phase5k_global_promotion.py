import json
from pathlib import Path

from kam_theorem_suite.lower_param.phase5k_global_promotion import (
    REQUIRED_COMPONENT_FLAGS,
    build_global_backend_candidate,
    independent_replay_and_promote,
)


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")


def test_phase5k_promotes_only_after_independent_replay(tmp_path):
    cert = tmp_path / "cert.json"
    write(cert, {"schema": "cert", "lower_anchor_K": 0.971635})
    import hashlib
    h = hashlib.sha256(cert.read_bytes()).hexdigest()
    att = tmp_path / "att.json"
    fe = {k: True for k in REQUIRED_COMPONENT_FLAGS}
    fe["formal_interval_backend"] = False
    fe["independent_replay_passed"] = False
    write(att, {
        "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
        "certificate_sha256": h,
        "formal_evidence": fe,
        "selected_constants": {
            "K": 0.971635,
            "nu": 1.001,
            "radius": 3e-5,
            "cutoff_spec": "full",
            "tail_start_frac": 0.9,
            "Y_interval_upper": 7e-8,
            "Z_interval_upper": 0.22,
            "Q_interval_upper": 551.0,
            "radii_margin_interval_lower": 2e-5,
            "radii_relative_margin_interval_lower": 0.75,
            "small_divisor_min_denominator_lower": 1e-3,
        },
    })
    out1 = tmp_path / "out1"
    c1 = build_global_backend_candidate(
        certificate_path=str(cert), base_attachment_path=str(att),
        required_min_lower_anchor_k=0.971635, require_nu=1.001,
        require_radius=3e-5, require_cutoff="full", require_tail_start=0.9,
        min_relative_margin=0.25, max_z=0.5, out_dir=str(out1), force=True)
    assert c1["passed"] is True
    assert "formal_interval_backend" in c1["formal_evidence_true_flags"]
    assert c1["missing_formal_evidence_flags"] == ["independent_replay_passed"]

    out2 = tmp_path / "out2"
    c2 = independent_replay_and_promote(
        certificate_path=str(cert),
        backend_candidate_path=str(out1 / "phase5k_global_backend_candidate.json"),
        attachment_candidate_path=str(out1 / "phase5k_formal_interval_attachment_BACKEND_CANDIDATE.json"),
        required_min_lower_anchor_k=0.971635, require_nu=1.001,
        require_radius=3e-5, require_cutoff="full", require_tail_start=0.9,
        min_relative_margin=0.25, max_z=0.5, out_dir=str(out2), force=True)
    assert c2["passed"] is True
    assert c2["missing_formal_evidence_flags"] == []
    assert c2["formal_attachment_ok"] is True


def test_phase5k_rejects_missing_prior_component(tmp_path):
    cert = tmp_path / "cert.json"
    write(cert, {"schema": "cert", "lower_anchor_K": 0.971635})
    import hashlib
    h = hashlib.sha256(cert.read_bytes()).hexdigest()
    fe = {k: True for k in REQUIRED_COMPONENT_FLAGS}
    fe["tail_bound_proof"] = False
    att = tmp_path / "att.json"
    write(att, {"schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1", "certificate_sha256": h, "formal_evidence": fe, "selected_constants": {"K":0.971635,"nu":1.001,"radius":3e-5,"cutoff_spec":"full","tail_start_frac":0.9,"Y_interval_upper":1e-8,"Z_interval_upper":0.2,"Q_interval_upper":1.0,"radii_margin_interval_lower":1e-5,"radii_relative_margin_interval_lower":0.5,"small_divisor_min_denominator_lower":1e-3}})
    c = build_global_backend_candidate(certificate_path=str(cert), base_attachment_path=str(att), required_min_lower_anchor_k=0.971635, require_nu=1.001, require_radius=3e-5, require_cutoff="full", require_tail_start=0.9, min_relative_margin=0.25, max_z=0.5, out_dir=str(tmp_path / "out"), force=True)
    assert c["passed"] is False
    assert "component_flag_tail_bound_proof_true" in c["failed_checks"]
