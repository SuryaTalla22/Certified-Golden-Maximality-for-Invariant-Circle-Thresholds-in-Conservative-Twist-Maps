#!/usr/bin/env python3
from __future__ import annotations

"""Regenerate the theorem-facing Track-B Theorem III certificate.

This script replaces the historical notebook workflow with a command-line,
fail-closed regeneration path for the final Theorem III lower-anchor object.
It deliberately records every command, path, elapsed time, selected seed, and
final artifact hash.

The default path is theorem-facing rather than archival: it regenerates the
canonical numerical seed, the selected H1-polished seed, the Phase 5 formal
attachments, Phase 5K promotion, and Phase 6 final integration. Historical
exploratory diagnostics may be added later, but they are not required for the
final theorem-facing certificate consumed by the proof chain.
"""

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Keep nested BLAS/OpenMP libraries from oversubscribing by default. Users can
# explicitly export different values before launching this script.
for _key in [
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
]:
    os.environ.setdefault(_key, "1")


K_ANCHOR = 0.971635
K_ANCHOR_STR = "0.9716350"
SELECTED_SEED_NAME = "K0p9716350000_M8192_H1_SELECTED.npz"
REQUIRED_NU = 1.001
REQUIRED_RADIUS = 3.0e-5
REQUIRED_CUTOFF = "full"
REQUIRED_TAIL_START = 0.90
MIN_RELATIVE_MARGIN = 0.25
MAX_Z = 0.5


def find_project_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for cand in [start, *start.parents]:
        if (cand / "kam_theorem_suite").is_dir() and (cand / "scripts").is_dir():
            return cand
    raise RuntimeError("Could not locate repository root containing kam_theorem_suite/ and scripts/.")


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def relpath(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dump_json(path: Path, obj: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class CommandResult:
    name: str
    cmd: list[str]
    returncode: int
    elapsed_seconds: float
    stdout_log: str | None
    stderr_log: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "cmd": self.cmd,
            "returncode": self.returncode,
            "elapsed_seconds": self.elapsed_seconds,
            "stdout_log": self.stdout_log,
            "stderr_log": self.stderr_log,
            "passed": self.returncode == 0,
        }


class Runner:
    def __init__(self, root: Path, logs_dir: Path, *, dry_run: bool = False):
        self.root = root
        self.logs_dir = logs_dir
        self.dry_run = dry_run
        self.results: list[CommandResult] = []
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def run(self, name: str, cmd: list[str]) -> CommandResult:
        pretty = " ".join(cmd)
        print(f"\n[{name}] $ {pretty}", flush=True)
        stdout_path = self.logs_dir / f"{name}.stdout.log"
        stderr_path = self.logs_dir / f"{name}.stderr.log"
        t0 = time.time()
        if self.dry_run:
            stdout_path.write_text("DRY RUN: command not executed.\n" + pretty + "\n", encoding="utf-8")
            stderr_path.write_text("", encoding="utf-8")
            rc = 0
        else:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.root) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
            with stdout_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
                proc = subprocess.run(cmd, cwd=self.root, stdout=out, stderr=err, text=True, env=env)
            rc = int(proc.returncode)
        dt = time.time() - t0
        result = CommandResult(
            name=name,
            cmd=cmd,
            returncode=rc,
            elapsed_seconds=dt,
            stdout_log=relpath(stdout_path, self.root),
            stderr_log=relpath(stderr_path, self.root),
        )
        self.results.append(result)
        print(f"[{name}] exit={rc} elapsed={dt:.2f}s", flush=True)
        if rc != 0:
            raise SystemExit(f"Stage {name!r} failed with exit code {rc}. See {stdout_path} and {stderr_path}.")
        return result


def py(root: Path, *args: str) -> list[str]:
    return [sys.executable, *args]


def clean_paths(paths: Iterable[Path], *, dry_run: bool = False) -> None:
    for path in paths:
        if not path.exists():
            continue
        print(f"Removing {path}")
        if dry_run:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def choose_and_copy_selected_h1_seed(root: Path, summary_path: Path, target_path: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Choose the canonical Phase-4i H1 seed and copy it to the stable selected path."""
    if dry_run:
        return {
            "status": "dry-run",
            "summary_path": relpath(summary_path, root),
            "selected_output_npz": relpath(target_path, root),
        }
    summary = load_json(summary_path)
    candidates = list(summary.get("top_candidates", []) or [])
    if not candidates:
        raise RuntimeError(f"No Phase-4i candidates found in {summary_path}.")

    def score(row: dict[str, Any]) -> tuple:
        # Prefer theorem-facing conditions: K=0.971635, M_out=8192, full cutoff,
        # converged H1, then smallest derivative residual and smallest scalar residual.
        k_pen = abs(float(row.get("K", 0.0)) - K_ANCHOR)
        m_pen = 0 if int(row.get("M_out", 0)) == 8192 else 1
        cutoff = row.get("cutoff_mode", "not-full")
        cutoff_pen = 0 if cutoff in (None, "", "full") else 1
        conv_pen = 0 if bool(row.get("converged_h1", False)) else 1
        deriv = float(row.get("after_derivative_linf", float("inf")))
        scalar = float(row.get("after_scalar_linf", float("inf")))
        return (k_pen, m_pen, cutoff_pen, conv_pen, deriv, scalar)

    selected = sorted(candidates, key=score)[0]
    source = root / str(selected.get("output_npz", ""))
    if not source.exists():
        raise FileNotFoundError(f"Selected Phase-4i seed does not exist: {source}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target_path)
    manifest = {
        "schema": "theorem_iii_trackb_selected_h1_seed_manifest_v1",
        "status": "selected-h1-seed-copied",
        "selected_row": selected,
        "source_path": relpath(source, root),
        "target_path": relpath(target_path, root),
        "source_sha256": sha256_file(source),
        "target_sha256": sha256_file(target_path),
        "selection_rule": "K=0.971635, M_out=8192, full cutoff, converged-H1 preferred, then smallest derivative/scalar residual.",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    dump_json(target_path.parent / "selected_h1_seed_manifest.json", manifest)
    print(f"Selected H1 seed: {relpath(source, root)} -> {relpath(target_path, root)}")
    return manifest


def copy_to_stage_cache(root: Path, final_artifact: Path, *, dry_run: bool = False) -> dict[str, Any]:
    stage_cache = root / "artifacts" / "final_discharge" / "stage_cache"
    stage_cache.mkdir(parents=True, exist_ok=True)
    target = stage_cache / "theorem_iii.json"
    if dry_run:
        return {
            "schema": "theorem_iii_trackb_stage_cache_install_v1",
            "status": "dry-run",
            "source": relpath(final_artifact, root),
            "target": relpath(target, root),
            "source_sha256": None,
            "target_sha256": None,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
    if not final_artifact.exists():
        raise FileNotFoundError(final_artifact)
    shutil.copy2(final_artifact, target)
    return {
        "schema": "theorem_iii_trackb_stage_cache_install_v1",
        "status": "installed",
        "source": relpath(final_artifact, root),
        "target": relpath(target, root),
        "source_sha256": sha256_file(final_artifact),
        "target_sha256": sha256_file(target),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Regenerate Theorem III Track-B final lower-anchor artifact from theorem-facing construction steps.")
    p.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1), help="Worker count for heavy parallelizable stages.")
    p.add_argument(
        "--interval-workers",
        type=int,
        default=1,
        help=(
            "Worker count for lightweight Phase-5 interval diagnostic/backend stages. "
            "The default is serial because these stages have few tasks but large FFT arrays; "
            "using many processes can trigger process or memory limits on shared systems."
        ),
    )
    p.add_argument("--force", action="store_true", help="Pass --force to child stages that support it.")
    p.add_argument("--from-scratch", action="store_true", help="Remove theorem-facing Track-B output directories before regenerating.")
    p.add_argument("--dry-run", action="store_true", help="Print and log commands without executing them.")
    p.add_argument("--logs-dir", default=None, help="Directory for command logs. Default: artifacts/full_regeneration/<stamp>/logs/theorem_iii_trackb")
    p.add_argument("--manifest-out", default=None, help="Path for final regeneration manifest JSON.")
    p.add_argument("--copy-to-stage-cache", action="store_true", help="Copy Phase-6 final artifact to artifacts/final_discharge/stage_cache/theorem_iii.json.")
    p.add_argument("--theorem-i-artifact", default="artifacts/final_discharge/stage_cache/theorem_i_ii.json")
    p.add_argument("--theorem-ii-artifact", default="artifacts/final_discharge/stage_cache/theorem_i_ii.json")
    p.add_argument("--theorem-iv-artifact", default="artifacts/final_discharge/stage_cache/theorem_iv.json")
    p.add_argument("--phase1-continuation-steps", type=int, default=44, help="Continuation steps for the canonical Phase-1 K=0.971635, M=1024 seed.")
    p.add_argument("--skip-phase5a", action="store_true", help="Skip diagnostic Phase 5A. Phase 5C remains theorem-facing.")
    p.add_argument("--skip-phase5b", action="store_true", help="Skip diagnostic Phase 5B. Phase 5C remains theorem-facing.")
    p.add_argument("--stop-after", choices=[
        "phase1", "phase4f", "phase4i", "select-seed", "phase5a", "phase5b", "phase5c", "phase5d",
        "phase5f", "phase5fb", "phase5gb", "phase5h", "phase5i", "phase5j", "phase5k-backend",
        "phase5k-replay", "phase5e-final", "phase6", "install"
    ], default=None)
    return p


def maybe_force(args: argparse.Namespace) -> list[str]:
    return ["--force"] if args.force else []


def resolve_phase1_seed_npz(root: Path, phase1_dir: Path, expected_path: Path, *, dry_run: bool = False) -> Path:
    """Resolve the Phase-1 seed produced by the runner.

    Earlier development runs used different continuation-step counts, so the
    exact filename can differ even when the seed is mathematically the same
    anchor/resolution target.  The reconstruction pipeline should consume the
    file actually produced by Phase 1 rather than relying only on a stale
    hard-coded filename.
    """
    if dry_run:
        return expected_path
    if expected_path.exists():
        return expected_path

    summary_path = phase1_dir / "phase1_seed_summary.json"
    anchor_key = f"{K_ANCHOR:.10f}"
    candidates: list[Path] = []

    if summary_path.exists():
        try:
            summary = load_json(summary_path)
            best = (summary.get("best_by_anchor") or {}).get(anchor_key) or {}
            out = best.get("output_npz")
            if out:
                candidates.append(root / str(out))
            for row in summary.get("records", []) or []:
                cfg = row.get("config", {}) or {}
                if abs(float(cfg.get("K_target", float("nan"))) - K_ANCHOR) < 1e-12 and int(cfg.get("M", -1)) == 1024:
                    out = row.get("output_npz")
                    if out:
                        candidates.append(root / str(out))
        except Exception:
            pass

    candidates.extend(sorted((phase1_dir / "embeddings").glob("K0p9716350000_M1024_steps*.npz")))
    seen: set[Path] = set()
    existing: list[Path] = []
    for c in candidates:
        c = c.resolve()
        if c in seen:
            continue
        seen.add(c)
        if c.exists():
            existing.append(c)

    if existing:
        # Prefer the highest step count, then newest mtime.  This preserves the
        # canonical steps44 seed when present but still allows resumed runs that
        # created a steps40 seed to continue instead of failing on a filename.
        def score(p: Path) -> tuple[int, float]:
            name = p.name
            step = -1
            if "_steps" in name:
                try:
                    step = int(name.split("_steps", 1)[1].split(".", 1)[0])
                except Exception:
                    step = -1
            return (step, p.stat().st_mtime)
        chosen = sorted(existing, key=score)[-1]
        print(f"Resolved Phase-1 seed from produced outputs: {relpath(chosen, root)}", flush=True)
        return chosen

    available = sorted(str(p) for p in (phase1_dir / "embeddings").glob("*.npz"))
    raise FileNotFoundError(
        "Phase 1 completed, but the expected seed was not found. "
        f"Expected {relpath(expected_path, root)}. Available embeddings: {available}. "
        "Check phase1_seed_summary.json and phase1 logs."
    )


def resolve_summary_output_npz(root: Path, summary_path: Path, expected_path: Path, *, candidate_key: str = "top_candidates", dry_run: bool = False) -> Path:
    """Resolve a downstream NPZ from a stage summary, falling back to expected_path."""
    if dry_run or expected_path.exists():
        return expected_path
    if summary_path.exists():
        try:
            summary = load_json(summary_path)
            rows = summary.get(candidate_key) or summary.get("records") or []
            for row in rows:
                out = row.get("output_npz") if isinstance(row, dict) else None
                if out:
                    p = root / str(out)
                    if p.exists():
                        print(f"Resolved stage output from summary: {relpath(p, root)}", flush=True)
                        return p
        except Exception:
            pass
    raise FileNotFoundError(
        f"Expected stage output was not found: {relpath(expected_path, root)}. "
        f"Summary checked: {relpath(summary_path, root)}"
    )


def main() -> None:
    args = build_parser().parse_args()
    root = find_project_root()
    stamp = now_stamp()
    base = root / "artifacts" / "proof_audit" / "theorem_iii_trackb"
    logs_dir = Path(args.logs_dir) if args.logs_dir else root / "artifacts" / "full_regeneration" / stamp / "logs" / "theorem_iii_trackb"
    manifest_out = Path(args.manifest_out) if args.manifest_out else root / "artifacts" / "full_regeneration" / stamp / "theorem_iii_trackb_regeneration_manifest.json"
    runner = Runner(root, logs_dir, dry_run=args.dry_run)

    if args.from_scratch:
        clean_paths([
            base / "phase1_seed",
            base / "phase4f_lsq_polish_M4096_os2",
            base / "phase4i_h1_pilot_M4096seed",
            base / "phase4i_selected_seed",
            base / "phase5a_radii_prep_selected_seed",
            base / "phase5b_interval_components_selected_seed",
            base / "phase5c_interval_backend_selected_seed",
            base / "phase5d_certificate_scaffold_selected_seed",
            base / "phase5e_promotion_gate_selected_seed",
            base / "phase5f_formal_attachment_candidate",
            base / "phase5fb_hash_bound_attachment",
            base / "phase5gb_formal_components_corrected",
            base / "phase5h_formal_components",
            base / "phase5i_formal_components",
            base / "phase5j_formal_components",
            base / "phase5k_global_backend_candidate",
            base / "phase5k_independent_replay",
            base / "phase5k_phase5e_final_promotion",
            base / "phase6_final_integration",
            base / "phase6_final_replay",
        ], dry_run=args.dry_run)

    force = maybe_force(args)
    workers = str(max(1, int(args.workers)))
    interval_workers = str(max(1, int(args.interval_workers)))

    phase1_seed = base / "phase1_seed" / "embeddings" / f"K0p9716350000_M1024_steps{int(args.phase1_continuation_steps)}.npz"
    phase4f_seed = base / "phase4f_lsq_polish_M4096_os2" / "embeddings" / "K0p9716350000_M4096_lsqdealias2_full_fromM1024.npz"
    phase4i_summary = base / "phase4i_h1_pilot_M4096seed" / "phase4i_h1_polish_summary.json"
    selected_seed = base / "phase4i_selected_seed" / SELECTED_SEED_NAME
    phase5c_summary = base / "phase5c_interval_backend_selected_seed" / "phase5c_interval_backend_summary.json"
    phase5d_cert = base / "phase5d_certificate_scaffold_selected_seed" / "theorem_iii_trackb_phase5d_certificate_scaffold.json"
    phase5f_attach = base / "phase5f_formal_attachment_candidate" / "phase5f_formal_interval_attachment_CANDIDATE.json"
    phase5fb_attach = base / "phase5fb_hash_bound_attachment" / "phase5f_formal_interval_attachment_CANDIDATE_HASH_BOUND.json"
    phase5gb_attach = base / "phase5gb_formal_components_corrected" / "phase5g_formal_interval_attachment_COMPONENTS.json"
    phase5h_attach = base / "phase5h_formal_components" / "phase5h_formal_interval_attachment_COMPONENTS.json"
    phase5i_attach = base / "phase5i_formal_components" / "phase5i_formal_interval_attachment_COMPONENTS.json"
    phase5j_attach = base / "phase5j_formal_components" / "phase5j_formal_interval_attachment_COMPONENTS.json"
    phase5k_backend = base / "phase5k_global_backend_candidate" / "phase5k_global_backend_candidate.json"
    phase5k_attach_candidate = base / "phase5k_global_backend_candidate" / "phase5k_formal_interval_attachment_BACKEND_CANDIDATE.json"
    phase5k_promoted = base / "phase5k_independent_replay" / "phase5k_formal_interval_attachment_PROMOTED.json"
    phase5e_final_summary = base / "phase5k_phase5e_final_promotion" / "phase5e_promotion_gate_summary.json"
    phase6_final = base / "phase6_final_integration" / "theorem_iii_trackb_PHASE6_FINAL_LOWER_ANCHOR_CERTIFICATE.json"

    runner.run("phase1_seed", py(root,
        "scripts/audit/run_theorem_iii_trackb_phase1_seed.py",
        "--anchors", K_ANCHOR_STR,
        "--resolutions", "1024",
        "--workers", workers,
        "--continuation-steps", str(int(args.phase1_continuation_steps)),
        "--out-dir", relpath(base / "phase1_seed", root),
        *force,
    ))
    phase1_seed = resolve_phase1_seed_npz(root, base / "phase1_seed", phase1_seed, dry_run=args.dry_run)
    if args.stop_after == "phase1":
        return

    runner.run("phase4f_lsq_polish", py(root,
        "scripts/audit/run_theorem_iii_trackb_phase4f_lsq_polish.py",
        "--npz", relpath(phase1_seed, root),
        "--M-outs", "4096",
        "--oversamples", "2",
        "--cutoff-modes", "full",
        "--workers", workers,
        "--out-dir", relpath(base / "phase4f_lsq_polish_M4096_os2", root),
        *force,
    ))
    phase4f_seed = resolve_summary_output_npz(
        root,
        base / "phase4f_lsq_polish_M4096_os2" / "phase4f_lsq_polish_summary.json",
        phase4f_seed,
        dry_run=args.dry_run,
    )
    if args.stop_after == "phase4f":
        return

    runner.run("phase4i_h1_polish", py(root,
        "scripts/audit/run_theorem_iii_trackb_phase4i_h1_polish.py",
        "--npz", relpath(phase4f_seed, root),
        "--M-outs", "4096,8192",
        "--oversamples", "2",
        "--cutoffs", "full,frac:0.95",
        "--lambda-h1", "0.5,1.0,2.0,4.0",
        "--eta-high", "1e-8",
        "--workers", workers,
        "--out-dir", relpath(base / "phase4i_h1_pilot_M4096seed", root),
        *force,
    ))
    if args.stop_after == "phase4i":
        return

    selection_manifest = choose_and_copy_selected_h1_seed(root, phase4i_summary, selected_seed, dry_run=args.dry_run)
    if args.stop_after == "select-seed":
        return

    common_thresholds = [
        "--required-min-lower-anchor-k", str(K_ANCHOR),
        "--require-nu", str(REQUIRED_NU),
        "--require-radius", str(REQUIRED_RADIUS),
        "--require-cutoff", REQUIRED_CUTOFF,
        "--require-tail-start", str(REQUIRED_TAIL_START),
        "--min-relative-margin", str(MIN_RELATIVE_MARGIN),
        "--max-z", str(MAX_Z),
    ]

    if not args.skip_phase5a:
        runner.run("phase5a_radii_prep", py(root,
            "scripts/audit/run_theorem_iii_trackb_phase5a_radii_prep.py",
            "--npz", relpath(selected_seed, root),
            "--nu-grid", "1.001",
            "--cutoffs", "full,frac:0.95,frac:0.90",
            "--tail-start-fracs", "0.90,0.75",
            "--grid-factors", "4",
            "--radii", "1e-5,3e-5",
            "--workers", interval_workers,
            "--out-dir", relpath(base / "phase5a_radii_prep_selected_seed", root),
            *force,
        ))
    if args.stop_after == "phase5a":
        return

    if not args.skip_phase5b:
        runner.run("phase5b_interval_components", py(root,
            "scripts/audit/run_theorem_iii_trackb_phase5b_interval_components.py",
            "--npz", relpath(selected_seed, root),
            "--nu-grid", "1.001",
            "--cutoffs", "full,frac:0.95,frac:0.90",
            "--tail-start-fracs", "0.90,0.75",
            "--grid-factors", "4",
            "--radii", "1e-5,3e-5",
            "--workers", interval_workers,
            "--out-dir", relpath(base / "phase5b_interval_components_selected_seed", root),
            *force,
        ))
    if args.stop_after == "phase5b":
        return

    runner.run("phase5c_interval_backend", py(root,
        "scripts/audit/run_theorem_iii_trackb_phase5c_interval_backend.py",
        "--npz", relpath(selected_seed, root),
        "--nu-grid", "1.001",
        "--cutoffs", "full,frac:0.95,frac:0.90",
        "--tail-start-fracs", "0.90,0.75",
        "--grid-factors", "4",
        "--radii", "1e-5,3e-5",
        "--workers", interval_workers,
        "--out-dir", relpath(base / "phase5c_interval_backend_selected_seed", root),
        *force,
    ))
    if args.stop_after == "phase5c":
        return

    runner.run("phase5d_scaffold", py(root,
        "scripts/audit/assemble_theorem_iii_trackb_phase5d_certificate_scaffold.py",
        "--phase5c-summary", relpath(phase5c_summary, root),
        "--prefer-cutoff", REQUIRED_CUTOFF,
        "--prefer-tail-start", str(REQUIRED_TAIL_START),
        "--prefer-radius", str(REQUIRED_RADIUS),
        "--min-anchor-k", str(K_ANCHOR),
        "--min-relative-margin", str(MIN_RELATIVE_MARGIN),
        "--max-z", str(MAX_Z),
        "--out-dir", relpath(base / "phase5d_certificate_scaffold_selected_seed", root),
        *force,
    ))
    if args.stop_after == "phase5d":
        return

    runner.run("phase5f_formal_attachment", py(root,
        "scripts/audit/generate_theorem_iii_trackb_phase5f_formal_attachment.py",
        "--certificate", relpath(phase5d_cert, root),
        "--phase5c-summary", relpath(phase5c_summary, root),
        "--out-dir", relpath(base / "phase5f_formal_attachment_candidate", root),
        *common_thresholds,
        *force,
    ))
    if args.stop_after == "phase5f":
        return

    runner.run("phase5fb_hash_binding", py(root,
        "scripts/audit/bind_theorem_iii_trackb_phase5fb_certificate_hash.py",
        "--certificate", relpath(phase5d_cert, root),
        "--attachment", relpath(phase5f_attach, root),
        "--out-dir", relpath(base / "phase5fb_hash_bound_attachment", root),
        *force,
    ))
    if args.stop_after == "phase5fb":
        return

    runner.run("phase5gb_formal_components", py(root,
        "scripts/audit/generate_theorem_iii_trackb_phase5gb_formal_components.py",
        "--certificate", relpath(phase5d_cert, root),
        "--base-attachment", relpath(phase5fb_attach, root),
        "--seed-npz", relpath(selected_seed, root),
        "--phase5c-summary", relpath(phase5c_summary, root),
        "--out-dir", relpath(base / "phase5gb_formal_components_corrected", root),
        "--require-nu", str(REQUIRED_NU),
        "--require-radius", str(REQUIRED_RADIUS),
        "--require-cutoff", REQUIRED_CUTOFF,
        "--require-tail-start", str(REQUIRED_TAIL_START),
        *force,
    ))
    if args.stop_after == "phase5gb":
        return

    runner.run("phase5h_formal_components", py(root,
        "scripts/audit/generate_theorem_iii_trackb_phase5h_formal_components.py",
        "--certificate", relpath(phase5d_cert, root),
        "--base-attachment", relpath(phase5gb_attach, root),
        "--seed-npz", relpath(selected_seed, root),
        "--phase5c-summary", relpath(phase5c_summary, root),
        "--out-dir", relpath(base / "phase5h_formal_components", root),
        *common_thresholds,
        *force,
    ))
    if args.stop_after == "phase5h":
        return

    runner.run("phase5i_formal_components", py(root,
        "scripts/audit/generate_theorem_iii_trackb_phase5i_formal_components.py",
        "--certificate", relpath(phase5d_cert, root),
        "--base-attachment", relpath(phase5h_attach, root),
        "--phase5c-summary", relpath(phase5c_summary, root),
        "--out-dir", relpath(base / "phase5i_formal_components", root),
        *common_thresholds,
        *force,
    ))
    if args.stop_after == "phase5i":
        return

    runner.run("phase5j_formal_components", py(root,
        "scripts/audit/generate_theorem_iii_trackb_phase5j_formal_components.py",
        "--certificate", relpath(phase5d_cert, root),
        "--base-attachment", relpath(phase5i_attach, root),
        "--out-dir", relpath(base / "phase5j_formal_components", root),
        *common_thresholds,
        *force,
    ))
    if args.stop_after == "phase5j":
        return

    runner.run("phase5k_global_backend", py(root,
        "scripts/audit/generate_theorem_iii_trackb_phase5k_global_backend.py",
        "--certificate", relpath(phase5d_cert, root),
        "--base-attachment", relpath(phase5j_attach, root),
        "--out-dir", relpath(base / "phase5k_global_backend_candidate", root),
        *common_thresholds,
        *force,
    ))
    if args.stop_after == "phase5k-backend":
        return

    runner.run("phase5k_independent_replay", py(root,
        "scripts/audit/run_theorem_iii_trackb_phase5k_independent_replay.py",
        "--certificate", relpath(phase5d_cert, root),
        "--backend-candidate", relpath(phase5k_backend, root),
        "--attachment-candidate", relpath(phase5k_attach_candidate, root),
        "--out-dir", relpath(base / "phase5k_independent_replay", root),
        *common_thresholds,
        *force,
    ))
    if args.stop_after == "phase5k-replay":
        return

    runner.run("phase5e_final_promotion", py(root,
        "scripts/audit/run_theorem_iii_trackb_phase5e_promotion_gate.py",
        "--certificate", relpath(phase5d_cert, root),
        "--formal-attachment", relpath(phase5k_promoted, root),
        "--out-dir", relpath(base / "phase5k_phase5e_final_promotion", root),
        "--no-template",
        *common_thresholds,
        *force,
    ))
    if args.stop_after == "phase5e-final":
        return

    phase6_cmd = py(root,
        "scripts/audit/assemble_theorem_iii_trackb_phase6_final_integration.py",
        "--certificate", relpath(phase5d_cert, root),
        "--promoted-attachment", relpath(phase5k_promoted, root),
        "--phase5e-summary", relpath(phase5e_final_summary, root),
        "--required-min-lower-anchor-k", str(K_ANCHOR),
        "--require-nu", str(REQUIRED_NU),
        "--require-radius", str(REQUIRED_RADIUS),
        "--require-cutoff", REQUIRED_CUTOFF,
        "--require-tail-start", str(REQUIRED_TAIL_START),
        "--min-relative-margin", str(MIN_RELATIVE_MARGIN),
        "--max-z", str(MAX_Z),
        "--out-dir", relpath(base / "phase6_final_integration", root),
        *force,
    )
    for flag, raw in [
        ("--theorem-i-artifact", args.theorem_i_artifact),
        ("--theorem-ii-artifact", args.theorem_ii_artifact),
        ("--theorem-iv-artifact", args.theorem_iv_artifact),
    ]:
        path = root / raw
        if path.exists() or args.dry_run:
            phase6_cmd.extend([flag, raw])
    runner.run("phase6_final_integration", phase6_cmd)
    if args.stop_after == "phase6":
        return

    runner.run("phase6_final_replay", py(root,
        "scripts/audit/run_theorem_iii_trackb_phase6_final_replay.py",
        "--final-artifact", relpath(phase6_final, root),
        "--required-min-lower-anchor-k", str(K_ANCHOR),
        "--require-nu", str(REQUIRED_NU),
        "--require-radius", str(REQUIRED_RADIUS),
        "--require-cutoff", REQUIRED_CUTOFF,
        "--require-tail-start", str(REQUIRED_TAIL_START),
        "--min-relative-margin", str(MIN_RELATIVE_MARGIN),
        "--max-z", str(MAX_Z),
        "--out-dir", relpath(base / "phase6_final_replay", root),
        *force,
    ))

    install_manifest = None
    if args.copy_to_stage_cache:
        install_manifest = copy_to_stage_cache(root, phase6_final, dry_run=args.dry_run)
        dump_json(root / "artifacts" / "final_discharge" / "stage_cache" / "theorem_iii_install_manifest.json", install_manifest)
    if args.stop_after == "install":
        return

    final_paths = [
        selected_seed,
        phase5d_cert,
        phase5k_promoted,
        phase5e_final_summary,
        phase6_final,
        root / "artifacts" / "proof_audit" / "theorem_iii_trackb" / "phase6_final_replay" / "phase6_final_replay_summary.json",
    ]
    manifest = {
        "schema": "theorem_iii_trackb_from_scratch_regeneration_manifest_v1",
        "status": "ok",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "parameters": {
            "workers": args.workers,
            "interval_workers": args.interval_workers,
            "force": args.force,
            "from_scratch": args.from_scratch,
            "K_anchor": K_ANCHOR,
            "required_nu": REQUIRED_NU,
            "required_radius": REQUIRED_RADIUS,
            "required_cutoff": REQUIRED_CUTOFF,
            "required_tail_start": REQUIRED_TAIL_START,
        },
        "selected_seed_manifest": selection_manifest,
        "stage_cache_install": install_manifest,
        "commands": [r.to_dict() for r in runner.results],
        "final_artifacts": [
            {
                "path": relpath(p, root),
                "exists": p.exists(),
                "sha256": sha256_file(p) if p.exists() and p.is_file() else None,
            }
            for p in final_paths
        ],
    }
    dump_json(manifest_out, manifest)
    print(f"\nTheorem III Track-B regeneration manifest: {relpath(manifest_out, root)}")
    print(f"Final Theorem III artifact: {relpath(phase6_final, root)}")


if __name__ == "__main__":
    main()
