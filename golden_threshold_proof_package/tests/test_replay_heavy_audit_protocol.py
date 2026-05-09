from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.proof_bundle_validator import validate_proof_audit_bundle
from kam_theorem_suite.audit.proof_payload import ProofAuditBundle
from kam_theorem_suite.audit.replay_protocol import (
    build_replay_audit_manifest,
    validate_expected_audit_bundles,
    verify_manifest_hashes,
)

ROOT = Path(__file__).resolve().parents[1]


class TestPhase7ReplayHeavyAuditProtocol(unittest.TestCase):
    def run_script(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            [sys.executable, "-S", *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
        )
        if check and proc.returncode != 0:
            self.fail(f"command failed: {args}\nstdout={proc.stdout[-2000:]}\nstderr={proc.stderr[-2000:]}")
        return proc

    def test_replay_artifact_audit_suite_succeeds_on_current_artifacts(self) -> None:
        proc = self.run_script("scripts/replay_artifact_audit_suite.py", "--refresh-manifest")
        self.assertIn("passed", proc.stdout)
        report = json.loads((ROOT / "artifacts/proof_audit/replay/artifact_audit_suite_report.json").read_text())
        self.assertTrue(report["status"].startswith("passed"))
        self.assertFalse(report["known_lower_gap"])
        self.assertTrue(report["strict_final_ready"])

    def test_removing_any_audit_json_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            audit_copy = Path(td) / "proof_audit"
            shutil.copytree(ROOT / "artifacts/proof_audit", audit_copy)
            (audit_copy / "upper_obstruction/upper_obstruction_audit.bundle.json").unlink()
            report = validate_expected_audit_bundles(repository_root=Path(td), audit_dir=audit_copy)
            self.assertFalse(report["protocol_passed"])
            self.assertEqual(report["layers"]["upper_obstruction"]["status"], "missing")

    def test_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            audit_copy = tmp / "artifacts/proof_audit"
            shutil.copytree(ROOT / "artifacts/proof_audit", audit_copy)
            manifest_path = tmp / "artifacts/proof_audit/replay/replay_audit_manifest.json"
            build_replay_audit_manifest(repository_root=tmp, audit_dir=audit_copy, manifest_path=manifest_path)
            target = audit_copy / "upper_obstruction/upper_obstruction_audit.bundle.json"
            data = json.loads(target.read_text())
            data.setdefault("audit_metadata", {})["tamper"] = True
            target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
            failures = verify_manifest_hashes(repository_root=tmp, manifest_path=manifest_path)
            self.assertTrue(any(f["code"] == "hash-mismatch" for f in failures))

    def test_payload_mismatch_with_same_status_flags_fails(self) -> None:
        bundle_path = ROOT / "artifacts/proof_audit/transport_budget/transport_budget_audit.bundle.json"
        data = json.loads(bundle_path.read_text())
        # Preserve the status/Boolean fields but perturb a raw value used by a
        # theorem-facing inequality.  The stored margin is now stale and must be rejected.
        data["derived_inequalities"]["budget_preserves_available_gap"]["lhs_value"] += 1.0e-3
        bundle = ProofAuditBundle.from_dict(data)
        failures = validate_proof_audit_bundle(bundle)
        codes = {f.code for f in failures}
        self.assertIn("margin-mismatch", codes)

    def test_full_verified_replay_writes_all_expected_reports(self) -> None:
        proc = self.run_script("scripts/replay_full_verified.py", "--allow-known-lower-gap", "--skip-figures", "--reuse-existing-audits")
        self.assertIn('"status": "passed"', proc.stdout)
        expected = [
            ROOT / "artifacts/proof_audit/replay/artifact_audit_suite_report.json",
            ROOT / "artifacts/proof_audit/replay/full_verified_report.json",
            ROOT / "artifacts/proof_audit/replay/replay_runtime_table.json",
            ROOT / "artifacts/proof_audit/replay/replay_audit_manifest.json",
        ]
        for path in expected:
            self.assertTrue(path.exists(), path)
        report = json.loads((ROOT / "artifacts/proof_audit/replay/full_verified_report.json").read_text())
        self.assertEqual(report["status"], "passed")
        self.assertFalse(report["known_lower_gap"])
        self.assertTrue(report["strict_final_ready"])


if __name__ == "__main__":
    unittest.main()
