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
    generate_anchor_windows,
    load_json,
    write_json,
)

ART_ROOT = Path("artifacts/proof_audit/lower_corridor/phase2x_anchor")
TAB_ROOT = Path("tables/proof_audit/lower_corridor/phase2x_anchor")
REPLAY_ROOT = Path("artifacts/proof_audit/replay")
PHASE2N_ROOT = Path("artifacts/proof_audit/lower_corridor/phase2n_probes")

PROFILES = {
    "anchor": {
        "radius_multipliers": "0.9,0.95,1.0,1.04,1.08,1.12,1.16,1.2,1.25,1.3",
        "phase2o_sigma_values": "0.0000001,0.00000025,0.0000005,0.000001",
        "phase2p_sigma_values": "0.0000001,0.00000025,0.0000005,0.000001",
        "tail_cutoffs": "1024,1536,2048",
        "tail_band_fractions": "0.65,0.85",
        "tail_safety_factors": "2,4",
    },
    "anchor1536": {
        "radius_multipliers": "0.95,1.0,1.04,1.08,1.12,1.16,1.2,1.25",
        "phase2o_sigma_values": "0.0000001",
        "phase2p_sigma_values": "0.0000001",
        "tail_cutoffs": "1536",
        "tail_band_fractions": "0.65",
        "tail_safety_factors": "2",
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


def selected(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        d = load_json(path)
    except Exception:
        return {"path": str(path), "read_error": True}
    row = d.get("selected_phase2p_row") or {}
    seg = (d.get("anchor_segments") or [{}])[0]
    return {
        "path": str(path), "K_lo": seg.get("K_lo"), "K_hi": seg.get("K_hi"),
        "theorem_facing": d.get("theorem_facing"), "promotion_allowed": d.get("promotion_allowed"),
        "failure_fields": d.get("failure_fields"), "theorem_ready": row.get("theorem_ready"),
        "radii_margin": row.get("radii_margin"), "tail_T": row.get("tail_T"),
        "allowable_tail_max": row.get("allowable_tail_max"), "finite_contraction_q": row.get("finite_contraction_q"),
        "model_name": row.get("model_name"), "failure_reasons": row.get("failure_reasons"),
    }


def paths_for(label: str, seg_id: str) -> dict[str, Path]:
    base = ART_ROOT / label
    tables = TAB_ROOT / label
    replay = REPLAY_ROOT / f"phase2x_anchor_{label}"
    return {
        "base": base, "tables": tables, "replay": replay,
        "phase2o": base / "phase2o", "phase2p": base / "phase2p", "ready": base / "ready",
        "phase2o_tables": tables / "phase2o", "phase2p_tables": tables / "phase2p",
        "log": replay / f"{seg_id}.log",
        "phase2n_summary": PHASE2N_ROOT / f"{seg_id}_phase2n_batch_summary.json",
        "phase2o_out": base / "phase2o" / f"{seg_id}_tail_radius_scan.json",
        "phase2o_csv": tables / "phase2o" / f"{seg_id}_tail_radius_scan.csv",
        "phase2o_candidate": base / "phase2o" / f"{seg_id}_tail_radius_candidate.json",
        "phase2p_out": base / "phase2p" / f"{seg_id}_modewise_tail_scan.json",
        "phase2p_csv": tables / "phase2p" / f"{seg_id}_modewise_tail_scan.csv",
        "phase2p_candidate": base / "phase2p" / f"{seg_id}_modewise_tail_candidate.json",
        "ready_candidate": base / "ready" / f"{seg_id}_THEOREM_READY_candidate.json",
    }


def ensure_dirs(paths: dict[str, Path]) -> None:
    for k in ["base", "tables", "replay", "phase2o", "phase2p", "ready", "phase2o_tables", "phase2p_tables"]:
        paths[k].mkdir(parents=True, exist_ok=True)


def run_anchor(task: dict[str, Any]) -> dict[str, Any]:
    a = task["anchor"]
    args = task["args"]
    profile = PROFILES[args.profile]
    seg_id = a["segment_id"]
    paths = paths_for(args.label, seg_id)
    ensure_dirs(paths)
    if is_ready(paths["ready_candidate"]) and not args.force:
        return {"index": a["index"], "closed": True, "status": "cached-ready", "ready_candidate": str(paths["ready_candidate"]), "selected": selected(paths["ready_candidate"]), **a}
    py = sys.executable
    phase2n = [py, "scripts/audit/run_lower_anchor_phase2n_batch.py", "--segment-id", seg_id, "--K-lo", a["K_lo"], "--K-hi", a["K_hi"], "--K-mid", a["K_mid"], "--N-values", args.n_values, "--oversample-factors", "16", "--sigma-caps", "0.0001", "--timeout-seconds", str(args.phase2n_timeout), "--skip-existing", "--seed-json", args.seed_json]
    phase2o = [py, "scripts/audit/run_lower_anchor_phase2o_radius_tail_scan.py", "--input", str(paths["phase2n_summary"]), "--out", str(paths["phase2o_out"]), "--csv", str(paths["phase2o_csv"]), "--candidate-out", str(paths["phase2o_candidate"]), "--radius-multipliers", args.radius_multipliers or profile["radius_multipliers"], "--sigma-values", profile["phase2o_sigma_values"], "--tail-band-fractions", profile["tail_band_fractions"], "--tail-safety-factors", profile["tail_safety_factors"]]
    phase2p = [py, "scripts/audit/run_lower_anchor_phase2p_modewise_tail_scan.py", "--input", str(paths["phase2o_candidate"]), "--out", str(paths["phase2p_out"]), "--csv", str(paths["phase2p_csv"]), "--candidate-out", str(paths["phase2p_candidate"]), "--sigma-values", profile["phase2p_sigma_values"], "--tail-cutoffs", profile["tail_cutoffs"], "--oversample-factors", "16"]
    if args.force:
        for p in [paths["phase2o_out"], paths["phase2o_csv"], paths["phase2o_candidate"], paths["phase2p_out"], paths["phase2p_csv"], paths["phase2p_candidate"], paths["ready_candidate"]]:
            try: p.unlink()
            except FileNotFoundError: pass
    results = []
    for phase, cmd, timeout in [("phase2n", phase2n, args.phase2n_timeout+30), ("phase2o", phase2o, args.phase2o_timeout), ("phase2p", phase2p, args.phase2p_timeout)]:
        r = run_cmd(cmd, paths["log"], timeout, dry_run=args.dry_run)
        r["phase"] = phase
        results.append(r)
        if r.get("returncode") != 0:
            break
    closed = is_ready(paths["phase2p_candidate"])
    if closed and not args.dry_run:
        shutil.copyfile(paths["phase2p_candidate"], paths["ready_candidate"])
    return {"index": a["index"], "closed": bool(closed), "status": "closed" if closed else "not-closed", "ready_candidate": str(paths["ready_candidate"]), "phase2p_candidate": str(paths["phase2p_candidate"]), "selected": selected(paths["phase2p_candidate"]), "run_results": results, **a}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Phase 2X anchor-and-openness fallback runner.")
    p.add_argument("--label", required=True)
    p.add_argument("--K-lo", required=True)
    p.add_argument("--K-hi", required=True)
    p.add_argument("--seed-json", required=True)
    p.add_argument("--anchor-count", type=int, default=128)
    p.add_argument("--half-width", default="0.00000045", help="Half-width around each anchor; use enough overlap for coverage.")
    p.add_argument("--workers", type=int, default=16)
    p.add_argument("--profile", choices=sorted(PROFILES), default="anchor1536")
    p.add_argument("--n-values", default="1024")
    p.add_argument("--radius-multipliers", default=None)
    p.add_argument("--anchor-start", type=int, default=0)
    p.add_argument("--anchor-stop", type=int, default=None)
    p.add_argument("--phase2n-timeout", type=float, default=1200.0)
    p.add_argument("--phase2o-timeout", type=float, default=600.0)
    p.add_argument("--phase2p-timeout", type=float, default=900.0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--out", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    anchors = generate_anchor_windows(args.K_lo, args.K_hi, args.anchor_count, args.half_width, args.label)
    stop = args.anchor_stop if args.anchor_stop is not None else len(anchors)
    selected_anchors = anchors[max(0,args.anchor_start):min(stop, len(anchors))]
    print("="*80)
    print(f"Phase 2X anchor openness: {args.label}")
    print(f"target interval: [{args.K_lo}, {args.K_hi}], anchors={args.anchor_count}, selected={len(selected_anchors)}, workers={args.workers}")
    print("="*80)
    tasks = [{"anchor": a, "args": args} for a in selected_anchors]
    results = []
    if args.dry_run or args.workers <= 1:
        for t in tasks:
            results.append(run_anchor(t))
    else:
        with cf.ThreadPoolExecutor(max_workers=max(1,int(args.workers))) as ex:
            futs = [ex.submit(run_anchor, t) for t in tasks]
            for fut in cf.as_completed(futs):
                results.append(fut.result())
                r = results[-1]
                print(f"[{r.get('status')}] anchor={r.get('index')} margin={r.get('selected',{}).get('radii_margin')} q={r.get('selected',{}).get('finite_contraction_q')}", flush=True)
    closed = [r for r in results if r.get("closed")]
    failed = [r for r in results if not r.get("closed")]
    failed.sort(key=lambda r: (r.get("selected",{}).get("radii_margin") if isinstance(r.get("selected",{}).get("radii_margin"), (int,float)) else -1e99), reverse=True)
    report = {"schema":"phase2x_anchor_openness_report_v1", "status":"phase2x-anchor-complete" if not failed and results else "phase2x-anchor-incomplete", "label":args.label, "K_lo":args.K_lo, "K_hi":args.K_hi, "anchor_count":args.anchor_count, "selected_count":len(selected_anchors), "closed_count":len(closed), "pending_count":len(failed), "ready_candidates":[r.get("ready_candidate") for r in closed], "best_failed_rows":[r.get("selected",{}) for r in failed[:20]], "results":results}
    out = Path(args.out) if args.out else ART_ROOT / args.label / f"phase2x_{args.label}_anchor_openness_summary.json"
    write_json(out, report)
    print("\nPhase 2X anchor run complete.")
    print(json.dumps({"status":report["status"], "closed_count":report["closed_count"], "pending_count":report["pending_count"], "summary_path":str(out)}, indent=2))
    return 0 if report["closed_count"] > 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
