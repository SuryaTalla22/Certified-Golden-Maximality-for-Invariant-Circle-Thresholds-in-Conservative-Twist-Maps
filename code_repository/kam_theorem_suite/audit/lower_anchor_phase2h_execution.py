from __future__ import annotations

"""Phase-2H execution/merge controller for the lower-anchor proof chain.

Phase 2F/2G added the machinery needed to run the remaining Phase-2E
analytic lower-anchor segments.  This module is deliberately JSON-first and
fail-closed: it can inventory available chunk candidates, identify the missing
segments still needed to reach the final anchor, write a reproducible run script,
optionally merge all available candidates, and optionally run the strict
Phase-2B ingestion check.  It does not promote partial evidence.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import math
import shlex

DEFAULT_LOWER_DIR = Path("artifacts/proof_audit/lower_corridor")
DEFAULT_REFINEMENT_DIR = DEFAULT_LOWER_DIR / "phase2g_refinements"
DEFAULT_TABLE_DIR = Path("tables/proof_audit/lower_corridor/phase2g_refinements")
DEFAULT_FINAL_ANCHOR = (0.971635, 0.971636)


@dataclass(frozen=True)
class Phase2HSegmentStatus:
    index: int
    segment_id: str
    K_lo: float
    K_hi: float
    K_mid: float
    candidate_path: str | None
    present: bool
    theorem_ready: bool
    certified: bool
    finite_dimensional_only: bool
    closure_level: str | None
    margin: float | None
    failure_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["failure_reasons"] = list(self.failure_reasons)
        return data


@dataclass(frozen=True)
class Phase2HExecutionStatus:
    schema: str
    plan_path: str
    lower_dir: str
    refinement_dir: str
    final_anchor: tuple[float, float]
    segment_count: int
    ready_segment_count: int
    missing_segment_count: int
    failed_segment_count: int
    coverage_interval: tuple[float, float] | None
    final_anchor_reached_by_available_segments: bool
    merge_attempted: bool
    merged_candidate_path: str | None
    strict_ingestion_attempted: bool
    strict_ingestion_passed: bool | None
    promotion_allowed: bool
    failure_fields: tuple[str, ...]
    segments: tuple[Phase2HSegmentStatus, ...]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["final_anchor"] = list(self.final_anchor)
        data["coverage_interval"] = None if self.coverage_interval is None else list(self.coverage_interval)
        data["failure_fields"] = list(self.failure_fields)
        data["segments"] = [s.to_dict() for s in self.segments]
        data["recommendations"] = list(self.recommendations)
        return data


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object at {p}")
    return data


def candidate_rows(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = candidate.get("anchor_segments", candidate.get("segments", candidate.get("candidate_segments", [])))
    if not isinstance(rows, list):
        return []
    return [dict(r) for r in rows if isinstance(r, Mapping)]


def recompute_margin(row: Mapping[str, Any]) -> float | None:
    try:
        r = float(row.get("radius_r", row.get("r", 0.0)))
        y = float(row.get("residual_Y", row.get("Y", 0.0)))
        z = float(row.get("linear_defect_Z", row.get("Z", 0.0)))
        t = float(row.get("tail_bound_T", row.get("T", row.get("tail_majorant", 0.0))))
        margin = r - (y + z * r + t)
        return margin if math.isfinite(margin) else None
    except Exception:
        return None


def row_is_theorem_ready(row: Mapping[str, Any]) -> bool:
    margin = recompute_margin(row)
    return bool(
        row.get("certified", False)
        and not row.get("finite_dimensional_only", False)
        and str(row.get("closure_level", "")) == "analytic_theorem_closure"
        and margin is not None
        and margin > 0.0
    )


def _candidate_name_for_segment(segment_id: str) -> str:
    return f"phase2g_complete_{segment_id}_candidate.json"


def _candidate_paths_for_segment(segment_id: str, lower_dir: Path, refinement_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    candidates.append(lower_dir / _candidate_name_for_segment(segment_id))
    candidates.append(refinement_dir / _candidate_name_for_segment(segment_id))
    candidates.append(refinement_dir / f"{segment_id}_candidate.json")
    # Phase 2F shipped the first two records as one chunk rather than one file
    # per segment.  The inventory routine below also searches every available
    # JSON candidate, so this list is only the fast path.
    return candidates


def _all_candidate_files(lower_dir: Path, refinement_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in [lower_dir / "lower_anchor_phase2f_chunk_000_candidate.json", lower_dir / "lower_anchor_heavy_candidate.json"]:
        if p.exists():
            files.append(p)
    if refinement_dir.exists():
        for p in sorted(refinement_dir.glob("*_candidate.json")):
            if p not in files:
                files.append(p)
    return files


def _index_candidate_rows(paths: Sequence[Path]) -> tuple[dict[str, tuple[Path, dict[str, Any]]], list[str]]:
    rows_by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    diagnostics: list[str] = []
    for path in paths:
        try:
            data = load_json(path)
        except Exception as exc:
            diagnostics.append(f"{path}:unreadable:{exc!r}")
            continue
        for row in candidate_rows(data):
            sid = str(row.get("segment_id", ""))
            if not sid:
                continue
            old = rows_by_id.get(sid)
            if old is None:
                rows_by_id[sid] = (path, row)
            else:
                old_margin = recompute_margin(old[1])
                new_margin = recompute_margin(row)
                if (new_margin is not None and old_margin is None) or ((new_margin or -math.inf) > (old_margin or -math.inf)):
                    rows_by_id[sid] = (path, row)
    return rows_by_id, diagnostics


def build_phase2h_execution_status(
    *,
    plan_path: str | Path,
    lower_dir: str | Path = DEFAULT_LOWER_DIR,
    refinement_dir: str | Path = DEFAULT_REFINEMENT_DIR,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
    merged_candidate_path: str | Path | None = None,
    strict_ingestion_report_path: str | Path | None = None,
) -> Phase2HExecutionStatus:
    plan_p = Path(plan_path)
    lower_p = Path(lower_dir)
    refine_p = Path(refinement_dir)
    plan = load_json(plan_p)
    segments_raw = plan.get("segments", plan.get("refinement_segments", []))
    if not isinstance(segments_raw, list):
        raise ValueError("Phase-2H plan must contain a segment list")

    candidate_files = _all_candidate_files(lower_p, refine_p)
    rows_by_id, diagnostics = _index_candidate_rows(candidate_files)
    statuses: list[Phase2HSegmentStatus] = []
    ready_intervals: list[tuple[float, float]] = []
    for idx, seg in enumerate(segments_raw):
        if not isinstance(seg, Mapping):
            continue
        sid = str(seg.get("segment_id", f"segment_{idx:03d}"))
        K_lo = float(seg.get("K_lo"))
        K_hi = float(seg.get("K_hi"))
        K_mid = float(seg.get("K_mid", 0.5 * (K_lo + K_hi)))
        row_entry = rows_by_id.get(sid)
        if row_entry is None:
            status = Phase2HSegmentStatus(
                index=int(seg.get("index", idx)), segment_id=sid, K_lo=K_lo, K_hi=K_hi, K_mid=K_mid,
                candidate_path=None, present=False, theorem_ready=False, certified=False,
                finite_dimensional_only=False, closure_level=None, margin=None,
                failure_reasons=("candidate_missing",),
            )
        else:
            path, row = row_entry
            margin = recompute_margin(row)
            theorem_ready = row_is_theorem_ready(row)
            if theorem_ready:
                ready_intervals.append((float(row.get("K_lo", K_lo)), float(row.get("K_hi", K_hi))))
            reasons = tuple(str(x) for x in (row.get("failure_reasons", []) or []))
            if not theorem_ready and not reasons:
                reasons = ("candidate_present_but_not_theorem_ready",)
            status = Phase2HSegmentStatus(
                index=int(seg.get("index", idx)), segment_id=sid, K_lo=K_lo, K_hi=K_hi, K_mid=K_mid,
                candidate_path=path.as_posix(), present=True, theorem_ready=theorem_ready,
                certified=bool(row.get("certified", False)),
                finite_dimensional_only=bool(row.get("finite_dimensional_only", False)),
                closure_level=None if row.get("closure_level") is None else str(row.get("closure_level")),
                margin=margin,
                failure_reasons=reasons,
            )
        statuses.append(status)

    missing = [s for s in statuses if not s.present]
    failed = [s for s in statuses if s.present and not s.theorem_ready]
    ready = [s for s in statuses if s.theorem_ready]
    coverage: tuple[float, float] | None = None
    if ready_intervals:
        coverage = (min(a for a, _ in ready_intervals), max(b for _, b in ready_intervals))
    final_lo, final_hi = float(final_anchor[0]), float(final_anchor[1])
    final_reached = bool(coverage and coverage[0] <= final_lo and coverage[1] >= final_hi)

    strict_passed: bool | None = None
    strict_attempted = strict_ingestion_report_path is not None and Path(strict_ingestion_report_path).exists()
    if strict_attempted:
        try:
            strict = load_json(Path(strict_ingestion_report_path))
            strict_passed = bool(strict.get("strict_ingestion_passed", False))
        except Exception:
            strict_passed = False

    failure_fields: list[str] = []
    if missing:
        failure_fields.append("phase2h_missing_required_segments")
    if failed:
        failure_fields.append("phase2h_present_segments_not_theorem_ready")
    if not final_reached:
        failure_fields.append("phase2h_available_segments_do_not_reach_final_anchor")
    if diagnostics:
        failure_fields.append("phase2h_candidate_inventory_diagnostics_present")
    if strict_attempted and not strict_passed:
        failure_fields.append("phase2h_strict_ingestion_failed")
    if not strict_attempted:
        failure_fields.append("phase2h_strict_ingestion_not_attempted")

    promotion_allowed = bool(not failure_fields and strict_passed is True)
    recommendations = [
        "Run all missing segment commands generated by scripts/audit/run_phase2h_missing_segments.sh.",
        "Merge the Phase-2F chunk and all Phase-2G/2H segment candidates before strict ingestion.",
        "Do not promote unless strict Phase-2B ingestion passes and this report has no failure fields.",
    ]
    if failed:
        recommendations.append("For present-but-failing segments, rerun locally with smaller K width and larger N/oversampling; do not weaken margin checks.")
    return Phase2HExecutionStatus(
        schema="phase2h_lower_anchor_execution_status_v1",
        plan_path=plan_p.as_posix(),
        lower_dir=lower_p.as_posix(),
        refinement_dir=refine_p.as_posix(),
        final_anchor=(final_lo, final_hi),
        segment_count=len(statuses),
        ready_segment_count=len(ready),
        missing_segment_count=len(missing),
        failed_segment_count=len(failed),
        coverage_interval=coverage,
        final_anchor_reached_by_available_segments=final_reached,
        merge_attempted=merged_candidate_path is not None and Path(merged_candidate_path).exists(),
        merged_candidate_path=None if merged_candidate_path is None else Path(merged_candidate_path).as_posix(),
        strict_ingestion_attempted=strict_attempted,
        strict_ingestion_passed=strict_passed,
        promotion_allowed=promotion_allowed,
        failure_fields=tuple(failure_fields),
        segments=tuple(statuses),
        recommendations=tuple(recommendations),
    )


def write_phase2h_missing_segment_script(
    *,
    status: Phase2HExecutionStatus,
    out_path: str | Path,
    out_dir: str | Path = DEFAULT_REFINEMENT_DIR,
    table_dir: str | Path = DEFAULT_TABLE_DIR,
    n_values: str = "64,96,128,192,256,384,512",
    oversample_factor: int = 16,
    sigma_cap: float = 0.02,
) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", "", "# AUTO-GENERATED Phase-2H missing-segment execution script."]
    for seg in status.segments:
        if seg.present and seg.theorem_ready:
            continue
        candidate_name = _candidate_name_for_segment(seg.segment_id)
        cmd = [
            "python", "scripts/audit/run_lower_anchor_phase2g_segment.py",
            "--segment-id", seg.segment_id,
            "--K-lo", repr(seg.K_lo),
            "--K-hi", repr(seg.K_hi),
            "--K-mid", repr(seg.K_mid),
            "--N-values", n_values,
            "--oversample-factor", str(int(oversample_factor)),
            "--sigma-cap", repr(float(sigma_cap)),
            "--out-dir", Path(out_dir).as_posix(),
            "--table-dir", Path(table_dir).as_posix(),
            "--candidate-name", candidate_name,
        ]
        lines.append(" ".join(shlex.quote(x) for x in cmd))
    out.write_text("\n".join(lines) + "\n")
    out.chmod(0o755)
    return out


def write_phase2h_status(status: Phase2HExecutionStatus, out_path: str | Path) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(status.to_dict(), indent=2, sort_keys=True) + "\n")
    return out


def candidate_paths_for_merge(
    *,
    status: Phase2HExecutionStatus,
    lower_dir: str | Path = DEFAULT_LOWER_DIR,
    refinement_dir: str | Path = DEFAULT_REFINEMENT_DIR,
) -> list[str]:
    lower_p = Path(lower_dir)
    refine_p = Path(refinement_dir)
    paths: list[Path] = []
    first_chunk = lower_p / "lower_anchor_phase2f_chunk_000_candidate.json"
    if first_chunk.exists():
        paths.append(first_chunk)
    for seg in status.segments:
        if seg.candidate_path:
            p = Path(seg.candidate_path)
            if p.exists() and p not in paths:
                paths.append(p)
        for p in _candidate_paths_for_segment(seg.segment_id, lower_p, refine_p):
            if p.exists() and p not in paths:
                paths.append(p)
    return [p.as_posix() for p in paths]


__all__ = [
    "Phase2HExecutionStatus",
    "Phase2HSegmentStatus",
    "build_phase2h_execution_status",
    "candidate_paths_for_merge",
    "write_phase2h_missing_segment_script",
    "write_phase2h_status",
]
