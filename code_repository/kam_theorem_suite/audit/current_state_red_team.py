from __future__ import annotations

"""Red-team audit of the current compact lower shell against cached artifacts.

This module implements the first useful Phase-1 failure: if the compact paper
replay claims a near-critical lower anchor, the audit checks whether the cached
Theorem-III lower artifact actually reaches that anchor.  In the currently
uploaded repository snapshot this check is expected to fail; the failure is
recorded as a proof-carrying audit object instead of being hidden behind a
status string.
"""

from pathlib import Path
from typing import Any, Mapping, Sequence

from .proof_payload import DerivedBoolean, InequalityPayload, IntervalPayload, ProofAuditBundle
from .stage_cache_extractors import extract_theorem_iii_lower_fields


DEFAULT_COMPACT_GOLDEN_LOWER_INTERVAL = (0.9716350, 0.9716360)


def build_lower_anchor_red_team_bundle(
    theorem_iii_path: str | Path,
    *,
    compact_lower_interval: Sequence[float] = DEFAULT_COMPACT_GOLDEN_LOWER_INTERVAL,
) -> ProofAuditBundle:
    """Return a proof-audit bundle comparing cached lower evidence to compact replay.

    The derivation inequality is

    ``cached_supported_lower_ceiling >= compact_lower_anchor_hi``.

    Positive margin means the cached lower artifact reaches the compact claimed
    lower anchor.  Negative margin means it does not.
    """

    extracted = extract_theorem_iii_lower_fields(theorem_iii_path)
    artifact = extracted["source_artifact"]
    compact_lo, compact_hi = float(compact_lower_interval[0]), float(compact_lower_interval[1])

    # Prefer the strongest lower-side interval the cached theorem-III artifact
    # exposes.  In the uploaded snapshot this is the lower-neighborhood stable
    # interval [0.215..., 0.265], not the compact near-critical anchor.
    supported = extracted.get("stable_lower_interval") or extracted["certified_below_threshold_interval"]
    supported_lo, supported_hi = float(supported[0]), float(supported[1])

    raw_intervals = {
        "cached_theorem_iii_supported_lower_interval": IntervalPayload(
            lo=supported_lo,
            hi=supported_hi,
            label="cached_theorem_iii_supported_lower_interval",
            source_artifact=artifact,
            source_json_pointer=(
                "/lower_neighborhood_closure/stable_lower_interval"
                if extracted.get("stable_lower_interval") is not None
                else "/certified_below_threshold_interval"
            ),
        ),
        "compact_replay_claimed_lower_anchor_interval": IntervalPayload(
            lo=compact_lo,
            hi=compact_hi,
            label="compact_replay_claimed_lower_anchor_interval",
            source_artifact="kam_theorem_suite/paper_replay_inputs.py",
            source_json_pointer="build_minimal_theorem_shells/theorem_iii/certified_below_threshold_interval",
        ),
    }
    margin = supported_hi - compact_hi
    inequalities = {
        "cached_lower_reaches_compact_lower_anchor": InequalityPayload(
            name="cached_lower_reaches_compact_lower_anchor",
            lhs_label="compact_replay_claimed_lower_anchor_hi",
            rhs_label="cached_theorem_iii_supported_lower_hi",
            lhs_value=compact_hi,
            rhs_value=supported_hi,
            sense="<=",
            margin=margin,
            source_fields=list(raw_intervals),
            source_artifact=artifact,
        )
    }
    booleans = {
        "lower_anchor_derivable_from_cached_artifact": DerivedBoolean(
            name="lower_anchor_derivable_from_cached_artifact",
            value=margin > 0.0,
            derived_from=["cached_lower_reaches_compact_lower_anchor"],
            margin=margin,
            trusted_as_input=False,
            notes=(
                "True only when the cached lower artifact supports the compact "
                "near-critical lower anchor used by the paper-facing replay."
            ),
        )
    }
    failures = [] if margin > 0.0 else ["cached_lower_artifact_does_not_reach_compact_near_critical_anchor"]
    return ProofAuditBundle(
        proof_payload_version="v2",
        theorem_layer="III",
        claim="lower corridor reaches the compact final golden lower anchor",
        raw_interval_fields=raw_intervals,
        raw_symbolic_fields={
            "cached_theorem_iii_status": extracted.get("theorem_status", ""),
            "cached_residual_burden": extracted.get("residual_theorem_iii_burden", []),
        },
        derived_inequalities=inequalities,
        derived_booleans=booleans,
        validator_recomputed=True,
        active_assumptions=[],
        open_hypotheses=[],
        failure_fields=failures,
        source_artifacts=[artifact, "kam_theorem_suite/paper_replay_inputs.py"],
        shell_payload={},
        audit_metadata={
            "audit_kind": "phase1-current-state-red-team",
            "expected_current_snapshot_result": "fail-until-near-critical-lower-chain-is-regenerated",
            "supported_lower_hi": supported_hi,
            "compact_lower_hi": compact_hi,
            "margin": margin,
        },
    )


def build_current_state_red_team_report(
    theorem_iii_path: str | Path,
    *,
    compact_lower_interval: Sequence[float] = DEFAULT_COMPACT_GOLDEN_LOWER_INTERVAL,
) -> dict[str, Any]:
    bundle = build_lower_anchor_red_team_bundle(theorem_iii_path, compact_lower_interval=compact_lower_interval)
    derived = bundle.derived_booleans["lower_anchor_derivable_from_cached_artifact"]
    bundle_dict = bundle.to_dict()
    return {
        "status": "passed" if derived.value else "failed",
        "bundle": bundle_dict,
        "lower_audit": bundle_dict,
        "summary": {
            "lower_anchor_derivable_from_cached_artifact": derived.value,
            "margin": derived.margin,
            "failure_fields": list(bundle.failure_fields),
        },
    }
