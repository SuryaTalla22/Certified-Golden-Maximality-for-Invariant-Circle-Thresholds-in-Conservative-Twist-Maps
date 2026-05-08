from pathlib import Path
import json

from kam_theorem_suite.lower_param.phase5e_promotion_gate import (
    GateThresholds,
    run_phase5e_promotion_gate,
)


def write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def base_cert():
    return {
        "schema": "theorem_iii_trackb_phase5d_certificate_scaffold_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "lower_anchor_K": 0.971635,
        "K": 0.971635,
        "Y_interval_upper": 7e-8,
        "Z_interval_upper": 0.23,
        "Q_interval_upper": 551.0,
        "radius": 3e-5,
        "radii_margin_interval_lower": 2e-5,
        "radii_relative_margin_interval_lower": 0.75,
        "nu": 1.001,
        "cutoff_spec": "full",
        "tail_start_frac": 0.90,
        "small_divisor_min_denominator_lower": 1e-3,
        "cohomology_inverse_linf_resolved_upper": 920.0,
        "active_assumptions": ["still diagnostic"],
        "open_hypotheses": ["formal backend required"],
    }


def attachment(cert_path: Path, flags: dict):
    from kam_theorem_suite.lower_param.phase5e_promotion_gate import _sha256_file
    return {
        "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
        "certificate_sha256": _sha256_file(cert_path),
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_evidence": flags,
        "Y_interval_upper": 7e-8,
        "Z_interval_upper": 0.23,
        "Q_interval_upper": 551.0,
        "radius": 3e-5,
        "radii_margin_interval_lower": 2e-5,
        "radii_relative_margin_interval_lower": 0.75,
        "nu": 1.001,
        "tail_start_frac": 0.90,
    }


def test_nested_component_flags_are_recognized_but_gate_still_rejects(tmp_path):
    cert_path = tmp_path / "cert.json"
    write(cert_path, base_cert())
    flags = {k: False for k in [
        "formal_interval_backend",
        "independent_replay_passed",
        "outward_rounded_residual_proof",
        "small_divisor_proof",
        "cohomology_inverse_proof",
        "frame_reducibility_proof",
        "nonlinear_bound_proof",
        "tail_bound_proof",
        "branch_chart_compatibility_proof",
        "final_graph_consumption_proof",
    ]}
    flags["outward_rounded_residual_proof"] = True
    flags["small_divisor_proof"] = True
    att_path = tmp_path / "att.json"
    write(att_path, attachment(cert_path, flags))
    summary = run_phase5e_promotion_gate(
        certificate_path=cert_path,
        formal_attachment_path=att_path,
        out_dir=tmp_path / "out",
        thresholds=GateThresholds(require_nu=1.001, require_radius=3e-5, require_cutoff="full", require_tail_start=0.90),
        force=True,
    )
    failed = [c["name"] for c in summary["formal_attachment_checks"] if not c["ok"]]
    assert "formal_evidence_outward_rounded_residual_proof" not in failed
    assert "formal_evidence_small_divisor_proof" not in failed
    assert "formal_evidence_cohomology_inverse_proof" in failed
    assert summary["decision"] == "REJECT_FAIL_CLOSED"
    assert summary["theorem_replay_accepted"] is False


def test_top_level_flags_still_work(tmp_path):
    cert_path = tmp_path / "cert.json"
    write(cert_path, base_cert())
    flags = {k: False for k in [
        "formal_interval_backend",
        "independent_replay_passed",
        "outward_rounded_residual_proof",
        "small_divisor_proof",
        "cohomology_inverse_proof",
        "frame_reducibility_proof",
        "nonlinear_bound_proof",
        "tail_bound_proof",
        "branch_chart_compatibility_proof",
        "final_graph_consumption_proof",
    ]}
    att = attachment(cert_path, flags)
    att["outward_rounded_residual_proof"] = True
    att["small_divisor_proof"] = True
    att_path = tmp_path / "att.json"
    write(att_path, att)
    summary = run_phase5e_promotion_gate(
        certificate_path=cert_path,
        formal_attachment_path=att_path,
        out_dir=tmp_path / "out",
        thresholds=GateThresholds(require_nu=1.001, require_radius=3e-5, require_cutoff="full", require_tail_start=0.90),
        force=True,
    )
    failed = [c["name"] for c in summary["formal_attachment_checks"] if not c["ok"]]
    assert "formal_evidence_outward_rounded_residual_proof" not in failed
    assert "formal_evidence_small_divisor_proof" not in failed
