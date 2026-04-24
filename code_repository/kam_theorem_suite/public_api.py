from __future__ import annotations

"""Small public API for paper-facing replay and audit tools."""

from .paper_replay_inputs import build_minimal_theorem_shells, build_shells_from_stage_cache
from .theorem_final_discharge_replay import (
    assert_stage108_final_discharge_verified,
    build_stage108_final_discharge_replay_report,
    save_stage108_final_discharge_artifacts,
)
from .final_proof_package_audit import audit_final_theorem_statement_scope, audit_patch_bundle_manifest

__all__ = [
    "build_minimal_theorem_shells",
    "build_shells_from_stage_cache",
    "build_stage108_final_discharge_replay_report",
    "assert_stage108_final_discharge_verified",
    "save_stage108_final_discharge_artifacts",
    "audit_final_theorem_statement_scope",
    "audit_patch_bundle_manifest",
]
