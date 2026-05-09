from __future__ import annotations

"""Neighborhood and resolution stability audit for the golden lower side.

This module strengthens the lower golden a-posteriori bridge by asking whether
nearby continuation grids *and* nearby resolution bundles support a coherent
lower-side existence object.  The goal is not to claim a finished analytic KAM
proof, but to turn the lower side from a single continuation profile into a
small stability atlas that can be paired more honestly with the increasingly
structured golden upper-side objects.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence

from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .golden_upper_tail_stability import build_golden_upper_tail_stability_certificate
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _window_intersection(windows: Iterable[tuple[float | None, float | None]]) -> tuple[float | None, float | None]:
    los: list[float] = []
    his: list[float] = []
    for lo, hi in windows:
        if lo is None or hi is None:
            continue
        los.append(float(lo))
        his.append(float(hi))
    if not los or not his:
        return None, None
    lo = max(los)
    hi = min(his)
    if lo > hi:
        return None, None
    return lo, hi


def _largest_overlapping_subset(indices: Sequence[int], windows: Sequence[tuple[float | None, float | None]]) -> list[int]:
    best: list[int] = []
    idxs = [int(i) for i in indices]
    for start in range(len(idxs)):
        current: list[int] = []
        current_windows: list[tuple[float | None, float | None]] = []
        for j in range(start, len(idxs)):
            idx = idxs[j]
            trial = current_windows + [windows[idx]]
            lo, hi = _window_intersection(trial)
            if lo is None or hi is None:
                continue
            current.append(idx)
            current_windows = trial
        if len(current) > len(best):
            best = current
    return best


@dataclass
class GoldenLowerNeighborhoodEntry:
    grid_shift: float
    K_values: list[float]
    N_values: list[int]
    theorem_status: str
    success_prefix_len: int
    last_success_K: float | None
    first_nonstrong_K: float | None
    best_step_status: str
    observed_upper_hint: float | None
    lower_window_lo: float | None
    lower_window_hi: float | None
    source: str
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenLowerNeighborhoodStabilityCertificate:
    rho: float
    family_label: str
    base_K_values: list[float]
    shift_grid: list[float]
    resolution_sets: list[list[int]]
    successful_entry_indices: list[int]
    clustered_entry_indices: list[int]
    stable_lower_bound: float | None
    stable_observed_upper_hint: float | None
    stable_window_lo: float | None
    stable_window_hi: float | None
    stable_window_width: float | None
    distinct_resolution_signatures: list[list[int]]
    strong_or_moderate_entry_count: int
    entries: list[GoldenLowerNeighborhoodEntry]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "base_K_values": [float(x) for x in self.base_K_values],
            "shift_grid": [float(x) for x in self.shift_grid],
            "resolution_sets": [[int(y) for y in xs] for xs in self.resolution_sets],
            "successful_entry_indices": [int(x) for x in self.successful_entry_indices],
            "clustered_entry_indices": [int(x) for x in self.clustered_entry_indices],
            "stable_lower_bound": self.stable_lower_bound,
            "stable_observed_upper_hint": self.stable_observed_upper_hint,
            "stable_window_lo": self.stable_window_lo,
            "stable_window_hi": self.stable_window_hi,
            "stable_window_width": self.stable_window_width,
            "distinct_resolution_signatures": [[int(y) for y in xs] for xs in self.distinct_resolution_signatures],
            "strong_or_moderate_entry_count": int(self.strong_or_moderate_entry_count),
            "entries": [e.to_dict() for e in self.entries],
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


@dataclass
class GoldenTwoSidedNeighborhoodTailBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_golden_lower_neighborhood_stability_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    shift_grid: Sequence[float] = (-0.015, 0.0, 0.015),
    resolution_sets: Sequence[Sequence[int]] = ((64, 96, 128), (80, 112, 144)),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    min_cluster_size: int = 2,
) -> GoldenLowerNeighborhoodStabilityCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    base_grid = [float(K) for K in base_K_values]
    if not base_grid:
        raise ValueError("base_K_values must be non-empty")

    entries: list[GoldenLowerNeighborhoodEntry] = []
    for shift in shift_grid:
        shifted = [float(K) + float(shift) for K in base_grid]
        for N_values in resolution_sets:
            report = continue_golden_aposteriori_certificates(
                K_values=shifted,
                family=family,
                rho=rho,
                N_values=N_values,
                sigma_cap=sigma_cap,
                use_multiresolution=use_multiresolution,
                oversample_factor=oversample_factor,
            ).to_dict()
            step_statuses = [str(s.get("theorem_status", "unknown")) for s in report.get("steps", [])]
            best_step_status = "golden-aposteriori-bridge-failed"
            for candidate in (
                "golden-aposteriori-bridge-strong",
                "golden-aposteriori-bridge-moderate",
                "golden-aposteriori-bridge-weak",
            ):
                if candidate in step_statuses:
                    best_step_status = candidate
                    break
            last_success = report.get("last_success_K")
            first_nonstrong = report.get("first_nonstrong_K")
            observed_upper_hint = first_nonstrong if first_nonstrong is not None else shifted[-1]
            entries.append(
                GoldenLowerNeighborhoodEntry(
                    grid_shift=float(shift),
                    K_values=[float(x) for x in shifted],
                    N_values=[int(x) for x in N_values],
                    theorem_status=str(report.get("steps", [{}])[-1].get("theorem_status", report.get("source", "unknown"))) if report.get("steps") else "unknown",
                    success_prefix_len=int(report.get("success_prefix_len", 0)),
                    last_success_K=None if last_success is None else float(last_success),
                    first_nonstrong_K=None if first_nonstrong is None else float(first_nonstrong),
                    best_step_status=str(best_step_status),
                    observed_upper_hint=float(observed_upper_hint),
                    lower_window_lo=None if last_success is None else float(last_success),
                    lower_window_hi=float(observed_upper_hint),
                    source=str(report.get("source", "unknown")),
                    report=report,
                )
            )

    successful_entry_indices = [i for i, e in enumerate(entries) if e.last_success_K is not None]
    windows = [(e.lower_window_lo, e.lower_window_hi) for e in entries]
    clustered_entry_indices = _largest_overlapping_subset(successful_entry_indices, windows)
    if len(clustered_entry_indices) < int(min_cluster_size) and successful_entry_indices:
        clustered_entry_indices = sorted(successful_entry_indices, key=lambda i: entries[i].last_success_K or -1.0)[-1:]
    clustered_entries = [entries[i] for i in clustered_entry_indices]

    stable_window_lo, stable_window_hi = _window_intersection((windows[i] for i in clustered_entry_indices))
    stable_window_width = None if stable_window_lo is None or stable_window_hi is None else float(stable_window_hi - stable_window_lo)
    stable_lower_bound = None if not clustered_entries else max(float(e.last_success_K) for e in clustered_entries if e.last_success_K is not None)
    upper_hints = [float(e.observed_upper_hint) for e in clustered_entries if e.observed_upper_hint is not None]
    stable_observed_upper_hint = None if not upper_hints else min(upper_hints)
    sigs = sorted({tuple(e.N_values) for e in clustered_entries})
    distinct_resolution_signatures = [list(sig) for sig in sigs]
    strong_or_moderate_entry_count = sum(1 for e in clustered_entries if e.best_step_status in {"golden-aposteriori-bridge-strong", "golden-aposteriori-bridge-moderate"})

    if stable_lower_bound is None:
        theorem_status = "golden-lower-neighborhood-stability-failed"
        notes = "No successful golden lower-side continuation entry was produced in the audited neighborhood."
    elif len(clustered_entry_indices) >= int(min_cluster_size) and len(distinct_resolution_signatures) >= 2 and strong_or_moderate_entry_count >= 2:
        theorem_status = "golden-lower-neighborhood-stability-strong"
        notes = "Nearby lower-side continuation grids and multiple resolution bundles support a coherent golden lower object. This is a stronger theorem-facing lower-side object than a single continuation profile."
    elif len(clustered_entry_indices) >= int(min_cluster_size) and len(distinct_resolution_signatures) >= 1:
        theorem_status = "golden-lower-neighborhood-stability-moderate"
        notes = "A coherent golden lower object survives across a neighborhood of continuation grids, but the cross-resolution support is still limited."
    elif stable_lower_bound is not None:
        theorem_status = "golden-lower-neighborhood-stability-weak"
        notes = "At least one golden lower-side continuation profile succeeds, but the neighborhood/resolution support is not yet strong enough for a higher status."
    else:
        theorem_status = "golden-lower-neighborhood-stability-failed"
        notes = "The lower-side neighborhood audit did not produce a usable stable lower object."

    return GoldenLowerNeighborhoodStabilityCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        base_K_values=base_grid,
        shift_grid=[float(x) for x in shift_grid],
        resolution_sets=[[int(y) for y in xs] for xs in resolution_sets],
        successful_entry_indices=successful_entry_indices,
        clustered_entry_indices=clustered_entry_indices,
        stable_lower_bound=stable_lower_bound,
        stable_observed_upper_hint=stable_observed_upper_hint,
        stable_window_lo=stable_window_lo,
        stable_window_hi=stable_window_hi,
        stable_window_width=stable_window_width,
        distinct_resolution_signatures=distinct_resolution_signatures,
        strong_or_moderate_entry_count=int(strong_or_moderate_entry_count),
        entries=entries,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_two_sided_neighborhood_tail_bridge_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    lower_shift_grid: Sequence[float] = (-0.015, 0.0, 0.015),
    lower_resolution_sets: Sequence[Sequence[int]] = ((64, 96, 128), (80, 112, 144)),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    min_lower_cluster_size: int = 2,
    **upper_kwargs,
) -> GoldenTwoSidedNeighborhoodTailBridgeCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    lower = build_golden_lower_neighborhood_stability_certificate(
        base_K_values=base_K_values,
        family=family,
        rho=rho,
        shift_grid=lower_shift_grid,
        resolution_sets=lower_resolution_sets,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
        min_cluster_size=min_lower_cluster_size,
    ).to_dict()
    upper = build_golden_upper_tail_stability_certificate(family=family, rho=rho, **upper_kwargs).to_dict()

    lower_bound = lower.get("stable_lower_bound")
    lower_hint_hi = lower.get("stable_observed_upper_hint")
    upper_lo = upper.get("stable_upper_lo")
    upper_hi = upper.get("stable_upper_hi")
    band_lo = upper.get("stable_band_lo")
    gap_to_upper = None if lower_bound is None or upper_lo is None else float(upper_lo - float(lower_bound))
    gap_hint_to_upper = None if lower_hint_hi is None or upper_lo is None else float(upper_lo - float(lower_hint_hi))
    gap_to_band = None if lower_bound is None or band_lo is None else float(band_lo - float(lower_bound))
    relation = {
        "lower_stable_bound": None if lower_bound is None else float(lower_bound),
        "lower_observed_upper_hint": None if lower_hint_hi is None else float(lower_hint_hi),
        "lower_cluster_size": len(lower.get("clustered_entry_indices", [])),
        "lower_resolution_signature_count": len(lower.get("distinct_resolution_signatures", [])),
        "upper_crossing_lo": None if upper_lo is None else float(upper_lo),
        "upper_crossing_hi": None if upper_hi is None else float(upper_hi),
        "upper_band_lo": None if band_lo is None else float(band_lo),
        "upper_tail_qs": [int(x) for x in upper.get("stable_tail_qs", [])],
        "upper_clustered_atlas_count": len(upper.get("clustered_entry_indices", [])),
        "gap_to_upper": gap_to_upper,
        "gap_hint_to_upper": gap_hint_to_upper,
        "gap_to_band": gap_to_band,
        "upper_status": str(upper.get("theorem_status", "unknown")),
    }
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        if lower_hint_hi is not None and float(lower_hint_hi) < float(upper_lo) and str(upper.get("theorem_status")) == "golden-supercritical-tail-stability-strong":
            theorem_status = "golden-two-sided-neighborhood-tail-strong"
            notes = "A neighborhood/resolution-stable golden lower object lies cleanly below a neighborhood-stable golden upper tail object. This is a stronger two-sided bridge than pairing one lower continuation profile with one upper audit."
        else:
            theorem_status = "golden-two-sided-neighborhood-tail-partial"
            notes = "The neighborhood-stable golden lower object lies below the neighborhood-stable golden upper tail object, but the separation is not yet sharp enough for the strongest status."
    else:
        theorem_status = "golden-two-sided-neighborhood-tail-incomplete"
        notes = "The current lower neighborhood/resolution audit does not yet separate cleanly from the golden upper tail-stability object."
    return GoldenTwoSidedNeighborhoodTailBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=theorem_status,
        notes=notes,
    )



@dataclass
class GoldenLowerTheoremNeighborhoodCertificate:
    rho: float
    family_label: str
    stable_threshold_band: list[float] | None
    certified_existence_interval: list[float] | None
    stable_lower_interval: list[float] | None
    stable_certified_lower_bound: float | None
    stable_upper_hint: float | None
    lower_interval_nonempty: bool
    lower_interval_certified: bool
    tail_bridge_compatible_with_closure: bool
    continuation_compatible_with_closure: bool
    neighborhood_lower_theorem_status: str
    source_certificate: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_golden_lower_theorem_neighborhood_certificate(certificate: GoldenLowerNeighborhoodStabilityCertificate) -> GoldenLowerTheoremNeighborhoodCertificate:
    threshold_band = None
    if certificate.stable_window_lo is not None and certificate.stable_window_hi is not None and float(certificate.stable_window_hi) >= float(certificate.stable_window_lo):
        threshold_band = [float(certificate.stable_window_lo), float(certificate.stable_window_hi)]

    entries = [certificate.entries[i] for i in certificate.clustered_entry_indices if 0 <= int(i) < len(certificate.entries)]
    interval = None
    if entries and certificate.stable_lower_bound is not None:
        left = min(min(float(K) for K in entry.K_values) for entry in entries if entry.K_values)
        right = float(certificate.stable_lower_bound)
        if right >= left:
            interval = [float(left), float(right)]

    lower_width = None if interval is None else float(interval[1] - interval[0])
    lower_nonempty = bool(interval is not None and lower_width is not None and lower_width >= 0.0)
    tail_ok = bool(certificate.strong_or_moderate_entry_count >= 1)
    continuation_ok = bool(len(certificate.clustered_entry_indices) >= 1)
    lower_certified = bool(lower_nonempty and lower_width is not None and lower_width > 1.0e-12 and continuation_ok)

    if lower_certified and tail_ok and certificate.theorem_status in {'golden-lower-neighborhood-stability-strong', 'golden-lower-neighborhood-stability-moderate'}:
        status = 'golden-lower-theorem-neighborhood-strong'
    elif lower_certified or lower_nonempty:
        status = 'golden-lower-theorem-neighborhood-partial'
    else:
        status = 'golden-lower-theorem-neighborhood-failed'

    return GoldenLowerTheoremNeighborhoodCertificate(
        rho=float(certificate.rho),
        family_label=str(certificate.family_label),
        stable_threshold_band=threshold_band,
        certified_existence_interval=interval,
        stable_lower_interval=interval,
        stable_certified_lower_bound=None if certificate.stable_lower_bound is None else float(certificate.stable_lower_bound),
        stable_upper_hint=None if certificate.stable_observed_upper_hint is None else float(certificate.stable_observed_upper_hint),
        lower_interval_nonempty=bool(lower_nonempty),
        lower_interval_certified=bool(lower_certified),
        tail_bridge_compatible_with_closure=bool(tail_ok),
        continuation_compatible_with_closure=bool(continuation_ok),
        neighborhood_lower_theorem_status=str(status),
        source_certificate=certificate.to_dict(),
    )
