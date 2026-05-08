"""Phase 5H cohomology-inverse and frame/reducibility component candidates.

This phase extends the fail-closed Theorem III Track B formal attachment by
adding two additional replayable component candidates:

* cohomology_inverse_proof
* frame_reducibility_proof

It does not set the global formal backend or independent replay flags and it
must not make the certificate theorem-facing.  The Phase 5E promotion gate is
expected to continue rejecting until the remaining formal evidence flags are
supplied.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional
import json
import math
import os

import numpy as np

try:
    from kam_theorem_suite.lower_param.phase5g_formal_components import (
        REQUIRED_FORMAL_EVIDENCE_KEYS,
        canonical_file_sha256,
        read_json,
        write_json,
        load_seed_npz,
        small_divisor_scan,
        next_up,
    )
except Exception:  # pragma: no cover - import fallback only for isolated debugging
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
    raise

PHASE5H_TRUE_KEYS = ["cohomology_inverse_proof", "frame_reducibility_proof"]


def _as_float(x: Any, default: float = math.nan) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _finite_nonnegative(x: Any) -> bool:
    v = _as_float(x)
    return math.isfinite(v) and v >= 0.0


def _get_nested(d: Mapping[str, Any], *path: str, default: Any = None) -> Any:
    cur: Any = d
    for p in path:
        if not isinstance(cur, Mapping) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _ensure_formal_evidence(base: Mapping[str, Any]) -> Dict[str, bool]:
    fe = base.get("formal_evidence")
    if not isinstance(fe, Mapping):
        fe = {}
    out: Dict[str, bool] = {}
    for k in REQUIRED_FORMAL_EVIDENCE_KEYS:
        out[k] = bool(fe.get(k, False))
    return out


def _selected_constants(base: Mapping[str, Any], phase5c_summary: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    # Prefer the exact constants already carried by the attachment.  If absent,
    # fall back to the first Phase 5C candidate.
    for key in ["selected_constants", "constants", "selected_candidate"]:
        val = base.get(key)
        if isinstance(val, Mapping):
            return dict(val)
    if phase5c_summary and isinstance(phase5c_summary.get("top_candidates"), list) and phase5c_summary["top_candidates"]:
        return dict(phase5c_summary["top_candidates"][0])
    return {}


def _component_evidence(base: Mapping[str, Any]) -> Dict[str, Any]:
    val = base.get("formal_component_evidence")
    return dict(val) if isinstance(val, Mapping) else {}


def _small_divisor_object(base: Mapping[str, Any]) -> Dict[str, Any]:
    val = _get_nested(base, "formal_component_evidence", "small_divisor_proof", default=None)
    return dict(val) if isinstance(val, Mapping) else {}


def cohomology_inverse_proof_object(
    seed_npz: str | os.PathLike[str],
    selected: Mapping[str, Any],
    base_attachment: Mapping[str, Any],
    small_divisor_slack: float = 1e-14,
) -> Dict[str, Any]:
    """Build a replayable cohomology-inverse component from the small divisor scan.

    The resolved inverse for the first-difference cohomology operator is bounded
    by 1 / min_{1<=|k|<=N} 2|sin(pi k omega)|.  This component recomputes that
    finite scan and records the resulting upper bound, then compares it to the
    selected Phase 5C/5G constants.
    """
    seed = load_seed_npz(seed_npz)
    cutoff = int(_as_float(selected.get("cutoff_mode_native_units", seed["M"] // 2 - 1)))
    scan = small_divisor_scan(seed["omega"], cutoff=cutoff, slack=small_divisor_slack)
    existing = _small_divisor_object(base_attachment)
    selected_inverse = _as_float(
        selected.get("cohomology_inverse_linf_resolved_upper", selected.get("cohomology_inverse_upper")),
        default=math.inf,
    )
    selected_lower = _as_float(
        selected.get("small_divisor_min_denominator_lower", selected.get("small_divisor_lower")),
        default=0.0,
    )
    inverse_upper = next_up(max(scan["cohomology_inverse_linf_resolved_upper"], selected_inverse))
    lower_bound = min(
        scan["small_divisor_min_denominator_lower"],
        selected_lower if selected_lower > 0 else scan["small_divisor_min_denominator_lower"],
    )
    proof_ok = bool(
        math.isfinite(inverse_upper)
        and inverse_upper > 0
        and lower_bound > 0
        and (not existing or _as_float(existing.get("small_divisor_min_denominator_lower"), 0.0) > 0)
    )
    return {
        "schema": "theorem_iii_trackb_phase5h_cohomology_inverse_proof_v1",
        "proof_component": "cohomology_inverse_proof",
        "proof_status": "component_replayable_candidate",
        "method": "Finite golden small-divisor scan carried forward to an upper bound for the resolved cohomology inverse, with IEEE nextafter upper/lower guards inherited from Phase 5G.",
        "seed_npz_path": str(seed_npz),
        "K": seed["K"],
        "M": seed["M"],
        "omega": seed["omega"],
        "cutoff_mode_native_units": cutoff,
        "small_divisor_min_mode": scan["small_divisor_min_mode"],
        "small_divisor_min_denominator_lower": float(lower_bound),
        "cohomology_inverse_linf_resolved_upper": float(inverse_upper),
        "selected_cohomology_inverse_upper": selected_inverse,
        "selected_small_divisor_lower": selected_lower,
        "small_divisor_slack": float(small_divisor_slack),
        "depends_on_small_divisor_proof": True,
        "component_ok": proof_ok,
    }


def frame_reducibility_proof_object(
    selected: Mapping[str, Any],
    max_z: float = 0.5,
    frame_slack: float = 1e-12,
) -> Dict[str, Any]:
    """Build a replayable frame/reducibility component from Phase 5C bounds.

    This component intentionally records the currently certified Phase 5C/5D
    automatic-reducibility quantities.  It is a formal attachment component, but
    not the final theorem-facing interval library.  Replay checks that all values
    are finite, determinant defects are tiny when present, and Z remains below
    the gate threshold.
    """
    z = _as_float(selected.get("Z_interval_upper", selected.get("Z", math.inf)), math.inf)
    a21 = _as_float(selected.get("a21_linf", selected.get("upper_triangular_defect_linf_max", math.nan)), math.nan)
    upper = _as_float(selected.get("upper_triangular_defect_linf_max", a21), a21)
    a11 = _as_float(selected.get("a11_minus_1_linf", 0.0), 0.0)
    a22 = _as_float(selected.get("a22_minus_1_linf", 0.0), 0.0)
    source_det = _as_float(selected.get("source_frame_det_defect_linf", 0.0), 0.0)
    target_det = _as_float(selected.get("target_frame_det_defect_linf", 0.0), 0.0)
    twist_avg = _as_float(selected.get("twist_average", math.nan), math.nan)
    tangent_min = _as_float(selected.get("frame_tangent_norm_min", 0.0), 0.0)
    tangent_max = _as_float(selected.get("frame_tangent_norm_max", math.nan), math.nan)
    radius = _as_float(selected.get("radius", math.nan), math.nan)
    rel_margin = _as_float(selected.get("radii_relative_margin_interval_lower", math.nan), math.nan)
    finite_core = all(math.isfinite(v) for v in [z, a21, upper, a11, a22, source_det, target_det, radius, rel_margin])
    det_ok = source_det <= max(1e-9, frame_slack * 1e4) and target_det <= max(1e-9, frame_slack * 1e4)
    twist_ok = (not math.isfinite(twist_avg)) or abs(twist_avg) > 1e-8
    tangent_ok = (tangent_min == 0.0 and not math.isfinite(tangent_max)) or (tangent_min >= 0.0 and (not math.isfinite(tangent_max) or tangent_max >= tangent_min))
    component_ok = bool(finite_core and z <= max_z and a21 >= 0 and upper >= 0 and det_ok and twist_ok and tangent_ok and radius > 0 and rel_margin > 0)
    return {
        "schema": "theorem_iii_trackb_phase5h_frame_reducibility_proof_v1",
        "proof_component": "frame_reducibility_proof",
        "proof_status": "component_replayable_candidate",
        "method": "Replay of Phase 5C/5D frame and reducibility interval-shaped constants with fail-closed threshold checks for Z, triangular defect, determinant defects, twist average, radius, and margin.",
        "Z_interval_upper": float(z),
        "max_z_threshold": float(max_z),
        "a11_minus_1_linf": float(a11),
        "a21_linf": float(a21),
        "a22_minus_1_linf": float(a22),
        "upper_triangular_defect_linf_max": float(upper),
        "source_frame_det_defect_linf": float(source_det),
        "target_frame_det_defect_linf": float(target_det),
        "twist_average": twist_avg,
        "frame_tangent_norm_min": tangent_min,
        "frame_tangent_norm_max": tangent_max,
        "radius": radius,
        "radii_relative_margin_interval_lower": rel_margin,
        "frame_slack": float(frame_slack),
        "component_ok": component_ok,
    }


def generate_phase5h_attachment(
    certificate_path: str | os.PathLike[str],
    base_attachment_path: str | os.PathLike[str],
    seed_npz: str | os.PathLike[str],
    phase5c_summary_path: Optional[str | os.PathLike[str]],
    out_dir: str | os.PathLike[str],
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    min_relative_margin: float,
    max_z: float,
    small_divisor_slack: float = 1e-14,
    frame_slack: float = 1e-12,
    force: bool = False,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    attachment_out = out_dir / "phase5h_formal_interval_attachment_COMPONENTS.json"
    summary_out = out_dir / "phase5h_component_summary.json"
    if attachment_out.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {attachment_out}; pass --force")

    base = read_json(base_attachment_path)
    phase5c_summary = read_json(phase5c_summary_path) if phase5c_summary_path else None
    selected = _selected_constants(base, phase5c_summary)
    cert_hash = canonical_file_sha256(certificate_path)
    fe = _ensure_formal_evidence(base)
    component_evidence = _component_evidence(base)

    cohom_obj = cohomology_inverse_proof_object(seed_npz, selected, base, small_divisor_slack=small_divisor_slack)
    frame_obj = frame_reducibility_proof_object(selected, max_z=max_z, frame_slack=frame_slack)

    # Only set the two new flags if their local component checks pass and the
    # already-completed prerequisites are still true.
    residual_prereq = fe.get("outward_rounded_residual_proof") is True
    small_prereq = fe.get("small_divisor_proof") is True
    if cohom_obj["component_ok"] and small_prereq:
        fe["cohomology_inverse_proof"] = True
    if frame_obj["component_ok"] and residual_prereq and small_prereq:
        fe["frame_reducibility_proof"] = True

    # Keep global and later flags fail-closed.
    fe["formal_interval_backend"] = False
    fe["independent_replay_passed"] = False
    for k in ["nonlinear_bound_proof", "tail_bound_proof", "branch_chart_compatibility_proof", "final_graph_consumption_proof"]:
        fe[k] = bool(fe.get(k, False)) and False

    component_evidence["cohomology_inverse_proof"] = cohom_obj
    component_evidence["frame_reducibility_proof"] = frame_obj

    attachment = dict(base)
    attachment.update(
        {
            "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
            "phase5h_schema": "theorem_iii_trackb_phase5h_formal_component_attachment_v1",
            "diagnostic_only": True,
            "theorem_facing": False,
            "promotion_allowed": False,
            "formal_attachment_ok": False,
            "promotion_ready": False,
            "certificate_sha256": cert_hash,
            "certificate_hash_sha256": cert_hash,
            "references_certificate_sha256": cert_hash,
            "certificate_path": str(certificate_path),
            "formal_evidence": fe,
            "formal_component_evidence": component_evidence,
            "selected_constants": selected,
            "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_REMAINING_FORMAL_EVIDENCE_FLAGS_TRUE",
            "open_requirements_for_promotion": [
                "Add independently replayed nonlinear bound proof.",
                "Add independently replayed tail bound proof.",
                "Validate branch/chart compatibility and final graph consumption.",
                "Set formal_interval_backend and independent_replay_passed only after all component proofs are independently replayed.",
            ],
        }
    )
    write_json(attachment_out, attachment)

    true_flags = [k for k, v in fe.items() if v]
    missing_false = [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if not fe.get(k, False)]
    config_ok = (
        abs(_as_float(selected.get("nu")) - require_nu) <= 1e-15
        and abs(_as_float(selected.get("radius")) - require_radius) <= 1e-18
        and str(selected.get("cutoff_spec")) == str(require_cutoff)
        and abs(_as_float(selected.get("tail_start_frac")) - require_tail_start) <= 1e-14
        and _as_float(selected.get("radii_relative_margin_interval_lower"), 0.0) >= min_relative_margin
        and _as_float(selected.get("Z_interval_upper", selected.get("Z")), math.inf) <= max_z
    )
    passed = bool(config_ok and cohom_obj["component_ok"] and frame_obj["component_ok"] and fe.get("cohomology_inverse_proof") and fe.get("frame_reducibility_proof"))
    summary = {
        "schema": "theorem_iii_trackb_phase5h_component_summary_v1",
        "status": "phase5h-formal-cohomology-frame-components-generated",
        "passed": {
            "cohomology_inverse_component_ok": bool(cohom_obj["component_ok"]),
            "frame_reducibility_component_ok": bool(frame_obj["component_ok"]),
            "configuration_ok": bool(config_ok),
        },
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "promotion_ready": False,
        "certificate_sha256": cert_hash,
        "certificate_path": str(certificate_path),
        "base_attachment_path": str(base_attachment_path),
        "attachment_path": str(attachment_out),
        "selected_constants": selected,
        "formal_evidence_true_flags": true_flags,
        "missing_formal_evidence_flags": missing_false,
        "cohomology_inverse_component": cohom_obj,
        "frame_reducibility_component": frame_obj,
        "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_REMAINING_FORMAL_EVIDENCE_FLAGS_TRUE",
        "overall_component_passed": passed,
    }
    write_json(summary_out, summary)
    return summary


def replay_phase5h_attachment(
    certificate_path: str | os.PathLike[str],
    attachment_path: str | os.PathLike[str],
    seed_npz: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    required_min_lower_anchor_k: float,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    min_relative_margin: float,
    max_z: float,
    small_divisor_slack: float = 1e-14,
    frame_slack: float = 1e-12,
    force: bool = False,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase5h_component_replay_summary.json"
    if out_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {out_path}; pass --force")

    attachment = read_json(attachment_path)
    cert_hash = canonical_file_sha256(certificate_path)
    selected = attachment.get("selected_constants", {}) if isinstance(attachment.get("selected_constants"), Mapping) else {}
    fe = _ensure_formal_evidence(attachment)
    comp = _component_evidence(attachment)
    stored_cohom = comp.get("cohomology_inverse_proof") if isinstance(comp.get("cohomology_inverse_proof"), Mapping) else {}
    stored_frame = comp.get("frame_reducibility_proof") if isinstance(comp.get("frame_reducibility_proof"), Mapping) else {}
    replay_cohom = cohomology_inverse_proof_object(seed_npz, selected, attachment, small_divisor_slack=small_divisor_slack)
    replay_frame = frame_reducibility_proof_object(selected, max_z=max_z, frame_slack=frame_slack)

    checks = []

    def add(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("schema", attachment.get("schema") == "theorem_iii_trackb_phase5e_formal_interval_attachment_v1", attachment.get("schema"))
    add("phase5h_schema", attachment.get("phase5h_schema") == "theorem_iii_trackb_phase5h_formal_component_attachment_v1", attachment.get("phase5h_schema"))
    add("diagnostic_only_true", attachment.get("diagnostic_only") is True, attachment.get("diagnostic_only"))
    add("theorem_facing_false", attachment.get("theorem_facing") is False, attachment.get("theorem_facing"))
    add("promotion_allowed_false", attachment.get("promotion_allowed") is False, attachment.get("promotion_allowed"))
    add("certificate_hash_matches", attachment.get("certificate_sha256") == cert_hash or attachment.get("references_certificate_sha256") == cert_hash, {"expected": cert_hash, "found": attachment.get("certificate_sha256")})
    add("residual_flag_still_true", fe.get("outward_rounded_residual_proof") is True, fe.get("outward_rounded_residual_proof"))
    add("small_divisor_flag_still_true", fe.get("small_divisor_proof") is True, fe.get("small_divisor_proof"))
    add("cohomology_inverse_flag_true", fe.get("cohomology_inverse_proof") is True, fe.get("cohomology_inverse_proof"))
    add("frame_reducibility_flag_true", fe.get("frame_reducibility_proof") is True, fe.get("frame_reducibility_proof"))
    remaining_false = ["formal_interval_backend", "independent_replay_passed", "nonlinear_bound_proof", "tail_bound_proof", "branch_chart_compatibility_proof", "final_graph_consumption_proof"]
    add("later_global_flags_false", all(fe.get(k, False) is False for k in remaining_false), {k: fe.get(k) for k in remaining_false})
    add("anchor_meets_min", _as_float(selected.get("K"), 0.0) >= required_min_lower_anchor_k, selected.get("K"))
    add("nu_matches", abs(_as_float(selected.get("nu")) - require_nu) <= 1e-15, selected.get("nu"))
    add("radius_matches", abs(_as_float(selected.get("radius")) - require_radius) <= 1e-18, selected.get("radius"))
    add("cutoff_matches", str(selected.get("cutoff_spec")) == str(require_cutoff), selected.get("cutoff_spec"))
    add("tail_start_matches", abs(_as_float(selected.get("tail_start_frac")) - require_tail_start) <= 1e-14, selected.get("tail_start_frac"))
    add("relative_margin_threshold", _as_float(selected.get("radii_relative_margin_interval_lower"), 0.0) >= min_relative_margin, selected.get("radii_relative_margin_interval_lower"))
    add("Z_below_threshold", _as_float(selected.get("Z_interval_upper", selected.get("Z")), math.inf) <= max_z, selected.get("Z_interval_upper", selected.get("Z")))
    add("cohomology_object_present", isinstance(stored_cohom, Mapping), bool(stored_cohom))
    add("frame_object_present", isinstance(stored_frame, Mapping), bool(stored_frame))
    add("cohomology_replay_component_ok", replay_cohom["component_ok"], replay_cohom)
    add("frame_replay_component_ok", replay_frame["component_ok"], replay_frame)
    if isinstance(stored_cohom, Mapping):
        add("cohomology_inverse_replay_covers", _as_float(stored_cohom.get("cohomology_inverse_linf_resolved_upper"), math.inf) + 1e-10 >= replay_cohom["cohomology_inverse_linf_resolved_upper"], {"stored": stored_cohom.get("cohomology_inverse_linf_resolved_upper"), "replayed": replay_cohom["cohomology_inverse_linf_resolved_upper"]})
        add("cohomology_small_divisor_positive", _as_float(stored_cohom.get("small_divisor_min_denominator_lower"), 0.0) > 0.0, stored_cohom.get("small_divisor_min_denominator_lower"))
    if isinstance(stored_frame, Mapping):
        add("frame_Z_replay_covers", _as_float(stored_frame.get("Z_interval_upper"), math.inf) + 1e-15 >= replay_frame["Z_interval_upper"], {"stored": stored_frame.get("Z_interval_upper"), "replayed": replay_frame["Z_interval_upper"]})
        add("frame_a21_finite", math.isfinite(_as_float(stored_frame.get("a21_linf"), math.inf)), stored_frame.get("a21_linf"))

    failed = [c["name"] for c in checks if not c["ok"]]
    true_flags = [k for k, v in fe.items() if v]
    missing_false = [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if not fe.get(k, False)]
    summary = {
        "schema": "theorem_iii_trackb_phase5h_component_replay_summary_v1",
        "status": "phase5h-component-replay-complete",
        "passed": len(failed) == 0,
        "failed_checks": failed,
        "checks": checks,
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "promotion_ready": False,
        "formal_attachment_ok": False,
        "certificate_sha256": cert_hash,
        "attachment_path": str(attachment_path),
        "selected_constants": selected,
        "formal_evidence_true_flags": true_flags,
        "missing_formal_evidence_flags": missing_false,
        "cohomology_inverse_component": replay_cohom,
        "frame_reducibility_component": replay_frame,
        "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_REMAINING_FORMAL_EVIDENCE_FLAGS_TRUE",
    }
    write_json(out_path, summary)
    return summary


def summarize_phase5h(input_path: str | os.PathLike[str], out_path: Optional[str | os.PathLike[str]] = None) -> Dict[str, Any]:
    r = read_json(input_path)
    selected = r.get("selected_constants", {}) if isinstance(r.get("selected_constants"), Mapping) else {}
    cohom = r.get("cohomology_inverse_component", {}) if isinstance(r.get("cohomology_inverse_component"), Mapping) else {}
    frame = r.get("frame_reducibility_component", {}) if isinstance(r.get("frame_reducibility_component"), Mapping) else {}
    compact = {
        "schema": "theorem_iii_trackb_phase5h_compact_report_v1",
        "status": r.get("status"),
        "diagnostic_only": r.get("diagnostic_only", True),
        "theorem_facing": r.get("theorem_facing", False),
        "promotion_allowed": r.get("promotion_allowed", False),
        "formal_attachment_ok": r.get("formal_attachment_ok", False),
        "promotion_ready": r.get("promotion_ready", False),
        "passed": r.get("passed", r.get("overall_component_passed", False)),
        "failed_checks": r.get("failed_checks", []),
        "certificate_sha256": r.get("certificate_sha256"),
        "attachment_path": r.get("attachment_path"),
        "formal_evidence_true_flags": r.get("formal_evidence_true_flags", []),
        "missing_formal_evidence_flags": r.get("missing_formal_evidence_flags", []),
        "selected_constants": {
            "K": selected.get("K"),
            "M": selected.get("M"),
            "nu": selected.get("nu"),
            "radius": selected.get("radius"),
            "cutoff_spec": selected.get("cutoff_spec"),
            "tail_start_frac": selected.get("tail_start_frac"),
            "Y_interval_upper": selected.get("Y_interval_upper"),
            "Z_interval_upper": selected.get("Z_interval_upper"),
            "Q_interval_upper": selected.get("Q_interval_upper"),
            "radii_margin_interval_lower": selected.get("radii_margin_interval_lower"),
            "radii_relative_margin_interval_lower": selected.get("radii_relative_margin_interval_lower"),
            "small_divisor_min_denominator_lower": selected.get("small_divisor_min_denominator_lower"),
            "cohomology_inverse_linf_resolved_upper": selected.get("cohomology_inverse_linf_resolved_upper"),
        },
        "cohomology_inverse_component": {
            "component_ok": cohom.get("component_ok"),
            "small_divisor_min_denominator_lower": cohom.get("small_divisor_min_denominator_lower"),
            "cohomology_inverse_linf_resolved_upper": cohom.get("cohomology_inverse_linf_resolved_upper"),
            "cutoff_mode_native_units": cohom.get("cutoff_mode_native_units"),
            "small_divisor_min_mode": cohom.get("small_divisor_min_mode"),
        },
        "frame_reducibility_component": {
            "component_ok": frame.get("component_ok"),
            "Z_interval_upper": frame.get("Z_interval_upper"),
            "a21_linf": frame.get("a21_linf"),
            "upper_triangular_defect_linf_max": frame.get("upper_triangular_defect_linf_max"),
            "a11_minus_1_linf": frame.get("a11_minus_1_linf"),
            "a22_minus_1_linf": frame.get("a22_minus_1_linf"),
            "source_frame_det_defect_linf": frame.get("source_frame_det_defect_linf"),
            "target_frame_det_defect_linf": frame.get("target_frame_det_defect_linf"),
            "twist_average": frame.get("twist_average"),
        },
        "expected_phase5e_decision": r.get("expected_phase5e_decision", "REJECT_FAIL_CLOSED_UNTIL_REMAINING_FORMAL_EVIDENCE_FLAGS_TRUE"),
    }
    if out_path:
        write_json(out_path, compact)
    return compact
