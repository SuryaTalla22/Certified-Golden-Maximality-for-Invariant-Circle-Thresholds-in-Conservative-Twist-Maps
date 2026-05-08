from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from kam_theorem_suite.audit.lower_anchor_phase2i_segment_executor import run_preflight


class Phase2IExecutorTests(unittest.TestCase):
    def test_preflight_returns_structured_payload(self):
        report = run_preflight(repo_root=Path.cwd(), no_site=True)
        data = report.to_dict()
        self.assertEqual(data["schema"], "phase2i_preflight_v1")
        self.assertIn("import_numpy_ok", data)
        self.assertIn("import_torus_validator_ok", data)

    def test_report_schema_is_json_serializable(self):
        report = run_preflight(repo_root=Path.cwd(), no_site=True)
        payload = json.dumps(report.to_dict(), sort_keys=True)
        self.assertIn("phase2i_preflight_v1", payload)


if __name__ == "__main__":
    unittest.main()
