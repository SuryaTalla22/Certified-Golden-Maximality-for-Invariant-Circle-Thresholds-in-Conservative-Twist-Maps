from __future__ import annotations

"""Serializable proof-payload dataclasses used by Phase-0/1 audits.

The compact replay path in :mod:`kam_theorem_suite.paper_replay_inputs` is useful
for smoke testing.  The objects in this file are stricter: theorem-facing
Booleans must be recorded as derived outputs of raw interval/symbolic payloads,
not as trusted primitive facts.  The dataclasses deliberately use only the
Python standard library so that reviewers can inspect and replay them in a fresh
environment.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping, MutableMapping, Sequence
import json
import math

InequalitySense = Literal["<", "<=", ">", ">="]


@dataclass(frozen=True)
class IntervalPayload:
    """One outward-rounded scalar interval exported from an artifact."""

    lo: float
    hi: float
    label: str
    outward_rounded: bool = True
    source_artifact: str = ""
    source_json_pointer: str = ""
    theorem_facing: bool = True
    diagnostic_only: bool = False

    @property
    def width(self) -> float:
        return float(self.hi) - float(self.lo)

    def is_ordered(self) -> bool:
        return math.isfinite(float(self.lo)) and math.isfinite(float(self.hi)) and float(self.lo) < float(self.hi)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["width"] = self.width
        out["ordered"] = self.is_ordered()
        return out

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "IntervalPayload":
        return cls(
            lo=float(data["lo"]),
            hi=float(data["hi"]),
            label=str(data.get("label", "")),
            outward_rounded=bool(data.get("outward_rounded", True)),
            source_artifact=str(data.get("source_artifact", "")),
            source_json_pointer=str(data.get("source_json_pointer", "")),
            theorem_facing=bool(data.get("theorem_facing", True)),
            diagnostic_only=bool(data.get("diagnostic_only", False)),
        )


@dataclass(frozen=True)
class InequalityPayload:
    """A scalar inequality whose margin is recomputed by the validator."""

    name: str
    lhs_label: str
    rhs_label: str
    lhs_value: float
    rhs_value: float
    sense: InequalitySense
    margin: float
    source_fields: list[str] = field(default_factory=list)
    source_artifact: str = ""
    theorem_facing: bool = True
    diagnostic_only: bool = False

    def recomputed_margin(self) -> float:
        lhs = float(self.lhs_value)
        rhs = float(self.rhs_value)
        if self.sense in ("<", "<="):
            return rhs - lhs
        if self.sense in (">", ">="):
            return lhs - rhs
        raise ValueError(f"Unsupported inequality sense: {self.sense!r}")

    @property
    def certified(self) -> bool:
        # Strict positivity is required even for <=/>= senses because the final
        # theorem uses positive separation margins, not merely nonnegative ties.
        return self.recomputed_margin() > 0.0

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["recomputed_margin"] = self.recomputed_margin()
        out["certified"] = self.certified
        return out

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InequalityPayload":
        return cls(
            name=str(data.get("name", "")),
            lhs_label=str(data.get("lhs_label", "")),
            rhs_label=str(data.get("rhs_label", "")),
            lhs_value=float(data["lhs_value"]),
            rhs_value=float(data["rhs_value"]),
            sense=data.get("sense", "<"),  # type: ignore[arg-type]
            margin=float(data.get("margin", data.get("recomputed_margin", 0.0))),
            source_fields=[str(x) for x in data.get("source_fields", [])],
            source_artifact=str(data.get("source_artifact", "")),
            theorem_facing=bool(data.get("theorem_facing", True)),
            diagnostic_only=bool(data.get("diagnostic_only", False)),
        )


@dataclass(frozen=True)
class DerivedBoolean:
    """A theorem-facing Boolean together with its derivation dependencies."""

    name: str
    value: bool
    derived_from: list[str] = field(default_factory=list)
    margin: float | None = None
    trusted_as_input: bool = False
    theorem_facing: bool = True
    diagnostic_only: bool = False
    source_artifact: str = ""
    notes: str = ""

    @property
    def certified(self) -> bool:
        if self.trusted_as_input:
            return False
        if self.diagnostic_only and self.theorem_facing:
            return False
        if self.value and self.margin is not None and float(self.margin) <= 0.0:
            return False
        if self.theorem_facing and self.value and not self.derived_from:
            return False
        return bool(self.value)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["certified"] = self.certified
        return out

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DerivedBoolean":
        margin = data.get("margin", None)
        return cls(
            name=str(data.get("name", "")),
            value=bool(data.get("value", False)),
            derived_from=[str(x) for x in data.get("derived_from", [])],
            margin=None if margin is None else float(margin),
            trusted_as_input=bool(data.get("trusted_as_input", False)),
            theorem_facing=bool(data.get("theorem_facing", True)),
            diagnostic_only=bool(data.get("diagnostic_only", False)),
            source_artifact=str(data.get("source_artifact", "")),
            notes=str(data.get("notes", "")),
        )


@dataclass(frozen=True)
class AuditFailure:
    """Structured validation failure emitted by proof-audit validators."""

    code: str
    message: str
    location: str = ""
    severity: Literal["error", "warning"] = "error"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AuditFailure":
        return cls(
            code=str(data.get("code", "")),
            message=str(data.get("message", "")),
            location=str(data.get("location", "")),
            severity=data.get("severity", "error"),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class ProofAuditBundle:
    """A theorem-layer proof-carrying audit bundle.

    ``raw_interval_fields`` and ``derived_inequalities`` provide the numerical
    payload.  ``derived_booleans`` are accepted only when the validator can trace
    them to these payloads and when no active assumptions/open hypotheses/failure
    fields remain.
    """

    proof_payload_version: str
    theorem_layer: str
    claim: str
    raw_interval_fields: dict[str, IntervalPayload] = field(default_factory=dict)
    raw_symbolic_fields: dict[str, Any] = field(default_factory=dict)
    derived_inequalities: dict[str, InequalityPayload] = field(default_factory=dict)
    derived_booleans: dict[str, DerivedBoolean] = field(default_factory=dict)
    validator_recomputed: bool = True
    active_assumptions: list[str] = field(default_factory=list)
    open_hypotheses: list[str] = field(default_factory=list)
    failure_fields: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    shell_payload: dict[str, Any] = field(default_factory=dict)
    audit_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proof_payload_version": self.proof_payload_version,
            "theorem_layer": self.theorem_layer,
            "claim": self.claim,
            "raw_interval_fields": {k: v.to_dict() for k, v in self.raw_interval_fields.items()},
            "raw_symbolic_fields": self.raw_symbolic_fields,
            "derived_inequalities": {k: v.to_dict() for k, v in self.derived_inequalities.items()},
            "derived_booleans": {k: v.to_dict() for k, v in self.derived_booleans.items()},
            "validator_recomputed": self.validator_recomputed,
            "active_assumptions": list(self.active_assumptions),
            "open_hypotheses": list(self.open_hypotheses),
            "failure_fields": list(self.failure_fields),
            "source_artifacts": list(self.source_artifacts),
            "shell_payload": self.shell_payload,
            "audit_metadata": self.audit_metadata,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProofAuditBundle":
        return cls(
            proof_payload_version=str(data.get("proof_payload_version", "")),
            theorem_layer=str(data.get("theorem_layer", "")),
            claim=str(data.get("claim", "")),
            raw_interval_fields={
                str(k): IntervalPayload.from_dict(v)
                for k, v in dict(data.get("raw_interval_fields", {})).items()
            },
            raw_symbolic_fields=dict(data.get("raw_symbolic_fields", {})),
            derived_inequalities={
                str(k): InequalityPayload.from_dict(v)
                for k, v in dict(data.get("derived_inequalities", {})).items()
            },
            derived_booleans={
                str(k): DerivedBoolean.from_dict(v)
                for k, v in dict(data.get("derived_booleans", {})).items()
            },
            validator_recomputed=bool(data.get("validator_recomputed", False)),
            active_assumptions=[str(x) for x in data.get("active_assumptions", [])],
            open_hypotheses=[str(x) for x in data.get("open_hypotheses", [])],
            failure_fields=[str(x) for x in data.get("failure_fields", [])],
            source_artifacts=[str(x) for x in data.get("source_artifacts", [])],
            shell_payload=dict(data.get("shell_payload", {})),
            audit_metadata=dict(data.get("audit_metadata", {})),
        )

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "ProofAuditBundle":
        return cls.from_dict(json.loads(text))


def bundle_from_dict(data: Mapping[str, Any] | ProofAuditBundle) -> ProofAuditBundle:
    if isinstance(data, ProofAuditBundle):
        return data
    return ProofAuditBundle.from_dict(data)


def bundle_to_dict(bundle: Mapping[str, Any] | ProofAuditBundle) -> dict[str, Any]:
    return bundle.to_dict() if isinstance(bundle, ProofAuditBundle) else dict(bundle)
