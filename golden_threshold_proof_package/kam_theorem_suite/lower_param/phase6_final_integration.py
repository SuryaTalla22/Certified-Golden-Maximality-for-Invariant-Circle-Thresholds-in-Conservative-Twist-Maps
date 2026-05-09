"""Phase 6 final integration for Theorem III Track B lower-anchor certificate.

This module deliberately avoids generating the large full-proof artifacts.  It
performs the small, replayable integration step that replaces the obsolete
Theorem III artifact with the promoted Phase 5K lower-anchor certificate and
emits a regeneration manifest for downstream artifacts.

The phase is intentionally conservative:
  * it requires a Phase 5E `PROMOTE` summary for the promoted attachment;
  * it checks that every required formal evidence flag is true;
  * it hash-binds copied artifacts to the original inputs;
  * it marks the final Theorem III object as theorem-facing but records that it
    is a direct lower-anchor certificate, not a parameter-interval certificate;
  * it does not attempt to regenerate the large theorem graph/audit artifacts.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

REQUIRED_FORMAL_FLAGS = [
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

SCHEMA_FINAL_ARTIFACT = "theorem_iii_trackb_phase6_final_lower_anchor_certificate_v1"
SCHEMA_ASSEMBLY_SUMMARY = "theorem_iii_trackb_phase6_final_integration_summary_v1"
SCHEMA_REPLAY_SUMMARY = "theorem_iii_trackb_phase6_final_replay_summary_v1"
SCHEMA_COMPACT = "theorem_iii_trackb_phase6_compact_report_v1"
SCHEMA_REGEN_MANIFEST = "theorem_iii_trackb_phase6_regeneration_manifest_v1"


def load_json(path: str | os.PathLike[str]) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, float):
        if math.isfinite(obj):
            return obj
        return None
    return obj


def write_json(path: str | os.PathLike[str], payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_json_safe(payload), f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    os.replace(tmp, path)


def sha256_file(path: str | os.PathLike[str]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def get_path(d: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, Mapping) or k not in cur:
            return default
        cur = cur[k]
    return cur


def formal_flag(attachment: Mapping[str, Any], key: str) -> bool:
    # Accept the canonical nested location plus earlier safe legacy locations.
    fe = attachment.get("formal_evidence")
    if isinstance(fe, Mapping) and fe.get(key) is True:
        return True
    if attachment.get(key) is True:
        return True
    flags = attachment.get("formal_evidence_true_flags")
    if isinstance(flags, list) and key in flags:
        return True
    return False


def _finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def _copy_with_hash(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> Dict[str, Any]:
    srcp = Path(src)
    dstp = Path(dst)
    dstp.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(srcp, dstp)
    return {
        "source_path": str(srcp),
        "copied_path": str(dstp),
        "sha256": sha256_file(dstp),
        "bytes": dstp.stat().st_size,
    }


def validate_promoted_inputs(
    certificate: Mapping[str, Any],
    promoted_attachment: Mapping[str, Any],
    phase5e_summary: Mapping[str, Any],
    *,
    required_min_lower_anchor_k: float,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    min_relative_margin: float,
    max_z: float,
) -> Tuple[List[Dict[str, Any]], bool]:
    cert_k = certificate.get("lower_anchor_K") or get_path(certificate, "anchor", "lower_anchor_K")
    # Phase 5D scaffold often stores target information under lower_anchor_claim.
    if cert_k is None:
        cert_k = get_path(certificate, "lower_anchor_claim", "lower_anchor_K")
    constants = promoted_attachment.get("selected_constants", {})
    if not constants:
        constants = phase5e_summary.get("selected_constants", {})

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("phase5e_decision_promote", phase5e_summary.get("decision") == "PROMOTE", phase5e_summary.get("decision"))
    add("phase5e_formal_attachment_ok", phase5e_summary.get("formal_attachment_ok") is True, phase5e_summary.get("formal_attachment_ok"))
    add("phase5e_theorem_replay_accepted", phase5e_summary.get("theorem_replay_accepted") is True, phase5e_summary.get("theorem_replay_accepted"))
    add("phase5e_theorem_facing", phase5e_summary.get("theorem_facing") is True, phase5e_summary.get("theorem_facing"))
    add("phase5e_promotion_allowed", phase5e_summary.get("promotion_allowed") is True, phase5e_summary.get("promotion_allowed"))
    add("phase5e_no_failed_attachment_checks", not phase5e_summary.get("failed_formal_attachment_checks"), phase5e_summary.get("failed_formal_attachment_checks"))
    add("phase5e_negative_controls_passed", phase5e_summary.get("negative_controls_passed") is True, phase5e_summary.get("negative_controls_passed"))

    add("attachment_theorem_facing", promoted_attachment.get("theorem_facing") is True, promoted_attachment.get("theorem_facing"))
    add("attachment_promotion_allowed", promoted_attachment.get("promotion_allowed") is True, promoted_attachment.get("promotion_allowed"))
    add("attachment_formal_attachment_ok", promoted_attachment.get("formal_attachment_ok") is True, promoted_attachment.get("formal_attachment_ok"))

    missing = [k for k in REQUIRED_FORMAL_FLAGS if not formal_flag(promoted_attachment, k)]
    add("all_required_formal_flags_true", len(missing) == 0, missing)

    cert_hash_actual = None
    # If assembly is run from files, the caller will add an external hash check.  Here
    # check only reported cross-reference shape.
    reported_cert_hash = promoted_attachment.get("certificate_sha256") or get_path(promoted_attachment, "binding", "certificate_sha256")
    add("attachment_has_certificate_sha256", isinstance(reported_cert_hash, str) and len(reported_cert_hash) == 64, reported_cert_hash)

    add("lower_anchor_meets_required", float(constants.get("K", cert_k or -math.inf)) >= required_min_lower_anchor_k, constants.get("K", cert_k))
    add("nu_matches", abs(float(constants.get("nu", math.nan)) - require_nu) <= 1e-15, constants.get("nu"))
    add("radius_matches", abs(float(constants.get("radius", math.nan)) - require_radius) <= 1e-18, constants.get("radius"))
    add("cutoff_matches", str(constants.get("cutoff_spec")) == str(require_cutoff), constants.get("cutoff_spec"))
    add("tail_start_matches", abs(float(constants.get("tail_start_frac", math.nan)) - require_tail_start) <= 1e-15, constants.get("tail_start_frac"))
    add("relative_margin_threshold", float(constants.get("radii_relative_margin_interval_lower", -math.inf)) >= min_relative_margin, constants.get("radii_relative_margin_interval_lower"))
    add("Z_threshold", float(constants.get("Z_interval_upper", math.inf)) <= max_z, constants.get("Z_interval_upper"))
    add("positive_margin", float(constants.get("radii_margin_interval_lower", -math.inf)) > 0.0, constants.get("radii_margin_interval_lower"))
    add("finite_YZQ", all(_finite_number(constants.get(k)) for k in ["Y_interval_upper", "Z_interval_upper", "Q_interval_upper"]), [constants.get(k) for k in ["Y_interval_upper", "Z_interval_upper", "Q_interval_upper"]])

    return checks, all(c["ok"] for c in checks)


def build_regeneration_manifest(
    *,
    final_artifact_path: str,
    theorem_i_artifact: Optional[str],
    theorem_ii_artifact: Optional[str],
    theorem_iv_artifact: Optional[str],
    output_root: str,
    downstream_output_root: str,
    commands_file: str,
) -> Dict[str, Any]:
    """Create a regeneration manifest without executing large downstream tasks."""
    theorem_inputs = {
        "theorem_I_artifact": theorem_i_artifact,
        "theorem_II_artifact": theorem_ii_artifact,
        "theorem_III_artifact": final_artifact_path,
        "theorem_IV_artifact": theorem_iv_artifact,
    }
    manifest = {
        "schema": SCHEMA_REGEN_MANIFEST,
        "status": "phase6-regeneration-manifest-created",
        "does_not_generate_large_artifacts": True,
        "theorem_inputs": theorem_inputs,
        "theorem_iii_replacement_policy": {
            "obsolete_theorem_iii_artifact_should_not_be_used": True,
            "replacement_artifact": final_artifact_path,
            "replacement_kind": "promoted_direct_lower_anchor_trackB_certificate",
        },
        "downstream_output_root": downstream_output_root,
        "recommended_large_artifacts_to_regenerate": [
            "global theorem graph / theorem dependency manifest",
            "combined proof audit summary",
            "paper-facing certificate index",
            "final Theorem III closure report",
            "any final PDF/LaTeX tables that quote Theorem III constants",
        ],
        "commands_file": commands_file,
        "notes": [
            "This manifest intentionally does not run the large generators.",
            "Run the emitted shell script after mapping the command placeholders to the repository's existing generators if the exact final artifact scripts have different names.",
            "Theorem III should be consumed only through the Phase 6 final artifact path recorded here.",
        ],
    }
    return manifest


def write_regeneration_commands(
    path: str | os.PathLike[str], *, final_artifact_path: str, theorem_i_artifact: Optional[str], theorem_ii_artifact: Optional[str], theorem_iv_artifact: Optional[str], downstream_output_root: str) -> None:
    """Emit a safe shell script of commands/user prompts for regenerating large artifacts.

    The script is deliberately conservative: it prints the selected paths and searches
    for likely existing generators, rather than inventing a repo-specific command that
    might be wrong.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    txt = f'''#!/usr/bin/env bash
set -euo pipefail

# Phase 6 downstream regeneration helper.
# This script does NOT guess repo-specific final generator arguments.  It prints the
# validated promoted Theorem III path and lists likely generator scripts to run.

export THEOREM_I_ARTIFACT={json.dumps(theorem_i_artifact or "")}
export THEOREM_II_ARTIFACT={json.dumps(theorem_ii_artifact or "")}
export THEOREM_III_ARTIFACT={json.dumps(final_artifact_path)}
export THEOREM_IV_ARTIFACT={json.dumps(theorem_iv_artifact or "")}
export PHASE6_DOWNSTREAM_OUT={json.dumps(downstream_output_root)}

mkdir -p "$PHASE6_DOWNSTREAM_OUT"

echo "Theorem I artifact:   $THEOREM_I_ARTIFACT"
echo "Theorem II artifact:  $THEOREM_II_ARTIFACT"
echo "Theorem III artifact: $THEOREM_III_ARTIFACT"
echo "Theorem IV artifact:  $THEOREM_IV_ARTIFACT"
echo "Downstream out:       $PHASE6_DOWNSTREAM_OUT"

echo
echo "Likely final-integration/regeneration scripts in this repo:"
find scripts -type f \
  \( -iname '*theorem*final*.py' -o -iname '*global*replay*.py' -o -iname '*proof*graph*.py' -o -iname '*certificate*index*.py' -o -iname '*audit*summary*.py' -o -iname '*paper*certificate*.py' \) \
  | sort || true

echo
echo "Suggested workflow:"
echo "  1. Replace the old Theorem III input with: $THEOREM_III_ARTIFACT"
echo "  2. Re-run the repository's existing full theorem graph / proof-audit generators."
echo "  3. Verify generated artifacts cite K=0.971635, nu=1.001, radius=3e-5, cutoff=full."
echo "  4. Verify no generated artifact references the obsolete Theorem III artifact."
'''
    p.write_text(txt, encoding="utf-8")
    os.chmod(p, 0o755)


def assemble_phase6_final_integration(
    *,
    certificate_path: str,
    promoted_attachment_path: str,
    phase5e_summary_path: str,
    theorem_i_artifact: Optional[str],
    theorem_ii_artifact: Optional[str],
    theorem_iv_artifact: Optional[str],
    required_min_lower_anchor_k: float,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    min_relative_margin: float,
    max_z: float,
    downstream_output_root: str,
    out_dir: str,
    force: bool = False,
) -> Dict[str, Any]:
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()) and not force:
        raise FileExistsError(f"Output directory exists and is nonempty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    certificate = load_json(certificate_path)
    promoted = load_json(promoted_attachment_path)
    phase5e = load_json(phase5e_summary_path)

    checks, passed = validate_promoted_inputs(
        certificate,
        promoted,
        phase5e,
        required_min_lower_anchor_k=required_min_lower_anchor_k,
        require_nu=require_nu,
        require_radius=require_radius,
        require_cutoff=require_cutoff,
        require_tail_start=require_tail_start,
        min_relative_margin=min_relative_margin,
        max_z=max_z,
    )

    cert_sha = sha256_file(certificate_path)
    attachment_reported_hash = promoted.get("certificate_sha256") or get_path(promoted, "binding", "certificate_sha256")
    checks.append({
        "name": "attachment_hash_matches_certificate_file",
        "ok": attachment_reported_hash == cert_sha,
        "detail": {"reported": attachment_reported_hash, "actual": cert_sha},
    })
    passed = passed and (attachment_reported_hash == cert_sha)

    constants = promoted.get("selected_constants", phase5e.get("selected_constants", {}))
    local_copy_dir = out / "inputs_copied"
    copied_certificate = _copy_with_hash(certificate_path, local_copy_dir / "theorem_iii_phase5d_certificate_scaffold.json")
    copied_attachment = _copy_with_hash(promoted_attachment_path, local_copy_dir / "theorem_iii_phase5k_promoted_attachment.json")
    copied_phase5e = _copy_with_hash(phase5e_summary_path, local_copy_dir / "theorem_iii_phase5e_final_promotion_summary.json")

    final_artifact = {
        "schema": SCHEMA_FINAL_ARTIFACT,
        "status": "phase6-final-theorem-iii-lower-anchor-artifact-assembled" if passed else "phase6-final-theorem-iii-lower-anchor-artifact-blocked",
        "passed": passed,
        "theorem": "III",
        "certificate_kind": "direct_lower_anchor_persistence_certificate",
        "track": "TrackB",
        "theorem_facing": bool(passed),
        "promotion_allowed": bool(passed),
        "consumption_scope": {
            "direct_lower_anchor_only": True,
            "does_not_claim_parameter_interval": True,
            "does_not_claim_mesh_corridor": True,
            "replacement_for_obsolete_theorem_iii_artifact": True,
        },
        "certificate_sha256": cert_sha,
        "promoted_attachment_sha256": sha256_file(promoted_attachment_path),
        "phase5e_summary_sha256": sha256_file(phase5e_summary_path),
        "selected_constants": constants,
        "formal_evidence_true_flags": [k for k in REQUIRED_FORMAL_FLAGS if formal_flag(promoted, k)],
        "failed_checks": [c for c in checks if not c["ok"]],
        "checks": checks,
        "source_paths": {
            "certificate": certificate_path,
            "promoted_attachment": promoted_attachment_path,
            "phase5e_summary": phase5e_summary_path,
            "theorem_I_artifact": theorem_i_artifact,
            "theorem_II_artifact": theorem_ii_artifact,
            "theorem_IV_artifact": theorem_iv_artifact,
        },
        "copied_inputs": {
            "certificate": copied_certificate,
            "promoted_attachment": copied_attachment,
            "phase5e_summary": copied_phase5e,
        },
    }

    final_artifact_path = out / "theorem_iii_trackb_PHASE6_FINAL_LOWER_ANCHOR_CERTIFICATE.json"
    write_json(final_artifact_path, final_artifact)

    commands_path = out / "phase6_regenerate_large_artifacts_PLAN.sh"
    write_regeneration_commands(
        commands_path,
        final_artifact_path=str(final_artifact_path),
        theorem_i_artifact=theorem_i_artifact,
        theorem_ii_artifact=theorem_ii_artifact,
        theorem_iv_artifact=theorem_iv_artifact,
        downstream_output_root=downstream_output_root,
    )

    regen_manifest = build_regeneration_manifest(
        final_artifact_path=str(final_artifact_path),
        theorem_i_artifact=theorem_i_artifact,
        theorem_ii_artifact=theorem_ii_artifact,
        theorem_iv_artifact=theorem_iv_artifact,
        output_root=str(out),
        downstream_output_root=downstream_output_root,
        commands_file=str(commands_path),
    )
    regen_manifest_path = out / "phase6_regeneration_manifest.json"
    write_json(regen_manifest_path, regen_manifest)

    replacement_manifest = {
        "schema": "theorem_iii_trackb_phase6_replacement_manifest_v1",
        "status": "theorem-iii-replacement-ready" if passed else "theorem-iii-replacement-blocked",
        "replace_old_theorem_iii_artifact": bool(passed),
        "new_theorem_iii_artifact": str(final_artifact_path),
        "old_theorem_iii_artifact_policy": "ignore/delete/do-not-consume",
        "theorem_iii_lower_anchor_K": constants.get("K"),
        "branch_label": get_path(promoted, "branch_chart_component", "branch_label", default="golden_lower_anchor_direct_trackB"),
        "chart_label": get_path(promoted, "branch_chart_component", "chart_label", default="standard_sine_twist_map_parameterization_chart"),
        "notes": [
            "The previous Theorem III artifact was declared incorrect and must not be consumed.",
            "Downstream large artifacts should be regenerated after pointing to this replacement artifact.",
        ],
    }
    replacement_manifest_path = out / "theorem_iii_replacement_manifest.json"
    write_json(replacement_manifest_path, replacement_manifest)

    summary = {
        "schema": SCHEMA_ASSEMBLY_SUMMARY,
        "status": "phase6-final-integration-assembled" if passed else "phase6-final-integration-blocked",
        "passed": passed,
        "theorem_iii_final_artifact": str(final_artifact_path),
        "regeneration_manifest": str(regen_manifest_path),
        "replacement_manifest": str(replacement_manifest_path),
        "regeneration_commands": str(commands_path),
        "selected_constants": constants,
        "failed_checks": [c for c in checks if not c["ok"]],
        "checks": checks,
        "theorem_inputs": {
            "I": theorem_i_artifact,
            "II": theorem_ii_artifact,
            "III": str(final_artifact_path),
            "IV": theorem_iv_artifact,
        },
        "does_not_generate_large_artifacts": True,
    }
    summary_path = out / "phase6_final_integration_summary.json"
    write_json(summary_path, summary)
    summarize_phase6(str(summary_path), str(out / "phase6_compact_report.json"))
    return summary


def replay_phase6_final_integration(
    *,
    final_artifact_path: str,
    required_min_lower_anchor_k: float,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    min_relative_margin: float,
    max_z: float,
    theorem_i_artifact: Optional[str],
    theorem_ii_artifact: Optional[str],
    theorem_iv_artifact: Optional[str],
    out_dir: str,
    force: bool = False,
) -> Dict[str, Any]:
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()) and not force:
        raise FileExistsError(f"Output directory exists and is nonempty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    artifact = load_json(final_artifact_path)
    constants = artifact.get("selected_constants", {})
    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("schema", artifact.get("schema") == SCHEMA_FINAL_ARTIFACT, artifact.get("schema"))
    add("phase6_artifact_passed", artifact.get("passed") is True, artifact.get("passed"))
    add("theorem_facing_true", artifact.get("theorem_facing") is True, artifact.get("theorem_facing"))
    add("promotion_allowed_true", artifact.get("promotion_allowed") is True, artifact.get("promotion_allowed"))
    add("direct_lower_anchor_only", get_path(artifact, "consumption_scope", "direct_lower_anchor_only") is True, artifact.get("consumption_scope"))
    add("does_not_claim_parameter_interval", get_path(artifact, "consumption_scope", "does_not_claim_parameter_interval") is True, artifact.get("consumption_scope"))
    missing = [k for k in REQUIRED_FORMAL_FLAGS if k not in artifact.get("formal_evidence_true_flags", [])]
    add("all_formal_flags_carried", len(missing) == 0, missing)
    add("lower_anchor_meets_required", float(constants.get("K", -math.inf)) >= required_min_lower_anchor_k, constants.get("K"))
    add("nu_matches", abs(float(constants.get("nu", math.nan)) - require_nu) <= 1e-15, constants.get("nu"))
    add("radius_matches", abs(float(constants.get("radius", math.nan)) - require_radius) <= 1e-18, constants.get("radius"))
    add("cutoff_matches", str(constants.get("cutoff_spec")) == str(require_cutoff), constants.get("cutoff_spec"))
    add("tail_start_matches", abs(float(constants.get("tail_start_frac", math.nan)) - require_tail_start) <= 1e-15, constants.get("tail_start_frac"))
    add("relative_margin_threshold", float(constants.get("radii_relative_margin_interval_lower", -math.inf)) >= min_relative_margin, constants.get("radii_relative_margin_interval_lower"))
    add("Z_threshold", float(constants.get("Z_interval_upper", math.inf)) <= max_z, constants.get("Z_interval_upper"))
    add("positive_margin", float(constants.get("radii_margin_interval_lower", -math.inf)) > 0.0, constants.get("radii_margin_interval_lower"))
    for label, path in [("I", theorem_i_artifact), ("II", theorem_ii_artifact), ("IV", theorem_iv_artifact)]:
        if path:
            add(f"theorem_{label}_artifact_exists", Path(path).exists(), path)
        else:
            add(f"theorem_{label}_artifact_not_supplied", True, "not supplied; replay limited to Theorem III final artifact")

    passed = all(c["ok"] for c in checks)
    summary = {
        "schema": SCHEMA_REPLAY_SUMMARY,
        "status": "phase6-final-replay-passed" if passed else "phase6-final-replay-failed",
        "passed": passed,
        "final_artifact_path": final_artifact_path,
        "final_artifact_sha256": sha256_file(final_artifact_path),
        "selected_constants": constants,
        "failed_checks": [c for c in checks if not c["ok"]],
        "checks": checks,
        "theorem_inputs": {"I": theorem_i_artifact, "II": theorem_ii_artifact, "III": final_artifact_path, "IV": theorem_iv_artifact},
    }
    summary_path = out / "phase6_final_replay_summary.json"
    write_json(summary_path, summary)
    summarize_phase6(str(summary_path), str(out / "phase6_replay_compact_report.json"))
    return summary


def summarize_phase6(input_path: str, out_path: str) -> Dict[str, Any]:
    data = load_json(input_path)
    constants = data.get("selected_constants", {})
    compact = {
        "schema": SCHEMA_COMPACT,
        "source_summary": input_path,
        "status": data.get("status"),
        "passed": data.get("passed"),
        "failed_checks": data.get("failed_checks", []),
        "theorem_iii_final_artifact": data.get("theorem_iii_final_artifact") or data.get("final_artifact_path"),
        "regeneration_manifest": data.get("regeneration_manifest"),
        "regeneration_commands": data.get("regeneration_commands"),
        "does_not_generate_large_artifacts": data.get("does_not_generate_large_artifacts", False),
        "theorem_inputs": data.get("theorem_inputs"),
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
            "radii_lhs_interval_upper": constants.get("radii_lhs_interval_upper"),
            "radii_margin_interval_lower": constants.get("radii_margin_interval_lower"),
            "radii_relative_margin_interval_lower": constants.get("radii_relative_margin_interval_lower"),
            "small_divisor_min_denominator_lower": constants.get("small_divisor_min_denominator_lower"),
            "cohomology_inverse_linf_resolved_upper": constants.get("cohomology_inverse_linf_resolved_upper"),
        },
    }
    write_json(out_path, compact)
    return compact
