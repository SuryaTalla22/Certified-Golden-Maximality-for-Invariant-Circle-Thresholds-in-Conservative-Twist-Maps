from __future__ import annotations

"""Phase-7 heavy replay and proof-audit protocol helpers.

The helpers in this module deliberately separate three notions that are easy to
conflate in a computer-assisted theorem repository:

* a script completed and wrote its audit reports;
* a proof-audit bundle is internally valid as a proof-carrying payload;
* the entire final theorem path is ready for strict artifact-derived replay.

In the current repository snapshot the lower-corridor audit is expected to be a
fail-closed audit artifact: it verifies the available local chain but refuses to
certify that the near-critical final anchor has been reached.  Phase 7 therefore
records this condition explicitly instead of hiding it behind a green status.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

from .proof_bundle_validator import (
    ProofAuditValidationError,
    load_proof_audit_bundle,
    validate_proof_audit_bundle,
)
from .proof_payload_validator import validate_layer_payload

EXPECTED_AUDIT_BUNDLES: dict[str, str] = {
    "lower_corridor": "lower_corridor/lower_corridor_audit.bundle.json",
    "upper_obstruction": "upper_obstruction/upper_obstruction_audit.bundle.json",
    "transport_budget": "transport_budget/transport_budget_audit.bundle.json",
    "arithmetic_domain": "arithmetic_domain/arithmetic_domain_audit.bundle.json",
    "gl2z_normalization": "gl2z_normalization/gl2z_normalization_audit.bundle.json",
}

LOWER_ANCHOR_CLOSURE_BUNDLE = "lower_corridor/lower_anchor_closure_audit.bundle.json"

LOWER_GAP_FAILURE_CODES = {"failure-fields", "nonpositive-margin"}
LOWER_GAP_FAILURE_LOCATIONS = {
    "/failure_fields",
    "/derived_inequalities/covered_hi_reaches_final_anchor_hi/margin",
}


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: list[str]
    returncode: int
    runtime_seconds: float
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": list(self.command),
            "returncode": int(self.returncode),
            "runtime_seconds": float(self.runtime_seconds),
            "stdout_tail": self.stdout[-4000:],
            "stderr_tail": self.stderr[-4000:],
        }


class ReplayProtocolError(RuntimeError):
    """Raised when the Phase-7 replay protocol fails before writing a report."""


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(data: Mapping[str, Any], path: str | Path) -> str:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return out.as_posix()


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ReplayProtocolError(f"JSON object expected at {path}")
    return data


def repo_relative(path: str | Path, root: str | Path) -> str:
    p = Path(path).resolve()
    r = Path(root).resolve()
    try:
        return p.relative_to(r).as_posix()
    except ValueError:
        return p.as_posix()


def run_command(
    name: str,
    command: Sequence[str],
    *,
    cwd: str | Path,
    env: Mapping[str, str] | None = None,
) -> CommandResult:
    start = time.perf_counter()
    completed = subprocess.run(
        list(command),
        cwd=str(cwd),
        env=None if env is None else dict(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed = time.perf_counter() - start
    return CommandResult(
        name=name,
        command=list(command),
        returncode=completed.returncode,
        runtime_seconds=elapsed,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def current_hardware_summary() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
    }


def expected_bundle_paths(audit_dir: str | Path) -> dict[str, Path]:
    root = Path(audit_dir)
    paths = {key: root / rel for key, rel in EXPECTED_AUDIT_BUNDLES.items()}
    closure = root / LOWER_ANCHOR_CLOSURE_BUNDLE
    if closure.exists():
        paths["lower_corridor"] = closure
    return paths


def build_replay_audit_manifest(
    *,
    repository_root: str | Path = ".",
    audit_dir: str | Path = "artifacts/proof_audit",
    manifest_path: str | Path = "artifacts/proof_audit/replay/replay_audit_manifest.json",
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    audit_root = (root / audit_dir).resolve() if not Path(audit_dir).is_absolute() else Path(audit_dir).resolve()
    entries: dict[str, Any] = {}
    for key, path in expected_bundle_paths(audit_root).items():
        if not path.exists():
            entries[key] = {
                "path": repo_relative(path, root),
                "exists": False,
                "sha256": None,
                "size_bytes": None,
            }
            continue
        entries[key] = {
            "path": repo_relative(path, root),
            "exists": True,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
    manifest = {
        "schema": "phase7_replay_audit_manifest_v1",
        "purpose": "Hash-pin proof-audit bundle inputs consumed by replay_artifact_audit_suite.py.",
        "repository_root": root.as_posix(),
        "audit_dir": repo_relative(audit_root, root),
        "entries": entries,
        "hardware_at_generation": current_hardware_summary(),
    }
    write_json(manifest, root / manifest_path)
    return manifest


def verify_manifest_hashes(
    *,
    repository_root: str | Path = ".",
    manifest_path: str | Path = "artifacts/proof_audit/replay/replay_audit_manifest.json",
) -> list[dict[str, Any]]:
    root = Path(repository_root).resolve()
    manifest_file = (root / manifest_path).resolve() if not Path(manifest_path).is_absolute() else Path(manifest_path).resolve()
    if not manifest_file.exists():
        return [{"code": "manifest-missing", "path": repo_relative(manifest_file, root), "message": "replay audit manifest is missing"}]
    manifest = load_json(manifest_file)
    entries = dict(manifest.get("entries", {}))
    failures: list[dict[str, Any]] = []
    for key, entry in entries.items():
        rel = entry.get("path")
        if not rel:
            failures.append({"code": "manifest-entry-missing-path", "layer": key, "message": "manifest entry path missing"})
            continue
        path = (root / rel).resolve()
        expected_exists = bool(entry.get("exists", True))
        if expected_exists and not path.exists():
            failures.append({"code": "artifact-missing", "layer": key, "path": str(rel), "message": "manifest-pinned artifact is missing"})
            continue
        if not expected_exists:
            continue
        observed = sha256_file(path)
        expected = str(entry.get("sha256", ""))
        if observed != expected:
            failures.append(
                {
                    "code": "hash-mismatch",
                    "layer": key,
                    "path": str(rel),
                    "expected_sha256": expected,
                    "observed_sha256": observed,
                    "message": "manifest-pinned artifact hash mismatch",
                }
            )
    return failures


def _is_known_lower_gap_failures(failures: Sequence[Any], bundle: Any) -> bool:
    if getattr(bundle, "theorem_layer", None) != "III":
        return False
    if "final_anchor_not_reached" not in list(getattr(bundle, "failure_fields", [])):
        return False
    if not failures:
        return False
    for failure in failures:
        code = getattr(failure, "code", None)
        location = getattr(failure, "location", None)
        if code not in LOWER_GAP_FAILURE_CODES:
            return False
        if location not in LOWER_GAP_FAILURE_LOCATIONS:
            return False
    return True


def validate_expected_audit_bundles(
    *,
    repository_root: str | Path = ".",
    audit_dir: str | Path = "artifacts/proof_audit",
    allow_known_lower_gap: bool = True,
) -> dict[str, Any]:
    """Validate all Phase-0--6 proof-audit bundles.

    Returns a structured report.  If ``allow_known_lower_gap`` is true, the
    current lower-corridor final-anchor failure is classified as a known
    fail-closed lower gap and does not make the protocol itself fail.  It still
    sets ``strict_final_ready`` to ``False``.
    """

    root = Path(repository_root).resolve()
    audit_root = (root / audit_dir).resolve() if not Path(audit_dir).is_absolute() else Path(audit_dir).resolve()
    layer_reports: dict[str, Any] = {}
    missing: list[dict[str, Any]] = []
    strict_final_ready = True
    protocol_passed = True
    known_lower_gap = False

    for layer, path in expected_bundle_paths(audit_root).items():
        rel = repo_relative(path, root)
        if not path.exists():
            missing.append({"layer": layer, "path": rel})
            layer_reports[layer] = {"path": rel, "exists": False, "status": "missing"}
            protocol_passed = False
            strict_final_ready = False
            continue
        bundle = load_proof_audit_bundle(path)
        # Phase 8 hardening: validate the generic proof-payload schema and
        # the layer-specific raw-field derivations.  The latter catches stale
        # status strings whose raw interval or symbolic payloads were perturbed.
        failures = validate_layer_payload(
            bundle,
            allow_known_lower_gap=allow_known_lower_gap,
            require_lower_final_anchor=not allow_known_lower_gap,
        )
        failure_dicts = [f.to_dict() for f in failures]
        current_known_lower_gap = (
            bundle.theorem_layer == "III"
            and "final_anchor_not_reached" in list(bundle.failure_fields)
        )
        if current_known_lower_gap:
            known_lower_gap = True
            strict_final_ready = False
        if failures:
            status = "failed"
            protocol_passed = False
            strict_final_ready = False
        elif current_known_lower_gap and allow_known_lower_gap:
            status = "known-fail-closed-lower-gap"
        elif current_known_lower_gap:
            status = "failed"
            protocol_passed = False
            strict_final_ready = False
        else:
            status = "passed"
        layer_reports[layer] = {
            "path": rel,
            "exists": True,
            "status": status,
            "theorem_layer": bundle.theorem_layer,
            "claim": bundle.claim,
            "failure_fields": list(bundle.failure_fields),
            "validator_failures": failure_dicts,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }

    return {
        "schema": "phase7_expected_audit_bundle_validation_v1",
        "protocol_passed": protocol_passed,
        "strict_final_ready": strict_final_ready,
        "known_lower_gap": known_lower_gap,
        "missing": missing,
        "layers": layer_reports,
    }


def write_runtime_table(
    *,
    repository_root: str | Path = ".",
    output_path: str | Path = "artifacts/proof_audit/replay/replay_runtime_table.json",
    observed_results: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    observed_results = dict(observed_results or {})

    def entry(name: str, script: str, heavy: bool = False) -> dict[str, Any]:
        observed = dict(observed_results.get(name, {}))
        return {
            "script": script,
            "runtime_seconds": float(observed.get("runtime_seconds", 0.0)),
            "returncode": observed.get("returncode"),
            "heavy_layer": heavy,
            "hardware": current_hardware_summary() if heavy else "platform-independent lightweight path",
        }

    table = {
        "schema": "phase7_replay_runtime_table_v1",
        "minimal": entry("minimal", "scripts/replay_minimal.py"),
        "downstream": entry("downstream", "scripts/replay_downstream_from_cache.py"),
        "artifact_audit_suite": entry("artifact_audit_suite", "scripts/replay_artifact_audit_suite.py"),
        "heavy_lower": entry("heavy_lower", "scripts/replay_heavy_lower.py", heavy=True),
        "heavy_upper": entry("heavy_upper", "scripts/replay_heavy_upper.py", heavy=True),
        "full_verified": entry("full_verified", "scripts/replay_full_verified.py", heavy=True),
    }
    write_json(table, root / output_path)
    return table
