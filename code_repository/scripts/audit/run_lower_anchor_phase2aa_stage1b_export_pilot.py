#!/usr/bin/env python
from __future__ import annotations

"""Phase 2AA Stage 1B exporter-patch pilot.

This is a thin orchestration script.  It reruns a small set of collar-012b1
Phase-2V indices through the existing Phase-2N -> Phase-2O -> Phase-2P pipeline
using the patched Phase-2O/2P exporters.  The mathematical closure gate is not
changed; the purpose is to regenerate diagnostic candidate JSONs that contain
``raw_validation_payload`` so Stage 1 can be rerun honestly.
"""

import argparse
from pathlib import Path
import subprocess
import sys
import json

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description="Rerun selected 012b1 pieces with Phase-2AA Stage-1B raw-payload exporters enabled.")
    ap.add_argument("--summary", required=True, help="Phase-2V 012b1 run summary JSON")
    ap.add_argument("--seed-json", required=True, help="Seed JSON used by Phase 2N")
    ap.add_argument("--indices", default="5,133,114,119,142,131,120,15,155,11")
    ap.add_argument("--label", default="collar_012b1_phase2aa_stage1b_export_pilot")
    ap.add_argument("--workers", type=int, default=64)
    ap.add_argument("--profile", default="pinpoint", choices=["weighted", "nlift1536", "nlift2048", "pinpoint"])
    ap.add_argument("--top-k", type=int, default=999)
    ap.add_argument("--force", action="store_true", help="Force regeneration of downstream 2O/2P candidates.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=None, help="Optional run summary path")
    args = ap.parse_args()

    out = args.out or f"artifacts/proof_audit/lower_corridor/phase2x_weighted/{args.label}/phase2x_{args.label}_run_summary.json"
    cmd = [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2x_weighted_rescue.py",
        "--summary", args.summary,
        "--label", args.label,
        "--seed-json", args.seed_json,
        "--indices", args.indices,
        "--top-k", str(args.top_k),
        "--workers", str(args.workers),
        "--profile", args.profile,
        "--out", out,
        "--buckets", "",
    ]
    if args.force:
        cmd.append("--force")
    if args.dry_run:
        cmd.append("--dry-run")

    print("Phase 2AA Stage 1B exporter pilot")
    print("This reruns selected pieces to regenerate candidates with raw_validation_payload.")
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=str(REPO), text=True)
    # Phase-2X returns 2 when no pieces close.  For Stage 1B this is expected;
    # the artifact is useful even if closed_count=0.  Treat 0 and 2 as success.
    if proc.returncode not in (0, 2):
        return int(proc.returncode)
    p = REPO / out
    if p.exists():
        try:
            d = json.loads(p.read_text())
            print(json.dumps({
                "status": d.get("status"),
                "label": d.get("label"),
                "result_count": d.get("result_count"),
                "closed_count": d.get("closed_count"),
                "pending_count": d.get("pending_count"),
                "summary_path": str(out),
            }, indent=2))
        except Exception:
            print(f"wrote run summary: {out}")
    else:
        print(f"WARNING: expected run summary not found: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
