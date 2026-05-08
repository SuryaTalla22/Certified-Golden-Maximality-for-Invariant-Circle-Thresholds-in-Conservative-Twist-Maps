from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kam_theorem_suite.audit.manuscript_audit_outputs import (  # noqa: E402
    EXPECTED_FIGURES,
    EXPECTED_TABLES,
    MANIFEST_PATH,
    generate_all_manuscript_outputs,
    load_sources,
)


class ManuscriptAuditOutputsTests(unittest.TestCase):
    def test_generate_all_outputs_from_existing_audit_payloads(self):
        manifest = generate_all_manuscript_outputs(REPO_ROOT)
        self.assertIn(manifest["status"], {"passed", "passed-with-known-lower-gap"})
        self.assertTrue(manifest["known_lower_gap"])
        for rel in EXPECTED_TABLES.values():
            path = REPO_ROOT / rel
            self.assertTrue(path.exists(), rel)
            text = path.read_text(encoding="utf-8")
            self.assertIn("AUTO-GENERATED", text)
            self.assertIn("proof-audit", text)
        for rel in EXPECTED_FIGURES.values():
            path = REPO_ROOT / rel
            self.assertTrue(path.exists(), rel)
            self.assertGreater(path.stat().st_size, 1000)
            self.assertEqual(path.read_bytes()[:5], b"%PDF-")

    def test_manifest_records_sources_outputs_and_no_manual_editing(self):
        generate_all_manuscript_outputs(REPO_ROOT)
        manifest = json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "phase10_manuscript_audit_outputs_v1")
        self.assertFalse(manifest["manual_editing_allowed"])
        source_paths = {entry["path"] for entry in manifest["source_payloads"]}
        output_paths = {entry["path"] for entry in manifest["outputs"]}
        self.assertIn("artifacts/proof_audit/lower_corridor/lower_corridor_audit.json", source_paths)
        for rel in list(EXPECTED_TABLES.values()) + list(EXPECTED_FIGURES.values()):
            self.assertIn(str(rel), output_paths)

    def test_missing_source_payload_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "repo"
            # Create only one source file; the loader must fail closed because the
            # rest of the proof-audit payload set is absent.
            source = tmp / "artifacts/proof_audit/lower_corridor/lower_corridor_audit.json"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("{}", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                load_sources(tmp)

    def test_cli_script_entrypoints_are_present(self):
        for script in ["scripts/generate_manuscript_audit_tables.py", "scripts/generate_manuscript_audit_figures.py", "scripts/generate_manuscript_audit_outputs.py"]:
            path = REPO_ROOT / script
            self.assertTrue(path.exists(), script)
            text = path.read_text(encoding="utf-8")
            self.assertIn("cli_", text)
            self.assertIn("os._exit", text)




if __name__ == "__main__":
    unittest.main()
