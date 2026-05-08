from __future__ import annotations

import json
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_phase2m_two_regime import (
    collect_ready_rows,
    freeze_regime_i,
    diagnose_collar_failures,
    write_collar_plan,
    verify_collar,
    assemble_two_regime_certificate,
)


def _write_candidate(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"anchor_segments": rows}, indent=2))


def _row(sid, lo, hi, margin=1e-8, ready=True):
    return {
        "segment_id": sid,
        "K_lo": lo,
        "K_hi": hi,
        "K_mid": 0.5 * (lo + hi),
        "closure_level": "analytic_theorem_closure",
        "theorem_ready": ready,
        "certified": ready,
        "finite_dimensional_only": False,
        "radii_margin": margin,
        "residual_Y": 1e-12,
        "linear_defect_Z": 1e-6,
        "tail_bound_T": 1e-12,
        "radius_r": 1e-8,
        "phase2e_ledger": {"sigma": 0.0001, "radii_margin": margin},
    }


def test_freeze_regime_i_greedy_cover(tmp_path):
    root = tmp_path
    _write_candidate(root / "artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_000_candidate.json", [
        _row("a", 0.265, 0.5),
        _row("b", 0.4999999, 0.7),
    ])
    _write_candidate(root / "artifacts/proof_audit/lower_corridor/phase2j_rescue/x_candidate.json", [
        _row("c", 0.6999999, 0.9),
        _row("d", 0.8999999, 0.9600002),
    ])
    payload = freeze_regime_i(root=root, target_hi=0.9600001)
    assert payload["theorem_facing"] is True
    assert payload["covered_interval"][1] >= 0.9600001
    assert len(payload["anchor_segments"]) == 4


def test_collar_diagnostics_detects_sigma_mismatch(tmp_path):
    root = tmp_path
    _write_candidate(root / "artifacts/proof_audit/lower_corridor/phase2j_rescue/phase2e_heavy_anchor_segment_005_phase2j_sub00_os64_sg0p00025_candidate.json", [
        _row("bad", 0.96, 0.9605, margin=-1e-6, ready=False) | {"sigma": 0.0, "phase2e_ledger": {"sigma": 0.0, "radii_margin": -1e-6}}
    ])
    payload = diagnose_collar_failures(root=root)
    assert payload["row_count"] == 1
    assert payload["sigma_mismatch_count"] == 1


def test_collar_plan_and_two_regime_fail_closed(tmp_path):
    root = tmp_path
    plan = write_collar_plan(root=root, max_jobs=2, python_executable="python")
    assert plan["job_count"] == 2
    collar = verify_collar(root=root)
    assert collar["theorem_facing"] is False
    cert = assemble_two_regime_certificate(root=root)
    assert cert["theorem_facing"] is False
    assert "nearcritical_collar_not_verified" in cert["failure_fields"]
