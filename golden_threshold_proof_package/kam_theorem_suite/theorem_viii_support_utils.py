from __future__ import annotations

"""Stage-107 support utilities for Theorem VIII final reduction closure."""

from typing import Any, Mapping

VIII_ASSUMPTION_FLAGS = {
    "final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality": "proves_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality",
    "gl2z_orbit_uniqueness_and_normalization_closed": "proves_gl2z_orbit_uniqueness_and_normalization_closed",
    "final_universality_class_matches_reduction_statement": "proves_final_universality_class_matches_reduction_statement",
}


def status_rank(status: str) -> int:
    if status.endswith("-final-strong") or "final-strong" in status or status.endswith("-strong") or "strong" in status:
        return 3
    if "front-complete" in status or "conditional-partial" in status or status.endswith("-partial"):
        return 2
    if status:
        return 1
    return 0


def is_front_complete(cert: Mapping[str, Any]) -> bool:
    return status_rank(str(cert.get("theorem_status", ""))) >= 2 and len(cert.get("open_hypotheses", [])) == 0


def is_theorem_vi_final_or_stage107_promotable(cert: Mapping[str, Any], support: Mapping[str, Any] | None = None) -> bool:
    status = str(cert.get("theorem_status", ""))
    residual_status = str((cert.get("residual_burden_summary") or {}).get("status", ""))
    if (
        "global-one-variable-strong" in status
        or "global-two-variable-strong" in status
        or residual_status == "theorem-vi-globally-discharged"
    ):
        return True
    support = support or {}
    return bool(
        support.get("promotes_screened_theorem_vi_to_global_final")
        and ("screened-one-variable-strong" in status or "screened-two-variable-strong" in status)
    )


def theorem_vii_is_final(cert: Mapping[str, Any]) -> bool:
    status = str(cert.get("theorem_status", ""))
    return bool(
        cert.get("theorem_vii_codepath_final", status_rank(status) >= 3 and len(cert.get("open_hypotheses", [])) == 0)
        and cert.get("theorem_vii_papergrade_final", False)
        and len(cert.get("theorem_vii_residual_citation_burden", [])) == 0
    )


def support_proves_assumption(support: Mapping[str, Any] | None, assumption_name: str) -> bool:
    if not support:
        return False
    flag = VIII_ASSUMPTION_FLAGS.get(assumption_name)
    return bool(flag and support.get(flag))


def undischarged_viii_assumptions(support: Mapping[str, Any] | None) -> list[str]:
    support = support or {}
    return [name for name in VIII_ASSUMPTION_FLAGS if not support_proves_assumption(support, name)]


def mark_assumption_rows_from_support(rows: list[Any], support: Mapping[str, Any] | None) -> list[Any]:
    support = support or {}
    for row in rows:
        if support_proves_assumption(support, row.name):
            row.assumed = True
            row.source = "Stage-107 theorem-facing support certificate"
            row.note = f"{row.note} Discharged by Stage-107 final reduction support."
    return rows
