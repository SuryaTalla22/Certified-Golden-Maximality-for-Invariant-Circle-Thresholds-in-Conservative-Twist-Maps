from __future__ import annotations

"""Explicit theorem-facing incompatibility bridges for Theorem IV.

Stage 33 produced a stronger upper-side object: a support-profile adaptive tail
coherence certificate. The next theorem-facing move is to compress that object
into an explicit *hypothesis ledger* for the current obstruction theorem front.

This module does not prove irrational nonexistence. It records, in one
machine-readable object, which pieces of the intended obstruction theorem are
already present and which ones still fail.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .adaptive_tail_coherence import build_golden_adaptive_tail_coherence_certificate
from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


@dataclass
class IncompatibilityHypothesisRow:
    name: str
    satisfied: bool
    margin: float | None
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenIncompatibilityTheoremBridgeCertificate:
    rho: float
    family_label: str
    upper_package: dict[str, Any]
    certified_upper_lo: float | None
    certified_upper_hi: float | None
    certified_upper_width: float | None
    certified_barrier_lo: float | None
    certified_barrier_hi: float | None
    certified_barrier_width: float | None
    certified_gap: float | None
    gap_to_localization_ratio: float | None
    certified_tail_qs: list[int]
    certified_tail_start_q: int | None
    certified_tail_is_suffix: bool
    supporting_entry_count: int
    support_fraction_floor: float | None
    entry_coverage_floor: float | None
    hypotheses: list[IncompatibilityHypothesisRow]
    satisfied_hypotheses: list[str]
    missing_hypotheses: list[str]
    bridge_margin: float | None
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho': float(self.rho),
            'family_label': str(self.family_label),
            'upper_package': self.upper_package,
            'certified_upper_lo': self.certified_upper_lo,
            'certified_upper_hi': self.certified_upper_hi,
            'certified_upper_width': self.certified_upper_width,
            'certified_barrier_lo': self.certified_barrier_lo,
            'certified_barrier_hi': self.certified_barrier_hi,
            'certified_barrier_width': self.certified_barrier_width,
            'certified_gap': self.certified_gap,
            'gap_to_localization_ratio': self.gap_to_localization_ratio,
            'certified_tail_qs': [int(x) for x in self.certified_tail_qs],
            'certified_tail_start_q': self.certified_tail_start_q,
            'certified_tail_is_suffix': bool(self.certified_tail_is_suffix),
            'supporting_entry_count': int(self.supporting_entry_count),
            'support_fraction_floor': self.support_fraction_floor,
            'entry_coverage_floor': self.entry_coverage_floor,
            'hypotheses': [h.to_dict() for h in self.hypotheses],
            'satisfied_hypotheses': [str(x) for x in self.satisfied_hypotheses],
            'missing_hypotheses': [str(x) for x in self.missing_hypotheses],
            'bridge_margin': self.bridge_margin,
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


@dataclass
class GoldenTwoSidedIncompatibilityTheoremBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_bridge: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_golden_incompatibility_theorem_bridge_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    min_cluster_size: int = 2,
    min_tail_members: int = 2,
    min_support_fraction: float = 0.75,
    min_entry_coverage: float = 0.75,
    min_gap_to_width_ratio: float = 1.0,
    require_suffix_tail: bool = False,
    adaptive_tail_coherence_certificate: Mapping[str, Any] | None = None,
    **coherence_kwargs,
) -> GoldenIncompatibilityTheoremBridgeCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    if adaptive_tail_coherence_certificate is not None:
        upper = dict(adaptive_tail_coherence_certificate)
    else:
        upper = build_golden_adaptive_tail_coherence_certificate(
            family=family,
            rho=rho,
            min_cluster_size=min_cluster_size,
            min_tail_members=min_tail_members,
            min_q_support_fraction=min_support_fraction,
            min_entry_tail_coverage=min_entry_coverage,
            min_tail_support_fraction=min_support_fraction,
            **coherence_kwargs,
        ).to_dict()

    upper_lo = None if upper.get('stable_upper_lo') is None else float(upper['stable_upper_lo'])
    upper_hi = None if upper.get('stable_upper_hi') is None else float(upper['stable_upper_hi'])
    barrier_lo = None if upper.get('stable_barrier_lo') is None else float(upper['stable_barrier_lo'])
    barrier_hi = None if upper.get('stable_barrier_hi') is None else float(upper['stable_barrier_hi'])
    upper_width = None if upper.get('stable_upper_width') is None else float(upper['stable_upper_width'])
    barrier_width = None if upper.get('stable_barrier_width') is None else float(upper['stable_barrier_width'])
    gap = None if upper.get('stable_incompatibility_gap') is None else float(upper['stable_incompatibility_gap'])
    tail_qs = [int(x) for x in upper.get('coherence_tail_qs', [])]
    tail_start_q = tail_qs[0] if tail_qs else None
    tail_is_suffix = bool(upper.get('coherence_tail_is_suffix_of_generated_union', False))
    supporting_entry_count = len(upper.get('supporting_entry_indices', []))
    support_fraction = upper.get('coherence_tail_support_fraction')
    support_fraction = None if support_fraction is None else float(support_fraction)
    coverage_floor = upper.get('coherence_tail_entry_coverage_floor')
    coverage_floor = None if coverage_floor is None else float(coverage_floor)

    loc_scale = max(1e-12, float(upper_width or 0.0), float(barrier_width or 0.0))
    ratio = None if gap is None else float(gap / loc_scale)

    hypotheses = [
        IncompatibilityHypothesisRow('coherent_upper_object', upper_lo is not None and upper_hi is not None, upper_width, 'adaptive-tail-coherence', 'A coherent upper localization window exists across the supporting adaptive neighborhood.'),
        IncompatibilityHypothesisRow('coherent_hyperbolic_barrier', barrier_lo is not None and barrier_hi is not None, barrier_width, 'adaptive-tail-coherence', 'A coherent hyperbolic barrier window exists across the same adaptive neighborhood.'),
        IncompatibilityHypothesisRow('positive_incompatibility_gap', gap is not None and gap > 0.0, gap, 'adaptive-tail-coherence', 'The coherent barrier begins strictly above the coherent upper localization window.'),
        IncompatibilityHypothesisRow('gap_dominates_localization', ratio is not None and ratio >= float(min_gap_to_width_ratio), None if ratio is None else float(ratio - float(min_gap_to_width_ratio)), 'adaptive-tail-coherence', 'The incompatibility gap is large relative to the localization widths, not merely positive.'),
        IncompatibilityHypothesisRow('supporting_tail_exists', bool(tail_qs), float(len(tail_qs)) if tail_qs else None, 'adaptive-tail-coherence', 'A denominator block/tail survives the neighborhood support-profile refinement.'),
        IncompatibilityHypothesisRow('supporting_cluster_size', supporting_entry_count >= int(min_cluster_size), float(supporting_entry_count - int(min_cluster_size)), 'adaptive-tail-coherence', 'Enough neighboring adaptive atlases support the same theorem-facing upper object.'),
        IncompatibilityHypothesisRow('tail_support_fraction', support_fraction is not None and support_fraction >= float(min_support_fraction), None if support_fraction is None else float(support_fraction - float(min_support_fraction)), 'adaptive-tail-coherence', 'The surviving denominator block is supported by a sufficiently large fraction of the neighborhood subcluster.'),
        IncompatibilityHypothesisRow('tail_entry_coverage_floor', coverage_floor is not None and coverage_floor >= float(min_entry_coverage), None if coverage_floor is None else float(coverage_floor - float(min_entry_coverage)), 'adaptive-tail-coherence', 'Each supporting entry covers enough of the surviving denominator block.'),
        IncompatibilityHypothesisRow('suffix_tail', (not require_suffix_tail) or tail_is_suffix, 1.0 if tail_is_suffix else 0.0, 'adaptive-tail-coherence', 'The surviving denominator block is suffix-stable on the generated union.' if require_suffix_tail else 'Suffix stability is recorded even when not required for the current bridge status.'),
    ]

    satisfied = [row.name for row in hypotheses if row.satisfied]
    missing = [row.name for row in hypotheses if not row.satisfied]
    margin_candidates = [
        gap,
        None if ratio is None else float(ratio - float(min_gap_to_width_ratio)),
        None if support_fraction is None else float(support_fraction - float(min_support_fraction)),
        None if coverage_floor is None else float(coverage_floor - float(min_entry_coverage)),
        float(supporting_entry_count - int(min_cluster_size)),
        float(len(tail_qs) - int(min_tail_members)) if tail_qs else None,
    ]
    if require_suffix_tail:
        margin_candidates.append(1.0 if tail_is_suffix else -1.0)
    finite_margins = [float(x) for x in margin_candidates if x is not None]
    bridge_margin = min(finite_margins) if finite_margins else None

    if all(row.satisfied for row in hypotheses):
        status = 'golden-incompatibility-theorem-bridge-strong'
        notes = 'The current upper obstruction package now closes as an explicit theorem-facing bridge: upper window, barrier, positive gap, localized dominance, and neighborhood-supported denominator tail all hold simultaneously.'
    elif all(row.satisfied for row in hypotheses if row.name != 'suffix_tail') and not require_suffix_tail:
        status = 'golden-incompatibility-theorem-bridge-strong'
        notes = 'All core obstruction-bridge hypotheses hold simultaneously. Suffix stability is recorded but not required in this run.'
    elif all(name in satisfied for name in ['coherent_upper_object', 'coherent_hyperbolic_barrier', 'positive_incompatibility_gap', 'supporting_tail_exists', 'supporting_cluster_size']):
        status = 'golden-incompatibility-theorem-bridge-moderate'
        notes = 'The obstruction front now has an explicit bridge ledger with a coherent upper/barrier pair and a supported denominator block, but one or more quantitative margins remain subcritical.'
    elif all(name in satisfied for name in ['coherent_upper_object', 'coherent_hyperbolic_barrier', 'positive_incompatibility_gap']):
        status = 'golden-incompatibility-theorem-bridge-weak'
        notes = 'A coherent upper/barrier pair with positive gap exists, but denominator-tail support is not yet strong enough for the full bridge package.'
    elif 'coherent_upper_object' in satisfied and 'coherent_hyperbolic_barrier' in satisfied:
        status = 'golden-incompatibility-theorem-bridge-fragile'
        notes = 'The bridge retains a coherent upper/barrier pair, but the explicit incompatibility hypotheses do not yet close beyond localization.'
    else:
        status = 'golden-incompatibility-theorem-bridge-failed'
        notes = 'The current adaptive upper package does not yet support an explicit theorem-facing incompatibility bridge.'

    return GoldenIncompatibilityTheoremBridgeCertificate(
        rho=float(rho), family_label=_family_label(family), upper_package=upper,
        certified_upper_lo=upper_lo, certified_upper_hi=upper_hi, certified_upper_width=upper_width,
        certified_barrier_lo=barrier_lo, certified_barrier_hi=barrier_hi, certified_barrier_width=barrier_width,
        certified_gap=gap, gap_to_localization_ratio=ratio, certified_tail_qs=tail_qs,
        certified_tail_start_q=tail_start_q, certified_tail_is_suffix=tail_is_suffix,
        supporting_entry_count=int(supporting_entry_count), support_fraction_floor=support_fraction,
        entry_coverage_floor=coverage_floor, hypotheses=hypotheses,
        satisfied_hypotheses=satisfied, missing_hypotheses=missing, bridge_margin=bridge_margin,
        theorem_status=status, notes=notes,
    )


def build_golden_two_sided_incompatibility_theorem_bridge_certificate(
    K_values: Sequence[float], family: HarmonicFamily | None = None, *, rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128), sigma_cap: float = 0.04,
    use_multiresolution: bool = True, oversample_factor: int = 8, **bridge_kwargs,
) -> GoldenTwoSidedIncompatibilityTheoremBridgeCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    lower = continue_golden_aposteriori_certificates(
        K_values=K_values, family=family, rho=rho, N_values=N_values, sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution, oversample_factor=oversample_factor,
    ).to_dict()
    upper = build_golden_incompatibility_theorem_bridge_certificate(family=family, rho=rho, **bridge_kwargs).to_dict()
    lower_bound = lower.get('last_stable_K') if lower.get('last_stable_K') is not None else lower.get('last_success_K')
    upper_lo = upper.get('certified_upper_lo')
    barrier_lo = upper.get('certified_barrier_lo')
    gap_to_upper = None if lower_bound is None or upper_lo is None else float(upper_lo - float(lower_bound))
    gap_to_barrier = None if lower_bound is None or barrier_lo is None else float(barrier_lo - float(lower_bound))
    relation = {
        'lower_bound': None if lower_bound is None else float(lower_bound),
        'upper_crossing_lo': None if upper_lo is None else float(upper_lo),
        'upper_crossing_hi': None if upper.get('certified_upper_hi') is None else float(upper['certified_upper_hi']),
        'upper_barrier_lo': None if barrier_lo is None else float(barrier_lo),
        'upper_barrier_hi': None if upper.get('certified_barrier_hi') is None else float(upper['certified_barrier_hi']),
        'gap_to_upper': gap_to_upper,
        'gap_to_barrier': gap_to_barrier,
        'tail_qs': [int(x) for x in upper.get('certified_tail_qs', [])],
        'tail_is_suffix': bool(upper.get('certified_tail_is_suffix', False)),
        'bridge_margin': upper.get('bridge_margin'),
        'upper_status': str(upper.get('theorem_status', 'unknown')),
        'missing_hypotheses': [str(x) for x in upper.get('missing_hypotheses', [])],
    }
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        if str(upper.get('theorem_status')) == 'golden-incompatibility-theorem-bridge-strong':
            status = 'golden-two-sided-incompatibility-theorem-bridge-strong'
            notes = 'The lower golden a-posteriori side now lies strictly below an explicit theorem-facing upper incompatibility bridge.'
        else:
            status = 'golden-two-sided-incompatibility-theorem-bridge-partial'
            notes = 'The lower golden a-posteriori side separates from the current explicit upper bridge, but some upper obstruction hypotheses remain quantitatively open.'
    else:
        status = 'golden-two-sided-incompatibility-theorem-bridge-incomplete'
        notes = 'The current explicit upper bridge does not yet separate cleanly from the lower a-posteriori side.'
    return GoldenTwoSidedIncompatibilityTheoremBridgeCertificate(
        rho=float(rho), family_label=_family_label(family), lower_side=lower, upper_bridge=upper,
        relation=relation, theorem_status=status, notes=notes,
    )


__all__ = [
    'IncompatibilityHypothesisRow',
    'GoldenIncompatibilityTheoremBridgeCertificate',
    'GoldenTwoSidedIncompatibilityTheoremBridgeCertificate',
    'build_golden_incompatibility_theorem_bridge_certificate',
    'build_golden_two_sided_incompatibility_theorem_bridge_certificate',
]
