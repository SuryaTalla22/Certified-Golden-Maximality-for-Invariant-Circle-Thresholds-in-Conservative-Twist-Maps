#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.theorem_iv_cache_inventory import (
    audit_theorem_iv_cache,
    copy_available_theorem_iv_cache,
    write_theorem_iv_cache_audit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory or restore cached Theorem-IV artifacts from an older repository checkout.")
    parser.add_argument("--stage-cache-dir", default="artifacts/final_discharge/stage_cache")
    parser.add_argument("--manifest", default="ARTIFACT_MANIFEST.tsv")
    parser.add_argument("--source-root", action="append", default=[], help="Old repository root, old stage_cache dir, or directory containing theorem_iv*.json. May be repeated.")
    parser.add_argument("--copy", action="store_true", help="Copy available missing Theorem-IV files from source roots into the stage cache.")
    parser.add_argument("--allow-overwrite", action="store_true")
    parser.add_argument("--no-hashes", dest="compute_hashes", action="store_false")
    parser.add_argument("--out", default="artifacts/proof_audit/replay/theorem_iv_cache_inventory.json")
    parser.set_defaults(compute_hashes=True)
    args = parser.parse_args(argv)
    stage = ROOT / args.stage_cache_dir
    manifest = ROOT / args.manifest
    sources = [Path(x) for x in args.source_root]
    if args.copy:
        report = copy_available_theorem_iv_cache(
            stage_cache_dir=stage,
            manifest_path=manifest,
            source_roots=sources,
            allow_overwrite=bool(args.allow_overwrite),
            compute_hashes=bool(args.compute_hashes),
        )
        status = "complete" if report["after"].get("complete") else "incomplete"
    else:
        audit = audit_theorem_iv_cache(stage_cache_dir=stage, manifest_path=manifest, source_roots=sources, compute_hashes=bool(args.compute_hashes))
        report = audit.to_dict()
        status = "complete" if audit.complete else "incomplete"
    out_path = ROOT / args.out
    write_theorem_iv_cache_audit(report, out_path)
    display = dict(report)
    if "records" in display:
        display["records"] = display["records"][:5]
        display["records_truncated"] = True
    print(json.dumps({"status": status, "out": out_path.relative_to(ROOT).as_posix(), "summary": {k: display.get(k) for k in ("required_count", "present_count", "missing_count", "source_available_count", "failure_fields", "complete") if k in display}}, indent=2, sort_keys=True))
    return 0 if status == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
