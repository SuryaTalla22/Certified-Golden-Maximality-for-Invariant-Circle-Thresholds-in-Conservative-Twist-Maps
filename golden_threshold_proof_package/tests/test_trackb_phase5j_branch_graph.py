from __future__ import annotations
import json
from pathlib import Path

from kam_theorem_suite.lower_param.phase5j_branch_graph import (
    generate_phase5j_attachment,
    replay_phase5j_attachment,
)


def _write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _base_attachment():
    return {
        "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "certificate_sha256": "will_be_replaced",
        "selected_constants": {
            "K": 0.971635,
            "M": 8192,
            "nu": 1.001,
            "radius": 3e-5,
            "cutoff_spec": "full",
            "tail_start_frac": 0.9,
            "Z_interval_upper": 0.23,
            "radii_relative_margin_interval_lower": 0.75,
            "radii_margin_interval_lower": 2.2e-5,
        },
        "formal_evidence": {
            "outward_rounded_residual_proof": True,
            "small_divisor_proof": True,
            "cohomology_inverse_proof": True,
            "frame_reducibility_proof": True,
            "nonlinear_bound_proof": True,
            "tail_bound_proof": True,
            "branch_chart_compatibility_proof": False,
            "final_graph_consumption_proof": False,
            "formal_interval_backend": False,
            "independent_replay_passed": False,
        },
    }


def test_phase5j_generation_and_replay(tmp_path: Path):
    cert = {"schema": "cert", "family": "standard_sine_twist_map", "omega": "golden", "lower_anchor_K": 0.971635}
    cert_path = tmp_path / "cert.json"
    _write(cert_path, cert)

    import hashlib
    h = hashlib.sha256(cert_path.read_bytes()).hexdigest()
    base = _base_attachment()
    base["certificate_sha256"] = h
    base_path = tmp_path / "base.json"
    _write(base_path, base)

    out_dir = tmp_path / "gen"
    s = generate_phase5j_attachment(
        certificate_path=str(cert_path),
        base_attachment_path=str(base_path),
        required_min_lower_anchor_k=0.971635,
        require_nu=1.001,
        require_radius=3e-5,
        require_cutoff="full",
        require_tail_start=0.90,
        expected_family="standard_sine_twist_map",
        expected_omega="golden",
        min_relative_margin=0.25,
        max_z=0.5,
        out_dir=str(out_dir),
        force=True,
    )
    assert s["passed"]["branch_chart_component_ok"] is True
    assert "branch_chart_compatibility_proof" in s["formal_evidence_true_flags"]
    assert "final_graph_consumption_proof" in s["formal_evidence_true_flags"]
    assert "formal_interval_backend" in s["missing_formal_evidence_flags"]

    r = replay_phase5j_attachment(
        certificate_path=str(cert_path),
        attachment_path=str(out_dir / "phase5j_formal_interval_attachment_COMPONENTS.json"),
        required_min_lower_anchor_k=0.971635,
        require_nu=1.001,
        require_radius=3e-5,
        require_cutoff="full",
        require_tail_start=0.90,
        expected_family="standard_sine_twist_map",
        expected_omega="golden",
        min_relative_margin=0.25,
        max_z=0.5,
        out_dir=str(tmp_path / "replay"),
        force=True,
    )
    assert r["passed"] is True
    assert not r["failed_checks"]


def test_phase5j_refuses_bad_family(tmp_path: Path):
    cert = {"schema": "cert", "family": "wrong_family", "omega": "golden", "lower_anchor_K": 0.971635}
    cert_path = tmp_path / "cert.json"
    _write(cert_path, cert)

    import hashlib
    h = hashlib.sha256(cert_path.read_bytes()).hexdigest()
    base = _base_attachment()
    base["certificate_sha256"] = h
    base_path = tmp_path / "base.json"
    _write(base_path, base)

    s = generate_phase5j_attachment(
        certificate_path=str(cert_path),
        base_attachment_path=str(base_path),
        required_min_lower_anchor_k=0.971635,
        require_nu=1.001,
        require_radius=3e-5,
        require_cutoff="full",
        require_tail_start=0.90,
        expected_family="standard_sine_twist_map",
        expected_omega="golden",
        min_relative_margin=0.25,
        max_z=0.5,
        out_dir=str(tmp_path / "gen"),
        force=True,
    )
    assert s["passed"]["branch_chart_component_ok"] is False
    assert "branch_chart_compatibility_proof" not in s["formal_evidence_true_flags"]
