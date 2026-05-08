from __future__ import annotations

"""Phase-8 hardened proof-payload validators.

This module is stricter than the generic Phase-0 bundle schema checker in
``proof_bundle_validator``.  The generic checker verifies that a payload is
well-formed, recomputes the margins explicitly stored inside every
``InequalityPayload``, and rejects trusted/diagnostic theorem-facing Booleans.
The hardened validators below additionally tie important theorem-facing
inequalities back to the *raw interval and symbolic fields* from which they are
supposed to be derived.  This prevents a status string, a stale copied margin,
or an edited derived-inequality row from passing after the underlying raw
payload has been perturbed.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import json
import math

from .proof_bundle_validator import validate_proof_audit_bundle as validate_generic_bundle
from .proof_payload import AuditFailure, ProofAuditBundle, bundle_from_dict


def _failure(code: str, message: str, location: str = "") -> AuditFailure:
    return AuditFailure(code=code, message=message, location=location)


def _close(a: float, b: float, *, rtol: float = 1e-11, atol: float = 1e-14) -> bool:
    return abs(float(a) - float(b)) <= max(atol, rtol * max(abs(float(a)), abs(float(b)), 1.0))


def _as_bundle(payload: Mapping[str, Any] | ProofAuditBundle) -> ProofAuditBundle:
    if isinstance(payload, ProofAuditBundle):
        return payload
    data = dict(payload)
    for wrapper_key in ("lower_audit", "upper_audit", "transport_audit", "domain_audit", "gl2z_audit", "bundle"):
        if "proof_payload_version" not in data and isinstance(data.get(wrapper_key), Mapping):
            data = dict(data[wrapper_key])
    return bundle_from_dict(data)


def _dict_sha256(data: Mapping[str, Any]) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _known_field_names(bundle: ProofAuditBundle) -> set[str]:
    return set(bundle.raw_interval_fields) | set(bundle.raw_symbolic_fields) | set(bundle.derived_inequalities) | set(bundle.derived_booleans)


def _get_symbol(bundle: ProofAuditBundle, key: str, default: Any = None) -> Any:
    return bundle.raw_symbolic_fields.get(key, default)


def _get_ineq(bundle: ProofAuditBundle, name: str):
    if name not in bundle.derived_inequalities:
        raise KeyError(name)
    return bundle.derived_inequalities[name]


def _check_ineq_values(
    bundle: ProofAuditBundle,
    name: str,
    *,
    lhs: float | None = None,
    rhs: float | None = None,
    margin: float | None = None,
    failures: list[AuditFailure],
    location_prefix: str = "/derived_inequalities",
) -> None:
    try:
        ineq = _get_ineq(bundle, name)
    except KeyError:
        failures.append(_failure("missing-required-inequality", f"required inequality {name!r} is missing", f"{location_prefix}/{name}"))
        return
    loc = f"{location_prefix}/{name}"
    if lhs is not None and not _close(ineq.lhs_value, lhs):
        failures.append(_failure("inequality-raw-lhs-mismatch", f"{name} lhs is not derived from raw payload", loc + "/lhs_value"))
    if rhs is not None and not _close(ineq.rhs_value, rhs):
        failures.append(_failure("inequality-raw-rhs-mismatch", f"{name} rhs is not derived from raw payload", loc + "/rhs_value"))
    if margin is not None and not _close(ineq.margin, margin):
        failures.append(_failure("inequality-raw-margin-mismatch", f"{name} margin is not derived from raw payload", loc + "/margin"))


def _check_bool(bundle: ProofAuditBundle, name: str, failures: list[AuditFailure], *, require_true: bool = True) -> None:
    if name not in bundle.derived_booleans:
        failures.append(_failure("missing-required-boolean", f"required derived Boolean {name!r} is missing", f"/derived_booleans/{name}"))
        return
    b = bundle.derived_booleans[name]
    loc = f"/derived_booleans/{name}"
    if b.trusted_as_input:
        failures.append(_failure("trusted-final-boolean", f"derived Boolean {name!r} is trusted as input", loc))
    if b.theorem_facing and b.diagnostic_only:
        failures.append(_failure("diagnostic-final-boolean", f"derived Boolean {name!r} is diagnostic-only", loc))
    if require_true and not b.value:
        failures.append(_failure("required-boolean-false", f"derived Boolean {name!r} is false", loc + "/value"))
    if require_true and not b.derived_from:
        failures.append(_failure("required-boolean-not-derived", f"derived Boolean {name!r} lacks dependencies", loc + "/derived_from"))
    known = _known_field_names(bundle)
    for dep in b.derived_from:
        if dep not in known:
            failures.append(_failure("unknown-boolean-dependency", f"Boolean {name!r} references unknown dependency {dep!r}", loc + "/derived_from"))
    if require_true and b.margin is not None and b.margin <= 0.0:
        failures.append(_failure("required-boolean-nonpositive-margin", f"derived Boolean {name!r} has nonpositive margin", loc + "/margin"))


def require_derived_boolean(payload: Mapping[str, Any] | ProofAuditBundle, name: str) -> None:
    """Raise if a theorem-facing derived Boolean is absent or not derivably true."""

    bundle = _as_bundle(payload)
    failures: list[AuditFailure] = []
    _check_bool(bundle, name, failures, require_true=True)
    if failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in failures)
        raise ValueError(detail)


def recompute_interval_inequality(payload: Mapping[str, Any] | ProofAuditBundle, inequality_name: str) -> bool:
    """Return whether an inequality's stored margin equals its recomputed margin.

    This is the small primitive requested in the Phase-8 plan.  Layer-specific
    validators call it first and then add raw-field consistency checks for the
    theorem-critical inequalities.
    """

    bundle = _as_bundle(payload)
    try:
        ineq = _get_ineq(bundle, inequality_name)
    except KeyError:
        return False
    try:
        recomputed = ineq.recomputed_margin()
    except Exception:
        return False
    return math.isfinite(recomputed) and _close(float(ineq.margin), recomputed) and recomputed > 0.0


def verify_no_trusted_final_booleans(payload: Mapping[str, Any] | ProofAuditBundle) -> None:
    """Raise if any theorem-facing final Boolean is trusted or diagnostic-only."""

    bundle = _as_bundle(payload)
    failures: list[AuditFailure] = []
    for name in bundle.derived_booleans:
        _check_bool(bundle, name, failures, require_true=False)
    if failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in failures)
        raise ValueError(detail)


def verify_payload_hash_and_content(payload: Mapping[str, Any] | ProofAuditBundle) -> dict[str, Any]:
    """Verify content-level theorem/diagnostic separation and return a digest.

    The function is intentionally independent of a filesystem manifest: it
    checks the payload itself, rejects diagnostic-only theorem-facing fields, and
    returns a stable content digest that replay manifests may pin externally.
    """

    bundle = _as_bundle(payload)
    failures = validate_generic_bundle(bundle)
    failures.extend(_validate_content_flags(bundle))
    if failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in failures)
        raise ValueError(detail)
    data = bundle.to_dict()
    return {
        "schema": "phase8_payload_content_hash_v1",
        "theorem_layer": bundle.theorem_layer,
        "claim": bundle.claim,
        "sha256": _dict_sha256(data),
        "size_bytes": len(json.dumps(data, sort_keys=True).encode("utf-8")),
        "derived_boolean_count": len(bundle.derived_booleans),
        "derived_inequality_count": len(bundle.derived_inequalities),
        "raw_interval_count": len(bundle.raw_interval_fields),
    }


def _validate_content_flags(bundle: ProofAuditBundle) -> list[AuditFailure]:
    failures: list[AuditFailure] = []
    meta = dict(bundle.audit_metadata or {})
    shell = dict(bundle.shell_payload or {})
    for obj, prefix in ((meta, "/audit_metadata"), (shell, "/shell_payload")):
        status = str(obj.get("theorem_facing_or_diagnostic", obj.get("status", ""))).lower()
        if "diagnostic" in status and obj.get("theorem_facing", True) is not False:
            failures.append(_failure("diagnostic-payload-consumed", "diagnostic payload is not explicitly excluded from theorem-facing replay", prefix))
    for name, interval in bundle.raw_interval_fields.items():
        if interval.theorem_facing and interval.diagnostic_only:
            failures.append(_failure("diagnostic-theorem-interval", "diagnostic interval is theorem-facing", f"/raw_interval_fields/{name}"))
    for name, ineq in bundle.derived_inequalities.items():
        if ineq.theorem_facing and ineq.diagnostic_only:
            failures.append(_failure("diagnostic-theorem-inequality", "diagnostic inequality is theorem-facing", f"/derived_inequalities/{name}"))
    for name, b in bundle.derived_booleans.items():
        if b.theorem_facing and b.diagnostic_only:
            failures.append(_failure("diagnostic-theorem-boolean", "diagnostic Boolean is theorem-facing", f"/derived_booleans/{name}"))
    return failures



def _is_direct_lower_anchor_bundle(bundle: ProofAuditBundle) -> bool:
    return (
        str(bundle.raw_symbolic_fields.get("certificate_kind", "")) == "direct_lower_anchor_persistence_certificate"
        or str(bundle.shell_payload.get("lower_anchor_mode", "")) == "direct-lower-anchor"
    )


def validate_direct_lower_anchor_payload(payload: Mapping[str, Any] | ProofAuditBundle) -> list[AuditFailure]:
    """Validate a TrackB direct Theorem-III lower-anchor payload.

    This is the strict successor to the legacy lower-corridor validator for the
    current Theorem-III object.  It verifies the direct-anchor certificate from
    raw fields and explicitly does not require continuation-chain segments.
    """

    bundle = _as_bundle(payload)
    failures = validate_generic_bundle(bundle)
    failures.extend(_validate_content_flags(bundle))
    if bundle.theorem_layer != "III":
        failures.append(_failure("wrong-layer", "direct lower-anchor payload must have theorem_layer III", "/theorem_layer"))
    if str(bundle.raw_symbolic_fields.get("certificate_kind", "")) != "direct_lower_anchor_persistence_certificate":
        failures.append(_failure("wrong-certificate-kind", "Theorem III direct-anchor payload has wrong certificate_kind", "/raw_symbolic_fields/certificate_kind"))
    if str(bundle.raw_symbolic_fields.get("track", "")) != "TrackB":
        failures.append(_failure("wrong-track", "Theorem III direct-anchor payload must be TrackB", "/raw_symbolic_fields/track"))
    if bundle.raw_symbolic_fields.get("direct_lower_anchor_only") is not True:
        failures.append(_failure("direct-anchor-scope-missing", "direct-anchor payload must record direct_lower_anchor_only=true", "/raw_symbolic_fields/direct_lower_anchor_only"))
    if bundle.raw_symbolic_fields.get("does_not_claim_mesh_corridor") is not True:
        failures.append(_failure("mesh-corridor-claim-not-excluded", "direct-anchor payload must explicitly exclude a mesh-corridor claim", "/raw_symbolic_fields/does_not_claim_mesh_corridor"))
    if bundle.raw_symbolic_fields.get("does_not_claim_parameter_interval") is not True:
        failures.append(_failure("parameter-interval-claim-not-excluded", "direct-anchor payload must explicitly exclude a parameter-interval claim", "/raw_symbolic_fields/does_not_claim_parameter_interval"))
    if list(bundle.raw_symbolic_fields.get("failed_checks", []) or []):
        failures.append(_failure("direct-anchor-failed-checks", "TrackB direct-anchor artifact has nonempty failed_checks", "/raw_symbolic_fields/failed_checks"))
    if bundle.raw_symbolic_fields.get("failed_checks_empty") is not True:
        failures.append(_failure("failed-checks-empty-flag-false", "failed_checks_empty must be true", "/raw_symbolic_fields/failed_checks_empty"))
    top = dict(bundle.raw_symbolic_fields.get("top_level_true_flags", {}) or {})
    for name in ("theorem_facing", "passed", "promotion_allowed"):
        if top.get(name) is not True:
            failures.append(_failure("missing-top-level-trackb-flag", f"required TrackB top-level flag {name!r} is not true", f"/raw_symbolic_fields/top_level_true_flags/{name}"))
    formal = dict(bundle.raw_symbolic_fields.get("formal_evidence_true_flags", {}) or {})
    for name in (
        "formal_interval_backend",
        "outward_rounded_residual_proof",
        "small_divisor_proof",
        "cohomology_inverse_proof",
        "frame_reducibility_proof",
        "nonlinear_bound_proof",
        "tail_bound_proof",
        "branch_chart_compatibility_proof",
        "final_graph_consumption_proof",
    ):
        if formal.get(name) is not True:
            failures.append(_failure("missing-formal-trackb-flag", f"required TrackB formal flag {name!r} is not true", f"/raw_symbolic_fields/formal_evidence_true_flags/{name}"))
    if bundle.raw_symbolic_fields.get("phase5e_promoted") is not True:
        failures.append(_failure("phase5e-not-promoted", "Phase-5E promotion gate is not recorded as promoted", "/raw_symbolic_fields/phase5e_promoted"))

    try:
        K = float(bundle.raw_symbolic_fields["direct_lower_anchor_value"])
        required = float(bundle.raw_symbolic_fields["required_lower_anchor_value"])
        tol = float(bundle.raw_symbolic_fields["match_tolerance"])
        upper = float(bundle.raw_symbolic_fields["near_top_upper_ceiling"])
        selected = dict(bundle.raw_symbolic_fields.get("selected_constants", {}) or {})
        radius = float(selected["radius"])
        radii_lhs = float(selected["radii_lhs_interval_upper"])
        stored_margin = float(selected["radii_margin_interval_lower"])
        margin_tol = float(bundle.raw_symbolic_fields["margin_consistency_tolerance"])
        Z = float(selected["Z_interval_upper"])
        small_div = float(selected["small_divisor_min_denominator_lower"])
        M = float(bundle.raw_symbolic_fields["M"])
        nu = float(bundle.raw_symbolic_fields["nu"])
    except Exception as exc:
        failures.append(_failure("direct-anchor-raw-field-missing", f"could not load direct-anchor raw fields: {exc}", "/raw_symbolic_fields"))
        return failures

    _check_ineq_values(bundle, "direct_anchor_matches_required", lhs=abs(K - required), rhs=tol, margin=tol - abs(K - required), failures=failures)
    _check_ineq_values(bundle, "radii_lhs_below_radius", lhs=radii_lhs, rhs=radius, margin=radius - radii_lhs, failures=failures)
    _check_ineq_values(bundle, "stored_radii_margin_matches_recomputed", lhs=abs((radius - radii_lhs) - stored_margin), rhs=margin_tol, margin=margin_tol - abs((radius - radii_lhs) - stored_margin), failures=failures)
    _check_ineq_values(bundle, "small_divisor_min_positive", lhs=0.0, rhs=small_div, margin=small_div, failures=failures)
    _check_ineq_values(bundle, "linear_defect_below_one", lhs=Z, rhs=1.0, margin=1.0 - Z, failures=failures)
    _check_ineq_values(bundle, "direct_anchor_above_near_top_upper_ceiling", lhs=upper, rhs=K, margin=K - upper, failures=failures)
    _check_ineq_values(bundle, "resolution_positive", lhs=0.0, rhs=M, margin=M, failures=failures)
    _check_ineq_values(bundle, "nu_above_one", lhs=1.0, rhs=nu, margin=nu - 1.0, failures=failures)

    for name in (
        "direct_lower_anchor_certified",
        "final_anchor_reached",
        "final_anchor_near_critical",
        "strict_comparison_margin_exported",
    ):
        _check_bool(bundle, name, failures, require_true=True)
    return failures


def validate_lower_corridor_payload(
    payload: Mapping[str, Any] | ProofAuditBundle,
    *,
    require_final_anchor: bool = True,
    allow_known_lower_gap: bool = False,
) -> list[AuditFailure]:
    bundle = _as_bundle(payload)
    if _is_direct_lower_anchor_bundle(bundle):
        return validate_direct_lower_anchor_payload(bundle)
    failures = validate_generic_bundle(bundle)
    failures.extend(_validate_content_flags(bundle))
    if bundle.theorem_layer != "III":
        failures.append(_failure("wrong-layer", "lower-corridor payload must have theorem_layer III", "/theorem_layer"))
    # Segment-level radii-polynomial recomputation from raw symbolic segment rows.
    segments = list(bundle.raw_symbolic_fields.get("segments", []))
    if not segments:
        failures.append(_failure("missing-lower-segments", "lower audit has no continuation-chain segments", "/raw_symbolic_fields/segments"))
    segment_failures = []
    for idx, seg in enumerate(segments):
        loc = f"/raw_symbolic_fields/segments/{idx}"
        try:
            Y = float(seg.get("residual_Y"))
            Z = float(seg.get("linear_defect_Z"))
            T = float(seg.get("tail_bound_T"))
            r = float(seg.get("radius_r"))
            lhs = Y + Z * r + T
            margin = r - lhs
        except Exception as exc:
            failures.append(_failure("segment-recompute-failed", f"could not recompute segment radii margin: {exc}", loc))
            continue
        if not _close(lhs, float(seg.get("lhs", lhs))):
            failures.append(_failure("segment-lhs-mismatch", "segment lhs is not recomputed from Y+Zr+T", loc + "/lhs"))
        if not _close(margin, float(seg.get("radii_margin", margin))):
            failures.append(_failure("segment-margin-mismatch", "segment radii margin is stale or not recomputed", loc + "/radii_margin"))
        if margin <= 0.0 or seg.get("certified") is not True or seg.get("radii_inequality_holds") is not True:
            segment_failures.append(str(seg.get("segment_id", idx)))
            failures.append(_failure("segment-nonpositive-margin", "lower chain segment has nonpositive radii margin", loc + "/radii_margin"))
    if segment_failures and bundle.derived_booleans.get("lower_chain_verified", None) is not None and bundle.derived_booleans["lower_chain_verified"].value:
        failures.append(_failure("lower-chain-boolean-contradicts-segments", "lower_chain_verified=true despite failed segment margins", "/derived_booleans/lower_chain_verified"))
    _check_bool(bundle, "lower_chain_verified", failures, require_true=require_final_anchor)
    if require_final_anchor:
        _check_bool(bundle, "final_anchor_reached", failures, require_true=True)
    elif "final_anchor_reached" in bundle.derived_booleans and bundle.derived_booleans["final_anchor_reached"].trusted_as_input:
        _check_bool(bundle, "final_anchor_reached", failures, require_true=False)
    if "lower_chain_covered_interval" in bundle.raw_interval_fields and "final_anchor" in bundle.raw_interval_fields:
        covered = bundle.raw_interval_fields["lower_chain_covered_interval"]
        anchor = bundle.raw_interval_fields["final_anchor"]
        _check_ineq_values(bundle, "covered_lo_below_final_anchor_lo", lhs=covered.lo, rhs=anchor.lo, margin=anchor.lo - covered.lo, failures=failures)
        _check_ineq_values(bundle, "covered_hi_reaches_final_anchor_hi", lhs=anchor.hi, rhs=covered.hi, margin=covered.hi - anchor.hi, failures=failures)
    if allow_known_lower_gap:
        failures = _remove_known_lower_gap_failures(failures, bundle)
    return failures


def _remove_known_lower_gap_failures(failures: list[AuditFailure], bundle: ProofAuditBundle) -> list[AuditFailure]:
    """Keep lower-gap failures visible in reports elsewhere, but allow protocol pass.

    Only the known final-anchor failures are removed.  Segment failures, trusted
    Booleans, diagnostic payloads, or stale margin mismatches remain fatal.
    """

    if "final_anchor_not_reached" not in bundle.failure_fields:
        return failures
    allowed = {
        ("failure-fields", "/failure_fields"),
        ("nonpositive-margin", "/derived_inequalities/covered_hi_reaches_final_anchor_hi/margin"),
        ("required-boolean-false", "/derived_booleans/final_anchor_reached/value"),
        ("required-boolean-nonpositive-margin", "/derived_booleans/final_anchor_reached/margin"),
    }
    return [f for f in failures if (f.code, f.location) not in allowed]


def validate_upper_obstruction_payload(payload: Mapping[str, Any] | ProofAuditBundle) -> list[AuditFailure]:
    bundle = _as_bundle(payload)
    failures = validate_generic_bundle(bundle)
    failures.extend(_validate_content_flags(bundle))
    if bundle.theorem_layer != "IV":
        failures.append(_failure("wrong-layer", "upper-obstruction payload must have theorem_layer IV", "/theorem_layer"))
    for name in ("analytic_incompatibility_certified", "support_geometry_certified", "tail_coherence_certified", "tail_stability_certified"):
        _check_bool(bundle, name, failures, require_true=True)
    upper = bundle.raw_interval_fields.get("certified_upper_interval")
    barrier = bundle.raw_interval_fields.get("certified_barrier_interval")
    gap = bundle.raw_interval_fields.get("exported_gap_interval")
    if upper is None or barrier is None:
        failures.append(_failure("missing-upper-intervals", "upper and barrier intervals are required", "/raw_interval_fields"))
        return failures
    sep = barrier.lo - upper.hi
    _check_ineq_values(bundle, "obstruction_separation", lhs=upper.hi, rhs=barrier.lo, margin=sep, failures=failures)
    _check_ineq_values(bundle, "upper_window_ordered", lhs=upper.lo, rhs=upper.hi, margin=upper.width, failures=failures)
    _check_ineq_values(bundle, "barrier_window_ordered", lhs=barrier.lo, rhs=barrier.hi, margin=barrier.width, failures=failures)
    if gap is not None:
        exported_mid = (gap.lo + gap.hi) / 2.0
        if not (gap.lo <= sep <= gap.hi) and not _close(exported_mid, sep, rtol=1e-10, atol=1e-12):
            failures.append(_failure("exported-gap-not-derived-from-raw-intervals", "exported gap interval does not enclose barrier.lo - upper.hi", "/raw_interval_fields/exported_gap_interval"))
    tail_qs = list(bundle.raw_symbolic_fields.get("tail_qs", []))
    if len(tail_qs) < 2 or not all(isinstance(q, int) and q > 0 for q in tail_qs):
        failures.append(_failure("tail-denominators-invalid", "tail_qs must contain positive integer denominators", "/raw_symbolic_fields/tail_qs"))
    if sep <= 0.0:
        failures.append(_failure("upper-not-below-barrier", "upper obstruction ceiling is not below analytic barrier", "/derived_inequalities/obstruction_separation"))
    return failures


def validate_transport_budget_payload(payload: Mapping[str, Any] | ProofAuditBundle) -> list[AuditFailure]:
    bundle = _as_bundle(payload)
    failures = validate_generic_bundle(bundle)
    failures.extend(_validate_content_flags(bundle))
    if bundle.theorem_layer != "V":
        failures.append(_failure("wrong-layer", "transport-budget payload must have theorem_layer V", "/theorem_layer"))
    for name in ("transport_gap_preservation_certified", "transport_budget_ledger_complete", "compressed_contract_budget_exposed"):
        _check_bool(bundle, name, failures, require_true=True)
    target = bundle.raw_interval_fields.get("transport_target_interval")
    available = bundle.raw_interval_fields.get("available_gap_interval")
    total = bundle.raw_interval_fields.get("total_charged_interval")
    remaining = bundle.raw_interval_fields.get("remaining_margin_interval")
    if target is None or available is None or total is None or remaining is None:
        failures.append(_failure("missing-transport-intervals", "transport target, available gap, total charge, and remaining margin intervals are required", "/raw_interval_fields"))
        return failures
    ledger = dict(bundle.raw_symbolic_fields.get("ledger", {}))
    components = {k: float(bundle.raw_symbolic_fields.get(k, ledger.get(k, 0.0))) for k in ("delta_rat", "delta_branch", "delta_tail", "delta_round")}
    total_recomputed = sum(components.values())
    avail = float(ledger.get("available_gap", (available.lo + available.hi) / 2.0))
    remaining_recomputed = avail - total_recomputed
    target_width = target.width
    ledger_target_width = float(ledger.get("target_width", bundle.raw_symbolic_fields.get("target_width", target_width)))
    ledger_total = float(ledger.get("total_charged", total_recomputed))
    ledger_remaining = float(ledger.get("remaining_margin", remaining_recomputed))
    _check_ineq_values(bundle, "target_interval_ordered", lhs=target.lo, rhs=target.hi, margin=target_width, failures=failures)
    _check_ineq_values(bundle, "target_width_export_matches", lhs=abs(float(bundle.raw_symbolic_fields.get("exported_target_width", ledger.get("exported_target_width", target_width))) - target_width), rhs=float(bundle.derived_inequalities.get("target_width_export_matches").rhs_value if "target_width_export_matches" in bundle.derived_inequalities else 1e-14), failures=failures)
    _check_ineq_values(bundle, "budget_preserves_available_gap", lhs=ledger_total, rhs=avail, margin=avail - ledger_total, failures=failures)
    _check_ineq_values(bundle, "total_matches_component_sum", lhs=abs(ledger_total - total_recomputed), rhs=float(bundle.derived_inequalities.get("total_matches_component_sum").rhs_value if "total_matches_component_sum" in bundle.derived_inequalities else 1e-14), failures=failures)
    _check_ineq_values(bundle, "remaining_margin_matches_difference", lhs=abs(ledger_remaining - remaining_recomputed), rhs=float(bundle.derived_inequalities.get("remaining_margin_matches_difference").rhs_value if "remaining_margin_matches_difference" in bundle.derived_inequalities else 1e-14), failures=failures)
    if not (available.lo <= avail <= available.hi):
        failures.append(_failure("available-gap-not-enclosed", "available_gap_interval does not enclose the symbolic available gap", "/raw_interval_fields/available_gap_interval"))
    if not (total.lo <= ledger_total <= total.hi):
        failures.append(_failure("total-charged-not-enclosed", "total_charged_interval does not enclose the recomputed total charge", "/raw_interval_fields/total_charged_interval"))
    if not (remaining.lo <= ledger_remaining <= remaining.hi):
        failures.append(_failure("remaining-margin-not-enclosed", "remaining_margin_interval does not enclose the recomputed remaining margin", "/raw_interval_fields/remaining_margin_interval"))
    if not _close(ledger_target_width, target_width):
        failures.append(_failure("target-width-not-derived-from-raw-interval", "symbolic target width is not derived from raw target interval", "/raw_symbolic_fields/target_width"))
    expected_from_width = {
        "delta_rat": 0.35 * target_width,
        "delta_branch": 0.25 * target_width,
        "delta_tail": 0.30 * target_width,
    }
    for k, expected in expected_from_width.items():
        if not _close(components[k], expected):
            failures.append(_failure("transport-component-formula-mismatch", f"{k} is not derived from the target-width formula", f"/raw_symbolic_fields/{k}"))
    for k, val in components.items():
        if val <= 0.0:
            failures.append(_failure("transport-component-nonpositive", f"{k} is not positive", f"/raw_symbolic_fields/{k}"))
    raw_shell_consumed = bool(bundle.raw_symbolic_fields.get("raw_shell_consumed", ledger.get("raw_shell_consumed", bundle.shell_payload.get("raw_shell_consumed", False))))
    if raw_shell_consumed:
        failures.append(_failure("raw-shell-consumed", "transport budget consumed a raw/diagnostic shell", "/raw_symbolic_fields/raw_shell_consumed"))
    if remaining_recomputed <= 0.0 or (avail - ledger_total) <= 0.0:
        failures.append(_failure("transport-budget-exceeds-gap", "transport budget exceeds available gap", "/derived_inequalities/budget_preserves_available_gap"))
    return failures


def validate_arithmetic_domain_payload(payload: Mapping[str, Any] | ProofAuditBundle) -> list[AuditFailure]:
    bundle = _as_bundle(payload)
    failures = validate_generic_bundle(bundle)
    failures.extend(_validate_content_flags(bundle))
    if bundle.theorem_layer != "VII":
        failures.append(_failure("wrong-layer", "arithmetic-domain payload must have theorem_layer VII", "/theorem_layer"))
    _check_bool(bundle, "domain_exhaustion_certified", failures, require_true=True)
    records = list(bundle.raw_symbolic_fields.get("domain_records", []))
    route_counts = dict(bundle.raw_symbolic_fields.get("route_counts", {}))
    failure_fields = dict(bundle.raw_symbolic_fields.get("failure_fields", {}))
    if not records:
        failures.append(_failure("missing-domain-records", "domain grammar has no generated records", "/raw_symbolic_fields/domain_records"))
    uncontrolled = []
    for idx, rec in enumerate(records):
        loc = f"/raw_symbolic_fields/domain_records/{idx}"
        if rec.get("theorem_facing", True) and rec.get("certified") is not True:
            uncontrolled.append(str(rec.get("label", idx)))
            failures.append(_failure("uncertified-domain-record", "theorem-facing domain record is not certified", loc))
        if rec.get("verified") is not True or rec.get("route_valid") is not True or rec.get("has_control_certificate") is not True:
            uncontrolled.append(str(rec.get("label", idx)))
            failures.append(_failure("uncontrolled-domain-record", "domain record lacks a closed route/control certificate", loc))
        if rec.get("upper_ceiling") is not None and rec.get("lower_reference") is not None:
            recomputed = float(rec["lower_reference"]) - float(rec["upper_ceiling"])
            if recomputed <= 0.0:
                failures.append(_failure("domain-record-nonpositive-margin", "domain record upper ceiling is not below lower reference", loc + "/margin"))
            if rec.get("margin") is not None and not _close(recomputed, float(rec.get("margin"))):
                failures.append(_failure("domain-record-margin-mismatch", "domain record margin is not recomputed from lower/upper", loc + "/margin"))
    nonempty_failure_fields = {k: v for k, v in failure_fields.items() if v}
    if nonempty_failure_fields:
        failures.append(_failure("domain-failure-fields-nonempty", "Theorem-VII failure fields are nonempty", "/raw_symbolic_fields/failure_fields"))
    if int(route_counts.get("uncontrolled_count", 0)) != 0:
        failures.append(_failure("domain-uncontrolled-count-nonzero", "route_counts reports uncontrolled records", "/raw_symbolic_fields/route_counts/uncontrolled_count"))
    if uncontrolled and bundle.derived_booleans.get("domain_exhaustion_certified") and bundle.derived_booleans["domain_exhaustion_certified"].value:
        failures.append(_failure("domain-boolean-contradicts-records", "domain_exhaustion_certified=true despite uncontrolled records", "/derived_booleans/domain_exhaustion_certified"))
    upper = bundle.raw_interval_fields.get("near_top_upper_bound")
    lower = bundle.raw_interval_fields.get("golden_lower_anchor")
    if upper is not None and lower is not None:
        _check_ineq_values(bundle, "near_top_upper_below_golden_lower", lhs=upper.hi, rhs=lower.lo, margin=lower.lo - upper.hi, failures=failures)
    return failures


def validate_gl2z_normalization_payload(payload: Mapping[str, Any] | ProofAuditBundle) -> list[AuditFailure]:
    bundle = _as_bundle(payload)
    failures = validate_generic_bundle(bundle)
    failures.extend(_validate_content_flags(bundle))
    if bundle.theorem_layer not in {"VIII.GL2Z", "VIII"}:
        failures.append(_failure("wrong-layer", "GL(2,Z) payload must have theorem_layer VIII.GL2Z", "/theorem_layer"))
    for name in ("representative_selection_convention_certified", "golden_orbit_representative_unique_in_Dnorm", "no_analytic_conjugacy_claim_used", "gl2z_normalization_certified"):
        _check_bool(bundle, name, failures, require_true=True)
    norm = dict(bundle.raw_symbolic_fields.get("certified_universe_normalization", {}))
    unique = dict(bundle.raw_symbolic_fields.get("unique_representative_verification", {}))
    records = list(bundle.raw_symbolic_fields.get("candidate_records", []))
    if norm.get("analytic_conjugacy_claimed") is not False or bundle.shell_payload.get("analytic_conjugacy_claimed") is not False:
        failures.append(_failure("analytic-conjugacy-claimed", "GL(2,Z) audit must not claim analytic conjugacy", "/raw_symbolic_fields/certified_universe_normalization"))
    accepted_golden_values = set()
    accepted_nongolden = 0
    duplicate_count = 0
    for rec in records:
        if rec.get("accepted_by_Dnorm") is True:
            if rec.get("canonical_golden") is True:
                accepted_golden_values.add(round(float(rec.get("representative_value")), 14))
            else:
                accepted_nongolden += 1
    # The compact cluster ledger is authoritative for duplicate representatives;
    # the raw records can contain multiple matrix witnesses for the same value.
    duplicate_count = int(unique.get("duplicate_golden_representative_count", 0))
    accepted_distinct = int(unique.get("accepted_distinct_representative_count", len(accepted_golden_values) + accepted_nongolden))
    accepted_nongolden_reported = int(unique.get("accepted_distinct_nongolden_count", accepted_nongolden))
    if duplicate_count != 0:
        failures.append(_failure("duplicate-golden-representative", "duplicate golden representative accepted in Dnorm", "/raw_symbolic_fields/unique_representative_verification"))
    if accepted_distinct != 1:
        failures.append(_failure("wrong-accepted-representative-count", "normalization should accept exactly one distinct representative", "/raw_symbolic_fields/unique_representative_verification/accepted_distinct_representative_count"))
    if accepted_nongolden_reported != 0:
        failures.append(_failure("nongolden-representative-accepted", "nongolden representative accepted in Dnorm", "/raw_symbolic_fields/unique_representative_verification/accepted_distinct_nongolden_count"))
    return failures


LAYER_VALIDATORS = {
    "III": validate_lower_corridor_payload,
    "IV": validate_upper_obstruction_payload,
    "V": validate_transport_budget_payload,
    "VII": validate_arithmetic_domain_payload,
    "VIII.GL2Z": validate_gl2z_normalization_payload,
    "VIII": validate_gl2z_normalization_payload,
}


def validate_layer_payload(
    payload: Mapping[str, Any] | ProofAuditBundle,
    *,
    allow_known_lower_gap: bool = False,
    require_lower_final_anchor: bool = True,
) -> list[AuditFailure]:
    bundle = _as_bundle(payload)
    validator = LAYER_VALIDATORS.get(bundle.theorem_layer)
    if validator is None:
        failures = validate_generic_bundle(bundle)
        failures.extend(_validate_content_flags(bundle))
        return failures
    if bundle.theorem_layer == "III":
        return validate_lower_corridor_payload(
            bundle,
            require_final_anchor=require_lower_final_anchor,
            allow_known_lower_gap=allow_known_lower_gap,
        )
    return validator(bundle)  # type: ignore[misc]


def assert_layer_payload_valid(
    payload: Mapping[str, Any] | ProofAuditBundle,
    *,
    allow_known_lower_gap: bool = False,
    require_lower_final_anchor: bool = True,
) -> None:
    failures = validate_layer_payload(payload, allow_known_lower_gap=allow_known_lower_gap, require_lower_final_anchor=require_lower_final_anchor)
    if failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in failures)
        raise ValueError(detail)


EXPECTED_DIR_BUNDLES: dict[str, str] = {
    "lower_corridor": "lower_corridor/lower_corridor_audit.bundle.json",
    "upper_obstruction": "upper_obstruction/upper_obstruction_audit.bundle.json",
    "transport_budget": "transport_budget/transport_budget_audit.bundle.json",
    "arithmetic_domain": "arithmetic_domain/arithmetic_domain_audit.bundle.json",
    "gl2z_normalization": "gl2z_normalization/gl2z_normalization_audit.bundle.json",
}
LOWER_ANCHOR_CLOSURE_BUNDLE = "lower_corridor/lower_anchor_closure_audit.bundle.json"


def validate_proof_audit_bundle(
    audit_dir_or_payload: str | Path | Mapping[str, Any] | ProofAuditBundle,
    *,
    allow_known_lower_gap: bool = False,
) -> dict[str, Any]:
    """Validate either one proof-audit payload or a standard audit directory.

    The return value is JSON-serializable and suitable for replay reports.
    """

    if isinstance(audit_dir_or_payload, (str, Path)):
        root = Path(audit_dir_or_payload)
        if root.is_file():
            payload = json.loads(root.read_text())
            failures = validate_layer_payload(payload, allow_known_lower_gap=allow_known_lower_gap, require_lower_final_anchor=not allow_known_lower_gap)
            return {
                "schema": "phase8_hardened_payload_validation_v1",
                "path": str(root),
                "status": "passed" if not failures else "failed",
                "failure_count": len(failures),
                "failures": [f.to_dict() for f in failures],
            }
        if not root.is_dir():
            return {"schema": "phase8_hardened_directory_validation_v1", "status": "failed", "failures": [{"code": "audit-path-missing", "path": str(root)}]}
        layer_reports: dict[str, Any] = {}
        missing: list[dict[str, Any]] = []
        total_failures: list[dict[str, Any]] = []
        strict_final_ready = True
        known_lower_gap = False
        for layer, rel in EXPECTED_DIR_BUNDLES.items():
            path = root / (LOWER_ANCHOR_CLOSURE_BUNDLE if layer == "lower_corridor" and (root / LOWER_ANCHOR_CLOSURE_BUNDLE).exists() else rel)
            if not path.exists():
                missing.append({"layer": layer, "path": path.as_posix()})
                strict_final_ready = False
                continue
            payload = json.loads(path.read_text())
            failures = validate_layer_payload(payload, allow_known_lower_gap=allow_known_lower_gap, require_lower_final_anchor=not allow_known_lower_gap)
            bundle = _as_bundle(payload)
            if bundle.theorem_layer == "III" and "final_anchor_not_reached" in bundle.failure_fields:
                known_lower_gap = True
                strict_final_ready = False
            if failures:
                content_hash = None
            elif bundle.theorem_layer == "III" and "final_anchor_not_reached" in bundle.failure_fields and allow_known_lower_gap:
                # The known lower gap is allowed for protocol continuity but is
                # still not a closed theorem-facing content payload.  Hash the
                # bytes for provenance without calling the strict content verifier.
                content_hash = _dict_sha256(bundle.to_dict())
            else:
                content_hash = verify_payload_hash_and_content(bundle)["sha256"]
            layer_reports[layer] = {
                "path": path.as_posix(),
                "theorem_layer": bundle.theorem_layer,
                "status": "passed" if not failures else "failed",
                "failure_count": len(failures),
                "failures": [f.to_dict() for f in failures],
                "content_hash": content_hash,
            }
            total_failures.extend({"layer": layer, **f.to_dict()} for f in failures)
        if missing:
            strict_final_ready = False
            total_failures.extend({"layer": m["layer"], "code": "missing-audit-bundle", "message": "expected audit bundle is missing", "location": m["path"]} for m in missing)
        status = "passed" if not total_failures else "failed"
        if allow_known_lower_gap and known_lower_gap and all(f.get("layer") == "lower_corridor" for f in total_failures):
            status = "passed-with-known-lower-gap"
        return {
            "schema": "phase8_hardened_directory_validation_v1",
            "status": status,
            "strict_final_ready": bool(strict_final_ready and not total_failures),
            "known_lower_gap": known_lower_gap,
            "missing": missing,
            "layers": layer_reports,
            "failure_count": len(total_failures),
            "failures": total_failures,
        }
    bundle = _as_bundle(audit_dir_or_payload)
    failures = validate_layer_payload(bundle, allow_known_lower_gap=allow_known_lower_gap, require_lower_final_anchor=not allow_known_lower_gap)
    return {
        "schema": "phase8_hardened_payload_validation_v1",
        "theorem_layer": bundle.theorem_layer,
        "status": "passed" if not failures else "failed",
        "failure_count": len(failures),
        "failures": [f.to_dict() for f in failures],
    }
