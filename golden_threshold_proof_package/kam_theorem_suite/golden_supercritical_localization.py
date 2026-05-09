from __future__ import annotations

"""Adaptive localization for the golden supercritical obstruction bridge.

This module tries to rescue fragile or failed golden supercritical continuation
certificates by *recentering* around the most promising surviving upper object
and rerunning a narrower continuation audit there.

The aim is theorem-facing but honest: if the golden upper-side continuation is
unstable on a wide initial neighborhood, we ask whether it becomes coherent on a
smaller locally chosen neighborhood.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .golden_supercritical_continuation import (
    GoldenSupercriticalContinuationCertificate,
    build_golden_supercritical_continuation_certificate,
)
from .standard_map import HarmonicFamily


_DEFAULT_CENTER_OFFSETS = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4)


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


@dataclass
class GoldenSupercriticalLocalizationRound:
    round_index: int
    crossing_center: float
    crossing_half_width: float
    crossing_center_offsets: list[float]
    continuation_status: str
    stable_upper_lo: float | None
    stable_upper_hi: float | None
    stable_upper_width: float | None
    stable_upper_support_size: int
    stable_band_lo: float | None
    stable_band_hi: float | None
    localized_target_center: float | None
    center_shift: float | None
    round_score: float
    certificate: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenSupercriticalLocalizationCertificate:
    rho: float
    family_label: str
    rounds: list[GoldenSupercriticalLocalizationRound]
    best_round_index: int | None
    best_round_status: str
    localized_upper_lo: float | None
    localized_upper_hi: float | None
    localized_upper_width: float | None
    localized_upper_source: str
    localized_support_size: int
    localized_band_lo: float | None
    localized_band_hi: float | None
    final_crossing_center: float
    final_crossing_half_width: float
    total_center_shift: float | None
    total_round_count: int
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "rounds": [r.to_dict() for r in self.rounds],
            "best_round_index": self.best_round_index,
            "best_round_status": str(self.best_round_status),
            "localized_upper_lo": self.localized_upper_lo,
            "localized_upper_hi": self.localized_upper_hi,
            "localized_upper_width": self.localized_upper_width,
            "localized_upper_source": str(self.localized_upper_source),
            "localized_support_size": int(self.localized_support_size),
            "localized_band_lo": self.localized_band_lo,
            "localized_band_hi": self.localized_band_hi,
            "final_crossing_center": float(self.final_crossing_center),
            "final_crossing_half_width": float(self.final_crossing_half_width),
            "total_center_shift": self.total_center_shift,
            "total_round_count": int(self.total_round_count),
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


@dataclass
class GoldenTwoSidedLocalizationBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SOURCE_PRIORITY = {
    "asymptotic-upper-ladder": 4,
    "refined-upper-ladder": 3,
    "raw-upper-ladder": 2,
    "no-stable-upper-object": 0,
    "no-upper-object": 0,
}

_STATUS_PRIORITY = {
    "golden-supercritical-continuation-strong": 5,
    "golden-supercritical-continuation-moderate": 4,
    "golden-supercritical-continuation-weak": 3,
    "golden-supercritical-continuation-fragile": 2,
    "golden-supercritical-continuation-failed": 1,
}


def _round_score(cert: dict[str, Any]) -> float:
    source = str(cert.get("stable_upper_source", "no-upper-object"))
    status = str(cert.get("theorem_status", "golden-supercritical-continuation-failed"))
    support = int(cert.get("stable_upper_support_size", 0))
    band_support = int(cert.get("stable_band_support_size", 0))
    width = cert.get("stable_upper_width")
    width_penalty = 0.0 if width is None else min(float(width), 1.0)
    return (
        100.0 * _STATUS_PRIORITY.get(status, 0)
        + 25.0 * _SOURCE_PRIORITY.get(source, 0)
        + 10.0 * float(support)
        + 3.0 * float(band_support)
        - 40.0 * width_penalty
    )


def _pick_target_center(cert: dict[str, Any]) -> float | None:
    lo = cert.get("stable_upper_lo")
    hi = cert.get("stable_upper_hi")
    if lo is not None and hi is not None:
        return float(0.5 * (float(lo) + float(hi)))
    best_step = None
    best_key = None
    for step in cert.get("steps", []):
        slo = step.get("selected_upper_lo")
        shi = step.get("selected_upper_hi")
        if slo is None or shi is None:
            continue
        width = float(shi) - float(slo)
        key = (
            _SOURCE_PRIORITY.get(str(step.get("selected_upper_source", "no-upper-object")), 0),
            int(step.get("successful_crossing_count", 0)),
            int(step.get("successful_band_count", 0)),
            -width,
        )
        if best_key is None or key > best_key:
            best_key = key
            best_step = step
    if best_step is not None:
        return float(0.5 * (float(best_step["selected_upper_lo"]) + float(best_step["selected_upper_hi"])))
    return None


def _build_round(
    *,
    family: HarmonicFamily,
    rho: float,
    crossing_center: float,
    crossing_center_offsets: Sequence[float],
    band_offset: float,
    band_offset_slope: float,
    crossing_half_width: float,
    band_width: float,
    n_terms: int,
    keep_last: int,
    min_q: int,
    max_q: int | None,
    target_residue: float,
    auto_localize_crossing: bool,
    initial_subdivisions: int,
    max_depth: int,
    min_width: float,
    refine_upper_ladder: bool,
    asymptotic_min_members: int,
) -> GoldenSupercriticalContinuationCertificate:
    return build_golden_supercritical_continuation_certificate(
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
    )


def build_golden_supercritical_localization_certificate(
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
    max_rounds: int = 3,
    center_shrink: float = 0.5,
    width_shrink: float = 0.7,
    min_center_spacing: float = 5.0e-5,
) -> GoldenSupercriticalLocalizationCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    offsets = tuple(float(x) for x in crossing_center_offsets)
    cur_center = float(crossing_center)
    cur_half_width = float(crossing_half_width)
    rounds: list[GoldenSupercriticalLocalizationRound] = []
    best_cert: dict[str, Any] | None = None
    best_round_index: int | None = None
    best_score = float("-inf")
    initial_center = float(cur_center)

    for ridx in range(int(max_rounds)):
        cert = _build_round(
            family=family,
            rho=rho,
            crossing_center=cur_center,
            crossing_center_offsets=offsets,
            band_offset=band_offset,
            band_offset_slope=band_offset_slope,
            crossing_half_width=cur_half_width,
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
        score = _round_score(cert)
        target_center = _pick_target_center(cert)
        center_shift = None if target_center is None else float(target_center - cur_center)
        rounds.append(
            GoldenSupercriticalLocalizationRound(
                round_index=int(ridx),
                crossing_center=float(cur_center),
                crossing_half_width=float(cur_half_width),
                crossing_center_offsets=[float(x) for x in offsets],
                continuation_status=str(cert.get("theorem_status", "unknown")),
                stable_upper_lo=(None if cert.get("stable_upper_lo") is None else float(cert["stable_upper_lo"])),
                stable_upper_hi=(None if cert.get("stable_upper_hi") is None else float(cert["stable_upper_hi"])),
                stable_upper_width=(None if cert.get("stable_upper_width") is None else float(cert["stable_upper_width"])),
                stable_upper_support_size=int(cert.get("stable_upper_support_size", 0)),
                stable_band_lo=(None if cert.get("stable_band_lo") is None else float(cert["stable_band_lo"])),
                stable_band_hi=(None if cert.get("stable_band_hi") is None else float(cert["stable_band_hi"])),
                localized_target_center=target_center,
                center_shift=center_shift,
                round_score=float(score),
                certificate=cert,
            )
        )
        if score > best_score:
            best_score = float(score)
            best_cert = cert
            best_round_index = int(ridx)

        status = str(cert.get("theorem_status", "failed"))
        if status in {"golden-supercritical-continuation-strong", "golden-supercritical-continuation-moderate"}:
            break
        if target_center is None:
            break
        if abs(float(target_center) - cur_center) < float(min_center_spacing):
            break
        cur_center = float(target_center)
        cur_half_width = max(float(min_width), float(cur_half_width) * float(width_shrink))
        offsets = tuple(float(x) * float(center_shrink) for x in offsets)

    best_cert = best_cert or {}
    loc_lo = None if best_cert.get("stable_upper_lo") is None else float(best_cert["stable_upper_lo"])
    loc_hi = None if best_cert.get("stable_upper_hi") is None else float(best_cert["stable_upper_hi"])
    loc_w = None if best_cert.get("stable_upper_width") is None else float(best_cert["stable_upper_width"])
    support = int(best_cert.get("stable_upper_support_size", 0))
    band_lo = None if best_cert.get("stable_band_lo") is None else float(best_cert["stable_band_lo"])
    band_hi = None if best_cert.get("stable_band_hi") is None else float(best_cert["stable_band_hi"])
    best_status = str(best_cert.get("theorem_status", "golden-supercritical-continuation-failed"))
    source = str(best_cert.get("stable_upper_source", "no-stable-upper-object"))

    if best_status == "golden-supercritical-continuation-strong":
        theorem_status = "golden-supercritical-localization-strong"
        msg = "adaptive recentering found a stable local golden upper object with strong continuation support"
    elif best_status == "golden-supercritical-continuation-moderate":
        theorem_status = "golden-supercritical-localization-moderate"
        msg = "adaptive recentering found a usable local golden upper object with moderate continuation support"
    elif loc_lo is not None and support >= 2:
        theorem_status = "golden-supercritical-localization-weak"
        msg = "adaptive recentering localized a smaller coherent golden upper object"
    elif loc_lo is not None:
        theorem_status = "golden-supercritical-localization-fragile"
        msg = "adaptive recentering found a local upper object, but it remains fragile"
    else:
        theorem_status = "golden-supercritical-localization-failed"
        msg = "adaptive recentering did not isolate a usable local golden upper object"

    notes = (
        f"{msg}. The localization layer narrows the upper-window geometry around the most promising surviving upper object, "
        "so the result is more focused than a one-shot or fixed-window continuation audit."
    )
    total_center_shift = None if not rounds else float(rounds[-1].crossing_center - initial_center)
    return GoldenSupercriticalLocalizationCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        rounds=rounds,
        best_round_index=best_round_index,
        best_round_status=best_status,
        localized_upper_lo=loc_lo,
        localized_upper_hi=loc_hi,
        localized_upper_width=loc_w,
        localized_upper_source=source,
        localized_support_size=support,
        localized_band_lo=band_lo,
        localized_band_hi=band_hi,
        final_crossing_center=float(rounds[-1].crossing_center if rounds else crossing_center),
        final_crossing_half_width=float(rounds[-1].crossing_half_width if rounds else crossing_half_width),
        total_center_shift=total_center_shift,
        total_round_count=int(len(rounds)),
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_two_sided_localization_bridge_certificate(
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
    max_rounds: int = 3,
    center_shrink: float = 0.5,
    width_shrink: float = 0.7,
    min_center_spacing: float = 5.0e-5,
) -> GoldenTwoSidedLocalizationBridgeCertificate:
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
    upper = build_golden_supercritical_localization_certificate(
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
        max_rounds=max_rounds,
        center_shrink=center_shrink,
        width_shrink=width_shrink,
        min_center_spacing=min_center_spacing,
    ).to_dict()
    lower_bound = lower.get("last_success_K")
    upper_lo = upper.get("localized_upper_lo")
    upper_hi = upper.get("localized_upper_hi")
    band_lo = upper.get("localized_band_lo")
    gap_to_upper = None if lower_bound is None or upper_lo is None else float(upper_lo) - float(lower_bound)
    gap_to_band = None if lower_bound is None or band_lo is None else float(band_lo) - float(lower_bound)
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        if str(upper.get("theorem_status")) == "golden-supercritical-localization-strong":
            status = "golden-two-sided-localization-strong"
            msg = "golden lower-side continuation separates from a localization-stable upper object"
        else:
            status = "golden-two-sided-localization-moderate"
            msg = "golden lower-side continuation separates from a localized upper object, but the upper side remains locally fragile"
    elif lower_bound is not None and upper_lo is not None:
        status = "golden-two-sided-localization-overlap"
        msg = "localized golden upper object still overlaps the lower-side continuation"
    elif lower_bound is not None:
        status = "golden-two-sided-localization-lower-only"
        msg = "only the lower-side golden continuation closed"
    elif upper_lo is not None:
        status = "golden-two-sided-localization-upper-only"
        msg = "only the localized upper-side golden object closed"
    else:
        status = "golden-two-sided-localization-incomplete"
        msg = "neither side closed enough to produce a localized golden corridor"
    relation = {
        "lower_bound_K": (None if lower_bound is None else float(lower_bound)),
        "upper_object_source": str(upper.get("localized_upper_source", "none")),
        "upper_crossing_lo": (None if upper_lo is None else float(upper_lo)),
        "upper_crossing_hi": (None if upper_hi is None else float(upper_hi)),
        "upper_crossing_width": (None if upper.get("localized_upper_width") is None else float(upper["localized_upper_width"])),
        "gap_to_upper_crossing": gap_to_upper,
        "gap_to_localized_hyperbolic_band": gap_to_band,
        "lower_success_prefix_len": int(lower.get("success_prefix_len", 0)),
        "upper_support_size": int(upper.get("localized_support_size", 0)),
        "upper_round_count": int(upper.get("total_round_count", 0)),
        "status": str(status),
    }
    notes = (
        f"{msg}. This bridge replaces the fixed-window upper continuation side by an adaptively localized golden upper object."
    )
    return GoldenTwoSidedLocalizationBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=str(status),
        notes=notes,
    )


__all__ = [
    "GoldenSupercriticalLocalizationRound",
    "GoldenSupercriticalLocalizationCertificate",
    "GoldenTwoSidedLocalizationBridgeCertificate",
    "build_golden_supercritical_localization_certificate",
    "build_golden_two_sided_localization_bridge_certificate",
]
