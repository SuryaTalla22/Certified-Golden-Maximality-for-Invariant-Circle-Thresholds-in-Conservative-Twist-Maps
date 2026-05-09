from __future__ import annotations

"""Aggregate Stage-107 support certificate for Theorem VIII."""

from typing import Any, Mapping

from .theorem_viii_final_reduction import build_final_reduction_implication_certificate
from .theorem_viii_gl2z_normalization import build_gl2z_orbit_normalization_certificate
from .theorem_viii_universality_matching import build_final_universality_matching_certificate
from .theorem_viii_support_utils import VIII_ASSUMPTION_FLAGS, undischarged_viii_assumptions


def _v_gap_preserved(theorem_v_certificate: Mapping[str, Any]) -> bool:
    if theorem_v_certificate.get("gap_preservation_certified") is not None:
        return bool(theorem_v_certificate.get("gap_preservation_certified"))
    if theorem_v_certificate.get("theorem_v_gap_preservation_certified") is not None:
        return bool(theorem_v_certificate.get("theorem_v_gap_preservation_certified"))
    law = theorem_v_certificate.get("uniform_error_law") or theorem_v_certificate.get("compressed_contract", {}).get("uniform_error_law", {})
    if isinstance(law, Mapping) and law.get("gap_preservation_certified") is not None:
        return bool(law.get("gap_preservation_certified"))
    return theorem_v_certificate.get("theorem_status") == "golden-theorem-v-compressed-contract-strong"


def build_theorem_viii_final_discharge_support_certificate(
    *,
    threshold_identification_certificate: Mapping[str, Any],
    theorem_i_ii_workstream_certificate: Mapping[str, Any],
    theorem_iii_certificate: Mapping[str, Any],
    theorem_iv_certificate: Mapping[str, Any],
    theorem_v_certificate: Mapping[str, Any],
    theorem_vi_certificate: Mapping[str, Any],
    theorem_vii_certificate: Mapping[str, Any],
    family_label: str = "standard-sine",
    representative_label: str = "golden",
    normalization_convention: str = "continued-fraction-positive-reduced-golden-orbit",
) -> dict[str, Any]:
    theorem_v_gap_preservation_certified = _v_gap_preserved(theorem_v_certificate)
    reduction = build_final_reduction_implication_certificate(
        threshold_identification_certificate=threshold_identification_certificate,
        theorem_vi_certificate=theorem_vi_certificate,
        theorem_vii_certificate=theorem_vii_certificate,
        theorem_v_gap_preservation_certified=theorem_v_gap_preservation_certified,
    )
    normalization = build_gl2z_orbit_normalization_certificate(
        representative_label=representative_label,
        normalization_convention=normalization_convention,
    )
    universality = build_final_universality_matching_certificate(
        theorem_i_ii_workstream_certificate=theorem_i_ii_workstream_certificate,
        theorem_iii_certificate=theorem_iii_certificate,
        theorem_iv_certificate=theorem_iv_certificate,
        theorem_v_certificate=theorem_v_certificate,
        theorem_vi_certificate=theorem_vi_certificate,
        theorem_vii_certificate=theorem_vii_certificate,
        family_label=family_label,
    )

    support_certificates = {
        "final_reduction_implication_certificate": reduction,
        "gl2z_orbit_normalization_certificate": normalization,
        "final_universality_matching_certificate": universality,
    }
    aggregate = {
        "status": "theorem-viii-final-discharge-support-certified",
        "stage": 107,
        "support_certificates": support_certificates,
        "promotes_screened_theorem_vi_to_global_final": True,
        "theorem_v_gap_preservation_certified": bool(theorem_v_gap_preservation_certified),
        "proves_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality": bool(reduction.get("proves_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality")),
        "proves_gl2z_orbit_uniqueness_and_normalization_closed": bool(normalization.get("proves_gl2z_orbit_uniqueness_and_normalization_closed")),
        "proves_final_universality_class_matches_reduction_statement": bool(universality.get("proves_final_universality_class_matches_reduction_statement")),
    }
    aggregate["undischarged_viii_assumptions"] = undischarged_viii_assumptions(aggregate)
    aggregate["all_viii_assumptions_dischargeable"] = len(aggregate["undischarged_viii_assumptions"]) == 0
    if not aggregate["all_viii_assumptions_dischargeable"]:
        aggregate["status"] = "theorem-viii-final-discharge-support-incomplete"
    aggregate["proof_note"] = "Stage 107 aggregates the final reduction implication, GL(2,Z) normalization, and universality matching certificates consumed by Theorem VIII."
    return aggregate


def extract_support_certificates(root: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(root, Mapping):
        return {}
    if root.get("status", "").startswith("theorem-viii-final-discharge-support"):
        return dict(root)
    support = root.get("theorem_viii_final_discharge_support_certificate")
    if isinstance(support, Mapping):
        return dict(support)
    support = root.get("final_discharge_support_certificate")
    if isinstance(support, Mapping):
        return dict(support)
    return {}
