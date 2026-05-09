from __future__ import annotations

"""Phase-2G adaptive refinement for lower-anchor failures.

Phase 2F made full-grid execution resumable.  Phase 2G is the diagnostic and
repair layer used after a full-grid or chunk merge fails: it identifies the
first theorem-relevant blocker, classifies the failure, proposes a local refined
segment plan, and emits deterministic rerun commands.  It deliberately does not
promote anything.  A refined chunk must still be merged into a complete
Phase-2E candidate and consumed by strict Phase-2B ingestion.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import csv
import json
import math

DEFAULT_FINAL_ANCHOR = (0.9716350, 0.9716360)
DEFAULT_N_VALUES = (64, 96, 128, 192, 256, 384, 512)


@dataclass(frozen=True)
class SegmentDiagnostic:
    segment_id: str
    K_lo: float | None
    K_hi: float | None
    K_mid: float | None
    theorem_ready: bool
    finite_success: bool | None
    closure_level: str
    margin: float | None
    failure_type: str
    failure_reasons: tuple[str, ...]
    suggested_action: str
    priority: int

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["failure_reasons"] = list(self.failure_reasons)
        return d


@dataclass(frozen=True)
class RefinementSegment:
    segment_id: str
    K_lo: float
    K_hi: float
    K_mid: float
    source_failure: str
    source_segment_id: str
    recommended_N_values: tuple[int, ...]
    recommended_oversample_factor: int
    recommended_sigma_cap: float
    recommended_subdivision_index: int
    recommended_subdivision_count: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["recommended_N_values"] = list(self.recommended_N_values)
        return d


@dataclass(frozen=True)
class Phase2GRefinementPlan:
    schema: str
    source_candidate: str
    source_plan: str | None
    final_anchor: tuple[float, float]
    coverage_interval: tuple[float, float] | None
    first_blocker: dict[str, Any] | None
    diagnostics: tuple[SegmentDiagnostic, ...]
    link_failures: tuple[dict[str, Any], ...]
    refinement_segments: tuple[RefinementSegment, ...]
    failure_fields: tuple[str, ...]
    recommendations: tuple[str, ...]

    @property
    def actionable(self) -> bool:
        return bool(self.refinement_segments)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_candidate": self.source_candidate,
            "source_plan": self.source_plan,
            "final_anchor": list(self.final_anchor),
            "coverage_interval": None if self.coverage_interval is None else list(self.coverage_interval),
            "first_blocker": self.first_blocker,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "link_failures": list(self.link_failures),
            "refinement_segments": [s.to_dict() for s in self.refinement_segments],
            "failure_fields": list(self.failure_fields),
            "recommendations": list(self.recommendations),
            "actionable": self.actionable,
        }


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object at {path}")
    return data


def _rows(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = candidate.get("anchor_segments", candidate.get("segments", candidate.get("candidate_segments", [])))
    if not isinstance(raw, list):
        raise ValueError("candidate does not contain an anchor segment list")
    return [dict(x) for x in raw]


def _planned_rows(plan: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not plan:
        return []
    raw = plan.get("segments", [])
    if not isinstance(raw, list):
        return []
    return [dict(x) for x in raw]


def recompute_radii_margin(row: Mapping[str, Any]) -> float | None:
    try:
        r = float(row.get("radius_r", row.get("r")))
        y = float(row.get("residual_Y", row.get("Y")))
        z = float(row.get("linear_defect_Z", row.get("Z")))
        t = float(row.get("tail_bound_T", row.get("T", row.get("tail_majorant"))))
    except Exception:
        return None
    margin = r - (y + z * r + t)
    return margin if math.isfinite(margin) else None


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "1", "yes"}:
            return True
        if v in {"false", "0", "no"}:
            return False
    return bool(value)


def classify_segment(row: Mapping[str, Any], *, tolerance: float = 1.0e-12) -> SegmentDiagnostic:
    sid = str(row.get("segment_id", row.get("id", "<missing-segment-id>")))
    def f(key: str) -> float | None:
        try:
            value = row.get(key)
            if value is None:
                return None
            out = float(value)
            return out if math.isfinite(out) else None
        except Exception:
            return None
    K_lo, K_hi, K_mid = f("K_lo"), f("K_hi"), f("K_mid")
    margin = recompute_radii_margin(row)
    stored_margin = f("radii_margin")
    reasons = tuple(str(x) for x in row.get("failure_reasons", []) or [])
    finite_success = _bool_or_none(row.get("finite_success", row.get("finite_dimensional_success")))
    certified = bool(row.get("certified", False))
    theorem_ready = bool(row.get("theorem_ready", certified))
    finite_dimensional_only = bool(row.get("finite_dimensional_only", False))
    closure_level = str(row.get("closure_level", ""))

    failure_type = "ready"
    priority = 1000
    action = "No action required."
    if K_lo is None or K_hi is None or K_mid is None or K_lo >= K_hi:
        failure_type = "row_payload_incomplete"
        priority = 0
        action = "Regenerate this row because it lacks a valid K interval."
    elif finite_success is False or "finite_validator_failed" in reasons:
        failure_type = "finite_validator_failed"
        priority = 1
        action = "Bisect the interval and rerun with larger N and oversampling; branch seed/finite solve is the first failure."
    elif finite_dimensional_only:
        failure_type = "finite_dimensional_only"
        priority = 2
        action = "Rerun with the Phase-2E direct analytic radii ledger enabled and reject finite-dimensional-only output."
    elif closure_level != "analytic_theorem_closure":
        failure_type = "not_analytic_closure"
        priority = 3
        action = "Rerun locally with analytic theorem closure enabled; the row is not promotable as an analytic certificate."
    elif margin is None:
        failure_type = "margin_terms_missing"
        priority = 4
        action = "Regenerate the row with explicit residual_Y, linear_defect_Z, tail_bound_T, and radius_r fields."
    elif margin <= max(tolerance, 0.0):
        if stored_margin is not None and abs(stored_margin - margin) > 1.0e-10:
            failure_type = "stored_margin_mismatch"
            priority = 5
            action = "Rebuild the candidate so stored and recomputed radii margins agree before refinement."
        elif finite_success is True:
            failure_type = "analytic_margin_failure"
            priority = 6
            action = "Finite branch appears viable but analytic majorants are too large; bisect and escalate N/oversampling."
        else:
            failure_type = "phase2b_margin_failure"
            priority = 7
            action = "Rerun with smaller K width and stronger analytic majorants; strict Phase-2B margin is nonpositive."
    elif not theorem_ready or not certified:
        failure_type = "status_not_theorem_ready"
        priority = 8
        action = "The raw terms look positive, but status fields are not theorem-ready; regenerate or inspect validator status logic."

    return SegmentDiagnostic(
        segment_id=sid,
        K_lo=K_lo,
        K_hi=K_hi,
        K_mid=K_mid,
        theorem_ready=bool(failure_type == "ready" and theorem_ready and certified),
        finite_success=finite_success,
        closure_level=closure_level,
        margin=margin,
        failure_type=failure_type,
        failure_reasons=reasons,
        suggested_action=action,
        priority=priority,
    )


def _escalated_N_values(row: Mapping[str, Any] | None, base: Sequence[int]) -> tuple[int, ...]:
    values = {int(x) for x in base}
    if row is not None:
        try:
            n = int(row.get("N", row.get("selected_N", 0)) or 0)
            if n > 0:
                values.update({n, max(n * 2, 64), max(n * 3, 96)})
        except Exception:
            pass
    values.update({256, 384, 512})
    return tuple(sorted(x for x in values if x > 0))


def _subdivide_interval(
    *,
    row: Mapping[str, Any],
    diag: SegmentDiagnostic,
    subdivisions: int,
    overlap: float,
    n_values: Sequence[int],
    oversample_factor: int,
    sigma_cap: float,
) -> list[RefinementSegment]:
    if diag.K_lo is None or diag.K_hi is None:
        return []
    count = max(1, int(subdivisions))
    lo = float(diag.K_lo)
    hi = float(diag.K_hi)
    width = hi - lo
    if width <= 0.0:
        return []
    rec_N = _escalated_N_values(row, n_values)
    out: list[RefinementSegment] = []
    for j in range(count):
        raw_lo = lo + width * j / count
        raw_hi = lo + width * (j + 1) / count
        seg_lo = raw_lo - (overlap if j > 0 else 0.0)
        seg_hi = raw_hi + (overlap if j < count - 1 else 0.0)
        seg_mid = 0.5 * (raw_lo + raw_hi)
        out.append(RefinementSegment(
            segment_id=f"phase2g_refine_{diag.segment_id}_part_{j:03d}",
            K_lo=float(seg_lo),
            K_hi=float(seg_hi),
            K_mid=float(seg_mid),
            source_failure=diag.failure_type,
            source_segment_id=diag.segment_id,
            recommended_N_values=rec_N,
            recommended_oversample_factor=max(oversample_factor, 16),
            recommended_sigma_cap=float(sigma_cap),
            recommended_subdivision_index=j,
            recommended_subdivision_count=count,
            rationale=diag.suggested_action,
        ))
    return out


def _find_link_failures(sorted_rows: Sequence[Mapping[str, Any]], diags_by_id: Mapping[str, SegmentDiagnostic]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for a, b in zip(sorted_rows, sorted_rows[1:]):
        sid_a = str(a.get("segment_id", a.get("id", "<a>")))
        sid_b = str(b.get("segment_id", b.get("id", "<b>")))
        da = diags_by_id.get(sid_a)
        db = diags_by_id.get(sid_b)
        if da is None or db is None or da.K_hi is None or db.K_lo is None:
            continue
        overlap = da.K_hi - db.K_lo
        if not math.isfinite(overlap) or overlap <= 0.0:
            failures.append({
                "failure_type": "nonpositive_overlap",
                "left_segment_id": sid_a,
                "right_segment_id": sid_b,
                "left_K_hi": da.K_hi,
                "right_K_lo": db.K_lo,
                "overlap": overlap,
            })
    return failures


def build_phase2g_refinement_plan(
    candidate: Mapping[str, Any],
    *,
    candidate_path: str | Path = "<in-memory-candidate>",
    plan: Mapping[str, Any] | None = None,
    plan_path: str | Path | None = None,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
    subdivisions: int = 2,
    near_critical_subdivisions: int = 4,
    overlap: float = 1.0e-7,
    n_values: Sequence[int] = DEFAULT_N_VALUES,
    oversample_factor: int = 16,
    sigma_cap: float = 0.02,
    tolerance: float = 1.0e-12,
) -> Phase2GRefinementPlan:
    rows = _rows(candidate)
    sorted_rows = sorted(rows, key=lambda r: (float(r.get("K_lo", float("inf"))), float(r.get("K_hi", float("inf"))), str(r.get("segment_id", ""))))
    diagnostics = tuple(classify_segment(r, tolerance=tolerance) for r in sorted_rows)
    diags_by_id = {d.segment_id: d for d in diagnostics}
    link_failures = tuple(_find_link_failures(sorted_rows, diags_by_id))
    coverage = None
    valid_lo = [d.K_lo for d in diagnostics if d.K_lo is not None]
    valid_hi = [d.K_hi for d in diagnostics if d.K_hi is not None]
    if valid_lo and valid_hi:
        coverage = (float(min(valid_lo)), float(max(valid_hi)))
    final_lo, final_hi = float(final_anchor[0]), float(final_anchor[1])
    final_reached = bool(coverage is not None and coverage[0] <= final_lo and coverage[1] >= final_hi)

    failure_fields: list[str] = []
    if not rows:
        failure_fields.append("candidate_has_no_anchor_segments")
    if any(d.failure_type != "ready" for d in diagnostics):
        failure_fields.append("candidate_has_nonready_segments")
    if link_failures:
        failure_fields.append("candidate_has_nonpositive_overlap_links")
    if not final_reached:
        failure_fields.append("candidate_does_not_reach_final_anchor")

    blocker: dict[str, Any] | None = None
    refinement_segments: list[RefinementSegment] = []
    nonready = [d for d in diagnostics if d.failure_type != "ready"]
    if nonready:
        first = min(nonready, key=lambda d: (d.priority, float("inf") if d.K_lo is None else d.K_lo))
        blocker = {"kind": "segment", **first.to_dict()}
        source_row = next((r for r in sorted_rows if str(r.get("segment_id", r.get("id", ""))) == first.segment_id), {})
        split_count = near_critical_subdivisions if first.K_hi is not None and first.K_hi >= 0.970 else subdivisions
        refinement_segments.extend(_subdivide_interval(
            row=source_row,
            diag=first,
            subdivisions=split_count,
            overlap=overlap,
            n_values=n_values,
            oversample_factor=oversample_factor,
            sigma_cap=sigma_cap,
        ))
    elif link_failures:
        lf = link_failures[0]
        blocker = {"kind": "link", **lf}
        lo = float(lf["left_K_hi"]) - float(overlap)
        hi = float(lf["right_K_lo"]) + float(overlap)
        if lo < hi:
            refinement_segments.append(RefinementSegment(
                segment_id=f"phase2g_overlap_bridge_{lf['left_segment_id']}_to_{lf['right_segment_id']}",
                K_lo=lo,
                K_hi=hi,
                K_mid=0.5 * (lo + hi),
                source_failure="nonpositive_overlap",
                source_segment_id=f"{lf['left_segment_id']}->{lf['right_segment_id']}",
                recommended_N_values=tuple(sorted(set(int(x) for x in n_values) | {256, 384, 512})),
                recommended_oversample_factor=max(oversample_factor, 16),
                recommended_sigma_cap=float(sigma_cap),
                recommended_subdivision_index=0,
                recommended_subdivision_count=1,
                rationale="Bridge the gap between adjacent analytic balls before re-merging the candidate.",
            ))
    elif not final_reached:
        blocker = {"kind": "coverage", "failure_type": "final_anchor_not_reached", "coverage_interval": None if coverage is None else list(coverage), "final_anchor": [final_lo, final_hi]}
        completed_hi = coverage[1] if coverage is not None else None
        planned = _planned_rows(plan)
        remaining = []
        if completed_hi is not None and planned:
            for pr in planned:
                try:
                    if float(pr["K_hi"]) > float(completed_hi) + 1.0e-14:
                        remaining.append(pr)
                except Exception:
                    continue
        if not remaining:
            start = final_lo if completed_hi is None else min(float(completed_hi) - overlap, final_lo)
            remaining = [{"segment_id": "phase2g_missing_final_anchor_segment", "K_lo": start, "K_hi": final_hi, "K_mid": 0.5 * (start + final_hi)}]
        for idx, pr in enumerate(remaining):
            lo = float(pr["K_lo"])
            hi = float(pr["K_hi"])
            mid = float(pr.get("K_mid", 0.5 * (lo + hi)))
            refinement_segments.append(RefinementSegment(
                segment_id=f"phase2g_complete_{str(pr.get('segment_id', idx))}",
                K_lo=lo,
                K_hi=hi,
                K_mid=mid,
                source_failure="final_anchor_not_reached",
                source_segment_id=str(pr.get("segment_id", "missing-plan-segment")),
                recommended_N_values=tuple(sorted(set(int(x) for x in n_values) | {256, 384, 512})),
                recommended_oversample_factor=max(oversample_factor, 16),
                recommended_sigma_cap=float(sigma_cap),
                recommended_subdivision_index=idx,
                recommended_subdivision_count=len(remaining),
                rationale="Continue the full grid until the final anchor is covered, then merge and run strict Phase-2B ingestion.",
            ))

    recs = [
        "Run each Phase-2G refinement segment as a diagnostic chunk; do not promote it directly.",
        "Merge refined chunks with all earlier theorem-ready chunks; then run strict Phase-2B ingestion.",
        "If a refined segment still has finite success but analytic failure, reduce the K width again and increase N/oversampling rather than weakening strict checks.",
    ]
    return Phase2GRefinementPlan(
        schema="phase2g_lower_anchor_adaptive_refinement_plan_v1",
        source_candidate=str(candidate_path),
        source_plan=None if plan_path is None else str(plan_path),
        final_anchor=(final_lo, final_hi),
        coverage_interval=coverage,
        first_blocker=blocker,
        diagnostics=diagnostics,
        link_failures=link_failures,
        refinement_segments=tuple(refinement_segments),
        failure_fields=tuple(failure_fields),
        recommendations=tuple(recs),
    )


def write_phase2g_refinement_outputs(
    refinement_plan: Phase2GRefinementPlan,
    *,
    out_json: str | Path,
    out_csv: str | Path | None = None,
    out_shell: str | Path | None = None,
    repo_root: str | Path = ".",
    out_dir: str = "artifacts/proof_audit/lower_corridor/phase2g_refinements",
    table_dir: str = "tables/proof_audit/lower_corridor/phase2g_refinements",
) -> dict[str, str | bool | int]:
    out_json = Path(out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(refinement_plan.to_dict(), indent=2, sort_keys=True) + "\n")
    summary: dict[str, str | bool | int] = {
        "plan_path": str(out_json),
        "actionable": refinement_plan.actionable,
        "refinement_segment_count": len(refinement_plan.refinement_segments),
    }
    if out_csv is not None:
        csv_path = Path(out_csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        fields = ["segment_id", "K_lo", "K_hi", "K_mid", "source_failure", "source_segment_id", "recommended_N_values", "recommended_oversample_factor", "recommended_sigma_cap", "rationale"]
        with csv_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for seg in refinement_plan.refinement_segments:
                row = seg.to_dict()
                row["recommended_N_values"] = ",".join(str(x) for x in seg.recommended_N_values)
                writer.writerow({k: row.get(k) for k in fields})
        summary["csv_path"] = str(csv_path)
    if out_shell is not None:
        sh_path = Path(out_shell)
        sh_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["#!/usr/bin/env bash", "set -euo pipefail", "", "# AUTO-GENERATED Phase-2G refinement rerun commands."]
        for idx, seg in enumerate(refinement_plan.refinement_segments):
            n_values = ",".join(str(x) for x in seg.recommended_N_values)
            candidate_name = f"{seg.segment_id}_candidate.json"
            lines.append(
                "python scripts/audit/run_lower_anchor_phase2g_segment.py "
                f"--segment-id {seg.segment_id} "
                f"--K-lo {seg.K_lo:.17g} --K-hi {seg.K_hi:.17g} --K-mid {seg.K_mid:.17g} "
                f"--N-values {n_values} --oversample-factor {seg.recommended_oversample_factor:d} "
                f"--sigma-cap {seg.recommended_sigma_cap:.17g} "
                f"--out-dir {out_dir} --table-dir {table_dir} --candidate-name {candidate_name}"
            )
        lines.append("")
        sh_path.write_text("\n".join(lines))
        try:
            sh_path.chmod(0o755)
        except Exception:
            pass
        summary["shell_path"] = str(sh_path)
    return summary


__all__ = [
    "DEFAULT_FINAL_ANCHOR",
    "DEFAULT_N_VALUES",
    "Phase2GRefinementPlan",
    "RefinementSegment",
    "SegmentDiagnostic",
    "build_phase2g_refinement_plan",
    "classify_segment",
    "load_json",
    "recompute_radii_margin",
    "write_phase2g_refinement_outputs",
]
