from __future__ import annotations

from kam_theorem_suite.lower_param.phase5f_formal_attachment import (
    ATTACHMENT_SCHEMA,
    build_formal_attachment_candidate,
    replay_formal_attachment_candidate,
    choose_phase5c_candidate,
)


def _fake_certificate():
    return {
        "schema": "theorem_iii_trackb_phase5d_certificate_scaffold_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "lower_anchor_K": 0.971635,
    }


def _fake_phase5c_summary():
    return {
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
                "radii_lhs_interval_upper": 7.466e-6,
                "radii_margin_interval_lower": 2.25e-5,
                "radii_relative_margin_interval_lower": 0.75,
                "small_divisor_min_denominator_lower": 1e-3,
                "cohomology_inverse_linf_resolved_upper": 920.0,
                "record_path": "records/fake.json",
            }
        ]
    }


def test_choose_candidate_exact_match():
    cand = choose_phase5c_candidate(_fake_phase5c_summary(), require_nu=1.001, require_radius=3e-5, prefer_cutoff="full", prefer_tail_start=0.9)
    assert cand["cutoff_spec"] == "full"


def test_build_attachment_is_fail_closed():
    a = build_formal_attachment_candidate(_fake_certificate(), _fake_phase5c_summary(), "cert.json", "p5c.json")
    assert a["schema"] == ATTACHMENT_SCHEMA
    assert a["component_readiness_passed"] is True
    assert a["formal_attachment_ok"] is False
    assert a["promotion_allowed"] is False
    assert all(v is False for v in a["formal_evidence"].values())


def test_replay_passes_but_not_promotion_ready():
    a = build_formal_attachment_candidate(_fake_certificate(), _fake_phase5c_summary(), "cert.json", "p5c.json")
    replay = replay_formal_attachment_candidate(a)
    assert replay["passed"] is True
    assert replay["promotion_ready"] is False
    assert replay["formal_attachment_ok"] is False
    assert replay["missing_formal_evidence_flags"]
