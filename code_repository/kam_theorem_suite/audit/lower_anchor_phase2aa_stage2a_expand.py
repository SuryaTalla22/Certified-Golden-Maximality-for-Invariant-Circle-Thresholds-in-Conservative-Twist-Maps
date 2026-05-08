from __future__ import annotations

"""Phase 2AA Stage 2A-Expand selection and report helpers.

This module is intentionally orchestration-only.  It does not change theorem
logic and it does not promote diagnostic closures.  Its purpose is to take the
Phase-2Y sensitivity/audit table, select a larger q-safe/tail-guard cohort,
and summarize the Stage-1B raw-payload export plus Stage-2A profiled-guard
results.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from collections import Counter, defaultdict
import json
import math

SCHEMA = "phase2aa_stage2a_expand_v1"


def as_mapping(x: Any) -> Mapping[str, Any]:
    return x if isinstance(x, Mapping) else {}


def finite_float(x: Any, default: float | None = None) -> float | None:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def finite_int(x: Any, default: int | None = None) -> int | None:
    y = finite_float(x)
    return default if y is None else int(y)


def load_json(path: str | Path) -> Any:
    p = Path(path)
    with p.open() as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True))


@dataclass(frozen=True)
class ExpandSelectionRow:
    index: int
    K_lo: float | None
    K_hi: float | None
    bucket: str
    radii_margin: float | None
    deficit: float | None
    finite_contraction_q: float | None
    tail_response_factor_needed: float | None
    tail_response_reduction_frac_needed: float | None
    guard_factor_needed: float | None
    guard_reduction_frac_needed: float | None
    tail_T_reduction_frac_needed: float | None
    recommended_upgrade: str
    closeable_by_tail_response_5pct: bool
    closeable_by_tail_response_10pct: bool
    closeable_by_guard_only_at_15pct: bool
    closeable_by_guard_only_at_20pct: bool
    priority_score: float
    path: str | None
    selection_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _row_index(row: Mapping[str, Any]) -> int | None:
    idx = finite_int(row.get("index"))
    if idx is not None:
        return idx
    # Fallback to parsing phase2v-style paths.
    import re
    m = re.search(r"_p(\d{4})_", str(row.get("path", "")))
    return None if not m else int(m.group(1))


def _bool(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        return x.strip().lower() in {"true", "1", "yes", "y"}
    return bool(x)


def _selection_priority(row: Mapping[str, Any], *, q_cutoff: float) -> tuple[float, str]:
    """Lower priority score is better.

    The priority favors rows that are q-safe, small-deficit, and Phase-2Y says
    can plausibly close under modest tail/guard sharpening.  This is still only
    a diagnostic selector; it is not a theorem criterion.
    """
    deficit = finite_float(row.get("deficit"), None)
    if deficit is None:
        margin = finite_float(row.get("radii_margin"), 0.0) or 0.0
        deficit = max(0.0, -margin)
    q = finite_float(row.get("finite_contraction_q"), 1.0)
    tail_factor_needed = finite_float(row.get("tail_response_factor_needed"), 0.0)
    guard_factor_needed = finite_float(row.get("guard_factor_needed"), 0.0)
    bucket = str(row.get("bucket", "unknown"))
    rec = str(row.get("recommended_upgrade", ""))

    closability_bonus = 0.0
    reasons: list[str] = []
    if _bool(row.get("closeable_by_tail_response_5pct")):
        closability_bonus -= 3.0
        reasons.append("tail_response_5pct_sensitive")
    if _bool(row.get("closeable_by_tail_response_10pct")):
        closability_bonus -= 2.0
        reasons.append("tail_response_10pct_sensitive")
    if _bool(row.get("closeable_by_guard_only_at_15pct")):
        closability_bonus -= 1.5
        reasons.append("guard_15pct_sensitive")
    if _bool(row.get("closeable_by_guard_only_at_20pct")):
        closability_bonus -= 0.75
        reasons.append("guard_20pct_sensitive")
    if rec == "coefficient_aware_nonlinear_guard":
        closability_bonus -= 1.0
        reasons.append("coefficient_guard_recommended")
    if rec == "modewise_tail_response_sharpening":
        closability_bonus -= 0.75
        reasons.append("tail_response_recommended")
    if bucket in {"safe_q_small_gap", "tail_or_guard_dominated", "q_boundary"}:
        closability_bonus -= 0.25
        reasons.append(f"bucket_{bucket}")

    # Penalize q close to the hard gate, but do not discard q<q_cutoff rows.
    q_penalty = 0.0 if q is None else max(0.0, (q - 0.98) * 10.0)
    # Penalize rows needing stronger hypothetical improvement.
    tf_penalty = 0.0 if tail_factor_needed is None else max(0.0, 0.90 - tail_factor_needed) * 10.0
    gf_penalty = 0.0 if guard_factor_needed is None else max(0.0, 0.80 - guard_factor_needed) * 5.0
    deficit_scale = 0.0 if deficit is None else math.log10(max(deficit, 1.0e-16)) + 16.0
    score = float(deficit_scale + q_penalty + tf_penalty + gf_penalty + closability_bonus)
    if not reasons:
        reasons.append("q_safe_tail_guard_screen")
    return score, ";".join(reasons)


def select_expand_rows(
    phase2y: Mapping[str, Any],
    *,
    max_indices: int = 96,
    q_cutoff: float = 0.999,
    max_tail_response_reduction: float = 0.25,
    max_guard_reduction: float = 0.35,
    include_recommended: Sequence[str] = (
        "coefficient_aware_nonlinear_guard",
        "modewise_tail_response_sharpening",
    ),
    include_buckets: Sequence[str] = (
        "safe_q_small_gap",
        "tail_or_guard_dominated",
        "q_boundary",
        "q_boundary_near_miss",
    ),
) -> list[ExpandSelectionRow]:
    rows = phase2y.get("required_improvement_rows", [])
    if not isinstance(rows, Sequence):
        rows = []
    selected: list[ExpandSelectionRow] = []
    seen: set[int] = set()

    include_recommended_set = {str(x) for x in include_recommended if str(x)}
    include_bucket_set = {str(x) for x in include_buckets if str(x)}

    for rr in rows:
        row = as_mapping(rr)
        idx = _row_index(row)
        if idx is None or idx in seen:
            continue
        q = finite_float(row.get("finite_contraction_q"), None)
        if q is None or q >= q_cutoff:
            continue
        if _bool(row.get("needs_finite_q_upgrade")):
            continue
        bucket = str(row.get("bucket", "unknown"))
        rec = str(row.get("recommended_upgrade", ""))
        tail_red = finite_float(row.get("tail_response_reduction_frac_needed"), None)
        guard_red = finite_float(row.get("guard_reduction_frac_needed"), None)
        # A row may pass because the recommended route is targeted, because it
        # lies in the relevant bucket set, or because its needed improvement is modest.
        route_ok = (rec in include_recommended_set) or (bucket in include_bucket_set)
        tail_ok = (tail_red is not None and tail_red <= max_tail_response_reduction)
        guard_ok = (guard_red is not None and guard_red <= max_guard_reduction)
        sensitivity_ok = any(_bool(row.get(k)) for k in (
            "closeable_by_tail_response_5pct",
            "closeable_by_tail_response_10pct",
            "closeable_by_guard_only_at_15pct",
            "closeable_by_guard_only_at_20pct",
        ))
        if not (route_ok and (tail_ok or guard_ok or sensitivity_ok)):
            continue
        score, reason = _selection_priority(row, q_cutoff=q_cutoff)
        selected.append(ExpandSelectionRow(
            index=idx,
            K_lo=finite_float(row.get("K_lo")),
            K_hi=finite_float(row.get("K_hi")),
            bucket=bucket,
            radii_margin=finite_float(row.get("radii_margin")),
            deficit=finite_float(row.get("deficit")),
            finite_contraction_q=q,
            tail_response_factor_needed=finite_float(row.get("tail_response_factor_needed")),
            tail_response_reduction_frac_needed=tail_red,
            guard_factor_needed=finite_float(row.get("guard_factor_needed")),
            guard_reduction_frac_needed=guard_red,
            tail_T_reduction_frac_needed=finite_float(row.get("tail_T_reduction_frac_needed")),
            recommended_upgrade=rec,
            closeable_by_tail_response_5pct=_bool(row.get("closeable_by_tail_response_5pct")),
            closeable_by_tail_response_10pct=_bool(row.get("closeable_by_tail_response_10pct")),
            closeable_by_guard_only_at_15pct=_bool(row.get("closeable_by_guard_only_at_15pct")),
            closeable_by_guard_only_at_20pct=_bool(row.get("closeable_by_guard_only_at_20pct")),
            priority_score=score,
            path=None if row.get("path") is None else str(row.get("path")),
            selection_reason=reason,
        ))
        seen.add(idx)

    selected.sort(key=lambda r: (r.priority_score, 1e9 if r.deficit is None else r.deficit, r.index))
    return selected[: max(0, int(max_indices))]


def build_expand_plan(
    *,
    phase2y_path: str | Path,
    max_indices: int = 96,
    q_cutoff: float = 0.999,
    max_tail_response_reduction: float = 0.25,
    max_guard_reduction: float = 0.35,
) -> dict[str, Any]:
    phase2y = as_mapping(load_json(phase2y_path))
    rows = select_expand_rows(
        phase2y,
        max_indices=max_indices,
        q_cutoff=q_cutoff,
        max_tail_response_reduction=max_tail_response_reduction,
        max_guard_reduction=max_guard_reduction,
    )
    indices = [r.index for r in rows]
    return {
        "schema": SCHEMA,
        "status": "phase2aa-stage2a-expand-plan-complete",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "inputs": {"phase2y": str(phase2y_path)},
        "parameters": {
            "max_indices": int(max_indices),
            "q_cutoff": float(q_cutoff),
            "max_tail_response_reduction": float(max_tail_response_reduction),
            "max_guard_reduction": float(max_guard_reduction),
        },
        "selected_count": len(rows),
        "selected_indices": indices,
        "selected_indices_csv": ",".join(str(i) for i in indices),
        "bucket_counts": dict(Counter(r.bucket for r in rows)),
        "recommended_upgrade_counts": dict(Counter(r.recommended_upgrade for r in rows)),
        "selection_reason_counts": dict(Counter(reason for r in rows for reason in r.selection_reason.split(";") if reason)),
        "selected_rows": [r.to_dict() for r in rows],
        "source_phase2y_summary": phase2y.get("summary", {}),
    }


def compact_json(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {"exists": False, "path": None}
    p = Path(path)
    if not p.exists():
        return {"exists": False, "path": str(p)}
    try:
        obj = as_mapping(load_json(p))
    except Exception as exc:
        return {"exists": True, "path": str(p), "error": repr(exc)}
    keys = [
        "status", "record_count", "candidate_count", "closed_count", "pending_count",
        "old_ledger_replay_passed_count", "q_safe_count", "q_blocked_count",
        "records_with_any_q_gated_diagnostic_closure",
        "records_with_any_tail_guard_diagnostic_closure_before_q_gate",
        "model_q_gated_close_counts", "model_tail_guard_close_counts",
        "model_mean_margin_improvements", "recommended_next_action_counts",
        "best_records_by_profiled_margin", "error_count", "missing_candidate_count",
        "summary_path",
    ]
    return {"exists": True, "path": str(p), "compact": {k: obj.get(k) for k in keys if k in obj}}


def build_expand_report(
    *,
    plan_path: str | Path,
    export_summary_path: str | Path | None = None,
    profiled_guard_path: str | Path | None = None,
) -> dict[str, Any]:
    plan = as_mapping(load_json(plan_path))
    profiled = compact_json(profiled_guard_path)
    export = compact_json(export_summary_path)

    compact_profiled = as_mapping(profiled.get("compact"))
    selected_count = finite_int(plan.get("selected_count"), 0) or 0
    diagnostic_closures = finite_int(compact_profiled.get("records_with_any_q_gated_diagnostic_closure"), 0) or 0
    old_replay_passed = finite_int(compact_profiled.get("old_ledger_replay_passed_count"), 0) or 0
    record_count = finite_int(compact_profiled.get("record_count"), 0) or 0

    if diagnostic_closures >= 8:
        next_action = "expanded_profiled_guard_promising_build_theorem_grade_tail_guard_majorant"
    elif diagnostic_closures >= 2:
        next_action = "expanded_profiled_guard_partially_promising_select_closed_clusters_and_theoremize"
    elif diagnostic_closures == 1:
        next_action = "only_one_expanded_closure_check_clustering_then_consider_stronger_tail_majorant"
    elif record_count > 0:
        next_action = "no_expanded_diagnostic_closure_move_to_true_tail_majorant_or_fhl_validator"
    else:
        next_action = "profiled_guard_not_run_or_no_records_fix_expand_pipeline"

    return {
        "schema": SCHEMA,
        "status": "phase2aa-stage2a-expand-report-complete",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "plan": {
            "path": str(plan_path),
            "selected_count": selected_count,
            "selected_indices": plan.get("selected_indices", []),
            "bucket_counts": plan.get("bucket_counts", {}),
            "recommended_upgrade_counts": plan.get("recommended_upgrade_counts", {}),
        },
        "export_summary": export,
        "profiled_guard": profiled,
        "derived": {
            "selected_count": selected_count,
            "profiled_record_count": record_count,
            "old_ledger_replay_passed_count": old_replay_passed,
            "diagnostic_closure_count": diagnostic_closures,
            "diagnostic_closure_fraction_of_selected": None if selected_count <= 0 else diagnostic_closures / selected_count,
            "old_ledger_replay_fraction": None if record_count <= 0 else old_replay_passed / record_count,
            "recommended_next_action": next_action,
        },
    }
