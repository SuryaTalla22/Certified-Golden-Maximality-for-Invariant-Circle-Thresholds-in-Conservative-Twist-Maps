#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kam_theorem_suite.lower_param.fourier_tail_audit import (
    load_npz_list_from_phase1_summary,
    run_phase2_tail_audit,
)


def _floats_csv(s: str | None):
    if not s:
        return None
    return [float(x.strip()) for x in s.split(",") if x.strip()]


def _ints_csv(s: str | None):
    if not s:
        return None
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def _strings_csv(s: str | None):
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def main() -> None:
    p = argparse.ArgumentParser(description="Track B Phase 2 diagnostic Fourier-tail audit for Phase 1 seed embeddings.")
    p.add_argument("--phase1-summary", default=None, help="Path to phase1_seed_summary.json. Used to select npz embeddings.")
    p.add_argument("--selection", default="converged", choices=["converged", "best_by_anchor", "all"], help="Which Phase 1 rows to audit.")
    p.add_argument("--anchors", default=None, help="Comma-separated K anchors to include, e.g. 0.9663,0.971635.")
    p.add_argument("--resolutions", default=None, help="Comma-separated resolutions to include, e.g. 128,1024.")
    p.add_argument("--npz", default=None, help="Comma-separated explicit npz paths. Combined with --phase1-summary selections.")
    p.add_argument("--npz-list-file", default=None, help="Text file with one npz path per line.")
    p.add_argument("--nu-grid", default="1.002,1.003,1.005,1.008,1.010,1.012,1.015")
    p.add_argument("--tail-start-fracs", default="0.25,0.50,0.75,0.85,0.90")
    p.add_argument("--fit-min-frac", type=float, default=0.08)
    p.add_argument("--fit-max-frac", type=float, default=0.70)
    p.add_argument("--coefficient-floor-rel", type=float, default=1e-14)
    p.add_argument("--shell-count", type=int, default=24)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--out-dir", default="artifacts/proof_audit/theorem_iii_trackb/phase2_tail_audit")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    paths: list[str] = []
    anchors = _floats_csv(args.anchors)
    resolutions = _ints_csv(args.resolutions)
    selection = "converged" if args.selection == "all" else args.selection
    if args.phase1_summary:
        paths.extend(load_npz_list_from_phase1_summary(args.phase1_summary, selection=selection, anchors=anchors, resolutions=resolutions))
    paths.extend(_strings_csv(args.npz))
    if args.npz_list_file:
        paths.extend([ln.strip() for ln in Path(args.npz_list_file).read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("#")])

    # Deduplicate while preserving order.
    deduped = []
    seen = set()
    for path in paths:
        if path not in seen:
            deduped.append(path); seen.add(path)
    if not deduped:
        raise SystemExit("No npz inputs selected. Provide --phase1-summary and/or --npz.")

    summary = run_phase2_tail_audit(
        npz_paths=deduped,
        out_dir=args.out_dir,
        workers=args.workers,
        nu_grid=_floats_csv(args.nu_grid) or [],
        tail_start_fracs=_floats_csv(args.tail_start_fracs) or [],
        fit_min_frac=args.fit_min_frac,
        fit_max_frac=args.fit_max_frac,
        coefficient_floor_rel=args.coefficient_floor_rel,
        shell_count=args.shell_count,
        force=args.force,
    )
    print(json.dumps({
        "status": summary.get("status"),
        "counts": summary.get("counts"),
        "parameters": summary.get("parameters"),
        "out_dir": args.out_dir,
        "summary_path": str(Path(args.out_dir) / "phase2_tail_audit_summary.json"),
        "csv": summary.get("csv"),
        "best_12_candidates": summary.get("best_12_candidates", [])[:12],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
