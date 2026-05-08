from __future__ import annotations

"""Phase-2I bounded executor for missing lower-anchor segments.

Phase 2H identified the remaining work: execute missing Phase-2E/2G refined
segments and then merge them.  The original generated shell script is correct
for an HPC/long-running environment, but it is inconvenient for bounded CI or
notebook sessions because a single difficult segment can hang the entire run.

This module adds a fail-closed subprocess executor.  It inventories the Phase-2H
status, runs missing or failing segment commands one-at-a-time with a hard wall
clock timeout, captures stdout/stderr, records dependency/preflight status, and
then refreshes the Phase-2H inventory.  It never marks a timed-out segment as
certified.  Its purpose is to turn "the run hung" into an auditable per-segment
failure table that can drive the next refinement step.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import signal
import shlex
import subprocess
import sys
import time

from .lower_anchor_phase2h_execution import (
    DEFAULT_LOWER_DIR,
    DEFAULT_REFINEMENT_DIR,
    DEFAULT_TABLE_DIR,
    build_phase2h_execution_status,
    write_phase2h_status,
)


@dataclass(frozen=True)
class Phase2IPreflight:
    schema: str
    python_executable: str
    no_site: bool
    repo_root: str
    pythonpath: str
    import_numpy_ok: bool
    import_mpmath_ok: bool
    import_torus_validator_ok: bool
    import_error: str | None
    using_mpmath_fallback: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Phase2ISegmentExecution:
    segment_id: str
    index: int
    K_lo: float
    K_hi: float
    K_mid: float
    command: tuple[str, ...]
    timeout_seconds: float
    started_at_epoch: float
    elapsed_seconds: float
    returncode: int | None
    timed_out: bool
    candidate_path: str
    stdout_path: str
    stderr_path: str
    stdout_tail: str
    stderr_tail: str
    candidate_created: bool
    theorem_ready_after_run: bool | None
    failure_class: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["command"] = list(self.command)
        return data


@dataclass(frozen=True)
class Phase2IExecutionReport:
    schema: str
    repo_root: str
    plan_path: str
    lower_dir: str
    refinement_dir: str
    table_dir: str
    preflight: Phase2IPreflight
    requested_segment_count: int
    executed_segment_count: int
    timeout_count: int
    success_returncode_count: int
    candidate_created_count: int
    theorem_ready_after_run_count: int
    before_ready_count: int
    after_ready_count: int
    before_missing_count: int
    after_missing_count: int
    before_failed_count: int
    after_failed_count: int
    final_anchor_reached_after_run: bool
    promotion_allowed_after_run: bool
    executions: tuple[Phase2ISegmentExecution, ...]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["preflight"] = self.preflight.to_dict()
        data["executions"] = [x.to_dict() for x in self.executions]
        data["recommendations"] = list(self.recommendations)
        return data


def _tail(text: str, max_chars: int = 2000) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _read_text(path: Path, max_chars: int = 2000) -> str:
    try:
        return _tail(path.read_text(errors="replace"), max_chars=max_chars)
    except Exception:
        return ""


def _build_pythonpath(repo_root: Path, extra_paths: Sequence[str] = ()) -> str:
    parts: list[str] = [repo_root.as_posix()]
    # Debian/Ubuntu place distro packages here; adding it lets ``python -S`` use
    # numpy without importing user/site startup files that can hang in notebooks.
    distro = Path("/usr/lib/python3/dist-packages")
    if distro.exists():
        parts.append(distro.as_posix())
    parts.extend(str(x) for x in extra_paths if str(x))
    old = os.environ.get("PYTHONPATH", "")
    if old:
        parts.append(old)
    # Deduplicate without changing order.
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        if p not in seen:
            out.append(p); seen.add(p)
    return os.pathsep.join(out)


def run_preflight(*, repo_root: str | Path, python_executable: str | None = None, no_site: bool = True, extra_pythonpath: Sequence[str] = ()) -> Phase2IPreflight:
    root = Path(repo_root).resolve()
    py = python_executable or sys.executable
    pythonpath = _build_pythonpath(root, extra_pythonpath)
    code = """
import json
out = {'numpy': False, 'mpmath': False, 'torus_validator': False, 'mpmath_fallback': False, 'error': None}
try:
    import numpy
    out['numpy'] = True
except Exception as exc:
    out['error'] = 'numpy:' + repr(exc)
try:
    import mpmath
    out['mpmath'] = True
except Exception:
    try:
        from kam_theorem_suite import _mpmath_fallback as mpmath
        out['mpmath'] = True
        out['mpmath_fallback'] = True
    except Exception as exc:
        out['error'] = (out['error'] or '') + ';mpmath:' + repr(exc)
try:
    from kam_theorem_suite.torus_validator import build_theorem_optimized_analytic_invariant_circle_certificate
    out['torus_validator'] = True
except Exception as exc:
    out['error'] = (out['error'] or '') + ';torus_validator:' + repr(exc)
print(json.dumps(out, sort_keys=True))
""".strip()
    cmd = [py]
    if no_site:
        cmd.append("-S")
    cmd.extend(["-c", code])
    env = os.environ.copy(); env["PYTHONPATH"] = pythonpath
    import_error: str | None = None
    np_ok = mp_ok = tv_ok = fallback = False
    try:
        proc = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True, timeout=60)
        payload = json.loads((proc.stdout or "{}").strip().splitlines()[-1]) if proc.stdout.strip() else {}
        np_ok = bool(payload.get("numpy")); mp_ok = bool(payload.get("mpmath")); tv_ok = bool(payload.get("torus_validator")); fallback = bool(payload.get("mpmath_fallback"))
        if proc.returncode != 0 or payload.get("error"):
            import_error = str(payload.get("error") or proc.stderr[-1000:])
    except Exception as exc:
        import_error = repr(exc)
    return Phase2IPreflight(
        schema="phase2i_preflight_v1",
        python_executable=str(py),
        no_site=bool(no_site),
        repo_root=root.as_posix(),
        pythonpath=pythonpath,
        import_numpy_ok=np_ok,
        import_mpmath_ok=mp_ok,
        import_torus_validator_ok=tv_ok,
        import_error=import_error,
        using_mpmath_fallback=fallback,
    )


def _segment_command(
    *,
    python_executable: str,
    no_site: bool,
    segment: Any,
    n_values: str,
    oversample_factor: int,
    sigma_cap: float,
    out_dir: Path,
    table_dir: Path,
) -> tuple[list[str], Path]:
    candidate_name = f"phase2g_complete_{segment.segment_id}_candidate.json"
    cmd = [python_executable]
    if no_site:
        cmd.append("-S")
    cmd.extend([
        "scripts/audit/run_lower_anchor_phase2g_segment.py",
        "--segment-id", str(segment.segment_id),
        "--K-lo", repr(float(segment.K_lo)),
        "--K-hi", repr(float(segment.K_hi)),
        "--K-mid", repr(float(segment.K_mid)),
        "--N-values", str(n_values),
        "--oversample-factor", str(int(oversample_factor)),
        "--sigma-cap", repr(float(sigma_cap)),
        "--out-dir", out_dir.as_posix(),
        "--table-dir", table_dir.as_posix(),
        "--candidate-name", candidate_name,
    ])
    return cmd, out_dir / candidate_name


def _candidate_theorem_ready(path: Path, segment_id: str) -> bool | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except Exception:
        return False
    rows = data.get("anchor_segments", [])
    if not isinstance(rows, list):
        return False
    for row in rows:
        if isinstance(row, Mapping) and str(row.get("segment_id")) == str(segment_id):
            try:
                r = float(row.get("radius_r", 0.0)); y = float(row.get("residual_Y", 0.0)); z = float(row.get("linear_defect_Z", 0.0)); t = float(row.get("tail_bound_T", 0.0))
                margin = r - (y + z*r + t)
            except Exception:
                margin = -1.0
            return bool(row.get("certified") and not row.get("finite_dimensional_only") and row.get("closure_level") == "analytic_theorem_closure" and margin > 0.0)
    return False


def run_phase2i_bounded_execution(
    *,
    repo_root: str | Path,
    plan_path: str | Path = DEFAULT_LOWER_DIR / "lower_anchor_phase2f_full_grid_plan.json",
    lower_dir: str | Path = DEFAULT_LOWER_DIR,
    refinement_dir: str | Path = DEFAULT_REFINEMENT_DIR,
    table_dir: str | Path = DEFAULT_TABLE_DIR,
    report_path: str | Path = DEFAULT_LOWER_DIR / "lower_anchor_phase2i_bounded_execution_report.json",
    refreshed_status_path: str | Path = DEFAULT_LOWER_DIR / "lower_anchor_phase2i_refreshed_phase2h_status.json",
    log_dir: str | Path = DEFAULT_LOWER_DIR / "phase2i_logs",
    python_executable: str | None = None,
    no_site: bool = True,
    n_values: str = "64,96,128,192,256,384,512",
    oversample_factor: int = 16,
    sigma_cap: float = 0.02,
    segment_timeout_seconds: float = 900.0,
    max_segments: int | None = None,
    include_failed_present: bool = False,
    extra_pythonpath: Sequence[str] = (),
) -> Phase2IExecutionReport:
    root = Path(repo_root).resolve()
    lower_p = (root / lower_dir) if not Path(lower_dir).is_absolute() else Path(lower_dir)
    refine_p = (root / refinement_dir) if not Path(refinement_dir).is_absolute() else Path(refinement_dir)
    table_p = (root / table_dir) if not Path(table_dir).is_absolute() else Path(table_dir)
    plan_p = (root / plan_path) if not Path(plan_path).is_absolute() else Path(plan_path)
    log_p = (root / log_dir) if not Path(log_dir).is_absolute() else Path(log_dir)
    report_p = (root / report_path) if not Path(report_path).is_absolute() else Path(report_path)
    refreshed_p = (root / refreshed_status_path) if not Path(refreshed_status_path).is_absolute() else Path(refreshed_status_path)
    refine_p.mkdir(parents=True, exist_ok=True); table_p.mkdir(parents=True, exist_ok=True); log_p.mkdir(parents=True, exist_ok=True)
    py = python_executable or sys.executable
    preflight = run_preflight(repo_root=root, python_executable=py, no_site=no_site, extra_pythonpath=extra_pythonpath)
    before = build_phase2h_execution_status(plan_path=plan_p, lower_dir=lower_p, refinement_dir=refine_p)
    targets = [s for s in before.segments if (not s.present) or (include_failed_present and s.present and not s.theorem_ready)]
    if max_segments is not None:
        targets = targets[: max(0, int(max_segments))]
    pythonpath = _build_pythonpath(root, extra_pythonpath)
    env = os.environ.copy(); env["PYTHONPATH"] = pythonpath
    executions: list[Phase2ISegmentExecution] = []
    for seg in targets:
        cmd, candidate_path = _segment_command(
            python_executable=py,
            no_site=no_site,
            segment=seg,
            n_values=n_values,
            oversample_factor=oversample_factor,
            sigma_cap=sigma_cap,
            out_dir=refine_p,
            table_dir=table_p,
        )
        stdout_file = log_p / f"{seg.segment_id}.stdout.log"
        stderr_file = log_p / f"{seg.segment_id}.stderr.log"
        started = time.time(); timed_out = False; rc: int | None = None; stdout = stderr = ""
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=root,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stdout, stderr = proc.communicate(timeout=float(segment_timeout_seconds))
                rc = int(proc.returncode)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                try:
                    stdout, stderr = proc.communicate(timeout=5.0)
                except Exception:
                    stdout, stderr = "", ""
                rc = None
                stderr = (stderr or "") + f"\n[phase2i] subprocess process-group killed after timeout={segment_timeout_seconds} seconds\n"
        except Exception as exc:
            rc = None
            stderr = repr(exc)
        elapsed = time.time() - started
        stdout_file.write_text(stdout or "")
        stderr_file.write_text(stderr or "")
        ready = _candidate_theorem_ready(candidate_path, seg.segment_id)
        if timed_out:
            failure_class = "timeout"
        elif rc != 0:
            failure_class = "subprocess_nonzero_returncode"
        elif not candidate_path.exists():
            failure_class = "candidate_not_created"
        elif ready is True:
            failure_class = "theorem_ready_candidate_created"
        else:
            failure_class = "candidate_created_but_not_theorem_ready"
        executions.append(Phase2ISegmentExecution(
            segment_id=seg.segment_id,
            index=int(seg.index),
            K_lo=float(seg.K_lo), K_hi=float(seg.K_hi), K_mid=float(seg.K_mid),
            command=tuple(cmd),
            timeout_seconds=float(segment_timeout_seconds),
            started_at_epoch=float(started),
            elapsed_seconds=float(elapsed),
            returncode=rc,
            timed_out=bool(timed_out),
            candidate_path=candidate_path.as_posix(),
            stdout_path=stdout_file.as_posix(),
            stderr_path=stderr_file.as_posix(),
            stdout_tail=_tail(stdout or ""),
            stderr_tail=_tail(stderr or ""),
            candidate_created=bool(candidate_path.exists()),
            theorem_ready_after_run=ready,
            failure_class=failure_class,
        ))
        # Incremental checkpoint so a bounded execution still leaves useful
        # evidence if the outer job is killed after several segments.
        checkpoint = {
            "schema": "phase2i_incremental_execution_checkpoint_v1",
            "completed_segment_count": len(executions),
            "latest_segment_id": str(seg.segment_id),
            "executions": [x.to_dict() for x in executions],
        }
        report_p.parent.mkdir(parents=True, exist_ok=True)
        report_p.with_suffix(".checkpoint.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")
    after = build_phase2h_execution_status(plan_path=plan_p, lower_dir=lower_p, refinement_dir=refine_p)
    write_phase2h_status(after, refreshed_p)
    recs = [
        "If timeout_count is nonzero, rerun those segments on HPC with a larger per-segment wall time or smaller subsegments.",
        "If candidate_created_but_not_theorem_ready appears, feed that candidate to the Phase-2G refinement planner for bound-specific rescue.",
        "Do not promote unless the refreshed Phase-2H status reports no missing/failed segments and strict ingestion passes.",
    ]
    if preflight.using_mpmath_fallback:
        recs.append("This run used the local float-based mpmath fallback; install real mpmath for theorem-grade interval paths before final promotion.")
    report = Phase2IExecutionReport(
        schema="phase2i_bounded_segment_execution_report_v1",
        repo_root=root.as_posix(),
        plan_path=plan_p.as_posix(),
        lower_dir=lower_p.as_posix(),
        refinement_dir=refine_p.as_posix(),
        table_dir=table_p.as_posix(),
        preflight=preflight,
        requested_segment_count=len(targets),
        executed_segment_count=len(executions),
        timeout_count=sum(1 for x in executions if x.timed_out),
        success_returncode_count=sum(1 for x in executions if x.returncode == 0),
        candidate_created_count=sum(1 for x in executions if x.candidate_created),
        theorem_ready_after_run_count=sum(1 for x in executions if x.theorem_ready_after_run is True),
        before_ready_count=int(before.ready_segment_count),
        after_ready_count=int(after.ready_segment_count),
        before_missing_count=int(before.missing_segment_count),
        after_missing_count=int(after.missing_segment_count),
        before_failed_count=int(before.failed_segment_count),
        after_failed_count=int(after.failed_segment_count),
        final_anchor_reached_after_run=bool(after.final_anchor_reached_by_available_segments),
        promotion_allowed_after_run=bool(after.promotion_allowed),
        executions=tuple(executions),
        recommendations=tuple(recs),
    )
    report_p.parent.mkdir(parents=True, exist_ok=True)
    report_p.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
    return report


__all__ = [
    "Phase2IPreflight",
    "Phase2ISegmentExecution",
    "Phase2IExecutionReport",
    "run_preflight",
    "run_phase2i_bounded_execution",
]
