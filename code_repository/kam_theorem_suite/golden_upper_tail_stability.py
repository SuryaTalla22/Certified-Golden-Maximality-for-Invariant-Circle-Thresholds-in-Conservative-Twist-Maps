from __future__ import annotations

"""Tail-stability audit across neighboring golden localization atlases.

This module upgrades the denominator-aware golden upper support audit by asking
whether the same high-denominator support tail persists across a *small
neighborhood of atlas constructions*, not just within one chosen atlas.

The implementation remains honest. It does not claim a finished irrational
nonexistence theorem; it organizes upper-side evidence across neighboring atlas
choices and reports whether the high-q support tail is stable, fragile, or
absent.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .golden_upper_support_audit import build_golden_upper_support_audit_certificate
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


def _intersection_sorted(seq_sets: Sequence[Sequence[int]]) -> list[int]:
    if not seq_sets:
        return []
    common = set(int(x) for x in seq_sets[0])
    for s in seq_sets[1:]:
        common &= {int(x) for x in s}
    return sorted(common)


def _union_sorted(seq_sets: Sequence[Sequence[int]]) -> list[int]:
    out: set[int] = set()
    for s in seq_sets:
        out.update(int(x) for x in s)
    return sorted(out)


def _is_suffix(candidate: Sequence[int], generated: Sequence[int]) -> bool:
    cand = [int(x) for x in candidate]
    gen = [int(x) for x in generated]
    if not cand or not gen or len(cand) > len(gen):
        return False
    for i in range(len(gen)):
        if gen[i:] == cand:
            return True
    return False


@dataclass
class GoldenUpperTailStabilityEntry:
    atlas_shift: float
    crossing_center: float
    theorem_status: str
    audited_upper_lo: float | None
    audited_upper_hi: float | None
    audited_upper_width: float | None
    audited_upper_source: str
    robust_qs: list[int]
    robust_tail_qs: list[int]
    robust_tail_start_q: int | None
    audited_support_size: int
    audited_center_support_size: int
    tail_is_suffix_of_generated: bool
    witness_count: int
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenUpperTailStabilityCertificate:
    rho: float
    family_label: str
    base_crossing_center: float
    atlas_shift_grid: list[float]
    successful_entry_indices: list[int]
    clustered_entry_indices: list[int]
    stable_tail_qs: list[int]
    stable_tail_start_q: int | None
    stable_tail_support_count: int
    stable_tail_support_fraction: float | None
    stable_tail_is_suffix_of_generated_union: bool
    stable_q_union: list[int]
    stable_q_intersection: list[int]
    stable_upper_lo: float | None
    stable_upper_hi: float | None
    stable_upper_width: float | None
    stable_band_lo: float | None
    stable_band_hi: float | None
    stable_upper_source: str
    entries: list[GoldenUpperTailStabilityEntry]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "base_crossing_center": float(self.base_crossing_center),
            "atlas_shift_grid": [float(x) for x in self.atlas_shift_grid],
            "successful_entry_indices": [int(x) for x in self.successful_entry_indices],
            "clustered_entry_indices": [int(x) for x in self.clustered_entry_indices],
            "stable_tail_qs": [int(x) for x in self.stable_tail_qs],
            "stable_tail_start_q": self.stable_tail_start_q,
            "stable_tail_support_count": int(self.stable_tail_support_count),
            "stable_tail_support_fraction": self.stable_tail_support_fraction,
            "stable_tail_is_suffix_of_generated_union": bool(self.stable_tail_is_suffix_of_generated_union),
            "stable_q_union": [int(x) for x in self.stable_q_union],
            "stable_q_intersection": [int(x) for x in self.stable_q_intersection],
            "stable_upper_lo": self.stable_upper_lo,
            "stable_upper_hi": self.stable_upper_hi,
            "stable_upper_width": self.stable_upper_width,
            "stable_band_lo": self.stable_band_lo,
            "stable_band_hi": self.stable_band_hi,
            "stable_upper_source": str(self.stable_upper_source),
            "entries": [e.to_dict() for e in self.entries],
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


@dataclass
class GoldenTwoSidedTailStabilityBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _normalize_theorem_iv_bridge_payload(payload: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    selected = payload.get("selected_bridge")
    if isinstance(selected, Mapping):
        return selected
    return payload


def _select_theorem_iv_upper_bridge(theorem_iv_certificate: Mapping[str, Any]) -> Mapping[str, Any]:
    nonexistence_front = theorem_iv_certificate.get("nonexistence_front")
    if not isinstance(nonexistence_front, Mapping):
        raise ValueError("Theorem-IV certificate does not expose a nonexistence_front payload.")

    search_order = (
        nonexistence_front.get("upper_bridge_profile"),
        nonexistence_front.get("upper_tail_aware_neighborhood"),
        nonexistence_front.get("upper_support_core_neighborhood"),
        nonexistence_front.get("upper_bridge_promotion"),
        nonexistence_front.get("upper_bridge"),
    )
    for candidate in search_order:
        bridge = _normalize_theorem_iv_bridge_payload(candidate)
        if isinstance(bridge, Mapping) and bridge.get("certified_upper_lo") is not None and bridge.get("certified_upper_hi") is not None:
            return bridge
    raise ValueError("Theorem-IV certificate does not expose a reusable upper bridge.")


def _coerce_theorem_iv_tail_stability_entries(
    theorem_iv_certificate: Mapping[str, Any],
    stable_upper_source: str,
) -> list[GoldenUpperTailStabilityEntry]:
    nonexistence_front = theorem_iv_certificate.get("nonexistence_front")
    if not isinstance(nonexistence_front, Mapping):
        return []
    tail_stability = nonexistence_front.get("upper_tail_stability")
    if not isinstance(tail_stability, Mapping):
        return []
    entries_payload = tail_stability.get("entries")
    if not isinstance(entries_payload, list):
        return []

    entries: list[GoldenUpperTailStabilityEntry] = []
    for idx, entry in enumerate(entries_payload):
        if not isinstance(entry, Mapping):
            continue
        robust_qs = entry.get("generated_qs") or entry.get("witness_qs") or []
        robust_tail_qs = entry.get("stable_tail_qs") or []
        entries.append(
            GoldenUpperTailStabilityEntry(
                atlas_shift=float(entry.get("atlas_shift", 0.0)),
                crossing_center=float(entry.get("crossing_center", 0.0)),
                theorem_status=str(entry.get("theorem_status", tail_stability.get("theorem_status", "unknown"))),
                audited_upper_lo=_coerce_float(entry.get("selected_upper_lo", tail_stability.get("stable_upper_lo"))),
                audited_upper_hi=_coerce_float(entry.get("selected_upper_hi", tail_stability.get("stable_upper_hi"))),
                audited_upper_width=_coerce_float(entry.get("selected_upper_width", tail_stability.get("stable_upper_width"))),
                audited_upper_source=stable_upper_source,
                robust_qs=[int(x) for x in robust_qs],
                robust_tail_qs=[int(x) for x in robust_tail_qs],
                robust_tail_start_q=(None if entry.get("stable_tail_start_q") is None else int(entry.get("stable_tail_start_q"))),
                audited_support_size=len([int(x) for x in robust_qs]),
                audited_center_support_size=len([int(x) for x in (entry.get("witness_qs") or [])]),
                tail_is_suffix_of_generated=bool(entry.get("tail_is_suffix_of_generated", tail_stability.get("stable_tail_is_suffix_of_generated_union", False))),
                witness_count=int(entry.get("fully_certified_count", len(entry.get("witness_qs") or []))),
                report={"source": "theorem-iv-final-object", "index": int(idx), "payload": dict(entry)},
            )
        )
    return entries


def build_golden_upper_tail_stability_certificate_from_theorem_iv(
    theorem_iv_certificate: Mapping[str, Any],
) -> GoldenUpperTailStabilityCertificate:
    bridge = _select_theorem_iv_upper_bridge(theorem_iv_certificate)
    nonexistence_front = theorem_iv_certificate.get("nonexistence_front")
    if not isinstance(nonexistence_front, Mapping):
        raise ValueError("Theorem-IV certificate does not expose a nonexistence_front payload.")
    tail_stability = nonexistence_front.get("upper_tail_stability")
    if not isinstance(tail_stability, Mapping):
        tail_stability = {}

    stable_upper_source = "theorem-iv-final-object"
    entries = _coerce_theorem_iv_tail_stability_entries(theorem_iv_certificate, stable_upper_source)
    successful_entry_indices = [idx for idx, entry in enumerate(entries) if entry.audited_upper_lo is not None and entry.audited_upper_hi is not None]
    clustered_entry_indices = [int(x) for x in tail_stability.get("clustered_entry_indices", successful_entry_indices)]
    if not clustered_entry_indices and successful_entry_indices:
        clustered_entry_indices = list(successful_entry_indices)

    stable_tail_qs = [int(x) for x in bridge.get("certified_tail_qs", tail_stability.get("stable_tail_qs", []))]
    stable_tail_start_q = bridge.get("certified_tail_start_q", tail_stability.get("stable_tail_start_q"))
    if stable_tail_start_q is not None:
        stable_tail_start_q = int(stable_tail_start_q)
    stable_tail_support_count = int(tail_stability.get("stable_tail_support_count", bridge.get("supporting_entry_count", 0)))
    stable_tail_support_fraction = tail_stability.get("stable_tail_support_fraction", bridge.get("support_fraction_floor"))
    if stable_tail_support_fraction is not None:
        stable_tail_support_fraction = float(stable_tail_support_fraction)

    theorem_iv_status = str(theorem_iv_certificate.get("theorem_status", "unknown"))
    contradiction_certified = bool(theorem_iv_certificate.get("nonexistence_contradiction_certified", False))
    bridge_status = str(bridge.get("theorem_status", tail_stability.get("theorem_status", "unknown")))
    if contradiction_certified and theorem_iv_status.endswith("-strong"):
        theorem_status = "golden-supercritical-tail-stability-strong"
    elif bridge_status.endswith("-strong"):
        theorem_status = "golden-supercritical-tail-stability-strong"
    elif tail_stability.get("stable_upper_lo") is not None and tail_stability.get("stable_upper_hi") is not None:
        theorem_status = "golden-supercritical-tail-stability-moderate"
    else:
        theorem_status = "golden-supercritical-tail-stability-fragile"

    notes = (
        "This upper-tail stability certificate is inherited directly from the finalized Theorem-IV shell rather than rebuilt from legacy support-audit paths. "
        f"Source theorem-IV status: {theorem_iv_status}."
    )

    return GoldenUpperTailStabilityCertificate(
        rho=float(theorem_iv_certificate.get("rho", golden_inverse())),
        family_label=str(theorem_iv_certificate.get("family_label", "standard-sine")),
        base_crossing_center=float(tail_stability.get("base_crossing_center", 0.0)),
        atlas_shift_grid=[float(x) for x in tail_stability.get("atlas_shift_grid", [])],
        successful_entry_indices=[int(x) for x in successful_entry_indices],
        clustered_entry_indices=[int(x) for x in clustered_entry_indices],
        stable_tail_qs=stable_tail_qs,
        stable_tail_start_q=stable_tail_start_q,
        stable_tail_support_count=stable_tail_support_count,
        stable_tail_support_fraction=stable_tail_support_fraction,
        stable_tail_is_suffix_of_generated_union=bool(bridge.get("certified_tail_is_suffix", tail_stability.get("stable_tail_is_suffix_of_generated_union", False))),
        stable_q_union=[int(x) for x in tail_stability.get("stable_q_union", [])],
        stable_q_intersection=[int(x) for x in tail_stability.get("stable_q_intersection", [])],
        stable_upper_lo=_coerce_float(bridge.get("certified_upper_lo", tail_stability.get("stable_upper_lo"))),
        stable_upper_hi=_coerce_float(bridge.get("certified_upper_hi", tail_stability.get("stable_upper_hi"))),
        stable_upper_width=_coerce_float(bridge.get("certified_upper_width", tail_stability.get("stable_upper_width"))),
        stable_band_lo=_coerce_float(bridge.get("certified_barrier_lo", tail_stability.get("stable_barrier_lo"))),
        stable_band_hi=_coerce_float(bridge.get("certified_barrier_hi", tail_stability.get("stable_barrier_hi"))),
        stable_upper_source=stable_upper_source,
        entries=entries,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_upper_tail_stability_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_shifts: Sequence[float] = (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4),
    min_cluster_size: int = 2,
    min_stable_tail_members: int = 2,
    **audit_kwargs,
) -> GoldenUpperTailStabilityCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    entries: list[GoldenUpperTailStabilityEntry] = []
    all_generated_qs: set[int] = set()
    for shift in atlas_shifts:
        report = build_golden_upper_support_audit_certificate(
            family=family,
            rho=rho,
            crossing_center=float(crossing_center) + float(shift),
            **audit_kwargs,
        ).to_dict()
        for w in report.get("witnesses", []) or []:
            all_generated_qs.update(int(q) for q in (w.get("q_support") or []))
        entries.append(
            GoldenUpperTailStabilityEntry(
                atlas_shift=float(shift),
                crossing_center=float(crossing_center) + float(shift),
                theorem_status=str(report.get("theorem_status", "unknown")),
                audited_upper_lo=None if report.get("audited_upper_lo") is None else float(report.get("audited_upper_lo")),
                audited_upper_hi=None if report.get("audited_upper_hi") is None else float(report.get("audited_upper_hi")),
                audited_upper_width=None if report.get("audited_upper_width") is None else float(report.get("audited_upper_width")),
                audited_upper_source=str(report.get("audited_upper_source", "no-upper-object")),
                robust_qs=[int(x) for x in report.get("robust_qs", [])],
                robust_tail_qs=[int(x) for x in report.get("robust_tail_qs", [])],
                robust_tail_start_q=report.get("robust_tail_start_q"),
                audited_support_size=int(report.get("audited_support_size", 0)),
                audited_center_support_size=int(report.get("audited_center_support_size", 0)),
                tail_is_suffix_of_generated=bool(report.get("tail_is_suffix_of_generated", False)),
                witness_count=int(report.get("witness_count", 0)),
                report=report,
            )
        )
    successful_entry_indices = [i for i, e in enumerate(entries) if e.audited_upper_lo is not None and e.audited_upper_hi is not None]
    windows = [(e.audited_upper_lo, e.audited_upper_hi) for e in entries]
    clustered_entry_indices = _largest_overlapping_subset(successful_entry_indices, windows)
    if len(clustered_entry_indices) < int(min_cluster_size) and successful_entry_indices:
        clustered_entry_indices = successful_entry_indices[:1]
    clustered_entries = [entries[i] for i in clustered_entry_indices]
    stable_upper_lo, stable_upper_hi = _window_intersection((windows[i] for i in clustered_entry_indices))
    stable_upper_width = None if stable_upper_lo is None or stable_upper_hi is None else float(stable_upper_hi - stable_upper_lo)
    q_sets = [e.robust_qs for e in clustered_entries if e.robust_qs]
    tail_sets = [e.robust_tail_qs for e in clustered_entries if e.robust_tail_qs]
    stable_q_intersection = _intersection_sorted(q_sets) if q_sets else []
    stable_q_union = _union_sorted(q_sets) if q_sets else []
    stable_tail_qs = _intersection_sorted(tail_sets) if tail_sets else []
    if len(stable_tail_qs) < int(min_stable_tail_members):
        stable_tail_qs = []
    stable_tail_start_q = stable_tail_qs[0] if stable_tail_qs else None
    stable_tail_support_count = sum(1 for e in clustered_entries if set(stable_tail_qs).issubset(set(e.robust_tail_qs or e.robust_qs))) if stable_tail_qs else 0
    stable_tail_support_fraction = None if not clustered_entries or not stable_tail_qs else float(stable_tail_support_count / len(clustered_entries))
    generated_union = sorted(all_generated_qs)
    stable_tail_is_suffix = _is_suffix(stable_tail_qs, generated_union)
    band_windows = []
    for e in clustered_entries:
        band_lo = e.report.get("audited_band_lo")
        band_hi = e.report.get("audited_band_hi")
        if band_lo is not None and band_hi is not None:
            band_windows.append((float(band_lo), float(band_hi)))
    stable_band_lo, stable_band_hi = _window_intersection(band_windows)
    sources = [e.audited_upper_source for e in clustered_entries if e.audited_upper_source != "no-upper-object"]
    stable_upper_source = sources[0] if sources and all(s == sources[0] for s in sources) else (sources[0] if sources else "no-upper-object")
    if stable_upper_lo is None or stable_upper_hi is None:
        theorem_status = "golden-supercritical-tail-stability-failed"
        notes = "No coherent upper window persisted across neighboring golden support-audit atlases."
    elif len(clustered_entry_indices) >= int(min_cluster_size) and stable_tail_qs and stable_tail_support_fraction is not None and stable_tail_support_fraction >= 0.75 and stable_tail_is_suffix:
        theorem_status = "golden-supercritical-tail-stability-strong"
        notes = "A coherent golden upper window persists across neighboring atlas constructions, and the same high-denominator support tail survives across that neighborhood. This is a stronger theorem-facing upper-side object than a single support audit."
    elif len(clustered_entry_indices) >= int(min_cluster_size) and stable_tail_qs:
        theorem_status = "golden-supercritical-tail-stability-moderate"
        notes = "A coherent golden upper window persists across neighboring atlas constructions, with a stable denominator tail, but the tail support is not yet strong enough for the strongest status."
    elif len(clustered_entry_indices) >= int(min_cluster_size) and stable_q_intersection:
        theorem_status = "golden-supercritical-tail-stability-weak"
        notes = "A coherent golden upper window persists across neighboring atlas constructions, but stable support is visible only at the level of convergent intersection rather than a robust tail."
    elif successful_entry_indices:
        theorem_status = "golden-supercritical-tail-stability-fragile"
        notes = "Some neighboring atlases produced upper-side objects, but they do not stabilize into a coherent tail-supported neighborhood object."
    else:
        theorem_status = "golden-supercritical-tail-stability-failed"
        notes = "Neighboring golden support audits did not produce usable upper-side objects."
    return GoldenUpperTailStabilityCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        base_crossing_center=float(crossing_center),
        atlas_shift_grid=[float(x) for x in atlas_shifts],
        successful_entry_indices=[int(x) for x in successful_entry_indices],
        clustered_entry_indices=[int(x) for x in clustered_entry_indices],
        stable_tail_qs=stable_tail_qs,
        stable_tail_start_q=stable_tail_start_q,
        stable_tail_support_count=int(stable_tail_support_count),
        stable_tail_support_fraction=stable_tail_support_fraction,
        stable_tail_is_suffix_of_generated_union=bool(stable_tail_is_suffix),
        stable_q_union=stable_q_union,
        stable_q_intersection=stable_q_intersection,
        stable_upper_lo=stable_upper_lo,
        stable_upper_hi=stable_upper_hi,
        stable_upper_width=stable_upper_width,
        stable_band_lo=stable_band_lo,
        stable_band_hi=stable_band_hi,
        stable_upper_source=str(stable_upper_source),
        entries=entries,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_two_sided_tail_stability_bridge_certificate(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    **tail_kwargs,
) -> GoldenTwoSidedTailStabilityBridgeCertificate:
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
    upper = build_golden_upper_tail_stability_certificate(family=family, rho=rho, **tail_kwargs).to_dict()
    lower_bound = lower.get("last_stable_K")
    upper_lo = upper.get("stable_upper_lo")
    upper_hi = upper.get("stable_upper_hi")
    band_lo = upper.get("stable_band_lo")
    gap = None if lower_bound is None or upper_lo is None else float(upper_lo - float(lower_bound))
    gap_to_band = None if lower_bound is None or band_lo is None else float(band_lo - float(lower_bound))
    relation = {
        "lower_bound": None if lower_bound is None else float(lower_bound),
        "upper_crossing_lo": None if upper_lo is None else float(upper_lo),
        "upper_crossing_hi": None if upper_hi is None else float(upper_hi),
        "upper_object_source": str(upper.get("stable_upper_source", "none")),
        "gap_to_upper": gap,
        "gap_to_band": gap_to_band,
        "stable_tail_qs": [int(x) for x in upper.get("stable_tail_qs", [])],
        "stable_tail_support_count": int(upper.get("stable_tail_support_count", 0)),
        "clustered_atlas_count": len(upper.get("clustered_entry_indices", [])),
        "upper_status": str(upper.get("theorem_status", "unknown")),
    }
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        if str(upper.get("theorem_status")) == "golden-supercritical-tail-stability-strong":
            status = "golden-two-sided-tail-stability-strong"
        else:
            status = "golden-two-sided-tail-stability-partial"
        notes = "Lower golden a-posteriori continuation lies below an upper object that is stable across neighboring support-audit atlases. This is still not the final critical-boundary theorem, but it is a stronger two-sided golden bridge than a single-atlas support audit."
    else:
        status = "golden-two-sided-tail-stability-incomplete"
        notes = "The neighborhood-level golden upper-side tail-stability audit did not yet separate cleanly from the lower a-posteriori side."
    return GoldenTwoSidedTailStabilityBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=status,
        notes=notes,
    )
