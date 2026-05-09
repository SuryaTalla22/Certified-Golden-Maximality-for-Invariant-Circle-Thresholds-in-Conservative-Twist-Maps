from __future__ import annotations

"""Theorem IV theorem-facing obstruction packages.

The current repository already has a rich upper-side bridge: obstruction atlases,
localized upper objects, support audits, and neighborhood-level tail stability.
What it has lacked is one compact package stating the sharpest obstruction-side
claim the code can currently make.

This module provides that package.  It does **not** claim a finished irrational
nonexistence theorem.  Instead it upgrades the obstruction side from scattered
bridge layers into a single incompatibility-oriented certificate.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Sequence

from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .adaptive_incompatibility import build_golden_adaptive_incompatibility_certificate
from .adaptive_tail_stability import build_golden_adaptive_tail_stability_certificate
from .adaptive_tail_coherence import build_golden_adaptive_tail_coherence_certificate
from .incompatibility_theorem_bridge import build_golden_incompatibility_theorem_bridge_certificate
from .incompatibility_bridge_profile import build_golden_incompatibility_bridge_profile_certificate
from .incompatibility_strict_bridge import build_golden_incompatibility_strict_bridge_certificate
from .adaptive_support_core_neighborhood import build_golden_adaptive_support_core_neighborhood_certificate
from .adaptive_tail_aware_neighborhood import build_golden_adaptive_tail_aware_neighborhood_certificate
from .nonexistence_front import build_golden_nonexistence_front_certificate
from .golden_supercritical import build_golden_supercritical_obstruction_certificate
from .golden_supercritical_continuation import build_golden_supercritical_continuation_certificate
from .golden_upper_support_audit import build_golden_upper_support_audit_certificate
from .golden_upper_tail_stability import build_golden_upper_tail_stability_certificate
from .hyperbolicity_certifier import certify_sustained_hyperbolic_tail
from .obstruction_atlas import ApproximantWindowSpec, build_multi_approximant_obstruction_atlas
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


@dataclass
class PeriodicLadderIncompatibilityCertificate:
    family_label: str
    atlas: dict[str, Any]
    hyperbolic_tail: dict[str, Any]
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_band_lo: float | None
    selected_band_hi: float | None
    incompatibility_gap: float | None
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenIrrationalIncompatibilityCertificate:
    rho: float
    family_label: str
    base_obstruction: dict[str, Any]
    continuation: dict[str, Any]
    support_audit: dict[str, Any]
    tail_stability: dict[str, Any]
    adaptive_upper_package: dict[str, Any]
    adaptive_tail_stability: dict[str, Any]
    adaptive_tail_coherence: dict[str, Any]
    ladder_hyperbolic_tail: dict[str, Any]
    theorem_bridge: dict[str, Any]
    theorem_bridge_promotion: dict[str, Any]
    support_core_neighborhood: dict[str, Any]
    tail_aware_neighborhood: dict[str, Any]
    theorem_bridge_profile: dict[str, Any]
    nonexistence_front: dict[str, Any]
    selected_upper_source: str
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_upper_width: float | None
    selected_barrier_source: str
    selected_barrier_lo: float | None
    selected_barrier_hi: float | None
    selected_tail_qs: list[int]
    selected_tail_is_suffix: bool
    incompatibility_gap: float | None
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "base_obstruction": dict(self.base_obstruction),
            "continuation": dict(self.continuation),
            "support_audit": dict(self.support_audit),
            "tail_stability": dict(self.tail_stability),
            "adaptive_upper_package": dict(self.adaptive_upper_package),
            "adaptive_tail_stability": dict(self.adaptive_tail_stability),
            "adaptive_tail_coherence": dict(self.adaptive_tail_coherence),
            "ladder_hyperbolic_tail": dict(self.ladder_hyperbolic_tail),
            "theorem_bridge": dict(self.theorem_bridge),
            "theorem_bridge_promotion": dict(self.theorem_bridge_promotion),
            "support_core_neighborhood": dict(self.support_core_neighborhood),
            "tail_aware_neighborhood": dict(self.tail_aware_neighborhood),
            "theorem_bridge_profile": dict(self.theorem_bridge_profile),
            "nonexistence_front": dict(self.nonexistence_front),
            "selected_upper_source": str(self.selected_upper_source),
            "selected_upper_lo": self.selected_upper_lo,
            "selected_upper_hi": self.selected_upper_hi,
            "selected_upper_width": self.selected_upper_width,
            "selected_barrier_source": str(self.selected_barrier_source),
            "selected_barrier_lo": self.selected_barrier_lo,
            "selected_barrier_hi": self.selected_barrier_hi,
            "selected_tail_qs": [int(x) for x in self.selected_tail_qs],
            "selected_tail_is_suffix": bool(self.selected_tail_is_suffix),
            "incompatibility_gap": self.incompatibility_gap,
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


@dataclass
class GoldenTwoSidedIncompatibilityBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_periodic_ladder_incompatibility_certificate(
    specs: Sequence[ApproximantWindowSpec],
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    min_tail_members: int = 2,
) -> PeriodicLadderIncompatibilityCertificate:
    family = family or HarmonicFamily()
    atlas = build_multi_approximant_obstruction_atlas(
        specs=specs,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()
    tail = certify_sustained_hyperbolic_tail(atlas, min_tail_members=min_tail_members).to_dict()
    gap = tail.get("incompatibility_gap")
    if tail["theorem_status"] == "sustained-hyperbolic-tail-strong":
        status = "periodic-ladder-incompatibility-strong"
        notes = "The rational ladder carries a sustained hyperbolic tail with a coherent barrier above a coherent crossing object. This is the sharpest current ladder-level obstruction package."
    elif tail["theorem_status"] == "sustained-hyperbolic-tail-moderate":
        status = "periodic-ladder-incompatibility-moderate"
        notes = "The rational ladder carries a sustained hyperbolic tail, but the barrier gap is not yet fully sharp."
    elif tail["theorem_status"] == "sustained-hyperbolic-tail-weak":
        status = "periodic-ladder-incompatibility-weak"
        notes = "The rational ladder supplies some crossing-plus-band witnesses, but they do not yet stabilize into a tail certificate."
    else:
        status = "periodic-ladder-incompatibility-failed"
        notes = "The current rational ladder did not yet close an incompatibility-oriented hyperbolic tail package."
    return PeriodicLadderIncompatibilityCertificate(
        family_label=_family_label(family),
        atlas=atlas,
        hyperbolic_tail=tail,
        selected_upper_lo=tail.get("coherent_upper_lo"),
        selected_upper_hi=tail.get("coherent_upper_hi"),
        selected_band_lo=tail.get("coherent_band_lo"),
        selected_band_hi=tail.get("coherent_band_hi"),
        incompatibility_gap=(None if gap is None else float(gap)),
        theorem_status=status,
        notes=notes,
    )


def _filter_kwargs(fn, kwargs: dict[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    return {k: v for k, v in kwargs.items() if k in params}


def _pick_first_available(*candidates: tuple[str, Any, Any]) -> tuple[str, float | None, float | None]:
    for name, lo, hi in candidates:
        if lo is not None and hi is not None:
            return str(name), float(lo), float(hi)
    return "none", None, None


def _status_rank(status: str) -> int:
    if str(status).endswith('-strong'):
        return 4
    if str(status).endswith('-moderate'):
        return 3
    if str(status).endswith('-weak'):
        return 2
    if str(status).endswith('-fragile'):
        return 1
    return 0


def _bridge_like_from_adaptive_coherence(adaptive_coherence: dict[str, Any]) -> dict[str, Any]:
    upper_lo = adaptive_coherence.get('stable_upper_lo')
    upper_hi = adaptive_coherence.get('stable_upper_hi')
    upper_width = adaptive_coherence.get('stable_upper_width')
    barrier_lo = adaptive_coherence.get('stable_barrier_lo')
    barrier_hi = adaptive_coherence.get('stable_barrier_hi')
    barrier_width = adaptive_coherence.get('stable_barrier_width')
    gap = adaptive_coherence.get('stable_incompatibility_gap')
    tail_qs = [int(x) for x in adaptive_coherence.get('coherence_tail_qs', [])]
    tail_is_suffix = bool(adaptive_coherence.get('coherence_tail_is_suffix_of_generated_union', False))
    supporting_entry_count = len(adaptive_coherence.get('supporting_entry_indices', []))
    support_fraction = adaptive_coherence.get('coherence_tail_support_fraction')
    entry_coverage = adaptive_coherence.get('coherence_tail_entry_coverage_floor')
    loc_scale = max(1e-12, float(upper_width or 0.0), float(barrier_width or 0.0))
    ratio = None if gap is None else float(float(gap) / loc_scale)

    missing: list[str] = []
    if not (upper_lo is not None and upper_hi is not None):
        missing.append('coherent_upper_object')
    if not (barrier_lo is not None and barrier_hi is not None):
        missing.append('coherent_hyperbolic_barrier')
    if not (gap is not None and float(gap) > 0.0):
        missing.append('positive_incompatibility_gap')
    if not (ratio is not None and float(ratio) >= 1.0):
        missing.append('gap_dominates_localization')
    if not tail_qs:
        missing.append('supporting_tail_exists')
    if supporting_entry_count < 2:
        missing.append('supporting_cluster_size')
    if support_fraction is None or float(support_fraction) < 0.75:
        missing.append('tail_support_fraction')
    if entry_coverage is None or float(entry_coverage) < 0.75:
        missing.append('tail_entry_coverage_floor')

    if not missing and str(adaptive_coherence.get('theorem_status', '')).endswith('-strong'):
        status = 'golden-incompatibility-theorem-bridge-strong'
    elif upper_lo is not None and barrier_lo is not None and tail_qs:
        status = 'golden-incompatibility-theorem-bridge-moderate'
    elif upper_lo is not None:
        status = 'golden-incompatibility-theorem-bridge-weak'
    else:
        status = 'golden-incompatibility-theorem-bridge-failed'

    margin_candidates = [
        gap,
        None if ratio is None else float(ratio - 1.0),
        None if support_fraction is None else float(support_fraction - 0.75),
        None if entry_coverage is None else float(entry_coverage - 0.75),
        float(supporting_entry_count - 2),
        float(len(tail_qs) - 2) if tail_qs else None,
    ]
    finite = [float(x) for x in margin_candidates if x is not None]
    bridge_margin = min(finite) if finite else None

    return {
        'rho': None,
        'family_label': 'coherence-reuse',
        'source_name': 'adaptive-tail-coherence',
        'upper_package': adaptive_coherence,
        'certified_upper_lo': upper_lo,
        'certified_upper_hi': upper_hi,
        'certified_upper_width': upper_width,
        'certified_barrier_lo': barrier_lo,
        'certified_barrier_hi': barrier_hi,
        'certified_barrier_width': barrier_width,
        'certified_gap': gap,
        'gap_to_localization_ratio': ratio,
        'certified_tail_qs': tail_qs,
        'certified_tail_start_q': tail_qs[0] if tail_qs else None,
        'certified_tail_is_suffix': tail_is_suffix,
        'supporting_entry_count': supporting_entry_count,
        'support_fraction_floor': support_fraction,
        'entry_coverage_floor': entry_coverage,
        'hypotheses': [],
        'satisfied_hypotheses': [],
        'missing_hypotheses': missing,
        'bridge_margin': bridge_margin,
        'theorem_status': status,
        'notes': 'Bridge-like ledger reused from the already constructed adaptive tail-coherence object.',
    }


def build_golden_irrational_incompatibility_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    min_tail_members: int = 2,
    **upper_kwargs,
) -> GoldenIrrationalIncompatibilityCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    base = build_golden_supercritical_obstruction_certificate(
        family=family, rho=rho, **_filter_kwargs(build_golden_supercritical_obstruction_certificate, upper_kwargs)
    ).to_dict()
    continuation = build_golden_supercritical_continuation_certificate(
        family=family, rho=rho, **_filter_kwargs(build_golden_supercritical_continuation_certificate, upper_kwargs)
    ).to_dict()
    support = build_golden_upper_support_audit_certificate(
        family=family, rho=rho, **_filter_kwargs(build_golden_upper_support_audit_certificate, upper_kwargs)
    ).to_dict()
    tail_kwargs = dict(_filter_kwargs(build_golden_upper_tail_stability_certificate, upper_kwargs))
    tail_kwargs.setdefault("min_stable_tail_members", min_tail_members)
    tail = build_golden_upper_tail_stability_certificate(
        family=family, rho=rho, **tail_kwargs
    ).to_dict()
    adaptive = build_golden_adaptive_incompatibility_certificate(
        family=family, rho=rho, min_tail_members=min_tail_members, **_filter_kwargs(build_golden_adaptive_incompatibility_certificate, upper_kwargs)
    ).to_dict()
    adaptive_tail = build_golden_adaptive_tail_stability_certificate(
        family=family, rho=rho, min_stable_tail_members=min_tail_members, **_filter_kwargs(build_golden_adaptive_tail_stability_certificate, upper_kwargs)
    ).to_dict()
    adaptive_coherence = build_golden_adaptive_tail_coherence_certificate(
        family=family, rho=rho, min_tail_members=min_tail_members, **_filter_kwargs(build_golden_adaptive_tail_coherence_certificate, upper_kwargs)
    ).to_dict()
    reuse_bridge = bool(upper_kwargs.get('reuse_existing_coherence_for_bridge', True))
    if reuse_bridge and _status_rank(str(adaptive_coherence.get('theorem_status', ''))) >= 3:
        theorem_bridge = _bridge_like_from_adaptive_coherence(adaptive_coherence)
    else:
        theorem_bridge = build_golden_incompatibility_theorem_bridge_certificate(
            family=family, rho=rho, min_tail_members=min_tail_members, **_filter_kwargs(build_golden_incompatibility_theorem_bridge_certificate, upper_kwargs)
        ).to_dict()
    theorem_bridge_promotion: dict[str, Any] = {}
    if _status_rank(str(theorem_bridge.get('theorem_status', ''))) <= 2 or bool(upper_kwargs.get('force_strict_bridge_promotion', False)):
        theorem_bridge_promotion = build_golden_incompatibility_strict_bridge_certificate(
            family=family, rho=rho, min_tail_members=min_tail_members, **_filter_kwargs(build_golden_incompatibility_strict_bridge_certificate, upper_kwargs)
        ).to_dict()
        if _status_rank(str(theorem_bridge_promotion.get('theorem_status', ''))) > _status_rank(str(theorem_bridge.get('theorem_status', ''))):
            theorem_bridge = dict(theorem_bridge_promotion)
    support_core_neighborhood: dict[str, Any] = {}
    if _status_rank(str(theorem_bridge.get('theorem_status', ''))) <= 2 or bool(upper_kwargs.get('force_support_core_neighborhood', False)):
        support_core_neighborhood = build_golden_adaptive_support_core_neighborhood_certificate(
            family=family, rho=rho, min_tail_members=min_tail_members, **_filter_kwargs(build_golden_adaptive_support_core_neighborhood_certificate, upper_kwargs)
        ).to_dict()
        candidate_bridge = dict(support_core_neighborhood.get('selected_bridge', {}) or {})
        if _status_rank(str(candidate_bridge.get('theorem_status', ''))) > _status_rank(str(theorem_bridge.get('theorem_status', ''))):
            theorem_bridge = candidate_bridge
    tail_aware_neighborhood: dict[str, Any] = {}
    if _status_rank(str(theorem_bridge.get('theorem_status', ''))) <= 2 or bool(upper_kwargs.get('force_tail_aware_neighborhood', False)):
        tail_aware_neighborhood = build_golden_adaptive_tail_aware_neighborhood_certificate(
            family=family, rho=rho, min_tail_members=min_tail_members, **_filter_kwargs(build_golden_adaptive_tail_aware_neighborhood_certificate, upper_kwargs)
        ).to_dict()
        candidate_bridge = dict(tail_aware_neighborhood.get('selected_bridge', {}) or {})
        if _status_rank(str(candidate_bridge.get('theorem_status', ''))) > _status_rank(str(theorem_bridge.get('theorem_status', ''))):
            theorem_bridge = candidate_bridge
    theorem_bridge_profile: dict[str, Any] = {}
    if _status_rank(str(theorem_bridge.get('theorem_status', ''))) <= 2 or bool(upper_kwargs.get('force_bridge_profile', False)):
        theorem_bridge_profile = build_golden_incompatibility_bridge_profile_certificate(
            family=family, rho=rho, min_tail_members=min_tail_members, **_filter_kwargs(build_golden_incompatibility_bridge_profile_certificate, upper_kwargs)
        ).to_dict()
        prof_bridge = theorem_bridge_profile.get('selected_bridge', {}) or {}
        if _status_rank(str(prof_bridge.get('theorem_status', ''))) > _status_rank(str(theorem_bridge.get('theorem_status', ''))):
            theorem_bridge = dict(prof_bridge)
    nonexistence_front: dict[str, Any] = {}
    base_K_values = upper_kwargs.get("base_K_values")
    if base_K_values is not None:
        try:
            nonexistence_front = build_golden_nonexistence_front_certificate(
                base_K_values=base_K_values,
                family=family,
                rho=rho,
                min_tail_members=min_tail_members,
                **_filter_kwargs(build_golden_nonexistence_front_certificate, upper_kwargs),
            ).to_dict()
        except Exception:
            nonexistence_front = {
                "theorem_status": "golden-nonexistence-front-failed",
                "notes": "Automatic nonexistence-front assembly failed inside the upper-side summary.",
            }
    ladder_tail = certify_sustained_hyperbolic_tail(base.get("ladder", {}), min_tail_members=min_tail_members).to_dict()

    theorem_bridge_source = str(theorem_bridge.get('source_name', 'incompatibility-theorem-bridge'))
    upper_source, upper_lo, upper_hi = _pick_first_available(
        (theorem_bridge_source, theorem_bridge.get("certified_upper_lo"), theorem_bridge.get("certified_upper_hi")),
        ("adaptive-tail-coherence", adaptive_coherence.get("stable_upper_lo"), adaptive_coherence.get("stable_upper_hi")),
        ("adaptive-tail-stability", adaptive_tail.get("stable_upper_lo"), adaptive_tail.get("stable_upper_hi")),
        ("adaptive-upper-package", adaptive.get("selected_upper_lo"), adaptive.get("selected_upper_hi")),
        ("tail-stability", tail.get("stable_upper_lo"), tail.get("stable_upper_hi")),
        ("support-audit", support.get("audited_upper_lo"), support.get("audited_upper_hi")),
        ("continuation", continuation.get("stable_upper_lo"), continuation.get("stable_upper_hi")),
        (str(base.get("selected_upper_source", "base-obstruction")), base.get("selected_upper_lo"), base.get("selected_upper_hi")),
        ("hyperbolic-tail", ladder_tail.get("coherent_upper_lo"), ladder_tail.get("coherent_upper_hi")),
    )
    barrier_source, barrier_lo, barrier_hi = _pick_first_available(
        (theorem_bridge_source, theorem_bridge.get("certified_barrier_lo"), theorem_bridge.get("certified_barrier_hi")),
        ("adaptive-tail-coherence", adaptive_coherence.get("stable_barrier_lo"), adaptive_coherence.get("stable_barrier_hi")),
        ("adaptive-tail-stability", adaptive_tail.get("stable_barrier_lo"), adaptive_tail.get("stable_barrier_hi")),
        ("adaptive-upper-package", adaptive.get("selected_barrier_lo"), adaptive.get("selected_barrier_hi")),
        ("tail-stability", tail.get("stable_band_lo"), tail.get("stable_band_hi")),
        ("support-audit", support.get("audited_band_lo"), support.get("audited_band_hi")),
        ("continuation", continuation.get("stable_band_lo"), continuation.get("stable_band_hi")),
        ("base-obstruction", base.get("earliest_hyperbolic_band_lo"), base.get("latest_hyperbolic_band_hi")),
        ("hyperbolic-tail", ladder_tail.get("coherent_band_lo"), ladder_tail.get("coherent_band_hi")),
    )
    upper_w = None if upper_lo is None or upper_hi is None else float(upper_hi - upper_lo)
    gap = None if upper_hi is None or barrier_lo is None else float(barrier_lo - upper_hi)

    tail_qs = theorem_bridge.get("certified_tail_qs") or adaptive_coherence.get("coherence_tail_qs") or adaptive_tail.get("stable_tail_qs") or tail.get("stable_tail_qs") or adaptive.get("atlas", {}).get("hyperbolic_tail", {}).get("tail_qs") or support.get("robust_tail_qs") or ladder_tail.get("tail_qs") or support.get("robust_qs") or []
    tail_is_suffix = bool(theorem_bridge.get("certified_tail_is_suffix", False) or adaptive_coherence.get("coherence_tail_is_suffix_of_generated_union", False) or adaptive_tail.get("stable_tail_is_suffix_of_generated_union", False) or tail.get("stable_tail_is_suffix_of_generated_union", False) or adaptive.get("atlas", {}).get("hyperbolic_tail", {}).get("tail_is_suffix_of_generated", False) or support.get("tail_is_suffix_of_generated", False) or ladder_tail.get("tail_is_suffix_of_generated", False))

    if theorem_bridge.get("theorem_status") == "golden-incompatibility-theorem-bridge-strong":
        status = "golden-irrational-incompatibility-strong"
        notes = "The golden upper-side obstruction now closes through an explicit theorem-facing incompatibility bridge: the coherent upper object, coherent barrier, quantitative gap, and supported denominator tail are packaged in one machine-readable ledger."
    elif upper_lo is not None and barrier_lo is not None and gap is not None and gap > 0.0 and tail_qs and tail_is_suffix:
        status = "golden-irrational-incompatibility-strong"
        notes = "The golden upper-side obstruction now closes as a theorem-facing incompatibility package: a coherent upper object sits strictly below a coherent hyperbolic barrier, and the supporting denominator tail is suffix-stable."
    elif upper_lo is not None and barrier_lo is not None and tail_qs:
        status = "golden-irrational-incompatibility-moderate"
        notes = "The golden upper side has a coherent upper object, a coherent barrier, and denominator-tail support, but the strict incompatibility gap is not yet uniformly sharp."
    elif upper_lo is not None and (tail_qs or ladder_tail.get("witness_qs")):
        status = "golden-irrational-incompatibility-weak"
        notes = "The golden upper side supplies a usable incompatibility-oriented obstruction package, but it remains only partially stabilized."
    elif upper_lo is not None:
        status = "golden-irrational-incompatibility-fragile"
        notes = "A coherent golden upper object exists, but support and barrier stabilization are still fragile."
    else:
        status = "golden-irrational-incompatibility-failed"
        notes = "The golden upper-side bridge did not yet compress into a usable incompatibility package."

    return GoldenIrrationalIncompatibilityCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        base_obstruction=base,
        continuation=continuation,
        support_audit=support,
        tail_stability=tail,
        adaptive_upper_package=adaptive,
        adaptive_tail_stability=adaptive_tail,
        adaptive_tail_coherence=adaptive_coherence,
        ladder_hyperbolic_tail=ladder_tail,
        theorem_bridge=theorem_bridge,
        theorem_bridge_promotion=theorem_bridge_promotion,
        support_core_neighborhood=support_core_neighborhood,
        tail_aware_neighborhood=tail_aware_neighborhood,
        theorem_bridge_profile=theorem_bridge_profile,
        nonexistence_front=nonexistence_front,
        selected_upper_source=str(upper_source),
        selected_upper_lo=upper_lo,
        selected_upper_hi=upper_hi,
        selected_upper_width=upper_w,
        selected_barrier_source=str(barrier_source),
        selected_barrier_lo=barrier_lo,
        selected_barrier_hi=barrier_hi,
        selected_tail_qs=[int(x) for x in tail_qs],
        selected_tail_is_suffix=bool(tail_is_suffix),
        incompatibility_gap=gap,
        theorem_status=status,
        notes=notes,
    )


def build_golden_two_sided_incompatibility_bridge_certificate(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    min_tail_members: int = 2,
    **upper_kwargs,
) -> GoldenTwoSidedIncompatibilityBridgeCertificate:
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
    upper = build_golden_irrational_incompatibility_certificate(
        family=family,
        rho=rho,
        min_tail_members=min_tail_members,
        **upper_kwargs,
    ).to_dict()
    lower_bound = lower.get("last_stable_K") if lower.get("last_stable_K") is not None else lower.get("last_success_K")
    upper_lo = upper.get("selected_upper_lo")
    barrier_lo = upper.get("selected_barrier_lo")
    gap_to_upper = None if lower_bound is None or upper_lo is None else float(upper_lo - float(lower_bound))
    gap_to_barrier = None if lower_bound is None or barrier_lo is None else float(barrier_lo - float(lower_bound))
    nonexistence_front = build_golden_nonexistence_front_certificate(
        base_K_values=K_values,
        family=family,
        rho=rho,
        min_tail_members=min_tail_members,
        **_filter_kwargs(build_golden_nonexistence_front_certificate, upper_kwargs),
    ).to_dict()
    relation = {
        "lower_bound": None if lower_bound is None else float(lower_bound),
        "upper_crossing_lo": None if upper_lo is None else float(upper_lo),
        "upper_crossing_hi": None if upper.get("selected_upper_hi") is None else float(upper["selected_upper_hi"]),
        "upper_barrier_lo": None if barrier_lo is None else float(barrier_lo),
        "upper_barrier_hi": None if upper.get("selected_barrier_hi") is None else float(upper["selected_barrier_hi"]),
        "upper_object_source": str(upper.get("selected_upper_source", "none")),
        "upper_barrier_source": str(upper.get("selected_barrier_source", "none")),
        "gap_to_upper": gap_to_upper,
        "gap_to_barrier": gap_to_barrier,
        "tail_qs": [int(x) for x in upper.get("selected_tail_qs", [])],
        "tail_is_suffix": bool(upper.get("selected_tail_is_suffix", False)),
        "upper_status": str(upper.get("theorem_status", "unknown")),
        "nonexistence_front_status": str(nonexistence_front.get("theorem_status", "unknown")),
        "nonexistence_front_margin": nonexistence_front.get("computational_front_margin"),
        "remaining_analytic_lifts": [str(x.get("name", x)) for x in nonexistence_front.get("remaining_analytic_lifts", [])],
    }
    if nonexistence_front.get("theorem_status") == "golden-nonexistence-front-strong":
        status = "golden-two-sided-incompatibility-strong"
        notes = "The strongest current lower neighborhood object and upper incompatibility theorem bridge now assemble into a sharp two-sided nonexistence front."
    elif lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        if upper.get("theorem_status") == "golden-irrational-incompatibility-strong":
            status = "golden-two-sided-incompatibility-strong"
            notes = "The lower golden a-posteriori side now sits strictly below a theorem-facing upper incompatibility package. This is the sharpest current two-sided golden bridge in the code."
        else:
            status = "golden-two-sided-incompatibility-partial"
            notes = "The lower golden a-posteriori side lies below the current upper incompatibility package, but the upper theorem package is not yet at its strongest status."
    else:
        status = "golden-two-sided-incompatibility-incomplete"
        notes = "The lower golden side does not yet separate cleanly from the current upper incompatibility package."
    return GoldenTwoSidedIncompatibilityBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=status,
        notes=notes,
    )


__all__ = [
    "PeriodicLadderIncompatibilityCertificate",
    "GoldenIrrationalIncompatibilityCertificate",
    "GoldenTwoSidedIncompatibilityBridgeCertificate",
    "build_periodic_ladder_incompatibility_certificate",
    "build_golden_irrational_incompatibility_certificate",
    "build_golden_two_sided_incompatibility_bridge_certificate",
]
