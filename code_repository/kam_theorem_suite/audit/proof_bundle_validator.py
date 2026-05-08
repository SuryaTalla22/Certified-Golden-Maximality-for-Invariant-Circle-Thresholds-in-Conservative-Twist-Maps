from __future__ import annotations

"""Fail-closed validators for proof-carrying audit bundles."""

from pathlib import Path
from typing import Any, Mapping
import json
import math

from .proof_payload import AuditFailure, ProofAuditBundle, bundle_from_dict


class ProofAuditValidationError(RuntimeError):
    """Raised when a proof-audit bundle cannot support theorem-facing replay."""


def _failure(code: str, message: str, location: str = "") -> AuditFailure:
    return AuditFailure(code=code, message=message, location=location)


def _close_enough(a: float, b: float, *, rtol: float = 1e-12, atol: float = 1e-15) -> bool:
    return abs(a - b) <= max(atol, rtol * max(abs(a), abs(b), 1.0))


def validate_proof_audit_bundle(bundle_like: Mapping[str, Any] | ProofAuditBundle) -> list[AuditFailure]:
    """Return all fail-closed validation failures for a proof-audit bundle.

    A valid theorem-facing bundle must contain at least one ordered raw interval,
    at least one recomputed inequality, and at least one non-trusted derived
    Boolean.  This intentionally makes empty or status-only bundles fail.
    """

    try:
        bundle = bundle_from_dict(bundle_like)
    except Exception as exc:  # pragma: no cover - defensive error path
        return [_failure("malformed-bundle", f"bundle could not be parsed: {exc}", "/")]

    failures: list[AuditFailure] = []

    if not bundle.proof_payload_version:
        failures.append(_failure("missing-version", "proof_payload_version is missing", "/proof_payload_version"))
    if not bundle.theorem_layer:
        failures.append(_failure("missing-layer", "theorem_layer is missing", "/theorem_layer"))
    if not bundle.claim:
        failures.append(_failure("missing-claim", "claim is missing", "/claim"))
    if not bundle.validator_recomputed:
        failures.append(_failure("not-recomputed", "validator_recomputed must be true", "/validator_recomputed"))
    if bundle.active_assumptions:
        failures.append(_failure("active-assumptions", "active assumptions are nonempty", "/active_assumptions"))
    if bundle.open_hypotheses:
        failures.append(_failure("open-hypotheses", "open hypotheses are nonempty", "/open_hypotheses"))
    if bundle.failure_fields:
        failures.append(_failure("failure-fields", "failure_fields is nonempty", "/failure_fields"))

    if not bundle.raw_interval_fields:
        failures.append(_failure("no-raw-intervals", "no raw interval fields are present", "/raw_interval_fields"))
    if not bundle.derived_inequalities:
        failures.append(_failure("no-derived-inequalities", "no derived inequalities are present", "/derived_inequalities"))
    if not bundle.derived_booleans:
        failures.append(_failure("no-derived-booleans", "no derived Booleans are present", "/derived_booleans"))

    known_fields: set[str] = set(bundle.raw_interval_fields) | set(bundle.raw_symbolic_fields)

    for name, interval in bundle.raw_interval_fields.items():
        loc = f"/raw_interval_fields/{name}"
        if interval.label and interval.label != name:
            # Labels are allowed to be more descriptive, but an empty label is not.
            pass
        if not interval.label:
            failures.append(_failure("interval-missing-label", "interval label is missing", loc + "/label"))
        if not interval.is_ordered():
            failures.append(_failure("interval-unordered", "interval is missing, nonfinite, or not strictly ordered", loc))
        if interval.theorem_facing and interval.diagnostic_only:
            failures.append(_failure("diagnostic-theorem-interval", "theorem-facing interval is marked diagnostic-only", loc))
        if interval.theorem_facing and not interval.outward_rounded:
            failures.append(_failure("not-outward-rounded", "theorem-facing interval is not outward-rounded", loc))

    for name, inequality in bundle.derived_inequalities.items():
        loc = f"/derived_inequalities/{name}"
        if inequality.name and inequality.name != name:
            pass
        if not inequality.name:
            failures.append(_failure("inequality-missing-name", "inequality name is missing", loc + "/name"))
        if inequality.theorem_facing and inequality.diagnostic_only:
            failures.append(_failure("diagnostic-theorem-inequality", "theorem-facing inequality is marked diagnostic-only", loc))
        if not math.isfinite(float(inequality.lhs_value)) or not math.isfinite(float(inequality.rhs_value)):
            failures.append(_failure("inequality-nonfinite", "inequality values must be finite", loc))
        if inequality.sense not in {"<", "<=", ">", ">="}:
            failures.append(_failure("unsupported-sense", f"unsupported inequality sense {inequality.sense!r}", loc + "/sense"))
        try:
            recomputed = inequality.recomputed_margin()
        except Exception as exc:
            failures.append(_failure("margin-recompute-failed", f"could not recompute margin: {exc}", loc))
            recomputed = float("nan")
        if not math.isfinite(recomputed):
            failures.append(_failure("margin-nonfinite", "recomputed margin is not finite", loc + "/margin"))
        elif not _close_enough(float(inequality.margin), recomputed):
            failures.append(
                _failure(
                    "margin-mismatch",
                    f"stored margin {inequality.margin!r} does not match recomputed margin {recomputed!r}",
                    loc + "/margin",
                )
            )
        if inequality.theorem_facing and not inequality.source_fields:
            failures.append(_failure("no-source-fields", "theorem-facing inequality has no source fields", loc + "/source_fields"))
        for source in inequality.source_fields:
            if source not in known_fields and source not in bundle.derived_inequalities:
                failures.append(_failure("unknown-source-field", f"unknown source field {source!r}", loc + "/source_fields"))
        if inequality.theorem_facing and recomputed <= 0.0:
            failures.append(_failure("nonpositive-margin", "theorem-facing inequality has nonpositive margin", loc + "/margin"))

    known_fields |= set(bundle.derived_inequalities)
    known_fields |= set(bundle.derived_booleans)

    for name, derived in bundle.derived_booleans.items():
        loc = f"/derived_booleans/{name}"
        if derived.name and derived.name != name:
            pass
        if not derived.name:
            failures.append(_failure("boolean-missing-name", "derived Boolean name is missing", loc + "/name"))
        if derived.theorem_facing and derived.trusted_as_input:
            failures.append(_failure("trusted-theorem-boolean", "theorem-facing Boolean is trusted as input", loc))
        if derived.theorem_facing and derived.diagnostic_only:
            failures.append(_failure("diagnostic-theorem-boolean", "theorem-facing Boolean is marked diagnostic-only", loc))
        if derived.theorem_facing and derived.value and not derived.derived_from:
            failures.append(_failure("boolean-not-derived", "true theorem-facing Boolean has no derivation dependencies", loc + "/derived_from"))
        for dep in derived.derived_from:
            if dep not in known_fields:
                failures.append(_failure("unknown-boolean-dependency", f"unknown dependency {dep!r}", loc + "/derived_from"))
        if derived.value and derived.margin is not None and float(derived.margin) <= 0.0:
            failures.append(_failure("boolean-nonpositive-margin", "true Boolean has nonpositive margin", loc + "/margin"))
        if not derived.certified and derived.theorem_facing and derived.value:
            failures.append(_failure("boolean-uncertified", "theorem-facing Boolean is true but uncertified", loc))

    return failures


def assert_proof_audit_bundle_valid(bundle_like: Mapping[str, Any] | ProofAuditBundle) -> None:
    """Raise :class:`ProofAuditValidationError` if the bundle fails validation."""

    failures = validate_proof_audit_bundle(bundle_like)
    if failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in failures)
        raise ProofAuditValidationError(detail)


def load_proof_audit_bundle(path: str | Path) -> ProofAuditBundle:
    return ProofAuditBundle.from_dict(json.loads(Path(path).read_text()))


def save_proof_audit_bundle(bundle: ProofAuditBundle, path: str | Path) -> str:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(bundle.to_json())
    return str(out)
