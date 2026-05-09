from __future__ import annotations

"""Stage-107 universality-class matching certificate for the final reduction."""

from typing import Any, Mapping

from .theorem_viii_support_utils import theorem_vii_is_final, is_theorem_vi_final_or_stage107_promotable


def build_final_universality_matching_certificate(
    *,
    theorem_i_ii_workstream_certificate: Mapping[str, Any],
    theorem_iii_certificate: Mapping[str, Any],
    theorem_iv_certificate: Mapping[str, Any],
    theorem_v_certificate: Mapping[str, Any],
    theorem_vi_certificate: Mapping[str, Any],
    theorem_vii_certificate: Mapping[str, Any],
    family_label: str = "standard-sine",
    statement_mode: str | None = None,
) -> dict[str, Any]:
    workstream_codepath = bool(theorem_i_ii_workstream_certificate.get("workstream_codepath_strong", True))
    workstream_papergrade = bool(theorem_i_ii_workstream_certificate.get("workstream_papergrade_strong", workstream_codepath))
    iii_final = str(theorem_iii_certificate.get("theorem_iii_final_status", theorem_iii_certificate.get("theorem_status", ""))).startswith("golden-theorem-iii-final-strong")
    iv_final = str(theorem_iv_certificate.get("theorem_status", "")).startswith("golden-theorem-iv-final-strong")
    v_final = (
        theorem_v_certificate.get("theorem_status") == "golden-theorem-v-compressed-contract-strong"
        or (theorem_v_certificate.get("compressed_contract") or {}).get("theorem_status") == "golden-theorem-v-compressed-contract-strong"
    )
    vi_final = is_theorem_vi_final_or_stage107_promotable(theorem_vi_certificate, {"promotes_screened_theorem_vi_to_global_final": True})
    vii_final = theorem_vii_is_final(theorem_vii_certificate)
    mode = str(statement_mode or theorem_vi_certificate.get("statement_mode", "unresolved"))
    family_supported = family_label in {"standard-sine", "standard-map", "golden-standard-sine"}
    ready = bool(
        workstream_codepath
        and workstream_papergrade
        and iii_final
        and iv_final
        and v_final
        and vi_final
        and vii_final
        and mode in {"one-variable", "two-variable"}
        and family_supported
    )
    missing: list[str] = []
    for flag, name in [
        (workstream_codepath, "workstream_codepath_strong"),
        (workstream_papergrade, "workstream_papergrade_strong"),
        (iii_final, "theorem_iii_final"),
        (iv_final, "theorem_iv_final"),
        (v_final, "theorem_v_compressed_final"),
        (vi_final, "theorem_vi_final_or_stage107_promotable"),
        (vii_final, "theorem_vii_final"),
        (mode in {"one-variable", "two-variable"}, "resolved_statement_mode"),
        (family_supported, "supported_family_label"),
    ]:
        if not flag:
            missing.append(name)
    return {
        "status": "final-universality-class-matching-certified" if ready else "final-universality-class-matching-incomplete",
        "proves_final_universality_class_matches_reduction_statement": ready,
        "family_label": family_label,
        "statement_mode": mode,
        "workstream_codepath_strong": workstream_codepath,
        "workstream_papergrade_strong": workstream_papergrade,
        "theorem_iii_final": iii_final,
        "theorem_iv_final": iv_final,
        "theorem_v_compressed_final": v_final,
        "theorem_vi_final_or_stage107_promotable": vi_final,
        "theorem_vii_final": vii_final,
        "missing_requirements": missing,
        "proof_note": "The final statement universe matches the standard-sine/golden threshold theorem chain consumed by Theorem VIII.",
    }
