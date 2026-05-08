from __future__ import annotations

"""Phase 2Y lower-corridor validator-upgrade sensitivity tools.

This module is deliberately fail-closed.  It does **not** promote a Phase-2V
or Phase-2P failed row to theorem-facing status.  Its job is to turn the
collar-012b1 failure atlas into precise next-step proof obligations:

* how much of the nonlinear guard would have to be saved;
* how much of the tail response would have to be saved;
* how much the finite-contraction q ledger would have to improve; and
* which records are the best pilot anchors for a real coefficient-aware guard
  or a real diagonal/weighted finite-Krawczyk implementation.

The output is diagnostic/prototype evidence only.  A row marked
``sensitivity_closes=True`` means "this row would close under the stated
hypothetical guard/tail/q improvement"; it is not a theorem certificate.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import csv
import json
import math

try:
    from .lower_anchor_phase2x_weighted_finite import (
        FailedPieceRecord,
        load_json,
        records_from_summary,
        record_from_candidate,
        write_json,
    )
except Exception:  # pragma: no cover - supports direct importlib test loading
    from kam_theorem_suite.audit.lower_anchor_phase2x_weighted_finite import (
        FailedPieceRecord,
        load_json,
        records_from_summary,
        record_from_candidate,
        write_json,
    )

DEFAULT_GUARD_FACTORS: tuple[float, ...] = (
    1.0,
    0.95,
    0.9,
    0.85,
    0.8,
    0.75,
    0.7,
    0.65,
    0.6,
)
DEFAULT_TAIL_FACTORS: tuple[float, ...] = (1.0, 0.98, 0.96, 0.94, 0.92, 0.9)
DEFAULT_Q_FACTORS: tuple[float, ...] = (1.0, 0.999, 0.9975, 0.995, 0.9925, 0.99, 0.985, 0.98)

# Keep the same outward tolerance scale used by Phase 2P unless caller overrides.
DEFAULT_MARGIN_SAFETY = 0.0
DEFAULT_Q_TARGET = 0.999


@dataclass(frozen=True)
class RequiredImprovementRow:
    index: int | None
    K_lo: float | None
    K_hi: float | None
    path: str | None
    bucket: str
    failure_reasons: tuple[str, ...]
    model_name: str | None
    radii_margin: float | None
    deficit: float | None
    finite_contraction_q: float | None
    radius_r: float | None
    tail_T: float | None
    allowable_tail_max: float | None
    tail_response_bound: float | None
    nonlinear_guard: float | None
    guard_reduction_frac_needed: float | None
    guard_factor_needed: float | None
    tail_response_reduction_frac_needed: float | None
    tail_response_factor_needed: float | None
    tail_T_reduction_frac_needed: float | None
    q_reduction_needed_to_target: float | None
    q_factor_needed_to_target: float | None
    closeable_by_guard_only_at_10pct: bool
    closeable_by_guard_only_at_15pct: bool
    closeable_by_guard_only_at_20pct: bool
    closeable_by_tail_response_5pct: bool
    closeable_by_tail_response_10pct: bool
    needs_finite_q_upgrade: bool
    recommended_upgrade: str
    priority_score: float

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["failure_reasons"] = list(self.failure_reasons)
        return d


@dataclass(frozen=True)
class SensitivityTrial:
    index: int | None
    K_lo: float | None
    K_hi: float | None
    path: str | None
    original_bucket: str
    original_margin: float | None
    original_q: float | None
    guard_factor: float
    tail_response_factor: float
    q_factor: float
    profiled_guard: float | None
    profiled_tail_response: float | None
    profiled_tail_T: float | None
    profiled_q: float | None
    profiled_margin: float | None
    margin_passes: bool
    q_passes: bool
    sensitivity_closes: bool
    diagnostic_only: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _finite_float(x: Any, default: float | None = None) -> float | None:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _safe_div(num: float | None, den: float | None) -> float | None:
    if num is None or den is None:
        return None
    if den == 0.0 or not math.isfinite(den):
        return None
    return float(num) / float(den)


def _bucket_from_record(r: FailedPieceRecord) -> str:
    q = r.finite_contraction_q
    margin = r.radii_margin
    deficit = None if margin is None else max(0.0, -float(margin))
    if r.theorem_ready:
        return "already_closed"
    if q is not None and q >= 1.0:
        return "q_over_one"
    if q is not None and q >= 0.99:
        return "q_boundary"
    if deficit is not None and deficit <= 2.5e-8:
        return "safe_q_small_gap"
    return "tail_or_guard_dominated"


def build_required_improvement_row(
    record: FailedPieceRecord,
    *,
    q_target: float = DEFAULT_Q_TARGET,
    margin_safety: float = DEFAULT_MARGIN_SAFETY,
) -> RequiredImprovementRow:
    margin = record.radii_margin
    deficit = None if margin is None else max(0.0, margin_safety - float(margin))
    guard = record.nonlinear_guard
    tail_response = record.tail_response_bound
    tail_T = record.tail_T
    q = record.finite_contraction_q

    guard_reduction_frac_needed = _safe_div(deficit, guard)
    tail_response_reduction_frac_needed = _safe_div(deficit, tail_response)
    tail_T_reduction_frac_needed = _safe_div(deficit, tail_T)
    guard_factor_needed = None if guard_reduction_frac_needed is None else max(0.0, 1.0 - guard_reduction_frac_needed)
    tail_response_factor_needed = None if tail_response_reduction_frac_needed is None else max(0.0, 1.0 - tail_response_reduction_frac_needed)

    q_reduction_needed = None
    q_factor_needed = None
    if q is not None:
        q_reduction_needed = max(0.0, float(q) - float(q_target))
        q_factor_needed = min(1.0, float(q_target) / float(q)) if q > 0 else None

    bucket = _bucket_from_record(record)
    q_needs = bool(q is not None and q >= float(q_target))
    if q_needs and guard_reduction_frac_needed is not None and guard_reduction_frac_needed <= 0.20:
        rec = "combined_diagonal_q_plus_profiled_guard"
    elif q_needs:
        rec = "diagonal_or_weighted_finite_krawczyk"
    elif guard_reduction_frac_needed is not None and guard_reduction_frac_needed <= 0.20:
        rec = "coefficient_aware_nonlinear_guard"
    elif tail_response_reduction_frac_needed is not None and tail_response_reduction_frac_needed <= 0.10:
        rec = "modewise_tail_response_sharpening"
    else:
        rec = "lower_priority_after_core_validator_upgrade"

    # Prioritize tiny deficits, then records requiring only one type of upgrade.
    priority = float("inf")
    if deficit is not None:
        penalty = 0.0
        if q_needs:
            penalty += 1.0e-6
        if guard_reduction_frac_needed is None or guard_reduction_frac_needed > 0.25:
            penalty += 5.0e-7
        priority = float(deficit + penalty)

    return RequiredImprovementRow(
        index=record.index,
        K_lo=record.K_lo,
        K_hi=record.K_hi,
        path=record.path,
        bucket=bucket,
        failure_reasons=tuple(record.failure_reasons),
        model_name=record.model_name,
        radii_margin=record.radii_margin,
        deficit=deficit,
        finite_contraction_q=q,
        radius_r=record.radius_r,
        tail_T=tail_T,
        allowable_tail_max=record.allowable_tail_max,
        tail_response_bound=tail_response,
        nonlinear_guard=guard,
        guard_reduction_frac_needed=guard_reduction_frac_needed,
        guard_factor_needed=guard_factor_needed,
        tail_response_reduction_frac_needed=tail_response_reduction_frac_needed,
        tail_response_factor_needed=tail_response_factor_needed,
        tail_T_reduction_frac_needed=tail_T_reduction_frac_needed,
        q_reduction_needed_to_target=q_reduction_needed,
        q_factor_needed_to_target=q_factor_needed,
        closeable_by_guard_only_at_10pct=bool((not q_needs) and guard_reduction_frac_needed is not None and guard_reduction_frac_needed <= 0.10),
        closeable_by_guard_only_at_15pct=bool((not q_needs) and guard_reduction_frac_needed is not None and guard_reduction_frac_needed <= 0.15),
        closeable_by_guard_only_at_20pct=bool((not q_needs) and guard_reduction_frac_needed is not None and guard_reduction_frac_needed <= 0.20),
        closeable_by_tail_response_5pct=bool((not q_needs) and tail_response_reduction_frac_needed is not None and tail_response_reduction_frac_needed <= 0.05),
        closeable_by_tail_response_10pct=bool((not q_needs) and tail_response_reduction_frac_needed is not None and tail_response_reduction_frac_needed <= 0.10),
        needs_finite_q_upgrade=q_needs,
        recommended_upgrade=rec,
        priority_score=priority,
    )


def build_required_improvement_rows(
    records: Iterable[FailedPieceRecord],
    *,
    q_target: float = DEFAULT_Q_TARGET,
    margin_safety: float = DEFAULT_MARGIN_SAFETY,
) -> list[RequiredImprovementRow]:
    rows = [build_required_improvement_row(r, q_target=q_target, margin_safety=margin_safety) for r in records]
    rows.sort(key=lambda r: (r.priority_score, r.index if r.index is not None else 10**9))
    return rows


def sensitivity_trial(
    req: RequiredImprovementRow,
    *,
    guard_factor: float,
    tail_response_factor: float = 1.0,
    q_factor: float = 1.0,
    q_target: float = DEFAULT_Q_TARGET,
    margin_safety: float = DEFAULT_MARGIN_SAFETY,
) -> SensitivityTrial:
    guard = req.nonlinear_guard
    tail_resp = req.tail_response_bound
    q = req.finite_contraction_q
    allowable = req.allowable_tail_max
    if guard is None or tail_resp is None or allowable is None:
        prof_guard = prof_tail = prof_tail_T = prof_margin = None
    else:
        prof_guard = float(guard) * float(guard_factor)
        prof_tail = float(tail_resp) * float(tail_response_factor)
        prof_tail_T = prof_guard + prof_tail
        prof_margin = float(allowable) - prof_tail_T - float(margin_safety)
    prof_q = None if q is None else float(q) * float(q_factor)
    margin_passes = bool(prof_margin is not None and prof_margin > 0.0)
    q_passes = bool(prof_q is None or prof_q < float(q_target))
    closes = bool(margin_passes and q_passes)
    return SensitivityTrial(
        index=req.index,
        K_lo=req.K_lo,
        K_hi=req.K_hi,
        path=req.path,
        original_bucket=req.bucket,
        original_margin=req.radii_margin,
        original_q=req.finite_contraction_q,
        guard_factor=float(guard_factor),
        tail_response_factor=float(tail_response_factor),
        q_factor=float(q_factor),
        profiled_guard=prof_guard,
        profiled_tail_response=prof_tail,
        profiled_tail_T=prof_tail_T,
        profiled_q=prof_q,
        profiled_margin=prof_margin,
        margin_passes=margin_passes,
        q_passes=q_passes,
        sensitivity_closes=closes,
        diagnostic_only=True,
        notes="Hypothetical Phase-2Y sensitivity trial only; not a theorem-facing certificate.",
    )


def grid_sensitivity_trials(
    rows: Sequence[RequiredImprovementRow],
    *,
    guard_factors: Sequence[float] = DEFAULT_GUARD_FACTORS,
    tail_response_factors: Sequence[float] = (1.0,),
    q_factors: Sequence[float] = DEFAULT_Q_FACTORS,
    q_target: float = DEFAULT_Q_TARGET,
    margin_safety: float = DEFAULT_MARGIN_SAFETY,
    top_k: int | None = None,
) -> list[SensitivityTrial]:
    selected = list(rows[:top_k] if top_k is not None else rows)
    trials: list[SensitivityTrial] = []
    for row in selected:
        for gf in guard_factors:
            for tf in tail_response_factors:
                q_grid = q_factors if row.needs_finite_q_upgrade else (1.0,)
                for qf in q_grid:
                    trials.append(
                        sensitivity_trial(
                            row,
                            guard_factor=float(gf),
                            tail_response_factor=float(tf),
                            q_factor=float(qf),
                            q_target=q_target,
                            margin_safety=margin_safety,
                        )
                    )
    trials.sort(key=lambda t: (
        not t.sensitivity_closes,
        t.guard_factor,
        t.tail_response_factor,
        t.q_factor,
        abs(t.profiled_margin or -1e99),
    ))
    return trials


def minimal_closing_trials(trials: Sequence[SensitivityTrial]) -> list[SensitivityTrial]:
    by_key: dict[tuple[Any, Any, Any, str | None], SensitivityTrial] = {}
    for t in trials:
        if not t.sensitivity_closes:
            continue
        key = (t.index, t.K_lo, t.K_hi, t.path)
        old = by_key.get(key)
        if old is None:
            by_key[key] = t
            continue
        # Prefer the least aggressive improvement: max factors, then larger margin.
        old_score = (old.guard_factor + old.tail_response_factor + old.q_factor, old.profiled_margin or -1e99)
        new_score = (t.guard_factor + t.tail_response_factor + t.q_factor, t.profiled_margin or -1e99)
        if new_score > old_score:
            by_key[key] = t
    out = list(by_key.values())
    out.sort(key=lambda t: (t.guard_factor + t.tail_response_factor + t.q_factor, t.profiled_margin or -1e99), reverse=True)
    return out


def _records_from_autopsy_json(path: str | Path) -> list[FailedPieceRecord]:
    data = load_json(path)
    records: list[FailedPieceRecord] = []
    for item in data.get("rows", []) or []:
        if not isinstance(item, Mapping):
            continue
        rec = item.get("record")
        if not isinstance(rec, Mapping):
            continue
        records.append(
            FailedPieceRecord(
                index=rec.get("index"),
                label=rec.get("label"),
                segment_id=rec.get("segment_id"),
                path=rec.get("path"),
                K_lo=_finite_float(rec.get("K_lo")),
                K_hi=_finite_float(rec.get("K_hi")),
                K_mid=_finite_float(rec.get("K_mid")),
                theorem_ready=bool(rec.get("theorem_ready")),
                theorem_facing=bool(rec.get("theorem_facing")),
                promotion_allowed=bool(rec.get("promotion_allowed")),
                model_name=rec.get("model_name"),
                sigma=_finite_float(rec.get("sigma")),
                radius_r=_finite_float(rec.get("radius_r")),
                radius_multiplier=_finite_float(rec.get("radius_multiplier")),
                finite_contraction_q=_finite_float(rec.get("finite_contraction_q")),
                tail_cutoff=int(rec.get("tail_cutoff")) if rec.get("tail_cutoff") is not None else None,
                radii_margin=_finite_float(rec.get("radii_margin")),
                tail_T=_finite_float(rec.get("tail_T")),
                allowable_tail_max=_finite_float(rec.get("allowable_tail_max")),
                tail_response_bound=_finite_float(rec.get("tail_response_bound")),
                nonlinear_guard=_finite_float(rec.get("nonlinear_guard")),
                failure_reasons=tuple(rec.get("failure_reasons") or ()),
                source_kind="autopsy.rows",
            )
        )
    return records


def collect_records(*, summaries: Sequence[str | Path] = (), candidates: Sequence[str | Path] = (), autopsies: Sequence[str | Path] = ()) -> list[FailedPieceRecord]:
    records: list[FailedPieceRecord] = []
    for sp in summaries:
        records.extend(records_from_summary(sp))
    for ap in autopsies:
        records.extend(_records_from_autopsy_json(ap))
    for cp in candidates:
        records.append(record_from_candidate(cp, source_kind="phase2y_candidate_cli"))

    seen: set[tuple[Any, ...]] = set()
    deduped: list[FailedPieceRecord] = []
    for r in records:
        key = (r.path, r.index, r.K_lo, r.K_hi)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return deduped


def write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fieldnames), extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


REQUIRED_FIELDS = [
    "index", "K_lo", "K_hi", "path", "bucket", "recommended_upgrade", "priority_score",
    "radii_margin", "deficit", "finite_contraction_q", "q_reduction_needed_to_target",
    "q_factor_needed_to_target", "tail_T", "allowable_tail_max", "tail_response_bound",
    "nonlinear_guard", "guard_reduction_frac_needed", "guard_factor_needed",
    "tail_response_reduction_frac_needed", "tail_response_factor_needed", "tail_T_reduction_frac_needed",
    "closeable_by_guard_only_at_10pct", "closeable_by_guard_only_at_15pct",
    "closeable_by_guard_only_at_20pct", "closeable_by_tail_response_5pct",
    "closeable_by_tail_response_10pct", "needs_finite_q_upgrade", "failure_reasons", "model_name",
]

TRIAL_FIELDS = [
    "index", "K_lo", "K_hi", "path", "original_bucket", "original_margin", "original_q",
    "guard_factor", "tail_response_factor", "q_factor", "profiled_guard", "profiled_tail_response",
    "profiled_tail_T", "profiled_q", "profiled_margin", "margin_passes", "q_passes",
    "sensitivity_closes", "diagnostic_only", "notes",
]


def summarize_phase2y(rows: Sequence[RequiredImprovementRow], trials: Sequence[SensitivityTrial]) -> dict[str, Any]:
    by_bucket: dict[str, int] = {}
    by_rec: dict[str, int] = {}
    for r in rows:
        by_bucket[r.bucket] = by_bucket.get(r.bucket, 0) + 1
        by_rec[r.recommended_upgrade] = by_rec.get(r.recommended_upgrade, 0) + 1
    closing = minimal_closing_trials(trials)
    return {
        "row_count": len(rows),
        "bucket_counts": by_bucket,
        "recommended_upgrade_counts": by_rec,
        "guard_only_10pct_count": sum(r.closeable_by_guard_only_at_10pct for r in rows),
        "guard_only_15pct_count": sum(r.closeable_by_guard_only_at_15pct for r in rows),
        "guard_only_20pct_count": sum(r.closeable_by_guard_only_at_20pct for r in rows),
        "tail_response_5pct_count": sum(r.closeable_by_tail_response_5pct for r in rows),
        "tail_response_10pct_count": sum(r.closeable_by_tail_response_10pct for r in rows),
        "needs_finite_q_upgrade_count": sum(r.needs_finite_q_upgrade for r in rows),
        "sensitivity_closing_trial_count": sum(t.sensitivity_closes for t in trials),
        "minimal_closing_trial_record_count": len(closing),
        "best_required_improvement_rows": [r.to_dict() for r in rows[:25]],
        "minimal_closing_trials": [t.to_dict() for t in closing[:25]],
        "diagnostic_only": True,
    }


def build_phase2y_report(
    *,
    summaries: Sequence[str | Path] = (),
    autopsies: Sequence[str | Path] = (),
    candidates: Sequence[str | Path] = (),
    q_target: float = DEFAULT_Q_TARGET,
    margin_safety: float = DEFAULT_MARGIN_SAFETY,
    top_k_trials: int = 80,
    guard_factors: Sequence[float] = DEFAULT_GUARD_FACTORS,
    tail_response_factors: Sequence[float] = (1.0,),
    q_factors: Sequence[float] = DEFAULT_Q_FACTORS,
) -> dict[str, Any]:
    records = collect_records(summaries=summaries, candidates=candidates, autopsies=autopsies)
    rows = build_required_improvement_rows(records, q_target=q_target, margin_safety=margin_safety)
    trials = grid_sensitivity_trials(
        rows,
        guard_factors=guard_factors,
        tail_response_factors=tail_response_factors,
        q_factors=q_factors,
        q_target=q_target,
        margin_safety=margin_safety,
        top_k=top_k_trials,
    )
    return {
        "schema": "phase2y_validator_upgrade_sensitivity_v1",
        "status": "phase2y-diagnostic-complete",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "inputs": {
            "summaries": [str(x) for x in summaries],
            "autopsies": [str(x) for x in autopsies],
            "candidates": [str(x) for x in candidates],
        },
        "parameters": {
            "q_target": float(q_target),
            "margin_safety": float(margin_safety),
            "top_k_trials": int(top_k_trials),
            "guard_factors": list(map(float, guard_factors)),
            "tail_response_factors": list(map(float, tail_response_factors)),
            "q_factors": list(map(float, q_factors)),
        },
        "summary": summarize_phase2y(rows, trials),
        "required_improvement_rows": [r.to_dict() for r in rows],
        "sensitivity_trials": [t.to_dict() for t in trials],
        "minimal_closing_trials": [t.to_dict() for t in minimal_closing_trials(trials)],
        "next_code_actions": [
            "Implement a theorem-facing coefficient-aware nonlinear guard and first test rows with closeable_by_guard_only_at_10pct/15pct.",
            "Implement a real diagonal/weighted finite-Krawczyk norm for rows with needs_finite_q_upgrade=True.",
            "Do not treat this sensitivity report as a theorem certificate; rerun Phase 2P or a new theorem-facing validator after implementing the actual bounds.",
        ],
    }
