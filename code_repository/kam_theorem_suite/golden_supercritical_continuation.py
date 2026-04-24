from __future__ import annotations

"""Golden supercritical continuation and stability audits.

This module is the next high-value step after the one-shot golden
supercritical obstruction certificate.  It builds *several* nearby golden
upper-side certificates, then asks whether the resulting upper object is stable
under small perturbations of the chosen upper-window geometry.

The goal is deliberately narrower than a finished irrational nonexistence
result.  We only try to answer a theorem-facing question:

    Does the golden upper-side obstruction object persist under a local
    continuation of nearby upper windows?

If yes, we obtain a stronger upper-side object than a single raw certificate.
If not, the output remains honest and records drift/failure.
"""

from dataclasses import asdict, dataclass
from itertools import combinations
from typing import Any, Sequence

from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .golden_supercritical import build_golden_supercritical_obstruction_certificate
from .standard_map import HarmonicFamily


@dataclass
class GoldenSupercriticalContinuationStep:
    index: int
    crossing_center: float
    band_offset: float
    theorem_status: str
    selected_upper_source: str
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_upper_width: float | None
    earliest_hyperbolic_band_lo: float | None
    latest_hyperbolic_band_hi: float | None
    successful_crossing_count: int
    successful_band_count: int
    certificate: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenSupercriticalContinuationCertificate:
    rho: float
    family_label: str
    steps: list[GoldenSupercriticalContinuationStep]
    successful_step_count: int
    usable_upper_step_count: int
    stable_upper_source: str
    stable_upper_lo: float | None
    stable_upper_hi: float | None
    stable_upper_width: float | None
    stable_upper_support_size: int
    stable_upper_support_indices: list[int]
    stable_band_lo: float | None
    stable_band_hi: float | None
    stable_band_support_size: int
    source_histogram: dict[str, int]
    upper_center_span: float | None
    upper_width_median: float | None
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "steps": [s.to_dict() for s in self.steps],
            "successful_step_count": int(self.successful_step_count),
            "usable_upper_step_count": int(self.usable_upper_step_count),
            "stable_upper_source": str(self.stable_upper_source),
            "stable_upper_lo": self.stable_upper_lo,
            "stable_upper_hi": self.stable_upper_hi,
            "stable_upper_width": self.stable_upper_width,
            "stable_upper_support_size": int(self.stable_upper_support_size),
            "stable_upper_support_indices": [int(i) for i in self.stable_upper_support_indices],
            "stable_band_lo": self.stable_band_lo,
            "stable_band_hi": self.stable_band_hi,
            "stable_band_support_size": int(self.stable_band_support_size),
            "source_histogram": {str(k): int(v) for k, v in self.source_histogram.items()},
            "upper_center_span": self.upper_center_span,
            "upper_width_median": self.upper_width_median,
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


@dataclass
class GoldenTwoSidedContinuationBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_DEFAULT_CENTER_OFFSETS = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4)


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _histogram(values: Sequence[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[str(value)] = out.get(str(value), 0) + 1
    return out


def _median(values: Sequence[float]) -> float | None:
    xs = sorted(float(v) for v in values)
    if not xs:
        return None
    n = len(xs)
    mid = n // 2
    if n % 2 == 1:
        return float(xs[mid])
    return float(0.5 * (xs[mid - 1] + xs[mid]))


def _largest_overlapping_subset(intervals: Sequence[tuple[int, float, float]]) -> tuple[list[int], float | None, float | None]:
    if not intervals:
        return [], None, None
    best_indices: list[int] = []
    best_lo: float | None = None
    best_hi: float | None = None
    n = len(intervals)
    # brute force is fine here because these continuation schedules are intentionally small
    for r in range(n, 0, -1):
        candidates: list[tuple[list[int], float, float, float]] = []
        for subset in combinations(intervals, r):
            lo = max(x[1] for x in subset)
            hi = min(x[2] for x in subset)
            if lo <= hi:
                idxs = [int(x[0]) for x in subset]
                width = float(hi - lo)
                candidates.append((idxs, float(lo), float(hi), width))
        if candidates:
            candidates.sort(key=lambda item: (item[3], item[1], item[2]))
            best = candidates[0]
            best_indices, best_lo, best_hi = best[0], best[1], best[2]
            return best_indices, best_lo, best_hi
    return best_indices, best_lo, best_hi


def build_golden_supercritical_continuation_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    crossing_center_offsets: Sequence[float] = _DEFAULT_CENTER_OFFSETS,
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
) -> GoldenSupercriticalContinuationCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    steps: list[GoldenSupercriticalContinuationStep] = []
    for idx, offset in enumerate(tuple(float(x) for x in crossing_center_offsets)):
        center = float(crossing_center) + float(offset)
        local_band_offset = float(band_offset) + float(band_offset_slope) * float(offset)
        cert = build_golden_supercritical_obstruction_certificate(
            family=family,
            rho=rho,
            n_terms=n_terms,
            keep_last=keep_last,
            min_q=min_q,
            max_q=max_q,
            crossing_center=center,
            crossing_half_width=crossing_half_width,
            band_offset=local_band_offset,
            band_width=band_width,
            target_residue=target_residue,
            auto_localize_crossing=auto_localize_crossing,
            initial_subdivisions=initial_subdivisions,
            max_depth=max_depth,
            min_width=min_width,
            refine_upper_ladder=refine_upper_ladder,
            asymptotic_min_members=asymptotic_min_members,
        ).to_dict()
        steps.append(
            GoldenSupercriticalContinuationStep(
                index=int(idx),
                crossing_center=float(center),
                band_offset=float(local_band_offset),
                theorem_status=str(cert.get("theorem_status", "unknown")),
                selected_upper_source=str(cert.get("selected_upper_source", "no-upper-object")),
                selected_upper_lo=(None if cert.get("selected_upper_lo") is None else float(cert["selected_upper_lo"])),
                selected_upper_hi=(None if cert.get("selected_upper_hi") is None else float(cert["selected_upper_hi"])),
                selected_upper_width=(None if cert.get("selected_upper_width") is None else float(cert["selected_upper_width"])),
                earliest_hyperbolic_band_lo=(None if cert.get("earliest_hyperbolic_band_lo") is None else float(cert["earliest_hyperbolic_band_lo"])),
                latest_hyperbolic_band_hi=(None if cert.get("latest_hyperbolic_band_hi") is None else float(cert["latest_hyperbolic_band_hi"])),
                successful_crossing_count=int(cert.get("successful_crossing_count", 0)),
                successful_band_count=int(cert.get("successful_band_count", 0)),
                certificate=cert,
            )
        )

    successful_step_count = sum(1 for s in steps if s.theorem_status != "golden-supercritical-obstruction-failed")
    usable_upper = [
        (s.index, float(s.selected_upper_lo), float(s.selected_upper_hi), s.selected_upper_source)
        for s in steps
        if s.selected_upper_lo is not None and s.selected_upper_hi is not None
    ]
    band_intervals = [
        (s.index, float(s.earliest_hyperbolic_band_lo), float(s.latest_hyperbolic_band_hi))
        for s in steps
        if s.earliest_hyperbolic_band_lo is not None and s.latest_hyperbolic_band_hi is not None
    ]
    source_hist = _histogram([s.selected_upper_source for s in steps])

    stable_upper_support_indices, stable_upper_lo, stable_upper_hi = _largest_overlapping_subset(
        [(idx, lo, hi) for idx, lo, hi, _source in usable_upper]
    )
    stable_upper_width = None
    stable_upper_source = "no-stable-upper-object"
    if stable_upper_lo is not None and stable_upper_hi is not None:
        stable_upper_width = float(stable_upper_hi - stable_upper_lo)
        support_sources = [src for idx, _lo, _hi, src in usable_upper if idx in stable_upper_support_indices]
        if support_sources:
            source_counts = _histogram(support_sources)
            stable_upper_source = max(source_counts.items(), key=lambda item: (item[1], item[0]))[0]

    stable_band_support_indices, stable_band_lo, stable_band_hi = _largest_overlapping_subset(band_intervals)

    centers = [0.5 * (lo + hi) for _idx, lo, hi, _src in usable_upper]
    center_span = None if not centers else float(max(centers) - min(centers))
    width_median = _median([hi - lo for _idx, lo, hi, _src in usable_upper])

    support_size = len(stable_upper_support_indices)
    band_support_size = len(stable_band_support_indices)
    if support_size >= 3 and stable_upper_lo is not None and band_support_size >= 2:
        theorem_status = "golden-supercritical-continuation-strong"
        msg = "golden upper object persists across several nearby upper windows and the supporting hyperbolic bands also overlap"
    elif support_size >= 3 and stable_upper_lo is not None:
        theorem_status = "golden-supercritical-continuation-moderate"
        msg = "golden upper object persists across several nearby upper windows, but the supercritical band side is not yet equally stable"
    elif support_size >= 2 and stable_upper_lo is not None:
        theorem_status = "golden-supercritical-continuation-weak"
        msg = "golden upper object persists on a smaller local subset of nearby upper windows"
    elif usable_upper:
        theorem_status = "golden-supercritical-continuation-fragile"
        msg = "some nearby upper windows succeed, but the golden upper object does not yet stabilize across them"
    else:
        theorem_status = "golden-supercritical-continuation-failed"
        msg = "nearby upper windows did not produce a usable continued golden upper object"

    notes = (
        f"{msg}. This is still a local continuation audit rather than a finished irrational nonexistence theorem, "
        "but it strengthens the one-shot golden supercritical certificate by asking whether the upper object survives window perturbations."
    )
    return GoldenSupercriticalContinuationCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        steps=steps,
        successful_step_count=int(successful_step_count),
        usable_upper_step_count=int(len(usable_upper)),
        stable_upper_source=str(stable_upper_source),
        stable_upper_lo=stable_upper_lo,
        stable_upper_hi=stable_upper_hi,
        stable_upper_width=stable_upper_width,
        stable_upper_support_size=int(support_size),
        stable_upper_support_indices=[int(i) for i in stable_upper_support_indices],
        stable_band_lo=stable_band_lo,
        stable_band_hi=stable_band_hi,
        stable_band_support_size=int(band_support_size),
        source_histogram=source_hist,
        upper_center_span=center_span,
        upper_width_median=width_median,
        theorem_status=str(theorem_status),
        notes=notes,
    )


def build_golden_two_sided_continuation_bridge_certificate(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    crossing_center: float = 0.971635406,
    crossing_center_offsets: Sequence[float] = _DEFAULT_CENTER_OFFSETS,
    band_offset: float = 5.5e-2,
    band_offset_slope: float = 0.0,
    crossing_half_width: float = 2.5e-3,
    band_width: float = 3.0e-2,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
) -> GoldenTwoSidedContinuationBridgeCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    lower = continue_golden_aposteriori_certificates(
        K_values=K_values,
        family=family,
        rho=rho,
        N_values=N_values,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
    ).to_dict()
    upper = build_golden_supercritical_continuation_certificate(
        family=family,
        rho=rho,
        crossing_center=crossing_center,
        crossing_center_offsets=crossing_center_offsets,
        band_offset=band_offset,
        band_offset_slope=band_offset_slope,
        crossing_half_width=crossing_half_width,
        band_width=band_width,
        n_terms=n_terms,
        keep_last=keep_last,
        min_q=min_q,
        max_q=max_q,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        refine_upper_ladder=refine_upper_ladder,
        asymptotic_min_members=asymptotic_min_members,
    ).to_dict()
    lower_bound = lower.get("last_success_K")
    upper_lo = upper.get("stable_upper_lo")
    upper_hi = upper.get("stable_upper_hi")
    band_lo = upper.get("stable_band_lo")
    gap_to_upper = None if lower_bound is None or upper_lo is None else float(upper_lo) - float(lower_bound)
    gap_to_band = None if lower_bound is None or band_lo is None else float(band_lo) - float(lower_bound)
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        if upper.get("theorem_status") == "golden-supercritical-continuation-strong":
            status = "golden-two-sided-continuation-strong"
            msg = "golden lower-side continuation and upper-side continuation-stable obstruction produce a separated corridor"
        else:
            status = "golden-two-sided-continuation-moderate"
            msg = "golden lower-side continuation separates from a continuation-stable upper object, but the supercritical side remains local"
    elif lower_bound is not None and upper_lo is not None:
        status = "golden-two-sided-continuation-overlap"
        msg = "continued golden lower-side and upper-side objects still overlap"
    elif lower_bound is not None:
        status = "golden-two-sided-continuation-lower-only"
        msg = "only the lower continuation side closed"
    elif upper_lo is not None:
        status = "golden-two-sided-continuation-upper-only"
        msg = "only the upper continuation side closed"
    else:
        status = "golden-two-sided-continuation-incomplete"
        msg = "neither side closed enough to produce a continuation-grade golden corridor"
    relation = {
        "lower_bound_K": (None if lower_bound is None else float(lower_bound)),
        "upper_object_source": str(upper.get("stable_upper_source", "none")),
        "upper_crossing_lo": (None if upper_lo is None else float(upper_lo)),
        "upper_crossing_hi": (None if upper_hi is None else float(upper_hi)),
        "upper_crossing_width": (None if upper.get("stable_upper_width") is None else float(upper["stable_upper_width"])),
        "gap_to_upper_crossing": gap_to_upper,
        "gap_to_stable_hyperbolic_band": gap_to_band,
        "lower_success_prefix_len": int(lower.get("success_prefix_len", 0)),
        "upper_support_size": int(upper.get("stable_upper_support_size", 0)),
        "upper_band_support_size": int(upper.get("stable_band_support_size", 0)),
        "status": str(status),
    }
    notes = (
        f"{msg}. This is the continuation-strengthened golden two-sided bridge: the lower side comes from a-posteriori continuation, "
        "and the upper side from a stability audit across nearby golden supercritical windows."
    )
    return GoldenTwoSidedContinuationBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=str(status),
        notes=notes,
    )


__all__ = [
    "GoldenSupercriticalContinuationStep",
    "GoldenSupercriticalContinuationCertificate",
    "GoldenTwoSidedContinuationBridgeCertificate",
    "build_golden_supercritical_continuation_certificate",
    "build_golden_two_sided_continuation_bridge_certificate",
]
