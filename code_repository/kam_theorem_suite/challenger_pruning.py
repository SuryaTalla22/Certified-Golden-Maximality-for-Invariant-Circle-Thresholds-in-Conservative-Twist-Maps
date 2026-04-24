from __future__ import annotations

"""Arithmetic-first challenger pruning scaffolding.

This module deliberately stays honest about what it proves. The current bridge
code does *not* have the final monotone-envelope theorem in eta, so pruning here
is organized as a structured decision layer rather than as a finished proof.

The core idea is simple:

1. compute rigorous-looking arithmetic summaries for challenger classes;
2. compare any available certified threshold upper bounds against a trusted
   golden lower bound; and
3. record which challengers are currently dominated, which still overlap, and
   which remain undecided because either arithmetic or threshold data are too
   weak.

That makes it possible to drive notebooks and proof notes with a consistent
vocabulary now, while keeping the door open for a later theorem that upgrades
these statuses into a true challenger-exhaustion result.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from .arithmetic import class_label
from .arithmetic_exact import periodic_class_eta_interval


@dataclass(frozen=True)
class ChallengerSpec:
    preperiod: tuple[int, ...]
    period: tuple[int, ...]
    threshold_upper_bound: float | None = None
    threshold_lower_bound: float | None = None
    label: str | None = None

    def normalized_label(self) -> str:
        return self.label or class_label(period=self.period, preperiod=self.preperiod)


@dataclass
class ChallengerRecord:
    label: str
    preperiod: tuple[int, ...]
    period: tuple[int, ...]
    rho: float
    eta_lo: float
    eta_hi: float
    eta_center: float
    arithmetic_method: str
    threshold_lower_bound: float | None
    threshold_upper_bound: float | None
    status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChallengerPruningReport:
    golden_lower_bound: float
    records: list[dict[str, Any]]
    dominated_count: int
    overlapping_count: int
    arithmetic_only_count: int
    undecided_count: int
    theorem_level_pruning_certificate: dict[str, Any]
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_challenger_against_golden(
    *,
    golden_lower_bound: float,
    eta_lo: float,
    eta_hi: float,
    threshold_upper_bound: float | None,
    threshold_lower_bound: float | None = None,
    eta_reference_golden: float = 1.0 / (5.0 ** 0.5),
    eta_gap_tol: float = 1e-10,
    threshold_gap_tol: float = 1e-10,
) -> tuple[str, str]:
    """Return a structured pruning status.

    Status meanings:
    - ``dominated``: the challenger has a certified threshold upper bound below
      the trusted golden lower bound.
    - ``overlapping``: a threshold upper bound exists but still reaches the
      golden lower bound, so the current bridge cannot prune it.
    - ``arithmetic-weaker-only``: arithmetic shows the class is strictly below
      golden in eta, but there is not yet a threshold upper bound to exploit.
    - ``undecided``: even the arithmetic separation is too weak or data are too
      sparse for the current pruning layer.
    """
    glb = float(golden_lower_bound)
    eta_lo = float(eta_lo)
    eta_hi = float(eta_hi)
    eta_ref = float(eta_reference_golden)
    if threshold_upper_bound is not None:
        tub = float(threshold_upper_bound)
        if tub < glb - threshold_gap_tol:
            return "dominated", "threshold upper bound lies below the trusted golden lower bound"
        return "overlapping", "threshold upper bound still overlaps the trusted golden lower bound"

    if eta_hi < eta_ref - eta_gap_tol:
        return "arithmetic-weaker-only", "eta interval lies strictly below the golden eta but no threshold upper bound is available"
    return "undecided", "current arithmetic/threshold data do not suffice to prune this challenger"


def build_theorem_level_pruning_certificate(
    records: Sequence[Mapping[str, Any]],
    *,
    theorem_level_dominated_labels: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Package the dominated-region pruning side as a theorem-facing object.

    By default this remains honest: a record marked ``dominated`` means the
    current local upper-side evidence dominates that *listed* challenger, not
    that a final theorem has promoted the surrounding challenger region.  To
    clear the theorem-side pruning burden one must provide the explicit set of
    labels whose dominated regions have been promoted theoremically.
    """
    theorem_level_labels = {str(x) for x in (theorem_level_dominated_labels or [])}
    dominated_labels = [str(r.get("label", r.get("class_label", "unknown"))) for r in records if str(r.get("status", r.get("pruning_status", ""))) == "dominated"]
    unresolved_labels = [str(r.get("label", r.get("class_label", "unknown"))) for r in records if str(r.get("status", r.get("pruning_status", ""))) != "dominated"]
    theorem_level_available = all(label in theorem_level_labels for label in dominated_labels)
    if dominated_labels and theorem_level_available:
        status = "theorem-level-dominated-regions-certified"
    elif dominated_labels:
        status = "dominated-regions-identified-but-not-promoted"
    else:
        status = "no-dominated-regions-yet"
    return {
        "status": status,
        "dominated_labels": dominated_labels,
        "unresolved_labels": unresolved_labels,
        "theorem_level_dominated_labels": sorted(theorem_level_labels),
        "proves_theorem_level_pruning_of_dominated_regions": theorem_level_available and len(dominated_labels) > 0,
        "notes": (
            "This certificate distinguishes classes that are already locally dominated by current upper-side evidence "
            "from classes whose surrounding challenger regions have actually been promoted to theorem-level dominated regions."
        ),
    }


def build_challenger_pruning_report(
    challengers: Sequence[ChallengerSpec],
    *,
    golden_lower_bound: float,
    dps: int = 160,
    burn_in_cycles: int = 12,
    eta_reference_golden: float = 1.0 / (5.0 ** 0.5),
    theorem_level_dominated_labels: Iterable[str] | None = None,
) -> ChallengerPruningReport:
    """Build a theorem-facing pruning table from challenger arithmetic + bounds."""
    records: list[dict[str, Any]] = []
    dominated = overlapping = arithmetic_only = undecided = 0
    for spec in challengers:
        arith = periodic_class_eta_interval(
            period=spec.period,
            preperiod=spec.preperiod,
            dps=dps,
            burn_in_cycles=burn_in_cycles,
        )
        status, reason = classify_challenger_against_golden(
            golden_lower_bound=golden_lower_bound,
            eta_lo=float(arith["eta_lo"]),
            eta_hi=float(arith["eta_hi"]),
            threshold_upper_bound=spec.threshold_upper_bound,
            threshold_lower_bound=spec.threshold_lower_bound,
            eta_reference_golden=eta_reference_golden,
        )
        if status == "dominated":
            dominated += 1
        elif status == "overlapping":
            overlapping += 1
        elif status == "arithmetic-weaker-only":
            arithmetic_only += 1
        else:
            undecided += 1
        records.append(
            ChallengerRecord(
                label=spec.normalized_label(),
                preperiod=tuple(spec.preperiod),
                period=tuple(spec.period),
                rho=float(arith["rho"]),
                eta_lo=float(arith["eta_lo"]),
                eta_hi=float(arith["eta_hi"]),
                eta_center=float(arith["eta_center"]),
                arithmetic_method=str(arith["method"]),
                threshold_lower_bound=None if spec.threshold_lower_bound is None else float(spec.threshold_lower_bound),
                threshold_upper_bound=None if spec.threshold_upper_bound is None else float(spec.threshold_upper_bound),
                status=status,
                reason=reason,
            ).to_dict()
        )
    records.sort(key=lambda r: (r["status"], r["threshold_upper_bound"] is None, -(r["eta_lo"]), r["label"]))
    if dominated and dominated == len(records):
        overall_status = "all-listed-challengers-dominated"
    elif dominated:
        overall_status = "partially-pruned"
    else:
        overall_status = "no-threshold-pruning-yet"
    notes = (
        "This is a challenger-pruning scaffold, not the final envelope theorem. It combines exact-periodic arithmetic summaries "
        "with whatever certified threshold upper bounds are currently available."
    )
    theorem_level_pruning_certificate = build_theorem_level_pruning_certificate(
        records,
        theorem_level_dominated_labels=theorem_level_dominated_labels,
    )
    return ChallengerPruningReport(
        golden_lower_bound=float(golden_lower_bound),
        records=records,
        dominated_count=int(dominated),
        overlapping_count=int(overlapping),
        arithmetic_only_count=int(arithmetic_only),
        undecided_count=int(undecided),
        theorem_level_pruning_certificate=theorem_level_pruning_certificate,
        status=overall_status,
        notes=notes,
    )


def extract_challengers_from_atlas(
    atlas: dict[str, Any],
    *,
    class_map: dict[str, tuple[tuple[int, ...], tuple[int, ...]]],
) -> list[ChallengerSpec]:
    """Convert an obstruction atlas into challenger specs for pruning.

    ``class_map`` maps atlas labels (e.g. ``"3/5"`` or ``"silver 12/29"``) to
    continued-fraction classes ``(preperiod, period)``. This keeps the pruning
    layer agnostic about how the atlas entries were generated.
    """
    out: list[ChallengerSpec] = []
    for entry in atlas.get("approximants", []):
        label = str(entry.get("label"))
        if label not in class_map:
            continue
        pre, per = class_map[label]
        upper = entry.get("crossing_root_window_hi")
        lower = entry.get("crossing_root_window_lo")
        out.append(
            ChallengerSpec(
                preperiod=tuple(pre),
                period=tuple(per),
                threshold_lower_bound=None if lower is None else float(lower),
                threshold_upper_bound=None if upper is None else float(upper),
                label=label,
            )
        )
    return out


__all__ = [
    "ChallengerSpec",
    "ChallengerRecord",
    "ChallengerPruningReport",
    "classify_challenger_against_golden",
    "build_theorem_level_pruning_certificate",
    "build_challenger_pruning_report",
    "extract_challengers_from_atlas",
]
