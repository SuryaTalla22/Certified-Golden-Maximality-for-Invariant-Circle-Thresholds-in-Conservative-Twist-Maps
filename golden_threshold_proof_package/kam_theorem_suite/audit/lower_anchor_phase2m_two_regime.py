from __future__ import annotations

"""Phase 2M: two-regime lower-anchor theorem scaffolding.

This module implements the next proof-engineering layer after the Phase 2K/2L
experiments.  The goal is to stop treating the near-critical lower-anchor proof
as one homogeneous rescue sweep.  Instead we split it into

  Regime I:  a segmentwise analytic chain that is already closing through about
             K = 0.9600001;
  Regime II: a near-critical collar starting at the Regime-I endpoint and ending
             at the final lower anchor K = 0.971636.

The code is intentionally fail-closed.  It never fabricates a theorem-facing
certificate.  It can

  * collect theorem-ready rows from existing Phase 2F/2J/2L candidate files;
  * freeze the best contiguous Regime-I chain;
  * diagnose why the collar starts failing, including requested-vs-actual sigma;
  * generate a targeted collar microsegment execution plan; and
  * verify/assemble a two-regime certificate if collar rows later become ready.

The mathematical collar proof is still carried by the raw candidate rows emitted
by the existing lower-anchor segment validator.  This module supplies the new
bookkeeping and gate structure required to make a two-regime theorem object
visible to downstream strict ingestion.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import csv
import json
import math
import os
import re
import shlex
import subprocess
import sys
import time

DEFAULT_LOWER_DIR = Path("artifacts/proof_audit/lower_corridor")
DEFAULT_RESCUE_DIR = DEFAULT_LOWER_DIR / "phase2j_rescue"
DEFAULT_COLLAR_DIR = DEFAULT_LOWER_DIR / "phase2m_collar"
DEFAULT_COLLAR_TABLE_DIR = Path("tables/proof_audit/lower_corridor/phase2m_collar")
DEFAULT_COLLAR_LOG_DIR = DEFAULT_LOWER_DIR / "phase2m_collar_logs"
DEFAULT_REGIME_I_OUT = DEFAULT_LOWER_DIR / "lower_regime_I_chain.json"
DEFAULT_COLLAR_THEOREM_OUT = DEFAULT_LOWER_DIR / "lower_nearcritical_collar_theorem.json"
DEFAULT_TWO_REGIME_OUT = DEFAULT_LOWER_DIR / "lower_two_regime_certificate.json"
DEFAULT_DIAGNOSTICS_OUT = DEFAULT_LOWER_DIR / "phase2m_collar_diagnostics.json"
DEFAULT_DIAGNOSTICS_CSV = Path("tables/proof_audit/lower_corridor/phase2m_segment005_terms.csv")
DEFAULT_PLAN_OUT = DEFAULT_LOWER_DIR / "phase2m_collar_plan.json"
DEFAULT_RUN_SCRIPT = Path("scripts/audit/run_phase2m_collar_jobs.sh")

DEFAULT_REGIME_I_START = 0.265
DEFAULT_REGIME_I_TARGET_HI = 0.9600001
DEFAULT_COLLAR_START = 0.9600001
DEFAULT_FINAL_ANCHOR = (0.971635, 0.971636)
DEFAULT_OVERLAP_TOL = 5.0e-7


@dataclass(frozen=True)
class ReadyRow:
    segment_id: str
    K_lo: float
    K_hi: float
    margin: float
    source_path: str
    row: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "K_lo": self.K_lo,
            "K_hi": self.K_hi,
            "margin": self.margin,
            "source_path": self.source_path,
            "row": self.row,
        }


@dataclass(frozen=True)
class CoverageResult:
    requested_interval: tuple[float, float]
    covered_interval: tuple[float, float] | None
    selected_rows: tuple[ReadyRow, ...]
    gaps: tuple[tuple[float, float], ...]
    min_margin: float | None
    min_overlap: float | None
    coverage_complete: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_interval": list(self.requested_interval),
            "covered_interval": None if self.covered_interval is None else list(self.covered_interval),
            "selected_rows": [r.to_dict() for r in self.selected_rows],
            "gaps": [list(g) for g in self.gaps],
            "min_margin": self.min_margin,
            "min_overlap": self.min_overlap,
            "coverage_complete": self.coverage_complete,
        }


@dataclass(frozen=True)
class CollarJob:
    job_id: str
    K_lo: float
    K_hi: float
    K_mid: float
    regime: str
    n_values: tuple[int, ...]
    oversample_factor: int
    sigma_cap: float
    max_wall_seconds: float
    candidate_name: str
    command: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["n_values"] = list(self.n_values)
        d["command"] = list(self.command)
        return d


@dataclass(frozen=True)
class CollarJobExecution:
    job_id: str
    candidate_name: str
    attempted: bool
    skipped_ready: bool
    returncode: int | None
    timed_out: bool
    duration_seconds: float | None
    theorem_ready_rows: int
    min_margin: float | None
    max_margin: float | None
    stdout_path: str | None
    stderr_path: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object at {p}")
    return data


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n")
    return p


def candidate_rows(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = data.get("anchor_segments", data.get("segments", data.get("candidate_segments", [])))
    if not isinstance(rows, list):
        return []
    return [dict(r) for r in rows if isinstance(r, Mapping)]


def recompute_margin(row: Mapping[str, Any]) -> float | None:
    """Return the best explicit margin field available for an anchor row.

    Existing Phase 2 rows sometimes store the final recomputed value under
    ``radii_margin`` and sometimes inside ``phase2e_ledger``.  Prefer fields
    that are already recomputed by the validator, but allow older candidates to
    be diagnosed rather than crashing.
    """

    ledger = row.get("phase2e_ledger") if isinstance(row.get("phase2e_ledger"), Mapping) else {}
    vals = [
        row.get("radii_margin"),
        row.get("recomputed_margin"),
        row.get("analytic_theorem_margin"),
        row.get("stored_margin"),
        ledger.get("radii_margin") if isinstance(ledger, Mapping) else None,
    ]
    numeric = []
    for v in vals:
        if isinstance(v, (int, float)) and math.isfinite(float(v)):
            numeric.append(float(v))
    if numeric:
        return max(numeric)

    # Fall back to the raw inequality if all fields are missing.
    y = row.get("residual_Y", ledger.get("residual_Y") if isinstance(ledger, Mapping) else None)
    z = row.get("linear_defect_Z", ledger.get("linear_defect_Z") if isinstance(ledger, Mapping) else None)
    t = row.get("tail_bound_T", ledger.get("tail_bound_T") if isinstance(ledger, Mapping) else None)
    r = row.get("radius_r", ledger.get("radius_r") if isinstance(ledger, Mapping) else None)
    if all(isinstance(x, (int, float)) and math.isfinite(float(x)) for x in (y, z, t, r)):
        return float(r) - (float(y) + float(z) * float(r) + float(t))
    return None


def row_is_ready(row: Mapping[str, Any]) -> bool:
    margin = recompute_margin(row)
    return bool(
        (row.get("theorem_ready") or row.get("certified"))
        and str(row.get("closure_level", "")) == "analytic_theorem_closure"
        and not bool(row.get("finite_dimensional_only", False))
        and margin is not None
        and math.isfinite(float(margin))
        and float(margin) > 0.0
    )


def iter_candidate_paths(root: str | Path = ".", extra_globs: Sequence[str] | None = None) -> list[Path]:
    root_p = Path(root)
    globs = list(extra_globs or [])
    if not globs:
        globs = [
            "artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_000_candidate.json",
            "artifacts/proof_audit/lower_corridor/lower_anchor_phase2k_merged_rescued_candidate.json",
            "artifacts/proof_audit/lower_corridor/phase2j_rescue/*_candidate.json",
            "artifacts/proof_audit/lower_corridor/phase2m_collar/*_candidate.json",
        ]
    paths: list[Path] = []
    seen: set[str] = set()
    for pattern in globs:
        for p in root_p.glob(pattern):
            key = p.resolve().as_posix()
            if p.is_file() and key not in seen:
                paths.append(p)
                seen.add(key)
    return sorted(paths)


def collect_ready_rows(root: str | Path = ".", extra_globs: Sequence[str] | None = None) -> list[ReadyRow]:
    out: list[ReadyRow] = []
    for path in iter_candidate_paths(root, extra_globs):
        try:
            data = _load_json(path)
        except Exception:
            continue
        for row in candidate_rows(data):
            if not row_is_ready(row):
                continue
            try:
                lo = float(row["K_lo"])
                hi = float(row["K_hi"])
                sid = str(row.get("segment_id", path.stem))
            except Exception:
                continue
            margin = recompute_margin(row)
            if margin is None:
                continue
            row2 = dict(row)
            row2.setdefault("source_artifact", path.as_posix())
            row2["radii_margin"] = float(margin)
            out.append(ReadyRow(sid, lo, hi, float(margin), path.as_posix(), row2))
    # De-duplicate exact source/segment/interval pairs, keeping the largest margin.
    best: dict[tuple[str, float, float], ReadyRow] = {}
    for r in out:
        key = (r.segment_id, round(r.K_lo, 15), round(r.K_hi, 15))
        if key not in best or r.margin > best[key].margin:
            best[key] = r
    return sorted(best.values(), key=lambda r: (r.K_lo, r.K_hi, -r.margin, r.segment_id))


def greedy_cover_interval(
    rows: Sequence[ReadyRow],
    *,
    start: float,
    target_hi: float,
    overlap_tol: float = DEFAULT_OVERLAP_TOL,
) -> CoverageResult:
    """Greedy interval cover using theorem-ready rows.

    At each step select an interval whose left endpoint overlaps the current
    covered frontier and whose right endpoint extends coverage the farthest.  If
    there is a tie, prefer the row with larger margin.
    """

    current = float(start)
    selected: list[ReadyRow] = []
    gaps: list[tuple[float, float]] = []
    min_overlap: float | None = None
    unused = list(rows)
    while current < float(target_hi) - overlap_tol:
        candidates = [r for r in unused if r.K_lo <= current + overlap_tol and r.K_hi > current + overlap_tol]
        if not candidates:
            next_lefts = [r.K_lo for r in unused if r.K_hi > current + overlap_tol]
            if next_lefts:
                gaps.append((current, min(next_lefts)))
            else:
                gaps.append((current, float(target_hi)))
            break
        chosen = max(candidates, key=lambda r: (r.K_hi, r.margin))
        if selected:
            ov = selected[-1].K_hi - chosen.K_lo
            min_overlap = ov if min_overlap is None else min(min_overlap, ov)
        selected.append(chosen)
        current = max(current, chosen.K_hi)
        unused.remove(chosen)
    covered = None if not selected else (float(start), max(r.K_hi for r in selected))
    min_margin = None if not selected else min(r.margin for r in selected)
    complete = bool(covered and covered[1] >= float(target_hi) - overlap_tol and not gaps)
    return CoverageResult(
        requested_interval=(float(start), float(target_hi)),
        covered_interval=covered,
        selected_rows=tuple(selected),
        gaps=tuple(gaps),
        min_margin=min_margin,
        min_overlap=min_overlap,
        coverage_complete=complete,
    )


def freeze_regime_i(
    *,
    root: str | Path = ".",
    start: float = DEFAULT_REGIME_I_START,
    target_hi: float = DEFAULT_REGIME_I_TARGET_HI,
    output_path: str | Path = DEFAULT_REGIME_I_OUT,
    extra_globs: Sequence[str] | None = None,
) -> dict[str, Any]:
    rows = collect_ready_rows(root, extra_globs)
    coverage = greedy_cover_interval(rows, start=float(start), target_hi=float(target_hi))
    payload = {
        "schema": "phase2m_lower_regime_I_chain_v1",
        "theorem_facing": bool(coverage.coverage_complete),
        "diagnostic_only": not bool(coverage.coverage_complete),
        "promotion_allowed": bool(coverage.coverage_complete),
        "covered_interval": None if coverage.covered_interval is None else list(coverage.covered_interval),
        "requested_interval": list(coverage.requested_interval),
        "min_segment_margin": coverage.min_margin,
        "min_internal_overlap": coverage.min_overlap,
        "failure_fields": [] if coverage.coverage_complete else ["regime_I_coverage_incomplete"],
        "coverage": coverage.to_dict(),
        "anchor_segments": [r.row for r in coverage.selected_rows],
        "notes": "Regime I is the cached/segment-certified lower chain. It is accepted only if selected theorem-ready rows continuously cover the requested interval.",
    }
    out = Path(root) / output_path if not Path(output_path).is_absolute() else Path(output_path)
    _write_json(out, payload)
    return payload


def _extract_requested_from_name(name: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    m_os = re.search(r"_os(\d+)_", name)
    if m_os:
        out["requested_oversample_factor"] = int(m_os.group(1))
    m_sg = re.search(r"_sg([^_]+)_candidate\.json$", name)
    if m_sg:
        raw = m_sg.group(1).replace("p", ".").replace("m", "-")
        try:
            out["requested_sigma_cap"] = float(raw)
        except Exception:
            out["requested_sigma_raw"] = m_sg.group(1)
    return out


def diagnose_collar_failures(
    *,
    root: str | Path = ".",
    candidate_glob: str = "artifacts/proof_audit/lower_corridor/phase2j_rescue/phase2e_heavy_anchor_segment_00[5-9]*_candidate.json",
    json_out: str | Path = DEFAULT_DIAGNOSTICS_OUT,
    csv_out: str | Path = DEFAULT_DIAGNOSTICS_CSV,
) -> dict[str, Any]:
    root_p = Path(root)
    paths = sorted(root_p.glob(candidate_glob))
    rows_out: list[dict[str, Any]] = []
    sigma_mismatches: list[str] = []
    for path in paths:
        try:
            data = _load_json(path)
        except Exception:
            continue
        requested = _extract_requested_from_name(path.name)
        for row in candidate_rows(data):
            ledger = row.get("phase2e_ledger") if isinstance(row.get("phase2e_ledger"), Mapping) else {}
            actual_sigma = ledger.get("sigma", row.get("sigma")) if isinstance(ledger, Mapping) else row.get("sigma")
            requested_sigma = requested.get("requested_sigma_cap")
            sigma_mismatch = False
            if isinstance(requested_sigma, (int, float)) and isinstance(actual_sigma, (int, float)):
                # Treat actual sigma=0 as suspicious whenever a positive sigma was requested.
                sigma_mismatch = abs(float(actual_sigma) - float(requested_sigma)) > max(1.0e-15, 1.0e-6 * abs(float(requested_sigma)))
            if sigma_mismatch:
                sigma_mismatches.append(path.name)
            y = row.get("residual_Y", ledger.get("residual_Y") if isinstance(ledger, Mapping) else None)
            z = row.get("linear_defect_Z", ledger.get("linear_defect_Z") if isinstance(ledger, Mapping) else None)
            t = row.get("tail_bound_T", ledger.get("tail_bound_T") if isinstance(ledger, Mapping) else None)
            r = row.get("radius_r", ledger.get("radius_r") if isinstance(ledger, Mapping) else None)
            zr = float(z) * float(r) if isinstance(z, (int, float)) and isinstance(r, (int, float)) else None
            margin = recompute_margin(row)
            terms = {"residual_Y": y, "linear_term_Zr": zr, "tail_bound_T": t}
            numeric_terms = {k: float(v) for k, v in terms.items() if isinstance(v, (int, float)) and math.isfinite(float(v))}
            dominant = max(numeric_terms, key=numeric_terms.get) if numeric_terms else None
            rows_out.append({
                "file": path.as_posix(),
                "segment_id": row.get("segment_id"),
                "K_lo": row.get("K_lo"),
                "K_hi": row.get("K_hi"),
                "K_mid": row.get("K_mid"),
                "N": row.get("N"),
                "row_sigma": row.get("sigma"),
                "ledger_sigma": ledger.get("sigma") if isinstance(ledger, Mapping) else None,
                "requested_sigma_cap": requested.get("requested_sigma_cap"),
                "requested_oversample_factor": requested.get("requested_oversample_factor"),
                "sigma_propagation_mismatch": sigma_mismatch,
                "radius_r": r,
                "residual_Y": y,
                "linear_defect_Z": z,
                "linear_term_Zr": zr,
                "tail_bound_T": t,
                "radii_margin": margin,
                "radii_lhs": (float(y) + float(zr) + float(t)) if isinstance(y, (int, float)) and isinstance(zr, (int, float)) and isinstance(t, (int, float)) else None,
                "ready": bool(row.get("theorem_ready") or row.get("certified")),
                "failure_reasons": list(row.get("failure_reasons", [])),
                "dominant_failure_term": dominant,
            })
    # Sort diagnostics: best margins first, then by K.
    rows_out.sort(key=lambda d: (d.get("radii_margin") is None, -(float(d.get("radii_margin") or -1e99)), float(d.get("K_lo") or 0.0)))
    out_json = Path(root) / json_out if not Path(json_out).is_absolute() else Path(json_out)
    out_csv = Path(root) / csv_out if not Path(csv_out).is_absolute() else Path(csv_out)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    if rows_out:
        with out_csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            writer.writeheader()
            writer.writerows(rows_out)
    else:
        out_csv.write_text("")
    payload = {
        "schema": "phase2m_collar_diagnostics_v1",
        "candidate_glob": candidate_glob,
        "row_count": len(rows_out),
        "ready_row_count": sum(1 for r in rows_out if r.get("ready")),
        "sigma_mismatch_count": len(sigma_mismatches),
        "sigma_mismatch_files_sample": sigma_mismatches[:30],
        "best_rows": rows_out[:20],
        "dominant_term_counts": _counts(r.get("dominant_failure_term") for r in rows_out if not r.get("ready")),
        "failure_reason_counts": _counts(reason for r in rows_out for reason in r.get("failure_reasons", [])),
        "csv_out": out_csv.as_posix(),
        "failure_fields": (["sigma_propagation_mismatch"] if sigma_mismatches else []) + ([] if rows_out else ["no_collar_candidate_rows_found"]),
    }
    _write_json(out_json, payload)
    return payload


def _counts(items: Iterable[Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        key = str(item)
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def collar_profile_for_interval(lo: float, hi: float) -> dict[str, Any]:
    mid = 0.5 * (float(lo) + float(hi))
    if hi <= 0.9650001:
        return {
            "regime": "collar_tail_linear",
            "n_values": (1024, 1536, 2048, 3072, 4096),
            "oversample_factors": (64,),
            "sigma_caps": (0.00025, 0.0001),
            "max_wall_seconds": 2400.0,
        }
    if hi <= 0.9700002:
        return {
            "regime": "collar_mixed_tail_residual",
            "n_values": (1024, 2048, 4096, 6144),
            "oversample_factors": (64,),
            "sigma_caps": (0.00025, 0.0001, 0.00005),
            "max_wall_seconds": 3600.0,
        }
    return {
        "regime": "collar_endpoint",
        "n_values": (2048, 4096, 6144, 8192),
        "oversample_factors": (64,),
        "sigma_caps": (0.0001, 0.00005, 0.000025),
        "max_wall_seconds": 4800.0,
    }


def build_collar_intervals(
    *,
    start: float = DEFAULT_COLLAR_START,
    end: float = DEFAULT_FINAL_ANCHOR[1],
    overlap: float = 1.0e-7,
) -> list[tuple[float, float, float]]:
    """Default near-critical collar grid.

    The grid is intentionally finer than Phase 2L in [0.960, 0.970], because the
    Phase 2L diagnostics show that the 3-way split fails there.  Past 0.970 the
    step is smaller again because the endpoint collar is expected to be harder.
    """
    breakpoints: list[float] = []
    x = float(start)
    breakpoints.append(x)
    while x < 0.9700001 - 1e-15:
        x = min(0.9700001, x + 0.0005)
        breakpoints.append(x)
    while x < float(end) - 1e-15:
        x = min(float(end), x + 0.0002)
        breakpoints.append(x)
    intervals: list[tuple[float, float, float]] = []
    for i, (a, b) in enumerate(zip(breakpoints, breakpoints[1:])):
        lo = float(a) - (overlap if i > 0 else 0.0)
        hi = float(b) + (overlap if i < len(breakpoints) - 2 else 0.0)
        intervals.append((lo, hi, 0.5 * (float(a) + float(b))))
    return intervals


def _encode_float_for_name(x: float) -> str:
    return (f"{x:.8g}").replace("-", "m").replace(".", "p")


def build_collar_jobs(
    *,
    root: str | Path = ".",
    start: float = DEFAULT_COLLAR_START,
    end: float = DEFAULT_FINAL_ANCHOR[1],
    out_dir: str | Path = DEFAULT_COLLAR_DIR,
    table_dir: str | Path = DEFAULT_COLLAR_TABLE_DIR,
    python_executable: str | None = None,
    max_jobs: int | None = None,
) -> list[CollarJob]:
    root_p = Path(root)
    py = python_executable or sys.executable
    jobs: list[CollarJob] = []
    for idx, (lo, hi, mid) in enumerate(build_collar_intervals(start=start, end=end)):
        prof = collar_profile_for_interval(lo, hi)
        n_values = tuple(int(n) for n in prof["n_values"])
        for osamp in prof["oversample_factors"]:
            for sigma in prof["sigma_caps"]:
                job_id = f"phase2m_collar_{idx:03d}_os{osamp}_sg{_encode_float_for_name(float(sigma))}"
                cand = f"{job_id}_candidate.json"
                cmd = [
                    py,
                    "scripts/audit/run_lower_anchor_phase2g_segment.py",
                    "--segment-id", f"phase2m_collar_{idx:03d}",
                    "--K-lo", repr(lo),
                    "--K-hi", repr(hi),
                    "--K-mid", repr(mid),
                    "--N-values", ",".join(str(n) for n in n_values),
                    "--oversample-factor", str(int(osamp)),
                    "--sigma-cap", repr(float(sigma)),
                    "--max-wall-seconds", str(float(prof["max_wall_seconds"])),
                    "--out-dir", Path(out_dir).as_posix(),
                    "--table-dir", Path(table_dir).as_posix(),
                    "--candidate-name", cand,
                ]
                jobs.append(CollarJob(job_id, lo, hi, mid, str(prof["regime"]), n_values, int(osamp), float(sigma), float(prof["max_wall_seconds"]), cand, tuple(cmd)))
                if max_jobs is not None and len(jobs) >= int(max_jobs):
                    return jobs
    return jobs


def write_collar_plan(
    *,
    root: str | Path = ".",
    output_path: str | Path = DEFAULT_PLAN_OUT,
    run_script_path: str | Path = DEFAULT_RUN_SCRIPT,
    python_executable: str | None = None,
    max_jobs: int | None = None,
) -> dict[str, Any]:
    root_p = Path(root)
    jobs = build_collar_jobs(root=root_p, python_executable=python_executable, max_jobs=max_jobs)
    payload = {
        "schema": "phase2m_nearcritical_collar_plan_v1",
        "start": DEFAULT_COLLAR_START,
        "final_anchor": list(DEFAULT_FINAL_ANCHOR),
        "job_count": len(jobs),
        "jobs": [j.to_dict() for j in jobs],
        "notes": "These are targeted collar microsegment jobs. They are not theorem evidence until their candidate rows are theorem_ready/certified and verified by the two-regime checker.",
    }
    out = root_p / output_path if not Path(output_path).is_absolute() else Path(output_path)
    _write_json(out, payload)
    script = root_p / run_script_path if not Path(run_script_path).is_absolute() else Path(run_script_path)
    script.parent.mkdir(parents=True, exist_ok=True)
    lines = ["#!/bin/bash", "set -euo pipefail", "", "# Auto-generated Phase 2M collar job runner."]
    for j in jobs:
        cand_path = Path(DEFAULT_COLLAR_DIR) / j.candidate_name
        lines.append("")
        lines.append(f"echo 'Running {j.job_id}'")
        lines.append(" ".join(shlex.quote(x) for x in j.command))
    script.write_text("\n".join(lines) + "\n")
    script.chmod(0o755)
    payload["run_script"] = script.as_posix()
    _write_json(out, payload)
    return payload


def execute_collar_jobs(
    *,
    root: str | Path = ".",
    plan_path: str | Path = DEFAULT_PLAN_OUT,
    log_dir: str | Path = DEFAULT_COLLAR_LOG_DIR,
    max_jobs: int | None = None,
    force: bool = False,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    root_p = Path(root)
    plan_p = root_p / plan_path if not Path(plan_path).is_absolute() else Path(plan_path)
    plan = _load_json(plan_p)
    raw_jobs = plan.get("jobs", [])
    if not isinstance(raw_jobs, list):
        raw_jobs = []
    if max_jobs is not None:
        raw_jobs = raw_jobs[: int(max_jobs)]
    log_p = root_p / log_dir if not Path(log_dir).is_absolute() else Path(log_dir)
    log_p.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root_p.resolve()) + ((os.pathsep + env.get("PYTHONPATH", "")) if env.get("PYTHONPATH") else "")
    executions: list[CollarJobExecution] = []
    for job in raw_jobs:
        if not isinstance(job, Mapping):
            continue
        candidate = root_p / DEFAULT_COLLAR_DIR / str(job["candidate_name"])
        skipped_ready = False
        if candidate.exists() and not force:
            try:
                data = _load_json(candidate)
                skipped_ready = any(row_is_ready(r) for r in candidate_rows(data))
            except Exception:
                skipped_ready = False
            if skipped_ready:
                rows = [r for r in candidate_rows(_load_json(candidate)) if row_is_ready(r)]
                margins = [recompute_margin(r) for r in rows]
                margins = [float(m) for m in margins if m is not None]
                executions.append(CollarJobExecution(str(job["job_id"]), str(job["candidate_name"]), False, True, None, False, None, len(rows), min(margins) if margins else None, max(margins) if margins else None, None, None))
                continue
        stdout = log_p / f"{job['job_id']}.stdout.log"
        stderr = log_p / f"{job['job_id']}.stderr.log"
        start = time.monotonic()
        timed_out = False
        rc: int | None = None
        try:
            proc = subprocess.run([str(x) for x in job["command"]], cwd=root_p, env=env, capture_output=True, text=True, timeout=timeout_seconds)
            rc = int(proc.returncode)
            stdout.write_text(proc.stdout or "")
            stderr.write_text(proc.stderr or "")
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout.write_text(exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""))
            stderr.write_text((exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")) + "\nPHASE2M_TIMEOUT\n")
        duration = time.monotonic() - start
        ready_count = 0
        margins: list[float] = []
        if candidate.exists():
            try:
                for r in candidate_rows(_load_json(candidate)):
                    if row_is_ready(r):
                        ready_count += 1
                    m = recompute_margin(r)
                    if m is not None:
                        margins.append(float(m))
            except Exception:
                pass
        executions.append(CollarJobExecution(str(job["job_id"]), str(job["candidate_name"]), True, False, rc, timed_out, duration, ready_count, min(margins) if margins else None, max(margins) if margins else None, stdout.as_posix(), stderr.as_posix()))
    summary = {
        "schema": "phase2m_collar_job_execution_summary_v1",
        "plan_path": plan_p.as_posix(),
        "attempted_count": sum(1 for e in executions if e.attempted),
        "skipped_ready_count": sum(1 for e in executions if e.skipped_ready),
        "theorem_ready_job_count": sum(1 for e in executions if e.theorem_ready_rows > 0),
        "timeout_count": sum(1 for e in executions if e.timed_out),
        "executions": [e.to_dict() for e in executions],
    }
    _write_json(root_p / DEFAULT_LOWER_DIR / "phase2m_collar_execution_summary.json", summary)
    return summary


def verify_collar(
    *,
    root: str | Path = ".",
    start: float = DEFAULT_COLLAR_START,
    end: float = DEFAULT_FINAL_ANCHOR[1],
    output_path: str | Path = DEFAULT_COLLAR_THEOREM_OUT,
) -> dict[str, Any]:
    rows = collect_ready_rows(root, ["artifacts/proof_audit/lower_corridor/phase2m_collar/*_candidate.json"])
    coverage = greedy_cover_interval(rows, start=float(start), target_hi=float(end), overlap_tol=DEFAULT_OVERLAP_TOL)
    payload = {
        "schema": "phase2m_nearcritical_collar_theorem_v1",
        "theorem_facing": bool(coverage.coverage_complete),
        "diagnostic_only": not bool(coverage.coverage_complete),
        "promotion_allowed": bool(coverage.coverage_complete),
        "collar_interval": [float(start), float(end)],
        "covered_interval": None if coverage.covered_interval is None else list(coverage.covered_interval),
        "min_segment_margin": coverage.min_margin,
        "min_internal_overlap": coverage.min_overlap,
        "failure_fields": [] if coverage.coverage_complete else ["nearcritical_collar_coverage_incomplete"],
        "coverage": coverage.to_dict(),
        "collar_segments": [r.row for r in coverage.selected_rows],
        "notes": "Regime II collar theorem. This is theorem-facing only when ready rows continuously cover the collar interval.",
    }
    out = Path(root) / output_path if not Path(output_path).is_absolute() else Path(output_path)
    _write_json(out, payload)
    return payload


def assemble_two_regime_certificate(
    *,
    root: str | Path = ".",
    regime_i_path: str | Path = DEFAULT_REGIME_I_OUT,
    collar_path: str | Path = DEFAULT_COLLAR_THEOREM_OUT,
    output_path: str | Path = DEFAULT_TWO_REGIME_OUT,
) -> dict[str, Any]:
    root_p = Path(root)
    reg_path = root_p / regime_i_path if not Path(regime_i_path).is_absolute() else Path(regime_i_path)
    col_path = root_p / collar_path if not Path(collar_path).is_absolute() else Path(collar_path)
    reg = _load_json(reg_path) if reg_path.exists() else {}
    col = _load_json(col_path) if col_path.exists() else {}
    reg_ok = bool(reg.get("theorem_facing") and not reg.get("diagnostic_only"))
    col_ok = bool(col.get("theorem_facing") and not col.get("diagnostic_only"))
    reg_interval = reg.get("covered_interval") or [None, None]
    col_interval = col.get("covered_interval") or [None, None]
    overlap = None
    if isinstance(reg_interval, list) and isinstance(col_interval, list) and len(reg_interval) == 2 and len(col_interval) == 2:
        if reg_interval[1] is not None and col_interval[0] is not None:
            overlap = float(reg_interval[1]) - float(col_interval[0])
    link_ok = overlap is not None and overlap >= -DEFAULT_OVERLAP_TOL
    final_ok = isinstance(col_interval, list) and len(col_interval) == 2 and col_interval[1] is not None and float(col_interval[1]) >= DEFAULT_FINAL_ANCHOR[1] - DEFAULT_OVERLAP_TOL
    margins = [x for x in [reg.get("min_segment_margin"), col.get("min_segment_margin")] if isinstance(x, (int, float))]
    min_margin = min(margins) if margins else None
    failure_fields: list[str] = []
    if not reg_ok:
        failure_fields.append("regime_I_not_verified")
    if not col_ok:
        failure_fields.append("nearcritical_collar_not_verified")
    if not link_ok:
        failure_fields.append("regime_I_to_collar_overlap_not_verified")
    if not final_ok:
        failure_fields.append("final_anchor_not_reached_by_two_regime_certificate")
    theorem_facing = not failure_fields
    anchor_segments = list(reg.get("anchor_segments", [])) + list(col.get("collar_segments", []))
    payload = {
        "schema": "phase2m_two_regime_lower_certificate_v1",
        "theorem_facing": theorem_facing,
        "diagnostic_only": not theorem_facing,
        "promotion_allowed": theorem_facing,
        "regime_I_path": reg_path.as_posix(),
        "collar_path": col_path.as_posix(),
        "regime_I_verified": reg_ok,
        "nearcritical_collar_verified": col_ok,
        "regime_I_to_collar_overlap": overlap,
        "regime_I_to_collar_overlap_positive": link_ok,
        "final_anchor_reached": final_ok,
        "covered_interval": [reg_interval[0], col_interval[1]] if theorem_facing else [reg_interval[0], col_interval[1] if isinstance(col_interval, list) and len(col_interval) == 2 else None],
        "final_anchor": list(DEFAULT_FINAL_ANCHOR),
        "min_segment_margin": min_margin,
        "failure_fields": failure_fields,
        "anchor_segments": anchor_segments,
        "notes": "Two-regime lower proof object: Regime I cached chain plus Regime II near-critical collar.",
    }
    out = root_p / output_path if not Path(output_path).is_absolute() else Path(output_path)
    _write_json(out, payload)
    return payload
