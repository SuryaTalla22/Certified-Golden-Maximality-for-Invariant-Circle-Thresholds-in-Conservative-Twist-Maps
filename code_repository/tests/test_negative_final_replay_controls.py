from __future__ import annotations

import pytest

from kam_theorem_suite.lightweight_stage108_stubs import install_lightweight_stage108_stubs
install_lightweight_stage108_stubs()

from kam_theorem_suite.paper_replay_inputs import (
    PaperReplayValidationError,
    build_minimal_theorem_shells,
    validate_paper_replay_shells,
)
from kam_theorem_suite.theorem_final_discharge_replay import (
    assert_stage108_final_discharge_verified,
    build_stage108_final_discharge_replay_report,
)


def _report(shells):
    validate_paper_replay_shells(shells, require_cached_upstream=False)
    return build_stage108_final_discharge_replay_report(
        theorem_i_ii_workstream_certificate=shells[0],
        theorem_iii_certificate=shells[1],
        theorem_iv_certificate=shells[2],
        theorem_v_certificate=shells[3],
        threshold_identification_certificate=shells[4],
        theorem_vi_certificate=shells[5],
        theorem_vii_certificate=shells[6],
    )


def test_negative_raw_theorem_v_shell_is_rejected():
    shells = list(build_minimal_theorem_shells())
    shells[3] = {
        "theorem_status": "golden-theorem-v-raw-diagnostic-partial",
        "open_hypotheses": ["raw_transport_shell_not_compressed"],
        "active_assumptions": ["raw_transport_shell_not_compressed"],
    }
    with pytest.raises(PaperReplayValidationError, match="Theorem V"):
        _report(shells)


def test_negative_nonempty_vii_burden_is_rejected_by_final_replay():
    shells = list(build_minimal_theorem_shells())
    theorem_vii = dict(shells[6])
    theorem_vii["theorem_status"] = "golden-theorem-vii-exhaustion-discharge-lift-incomplete"
    # Keep the validator-specific failure fields empty so this reaches the final replay.
    theorem_vii["theorem_vii_residual_citation_burden"] = []
    shells[6] = theorem_vii
    report = build_stage108_final_discharge_replay_report(
        theorem_i_ii_workstream_certificate=shells[0],
        theorem_iii_certificate=shells[1],
        theorem_iv_certificate=shells[2],
        theorem_v_certificate=shells[3],
        threshold_identification_certificate=shells[4],
        theorem_vi_certificate=shells[5],
        theorem_vii_certificate=shells[6],
    )
    assert report.final_discharge_verified is False
    assert "theorem_vii_final" in report.audit["failed_checks"]


def test_negative_scope_mismatch_in_support_certificate_is_rejected():
    shells = list(build_minimal_theorem_shells())
    support = {
        "all_viii_assumptions_dischargeable": True,
        "proves_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality": True,
        "proves_gl2z_orbit_uniqueness_and_normalization_closed": True,
        "proves_final_universality_class_matches_reduction_statement": False,
    }
    report = build_stage108_final_discharge_replay_report(
        theorem_i_ii_workstream_certificate=shells[0],
        theorem_iii_certificate=shells[1],
        theorem_iv_certificate=shells[2],
        theorem_v_certificate=shells[3],
        threshold_identification_certificate=shells[4],
        theorem_vi_certificate=shells[5],
        theorem_vii_certificate=shells[6],
        theorem_viii_final_discharge_support_certificate=support,
    )
    assert report.final_discharge_verified is False
    assert "universality_matching" in report.audit["failed_checks"]
    with pytest.raises(AssertionError):
        assert_stage108_final_discharge_verified(report)


def test_negative_branch_label_mismatch_is_rejected():
    shells = list(build_minimal_theorem_shells())
    ident = dict(shells[4])
    ident["transport_branch_label"] = "wrong-branch"
    shells[4] = ident
    with pytest.raises(PaperReplayValidationError, match="branch-label mismatch"):
        validate_paper_replay_shells(shells)


def test_negative_chart_label_mismatch_is_rejected():
    shells = list(build_minimal_theorem_shells())
    ident = dict(shells[4])
    ident["transport_chart_label"] = "wrong-chart"
    shells[4] = ident
    with pytest.raises(PaperReplayValidationError, match="chart-label mismatch"):
        validate_paper_replay_shells(shells)


def test_negative_eroded_margin_is_rejected():
    shells = list(build_minimal_theorem_shells())
    theorem_vii = dict(shells[6])
    theorem_vii["current_near_top_exhaustion_upper_bound"] = 0.9716351
    shells[6] = theorem_vii
    with pytest.raises(PaperReplayValidationError, match="near-top upper bound"):
        validate_paper_replay_shells(shells)


def test_negative_challenger_upper_margin_is_rejected():
    shells = list(build_minimal_theorem_shells())
    theorem_vi = dict(shells[5])
    theorem_vi["current_most_dangerous_challenger_upper"] = 0.9716351
    shells[5] = theorem_vi
    with pytest.raises(PaperReplayValidationError, match="challenger upper"):
        validate_paper_replay_shells(shells)


def test_negative_nonempty_omitted_label_failure_is_rejected():
    shells = list(build_minimal_theorem_shells())
    theorem_vii = dict(shells[6])
    failure_fields = dict(theorem_vii["vii_failure_fields"])
    failure_fields["uncontrolled_omitted_labels"] = ["tail-cylinder-unknown"]
    theorem_vii["vii_failure_fields"] = failure_fields
    shells[6] = theorem_vii
    with pytest.raises(PaperReplayValidationError, match="uncontrolled_omitted_labels"):
        validate_paper_replay_shells(shells)


def test_negative_witness_outside_overlap_is_rejected():
    shells = list(build_minimal_theorem_shells())
    ident = dict(shells[4])
    ident["discharged_bridge_native_tail_witness_interval"] = [0.9716381, 0.9716382]
    shells[4] = ident
    with pytest.raises(PaperReplayValidationError, match="witness"):
        validate_paper_replay_shells(shells)
