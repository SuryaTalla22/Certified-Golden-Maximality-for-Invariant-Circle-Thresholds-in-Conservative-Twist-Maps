#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from kam_theorem_suite.audit.lower_anchor_phase2x_weighted_finite import (
    THREAD_LIMIT_ENV,
    autopsy_records,
    infer_bounds_for_record,
    load_json,
    phase2x_piece_label,
    records_from_summary,
    select_top_records,
    write_json,
)

ART_ROOT = Path("artifacts/proof_audit/lower_corridor/phase2x_weighted")
TAB_ROOT = Path("tables/proof_audit/lower_corridor/phase2x_weighted")
REPLAY_ROOT = Path("artifacts/proof_audit/replay")
PHASE2N_ROOT = Path("artifacts/proof_audit/lower_corridor/phase2n_probes")

PROFILES = {
    # Fast first-line rescue: top pieces, N=1024, narrow sigma/cutoff, finer radius shells.
    "weighted": {
        "n_values": "1024",
        "radius_multipliers": "0.92,0.95,0.98,1.0,1.02,1.04,1.06,1.08,1.1,1.12,1.14,1.16,1.18,1.2,1.22,1.25,1.3,1.35",
        "phase2o_sigma_values": "0.0000001,0.00000025,0.0000005,0.000001",
        "phase2p_sigma_values": "0.0000001,0.00000025,0.0000005,0.000001",
        "tail_cutoffs": "1024,1536,2048",
        "tail_band_fractions": "0.65,0.85",
        "tail_safety_factors": "2,4",
        "phase2p_timeout": 900.0,
    },
    # N-lift rescue: real recomputation of finite certificate at slightly larger N.
    "nlift1536": {
        "n_values": "1536",
        "radius_multipliers": "0.9,0.95,1.0,1.04,1.08,1.12,1.16,1.2,1.25,1.3,1.4",
        "phase2o_sigma_values": "0.0000001,0.00000025,0.0000005,0.000001",
        "phase2p_sigma_values": "0.0000001,0.00000025,0.0000005,0.000001",
        "tail_cutoffs": "1024,1536,2048,3072",
        "tail_band_fractions": "0.65,0.85",
        "tail_safety_factors": "2,4",
        "phase2p_timeout": 1200.0,
    },
    # Expensive but focused. Use only top 5-10 pieces.
    "nlift2048": {
        "n_values": "2048",
        "radius_multipliers": "0.9,0.95,1.0,1.04,1.08,1.12,1.16,1.2,1.25,1.3",
        "phase2o_sigma_values": "0.0000001,0.00000025,0.0000005",
        "phase2p_sigma_values": "0.0000001,0.00000025,0.0000005",
        "tail_cutoffs": "1536,2048,3072",
        "tail_band_fractions": "0.65",
        "tail_safety_factors": "2,4",
        "phase2p_timeout": 1800.0,
    },
    # Very small P grid to avoid timeouts when the best rows are known.
    "pinpoint": {
        "n_values": "1024",
        "radius_multipliers": "1.0,1.04,1.06,1.08,1.1,1.12,1.14,1.16,1.18,1.2,1.22,1.25",
        "phase2o_sigma_values": "0.0000001",
        "phase2p_sigma_values": "0.0000001",
        "tail_cutoffs": "1536",
        "tail_band_fractions": "0.65",
        "tail_safety_factors": "2",
        "phase2p_timeout": 600.0,
    },
}


def env_for_subprocess() -> dict[str, str]:
    env = os.environ.copy()
    env.update(THREAD_LIMIT_ENV)
    return env


def run_cmd(cmd: list[str], log_path: Path, timeout: float | None, dry_run: bool = False) -> dict[str, Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        with log_path.open("a") as f:
            f.write("\n[dry-run] $ " + " ".join(cmd) + "\n")
        return {"returncode": 0, "timed_out": False, "elapsed_seconds": 0.0, "cmd": cmd, "dry_run": True}
    started = time.time()
    with log_path.open("a") as f:
        f.write("\n$ " + " ".join(cmd) + "\n")
        f.flush()
        try:
            proc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env_for_subprocess(), timeout=timeout, text=True)
            return {"returncode": proc.returncode, "timed_out": False, "elapsed_seconds": time.time() - started, "cmd": cmd}
        except subprocess.TimeoutExpired:
            f.write(f"\n[TIMEOUT after {timeout} seconds]\n")
            return {"returncode": 124, "timed_out": True, "elapsed_seconds": time.time() - started, "cmd": cmd}


def is_ready(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        d = load_json(path)
    except Exception:
        return False
    row = d.get("selected_phase2p_row") or {}
    return bool(d.get("theorem_facing") is True and d.get("promotion_allowed") is True and not d.get("failure_fields") and row.get("theorem_ready") is True and not row.get("failure_reasons"))


def selected_from_candidate(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        d = load_json(path)
    except Exception as e:
        return {"read_error": str(e), "path": str(path)}
    row = d.get("selected_phase2p_row") or {}
    seg = (d.get("anchor_segments") or [{}])[0]
    return {
        "path": str(path),
        "theorem_facing": d.get("theorem_facing"),
        "promotion_allowed": d.get("promotion_allowed"),
        "closure_level": d.get("closure_level"),
        "failure_fields": d.get("failure_fields"),
        "K_lo": seg.get("K_lo"),
        "K_hi": seg.get("K_hi"),
        "theorem_ready": row.get("theorem_ready"),
        "model_name": row.get("model_name"),
        "sigma": row.get("sigma"),
        "radius_r": row.get("radius_r"),
        "finite_contraction_q": row.get("finite_contraction_q"),
        "tail_cutoff": row.get("tail_cutoff"),
        "radii_margin": row.get("radii_margin"),
        "tail_T": row.get("tail_T"),
        "allowable_tail_max": row.get("allowable_tail_max"),
        "tail_response_bound": row.get("tail_response_bound"),
        "nonlinear_guard": row.get("nonlinear_guard"),
        "failure_reasons": row.get("failure_reasons"),
    }



def parse_index_csv(raw: str | None) -> set[int]:
    if raw is None:
        return set()
    out: set[int] = set()
    for part in str(raw).split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            lo, hi = part.split('-', 1)
            try:
                a, b = int(lo), int(hi)
            except ValueError:
                raise ValueError(f"invalid index range: {part!r}")
            if b < a:
                a, b = b, a
            out.update(range(a, b + 1))
        else:
            try:
                out.add(int(part))
            except ValueError:
                raise ValueError(f"invalid index: {part!r}")
    return out

def paths_for(label: str, segment_id: str) -> dict[str, Path]:
    base = ART_ROOT / label
    tables = TAB_ROOT / label
    replay = REPLAY_ROOT / f"phase2x_{label}"
    return {
        "base": base, "tables": tables, "replay": replay,
        "phase2o": base / "phase2o", "phase2p": base / "phase2p", "ready": base / "ready",
        "phase2o_tables": tables / "phase2o", "phase2p_tables": tables / "phase2p",
        "log": replay / f"{segment_id}.log",
        "phase2n_summary": PHASE2N_ROOT / f"{segment_id}_phase2n_batch_summary.json",
        "phase2n_attempt": PHASE2N_ROOT / f"{segment_id}_N1024_os16_sg0p0001.json",
        "phase2o_out": base / "phase2o" / f"{segment_id}_tail_radius_scan.json",
        "phase2o_csv": tables / "phase2o" / f"{segment_id}_tail_radius_scan.csv",
        "phase2o_candidate": base / "phase2o" / f"{segment_id}_tail_radius_candidate.json",
        "phase2p_out": base / "phase2p" / f"{segment_id}_modewise_tail_scan.json",
        "phase2p_csv": tables / "phase2p" / f"{segment_id}_modewise_tail_scan.csv",
        "phase2p_candidate": base / "phase2p" / f"{segment_id}_modewise_tail_candidate.json",
        "ready_candidate": base / "ready" / f"{segment_id}_THEOREM_READY_candidate.json",
    }


def ensure_dirs(paths: dict[str, Path]) -> None:
    for k in ["base", "tables", "replay", "phase2o", "phase2p", "ready", "phase2o_tables", "phase2p_tables"]:
        paths[k].mkdir(parents=True, exist_ok=True)


def run_record(task: dict[str, Any]) -> dict[str, Any]:
    rec = task["record"]
    args = task["args"]
    profile = task["profile"]
    K_lo, K_hi, K_mid = infer_bounds_for_record(rec)
    stem = phase2x_piece_label(args.label, rec.index, suffix="_" + args.profile)
    segment_id = f"phase2x_{stem}"
    paths = paths_for(args.label, segment_id)
    ensure_dirs(paths)
    if is_ready(paths["ready_candidate"]) and not args.force:
        return {"closed": True, "status": "cached-ready", "index": rec.index, "ready_candidate": str(paths["ready_candidate"]), "selected": selected_from_candidate(paths["ready_candidate"])}
    py = sys.executable
    n_values = args.n_values or profile["n_values"]
    phase2n = [
        py, "scripts/audit/run_lower_anchor_phase2n_batch.py",
        "--segment-id", segment_id,
        "--K-lo", K_lo, "--K-hi", K_hi, "--K-mid", K_mid,
        "--N-values", n_values,
        "--oversample-factors", "16",
        "--sigma-caps", "0.0001",
        "--timeout-seconds", str(args.phase2n_timeout),
        "--skip-existing",
        "--seed-json", args.seed_json,
    ]
    if args.force:
        # Existing batch scripts generally use --skip-existing rather than --force;
        # stale downstream artifacts are removed below.
        pass
    phase2o = [
        py, "scripts/audit/run_lower_anchor_phase2o_radius_tail_scan.py",
        "--input", str(paths["phase2n_summary"]),
        "--out", str(paths["phase2o_out"]),
        "--csv", str(paths["phase2o_csv"]),
        "--candidate-out", str(paths["phase2o_candidate"]),
        "--radius-multipliers", args.radius_multipliers or profile["radius_multipliers"],
        "--sigma-values", args.phase2o_sigma_values or profile["phase2o_sigma_values"],
        "--tail-band-fractions", profile["tail_band_fractions"],
        "--tail-safety-factors", profile["tail_safety_factors"],
    ]
    phase2p = [
        py, "scripts/audit/run_lower_anchor_phase2p_modewise_tail_scan.py",
        "--input", str(paths["phase2o_candidate"]),
        "--out", str(paths["phase2p_out"]),
        "--csv", str(paths["phase2p_csv"]),
        "--candidate-out", str(paths["phase2p_candidate"]),
        "--sigma-values", args.phase2p_sigma_values or profile["phase2p_sigma_values"],
        "--tail-cutoffs", args.tail_cutoffs or profile["tail_cutoffs"],
        "--oversample-factors", "16",
    ]
    if args.force:
        for p in [paths["phase2o_out"], paths["phase2o_csv"], paths["phase2o_candidate"], paths["phase2p_out"], paths["phase2p_csv"], paths["phase2p_candidate"], paths["ready_candidate"]]:
            try:
                p.unlink()
            except FileNotFoundError:
                pass
    results = []
    for phase, cmd, timeout in [
        ("phase2n", phase2n, args.phase2n_timeout + 30.0),
        ("phase2o", phase2o, args.phase2o_timeout),
        ("phase2p", phase2p, args.phase2p_timeout or profile["phase2p_timeout"]),
    ]:
        r = run_cmd(cmd, paths["log"], timeout, dry_run=args.dry_run)
        r["phase"] = phase
        results.append(r)
        if r.get("returncode") != 0:
            break
    closed = is_ready(paths["phase2p_candidate"])
    if closed and not args.dry_run:
        shutil.copyfile(paths["phase2p_candidate"], paths["ready_candidate"])
    return {
        "index": rec.index,
        "label": rec.label,
        "segment_id": segment_id,
        "K_lo": K_lo,
        "K_hi": K_hi,
        "K_mid": K_mid,
        "closed": bool(closed),
        "status": "closed" if closed else "not-closed",
        "run_results": results,
        "phase2p_candidate": str(paths["phase2p_candidate"]),
        "ready_candidate": str(paths["ready_candidate"]),
        "selected": selected_from_candidate(paths["phase2p_candidate"]),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Phase 2X targeted weighted/n-lift finite rescue for top failed microsegments.")
    p.add_argument("--summary", required=True, help="Phase 2U/2V run summary JSON.")
    p.add_argument("--label", required=True, help="Output label for this rescue batch.")
    p.add_argument("--seed-json", required=True, help="Seed Phase 2N JSON.")
    p.add_argument("--top-k", type=int, default=20)
    p.add_argument("--indices", default=None, help="Comma-separated explicit Phase-2V piece indices/ranges to run, e.g. 5,11,133 or 120-150. If set, this filter is applied before --top-k.")
    p.add_argument("--buckets", default="safe_q_small_gap,near_q_small_gap,q_boundary_near_miss,tail_or_guard_dominated", help="Comma-separated autopsy buckets to include, or empty for all.")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--profile", choices=sorted(PROFILES), default="weighted")
    p.add_argument("--n-values", default=None, help="Override N-values for Phase 2N, e.g. 1536 or 1536,2048.")
    p.add_argument("--radius-multipliers", default=None)
    p.add_argument("--phase2o-sigma-values", default=None)
    p.add_argument("--phase2p-sigma-values", default=None)
    p.add_argument("--tail-cutoffs", default=None)
    p.add_argument("--phase2n-timeout", type=float, default=1200.0)
    p.add_argument("--phase2o-timeout", type=float, default=900.0)
    p.add_argument("--phase2p-timeout", type=float, default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--out", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    profile = PROFILES[args.profile]
    records = records_from_summary(args.summary)
    rows = autopsy_records(records)
    explicit_indices = parse_index_csv(args.indices)
    if explicit_indices:
        rows = [row for row in rows if row.record.index in explicit_indices]
    buckets = [x.strip() for x in args.buckets.split(",") if x.strip()] if args.buckets else []
    selected_rows = select_top_records(rows, args.top_k, buckets=buckets)
    selected_records = [r.record for r in selected_rows]
    print("=" * 80)
    print(f"Phase 2X weighted finite rescue: {args.label}")
    print(f"summary: {args.summary}")
    print(f"selected records: {len(selected_records)}; workers: {args.workers}; profile: {args.profile}")
    print("=" * 80)
    tasks = [{"record": r, "args": args, "profile": profile} for r in selected_records]
    results = []
    if args.dry_run or args.workers <= 1:
        for t in tasks:
            results.append(run_record(t))
    else:
        with cf.ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as ex:
            futs = [ex.submit(run_record, t) for t in tasks]
            for fut in cf.as_completed(futs):
                results.append(fut.result())
                r = results[-1]
                sel = r.get("selected", {})
                print(f"[{r.get('status')}] index={r.get('index')} margin={sel.get('radii_margin')} q={sel.get('finite_contraction_q')} model={sel.get('model_name')}", flush=True)
    closed = [r for r in results if r.get("closed")]
    failed = [r for r in results if not r.get("closed")]
    failed.sort(key=lambda r: (r.get("selected", {}).get("radii_margin") if isinstance(r.get("selected", {}).get("radii_margin"), (int, float)) else -1e99), reverse=True)
    report = {
        "schema": "phase2x_weighted_rescue_report_v1",
        "status": "phase2x-complete" if not failed and results else "phase2x-incomplete",
        "summary": args.summary,
        "label": args.label,
        "profile": args.profile,
        "top_k": args.top_k,
        "indices": sorted(explicit_indices),
        "selected_count": len(selected_records),
        "result_count": len(results),
        "closed_count": len(closed),
        "pending_count": len(failed),
        "ready_candidates": [r.get("ready_candidate") for r in closed],
        "best_failed_rows": [r.get("selected", {}) for r in failed[:20]],
        "results": results,
    }
    out = Path(args.out) if args.out else ART_ROOT / args.label / f"phase2x_{args.label}_run_summary.json"
    write_json(out, report)
    print("\nPhase 2X complete.")
    print(json.dumps({"status": report["status"], "closed_count": report["closed_count"], "pending_count": report["pending_count"], "summary_path": str(out)}, indent=2))
    return 0 if report["closed_count"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
