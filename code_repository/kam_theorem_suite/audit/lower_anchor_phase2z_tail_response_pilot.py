from __future__ import annotations

"""Phase 2Z pilot selection for collar-012b1 tail-response sharpening.

Phase 2Y showed that many collar-012b1 failures would close if the strict
modewise tail response were sharpened by roughly 5--10%, while N-lifting made
margins worse.  This module is a fail-closed *orchestration* layer: it selects
which existing microsegments should be rerun through the existing Phase-2N/O/P
pipeline using fixed N=1024 and deeper Phase-2P tail-response scans.

It does not alter theorem-facing inequalities and it does not promote any
candidate by sensitivity arithmetic.  A segment is closed only if the normal
Phase-2P candidate produced by the rerun is theorem_ready/promotion_allowed.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import math


@dataclass(frozen=True)
class Phase2ZSelection:
    index: int
    K_lo: float | None
    K_hi: float | None
    source_bucket: str
    recommended_upgrade: str | None
    original_margin: float | None
    original_q: float | None
    guard_factor_needed: float | None
    tail_response_factor_needed: float | None
    path: str | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, Mapping):
        raise ValueError(f"expected JSON object in {path}")
    return dict(data)


def write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(p)


def _finite_float(x: Any) -> float | None:
    try:
        y = float(x)
    except Exception:
        return None
    return y if math.isfinite(y) else None


def _finite_int(x: Any) -> int | None:
    y = _finite_float(x)
    return None if y is None else int(y)


def _rows(phase2y: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = phase2y.get("required_improvement_rows")
    if isinstance(rows, list):
        return [r for r in rows if isinstance(r, Mapping)]
    summary = phase2y.get("summary") if isinstance(phase2y.get("summary"), Mapping) else {}
    rows2 = summary.get("best_required_improvement_rows") if isinstance(summary, Mapping) else None
    if isinstance(rows2, list):
        return [r for r in rows2 if isinstance(r, Mapping)]
    return []


def select_phase2z_tail_response_indices(
    phase2y: Mapping[str, Any],
    *,
    max_indices: int = 74,
    q_target: float = 0.999,
    max_tail_factor_needed: float = 0.92,
    max_guard_factor_needed: float = 0.90,
    include_q_boundary_below_target: bool = True,
    include_tail_or_guard: bool = True,
    include_safe_q: bool = True,
) -> list[Phase2ZSelection]:
    """Select a deterministic first pilot set for the Phase-2Z rerun.

    Priority is given to rows that do *not* need a finite-q improvement, because
    these are the rows most likely to close from a true tail-response sharpening
    without diagonal finite-Krawczyk work.  The default threshold mirrors the
    Phase-2Y sensitivity result: a tail-response factor <= 0.92 or guard factor
    <= 0.90.
    """
    selected: list[Phase2ZSelection] = []
    seen: set[int] = set()
    allowed_buckets: set[str] = set()
    if include_q_boundary_below_target:
        allowed_buckets.add("q_boundary")
    if include_tail_or_guard:
        allowed_buckets.add("tail_or_guard_dominated")
    if include_safe_q:
        allowed_buckets.add("safe_q_small_gap")

    def priority(row: Mapping[str, Any]) -> tuple[float, float, int]:
        deficit = _finite_float(row.get("deficit"))
        tail_factor = _finite_float(row.get("tail_response_factor_needed"))
        guard_factor = _finite_float(row.get("guard_factor_needed"))
        idx = _finite_int(row.get("index")) or 10**9
        # Lower factor means a larger required improvement; prefer smaller deficit first.
        return (float("inf") if deficit is None else deficit, float("inf") if tail_factor is None else tail_factor, idx)

    candidates = sorted(_rows(phase2y), key=priority)
    for row in candidates:
        idx = _finite_int(row.get("index"))
        if idx is None or idx in seen:
            continue
        q = _finite_float(row.get("finite_contraction_q"))
        if q is None or q >= float(q_target):
            continue
        bucket = str(row.get("bucket"))
        if bucket not in allowed_buckets:
            continue
        tail_factor = _finite_float(row.get("tail_response_factor_needed"))
        guard_factor = _finite_float(row.get("guard_factor_needed"))
        rec = str(row.get("recommended_upgrade") or "")
        eligible_tail = tail_factor is not None and tail_factor >= 0.0 and tail_factor <= max_tail_factor_needed
        eligible_guard = guard_factor is not None and guard_factor >= 0.0 and guard_factor <= max_guard_factor_needed
        if not (eligible_tail or eligible_guard or rec in {"modewise_tail_response_sharpening", "coefficient_aware_nonlinear_guard"}):
            continue
        reason = "tail_response_first" if eligible_tail else "guard_first"
        selected.append(Phase2ZSelection(
            index=idx,
            K_lo=_finite_float(row.get("K_lo")),
            K_hi=_finite_float(row.get("K_hi")),
            source_bucket=bucket,
            recommended_upgrade=None if not rec else rec,
            original_margin=_finite_float(row.get("radii_margin")),
            original_q=q,
            guard_factor_needed=guard_factor,
            tail_response_factor_needed=tail_factor,
            path=None if row.get("path") is None else str(row.get("path")),
            reason=reason,
        ))
        seen.add(idx)
        if len(selected) >= int(max_indices):
            break
    return selected


def build_phase2z_plan(
    *,
    phase2y_path: str | Path,
    summary_path: str,
    seed_json: str,
    label: str,
    max_indices: int = 74,
    workers: int = 64,
    q_target: float = 0.999,
    max_tail_factor_needed: float = 0.92,
    max_guard_factor_needed: float = 0.90,
    tail_cutoffs: str = "1536,2048,3072,4096,6144,8192,12288",
    phase2p_sigma_values: str = "0.0000001,0.000000075,0.00000005,0.000000025",
    phase2o_sigma_values: str = "0.0000001,0.00000025,0.0000005,0.000001",
    radius_multipliers: str = "0.95,0.98,1.0,1.02,1.04,1.06,1.08,1.1,1.12,1.14,1.16,1.18,1.2,1.25,1.3",
) -> dict[str, Any]:
    phase2y = load_json(phase2y_path)
    selections = select_phase2z_tail_response_indices(
        phase2y,
        max_indices=max_indices,
        q_target=q_target,
        max_tail_factor_needed=max_tail_factor_needed,
        max_guard_factor_needed=max_guard_factor_needed,
    )
    indices = ",".join(str(s.index) for s in selections)
    command = [
        "python", "scripts/audit/run_lower_anchor_phase2x_weighted_rescue.py",
        "--summary", summary_path,
        "--label", label,
        "--seed-json", seed_json,
        "--indices", indices,
        "--top-k", str(len(selections)),
        "--workers", str(workers),
        "--profile", "weighted",
        "--n-values", "1024",
        "--tail-cutoffs", tail_cutoffs,
        "--phase2p-sigma-values", phase2p_sigma_values,
        "--phase2o-sigma-values", phase2o_sigma_values,
        "--radius-multipliers", radius_multipliers,
    ]
    bucket_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    for s in selections:
        bucket_counts[s.source_bucket] = bucket_counts.get(s.source_bucket, 0) + 1
        reason_counts[s.reason] = reason_counts.get(s.reason, 0) + 1
    return {
        "schema": "phase2z_tail_response_pilot_plan_v1",
        "status": "phase2z-plan-ready" if selections else "phase2z-no-selected-indices",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "phase2y_path": str(phase2y_path),
        "summary_path": str(summary_path),
        "seed_json": str(seed_json),
        "label": str(label),
        "selected_count": len(selections),
        "indices_csv": indices,
        "bucket_counts": bucket_counts,
        "reason_counts": reason_counts,
        "parameters": {
            "q_target": q_target,
            "max_indices": max_indices,
            "max_tail_factor_needed": max_tail_factor_needed,
            "max_guard_factor_needed": max_guard_factor_needed,
            "workers": workers,
            "tail_cutoffs": tail_cutoffs,
            "phase2p_sigma_values": phase2p_sigma_values,
            "phase2o_sigma_values": phase2o_sigma_values,
            "radius_multipliers": radius_multipliers,
        },
        "selected_records": [s.to_dict() for s in selections],
        "command": command,
        "command_string": " ".join(command),
        "notes": [
            "This plan intentionally fixes N=1024 because the N=1536 lift worsened margins.",
            "This rerun is fail-closed: only ordinary Phase-2P theorem_ready candidates may close.",
            "If this closes few or no rows, proceed to diagonal finite-Krawczyk rather than N=2048.",
        ],
    }


def summarize_phase2z_run(run_summary: Mapping[str, Any], plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    best = run_summary.get("best_failed_rows") if isinstance(run_summary.get("best_failed_rows"), list) else []
    return {
        "schema": "phase2z_tail_response_pilot_summary_v1",
        "status": run_summary.get("status"),
        "label": run_summary.get("label"),
        "selected_count": run_summary.get("selected_count"),
        "closed_count": run_summary.get("closed_count"),
        "pending_count": run_summary.get("pending_count"),
        "ready_candidates": run_summary.get("ready_candidates"),
        "plan_selected_count": None if plan is None else plan.get("selected_count"),
        "plan_bucket_counts": None if plan is None else plan.get("bucket_counts"),
        "best_failed_rows": best[:20],
        "recommendation": (
            "assemble_closed_candidates_or_expand_tail_response_pilot" if int(run_summary.get("closed_count") or 0) > 0
            else "proceed_to_diagonal_finite_krawczyk_or_true_tail_majorant_sharpening"
        ),
    }
