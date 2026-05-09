from __future__ import annotations

"""Evidence-accumulating localization atlas for the golden supercritical upper side."""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .golden_supercritical_localization import build_golden_supercritical_localization_certificate
from .standard_map import HarmonicFamily

_DEFAULT_ATLAS_CENTER_OFFSETS = (-1.2e-3, -6.0e-4, 0.0, 6.0e-4, 1.2e-3)
_DEFAULT_LOCALIZATION_OFFSETS = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4)


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


_SOURCE_PRIORITY = {
    "asymptotic-upper-ladder": 4,
    "refined-upper-ladder": 3,
    "raw-upper-ladder": 2,
    "no-stable-upper-object": 0,
    "no-upper-object": 0,
}

_STATUS_PRIORITY = {
    "golden-supercritical-localization-strong": 5,
    "golden-supercritical-localization-moderate": 4,
    "golden-supercritical-localization-weak": 3,
    "golden-supercritical-localization-fragile": 2,
    "golden-supercritical-localization-failed": 1,
}


@dataclass
class GoldenLocalizationAtlasEntry:
    atlas_index: int
    seed_center: float
    localization_status: str
    localized_upper_lo: float | None
    localized_upper_hi: float | None
    localized_upper_width: float | None
    localized_upper_source: str
    localized_support_size: int
    localized_band_lo: float | None
    localized_band_hi: float | None
    total_round_count: int
    certificate: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenLocalizationAtlasCertificate:
    rho: float
    family_label: str
    crossing_center: float
    atlas_center_offsets: list[float]
    entries: list[GoldenLocalizationAtlasEntry]
    successful_entry_count: int
    clustered_entry_count: int
    atlas_upper_lo: float | None
    atlas_upper_hi: float | None
    atlas_upper_width: float | None
    atlas_upper_source: str
    atlas_support_size: int
    atlas_center_mean: float | None
    atlas_center_spread: float | None
    atlas_band_lo: float | None
    atlas_band_hi: float | None
    best_entry_index: int | None
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "crossing_center": float(self.crossing_center),
            "atlas_center_offsets": [float(x) for x in self.atlas_center_offsets],
            "entries": [e.to_dict() for e in self.entries],
            "successful_entry_count": int(self.successful_entry_count),
            "clustered_entry_count": int(self.clustered_entry_count),
            "atlas_upper_lo": self.atlas_upper_lo,
            "atlas_upper_hi": self.atlas_upper_hi,
            "atlas_upper_width": self.atlas_upper_width,
            "atlas_upper_source": str(self.atlas_upper_source),
            "atlas_support_size": int(self.atlas_support_size),
            "atlas_center_mean": self.atlas_center_mean,
            "atlas_center_spread": self.atlas_center_spread,
            "atlas_band_lo": self.atlas_band_lo,
            "atlas_band_hi": self.atlas_band_hi,
            "best_entry_index": self.best_entry_index,
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


@dataclass
class GoldenTwoSidedLocalizationAtlasBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _entry_score(entry: GoldenLocalizationAtlasEntry) -> float:
    width = entry.localized_upper_width
    width_penalty = 0.0 if width is None else min(float(width), 1.0)
    return (
        100.0 * _STATUS_PRIORITY.get(entry.localization_status, 0)
        + 20.0 * _SOURCE_PRIORITY.get(entry.localized_upper_source, 0)
        + 8.0 * float(entry.localized_support_size)
        + 2.0 * float(entry.total_round_count)
        - 40.0 * width_penalty
    )


def _build_entry(index: int, seed_center: float, cert) -> GoldenLocalizationAtlasEntry:
    d = cert.to_dict()
    return GoldenLocalizationAtlasEntry(
        atlas_index=int(index),
        seed_center=float(seed_center),
        localization_status=str(d.get("theorem_status", "golden-supercritical-localization-failed")),
        localized_upper_lo=None if d.get("localized_upper_lo") is None else float(d["localized_upper_lo"]),
        localized_upper_hi=None if d.get("localized_upper_hi") is None else float(d["localized_upper_hi"]),
        localized_upper_width=None if d.get("localized_upper_width") is None else float(d["localized_upper_width"]),
        localized_upper_source=str(d.get("localized_upper_source", "no-upper-object")),
        localized_support_size=int(d.get("localized_support_size", 0)),
        localized_band_lo=None if d.get("localized_band_lo") is None else float(d["localized_band_lo"]),
        localized_band_hi=None if d.get("localized_band_hi") is None else float(d["localized_band_hi"]),
        total_round_count=int(d.get("total_round_count", 0)),
        certificate=d,
    )


def _cluster_entries(entries: Sequence[GoldenLocalizationAtlasEntry]) -> tuple[list[GoldenLocalizationAtlasEntry], tuple[float, float] | None]:
    usable = [e for e in entries if e.localized_upper_lo is not None and e.localized_upper_hi is not None]
    if not usable:
        return [], None
    best_cluster: list[GoldenLocalizationAtlasEntry] = []
    best_iv: tuple[float, float] | None = None
    best_key = None
    for anchor in usable:
        current = [anchor]
        lo = float(anchor.localized_upper_lo)
        hi = float(anchor.localized_upper_hi)
        others = sorted(
            [e for e in usable if e is not anchor],
            key=lambda e: (
                abs(0.5 * (float(e.localized_upper_lo) + float(e.localized_upper_hi)) - 0.5 * (lo + hi)),
                -(e.localized_support_size),
                -_STATUS_PRIORITY.get(e.localization_status, 0),
            ),
        )
        for cand in others:
            clo = max(lo, float(cand.localized_upper_lo))
            chi = min(hi, float(cand.localized_upper_hi))
            if clo <= chi:
                current.append(cand)
                lo, hi = clo, chi
        center_mean = sum(0.5 * (float(e.localized_upper_lo) + float(e.localized_upper_hi)) for e in current) / len(current)
        center_spread = max(abs(0.5 * (float(e.localized_upper_lo) + float(e.localized_upper_hi)) - center_mean) for e in current)
        quality = sum(_entry_score(e) for e in current)
        key = (len(current), quality, -float(hi - lo), -center_spread)
        if best_key is None or key > best_key:
            best_key = key
            best_cluster = list(current)
            best_iv = (float(lo), float(hi))
    return best_cluster, best_iv


def _cluster_band(entries: Sequence[GoldenLocalizationAtlasEntry]) -> tuple[float | None, float | None]:
    usable = [e for e in entries if e.localized_band_lo is not None and e.localized_band_hi is not None]
    if not usable:
        return None, None
    lo = max(float(e.localized_band_lo) for e in usable)
    hi = min(float(e.localized_band_hi) for e in usable)
    if lo <= hi:
        return float(lo), float(hi)
    best = min(usable, key=lambda e: float(e.localized_band_hi) - float(e.localized_band_lo))
    return float(best.localized_band_lo), float(best.localized_band_hi)


def build_golden_supercritical_localization_atlas_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_center_offsets: Sequence[float] = _DEFAULT_ATLAS_CENTER_OFFSETS,
    crossing_center_offsets: Sequence[float] = _DEFAULT_LOCALIZATION_OFFSETS,
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
) -> GoldenLocalizationAtlasCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    offsets = tuple(float(x) for x in atlas_center_offsets)
    loc_offsets = tuple(float(x) for x in crossing_center_offsets)
    entries: list[GoldenLocalizationAtlasEntry] = []
    best_idx = None
    best_score = float('-inf')
    for idx, off in enumerate(offsets):
        seed_center = float(crossing_center) + float(off)
        cert = build_golden_supercritical_localization_certificate(
            family=family,
            rho=rho,
            crossing_center=seed_center,
            crossing_center_offsets=loc_offsets,
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
        )
        entry = _build_entry(idx, seed_center, cert)
        entries.append(entry)
        sc = _entry_score(entry)
        if sc > best_score:
            best_score = sc
            best_idx = idx
    cluster, atlas_iv = _cluster_entries(entries)
    atlas_lo = atlas_hi = atlas_width = None
    atlas_source = 'no-upper-object'
    atlas_support = 0
    atlas_center_mean = atlas_center_spread = None
    if atlas_iv is not None:
        atlas_lo, atlas_hi = atlas_iv
        atlas_width = float(atlas_hi - atlas_lo)
        atlas_support = len(cluster)
        centers = [0.5 * (float(e.localized_upper_lo) + float(e.localized_upper_hi)) for e in cluster]
        atlas_center_mean = float(sum(centers) / len(centers))
        atlas_center_spread = float(max(abs(c - atlas_center_mean) for c in centers))
        atlas_source = max(cluster, key=_entry_score).localized_upper_source
    band_lo, band_hi = _cluster_band(cluster)
    success_count = sum(1 for e in entries if e.localized_upper_lo is not None and e.localized_upper_hi is not None)

    if atlas_iv is not None and atlas_support >= 3 and atlas_width is not None and atlas_width <= 2.5e-3:
        theorem_status = 'golden-supercritical-localization-atlas-strong'
        msg = 'nearby localization attempts support a coherent golden upper atlas across several seed centers'
    elif atlas_iv is not None and atlas_support >= 2:
        theorem_status = 'golden-supercritical-localization-atlas-moderate'
        msg = 'nearby localization attempts support a usable overlapping golden upper atlas'
    elif atlas_iv is not None:
        theorem_status = 'golden-supercritical-localization-atlas-weak'
        msg = 'only a thin single-entry golden upper atlas object survived'
    elif success_count > 0:
        theorem_status = 'golden-supercritical-localization-atlas-fragile'
        msg = 'some localization attempts survived but they did not agree on a coherent atlas object'
    else:
        theorem_status = 'golden-supercritical-localization-atlas-failed'
        msg = 'no usable golden upper localization atlas formed'
    notes = f"{msg}. The atlas layer accumulates evidence across several nearby seed centers instead of trusting a single localization attempt."
    return GoldenLocalizationAtlasCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        crossing_center=float(crossing_center),
        atlas_center_offsets=[float(x) for x in offsets],
        entries=entries,
        successful_entry_count=int(success_count),
        clustered_entry_count=int(len(cluster)),
        atlas_upper_lo=atlas_lo,
        atlas_upper_hi=atlas_hi,
        atlas_upper_width=atlas_width,
        atlas_upper_source=str(atlas_source),
        atlas_support_size=int(atlas_support),
        atlas_center_mean=atlas_center_mean,
        atlas_center_spread=atlas_center_spread,
        atlas_band_lo=band_lo,
        atlas_band_hi=band_hi,
        best_entry_index=best_idx,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_two_sided_localization_atlas_bridge_certificate(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    crossing_center: float = 0.971635406,
    atlas_center_offsets: Sequence[float] = _DEFAULT_ATLAS_CENTER_OFFSETS,
    crossing_center_offsets: Sequence[float] = _DEFAULT_LOCALIZATION_OFFSETS,
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
) -> GoldenTwoSidedLocalizationAtlasBridgeCertificate:
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
    upper = build_golden_supercritical_localization_atlas_certificate(
        family=family,
        rho=rho,
        crossing_center=crossing_center,
        atlas_center_offsets=atlas_center_offsets,
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
    lower_bound = lower.get('last_success_K')
    upper_lo = upper.get('atlas_upper_lo')
    upper_hi = upper.get('atlas_upper_hi')
    band_lo = upper.get('atlas_band_lo')
    gap_to_upper = None if lower_bound is None or upper_lo is None else float(upper_lo) - float(lower_bound)
    gap_to_band = None if lower_bound is None or band_lo is None else float(band_lo) - float(lower_bound)
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        if str(upper.get('theorem_status')) == 'golden-supercritical-localization-atlas-strong':
            status = 'golden-two-sided-localization-atlas-strong'
            msg = 'golden lower-side continuation separates from a coherent localization atlas on the upper side'
        else:
            status = 'golden-two-sided-localization-atlas-moderate'
            msg = 'golden lower-side continuation separates from a usable but not fully stable upper localization atlas'
    elif lower_bound is not None and upper_lo is not None:
        status = 'golden-two-sided-localization-atlas-overlap'
        msg = 'the golden localization atlas still overlaps the lower-side continuation'
    elif lower_bound is not None:
        status = 'golden-two-sided-localization-atlas-lower-only'
        msg = 'only the lower-side golden continuation closed'
    elif upper_lo is not None:
        status = 'golden-two-sided-localization-atlas-upper-only'
        msg = 'only the upper-side golden localization atlas closed'
    else:
        status = 'golden-two-sided-localization-atlas-incomplete'
        msg = 'neither side closed enough to produce a two-sided golden localization atlas corridor'
    relation = {
        'lower_bound_K': (None if lower_bound is None else float(lower_bound)),
        'upper_object_source': str(upper.get('atlas_upper_source', 'none')),
        'upper_crossing_lo': (None if upper_lo is None else float(upper_lo)),
        'upper_crossing_hi': (None if upper_hi is None else float(upper_hi)),
        'upper_crossing_width': (None if upper.get('atlas_upper_width') is None else float(upper['atlas_upper_width'])),
        'gap_to_upper_crossing': gap_to_upper,
        'gap_to_localized_hyperbolic_band': gap_to_band,
        'lower_success_prefix_len': int(lower.get('success_prefix_len', 0)),
        'upper_support_size': int(upper.get('atlas_support_size', 0)),
        'atlas_successful_entry_count': int(upper.get('successful_entry_count', 0)),
        'status': str(status),
    }
    notes = f"{msg}. This bridge replaces a single localized retry by an evidence-accumulating upper-side atlas across nearby seed centers."
    return GoldenTwoSidedLocalizationAtlasBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=str(status),
        notes=notes,
    )


__all__ = [
    'GoldenLocalizationAtlasEntry',
    'GoldenLocalizationAtlasCertificate',
    'GoldenTwoSidedLocalizationAtlasBridgeCertificate',
    'build_golden_supercritical_localization_atlas_certificate',
    'build_golden_two_sided_localization_atlas_bridge_certificate',
]
