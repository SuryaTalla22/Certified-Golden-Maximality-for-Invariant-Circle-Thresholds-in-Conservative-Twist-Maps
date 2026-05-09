from __future__ import annotations

"""Stage-107 final reduction implication certificate.

This module packages the logical implication that the final proof needs:
threshold identification + Theorem VI envelope/top-gap geometry + Theorem VII
global exhaustion imply the golden maximality conclusion.  It intentionally does
not rebuild upstream theorem artifacts; it consumes theorem-facing shells and
records whether the reduction implication can be used by Theorem VIII.
"""

from typing import Any, Mapping

from .theorem_viii_support_utils import is_front_complete, is_theorem_vi_final_or_stage107_promotable, theorem_vii_is_final


def build_final_reduction_implication_certificate(
    *,
    threshold_identification_certificate: Mapping[str, Any],
    theorem_vi_certificate: Mapping[str, Any],
    theorem_vii_certificate: Mapping[str, Any],
    theorem_v_gap_preservation_certified: bool | None = None,
) -> dict[str, Any]:
    identification_complete = is_front_complete(threshold_identification_certificate)
    vi_final_or_promotable = is_theorem_vi_final_or_stage107_promotable(
        theorem_vi_certificate,
        {"promotes_screened_theorem_vi_to_global_final": True},
    )
    vii_final = theorem_vii_is_final(theorem_vii_certificate)
    statement_mode = str(theorem_vi_certificate.get("statement_mode", "unresolved"))

    witness = threshold_identification_certificate.get("discharged_bridge_native_tail_witness_interval")
    if witness is None:
        witness = theorem_vi_certificate.get("discharged_identified_branch_witness_interval")
    witness_available = isinstance(witness, (list, tuple)) and len(witness) == 2

    top_gap_scale = theorem_vi_certificate.get("current_top_gap_scale")
    challenger_upper = theorem_vi_certificate.get("current_most_dangerous_challenger_upper")
    exhaustion_margin = theorem_vii_certificate.get("current_near_top_exhaustion_margin")
    geometry_available = top_gap_scale is not None and challenger_upper is not None and exhaustion_margin is not None

    ready = bool(
        identification_complete
        and vi_final_or_promotable
        and vii_final
        and statement_mode in {"one-variable", "two-variable"}
        and bool(theorem_v_gap_preservation_certified)
        and witness_available
        and geometry_available
    )
    missing: list[str] = []
    if not identification_complete:
        missing.append("threshold_identification_front_complete")
    if not vi_final_or_promotable:
        missing.append("theorem_vi_final_or_stage107_promotable")
    if not vii_final:
        missing.append("theorem_vii_global_exhaustion_final")
    if statement_mode not in {"one-variable", "two-variable"}:
        missing.append("resolved_statement_mode")
    if not theorem_v_gap_preservation_certified:
        missing.append("theorem_v_gap_preservation_certified")
    if not witness_available:
        missing.append("identified_branch_witness_available")
    if not geometry_available:
        missing.append("current_gap_and_exhaustion_geometry_available")

    return {
        "status": "final-reduction-implication-certified" if ready else "final-reduction-implication-incomplete",
        "proves_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality": ready,
        "identification_front_complete": identification_complete,
        "theorem_vi_final_or_stage107_promotable": vi_final_or_promotable,
        "theorem_vii_global_exhaustion_final": vii_final,
        "statement_mode": statement_mode,
        "theorem_v_gap_preservation_certified": bool(theorem_v_gap_preservation_certified),
        "identified_branch_witness_interval": None if not witness_available else [float(witness[0]), float(witness[1])],
        "current_top_gap_scale": None if top_gap_scale is None else float(top_gap_scale),
        "current_most_dangerous_challenger_upper": None if challenger_upper is None else float(challenger_upper),
        "current_near_top_exhaustion_margin": None if exhaustion_margin is None else float(exhaustion_margin),
        "missing_requirements": missing,
        "proof_note": "Stage 107 consumes closed identification, screened/globalized VI, and globally complete VII to certify the final golden-maximality implication.",
    }
