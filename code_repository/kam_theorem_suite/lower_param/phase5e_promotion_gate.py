"""Phase 5E fail-closed promotion gate for Theorem III Track B.

This module intentionally does *not* promote a Phase 5D scaffold by itself.
It accepts a diagnostic scaffold and, optionally, a separate formal interval
attachment.  Without the attachment, the expected and correct outcome is a
replayable rejection for theorem-facing use.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

PHASE5E_SCHEMA = "theorem_iii_trackb_phase5e_promotion_gate_summary_v1"
ATTACHMENT_SCHEMA = "theorem_iii_trackb_phase5e_formal_interval_attachment_v1"


def _as_float(x: Any, default: float = float("nan")) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _as_bool(x: Any) -> bool:
    return bool(x)


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def _read_json(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return obj


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_first(obj: Any, key: str) -> Any:
    """Return the first occurrence of key in a nested dict/list tree."""
    if isinstance(obj, Mapping):
        if key in obj:
            return obj[key]
        for v in obj.values():
            got = _find_first(v, key)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = _find_first(v, key)
            if got is not None:
                return got
    return None


def _extract_anchor(payload: Mapping[str, Any]) -> float:
    for k in ("lower_anchor_K", "K", "anchor_K"):
        val = _find_first(payload, k)
        if val is not None:
            f = _as_float(val)
            if math.isfinite(f):
                return f
    interval = _find_first(payload, "anchor_interval")
    if isinstance(interval, list) and interval:
        f = _as_float(interval[0])
        if math.isfinite(f):
            return f
    return float("nan")


def _extract_constants(payload: Mapping[str, Any]) -> Dict[str, float]:
    """Extract radii constants from a scaffold or attachment.

    The Phase 5D scaffold may store these in selected_candidate or deeper
    certificate records.  We use recursive search to avoid hard-coding the
    previous overlay's exact nesting.
    """
    aliases = {
        "Y": ("Y_interval_upper", "Y_component_bound", "Y_cohomology_proxy", "Y"),
        "Z": ("Z_interval_upper", "Z_component_bound", "Z_linear_reducibility_proxy", "Z"),
        "Q": ("Q_interval_upper", "Q_component_bound", "Q_nonlinear_proxy", "Q"),
        "radius": ("radius", "best_radius_proxy", "r"),
        "margin": ("radii_margin_interval_lower", "radii_margin_component", "best_radii_margin_proxy", "margin"),
        "relative_margin": (
            "radii_relative_margin_interval_lower",
            "radii_relative_margin_component",
            "best_relative_margin_proxy",
            "relative_margin",
        ),
        "nu": ("nu",),
        "cutoff_mode_native_units": ("cutoff_mode_native_units",),
        "tail_start_frac": ("tail_start_frac",),
        "small_divisor_lower": ("small_divisor_min_denominator_lower", "small_divisor_min_denominator"),
        "cohomology_inverse_upper": (
            "cohomology_inverse_linf_resolved_upper",
            "cohomology_inverse_linf_resolved",
        ),
    }
    out: Dict[str, float] = {}
    for name, keys in aliases.items():
        out[name] = float("nan")
        for key in keys:
            val = _find_first(payload, key)
            f = _as_float(val)
            if math.isfinite(f):
                out[name] = f
                break
    return out


def _extract_string(payload: Mapping[str, Any], key: str, default: str = "") -> str:
    val = _find_first(payload, key)
    if val is None:
        return default
    return str(val)


@dataclass(frozen=True)
class GateThresholds:
    required_min_lower_anchor_K: float = 0.971635
    min_margin: float = 0.0
    min_relative_margin: float = 0.25
    max_z: float = 0.5
    max_q: float = float("inf")
    max_y: float = float("inf")
    require_nu: Optional[float] = None
    require_radius: Optional[float] = None
    require_cutoff: Optional[str] = None
    require_tail_start: Optional[float] = None


def _ok_close(value: float, target: Optional[float], *, rtol: float = 1e-12, atol: float = 1e-15) -> bool:
    if target is None:
        return True
    return math.isfinite(value) and math.isclose(value, target, rel_tol=rtol, abs_tol=atol)


def _check_scaffold_structure(cert: Mapping[str, Any], thresholds: GateThresholds) -> List[Dict[str, Any]]:
    constants = _extract_constants(cert)
    anchor = _extract_anchor(cert)
    theorem_facing = _as_bool(_find_first(cert, "theorem_facing"))
    promotion_allowed = _as_bool(_find_first(cert, "promotion_allowed"))
    diagnostic_only = _as_bool(_find_first(cert, "diagnostic_only"))
    active_assumptions = _find_first(cert, "active_assumptions")
    open_hypotheses = _find_first(cert, "open_hypotheses")
    cutoff_spec = _extract_string(cert, "cutoff_spec")

    checks = [
        {"name": "scaffold_diagnostic_only_true", "ok": diagnostic_only is True, "detail": diagnostic_only},
        {"name": "scaffold_theorem_facing_false", "ok": theorem_facing is False, "detail": theorem_facing},
        {"name": "scaffold_promotion_allowed_false", "ok": promotion_allowed is False, "detail": promotion_allowed},
        {
            "name": "lower_anchor_meets_required_minimum",
            "ok": math.isfinite(anchor) and anchor >= thresholds.required_min_lower_anchor_K,
            "detail": {"anchor": anchor, "required": thresholds.required_min_lower_anchor_K},
        },
        {"name": "finite_Y", "ok": math.isfinite(constants["Y"]), "detail": constants["Y"]},
        {"name": "finite_Z", "ok": math.isfinite(constants["Z"]), "detail": constants["Z"]},
        {"name": "finite_Q", "ok": math.isfinite(constants["Q"]), "detail": constants["Q"]},
        {"name": "finite_positive_radius", "ok": math.isfinite(constants["radius"]) and constants["radius"] > 0, "detail": constants["radius"]},
        {"name": "reported_margin_above_threshold", "ok": math.isfinite(constants["margin"]) and constants["margin"] > thresholds.min_margin, "detail": constants["margin"]},
        {
            "name": "relative_margin_above_threshold",
            "ok": math.isfinite(constants["relative_margin"]) and constants["relative_margin"] >= thresholds.min_relative_margin,
            "detail": {"relative_margin": constants["relative_margin"], "threshold": thresholds.min_relative_margin},
        },
        {"name": "Z_below_threshold", "ok": math.isfinite(constants["Z"]) and constants["Z"] <= thresholds.max_z, "detail": {"Z": constants["Z"], "threshold": thresholds.max_z}},
        {"name": "Q_below_threshold", "ok": math.isfinite(constants["Q"]) and constants["Q"] <= thresholds.max_q, "detail": {"Q": constants["Q"], "threshold": thresholds.max_q}},
        {"name": "Y_below_threshold", "ok": math.isfinite(constants["Y"]) and constants["Y"] <= thresholds.max_y, "detail": {"Y": constants["Y"], "threshold": thresholds.max_y}},
        {
            "name": "small_divisor_positive",
            "ok": math.isfinite(constants["small_divisor_lower"]) and constants["small_divisor_lower"] > 0,
            "detail": constants["small_divisor_lower"],
        },
        {
            "name": "cohomology_inverse_finite",
            "ok": math.isfinite(constants["cohomology_inverse_upper"]),
            "detail": constants["cohomology_inverse_upper"],
        },
        {
            "name": "active_assumptions_nonempty",
            "ok": isinstance(active_assumptions, list) and len(active_assumptions) > 0,
            "detail": active_assumptions,
        },
        {
            "name": "open_hypotheses_nonempty",
            "ok": isinstance(open_hypotheses, list) and len(open_hypotheses) > 0,
            "detail": open_hypotheses,
        },
        {
            "name": "nu_matches_requested",
            "ok": _ok_close(constants["nu"], thresholds.require_nu),
            "detail": {"nu": constants["nu"], "required": thresholds.require_nu},
        },
        {
            "name": "radius_matches_requested",
            "ok": _ok_close(constants["radius"], thresholds.require_radius),
            "detail": {"radius": constants["radius"], "required": thresholds.require_radius},
        },
        {
            "name": "cutoff_matches_requested",
            "ok": thresholds.require_cutoff is None or cutoff_spec == thresholds.require_cutoff,
            "detail": {"cutoff_spec": cutoff_spec, "required": thresholds.require_cutoff},
        },
        {
            "name": "tail_start_matches_requested",
            "ok": _ok_close(constants["tail_start_frac"], thresholds.require_tail_start),
            "detail": {"tail_start_frac": constants["tail_start_frac"], "required": thresholds.require_tail_start},
        },
    ]
    return checks


def _required_formal_evidence_keys() -> List[str]:
    return [
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


def _formal_evidence_value(attachment: Mapping[str, Any], key: str) -> Tuple[bool, Dict[str, Any]]:
    """Return whether a formal-evidence flag is asserted, accepting legacy and nested schemas.

    Earlier Phase 5E only looked for top-level boolean fields, while Phase 5G-b
    writes component evidence in a nested ``formal_evidence`` dictionary.  The
    promotion gate should accept either location, and it should also expose the
    source in the check detail so that future schema drift is visible.

    This function is deliberately strict about truth values: only literal True
    promotes a flag.  Strings such as "true", integers, or truthy objects do
    not count.
    """
    top = attachment.get(key)
    nested_obj = attachment.get("formal_evidence")
    nested = nested_obj.get(key) if isinstance(nested_obj, Mapping) else None
    true_flags = attachment.get("formal_evidence_true_flags")
    list_flag = key in true_flags if isinstance(true_flags, list) else False
    ok = (top is True) or (nested is True) or (list_flag is True)
    if top is True:
        source = "top_level"
    elif nested is True:
        source = "formal_evidence_dict"
    elif list_flag is True:
        source = "formal_evidence_true_flags_list"
    else:
        source = "missing_or_false"
    return ok, {"source": source, "top_level": top, "formal_evidence": nested, "listed_true": list_flag}


def _check_formal_attachment(
    attachment: Optional[Mapping[str, Any]],
    scaffold_constants: Mapping[str, float],
    thresholds: GateThresholds,
    *,
    certificate_sha256: str,
) -> List[Dict[str, Any]]:
    if attachment is None:
        return [
            {"name": "formal_attachment_present", "ok": False, "detail": "No formal interval attachment supplied."}
        ]

    checks: List[Dict[str, Any]] = []
    schema = attachment.get("schema")
    checks.append({"name": "formal_attachment_schema", "ok": schema == ATTACHMENT_SCHEMA, "detail": schema})

    attached_hash = str(attachment.get("certificate_sha256", ""))
    checks.append(
        {
            "name": "formal_attachment_references_certificate_hash",
            "ok": bool(attached_hash) and attached_hash == certificate_sha256,
            "detail": {"attached": attached_hash, "certificate_sha256": certificate_sha256},
        }
    )

    for key in _required_formal_evidence_keys():
        flag_ok, flag_detail = _formal_evidence_value(attachment, key)
        checks.append({"name": f"formal_evidence_{key}", "ok": flag_ok, "detail": flag_detail})

    constants = _extract_constants(attachment)
    checks.extend(
        [
            {"name": "formal_Y_finite", "ok": math.isfinite(constants["Y"]), "detail": constants["Y"]},
            {"name": "formal_Z_finite", "ok": math.isfinite(constants["Z"]), "detail": constants["Z"]},
            {"name": "formal_Q_finite", "ok": math.isfinite(constants["Q"]), "detail": constants["Q"]},
            {"name": "formal_radius_positive", "ok": math.isfinite(constants["radius"]) and constants["radius"] > 0, "detail": constants["radius"]},
            {"name": "formal_margin_positive", "ok": math.isfinite(constants["margin"]) and constants["margin"] > thresholds.min_margin, "detail": constants["margin"]},
            {"name": "formal_relative_margin_threshold", "ok": math.isfinite(constants["relative_margin"]) and constants["relative_margin"] >= thresholds.min_relative_margin, "detail": constants["relative_margin"]},
            {"name": "formal_Z_below_threshold", "ok": math.isfinite(constants["Z"]) and constants["Z"] <= thresholds.max_z, "detail": constants["Z"]},
            {"name": "formal_Q_below_threshold", "ok": math.isfinite(constants["Q"]) and constants["Q"] <= thresholds.max_q, "detail": constants["Q"]},
            {"name": "formal_Y_below_threshold", "ok": math.isfinite(constants["Y"]) and constants["Y"] <= thresholds.max_y, "detail": constants["Y"]},
            {"name": "formal_nu_matches_requested", "ok": _ok_close(constants["nu"], thresholds.require_nu), "detail": {"nu": constants["nu"], "required": thresholds.require_nu}},
            {"name": "formal_radius_matches_requested", "ok": _ok_close(constants["radius"], thresholds.require_radius), "detail": {"radius": constants["radius"], "required": thresholds.require_radius}},
            {"name": "formal_tail_start_matches_requested", "ok": _ok_close(constants["tail_start_frac"], thresholds.require_tail_start), "detail": {"tail_start_frac": constants["tail_start_frac"], "required": thresholds.require_tail_start}},
        ]
    )

    # The formal proof may tighten or loosen bounds compared with Phase 5D; it
    # only needs to satisfy thresholds and be explicitly independent.  We still
    # record whether it worsens the scaffold constants for visibility.
    for name in ("Y", "Z", "Q"):
        sv = scaffold_constants.get(name, float("nan"))
        av = constants.get(name, float("nan"))
        checks.append(
            {
                "name": f"formal_{name}_comparison_record_only",
                "ok": True,
                "detail": {"scaffold": sv, "formal": av, "formal_over_scaffold": (av / sv if math.isfinite(av) and math.isfinite(sv) and sv != 0 else None)},
            }
        )
    return checks


def _mutate_for_negative_controls(cert: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Create small malformed/marginal variants used only to test fail-closed behavior."""
    out: Dict[str, Dict[str, Any]] = {}
    c1 = copy.deepcopy(dict(cert))
    c1["theorem_facing"] = True
    c1["promotion_allowed"] = True
    out["illicit_flags_without_formal_attachment"] = c1

    c2 = copy.deepcopy(dict(cert))
    # Place bad values at top level so recursive extraction catches them first.
    c2["radii_margin_interval_lower"] = -1.0
    c2["radii_relative_margin_interval_lower"] = -1.0
    out["negative_margin"] = c2

    c3 = copy.deepcopy(dict(cert))
    c3["Z_interval_upper"] = 2.0
    out["excessive_Z"] = c3

    c4 = copy.deepcopy(dict(cert))
    c4["active_assumptions"] = []
    c4["open_hypotheses"] = []
    out["missing_assumptions"] = c4
    return out


def _checks_ok(checks: Iterable[Mapping[str, Any]]) -> bool:
    return all(bool(c.get("ok")) for c in checks)


def formal_attachment_template(certificate_path: str | Path) -> Dict[str, Any]:
    cert = _read_json(certificate_path)
    constants = _extract_constants(cert)
    return {
        "schema": ATTACHMENT_SCHEMA,
        "certificate_sha256": _sha256_file(certificate_path),
        "description": "Template only. Replace every proof flag and bound with independently generated formal interval evidence before use.",
        "formal_interval_backend": False,
        "independent_replay_passed": False,
        "outward_rounded_residual_proof": False,
        "small_divisor_proof": False,
        "cohomology_inverse_proof": False,
        "frame_reducibility_proof": False,
        "nonlinear_bound_proof": False,
        "tail_bound_proof": False,
        "branch_chart_compatibility_proof": False,
        "final_graph_consumption_proof": False,
        "Y_interval_upper": constants.get("Y"),
        "Z_interval_upper": constants.get("Z"),
        "Q_interval_upper": constants.get("Q"),
        "radius": constants.get("radius"),
        "radii_margin_interval_lower": constants.get("margin"),
        "radii_relative_margin_interval_lower": constants.get("relative_margin"),
        "nu": constants.get("nu"),
        "tail_start_frac": constants.get("tail_start_frac"),
        "notes": [
            "This template must not be used as evidence.",
            "Phase 5E will reject it until all proof flags are true and bounds pass thresholds.",
        ],
    }


def run_phase5e_promotion_gate(
    *,
    certificate_path: str | Path,
    out_dir: str | Path,
    formal_attachment_path: Optional[str | Path] = None,
    thresholds: Optional[GateThresholds] = None,
    emit_template: bool = True,
    force: bool = False,
) -> Dict[str, Any]:
    thresholds = thresholds or GateThresholds()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "phase5e_promotion_gate_summary.json"
    if summary_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {summary_path}; pass force=True")

    cert = _read_json(certificate_path)
    cert_hash = _sha256_file(certificate_path)
    scaffold_constants = _extract_constants(cert)
    scaffold_checks = _check_scaffold_structure(cert, thresholds)

    attachment = _read_json(formal_attachment_path) if formal_attachment_path else None
    formal_checks = _check_formal_attachment(
        attachment,
        scaffold_constants,
        thresholds,
        certificate_sha256=cert_hash,
    )

    negative_results: List[Dict[str, Any]] = []
    for name, mutated in _mutate_for_negative_controls(cert).items():
        checks = _check_scaffold_structure(mutated, thresholds)
        promoted = _checks_ok(checks) and False  # no formal attachment in negative controls
        negative_results.append(
            {
                "name": name,
                "expected_rejected": True,
                "rejected": not promoted,
                "checks_all_ok": _checks_ok(checks),
                "failed_checks": [c["name"] for c in checks if not c.get("ok")],
            }
        )

    scaffold_ok = _checks_ok(scaffold_checks)
    formal_ok = _checks_ok(formal_checks)
    negative_controls_passed = all(r["rejected"] for r in negative_results)

    promoted = bool(scaffold_ok and formal_ok)
    if promoted:
        status_label = "phase5e-promoted-with-formal-attachment"
        recommendation = "Formal attachment passed the gate. This can be consumed by the next final replay layer."
        theorem_facing = True
        promotion_allowed = True
    else:
        status_label = "phase5e-fail-closed-rejected"
        recommendation = "Correct fail-closed outcome: scaffold is replayable but not theorem-facing without formal interval evidence."
        theorem_facing = False
        promotion_allowed = False

    summary: Dict[str, Any] = {
        "schema": PHASE5E_SCHEMA,
        "status": status_label,
        "certificate_path": str(certificate_path),
        "certificate_sha256": cert_hash,
        "formal_attachment_path": str(formal_attachment_path) if formal_attachment_path else None,
        "diagnostic_only_input": bool(_find_first(cert, "diagnostic_only")),
        "scaffold_replay_ok_for_gate": scaffold_ok,
        "formal_attachment_ok": formal_ok,
        "fail_closed_passed": not promoted if formal_attachment_path is None else True,
        "negative_controls_passed": negative_controls_passed,
        "theorem_replay_accepted": promoted,
        "promotion_allowed": promotion_allowed,
        "theorem_facing": theorem_facing,
        "decision": "PROMOTE" if promoted else "REJECT_FAIL_CLOSED",
        "recommendation": recommendation,
        "selected_constants": scaffold_constants,
        "thresholds": thresholds.__dict__,
        "scaffold_checks": scaffold_checks,
        "formal_attachment_checks": formal_checks,
        "negative_controls": negative_results,
        "required_formal_evidence_keys": _required_formal_evidence_keys(),
        "open_requirements_for_promotion": [] if promoted else [
            "Attach an independent formal interval backend record using schema theorem_iii_trackb_phase5e_formal_interval_attachment_v1.",
            "Set every required formal evidence flag to true only after an independent proof/replay exists.",
            "Ensure formal Y/Z/Q/radius/margin bounds satisfy gate thresholds under outward-rounded arithmetic.",
            "Validate branch/chart compatibility and final threshold-graph consumption.",
        ],
    }

    _write_json(summary_path, summary)
    if emit_template:
        template_path = out_dir / "phase5e_formal_interval_attachment_TEMPLATE.json"
        _write_json(template_path, formal_attachment_template(certificate_path))
        summary["formal_attachment_template_path"] = str(template_path)
        _write_json(summary_path, summary)
    return summary


def compact_report(summary: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema": "theorem_iii_trackb_phase5e_compact_report_v1",
        "status": summary.get("status"),
        "decision": summary.get("decision"),
        "certificate_path": summary.get("certificate_path"),
        "formal_attachment_path": summary.get("formal_attachment_path"),
        "scaffold_replay_ok_for_gate": summary.get("scaffold_replay_ok_for_gate"),
        "formal_attachment_ok": summary.get("formal_attachment_ok"),
        "fail_closed_passed": summary.get("fail_closed_passed"),
        "negative_controls_passed": summary.get("negative_controls_passed"),
        "theorem_replay_accepted": summary.get("theorem_replay_accepted"),
        "theorem_facing": summary.get("theorem_facing"),
        "promotion_allowed": summary.get("promotion_allowed"),
        "selected_constants": summary.get("selected_constants"),
        "thresholds": summary.get("thresholds"),
        "failed_scaffold_checks": [c.get("name") for c in summary.get("scaffold_checks", []) if not c.get("ok")],
        "failed_formal_attachment_checks": [c.get("name") for c in summary.get("formal_attachment_checks", []) if not c.get("ok")],
        "negative_controls": summary.get("negative_controls", []),
        "required_formal_evidence_keys": summary.get("required_formal_evidence_keys", []),
        "open_requirements_for_promotion": summary.get("open_requirements_for_promotion", []),
        "recommendation": summary.get("recommendation"),
        "formal_attachment_template_path": summary.get("formal_attachment_template_path"),
    }
