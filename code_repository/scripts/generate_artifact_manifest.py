#!/usr/bin/env python3
from __future__ import annotations

"""Generate the paper artifact manifest and SHA256 ledger.

The manifest lists every JSON artifact in the final-discharge stage cache.  The
hash ledger lists those artifacts plus the core paper-facing audit files.  Run
this script from the repository root after changing artifacts, replay scripts, or
audit documentation.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


THEOREM_LAYER_BY_NAME = {
    "theorem_i_ii": "I--II",
    "theorem_iii": "III",
    "theorem_iv": "IV",
    "theorem_v": "V",
    "identification": "ID",
    "theorem_vi": "VI",
    "theorem_vii": "VII",
    "theorem_viii": "VIII",
    "final": "Final replay",
    "stage108": "Final replay",
}
CORE_AUDIT_FILES = [
    "README.md",
    "pyproject.toml",
    "CERTIFIED_UNIVERSE.json",
    "RELEASE_INFO.md",
    "docs/VALIDATOR_SPEC.md",
    "docs/CERTIFICATE_GLOSSARY.md",
    "docs/REFEREE_AUDIT_PROTOCOL.md",
    "scripts/replay_minimal.py",
    "scripts/replay_downstream_from_cache.py",
    "scripts/replay_full.py",
    "scripts/generate_artifact_manifest.py",
    "kam_theorem_suite/paper_replay_inputs.py",
    "tests/test_paper_replay_scripts.py",
    "tests/test_negative_final_replay_controls.py",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_layer(path: Path) -> str:
    text = path.name.lower()
    for token, layer in THEOREM_LAYER_BY_NAME.items():
        if token in text:
            return layer
    return "support"


def theorem_facing(path: Path, layer: str) -> str:
    base = path.name
    if base in {
        "theorem_i_ii.json",
        "theorem_iii.json",
        "theorem_iv.json",
        "theorem_v.json",
        "identification.json",
        "theorem_vi.json",
        "theorem_vii.json",
        "theorem_viii.json",
        "final_discharge_replay.json",
    }:
        return "theorem-facing"
    if layer in {"I--II", "III", "IV", "V", "ID", "VI", "VII", "VIII", "Final replay"}:
        return "support/cache"
    return "diagnostic/support"


def status_from_json(path: Path) -> str:
    # Avoid loading very large profile artifacts while keeping small theorem
    # objects transparent in the manifest.
    if path.stat().st_size > 5_000_000:
        return "see-large-artifact-payload"
    try:
        payload: Any = json.loads(path.read_text())
    except Exception:
        return ""
    if isinstance(payload, dict):
        return str(payload.get("theorem_status", payload.get("status", "")))
    return ""


def role_for(path: Path, layer: str) -> str:
    name = path.name
    if name == "theorem_i_ii.json":
        return "Cached theorem-facing workstream package consumed by downstream replay"
    if name == "theorem_iii.json":
        return "Cached theorem-facing lower-corridor package consumed by downstream replay"
    if name == "theorem_iv.json":
        return "Cached theorem-facing upper-obstruction package consumed by downstream replay"
    if name.startswith("theorem_iv_upper"):
        return "Theorem-IV support/cache artifact for obstruction-side audit"
    return f"Cached {layer} artifact or support record"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--artifact-dir", default="artifacts/final_discharge/stage_cache")
    parser.add_argument("--out", default="ARTIFACT_MANIFEST.tsv")
    parser.add_argument("--hashes", default="HASHES.sha256")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    artifact_dir = (root / args.artifact_dir).resolve()
    files = sorted(p for p in artifact_dir.glob("*.json") if p.is_file()) if artifact_dir.exists() else []

    fieldnames = [
        "artifact_id",
        "filename",
        "theorem_layer",
        "theorem_facing_or_diagnostic",
        "producing_module",
        "producing_command",
        "upstream_artifact_hashes",
        "sha256",
        "status_field",
        "active_assumptions",
        "open_hypotheses",
        "mathematical_role",
        "included_in_minimal_replay",
        "included_in_downstream_replay",
        "included_in_full_replay",
    ]

    rows = []
    hash_targets: list[Path] = []
    for idx, path in enumerate(files, start=1):
        rel = path.relative_to(root).as_posix()
        digest = sha256(path)
        layer = classify_layer(path)
        rows.append(
            {
                "artifact_id": f"A{idx:04d}",
                "filename": rel,
                "theorem_layer": layer,
                "theorem_facing_or_diagnostic": theorem_facing(path, layer),
                "producing_module": "archival theorem generation stack; see manuscript and release log",
                "producing_command": "scripts/replay_full.py after heavy Theorem-IV regeneration is wired, or archived cache in this release",
                "upstream_artifact_hashes": "see HASHES.sha256 and release log",
                "sha256": digest,
                "status_field": status_from_json(path),
                "active_assumptions": "see artifact payload",
                "open_hypotheses": "see artifact payload",
                "mathematical_role": role_for(path, layer),
                "included_in_minimal_replay": "no",
                "included_in_downstream_replay": "yes" if path.name in {"theorem_i_ii.json", "theorem_iii.json", "theorem_iv.json"} else "cache/provenance",
                "included_in_full_replay": "yes",
            }
        )
        hash_targets.append(path)

    for rel in CORE_AUDIT_FILES:
        path = root / rel
        if path.exists():
            hash_targets.append(path)

    out = root / args.out
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    seen: set[str] = set()
    lines: list[str] = []
    for path in hash_targets:
        rel = path.relative_to(root).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        lines.append(f"{sha256(path)}  {rel}")
    (root / args.hashes).write_text("\n".join(lines) + ("\n" if lines else ""))
    print(f"wrote {out} with {len(rows)} artifact rows")
    print(f"wrote {root / args.hashes} with {len(lines)} hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
