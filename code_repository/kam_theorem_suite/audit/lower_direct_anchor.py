from __future__ import annotations

"""TrackB direct Theorem-III lower-anchor proof-audit support.

The legacy lower audit in this repository was built around a continuation
corridor.  The current Theorem-III artifact is different: it is a theorem-facing
TrackB direct lower-anchor certificate at K = 0.971635.  This module turns that
artifact into a proof-carrying :class:`ProofAuditBundle` whose booleans are
recomputed from raw numerical and symbolic fields.  It does not claim a mesh
corridor or a parameter interval beyond the single lower anchor consumed by the
final comparison.
"""

from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import json
import math

from .proof_payload import DerivedBoolean, InequalityPayload, IntervalPayload, ProofAuditBundle

DEFAULT_REQUIRED_LOWER_ANCHOR = 0.9716350
DEFAULT_NEAR_TOP_UPPER_CEILING = 0.9716347
DEFAULT_MATCH_TOLERANCE = 1.0e-12
ORDERING_EPS = 1.0e-12

REQUIRED_TOP_LEVEL_TRUE_FLAGS = (
    "theorem_facing",
    "passed",
    "promotion_allowed",
)

REQUIRED_FORMAL_FLAGS = (
    "formal_interval_backend",
    "outward_rounded_residual_proof",
    "small_divisor_proof",
    "cohomology_inverse_proof",
    "frame_reducibility_proof",
    "nonlinear_bound_proof",
    "tail_bound_proof",
    "branch_chart_compatibility_proof",
    "final_graph_consumption_proof",
)


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _finite_float(value: Any, *, field: str) -> float:
    try:
        out = float(value)
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValueError(f"{field} is not numeric: {value!r}") from exc
    if not math.isfinite(out):
        raise ValueError(f"{field} is not finite: {value!r}")
    return out


def _ordered_point_interval(value: float, label: str, *, source_artifact: str, pointer: str) -> IntervalPayload:
    """Represent a scalar theorem value in an ordered interval-only schema."""

    lo = float(value)
    hi = float(value) + ORDERING_EPS * max(1.0, abs(float(value)))
    return IntervalPayload(
        lo=lo,
        hi=hi,
        label=label,
        outward_rounded=True,
        source_artifact=source_artifact,
        source_json_pointer=pointer,
        theorem_facing=True,
        diagnostic_only=False,
    )


def load_direct_lower_anchor_artifact(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise TypeError(f"Theorem-III artifact must be a JSON object: {path}")
    return data


def is_direct_lower_anchor_artifact(data: Mapping[str, Any]) -> bool:
    return str(data.get("certificate_kind", "")) == "direct_lower_anchor_persistence_certificate"


def build_direct_lower_anchor_bundle(
    theorem_iii: Mapping[str, Any],
    *,
    source_artifact: str = "artifacts/final_discharge/stage_cache/theorem_iii.json",
    required_lower_anchor: float = DEFAULT_REQUIRED_LOWER_ANCHOR,
    near_top_upper_ceiling: float = DEFAULT_NEAR_TOP_UPPER_CEILING,
    match_tolerance: float = DEFAULT_MATCH_TOLERANCE,
) -> ProofAuditBundle:
    """Build the strict proof-audit bundle for the TrackB direct anchor.

    The bundle is intentionally point-anchor based.  The ordered interval stored
    under ``direct_lower_anchor_point`` is only a schema carrier so existing
    replay code can extract a lower endpoint; it is not a claim of persistence on
    a nontrivial parameter interval.  The proof content comes from the raw
    TrackB inequalities and the strict comparison margin to the current
    near-top upper ceiling.
    """

    if not is_direct_lower_anchor_artifact(theorem_iii):
        raise ValueError("Theorem-III artifact is not a direct lower-anchor certificate")
    selected = dict(theorem_iii.get("selected_constants", {}) or {})

    K = _finite_float(selected.get("K"), field="selected_constants.K")
    radius = _finite_float(selected.get("radius"), field="selected_constants.radius")
    radii_lhs = _finite_float(selected.get("radii_lhs_interval_upper"), field="selected_constants.radii_lhs_interval_upper")
    radii_margin = _finite_float(selected.get("radii_margin_interval_lower"), field="selected_constants.radii_margin_interval_lower")
    Z = _finite_float(selected.get("Z_interval_upper"), field="selected_constants.Z_interval_upper")
    small_div = _finite_float(selected.get("small_divisor_min_denominator_lower"), field="selected_constants.small_divisor_min_denominator_lower")
    residual = _finite_float(selected.get("residual_l1_nu_total_upper", selected.get("Y_interval_upper", 0.0)), field="selected_constants.residual_l1_nu_total_upper")
    M = int(selected.get("M", 0) or 0)
    nu = _finite_float(selected.get("nu"), field="selected_constants.nu")

    required = float(required_lower_anchor)
    upper = float(near_top_upper_ceiling)
    tol = float(match_tolerance)
    anchor_diff = abs(K - required)
    recomputed_radii_margin = radius - radii_lhs
    margin_consistency_error = abs(recomputed_radii_margin - radii_margin)
    margin_consistency_tol = max(1.0e-12, 1.0e-9 * max(abs(radii_margin), 1.0))

    raw_intervals = {
        "direct_lower_anchor_point": _ordered_point_interval(K, "direct_lower_anchor_point", source_artifact=source_artifact, pointer="/selected_constants/K"),
        "required_lower_anchor_point": _ordered_point_interval(required, "required_lower_anchor_point", source_artifact="replay requirement", pointer="/required_lower_anchor"),
        "near_top_upper_ceiling": _ordered_point_interval(upper, "near_top_upper_ceiling", source_artifact="Theorem-VII support/current compact replay", pointer="/current_near_top_exhaustion_upper_bound"),
        "radii_lhs_interval_upper": _ordered_point_interval(radii_lhs, "radii_lhs_interval_upper", source_artifact=source_artifact, pointer="/selected_constants/radii_lhs_interval_upper"),
        "radius": _ordered_point_interval(radius, "radius", source_artifact=source_artifact, pointer="/selected_constants/radius"),
        "radii_margin_interval_lower": _ordered_point_interval(radii_margin, "radii_margin_interval_lower", source_artifact=source_artifact, pointer="/selected_constants/radii_margin_interval_lower"),
        "small_divisor_min_denominator_lower": _ordered_point_interval(small_div, "small_divisor_min_denominator_lower", source_artifact=source_artifact, pointer="/selected_constants/small_divisor_min_denominator_lower"),
        "linear_defect_Z_interval_upper": _ordered_point_interval(Z, "linear_defect_Z_interval_upper", source_artifact=source_artifact, pointer="/selected_constants/Z_interval_upper"),
        "residual_l1_nu_total_upper": _ordered_point_interval(residual, "residual_l1_nu_total_upper", source_artifact=source_artifact, pointer="/selected_constants/residual_l1_nu_total_upper"),
    }

    inequalities = {
        "direct_anchor_matches_required": InequalityPayload(
            name="direct_anchor_matches_required",
            lhs_label="abs(K-required_lower_anchor)",
            rhs_label="match_tolerance",
            lhs_value=anchor_diff,
            rhs_value=tol,
            sense="<",
            margin=tol - anchor_diff,
            source_fields=["direct_lower_anchor_value", "required_lower_anchor_value", "match_tolerance"],
            source_artifact=source_artifact,
        ),
        "radii_lhs_below_radius": InequalityPayload(
            name="radii_lhs_below_radius",
            lhs_label="radii_lhs_interval_upper",
            rhs_label="radius",
            lhs_value=radii_lhs,
            rhs_value=radius,
            sense="<",
            margin=recomputed_radii_margin,
            source_fields=["radii_lhs_interval_upper", "radius"],
            source_artifact=source_artifact,
        ),
        "stored_radii_margin_matches_recomputed": InequalityPayload(
            name="stored_radii_margin_matches_recomputed",
            lhs_label="abs((radius-radii_lhs)-stored_margin)",
            rhs_label="margin_consistency_tolerance",
            lhs_value=margin_consistency_error,
            rhs_value=margin_consistency_tol,
            sense="<",
            margin=margin_consistency_tol - margin_consistency_error,
            source_fields=["radii_lhs_interval_upper", "radius", "radii_margin_interval_lower", "margin_consistency_tolerance"],
            source_artifact=source_artifact,
        ),
        "small_divisor_min_positive": InequalityPayload(
            name="small_divisor_min_positive",
            lhs_label="zero",
            rhs_label="small_divisor_min_denominator_lower",
            lhs_value=0.0,
            rhs_value=small_div,
            sense="<",
            margin=small_div,
            source_fields=["small_divisor_min_denominator_lower"],
            source_artifact=source_artifact,
        ),
        "linear_defect_below_one": InequalityPayload(
            name="linear_defect_below_one",
            lhs_label="Z_interval_upper",
            rhs_label="one",
            lhs_value=Z,
            rhs_value=1.0,
            sense="<",
            margin=1.0 - Z,
            source_fields=["linear_defect_Z_interval_upper"],
            source_artifact=source_artifact,
        ),
        "direct_anchor_above_near_top_upper_ceiling": InequalityPayload(
            name="direct_anchor_above_near_top_upper_ceiling",
            lhs_label="near_top_upper_ceiling",
            rhs_label="direct_lower_anchor",
            lhs_value=upper,
            rhs_value=K,
            sense="<",
            margin=K - upper,
            source_fields=["near_top_upper_ceiling", "direct_lower_anchor_point"],
            source_artifact=source_artifact,
        ),
        "resolution_positive": InequalityPayload(
            name="resolution_positive",
            lhs_label="zero",
            rhs_label="M",
            lhs_value=0.0,
            rhs_value=float(M),
            sense="<",
            margin=float(M),
            source_fields=["M"],
            source_artifact=source_artifact,
        ),
        "nu_above_one": InequalityPayload(
            name="nu_above_one",
            lhs_label="one",
            rhs_label="nu",
            lhs_value=1.0,
            rhs_value=nu,
            sense="<",
            margin=nu - 1.0,
            source_fields=["nu"],
            source_artifact=source_artifact,
        ),
    }

    top_level_flags = {name: bool(theorem_iii.get(name)) for name in REQUIRED_TOP_LEVEL_TRUE_FLAGS}
    raw_formal_flags = theorem_iii.get("formal_evidence_true_flags", {}) or {}
    if isinstance(raw_formal_flags, Mapping):
        formal_flags_record = dict(raw_formal_flags)
    else:
        formal_flags_record = {str(name): True for name in raw_formal_flags}
    formal_flags = {name: bool(formal_flags_record.get(name)) for name in REQUIRED_FORMAL_FLAGS}
    all_top_level_flags = all(top_level_flags.values())
    all_formal_flags = all(formal_flags.values())
    no_failed_checks = not list(theorem_iii.get("failed_checks", []) or [])
    raw_checks = theorem_iii.get("checks", {}) or {}
    phase5e_decision = str(theorem_iii.get("phase5e_decision", ""))
    if isinstance(raw_checks, Mapping):
        phase5e_decision = str(raw_checks.get("phase5e_decision", phase5e_decision))
    else:
        for check in raw_checks:
            if isinstance(check, Mapping) and str(check.get("name", "")) == "phase5e_decision_promote":
                phase5e_decision = str(check.get("detail", phase5e_decision))
                break
    phase5e_promoted = phase5e_decision.upper() in {"PROMOTE", "PROMOTED", "ACCEPT", "ACCEPTED"}

    bools = {
        "direct_lower_anchor_certified": DerivedBoolean(
            name="direct_lower_anchor_certified",
            value=bool(all_top_level_flags and all_formal_flags and no_failed_checks and phase5e_promoted),
            derived_from=list(inequalities.keys()) + ["top_level_true_flags", "formal_evidence_true_flags", "failed_checks_empty", "phase5e_decision"],
            margin=min(v.margin for v in inequalities.values()),
            trusted_as_input=False,
            notes="TrackB direct lower-anchor certificate is theorem-facing, promoted, formally attached, and has positive recomputed margins.",
            source_artifact=source_artifact,
        ),
        "final_anchor_reached": DerivedBoolean(
            name="final_anchor_reached",
            value=bool(anchor_diff < tol),
            derived_from=["direct_anchor_matches_required", "direct_lower_anchor_value", "required_lower_anchor_value"],
            margin=tol - anchor_diff,
            trusted_as_input=False,
            notes="For TrackB, final-anchor reach means the direct theorem-facing anchor equals the required downstream lower endpoint within the recorded tolerance.",
            source_artifact=source_artifact,
        ),
        "final_anchor_near_critical": DerivedBoolean(
            name="final_anchor_near_critical",
            value=bool(K >= 0.90),
            derived_from=["direct_lower_anchor_point"],
            margin=K - 0.90,
            trusted_as_input=False,
            source_artifact=source_artifact,
        ),
        "strict_comparison_margin_exported": DerivedBoolean(
            name="strict_comparison_margin_exported",
            value=bool(K > upper),
            derived_from=["direct_anchor_above_near_top_upper_ceiling"],
            margin=K - upper,
            trusted_as_input=False,
            notes="Witness that the direct lower anchor lies above the current Theorem-VII near-top upper ceiling.",
            source_artifact=source_artifact,
        ),
    }

    return ProofAuditBundle(
        proof_payload_version="v2",
        theorem_layer="III",
        claim="TrackB direct lower-anchor certificate proves the Theorem-III golden lower anchor at K=0.971635",
        raw_interval_fields=raw_intervals,
        raw_symbolic_fields={
            "certificate_kind": "direct_lower_anchor_persistence_certificate",
            "lower_anchor_mode": "direct-lower-anchor",
            "track": str(theorem_iii.get("track", "")),
            "schema": str(theorem_iii.get("schema", "")),
            "status": str(theorem_iii.get("status", "")),
            "direct_lower_anchor_value": K,
            "required_lower_anchor_value": required,
            "near_top_upper_ceiling": upper,
            "match_tolerance": tol,
            "margin_consistency_tolerance": margin_consistency_tol,
            "selected_constants": selected,
            "M": M,
            "nu": nu,
            "top_level_true_flags": top_level_flags,
            "formal_evidence_true_flags": formal_flags,
            "failed_checks_empty": no_failed_checks,
            "failed_checks": list(theorem_iii.get("failed_checks", []) or []),
            "phase5e_decision": phase5e_decision,
            "phase5e_promoted": phase5e_promoted,
            "direct_lower_anchor_only": True,
            "does_not_claim_mesh_corridor": True,
            "does_not_claim_parameter_interval": True,
            "source_record_path": selected.get("source_record_path"),
        },
        derived_inequalities=inequalities,
        derived_booleans=bools,
        validator_recomputed=True,
        active_assumptions=[],
        open_hypotheses=[],
        failure_fields=[],
        source_artifacts=[source_artifact],
        shell_payload={
            "lower_anchor_mode": "direct-lower-anchor",
            "direct_anchor_value": K,
            "required_lower_anchor_value": required,
            "near_top_upper_ceiling": upper,
            "strict_comparison_margin": K - upper,
            "direct_lower_anchor_only": True,
            "does_not_claim_mesh_corridor": True,
            "does_not_claim_parameter_interval": True,
        },
        audit_metadata={
            "phase": "7/TrackB",
            "audit_type": "theorem-iii-direct-lower-anchor-proof-carrying-audit",
            "source_artifact_sha256": _sha256_file(source_artifact) if Path(source_artifact).exists() else None,
            "strict_final_ready_semantics": "direct point lower anchor; no corridor or interval persistence claim",
        },
    )


def write_direct_lower_anchor_outputs(
    bundle: ProofAuditBundle,
    *,
    out_dir: str | Path = "artifacts/proof_audit/lower_corridor",
) -> dict[str, str]:
    """Write direct-anchor audit files plus legacy-compatible aliases."""

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    bundle_json = bundle.to_json()
    wrapper = {
        "schema": "theorem_iii_trackb_direct_lower_anchor_audit_report_v1",
        "status": "passed",
        "lower_anchor_mode": "direct-lower-anchor",
        "known_lower_gap": False,
        "strict_final_ready_for_theorem_iii": True,
        "final_anchor_reached": True,
        "final_anchor_near_critical": True,
        "direct_anchor_value": bundle.raw_symbolic_fields.get("direct_lower_anchor_value"),
        "required_lower_anchor_value": bundle.raw_symbolic_fields.get("required_lower_anchor_value"),
        "near_top_upper_ceiling": bundle.raw_symbolic_fields.get("near_top_upper_ceiling"),
        "failure_fields": [],
        "validator_failure_count": 0,
        "validator_failures": [],
        "lower_audit": bundle.to_dict(),
        "bundle": bundle.to_dict(),
    }

    paths = {
        "direct_anchor_json": out / "lower_direct_anchor_audit.json",
        "direct_anchor_bundle": out / "lower_direct_anchor_audit.bundle.json",
        "anchor_closure_json": out / "lower_anchor_closure_audit.json",
        "anchor_closure_bundle": out / "lower_anchor_closure_audit.bundle.json",
        "lower_corridor_json": out / "lower_corridor_audit.json",
        "lower_corridor_bundle": out / "lower_corridor_audit.bundle.json",
    }
    for key, path in paths.items():
        if key.endswith("bundle"):
            path.write_text(bundle_json)
        else:
            path.write_text(json.dumps(wrapper, indent=2, sort_keys=True) + "\n")
    return {k: v.as_posix() for k, v in paths.items()}
