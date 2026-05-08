#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"missing": str(p)}
    return json.loads(p.read_text())


def tail(path: str | Path, n: int = 80) -> str:
    p = Path(path)
    if not p.exists():
        return f"MISSING: {p}"
    lines = p.read_text(errors="replace").splitlines()
    return "\n".join(lines[-n:])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fast targeted Phase 2Y report printer; avoids recursive artifact scans.")
    p.add_argument("--phase2v-summary", default="artifacts/proof_audit/lower_corridor/phase2v_micro/collar_012b1_v256/phase2v_collar_012b1_v256_run_summary.json")
    p.add_argument("--autopsy", default="artifacts/proof_audit/lower_corridor/pass1_012b1/phase2x_collar_012b1_autopsy.json")
    p.add_argument("--weighted-summary", default="artifacts/proof_audit/lower_corridor/phase2x_weighted/collar_012b1_phase2x_weighted_top64/phase2x_collar_012b1_phase2x_weighted_top64_run_summary.json")
    p.add_argument("--nlift1536-summary", default="artifacts/proof_audit/lower_corridor/phase2x_weighted/collar_012b1_phase2x_nlift1536_top64/phase2x_collar_012b1_phase2x_nlift1536_top64_run_summary.json")
    p.add_argument("--phase2y", default="artifacts/proof_audit/lower_corridor/phase2y_upgrade/collar_012b1_phase2y_upgrade_sensitivity.json")
    p.add_argument("--out", default="artifacts/proof_audit/lower_corridor/phase2y_upgrade/collar_012b1_phase2y_fast_report.json")
    p.add_argument("--log", action="append", default=[])
    return p


def compact(d: dict) -> dict:
    keys = [
        "status", "closed_count", "pending_count", "record_count", "failed_count", "best_margin",
        "bucket_counts", "recommended_upgrade_counts", "guard_only_10pct_count", "guard_only_15pct_count",
        "guard_only_20pct_count", "needs_finite_q_upgrade_count", "minimal_closing_trial_record_count",
        "summary", "assemble_report",
    ]
    out = {k: d.get(k) for k in keys if k in d}
    if "summary" in d and isinstance(d["summary"], dict):
        out["nested_summary"] = compact(d["summary"])
    if "best_failed_rows" in d:
        out["best_failed_rows"] = d["best_failed_rows"][:8]
    if "minimal_closing_trials" in d:
        out["minimal_closing_trials"] = d["minimal_closing_trials"][:12]
    return out


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = {
        "phase2v_summary": args.phase2v_summary,
        "autopsy": args.autopsy,
        "weighted_summary": args.weighted_summary,
        "nlift1536_summary": args.nlift1536_summary,
        "phase2y": args.phase2y,
    }
    report = {name: {"path": path, "compact": compact(load(path))} for name, path in paths.items()}
    report["log_tails"] = {path: tail(path, 120) for path in args.log}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"WROTE={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
