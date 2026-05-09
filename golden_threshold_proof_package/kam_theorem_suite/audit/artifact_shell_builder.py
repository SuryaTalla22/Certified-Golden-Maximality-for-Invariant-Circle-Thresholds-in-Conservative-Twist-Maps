from __future__ import annotations

"""Build replay shells from proof-carrying audit artifacts.

Phase 1 adds this module as the fail-closed bridge between proof-audit JSON and
paper-facing theorem shells.  It intentionally refuses to turn compact status
strings into theorem shells unless the relevant Boolean has been derived by the
proof-audit validator from raw payload fields.
"""

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence
import json

from .proof_bundle_validator import ProofAuditValidationError, assert_proof_audit_bundle_valid
from .proof_payload import ProofAuditBundle, bundle_from_dict
from .proof_payload_validator import (
    assert_layer_payload_valid,
    validate_arithmetic_domain_payload,
    validate_gl2z_normalization_payload,
    validate_lower_corridor_payload,
    validate_transport_budget_payload,
    validate_upper_obstruction_payload,
)


DEFAULT_REQUIRED_LAYER_KEYS = ("lower_audit", "upper_audit", "transport_audit", "domain_audit")


def load_audit_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ProofAuditValidationError(f"audit JSON must be an object: {path}")
    return data


def _as_bundle(bundle_or_dict: Mapping[str, Any] | ProofAuditBundle) -> ProofAuditBundle:
    """Coerce a raw bundle or common audit-report wrapper to ProofAuditBundle."""

    if isinstance(bundle_or_dict, ProofAuditBundle):
        return bundle_or_dict
    data = dict(bundle_or_dict)
    # Phase-2 lower-corridor reports are written as a reviewer-friendly wrapper
    # containing both summary fields and the actual proof-carrying bundle.
    if "proof_payload_version" not in data:
        if isinstance(data.get("lower_audit"), Mapping):
            data = dict(data["lower_audit"])
        elif isinstance(data.get("domain_audit"), Mapping):
            data = dict(data["domain_audit"])
        elif isinstance(data.get("transport_audit"), Mapping):
            data = dict(data["transport_audit"])
        elif isinstance(data.get("upper_audit"), Mapping):
            data = dict(data["upper_audit"])
        elif isinstance(data.get("gl2z_audit"), Mapping):
            data = dict(data["gl2z_audit"])
        elif isinstance(data.get("bundle"), Mapping):
            data = dict(data["bundle"])
    return bundle_from_dict(data)


def _require_boolean(bundle: ProofAuditBundle, name: str) -> None:
    if name not in bundle.derived_booleans:
        raise ProofAuditValidationError(f"required derived Boolean is missing: {name}")
    value = bundle.derived_booleans[name]
    if value.trusted_as_input:
        raise ProofAuditValidationError(f"derived Boolean {name!r} is trusted as input")
    if not value.value or not value.certified:
        raise ProofAuditValidationError(
            f"derived Boolean {name!r} is not certified true; margin={value.margin!r}"
        )


def _template(base_shell: Mapping[str, Any] | None, *, theorem_status: str) -> dict[str, Any]:
    out = dict(base_shell or {})
    out.setdefault("theorem_status", theorem_status)
    out.setdefault("open_hypotheses", [])
    out.setdefault("active_assumptions", [])
    return out


def build_theorem_iii_shell_from_audit(
    lower_audit: Mapping[str, Any] | ProofAuditBundle,
    *,
    base_shell: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a Theorem-III shell only if the lower anchor is derived."""

    bundle = _as_bundle(lower_audit)
    assert_proof_audit_bundle_valid(bundle)
    lower_failures = validate_lower_corridor_payload(bundle, require_final_anchor=True)
    if lower_failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in lower_failures)
        raise ProofAuditValidationError(detail)
    # Phase 1 accepted a compact-cache red-team Boolean.  Phase 2 accepted a
    # lower-corridor chain pair.  The current closed Theorem-III artifact is a
    # TrackB direct lower-anchor certificate, so accept that schema explicitly
    # without pretending it proves a mesh corridor or a nontrivial K-interval.
    lower_anchor_mode = str(bundle.raw_symbolic_fields.get("lower_anchor_mode", bundle.shell_payload.get("lower_anchor_mode", "")))
    if str(bundle.raw_symbolic_fields.get("certificate_kind", "")) == "direct_lower_anchor_persistence_certificate" or lower_anchor_mode == "direct-lower-anchor":
        _require_boolean(bundle, "direct_lower_anchor_certified")
        _require_boolean(bundle, "final_anchor_reached")
        _require_boolean(bundle, "final_anchor_near_critical")
        _require_boolean(bundle, "strict_comparison_margin_exported")
        claimed = bundle.raw_interval_fields.get("direct_lower_anchor_point")
    elif "lower_anchor_derivable_from_cached_artifact" in bundle.derived_booleans:
        _require_boolean(bundle, "lower_anchor_derivable_from_cached_artifact")
        claimed = bundle.raw_interval_fields.get("compact_replay_claimed_lower_anchor_interval")
    else:
        _require_boolean(bundle, "lower_chain_verified")
        _require_boolean(bundle, "final_anchor_reached")
        if "final_anchor_near_critical" in bundle.derived_booleans:
            _require_boolean(bundle, "final_anchor_near_critical")
        claimed = bundle.raw_interval_fields.get("final_anchor")
    if claimed is None:
        raise ProofAuditValidationError("lower audit lacks a theorem-facing lower anchor interval")
    shell = _template(base_shell, theorem_status="golden-theorem-iii-final-strong")
    shell.update(
        {
            "theorem_iii_final_status": "golden-theorem-iii-final-strong",
            "residual_theorem_iii_burden": [],
            "certified_below_threshold_interval": [float(claimed.lo), float(claimed.hi)],
            "lower_anchor_mode": str(bundle.raw_symbolic_fields.get("lower_anchor_mode", bundle.shell_payload.get("lower_anchor_mode", "legacy-lower-corridor"))),
            "direct_lower_anchor_only": bool(bundle.raw_symbolic_fields.get("direct_lower_anchor_only", False)),
            "does_not_claim_mesh_corridor": bool(bundle.raw_symbolic_fields.get("does_not_claim_mesh_corridor", False)),
            "does_not_claim_parameter_interval": bool(bundle.raw_symbolic_fields.get("does_not_claim_parameter_interval", False)),
            "proof_audit_verified": True,
            "proof_audit_layer": bundle.theorem_layer,
            "proof_audit_claim": bundle.claim,
            "proof_audit_source_artifacts": list(bundle.source_artifacts),
            "proof_audit_bundle": bundle.to_dict(),
            "proof_audit_derived_booleans": {
                k: v.to_dict() for k, v in bundle.derived_booleans.items()
            },
            "lower_corridor_chain_segments": list(bundle.raw_symbolic_fields.get("segments", [])),
            "lower_corridor_chain_verification": dict(bundle.raw_symbolic_fields.get("verification", {})),
        }
    )
    return shell


def build_theorem_iv_shell_from_audit(
    upper_audit: Mapping[str, Any] | ProofAuditBundle,
    *,
    base_shell: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a Theorem-IV shell from derived upper-obstruction Booleans."""

    bundle = _as_bundle(upper_audit)
    assert_proof_audit_bundle_valid(bundle)
    upper_failures = validate_upper_obstruction_payload(bundle)
    if upper_failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in upper_failures)
        raise ProofAuditValidationError(detail)
    for name in (
        "analytic_incompatibility_certified",
        "support_geometry_certified",
        "tail_coherence_certified",
        "tail_stability_certified",
    ):
        _require_boolean(bundle, name)
    shell = _template(base_shell, theorem_status="golden-theorem-iv-final-strong")
    upper_interval = bundle.raw_interval_fields.get("certified_upper_interval")
    barrier_interval = bundle.raw_interval_fields.get("certified_barrier_interval")
    ledger = dict(bundle.raw_symbolic_fields.get("ledger", {}))
    shell.update(
        {
            "analytic_incompatibility_certified": True,
            "supercritical_obstruction_locked": True,
            "support_geometry_certified": True,
            "tail_coherence_certified": True,
            "tail_stability_certified": True,
            "upper_obstruction_interval": (
                None if upper_interval is None else [float(upper_interval.lo), float(upper_interval.hi)]
            ),
            "analytic_barrier_interval": (
                None if barrier_interval is None else [float(barrier_interval.lo), float(barrier_interval.hi)]
            ),
            "analytic_incompatibility_margin": ledger.get(
                "recomputed_gap",
                bundle.shell_payload.get("analytic_incompatibility_margin"),
            ),
            "upper_obstruction_gap_minus_width": ledger.get(
                "gap_minus_upper_width",
                bundle.shell_payload.get("gap_minus_upper_width"),
            ),
            "upper_obstruction_tail_qs": list(bundle.raw_symbolic_fields.get("tail_qs", [])),
            "proof_audit_verified": True,
            "proof_audit_layer": bundle.theorem_layer,
            "proof_audit_claim": bundle.claim,
            "proof_audit_source_artifacts": list(bundle.source_artifacts),
            "upper_obstruction_audit": bundle.to_dict(),
            "proof_audit_bundle": bundle.to_dict(),
            "proof_audit_derived_booleans": {
                k: v.to_dict() for k, v in bundle.derived_booleans.items()
            },
            "proof_audit_margin_ledger": {
                k: v.to_dict() for k, v in bundle.derived_inequalities.items()
            },
        }
    )
    return shell


def build_theorem_v_shell_from_audit(
    transport_audit: Mapping[str, Any] | ProofAuditBundle,
    *,
    base_shell: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a Theorem-V compressed-contract shell from a transport audit."""

    bundle = _as_bundle(transport_audit)
    assert_proof_audit_bundle_valid(bundle)
    transport_failures = validate_transport_budget_payload(bundle)
    if transport_failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in transport_failures)
        raise ProofAuditValidationError(detail)
    for name in (
        "transport_gap_preservation_certified",
        "transport_budget_ledger_complete",
        "compressed_contract_budget_exposed",
    ):
        _require_boolean(bundle, name)
    target = bundle.raw_interval_fields.get("transport_target_interval")
    if target is None:
        raise ProofAuditValidationError("transport audit lacks transport_target_interval")

    shell_payload = dict(bundle.shell_payload or {})
    uniform_majorant = dict(shell_payload.get("uniform_majorant", {}) or {})
    budget = dict(uniform_majorant.get("budget", {}) or {})
    if not budget:
        ledger = dict(bundle.raw_symbolic_fields.get("ledger", {}) or {})
        budget = {
            "available_gap": ledger.get("available_gap"),
            "delta_rat": {"value": ledger.get("delta_rat")},
            "delta_branch": {"value": ledger.get("delta_branch")},
            "delta_tail": {"value": ledger.get("delta_tail")},
            "delta_round": {"value": ledger.get("delta_round")},
            "total_charged": ledger.get("total_charged"),
            "remaining_margin": ledger.get("remaining_margin"),
            "margin_ratio": ledger.get("margin_ratio"),
        }
    shell = _template(base_shell, theorem_status="golden-theorem-v-compressed-contract-strong")
    shell.update(
        {
            "compressed_contract": {
                "theorem_status": "golden-theorem-v-compressed-contract-strong",
                "target_interval": {"lo": float(target.lo), "hi": float(target.hi), "width": target.width},
                "uniform_majorant": {
                    "preserves_golden_gap": True,
                    "certified": True,
                    "error_ledger_exposed": True,
                    "budget": budget,
                },
                "two_sided_separation": {"certified": True},
                "raw_shell_consumed": False,
            },
            "proof_audit_verified": True,
            "proof_audit_layer": bundle.theorem_layer,
            "proof_audit_claim": bundle.claim,
            "proof_audit_source_artifacts": list(bundle.source_artifacts),
            "transport_budget_audit": bundle.to_dict(),
            "proof_audit_bundle": bundle.to_dict(),
            "proof_audit_derived_booleans": {
                k: v.to_dict() for k, v in bundle.derived_booleans.items()
            },
            "proof_audit_margin_ledger": {
                k: v.to_dict() for k, v in bundle.derived_inequalities.items()
            },
            "transport_budget_components": dict(bundle.raw_symbolic_fields.get("transport_components", {})),
            "transport_budget_remaining_margin": budget.get("remaining_margin"),
            "transport_budget_margin_ratio": budget.get("margin_ratio"),
        }
    )
    return shell


def build_theorem_vii_shell_from_audit(
    domain_audit: Mapping[str, Any] | ProofAuditBundle,
    *,
    base_shell: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a Theorem-VII shell from a generated-domain audit."""

    bundle = _as_bundle(domain_audit)
    assert_proof_audit_bundle_valid(bundle)
    domain_failures = validate_arithmetic_domain_payload(bundle)
    if domain_failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in domain_failures)
        raise ProofAuditValidationError(detail)
    _require_boolean(bundle, "domain_exhaustion_certified")
    upper = bundle.raw_interval_fields.get("near_top_upper_bound")
    lower = bundle.raw_interval_fields.get("golden_lower_anchor")
    if upper is None or lower is None:
        raise ProofAuditValidationError("domain audit lacks near_top_upper_bound or golden_lower_anchor")
    margin = float(lower.lo) - float(upper.hi)
    if margin <= 0.0:
        raise ProofAuditValidationError("domain exhaustion upper is not below golden lower anchor")
    shell = _template(base_shell, theorem_status="golden-theorem-vii-exhaustion-discharge-lift-conditional-strong")
    shell.update(
        {
            "theorem_vii_codepath_final": True,
            "theorem_vii_papergrade_final": True,
            "theorem_vii_residual_citation_burden": [],
            "current_near_top_exhaustion_upper_bound": float(upper.hi),
            "current_near_top_exhaustion_margin": margin,
            "current_near_top_exhaustion_pending_count": 0,
            "current_near_top_exhaustion_source": "proof-audit-domain-grammar",
            "current_near_top_exhaustion_status": "near-top-exhaustion-strong",
            "vii_failure_fields": {
                "unranked_labels": [],
                "unproved_pruning_labels": [],
                "missing_completion_labels": [],
                "uncontrolled_deferred_labels": [],
                "uncontrolled_retired_labels": [],
                "unpromoted_candidate_labels": [],
                "uncontrolled_omitted_labels": [],
            },
            "proof_audit_verified": True,
            "proof_audit_layer": bundle.theorem_layer,
            "proof_audit_claim": bundle.claim,
            "domain_audit_bundle": bundle.to_dict(),
            "proof_audit_bundle": bundle.to_dict(),
            "domain_grammar_audit": dict(bundle.raw_symbolic_fields.get("route_counts", {})),
            "domain_grammar_records": list(bundle.raw_symbolic_fields.get("domain_records", [])),
            "domain_grammar_failure_fields": dict(bundle.raw_symbolic_fields.get("failure_fields", {})),
            "domain_grammar_omitted_tail_status": bundle.raw_symbolic_fields.get("omitted_tail_status"),
            "proof_audit_derived_booleans": {k: v.to_dict() for k, v in bundle.derived_booleans.items()},
            "proof_audit_margin_ledger": {k: v.to_dict() for k, v in bundle.derived_inequalities.items()},
        }
    )
    return shell



def build_theorem_viii_gl2z_shell_from_audit(
    gl2z_audit: Mapping[str, Any] | ProofAuditBundle,
    *,
    base_shell: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a final-reduction GL(2,Z) normalization shell from Phase-6 audit.

    This shell is an audit attachment rather than an eighth minimal-replay
    theorem shell.  It records that GL(2,Z) is used as a representative-selection
    convention inside Dnorm and that no analytic-conjugacy claim is consumed.
    """

    bundle = _as_bundle(gl2z_audit)
    assert_proof_audit_bundle_valid(bundle)
    gl2z_failures = validate_gl2z_normalization_payload(bundle)
    if gl2z_failures:
        detail = "; ".join(f"{f.code}: {f.message} at {f.location}" for f in gl2z_failures)
        raise ProofAuditValidationError(detail)
    for name in (
        "representative_selection_convention_certified",
        "golden_orbit_representative_unique_in_Dnorm",
        "no_analytic_conjugacy_claim_used",
        "gl2z_normalization_certified",
    ):
        _require_boolean(bundle, name)
    if bundle.shell_payload.get("analytic_conjugacy_claimed") is not False:
        raise ProofAuditValidationError("GL(2,Z) final-reduction audit must have analytic_conjugacy_claimed=False")
    dnorm = dict(bundle.raw_symbolic_fields.get("Dnorm", {}))
    unique = dict(bundle.raw_symbolic_fields.get("unique_representative_verification", {}))
    shell = _template(base_shell, theorem_status="golden-theorem-viii-gl2z-normalization-audit-strong")
    shell.update(
        {
            "theorem_viii_gl2z_normalization_status": "golden-theorem-viii-gl2z-normalization-audit-strong",
            "normalization_type": "representative_selection",
            "normalization_domain": dnorm,
            "analytic_conjugacy_claimed": False,
            "claimed_analytic_conjugacy_outside_Dnorm": False,
            "golden_orbit_representative_unique_in_Dnorm": True,
            "proves_gl2z_orbit_uniqueness_and_normalization_closed": True,
            "candidate_count": int(unique.get("candidate_count", 0)),
            "accepted_distinct_representative_count": int(unique.get("accepted_distinct_representative_count", 0)),
            "accepted_matrix_witness_count": int(unique.get("accepted_matrix_witness_count", 0)),
            "proof_audit_verified": True,
            "proof_audit_layer": bundle.theorem_layer,
            "proof_audit_claim": bundle.claim,
            "proof_audit_source_artifacts": list(bundle.source_artifacts),
            "gl2z_audit_bundle": bundle.to_dict(),
            "proof_audit_bundle": bundle.to_dict(),
            "proof_audit_derived_booleans": {k: v.to_dict() for k, v in bundle.derived_booleans.items()},
            "proof_audit_margin_ledger": {k: v.to_dict() for k, v in bundle.derived_inequalities.items()},
        }
    )
    return shell

def build_final_replay_shells_from_audit_bundle(
    audit_bundle: Mapping[str, Any],
    *,
    base_shells: Sequence[Mapping[str, Any]] | None = None,
    allow_missing_layers: bool = False,
) -> tuple[dict[str, Any], ...]:
    """Build all final replay shells from a multi-layer proof-audit bundle.

    ``audit_bundle`` must contain layer keys named ``lower_audit``,
    ``upper_audit``, ``transport_audit``, and ``domain_audit`` unless
    ``allow_missing_layers`` is set.  Missing layers are not silently treated as
    theorem evidence; with ``allow_missing_layers=True`` the corresponding base
    shell is merely copied and annotated as not proof-audit-derived.
    """

    from kam_theorem_suite.paper_replay_inputs import build_minimal_theorem_shells, validate_paper_replay_shells

    shells = [dict(x) for x in (base_shells or build_minimal_theorem_shells())]
    if len(shells) != 7:
        raise ProofAuditValidationError(f"expected 7 base shells, got {len(shells)}")

    missing = [key for key in DEFAULT_REQUIRED_LAYER_KEYS if key not in audit_bundle]
    if missing and not allow_missing_layers:
        raise ProofAuditValidationError(f"multi-layer audit bundle is missing required layers: {missing}")

    if "lower_audit" in audit_bundle:
        shells[1] = build_theorem_iii_shell_from_audit(audit_bundle["lower_audit"], base_shell=shells[1])
    elif allow_missing_layers:
        shells[1]["proof_audit_verified"] = False

    if "upper_audit" in audit_bundle:
        shells[2] = build_theorem_iv_shell_from_audit(audit_bundle["upper_audit"], base_shell=shells[2])
    elif allow_missing_layers:
        shells[2]["proof_audit_verified"] = False

    if "transport_audit" in audit_bundle:
        shells[3] = build_theorem_v_shell_from_audit(audit_bundle["transport_audit"], base_shell=shells[3])
    elif allow_missing_layers:
        shells[3]["proof_audit_verified"] = False

    if "domain_audit" in audit_bundle:
        shells[6] = build_theorem_vii_shell_from_audit(audit_bundle["domain_audit"], base_shell=shells[6])
    elif allow_missing_layers:
        shells[6]["proof_audit_verified"] = False

    if "gl2z_audit" in audit_bundle:
        shells[6]["theorem_viii_gl2z_normalization"] = build_theorem_viii_gl2z_shell_from_audit(
            audit_bundle["gl2z_audit"]
        )
        shells[6]["proves_gl2z_orbit_uniqueness_and_normalization_closed"] = True
        shells[6]["analytic_conjugacy_claimed"] = False

    validate_paper_replay_shells(tuple(shells), require_cached_upstream=False, require_proof_audit_payloads=True)
    return tuple(deepcopy(x) for x in shells)


def build_all_shells_from_proof_audits(audit_dir: str | Path) -> tuple[dict[str, Any], ...]:
    """Load standard proof-audit JSON files from a directory and build shells.

    The lower audit may be either a direct ProofAuditBundle JSON file or the
    Phase-2 wrapper emitted by scripts/audit/audit_lower_corridor_chain.py.
    """

    directory = Path(audit_dir)
    candidates = {
        "lower_audit": [
            directory / "lower_direct_anchor_audit.bundle.json",
            directory / "lower_direct_anchor_audit.json",
            directory / "lower_corridor" / "lower_direct_anchor_audit.bundle.json",
            directory / "lower_corridor" / "lower_direct_anchor_audit.json",
            directory / "lower_anchor_closure_audit.bundle.json",
            directory / "lower_anchor_closure_audit.json",
            directory / "lower_corridor" / "lower_anchor_closure_audit.bundle.json",
            directory / "lower_corridor" / "lower_anchor_closure_audit.json",
            directory / "lower_corridor_audit.bundle.json",
            directory / "lower_corridor_audit.json",
            directory / "lower_corridor" / "lower_corridor_audit.bundle.json",
            directory / "lower_corridor" / "lower_corridor_audit.json",
        ],
        "upper_audit": [
            directory / "upper_obstruction_audit.bundle.json",
            directory / "upper_obstruction_audit.json",
            directory / "upper_obstruction" / "upper_obstruction_audit.bundle.json",
            directory / "upper_obstruction" / "upper_obstruction_audit.json",
        ],
        "transport_audit": [
            directory / "transport_budget_audit.bundle.json",
            directory / "transport_budget_audit.json",
            directory / "transport_budget" / "transport_budget_audit.bundle.json",
            directory / "transport_budget" / "transport_budget_audit.json",
        ],
        "domain_audit": [
            directory / "arithmetic_domain_audit.bundle.json",
            directory / "arithmetic_domain_audit.json",
            directory / "arithmetic_domain" / "arithmetic_domain_audit.bundle.json",
            directory / "arithmetic_domain" / "arithmetic_domain_audit.json",
        ],
        "gl2z_audit": [
            directory / "gl2z_normalization_audit.bundle.json",
            directory / "gl2z_normalization_audit.json",
            directory / "gl2z_normalization" / "gl2z_normalization_audit.bundle.json",
            directory / "gl2z_normalization" / "gl2z_normalization_audit.json",
        ],
    }
    payload: dict[str, Any] = {}
    missing: list[str] = []
    for key, paths in candidates.items():
        for path in paths:
            if path.exists():
                payload[key] = load_audit_json(path)
                break
        else:
            if key == "gl2z_audit":
                continue
            missing.append(key)
    if missing:
        raise ProofAuditValidationError(f"missing proof-audit files in {directory}: {missing}")
    return build_final_replay_shells_from_audit_bundle(payload)
