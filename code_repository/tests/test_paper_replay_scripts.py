from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _run(cmd, cwd, *, check=True):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def test_minimal_replay_script_generates_verified_ledger(tmp_path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "minimal"
    proc = _run([sys.executable, "-S", "scripts/replay_minimal.py", "--out", str(out)], root)
    payload = json.loads(proc.stdout)
    assert payload["status"] == "ok"
    assert payload["theorem_status"] == "golden-universal-theorem-final-strong"
    replay = json.loads((out / "stage108_final_discharge_replay.json").read_text())
    assert replay["final_discharge_verified"] is True
    assert replay["active_assumptions"] == []
    assert replay["open_hypotheses"] == []
    assert replay["remaining_true_mathematical_burden"] == []


def test_downstream_from_cache_script_generates_verified_ledger(tmp_path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "downstream"
    proc = _run(
        [
            sys.executable,
            "-S",
            "scripts/replay_downstream_from_cache.py",
            "--stage-cache",
            "artifacts/final_discharge/stage_cache",
            "--out",
            str(out),
        ],
        root,
    )
    payload = json.loads(proc.stdout)
    assert payload["status"] == "ok"
    assert payload["replay_mode"] == "downstream-from-verified-cache"
    assert payload["theorem_status"] == "golden-universal-theorem-final-strong"


def test_downstream_from_cache_fails_when_cache_is_missing(tmp_path):
    root = Path(__file__).resolve().parents[1]
    proc = _run(
        [
            sys.executable,
            "-S",
            "scripts/replay_downstream_from_cache.py",
            "--stage-cache",
            str(tmp_path / "missing-cache"),
            "--out",
            str(tmp_path / "out"),
        ],
        root,
        check=False,
    )
    assert proc.returncode == 2
    assert "failed closed" in proc.stderr


def test_downstream_from_cache_allows_synthetic_only_when_explicit(tmp_path):
    root = Path(__file__).resolve().parents[1]
    proc = _run(
        [
            sys.executable,
            "-S",
            "scripts/replay_downstream_from_cache.py",
            "--stage-cache",
            str(tmp_path / "missing-cache"),
            "--allow-synthetic-upstream",
            "--out",
            str(tmp_path / "out"),
        ],
        root,
    )
    payload = json.loads(proc.stdout)
    assert payload["status"] == "ok"
    assert payload["replay_mode"] == "synthetic-upstream-explicitly-allowed"


def test_generate_artifact_manifest_writes_hash_ledger(tmp_path):
    root = Path(__file__).resolve().parents[1]
    manifest = tmp_path / "ARTIFACT_MANIFEST.tsv"
    hashes = tmp_path / "HASHES.sha256"
    _run(
        [
            sys.executable,
            "-S",
            "scripts/generate_artifact_manifest.py",
            "--root",
            str(root),
            "--out",
            str(manifest),
            "--hashes",
            str(hashes),
        ],
        root,
    )
    text = manifest.read_text()
    assert "artifact_id\tfilename\ttheorem_layer" in text
    assert "theorem_iii.json" in text
    assert "theorem_iv.json" in text
    assert "theorem_i_ii.json" in text
    hash_text = hashes.read_text()
    assert "artifacts/final_discharge/stage_cache/theorem_iv.json" in hash_text
    assert "scripts/replay_downstream_from_cache.py" in hash_text


def test_required_hash_mismatch_is_rejected(tmp_path):
    root = Path(__file__).resolve().parents[1]
    cache = tmp_path / "cache"
    cache.mkdir()
    for name in ("theorem_i_ii.json", "theorem_iii.json", "theorem_iv.json"):
        (cache / name).write_text("{}\n")
    ledger = tmp_path / "HASHES.sha256"
    rels = [str((cache / name).resolve()) for name in ("theorem_i_ii.json", "theorem_iii.json", "theorem_iv.json")]
    # Absolute paths are not used in the normal ledger, so call with --no-hash-check first
    # to show that the cache exists, then with a deliberately wrong ledger through the helper.
    proc = _run(
        [
            sys.executable,
            "-S",
            "scripts/replay_downstream_from_cache.py",
            "--stage-cache",
            str(cache),
            "--no-hash-check",
            "--out",
            str(tmp_path / "ok"),
        ],
        root,
    )
    assert json.loads(proc.stdout)["status"] == "ok"
    ledger.write_text("0" * 64 + "  " + str((cache / "theorem_i_ii.json").resolve()) + "\n")
    proc_bad = _run(
        [
            sys.executable,
            "-S",
            "scripts/replay_downstream_from_cache.py",
            "--stage-cache",
            str(cache),
            "--hashes",
            str(ledger),
            "--out",
            str(tmp_path / "bad"),
        ],
        root,
        check=False,
    )
    assert proc_bad.returncode == 2
    assert "hash" in proc_bad.stderr.lower() or "ledger" in proc_bad.stderr.lower()


def test_full_replay_fails_closed_without_archival_configuration():
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-S", "scripts/replay_full.py"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "Full archival replay is not configured" in proc.stderr
