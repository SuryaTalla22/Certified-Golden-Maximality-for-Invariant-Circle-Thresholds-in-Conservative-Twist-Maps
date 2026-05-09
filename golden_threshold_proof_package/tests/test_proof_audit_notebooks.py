from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.proof_audit_notebooks import (
    EXPECTED_NOTEBOOKS,
    execute_notebook_code_cells,
    execute_proof_audit_notebooks,
    load_notebook,
    validate_proof_audit_notebook_inventory,
    write_proof_audit_notebooks,
)

ROOT = Path(__file__).resolve().parents[1]


class TestPhase9ProofAuditNotebooks(unittest.TestCase):
    def test_expected_notebooks_exist_and_are_valid_nbformat(self) -> None:
        failures = validate_proof_audit_notebook_inventory(repository_root=ROOT)
        self.assertEqual(failures, [])
        for spec in EXPECTED_NOTEBOOKS:
            path = ROOT / "notebooks/proof_audit" / spec.filename
            nb = load_notebook(path)
            self.assertEqual(nb["nbformat"], 4)
            self.assertTrue(any(c.get("cell_type") == "markdown" for c in nb["cells"]))
            self.assertTrue(any(c.get("cell_type") == "code" for c in nb["cells"]))
            self.assertEqual(nb["metadata"].get("proof_audit_phase"), 9)

    def test_generated_inventory_lists_all_notebooks(self) -> None:
        inventory_path = ROOT / "notebooks/proof_audit/NOTEBOOK_INVENTORY.json"
        self.assertTrue(inventory_path.exists())
        inventory = json.loads(inventory_path.read_text())
        self.assertEqual(inventory["notebook_count"], len(EXPECTED_NOTEBOOKS))
        filenames = {entry["filename"] for entry in inventory["notebooks"]}
        self.assertEqual(filenames, {spec.filename for spec in EXPECTED_NOTEBOOKS})

    def test_execute_all_proof_audit_notebooks(self) -> None:
        old = os.environ.get("PHASE9_NOTEBOOK_DRY_RUN")
        os.environ["PHASE9_NOTEBOOK_DRY_RUN"] = "1"
        try:
            report = execute_proof_audit_notebooks(repository_root=ROOT)
        finally:
            if old is None:
                os.environ.pop("PHASE9_NOTEBOOK_DRY_RUN", None)
            else:
                os.environ["PHASE9_NOTEBOOK_DRY_RUN"] = old
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual(report["notebook_count"], len(EXPECTED_NOTEBOOKS))
        dashboard = json.loads((ROOT / "artifacts/proof_audit/notebooks/07_reviewer_dashboard_summary.json").read_text())
        self.assertEqual(dashboard["phase9_status"], "passed-with-known-lower-gap")
        self.assertTrue(dashboard["known_lower_gap"])
        self.assertFalse(dashboard["strict_final_ready"])

    def test_execute_notebook_script_main_writes_report(self) -> None:
        from scripts.audit.execute_proof_audit_notebooks import main as execute_main

        old = os.environ.get("PHASE9_NOTEBOOK_DRY_RUN")
        os.environ["PHASE9_NOTEBOOK_DRY_RUN"] = "1"
        try:
            rc = execute_main([])
        finally:
            if old is None:
                os.environ.pop("PHASE9_NOTEBOOK_DRY_RUN", None)
            else:
                os.environ["PHASE9_NOTEBOOK_DRY_RUN"] = old
        self.assertEqual(rc, 0)
        report_path = ROOT / "artifacts/proof_audit/notebooks/phase9_notebook_execution_report.json"
        report = json.loads(report_path.read_text())
        self.assertEqual(report["status"], "passed")

    def test_generate_notebooks_script_main_is_idempotent(self) -> None:
        from scripts.audit.generate_proof_audit_notebooks import main as generate_main

        rc = generate_main([])
        self.assertEqual(rc, 0)
        report = json.loads((ROOT / "artifacts/proof_audit/notebooks/phase9_notebook_generation_report.json").read_text())
        self.assertEqual(report["status"], "passed")

    def test_failing_notebook_fails_preflight_executor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            nb = {
                "cells": [
                    {"cell_type": "markdown", "metadata": {}, "source": ["# Failing notebook\n"]},
                    {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": ["raise RuntimeError('expected failure')\n"]},
                ],
                "metadata": {"proof_audit_phase": 9},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
            path = tmp / "failing.ipynb"
            path.write_text(json.dumps(nb))
            result = execute_notebook_code_cells(path, repository_root=ROOT)
            self.assertEqual(result["status"], "failed")
            self.assertIn("expected failure", result["error"]["message"])

    def test_notebooks_do_not_reference_forbidden_stage_cache_outputs(self) -> None:
        forbidden = [
            "artifacts/final_discharge/stage_cache/theorem_v",
            "artifacts/final_discharge/stage_cache/theorem_vi",
            "artifacts/final_discharge/stage_cache/theorem_vii",
            "artifacts/final_discharge/stage_cache/theorem_viii",
            "artifacts/final_discharge/stage_cache/stage108",
        ]
        for spec in EXPECTED_NOTEBOOKS:
            text = (ROOT / "notebooks/proof_audit" / spec.filename).read_text().lower()
            for needle in forbidden:
                self.assertNotIn(needle, text, f"{needle} found in {spec.filename}")

    def test_write_notebooks_to_temp_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            inventory = write_proof_audit_notebooks(repository_root=ROOT, notebook_dir=Path(td) / "nb")
            self.assertEqual(inventory["notebook_count"], len(EXPECTED_NOTEBOOKS))
            failures = validate_proof_audit_notebook_inventory(repository_root=ROOT, notebook_dir=Path(td) / "nb")
            self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
