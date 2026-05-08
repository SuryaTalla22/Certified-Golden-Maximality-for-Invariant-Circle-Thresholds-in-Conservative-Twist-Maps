"""Phase 5F-b certificate-hash binding utilities for Track B / Theorem III.

This corrective phase patches the Phase 5F formal-attachment candidate so that
it explicitly binds itself to the exact Phase 5D certificate scaffold file by a
byte-level SHA256 hash.  It remains intentionally fail-closed: the binding is a
metadata/integrity repair only, not theorem-facing formal evidence.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

getcontext().prec = 80

HASH_BINDING_SCHEMA = "theorem_iii_trackb_phase5fb_hash_binding_summary_v1"
REPLAY_SCHEMA = "theorem_iii_trackb_phase5fb_hash_binding_replay_v1"
COMPACT_SCHEMA = "theorem_iii_trackb_phase5fb_compact_report_v1"

REQUIRED_FORMAL_EVIDENCE_KEYS = [
    "formal_interval_backend",
    "independent_replay_passed",
    "outward_rounded_residual_proof",
    "small_divisor_proof",
    "cohomology_inverse_proof",
    "frame_reducibility_proof",
    "nonlinear_bound_proof",
    "tail_bound_proof",
    "branch_chart_compatibility_proof",
    "final_graph_consumption_proof",
]


def _read_json(path: str | os.PathLike[str]) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | os.PathLike[str], payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def sha256_file(path: str | os.PathLike[str]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_payload(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        y = float(x)
        if math.isfinite(y):
            return y
    except Exception:
        pass
    return default


def _formal_evidence_false(formal_evidence: Mapping[str, Any]) -> Tuple[List[str], List[str], List[str]]:
    """Return (missing_keys, true_flags, false_flags) for required evidence keys."""
    missing: List[str] = []
    true_flags: List[str] = []
    false_flags: List[str] = []
    for key in REQUIRED_FORMAL_EVIDENCE_KEYS:
        if key not in formal_evidence:
            missing.append(key)
        elif bool(formal_evidence.get(key)):
            true_flags.append(key)
        else:
            false_flags.append(key)
    return missing, true_flags, false_flags


def bind_certificate_hash(
    *,
    certificate_path: str | os.PathLike[str],
    attachment_path: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    force: bool = False,
) -> Dict[str, Any]:
    """Patch a Phase 5F candidate attachment with the top-level certificate SHA256.

    The Phase 5E gate expects `certificate_sha256` at the top level.  The Phase
    5F candidate already carried the same value under `source_hashes`, but not
    at the top level.  This function makes the binding explicit and writes a new
    candidate file, preserving fail-closed formal-evidence flags.
    """
    certificate_path = str(certificate_path)
    attachment_path = str(attachment_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_attachment = out_dir / "phase5f_formal_interval_attachment_CANDIDATE_HASH_BOUND.json"
    out_summary = out_dir / "phase5fb_hash_binding_summary.json"
    if out_attachment.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file without --force: {out_attachment}")

    attachment = _read_json(attachment_path)
    cert_hash = sha256_file(certificate_path)
    old_source_hash = None
    if isinstance(attachment.get("source_hashes"), Mapping):
        old_source_hash = attachment["source_hashes"].get("certificate_sha256")

    patched = copy.deepcopy(attachment)
    patched["certificate_sha256"] = cert_hash
    patched["certificate_hash"] = cert_hash  # compatibility alias for human inspection
    patched["certificate_binding"] = {
        "schema": "theorem_iii_trackb_phase5fb_certificate_binding_v1",
        "algorithm": "sha256",
        "hash_type": "byte_stream_sha256",
        "certificate_path": certificate_path,
        "certificate_sha256": cert_hash,
        "binding_status": "bound_to_phase5d_scaffold",
        "purpose": "Allow Phase 5E to verify that this attachment belongs to the exact scaffold being gated.",
    }
    source_hashes = dict(patched.get("source_hashes", {}) or {})
    source_hashes["certificate_sha256"] = cert_hash
    patched["source_hashes"] = source_hashes
    source_paths = dict(patched.get("source_paths", {}) or {})
    source_paths["certificate_path"] = certificate_path
    patched["source_paths"] = source_paths
    patched["phase5fb_hash_binding"] = {
        "schema": HASH_BINDING_SCHEMA,
        "status": "hash-bound-candidate-written",
        "input_attachment_path": attachment_path,
        "output_attachment_path": str(out_attachment),
        "certificate_path": certificate_path,
        "certificate_sha256": cert_hash,
        "old_source_hash_matches": bool(old_source_hash) and old_source_hash == cert_hash,
    }
    # Recompute a payload hash after patching.  Keep old hash if present for audit trail.
    if "attachment_sha256" in patched:
        patched["previous_attachment_sha256_before_hash_binding"] = patched.get("attachment_sha256")
    patched["attachment_sha256"] = sha256_payload({k: v for k, v in patched.items() if k != "attachment_sha256"})

    formal_evidence = patched.get("formal_evidence", {}) if isinstance(patched, Mapping) else {}
    missing, true_flags, false_flags = _formal_evidence_false(formal_evidence if isinstance(formal_evidence, Mapping) else {})

    summary = {
        "schema": HASH_BINDING_SCHEMA,
        "status": "phase5fb-certificate-hash-binding-complete",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "promotion_ready": False,
        "certificate_path": certificate_path,
        "input_attachment_path": attachment_path,
        "hash_bound_attachment_path": str(out_attachment),
        "certificate_sha256": cert_hash,
        "old_source_hash": old_source_hash,
        "old_source_hash_matches": bool(old_source_hash) and old_source_hash == cert_hash,
        "top_level_certificate_sha256_written": True,
        "source_hashes_certificate_sha256_written": True,
        "required_formal_evidence_keys": REQUIRED_FORMAL_EVIDENCE_KEYS,
        "missing_formal_evidence_flags": missing + true_flags,
        "formal_evidence_true_flags": true_flags,
        "formal_evidence_false_flags": false_flags,
        "expected_phase5e_decision_after_patch": "REJECT_FAIL_CLOSED_WITH_ONLY_FORMAL_EVIDENCE_FLAGS_FAILED",
        "open_requirements_for_promotion": [
            "Attach an independently verified formal interval backend record.",
            "Set required formal evidence flags to true only after independent formal replay exists.",
            "Rerun Phase 5E and require theorem promotion to remain fail-closed until all formal flags and thresholds pass.",
        ],
        "selected_constants": patched.get("selected_constants", {}),
    }

    _write_json(out_attachment, patched)
    _write_json(out_summary, summary)
    return summary


def replay_hash_binding(
    *,
    certificate_path: str | os.PathLike[str],
    attachment_path: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    force: bool = False,
    required_min_lower_anchor_k: float = 0.971635,
    require_nu: Optional[float] = 1.001,
    require_radius: Optional[float] = 3e-5,
    require_cutoff: Optional[str] = "full",
    require_tail_start: Optional[float] = 0.90,
    min_relative_margin: float = 0.25,
    max_z: float = 0.5,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase5fb_hash_binding_replay_summary.json"
    if out_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file without --force: {out_path}")

    attachment = _read_json(attachment_path)
    cert_hash = sha256_file(certificate_path)
    constants = attachment.get("selected_constants", {}) if isinstance(attachment, Mapping) else {}
    formal_evidence = attachment.get("formal_evidence", {}) if isinstance(attachment, Mapping) else {}
    missing, true_flags, false_flags = _formal_evidence_false(formal_evidence if isinstance(formal_evidence, Mapping) else {})

    checks: List[Dict[str, Any]] = []
    def add(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    top_hash = attachment.get("certificate_sha256")
    alias_hash = attachment.get("certificate_hash")
    source_hash = None
    if isinstance(attachment.get("source_hashes"), Mapping):
        source_hash = attachment["source_hashes"].get("certificate_sha256")
    binding_hash = None
    if isinstance(attachment.get("certificate_binding"), Mapping):
        binding_hash = attachment["certificate_binding"].get("certificate_sha256")

    add("schema", attachment.get("schema") == "theorem_iii_trackb_phase5e_formal_interval_attachment_v1", attachment.get("schema"))
    add("diagnostic_only_true", attachment.get("diagnostic_only") is True, attachment.get("diagnostic_only"))
    add("theorem_facing_false", attachment.get("theorem_facing") is False, attachment.get("theorem_facing"))
    add("promotion_allowed_false", attachment.get("promotion_allowed") is False, attachment.get("promotion_allowed"))
    add("formal_attachment_ok_false", attachment.get("formal_attachment_ok") is False, attachment.get("formal_attachment_ok"))
    add("top_level_certificate_sha256_matches", bool(top_hash) and top_hash == cert_hash, {"attached": top_hash, "computed": cert_hash})
    add("certificate_hash_alias_matches", bool(alias_hash) and alias_hash == cert_hash, {"attached": alias_hash, "computed": cert_hash})
    add("source_hash_certificate_sha256_matches", bool(source_hash) and source_hash == cert_hash, {"attached": source_hash, "computed": cert_hash})
    add("certificate_binding_hash_matches", bool(binding_hash) and binding_hash == cert_hash, {"attached": binding_hash, "computed": cert_hash})
    add("all_required_formal_evidence_keys_present", not missing, missing)
    add("required_formal_evidence_flags_false_for_now", not true_flags and len(false_flags) == len(REQUIRED_FORMAL_EVIDENCE_KEYS), {"true_flags": true_flags, "false_count": len(false_flags)})
    add("anchor_meets_min", _safe_float(constants.get("K"), -float("inf")) >= required_min_lower_anchor_k - 5e-13, constants.get("K"))
    if require_nu is not None:
        add("nu_matches", abs(_safe_float(constants.get("nu")) - float(require_nu)) < 5e-13, constants.get("nu"))
    if require_radius is not None:
        add("radius_matches", abs(_safe_float(constants.get("radius")) - float(require_radius)) < 5e-13, constants.get("radius"))
    if require_cutoff is not None:
        add("cutoff_matches", str(constants.get("cutoff_spec")) == str(require_cutoff), constants.get("cutoff_spec"))
    if require_tail_start is not None:
        add("tail_start_matches", abs(_safe_float(constants.get("tail_start_frac")) - float(require_tail_start)) < 5e-13, constants.get("tail_start_frac"))
    add("relative_margin_threshold", _safe_float(constants.get("radii_relative_margin_interval_lower"), -float("inf")) >= min_relative_margin, constants.get("radii_relative_margin_interval_lower"))
    add("Z_below_threshold", _safe_float(constants.get("Z_interval_upper"), float("inf")) <= max_z, constants.get("Z_interval_upper"))

    failed_checks = [c["name"] for c in checks if not c["ok"]]
    passed = not failed_checks
    summary = {
        "schema": REPLAY_SCHEMA,
        "status": "phase5fb-hash-binding-replay-complete" if passed else "phase5fb-hash-binding-replay-failed",
        "passed": passed,
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "promotion_ready": False,
        "certificate_path": str(certificate_path),
        "attachment_path": str(attachment_path),
        "certificate_sha256_computed": cert_hash,
        "failed_checks": failed_checks,
        "checks": checks,
        "missing_formal_evidence_flags": missing + true_flags,
        "expected_phase5e_decision_after_patch": "REJECT_FAIL_CLOSED_WITH_ONLY_FORMAL_EVIDENCE_FLAGS_FAILED",
        "selected_constants": constants,
    }
    _write_json(out_path, summary)
    return summary


def summarize_phase5fb(summary_path: str | os.PathLike[str]) -> Dict[str, Any]:
    payload = _read_json(summary_path)
    # Accept either binding summary or replay summary and normalize.
    constants = payload.get("selected_constants", {}) if isinstance(payload, Mapping) else {}
    compact = {
        "schema": COMPACT_SCHEMA,
        "status": payload.get("status"),
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "promotion_ready": False,
        "formal_attachment_ok": False,
        "certificate_sha256": payload.get("certificate_sha256") or payload.get("certificate_sha256_computed"),
        "hash_bound_attachment_path": payload.get("hash_bound_attachment_path") or payload.get("attachment_path"),
        "passed": payload.get("passed", payload.get("top_level_certificate_sha256_written", False)),
        "failed_checks": payload.get("failed_checks", []),
        "missing_formal_evidence_flags": payload.get("missing_formal_evidence_flags", []),
        "formal_evidence_true_flags": payload.get("formal_evidence_true_flags", []),
        "expected_phase5e_decision_after_patch": payload.get("expected_phase5e_decision_after_patch"),
        "selected_constants": {
            "K": constants.get("K"),
            "M": constants.get("M"),
            "nu": constants.get("nu"),
            "radius": constants.get("radius"),
            "cutoff_spec": constants.get("cutoff_spec"),
            "tail_start_frac": constants.get("tail_start_frac"),
            "Y_interval_upper": constants.get("Y_interval_upper"),
            "Z_interval_upper": constants.get("Z_interval_upper"),
            "Q_interval_upper": constants.get("Q_interval_upper"),
            "radii_margin_interval_lower": constants.get("radii_margin_interval_lower"),
            "radii_relative_margin_interval_lower": constants.get("radii_relative_margin_interval_lower"),
            "small_divisor_min_denominator_lower": constants.get("small_divisor_min_denominator_lower"),
            "cohomology_inverse_linf_resolved_upper": constants.get("cohomology_inverse_linf_resolved_upper"),
        },
    }
    return compact


__all__ = [
    "bind_certificate_hash",
    "replay_hash_binding",
    "summarize_phase5fb",
    "sha256_file",
]
