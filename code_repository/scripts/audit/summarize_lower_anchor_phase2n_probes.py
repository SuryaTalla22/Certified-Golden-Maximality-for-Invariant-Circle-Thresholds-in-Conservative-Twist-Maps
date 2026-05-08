#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2n import atomic_write_json, summarize_attempts, build_phase2e_candidate_from_best_attempt


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except Exception:
        return str(p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize Phase-2N probe JSON files and emit best-by-Phase2E-margin tables.")
    parser.add_argument("--glob", default="artifacts/proof_audit/lower_corridor/phase2n_probes/*.json")
    parser.add_argument("--out", default="artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_summary.json")
    parser.add_argument("--csv", default="tables/proof_audit/lower_corridor/phase2n_probes/phase2n_summary.csv")
    parser.add_argument("--candidate-out", default="artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_best_single_segment_candidate.json")
    args = parser.parse_args(argv)

    paths = sorted(ROOT.glob(args.glob) if not Path(args.glob).is_absolute() else Path("/").glob(str(Path(args.glob).relative_to('/'))))
    attempts = []
    for p in paths:
        if p.name.endswith(".started.json") or "summary" in p.name or "candidate" in p.name:
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if isinstance(d, dict) and d.get("schema") == "phase2n_single_N_attempt_v1":
            d["_path"] = _rel(p)
            attempts.append(d)
    summary = summarize_attempts(attempts)
    out = _resolve(args.out); csv_path = _resolve(args.csv); cand = _resolve(args.candidate_out)
    out.parent.mkdir(parents=True, exist_ok=True); csv_path.parent.mkdir(parents=True, exist_ok=True); cand.parent.mkdir(parents=True, exist_ok=True)
    best = summary.get("best")
    if best and best.get("path"):
        bp = ROOT / best["path"] if not Path(best["path"]).is_absolute() else Path(best["path"])
        best_attempt = json.loads(bp.read_text())
        candidate = build_phase2e_candidate_from_best_attempt(best_attempt, source_artifact=_rel(cand))
        atomic_write_json(cand, candidate)
        summary["best_candidate_path"] = _rel(cand)
    atomic_write_json(out, summary)
    fields = ["path", "status", "segment_id", "K_mid", "N", "oversample_factor", "sigma_cap", "sigma_used", "theorem_ready", "radii_margin", "residual_Y", "linear_Z", "radius_r", "tail_T", "finite_radii_margin", "source_theorem_margin", "elapsed_seconds", "failure_reasons"]
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in summary.get("rows", []):
            rr = dict(row)
            rr["failure_reasons"] = ";".join(str(x) for x in rr.get("failure_reasons", []) or [])
            writer.writerow({k: rr.get(k) for k in fields})
    print(json.dumps({"summary_path": _rel(out), "csv_path": _rel(csv_path), "best_candidate_path": _rel(cand) if cand.exists() else None, "best": summary.get("best")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
