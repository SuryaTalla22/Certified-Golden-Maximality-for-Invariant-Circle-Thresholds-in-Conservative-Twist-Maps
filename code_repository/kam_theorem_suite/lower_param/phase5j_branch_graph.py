"""Phase 5J branch/chart compatibility and final graph-consumption components.

This module is intentionally conservative and fail-closed.  It does not promote a
certificate to theorem-facing status; it only appends/replays two integration
proof-object flags to an already hash-bound Phase 5I attachment:

    branch_chart_compatibility_proof = true
    final_graph_consumption_proof = true

The global flags remain false:

    formal_interval_backend = false
    independent_replay_passed = false

The code is schema-tolerant because earlier Phase 5 artifacts evolved through
several diagnostic schemas.  It checks the fields that are needed for the lower
anchor contract and refuses to set the two new flags unless the prior component
flags and the chosen configuration are consistent.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

REQUIRED_PRIOR_FLAGS = [
    "outward_rounded_residual_proof",
    "small_divisor_proof",
    "cohomology_inverse_proof",
    "frame_reducibility_proof",
    "nonlinear_bound_proof",
    "tail_bound_proof",
]

PHASE5J_FLAGS = [
    "branch_chart_compatibility_proof",
    "final_graph_consumption_proof",
]

GLOBAL_FLAGS_STILL_FALSE = [
    "formal_interval_backend",
    "independent_replay_passed",
]

ALL_FORMAL_FLAGS = GLOBAL_FLAGS_STILL_FALSE + REQUIRED_PRIOR_FLAGS + PHASE5J_FLAGS


def _read_json(path: str | os.PathLike[str]) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | os.PathLike[str], payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_json_safe(payload), f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    os.replace(tmp, path)


def _json_safe(x: Any) -> Any:
    """Convert numpy-ish/scalar/nonfinite values into strict JSON-safe objects."""
    # Avoid importing numpy in this utility; support objects with item().
    if hasattr(x, "item") and not isinstance(x, (str, bytes, bytearray)):
        try:
            return _json_safe(x.item())
        except Exception:
            pass
    if isinstance(x, dict):
        return {str(k): _json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_safe(v) for v in x]
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    return x


def _sha256_raw(path: str | os.PathLike[str]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _as_float(x: Any, default: float = math.nan) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _close(a: Any, b: Any, tol: float = 1e-12) -> bool:
    af = _as_float(a)
    bf = _as_float(b)
    return math.isfinite(af) and math.isfinite(bf) and abs(af - bf) <= tol * max(1.0, abs(af), abs(bf))


def _formal_evidence(att: Mapping[str, Any]) -> Dict[str, Any]:
    fe = att.get("formal_evidence")
    if isinstance(fe, dict):
        return dict(fe)
    # Legacy compact attachments sometimes use a list of true flags.
    flags = {k: False for k in ALL_FORMAL_FLAGS}
    for k in att.get("formal_evidence_true_flags", []) or []:
        flags[str(k)] = True
    return flags


def _set_formal_flag(att: MutableMapping[str, Any], key: str, value: bool) -> None:
    fe = att.setdefault("formal_evidence", {})
    if not isinstance(fe, dict):
        fe = {}
        att["formal_evidence"] = fe
    fe[key] = bool(value)


def _flag_true(att: Mapping[str, Any], key: str) -> bool:
    if att.get(key) is True:
        return True
    fe = att.get("formal_evidence")
    if isinstance(fe, dict) and fe.get(key) is True:
        return True
    flags = att.get("formal_evidence_true_flags")
    if isinstance(flags, list) and key in flags:
        return True
    return False


def _selected_constants(att: Mapping[str, Any]) -> Dict[str, Any]:
    for key in ("selected_constants", "constants", "selected_candidate"):
        val = att.get(key)
        if isinstance(val, dict):
            return dict(val)
    return {}


def _find_key(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            ans = _find_key(v, key)
            if ans is not None:
                return ans
    elif isinstance(obj, list):
        for v in obj:
            ans = _find_key(v, key)
            if ans is not None:
                return ans
    return None


def _certificate_lower_anchor(cert: Mapping[str, Any], constants: Mapping[str, Any]) -> float:
    for key in ("lower_anchor_K", "K"):
        val = _find_key(cert, key)
        if val is not None:
            f = _as_float(val)
            if math.isfinite(f):
                return f
    return _as_float(constants.get("K"))


def _certificate_family(cert: Mapping[str, Any]) -> str:
    val = _find_key(cert, "family")
    return str(val) if val is not None else "standard_sine_twist_map"


def _certificate_omega(cert: Mapping[str, Any]) -> str:
    val = _find_key(cert, "omega")
    if val is None:
        return "golden"
    return str(val)


def _true_flags(att: Mapping[str, Any]) -> List[str]:
    return [k for k in ALL_FORMAL_FLAGS if _flag_true(att, k)]


def _missing_flags(att: Mapping[str, Any]) -> List[str]:
    return [k for k in ALL_FORMAL_FLAGS if not _flag_true(att, k)]


def _component_summary(att: Mapping[str, Any]) -> Dict[str, Any]:
    # Keep compact but useful details for replay/reporting.
    out: Dict[str, Any] = {}
    for k in (
        "branch_chart_component",
        "final_graph_consumption_component",
        "nonlinear_component",
        "tail_component",
        "frame_reducibility_component",
        "cohomology_inverse_component",
        "residual_component",
        "small_divisor_component",
    ):
        if isinstance(att.get(k), dict):
            out[k] = att[k]
    return out


def check_phase5j_conditions(
    certificate: Mapping[str, Any],
    base_attachment: Mapping[str, Any],
    certificate_hash: str,
    *,
    required_min_lower_anchor_k: float,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    expected_family: str,
    expected_omega: str,
    min_relative_margin: float,
    max_z: float,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return branch and graph component dictionaries.

    The components are proof-object summaries.  They only pass if the local
    lower-anchor attachment is hash-bound, has all prior component flags, and
    matches the selected theorem-graph contract.
    """
    constants = _selected_constants(base_attachment)
    reported_hash = str(base_attachment.get("certificate_sha256", ""))
    lower_anchor = _certificate_lower_anchor(certificate, constants)
    family = _certificate_family(certificate)
    omega = _certificate_omega(certificate)

    prior_flags_ok = all(_flag_true(base_attachment, k) for k in REQUIRED_PRIOR_FLAGS)
    hash_ok = bool(reported_hash) and reported_hash == certificate_hash
    config_ok = (
        _close(constants.get("nu"), require_nu)
        and _close(constants.get("radius"), require_radius)
        and str(constants.get("cutoff_spec")) == str(require_cutoff)
        and _close(constants.get("tail_start_frac"), require_tail_start)
    )
    lower_anchor_ok = math.isfinite(lower_anchor) and lower_anchor >= required_min_lower_anchor_k
    family_ok = str(family) == str(expected_family)
    omega_ok = str(omega).lower() == str(expected_omega).lower()
    rel_margin = _as_float(constants.get("radii_relative_margin_interval_lower"))
    margin_ok = math.isfinite(rel_margin) and rel_margin >= min_relative_margin
    z = _as_float(constants.get("Z_interval_upper"))
    z_ok = math.isfinite(z) and z <= max_z

    branch_ok = bool(
        hash_ok
        and prior_flags_ok
        and config_ok
        and lower_anchor_ok
        and family_ok
        and omega_ok
        and margin_ok
        and z_ok
    )

    branch_component = {
        "component_ok": branch_ok,
        "certificate_sha256": certificate_hash,
        "attachment_certificate_sha256": reported_hash,
        "hash_binding_ok": hash_ok,
        "prior_local_component_flags_ok": prior_flags_ok,
        "family": family,
        "expected_family": expected_family,
        "family_ok": family_ok,
        "omega": omega,
        "expected_omega": expected_omega,
        "omega_ok": omega_ok,
        "lower_anchor_K": lower_anchor,
        "required_min_lower_anchor_K": required_min_lower_anchor_k,
        "lower_anchor_ok": lower_anchor_ok,
        "nu": _as_float(constants.get("nu")),
        "required_nu": require_nu,
        "radius": _as_float(constants.get("radius")),
        "required_radius": require_radius,
        "cutoff_spec": constants.get("cutoff_spec"),
        "required_cutoff": require_cutoff,
        "tail_start_frac": _as_float(constants.get("tail_start_frac")),
        "required_tail_start_frac": require_tail_start,
        "configuration_ok": config_ok,
        "Z_interval_upper": z,
        "max_z": max_z,
        "Z_ok": z_ok,
        "relative_margin": rel_margin,
        "min_relative_margin": min_relative_margin,
        "relative_margin_ok": margin_ok,
        "branch_label": "golden_lower_anchor_direct_trackB",
        "chart_label": "standard_sine_twist_map_parameterization_chart",
        "compatibility_statement": (
            "The lower-anchor certificate constants match the branch/chart "
            "contract for the golden invariant circle in the standard sine "
            "twist map at the direct lower anchor."
        ),
    }

    graph_ok = bool(branch_ok)
    graph_component = {
        "component_ok": graph_ok,
        "consumes_branch_label": branch_component["branch_label"],
        "consumes_chart_label": branch_component["chart_label"],
        "lower_anchor_K": lower_anchor,
        "required_min_lower_anchor_K": required_min_lower_anchor_k,
        "anchor_consumed_as": "direct_lower_anchor",
        "does_not_claim_parameter_interval": True,
        "does_not_claim_mesh_corridor": True,
        "local_certificate_margin": _as_float(constants.get("radii_margin_interval_lower")),
        "local_certificate_relative_margin": rel_margin,
        "graph_consumption_statement": (
            "The final threshold graph may consume this object only as a direct "
            "lower-anchor persistence certificate at K >= required_min_lower_anchor_K; "
            "it does not by itself certify a full parameter interval or mesh corridor."
        ),
    }
    return branch_component, graph_component


def generate_phase5j_attachment(
    *,
    certificate_path: str,
    base_attachment_path: str,
    required_min_lower_anchor_k: float,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    expected_family: str,
    expected_omega: str,
    min_relative_margin: float,
    max_z: float,
    out_dir: str,
    force: bool = False,
) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    attachment_out = out / "phase5j_formal_interval_attachment_COMPONENTS.json"
    summary_out = out / "phase5j_component_summary.json"
    compact_out = out / "phase5j_compact_report.json"
    if attachment_out.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing {attachment_out}; use --force")

    cert = _read_json(certificate_path)
    base = _read_json(base_attachment_path)
    cert_hash = _sha256_raw(certificate_path)
    branch_component, graph_component = check_phase5j_conditions(
        cert,
        base,
        cert_hash,
        required_min_lower_anchor_k=required_min_lower_anchor_k,
        require_nu=require_nu,
        require_radius=require_radius,
        require_cutoff=require_cutoff,
        require_tail_start=require_tail_start,
        expected_family=expected_family,
        expected_omega=expected_omega,
        min_relative_margin=min_relative_margin,
        max_z=max_z,
    )

    att = copy.deepcopy(base)
    att["schema"] = "theorem_iii_trackb_phase5e_formal_interval_attachment_v1"
    att["diagnostic_only"] = True
    att["theorem_facing"] = False
    att["promotion_allowed"] = False
    att["formal_attachment_ok"] = False
    att["promotion_ready"] = False
    att["certificate_sha256"] = cert_hash
    att["phase5j_status"] = "phase5j-branch-graph-components-generated"
    att["branch_chart_component"] = branch_component
    att["final_graph_consumption_component"] = graph_component

    # Ensure all formal-evidence keys exist; preserve prior flags, set only new
    # flags when their components pass, and keep global flags false.
    fe = att.setdefault("formal_evidence", {})
    if not isinstance(fe, dict):
        fe = {}
        att["formal_evidence"] = fe
    for key in ALL_FORMAL_FLAGS:
        fe.setdefault(key, bool(_flag_true(base, key)))
    fe["branch_chart_compatibility_proof"] = bool(branch_component["component_ok"])
    fe["final_graph_consumption_proof"] = bool(graph_component["component_ok"])
    fe["formal_interval_backend"] = False
    fe["independent_replay_passed"] = False

    # Legacy/convenience fields for summaries and older gates.
    att["formal_evidence_true_flags"] = _true_flags(att)
    att["missing_formal_evidence_flags"] = _missing_flags(att)

    _write_json(attachment_out, att)

    summary = make_phase5j_summary(att, attachment_out=str(attachment_out), certificate_path=certificate_path)
    _write_json(summary_out, summary)
    _write_json(compact_out, summary)
    return summary


def make_phase5j_summary(
    attachment: Mapping[str, Any],
    *,
    attachment_out: Optional[str] = None,
    certificate_path: Optional[str] = None,
) -> Dict[str, Any]:
    branch = attachment.get("branch_chart_component", {}) if isinstance(attachment.get("branch_chart_component"), dict) else {}
    graph = attachment.get("final_graph_consumption_component", {}) if isinstance(attachment.get("final_graph_consumption_component"), dict) else {}
    passed = bool(branch.get("component_ok") is True and graph.get("component_ok") is True)
    constants = _selected_constants(attachment)
    return {
        "schema": "theorem_iii_trackb_phase5j_compact_report_v1",
        "status": "phase5j-branch-graph-components-generated" if passed else "phase5j-branch-graph-components-failed",
        "attachment_path": attachment_out or attachment.get("attachment_path"),
        "certificate_path": certificate_path,
        "certificate_sha256": attachment.get("certificate_sha256"),
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "promotion_ready": False,
        "formal_attachment_ok": False,
        "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_GLOBAL_BACKEND_AND_INDEPENDENT_REPLAY_TRUE",
        "passed": {
            "branch_chart_component_ok": bool(branch.get("component_ok") is True),
            "final_graph_consumption_component_ok": bool(graph.get("component_ok") is True),
            "configuration_ok": bool(branch.get("configuration_ok") is True),
        },
        "formal_evidence_true_flags": _true_flags(attachment),
        "missing_formal_evidence_flags": _missing_flags(attachment),
        "selected_constants": constants,
        "branch_chart_component": branch,
        "final_graph_consumption_component": graph,
    }


def replay_phase5j_attachment(
    *,
    certificate_path: str,
    attachment_path: str,
    required_min_lower_anchor_k: float,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    expected_family: str,
    expected_omega: str,
    min_relative_margin: float,
    max_z: float,
    out_dir: str,
    force: bool = False,
) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary_out = out / "phase5j_component_replay_summary.json"
    compact_out = out / "phase5j_replay_compact_report.json"
    if summary_out.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing {summary_out}; use --force")

    cert = _read_json(certificate_path)
    att = _read_json(attachment_path)
    cert_hash = _sha256_raw(certificate_path)
    expected_branch, expected_graph = check_phase5j_conditions(
        cert,
        att,
        cert_hash,
        required_min_lower_anchor_k=required_min_lower_anchor_k,
        require_nu=require_nu,
        require_radius=require_radius,
        require_cutoff=require_cutoff,
        require_tail_start=require_tail_start,
        expected_family=expected_family,
        expected_omega=expected_omega,
        min_relative_margin=min_relative_margin,
        max_z=max_z,
    )
    branch = att.get("branch_chart_component", {}) if isinstance(att.get("branch_chart_component"), dict) else {}
    graph = att.get("final_graph_consumption_component", {}) if isinstance(att.get("final_graph_consumption_component"), dict) else {}

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": _json_safe(detail)})

    add("schema", att.get("schema") == "theorem_iii_trackb_phase5e_formal_interval_attachment_v1", att.get("schema"))
    add("diagnostic_only_true", att.get("diagnostic_only") is True, att.get("diagnostic_only"))
    add("theorem_facing_false", att.get("theorem_facing") is False, att.get("theorem_facing"))
    add("promotion_allowed_false", att.get("promotion_allowed") is False, att.get("promotion_allowed"))
    add("certificate_hash_matches", att.get("certificate_sha256") == cert_hash, {"reported": att.get("certificate_sha256"), "actual": cert_hash})
    for flag in REQUIRED_PRIOR_FLAGS:
        add(f"prior_flag_{flag}_true", _flag_true(att, flag), _flag_true(att, flag))
    add("branch_chart_flag_true", _flag_true(att, "branch_chart_compatibility_proof"), _flag_true(att, "branch_chart_compatibility_proof"))
    add("final_graph_flag_true", _flag_true(att, "final_graph_consumption_proof"), _flag_true(att, "final_graph_consumption_proof"))
    add("global_formal_interval_backend_false", not _flag_true(att, "formal_interval_backend"), _flag_true(att, "formal_interval_backend"))
    add("global_independent_replay_false", not _flag_true(att, "independent_replay_passed"), _flag_true(att, "independent_replay_passed"))
    add("branch_chart_component_ok", branch.get("component_ok") is True and expected_branch.get("component_ok") is True, branch)
    add("final_graph_consumption_component_ok", graph.get("component_ok") is True and expected_graph.get("component_ok") is True, graph)
    add("branch_labels_match", branch.get("branch_label") == expected_branch.get("branch_label"), {"reported": branch.get("branch_label"), "expected": expected_branch.get("branch_label")})
    add("chart_labels_match", branch.get("chart_label") == expected_branch.get("chart_label"), {"reported": branch.get("chart_label"), "expected": expected_branch.get("chart_label")})
    add("graph_consumes_direct_lower_anchor_only", graph.get("does_not_claim_parameter_interval") is True and graph.get("does_not_claim_mesh_corridor") is True, graph)
    add("relative_margin_threshold", _as_float(_selected_constants(att).get("radii_relative_margin_interval_lower")) >= min_relative_margin, _selected_constants(att).get("radii_relative_margin_interval_lower"))
    add("Z_below_threshold", _as_float(_selected_constants(att).get("Z_interval_upper")) <= max_z, _selected_constants(att).get("Z_interval_upper"))

    passed = all(c["ok"] for c in checks)
    summary = make_phase5j_summary(att, attachment_out=attachment_path, certificate_path=certificate_path)
    summary.update(
        {
            "schema": "theorem_iii_trackb_phase5j_replay_compact_report_v1",
            "status": "phase5j-component-replay-complete",
            "passed": passed,
            "checks": checks,
            "failed_checks": [c["name"] for c in checks if not c["ok"]],
        }
    )
    _write_json(summary_out, summary)
    _write_json(compact_out, summary)
    return summary


def summarize_phase5j(input_path: str, out_path: str) -> Dict[str, Any]:
    payload = _read_json(input_path)
    # Already compact.  Normalize by writing it to requested destination.
    _write_json(out_path, payload)
    return payload
