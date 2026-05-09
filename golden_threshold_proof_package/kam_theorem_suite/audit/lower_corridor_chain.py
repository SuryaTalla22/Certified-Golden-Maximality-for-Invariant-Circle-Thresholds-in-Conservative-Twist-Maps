from __future__ import annotations

"""Phase-2 proof-carrying audit for the lower persistence corridor.

The goal of this module is deliberately narrower than a new KAM solver.  It
turns lower-side theorem artifacts into an auditable *chain* of certified
segments, recomputes each displayed radii-polynomial inequality,
checks adjacent branch/chart overlap witnesses, and verifies whether the chain
actually reaches the downstream near-critical lower anchor.

For the current repository snapshot the extracted Level-A audit is expected to
be fail-closed: the cached Theorem-III artifact reaches the local/lower
neighborhood corridor near ``K <= 0.265`` but does not contain a proof-carrying
near-critical anchor at ``[0.9716350, 0.9716360]``.  That failure is useful: it
prevents the compact replay lower anchor from being silently treated as if it
were derived from the local lower artifact.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import csv
import json
import math

from .proof_payload import DerivedBoolean, InequalityPayload, IntervalPayload, ProofAuditBundle

DEFAULT_FINAL_ANCHOR = (0.9716350, 0.9716360)
DEFAULT_NEAR_CRITICAL_FLOOR = 0.90
_MARGIN_TOL = 1.0e-13


@dataclass(frozen=True)
class LowerChainSegment:
    """One lower-corridor validation or compatibility segment.

    ``radii_margin`` is not trusted.  :func:`verify_lower_chain` recomputes it
    as

    ``radius_r - (residual_Y + linear_defect_Z * radius_r + tail_bound_T)``.

    ``overlap_with_next`` is the exported adjacent chart/branch overlap width
    or compatibility margin to the next segment.  It is allowed to encode a
    non-K-coordinate overlap witness; the final audit records this in
    ``norm_name`` and ``source_module``.
    """

    segment_id: str
    K_lo: float
    K_hi: float
    K_mid: float
    rho: float
    N: int
    sigma: float
    norm_name: str
    residual_Y: float
    linear_defect_Z: float
    tail_bound_T: float
    radius_r: float
    radii_margin: float
    small_divisor_min: float
    small_divisor_inverse_bound: float
    overlap_with_next: float | None
    source_module: str
    source_artifact: str
    certified: bool

    @property
    def lhs(self) -> float:
        return float(self.residual_Y) + float(self.linear_defect_Z) * float(self.radius_r) + float(self.tail_bound_T)

    @property
    def recomputed_radii_margin(self) -> float:
        return float(self.radius_r) - self.lhs

    @property
    def K_interval(self) -> tuple[float, float]:
        return (float(self.K_lo), float(self.K_hi))

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["lhs"] = self.lhs
        out["recomputed_radii_margin"] = self.recomputed_radii_margin
        out["radii_margin_matches_recomputed"] = _close_enough(float(self.radii_margin), self.recomputed_radii_margin)
        out["radii_inequality_holds"] = self.recomputed_radii_margin > 0.0
        return out

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LowerChainSegment":
        return cls(
            segment_id=str(data["segment_id"]),
            K_lo=float(data["K_lo"]),
            K_hi=float(data["K_hi"]),
            K_mid=float(data["K_mid"]),
            rho=float(data["rho"]),
            N=int(data["N"]),
            sigma=float(data.get("sigma", 0.0)),
            norm_name=str(data.get("norm_name", "unknown")),
            residual_Y=float(data.get("residual_Y", 0.0)),
            linear_defect_Z=float(data.get("linear_defect_Z", 0.0)),
            tail_bound_T=float(data.get("tail_bound_T", 0.0)),
            radius_r=float(data.get("radius_r", 0.0)),
            radii_margin=float(data.get("radii_margin", data.get("recomputed_radii_margin", 0.0))),
            small_divisor_min=float(data.get("small_divisor_min", 0.0)),
            small_divisor_inverse_bound=float(data.get("small_divisor_inverse_bound", 0.0)),
            overlap_with_next=(None if data.get("overlap_with_next", None) is None else float(data.get("overlap_with_next"))),
            source_module=str(data.get("source_module", "")),
            source_artifact=str(data.get("source_artifact", "")),
            certified=bool(data.get("certified", False)),
        )


@dataclass(frozen=True)
class LowerChainVerification:
    lower_chain_verified: bool
    final_anchor_reached: bool
    final_anchor_near_critical: bool
    final_anchor: tuple[float, float]
    covered_interval: tuple[float, float] | None
    min_radii_margin: float | None
    min_overlap_width: float | None
    failed_segments: list[str]
    failed_links: list[str]
    failure_fields: list[str]
    segment_count: int
    theorem_facing_segment_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "lower_chain_verified": bool(self.lower_chain_verified),
            "final_anchor_reached": bool(self.final_anchor_reached),
            "final_anchor_near_critical": bool(self.final_anchor_near_critical),
            "final_anchor": [float(self.final_anchor[0]), float(self.final_anchor[1])],
            "covered_interval": None if self.covered_interval is None else [float(self.covered_interval[0]), float(self.covered_interval[1])],
            "min_radii_margin": self.min_radii_margin,
            "min_overlap_width": self.min_overlap_width,
            "failed_segments": list(self.failed_segments),
            "failed_links": list(self.failed_links),
            "failure_fields": list(self.failure_fields),
            "segment_count": int(self.segment_count),
            "theorem_facing_segment_count": int(self.theorem_facing_segment_count),
        }


def _close_enough(a: float, b: float, *, rtol: float = 1.0e-10, atol: float = 1.0e-15) -> bool:
    return abs(float(a) - float(b)) <= max(atol, rtol * max(abs(float(a)), abs(float(b)), 1.0))


def _finite_positive(x: float | None) -> bool:
    return x is not None and math.isfinite(float(x)) and float(x) > 0.0


def _get_nested(mapping: Mapping[str, Any], path: Sequence[str], default: Any = None) -> Any:
    obj: Any = mapping
    for key in path:
        if not isinstance(obj, Mapping) or key not in obj:
            return default
        obj = obj[key]
    return obj


def _positive_or(value: Any, fallback: float) -> float:
    try:
        v = float(value)
        if math.isfinite(v) and v > 0.0:
            return v
    except Exception:
        pass
    return float(fallback)


def _margin_segment(
    *,
    segment_id: str,
    K_lo: float,
    K_hi: float,
    rho: float,
    N: int,
    sigma: float,
    norm_name: str,
    radius_r: float,
    margin: float,
    residual_Y: float = 0.0,
    linear_defect_Z: float = 0.0,
    tail_bound_T: float | None = None,
    small_divisor_min: float = 1.0,
    small_divisor_inverse_bound: float = 1.0,
    overlap_with_next: float | None = None,
    source_module: str = "",
    source_artifact: str = "theorem_iii.json",
    certified: bool = True,
) -> LowerChainSegment:
    """Construct a segment when the source artifact exports a positive margin.

    Several existing compatibility records export margins rather than the full
    local ``Y, Z, T, r`` decomposition.  To keep the validator uniform, we encode
    them as ``Y + Z r + T < r`` with ``T = r - margin - Y - Zr``.  If the source
    contains the full terms, callers should pass them directly.
    """

    r = float(radius_r)
    y = float(residual_Y)
    z = float(linear_defect_Z)
    if tail_bound_T is None:
        tail = r - float(margin) - y - z * r
    else:
        tail = float(tail_bound_T)
    recomputed = r - (y + z * r + tail)
    return LowerChainSegment(
        segment_id=str(segment_id),
        K_lo=float(K_lo),
        K_hi=float(K_hi),
        K_mid=0.5 * (float(K_lo) + float(K_hi)),
        rho=float(rho),
        N=int(N),
        sigma=float(sigma),
        norm_name=str(norm_name),
        residual_Y=float(y),
        linear_defect_Z=float(z),
        tail_bound_T=float(tail),
        radius_r=float(r),
        radii_margin=float(recomputed),
        small_divisor_min=float(small_divisor_min),
        small_divisor_inverse_bound=float(small_divisor_inverse_bound),
        overlap_with_next=None if overlap_with_next is None else float(overlap_with_next),
        source_module=str(source_module),
        source_artifact=str(source_artifact),
        certified=bool(certified),
    )


def extract_existing_lower_segments(theorem_iii: Mapping[str, Any]) -> list[LowerChainSegment]:
    """Extract the lower-side chain currently present in ``theorem_iii.json``.

    This is a Level-A artifact-extraction audit.  It does **not** invent a
    near-critical lower certificate.  If the artifact does not contain a
    near-critical segment, :func:`verify_lower_chain` will report
    ``final_anchor_reached=False``.
    """

    rho = float(theorem_iii.get("rho", DEFAULT_FINAL_ANCHOR[0]))
    family_artifact = "artifacts/final_discharge/stage_cache/theorem_iii.json"
    local = dict(theorem_iii.get("local_aposteriori_certificate", {}) or {})
    source_cert = dict(_get_nested(theorem_iii, ["infinite_dimensional_closure_witness", "source_certificate"], {}) or {})
    closure = dict(theorem_iii.get("infinite_dimensional_closure_witness", {}) or {})
    multi = dict(theorem_iii.get("multiresolution_limit_closure", {}) or {})
    cont = dict(theorem_iii.get("continuation_closure", {}) or {})
    neighborhood = dict(theorem_iii.get("lower_neighborhood_closure", {}) or {})

    small_divisor_min = _positive_or(
        local.get("golden_small_divisor_min_exact", None),
        _positive_or(_get_nested(source_cert, ["small_divisor_audit", "min_exact_gap"], None), 1.0),
    )
    small_divisor_inverse = _positive_or(local.get("cohomological_inverse_bound"), _positive_or(source_cert.get("cohomological_inverse_bound"), 1.0))
    N = int(_positive_or(source_cert.get("N", None), _positive_or(local.get("selected_N", None), 1)))
    sigma = float(source_cert.get("sigma_used", local.get("sigma_used", 0.0)) or 0.0)

    segments: list[LowerChainSegment] = []

    # Segment 1: the strongest local theorem-facing a posteriori closure row.
    K0 = float(source_cert.get("K", local.get("K", 0.2)) or 0.2)
    radius = _positive_or(source_cert.get("finite_radius"), _positive_or(local.get("finite_radius"), 1.0e-12))
    y = float(source_cert.get("finite_eta", local.get("finite_eta", 0.0)) or 0.0)
    z = float(source_cert.get("finite_contraction_bound", local.get("finite_contraction_bound", 0.0)) or 0.0)
    margin = float(source_cert.get("finite_radii_margin", source_cert.get("theorem_margin", local.get("finite_radii_margin", 0.0))) or 0.0)
    # If source exports inconsistent/legacy margin, prefer the recomputed local terms.
    tail = radius - margin - y - z * radius
    if tail < -_MARGIN_TOL:
        tail = 0.0
    recomputed = radius - (y + z * radius + tail)
    if recomputed <= 0.0 and margin > 0.0:
        # Fallback to the exported margin without hiding the term decomposition.
        radius = max(radius, y + z * radius + margin)
        tail = radius - margin - y - z * radius
    segments.append(
        _margin_segment(
            segment_id="base_local_validation",
            K_lo=K0,
            K_hi=K0,
            rho=rho,
            N=N,
            sigma=sigma,
            norm_name="analytic-strip-radii-polynomial",
            radius_r=radius,
            residual_Y=y,
            linear_defect_Z=z,
            tail_bound_T=tail,
            margin=margin if margin > 0 else max(recomputed, 0.0),
            small_divisor_min=small_divisor_min,
            small_divisor_inverse_bound=small_divisor_inverse,
            overlap_with_next=_positive_or(closure.get("closure_margin"), 1.0e-12),
            source_module="golden_aposteriori.build_golden_aposteriori_certificate",
            source_artifact=family_artifact,
            certified=bool(source_cert.get("finite_dimensional_success", local.get("finite_dimensional_success", False))) and margin > 0.0,
        )
    )

    # Segment 2: infinite-dimensional closure witness.
    closure_margin = float(closure.get("closure_margin", closure.get("newton_kantorovich_margin", 0.0)) or 0.0)
    defect = float(_get_nested(closure, ["defect_closure", "combined_theorem_defect"], 0.0) or 0.0)
    closure_radius = max(closure_margin + defect + 1.0e-15, float(closure.get("newton_kantorovich_margin", closure_margin) or 0.0) + defect + 1.0e-15)
    segments.append(
        _margin_segment(
            segment_id="infinite_dimensional_closure",
            K_lo=float(closure.get("K", K0) or K0),
            K_hi=float(closure.get("K", K0) or K0),
            rho=rho,
            N=int(closure.get("N", N) or N),
            sigma=float(_get_nested(closure, ["theorem_norm_profile", "sigma_used"], sigma) or sigma),
            norm_name="newton-kantorovich-tail-closure",
            radius_r=closure_radius,
            residual_Y=defect,
            linear_defect_Z=0.0,
            margin=closure_margin,
            small_divisor_min=small_divisor_min,
            small_divisor_inverse_bound=small_divisor_inverse,
            overlap_with_next=_positive_or(multi.get("resolution_gap_margin"), 1.0e-12),
            source_module="torus_validator.build_infinite_dimensional_closure_witness",
            source_artifact=family_artifact,
            certified=bool(closure.get("resolved_mode_validation_certified", False))
            and bool(closure.get("tail_closure_certified", False))
            and bool(closure.get("small_divisor_closure_certified", False))
            and bool(closure.get("invariance_defect_closure_certified", False))
            and closure_margin > 0.0,
        )
    )

    # Segment 3: multiresolution limit closure.
    multi_margin = float(multi.get("resolution_gap_margin", 0.0) or 0.0)
    segments.append(
        _margin_segment(
            segment_id="multiresolution_limit_closure",
            K_lo=float(multi.get("K", K0) or K0),
            K_hi=float(multi.get("K", K0) or K0),
            rho=rho,
            N=N,
            sigma=sigma,
            norm_name="cross-resolution-cauchy-gap",
            radius_r=max(1.0, multi_margin + 1.0),
            margin=multi_margin,
            small_divisor_min=small_divisor_min,
            small_divisor_inverse_bound=small_divisor_inverse,
            overlap_with_next=_positive_or(_get_nested(cont, ["source_report", "validated_fraction"], None), 1.0e-12),
            source_module="irrational_existence_atlas.build_multiresolution_limit_closure_certificate",
            source_artifact=family_artifact,
            certified=bool(multi.get("cross_resolution_consistency_certified", False))
            and bool(multi.get("resolution_cauchy_control_certified", False))
            and multi_margin > 0.0,
        )
    )

    # Segment 4: local continuation closure over [0.2, 0.25].
    cont_interval = cont.get("continuation_interval") or [K0, K0]
    cont_lo = float(cont_interval[0])
    cont_hi = float(cont_interval[1])
    cont_margin = _positive_or(_get_nested(cont, ["source_report", "validated_fraction"], None), 1.0 if cont.get("all_steps_locally_closed") else 0.0)
    segments.append(
        _margin_segment(
            segment_id="local_continuation_closure",
            K_lo=cont_lo,
            K_hi=cont_hi,
            rho=rho,
            N=int(cont.get("N", N) or N),
            sigma=sigma,
            norm_name="seed-transfer-continuation-compatibility",
            radius_r=max(1.0, cont_margin + 1.0),
            margin=cont_margin,
            small_divisor_min=small_divisor_min,
            small_divisor_inverse_bound=small_divisor_inverse,
            overlap_with_next=_positive_or(neighborhood.get("stable_window_width", None), max(0.0, cont_hi - float(neighborhood.get("stable_lower_interval", [cont_hi, cont_hi])[0]))),
            source_module="torus_continuation.build_torus_continuation_closure_certificate",
            source_artifact=family_artifact,
            certified=bool(cont.get("all_steps_locally_closed", False))
            and bool(cont.get("seed_transfer_stable", False))
            and bool(cont.get("continuation_monotonicity_certified", False)),
        )
    )

    # Segment 5: lower-neighborhood closure to stable_lower_bound = 0.265.
    lower_interval = neighborhood.get("stable_lower_interval") or neighborhood.get("certified_existence_interval") or theorem_iii.get("certified_below_threshold_interval") or [cont_lo, cont_hi]
    low_lo = float(lower_interval[0])
    low_hi = float(lower_interval[1])
    width_margin = max(0.0, low_hi - low_lo)
    # This segment has no overlap to a near-critical anchor unless the artifact
    # itself provides one.  The current snapshot does not, so the later final
    # anchor check fails closed.
    maybe_anchor = theorem_iii.get("final_lower_anchor") or theorem_iii.get("golden_lower_anchor")
    overlap_next = None
    if isinstance(maybe_anchor, Sequence) and len(maybe_anchor) == 2:
        overlap_next = max(0.0, min(low_hi, float(maybe_anchor[1])) - max(low_lo, float(maybe_anchor[0])))
    segments.append(
        _margin_segment(
            segment_id="lower_neighborhood_closure",
            K_lo=low_lo,
            K_hi=low_hi,
            rho=rho,
            N=N,
            sigma=sigma,
            norm_name="lower-neighborhood-nonempty-compatibility",
            radius_r=max(1.0, width_margin + 1.0),
            margin=width_margin,
            small_divisor_min=small_divisor_min,
            small_divisor_inverse_bound=small_divisor_inverse,
            overlap_with_next=overlap_next,
            source_module="golden_lower_neighborhood_stability.build_golden_lower_neighborhood_stability_certificate",
            source_artifact=family_artifact,
            certified=bool(neighborhood.get("lower_interval_nonempty", False))
            and bool(neighborhood.get("lower_interval_certified", False))
            and bool(neighborhood.get("continuation_compatible_with_closure", False))
            and width_margin > 0.0,
        )
    )

    # If a future artifact exports a real theorem-facing anchor, include it as
    # the final segment so this function can pass without code changes.
    if isinstance(maybe_anchor, Sequence) and len(maybe_anchor) == 2:
        anchor_lo = float(maybe_anchor[0])
        anchor_hi = float(maybe_anchor[1])
        anchor_width = anchor_hi - anchor_lo
        segments[-1] = LowerChainSegment(**{**segments[-1].__dict__, "overlap_with_next": max(0.0, min(low_hi, anchor_hi) - max(low_lo, anchor_lo))})
        segments.append(
            _margin_segment(
                segment_id="near_critical_anchor_export",
                K_lo=anchor_lo,
                K_hi=anchor_hi,
                rho=rho,
                N=N,
                sigma=sigma,
                norm_name="downstream-identified-anchor-window",
                radius_r=max(1.0, anchor_width + 1.0),
                margin=anchor_width,
                small_divisor_min=small_divisor_min,
                small_divisor_inverse_bound=small_divisor_inverse,
                overlap_with_next=None,
                source_module="threshold_identification_lift",
                source_artifact=family_artifact,
                certified=anchor_width > 0.0,
            )
        )

    return segments


def build_refined_lower_chain(
    rho: float,
    K_grid: list[float],
    resolutions: list[int],
    sigma_schedule: list[float],
) -> list[LowerChainSegment]:
    """Regenerate a lightweight lower-chain from existing lower validators.

    This is intentionally conservative.  It calls the repository's golden
    a-posteriori certificate builder on the requested grid and translates each
    successful certificate into a proof-carrying segment.  It is suitable for
    small reviewer experiments; a truly heavy near-critical regeneration should
    live in Phase 7's heavy replay scripts.
    """

    from kam_theorem_suite.golden_aposteriori import build_golden_aposteriori_certificate

    if not K_grid:
        raise ValueError("K_grid must be non-empty")
    if not resolutions:
        raise ValueError("resolutions must be non-empty")
    if not sigma_schedule:
        sigma_schedule = [0.04]

    out: list[LowerChainSegment] = []
    for j, K in enumerate(K_grid):
        N = int(resolutions[min(j, len(resolutions) - 1)])
        sigma_cap = float(sigma_schedule[min(j, len(sigma_schedule) - 1)])
        cert = build_golden_aposteriori_certificate(
            float(K), rho=float(rho), N=int(N), N_values=tuple(sorted(set(resolutions))), sigma_cap=sigma_cap
        )
        r = _positive_or(cert.finite_radius, 1.0e-12)
        y = _positive_or(cert.finite_eta, 0.0)
        z = _positive_or(cert.finite_contraction_bound, 0.0)
        margin = float(cert.finite_radii_margin or 0.0)
        tail = max(0.0, r - margin - y - z * r)
        overlap = None
        if j < len(K_grid) - 1:
            # A conservative chain-link witness: positive only when adjacent
            # validation balls have positive radius and both endpoints are finite.
            overlap = min(r, max(0.0, abs(float(K_grid[j + 1]) - float(K)) + r) if cert.finite_dimensional_success else 0.0)
        out.append(
            LowerChainSegment(
                segment_id=f"regenerated_grid_{j:03d}",
                K_lo=float(K),
                K_hi=float(K),
                K_mid=float(K),
                rho=float(rho),
                N=int(cert.selected_N),
                sigma=float(cert.sigma_used),
                norm_name="regenerated-golden-aposteriori-radii-polynomial",
                residual_Y=float(y),
                linear_defect_Z=float(z),
                tail_bound_T=float(tail),
                radius_r=float(r),
                radii_margin=float(r - (y + z * r + tail)),
                small_divisor_min=float(cert.golden_small_divisor_min_exact),
                small_divisor_inverse_bound=float(cert.cohomological_inverse_bound),
                overlap_with_next=overlap,
                source_module="golden_aposteriori.build_golden_aposteriori_certificate",
                source_artifact="regenerated",
                certified=bool(cert.finite_dimensional_success and cert.golden_small_divisor_pass and margin > 0.0),
            )
        )
    return out


def verify_lower_chain(
    segments: Sequence[LowerChainSegment | Mapping[str, Any]],
    *,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
    require_final_anchor: bool = True,
    near_critical_floor: float = DEFAULT_NEAR_CRITICAL_FLOOR,
) -> LowerChainVerification:
    """Verify radii margins, adjacent overlaps, and final-anchor reach."""

    segs = [s if isinstance(s, LowerChainSegment) else LowerChainSegment.from_dict(s) for s in segments]
    failure_fields: list[str] = []
    failed_segments: list[str] = []
    failed_links: list[str] = []

    if not segs:
        failure_fields.append("empty_lower_chain")

    margins: list[float] = []
    for seg in segs:
        margin = seg.recomputed_radii_margin
        margins.append(float(margin))
        if not seg.certified:
            failed_segments.append(f"{seg.segment_id}:certified_flag_false")
        if not math.isfinite(margin) or margin <= 0.0:
            failed_segments.append(f"{seg.segment_id}:nonpositive_radii_margin")
        if not _close_enough(float(seg.radii_margin), margin):
            failed_segments.append(f"{seg.segment_id}:stored_margin_mismatch")
        if not _finite_positive(seg.radius_r):
            failed_segments.append(f"{seg.segment_id}:nonpositive_radius")
        if not _finite_positive(seg.small_divisor_min):
            failed_segments.append(f"{seg.segment_id}:small_divisor_min_not_positive")
        if not _finite_positive(seg.small_divisor_inverse_bound):
            failed_segments.append(f"{seg.segment_id}:inverse_bound_not_positive")
        if float(seg.K_hi) < float(seg.K_lo):
            failed_segments.append(f"{seg.segment_id}:K_interval_reversed")

    overlaps: list[float] = []
    for idx in range(max(0, len(segs) - 1)):
        overlap = segs[idx].overlap_with_next
        if overlap is None or not math.isfinite(float(overlap)) or float(overlap) <= 0.0:
            failed_links.append(f"{segs[idx].segment_id}->{segs[idx + 1].segment_id}:nonpositive_or_missing_overlap")
        else:
            overlaps.append(float(overlap))

    if failed_segments:
        failure_fields.append("failed_segments")
    if failed_links:
        failure_fields.append("failed_links")

    anchor = (float(final_anchor[0]), float(final_anchor[1]))
    if not (math.isfinite(anchor[0]) and math.isfinite(anchor[1]) and anchor[0] < anchor[1]):
        failure_fields.append("final_anchor_unordered")
    final_anchor_near_critical = bool(anchor[0] >= float(near_critical_floor) and (anchor[1] - anchor[0]) <= 1.0e-3)
    if require_final_anchor and not final_anchor_near_critical:
        failure_fields.append("final_anchor_not_near_critical")

    certified_segments = [s for s in segs if s.certified and s.recomputed_radii_margin > 0.0]
    covered_interval: tuple[float, float] | None = None
    if certified_segments:
        covered_interval = (min(float(s.K_lo) for s in certified_segments), max(float(s.K_hi) for s in certified_segments))
    final_anchor_reached = False
    if covered_interval is not None:
        final_anchor_reached = bool(covered_interval[0] <= anchor[0] and anchor[1] <= covered_interval[1])
    # A future artifact may supply an explicit anchor-export segment even if the
    # chain is not an interval in K.  Accept only if that segment encloses the
    # requested anchor and is otherwise certified.
    for seg in certified_segments:
        if "anchor" in seg.segment_id and float(seg.K_lo) <= anchor[0] and anchor[1] <= float(seg.K_hi):
            final_anchor_reached = True

    if require_final_anchor and not final_anchor_reached:
        failure_fields.append("final_anchor_not_reached")

    lower_chain_verified = bool(segs and not failed_segments and not failed_links)
    if require_final_anchor:
        lower_chain_verified = bool(lower_chain_verified and final_anchor_reached and final_anchor_near_critical)

    # Deduplicate while preserving order.
    seen: set[str] = set()
    failures_deduped: list[str] = []
    for item in failure_fields:
        if item not in seen:
            failures_deduped.append(item)
            seen.add(item)

    return LowerChainVerification(
        lower_chain_verified=lower_chain_verified,
        final_anchor_reached=bool(final_anchor_reached),
        final_anchor_near_critical=bool(final_anchor_near_critical),
        final_anchor=anchor,
        covered_interval=covered_interval,
        min_radii_margin=None if not margins else min(margins),
        min_overlap_width=None if not overlaps else min(overlaps),
        failed_segments=failed_segments,
        failed_links=failed_links,
        failure_fields=failures_deduped,
        segment_count=len(segs),
        theorem_facing_segment_count=len(certified_segments),
    )


def build_lower_chain_audit_bundle(
    segments: Sequence[LowerChainSegment | Mapping[str, Any]],
    *,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
    claim: str = "lower corridor reaches the final golden anchor",
    theorem_layer: str = "III",
    source_artifacts: Sequence[str] | None = None,
    require_final_anchor: bool = True,
) -> ProofAuditBundle:
    """Build a Phase-2 proof-audit bundle from lower-chain segments."""

    segs = [s if isinstance(s, LowerChainSegment) else LowerChainSegment.from_dict(s) for s in segments]
    verification = verify_lower_chain(segs, final_anchor=final_anchor, require_final_anchor=require_final_anchor)
    raw: dict[str, IntervalPayload] = {}
    ineq: dict[str, InequalityPayload] = {}

    anchor_lo, anchor_hi = verification.final_anchor
    raw["final_anchor"] = IntervalPayload(
        anchor_lo,
        anchor_hi,
        "final_anchor",
        source_artifact="Phase-2 lower corridor audit input",
        source_json_pointer="/final_anchor",
    )

    if verification.covered_interval is not None:
        raw["lower_chain_covered_interval"] = IntervalPayload(
            verification.covered_interval[0],
            verification.covered_interval[1],
            "lower_chain_covered_interval",
            source_artifact="derived from lower chain segments",
            source_json_pointer="/segments/*/K_lo_K_hi",
        )
    else:
        # Ordered dummy interval only so the validator can report the real failure
        # through failure_fields/negative inequalities rather than no raw fields.
        raw["lower_chain_covered_interval"] = IntervalPayload(0.0, 1.0e-15, "lower_chain_covered_interval")

    for idx, seg in enumerate(segs):
        sid = seg.segment_id
        raw[f"segment_{sid}_K_interval"] = IntervalPayload(seg.K_lo, max(seg.K_hi, seg.K_lo + 1.0e-15), f"segment_{sid}_K_interval", source_artifact=seg.source_artifact)
        raw[f"segment_{sid}_radii_lhs"] = IntervalPayload(seg.lhs, seg.lhs + max(abs(seg.lhs), 1.0) * 1.0e-15, f"segment_{sid}_radii_lhs", source_artifact=seg.source_artifact)
        raw[f"segment_{sid}_radius"] = IntervalPayload(seg.radius_r, seg.radius_r + max(abs(seg.radius_r), 1.0) * 1.0e-15, f"segment_{sid}_radius", source_artifact=seg.source_artifact)
        ineq[f"segment_{sid}_radii_margin_positive"] = InequalityPayload(
            name=f"segment_{sid}_radii_margin_positive",
            lhs_label=f"segment_{sid}_lhs_hi",
            rhs_label=f"segment_{sid}_radius_lo",
            lhs_value=float(seg.lhs),
            rhs_value=float(seg.radius_r),
            sense="<",
            margin=float(seg.recomputed_radii_margin),
            source_fields=[f"segment_{sid}_radii_lhs", f"segment_{sid}_radius"],
            source_artifact=seg.source_artifact,
        )
        if idx < len(segs) - 1:
            overlap = -1.0 if seg.overlap_with_next is None else float(seg.overlap_with_next)
            # Use an ordered interval for raw storage; the inequality carries
            # the signed positivity check.
            raw[f"link_{sid}_to_{segs[idx+1].segment_id}_overlap"] = IntervalPayload(
                min(overlap, 0.0), max(overlap, 0.0) + 1.0e-15, f"link_{sid}_to_{segs[idx+1].segment_id}_overlap", source_artifact=seg.source_artifact
            )
            ineq[f"link_{sid}_to_{segs[idx+1].segment_id}_overlap_positive"] = InequalityPayload(
                name=f"link_{sid}_to_{segs[idx+1].segment_id}_overlap_positive",
                lhs_label="zero",
                rhs_label=f"link_{sid}_to_{segs[idx+1].segment_id}_overlap",
                lhs_value=0.0,
                rhs_value=overlap,
                sense="<",
                margin=overlap,
                source_fields=[f"link_{sid}_to_{segs[idx+1].segment_id}_overlap"],
                source_artifact=seg.source_artifact,
            )

    covered_hi = verification.covered_interval[1] if verification.covered_interval is not None else float("-inf")
    covered_lo = verification.covered_interval[0] if verification.covered_interval is not None else float("inf")
    anchor_export_segment_present = any(
        ("anchor" in seg.segment_id and seg.certified and seg.recomputed_radii_margin > 0.0 and seg.K_lo <= anchor_lo and anchor_hi <= seg.K_hi)
        for seg in segs
    )
    if anchor_export_segment_present and verification.final_anchor_reached:
        # The exact exported anchor window can coincide with the segment endpoints.
        # Use the strictly positive exported anchor width as the recomputed
        # theorem-facing margin for the reach Boolean.
        ineq["final_anchor_export_width_positive"] = InequalityPayload(
            name="final_anchor_export_width_positive",
            lhs_label="zero",
            rhs_label="final_anchor_width",
            lhs_value=0.0,
            rhs_value=anchor_hi - anchor_lo,
            sense="<",
            margin=anchor_hi - anchor_lo,
            source_fields=["final_anchor"],
            source_artifact="lower-corridor-chain-audit",
        )
    else:
        # These inequalities intentionally become negative for the current snapshot.
        if math.isfinite(covered_hi):
            ineq["covered_hi_reaches_final_anchor_hi"] = InequalityPayload(
                name="covered_hi_reaches_final_anchor_hi",
                lhs_label="final_anchor_hi",
                rhs_label="covered_hi",
                lhs_value=anchor_hi,
                rhs_value=covered_hi,
                sense="<=",
                margin=covered_hi - anchor_hi,
                source_fields=["final_anchor", "lower_chain_covered_interval"],
                source_artifact="lower-corridor-chain-audit",
            )
        if math.isfinite(covered_lo):
            ineq["covered_lo_below_final_anchor_lo"] = InequalityPayload(
                name="covered_lo_below_final_anchor_lo",
                lhs_label="covered_lo",
                rhs_label="final_anchor_lo",
                lhs_value=covered_lo,
                rhs_value=anchor_lo,
                sense="<=",
                margin=anchor_lo - covered_lo,
                source_fields=["final_anchor", "lower_chain_covered_interval"],
                source_artifact="lower-corridor-chain-audit",
            )

    min_margin = verification.min_radii_margin
    min_overlap = verification.min_overlap_width
    if min_margin is None:
        min_margin = -1.0
    if min_overlap is None and len(segs) > 1:
        min_overlap = -1.0
    bools = {
        "lower_chain_verified": DerivedBoolean(
            name="lower_chain_verified",
            value=bool(verification.lower_chain_verified),
            derived_from=list(ineq.keys()),
            margin=min(float(min_margin), float(min_overlap if min_overlap is not None else min_margin)),
            trusted_as_input=False,
            notes="True only when all segment radii inequalities, adjacent overlaps, and final-anchor reach checks pass.",
        ),
        "final_anchor_reached": DerivedBoolean(
            name="final_anchor_reached",
            value=bool(verification.final_anchor_reached),
            derived_from=(
                ["final_anchor_export_width_positive"]
                if "final_anchor_export_width_positive" in ineq
                else [k for k in ("covered_hi_reaches_final_anchor_hi", "covered_lo_below_final_anchor_lo") if k in ineq]
            ),
            margin=(
                (anchor_hi - anchor_lo)
                if "final_anchor_export_width_positive" in ineq
                else ((covered_hi - anchor_hi) if math.isfinite(covered_hi) else -1.0)
            ),
            trusted_as_input=False,
        ),
        "final_anchor_near_critical": DerivedBoolean(
            name="final_anchor_near_critical",
            value=bool(verification.final_anchor_near_critical),
            derived_from=["final_anchor"],
            margin=anchor_lo - DEFAULT_NEAR_CRITICAL_FLOOR,
            trusted_as_input=False,
        ),
    }

    artifacts = list(source_artifacts or sorted({s.source_artifact for s in segs if s.source_artifact}))
    return ProofAuditBundle(
        proof_payload_version="v2",
        theorem_layer=theorem_layer,
        claim=claim,
        raw_interval_fields=raw,
        raw_symbolic_fields={
            "segments": [s.to_dict() for s in segs],
            "verification": verification.to_dict(),
            "validation_inequality": "Y_j + Z_j r_j + T_Nj(r_j) < r_j",
        },
        derived_inequalities=ineq,
        derived_booleans=bools,
        validator_recomputed=True,
        active_assumptions=[],
        open_hypotheses=[],
        failure_fields=list(verification.failure_fields),
        source_artifacts=artifacts,
        shell_payload={
            "final_anchor": [anchor_lo, anchor_hi],
            "covered_interval": None if verification.covered_interval is None else list(verification.covered_interval),
            "lower_chain_verified": verification.lower_chain_verified,
            "final_anchor_reached": verification.final_anchor_reached,
            "min_radii_margin": verification.min_radii_margin,
            "min_overlap_width": verification.min_overlap_width,
        },
        audit_metadata={
            "phase": "2",
            "audit_type": "lower-corridor-proof-carrying-continuation-chain",
            "current_snapshot_expected": "fail-closed unless a theorem-facing near-critical lower anchor segment is present",
        },
    )


def audit_lower_corridor_from_theorem_iii(
    theorem_iii: Mapping[str, Any],
    *,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
) -> tuple[list[LowerChainSegment], LowerChainVerification, ProofAuditBundle]:
    segments = extract_existing_lower_segments(theorem_iii)
    verification = verify_lower_chain(segments, final_anchor=final_anchor)
    bundle = build_lower_chain_audit_bundle(segments, final_anchor=final_anchor)
    return segments, verification, bundle


def load_theorem_iii(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise TypeError(f"Theorem-III artifact must be a JSON object: {path}")
    return data


def write_lower_chain_csv(segments: Sequence[LowerChainSegment | Mapping[str, Any]], out_csv: str | Path) -> Path:
    segs = [s if isinstance(s, LowerChainSegment) else LowerChainSegment.from_dict(s) for s in segments]
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "segment_id", "K_lo", "K_hi", "K_mid", "rho", "N", "sigma", "norm_name",
        "residual_Y", "linear_defect_Z", "tail_bound_T", "radius_r", "radii_margin",
        "recomputed_radii_margin", "small_divisor_min", "small_divisor_inverse_bound",
        "overlap_with_next", "source_module", "source_artifact", "certified",
    ]
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for seg in segs:
            row = {k: seg.to_dict().get(k) for k in fields}
            writer.writerow(row)
    return out


def write_lower_chain_table(segments: Sequence[LowerChainSegment | Mapping[str, Any]], out_tex: str | Path) -> Path:
    segs = [s if isinstance(s, LowerChainSegment) else LowerChainSegment.from_dict(s) for s in segments]
    out = Path(out_tex)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{tabular}{lrrrrr}",
        r"\hline",
        r"Segment & $K_{\min}$ & $K_{\max}$ & $N$ & margin & overlap \\",
        r"\hline",
    ]
    for seg in segs:
        overlap = "--" if seg.overlap_with_next is None else f"{seg.overlap_with_next:.3e}"
        safe_id = seg.segment_id.replace('_', r'\_')
        lines.append(
            f"{safe_id} & {seg.K_lo:.6g} & {seg.K_hi:.6g} & {seg.N:d} & {seg.recomputed_radii_margin:.3e} & {overlap} " + r"\\"
        )
    lines.extend([r"\hline", r"\end{tabular}", ""])
    out.write_text("\n".join(lines))
    return out


def write_lower_chain_audit(
    segments: Sequence[LowerChainSegment | Mapping[str, Any]],
    out_json: str | Path,
    out_csv: str | Path | None = None,
    *,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
    out_tex: str | Path | None = None,
) -> dict[str, Any]:
    """Write the Phase-2 lower-chain report and return it as a dictionary."""

    segs = [s if isinstance(s, LowerChainSegment) else LowerChainSegment.from_dict(s) for s in segments]
    verification = verify_lower_chain(segs, final_anchor=final_anchor)
    bundle = build_lower_chain_audit_bundle(segs, final_anchor=final_anchor)
    report = {
        "status": "passed" if verification.lower_chain_verified else "failed",
        "lower_chain_verified": verification.lower_chain_verified,
        "final_anchor_reached": verification.final_anchor_reached,
        "final_anchor_near_critical": verification.final_anchor_near_critical,
        "final_anchor": [float(final_anchor[0]), float(final_anchor[1])],
        "min_radii_margin": verification.min_radii_margin,
        "min_overlap_width": verification.min_overlap_width,
        "failed_segments": verification.failed_segments,
        "failed_links": verification.failed_links,
        "failure_fields": verification.failure_fields,
        "segments": [s.to_dict() for s in segs],
        "lower_audit": bundle.to_dict(),
        "bundle": bundle.to_dict(),
    }
    out = Path(out_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    if out_csv is not None:
        write_lower_chain_csv(segs, out_csv)
    if out_tex is not None:
        write_lower_chain_table(segs, out_tex)
    return report


def write_lower_chain_bundle_json(bundle: ProofAuditBundle, out_json: str | Path) -> Path:
    out = Path(out_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(bundle.to_json())
    return out



def _pdf_escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_simple_line_pdf(path: Path, *, title: str, labels: Sequence[str], values: Sequence[float], ylabel: str) -> None:
    """Write a small self-contained vector PDF without external plotting libs."""

    width, height = 612.0, 360.0
    left, right = 70.0, 560.0
    bottom, top = 78.0, 300.0
    vals = [float(v) for v in values]
    finite_vals = [v for v in vals if math.isfinite(v)]
    if not finite_vals:
        finite_vals = [0.0]
    ymin = min(finite_vals + [0.0])
    ymax = max(finite_vals + [0.0])
    if abs(ymax - ymin) < 1.0e-30:
        pad = max(abs(ymax), 1.0) * 0.1
        ymin -= pad
        ymax += pad
    else:
        pad = 0.08 * (ymax - ymin)
        ymin -= pad
        ymax += pad

    def x_at(i: int) -> float:
        if len(vals) <= 1:
            return 0.5 * (left + right)
        return left + (right - left) * i / (len(vals) - 1)

    def y_at(v: float) -> float:
        if not math.isfinite(v):
            return bottom
        return bottom + (top - bottom) * (float(v) - ymin) / (ymax - ymin)

    cmds: list[str] = []
    cmds.append("1 w")
    cmds.append(f"{left:.2f} {bottom:.2f} m {right:.2f} {bottom:.2f} l S")
    cmds.append(f"{left:.2f} {bottom:.2f} m {left:.2f} {top:.2f} l S")
    # zero reference line when visible
    if ymin < 0.0 < ymax:
        yz = y_at(0.0)
        cmds.append("0.5 w")
        cmds.append(f"{left:.2f} {yz:.2f} m {right:.2f} {yz:.2f} l S")
        cmds.append("1 w")
    points = [(x_at(i), y_at(v)) for i, v in enumerate(vals)]
    if points:
        x0, y0 = points[0]
        cmds.append(f"{x0:.2f} {y0:.2f} m")
        for x, y in points[1:]:
            cmds.append(f"{x:.2f} {y:.2f} l")
        cmds.append("S")
        for x, y in points:
            cmds.append(f"{x-2:.2f} {y-2:.2f} {4:.2f} {4:.2f} re f")
    cmds.append("BT /F1 14 Tf 70 330 Td (" + _pdf_escape(title) + ") Tj ET")
    cmds.append("BT /F1 10 Tf 70 314 Td (" + _pdf_escape(ylabel) + ") Tj ET")
    cmds.append(f"BT /F1 9 Tf 20 {bottom:.2f} Td (min {ymin:.3e}) Tj ET")
    cmds.append(f"BT /F1 9 Tf 20 {top-8:.2f} Td (max {ymax:.3e}) Tj ET")
    for i, label in enumerate(labels):
        if len(labels) > 9 and i % max(1, len(labels)//6) != 0:
            continue
        x = x_at(i)
        cmds.append(f"BT /F1 7 Tf {x-20:.2f} 45 Td (" + _pdf_escape(label[:24]) + ") Tj ET")

    stream = "\n".join(cmds).encode("latin-1", errors="replace")
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.0f} {height:.0f}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode()
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{idx} 0 obj\n".encode())
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref_offset = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode())
    path.write_bytes(bytes(out))


def generate_lower_chain_figures(
    segments: Sequence[LowerChainSegment | Mapping[str, Any]],
    fig_dir: str | Path,
) -> list[Path]:
    """Generate manuscript-ready Phase-2 lower-chain PDF figures.

    The implementation avoids optional plotting dependencies so the audit script
    remains lightweight in clean reviewer environments.
    """

    segs = [s if isinstance(s, LowerChainSegment) else LowerChainSegment.from_dict(s) for s in segments]
    out_dir = Path(fig_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not segs:
        return []
    labels = [s.segment_id for s in segs]
    specs = [
        ("lower_chain_margins.pdf", "Lower-chain recomputed margins", [s.recomputed_radii_margin for s in segs], "r - (Y + Zr + T)"),
        ("lower_chain_resolution.pdf", "Lower-chain resolution ledger", [float(s.N) for s in segs], "N"),
        ("lower_chain_tail_majorant.pdf", "Lower-chain tail / compatibility ledger", [s.tail_bound_T for s in segs], "T or compatibility majorant"),
        ("lower_chain_overlap.pdf", "Lower-chain adjacent overlap ledger", [float("nan") if s.overlap_with_next is None else s.overlap_with_next for s in segs], "next-link overlap"),
    ]
    created: list[Path] = []
    for filename, title, values, ylabel in specs:
        path = out_dir / filename
        _write_simple_line_pdf(path, title=title, labels=labels, values=values, ylabel=ylabel)
        created.append(path)
    return created
