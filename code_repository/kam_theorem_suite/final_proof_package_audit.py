from __future__ import annotations

"""Stage-108 final proof-package audit helpers.

These helpers are deliberately small and conservative.  They check whether a
bundle manifest is consistent with the repository's packaging convention: patch
bundles may include source, tests, docs, notebooks, and summaries, but should not
include regenerated downstream theorem artifact caches from Theorem V,
identification, VI, VII, VIII, or beyond.
"""

from pathlib import Path
from typing import Iterable, Mapping, Any


DISALLOWED_ARTIFACT_TOKENS = (
    "theorem_v",
    "identification",
    "theorem_vi",
    "theorem_vii",
    "theorem_viii",
    "final_discharge",
    "stage_cache",
)


def classify_patch_bundle_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if "/artifacts/" in normalized or normalized.startswith("artifacts/"):
        return "artifact"
    if normalized.endswith(".py"):
        return "source"
    if "/tests/" in normalized or normalized.startswith("tests/"):
        return "test"
    if "/docs/" in normalized or normalized.startswith("docs/"):
        return "doc"
    if "/notebooks/" in normalized or normalized.startswith("notebooks/"):
        return "notebook"
    if normalized.endswith(".txt") or normalized.endswith(".md"):
        return "summary"
    return "other"


def audit_patch_bundle_manifest(paths: Iterable[str]) -> dict[str, Any]:
    path_list = [str(p) for p in paths]
    disallowed = []
    classifications: dict[str, int] = {}
    for p in path_list:
        kind = classify_patch_bundle_path(p)
        classifications[kind] = classifications.get(kind, 0) + 1
        normalized = p.replace("\\", "/").lower()
        if kind == "artifact" and any(token in normalized for token in DISALLOWED_ARTIFACT_TOKENS):
            disallowed.append(p)
    return {
        "status": "stage108-patch-bundle-manifest-clean" if not disallowed else "stage108-patch-bundle-manifest-has-disallowed-artifacts",
        "path_count": len(path_list),
        "classifications": classifications,
        "disallowed_downstream_artifact_paths": disallowed,
        "excludes_theorem_v_identification_vi_vii_viii_artifact_caches": len(disallowed) == 0,
    }


def audit_final_theorem_statement_scope(report: Mapping[str, Any]) -> dict[str, Any]:
    """Check that the replay report exposes the scope commitments needed in the paper."""

    discharge = dict(report.get("theorem_viii_discharge", {}))
    support = dict(report.get("support_certificate", {}))
    upstream = dict(report.get("upstream_statuses", {}))

    flags = {
        "final_status_is_strong": report.get("theorem_viii_discharge_status") == "golden-universal-theorem-final-strong",
        "gl2z_normalization_closed": bool(support.get("proves_gl2z_orbit_uniqueness_and_normalization_closed")),
        "universality_matching_closed": bool(support.get("proves_final_universality_class_matches_reduction_statement")),
        "final_reduction_closed": bool(
            support.get("proves_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality")
        ),
        "theorem_vii_global_exhaustion_consumed": "theorem_vii" in upstream and "strong" in str(upstream.get("theorem_vii", "")),
        "final_golden_maximality_discharge": bool(discharge.get("final_golden_maximality_discharge")),
        "paper_ready": bool(discharge.get("final_certificate_ready_for_paper")),
    }
    failed = [k for k, v in flags.items() if not v]
    return {
        "status": "stage108-final-statement-scope-audit-passed" if not failed else "stage108-final-statement-scope-audit-failed",
        "flags": flags,
        "failed_checks": failed,
    }
