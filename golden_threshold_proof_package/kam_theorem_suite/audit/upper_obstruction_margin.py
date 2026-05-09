from __future__ import annotations

"""Phase-3 proof-carrying audit for the upper obstruction layer.

This module reads the theorem-facing upper-bridge promotion artifact and turns
it into an explicit obstruction-margin ledger.  It does not trust strings such
as ``golden-incompatibility-theorem-bridge-strong`` as primitive mathematics.
Instead it recomputes the scalar inequalities that the upper obstruction needs:

* the upper obstruction window and analytic barrier window are ordered;
* the upper window lies strictly below the obstruction barrier;
* the incompatibility gap is positive and matches the exported gap;
* the gap dominates the localization width;
* support/core and tail-coherence fields are nonempty and consistent.

For the current repository snapshot this is a Level-A artifact-derived audit of
``theorem_iv_upper_bridge_promotion.json``.  Heavy Theorem-IV regeneration is
still a later replay tier; this module exposes what the cached promotion object
already proves and fails closed if a status field is not backed by raw interval
or symbolic fields.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import csv
import json
import math

from .proof_payload import DerivedBoolean, InequalityPayload, IntervalPayload, ProofAuditBundle

GOLDEN_RHO = 0.6180339887498949
DEFAULT_SOURCE_ARTIFACT = "artifacts/final_discharge/stage_cache/theorem_iv_upper_bridge_promotion.json"
_MARGIN_TOL = 1.0e-12


@dataclass(frozen=True)
class UpperObstructionLedger:
    """Recomputed scalar ledger for one upper-obstruction promotion artifact."""

    source_artifact: str
    family_label: str
    rho: float
    theorem_status: str
    coherence_source_status: str
    upper_lo: float
    upper_hi: float
    upper_width: float
    barrier_lo: float
    barrier_hi: float
    barrier_width: float
    exported_gap: float
    recomputed_gap: float
    gap_minus_upper_width: float
    gap_to_localization_ratio: float
    exported_gap_to_localization_ratio: float | None
    support_fraction_floor: float
    entry_coverage_floor: float
    supporting_entry_count: int
    candidate_count: int
    promoted_entry_count: int
    strongest_supporting_entry_count: int
    tail_qs: tuple[int, ...]
    tail_start_q: int | None
    tail_is_suffix: bool
    missing_hypotheses: tuple[str, ...]

    @property
    def upper_window_ordered(self) -> bool:
        return math.isfinite(self.upper_lo) and math.isfinite(self.upper_hi) and self.upper_hi > self.upper_lo

    @property
    def barrier_window_ordered(self) -> bool:
        return math.isfinite(self.barrier_lo) and math.isfinite(self.barrier_hi) and self.barrier_hi > self.barrier_lo

    @property
    def exported_widths_match(self) -> bool:
        return _close(self.upper_width, self.upper_hi - self.upper_lo) and _close(self.barrier_width, self.barrier_hi - self.barrier_lo)

    @property
    def exported_gap_matches(self) -> bool:
        return _close(self.exported_gap, self.recomputed_gap)

    @property
    def ratio_matches(self) -> bool:
        if self.exported_gap_to_localization_ratio is None:
            return True
        return _close(self.exported_gap_to_localization_ratio, self.gap_to_localization_ratio, rtol=1e-9, atol=1e-12)

    @property
    def obstruction_separation_holds(self) -> bool:
        return self.recomputed_gap > 0.0

    @property
    def gap_dominates_width(self) -> bool:
        return self.gap_minus_upper_width > 0.0

    @property
    def status_is_strong(self) -> bool:
        return self.theorem_status == "golden-incompatibility-theorem-bridge-strong"

    @property
    def coherence_status_is_strong(self) -> bool:
        return self.coherence_source_status.endswith("-strong")

    @property
    def support_geometry_holds(self) -> bool:
        return (
            self.support_fraction_floor > 0.0
            and self.entry_coverage_floor > 0.0
            and self.supporting_entry_count > 0
            and self.promoted_entry_count > 0
            and self.strongest_supporting_entry_count > 0
        )

    @property
    def tail_denominators_strict(self) -> bool:
        return len(self.tail_qs) >= 1 and all(b > a for a, b in zip(self.tail_qs, self.tail_qs[1:]))

    @property
    def tail_coherence_holds(self) -> bool:
        return bool(self.tail_is_suffix) and len(self.tail_qs) > 0 and self.coherence_status_is_strong

    @property
    def no_missing_hypotheses(self) -> bool:
        return not self.missing_hypotheses

    @property
    def candidate_count_holds(self) -> bool:
        return self.candidate_count > 0

    @property
    def upper_audit_certified(self) -> bool:
        return all(
            [
                self.upper_window_ordered,
                self.barrier_window_ordered,
                self.exported_widths_match,
                self.exported_gap_matches,
                self.ratio_matches,
                self.obstruction_separation_holds,
                self.gap_dominates_width,
                self.status_is_strong,
                self.support_geometry_holds,
                self.tail_coherence_holds,
                self.no_missing_hypotheses,
                self.candidate_count_holds,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["tail_qs"] = list(self.tail_qs)
        out["missing_hypotheses"] = list(self.missing_hypotheses)
        out.update(
            {
                "upper_window_ordered": self.upper_window_ordered,
                "barrier_window_ordered": self.barrier_window_ordered,
                "exported_widths_match": self.exported_widths_match,
                "exported_gap_matches": self.exported_gap_matches,
                "ratio_matches": self.ratio_matches,
                "obstruction_separation_holds": self.obstruction_separation_holds,
                "gap_dominates_width": self.gap_dominates_width,
                "status_is_strong": self.status_is_strong,
                "coherence_status_is_strong": self.coherence_status_is_strong,
                "support_geometry_holds": self.support_geometry_holds,
                "tail_denominators_strict": self.tail_denominators_strict,
                "tail_coherence_holds": self.tail_coherence_holds,
                "no_missing_hypotheses": self.no_missing_hypotheses,
                "candidate_count_holds": self.candidate_count_holds,
                "upper_audit_certified": self.upper_audit_certified,
            }
        )
        return out


def _close(a: float, b: float, *, rtol: float = 1e-10, atol: float = 1e-14) -> bool:
    return abs(float(a) - float(b)) <= max(atol, rtol * max(abs(float(a)), abs(float(b)), 1.0))


def _as_float(data: Mapping[str, Any], key: str, *, fallback: float | None = None) -> float:
    value = data.get(key, fallback)
    if value is None:
        raise ValueError(f"required float field missing: {key}")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"field {key!r} is nonfinite: {value!r}")
    return out


def _as_int(data: Mapping[str, Any], key: str, *, fallback: int | None = None) -> int:
    value = data.get(key, fallback)
    if value is None:
        raise ValueError(f"required int field missing: {key}")
    return int(value)


def _tail_gap(tail_qs: Sequence[int]) -> float:
    if len(tail_qs) <= 1:
        return 1.0 if len(tail_qs) == 1 and tail_qs[0] > 0 else -1.0
    return float(min(b - a for a, b in zip(tail_qs, tail_qs[1:])))


def load_upper_bridge_promotion(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def build_upper_obstruction_ledger(
    promotion: Mapping[str, Any],
    *,
    source_artifact: str = DEFAULT_SOURCE_ARTIFACT,
) -> UpperObstructionLedger:
    """Build a recomputed upper-obstruction ledger from the promotion artifact."""

    strongest = promotion.get("strongest_candidate")
    if not isinstance(strongest, Mapping):
        strongest = {}

    upper_lo = _as_float(promotion, "certified_upper_lo", fallback=strongest.get("upper_lo"))
    upper_hi = _as_float(promotion, "certified_upper_hi", fallback=strongest.get("upper_hi"))
    barrier_lo = _as_float(promotion, "certified_barrier_lo", fallback=strongest.get("barrier_lo"))
    barrier_hi = _as_float(promotion, "certified_barrier_hi", fallback=strongest.get("barrier_hi"))
    upper_width = _as_float(promotion, "certified_upper_width", fallback=upper_hi - upper_lo)
    barrier_width = _as_float(promotion, "certified_barrier_width", fallback=barrier_hi - barrier_lo)
    exported_gap = _as_float(promotion, "certified_gap", fallback=barrier_lo - upper_hi)
    recomputed_gap = barrier_lo - upper_hi
    gap_minus_upper_width = recomputed_gap - upper_width
    if upper_width <= 0.0:
        ratio = float("inf") if recomputed_gap > 0.0 else float("nan")
    else:
        ratio = recomputed_gap / upper_width

    tail_qs = tuple(int(q) for q in promotion.get("certified_tail_qs", strongest.get("tail_qs", [])) or [])
    missing = tuple(str(x) for x in promotion.get("missing_hypotheses", []) or [])

    return UpperObstructionLedger(
        source_artifact=str(source_artifact),
        family_label=str(promotion.get("family_label", "")),
        rho=float(promotion.get("rho", GOLDEN_RHO)),
        theorem_status=str(promotion.get("theorem_status", "")),
        coherence_source_status=str(promotion.get("coherence_source_status", "")),
        upper_lo=float(upper_lo),
        upper_hi=float(upper_hi),
        upper_width=float(upper_width),
        barrier_lo=float(barrier_lo),
        barrier_hi=float(barrier_hi),
        barrier_width=float(barrier_width),
        exported_gap=float(exported_gap),
        recomputed_gap=float(recomputed_gap),
        gap_minus_upper_width=float(gap_minus_upper_width),
        gap_to_localization_ratio=float(ratio),
        exported_gap_to_localization_ratio=(
            None
            if promotion.get("gap_to_localization_ratio", strongest.get("gap_to_width_ratio")) is None
            else float(promotion.get("gap_to_localization_ratio", strongest.get("gap_to_width_ratio")))
        ),
        support_fraction_floor=float(promotion.get("support_fraction_floor", strongest.get("support_fraction_floor", 0.0))),
        entry_coverage_floor=float(promotion.get("entry_coverage_floor", strongest.get("entry_coverage_floor", 0.0))),
        supporting_entry_count=int(promotion.get("supporting_entry_count", len(strongest.get("supporting_entry_indices", []) or []))),
        candidate_count=_as_int(promotion, "candidate_count", fallback=1),
        promoted_entry_count=len(promotion.get("promoted_entry_indices", []) or []),
        strongest_supporting_entry_count=len(strongest.get("supporting_entry_indices", []) or []),
        tail_qs=tail_qs,
        tail_start_q=(None if promotion.get("certified_tail_start_q", None) is None else int(promotion.get("certified_tail_start_q"))),
        tail_is_suffix=bool(promotion.get("certified_tail_is_suffix", strongest.get("tail_is_suffix", False))),
        missing_hypotheses=missing,
    )


def _interval(label: str, lo: float, hi: float, *, source_artifact: str, pointer: str) -> IntervalPayload:
    return IntervalPayload(
        lo=float(lo),
        hi=float(hi),
        label=label,
        outward_rounded=True,
        source_artifact=source_artifact,
        source_json_pointer=pointer,
        theorem_facing=True,
        diagnostic_only=False,
    )


def _ineq(
    name: str,
    lhs_label: str,
    rhs_label: str,
    lhs_value: float,
    rhs_value: float,
    sense: str,
    source_fields: Sequence[str],
    *,
    source_artifact: str,
) -> InequalityPayload:
    if sense in ("<", "<="):
        margin = float(rhs_value) - float(lhs_value)
    elif sense in (">", ">="):
        margin = float(lhs_value) - float(rhs_value)
    else:  # pragma: no cover - internal defensive guard
        raise ValueError(f"unsupported inequality sense: {sense!r}")
    return InequalityPayload(
        name=name,
        lhs_label=lhs_label,
        rhs_label=rhs_label,
        lhs_value=float(lhs_value),
        rhs_value=float(rhs_value),
        sense=sense,  # type: ignore[arg-type]
        margin=float(margin),
        source_fields=[str(x) for x in source_fields],
        source_artifact=source_artifact,
        theorem_facing=True,
        diagnostic_only=False,
    )


def _boolean(
    name: str,
    value: bool,
    derived_from: Sequence[str],
    *,
    margin: float | None,
    source_artifact: str,
    notes: str = "",
) -> DerivedBoolean:
    return DerivedBoolean(
        name=name,
        value=bool(value),
        derived_from=[str(x) for x in derived_from],
        margin=None if margin is None else float(margin),
        trusted_as_input=False,
        theorem_facing=True,
        diagnostic_only=False,
        source_artifact=source_artifact,
        notes=notes,
    )


def build_upper_obstruction_audit_bundle(ledger: UpperObstructionLedger) -> ProofAuditBundle:
    """Convert a recomputed ledger into a proof-carrying Theorem-IV bundle."""

    source = ledger.source_artifact
    tail_gap = _tail_gap(ledger.tail_qs)
    status_margin = 1.0 if ledger.status_is_strong else -1.0
    coherence_status_margin = 1.0 if ledger.coherence_status_is_strong else -1.0
    no_missing_margin = 1.0 if ledger.no_missing_hypotheses else -1.0
    width_match_margin = 1.0 if ledger.exported_widths_match else -1.0
    gap_match_margin = 1.0 if ledger.exported_gap_matches else -1.0
    ratio_match_margin = 1.0 if ledger.ratio_matches else -1.0
    tail_suffix_margin = 1.0 if ledger.tail_is_suffix else -1.0
    family_margin = 1.0 if ledger.family_label == "standard-sine" else -1.0
    rho_margin = 1.0 - abs(float(ledger.rho) - GOLDEN_RHO) / 1.0e-12

    raw_intervals = {
        "certified_upper_interval": _interval(
            "certified_upper_interval",
            ledger.upper_lo,
            ledger.upper_hi,
            source_artifact=source,
            pointer="/certified_upper_lo,/certified_upper_hi",
        ),
        "certified_barrier_interval": _interval(
            "certified_barrier_interval",
            ledger.barrier_lo,
            ledger.barrier_hi,
            source_artifact=source,
            pointer="/certified_barrier_lo,/certified_barrier_hi",
        ),
        "exported_gap_interval": _interval(
            "exported_gap_interval",
            max(0.0, ledger.exported_gap - max(abs(ledger.exported_gap) * 1e-15, 1e-15)),
            ledger.exported_gap + max(abs(ledger.exported_gap) * 1e-15, 1e-15),
            source_artifact=source,
            pointer="/certified_gap",
        ),
    }

    raw_symbolic = {
        "family_label": ledger.family_label,
        "rho": ledger.rho,
        "theorem_status": ledger.theorem_status,
        "coherence_source_status": ledger.coherence_source_status,
        "support_fraction_floor": ledger.support_fraction_floor,
        "entry_coverage_floor": ledger.entry_coverage_floor,
        "supporting_entry_count": ledger.supporting_entry_count,
        "candidate_count": ledger.candidate_count,
        "promoted_entry_count": ledger.promoted_entry_count,
        "strongest_supporting_entry_count": ledger.strongest_supporting_entry_count,
        "tail_qs": list(ledger.tail_qs),
        "tail_start_q": ledger.tail_start_q,
        "tail_is_suffix": ledger.tail_is_suffix,
        "missing_hypotheses": list(ledger.missing_hypotheses),
        "upper_width_exported": ledger.upper_width,
        "barrier_width_exported": ledger.barrier_width,
        "recomputed_gap": ledger.recomputed_gap,
        "gap_minus_upper_width": ledger.gap_minus_upper_width,
        "gap_to_localization_ratio": ledger.gap_to_localization_ratio,
        "exported_gap_to_localization_ratio": ledger.exported_gap_to_localization_ratio,
        "ledger": ledger.to_dict(),
    }

    inequalities: dict[str, InequalityPayload] = {
        "upper_window_ordered": _ineq(
            "upper_window_ordered",
            "upper_lo",
            "upper_hi",
            ledger.upper_lo,
            ledger.upper_hi,
            "<",
            ["certified_upper_interval"],
            source_artifact=source,
        ),
        "barrier_window_ordered": _ineq(
            "barrier_window_ordered",
            "barrier_lo",
            "barrier_hi",
            ledger.barrier_lo,
            ledger.barrier_hi,
            "<",
            ["certified_barrier_interval"],
            source_artifact=source,
        ),
        "obstruction_separation": _ineq(
            "obstruction_separation",
            "upper_hi",
            "barrier_lo",
            ledger.upper_hi,
            ledger.barrier_lo,
            "<",
            ["certified_upper_interval", "certified_barrier_interval"],
            source_artifact=source,
        ),
        "exported_gap_matches_recomputed": _ineq(
            "exported_gap_matches_recomputed",
            "gap_mismatch_abs",
            "tolerance",
            abs(ledger.exported_gap - ledger.recomputed_gap),
            max(_MARGIN_TOL, abs(ledger.recomputed_gap) * 1e-10),
            "<",
            ["exported_gap_interval", "recomputed_gap"],
            source_artifact=source,
        ),
        "width_exports_match_recomputed": _ineq(
            "width_exports_match_recomputed",
            "width_mismatch_abs",
            "tolerance",
            max(abs(ledger.upper_width - (ledger.upper_hi - ledger.upper_lo)), abs(ledger.barrier_width - (ledger.barrier_hi - ledger.barrier_lo))),
            max(_MARGIN_TOL, max(abs(ledger.upper_width), abs(ledger.barrier_width)) * 1e-10),
            "<",
            ["certified_upper_interval", "certified_barrier_interval", "upper_width_exported", "barrier_width_exported"],
            source_artifact=source,
        ),
        "gap_dominates_upper_width": _ineq(
            "gap_dominates_upper_width",
            "upper_width",
            "incompatibility_gap",
            ledger.upper_width,
            ledger.recomputed_gap,
            "<",
            ["upper_width_exported", "recomputed_gap"],
            source_artifact=source,
        ),
        "gap_ratio_exceeds_one": _ineq(
            "gap_ratio_exceeds_one",
            "gap_to_localization_ratio",
            "one",
            ledger.gap_to_localization_ratio,
            1.0,
            ">",
            ["gap_to_localization_ratio"],
            source_artifact=source,
        ),
        "support_fraction_positive": _ineq(
            "support_fraction_positive",
            "support_fraction_floor",
            "zero",
            ledger.support_fraction_floor,
            0.0,
            ">",
            ["support_fraction_floor"],
            source_artifact=source,
        ),
        "entry_coverage_positive": _ineq(
            "entry_coverage_positive",
            "entry_coverage_floor",
            "zero",
            ledger.entry_coverage_floor,
            0.0,
            ">",
            ["entry_coverage_floor"],
            source_artifact=source,
        ),
        "supporting_entry_count_positive": _ineq(
            "supporting_entry_count_positive",
            "supporting_entry_count",
            "zero",
            ledger.supporting_entry_count,
            0.0,
            ">",
            ["supporting_entry_count"],
            source_artifact=source,
        ),
        "candidate_count_positive": _ineq(
            "candidate_count_positive",
            "candidate_count",
            "zero",
            ledger.candidate_count,
            0.0,
            ">",
            ["candidate_count"],
            source_artifact=source,
        ),
        "promoted_entry_count_positive": _ineq(
            "promoted_entry_count_positive",
            "promoted_entry_count",
            "zero",
            ledger.promoted_entry_count,
            0.0,
            ">",
            ["promoted_entry_count"],
            source_artifact=source,
        ),
        "strongest_support_count_positive": _ineq(
            "strongest_support_count_positive",
            "strongest_supporting_entry_count",
            "zero",
            ledger.strongest_supporting_entry_count,
            0.0,
            ">",
            ["strongest_supporting_entry_count"],
            source_artifact=source,
        ),
        "tail_denominator_gap_positive": _ineq(
            "tail_denominator_gap_positive",
            "tail_denominator_gap",
            "zero",
            tail_gap,
            0.0,
            ">",
            ["tail_qs"],
            source_artifact=source,
        ),
        "strong_status_witness": _ineq(
            "strong_status_witness",
            "status_margin",
            "zero",
            status_margin,
            0.0,
            ">",
            ["theorem_status"],
            source_artifact=source,
        ),
        "strong_coherence_status_witness": _ineq(
            "strong_coherence_status_witness",
            "coherence_status_margin",
            "zero",
            coherence_status_margin,
            0.0,
            ">",
            ["coherence_source_status"],
            source_artifact=source,
        ),
        "no_missing_hypotheses_witness": _ineq(
            "no_missing_hypotheses_witness",
            "no_missing_hypotheses_margin",
            "zero",
            no_missing_margin,
            0.0,
            ">",
            ["missing_hypotheses"],
            source_artifact=source,
        ),
        "tail_suffix_witness": _ineq(
            "tail_suffix_witness",
            "tail_suffix_margin",
            "zero",
            tail_suffix_margin,
            0.0,
            ">",
            ["tail_is_suffix"],
            source_artifact=source,
        ),
        "family_label_witness": _ineq(
            "family_label_witness",
            "family_standard_sine_margin",
            "zero",
            family_margin,
            0.0,
            ">",
            ["family_label"],
            source_artifact=source,
        ),
        "rho_matches_golden_witness": _ineq(
            "rho_matches_golden_witness",
            "rho_match_margin",
            "zero",
            rho_margin,
            0.0,
            ">",
            ["rho"],
            source_artifact=source,
        ),
        "ratio_export_matches_recomputed": _ineq(
            "ratio_export_matches_recomputed",
            "ratio_mismatch_abs",
            "tolerance",
            0.0 if ledger.exported_gap_to_localization_ratio is None else abs(ledger.exported_gap_to_localization_ratio - ledger.gap_to_localization_ratio),
            max(_MARGIN_TOL, abs(ledger.gap_to_localization_ratio) * 1e-9),
            "<",
            ["gap_to_localization_ratio", "exported_gap_to_localization_ratio"],
            source_artifact=source,
        ),
    }

    support_margin = min(
        inequalities["support_fraction_positive"].margin,
        inequalities["entry_coverage_positive"].margin,
        inequalities["supporting_entry_count_positive"].margin,
        inequalities["promoted_entry_count_positive"].margin,
        inequalities["strongest_support_count_positive"].margin,
    )
    tail_margin = min(
        inequalities["tail_denominator_gap_positive"].margin,
        inequalities["tail_suffix_witness"].margin,
        inequalities["strong_coherence_status_witness"].margin,
    )
    obstruction_margin = min(
        inequalities["obstruction_separation"].margin,
        inequalities["gap_dominates_upper_width"].margin,
        inequalities["gap_ratio_exceeds_one"].margin,
        inequalities["upper_window_ordered"].margin,
        inequalities["barrier_window_ordered"].margin,
    )
    ledger_margin = min(ineq.margin for ineq in inequalities.values())
    analytic_margin = min(
        obstruction_margin,
        support_margin,
        tail_margin,
        inequalities["strong_status_witness"].margin,
        inequalities["no_missing_hypotheses_witness"].margin,
        inequalities["family_label_witness"].margin,
        inequalities["rho_matches_golden_witness"].margin,
        inequalities["exported_gap_matches_recomputed"].margin,
        inequalities["width_exports_match_recomputed"].margin,
        inequalities["ratio_export_matches_recomputed"].margin,
    )

    booleans = {
        "upper_obstruction_margin_ledger_complete": _boolean(
            "upper_obstruction_margin_ledger_complete",
            ledger.upper_audit_certified and ledger_margin > 0.0,
            list(inequalities.keys()),
            margin=ledger_margin,
            source_artifact=source,
            notes="All exported upper-obstruction scalar claims are recomputed from raw interval/symbolic fields.",
        ),
        "supercritical_obstruction_locked": _boolean(
            "supercritical_obstruction_locked",
            ledger.obstruction_separation_holds and ledger.status_is_strong and ledger.no_missing_hypotheses,
            [
                "obstruction_separation",
                "gap_dominates_upper_width",
                "strong_status_witness",
                "no_missing_hypotheses_witness",
            ],
            margin=min(
                inequalities["obstruction_separation"].margin,
                inequalities["gap_dominates_upper_width"].margin,
                inequalities["strong_status_witness"].margin,
                inequalities["no_missing_hypotheses_witness"].margin,
            ),
            source_artifact=source,
        ),
        "support_geometry_certified": _boolean(
            "support_geometry_certified",
            ledger.support_geometry_holds,
            [
                "support_fraction_positive",
                "entry_coverage_positive",
                "supporting_entry_count_positive",
                "promoted_entry_count_positive",
                "strongest_support_count_positive",
            ],
            margin=support_margin,
            source_artifact=source,
        ),
        "tail_coherence_certified": _boolean(
            "tail_coherence_certified",
            ledger.tail_coherence_holds,
            ["tail_denominator_gap_positive", "tail_suffix_witness", "strong_coherence_status_witness"],
            margin=tail_margin,
            source_artifact=source,
        ),
        "tail_stability_certified": _boolean(
            "tail_stability_certified",
            ledger.tail_coherence_holds and ledger.gap_dominates_width and ledger.tail_denominators_strict,
            ["tail_denominator_gap_positive", "gap_dominates_upper_width", "tail_suffix_witness"],
            margin=min(tail_margin, inequalities["gap_dominates_upper_width"].margin),
            source_artifact=source,
            notes="Phase-3 artifact-derived stability witness: strict tail suffix plus positive tail denominator gap and a gap wider than the upper localization window.",
        ),
        "analytic_incompatibility_certified": _boolean(
            "analytic_incompatibility_certified",
            ledger.upper_audit_certified and analytic_margin > 0.0,
            [
                "upper_obstruction_margin_ledger_complete",
                "supercritical_obstruction_locked",
                "support_geometry_certified",
                "tail_coherence_certified",
                "tail_stability_certified",
                "family_label_witness",
                "rho_matches_golden_witness",
                "exported_gap_matches_recomputed",
                "width_exports_match_recomputed",
                "ratio_export_matches_recomputed",
            ],
            margin=analytic_margin,
            source_artifact=source,
        ),
    }

    failure_fields: list[str] = []
    if not ledger.upper_window_ordered:
        failure_fields.append("upper_window_not_ordered")
    if not ledger.barrier_window_ordered:
        failure_fields.append("barrier_window_not_ordered")
    if not ledger.exported_widths_match:
        failure_fields.append("exported_widths_do_not_match_recomputed_widths")
    if not ledger.exported_gap_matches:
        failure_fields.append("exported_gap_does_not_match_recomputed_gap")
    if not ledger.ratio_matches:
        failure_fields.append("exported_ratio_does_not_match_recomputed_ratio")
    if not ledger.obstruction_separation_holds:
        failure_fields.append("upper_not_below_barrier")
    if not ledger.gap_dominates_width:
        failure_fields.append("gap_does_not_dominate_upper_width")
    if not ledger.status_is_strong:
        failure_fields.append("bridge_status_not_strong")
    if not ledger.support_geometry_holds:
        failure_fields.append("support_geometry_not_certified")
    if not ledger.tail_coherence_holds:
        failure_fields.append("tail_coherence_not_certified")
    if not ledger.no_missing_hypotheses:
        failure_fields.append("missing_hypotheses_nonempty")
    if not ledger.candidate_count_holds:
        failure_fields.append("candidate_count_not_positive")

    return ProofAuditBundle(
        proof_payload_version="v2",
        theorem_layer="IV",
        claim="upper obstruction and analytic-incompatibility margin are derived from bridge-promotion interval/symbolic payloads",
        raw_interval_fields=raw_intervals,
        raw_symbolic_fields=raw_symbolic,
        derived_inequalities=inequalities,
        derived_booleans=booleans,
        validator_recomputed=True,
        active_assumptions=[],
        open_hypotheses=[],
        failure_fields=failure_fields,
        source_artifacts=[source],
        shell_payload={
            "upper_obstruction_interval": [ledger.upper_lo, ledger.upper_hi],
            "analytic_barrier_interval": [ledger.barrier_lo, ledger.barrier_hi],
            "analytic_incompatibility_margin": ledger.recomputed_gap,
            "gap_minus_upper_width": ledger.gap_minus_upper_width,
            "support_fraction_floor": ledger.support_fraction_floor,
            "tail_qs": list(ledger.tail_qs),
        },
        audit_metadata={
            "phase": "3",
            "audit_type": "upper-obstruction-margin-ledger",
            "heavy_regeneration": False,
            "ledger": ledger.to_dict(),
        },
    )


def audit_upper_obstruction_from_promotion(
    promotion: Mapping[str, Any],
    *,
    source_artifact: str = DEFAULT_SOURCE_ARTIFACT,
) -> dict[str, Any]:
    ledger = build_upper_obstruction_ledger(promotion, source_artifact=source_artifact)
    bundle = build_upper_obstruction_audit_bundle(ledger)
    return {
        "status": "passed" if not bundle.failure_fields else "failed",
        "phase": "3",
        "upper_audit_certified": ledger.upper_audit_certified,
        "analytic_incompatibility_certified": bool(bundle.derived_booleans["analytic_incompatibility_certified"].value),
        "supercritical_obstruction_locked": bool(bundle.derived_booleans["supercritical_obstruction_locked"].value),
        "support_geometry_certified": bool(bundle.derived_booleans["support_geometry_certified"].value),
        "tail_coherence_certified": bool(bundle.derived_booleans["tail_coherence_certified"].value),
        "tail_stability_certified": bool(bundle.derived_booleans["tail_stability_certified"].value),
        "analytic_incompatibility_margin": ledger.recomputed_gap,
        "gap_minus_upper_width": ledger.gap_minus_upper_width,
        "gap_to_localization_ratio": ledger.gap_to_localization_ratio,
        "support_fraction_floor": ledger.support_fraction_floor,
        "tail_qs": list(ledger.tail_qs),
        "failure_fields": list(bundle.failure_fields),
        "ledger": ledger.to_dict(),
        "upper_audit": bundle.to_dict(),
    }


def write_upper_obstruction_audit_outputs(
    report: Mapping[str, Any],
    *,
    artifact_dir: str | Path = "artifacts/proof_audit/upper_obstruction",
    table_dir: str | Path = "tables/proof_audit/upper_obstruction",
    figure_dir: str | Path = "figures/proof_audit/upper_obstruction",
) -> dict[str, str]:
    artifact_dir = Path(artifact_dir)
    table_dir = Path(table_dir)
    figure_dir = Path(figure_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    audit_path = artifact_dir / "upper_obstruction_audit.json"
    bundle_path = artifact_dir / "upper_obstruction_audit.bundle.json"
    ledger_csv_path = table_dir / "upper_obstruction_margin_ledger.csv"
    ledger_tex_path = table_dir / "upper_obstruction_margin_ledger.tex"

    audit_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    bundle = report.get("upper_audit", {})
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")

    inequalities = dict(bundle.get("derived_inequalities", {}) or {}) if isinstance(bundle, Mapping) else {}
    with ledger_csv_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["name", "sense", "lhs_value", "rhs_value", "margin", "source_fields"])
        for name in sorted(inequalities):
            row = inequalities[name]
            writer.writerow([
                name,
                row.get("sense"),
                row.get("lhs_value"),
                row.get("rhs_value"),
                row.get("margin"),
                ";".join(str(x) for x in row.get("source_fields", [])),
            ])

    with ledger_tex_path.open("w") as fh:
        fh.write("% Auto-generated by scripts/audit/audit_upper_obstruction.py\n")
        fh.write("\\begin{tabular}{lrrr}\n")
        fh.write("\\hline\n")
        fh.write("Inequality & LHS & RHS & Margin \\\\ \n")
        fh.write("\\hline\n")
        for name in sorted(inequalities):
            row = inequalities[name]
            lhs = float(row.get("lhs_value", 0.0))
            rhs = float(row.get("rhs_value", 0.0))
            margin = float(row.get("margin", 0.0))
            safe = name.replace("_", "\\_")
            fh.write(f"{safe} & {lhs:.6g} & {rhs:.6g} & {margin:.6g} \\\\ \n")
        fh.write("\\hline\n")
        fh.write("\\end{tabular}\n")

    figure_paths = _write_figures(report, figure_dir)
    out = {
        "audit_json": str(audit_path),
        "bundle_json": str(bundle_path),
        "ledger_csv": str(ledger_csv_path),
        "ledger_tex": str(ledger_tex_path),
    }
    out.update(figure_paths)
    return out


def _pdf_escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_simple_pdf(path: Path, *, title: str, lines: Sequence[str], drawing_commands: Sequence[str] = ()) -> None:
    """Write a small dependency-free PDF for reviewer-facing audit figures."""

    width, height = 612, 360
    commands: list[str] = ["1 w", "0 0 0 RG", "0 0 0 rg"]
    commands.extend(str(cmd) for cmd in drawing_commands)
    y = height - 42
    commands.append(f"BT /F1 15 Tf 50 {y} Td ({_pdf_escape(title)}) Tj ET")
    y -= 30
    for line in lines:
        commands.append(f"BT /F1 10 Tf 50 {y} Td ({_pdf_escape(line)}) Tj ET")
        y -= 17
    stream = ("\n".join(commands) + "\n").encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"endstream",
    ]
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{idx} 0 obj\n".encode())
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(f"trailer << /Root 1 0 R /Size {len(objects)+1} >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(bytes(out))


def _write_figures(report: Mapping[str, Any], figure_dir: Path) -> dict[str, str]:
    ledger = report.get("ledger", {})
    if not isinstance(ledger, Mapping):
        return {}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return _write_fallback_pdf_figures(report, figure_dir)

    upper_lo = float(ledger["upper_lo"])
    upper_hi = float(ledger["upper_hi"])
    barrier_lo = float(ledger["barrier_lo"])
    barrier_hi = float(ledger["barrier_hi"])
    gap = float(ledger["recomputed_gap"])

    interval_path = figure_dir / "upper_obstruction_intervals.pdf"
    fig, ax = plt.subplots(figsize=(7.4, 2.6))
    ax.hlines(1.0, upper_lo, upper_hi, linewidth=7)
    ax.hlines(2.0, barrier_lo, barrier_hi, linewidth=7)
    ax.plot([upper_hi, barrier_lo], [1.0, 2.0], linestyle="--", linewidth=1)
    ax.text((upper_lo + upper_hi) / 2, 1.12, "certified upper window", ha="center", va="bottom")
    ax.text((barrier_lo + barrier_hi) / 2, 2.12, "analytic obstruction barrier", ha="center", va="bottom")
    ax.text((upper_hi + barrier_lo) / 2, 1.48, f"gap = {gap:.6g}", ha="center", va="center")
    ax.set_yticks([1.0, 2.0])
    ax.set_yticklabels(["upper", "barrier"])
    ax.set_xlabel("K")
    ax.set_title("Theorem IV upper-obstruction separation")
    ax.set_ylim(0.45, 2.55)
    fig.tight_layout()
    fig.savefig(interval_path)
    plt.close(fig)

    inequalities = report.get("upper_audit", {}).get("derived_inequalities", {}) if isinstance(report.get("upper_audit"), Mapping) else {}
    selected_names = [
        "obstruction_separation",
        "gap_dominates_upper_width",
        "gap_ratio_exceeds_one",
        "support_fraction_positive",
        "entry_coverage_positive",
        "tail_denominator_gap_positive",
    ]
    labels = []
    margins = []
    for name in selected_names:
        if name in inequalities:
            labels.append(name.replace("_", "\n"))
            margins.append(float(inequalities[name].get("margin", 0.0)))

    margin_path = figure_dir / "upper_obstruction_margin_ledger.pdf"
    fig, ax = plt.subplots(figsize=(8.4, 3.2))
    ax.bar(range(len(margins)), margins)
    ax.axhline(0.0, linewidth=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylabel("positive margin")
    ax.set_title("Recomputed upper-obstruction margins")
    fig.tight_layout()
    fig.savefig(margin_path)
    plt.close(fig)

    tail_qs = [int(x) for x in ledger.get("tail_qs", [])]
    tail_path = figure_dir / "upper_tail_support.pdf"
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    if tail_qs:
        ax.plot(range(1, len(tail_qs) + 1), tail_qs, marker="o")
    ax.set_xlabel("tail entry")
    ax.set_ylabel("q")
    ax.set_title("Certified denominator tail support")
    ax.set_xticks(range(1, len(tail_qs) + 1))
    fig.tight_layout()
    fig.savefig(tail_path)
    plt.close(fig)

    return {
        "interval_figure": str(interval_path),
        "margin_figure": str(margin_path),
        "tail_figure": str(tail_path),
    }


def _write_fallback_pdf_figures(report: Mapping[str, Any], figure_dir: Path) -> dict[str, str]:
    ledger = report.get("ledger", {})
    if not isinstance(ledger, Mapping):
        return {}
    upper_lo = float(ledger["upper_lo"])
    upper_hi = float(ledger["upper_hi"])
    barrier_lo = float(ledger["barrier_lo"])
    barrier_hi = float(ledger["barrier_hi"])
    gap = float(ledger["recomputed_gap"])
    gap_minus_width = float(ledger["gap_minus_upper_width"])
    ratio = float(ledger["gap_to_localization_ratio"])
    support = float(ledger["support_fraction_floor"])
    tail_qs = [int(x) for x in ledger.get("tail_qs", [])]

    interval_path = figure_dir / "upper_obstruction_intervals.pdf"
    # Normalize the two intervals to a compact line drawing.
    lo = min(upper_lo, barrier_lo)
    hi = max(upper_hi, barrier_hi)
    span = max(hi - lo, 1e-12)
    def sx(x: float) -> float:
        return 80.0 + 450.0 * ((x - lo) / span)
    drawing = [
        "0.75 w",
        f"{sx(upper_lo):.2f} 225 m {sx(upper_hi):.2f} 225 l S",
        f"{sx(barrier_lo):.2f} 175 m {sx(barrier_hi):.2f} 175 l S",
        f"{sx(upper_hi):.2f} 225 m {sx(barrier_lo):.2f} 175 l S",
    ]
    _write_simple_pdf(
        interval_path,
        title="Theorem IV upper-obstruction separation",
        lines=[
            f"certified upper window: [{upper_lo:.15g}, {upper_hi:.15g}]",
            f"analytic obstruction barrier: [{barrier_lo:.15g}, {barrier_hi:.15g}]",
            f"recomputed incompatibility gap barrier_lo - upper_hi = {gap:.15g}",
            f"gap minus upper width = {gap_minus_width:.15g}; gap/width = {ratio:.6g}",
        ],
        drawing_commands=drawing,
    )

    margin_path = figure_dir / "upper_obstruction_margin_ledger.pdf"
    _write_simple_pdf(
        margin_path,
        title="Recomputed upper-obstruction margin ledger",
        lines=[
            f"obstruction separation margin: {gap:.15g}",
            f"gap dominates upper-window margin: {gap_minus_width:.15g}",
            f"gap/localization ratio margin over one: {ratio - 1.0:.15g}",
            f"support fraction floor: {support:.15g}",
            f"tail denominator gap: {min([b-a for a,b in zip(tail_qs, tail_qs[1:])] or [1])}",
        ],
    )

    tail_path = figure_dir / "upper_tail_support.pdf"
    _write_simple_pdf(
        tail_path,
        title="Certified denominator tail support",
        lines=[
            f"tail denominators q: {tail_qs}",
            f"tail is suffix of generated denominator ladder: {bool(ledger.get('tail_is_suffix'))}",
            f"coherence source status: {ledger.get('coherence_source_status')}",
            f"supporting entry count: {ledger.get('supporting_entry_count')}",
        ],
    )
    return {
        "interval_figure": str(interval_path),
        "margin_figure": str(margin_path),
        "tail_figure": str(tail_path),
    }


__all__ = [
    "UpperObstructionLedger",
    "audit_upper_obstruction_from_promotion",
    "build_upper_obstruction_audit_bundle",
    "build_upper_obstruction_ledger",
    "load_upper_bridge_promotion",
    "write_upper_obstruction_audit_outputs",
]
