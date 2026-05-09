from __future__ import annotations

"""Phase-2J adaptive rescue orchestration helpers.

This layer is intentionally light: it does not certify any row.  It builds the
failure atlas, writes commands for the old-solver-style rescue variants, and can
summarize rescue candidates generated later.  The final theorem decision remains
with strict Phase-2B ingestion.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import math

from .lower_anchor_phase2h_execution import candidate_rows, recompute_margin
from .lower_anchor_phase2j_failure_atlas import build_failure_atlas, write_failure_atlas_outputs


@dataclass(frozen=True)
class Phase2JRescueCandidateSummary:
    path: str
    segment_ids: tuple[str, ...]
    theorem_ready_count: int
    row_count: int
    min_margin: float | None
    max_margin: float | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["segment_ids"] = list(self.segment_ids)
        return data


@dataclass(frozen=True)
class Phase2JAdaptiveRescueSummary:
    schema: str
    atlas_path: str
    failed_segment_count: int
    rescue_variant_count: int
    rescue_candidate_count: int
    theorem_ready_rescue_candidate_count: int
    best_candidate_paths: tuple[str, ...]
    recommendations: tuple[str, ...]
    candidates: tuple[Phase2JRescueCandidateSummary, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "atlas_path": self.atlas_path,
            "failed_segment_count": self.failed_segment_count,
            "rescue_variant_count": self.rescue_variant_count,
            "rescue_candidate_count": self.rescue_candidate_count,
            "theorem_ready_rescue_candidate_count": self.theorem_ready_rescue_candidate_count,
            "best_candidate_paths": list(self.best_candidate_paths),
            "recommendations": list(self.recommendations),
            "candidates": [c.to_dict() for c in self.candidates],
        }


def _load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    return data if isinstance(data, dict) else {}


def summarize_candidate(path: str | Path) -> Phase2JRescueCandidateSummary:
    p = Path(path)
    data = _load_json(p)
    rows = candidate_rows(data)
    margins = [recompute_margin(row) for row in rows]
    margins = [float(x) for x in margins if x is not None and math.isfinite(float(x))]
    ready = [row for row in rows if bool(row.get("theorem_ready", False)) and bool(row.get("certified", False)) and not bool(row.get("finite_dimensional_only", False)) and (recompute_margin(row) or -1.0) > 0.0]
    return Phase2JRescueCandidateSummary(
        path=p.as_posix(),
        segment_ids=tuple(str(row.get("segment_id", "")) for row in rows),
        theorem_ready_count=len(ready),
        row_count=len(rows),
        min_margin=None if not margins else min(margins),
        max_margin=None if not margins else max(margins),
    )


def summarize_rescue_directory(*, atlas_path: str | Path, rescue_dir: str | Path) -> Phase2JAdaptiveRescueSummary:
    atlas = _load_json(atlas_path)
    candidates = [summarize_candidate(p) for p in sorted(Path(rescue_dir).glob("*_candidate.json"))]
    ready_candidates = [c for c in candidates if c.row_count > 0 and c.theorem_ready_count == c.row_count]
    # For each rescue segment id, keep the ready candidate with the largest margin.
    best_by_segment: dict[str, Phase2JRescueCandidateSummary] = {}
    for cand in ready_candidates:
        for sid in cand.segment_ids:
            if not sid:
                continue
            old = best_by_segment.get(sid)
            if old is None or ((cand.min_margin or -math.inf) > (old.min_margin or -math.inf)):
                best_by_segment[sid] = cand
    recs = [
        "If no theorem-ready rescue candidates are present, execute scripts/audit/run_phase2j_rescue_segments.sh in a full numerical environment.",
        "If some rescue candidates are theorem-ready, merge only those with the original ready prefix and rerun strict Phase-2B ingestion.",
        "A rescue directory summary is not a theorem certificate; it is only a selection aid before strict ingestion.",
    ]
    return Phase2JAdaptiveRescueSummary(
        schema="phase2j_adaptive_rescue_directory_summary_v1",
        atlas_path=Path(atlas_path).as_posix(),
        failed_segment_count=int(atlas.get("failed_segment_count", 0)),
        rescue_variant_count=len(atlas.get("rescue_variants", []) or []),
        rescue_candidate_count=len(candidates),
        theorem_ready_rescue_candidate_count=len(ready_candidates),
        best_candidate_paths=tuple(sorted({c.path for c in best_by_segment.values()})),
        recommendations=tuple(recs),
        candidates=tuple(candidates),
    )


def build_and_write_phase2j_plan(*, candidate_path: str | Path, strict_report_path: str | Path | None, atlas_out: str | Path, csv_out: str | Path, script_out: str | Path, dry_run_script_out: str | Path | None = None, max_variants_per_parent: int | None = None, python_executable: str = "python", no_site: bool = False) -> dict[str, Any]:
    atlas = build_failure_atlas(candidate_path, strict_report_path=strict_report_path, max_variants_per_parent=max_variants_per_parent, python_executable=python_executable, no_site=no_site)
    return write_failure_atlas_outputs(atlas, out_json=atlas_out, out_csv=csv_out, script_out=script_out, dry_run_script_out=dry_run_script_out)


__all__ = [
    "Phase2JAdaptiveRescueSummary",
    "Phase2JRescueCandidateSummary",
    "build_and_write_phase2j_plan",
    "summarize_candidate",
    "summarize_rescue_directory",
]
