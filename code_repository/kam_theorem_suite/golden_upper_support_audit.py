from __future__ import annotations

"""Denominator-aware support audit for the golden upper-side localization atlas.

This module upgrades the golden upper-side atlas from a pure overlap object to a
more theorem-facing *support audit*.

The key question is no longer only:
    Do nearby localized upper objects overlap?

but also:
    Which golden convergents actually support those localized upper objects, and
    is that support coherent on a high-denominator tail?

The implementation remains honest: it does not claim a finished irrational
nonexistence theorem.  It turns the current localization-atlas evidence into a
structured audit across both nearby centers and denominator growth.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence

from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .golden_supercritical_localization_atlas import build_golden_supercritical_localization_atlas_certificate
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _overlaps(lo1: float | None, hi1: float | None, lo2: float | None, hi2: float | None) -> bool:
    if lo1 is None or hi1 is None or lo2 is None or hi2 is None:
        return False
    return max(float(lo1), float(lo2)) <= min(float(hi1), float(hi2))


@dataclass
class GoldenUpperSupportWitness:
    atlas_index: int
    round_index: int
    step_index: int
    seed_center: float
    crossing_center: float
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_upper_source: str
    q_support: list[int]
    q_support_labels: list[str]
    q_support_count: int
    q_min: int | None
    q_max: int | None
    q_tail_threshold: int | None
    band_q_support: list[int]
    band_q_support_count: int
    witness_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenUpperSupportAuditCertificate:
    rho: float
    family_label: str
    atlas_summary: dict[str, Any]
    clustered_entry_indices: list[int]
    witness_count: int
    support_vote_counts: dict[int, int]
    band_vote_counts: dict[int, int]
    robust_qs: list[int]
    robust_q_labels: list[str]
    robust_tail_qs: list[int]
    robust_tail_start_q: int | None
    tail_support_min_votes: int
    support_fraction_threshold: float
    support_witness_fraction: float | None
    tail_is_suffix_of_generated: bool
    audited_upper_lo: float | None
    audited_upper_hi: float | None
    audited_upper_width: float | None
    audited_upper_source: str
    audited_support_size: int
    audited_center_support_size: int
    audited_band_lo: float | None
    audited_band_hi: float | None
    witnesses: list[GoldenUpperSupportWitness]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "atlas_summary": dict(self.atlas_summary),
            "clustered_entry_indices": [int(x) for x in self.clustered_entry_indices],
            "witness_count": int(self.witness_count),
            "support_vote_counts": {int(k): int(v) for k, v in self.support_vote_counts.items()},
            "band_vote_counts": {int(k): int(v) for k, v in self.band_vote_counts.items()},
            "robust_qs": [int(x) for x in self.robust_qs],
            "robust_q_labels": [str(x) for x in self.robust_q_labels],
            "robust_tail_qs": [int(x) for x in self.robust_tail_qs],
            "robust_tail_start_q": self.robust_tail_start_q,
            "tail_support_min_votes": int(self.tail_support_min_votes),
            "support_fraction_threshold": float(self.support_fraction_threshold),
            "support_witness_fraction": self.support_witness_fraction,
            "tail_is_suffix_of_generated": bool(self.tail_is_suffix_of_generated),
            "audited_upper_lo": self.audited_upper_lo,
            "audited_upper_hi": self.audited_upper_hi,
            "audited_upper_width": self.audited_upper_width,
            "audited_upper_source": str(self.audited_upper_source),
            "audited_support_size": int(self.audited_support_size),
            "audited_center_support_size": int(self.audited_center_support_size),
            "audited_band_lo": self.audited_band_lo,
            "audited_band_hi": self.audited_band_hi,
            "witnesses": [w.to_dict() for w in self.witnesses],
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


@dataclass
class GoldenTwoSidedSupportAuditBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _support_from_obstruction(cert: dict[str, Any], *, target_lo: float | None, target_hi: float | None) -> tuple[list[int], list[str], int | None, list[int]]:
    ladder = cert.get("ladder", {})
    approximants = ladder.get("approximants", []) or []
    refined = cert.get("refined", {}) or {}
    audit = cert.get("asymptotic_audit", {}) or {}
    source = str(cert.get("selected_upper_source", "no-upper-object"))
    restrict_qs: set[int] | None = None
    tail_threshold = None
    if source == "refined-upper-ladder":
        qs = refined.get("selected_cluster_member_qs") or []
        if qs:
            restrict_qs = {int(q) for q in qs}
    elif source == "asymptotic-upper-ladder":
        thr = audit.get("audited_upper_source_threshold")
        if thr is not None:
            tail_threshold = int(thr)
    support_qs: list[int] = []
    support_labels: list[str] = []
    band_qs: list[int] = []
    for app in approximants:
        q = int(app.get("q", 0))
        if q <= 0:
            continue
        if restrict_qs is not None and q not in restrict_qs:
            continue
        if tail_threshold is not None and q < tail_threshold:
            continue
        if _overlaps(app.get("crossing_root_window_lo"), app.get("crossing_root_window_hi"), target_lo, target_hi):
            support_qs.append(q)
            support_labels.append(str(app.get("label", f"q={q}")))
        if _overlaps(app.get("hyperbolic_band_lo"), app.get("hyperbolic_band_hi"), cert.get("earliest_hyperbolic_band_lo"), cert.get("latest_hyperbolic_band_hi")):
            band_qs.append(q)
    return sorted(set(support_qs)), sorted(set(support_labels)), tail_threshold, sorted(set(band_qs))


def _entry_is_clustered(entry: dict[str, Any], atlas_lo: float | None, atlas_hi: float | None) -> bool:
    return _overlaps(entry.get("localized_upper_lo"), entry.get("localized_upper_hi"), atlas_lo, atlas_hi)


def build_golden_upper_support_audit_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    crossing_center: float = 0.971635406,
    atlas_center_offsets: Sequence[float] = (-1.2e-3, -6.0e-4, 0.0, 6.0e-4, 1.2e-3),
    crossing_center_offsets: Sequence[float] = (-8.0e-4, -4.0e-4, 0.0, 4.0e-4, 8.0e-4),
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
    support_fraction_threshold: float = 0.6,
    min_tail_members: int = 2,
) -> GoldenUpperSupportAuditCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    atlas = build_golden_supercritical_localization_atlas_certificate(
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

    atlas_lo = atlas.get("atlas_upper_lo")
    atlas_hi = atlas.get("atlas_upper_hi")
    entries = atlas.get("entries", []) or []
    clustered_entry_indices = [int(i) for i, e in enumerate(entries) if _entry_is_clustered(e, atlas_lo, atlas_hi)]
    witnesses: list[GoldenUpperSupportWitness] = []
    all_generated_qs: set[int] = set()
    for entry_idx in clustered_entry_indices:
        entry = entries[entry_idx]
        loc_cert = entry.get("certificate", {}) or {}
        best_round_index = loc_cert.get("best_round_index")
        round_indices: Iterable[int]
        if best_round_index is None:
            round_indices = range(len(loc_cert.get("rounds", [])))
        else:
            round_indices = [int(best_round_index)]
        for ridx in round_indices:
            rounds = loc_cert.get("rounds", []) or []
            if ridx < 0 or ridx >= len(rounds):
                continue
            r = rounds[ridx]
            continuation = r.get("certificate", {}) or {}
            support_step_indices = continuation.get("stable_upper_support_indices") or [s.get("index") for s in continuation.get("steps", [])]
            step_map = {int(s.get("index", i)): s for i, s in enumerate(continuation.get("steps", []) or [])}
            for step_idx in support_step_indices:
                if step_idx not in step_map:
                    continue
                step = step_map[int(step_idx)]
                obstruction = step.get("certificate", {}) or {}
                for gc in obstruction.get("generated_convergents", []) or []:
                    q = gc.get("q")
                    if q is not None:
                        all_generated_qs.add(int(q))
                target_lo = atlas_lo if atlas_lo is not None else step.get("selected_upper_lo")
                target_hi = atlas_hi if atlas_hi is not None else step.get("selected_upper_hi")
                q_support, q_labels, tail_thr, band_qs = _support_from_obstruction(obstruction, target_lo=target_lo, target_hi=target_hi)
                witness_status = "supported" if q_support else "unsupported"
                witnesses.append(
                    GoldenUpperSupportWitness(
                        atlas_index=int(entry_idx),
                        round_index=int(ridx),
                        step_index=int(step_idx),
                        seed_center=float(entry.get("seed_center", 0.0)),
                        crossing_center=float(step.get("crossing_center", 0.0)),
                        selected_upper_lo=None if step.get("selected_upper_lo") is None else float(step.get("selected_upper_lo")),
                        selected_upper_hi=None if step.get("selected_upper_hi") is None else float(step.get("selected_upper_hi")),
                        selected_upper_source=str(step.get("selected_upper_source", obstruction.get("selected_upper_source", "no-upper-object"))),
                        q_support=[int(q) for q in q_support],
                        q_support_labels=[str(x) for x in q_labels],
                        q_support_count=len(q_support),
                        q_min=(min(q_support) if q_support else None),
                        q_max=(max(q_support) if q_support else None),
                        q_tail_threshold=tail_thr,
                        band_q_support=[int(q) for q in band_qs],
                        band_q_support_count=len(band_qs),
                        witness_status=witness_status,
                    )
                )

    support_vote_counts: dict[int, int] = {}
    band_vote_counts: dict[int, int] = {}
    support_labels_by_q: dict[int, str] = {}
    center_support: dict[int, set[int]] = {}
    for w in witnesses:
        center_support.setdefault(int(w.atlas_index), set()).update(int(q) for q in w.q_support)
        for q, lab in zip(w.q_support, w.q_support_labels):
            support_vote_counts[int(q)] = support_vote_counts.get(int(q), 0) + 1
            support_labels_by_q.setdefault(int(q), str(lab))
        for q in w.band_q_support:
            band_vote_counts[int(q)] = band_vote_counts.get(int(q), 0) + 1

    witness_count = len(witnesses)
    min_votes = max(1, int((witness_count * float(support_fraction_threshold)) + 0.999999)) if witness_count else 1
    robust_qs = sorted(q for q, votes in support_vote_counts.items() if votes >= min_votes)
    robust_q_labels = [support_labels_by_q[q] for q in robust_qs]
    generated_sorted = sorted(all_generated_qs)
    robust_tail_qs: list[int] = []
    tail_is_suffix = False
    robust_tail_start_q = None
    if robust_qs:
        candidate = list(robust_qs)
        if generated_sorted:
            for i, q in enumerate(generated_sorted):
                suffix = generated_sorted[i:]
                if len(suffix) >= min_tail_members and all(x in robust_qs for x in suffix):
                    candidate = suffix
                    tail_is_suffix = True
                    robust_tail_start_q = q
                    break
        if len(candidate) >= int(min_tail_members):
            robust_tail_qs = [int(x) for x in candidate]
        elif len(robust_qs) >= int(min_tail_members):
            robust_tail_qs = [int(x) for x in robust_qs]
            robust_tail_start_q = robust_qs[0]

    support_witness_fraction = None if witness_count == 0 or not robust_qs else float(sum(support_vote_counts[q] for q in robust_qs) / (witness_count * len(robust_qs)))
    audited_support_size = len(robust_tail_qs) if robust_tail_qs else len(robust_qs)
    audited_center_support_size = sum(1 for qs in center_support.values() if any(q in qs for q in (robust_tail_qs or robust_qs)))
    audited_upper_lo = None if atlas_lo is None else float(atlas_lo)
    audited_upper_hi = None if atlas_hi is None else float(atlas_hi)
    audited_upper_width = None
    if audited_upper_lo is not None and audited_upper_hi is not None:
        audited_upper_width = float(audited_upper_hi - audited_upper_lo)
    audited_band_lo = atlas.get("atlas_band_lo")
    audited_band_hi = atlas.get("atlas_band_hi")
    source = str(atlas.get("atlas_upper_source", "no-upper-object"))

    if audited_upper_lo is None or audited_upper_hi is None:
        theorem_status = "golden-supercritical-support-audit-failed"
        notes = "No atlas-level golden upper object was available to audit across denominators."
    elif robust_tail_qs and audited_center_support_size >= 2 and tail_is_suffix:
        theorem_status = "golden-supercritical-support-audit-strong"
        notes = "Localized golden upper object is supported by a suffix-like high-denominator tail across multiple nearby centers. This is still not an irrational nonexistence theorem, but it is the strongest denominator-aware upper-side audit currently implemented."
    elif robust_tail_qs and audited_center_support_size >= 1:
        theorem_status = "golden-supercritical-support-audit-moderate"
        notes = "Localized golden upper object has coherent high-denominator support, but the tail either lacks center redundancy or has not stabilized into a clean generated suffix."
    elif robust_qs:
        theorem_status = "golden-supercritical-support-audit-weak"
        notes = "Localized golden upper object has some convergent support, but the denominator pattern is too sparse for a tail-level audit."
    else:
        theorem_status = "golden-supercritical-support-audit-fragile"
        notes = "Localized golden upper object exists, but the denominator support is too unstable or too thin to audit meaningfully."

    return GoldenUpperSupportAuditCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        atlas_summary={
            "theorem_status": atlas.get("theorem_status"),
            "successful_entry_count": atlas.get("successful_entry_count"),
            "clustered_entry_count": atlas.get("clustered_entry_count"),
            "atlas_upper_source": atlas.get("atlas_upper_source"),
            "atlas_upper_lo": atlas.get("atlas_upper_lo"),
            "atlas_upper_hi": atlas.get("atlas_upper_hi"),
            "atlas_upper_width": atlas.get("atlas_upper_width"),
        },
        clustered_entry_indices=clustered_entry_indices,
        witness_count=witness_count,
        support_vote_counts=support_vote_counts,
        band_vote_counts=band_vote_counts,
        robust_qs=robust_qs,
        robust_q_labels=robust_q_labels,
        robust_tail_qs=robust_tail_qs,
        robust_tail_start_q=robust_tail_start_q,
        tail_support_min_votes=min_votes,
        support_fraction_threshold=float(support_fraction_threshold),
        support_witness_fraction=support_witness_fraction,
        tail_is_suffix_of_generated=tail_is_suffix,
        audited_upper_lo=audited_upper_lo,
        audited_upper_hi=audited_upper_hi,
        audited_upper_width=audited_upper_width,
        audited_upper_source=source,
        audited_support_size=audited_support_size,
        audited_center_support_size=audited_center_support_size,
        audited_band_lo=(None if audited_band_lo is None else float(audited_band_lo)),
        audited_band_hi=(None if audited_band_hi is None else float(audited_band_hi)),
        witnesses=witnesses,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_two_sided_support_audit_bridge_certificate(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    **audit_kwargs,
) -> GoldenTwoSidedSupportAuditBridgeCertificate:
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
    upper = build_golden_upper_support_audit_certificate(family=family, rho=rho, **audit_kwargs).to_dict()
    lower_bound = lower.get("last_stable_K")
    upper_lo = upper.get("audited_upper_lo")
    upper_hi = upper.get("audited_upper_hi")
    band_lo = upper.get("audited_band_lo")
    gap = None if lower_bound is None or upper_lo is None else float(upper_lo - float(lower_bound))
    gap_to_band = None if lower_bound is None or band_lo is None else float(band_lo - float(lower_bound))
    relation = {
        "lower_bound": None if lower_bound is None else float(lower_bound),
        "upper_crossing_lo": None if upper_lo is None else float(upper_lo),
        "upper_crossing_hi": None if upper_hi is None else float(upper_hi),
        "upper_object_source": str(upper.get("audited_upper_source", "none")),
        "gap_to_upper": gap,
        "gap_to_band": gap_to_band,
        "upper_support_size": int(upper.get("audited_support_size", 0)),
        "upper_center_support_size": int(upper.get("audited_center_support_size", 0)),
        "upper_status": str(upper.get("theorem_status", "unknown")),
    }
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        if str(upper.get("theorem_status")) == "golden-supercritical-support-audit-strong":
            status = "golden-two-sided-support-audit-strong"
        else:
            status = "golden-two-sided-support-audit-partial"
        notes = "Lower golden a-posteriori continuation lies below the denominator-audited upper-side object. This is still not the final critical-boundary theorem, but it is a stronger two-sided golden bridge than the previous center-only atlas."
    else:
        status = "golden-two-sided-support-audit-incomplete"
        notes = "The denominator-aware golden upper-side audit did not yet separate cleanly from the lower a-posteriori side."
    return GoldenTwoSidedSupportAuditBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=status,
        notes=notes,
    )
