#!/usr/bin/env python3
from __future__ import annotations

"""Tiered Phase-7 full verified replay protocol.

This script runs the heavy lower audit boundary, heavy upper audit boundary,
transport-budget audit, arithmetic-domain audit, GL(2,Z) normalization audit,
and the fast artifact-audit suite.  It never stores cached Theorem V-or-above
stage artifacts.  In the current snapshot strict final replay is expected to fail
closed because the lower near-critical anchor is not yet derivable from the
available lower-corridor artifact.  Use ``--allow-known-lower-gap`` to treat that
condition as a successful protocol run while still reporting
``strict_final_ready=false``.
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
    run_command,
    write_json,
    write_runtime_table,
)


def _python_cmd() -> list[str]:
    # Use -S for subprocesses so clean artifact-review environments do not
    # execute unrelated user/site startup hooks.  All Phase-7 audit scripts have
    # standard-library fallbacks for figure generation.
    return [sys.executable or "python", "-S", "-u"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="artifacts/proof_audit/replay/full_verified_report.json")
    parser.add_argument("--audit-dir", default="artifacts/proof_audit")
    parser.add_argument("--manifest", default="artifacts/proof_audit/replay/replay_audit_manifest.json")
    parser.add_argument("--allow-known-lower-gap", action="store_true")
    parser.add_argument("--skip-figures", action="store_true", help="Skip lower figures only; other audit scripts may still render their default figures.")
    parser.add_argument("--reuse-existing-audits", action="store_true", help="Skip heavy regeneration commands and run only the artifact audit suite on existing Phase-0--6 outputs.")
    parser.add_argument("--lower-anchor-candidate", default=None, help="Optional Phase-2B heavy lower-anchor candidate passed to replay_heavy_lower.py.")
    parser.add_argument("--promote-lower-anchor", action="store_true", help="Promote a passing Phase-2B lower-anchor closure to the canonical lower bundle during full replay.")
    args = parser.parse_args(argv)

    started = time.perf_counter()

    if args.reuse_existing_audits:
        # Fast in-process path used by tests and lightweight artifact review.
        # It avoids a nested subprocess while preserving the same output report
        # written by replay_artifact_audit_suite.py.
        build_replay_audit_manifest(repository_root=ROOT, audit_dir=args.audit_dir, manifest_path=args.manifest)
        hash_failures = verify_manifest_hashes(repository_root=ROOT, manifest_path=args.manifest)
        bundle_report = validate_expected_audit_bundles(
            repository_root=ROOT,
            audit_dir=args.audit_dir,
            allow_known_lower_gap=args.allow_known_lower_gap,
        )
        final_replay = {
            "attempted": False,
            "status": "skipped-known-lower-gap" if bundle_report.get("known_lower_gap") else "not-attempted",
            "error": None,
            "num_shells": None,
        }
        runtime_seconds = time.perf_counter() - started
        artifact_status = "passed"
        if hash_failures or not bundle_report.get("protocol_passed", False):
            artifact_status = "failed"
        elif bundle_report.get("known_lower_gap"):
            artifact_status = "passed-with-known-lower-gap"
        artifact_report = {
            "schema": "phase7_artifact_audit_suite_report_v1",
            "status": artifact_status,
            "strict_final_requested": False,
            "strict_final_ready": bool(bundle_report.get("strict_final_ready")) and not bool(hash_failures),
            "known_lower_gap": bool(bundle_report.get("known_lower_gap")),
            "hash_failures": hash_failures,
            "bundle_validation": bundle_report,
            "final_artifact_derived_replay": final_replay,
            "runtime_seconds": runtime_seconds,
        }
        write_json(artifact_report, ROOT / "artifacts/proof_audit/replay/artifact_audit_suite_report.json")
        full_status = "failed" if artifact_status == "failed" else artifact_status
        full_report = {
            "schema": "phase7_full_verified_report_v1",
            "status": full_status,
            "allow_known_lower_gap": bool(args.allow_known_lower_gap),
            "strict_final_ready": bool(artifact_report["strict_final_ready"]),
            "known_lower_gap": bool(artifact_report["known_lower_gap"]),
            "blocking_failures": [] if artifact_status != "failed" else [{"name": "artifact_audit_suite", "returncode": 2}],
            "commands": [],
            "artifact_audit_suite_report": "artifacts/proof_audit/replay/artifact_audit_suite_report.json",
            "runtime_seconds": runtime_seconds,
        }
        write_json(full_report, ROOT / args.out)
        write_runtime_table(
            repository_root=ROOT,
            observed_results={
                "artifact_audit_suite": {"runtime_seconds": runtime_seconds, "returncode": 0 if artifact_status.startswith("passed") else 2},
                "full_verified": {"runtime_seconds": runtime_seconds, "returncode": 0 if full_status.startswith("passed") else 2},
            },
        )
        print(json.dumps({
            "schema": full_report["schema"],
            "status": full_report["status"],
            "strict_final_ready": full_report["strict_final_ready"],
            "known_lower_gap": full_report["known_lower_gap"],
        }, indent=2, sort_keys=True), flush=True)
        return 0 if full_status.startswith("passed") else 2

    py = _python_cmd()
    commands: list[tuple[str, list[str], bool]] = []
    if not args.reuse_existing_audits:
        lower_cmd = [*py, "scripts/replay_heavy_lower.py", "--mode", "regenerate-heavy"]
        if args.skip_figures:
            lower_cmd.append("--no-figures")
        if args.lower_anchor_candidate:
            lower_cmd.extend(["--anchor-candidate", args.lower_anchor_candidate])
        if args.promote_lower_anchor:
            lower_cmd.append("--promote-anchor-closure")
        commands.append(("heavy_lower", lower_cmd, True))
        commands.append(("heavy_upper", [*py, "scripts/replay_heavy_upper.py", "--mode", "regenerate-heavy"], True))
        commands.append(("transport_budget", [*py, "scripts/audit/audit_transport_budget.py"], True))
        commands.append(("arithmetic_domain", [*py, "scripts/audit/audit_arithmetic_domain.py"], True))
        commands.append(("gl2z_normalization", [*py, "scripts/audit/audit_gl2z_normalization.py", "--strict", "--no-figures"], True))
    commands.append(
        (
            "artifact_audit_suite",
            [*py, "scripts/replay_artifact_audit_suite.py", "--refresh-manifest", "--audit-dir", args.audit_dir, "--manifest", args.manifest]
            + ([] if args.allow_known_lower_gap else ["--strict-final"]),
            False,
        )
    )

    command_reports = []
    observed_runtime = {}
    blocking_failures = []
    for name, cmd, required in commands:
        result = run_command(name, cmd, cwd=ROOT)
        command_reports.append(result.to_dict())
        observed_runtime[name] = {"runtime_seconds": result.runtime_seconds, "returncode": result.returncode}
        if result.returncode != 0 and required:
            blocking_failures.append({"name": name, "returncode": result.returncode})
        if result.returncode != 0 and name == "artifact_audit_suite" and not args.allow_known_lower_gap:
            blocking_failures.append({"name": name, "returncode": result.returncode})

    total_runtime = time.perf_counter() - started
    status = "passed"
    strict_final_ready = True
    known_lower_gap = False
    artifact_report_path = ROOT / "artifacts/proof_audit/replay/artifact_audit_suite_report.json"
    artifact_report = None
    if artifact_report_path.exists():
        try:
            artifact_report = json.loads(artifact_report_path.read_text())
            strict_final_ready = bool(artifact_report.get("strict_final_ready", False))
            known_lower_gap = bool(artifact_report.get("known_lower_gap", False))
        except Exception:
            artifact_report = None
            strict_final_ready = False
    if blocking_failures:
        status = "failed"
    elif known_lower_gap:
        status = "passed-with-known-lower-gap" if args.allow_known_lower_gap else "failed-strict-known-lower-gap"
    elif not strict_final_ready:
        status = "failed-not-final-ready"

    report = {
        "schema": "phase7_full_verified_report_v1",
        "status": status,
        "allow_known_lower_gap": bool(args.allow_known_lower_gap),
        "strict_final_ready": bool(strict_final_ready),
        "known_lower_gap": bool(known_lower_gap),
        "blocking_failures": blocking_failures,
        "commands": command_reports,
        "artifact_audit_suite_report": None if artifact_report is None else "artifacts/proof_audit/replay/artifact_audit_suite_report.json",
        "runtime_seconds": total_runtime,
    }
    write_json(report, ROOT / args.out)
    observed_runtime["full_verified"] = {"runtime_seconds": total_runtime, "returncode": 0 if status.startswith("passed") else 2}
    write_runtime_table(repository_root=ROOT, observed_results=observed_runtime)
    # Keep stdout compact so callers that capture replay output do not inherit
    # large nested child-report payloads.  The complete report is written to
    # ``args.out`` above.
    print(json.dumps({
        "schema": report["schema"],
        "status": report["status"],
        "strict_final_ready": report["strict_final_ready"],
        "known_lower_gap": report["known_lower_gap"],
    }, indent=2, sort_keys=True), flush=True)
    return 0 if status.startswith("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
