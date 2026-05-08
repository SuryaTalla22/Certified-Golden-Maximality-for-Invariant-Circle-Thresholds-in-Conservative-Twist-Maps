from __future__ import annotations

"""Theorem-IV cache inventory and restoration helpers.

Phase 2C intentionally omits most heavy Theorem-IV cache payloads.  This module
lets a reviewer or maintainer compare the current repository against the
manifest, copy available cached IV artifacts from an older repository checkout,
and write a machine-readable report.  The helper never fabricates missing
payloads and never treats restored cache provenance as a mathematical proof.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import csv
import hashlib
import json
import shutil


@dataclass(frozen=True)
class TheoremIVManifestEntry:
    artifact_id: str
    path: str
    layer: str
    role: str
    expected_sha256: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TheoremIVCacheRecord:
    artifact_id: str
    path: str
    role: str
    expected_sha256: str | None
    present: bool
    size_bytes: int | None
    sha256: str | None
    hash_matches_manifest: bool | None
    available_sources: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["available_sources"] = list(self.available_sources)
        return d


@dataclass(frozen=True)
class TheoremIVCacheAudit:
    schema: str
    stage_cache_dir: str
    manifest_path: str
    required_count: int
    present_count: int
    missing_count: int
    hash_checked_count: int
    hash_match_count: int
    source_available_count: int
    records: tuple[TheoremIVCacheRecord, ...]
    failure_fields: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return self.missing_count == 0 and not self.failure_fields

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "stage_cache_dir": self.stage_cache_dir,
            "manifest_path": self.manifest_path,
            "required_count": self.required_count,
            "present_count": self.present_count,
            "missing_count": self.missing_count,
            "hash_checked_count": self.hash_checked_count,
            "hash_match_count": self.hash_match_count,
            "source_available_count": self.source_available_count,
            "complete": self.complete,
            "records": [r.to_dict() for r in self.records],
            "failure_fields": list(self.failure_fields),
        }


def sha256_file(path: str | Path, *, block_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(block_size), b""):
            h.update(block)
    return h.hexdigest()


def parse_theorem_iv_manifest(manifest_path: str | Path) -> list[TheoremIVManifestEntry]:
    path = Path(manifest_path)
    entries: list[TheoremIVManifestEntry] = []
    with path.open(newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        for row in reader:
            if not row or row[0].startswith("#"):
                continue
            if len(row) < 8:
                continue
            artifact_id, artifact_path, layer, role = row[0], row[1], row[2], row[3]
            if layer != "IV" and "theorem_iv" not in artifact_path:
                continue
            expected = row[7].strip() if len(row) > 7 and row[7].strip() and row[7].strip() != "see HASHES.sha256 and release log" else None
            entries.append(TheoremIVManifestEntry(str(artifact_id), str(artifact_path), str(layer), str(role), expected))
    return entries


def _candidate_source_paths(entry: TheoremIVManifestEntry, source_roots: Sequence[str | Path]) -> tuple[str, ...]:
    out: list[str] = []
    rel = Path(entry.path)
    name = rel.name
    for root in source_roots:
        rootp = Path(root)
        candidates = [rootp / rel, rootp / "artifacts/final_discharge/stage_cache" / name, rootp / name]
        for p in candidates:
            if p.exists() and p.is_file():
                s = str(p)
                if s not in out:
                    out.append(s)
    return tuple(out)


def audit_theorem_iv_cache(
    *,
    stage_cache_dir: str | Path,
    manifest_path: str | Path,
    source_roots: Sequence[str | Path] = (),
    compute_hashes: bool = True,
) -> TheoremIVCacheAudit:
    stage = Path(stage_cache_dir)
    entries = parse_theorem_iv_manifest(manifest_path)
    records: list[TheoremIVCacheRecord] = []
    for entry in entries:
        local = stage / Path(entry.path).name
        present = local.exists() and local.is_file()
        size = local.stat().st_size if present else None
        digest = sha256_file(local) if present and compute_hashes else None
        match = None
        if present and compute_hashes and entry.expected_sha256:
            match = digest == entry.expected_sha256
        records.append(TheoremIVCacheRecord(
            artifact_id=entry.artifact_id,
            path=entry.path,
            role=entry.role,
            expected_sha256=entry.expected_sha256,
            present=bool(present),
            size_bytes=size,
            sha256=digest,
            hash_matches_manifest=match,
            available_sources=_candidate_source_paths(entry, source_roots),
        ))
    missing = [r for r in records if not r.present]
    hash_checked = [r for r in records if r.hash_matches_manifest is not None]
    hash_matches = [r for r in hash_checked if r.hash_matches_manifest]
    source_available = [r for r in records if r.available_sources]
    failures: list[str] = []
    if missing:
        failures.append("theorem_iv_cache_files_missing")
    if hash_checked and len(hash_matches) != len(hash_checked):
        failures.append("theorem_iv_cache_hash_mismatch")
    return TheoremIVCacheAudit(
        schema="theorem_iv_cache_inventory_v1",
        stage_cache_dir=str(stage),
        manifest_path=str(manifest_path),
        required_count=len(records),
        present_count=len(records) - len(missing),
        missing_count=len(missing),
        hash_checked_count=len(hash_checked),
        hash_match_count=len(hash_matches),
        source_available_count=len(source_available),
        records=tuple(records),
        failure_fields=tuple(failures),
    )


def copy_available_theorem_iv_cache(
    *,
    stage_cache_dir: str | Path,
    manifest_path: str | Path,
    source_roots: Sequence[str | Path],
    allow_overwrite: bool = False,
    compute_hashes: bool = True,
) -> dict[str, Any]:
    stage = Path(stage_cache_dir)
    stage.mkdir(parents=True, exist_ok=True)
    before = audit_theorem_iv_cache(stage_cache_dir=stage, manifest_path=manifest_path, source_roots=source_roots, compute_hashes=False)
    copied: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for record in before.records:
        target = stage / Path(record.path).name
        if target.exists() and not allow_overwrite:
            skipped.append({"path": record.path, "reason": "target_exists"})
            continue
        if not record.available_sources:
            skipped.append({"path": record.path, "reason": "no_available_source"})
            continue
        source = Path(record.available_sources[0])
        shutil.copy2(source, target)
        copied.append({"path": record.path, "source": str(source), "target": str(target)})
    after = audit_theorem_iv_cache(stage_cache_dir=stage, manifest_path=manifest_path, source_roots=source_roots, compute_hashes=compute_hashes)
    return {
        "schema": "theorem_iv_cache_restore_report_v1",
        "copied": copied,
        "skipped": skipped,
        "before": before.to_dict(),
        "after": after.to_dict(),
    }


def write_theorem_iv_cache_audit(audit_or_report: Mapping[str, Any] | TheoremIVCacheAudit, path: str | Path) -> None:
    data = audit_or_report.to_dict() if isinstance(audit_or_report, TheoremIVCacheAudit) else dict(audit_or_report)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


__all__ = [
    "TheoremIVCacheAudit",
    "TheoremIVCacheRecord",
    "TheoremIVManifestEntry",
    "audit_theorem_iv_cache",
    "copy_available_theorem_iv_cache",
    "parse_theorem_iv_manifest",
    "sha256_file",
    "write_theorem_iv_cache_audit",
]
