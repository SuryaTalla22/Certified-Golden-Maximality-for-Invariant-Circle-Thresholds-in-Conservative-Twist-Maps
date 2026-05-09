#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kam_theorem_suite.lower_param.automatic_reducibility_audit import (
    load_npz_list_from_phase3_summary,
    run_phase4_auto_reducibility_audit,
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
    p = argparse.ArgumentParser(description="Track B Phase 4 diagnostic automatic-reducibility and radii-proxy audit.")
    p.add_argument("--phase3-summary", default=None, help="Path to phase3_small_divisor_summary.json. Used to select npz embeddings.")
    p.add_argument("--selection", default="strong", choices=["strong", "all"], help="Which Phase 3 candidates to audit.")
    p.add_argument("--anchors", default=None, help="Comma-separated K anchors to include, e.g. 0.971635.")
    p.add_argument("--resolutions", default=None, help="Comma-separated resolutions to include, e.g. 1024.")
    p.add_argument("--top", type=int, default=None, help="Limit to top-N Phase 3 candidates after filters.")
    p.add_argument("--npz", default=None, help="Comma-separated explicit npz paths. Combined with --phase3-summary selections.")
    p.add_argument("--npz-list-file", default=None, help="Text file with one npz path per line.")
    p.add_argument("--nu-grid", default="1.002,1.003,1.005")
    p.add_argument("--tail-start-fracs", default="0.50,0.75,0.90")
    p.add_argument("--omega-override", type=float, default=None)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--out-dir", default="artifacts/proof_audit/theorem_iii_trackb/phase4_auto_reducibility")
    p.add_argument("--force", action="store_true")
    p.add_argument("--y-safety-factor", type=float, default=8.0)
    p.add_argument("--z-safety-factor", type=float, default=8.0)
    p.add_argument("--q-safety-factor", type=float, default=8.0)
    args = p.parse_args()

    paths: list[str] = []
    if args.phase3_summary:
        paths.extend(load_npz_list_from_phase3_summary(
            args.phase3_summary,
            selection=args.selection,
            anchors=_floats_csv(args.anchors),
            resolutions=_ints_csv(args.resolutions),
            top=args.top,
        ))
    paths.extend(_strings_csv(args.npz))
    if args.npz_list_file:
        paths.extend([ln.strip() for ln in Path(args.npz_list_file).read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("#")])
    deduped = []
    seen = set()
    for path in paths:
        if path not in seen:
            deduped.append(path); seen.add(path)
    if not deduped:
        raise SystemExit("No npz inputs selected. Provide --phase3-summary and/or --npz.")

    summary = run_phase4_auto_reducibility_audit(
        npz_paths=deduped,
        out_dir=args.out_dir,
        workers=args.workers,
        nu_grid=_floats_csv(args.nu_grid) or [],
        tail_start_fracs=_floats_csv(args.tail_start_fracs) or [],
        omega_override=args.omega_override,
        force=args.force,
        y_safety_factor=args.y_safety_factor,
        z_safety_factor=args.z_safety_factor,
        q_safety_factor=args.q_safety_factor,
    )
    print(json.dumps({
        "status": summary.get("status"),
        "counts": summary.get("counts"),
        "parameters": summary.get("parameters"),
        "out_dir": args.out_dir,
        "summary_path": str(Path(args.out_dir) / "phase4_auto_reducibility_summary.json"),
        "csv": summary.get("csv"),
        "best_12_candidates": summary.get("best_12_candidates", [])[:12],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
