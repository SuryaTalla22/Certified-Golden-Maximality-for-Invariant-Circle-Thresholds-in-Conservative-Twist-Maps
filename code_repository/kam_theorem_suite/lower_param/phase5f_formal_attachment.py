"""Phase 5F formal-interval attachment candidate utilities.

This module is intentionally fail-closed.  It can assemble a formal-attachment
*candidate* from the Phase 5D scaffold and Phase 5C interval-backend record, but
it does not assert theorem-facing proof flags.  The required formal-evidence
flags remain false until a genuinely independent formal interval backend exists.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
import copy
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

getcontext().prec = 80

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

ATTACHMENT_SCHEMA = "theorem_iii_trackb_phase5e_formal_interval_attachment_v1"
PHASE5F_SUMMARY_SCHEMA = "theorem_iii_trackb_phase5f_attachment_candidate_summary_v1"
PHASE5F_REPLAY_SCHEMA = "theorem_iii_trackb_phase5f_attachment_candidate_replay_v1"


def load_json(path: str | os.PathLike[str]) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _atomic_write_json(path: str | os.PathLike[str], payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def _sha256_json_payload(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _sha256_file(path: str | os.PathLike[str]) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None


def _safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _dec(x: Any) -> Decimal:
    # Decimal(str(x)) avoids binary-float artifacts in the printed input while
    # still preserving enough precision for a replay-oriented audit.
    return Decimal(str(x))


def _finite(x: Any) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def _iter_dicts(obj: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(obj, Mapping):
        yield obj
        for v in obj.values():
            yield from _iter_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_dicts(v)


def find_first_key(obj: Any, key: str, default: Any = None) -> Any:
    for d in _iter_dicts(obj):
        if key in d:
            return d[key]
    return default


def candidate_matches(
    cand: Mapping[str, Any],
    require_nu: Optional[float] = None,
    require_radius: Optional[float] = None,
    require_cutoff: Optional[str] = None,
    require_tail_start: Optional[float] = None,
    min_anchor_k: Optional[float] = None,
    tol: float = 5e-13,
) -> bool:
    if require_nu is not None and abs(_safe_float(cand.get("nu")) - float(require_nu)) > tol:
        return False
    if require_radius is not None and abs(_safe_float(cand.get("radius")) - float(require_radius)) > tol:
        return False
    if require_cutoff is not None and str(cand.get("cutoff_spec")) != str(require_cutoff):
        return False
    if require_tail_start is not None and abs(_safe_float(cand.get("tail_start_frac")) - float(require_tail_start)) > tol:
        return False
    if min_anchor_k is not None and _safe_float(cand.get("K"), -float("inf")) + tol < float(min_anchor_k):
        return False
    return True


def extract_phase5c_candidates(phase5c_summary: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    cands = phase5c_summary.get("top_candidates", [])
    if not isinstance(cands, list):
        return []
    return [c for c in cands if isinstance(c, Mapping)]


def choose_phase5c_candidate(
    phase5c_summary: Mapping[str, Any],
    require_nu: Optional[float] = None,
    require_radius: Optional[float] = None,
    prefer_cutoff: Optional[str] = None,
    prefer_tail_start: Optional[float] = None,
    min_anchor_k: Optional[float] = None,
) -> Mapping[str, Any]:
    cands = extract_phase5c_candidates(phase5c_summary)
    if not cands:
        raise ValueError("Phase 5C summary contains no top_candidates")

    def score(c: Mapping[str, Any]) -> Tuple[int, float, float, float]:
        s = 0
        if require_nu is None or abs(_safe_float(c.get("nu")) - float(require_nu)) < 5e-13:
            s += 10
        if require_radius is None or abs(_safe_float(c.get("radius")) - float(require_radius)) < 5e-13:
            s += 10
        if prefer_cutoff is None or str(c.get("cutoff_spec")) == str(prefer_cutoff):
            s += 5
        if prefer_tail_start is None or abs(_safe_float(c.get("tail_start_frac")) - float(prefer_tail_start)) < 5e-13:
            s += 5
        if min_anchor_k is None or _safe_float(c.get("K"), -float("inf")) >= float(min_anchor_k) - 5e-13:
            s += 10
        margin = _safe_float(c.get("radii_margin_interval_lower"), _safe_float(c.get("radii_margin_component"), -float("inf")))
        rel = _safe_float(c.get("radii_relative_margin_interval_lower"), _safe_float(c.get("radii_relative_margin_component"), -float("inf")))
        z = _safe_float(c.get("Z_interval_upper"), _safe_float(c.get("Z_component_bound"), float("inf")))
        # Higher score, larger margin/rel, smaller Z.
        return (s, margin, rel, -z)

    exact = [
        c for c in cands
        if candidate_matches(c, require_nu, require_radius, prefer_cutoff, prefer_tail_start, min_anchor_k)
    ]
    if exact:
        exact.sort(key=score, reverse=True)
        return exact[0]
    cands.sort(key=score, reverse=True)
    return cands[0]


def normalize_candidate_constants(c: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a normalized constants dictionary from Phase 5C/5B-style records."""
    Y = c.get("Y_interval_upper", c.get("Y_component_bound", c.get("Y_cohomology_proxy")))
    Z = c.get("Z_interval_upper", c.get("Z_component_bound", c.get("Z_linear_reducibility_proxy")))
    Q = c.get("Q_interval_upper", c.get("Q_component_bound", c.get("Q_nonlinear_proxy")))
    r = c.get("radius", c.get("best_radius_proxy"))
    margin = c.get("radii_margin_interval_lower", c.get("radii_margin_component", c.get("best_radii_margin_proxy")))
    rel = c.get("radii_relative_margin_interval_lower", c.get("radii_relative_margin_component", c.get("best_relative_margin_proxy")))
    lhs = c.get("radii_lhs_interval_upper", c.get("radii_lhs_component_bound"))
    return {
        "K": c.get("K"),
        "M": c.get("M"),
        "nu": c.get("nu"),
        "radius": r,
        "cutoff_spec": c.get("cutoff_spec"),
        "cutoff_mode_native_units": c.get("cutoff_mode_native_units"),
        "tail_start_frac": c.get("tail_start_frac"),
        "grid_factor": c.get("grid_factor"),
        "grid_size": c.get("grid_size"),
        "Y_interval_upper": Y,
        "Z_interval_upper": Z,
        "Q_interval_upper": Q,
        "radii_lhs_interval_upper": lhs,
        "radii_margin_interval_lower": margin,
        "radii_relative_margin_interval_lower": rel,
        "small_divisor_min_denominator_lower": c.get("small_divisor_min_denominator_lower", c.get("small_divisor_min_denominator")),
        "small_divisor_min_mode": c.get("small_divisor_min_mode"),
        "cohomology_inverse_linf_resolved_upper": c.get("cohomology_inverse_linf_resolved_upper", c.get("cohomology_inverse_linf_resolved")),
        "scalar_residual_linf": c.get("scalar_residual_linf"),
        "derivative_residual_linf": c.get("derivative_residual_linf"),
        "residual_l1_nu_total_upper": c.get("residual_l1_nu_total_upper", c.get("residual_l1_nu_total")),
        "tail_residual_component_upper": c.get("tail_residual_component_upper", c.get("tail_residual_component_bound")),
        "upper_triangular_defect_linf_max": c.get("upper_triangular_defect_linf_max"),
        "a11_minus_1_linf": c.get("a11_minus_1_linf"),
        "a21_linf": c.get("a21_linf"),
        "a22_minus_1_linf": c.get("a22_minus_1_linf"),
        "twist_average": c.get("twist_average"),
        "twist_min": c.get("twist_min"),
        "twist_max": c.get("twist_max"),
        "source_record_path": c.get("record_path"),
        "npz_path": c.get("npz_path"),
    }


def decimal_radii_replay(constants: Mapping[str, Any]) -> Dict[str, Any]:
    Y, Z, Q, r = (_dec(constants[k]) for k in ("Y_interval_upper", "Z_interval_upper", "Q_interval_upper", "radius"))
    lhs = Y + Z * r + Q * r * r
    margin = r - lhs
    rel = margin / r if r != 0 else Decimal("NaN")
    reported_lhs = constants.get("radii_lhs_interval_upper")
    reported_margin = constants.get("radii_margin_interval_lower")
    return {
        "Y_decimal": str(Y),
        "Z_decimal": str(Z),
        "Q_decimal": str(Q),
        "radius_decimal": str(r),
        "recomputed_lhs_decimal": str(lhs),
        "recomputed_margin_decimal": str(margin),
        "recomputed_relative_margin_decimal": str(rel),
        "reported_lhs": reported_lhs,
        "reported_margin": reported_margin,
        "reported_lhs_covers_recomputed": (
            reported_lhs is None or _dec(reported_lhs) >= lhs
        ),
        "reported_margin_not_above_recomputed_by_more_than_1e_minus_10": (
            reported_margin is None or _dec(reported_margin) <= margin + Decimal("1e-10")
        ),
        "positive_recomputed_margin": margin > Decimal("0"),
    }


def make_false_formal_evidence() -> Dict[str, bool]:
    return {k: False for k in REQUIRED_FORMAL_EVIDENCE_KEYS}


def build_formal_attachment_candidate(
    certificate: Mapping[str, Any],
    phase5c_summary: Mapping[str, Any],
    certificate_path: str,
    phase5c_summary_path: str,
    require_nu: Optional[float] = 1.001,
    require_radius: Optional[float] = 3e-5,
    prefer_cutoff: Optional[str] = "full",
    prefer_tail_start: Optional[float] = 0.90,
    min_anchor_k: Optional[float] = 0.971635,
    max_z: float = 0.5,
    min_relative_margin: float = 0.25,
    min_margin: float = 0.0,
) -> Dict[str, Any]:
    cand = choose_phase5c_candidate(
        phase5c_summary,
        require_nu=require_nu,
        require_radius=require_radius,
        prefer_cutoff=prefer_cutoff,
        prefer_tail_start=prefer_tail_start,
        min_anchor_k=min_anchor_k,
    )
    constants = normalize_candidate_constants(cand)
    replay = decimal_radii_replay(constants)

    evidence_checks = {
        "candidate_matches_required_nu": require_nu is None or abs(_safe_float(constants["nu"]) - float(require_nu)) < 5e-13,
        "candidate_matches_required_radius": require_radius is None or abs(_safe_float(constants["radius"]) - float(require_radius)) < 5e-13,
        "candidate_matches_required_cutoff": prefer_cutoff is None or str(constants["cutoff_spec"]) == str(prefer_cutoff),
        "candidate_matches_required_tail_start": prefer_tail_start is None or abs(_safe_float(constants["tail_start_frac"]) - float(prefer_tail_start)) < 5e-13,
        "anchor_meets_required_min": min_anchor_k is None or _safe_float(constants["K"], -float("inf")) >= float(min_anchor_k) - 5e-13,
        "finite_YZQr": all(_finite(constants[k]) for k in ("Y_interval_upper", "Z_interval_upper", "Q_interval_upper", "radius")),
        "positive_recomputed_margin": bool(replay["positive_recomputed_margin"]),
        "relative_margin_above_threshold": _safe_float(constants.get("radii_relative_margin_interval_lower"), float("nan")) >= min_relative_margin,
        "reported_margin_above_threshold": _safe_float(constants.get("radii_margin_interval_lower"), float("nan")) >= min_margin,
        "Z_below_threshold": _safe_float(constants.get("Z_interval_upper"), float("inf")) <= max_z,
        "small_divisor_positive": _safe_float(constants.get("small_divisor_min_denominator_lower"), 0.0) > 0.0,
        "cohomology_inverse_finite": _finite(constants.get("cohomology_inverse_linf_resolved_upper")),
        "source_record_path_present": bool(constants.get("source_record_path")),
    }

    component_readiness_passed = all(evidence_checks.values())
    formal_evidence = make_false_formal_evidence()

    attachment = {
        "schema": ATTACHMENT_SCHEMA,
        "phase": "5F",
        "status": "formal-attachment-candidate-generated",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "component_readiness_passed": component_readiness_passed,
        "formal_evidence": formal_evidence,
        "required_formal_evidence_keys": REQUIRED_FORMAL_EVIDENCE_KEYS,
        "formal_evidence_policy": {
            "all_required_flags_must_be_true_for_phase5e_promotion": True,
            "this_generator_sets_required_flags_false_by_design": True,
            "reason": "Phase 5F records diagnostic/nextafter evidence and exact missing proof obligations; it does not constitute an independently verified formal interval backend.",
        },
        "selected_constants": constants,
        "decimal_radii_replay": replay,
        "component_readiness_checks": evidence_checks,
        "source_paths": {
            "certificate_path": certificate_path,
            "phase5c_summary_path": phase5c_summary_path,
            "phase5c_record_path": constants.get("source_record_path"),
            "npz_path": constants.get("npz_path"),
        },
        "source_hashes": {
            "certificate_sha256": _sha256_file(certificate_path),
            "phase5c_summary_sha256": _sha256_file(phase5c_summary_path),
        },
        "open_requirements_for_promotion": [
            "Replace diagnostic/nextafter bounds with independently verified outward-rounded interval computations.",
            "Set formal_evidence.formal_interval_backend=true only after that backend exists and is replayed independently.",
            "Prove residual, small-divisor, cohomology inverse, frame/reducibility, nonlinear, and tail bounds in the formal backend.",
            "Prove branch/chart compatibility and final threshold-graph consumption.",
            "Rerun Phase 5E; theorem promotion must remain fail-closed until all formal evidence flags are true and thresholds hold.",
        ],
        "certificate_snapshot": {
            "schema": certificate.get("schema"),
            "diagnostic_only": certificate.get("diagnostic_only", find_first_key(certificate, "diagnostic_only")),
            "theorem_facing": certificate.get("theorem_facing", find_first_key(certificate, "theorem_facing")),
            "promotion_allowed": certificate.get("promotion_allowed", find_first_key(certificate, "promotion_allowed")),
            "lower_anchor_K": find_first_key(certificate, "lower_anchor_K", constants.get("K")),
        },
    }
    attachment["attachment_sha256"] = _sha256_json_payload(attachment)
    return attachment


def replay_formal_attachment_candidate(
    attachment: Mapping[str, Any],
    min_anchor_k: float = 0.971635,
    max_z: float = 0.5,
    min_relative_margin: float = 0.25,
    require_nu: Optional[float] = 1.001,
    require_radius: Optional[float] = 3e-5,
    require_cutoff: Optional[str] = "full",
    require_tail_start: Optional[float] = 0.90,
) -> Dict[str, Any]:
    constants = attachment.get("selected_constants", {}) if isinstance(attachment, Mapping) else {}
    formal_evidence = attachment.get("formal_evidence", {}) if isinstance(attachment, Mapping) else {}
    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("schema", attachment.get("schema") == ATTACHMENT_SCHEMA, attachment.get("schema"))
    add("diagnostic_only_true", attachment.get("diagnostic_only") is True, attachment.get("diagnostic_only"))
    add("theorem_facing_false", attachment.get("theorem_facing") is False, attachment.get("theorem_facing"))
    add("promotion_allowed_false", attachment.get("promotion_allowed") is False, attachment.get("promotion_allowed"))
    add("formal_attachment_ok_false", attachment.get("formal_attachment_ok") is False, attachment.get("formal_attachment_ok"))
    add("component_readiness_passed", attachment.get("component_readiness_passed") is True, attachment.get("component_readiness_passed"))
    add("formal_evidence_dict_present", isinstance(formal_evidence, Mapping), list(formal_evidence) if isinstance(formal_evidence, Mapping) else None)
    missing = [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if k not in formal_evidence]
    add("all_required_formal_evidence_keys_present", not missing, missing)
    true_flags = [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if formal_evidence.get(k) is True]
    false_flags = [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if formal_evidence.get(k) is False]
    add("required_formal_evidence_flags_false_for_now", len(true_flags) == 0 and len(false_flags) == len(REQUIRED_FORMAL_EVIDENCE_KEYS), {"true_flags": true_flags, "false_count": len(false_flags)})

    add("anchor_meets_min", _safe_float(constants.get("K"), -float("inf")) >= min_anchor_k - 5e-13, constants.get("K"))
    add("nu_matches", require_nu is None or abs(_safe_float(constants.get("nu")) - require_nu) < 5e-13, constants.get("nu"))
    add("radius_matches", require_radius is None or abs(_safe_float(constants.get("radius")) - require_radius) < 5e-13, constants.get("radius"))
    add("cutoff_matches", require_cutoff is None or str(constants.get("cutoff_spec")) == str(require_cutoff), constants.get("cutoff_spec"))
    add("tail_start_matches", require_tail_start is None or abs(_safe_float(constants.get("tail_start_frac")) - require_tail_start) < 5e-13, constants.get("tail_start_frac"))
    add("finite_YZQr", all(_finite(constants.get(k)) for k in ("Y_interval_upper", "Z_interval_upper", "Q_interval_upper", "radius")), [constants.get(k) for k in ("Y_interval_upper", "Z_interval_upper", "Q_interval_upper", "radius")])
    replay = decimal_radii_replay(constants) if constants else {"positive_recomputed_margin": False}
    add("positive_recomputed_margin", bool(replay.get("positive_recomputed_margin")), replay.get("recomputed_margin_decimal"))
    add("relative_margin_threshold", _safe_float(constants.get("radii_relative_margin_interval_lower"), -float("inf")) >= min_relative_margin, constants.get("radii_relative_margin_interval_lower"))
    add("Z_below_threshold", _safe_float(constants.get("Z_interval_upper"), float("inf")) <= max_z, constants.get("Z_interval_upper"))
    add("small_divisor_positive", _safe_float(constants.get("small_divisor_min_denominator_lower"), 0.0) > 0.0, constants.get("small_divisor_min_denominator_lower"))
    add("cohomology_inverse_finite", _finite(constants.get("cohomology_inverse_linf_resolved_upper")), constants.get("cohomology_inverse_linf_resolved_upper"))

    failed = [c for c in checks if not c["ok"]]
    promotion_ready = False  # By design for Phase 5F candidate artifacts.
    return {
        "schema": PHASE5F_REPLAY_SCHEMA,
        "status": "phase5f-attachment-candidate-replay-complete",
        "passed": not failed,
        "promotion_ready": promotion_ready,
        "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_FORMAL_EVIDENCE_FLAGS_TRUE",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "checks": checks,
        "failed_checks": failed,
        "decimal_radii_replay": replay,
        "missing_formal_evidence_flags": [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if formal_evidence.get(k) is not True],
        "selected_constants": constants,
    }


def assemble_phase5f(
    certificate_path: str,
    phase5c_summary_path: str,
    out_dir: str,
    require_nu: float = 1.001,
    require_radius: float = 3e-5,
    require_cutoff: str = "full",
    require_tail_start: float = 0.90,
    min_anchor_k: float = 0.971635,
    max_z: float = 0.5,
    min_relative_margin: float = 0.25,
    min_margin: float = 0.0,
    force: bool = False,
) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    attach_path = out / "phase5f_formal_interval_attachment_CANDIDATE.json"
    summary_path = out / "phase5f_attachment_candidate_summary.json"
    replay_path = out / "phase5f_attachment_candidate_replay_summary.json"
    if attach_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {attach_path}; use --force")

    cert = load_json(certificate_path)
    p5c = load_json(phase5c_summary_path)
    attachment = build_formal_attachment_candidate(
        cert,
        p5c,
        certificate_path=certificate_path,
        phase5c_summary_path=phase5c_summary_path,
        require_nu=require_nu,
        require_radius=require_radius,
        prefer_cutoff=require_cutoff,
        prefer_tail_start=require_tail_start,
        min_anchor_k=min_anchor_k,
        max_z=max_z,
        min_relative_margin=min_relative_margin,
        min_margin=min_margin,
    )
    _atomic_write_json(attach_path, attachment)
    replay = replay_formal_attachment_candidate(
        attachment,
        min_anchor_k=min_anchor_k,
        max_z=max_z,
        min_relative_margin=min_relative_margin,
        require_nu=require_nu,
        require_radius=require_radius,
        require_cutoff=require_cutoff,
        require_tail_start=require_tail_start,
    )
    _atomic_write_json(replay_path, replay)

    summary = {
        "schema": PHASE5F_SUMMARY_SCHEMA,
        "status": "phase5f-formal-attachment-candidate-assembled",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "attachment_path": str(attach_path),
        "replay_path": str(replay_path),
        "replay_passed": replay["passed"],
        "promotion_ready": False,
        "expected_phase5e_decision": replay["expected_phase5e_decision"],
        "selected_constants": attachment["selected_constants"],
        "component_readiness_passed": attachment["component_readiness_passed"],
        "formal_evidence": attachment["formal_evidence"],
        "missing_formal_evidence_flags": replay["missing_formal_evidence_flags"],
        "open_requirements_for_promotion": attachment["open_requirements_for_promotion"],
    }
    _atomic_write_json(summary_path, summary)
    return summary


def summarize_phase5f(summary_path: str, out_path: Optional[str] = None) -> Dict[str, Any]:
    summary = load_json(summary_path)
    compact = {
        "schema": "theorem_iii_trackb_phase5f_compact_report_v1",
        "status": summary.get("status"),
        "diagnostic_only": summary.get("diagnostic_only"),
        "theorem_facing": summary.get("theorem_facing"),
        "promotion_allowed": summary.get("promotion_allowed"),
        "formal_attachment_ok": summary.get("formal_attachment_ok"),
        "replay_passed": summary.get("replay_passed"),
        "promotion_ready": summary.get("promotion_ready"),
        "expected_phase5e_decision": summary.get("expected_phase5e_decision"),
        "attachment_path": summary.get("attachment_path"),
        "replay_path": summary.get("replay_path"),
        "selected_constants": summary.get("selected_constants"),
        "missing_formal_evidence_flags": summary.get("missing_formal_evidence_flags"),
        "open_requirements_for_promotion": summary.get("open_requirements_for_promotion"),
    }
    if out_path:
        _atomic_write_json(out_path, compact)
    return compact
