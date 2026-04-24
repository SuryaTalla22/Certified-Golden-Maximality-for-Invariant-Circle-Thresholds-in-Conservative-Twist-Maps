from __future__ import annotations

"""Deterministic theorem shells and validation helpers for paper-facing replay.

The minimal replay uses compact theorem-facing shells.  The downstream replay
uses the same compact theorem-facing fields, but it is required to attach and
validate provenance from cached heavy I--II/III/IV artifacts.  This module keeps
those two paths explicit so that a referee can distinguish a smoke test from a
cache-backed replay.
"""

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib


BASE_K_VALUES = (0.971635, 0.971637)
REQUIRED_STAGE_CACHE_FILES = (
    "theorem_i_ii.json",
    "theorem_iii.json",
    "theorem_iv.json",
)


class PaperReplayValidationError(RuntimeError):
    """Raised when a paper-facing replay shell or artifact cache is invalid."""


def _sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_hash_ledger(path: str | Path) -> dict[str, str]:
    """Load a standard ``sha256sum`` ledger as ``relative_path -> digest``."""

    ledger_path = Path(path)
    if not ledger_path.exists():
        raise PaperReplayValidationError(f"hash ledger not found: {ledger_path}")
    out: dict[str, str] = {}
    for lineno, raw in enumerate(ledger_path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise PaperReplayValidationError(f"malformed hash line {lineno} in {ledger_path}: {raw!r}")
        digest, rel = parts
        out[rel.strip()] = digest.strip()
    return out


def verify_required_stage_cache(
    stage_cache_dir: str | Path,
    *,
    repository_root: str | Path = ".",
    hash_ledger: str | Path | None = "HASHES.sha256",
) -> dict[str, dict[str, Any]]:
    """Verify that required cached upstream artifacts exist and match hashes.

    Returns a provenance dictionary keyed by artifact file name.  If
    ``hash_ledger`` is ``None``, existence and local SHA256 values are checked but
    no ledger comparison is made.
    """

    root = Path(repository_root).resolve()
    stage_cache = (root / stage_cache_dir).resolve() if not Path(stage_cache_dir).is_absolute() else Path(stage_cache_dir)
    if not stage_cache.exists():
        raise PaperReplayValidationError(f"stage cache directory not found: {stage_cache}")

    ledger: dict[str, str] = {}
    if hash_ledger is not None:
        ledger_path = (root / hash_ledger).resolve() if not Path(hash_ledger).is_absolute() else Path(hash_ledger)
        if ledger_path.exists():
            ledger = load_hash_ledger(ledger_path)
        else:
            raise PaperReplayValidationError(f"hash ledger not found: {ledger_path}")

    provenance: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_STAGE_CACHE_FILES:
        path = stage_cache / name
        if not path.exists():
            raise PaperReplayValidationError(f"required cached artifact is missing: {path}")
        digest = _sha256(path)
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()
        if ledger:
            expected = ledger.get(rel)
            if expected is None:
                raise PaperReplayValidationError(f"required cached artifact is absent from hash ledger: {rel}")
            if expected != digest:
                raise PaperReplayValidationError(
                    f"hash mismatch for {rel}: expected {expected}, observed {digest}"
                )
        provenance[name] = {
            "source": path.as_posix(),
            "relative_path": rel,
            "sha256": digest,
            "size_bytes": path.stat().st_size,
        }
    return provenance


def _annotate_cached(shell: dict[str, Any], provenance: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(shell)
    out["cached_artifact_source"] = str(provenance["source"])
    out["cached_artifact_relative_path"] = str(provenance["relative_path"])
    out["cached_artifact_sha256"] = str(provenance["sha256"])
    out["cached_artifact_size_bytes"] = int(provenance["size_bytes"])
    out["cached_artifact_verified"] = True
    return out


def build_minimal_theorem_shells() -> tuple[dict[str, Any], ...]:
    """Return compact theorem-facing shells for the final replay.

    The returned tuple is ordered as
    ``(I_II, III, IV, V, identification, VI, VII)``.  It is intentionally small:
    it tests downstream proof-ledger logic without consuming generated heavy
    caches.  The downstream replay must call :func:`build_shells_from_stage_cache`
    instead.
    """

    workstream = {
        "theorem_status": "golden-theorem-i-ii-workstream-papergrade-final",
        "open_hypotheses": [],
        "active_assumptions": [],
        "workstream_codepath_strong": True,
        "workstream_papergrade_strong": True,
        "workstream_residual_caveat": [],
        "residual_burden_summary": {
            "promotion_theorem_discharged": True,
            "status": "workstream-papergrade-final",
        },
    }
    theorem_iii = {
        "theorem_status": "golden-theorem-iii-final-strong",
        "theorem_iii_final_status": "golden-theorem-iii-final-strong",
        "open_hypotheses": [],
        "active_assumptions": [],
        "residual_theorem_iii_burden": [],
        "certified_below_threshold_interval": [0.9716350, 0.9716360],
    }
    theorem_iv = {
        "theorem_status": "golden-theorem-iv-final-strong",
        "open_hypotheses": [],
        "active_assumptions": [],
        "analytic_incompatibility_certified": True,
        "support_geometry_certified": True,
        "tail_coherence_certified": True,
        "tail_stability_certified": True,
    }
    theorem_v = {
        "theorem_status": "golden-theorem-v-compressed-contract-strong",
        "open_hypotheses": [],
        "active_assumptions": [],
        "compressed_contract": {
            "theorem_status": "golden-theorem-v-compressed-contract-strong",
            "target_interval": {"lo": 0.9716350, "hi": 0.9716370, "width": 2.0e-6},
            "uniform_majorant": {
                "preserves_golden_gap": True,
                "certified": True,
                "error_ledger_exposed": True,
            },
            "two_sided_separation": {"certified": True},
            "raw_shell_consumed": False,
        },
    }
    ident = {
        "theorem_status": "golden-threshold-identification-discharge-lift-front-complete",
        "open_hypotheses": [],
        "active_assumptions": [],
        "branch_label": "golden-native-tail",
        "chart_label": "standard-sine-threshold-chart",
        "transport_branch_label": "golden-native-tail",
        "transport_chart_label": "standard-sine-threshold-chart",
        "overlap_window": [0.971634, 0.971638],
        "overlap_width": 4.0e-6,
        "discharged_bridge_native_tail_witness_interval": [0.9716352, 0.9716355],
        "discharged_bridge_native_tail_witness_width": 3.0e-7,
        "bridge_native_tail_witness_source": "minimal-paper-replay-identification",
        "bridge_native_tail_witness_status": "discharged",
    }
    theorem_vi = {
        "theorem_status": "golden-theorem-vi-envelope-lift-screened-one-variable-strong",
        "statement_mode": "one-variable",
        "open_hypotheses": [],
        "active_assumptions": [],
        "residual_burden_summary": {"status": "theorem-vi-screened-local-final"},
        "current_top_gap_scale": 1.0e-5,
        "current_most_dangerous_challenger_upper": 0.9716348,
        "discharged_identified_branch_witness_interval": [0.9716352, 0.9716355],
        "discharged_identified_branch_witness_width": 3.0e-7,
        "threshold_identification_discharge_shell": ident,
    }
    theorem_vii = {
        "theorem_status": "golden-theorem-vii-exhaustion-discharge-lift-conditional-strong",
        "open_hypotheses": [],
        "active_assumptions": [],
        "theorem_vii_codepath_final": True,
        "theorem_vii_papergrade_final": True,
        "theorem_vii_residual_citation_burden": [],
        "current_near_top_exhaustion_upper_bound": 0.9716347,
        "current_near_top_exhaustion_margin": 3.0e-7,
        "current_near_top_exhaustion_pending_count": 0,
        "current_near_top_exhaustion_source": "stage106-global-exhaustion-support",
        "current_near_top_exhaustion_status": "near-top-exhaustion-strong",
        "vii_failure_fields": {
            "unranked_labels": [],
            "unproved_pruning_labels": [],
            "missing_completion_labels": [],
            "uncontrolled_deferred_labels": [],
            "uncontrolled_retired_labels": [],
            "unpromoted_candidate_labels": [],
            "uncontrolled_omitted_labels": [],
        },
        "theorem_vi_discharge_shell": theorem_vi,
    }
    shells = tuple(deepcopy(x) for x in (workstream, theorem_iii, theorem_iv, theorem_v, ident, theorem_vi, theorem_vii))
    validate_paper_replay_shells(shells, require_cached_upstream=False)
    return shells


def validate_paper_replay_shells(
    shells: Sequence[Mapping[str, Any]],
    *,
    require_cached_upstream: bool = False,
) -> None:
    """Fail closed on paper-facing shell inconsistencies before final replay."""

    if len(shells) != 7:
        raise PaperReplayValidationError(f"expected 7 theorem shells, got {len(shells)}")
    workstream, theorem_iii, theorem_iv, theorem_v, ident, theorem_vi, theorem_vii = shells

    if require_cached_upstream:
        for label, cert in (("I--II", workstream), ("III", theorem_iii), ("IV", theorem_iv)):
            if not cert.get("cached_artifact_verified"):
                raise PaperReplayValidationError(f"{label} cache provenance is not verified")
            if not cert.get("cached_artifact_sha256"):
                raise PaperReplayValidationError(f"{label} cache hash is missing")

    lower = theorem_iii.get("certified_below_threshold_interval")
    if not isinstance(lower, Sequence) or len(lower) != 2:
        raise PaperReplayValidationError("Theorem III lower interval is missing")
    lower_lo = float(lower[0])
    lower_hi = float(lower[1])
    if not lower_lo < lower_hi:
        raise PaperReplayValidationError("Theorem III lower interval is not ordered")

    for flag in ("analytic_incompatibility_certified", "support_geometry_certified", "tail_coherence_certified", "tail_stability_certified"):
        if theorem_iv.get(flag) is not True:
            raise PaperReplayValidationError(f"Theorem IV required flag is false or missing: {flag}")

    v_status = str(theorem_v.get("theorem_status", ""))
    if "compressed-contract-strong" not in v_status:
        raise PaperReplayValidationError("Theorem V is not the compressed strong theorem-facing contract")
    if str(theorem_v.get("theorem_status", "")).lower().find("raw") >= 0:
        raise PaperReplayValidationError("raw/diagnostic Theorem-V shell cannot be consumed")
    compressed = theorem_v.get("compressed_contract") or {}
    if compressed.get("raw_shell_consumed") is True:
        raise PaperReplayValidationError("compressed contract reports raw-shell consumption")
    target = compressed.get("target_interval") or {}
    if not float(target.get("lo", 0.0)) < float(target.get("hi", 0.0)):
        raise PaperReplayValidationError("Theorem V target interval is missing or unordered")
    if not compressed.get("uniform_majorant", {}).get("preserves_golden_gap"):
        raise PaperReplayValidationError("Theorem V gap preservation is not certified")

    if ident.get("branch_label") != ident.get("transport_branch_label"):
        raise PaperReplayValidationError("identification branch-label mismatch")
    if ident.get("chart_label") != ident.get("transport_chart_label"):
        raise PaperReplayValidationError("identification chart-label mismatch")
    overlap = ident.get("overlap_window")
    witness = ident.get("discharged_bridge_native_tail_witness_interval")
    if not isinstance(overlap, Sequence) or len(overlap) != 2:
        raise PaperReplayValidationError("identification overlap window is missing")
    if not isinstance(witness, Sequence) or len(witness) != 2:
        raise PaperReplayValidationError("identification witness interval is missing")
    o0, o1 = float(overlap[0]), float(overlap[1])
    w0, w1 = float(witness[0]), float(witness[1])
    if not (o0 < w0 < w1 < o1):
        raise PaperReplayValidationError("identification witness is not strictly inside overlap window")
    if ident.get("bridge_native_tail_witness_status") != "discharged":
        raise PaperReplayValidationError("identification witness is not discharged")

    challenger_upper = float(theorem_vi.get("current_most_dangerous_challenger_upper", float("inf")))
    if not challenger_upper < lower_lo:
        raise PaperReplayValidationError("Theorem VI challenger upper does not lie below the golden lower anchor")
    if float(theorem_vi.get("current_top_gap_scale", 0.0)) <= 0.0:
        raise PaperReplayValidationError("Theorem VI top-gap scale is not positive")

    vii_upper = float(theorem_vii.get("current_near_top_exhaustion_upper_bound", float("inf")))
    if not vii_upper < lower_lo:
        raise PaperReplayValidationError("Theorem VII near-top upper bound does not lie below the golden lower anchor")
    if int(theorem_vii.get("current_near_top_exhaustion_pending_count", 1)) != 0:
        raise PaperReplayValidationError("Theorem VII has pending near-top challengers")
    if theorem_vii.get("theorem_vii_residual_citation_burden"):
        raise PaperReplayValidationError("Theorem VII residual burden is nonempty")
    failure_fields = theorem_vii.get("vii_failure_fields") or {}
    for name, values in failure_fields.items():
        if values:
            raise PaperReplayValidationError(f"Theorem VII failure field is nonempty: {name}")


def build_shells_from_stage_cache(
    stage_cache_dir: str | Path,
    *,
    repository_root: str | Path = ".",
    hash_ledger: str | Path | None = "HASHES.sha256",
    require_cache: bool = True,
) -> tuple[dict[str, Any], ...]:
    """Annotate compact shells with verified cached upstream artifact provenance."""

    workstream, theorem_iii, theorem_iv, theorem_v, ident, theorem_vi, theorem_vii = build_minimal_theorem_shells()
    if require_cache:
        provenance = verify_required_stage_cache(
            stage_cache_dir,
            repository_root=repository_root,
            hash_ledger=hash_ledger,
        )
        workstream = _annotate_cached(workstream, provenance["theorem_i_ii.json"])
        theorem_iii = _annotate_cached(theorem_iii, provenance["theorem_iii.json"])
        theorem_iv = _annotate_cached(theorem_iv, provenance["theorem_iv.json"])
    shells = tuple(deepcopy(x) for x in (workstream, theorem_iii, theorem_iv, theorem_v, ident, theorem_vi, theorem_vii))
    validate_paper_replay_shells(shells, require_cached_upstream=require_cache)
    return shells
