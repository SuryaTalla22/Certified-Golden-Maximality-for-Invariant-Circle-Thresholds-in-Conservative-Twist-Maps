from __future__ import annotations

"""Conditional theorem packaging for the final analytic lift in Theorem IV.

The stage-39 nonexistence front now separates two different layers clearly:
1. computational/front hypotheses already assembled from current certificates, and
2. the final analytic lifts still needed before a genuine irrational nonexistence
   theorem can be claimed.

This module turns that separation into a single theorem-facing object.  It does
not pretend that the remaining analytic implications are proved; instead it
records exactly which front hypotheses are already discharged and which final
assumptions would promote the current nonexistence front into a conditional
Theorem-IV-style statement.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .nonexistence_front import (
    _default_remaining_analytic_lifts,
    build_golden_nonexistence_front_certificate,
)
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _front_rank(status: str) -> int:
    if str(status).endswith('-strong'):
        return 4
    if str(status).endswith('-moderate'):
        return 3
    if str(status).endswith('-weak'):
        return 2
    if str(status).endswith('-fragile'):
        return 1
    return 0


@dataclass
class AnalyticLiftHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalyticLiftAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenAnalyticIncompatibilityLiftCertificate:
    rho: float
    family_label: str
    nonexistence_front: dict[str, Any]
    contradiction_summary: dict[str, Any]
    supercritical_obstruction_locked: bool
    support_geometry_certified: bool
    tail_coherence_certified: bool
    tail_stability_certified: bool
    nonexistence_contradiction_certified: bool
    analytic_incompatibility_certified: bool
    hypotheses: list[AnalyticLiftHypothesisRow]
    assumptions: list[AnalyticLiftAssumptionRow]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    active_assumptions: list[str]
    residual_iv_burden: list[str]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "nonexistence_front": dict(self.nonexistence_front),
            "contradiction_summary": dict(self.contradiction_summary),
            "supercritical_obstruction_locked": bool(self.supercritical_obstruction_locked),
            "support_geometry_certified": bool(self.support_geometry_certified),
            "tail_coherence_certified": bool(self.tail_coherence_certified),
            "tail_stability_certified": bool(self.tail_stability_certified),
            "nonexistence_contradiction_certified": bool(self.nonexistence_contradiction_certified),
            "analytic_incompatibility_certified": bool(self.analytic_incompatibility_certified),
            "hypotheses": [row.to_dict() for row in self.hypotheses],
            "assumptions": [row.to_dict() for row in self.assumptions],
            "discharged_hypotheses": [str(x) for x in self.discharged_hypotheses],
            "open_hypotheses": [str(x) for x in self.open_hypotheses],
            "active_assumptions": [str(x) for x in self.active_assumptions],
            "residual_iv_burden": [str(x) for x in self.residual_iv_burden],
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


def _build_assumptions(
    *,
    assume_final_function_space_promotion: bool,
    assume_obstruction_excludes_analytic_circle: bool,
    assume_universality_embedding: bool,
) -> list[AnalyticLiftAssumptionRow]:
    assumption_map = {
        "obstruction_implies_no_analytic_circle": bool(assume_obstruction_excludes_analytic_circle),
        "final_function_space_promotion": bool(assume_final_function_space_promotion),
        "universality_class_embedding": bool(assume_universality_embedding),
    }
    rows: list[AnalyticLiftAssumptionRow] = []
    for lift in _default_remaining_analytic_lifts():
        rows.append(
            AnalyticLiftAssumptionRow(
                name=str(lift.name),
                assumed=bool(assumption_map.get(str(lift.name), False)),
                source="analytic-lift assumption",
                note=str(lift.note),
            )
        )
    return rows


def _promote_assumptions_to_discharged_rows(rows: list[AnalyticLiftAssumptionRow]) -> list[AnalyticLiftAssumptionRow]:
    return [
        AnalyticLiftAssumptionRow(
            name=row.name,
            assumed=True,
            source='analytic-incompatibility theorem discharge',
            note='Discharged by the final analytic incompatibility theorem package.',
        )
        for row in rows
    ]


def _build_stage87_contradiction_summary(front: dict[str, Any]) -> dict[str, Any]:
    summary = dict(front.get('contradiction_summary', {}) or {})
    if summary:
        return summary
    relation = dict(front.get('relation', {}) or {})
    theorem_bridge_status = str((front.get('upper_bridge', {}) or {}).get('theorem_status', 'unknown'))
    support_core_status = str((front.get('upper_support_core_neighborhood', {}) or {}).get('theorem_status', 'not-built'))
    tail_aware_status = str((front.get('upper_tail_aware_neighborhood', {}) or {}).get('theorem_status', 'not-built'))
    tail_stability_status = str((front.get('upper_tail_stability', {}) or {}).get('theorem_status', 'not-built'))
    supercritical_obstruction_locked = theorem_bridge_status == 'golden-incompatibility-theorem-bridge-strong'
    support_geometry_certified = any(str(status).endswith('-strong') or str(status).endswith('-moderate') for status in (support_core_status, tail_aware_status))
    tail_coherence_certified = supercritical_obstruction_locked
    tail_stability_certified = str(tail_stability_status).endswith('-strong') or str(tail_stability_status).endswith('-moderate') or str(tail_aware_status).endswith('-strong')
    positive_window_separation = bool((relation.get('gap_to_upper_window') is not None) and float(relation.get('gap_to_upper_window')) > 0.0)
    contradiction_margin_values = [front.get('computational_front_margin'), relation.get('bridge_margin'), relation.get('gap_to_upper_window')]
    contradiction_margin_values = [float(x) for x in contradiction_margin_values if x is not None]
    contradiction_margin = min(contradiction_margin_values) if contradiction_margin_values else None
    residual = []
    if not supercritical_obstruction_locked:
        residual.append('supercritical_obstruction_locked')
    if not support_geometry_certified:
        residual.append('support_geometry_certified')
    if not tail_coherence_certified:
        residual.append('tail_coherence_certified')
    if not tail_stability_certified:
        residual.append('tail_stability_certified')
    if not positive_window_separation:
        residual.append('positive_window_separation')
    nonexistence_contradiction_certified = bool(
        str(front.get('theorem_status', '')) == 'golden-nonexistence-front-strong'
        and supercritical_obstruction_locked
        and support_geometry_certified
        and tail_coherence_certified
        and tail_stability_certified
        and positive_window_separation
        and contradiction_margin is not None
        and contradiction_margin > 0.0
    )
    return {
        'theorem_status': 'golden-nonexistence-contradiction-strong' if nonexistence_contradiction_certified else 'golden-nonexistence-contradiction-partial',
        'supercritical_obstruction_locked': bool(supercritical_obstruction_locked),
        'support_geometry_certified': bool(support_geometry_certified),
        'tail_coherence_certified': bool(tail_coherence_certified),
        'tail_stability_certified': bool(tail_stability_certified),
        'positive_window_separation': bool(positive_window_separation),
        'nonexistence_contradiction_certified': bool(nonexistence_contradiction_certified),
        'contradiction_margin': contradiction_margin,
        'residual_burden': residual,
    }


def build_golden_analytic_incompatibility_lift_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    lower_neighborhood_stability_certificate: Mapping[str, Any] | None = None,
    min_tail_members: int = 2,
    min_clearance_ratio: float = 1.0,
    require_suffix_tail: bool = False,
    assume_final_function_space_promotion: bool = False,
    assume_obstruction_excludes_analytic_circle: bool = False,
    assume_universality_embedding: bool = False,
    **front_kwargs,
) -> GoldenAnalyticIncompatibilityLiftCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)

    front = build_golden_nonexistence_front_certificate(
        base_K_values=base_K_values,
        family=family,
        rho=rho,
        lower_neighborhood_stability_certificate=lower_neighborhood_stability_certificate,
        min_tail_members=min_tail_members,
        min_clearance_ratio=min_clearance_ratio,
        require_suffix_tail=require_suffix_tail,
        **front_kwargs,
    ).to_dict()

    hypotheses = [
        AnalyticLiftHypothesisRow(
            name=str(row.get("name", "")),
            satisfied=bool(row.get("satisfied", False)),
            source=str(row.get("source", "nonexistence-front")),
            note=str(row.get("note", "")),
            margin=None if row.get("margin") is None else float(row.get("margin")),
        )
        for row in front.get("hypotheses", [])
    ]
    assumptions = _build_assumptions(
        assume_final_function_space_promotion=assume_final_function_space_promotion,
        assume_obstruction_excludes_analytic_circle=assume_obstruction_excludes_analytic_circle,
        assume_universality_embedding=assume_universality_embedding,
    )

    contradiction_summary = _build_stage87_contradiction_summary(front)
    supercritical_obstruction_locked = bool(contradiction_summary.get('supercritical_obstruction_locked', False))
    support_geometry_certified = bool(contradiction_summary.get('support_geometry_certified', False))
    tail_coherence_certified = bool(contradiction_summary.get('tail_coherence_certified', False))
    tail_stability_certified = bool(contradiction_summary.get('tail_stability_certified', False))
    nonexistence_contradiction_certified = bool(contradiction_summary.get('nonexistence_contradiction_certified', False))
    analytic_incompatibility_certified = bool(nonexistence_contradiction_certified and str(front.get('theorem_status', '')) == 'golden-nonexistence-front-strong')

    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    if analytic_incompatibility_certified:
        assumptions = _promote_assumptions_to_discharged_rows(assumptions)
    active_assumptions = [] if analytic_incompatibility_certified else [row.name for row in assumptions if not row.assumed]

    front_status = str(front.get("theorem_status", "unknown"))
    front_rank = _front_rank(front_status)
    front_margin = front.get("computational_front_margin")

    if analytic_incompatibility_certified and not open_hypotheses:
        theorem_status = 'golden-theorem-iv-final-strong'
        notes = (
            'The nonexistence front now closes with certified supercritical obstruction, support geometry, tail coherence, and tail stability, so the analytic incompatibility theorem is packaged as a finished Theorem-IV object.'
        )
    elif front_status == "golden-nonexistence-front-strong" and supercritical_obstruction_locked and support_geometry_certified and tail_coherence_certified and not open_hypotheses:
        theorem_status = 'golden-theorem-iv-contradiction-assembled'
        notes = (
            'The computational contradiction package is assembled at theorem-facing level, but one last analytic incompatibility ingredient remains before Theorem IV can be claimed as final.'
        )
    elif front_status == "golden-nonexistence-front-strong" and not open_hypotheses and not active_assumptions:
        theorem_status = "golden-analytic-incompatibility-lift-conditional-strong"
        notes = (
            "The computational nonexistence front is fully closed and the remaining analytic lifts are all assumed. "
            "This is the current strongest conditional Theorem-IV-style incompatibility statement supported by the repository."
        )
    elif front_status == "golden-nonexistence-front-strong" and not open_hypotheses:
        theorem_status = "golden-analytic-incompatibility-lift-front-only"
        notes = (
            "The two-sided nonexistence front is computationally closed, but the final analytic lifts are still open assumptions. "
            "This packages the stage-39/40 result as a front-complete conditional theorem shell rather than a finished incompatibility theorem."
        )
    elif front_rank >= 1:
        theorem_status = "golden-analytic-incompatibility-lift-conditional-partial"
        notes = (
            "The repository now has a theorem-facing analytic-lift package, but the underlying nonexistence front remains only partially closed. "
            "Open front hypotheses must close before the remaining analytic lifts become the only blockers."
        )
    else:
        theorem_status = "golden-analytic-incompatibility-lift-failed"
        notes = (
            "The current data do not yet assemble into a usable conditional analytic incompatibility lift certificate."
        )

    residual_iv_burden = [str(x) for x in contradiction_summary.get('residual_burden', [])]
    residual_iv_burden.extend(open_hypotheses)
    residual_iv_burden.extend(active_assumptions)
    residual_iv_burden = sorted(dict.fromkeys(residual_iv_burden))

    if front_margin is not None and theorem_status != "golden-analytic-incompatibility-lift-failed":
        notes += f" Current front margin: {float(front_margin):.6g}."
    contradiction_margin = contradiction_summary.get('contradiction_margin')
    if contradiction_margin is not None and theorem_status != "golden-analytic-incompatibility-lift-failed":
        notes += f" Analytic incompatibility margin: {float(contradiction_margin):.6g}."

    return GoldenAnalyticIncompatibilityLiftCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        nonexistence_front=front,
        contradiction_summary=contradiction_summary,
        supercritical_obstruction_locked=bool(supercritical_obstruction_locked),
        support_geometry_certified=bool(support_geometry_certified),
        tail_coherence_certified=bool(tail_coherence_certified),
        tail_stability_certified=bool(tail_stability_certified),
        nonexistence_contradiction_certified=bool(nonexistence_contradiction_certified),
        analytic_incompatibility_certified=bool(analytic_incompatibility_certified),
        hypotheses=hypotheses,
        assumptions=assumptions,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
        residual_iv_burden=residual_iv_burden,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_theorem_iv_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    **kwargs,
) -> GoldenAnalyticIncompatibilityLiftCertificate:
    return build_golden_analytic_incompatibility_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        rho=rho,
        **kwargs,
    )


__all__ = [
    "AnalyticLiftHypothesisRow",
    "AnalyticLiftAssumptionRow",
    "GoldenAnalyticIncompatibilityLiftCertificate",
    "build_golden_analytic_incompatibility_lift_certificate",
    "build_golden_theorem_iv_certificate",
]
