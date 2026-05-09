from __future__ import annotations

"""Adaptive upper-side incompatibility packages driven by branch-generic crossing certificates.

This stage upgrades the Theorem IV front by feeding the stage-30 adaptive
branch-localization layer directly into the upper obstruction package.

The goal is not to claim a finished irrational nonexistence theorem. The goal is
more modest and more honest:

- start from broad rational crossing windows,
- adaptively localize theorem-like crossing subwindows on each approximant,
- attach later hyperbolic-band witnesses using those localized windows rather
  than only the original broad inputs, and
- compress the resulting ladder into one coherent incompatibility-oriented
  certificate.

This is stronger than a raw obstruction atlas because it makes the upper-side
package depend on the branch-generic crossing machinery rather than on looser
window guesses alone.
"""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .golden_supercritical import generate_golden_convergent_specs
from .hyperbolicity_certifier import certify_sustained_hyperbolic_tail
from .obstruction_atlas import ApproximantWindowSpec
from .residue_branch import adaptive_localize_residue_crossing
from .standard_map import HarmonicFamily
from .supercritical_bands import build_supercritical_band_report
from .theorem_iv_methodology import (
    get_theorem_iv_methodology_profile,
    methodology_localize_theorem_iv_crossing,
)


@dataclass
class AdaptiveIncompatibilityAtlasEntry:
    p: int
    q: int
    label: str
    crossing_window_input_lo: float
    crossing_window_input_hi: float
    band_search_lo: float
    band_search_hi: float
    adaptive_crossing: dict[str, Any]
    localized_crossing_source: str
    crossing_root_window_lo: float | None
    crossing_root_window_hi: float | None
    crossing_root_window_width: float | None
    band_report: dict[str, Any]
    hyperbolic_band_lo: float | None
    hyperbolic_band_hi: float | None
    hyperbolic_band_width: float | None
    gap_from_crossing_to_band: float | None
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["crossing_certificate"] = {
            "certification_tier": self.adaptive_crossing.get("status", "incomplete"),
            "source": self.localized_crossing_source,
        }
        return d


@dataclass
class AdaptiveIncompatibilityAtlasCertificate:
    family_label: str
    entries: list[dict[str, Any]]
    hyperbolic_tail: dict[str, Any]
    coherent_upper_lo: float | None
    coherent_upper_hi: float | None
    coherent_upper_width: float | None
    coherent_band_lo: float | None
    coherent_band_hi: float | None
    coherent_band_width: float | None
    incompatibility_gap: float | None
    interval_newton_count: int
    monotone_count: int
    fully_certified_count: int
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenAdaptiveIncompatibilityCertificate:
    rho: float
    family_label: str
    generated_convergents: list[dict[str, Any]]
    atlas: dict[str, Any]
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_upper_width: float | None
    selected_barrier_lo: float | None
    selected_barrier_hi: float | None
    selected_barrier_width: float | None
    incompatibility_gap: float | None
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"



def _extract_best_crossing_window(adaptive_report: dict[str, Any]) -> tuple[str, float | None, float | None]:
    best = adaptive_report.get("best_window") or {}
    status = str(adaptive_report.get("status", "failed"))
    if status == "theorem_mode_local":
        lo = adaptive_report.get("K_lo") or best.get("K_lo")
        hi = adaptive_report.get("K_hi") or best.get("K_hi")
        if lo is not None and hi is not None:
            return "methodology-theorem-window", float(lo), float(hi)
    if status == "interval_newton":
        newton = best.get("interval_newton", {}) or {}
        lo = newton.get("refined_lo")
        hi = newton.get("refined_hi")
        if lo is not None and hi is not None:
            return "adaptive-interval-newton", float(lo), float(hi)
    if status in {"interval_newton", "monotone_window"}:
        lo = best.get("K_lo")
        hi = best.get("K_hi")
        if lo is not None and hi is not None:
            return "adaptive-monotone-window", float(lo), float(hi)
    return "none", None, None



def _entry_status(crossing_lo: float | None, crossing_hi: float | None, band_lo: float | None, band_hi: float | None) -> tuple[str, str]:
    if crossing_lo is not None and crossing_hi is not None and band_lo is not None and band_hi is not None:
        return "adaptive-crossing-plus-band", "adaptive crossing localization and later hyperbolic band both certified"
    if crossing_lo is not None and crossing_hi is not None:
        return "adaptive-crossing-only", "adaptive crossing localized but no later hyperbolic band was certified"
    if band_lo is not None and band_hi is not None:
        return "band-only", "band certified without a localized crossing window"
    return "incomplete", "adaptive upper-side entry remains exploratory"



def build_adaptive_incompatibility_entry_certificate(
    spec: ApproximantWindowSpec,
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    crossing_max_depth: int = 5,
    crossing_min_width: float = 5e-4,
    crossing_n_pieces: int = 2,
    band_initial_subdivisions: int = 4,
    band_max_depth: int = 4,
    band_min_width: float = 5e-4,
    use_seed_propagation: bool = True,
    use_methodology_frontend: bool = True,
    predictive_hint_center: float | None = None,
    previous_entry_dicts: Sequence[dict[str, Any]] | None = None,
) -> AdaptiveIncompatibilityAtlasEntry:
    family = family or HarmonicFamily()
    methodology = None
    seed_guess = None
    crossing_lo = float(spec.crossing_K_lo)
    crossing_hi = float(spec.crossing_K_hi)
    if use_methodology_frontend and int(spec.q) >= 21:
        methodology = methodology_localize_theorem_iv_crossing(
            spec,
            family=family,
            target_residue=target_residue,
            profile=get_theorem_iv_methodology_profile(spec.p, spec.q),
            predictive_hint_center=predictive_hint_center,
            previous_entry_dicts=previous_entry_dicts,
            enable_high_precision=True,
        )
        seed_guess = methodology.get('x_seed')
        if methodology.get('proof_ready', False):
            adaptive = {
                'p': int(spec.p),
                'q': int(spec.q),
                'K_lo': float(methodology['K_lo']),
                'K_hi': float(methodology['K_hi']),
                'target_residue': float(target_residue),
                'analyzed_windows': len(methodology.get('scan_rows', []) or []),
                'max_depth_reached': 0,
                'best_window': {
                    'K_lo': float(methodology['K_lo']),
                    'K_hi': float(methodology['K_hi']),
                    'interval_newton': {
                        'refined_lo': float(methodology['K_lo']),
                        'refined_hi': float(methodology['K_hi']),
                    },
                },
                'successful_window_count': 1,
                'monotone_window_count': 1,
                'interval_newton_window_count': 1 if methodology.get('method') in {'newton_local', 'certified_unique_window'} else 0,
                'status': 'theorem_mode_local',
                'windows': [],
                'message': 'methodology front-end produced a proof-ready local crossing certificate',
                'methodology_frontend': methodology,
            }
        else:
            crossing_lo = float(methodology.get('K_lo', crossing_lo))
            crossing_hi = float(methodology.get('K_hi', crossing_hi))
            adaptive = adaptive_localize_residue_crossing(
                p=spec.p,
                q=spec.q,
                K_lo=crossing_lo,
                K_hi=crossing_hi,
                family=family,
                target_residue=target_residue,
                max_depth=crossing_max_depth,
                min_width=crossing_min_width,
                n_pieces=crossing_n_pieces,
                use_seed_propagation=use_seed_propagation,
                initial_x_guess=seed_guess,
            ).to_dict()
            adaptive['methodology_frontend'] = methodology
    else:
        adaptive = adaptive_localize_residue_crossing(
            p=spec.p,
            q=spec.q,
            K_lo=spec.crossing_K_lo,
            K_hi=spec.crossing_K_hi,
            family=family,
            target_residue=target_residue,
            max_depth=crossing_max_depth,
            min_width=crossing_min_width,
            n_pieces=crossing_n_pieces,
            use_seed_propagation=use_seed_propagation,
        ).to_dict()
    crossing_source, root_lo, root_hi = _extract_best_crossing_window(adaptive)
    root_w = None if root_lo is None or root_hi is None else float(root_hi - root_lo)
    effective_band_lo = float(spec.band_search_lo if root_hi is None else max(float(spec.band_search_lo), float(root_hi)))
    band_seed = None
    best_window = adaptive.get("best_window") or {}
    branch = best_window.get("branch_tube") or {}
    if branch.get("x_right") is not None:
        band_seed = branch.get("x_right")
    elif branch.get("x_mid") is not None:
        band_seed = branch.get("x_mid")
    elif methodology is not None and methodology.get('x_seed') is not None:
        band_seed = methodology.get('x_seed')
    band = build_supercritical_band_report(
        p=spec.p,
        q=spec.q,
        K_lo=effective_band_lo,
        K_hi=float(spec.band_search_hi),
        family=family,
        x_guess=band_seed,
        target_residue=target_residue,
        initial_subdivisions=band_initial_subdivisions,
        max_depth=band_max_depth,
        min_width=band_min_width,
        use_seed_propagation=use_seed_propagation,
        use_methodology_frontend=True,
        crossing_root_hi=root_hi,
        previous_entry_dicts=list(previous_entry_dicts or []),
        skip_recursive_scan_on_success=True,
    ).to_dict()
    band_lo = band.get("longest_band_lo")
    band_hi = band.get("longest_band_hi")
    band_w = None if band_lo is None or band_hi is None else float(float(band_hi) - float(band_lo))
    gap = None if root_hi is None or band_lo is None else float(float(band_lo) - float(root_hi))
    status, notes = _entry_status(root_lo, root_hi, band_lo, band_hi)
    return AdaptiveIncompatibilityAtlasEntry(
        p=int(spec.p),
        q=int(spec.q),
        label=str(spec.normalized_label()),
        crossing_window_input_lo=float(spec.crossing_K_lo),
        crossing_window_input_hi=float(spec.crossing_K_hi),
        band_search_lo=float(spec.band_search_lo),
        band_search_hi=float(spec.band_search_hi),
        adaptive_crossing=adaptive,
        localized_crossing_source=crossing_source,
        crossing_root_window_lo=root_lo,
        crossing_root_window_hi=root_hi,
        crossing_root_window_width=root_w,
        band_report=band,
        hyperbolic_band_lo=None if band_lo is None else float(band_lo),
        hyperbolic_band_hi=None if band_hi is None else float(band_hi),
        hyperbolic_band_width=band_w,
        gap_from_crossing_to_band=gap,
        status=status,
        notes=notes,
    )


def _build_adaptive_incompatibility_entry_worker(payload: dict[str, Any]) -> dict[str, Any]:
    spec = ApproximantWindowSpec(**payload["spec"])
    family = payload.get("family")
    kwargs = dict(payload.get("kwargs", {}))
    return build_adaptive_incompatibility_entry_certificate(spec, family=family, **kwargs).to_dict()


def _normalize_adaptive_incompatibility_entry_dict(
    entry: AdaptiveIncompatibilityAtlasEntry | dict[str, Any]
) -> dict[str, Any]:
    out = entry.to_dict() if isinstance(entry, AdaptiveIncompatibilityAtlasEntry) else dict(entry)

    adaptive = dict(out.get("adaptive_crossing") or {})
    crossing = dict(out.get("crossing_certificate") or {})
    if not crossing:
        crossing = {
            "certification_tier": str(adaptive.get("status", "incomplete")),
            "source": str(out.get("localized_crossing_source", adaptive.get("message", "normalized-entry"))),
        }
    out["crossing_certificate"] = crossing
    out.setdefault("localized_crossing_source", str(crossing.get("source", "normalized-entry")))

    if not adaptive:
        adaptive = {
            "status": str(crossing.get("certification_tier", "incomplete")),
            "message": "normalized atlas entry",
        }
    out["adaptive_crossing"] = adaptive

    clo = out.get("crossing_root_window_lo")
    chi = out.get("crossing_root_window_hi")
    if out.get("crossing_root_window_width") is None and clo is not None and chi is not None:
        out["crossing_root_window_width"] = float(chi) - float(clo)

    blo = out.get("hyperbolic_band_lo")
    bhi = out.get("hyperbolic_band_hi")
    if out.get("hyperbolic_band_width") is None and blo is not None and bhi is not None:
        out["hyperbolic_band_width"] = float(bhi) - float(blo)

    out.setdefault("crossing_window_input_lo", clo)
    out.setdefault("crossing_window_input_hi", chi)
    out.setdefault("band_search_lo", blo)
    out.setdefault("band_search_hi", bhi)

    if out.get("status") == "tail-transport-derived" and clo is not None and chi is not None and blo is not None and bhi is not None:
        out["status"] = "adaptive-crossing-plus-band"

    if out.get("status") is None:
        status, notes = _entry_status(clo, chi, blo, bhi)
        out["status"] = status
        out["notes"] = notes
    else:
        out.setdefault("notes", "normalized atlas entry")
    return out


def _longest_suffix_subset(generated_qs: Sequence[int], witness_qs: set[int]) -> list[int]:
    ordered = sorted({int(q) for q in generated_qs})
    if not ordered:
        return []
    for idx in range(len(ordered)):
        tail = ordered[idx:]
        if tail and all(q in witness_qs for q in tail):
            return tail
    return []


def _build_tail_summary_from_normalized_entries(
    entries: Sequence[dict[str, Any]],
    *,
    min_tail_members: int,
) -> dict[str, Any]:
    legacy_tail = certify_sustained_hyperbolic_tail(entries, min_tail_members=min_tail_members).to_dict()

    derived_witnesses = [
        e for e in entries
        if str((e.get("crossing_certificate") or {}).get("certification_tier", "")) == "anchor_upper_object"
        and e.get("crossing_root_window_lo") is not None
        and e.get("crossing_root_window_hi") is not None
        and e.get("hyperbolic_band_lo") is not None
        and e.get("hyperbolic_band_hi") is not None
        and (e.get("gap_from_crossing_to_band") is not None and float(e.get("gap_from_crossing_to_band")) > 0.0)
    ]
    generated_qs = sorted({int(e.get("q", 0)) for e in entries if int(e.get("q", 0)) > 0})
    derived_qs = sorted({int(e.get("q", 0)) for e in derived_witnesses if int(e.get("q", 0)) > 0})
    tail_qs = _longest_suffix_subset(generated_qs, set(derived_qs))

    if len(tail_qs) < int(min_tail_members):
        return legacy_tail

    tail_entries = [e for e in derived_witnesses if int(e.get("q", 0)) in set(tail_qs)]
    upper_lo = max(float(e["crossing_root_window_lo"]) for e in tail_entries)
    upper_hi = min(float(e["crossing_root_window_hi"]) for e in tail_entries)
    band_lo = min(float(e["hyperbolic_band_lo"]) for e in tail_entries)
    band_hi = max(float(e["hyperbolic_band_hi"]) for e in tail_entries)
    incompat_gap = float(band_lo - upper_hi)

    witnesses = []
    witness_qs = []
    for entry in entries:
        q = int(entry.get("q", 0))
        cross_ok = (entry.get("crossing_root_window_lo") is not None and entry.get("crossing_root_window_hi") is not None)
        band_ok = (entry.get("hyperbolic_band_lo") is not None and entry.get("hyperbolic_band_hi") is not None)
        gap = entry.get("gap_from_crossing_to_band")
        if gap is None and cross_ok and band_ok:
            gap = float(entry["hyperbolic_band_lo"]) - float(entry["crossing_root_window_hi"])
        witness_ok = cross_ok and band_ok and gap is not None and float(gap) > 0.0
        status = "sustained-hyperbolic-witness" if witness_ok else (
            "crossing-only" if cross_ok and not band_ok else "band-only" if band_ok and not cross_ok else "incomplete"
        )
        witnesses.append({
            "q": q,
            "label": str(entry.get("label", f"q={q}")),
            "crossing_root_window_lo": None if not cross_ok else float(entry["crossing_root_window_lo"]),
            "crossing_root_window_hi": None if not cross_ok else float(entry["crossing_root_window_hi"]),
            "hyperbolic_band_lo": None if not band_ok else float(entry["hyperbolic_band_lo"]),
            "hyperbolic_band_hi": None if not band_ok else float(entry["hyperbolic_band_hi"]),
            "gap_from_crossing_to_band": None if gap is None else float(gap),
            "crossing_certified": bool(cross_ok),
            "band_certified": bool(band_ok),
            "witness_status": status,
        })
        if witness_ok:
            witness_qs.append(q)

    return {
        "generated_qs": generated_qs,
        "witness_qs": sorted(set(int(q) for q in witness_qs)),
        "tail_qs": [int(q) for q in tail_qs],
        "tail_start_q": int(tail_qs[0]),
        "tail_is_suffix_of_generated": True,
        "tail_member_count": int(len(tail_qs)),
        "coherent_upper_lo": float(upper_lo),
        "coherent_upper_hi": float(upper_hi),
        "coherent_upper_width": float(upper_hi - upper_lo),
        "coherent_band_lo": float(band_lo),
        "coherent_band_hi": float(band_hi),
        "coherent_band_width": float(band_hi - band_lo),
        "incompatibility_gap": float(incompat_gap),
        "witnesses": witnesses,
        "theorem_status": "sustained-hyperbolic-tail-strong" if incompat_gap > 0.0 else "sustained-hyperbolic-tail-moderate",
        "notes": "A suffix of the generated ladder is certified by the tail-replacement theorem using a shared anchor upper object and positive local barrier floor; common crossing-window intersection across the anchor rows is not required.",
        "legacy_tail_diagnostics": legacy_tail,
    }


def build_adaptive_incompatibility_atlas_certificate_from_entries(
    entries: Sequence[AdaptiveIncompatibilityAtlasEntry | dict[str, Any]],
    family: HarmonicFamily | None = None,
    *,
    min_tail_members: int = 2,
) -> AdaptiveIncompatibilityAtlasCertificate:
    family = family or HarmonicFamily()
    entry_dicts = [_normalize_adaptive_incompatibility_entry_dict(entry) for entry in entries]
    tail = _build_tail_summary_from_normalized_entries(entry_dicts, min_tail_members=min_tail_members)
    upper_lo = tail.get("coherent_upper_lo")
    upper_hi = tail.get("coherent_upper_hi")
    upper_w = tail.get("coherent_upper_width")
    band_lo = tail.get("coherent_band_lo")
    band_hi = tail.get("coherent_band_hi")
    band_w = tail.get("coherent_band_width")
    gap = tail.get("incompatibility_gap")

    interval_newton_count = sum(1 for e in entry_dicts if (e.get("adaptive_crossing") or {}).get("status") in {"interval_newton", "theorem_mode_local"})
    monotone_count = sum(1 for e in entry_dicts if (e.get("adaptive_crossing") or {}).get("status") in {"interval_newton", "monotone_window", "theorem_mode_local"})
    fully_certified_count = sum(1 for e in entry_dicts if e.get("status") == "adaptive-crossing-plus-band")

    tail_status = str(tail.get("theorem_status", "sustained-hyperbolic-tail-failed"))
    anchor_upper_count = sum(1 for e in entry_dicts if (e.get("crossing_certificate") or {}).get("certification_tier") == "anchor_upper_object")
    if tail_status == "sustained-hyperbolic-tail-strong" and (interval_newton_count + anchor_upper_count) >= max(1, min_tail_members):
        theorem_status = "adaptive-incompatibility-strong"
        notes = (
            "Adaptive branch localization closes theorem-like crossing subwindows on the rational ladder, "
            "and those localized or tail-replaced upper objects feed a sustained hyperbolic tail certificate."
        )
    elif tail_status in {"sustained-hyperbolic-tail-strong", "sustained-hyperbolic-tail-moderate"}:
        theorem_status = "adaptive-incompatibility-moderate"
        notes = (
            "The adaptive upper-side atlas is coherent on a ladder tail, but the localized branch windows "
            "or barrier gap are not yet sharp enough for the strongest status."
        )
    elif fully_certified_count > 0:
        theorem_status = "adaptive-incompatibility-weak"
        notes = (
            "At least one approximant now carries an adaptive crossing-plus-band witness, but the ladder tail "
            "does not yet stabilize into a coherent incompatibility package."
        )
    else:
        theorem_status = "adaptive-incompatibility-failed"
        notes = "The adaptive upper-side atlas did not yet close a usable incompatibility package."

    return AdaptiveIncompatibilityAtlasCertificate(
        family_label=_family_label(family),
        entries=entry_dicts,
        hyperbolic_tail=tail,
        coherent_upper_lo=None if upper_lo is None else float(upper_lo),
        coherent_upper_hi=None if upper_hi is None else float(upper_hi),
        coherent_upper_width=None if upper_w is None else float(upper_w),
        coherent_band_lo=None if band_lo is None else float(band_lo),
        coherent_band_hi=None if band_hi is None else float(band_hi),
        coherent_band_width=None if band_w is None else float(band_w),
        incompatibility_gap=None if gap is None else float(gap),
        interval_newton_count=int(interval_newton_count),
        monotone_count=int(monotone_count),
        fully_certified_count=int(fully_certified_count),
        theorem_status=theorem_status,
        notes=notes,
    )


def build_adaptive_incompatibility_atlas_certificate(
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    crossing_max_depth: int = 5,
    crossing_min_width: float = 5e-4,
    crossing_n_pieces: int = 2,
    band_initial_subdivisions: int = 4,
    band_max_depth: int = 4,
    band_min_width: float = 5e-4,
    min_tail_members: int = 2,
    use_seed_propagation: bool = True,
    use_methodology_frontend: bool = True,
    n_jobs: int = 1,
    parallelism: str = "serial",
) -> AdaptiveIncompatibilityAtlasCertificate:
    family = family or HarmonicFamily()
    entry_kwargs = dict(
        target_residue=target_residue,
        crossing_max_depth=crossing_max_depth,
        crossing_min_width=crossing_min_width,
        crossing_n_pieces=crossing_n_pieces,
        band_initial_subdivisions=band_initial_subdivisions,
        band_max_depth=band_max_depth,
        band_min_width=band_min_width,
        use_seed_propagation=use_seed_propagation,
        use_methodology_frontend=use_methodology_frontend,
    )
    entries: list[AdaptiveIncompatibilityAtlasEntry] = []
    if int(n_jobs) > 1 and parallelism in {"thread", "process"} and len(specs) > 1:
        executor_cls = ThreadPoolExecutor if parallelism == "thread" else ProcessPoolExecutor
        with executor_cls(max_workers=int(n_jobs)) as ex:
            payloads = [{"spec": s.to_dict(), "family": family, "kwargs": entry_kwargs} for s in specs]
            for entry_dict in ex.map(_build_adaptive_incompatibility_entry_worker, payloads):
                entries.append(AdaptiveIncompatibilityAtlasEntry(**entry_dict))
    else:
        local_cache: dict[tuple[int, int, float, float, float, float], AdaptiveIncompatibilityAtlasEntry] = {}
        previous_entry_dicts: list[dict[str, Any]] = []
        for spec in specs:
            key = (
                int(spec.p), int(spec.q),
                round(float(spec.crossing_K_lo), 15), round(float(spec.crossing_K_hi), 15),
                round(float(spec.band_search_lo), 15), round(float(spec.band_search_hi), 15),
            )
            if key not in local_cache:
                local_cache[key] = build_adaptive_incompatibility_entry_certificate(
                    spec, family=family, previous_entry_dicts=previous_entry_dicts, **entry_kwargs
                )
            entry = local_cache[key]
            entries.append(entry)
            previous_entry_dicts.append(entry.to_dict())

    return build_adaptive_incompatibility_atlas_certificate_from_entries(entries, family=family, min_tail_members=min_tail_members)



def build_golden_adaptive_incompatibility_certificate_from_atlas(
    atlas: AdaptiveIncompatibilityAtlasCertificate | dict[str, Any],
    *,
    family: HarmonicFamily | None = None,
    rho: float = 0.0,
    generated_convergents: Sequence[dict[str, Any]] | None = None,
) -> GoldenAdaptiveIncompatibilityCertificate:
    family = family or HarmonicFamily()
    atlas_dict = atlas.to_dict() if isinstance(atlas, AdaptiveIncompatibilityAtlasCertificate) else dict(atlas)
    up_lo = atlas_dict.get("coherent_upper_lo")
    up_hi = atlas_dict.get("coherent_upper_hi")
    up_w = atlas_dict.get("coherent_upper_width")
    band_lo = atlas_dict.get("coherent_band_lo")
    band_hi = atlas_dict.get("coherent_band_hi")
    band_w = atlas_dict.get("coherent_band_width")
    gap = atlas_dict.get("incompatibility_gap")
    atlas_status = str(atlas_dict.get("theorem_status", "adaptive-incompatibility-failed"))
    if atlas_status == "adaptive-incompatibility-strong":
        theorem_status = "golden-adaptive-incompatibility-strong"
        notes = "The golden convergent ladder now supports an adaptive branch-driven incompatibility package with a coherent localized upper object and a coherent hyperbolic barrier."
    elif atlas_status in {"adaptive-incompatibility-moderate", "adaptive-incompatibility-weak"}:
        theorem_status = "golden-adaptive-incompatibility-moderate"
        notes = "The golden convergent ladder now supports an adaptive upper-side package, but the irrational nonexistence bridge remains unfinished."
    else:
        theorem_status = "golden-adaptive-incompatibility-failed"
        notes = "The adaptive golden upper-side package did not yet close on the supplied ladder."
    return GoldenAdaptiveIncompatibilityCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        generated_convergents=[dict(x) for x in (generated_convergents or [])],
        atlas=atlas_dict,
        selected_upper_lo=None if up_lo is None else float(up_lo),
        selected_upper_hi=None if up_hi is None else float(up_hi),
        selected_upper_width=None if up_w is None else float(up_w),
        selected_barrier_lo=None if band_lo is None else float(band_lo),
        selected_barrier_hi=None if band_hi is None else float(band_hi),
        selected_barrier_width=None if band_w is None else float(band_w),
        incompatibility_gap=None if gap is None else float(gap),
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_adaptive_incompatibility_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    crossing_center: float = 0.971635406,
    crossing_half_width: float = 2.5e-3,
    band_offset: float = 5.5e-2,
    band_width: float = 3.0e-2,
    target_residue: float = 0.25,
    crossing_max_depth: int = 5,
    crossing_min_width: float = 5e-4,
    crossing_n_pieces: int = 2,
    band_initial_subdivisions: int = 4,
    band_max_depth: int = 4,
    band_min_width: float = 5e-4,
    min_tail_members: int = 2,
    use_methodology_frontend: bool = True,
) -> GoldenAdaptiveIncompatibilityCertificate:
    family = family or HarmonicFamily()
    specs = generate_golden_convergent_specs(
        rho=rho,
        n_terms=n_terms,
        keep_last=keep_last,
        min_q=min_q,
        max_q=max_q,
        crossing_center=crossing_center,
        crossing_half_width=crossing_half_width,
        band_offset=band_offset,
        band_width=band_width,
    )
    atlas = build_adaptive_incompatibility_atlas_certificate(
        [s.to_approximant_window_spec() for s in specs],
        family=family,
        target_residue=target_residue,
        crossing_max_depth=crossing_max_depth,
        crossing_min_width=crossing_min_width,
        crossing_n_pieces=crossing_n_pieces,
        band_initial_subdivisions=band_initial_subdivisions,
        band_max_depth=band_max_depth,
        band_min_width=band_min_width,
        min_tail_members=min_tail_members,
        use_seed_propagation=True,
        use_methodology_frontend=use_methodology_frontend,
    )

    return build_golden_adaptive_incompatibility_certificate_from_atlas(
        atlas,
        family=family,
        rho=float(specs[-1].rho if specs else (rho if rho is not None else 0.0)),
        generated_convergents=[s.to_dict() for s in specs],
    )


__all__ = [
    "AdaptiveIncompatibilityAtlasEntry",
    "AdaptiveIncompatibilityAtlasCertificate",
    "GoldenAdaptiveIncompatibilityCertificate",
    "build_adaptive_incompatibility_entry_certificate",
    "build_golden_adaptive_incompatibility_certificate_from_atlas",
    "build_adaptive_incompatibility_atlas_certificate_from_entries",
    "build_adaptive_incompatibility_atlas_certificate",
    "build_golden_adaptive_incompatibility_certificate",
]
