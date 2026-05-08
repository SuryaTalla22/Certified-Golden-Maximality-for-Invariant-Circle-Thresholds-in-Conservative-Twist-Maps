"""Proof-carrying audit utilities for theorem-facing replay.

The audit namespace is intentionally lightweight at import time.  Heavy or
figure-generating phase modules should be imported directly from their
submodules so that proof-audit validators, scripts, and tests do not acquire
incidental dependencies merely by importing :mod:`kam_theorem_suite.audit`.
"""

from .proof_payload import (
    AuditFailure,
    DerivedBoolean,
    InequalityPayload,
    IntervalPayload,
    ProofAuditBundle,
    bundle_from_dict,
    bundle_to_dict,
)
from .proof_bundle_validator import (
    ProofAuditValidationError,
    assert_proof_audit_bundle_valid,
    validate_proof_audit_bundle,
)
from .proof_payload_validator import (
    assert_layer_payload_valid,
    validate_layer_payload,
)

__all__ = [
    "AuditFailure",
    "DerivedBoolean",
    "InequalityPayload",
    "IntervalPayload",
    "ProofAuditBundle",
    "ProofAuditValidationError",
    "assert_proof_audit_bundle_valid",
    "bundle_from_dict",
    "bundle_to_dict",
    "validate_proof_audit_bundle",
    "assert_layer_payload_valid",
    "validate_layer_payload",
]
