#!/usr/bin/env python3
from __future__ import annotations

"""Build the Phase-7 replay audit manifest for proof-audit bundle hashes."""

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.replay_protocol import build_replay_audit_manifest  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", default="artifacts/proof_audit")
    parser.add_argument("--out", default="artifacts/proof_audit/replay/replay_audit_manifest.json")
    args = parser.parse_args(argv)
    manifest = build_replay_audit_manifest(repository_root=ROOT, audit_dir=args.audit_dir, manifest_path=args.out)
    print(json.dumps({"status": "ok", "out": args.out, "entries": sorted(manifest["entries"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
