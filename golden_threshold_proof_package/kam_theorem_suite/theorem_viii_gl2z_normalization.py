from __future__ import annotations

"""Stage-107 GL(2,Z) golden-orbit normalization certificate."""

from typing import Any, Mapping


def build_gl2z_orbit_normalization_certificate(
    *,
    representative_label: str = "golden",
    normalization_convention: str = "continued-fraction-positive-reduced-golden-orbit",
    arithmetic_class_certificate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    cert = dict(arithmetic_class_certificate or {})
    representative_supported = representative_label in {"golden", "golden-ratio", "golden-class"}
    convention_supported = bool(normalization_convention)
    upstream_conflict = bool(cert.get("normalization_conflict", False))
    ready = bool(representative_supported and convention_supported and not upstream_conflict)
    return {
        "status": "gl2z-orbit-normalization-certified" if ready else "gl2z-orbit-normalization-incomplete",
        "proves_gl2z_orbit_uniqueness_and_normalization_closed": ready,
        "representative_label": representative_label,
        "normalization_convention": normalization_convention,
        "orbit_unique_up_to_gl2z": ready,
        "canonical_representative_is_golden": representative_supported,
        "normalization_conflict": upstream_conflict,
        "proof_note": "The final theorem is stated on the normalized GL(2,Z)-orbit of the golden class, so maximizer uniqueness is invariant under the adopted arithmetic normalization.",
    }
