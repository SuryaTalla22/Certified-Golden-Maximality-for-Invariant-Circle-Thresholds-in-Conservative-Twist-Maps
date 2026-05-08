from __future__ import annotations

"""Phase-2B lower-anchor closure audit.

Phase 2 created a fail-closed lower-corridor audit: it verifies the lower-side
segments available in the cached Theorem-III artifact, but it does not certify
that those segments reach the near-critical final lower anchor.  This module is
the strict bridge from that audit to a final Theorem-III lower-anchor payload.

The module deliberately does **not** fabricate a near-critical KAM certificate.
It has two allowed theorem-facing inputs:

1. the existing Phase-2 lower-corridor proof-audit bundle; and
2. a supplied heavy lower-anchor candidate whose rows expose the same raw
   radii-polynomial terms ``Y, Z, T, r`` as the Phase-2 chain.

The candidate is accepted only if every row recomputes a positive margin,
adjacent K-intervals overlap strictly, the first candidate row overlaps the
existing lower-corridor covered interval, the last certified coverage contains
``[0.9716350, 0.9716360]`` by default, and no candidate row is diagnostic-only or
trusted by status string.  If the candidate is absent, the output is a structured
fail-closed report that explains that an external/regenerated lower-anchor
artifact is still required.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import csv
import json
import math

from .lower_corridor_chain import (
    DEFAULT_FINAL_ANCHOR,
    LowerChainSegment,
    LowerChainVerification,
    build_lower_chain_audit_bundle,
    generate_lower_chain_figures,
    verify_lower_chain,
    write_lower_chain_bundle_json,
    write_lower_chain_csv,
    write_lower_chain_table,
)
from .proof_payload import DerivedBoolean, InequalityPayload, IntervalPayload, ProofAuditBundle, bundle_from_dict
from .proof_payload_validator import validate_lower_corridor_payload


@dataclass(frozen=True)
class AnchorCandidateValidation:
    candidate_present: bool
    candidate_theorem_facing: bool
    candidate_diagnostic_only: bool
    existing_covered_interval: tuple[float, float] | None
    candidate_covered_interval: tuple[float, float] | None
    combined_covered_interval: tuple[float, float] | None
    first_candidate_link_overlap: float | None
    min_anchor_segment_margin: float | None
    min_anchor_internal_overlap: float | None
    final_anchor_reached: bool
    anchor_chain_linked_to_existing_corridor: bool
    anchor_segments_verified: bool
    failure_fields: list[str]
    failed_segments: list[str]
    failed_links: list[str]
    candidate_segment_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LowerAnchorClosureError(RuntimeError):
    """Raised when a Phase-2B lower-anchor candidate is malformed."""


def _as_bundle(payload: Mapping[str, Any] | ProofAuditBundle) -> ProofAuditBundle:
    if isinstance(payload, ProofAuditBundle):
        return payload
    data = dict(payload)
    for key in ("lower_audit", "bundle"):
        if "proof_payload_version" not in data and isinstance(data.get(key), Mapping):
            data = dict(data[key])
    return bundle_from_dict(data)


def _load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise LowerAnchorClosureError(f"JSON object expected at {path}")
    return data


def load_lower_corridor_bundle(path: str | Path) -> ProofAuditBundle:
    return _as_bundle(_load_json(path))


def load_anchor_candidate(path: str | Path) -> dict[str, Any]:
    return _load_json(path)


def _finite(x: Any) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def _float(data: Mapping[str, Any], *keys: str, default: float | None = None) -> float:
    for key in keys:
        if key in data and data[key] is not None:
            return float(data[key])
    if default is not None:
        return float(default)
    raise LowerAnchorClosureError(f"candidate segment lacks any of keys {keys!r}")


def _candidate_container(candidate: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], dict[str, Any]]:
    """Return candidate segment rows and metadata from several accepted schemas."""

    data: Mapping[str, Any] = candidate
    if "proof_payload_version" in data:
        bundle = _as_bundle(data)
        meta = dict(bundle.audit_metadata)
        rows = list(bundle.raw_symbolic_fields.get("anchor_segments", bundle.raw_symbolic_fields.get("segments", [])))
        if not rows:
            rows = list(bundle.raw_symbolic_fields.get("candidate_segments", []))
        meta.setdefault("theorem_facing", True)
        meta.setdefault("diagnostic_only", False)
        meta.setdefault("source_schema", "ProofAuditBundle")
        return [dict(x) for x in rows], meta
    for key in ("anchor_segments", "segments", "candidate_segments"):
        if isinstance(data.get(key), list):
            meta = {k: v for k, v in data.items() if k not in {"anchor_segments", "segments", "candidate_segments"}}
            meta.setdefault("source_schema", f"plain-json/{key}")
            return [dict(x) for x in data[key]], meta
    raise LowerAnchorClosureError("anchor candidate must contain anchor_segments, segments, candidate_segments, or a ProofAuditBundle")


def segment_from_candidate_row(row: Mapping[str, Any], *, source_artifact: str) -> LowerChainSegment:
    """Convert one heavy-anchor candidate row into a LowerChainSegment.

    Accepted aliases intentionally mirror the names used in Phase-2 and in the
    manuscript: ``Y``/``residual_Y``, ``Z``/``linear_defect_Z``,
    ``T``/``tail_bound_T``, and ``r``/``radius_r``.
    """

    sid = str(row.get("segment_id", row.get("id", row.get("label", "anchor_segment"))))
    K_lo = _float(row, "K_lo", "k_lo", "K_min", "left")
    K_hi = _float(row, "K_hi", "k_hi", "K_max", "right")
    if K_hi <= K_lo:
        raise LowerAnchorClosureError(f"candidate segment {sid!r} has nonpositive K width")
    Y = _float(row, "residual_Y", "Y")
    Z = _float(row, "linear_defect_Z", "Z")
    T = _float(row, "tail_bound_T", "T", "tail_majorant")
    r = _float(row, "radius_r", "r", "validation_radius")
    margin = float(r - (Y + Z * r + T))
    stored_margin = float(row.get("radii_margin", row.get("margin", margin)))
    if not math.isclose(stored_margin, margin, rel_tol=1e-10, abs_tol=1e-15):
        # Keep the recomputed value; the validator will expose the mismatch if a
        # caller separately stores stale terms.  We reject here because Phase-2B
        # is an ingestion boundary, not a loose repair step.
        raise LowerAnchorClosureError(
            f"candidate segment {sid!r} stored margin {stored_margin!r} does not match recomputed {margin!r}"
        )
    return LowerChainSegment(
        segment_id=sid,
        K_lo=K_lo,
        K_hi=K_hi,
        K_mid=float(row.get("K_mid", 0.5 * (K_lo + K_hi))),
        rho=float(row.get("rho", (math.sqrt(5.0) - 1.0) / 2.0)),
        N=int(row.get("N", row.get("resolution_N", 0))),
        sigma=float(row.get("sigma", 0.0)),
        norm_name=str(row.get("norm_name", row.get("norm", "analytic_weighted_fourier"))),
        residual_Y=Y,
        linear_defect_Z=Z,
        tail_bound_T=T,
        radius_r=r,
        radii_margin=margin,
        small_divisor_min=float(row.get("small_divisor_min", row.get("small_divisor_lower_bound", 1.0))),
        small_divisor_inverse_bound=float(row.get("small_divisor_inverse_bound", row.get("cohomological_inverse_bound", 1.0))),
        overlap_with_next=None,
        source_module=str(row.get("source_module", row.get("module", "external_lower_anchor_candidate"))),
        source_artifact=str(row.get("source_artifact", source_artifact)),
        certified=bool(row.get("certified", True)),
    )


def normalize_anchor_candidate_segments(candidate: Mapping[str, Any], *, source_artifact: str) -> tuple[list[LowerChainSegment], dict[str, Any]]:
    rows, meta = _candidate_container(candidate)
    segments = [segment_from_candidate_row(row, source_artifact=source_artifact) for row in rows]
    segments.sort(key=lambda s: (float(s.K_lo), float(s.K_hi), s.segment_id))
    return segments, dict(meta)


def _copy_segment(seg: LowerChainSegment, *, overlap_with_next: float | None = None) -> LowerChainSegment:
    data = seg.to_dict()
    data.pop("lhs", None)
    data.pop("recomputed_radii_margin", None)
    data.pop("radii_margin_matches_recomputed", None)
    data.pop("radii_inequality_holds", None)
    data["overlap_with_next"] = overlap_with_next
    return LowerChainSegment.from_dict(data)


def _derive_overlaps(existing: Sequence[LowerChainSegment], anchor: Sequence[LowerChainSegment]) -> tuple[list[LowerChainSegment], AnchorCandidateValidation]:
    failure_fields: list[str] = []
    failed_segments: list[str] = []
    failed_links: list[str] = []

    existing_covered: tuple[float, float] | None = None
    if existing:
        existing_covered = (min(s.K_lo for s in existing), max(s.K_hi for s in existing if s.certified and s.recomputed_radii_margin > 0.0))

    candidate_covered: tuple[float, float] | None = None
    if anchor:
        candidate_covered = (min(s.K_lo for s in anchor), max(s.K_hi for s in anchor))

    if not anchor:
        failure_fields.append("anchor_candidate_missing")
        return list(existing), AnchorCandidateValidation(
            candidate_present=False,
            candidate_theorem_facing=False,
            candidate_diagnostic_only=False,
            existing_covered_interval=existing_covered,
            candidate_covered_interval=None,
            combined_covered_interval=existing_covered,
            first_candidate_link_overlap=None,
            min_anchor_segment_margin=None,
            min_anchor_internal_overlap=None,
            final_anchor_reached=False,
            anchor_chain_linked_to_existing_corridor=False,
            anchor_segments_verified=False,
            failure_fields=failure_fields,
            failed_segments=failed_segments,
            failed_links=failed_links,
            candidate_segment_count=0,
        )

    # Verify raw segment terms before merging with the old chain.
    margins = []
    for seg in anchor:
        margin = seg.recomputed_radii_margin
        margins.append(margin)
        if not seg.certified:
            failed_segments.append(f"{seg.segment_id}:certified_flag_false")
        if not math.isfinite(margin) or margin <= 0.0:
            failed_segments.append(f"{seg.segment_id}:nonpositive_radii_margin")
        if seg.radius_r <= 0.0:
            failed_segments.append(f"{seg.segment_id}:nonpositive_radius")
        if seg.small_divisor_min <= 0.0:
            failed_segments.append(f"{seg.segment_id}:small_divisor_min_not_positive")
        if seg.N <= 0:
            failed_segments.append(f"{seg.segment_id}:resolution_not_positive")
        if not seg.source_artifact:
            failed_segments.append(f"{seg.segment_id}:missing_source_artifact")
        if not seg.source_module:
            failed_segments.append(f"{seg.segment_id}:missing_source_module")

    internal_overlaps: list[float] = []
    anchor_with_overlaps: list[LowerChainSegment] = []
    for idx, seg in enumerate(anchor):
        overlap = None
        if idx < len(anchor) - 1:
            overlap = float(seg.K_hi - anchor[idx + 1].K_lo)
            if not math.isfinite(overlap) or overlap <= 0.0:
                failed_links.append(f"{seg.segment_id}->{anchor[idx + 1].segment_id}:nonpositive_K_overlap")
            else:
                internal_overlaps.append(overlap)
        anchor_with_overlaps.append(_copy_segment(seg, overlap_with_next=overlap))

    first_link_overlap: float | None = None
    if existing_covered is None:
        failed_links.append("existing_lower_corridor:missing")
    else:
        first_link_overlap = float(existing_covered[1] - anchor[0].K_lo)
        if not math.isfinite(first_link_overlap) or first_link_overlap <= 0.0:
            failed_links.append("existing_lower_corridor->anchor_candidate:nonpositive_K_overlap")

    existing_with_bridge = list(existing)
    if existing_with_bridge:
        existing_with_bridge[-1] = _copy_segment(existing_with_bridge[-1], overlap_with_next=first_link_overlap)

    if failed_segments:
        failure_fields.append("anchor_failed_segments")
    if failed_links:
        failure_fields.append("anchor_failed_links")

    combined = existing_with_bridge + anchor_with_overlaps
    combined_covered = None
    if combined:
        combined_covered = (min(s.K_lo for s in combined), max(s.K_hi for s in combined if s.certified and s.recomputed_radii_margin > 0.0))

    return combined, AnchorCandidateValidation(
        candidate_present=True,
        candidate_theorem_facing=True,
        candidate_diagnostic_only=False,
        existing_covered_interval=existing_covered,
        candidate_covered_interval=candidate_covered,
        combined_covered_interval=combined_covered,
        first_candidate_link_overlap=first_link_overlap,
        min_anchor_segment_margin=None if not margins else min(margins),
        min_anchor_internal_overlap=None if not internal_overlaps else min(internal_overlaps),
        final_anchor_reached=False,  # filled in build_anchor_closure_audit
        anchor_chain_linked_to_existing_corridor=bool(first_link_overlap is not None and first_link_overlap > 0.0),
        anchor_segments_verified=bool(not failed_segments and not failed_links),
        failure_fields=failure_fields,
        failed_segments=failed_segments,
        failed_links=failed_links,
        candidate_segment_count=len(anchor),
    )


def _existing_segments_from_bundle(bundle: ProofAuditBundle) -> list[LowerChainSegment]:
    return [LowerChainSegment.from_dict(row) for row in bundle.raw_symbolic_fields.get("segments", [])]


def build_anchor_closure_audit(
    lower_corridor_bundle: Mapping[str, Any] | ProofAuditBundle,
    *,
    anchor_candidate: Mapping[str, Any] | None = None,
    anchor_candidate_path: str | Path | None = None,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
) -> tuple[list[LowerChainSegment], AnchorCandidateValidation, LowerChainVerification, ProofAuditBundle]:
    """Build the Phase-2B lower-anchor closure payload.

    If ``anchor_candidate`` is ``None``, the return bundle is fail-closed and
    records ``anchor_candidate_missing``.  If a candidate is supplied, it is
    normalized, linked to the existing Phase-2 chain, and revalidated as one
    combined lower-corridor proof payload.
    """

    lower_bundle = _as_bundle(lower_corridor_bundle)
    existing = _existing_segments_from_bundle(lower_bundle)
    candidate_source = ""
    candidate_segments: list[LowerChainSegment] = []
    candidate_meta: dict[str, Any] = {}

    if anchor_candidate is not None:
        candidate_source = str(anchor_candidate_path or anchor_candidate.get("source_artifact", "external-anchor-candidate.json"))
        candidate_segments, candidate_meta = normalize_anchor_candidate_segments(anchor_candidate, source_artifact=candidate_source)
        if bool(candidate_meta.get("diagnostic_only", False)):
            # Keep rows but report fail-closed.  The candidate cannot be promoted.
            pass
    combined_segments, candidate_validation = _derive_overlaps(existing, candidate_segments)

    candidate_failure_fields = list(candidate_validation.failure_fields)
    if candidate_meta and bool(candidate_meta.get("diagnostic_only", False)):
        candidate_failure_fields.append("anchor_candidate_diagnostic_only")
    if candidate_meta and not bool(candidate_meta.get("theorem_facing", True)):
        candidate_failure_fields.append("anchor_candidate_not_theorem_facing")

    verification = verify_lower_chain(combined_segments, final_anchor=final_anchor, require_final_anchor=True)
    final_anchor_reached = verification.final_anchor_reached
    candidate_validation = AnchorCandidateValidation(
        candidate_present=candidate_validation.candidate_present,
        candidate_theorem_facing=bool(candidate_meta.get("theorem_facing", True)) if candidate_meta else False,
        candidate_diagnostic_only=bool(candidate_meta.get("diagnostic_only", False)) if candidate_meta else False,
        existing_covered_interval=candidate_validation.existing_covered_interval,
        candidate_covered_interval=candidate_validation.candidate_covered_interval,
        combined_covered_interval=candidate_validation.combined_covered_interval,
        first_candidate_link_overlap=candidate_validation.first_candidate_link_overlap,
        min_anchor_segment_margin=candidate_validation.min_anchor_segment_margin,
        min_anchor_internal_overlap=candidate_validation.min_anchor_internal_overlap,
        final_anchor_reached=final_anchor_reached,
        anchor_chain_linked_to_existing_corridor=candidate_validation.anchor_chain_linked_to_existing_corridor,
        anchor_segments_verified=bool(candidate_validation.anchor_segments_verified and not candidate_failure_fields),
        failure_fields=list(dict.fromkeys(candidate_failure_fields)),
        failed_segments=candidate_validation.failed_segments,
        failed_links=candidate_validation.failed_links,
        candidate_segment_count=candidate_validation.candidate_segment_count,
    )

    bundle = build_lower_chain_audit_bundle(
        combined_segments,
        final_anchor=final_anchor,
        claim="lower corridor proof-carrying chain reaches the near-critical golden lower anchor",
        source_artifacts=sorted({s.source_artifact for s in combined_segments if s.source_artifact}),
        require_final_anchor=True,
    )

    # Add Phase-2B-specific raw intervals and inequalities without weakening the
    # generic lower-chain validator.  These objects make the anchor closure
    # auditable separately from the pre-existing Phase-2 rows.
    raw = dict(bundle.raw_interval_fields)
    ineq = dict(bundle.derived_inequalities)
    bools = dict(bundle.derived_booleans)
    sym = dict(bundle.raw_symbolic_fields)

    # The Phase-8 validator always checks the canonical covered-interval
    # inequalities.  Older Phase-2 bundles omitted them when an explicit anchor
    # export segment was present; Phase-2B writes them unconditionally so the
    # strict replay can recompute final-anchor reach from raw endpoints.
    if "lower_chain_covered_interval" in raw and "final_anchor" in raw:
        covered = raw["lower_chain_covered_interval"]
        anchor = raw["final_anchor"]
        ineq.setdefault("covered_lo_below_final_anchor_lo", InequalityPayload(
            name="covered_lo_below_final_anchor_lo",
            lhs_label="covered_lo",
            rhs_label="final_anchor_lo",
            lhs_value=float(covered.lo),
            rhs_value=float(anchor.lo),
            sense="<=",
            margin=float(anchor.lo - covered.lo),
            source_fields=["final_anchor", "lower_chain_covered_interval"],
            source_artifact="phase2b-lower-anchor-closure",
        ))
        ineq.setdefault("covered_hi_reaches_final_anchor_hi", InequalityPayload(
            name="covered_hi_reaches_final_anchor_hi",
            lhs_label="final_anchor_hi",
            rhs_label="covered_hi",
            lhs_value=float(anchor.hi),
            rhs_value=float(covered.hi),
            sense="<=",
            margin=float(covered.hi - anchor.hi),
            source_fields=["final_anchor", "lower_chain_covered_interval"],
            source_artifact="phase2b-lower-anchor-closure",
        ))

    if candidate_validation.existing_covered_interval is not None:
        raw["phase2_existing_covered_interval"] = IntervalPayload(
            candidate_validation.existing_covered_interval[0],
            candidate_validation.existing_covered_interval[1],
            "phase2_existing_covered_interval",
            source_artifact="Phase-2 lower-corridor audit bundle",
            source_json_pointer="/raw_interval_fields/lower_chain_covered_interval",
        )
    if candidate_validation.candidate_covered_interval is not None:
        raw["anchor_candidate_covered_interval"] = IntervalPayload(
            candidate_validation.candidate_covered_interval[0],
            candidate_validation.candidate_covered_interval[1],
            "anchor_candidate_covered_interval",
            source_artifact=candidate_source,
            source_json_pointer="/anchor_segments/*/K_lo_K_hi",
        )
    link_margin = candidate_validation.first_candidate_link_overlap
    if link_margin is not None:
        raw["anchor_first_link_overlap"] = IntervalPayload(
            min(0.0, link_margin),
            max(0.0, link_margin) + 1.0e-15,
            "anchor_first_link_overlap",
            source_artifact=candidate_source,
            source_json_pointer="/anchor_segments/0/K_lo and phase2 covered hi",
        )
        ineq["anchor_chain_links_to_existing_corridor"] = InequalityPayload(
            name="anchor_chain_links_to_existing_corridor",
            lhs_label="zero",
            rhs_label="anchor_first_link_overlap",
            lhs_value=0.0,
            rhs_value=float(link_margin),
            sense="<",
            margin=float(link_margin),
            source_fields=["anchor_first_link_overlap", "phase2_existing_covered_interval", "anchor_candidate_covered_interval"],
            source_artifact=candidate_source,
        )
    if candidate_validation.min_anchor_segment_margin is not None:
        raw["anchor_min_segment_margin"] = IntervalPayload(
            0.0,
            candidate_validation.min_anchor_segment_margin,
            "anchor_min_segment_margin",
            source_artifact=candidate_source,
            source_json_pointer="/anchor_segments/*/radii_margin",
        )
        ineq["anchor_segment_margins_positive"] = InequalityPayload(
            name="anchor_segment_margins_positive",
            lhs_label="zero",
            rhs_label="anchor_min_segment_margin",
            lhs_value=0.0,
            rhs_value=float(candidate_validation.min_anchor_segment_margin),
            sense="<",
            margin=float(candidate_validation.min_anchor_segment_margin),
            source_fields=["anchor_min_segment_margin"],
            source_artifact=candidate_source,
        )
    if candidate_validation.min_anchor_internal_overlap is not None:
        raw["anchor_min_internal_overlap"] = IntervalPayload(
            0.0,
            candidate_validation.min_anchor_internal_overlap,
            "anchor_min_internal_overlap",
            source_artifact=candidate_source,
            source_json_pointer="/anchor_segments adjacent K overlaps",
        )
        ineq["anchor_internal_overlaps_positive"] = InequalityPayload(
            name="anchor_internal_overlaps_positive",
            lhs_label="zero",
            rhs_label="anchor_min_internal_overlap",
            lhs_value=0.0,
            rhs_value=float(candidate_validation.min_anchor_internal_overlap),
            sense="<",
            margin=float(candidate_validation.min_anchor_internal_overlap),
            source_fields=["anchor_min_internal_overlap"],
            source_artifact=candidate_source,
        )

    phase2b_failure_fields = list(dict.fromkeys(list(bundle.failure_fields) + list(candidate_validation.failure_fields)))
    if candidate_validation.candidate_present and not candidate_validation.final_anchor_reached:
        if "anchor_candidate_does_not_reach_final_anchor" not in phase2b_failure_fields:
            phase2b_failure_fields.append("anchor_candidate_does_not_reach_final_anchor")

    bools["lower_anchor_closure_candidate_verified"] = DerivedBoolean(
        name="lower_anchor_closure_candidate_verified",
        value=bool(candidate_validation.candidate_present and candidate_validation.anchor_segments_verified and candidate_validation.final_anchor_reached and not phase2b_failure_fields),
        derived_from=[k for k in ("anchor_chain_links_to_existing_corridor", "anchor_segment_margins_positive", "anchor_internal_overlaps_positive", "covered_hi_reaches_final_anchor_hi", "final_anchor_export_width_positive") if k in ineq],
        margin=min([
            x for x in (
                candidate_validation.first_candidate_link_overlap,
                candidate_validation.min_anchor_segment_margin,
                candidate_validation.min_anchor_internal_overlap if candidate_validation.min_anchor_internal_overlap is not None else candidate_validation.min_anchor_segment_margin,
                verification.min_radii_margin,
                verification.min_overlap_width,
            )
            if x is not None
        ] or [-1.0]),
        trusted_as_input=False,
        notes="True only when a supplied theorem-facing lower-anchor candidate links to the Phase-2 chain and reaches the final anchor.",
    )
    bools["anchor_chain_linked_to_existing_corridor"] = DerivedBoolean(
        name="anchor_chain_linked_to_existing_corridor",
        value=bool(candidate_validation.anchor_chain_linked_to_existing_corridor and not candidate_validation.candidate_diagnostic_only),
        derived_from=["anchor_chain_links_to_existing_corridor"] if "anchor_chain_links_to_existing_corridor" in ineq else [],
        margin=-1.0 if link_margin is None else float(link_margin),
        trusted_as_input=False,
    )

    sym["phase2b_anchor_candidate_validation"] = candidate_validation.to_dict()
    sym["phase2b_schema"] = "lower_anchor_closure_v1"
    sym["anchor_candidate_metadata"] = candidate_meta
    audit_metadata = dict(bundle.audit_metadata)
    audit_metadata.update({
        "phase": "2B",
        "audit_type": "lower-anchor-closure-proof-carrying-candidate-ingestion",
        "strict_promotion_rule": "candidate must be theorem-facing, non-diagnostic, linked to Phase-2 coverage, and final-anchor-reaching",
    })

    upgraded_bundle = ProofAuditBundle(
        proof_payload_version=bundle.proof_payload_version,
        theorem_layer=bundle.theorem_layer,
        claim="lower corridor proof-carrying chain reaches the near-critical golden lower anchor",
        raw_interval_fields=raw,
        raw_symbolic_fields=sym,
        derived_inequalities=ineq,
        derived_booleans=bools,
        validator_recomputed=True,
        active_assumptions=[],
        open_hypotheses=[],
        failure_fields=phase2b_failure_fields,
        source_artifacts=sorted(set(bundle.source_artifacts) | {candidate_source} if candidate_source else set(bundle.source_artifacts)),
        shell_payload={**dict(bundle.shell_payload), "phase2b_anchor_candidate_validation": candidate_validation.to_dict()},
        audit_metadata=audit_metadata,
    )
    return combined_segments, candidate_validation, verification, upgraded_bundle


def write_anchor_closure_outputs(
    *,
    segments: Sequence[LowerChainSegment],
    candidate_validation: AnchorCandidateValidation,
    verification: LowerChainVerification,
    bundle: ProofAuditBundle,
    out_json: str | Path,
    out_bundle: str | Path,
    out_csv: str | Path | None = None,
    out_tex: str | Path | None = None,
    fig_dir: str | Path | None = None,
) -> dict[str, Any]:
    report = {
        "schema": "phase2b_lower_anchor_closure_report_v1",
        "status": "passed" if not bundle.failure_fields and verification.lower_chain_verified else "failed-closed",
        "strict_final_ready_for_theorem_iii": bool(not bundle.failure_fields and verification.lower_chain_verified),
        "lower_chain_verified": verification.lower_chain_verified,
        "final_anchor_reached": verification.final_anchor_reached,
        "known_lower_gap": not verification.final_anchor_reached,
        "failure_fields": list(bundle.failure_fields),
        "candidate_validation": candidate_validation.to_dict(),
        "verification": verification.to_dict(),
        "segments": [s.to_dict() for s in segments],
        "lower_audit": bundle.to_dict(),
        "bundle": bundle.to_dict(),
        "figures": [],
    }
    out_path = Path(out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_lower_chain_bundle_json(bundle, out_bundle)
    if out_csv is not None:
        write_lower_chain_csv(segments, out_csv)
    if out_tex is not None:
        write_lower_chain_table(segments, out_tex)
    if fig_dir is not None:
        figs = generate_lower_chain_figures(segments, fig_dir)
        report["figures"] = [str(p) for p in figs]
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def anchor_candidate_template(*, final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR) -> dict[str, Any]:
    """Return a non-theorem template documenting the required heavy artifact schema."""

    lo, hi = float(final_anchor[0]), float(final_anchor[1])
    return {
        "schema": "lower_anchor_candidate_v1",
        "theorem_facing": False,
        "diagnostic_only": True,
        "notes": "Fill this with regenerated heavy lower-anchor rows before theorem-facing promotion.",
        "required_rule": "Rows must overlap the Phase-2 covered interval and each other, and the final row must cover the requested final anchor.",
        "anchor_segments": [
            {
                "segment_id": "example_replace_me_anchor_segment",
                "K_lo": lo - 1.0e-6,
                "K_hi": hi,
                "rho": (math.sqrt(5.0) - 1.0) / 2.0,
                "N": 0,
                "sigma": 0.0,
                "residual_Y": 0.0,
                "linear_defect_Z": 0.0,
                "tail_bound_T": 0.0,
                "radius_r": 0.0,
                "radii_margin": 0.0,
                "small_divisor_min": 0.0,
                "small_divisor_inverse_bound": 0.0,
                "source_module": "replace_with_heavy_solver_module",
                "source_artifact": "replace_with_hash_pinned_heavy_artifact.json",
                "certified": False,
            }
        ],
    }


def write_anchor_candidate_template(path: str | Path, *, final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(anchor_candidate_template(final_anchor=final_anchor), indent=2, sort_keys=True) + "\n")
    return out


# Test helper intentionally not used by CLI defaults.  It creates a mathematically
# shaped synthetic chain for negative/positive validator controls without placing
# any synthetic theorem-facing artifact in the released stage cache.
def build_synthetic_anchor_candidate_for_tests(
    *,
    start: float = 0.26499999,
    stop: float = DEFAULT_FINAL_ANCHOR[1] + 1.0e-8,
    n: int = 9,
    theorem_facing: bool = True,
    diagnostic_only: bool = False,
) -> dict[str, Any]:
    if n < 2:
        raise ValueError("n must be at least 2")
    width = (float(stop) - float(start)) / float(n)
    rows = []
    for i in range(n):
        k_lo = float(start) + i * width
        k_hi = float(start) + (i + 1) * width + (1.0e-5 if i < n - 1 else 0.0)
        r = 1.0e-4
        Y = 1.0e-5 + i * 1.0e-8
        Z = 0.05
        T = 7.0e-5 - i * 1.0e-8
        margin = r - (Y + Z * r + T)
        rows.append({
            "segment_id": f"synthetic_anchor_{i:02d}",
            "K_lo": k_lo,
            "K_hi": k_hi,
            "rho": (math.sqrt(5.0) - 1.0) / 2.0,
            "N": 256 + 16 * i,
            "sigma": 0.01,
            "residual_Y": Y,
            "linear_defect_Z": Z,
            "tail_bound_T": T,
            "radius_r": r,
            "radii_margin": margin,
            "small_divisor_min": 1.0e-3,
            "small_divisor_inverse_bound": 1.0e3,
            "source_module": "tests.synthetic_lower_anchor_solver",
            "source_artifact": "tests/synthetic_lower_anchor_candidate.json",
            "certified": True,
        })
    return {
        "schema": "lower_anchor_candidate_v1",
        "theorem_facing": theorem_facing,
        "diagnostic_only": diagnostic_only,
        "anchor_segments": rows,
    }
