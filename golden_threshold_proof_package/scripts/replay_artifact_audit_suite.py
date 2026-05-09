#!/usr/bin/env python3
from __future__ import annotations

"""Fast Phase-7 proof-artifact audit suite.

This is the reviewer-friendly path that validates proof-carrying audit bundles,
checks their replay manifest hashes, and attempts strict artifact-derived final
replay when the lower anchor is available.  The current repository snapshot is
allowed to complete successfully while reporting ``strict_final_ready=false``
because the Phase-2 lower audit intentionally exposes a known final-anchor gap.
Pass ``--strict-final`` to require strict artifact-derived final replay.
"""

from pathlib import Path
import argparse
import json
import sys

sys.dont_write_bytecode = True
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.replay_protocol import (  # noqa: E402
    build_replay_audit_manifest,
    validate_expected_audit_bundles,
    verify_manifest_hashes,
    write_json,
    write_runtime_table,
)
from kam_theorem_suite.paper_replay_inputs import build_shells_from_proof_audit  # noqa: E402
from kam_theorem_suite.lightweight_stage108_stubs import install_lightweight_stage108_stubs  # noqa: E402

install_lightweight_stage108_stubs()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", default="artifacts/proof_audit")
    parser.add_argument("--manifest", default="artifacts/proof_audit/replay/replay_audit_manifest.json")
    parser.add_argument("--out", default="artifacts/proof_audit/replay/artifact_audit_suite_report.json")
    parser.add_argument("--refresh-manifest", action="store_true", help="Rewrite the manifest before verifying hashes.")
    parser.add_argument("--no-hash-check", action="store_true", help="Skip replay audit manifest hash validation.")
    parser.add_argument("--strict-final", action="store_true", help="Require strict artifact-derived final replay and no known lower gap.")
    args = parser.parse_args(argv)

    started = time.perf_counter()
    if args.refresh_manifest:
        build_replay_audit_manifest(repository_root=ROOT, audit_dir=args.audit_dir, manifest_path=args.manifest)

    hash_failures = [] if args.no_hash_check else verify_manifest_hashes(repository_root=ROOT, manifest_path=args.manifest)
    bundle_report = validate_expected_audit_bundles(
        repository_root=ROOT,
        audit_dir=args.audit_dir,
        allow_known_lower_gap=not args.strict_final,
    )

    final_replay = {
        "attempted": False,
        "status": "skipped-known-lower-gap" if bundle_report.get("known_lower_gap") else "not-attempted",
        "error": None,
        "num_shells": None,
    }
    if bundle_report.get("strict_final_ready") and not hash_failures:
        final_replay["attempted"] = True
        try:
            shells = build_shells_from_proof_audit(ROOT / args.audit_dir)
            final_replay.update({"status": "passed", "num_shells": len(shells)})
        except Exception as exc:  # pragma: no cover - exercised by CLI tests
            final_replay.update({"status": "failed-closed", "error": str(exc)})
    elif args.strict_final:
        final_replay["attempted"] = True
        final_replay["status"] = "failed-before-final-replay"
        if hash_failures:
            final_replay["error"] = "hash manifest failures prevent final replay"
        elif bundle_report.get("known_lower_gap"):
            final_replay["error"] = "known lower final-anchor gap prevents strict final replay"
        else:
            final_replay["error"] = "bundle validation prevents strict final replay"

    runtime_seconds = time.perf_counter() - started
    status = "passed"
    if hash_failures or not bundle_report.get("protocol_passed", False):
        status = "failed"
    if args.strict_final and final_replay.get("status") != "passed":
        status = "failed"
    elif bundle_report.get("known_lower_gap"):
        status = "passed-with-known-lower-gap"

    report = {
        "schema": "phase7_artifact_audit_suite_report_v1",
        "status": status,
        "strict_final_requested": bool(args.strict_final),
        "strict_final_ready": bool(bundle_report.get("strict_final_ready")) and not bool(hash_failures),
        "known_lower_gap": bool(bundle_report.get("known_lower_gap")),
        "hash_failures": hash_failures,
        "bundle_validation": bundle_report,
        "final_artifact_derived_replay": final_replay,
        "runtime_seconds": runtime_seconds,
    }
    write_json(report, ROOT / args.out)
    write_runtime_table(
        repository_root=ROOT,
        observed_results={"artifact_audit_suite": {"runtime_seconds": runtime_seconds, "returncode": 0 if status.startswith("passed") else 2}},
    )
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0 if status.startswith("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
