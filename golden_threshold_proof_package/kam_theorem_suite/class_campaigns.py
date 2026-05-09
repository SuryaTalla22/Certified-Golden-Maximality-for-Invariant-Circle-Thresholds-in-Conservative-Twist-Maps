from __future__ import annotations

"""Automatic arithmetic-class ladder and atlas campaign builders.

This module turns the previous hand-assembled obstruction atlases into a more
scalable workflow.  The key idea is to start from an eventually periodic
continued-fraction class, generate a filtered ladder of rational convergents,
attach heuristic-but-explicit crossing/band search windows, and then feed the
result into the existing atlas/pruning machinery.

The resulting objects are still proof-bridge artifacts:
- the arithmetic class itself is exact/eventually periodic;
- the convergent ladder is exact;
- the crossing and band windows are explicit heuristics based on a trusted
  reference window;
- the atlas entries are only as good as the downstream certified crossing/band
  routines.

The benefit is that challenger studies stop being assembled entry-by-entry in
notebooks.  Instead, they become reproducible campaigns that can be re-run as
certification quality improves.
"""

from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any, Iterable, Sequence

from .arithmetic import class_label
from .arithmetic_exact import (
    convergents_from_cf,
    periodic_cf_value,
    periodic_class_eta_interval,
)
from .obstruction_atlas import ApproximantWindowSpec, build_multi_approximant_obstruction_atlas
from .challenger_pruning import ChallengerSpec, build_challenger_pruning_report
from .standard_map import HarmonicFamily


@dataclass(frozen=True)
class ArithmeticClassSpec:
    preperiod: tuple[int, ...]
    period: tuple[int, ...]
    label: str | None = None

    def normalized_label(self) -> str:
        return self.label or class_label(period=self.period, preperiod=self.preperiod)


@dataclass
class LadderApproximant:
    p: int
    q: int
    order_index: int
    rho_error: float
    label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ClassLadderReport:
    class_label: str
    preperiod: tuple[int, ...]
    period: tuple[int, ...]
    rho: float
    eta_lo: float
    eta_hi: float
    eta_center: float
    arithmetic_method: str
    approximants: list[dict[str, Any]]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AtlasCampaignReport:
    class_label: str
    ladder: dict[str, Any]
    atlas: dict[str, Any]
    pruning_against_reference: dict[str, Any]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiClassCampaignReport:
    reference_label: str
    reference_lower_bound: float
    class_campaigns: list[dict[str, Any]]
    dominated_classes: list[str]
    overlapping_classes: list[str]
    undecided_classes: list[str]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _eventually_periodic_prefix(preperiod: Sequence[int], period: Sequence[int], n_terms: int) -> list[int]:
    pre = list(preperiod)
    per = list(period)
    if not per:
        raise ValueError("period must be non-empty")
    seq = pre[:]
    while len(seq) < max(n_terms, len(pre) + len(per) * 2):
        seq.extend(per)
    return seq[:n_terms]


def _unique_fractions(fracs: Iterable[Fraction]) -> list[Fraction]:
    out: list[Fraction] = []
    seen: set[tuple[int, int]] = set()
    for f in fracs:
        key = (int(f.numerator), int(f.denominator))
        if key in seen:
            continue
        seen.add(key)
        out.append(Fraction(*key))
    return out


def generate_eventually_periodic_convergents(
    *,
    preperiod: Sequence[int],
    period: Sequence[int],
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 1,
    keep_last: int | None = None,
) -> list[Fraction]:
    """Generate exact convergents for an eventually periodic continued fraction.

    Parameters are intentionally simple: the theorem-facing object is the class,
    while the ladder is only a finite working subset controlled by ``max_q`` and
    ``keep_last``.
    """
    seq = _eventually_periodic_prefix(preperiod, period, n_terms=n_terms)
    fracs = [f for f in convergents_from_cf(seq) if q_min <= f.denominator <= max_q]
    uniq = _unique_fractions(fracs)
    if keep_last is not None and keep_last > 0 and len(uniq) > keep_last:
        uniq = uniq[-keep_last:]
    return uniq


def build_class_ladder_report(
    spec: ArithmeticClassSpec,
    *,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    dps: int = 160,
    burn_in_cycles: int = 12,
) -> ClassLadderReport:
    arith = periodic_class_eta_interval(
        period=spec.period,
        preperiod=spec.preperiod,
        dps=dps,
        burn_in_cycles=burn_in_cycles,
    )
    rho = float(arith["rho"])
    fracs = generate_eventually_periodic_convergents(
        preperiod=spec.preperiod,
        period=spec.period,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
    )
    approximants = []
    for idx, frac in enumerate(fracs):
        approximants.append(
            LadderApproximant(
                p=int(frac.numerator),
                q=int(frac.denominator),
                order_index=int(idx),
                rho_error=float(abs(rho - float(frac))),
                label=f"{frac.numerator}/{frac.denominator}",
            ).to_dict()
        )
    notes = (
        "Exact convergents were generated from a finite eventually periodic continued-fraction prefix. "
        "This ladder is a campaign scaffold, not an asymptotic theorem."
    )
    return ClassLadderReport(
        class_label=spec.normalized_label(),
        preperiod=tuple(spec.preperiod),
        period=tuple(spec.period),
        rho=rho,
        eta_lo=float(arith["eta_lo"]),
        eta_hi=float(arith["eta_hi"]),
        eta_center=float(arith["eta_center"]),
        arithmetic_method=str(arith["method"]),
        approximants=approximants,
        notes=notes,
    )


def make_window_spec_for_fraction(
    frac: Fraction,
    *,
    reference_crossing_center: float,
    crossing_half_width: float = 2.5e-3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    label_prefix: str | None = None,
) -> ApproximantWindowSpec:
    p = int(frac.numerator)
    q = int(frac.denominator)
    crossing_lo = float(reference_crossing_center - crossing_half_width)
    crossing_hi = float(reference_crossing_center + crossing_half_width)
    band_lo = float(reference_crossing_center + band_offset_lo)
    band_hi = float(reference_crossing_center + band_offset_hi)
    label = f"{p}/{q}" if not label_prefix else f"{label_prefix} {p}/{q}"
    return ApproximantWindowSpec(
        p=p,
        q=q,
        crossing_K_lo=crossing_lo,
        crossing_K_hi=crossing_hi,
        band_search_lo=band_lo,
        band_search_hi=band_hi,
        label=label,
    )


def build_campaign_window_specs(
    spec: ArithmeticClassSpec,
    *,
    reference_crossing_center: float,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    crossing_half_width: float = 2.5e-3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
) -> list[ApproximantWindowSpec]:
    fracs = generate_eventually_periodic_convergents(
        preperiod=spec.preperiod,
        period=spec.period,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
    )
    return [
        make_window_spec_for_fraction(
            frac,
            reference_crossing_center=reference_crossing_center,
            crossing_half_width=crossing_half_width,
            band_offset_lo=band_offset_lo,
            band_offset_hi=band_offset_hi,
            label_prefix=spec.normalized_label(),
        )
        for frac in fracs
    ]


def build_class_atlas_campaign(
    spec: ArithmeticClassSpec,
    *,
    reference_lower_bound: float,
    reference_crossing_center: float,
    family: HarmonicFamily | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = True,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    crossing_half_width: float = 2.5e-3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
    dps: int = 160,
    burn_in_cycles: int = 12,
) -> AtlasCampaignReport:
    family = family or HarmonicFamily()
    ladder = build_class_ladder_report(
        spec,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
        dps=dps,
        burn_in_cycles=burn_in_cycles,
    )
    specs = build_campaign_window_specs(
        spec,
        reference_crossing_center=reference_crossing_center,
        max_q=max_q,
        n_terms=n_terms,
        q_min=q_min,
        keep_last=keep_last,
        crossing_half_width=crossing_half_width,
        band_offset_lo=band_offset_lo,
        band_offset_hi=band_offset_hi,
    )
    atlas = build_multi_approximant_obstruction_atlas(
        specs,
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()
    challengers = [
        ChallengerSpec(
            preperiod=tuple(spec.preperiod),
            period=tuple(spec.period),
            threshold_lower_bound=(None if entry.get("crossing_root_window_lo") is None else float(entry["crossing_root_window_lo"])),
            threshold_upper_bound=(None if entry.get("crossing_root_window_hi") is None else float(entry["crossing_root_window_hi"])),
            label=str(entry.get("label")),
        )
        for entry in atlas.get("approximants", [])
    ]
    pruning = build_challenger_pruning_report(challengers, golden_lower_bound=reference_lower_bound).to_dict()
    notes = (
        "Campaign built automatically from an arithmetic class specification, a convergent ladder, and heuristic search windows around a trusted reference regime."
    )
    return AtlasCampaignReport(
        class_label=spec.normalized_label(),
        ladder=ladder.to_dict(),
        atlas=atlas,
        pruning_against_reference=pruning,
        notes=notes,
    )


def build_multi_class_campaign(
    classes: Sequence[ArithmeticClassSpec],
    *,
    reference_label: str,
    reference_lower_bound: float,
    reference_crossing_center: float,
    family: HarmonicFamily | None = None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = True,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    max_q: int = 144,
    n_terms: int = 96,
    q_min: int = 8,
    keep_last: int | None = 6,
    crossing_half_width: float = 2.5e-3,
    band_offset_lo: float = 3.5e-3,
    band_offset_hi: float = 1.8e-2,
) -> MultiClassCampaignReport:
    family = family or HarmonicFamily()
    class_reports: list[dict[str, Any]] = []
    dominated: list[str] = []
    overlapping: list[str] = []
    undecided: list[str] = []
    for spec in classes:
        rep = build_class_atlas_campaign(
            spec,
            reference_lower_bound=reference_lower_bound,
            reference_crossing_center=reference_crossing_center,
            family=family,
            target_residue=target_residue,
            auto_localize_crossing=auto_localize_crossing,
            initial_subdivisions=initial_subdivisions,
            max_depth=max_depth,
            min_width=min_width,
            max_q=max_q,
            n_terms=n_terms,
            q_min=q_min,
            keep_last=keep_last,
            crossing_half_width=crossing_half_width,
            band_offset_lo=band_offset_lo,
            band_offset_hi=band_offset_hi,
        ).to_dict()
        class_reports.append(rep)
        status = rep["pruning_against_reference"].get("status", "")
        label = rep["class_label"]
        if rep["pruning_against_reference"].get("dominated_count", 0) > 0 and rep["pruning_against_reference"].get("overlapping_count", 0) == 0:
            dominated.append(label)
        elif rep["pruning_against_reference"].get("overlapping_count", 0) > 0:
            overlapping.append(label)
        else:
            undecided.append(label)
    notes = (
        "This multi-class campaign is an orchestration/reporting layer above the certified atlas routines. "
        "It scales challenger studies across several arithmetic classes but does not by itself prove challenger exhaustion."
    )
    return MultiClassCampaignReport(
        reference_label=str(reference_label),
        reference_lower_bound=float(reference_lower_bound),
        class_campaigns=class_reports,
        dominated_classes=dominated,
        overlapping_classes=overlapping,
        undecided_classes=undecided,
        notes=notes,
    )


__all__ = [
    "ArithmeticClassSpec",
    "LadderApproximant",
    "ClassLadderReport",
    "AtlasCampaignReport",
    "MultiClassCampaignReport",
    "generate_eventually_periodic_convergents",
    "build_class_ladder_report",
    "make_window_spec_for_fraction",
    "build_campaign_window_specs",
    "build_class_atlas_campaign",
    "build_multi_class_campaign",
]
