from __future__ import annotations

"""Multi-approximant obstruction atlas builders.

This module is the next layer after local crossing certificates and
supercritical-band reports. It does **not** claim a global irrational theorem.
Instead, it organizes several rational approximants into one structured atlas so
that notebooks and scripts can inspect:

- which approximants admit a certified local crossing window,
- which approximants admit a later hyperbolic supercritical band,
- how those windows line up across the approximant ladder, and
- what the current bottlenecks are before any challenger-pruning theorem can be
  stated.

The intended use is a theorem-facing workflow in which one builds a coherent
atlas for a family (typically the standard map), then feeds the resulting upper
and lower windows into an arithmetic pruning layer.
"""

from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any, Iterable, Sequence

from .crossing_certificate import certify_unique_crossing_window
from .supercritical_bands import build_crossing_to_hyperbolic_band_bridge
from .standard_map import HarmonicFamily


@dataclass(frozen=True)
class ApproximantWindowSpec:
    """Input specification for one rational approximant in an obstruction atlas."""

    p: int
    q: int
    crossing_K_lo: float
    crossing_K_hi: float
    band_search_lo: float
    band_search_hi: float
    label: str | None = None
    eta_reference: float | None = None

    def normalized_label(self) -> str:
        return self.label or f"{self.p}/{self.q}"


@dataclass
class ApproximantAtlasEntry:
    p: int
    q: int
    label: str
    rho: float
    eta_reference: float | None
    crossing_window_input_lo: float
    crossing_window_input_hi: float
    crossing_certificate: dict[str, Any]
    crossing_root_window_lo: float | None
    crossing_root_window_hi: float | None
    crossing_root_window_width: float | None
    band_report: dict[str, Any]
    hyperbolic_band_lo: float | None
    hyperbolic_band_hi: float | None
    hyperbolic_band_width: float
    bridge_report: dict[str, Any]
    gap_from_crossing_to_band: float | None
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiApproximantObstructionAtlas:
    family_label: str
    approximants: list[dict[str, Any]]
    min_crossing_root_lo: float | None
    max_crossing_root_hi: float | None
    crossing_envelope_width: float | None
    min_band_lo: float | None
    max_band_hi: float | None
    band_envelope_width: float | None
    atlas_status: str
    fully_certified_count: int
    crossing_only_count: int
    failed_count: int
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AtlasComparisonSummary:
    reference_label: str
    reference_crossing_lo: float | None
    reference_crossing_hi: float | None
    dominated_labels: list[str]
    overlapping_labels: list[str]
    uncertified_labels: list[str]
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _fraction_rho(p: int, q: int) -> float:
    return float(Fraction(int(p), int(q)))


def _entry_status(crossing: dict[str, Any], band: dict[str, Any], bridge: dict[str, Any]) -> tuple[str, str]:
    tier = str(crossing.get("certification_tier", "incomplete"))
    band_lo = band.get("longest_band_lo")
    band_hi = band.get("longest_band_hi")
    if tier in {"interval_newton", "monotone_window"} and band_lo is not None and band_hi is not None:
        return "crossing-plus-band", "local crossing plus sustained hyperbolic band"
    if tier in {"interval_newton", "monotone_window"}:
        return "crossing-only", "crossing certified but no sustained hyperbolic band found on the search window"
    if bridge.get("status") == "incomplete":
        return "incomplete", "crossing certificate did not close; obstruction atlas entry remains exploratory"
    return "partial", "entry has some certified pieces but not the full crossing-to-band bridge"


def build_approximant_atlas_entry(
    spec: ApproximantWindowSpec,
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
) -> ApproximantAtlasEntry:
    """Build one atlas entry from a crossing window and a later band search window."""
    family = family or HarmonicFamily()
    crossing = certify_unique_crossing_window(
        p=spec.p,
        q=spec.q,
        K_lo=spec.crossing_K_lo,
        K_hi=spec.crossing_K_hi,
        family=family,
        target_residue=target_residue,
        auto_localize=auto_localize_crossing,
    ).to_dict()
    bridge = build_crossing_to_hyperbolic_band_bridge(
        p=spec.p,
        q=spec.q,
        crossing_K_lo=spec.crossing_K_lo,
        crossing_K_hi=spec.crossing_K_hi,
        band_search_lo=spec.band_search_lo,
        band_search_hi=spec.band_search_hi,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()
    band = dict(bridge.get("band_report", {}))
    root_lo = crossing.get("certified_root_window_lo")
    root_hi = crossing.get("certified_root_window_hi")
    root_w = None if root_lo is None or root_hi is None else float(root_hi) - float(root_lo)
    band_lo = band.get("longest_band_lo")
    band_hi = band.get("longest_band_hi")
    band_w = 0.0 if band_lo is None or band_hi is None else float(band_hi) - float(band_lo)
    status, notes = _entry_status(crossing, band, bridge)
    return ApproximantAtlasEntry(
        p=int(spec.p),
        q=int(spec.q),
        label=spec.normalized_label(),
        rho=_fraction_rho(spec.p, spec.q),
        eta_reference=None if spec.eta_reference is None else float(spec.eta_reference),
        crossing_window_input_lo=float(spec.crossing_K_lo),
        crossing_window_input_hi=float(spec.crossing_K_hi),
        crossing_certificate=crossing,
        crossing_root_window_lo=None if root_lo is None else float(root_lo),
        crossing_root_window_hi=None if root_hi is None else float(root_hi),
        crossing_root_window_width=root_w,
        band_report=band,
        hyperbolic_band_lo=None if band_lo is None else float(band_lo),
        hyperbolic_band_hi=None if band_hi is None else float(band_hi),
        hyperbolic_band_width=float(band_w),
        bridge_report=bridge,
        gap_from_crossing_to_band=bridge.get("first_supercritical_gap"),
        status=status,
        notes=notes,
    )


def build_multi_approximant_obstruction_atlas(
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
) -> MultiApproximantObstructionAtlas:
    """Build a coherent obstruction atlas over several rational approximants."""
    family = family or HarmonicFamily()
    entries = [
        build_approximant_atlas_entry(
            spec,
            family=family,
            target_residue=target_residue,
            auto_localize_crossing=auto_localize_crossing,
            initial_subdivisions=initial_subdivisions,
            max_depth=max_depth,
            min_width=min_width,
        ).to_dict()
        for spec in specs
    ]
    crossing_los = [float(e["crossing_root_window_lo"]) for e in entries if e.get("crossing_root_window_lo") is not None]
    crossing_his = [float(e["crossing_root_window_hi"]) for e in entries if e.get("crossing_root_window_hi") is not None]
    band_los = [float(e["hyperbolic_band_lo"]) for e in entries if e.get("hyperbolic_band_lo") is not None]
    band_his = [float(e["hyperbolic_band_hi"]) for e in entries if e.get("hyperbolic_band_hi") is not None]
    min_crossing_lo = min(crossing_los) if crossing_los else None
    max_crossing_hi = max(crossing_his) if crossing_his else None
    crossing_width = None if min_crossing_lo is None or max_crossing_hi is None else float(max_crossing_hi - min_crossing_lo)
    min_band_lo = min(band_los) if band_los else None
    max_band_hi = max(band_his) if band_his else None
    band_width = None if min_band_lo is None or max_band_hi is None else float(max_band_hi - min_band_lo)

    fully = sum(e["status"] == "crossing-plus-band" for e in entries)
    crossing_only = sum(e["status"] == "crossing-only" for e in entries)
    failed = sum(e["status"] in {"partial", "incomplete"} for e in entries)
    if fully == len(entries) and entries:
        atlas_status = "fully-certified-local-atlas"
    elif fully > 0 or crossing_only > 0:
        atlas_status = "partial-certified-local-atlas"
    else:
        atlas_status = "exploratory-atlas"

    notes = (
        "This atlas is rational and local: it summarizes certified crossing windows and later hyperbolic bands "
        "across several approximants, but it is not yet a universal irrational obstruction theorem."
    )
    return MultiApproximantObstructionAtlas(
        family_label=type(family).__name__,
        approximants=entries,
        min_crossing_root_lo=min_crossing_lo,
        max_crossing_root_hi=max_crossing_hi,
        crossing_envelope_width=crossing_width,
        min_band_lo=min_band_lo,
        max_band_hi=max_band_hi,
        band_envelope_width=band_width,
        atlas_status=atlas_status,
        fully_certified_count=int(fully),
        crossing_only_count=int(crossing_only),
        failed_count=int(failed),
        notes=notes,
    )


def compare_atlas_to_reference(
    atlas: MultiApproximantObstructionAtlas | dict[str, Any],
    *,
    reference_label: str,
    reference_crossing_lo: float,
    reference_crossing_hi: float,
) -> AtlasComparisonSummary:
    """Compare atlas crossing windows against a reference threshold window.

    The intended use is golden-vs-challenger comparison after a local atlas has
    been built. Any approximant whose certified crossing upper endpoint lies
    below the reference lower endpoint is marked as currently dominated.
    """
    d = atlas.to_dict() if hasattr(atlas, "to_dict") else dict(atlas)
    dominated: list[str] = []
    overlapping: list[str] = []
    uncertified: list[str] = []
    for entry in d.get("approximants", []):
        label = str(entry.get("label", f"{entry.get('p')}/{entry.get('q')}"))
        lo = entry.get("crossing_root_window_lo")
        hi = entry.get("crossing_root_window_hi")
        if lo is None or hi is None:
            uncertified.append(label)
            continue
        if float(hi) < float(reference_crossing_lo):
            dominated.append(label)
        elif float(lo) > float(reference_crossing_hi):
            overlapping.append(label)
        else:
            overlapping.append(label)
    status = "reference-dominates-certified-subset" if dominated else "no-dominated-certified-entries"
    notes = (
        "Entries in 'dominated_labels' are those whose certified crossing upper endpoint lies below the reference lower endpoint. "
        "Uncertified entries remain outside the current pruning layer."
    )
    return AtlasComparisonSummary(
        reference_label=str(reference_label),
        reference_crossing_lo=float(reference_crossing_lo),
        reference_crossing_hi=float(reference_crossing_hi),
        dominated_labels=dominated,
        overlapping_labels=overlapping,
        uncertified_labels=uncertified,
        status=status,
        notes=notes,
    )


__all__ = [
    "ApproximantWindowSpec",
    "ApproximantAtlasEntry",
    "MultiApproximantObstructionAtlas",
    "AtlasComparisonSummary",
    "build_approximant_atlas_entry",
    "build_multi_approximant_obstruction_atlas",
    "compare_atlas_to_reference",
]
