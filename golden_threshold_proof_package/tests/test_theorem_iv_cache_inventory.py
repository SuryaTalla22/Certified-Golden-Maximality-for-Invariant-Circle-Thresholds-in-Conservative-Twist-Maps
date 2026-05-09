from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kam_theorem_suite.audit.theorem_iv_cache_inventory import (
    audit_theorem_iv_cache,
    copy_available_theorem_iv_cache,
    parse_theorem_iv_manifest,
    sha256_file,
)


class TheoremIVCacheInventoryTests(unittest.TestCase):
    def test_parse_manifest_and_audit_missing_available_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "ARTIFACT_MANIFEST.tsv"
            source = root / "old" / "artifacts/final_discharge/stage_cache"
            source.mkdir(parents=True)
            payload = source / "theorem_iv.json"
            payload.write_text('{"ok": true}\n')
            digest = sha256_file(payload)
            manifest.write_text(
                "A0003\tartifacts/final_discharge/stage_cache/theorem_iv.json\tIV\ttheorem-facing\tx\tx\tx\t" + digest + "\n"
                "A0004\tartifacts/final_discharge/stage_cache/theorem_iv_upper_bridge.json\tIV\tsupport/cache\tx\tx\tx\tdeadbeef\n"
            )
            entries = parse_theorem_iv_manifest(manifest)
            self.assertEqual(len(entries), 2)
            audit = audit_theorem_iv_cache(stage_cache_dir=root / "new", manifest_path=manifest, source_roots=[root / "old"], compute_hashes=True)
            self.assertEqual(audit.required_count, 2)
            self.assertEqual(audit.present_count, 0)
            self.assertEqual(audit.source_available_count, 1)
            self.assertIn("theorem_iv_cache_files_missing", audit.failure_fields)

    def test_copy_available_cache_preserves_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "ARTIFACT_MANIFEST.tsv"
            source = root / "old" / "artifacts/final_discharge/stage_cache"
            source.mkdir(parents=True)
            payload = source / "theorem_iv.json"
            payload.write_text('{"ok": true}\n')
            digest = sha256_file(payload)
            manifest.write_text("A0003\tartifacts/final_discharge/stage_cache/theorem_iv.json\tIV\ttheorem-facing\tx\tx\tx\t" + digest + "\n")
            report = copy_available_theorem_iv_cache(stage_cache_dir=root / "new", manifest_path=manifest, source_roots=[root / "old"], compute_hashes=True)
            self.assertEqual(len(report["copied"]), 1)
            self.assertEqual(report["after"]["present_count"], 1)
            self.assertEqual(report["after"]["hash_match_count"], 1)
            self.assertTrue((root / "new" / "theorem_iv.json").exists())


if __name__ == "__main__":
    unittest.main()
