from __future__ import annotations

"""Phase-2F orchestration for completing the Phase-2E lower-anchor grid.

Phase 2E added a direct analytic Krawczyk/radii-polynomial ledger for individual
lower-anchor segments.  This module is the next-layer orchestration boundary:
it writes the full adaptive grid plan, runs bounded chunks, merges chunk
candidates, and performs an in-process strict Phase-2B ingestion check.

The module deliberately does not weaken the theorem-facing promotion rule.  A
merged candidate is theorem-facing only when every row is certified, every row
has a positive recomputable radii margin, adjacent rows overlap, and the merged
coverage reaches the requested final anchor.  Partial/chunk reports remain
diagnostic.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import math

from .lower_anchor_heavy_certificate import (
    HeavyLowerAnchorConfig,
    build_adaptive_near_anchor_grid,
    run_heavy_lower_anchor_certificate,
    write_heavy_lower_anchor_outputs,
)
from .lower_anchor_closure import (
    build_anchor_closure_audit,
    load_lower_corridor_bundle,
    write_anchor_closure_outputs,
)
from .proof_payload_validator import validate_lower_corridor_payload
from .lower_corridor_chain import DEFAULT_FINAL_ANCHOR


@dataclass(frozen=True)
class Phase2EFullGridPlan:
    schema: str
    start_K: float
    final_anchor: tuple[float, float]
    overlap: float
    segment_count: int
    segments: tuple[dict[str, float | int | str], ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["final_anchor"] = list(self.final_anchor)
        data["segments"] = list(self.segments)
        return data


def build_phase2e_full_grid_plan(config: HeavyLowerAnchorConfig | None = None) -> Phase2EFullGridPlan:
    cfg = config or HeavyLowerAnchorConfig()
    rows = build_adaptive_near_anchor_grid(
        start_K=cfg.start_K,
        final_anchor_hi=cfg.final_anchor_hi,
        overlap=cfg.overlap,
    )
    segments = []
    for idx, (lo, hi, mid) in enumerate(rows):
        segments.append({
            "index": int(idx),
            "segment_id": f"phase2e_heavy_anchor_segment_{idx:03d}",
            "K_lo": float(lo),
            "K_hi": float(hi),
            "K_mid": float(mid),
            "nominal_width": float(hi - lo),
        })
    return Phase2EFullGridPlan(
        schema="phase2f_lower_anchor_phase2e_full_grid_plan_v1",
        start_K=float(cfg.start_K),
        final_anchor=(float(cfg.final_anchor_lo), float(cfg.final_anchor_hi)),
        overlap=float(cfg.overlap),
        segment_count=len(segments),
        segments=tuple(segments),
    )


def write_phase2e_full_grid_plan(path: str | Path, config: HeavyLowerAnchorConfig | None = None) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_phase2e_full_grid_plan(config).to_dict(), indent=2, sort_keys=True) + "\n")
    return out


def _load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"JSON object expected at {path}")
    return data


def _segment_margin(row: Mapping[str, Any]) -> float:
    r = float(row.get("radius_r", row.get("r", 0.0)))
    y = float(row.get("residual_Y", row.get("Y", 0.0)))
    z = float(row.get("linear_defect_Z", row.get("Z", 0.0)))
    t = float(row.get("tail_bound_T", row.get("T", row.get("tail_majorant", 0.0))))
    return float(r - (y + z * r + t))


def _row_theorem_ready(row: Mapping[str, Any]) -> bool:
    if not bool(row.get("certified", False)):
        return False
    if bool(row.get("finite_dimensional_only", False)):
        return False
    if str(row.get("closure_level", "")) != "analytic_theorem_closure":
        return False
    try:
        margin = _segment_margin(row)
    except Exception:
        return False
    if not math.isfinite(margin) or margin <= 0.0:
        return False
    return True


def _candidate_rows(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = candidate.get("anchor_segments", candidate.get("segments", candidate.get("candidate_segments", [])))
    if not isinstance(rows, list):
        raise ValueError("candidate has no anchor segment list")
    return [dict(x) for x in rows]


def merge_phase2e_anchor_candidates(
    candidate_paths: Sequence[str | Path],
    *,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
    source: str = "Phase-2F merged Phase-2E full-grid lower-anchor candidate",
) -> dict[str, Any]:
    """Merge chunk candidate JSON files into one Phase-2B candidate.

    Duplicate segment ids are allowed only when the duplicate rows agree on the
    K-interval; the theorem-ready row with the largest recomputed margin is kept.
    """

    by_id: dict[str, dict[str, Any]] = {}
    raw_sources: list[str] = []
    diagnostics: list[str] = []
    for path in candidate_paths:
        data = _load_json(path)
        raw_sources.append(str(path))
        if bool(data.get("diagnostic_only", False)):
            diagnostics.append(f"{path}:diagnostic_only")
        if not bool(data.get("theorem_facing", False)):
            diagnostics.append(f"{path}:not_theorem_facing")
        for row in _candidate_rows(data):
            sid = str(row.get("segment_id", row.get("id", "")))
            if not sid:
                raise ValueError(f"candidate row without segment_id in {path}")
            row["source_artifact"] = str(path)
            if sid in by_id:
                old = by_id[sid]
                if not (math.isclose(float(old["K_lo"]), float(row["K_lo"]), abs_tol=1e-12) and math.isclose(float(old["K_hi"]), float(row["K_hi"]), abs_tol=1e-12)):
                    raise ValueError(f"duplicate segment id {sid!r} has incompatible K interval")
                old_margin = _segment_margin(old)
                new_margin = _segment_margin(row)
                if new_margin > old_margin:
                    by_id[sid] = row
            else:
                by_id[sid] = row

    rows = sorted(by_id.values(), key=lambda r: (float(r["K_lo"]), float(r["K_hi"]), str(r.get("segment_id", ""))))
    failure_fields: list[str] = []
    failed_segments: list[str] = []
    failed_links: list[str] = []
    if not rows:
        failure_fields.append("merged_anchor_segments_missing")
    margins: list[float] = []
    for row in rows:
        try:
            margin = _segment_margin(row)
            stored = float(row.get("radii_margin", margin))
            # Rewrite the row to the recomputed value so downstream strict
            # Phase-2B ingestion sees an internally consistent merged object.
            row["radii_margin"] = margin
            margins.append(margin)
            if not math.isfinite(margin) or margin <= 0.0:
                failed_segments.append(f"{row.get('segment_id')}:nonpositive_margin")
            if not math.isclose(stored, margin, rel_tol=1e-10, abs_tol=1e-15):
                failed_segments.append(f"{row.get('segment_id')}:stored_margin_mismatch_repaired_in_merge")
        except Exception as exc:
            failed_segments.append(f"{row.get('segment_id')}:margin_exception:{exc!r}")
        if not _row_theorem_ready(row):
            failed_segments.append(f"{row.get('segment_id')}:not_theorem_ready")

    overlaps: list[float] = []
    for a, b in zip(rows, rows[1:]):
        overlap = float(a["K_hi"]) - float(b["K_lo"])
        overlaps.append(overlap)
        if not math.isfinite(overlap) or overlap <= 0.0:
            failed_links.append(f"{a.get('segment_id')}->{b.get('segment_id')}:nonpositive_overlap")

    coverage = None
    if rows:
        coverage = [float(min(r["K_lo"] for r in rows)), float(max(r["K_hi"] for r in rows))]
    final_lo, final_hi = float(final_anchor[0]), float(final_anchor[1])
    final_reached = bool(coverage and coverage[0] <= final_lo and coverage[1] >= final_hi)
    if failed_segments:
        failure_fields.append("merged_anchor_failed_segments")
    if failed_links:
        failure_fields.append("merged_anchor_failed_links")
    if not final_reached:
        failure_fields.append("merged_grid_does_not_reach_final_anchor")
    # Chunk candidates are usually diagnostic because they are partial.  Do not
    # let that poison a valid merge if every row itself is theorem-ready.
    theorem_facing = bool(rows and not failed_segments and not failed_links and final_reached)
    return {
        "schema": "phase2f_merged_phase2e_lower_anchor_candidate_v1",
        "theorem_facing": theorem_facing,
        "diagnostic_only": not theorem_facing,
        "promotion_allowed": theorem_facing,
        "closure_level": "analytic_theorem_closure" if theorem_facing else "merged_phase2e_grid_incomplete_or_diagnostic",
        "source": source,
        "source_candidate_paths": raw_sources,
        "source_candidate_diagnostics": diagnostics,
        "final_anchor": [final_lo, final_hi],
        "coverage_interval": coverage,
        "min_segment_margin": None if not margins else float(min(margins)),
        "min_internal_overlap": None if not overlaps else float(min(overlaps)),
        "failure_fields": failure_fields,
        "failed_segments": failed_segments,
        "failed_links": failed_links,
        "anchor_segments": rows,
    }


def write_merged_phase2e_anchor_candidate(
    candidate_paths: Sequence[str | Path],
    *,
    out_path: str | Path,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
) -> dict[str, Any]:
    merged = merge_phase2e_anchor_candidates(candidate_paths, final_anchor=final_anchor)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n")
    return merged


def check_phase2b_strict_ingestion(
    *,
    lower_bundle_path: str | Path,
    candidate_path: str | Path,
    out_json: str | Path,
    out_bundle: str | Path,
    out_csv: str | Path | None = None,
    out_tex: str | Path | None = None,
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
) -> dict[str, Any]:
    lower = load_lower_corridor_bundle(lower_bundle_path)
    candidate = _load_json(candidate_path)
    segments, candidate_validation, verification, bundle = build_anchor_closure_audit(
        lower,
        anchor_candidate=candidate,
        anchor_candidate_path=candidate_path,
        final_anchor=final_anchor,
    )
    report = write_anchor_closure_outputs(
        segments=segments,
        candidate_validation=candidate_validation,
        verification=verification,
        bundle=bundle,
        out_json=out_json,
        out_bundle=out_bundle,
        out_csv=out_csv,
        out_tex=out_tex,
        fig_dir=None,
    )
    failures = validate_lower_corridor_payload(bundle, require_final_anchor=True, allow_known_lower_gap=False)
    report["validator_failure_count"] = len(failures)
    report["validator_failures"] = [f.to_dict() for f in failures]
    report["strict_ingestion_passed"] = bool(report.get("strict_final_ready_for_theorem_iii") and not failures)
    Path(out_json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def run_phase2e_chunk(
    *,
    config: HeavyLowerAnchorConfig,
    out_dir: str | Path,
    table_dir: str | Path,
    candidate_name: str,
) -> dict[str, Any]:
    report = run_heavy_lower_anchor_certificate(config)
    summary = write_heavy_lower_anchor_outputs(report, out_dir=out_dir, table_dir=table_dir, candidate_name=candidate_name)
    summary.update({
        "status": report.status,
        "theorem_facing": report.theorem_facing,
        "diagnostic_only": report.diagnostic_only,
        "promotion_allowed": report.promotion_allowed,
        "attempted_record_count": report.attempted_record_count,
        "theorem_ready_record_count": report.theorem_ready_record_count,
        "failure_fields": list(report.failure_fields),
    })
    return summary


__all__ = [
    "Phase2EFullGridPlan",
    "build_phase2e_full_grid_plan",
    "write_phase2e_full_grid_plan",
    "merge_phase2e_anchor_candidates",
    "write_merged_phase2e_anchor_candidate",
    "check_phase2b_strict_ingestion",
    "run_phase2e_chunk",
]
