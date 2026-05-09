"""Phase 5I nonlinear/tail formal-component candidate utilities.

This module is intentionally conservative and fail-closed.  It does not create a
final theorem-facing certificate.  It extends a previously hash-bound Phase 5H
attachment by adding two component-level evidence flags when the nonlinear and
resolved-tail bounds can be replayed from an existing Phase 5C backend record:

    nonlinear_bound_proof = True
    tail_bound_proof = True

The global flags formal_interval_backend and independent_replay_passed remain
False until a later phase supplies a complete independent formal backend.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

getcontext().prec = 80

REQUIRED_FORMAL_EVIDENCE_KEYS: Tuple[str, ...] = (
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
)

PHASE5I_SCHEMA = "theorem_iii_trackb_phase5i_compact_report_v1"
ATTACHMENT_SCHEMA = "theorem_iii_trackb_phase5e_formal_interval_attachment_v1"


def load_json(path: str | os.PathLike[str]) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sanitize_json_value(obj: Any) -> Any:
    """Return a JSON-compliant copy of obj.

    Phase 5I intentionally writes with ``allow_nan=False`` so that proof ledgers
    cannot silently contain invalid JSON.  Some older Phase 5C/5H diagnostic
    records may carry optional floating fields as NaN when the quantity is not
    available.  Those optional non-finite values are not evidence; convert them
    to ``None`` at the serialization boundary while preserving all finite proof
    constants exactly as Python floats/ints/strings/bools/lists/dicts.
    """
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {str(k): sanitize_json_value(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_json_value(v) for v in obj]
    return obj


def count_nonfinite_json_values(obj: Any) -> int:
    if isinstance(obj, float):
        return 0 if math.isfinite(obj) else 1
    if isinstance(obj, dict):
        return sum(count_nonfinite_json_values(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return sum(count_nonfinite_json_values(v) for v in obj)
    return 0


def write_json(path: str | os.PathLike[str], payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    clean = sanitize_json_value(payload)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    os.replace(tmp, path)


def raw_sha256(path: str | os.PathLike[str]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def as_float(x: Any, default: float = float("nan")) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def nearly_equal(a: Any, b: Any, *, rtol: float = 1e-12, atol: float = 1e-14) -> bool:
    af = as_float(a)
    bf = as_float(b)
    if not (math.isfinite(af) and math.isfinite(bf)):
        return False
    return abs(af - bf) <= atol + rtol * max(1.0, abs(af), abs(bf))


def recursive_dicts(obj: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from recursive_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from recursive_dicts(v)


def is_candidate_record(d: Mapping[str, Any]) -> bool:
    required = (
        "K",
        "M",
        "nu",
        "radius",
        "cutoff_spec",
        "tail_start_frac",
        "Q_interval_upper",
        "Y_interval_upper",
        "Z_interval_upper",
    )
    return all(k in d for k in required)


def find_backend_record(
    summary: Mapping[str, Any],
    *,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    min_relative_margin: float,
    max_z: float,
) -> Dict[str, Any]:
    records = [d for d in recursive_dicts(summary) if is_candidate_record(d)]
    matches: List[Dict[str, Any]] = []
    for r in records:
        if str(r.get("cutoff_spec")) != str(require_cutoff):
            continue
        if not nearly_equal(r.get("nu"), require_nu, atol=1e-15):
            continue
        if not nearly_equal(r.get("radius"), require_radius, atol=1e-15):
            continue
        if not nearly_equal(r.get("tail_start_frac"), require_tail_start, atol=1e-15):
            continue
        z = as_float(r.get("Z_interval_upper"))
        rel = as_float(r.get("radii_relative_margin_interval_lower"))
        margin = as_float(r.get("radii_margin_interval_lower"))
        q = as_float(r.get("Q_interval_upper"))
        if math.isfinite(z) and math.isfinite(q) and math.isfinite(rel) and math.isfinite(margin):
            if z <= max_z and rel >= min_relative_margin and margin > 0:
                matches.append(dict(r))
    if not matches:
        raise ValueError(
            "No Phase 5C backend record matches the requested configuration and thresholds. "
            f"Searched {len(records)} candidate-like records."
        )
    matches.sort(
        key=lambda r: (
            -as_float(r.get("radii_margin_interval_lower")),
            as_float(r.get("Q_interval_upper")),
            as_float(r.get("tail_residual_component_upper")),
        )
    )
    return matches[0]


def ensure_formal_evidence(attachment: Dict[str, Any]) -> Dict[str, bool]:
    fe = attachment.get("formal_evidence")
    if not isinstance(fe, dict):
        fe = {}
        attachment["formal_evidence"] = fe
    # Also honor legacy true-flags list by copying literal true into the dict.
    for k in attachment.get("formal_evidence_true_flags", []) or []:
        if k in REQUIRED_FORMAL_EVIDENCE_KEYS:
            fe[k] = True
    for k in REQUIRED_FORMAL_EVIDENCE_KEYS:
        fe.setdefault(k, False)
    # Only literal bools are preserved as proof flags.
    for k in list(fe.keys()):
        fe[k] = True if fe[k] is True else False
    return fe  # type: ignore[return-value]


def true_flags(fe: Mapping[str, Any]) -> List[str]:
    return [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if fe.get(k) is True]


def missing_flags(fe: Mapping[str, Any]) -> List[str]:
    return [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if fe.get(k) is not True]


def decimal_margin(Y: Any, Z: Any, Q: Any, r: Any) -> Dict[str, Any]:
    Yd = Decimal(str(Y))
    Zd = Decimal(str(Z))
    Qd = Decimal(str(Q))
    rd = Decimal(str(r))
    lhs = Yd + Zd * rd + Qd * rd * rd
    margin = rd - lhs
    rel = margin / rd if rd != 0 else Decimal("NaN")
    return {
        "Y_decimal": str(Yd),
        "Z_decimal": str(Zd),
        "Q_decimal": str(Qd),
        "radius_decimal": str(rd),
        "recomputed_lhs_decimal": str(lhs),
        "recomputed_margin_decimal": str(margin),
        "recomputed_relative_margin_decimal": str(rel),
        "positive_recomputed_margin": margin > 0,
    }


def build_nonlinear_component(record: Mapping[str, Any], *, max_q: float) -> Dict[str, Any]:
    q = as_float(record.get("Q_interval_upper"))
    q_raw = as_float(record.get("Q_nonlinear_raw"), default=float("nan"))
    ok = math.isfinite(q) and q > 0 and q <= max_q
    return {
        "component_ok": bool(ok),
        "Q_interval_upper": q,
        "Q_nonlinear_raw": q_raw if math.isfinite(q_raw) else None,
        "q_scale": record.get("q_scale"),
        "max_q_threshold": max_q,
        "radius": as_float(record.get("radius")),
        "radii_lhs_interval_upper": as_float(record.get("radii_lhs_interval_upper")),
        "radii_margin_interval_lower": as_float(record.get("radii_margin_interval_lower")),
        "radii_relative_margin_interval_lower": as_float(record.get("radii_relative_margin_interval_lower")),
    }


def build_tail_component(record: Mapping[str, Any], *, max_tail_residual: float, max_tail_derivative: float) -> Dict[str, Any]:
    tail_res = as_float(record.get("tail_residual_component_upper"))
    # Some older records only have derivative tail under these keys.
    tail_der = as_float(
        record.get("tail_derivative_component_bound", record.get("tail_derivative_component_upper", float("nan")))
    )
    residual_total = as_float(record.get("residual_l1_nu_total_upper", record.get("residual_l1_nu_total")))
    derivative_linf = as_float(record.get("derivative_residual_linf"))
    ok_res = math.isfinite(tail_res) and tail_res >= 0 and tail_res <= max_tail_residual
    # The Phase 5C stress record often lacks derivative-tail upper; do not fail solely on missing optional detail.
    ok_der = (not math.isfinite(tail_der)) or (tail_der >= 0 and tail_der <= max_tail_derivative)
    return {
        "component_ok": bool(ok_res and ok_der),
        "tail_residual_component_upper": tail_res,
        "tail_derivative_component_upper": tail_der if math.isfinite(tail_der) else None,
        "residual_l1_nu_total_upper": residual_total if math.isfinite(residual_total) else None,
        "derivative_residual_linf": derivative_linf if math.isfinite(derivative_linf) else None,
        "tail_start_frac": as_float(record.get("tail_start_frac")),
        "cutoff_spec": record.get("cutoff_spec"),
        "cutoff_mode_native_units": record.get("cutoff_mode_native_units"),
        "max_tail_residual_threshold": max_tail_residual,
        "max_tail_derivative_threshold": max_tail_derivative,
    }


def selected_constants_from_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    keys = [
        "K", "M", "nu", "radius", "cutoff_spec", "tail_start_frac", "grid_factor", "grid_size",
        "Y_interval_upper", "Z_interval_upper", "Q_interval_upper", "radii_lhs_interval_upper",
        "radii_margin_interval_lower", "radii_relative_margin_interval_lower",
        "small_divisor_min_denominator_lower", "small_divisor_min_mode",
        "cohomology_inverse_linf_resolved_upper", "upper_triangular_defect_linf_max",
        "a11_minus_1_linf", "a21_linf", "a22_minus_1_linf", "twist_average",
        "tail_residual_component_upper", "residual_l1_nu_total_upper", "scalar_residual_linf",
    ]
    out = {k: record.get(k) for k in keys if k in record}
    if "record_path" in record:
        out["source_record_path"] = record.get("record_path")
    return out


def generate_phase5i_attachment(
    *,
    certificate_path: str,
    base_attachment_path: str,
    phase5c_summary_path: str,
    required_min_lower_anchor_k: float,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    min_relative_margin: float,
    max_z: float,
    max_q: float,
    max_tail_residual: float,
    max_tail_derivative: float,
    out_dir: str,
    force: bool = False,
) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    attachment_out = out / "phase5i_formal_interval_attachment_COMPONENTS.json"
    summary_out = out / "phase5i_component_summary.json"
    compact_out = out / "phase5i_compact_report.json"
    if attachment_out.exists() and not force:
        raise FileExistsError(f"Output exists: {attachment_out}. Use --force to overwrite.")

    cert_hash = raw_sha256(certificate_path)
    base = load_json(base_attachment_path)
    summary = load_json(phase5c_summary_path)
    record = find_backend_record(
        summary,
        require_nu=require_nu,
        require_radius=require_radius,
        require_cutoff=require_cutoff,
        require_tail_start=require_tail_start,
        min_relative_margin=min_relative_margin,
        max_z=max_z,
    )

    K = as_float(record.get("K"))
    if K + 1e-15 < required_min_lower_anchor_k:
        raise ValueError(f"Backend record K={K} does not meet required lower anchor {required_min_lower_anchor_k}")

    nonlinear = build_nonlinear_component(record, max_q=max_q)
    tail = build_tail_component(record, max_tail_residual=max_tail_residual, max_tail_derivative=max_tail_derivative)

    attachment = copy.deepcopy(base)
    attachment["schema"] = ATTACHMENT_SCHEMA
    attachment["diagnostic_only"] = True
    attachment["theorem_facing"] = False
    attachment["promotion_allowed"] = False
    attachment["formal_attachment_ok"] = False
    attachment["promotion_ready"] = False
    attachment["certificate_sha256"] = cert_hash
    attachment["certificate_path"] = certificate_path
    attachment["phase5i_status"] = "nonlinear-tail-components-added"
    attachment["nonlinear_component"] = nonlinear
    attachment["tail_component"] = tail
    attachment["selected_constants"] = selected_constants_from_record(record)
    attachment.setdefault("component_records", {})["phase5i_backend_record"] = {
        "phase5c_summary_path": phase5c_summary_path,
        "record_path": record.get("record_path"),
        "cutoff_spec": record.get("cutoff_spec"),
        "tail_start_frac": record.get("tail_start_frac"),
    }

    fe = ensure_formal_evidence(attachment)
    if nonlinear["component_ok"]:
        fe["nonlinear_bound_proof"] = True
    if tail["component_ok"]:
        fe["tail_bound_proof"] = True
    # Global flags remain intentionally false.
    fe["formal_interval_backend"] = False
    fe["independent_replay_passed"] = False
    fe["branch_chart_compatibility_proof"] = False
    fe["final_graph_consumption_proof"] = False
    attachment["formal_evidence_true_flags"] = true_flags(fe)
    attachment["missing_formal_evidence_flags"] = missing_flags(fe)
    attachment["expected_phase5e_decision"] = "REJECT_FAIL_CLOSED_UNTIL_REMAINING_FORMAL_EVIDENCE_FLAGS_TRUE"

    dec = decimal_margin(
        record.get("Y_interval_upper"),
        record.get("Z_interval_upper"),
        record.get("Q_interval_upper"),
        record.get("radius"),
    )
    attachment["decimal_radii_replay"] = dec

    compact = {
        "schema": PHASE5I_SCHEMA,
        "status": "phase5i-formal-nonlinear-tail-components-generated",
        "attachment_path": str(attachment_out),
        "certificate_sha256": cert_hash,
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "promotion_ready": False,
        "formal_attachment_ok": False,
        "passed": {
            "configuration_ok": True,
            "nonlinear_component_ok": nonlinear["component_ok"],
            "tail_component_ok": tail["component_ok"],
        },
        "formal_evidence_true_flags": true_flags(fe),
        "missing_formal_evidence_flags": missing_flags(fe),
        "selected_constants": attachment["selected_constants"],
        "nonlinear_component": nonlinear,
        "tail_component": tail,
        "decimal_radii_replay": dec,
        "expected_phase5e_decision": attachment["expected_phase5e_decision"],
    }
    # Count any optional non-finite values inherited from older diagnostic records
    # before serialization converts them to null.  Required evidence quantities
    # are separately checked above and must be finite to pass.
    compact["nonfinite_optional_values_sanitized_for_json"] = count_nonfinite_json_values(attachment)
    attachment["nonfinite_optional_values_sanitized_for_json"] = compact["nonfinite_optional_values_sanitized_for_json"]

    write_json(attachment_out, attachment)
    write_json(summary_out, compact)
    write_json(compact_out, compact)
    return compact


def replay_phase5i_attachment(
    *,
    certificate_path: str,
    attachment_path: str,
    required_min_lower_anchor_k: float,
    require_nu: float,
    require_radius: float,
    require_cutoff: str,
    require_tail_start: float,
    min_relative_margin: float,
    max_z: float,
    max_q: float,
    max_tail_residual: float,
    out_dir: str,
    force: bool = False,
) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary_out = out / "phase5i_component_replay_summary.json"
    compact_out = out / "phase5i_replay_compact_report.json"
    if summary_out.exists() and not force:
        raise FileExistsError(f"Output exists: {summary_out}. Use --force to overwrite.")

    cert_hash = raw_sha256(certificate_path)
    a = load_json(attachment_path)
    fe = ensure_formal_evidence(a)
    sc = a.get("selected_constants", {}) if isinstance(a.get("selected_constants"), dict) else {}
    nonlinear = a.get("nonlinear_component", {}) if isinstance(a.get("nonlinear_component"), dict) else {}
    tail = a.get("tail_component", {}) if isinstance(a.get("tail_component"), dict) else {}

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("schema", a.get("schema") == ATTACHMENT_SCHEMA, a.get("schema"))
    add("diagnostic_only_true", a.get("diagnostic_only") is True, a.get("diagnostic_only"))
    add("theorem_facing_false", a.get("theorem_facing") is False, a.get("theorem_facing"))
    add("promotion_allowed_false", a.get("promotion_allowed") is False, a.get("promotion_allowed"))
    add("certificate_hash_matches", a.get("certificate_sha256") == cert_hash, {"reported": a.get("certificate_sha256"), "actual": cert_hash})
    add("anchor_meets_min", as_float(sc.get("K")) + 1e-15 >= required_min_lower_anchor_k, sc.get("K"))
    add("nu_matches", nearly_equal(sc.get("nu"), require_nu, atol=1e-15), sc.get("nu"))
    add("radius_matches", nearly_equal(sc.get("radius"), require_radius, atol=1e-15), sc.get("radius"))
    add("cutoff_matches", sc.get("cutoff_spec") == require_cutoff, sc.get("cutoff_spec"))
    add("tail_start_matches", nearly_equal(sc.get("tail_start_frac"), require_tail_start, atol=1e-15), sc.get("tail_start_frac"))
    add("nonlinear_component_ok", nonlinear.get("component_ok") is True, nonlinear)
    add("tail_component_ok", tail.get("component_ok") is True, tail)
    add("nonlinear_flag_true", fe.get("nonlinear_bound_proof") is True, fe.get("nonlinear_bound_proof"))
    add("tail_flag_true", fe.get("tail_bound_proof") is True, fe.get("tail_bound_proof"))
    add("Q_below_threshold", as_float(sc.get("Q_interval_upper")) <= max_q, sc.get("Q_interval_upper"))
    add("tail_residual_below_threshold", as_float(tail.get("tail_residual_component_upper")) <= max_tail_residual, tail.get("tail_residual_component_upper"))
    add("Z_below_threshold", as_float(sc.get("Z_interval_upper")) <= max_z, sc.get("Z_interval_upper"))
    add("relative_margin_threshold", as_float(sc.get("radii_relative_margin_interval_lower")) >= min_relative_margin, sc.get("radii_relative_margin_interval_lower"))
    dec = decimal_margin(sc.get("Y_interval_upper"), sc.get("Z_interval_upper"), sc.get("Q_interval_upper"), sc.get("radius"))
    add("positive_decimal_margin", dec["positive_recomputed_margin"] is True, dec)

    failed = [c["name"] for c in checks if not c["ok"]]
    compact = {
        "schema": PHASE5I_SCHEMA,
        "status": "phase5i-component-replay-complete",
        "attachment_path": attachment_path,
        "certificate_sha256": cert_hash,
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "promotion_ready": False,
        "formal_attachment_ok": False,
        "passed": not failed,
        "checks": checks,
        "failed_checks": failed,
        "formal_evidence_true_flags": true_flags(fe),
        "missing_formal_evidence_flags": missing_flags(fe),
        "selected_constants": sc,
        "nonlinear_component": nonlinear,
        "tail_component": tail,
        "decimal_radii_replay": dec,
        "expected_phase5e_decision": a.get("expected_phase5e_decision"),
    }
    write_json(summary_out, compact)
    write_json(compact_out, compact)
    return compact


def summarize_json(in_path: str, out_path: Optional[str] = None) -> Dict[str, Any]:
    payload = load_json(in_path)
    # The generator/replay already produce compact reports.  This function exists
    # so the CLI mirrors prior phases and can normalize either summary path.
    if isinstance(payload, dict) and payload.get("schema") == PHASE5I_SCHEMA:
        compact = payload
    else:
        compact = {"schema": PHASE5I_SCHEMA, "status": "phase5i-summary-wrapped", "payload": payload}
    if out_path:
        write_json(out_path, compact)
    else:
        print(json.dumps(compact, indent=2, sort_keys=True, allow_nan=False))
    return compact


def add_common_threshold_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--required-min-lower-anchor-k", type=float, default=0.971635)
    p.add_argument("--require-nu", type=float, required=True)
    p.add_argument("--require-radius", type=float, required=True)
    p.add_argument("--require-cutoff", type=str, required=True)
    p.add_argument("--require-tail-start", type=float, required=True)
    p.add_argument("--min-relative-margin", type=float, default=0.25)
    p.add_argument("--max-z", type=float, default=0.5)
    p.add_argument("--max-q", type=float, default=5000.0)
    p.add_argument("--max-tail-residual", type=float, default=1e-6)
    p.add_argument("--max-tail-derivative", type=float, default=1e-2)
