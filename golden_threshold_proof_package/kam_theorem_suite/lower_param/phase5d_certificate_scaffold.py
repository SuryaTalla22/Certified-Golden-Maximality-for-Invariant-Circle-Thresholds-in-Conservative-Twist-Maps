"""Phase 5D certificate assembly scaffold for Track B Theorem III.

This module assembles a replayable, diagnostic-only certificate candidate from the
Phase 5C interval-backend audit.  It intentionally does *not* promote the result
to a theorem-facing proof object.  The goal is to freeze the winning backend
configuration, make the radii inequality mechanically replayable, and expose the
remaining assumptions/open hypotheses that must be discharged in later phases.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import copy
import json
import math
import os
import time

SCHEMA_CERT = "theorem_iii_trackb_phase5d_certificate_scaffold_v1"
SCHEMA_SUMMARY = "theorem_iii_trackb_phase5d_assembly_summary_v1"
SCHEMA_REPLAY = "theorem_iii_trackb_phase5d_replay_summary_v1"

REQUIRED_CANDIDATE_FIELDS = [
    "K",
    "M",
    "nu",
    "radius",
    "grid_factor",
    "cutoff_spec",
    "tail_start_frac",
    "Y_interval_upper",
    "Z_interval_upper",
    "Q_interval_upper",
    "radii_lhs_interval_upper",
    "radii_margin_interval_lower",
    "radii_relative_margin_interval_lower",
    "small_divisor_min_denominator_lower",
    "cohomology_inverse_linf_resolved_upper",
    "residual_l1_nu_total_upper",
    "scalar_residual_linf",
    "derivative_residual_linf",
    "upper_triangular_defect_linf_max",
    "dominant_interval_term",
    "recommendation_label",
    "npz_path",
]


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def read_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}.{time.time_ns()}")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, default=_json_default)
        f.write("\n")
    os.replace(tmp, path)


def _finite_float(x: Any) -> bool:
    try:
        v = float(x)
    except Exception:
        return False
    return math.isfinite(v)


def _num(x: Any) -> float:
    return float(x)


def load_candidates_from_summary(summary_path: str | Path) -> List[Dict[str, Any]]:
    summary = read_json(summary_path)
    candidates = summary.get("top_candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("Phase 5C summary has no list field 'top_candidates'.")
    return candidates


def load_candidate_from_record(record_path: str | Path) -> Dict[str, Any]:
    payload = read_json(record_path)
    # Records and compact candidates use the same core fields.  If the record wraps
    # the candidate under a field later, support both layouts.
    if "candidate" in payload and isinstance(payload["candidate"], dict):
        return payload["candidate"]
    return payload


def candidate_missing_fields(candidate: Dict[str, Any]) -> List[str]:
    return [k for k in REQUIRED_CANDIDATE_FIELDS if k not in candidate]


def candidate_sort_key(candidate: Dict[str, Any], prefer_cutoff: str, prefer_tail_start: float, prefer_radius: float) -> Tuple[Any, ...]:
    """Sort candidates best-first.

    The sort prioritizes backend-ready records, preferred radius/tail/cutoff, then
    larger interval margin and lower Z.  It still permits alternate records to be
    inspected if the preferred one is not present.
    """
    label = str(candidate.get("recommendation_label", ""))
    ready = 1 if label == "backend_ready_candidate" else 0
    positive = 1 if bool(candidate.get("any_positive_interval_margin", False)) else 0
    radius = _num(candidate.get("radius", float("nan"))) if _finite_float(candidate.get("radius")) else float("nan")
    tail = _num(candidate.get("tail_start_frac", float("nan"))) if _finite_float(candidate.get("tail_start_frac")) else float("nan")
    cutoff = str(candidate.get("cutoff_spec", ""))
    margin = _num(candidate.get("radii_margin_interval_lower", float("-inf"))) if _finite_float(candidate.get("radii_margin_interval_lower")) else float("-inf")
    rel_margin = _num(candidate.get("radii_relative_margin_interval_lower", float("-inf"))) if _finite_float(candidate.get("radii_relative_margin_interval_lower")) else float("-inf")
    z = _num(candidate.get("Z_interval_upper", float("inf"))) if _finite_float(candidate.get("Z_interval_upper")) else float("inf")
    # Negative distance means closer to preferred value is larger after negation.
    radius_match = -abs(radius - prefer_radius) if math.isfinite(radius) else -1e9
    tail_match = -abs(tail - prefer_tail_start) if math.isfinite(tail) else -1e9
    cutoff_match = 1 if cutoff == prefer_cutoff else 0
    return (ready, positive, radius_match, tail_match, cutoff_match, margin, rel_margin, -z)


def select_candidate(
    summary_path: Optional[str | Path] = None,
    record_path: Optional[str | Path] = None,
    prefer_cutoff: str = "full",
    prefer_tail_start: float = 0.90,
    prefer_radius: float = 3e-5,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if record_path:
        cand = load_candidate_from_record(record_path)
        return cand, {"selection_mode": "explicit_record", "record_path": str(record_path)}
    if not summary_path:
        raise ValueError("Either summary_path or record_path is required.")
    candidates = load_candidates_from_summary(summary_path)
    if not candidates:
        raise ValueError("No candidates found in Phase 5C summary.")
    ranked = sorted(
        candidates,
        key=lambda c: candidate_sort_key(c, prefer_cutoff, prefer_tail_start, prefer_radius),
        reverse=True,
    )
    return ranked[0], {
        "selection_mode": "ranked_from_summary",
        "summary_path": str(summary_path),
        "candidate_count": len(candidates),
        "prefer_cutoff": prefer_cutoff,
        "prefer_tail_start": prefer_tail_start,
        "prefer_radius": prefer_radius,
        "selected_record_path": ranked[0].get("record_path"),
    }


def assemble_certificate_scaffold(
    candidate: Dict[str, Any],
    selection_info: Dict[str, Any],
    min_anchor_k: float = 0.971635,
) -> Dict[str, Any]:
    missing = candidate_missing_fields(candidate)
    if missing:
        raise ValueError(f"Selected Phase 5C candidate is missing required fields: {missing}")

    k = _num(candidate["K"])
    r = _num(candidate["radius"])
    y = _num(candidate["Y_interval_upper"])
    z = _num(candidate["Z_interval_upper"])
    q = _num(candidate["Q_interval_upper"])
    recomputed_lhs = y + z * r + q * r * r
    reported_lhs = _num(candidate["radii_lhs_interval_upper"])
    reported_margin = _num(candidate["radii_margin_interval_lower"])
    recomputed_margin = r - recomputed_lhs

    certificate = {
        "schema": SCHEMA_CERT,
        "status": "diagnostic_certificate_scaffold",
        "theorem": "III",
        "track": "B",
        "certificate_type": "direct_lower_anchor_parameterization_interval_backend_scaffold",
        "validator_type": "fhl_style_parameterization_backend_scaffold",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "created_from": "phase5c_interval_backend",
        "selection_info": selection_info,
        "claim_scaffold": {
            "statement": "Diagnostic scaffold for a direct lower-anchor persistence certificate for the golden invariant circle.",
            "family": "standard_sine_twist_map",
            "omega": "golden",
            "lower_anchor_K": k,
            "required_min_lower_anchor_K": min_anchor_k,
            "lower_anchor_meets_target": bool(k >= min_anchor_k),
            "anchor_interval": [k, k],
        },
        "seed": {
            "npz_path": candidate.get("npz_path"),
            "K": k,
            "M": int(candidate["M"]),
        },
        "validation_parameters": {
            "nu": _num(candidate["nu"]),
            "radius": r,
            "grid_factor": int(candidate["grid_factor"]),
            "grid_size": int(candidate.get("grid_size", int(candidate["M"]) * int(candidate["grid_factor"]))),
            "cutoff_spec": candidate["cutoff_spec"],
            "cutoff_mode_native_units": int(candidate.get("cutoff_mode_native_units", int(candidate["M"]) // 2)),
            "tail_start_frac": _num(candidate["tail_start_frac"]),
        },
        "interval_backend_bounds": {
            "Y_interval_upper": y,
            "Z_interval_upper": z,
            "Q_interval_upper": q,
            "radii_lhs_interval_upper_reported": reported_lhs,
            "radii_lhs_interval_upper_recomputed": recomputed_lhs,
            "radii_margin_interval_lower_reported": reported_margin,
            "radii_margin_interval_lower_recomputed": recomputed_margin,
            "radii_relative_margin_interval_lower": _num(candidate["radii_relative_margin_interval_lower"]),
            "dominant_interval_term": candidate["dominant_interval_term"],
            "any_positive_interval_margin": bool(candidate.get("any_positive_interval_margin", False)),
        },
        "component_terms": {
            "Y": y,
            "Z_times_r": z * r,
            "Q_times_r_squared": q * r * r,
        },
        "residual_bounds": {
            "scalar_residual_linf": _num(candidate["scalar_residual_linf"]),
            "derivative_residual_linf": _num(candidate["derivative_residual_linf"]),
            "residual_l1_nu_total_upper": _num(candidate["residual_l1_nu_total_upper"]),
            "tail_residual_component_upper": _num(candidate.get("tail_residual_component_upper", 0.0)),
        },
        "small_divisor_and_cohomology": {
            "small_divisor_min_denominator_lower": _num(candidate["small_divisor_min_denominator_lower"]),
            "small_divisor_min_mode": int(candidate.get("small_divisor_min_mode", 0)),
            "cohomology_inverse_linf_resolved_upper": _num(candidate["cohomology_inverse_linf_resolved_upper"]),
        },
        "frame_and_reducibility": {
            "upper_triangular_defect_linf_max": _num(candidate["upper_triangular_defect_linf_max"]),
            "a11_minus_1_linf": _num(candidate.get("a11_minus_1_linf", float("nan"))),
            "a21_linf": _num(candidate.get("a21_linf", float("nan"))),
            "a22_minus_1_linf": _num(candidate.get("a22_minus_1_linf", float("nan"))),
            "source_frame_det_defect_linf": _num(candidate.get("source_frame_det_defect_linf", float("nan"))),
            "target_frame_det_defect_linf": _num(candidate.get("target_frame_det_defect_linf", float("nan"))),
            "twist_average": _num(candidate.get("twist_average", float("nan"))),
            "twist_min": _num(candidate.get("twist_min", float("nan"))),
            "twist_max": _num(candidate.get("twist_max", float("nan"))),
        },
        "source_phase5c_candidate": candidate,
        "replay_policy": {
            "must_fail_if_theorem_facing_true_without_phase5e": True,
            "must_fail_if_promotion_allowed_true_without_phase5e": True,
            "must_fail_if_margin_nonpositive": True,
            "must_fail_if_Z_exceeds_threshold": True,
            "max_Z_interval_upper_for_scaffold": 0.5,
            "min_margin_interval_lower_for_scaffold": 0.0,
            "min_relative_margin_interval_lower_for_scaffold": 0.25,
        },
        "active_assumptions": [
            "Phase 5C uses nextafter outward rounding and conservative inflations but is not an independently verified formal interval proof.",
            "Fourier residual, frame, reducibility, and nonlinear constants still need a formal outward-rounded implementation/replay in Phase 5E or later.",
            "Branch/chart compatibility and final theorem graph consumption remain to be validated by the final replay gate.",
            "The scaffold certifies only a direct lower anchor candidate, not a full parameter interval or mesh corridor.",
        ],
        "open_hypotheses": [
            "Independent formal interval arithmetic backend reproduces or improves the Phase 5C bounds.",
            "Final replay rejects this scaffold unless promoted by a theorem-facing Phase 5E certificate.",
            "The lower anchor is consumed by the threshold-identification layer with matching branch/chart labels.",
        ],
    }
    return certificate


def validate_certificate_scaffold(
    cert: Dict[str, Any],
    *,
    min_margin: float = 0.0,
    min_relative_margin: float = 0.25,
    max_z: float = 0.5,
    require_not_theorem_facing: bool = True,
) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("schema", cert.get("schema") == SCHEMA_CERT, cert.get("schema"))
    add("diagnostic_only_true", cert.get("diagnostic_only") is True, cert.get("diagnostic_only"))
    if require_not_theorem_facing:
        add("theorem_facing_false", cert.get("theorem_facing") is False, cert.get("theorem_facing"))
        add("promotion_allowed_false", cert.get("promotion_allowed") is False, cert.get("promotion_allowed"))

    claim = cert.get("claim_scaffold", {})
    add("lower_anchor_meets_target", bool(claim.get("lower_anchor_meets_target", False)), claim)

    bounds = cert.get("interval_backend_bounds", {})
    params = cert.get("validation_parameters", {})
    r = bounds.get("radius", params.get("radius"))
    try:
        r = float(params["radius"])
        y = float(bounds["Y_interval_upper"])
        z = float(bounds["Z_interval_upper"])
        q = float(bounds["Q_interval_upper"])
        reported_lhs = float(bounds["radii_lhs_interval_upper_reported"])
        reported_margin = float(bounds["radii_margin_interval_lower_reported"])
        rel_margin = float(bounds["radii_relative_margin_interval_lower"])
        recomputed_lhs = y + z * r + q * r * r
        recomputed_margin = r - recomputed_lhs
        add("finite_YZQr", all(math.isfinite(v) for v in [y, z, q, r]), [y, z, q, r])
        add("positive_radius", r > 0, r)
        add("positive_reported_margin", reported_margin > min_margin, reported_margin)
        add("positive_recomputed_margin", recomputed_margin > min_margin, recomputed_margin)
        add("relative_margin_threshold", rel_margin >= min_relative_margin, rel_margin)
        add("Z_below_threshold", z <= max_z, z)
        # Allow reported_lhs to be either equal or more conservative than recomputed_lhs,
        # within small numerical tolerance.
        add("reported_lhs_covers_recomputed_lhs", reported_lhs + 1e-12 >= recomputed_lhs, {"reported": reported_lhs, "recomputed": recomputed_lhs})
    except Exception as exc:
        add("radii_fields_parse", False, repr(exc))

    sd = cert.get("small_divisor_and_cohomology", {})
    add("small_divisor_positive", _finite_float(sd.get("small_divisor_min_denominator_lower")) and float(sd["small_divisor_min_denominator_lower"]) > 0, sd.get("small_divisor_min_denominator_lower"))
    add("cohomology_inverse_finite", _finite_float(sd.get("cohomology_inverse_linf_resolved_upper")), sd.get("cohomology_inverse_linf_resolved_upper"))

    fr = cert.get("frame_and_reducibility", {})
    add("twist_average_finite", _finite_float(fr.get("twist_average")), fr.get("twist_average"))
    add("upper_triangular_defect_finite", _finite_float(fr.get("upper_triangular_defect_linf_max")), fr.get("upper_triangular_defect_linf_max"))

    add("active_assumptions_nonempty", bool(cert.get("active_assumptions")), cert.get("active_assumptions"))
    add("open_hypotheses_nonempty", bool(cert.get("open_hypotheses")), cert.get("open_hypotheses"))

    passed = all(c["ok"] for c in checks)
    return {
        "schema": SCHEMA_REPLAY,
        "status": "phase5d-replay-scaffold-complete",
        "passed": passed,
        "checks": checks,
        "failed_checks": [c for c in checks if not c["ok"]],
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
    }


def build_negative_controls(cert: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    controls: List[Tuple[str, Dict[str, Any]]] = []

    bad_margin = copy.deepcopy(cert)
    bad_margin["interval_backend_bounds"]["radii_margin_interval_lower_reported"] = -1e-12
    bad_margin["interval_backend_bounds"]["radii_lhs_interval_upper_reported"] = bad_margin["validation_parameters"]["radius"] + 1e-12
    controls.append(("negative_bad_margin", bad_margin))

    bad_z = copy.deepcopy(cert)
    bad_z["interval_backend_bounds"]["Z_interval_upper"] = 1.25
    controls.append(("negative_bad_Z", bad_z))

    bad_promotion = copy.deepcopy(cert)
    bad_promotion["theorem_facing"] = True
    bad_promotion["promotion_allowed"] = True
    controls.append(("negative_premature_promotion", bad_promotion))

    bad_anchor = copy.deepcopy(cert)
    bad_anchor["claim_scaffold"]["lower_anchor_K"] = 0.9710
    bad_anchor["claim_scaffold"]["lower_anchor_meets_target"] = False
    controls.append(("negative_bad_anchor", bad_anchor))

    return controls


def run_negative_controls(cert: Dict[str, Any]) -> Dict[str, Any]:
    results = []
    for name, bad in build_negative_controls(cert):
        replay = validate_certificate_scaffold(bad)
        results.append({
            "name": name,
            "expected_to_fail": True,
            "failed_as_expected": not replay["passed"],
            "replay": replay,
        })
    return {
        "negative_controls_passed": all(r["failed_as_expected"] for r in results),
        "negative_controls": results,
    }


def assemble_phase5d(
    *,
    summary_path: Optional[str | Path],
    record_path: Optional[str | Path],
    out_dir: str | Path,
    prefer_cutoff: str = "full",
    prefer_tail_start: float = 0.90,
    prefer_radius: float = 3e-5,
    min_anchor_k: float = 0.971635,
    min_margin: float = 0.0,
    min_relative_margin: float = 0.25,
    max_z: float = 0.5,
    run_negatives: bool = True,
    force: bool = False,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    if out_dir.exists() and not force:
        raise FileExistsError(f"Output directory exists: {out_dir}. Use --force to overwrite files.")
    out_dir.mkdir(parents=True, exist_ok=True)

    candidate, selection_info = select_candidate(
        summary_path=summary_path,
        record_path=record_path,
        prefer_cutoff=prefer_cutoff,
        prefer_tail_start=prefer_tail_start,
        prefer_radius=prefer_radius,
    )
    cert = assemble_certificate_scaffold(candidate, selection_info, min_anchor_k=min_anchor_k)
    replay = validate_certificate_scaffold(cert, min_margin=min_margin, min_relative_margin=min_relative_margin, max_z=max_z)
    negative_summary = run_negative_controls(cert) if run_negatives else {"negative_controls_passed": None, "negative_controls": []}

    cert_path = out_dir / "theorem_iii_trackb_phase5d_certificate_scaffold.json"
    replay_path = out_dir / "phase5d_replay_summary.json"
    summary_path_out = out_dir / "phase5d_assembly_summary.json"

    write_json(cert_path, cert)
    write_json(replay_path, replay)

    summary = {
        "schema": SCHEMA_SUMMARY,
        "status": "phase5d-certificate-scaffold-assembled",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "certificate_path": str(cert_path),
        "replay_path": str(replay_path),
        "replay_passed": replay["passed"],
        "negative_controls_passed": negative_summary["negative_controls_passed"],
        "selected_candidate": {
            "K": candidate.get("K"),
            "M": candidate.get("M"),
            "nu": candidate.get("nu"),
            "radius": candidate.get("radius"),
            "cutoff_spec": candidate.get("cutoff_spec"),
            "tail_start_frac": candidate.get("tail_start_frac"),
            "Y_interval_upper": candidate.get("Y_interval_upper"),
            "Z_interval_upper": candidate.get("Z_interval_upper"),
            "Q_interval_upper": candidate.get("Q_interval_upper"),
            "radii_margin_interval_lower": candidate.get("radii_margin_interval_lower"),
            "radii_relative_margin_interval_lower": candidate.get("radii_relative_margin_interval_lower"),
            "recommendation_label": candidate.get("recommendation_label"),
            "record_path": candidate.get("record_path"),
        },
        "selection_info": selection_info,
        "failed_replay_checks": replay["failed_checks"],
        "negative_controls": negative_summary["negative_controls"],
        "next_phase_recommendation": "Proceed to Phase 5E theorem-facing replay gate and formal certificate promotion only if independent interval checks are attached.",
        "active_assumptions": cert["active_assumptions"],
        "open_hypotheses": cert["open_hypotheses"],
    }
    write_json(summary_path_out, summary)
    return summary


def replay_certificate_file(
    certificate_path: str | Path,
    out_dir: str | Path,
    min_margin: float = 0.0,
    min_relative_margin: float = 0.25,
    max_z: float = 0.5,
    force: bool = False,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    if out_dir.exists() and not force:
        raise FileExistsError(f"Output directory exists: {out_dir}. Use --force to overwrite files.")
    out_dir.mkdir(parents=True, exist_ok=True)
    cert = read_json(certificate_path)
    replay = validate_certificate_scaffold(cert, min_margin=min_margin, min_relative_margin=min_relative_margin, max_z=max_z)
    replay["certificate_path"] = str(certificate_path)
    replay_path = out_dir / "phase5d_replay_summary.json"
    write_json(replay_path, replay)
    return replay
