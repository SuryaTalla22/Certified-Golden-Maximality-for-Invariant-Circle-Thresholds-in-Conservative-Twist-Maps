from __future__ import annotations

"""Phase-2K execution, merge, and strict-ingestion controller.

Phase 2J built an old-solver-style adaptive rescue *plan* for the lower-anchor
segments whose Phase-2E analytic radii margins were negative.  This module is
the next fail-closed boundary.  It can

* execute rescue variants with subprocess timeouts and per-variant logs;
* summarize existing rescue candidate files without re-running expensive code;
* select only theorem-ready rescue rows whose raw ``Y,Z,T,r`` fields recompute a
  positive radii margin;
* merge the already theorem-ready lower-prefix rows with successful rescued
  rows;
* report parent-segment coverage and K-gaps; and
* optionally run the strict Phase-2B ingestion gate.

It deliberately does not fabricate successful rows.  If the rescue directory
contains no theorem-ready candidates, the merged object is diagnostic-only and
strict ingestion remains false.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import math
import os
import shlex
import subprocess
import sys
import time

from .lower_anchor_phase2e_full_grid import check_phase2b_strict_ingestion
from .lower_anchor_phase2h_execution import recompute_margin

DEFAULT_LOWER_DIR = Path("artifacts/proof_audit/lower_corridor")
DEFAULT_RESCUE_DIR = DEFAULT_LOWER_DIR / "phase2j_rescue"
DEFAULT_LOG_DIR = DEFAULT_LOWER_DIR / "phase2k_logs"
DEFAULT_FINAL_ANCHOR = (0.971635, 0.971636)


@dataclass(frozen=True)
class Phase2KEnvironmentStatus:
    python_executable: str
    mpmath_available_regular_python: bool
    mpmath_available_no_site_python: bool
    mpmath_regular_path: str | None
    mpmath_no_site_path: str | None
    theorem_grade_dependency_warning: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Phase2KVariantExecution:
    variant_id: str
    parent_segment_id: str
    rescue_segment_id: str
    candidate_path: str
    stdout_path: str | None
    stderr_path: str | None
    command: tuple[str, ...]
    skipped_existing: bool
    dry_run: bool
    attempted: bool
    returncode: int | None
    timed_out: bool
    duration_seconds: float | None
    row_count: int
    theorem_ready_row_count: int
    min_margin: float | None
    max_margin: float | None
    failure_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["command"] = list(self.command)
        data["failure_fields"] = list(self.failure_fields)
        return data


@dataclass(frozen=True)
class Phase2KParentCoverage:
    parent_segment_id: str
    required_K_lo: float
    required_K_hi: float
    successful_interval_count: int
    successful_candidate_paths: tuple[str, ...]
    coverage_interval: tuple[float, float] | None
    gaps: tuple[tuple[float, float], ...]
    min_margin: float | None
    coverage_complete: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_segment_id": self.parent_segment_id,
            "required_K_lo": self.required_K_lo,
            "required_K_hi": self.required_K_hi,
            "successful_interval_count": self.successful_interval_count,
            "successful_candidate_paths": list(self.successful_candidate_paths),
            "coverage_interval": None if self.coverage_interval is None else list(self.coverage_interval),
            "gaps": [list(g) for g in self.gaps],
            "min_margin": self.min_margin,
            "coverage_complete": self.coverage_complete,
        }


@dataclass(frozen=True)
class Phase2KMergedRescueSummary:
    schema: str
    atlas_path: str
    rescue_dir: str
    merged_candidate_path: str
    strict_ingestion_report_path: str | None
    environment: Phase2KEnvironmentStatus
    rescue_variant_count: int
    execution_attempted_count: int
    execution_timeout_count: int
    existing_candidate_count: int
    theorem_ready_rescue_row_count: int
    successful_parent_count: int
    failed_parent_count: int
    coverage_interval: tuple[float, float] | None
    final_anchor_reached: bool
    merged_theorem_facing: bool
    merged_promotion_allowed: bool
    strict_ingestion_attempted: bool
    strict_ingestion_passed: bool | None
    failure_fields: tuple[str, ...]
    parent_coverages: tuple[Phase2KParentCoverage, ...]
    executions: tuple[Phase2KVariantExecution, ...]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "atlas_path": self.atlas_path,
            "rescue_dir": self.rescue_dir,
            "merged_candidate_path": self.merged_candidate_path,
            "strict_ingestion_report_path": self.strict_ingestion_report_path,
            "environment": self.environment.to_dict(),
            "rescue_variant_count": self.rescue_variant_count,
            "execution_attempted_count": self.execution_attempted_count,
            "execution_timeout_count": self.execution_timeout_count,
            "existing_candidate_count": self.existing_candidate_count,
            "theorem_ready_rescue_row_count": self.theorem_ready_rescue_row_count,
            "successful_parent_count": self.successful_parent_count,
            "failed_parent_count": self.failed_parent_count,
            "coverage_interval": None if self.coverage_interval is None else list(self.coverage_interval),
            "final_anchor_reached": self.final_anchor_reached,
            "merged_theorem_facing": self.merged_theorem_facing,
            "merged_promotion_allowed": self.merged_promotion_allowed,
            "strict_ingestion_attempted": self.strict_ingestion_attempted,
            "strict_ingestion_passed": self.strict_ingestion_passed,
            "failure_fields": list(self.failure_fields),
            "parent_coverages": [p.to_dict() for p in self.parent_coverages],
            "executions": [e.to_dict() for e in self.executions],
            "recommendations": list(self.recommendations),
        }


def _load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object at {path}")
    return data


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n")
    return out


def candidate_rows(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = candidate.get("anchor_segments", candidate.get("segments", candidate.get("candidate_segments", [])))
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def row_is_theorem_ready(row: Mapping[str, Any]) -> bool:
    margin = recompute_margin(row)
    return bool(
        bool(row.get("theorem_ready", False))
        and bool(row.get("certified", False))
        and not bool(row.get("finite_dimensional_only", False))
        and str(row.get("closure_level", "")) == "analytic_theorem_closure"
        and margin is not None
        and math.isfinite(float(margin))
        and float(margin) > 0.0
    )


def _row_with_recomputed_margin(row: Mapping[str, Any], *, source_artifact: str) -> dict[str, Any]:
    out = dict(row)
    margin = recompute_margin(out)
    if margin is not None and math.isfinite(float(margin)):
        out["radii_margin"] = float(margin)
        out.setdefault("analytic_theorem_margin", float(margin))
    out.setdefault("source_artifact", source_artifact)
    out.setdefault("source_module", "phase2k_rescue_execution_selected_candidate")
    return out


def _candidate_stats(path: str | Path) -> tuple[int, int, float | None, float | None, list[dict[str, Any]], list[str]]:
    p = Path(path)
    failures: list[str] = []
    if not p.exists():
        return 0, 0, None, None, [], ["candidate_missing"]
    try:
        data = _load_json(p)
    except Exception as exc:
        return 0, 0, None, None, [], [f"candidate_unreadable:{exc!r}"]
    rows = candidate_rows(data)
    margins: list[float] = []
    ready: list[dict[str, Any]] = []
    for row in rows:
        m = recompute_margin(row)
        if m is not None and math.isfinite(float(m)):
            margins.append(float(m))
        if row_is_theorem_ready(row):
            ready.append(_row_with_recomputed_margin(row, source_artifact=p.as_posix()))
    if not rows:
        failures.append("candidate_has_no_rows")
    if ready and len(ready) != len(rows):
        failures.append("candidate_has_mixed_ready_and_nonready_rows")
    if rows and not ready:
        failures.append("candidate_has_no_theorem_ready_rows")
    return len(rows), len(ready), (None if not margins else min(margins)), (None if not margins else max(margins)), ready, failures


def _probe_mpmath(*, no_site: bool) -> tuple[bool, str | None]:
    """Lightweight mpmath availability probe.

    Earlier phases sometimes run under ``python -S`` to avoid slow site startup
    in constrained environments.  Spawning a regular Python process just to test
    site-packages can hang on such systems, so Phase 2K probes only the current
    interpreter.  A full theorem run should execute the controller under the
    same interpreter/environment intended for proof generation.
    """

    if bool(no_site) != bool(sys.flags.no_site):
        return False, None
    try:
        import mpmath  # type: ignore
        return True, getattr(mpmath, "__file__", None)
    except Exception:
        return False, None


def build_environment_status() -> Phase2KEnvironmentStatus:
    regular_ok, regular_path = _probe_mpmath(no_site=False)
    nosite_ok, nosite_path = _probe_mpmath(no_site=True)
    warning = None
    if not regular_ok:
        warning = "mpmath is not importable under regular Python; theorem-grade Phase-2K execution must be rerun in a full numerical environment."
    elif not nosite_ok:
        warning = "mpmath is importable under regular Python but not with -S; generated rescue scripts that use -S may run fallback/diagnostic paths unless edited."
    return Phase2KEnvironmentStatus(
        python_executable=sys.executable,
        mpmath_available_regular_python=regular_ok,
        mpmath_available_no_site_python=nosite_ok,
        mpmath_regular_path=regular_path,
        mpmath_no_site_path=nosite_path,
        theorem_grade_dependency_warning=warning,
    )


def _variant_candidate_path(variant: Mapping[str, Any], rescue_dir: str | Path) -> Path:
    candidate_name = str(variant.get("candidate_name", f"{variant.get('variant_id', 'variant')}_candidate.json"))
    return Path(rescue_dir) / candidate_name


def _variant_command(variant: Mapping[str, Any], *, python_executable: str | None = None, no_site: bool | None = None) -> list[str]:
    raw = variant.get("command", [])
    if not isinstance(raw, list):
        raw = []
    cmd = [str(x) for x in raw]
    if python_executable and cmd:
        cmd[0] = python_executable
    if no_site is not None and cmd:
        has_no_site = "-S" in cmd[:3]
        if no_site and not has_no_site:
            cmd.insert(1, "-S")
        if not no_site and has_no_site:
            cmd = [x for idx, x in enumerate(cmd) if not (idx <= 2 and x == "-S")]
    return cmd


def execute_rescue_variants(
    *,
    atlas_path: str | Path,
    repo_root: str | Path = ".",
    rescue_dir: str | Path = DEFAULT_RESCUE_DIR,
    log_dir: str | Path = DEFAULT_LOG_DIR,
    max_variants: int | None = None,
    timeout_seconds: float | None = None,
    dry_run: bool = False,
    force: bool = False,
    python_executable: str | None = None,
    no_site: bool | None = None,
) -> list[Phase2KVariantExecution]:
    """Execute or summarize Phase-2J rescue variants.

    Existing candidate files are summarized and skipped unless ``force=True``.
    This makes the command safe to rerun after interrupted long jobs.
    """

    root = Path(repo_root)
    rescue_p = root / rescue_dir if not Path(rescue_dir).is_absolute() else Path(rescue_dir)
    log_p = root / log_dir if not Path(log_dir).is_absolute() else Path(log_dir)
    rescue_p.mkdir(parents=True, exist_ok=True)
    log_p.mkdir(parents=True, exist_ok=True)
    atlas = _load_json(root / atlas_path if not Path(atlas_path).is_absolute() else atlas_path)
    variants_raw = atlas.get("rescue_variants", [])
    if not isinstance(variants_raw, list):
        variants_raw = []
    if max_variants is not None:
        variants_raw = variants_raw[: max(0, int(max_variants))]

    executions: list[Phase2KVariantExecution] = []
    env = os.environ.copy()
    old_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(root.resolve()) + ((os.pathsep + old_pp) if old_pp else "")
    for variant in variants_raw:
        if not isinstance(variant, Mapping):
            continue
        variant_id = str(variant.get("variant_id", "unknown_variant"))
        parent_id = str(variant.get("parent_segment_id", ""))
        rescue_id = str(variant.get("rescue_segment_id", ""))
        candidate_path = root / _variant_candidate_path(variant, rescue_dir) if not _variant_candidate_path(variant, rescue_dir).is_absolute() else _variant_candidate_path(variant, rescue_dir)
        stdout_path = log_p / f"{variant_id}.stdout.log"
        stderr_path = log_p / f"{variant_id}.stderr.log"
        cmd = _variant_command(variant, python_executable=python_executable, no_site=no_site)
        skipped = candidate_path.exists() and not force
        attempted = False
        rc: int | None = None
        timed_out = False
        duration: float | None = None
        if dry_run:
            stdout_path.write_text("DRY RUN: " + " ".join(shlex.quote(x) for x in cmd) + "\n")
            stderr_path.write_text("")
        elif not skipped:
            attempted = True
            start = time.monotonic()
            try:
                proc = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, timeout=timeout_seconds)
                rc = int(proc.returncode)
                stdout_path.write_text(proc.stdout or "")
                stderr_path.write_text(proc.stderr or "")
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                rc = None
                stdout_path.write_text(exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""))
                stderr_path.write_text((exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")) + "\nPHASE2K_TIMEOUT\n")
            duration = time.monotonic() - start
        row_count, ready_count, min_margin, max_margin, _ready_rows, failures = _candidate_stats(candidate_path)
        if attempted and rc not in (0, None):
            failures.append(f"execution_returncode_{rc}")
        if timed_out:
            failures.append("execution_timed_out")
        if dry_run:
            failures.append("dry_run_no_execution")
        executions.append(Phase2KVariantExecution(
            variant_id=variant_id,
            parent_segment_id=parent_id,
            rescue_segment_id=rescue_id,
            candidate_path=candidate_path.as_posix(),
            stdout_path=stdout_path.as_posix() if (dry_run or attempted) else None,
            stderr_path=stderr_path.as_posix() if (dry_run or attempted) else None,
            command=tuple(cmd),
            skipped_existing=skipped,
            dry_run=bool(dry_run),
            attempted=attempted,
            returncode=rc,
            timed_out=timed_out,
            duration_seconds=duration,
            row_count=row_count,
            theorem_ready_row_count=ready_count,
            min_margin=min_margin,
            max_margin=max_margin,
            failure_fields=tuple(failures),
        ))
    return executions


def _parent_required_intervals(atlas: Mapping[str, Any]) -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    for row in atlas.get("failed_rows", []) or []:
        if isinstance(row, Mapping):
            sid = str(row.get("segment_id", ""))
            if sid:
                out[sid] = (float(row.get("K_lo")), float(row.get("K_hi")))
    return out


def _variant_parent_map(atlas: Mapping[str, Any], rescue_dir: str | Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for variant in atlas.get("rescue_variants", []) or []:
        if isinstance(variant, Mapping):
            p = _variant_candidate_path(variant, rescue_dir).as_posix()
            out[p] = str(variant.get("parent_segment_id", ""))
    return out


def _infer_parent_from_segment_id(segment_id: str) -> str:
    marker = "_phase2j_sub"
    if marker in segment_id:
        return segment_id.split(marker, 1)[0]
    return segment_id


def _merge_intervals(intervals: Sequence[tuple[float, float, dict[str, Any], str]], *, tol: float = 0.0) -> tuple[list[tuple[float, float]], list[tuple[float, float, dict[str, Any], str]]]:
    if not intervals:
        return [], []
    ordered = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged: list[tuple[float, float]] = []
    cur_lo, cur_hi = ordered[0][0], ordered[0][1]
    for lo, hi, _row, _path in ordered[1:]:
        if lo <= cur_hi + tol:
            cur_hi = max(cur_hi, hi)
        else:
            merged.append((cur_lo, cur_hi))
            cur_lo, cur_hi = lo, hi
    merged.append((cur_lo, cur_hi))
    return merged, ordered


def _gaps_against_required(required: tuple[float, float], intervals: Sequence[tuple[float, float]], *, tol: float = 0.0) -> list[tuple[float, float]]:
    req_lo, req_hi = required
    gaps: list[tuple[float, float]] = []
    cursor = req_lo
    for lo, hi in intervals:
        if hi < req_lo or lo > req_hi:
            continue
        lo_c = max(lo, req_lo)
        hi_c = min(hi, req_hi)
        if lo_c > cursor + tol:
            gaps.append((cursor, lo_c))
        cursor = max(cursor, hi_c)
    if cursor < req_hi - tol:
        gaps.append((cursor, req_hi))
    return gaps


def collect_successful_rescue_rows(*, atlas_path: str | Path, rescue_dir: str | Path = DEFAULT_RESCUE_DIR) -> tuple[list[dict[str, Any]], list[Phase2KParentCoverage]]:
    atlas_p = Path(atlas_path)
    atlas = _load_json(atlas_p)
    rescue_p = Path(rescue_dir)
    required = _parent_required_intervals(atlas)
    parent_by_path = _variant_parent_map(atlas, rescue_p)
    by_parent: dict[str, list[tuple[float, float, dict[str, Any], str]]] = {k: [] for k in required}
    ready_rows: list[dict[str, Any]] = []
    for path in sorted(rescue_p.glob("*_candidate.json")) if rescue_p.exists() else []:
        try:
            data = _load_json(path)
        except Exception:
            continue
        for row in candidate_rows(data):
            if not row_is_theorem_ready(row):
                continue
            row2 = _row_with_recomputed_margin(row, source_artifact=path.as_posix())
            sid = str(row2.get("segment_id", ""))
            parent = parent_by_path.get(path.as_posix()) or parent_by_path.get((rescue_p / path.name).as_posix()) or _infer_parent_from_segment_id(sid)
            lo = float(row2.get("K_lo")); hi = float(row2.get("K_hi"))
            by_parent.setdefault(parent, []).append((lo, hi, row2, path.as_posix()))
            ready_rows.append(row2)
    coverages: list[Phase2KParentCoverage] = []
    for parent, req in required.items():
        merged, ordered = _merge_intervals(by_parent.get(parent, []), tol=0.0)
        gaps = _gaps_against_required(req, merged, tol=0.0)
        margins = [float(recompute_margin(row) or 0.0) for _lo, _hi, row, _path in by_parent.get(parent, [])]
        paths = tuple(sorted({path for _lo, _hi, _row, path in by_parent.get(parent, [])}))
        coverage = None if not merged else (min(lo for lo, _hi in merged), max(hi for _lo, hi in merged))
        coverages.append(Phase2KParentCoverage(
            parent_segment_id=parent,
            required_K_lo=float(req[0]),
            required_K_hi=float(req[1]),
            successful_interval_count=len(by_parent.get(parent, [])),
            successful_candidate_paths=paths,
            coverage_interval=coverage,
            gaps=tuple(gaps),
            min_margin=None if not margins else min(margins),
            coverage_complete=(len(gaps) == 0 and bool(merged)),
        ))
    return ready_rows, coverages


def _load_theorem_ready_prefix(prefix_candidate_paths: Sequence[str | Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in prefix_candidate_paths:
        p = Path(path)
        if not p.exists():
            continue
        try:
            data = _load_json(p)
        except Exception:
            continue
        for row in candidate_rows(data):
            if row_is_theorem_ready(row):
                rows.append(_row_with_recomputed_margin(row, source_artifact=p.as_posix()))
    return rows


def build_merged_rescued_candidate(
    *,
    atlas_path: str | Path,
    rescue_dir: str | Path = DEFAULT_RESCUE_DIR,
    prefix_candidate_paths: Sequence[str | Path] = (DEFAULT_LOWER_DIR / "lower_anchor_phase2f_chunk_000_candidate.json",),
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
) -> tuple[dict[str, Any], tuple[Phase2KParentCoverage, ...]]:
    prefix_rows = _load_theorem_ready_prefix(prefix_candidate_paths)
    rescue_rows, coverages = collect_successful_rescue_rows(atlas_path=atlas_path, rescue_dir=rescue_dir)
    rows_by_id: dict[str, dict[str, Any]] = {}
    for row in prefix_rows + rescue_rows:
        sid = str(row.get("segment_id", ""))
        if not sid:
            continue
        old = rows_by_id.get(sid)
        if old is None or ((recompute_margin(row) or -math.inf) > (recompute_margin(old) or -math.inf)):
            rows_by_id[sid] = row
    rows = sorted(rows_by_id.values(), key=lambda r: (float(r.get("K_lo")), float(r.get("K_hi")), str(r.get("segment_id", ""))))
    failure_fields: list[str] = []
    failed_segments: list[str] = []
    failed_links: list[str] = []
    margins: list[float] = []
    for row in rows:
        m = recompute_margin(row)
        if m is not None and math.isfinite(float(m)):
            margins.append(float(m))
        if not row_is_theorem_ready(row):
            failed_segments.append(f"{row.get('segment_id')}:not_theorem_ready")
    overlaps: list[float] = []
    for a, b in zip(rows, rows[1:]):
        overlap = float(a.get("K_hi")) - float(b.get("K_lo"))
        overlaps.append(overlap)
        if not math.isfinite(overlap) or overlap <= 0.0:
            failed_links.append(f"{a.get('segment_id')}->{b.get('segment_id')}:nonpositive_overlap_or_gap")
    coverage = None if not rows else [float(min(r["K_lo"] for r in rows)), float(max(r["K_hi"] for r in rows))]
    final_lo, final_hi = float(final_anchor[0]), float(final_anchor[1])
    final_reached = bool(coverage and coverage[0] <= final_lo and coverage[1] >= final_hi)
    incomplete = [c.parent_segment_id for c in coverages if not c.coverage_complete]
    if failed_segments:
        failure_fields.append("phase2k_merged_failed_segments")
    if failed_links:
        failure_fields.append("phase2k_merged_failed_links")
    if incomplete:
        failure_fields.append("phase2k_unrescued_parent_segments")
    if not final_reached:
        failure_fields.append("phase2k_merged_grid_does_not_reach_final_anchor")
    theorem_facing = bool(rows and not failure_fields and final_reached)
    candidate = {
        "schema": "phase2k_merged_rescued_lower_anchor_candidate_v1",
        "theorem_facing": theorem_facing,
        "diagnostic_only": not theorem_facing,
        "promotion_allowed": theorem_facing,
        "closure_level": "analytic_theorem_closure" if theorem_facing else "phase2k_rescue_incomplete_or_diagnostic",
        "source": "Phase-2K merged lower-anchor candidate from theorem-ready prefix and successful Phase-2J rescue rows",
        "final_anchor": [final_lo, final_hi],
        "coverage_interval": coverage,
        "min_segment_margin": None if not margins else min(margins),
        "min_internal_overlap": None if not overlaps else min(overlaps),
        "failure_fields": failure_fields,
        "failed_segments": failed_segments,
        "failed_links": failed_links,
        "unrescued_parent_segments": incomplete,
        "parent_coverages": [c.to_dict() for c in coverages],
        "anchor_segments": rows,
    }
    return candidate, tuple(coverages)


def run_phase2k_controller(
    *,
    atlas_path: str | Path,
    repo_root: str | Path = ".",
    rescue_dir: str | Path = DEFAULT_RESCUE_DIR,
    log_dir: str | Path = DEFAULT_LOG_DIR,
    merged_candidate_path: str | Path = DEFAULT_LOWER_DIR / "lower_anchor_phase2k_merged_rescued_candidate.json",
    summary_out: str | Path = DEFAULT_LOWER_DIR / "lower_anchor_phase2k_execution_summary.json",
    lower_bundle_path: str | Path = DEFAULT_LOWER_DIR / "lower_corridor_audit.bundle.json",
    strict_ingestion_report_path: str | Path = DEFAULT_LOWER_DIR / "lower_anchor_phase2k_strict_ingestion_check.json",
    strict_ingestion_bundle_path: str | Path = DEFAULT_LOWER_DIR / "lower_anchor_phase2k_strict_ingestion_check.bundle.json",
    strict_ingestion_csv_path: str | Path | None = Path("tables/proof_audit/lower_corridor/lower_anchor_phase2k_strict_ingestion_segments.csv"),
    strict_ingestion_tex_path: str | Path | None = Path("tables/proof_audit/lower_corridor/lower_anchor_phase2k_strict_ingestion_segments.tex"),
    prefix_candidate_paths: Sequence[str | Path] = (DEFAULT_LOWER_DIR / "lower_anchor_phase2f_chunk_000_candidate.json",),
    final_anchor: Sequence[float] = DEFAULT_FINAL_ANCHOR,
    execute: bool = False,
    dry_run: bool = False,
    force: bool = False,
    max_variants: int | None = None,
    timeout_seconds: float | None = None,
    python_executable: str | None = None,
    no_site: bool | None = None,
    strict_ingestion_check: bool = True,
) -> Phase2KMergedRescueSummary:
    root = Path(repo_root)
    atlas_p = root / atlas_path if not Path(atlas_path).is_absolute() else Path(atlas_path)
    rescue_p = root / rescue_dir if not Path(rescue_dir).is_absolute() else Path(rescue_dir)
    merged_p = root / merged_candidate_path if not Path(merged_candidate_path).is_absolute() else Path(merged_candidate_path)
    summary_p = root / summary_out if not Path(summary_out).is_absolute() else Path(summary_out)
    strict_report_p = root / strict_ingestion_report_path if not Path(strict_ingestion_report_path).is_absolute() else Path(strict_ingestion_report_path)
    strict_bundle_p = root / strict_ingestion_bundle_path if not Path(strict_ingestion_bundle_path).is_absolute() else Path(strict_ingestion_bundle_path)
    env_status = build_environment_status()
    atlas = _load_json(atlas_p)
    executions: list[Phase2KVariantExecution] = []
    if execute or dry_run:
        executions = execute_rescue_variants(
            atlas_path=atlas_p,
            repo_root=root,
            rescue_dir=rescue_p,
            log_dir=root / log_dir if not Path(log_dir).is_absolute() else Path(log_dir),
            max_variants=max_variants,
            timeout_seconds=timeout_seconds,
            dry_run=dry_run,
            force=force,
            python_executable=python_executable,
            no_site=no_site,
        )
    else:
        # Summarize all variants against existing candidate files without spawning heavy subprocesses.
        executions = execute_rescue_variants(
            atlas_path=atlas_p,
            repo_root=root,
            rescue_dir=rescue_p,
            log_dir=root / log_dir if not Path(log_dir).is_absolute() else Path(log_dir),
            max_variants=max_variants,
            dry_run=True,
            force=False,
        )
        # Mark these as summaries, not actual dry-run executions, by clearing log-only failure inflation where candidate already exists.
        cleaned: list[Phase2KVariantExecution] = []
        for e in executions:
            failures = tuple(f for f in e.failure_fields if f != "dry_run_no_execution") if e.skipped_existing else e.failure_fields
            cleaned.append(Phase2KVariantExecution(**{**e.to_dict(), "command": tuple(e.command), "failure_fields": failures}))
        executions = cleaned

    prefix_abs = [root / p if not Path(p).is_absolute() else Path(p) for p in prefix_candidate_paths]
    candidate, coverages = build_merged_rescued_candidate(
        atlas_path=atlas_p,
        rescue_dir=rescue_p,
        prefix_candidate_paths=prefix_abs,
        final_anchor=final_anchor,
    )
    _write_json(merged_p, candidate)

    strict_passed: bool | None = None
    strict_attempted = False
    if strict_ingestion_check:
        strict_attempted = True
        try:
            report = check_phase2b_strict_ingestion(
                lower_bundle_path=root / lower_bundle_path if not Path(lower_bundle_path).is_absolute() else Path(lower_bundle_path),
                candidate_path=merged_p,
                out_json=strict_report_p,
                out_bundle=strict_bundle_p,
                out_csv=(None if strict_ingestion_csv_path is None else (root / strict_ingestion_csv_path if not Path(strict_ingestion_csv_path).is_absolute() else strict_ingestion_csv_path)),
                out_tex=(None if strict_ingestion_tex_path is None else (root / strict_ingestion_tex_path if not Path(strict_ingestion_tex_path).is_absolute() else strict_ingestion_tex_path)),
                final_anchor=final_anchor,
            )
            strict_passed = bool(report.get("strict_ingestion_passed", False))
        except Exception as exc:
            strict_passed = False
            _write_json(strict_report_p, {"schema": "phase2k_strict_ingestion_exception_v1", "strict_ingestion_passed": False, "exception": repr(exc)})

    final_lo, final_hi = float(final_anchor[0]), float(final_anchor[1])
    coverage = None if candidate.get("coverage_interval") is None else tuple(float(x) for x in candidate["coverage_interval"])
    final_reached = bool(coverage and coverage[0] <= final_lo and coverage[1] >= final_hi)
    successful_parents = [c for c in coverages if c.coverage_complete]
    failed_parents = [c for c in coverages if not c.coverage_complete]
    failure_fields = list(candidate.get("failure_fields", []))
    if env_status.theorem_grade_dependency_warning:
        failure_fields.append("phase2k_theorem_grade_dependency_warning")
    if strict_attempted and not strict_passed:
        failure_fields.append("phase2k_strict_ingestion_failed")
    if not strict_attempted:
        failure_fields.append("phase2k_strict_ingestion_not_attempted")
    theorem_ready_rows = sum(1 for e in executions if e.theorem_ready_row_count > 0)
    existing_count = sum(1 for e in executions if e.skipped_existing)
    recommendations = [
        "Run this controller with --execute in an environment where real mpmath is available before treating Phase-2K outputs as theorem-grade.",
        "Merge and promote only after every failed parent segment has complete successful rescue coverage and strict Phase-2B ingestion passes.",
        "If parent coverage remains incomplete, regenerate the Phase-2J atlas without max-variants-per-parent and run all subsegments for the affected parents.",
        "Do not edit candidate status flags by hand; strict ingestion must recompute all Y+Zr+T<r margins.",
    ]
    summary = Phase2KMergedRescueSummary(
        schema="phase2k_rescue_execution_merge_summary_v1",
        atlas_path=atlas_p.as_posix(),
        rescue_dir=rescue_p.as_posix(),
        merged_candidate_path=merged_p.as_posix(),
        strict_ingestion_report_path=strict_report_p.as_posix() if strict_attempted else None,
        environment=env_status,
        rescue_variant_count=len(atlas.get("rescue_variants", []) or []),
        execution_attempted_count=sum(1 for e in executions if e.attempted),
        execution_timeout_count=sum(1 for e in executions if e.timed_out),
        existing_candidate_count=existing_count,
        theorem_ready_rescue_row_count=sum(e.theorem_ready_row_count for e in executions),
        successful_parent_count=len(successful_parents),
        failed_parent_count=len(failed_parents),
        coverage_interval=coverage,
        final_anchor_reached=final_reached,
        merged_theorem_facing=bool(candidate.get("theorem_facing")),
        merged_promotion_allowed=bool(candidate.get("promotion_allowed")),
        strict_ingestion_attempted=strict_attempted,
        strict_ingestion_passed=strict_passed,
        failure_fields=tuple(dict.fromkeys(failure_fields)),
        parent_coverages=tuple(coverages),
        executions=tuple(executions),
        recommendations=tuple(recommendations),
    )
    _write_json(summary_p, summary.to_dict())
    return summary


__all__ = [
    "Phase2KEnvironmentStatus",
    "Phase2KVariantExecution",
    "Phase2KParentCoverage",
    "Phase2KMergedRescueSummary",
    "build_environment_status",
    "execute_rescue_variants",
    "collect_successful_rescue_rows",
    "build_merged_rescued_candidate",
    "run_phase2k_controller",
]
