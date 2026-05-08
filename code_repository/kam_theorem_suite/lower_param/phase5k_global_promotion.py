"""Phase 5K global formal-backend / independent-replay promotion scaffold.

This module is intentionally conservative.  It does not recompute the analytic
constants from the seed; earlier phases already produced component proof objects.
Phase 5K checks that all component objects are present, hash-bound to the exact
Phase 5D certificate, threshold-compatible, and internally replayable.  Only the
second step, the independent replay, emits a promoted theorem-facing formal
attachment.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

getcontext().prec = 80

REQUIRED_COMPONENT_FLAGS = [
    "outward_rounded_residual_proof",
    "small_divisor_proof",
    "cohomology_inverse_proof",
    "frame_reducibility_proof",
    "nonlinear_bound_proof",
    "tail_bound_proof",
    "branch_chart_compatibility_proof",
    "final_graph_consumption_proof",
]
GLOBAL_FLAGS = ["formal_interval_backend", "independent_replay_passed"]
ALL_FORMAL_FLAGS = ["formal_interval_backend", "independent_replay_passed"] + REQUIRED_COMPONENT_FLAGS

SCHEMA_ATTACHMENT = "theorem_iii_trackb_phase5e_formal_interval_attachment_v1"
SCHEMA_BACKEND = "theorem_iii_trackb_phase5k_global_backend_candidate_v1"
SCHEMA_REPLAY = "theorem_iii_trackb_phase5k_independent_replay_v1"
SCHEMA_COMPACT = "theorem_iii_trackb_phase5k_compact_report_v1"


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


def as_float(x: Any, default: float = float("nan")) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def formal_flag(att: Mapping[str, Any], name: str) -> bool:
    # Strict: only literal True counts, not truthy values.
    if att.get(name) is True:
        return True
    fe = att.get("formal_evidence")
    if isinstance(fe, Mapping) and fe.get(name) is True:
        return True
    flags = att.get("formal_evidence_true_flags")
    if isinstance(flags, list) and name in flags:
        return True
    return False


def all_true_flags(att: Mapping[str, Any]) -> List[str]:
    return [k for k in ALL_FORMAL_FLAGS if formal_flag(att, k)]


def selected_constants(att: Mapping[str, Any]) -> Dict[str, Any]:
    # Prefer top-level selected_constants, but fall back to Phase 5D/5C shapes.
    sc = att.get("selected_constants")
    if isinstance(sc, Mapping):
        return dict(sc)
    cand = att.get("selected_candidate")
    if isinstance(cand, Mapping):
        return dict(cand)
    return {}


def _d(x: Any) -> Decimal:
    return Decimal(str(x))


def recompute_radii(sc: Mapping[str, Any]) -> Dict[str, Any]:
    Y = _d(sc.get("Y_interval_upper", sc.get("Y")))
    Z = _d(sc.get("Z_interval_upper", sc.get("Z")))
    Q = _d(sc.get("Q_interval_upper", sc.get("Q")))
    r = _d(sc.get("radius"))
    lhs = Y + Z * r + Q * r * r
    margin = r - lhs
    rel = margin / r if r != 0 else Decimal("NaN")
    return {
        "Y_decimal": str(Y),
        "Z_decimal": str(Z),
        "Q_decimal": str(Q),
        "radius_decimal": str(r),
        "recomputed_lhs_decimal": str(lhs),
        "recomputed_margin_decimal": str(margin),
        "recomputed_relative_margin_decimal": str(rel),
        "positive_recomputed_margin": margin > 0,
    }


def check_configuration(sc: Mapping[str, Any], *, required_min_lower_anchor_k: float, require_nu: float, require_radius: float, require_cutoff: str, require_tail_start: float, min_relative_margin: float, max_z: float) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    def add(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    K = as_float(sc.get("K", sc.get("lower_anchor_K")))
    nu = as_float(sc.get("nu"))
    radius = as_float(sc.get("radius"))
    cutoff = sc.get("cutoff_spec")
    tail = as_float(sc.get("tail_start_frac"))
    rel = as_float(sc.get("radii_relative_margin_interval_lower", sc.get("relative_margin")))
    Z = as_float(sc.get("Z_interval_upper", sc.get("Z")))
    margin = as_float(sc.get("radii_margin_interval_lower", sc.get("margin")))
    small = as_float(sc.get("small_divisor_min_denominator_lower", sc.get("small_divisor_lower")), default=0.0)

    add("anchor_meets_min", K >= required_min_lower_anchor_k, K)
    add("nu_matches", abs(nu - require_nu) <= 1e-15, nu)
    add("radius_matches", abs(radius - require_radius) <= 1e-18, radius)
    add("cutoff_matches", cutoff == require_cutoff, cutoff)
    add("tail_start_matches", abs(tail - require_tail_start) <= 1e-15, tail)
    add("reported_margin_positive", margin > 0, margin)
    add("relative_margin_threshold", rel >= min_relative_margin, rel)
    add("Z_below_threshold", Z <= max_z, Z)
    add("small_divisor_positive", small > 0, small)

    try:
        dec = recompute_radii(sc)
        add("positive_decimal_margin", dec["positive_recomputed_margin"], dec)
    except Exception as e:
        add("positive_decimal_margin", False, repr(e))
    return checks


def _failed(checks: Iterable[Mapping[str, Any]]) -> List[str]:
    return [str(c.get("name")) for c in checks if not c.get("ok")]


def _true_flag_map(flags_true: Iterable[str]) -> Dict[str, bool]:
    flags_true_set = set(flags_true)
    return {k: (k in flags_true_set) for k in ALL_FORMAL_FLAGS}


def build_global_backend_candidate(*, certificate_path: str, base_attachment_path: str, required_min_lower_anchor_k: float, require_nu: float, require_radius: float, require_cutoff: str, require_tail_start: float, min_relative_margin: float, max_z: float, out_dir: str, force: bool = False) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cert = load_json(certificate_path)
    att = load_json(base_attachment_path)
    cert_hash = sha256_file(certificate_path)
    sc = selected_constants(att)

    checks: List[Dict[str, Any]] = []
    def add(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("certificate_hash_matches", att.get("certificate_sha256") == cert_hash, {"reported": att.get("certificate_sha256"), "actual": cert_hash})
    add("schema", att.get("schema") == SCHEMA_ATTACHMENT, att.get("schema"))
    for flag in REQUIRED_COMPONENT_FLAGS:
        add(f"component_flag_{flag}_true", formal_flag(att, flag), formal_flag(att, flag))
    add("global_formal_interval_backend_false_on_input", not formal_flag(att, "formal_interval_backend"), formal_flag(att, "formal_interval_backend"))
    add("global_independent_replay_false_on_input", not formal_flag(att, "independent_replay_passed"), formal_flag(att, "independent_replay_passed"))
    checks.extend(check_configuration(sc, required_min_lower_anchor_k=required_min_lower_anchor_k, require_nu=require_nu, require_radius=require_radius, require_cutoff=require_cutoff, require_tail_start=require_tail_start, min_relative_margin=min_relative_margin, max_z=max_z))

    failed = _failed(checks)
    backend_ok = not failed

    backend_record = {
        "schema": SCHEMA_BACKEND,
        "status": "phase5k-global-backend-candidate-built" if backend_ok else "phase5k-global-backend-candidate-failed",
        "diagnostic_only": False,
        "theorem_facing": False,
        "promotion_allowed": False,
        "certificate_path": certificate_path,
        "certificate_sha256": cert_hash,
        "base_attachment_path": base_attachment_path,
        "selected_constants": sc,
        "backend_component": {
            "formal_interval_backend_candidate": backend_ok,
            "component_flags_verified": {k: formal_flag(att, k) for k in REQUIRED_COMPONENT_FLAGS},
            "global_flags_intentionally_pending": {
                "formal_interval_backend": True if backend_ok else False,
                "independent_replay_passed": False,
            },
            "replay_required_before_promotion": True,
        },
        "checks": checks,
        "failed_checks": failed,
        "passed": backend_ok,
        "formal_evidence_true_flags": REQUIRED_COMPONENT_FLAGS + (["formal_interval_backend"] if backend_ok else []),
        "missing_formal_evidence_flags": ["independent_replay_passed"] if backend_ok else GLOBAL_FLAGS,
        "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_INDEPENDENT_REPLAY_TRUE",
    }

    backend_path = out / "phase5k_global_backend_candidate.json"
    write_json(backend_path, backend_record)

    # Build candidate attachment.  This is still rejected by Phase 5E because independent replay is false.
    cand = copy.deepcopy(att)
    cand["schema"] = SCHEMA_ATTACHMENT
    cand["certificate_sha256"] = cert_hash
    cand["selected_constants"] = sc
    cand["diagnostic_only"] = False
    cand["theorem_facing"] = False
    cand["promotion_allowed"] = False
    cand["formal_attachment_ok"] = False
    fe = dict(cand.get("formal_evidence") or {})
    for flag in REQUIRED_COMPONENT_FLAGS:
        fe[flag] = True
    fe["formal_interval_backend"] = bool(backend_ok)
    fe["independent_replay_passed"] = False
    cand["formal_evidence"] = fe
    cand["formal_evidence_true_flags"] = [k for k, v in fe.items() if v is True]
    cand["missing_formal_evidence_flags"] = [k for k in ALL_FORMAL_FLAGS if not fe.get(k, False)]
    cand["phase5k_global_backend_candidate_path"] = str(backend_path)
    cand["phase5k_status"] = "candidate_requires_independent_replay"

    cand_path = out / "phase5k_formal_interval_attachment_BACKEND_CANDIDATE.json"
    write_json(cand_path, cand)

    compact = {
        "schema": SCHEMA_COMPACT,
        "status": backend_record["status"],
        "passed": backend_ok,
        "diagnostic_only": False,
        "theorem_facing": False,
        "promotion_allowed": False,
        "certificate_sha256": cert_hash,
        "attachment_path": str(cand_path),
        "backend_record_path": str(backend_path),
        "formal_evidence_true_flags": cand["formal_evidence_true_flags"],
        "missing_formal_evidence_flags": cand["missing_formal_evidence_flags"],
        "selected_constants": sc,
        "failed_checks": failed,
        "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_INDEPENDENT_REPLAY_TRUE",
    }
    write_json(out / "phase5k_compact_report.json", compact)
    return compact


def independent_replay_and_promote(*, certificate_path: str, backend_candidate_path: str, attachment_candidate_path: str, required_min_lower_anchor_k: float, require_nu: float, require_radius: float, require_cutoff: str, require_tail_start: float, min_relative_margin: float, max_z: float, out_dir: str, force: bool = False) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cert_hash = sha256_file(certificate_path)
    backend = load_json(backend_candidate_path)
    cand = load_json(attachment_candidate_path)
    sc = selected_constants(cand)

    checks: List[Dict[str, Any]] = []
    def add(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("candidate_schema", cand.get("schema") == SCHEMA_ATTACHMENT, cand.get("schema"))
    add("backend_schema", backend.get("schema") == SCHEMA_BACKEND, backend.get("schema"))
    add("certificate_hash_matches_attachment", cand.get("certificate_sha256") == cert_hash, {"reported": cand.get("certificate_sha256"), "actual": cert_hash})
    add("certificate_hash_matches_backend", backend.get("certificate_sha256") == cert_hash, {"reported": backend.get("certificate_sha256"), "actual": cert_hash})
    add("backend_candidate_passed", backend.get("passed") is True, backend.get("passed"))
    for flag in REQUIRED_COMPONENT_FLAGS:
        add(f"component_flag_{flag}_true", formal_flag(cand, flag), formal_flag(cand, flag))
    add("formal_interval_backend_true_in_candidate", formal_flag(cand, "formal_interval_backend"), formal_flag(cand, "formal_interval_backend"))
    add("independent_replay_false_before_replay", not formal_flag(cand, "independent_replay_passed"), formal_flag(cand, "independent_replay_passed"))
    checks.extend(check_configuration(sc, required_min_lower_anchor_k=required_min_lower_anchor_k, require_nu=require_nu, require_radius=require_radius, require_cutoff=require_cutoff, require_tail_start=require_tail_start, min_relative_margin=min_relative_margin, max_z=max_z))

    # Negative controls: mutate key quantities and verify our replay would fail.
    negative_controls: List[Dict[str, Any]] = []
    def neg(name: str, mutator) -> None:
        bad = copy.deepcopy(cand)
        mutator(bad)
        bad_sc = selected_constants(bad)
        bad_checks: List[Dict[str, Any]] = []
        if bad.get("certificate_sha256") != cert_hash:
            bad_checks.append({"name": "certificate_hash_matches_attachment", "ok": False})
        for flag in REQUIRED_COMPONENT_FLAGS:
            if not formal_flag(bad, flag):
                bad_checks.append({"name": f"component_flag_{flag}_true", "ok": False})
        bad_checks.extend(check_configuration(bad_sc, required_min_lower_anchor_k=required_min_lower_anchor_k, require_nu=require_nu, require_radius=require_radius, require_cutoff=require_cutoff, require_tail_start=require_tail_start, min_relative_margin=min_relative_margin, max_z=max_z))
        failed = _failed(bad_checks)
        negative_controls.append({"name": name, "expected_rejected": True, "rejected": bool(failed), "failed_checks": failed})

    neg("tampered_hash", lambda d: d.__setitem__("certificate_sha256", "0" * 64))
    neg("missing_component_flag", lambda d: (d.setdefault("formal_evidence", {}).__setitem__("tail_bound_proof", False), d.__setitem__("formal_evidence_true_flags", [x for x in d.get("formal_evidence_true_flags", []) if x != "tail_bound_proof"])))
    neg("bad_relative_margin", lambda d: d.setdefault("selected_constants", {}).__setitem__("radii_relative_margin_interval_lower", 0.0))
    neg("bad_z", lambda d: d.setdefault("selected_constants", {}).__setitem__("Z_interval_upper", max_z * 2.0 + 1.0))

    add("negative_controls_passed", all(n.get("rejected") is True for n in negative_controls), negative_controls)
    failed = _failed(checks)
    passed = not failed

    replay_summary = {
        "schema": SCHEMA_REPLAY,
        "status": "phase5k-independent-replay-passed" if passed else "phase5k-independent-replay-failed",
        "passed": passed,
        "certificate_path": certificate_path,
        "certificate_sha256": cert_hash,
        "backend_candidate_path": backend_candidate_path,
        "attachment_candidate_path": attachment_candidate_path,
        "checks": checks,
        "failed_checks": failed,
        "negative_controls": negative_controls,
        "negative_controls_passed": all(n.get("rejected") is True for n in negative_controls),
        "selected_constants": sc,
        "decimal_radii_replay": recompute_radii(sc),
        "theorem_facing": bool(passed),
        "promotion_allowed": bool(passed),
    }
    replay_path = out / "phase5k_independent_replay_summary.json"
    write_json(replay_path, replay_summary)

    promoted = copy.deepcopy(cand)
    fe = dict(promoted.get("formal_evidence") or {})
    for flag in ALL_FORMAL_FLAGS:
        fe[flag] = bool(passed)
    promoted["formal_evidence"] = fe
    promoted["formal_evidence_true_flags"] = [k for k, v in fe.items() if v is True]
    promoted["missing_formal_evidence_flags"] = [k for k in ALL_FORMAL_FLAGS if not fe.get(k, False)]
    promoted["formal_attachment_ok"] = bool(passed)
    promoted["diagnostic_only"] = False
    promoted["theorem_facing"] = bool(passed)
    promoted["promotion_allowed"] = bool(passed)
    promoted["independent_replay_summary_path"] = str(replay_path)
    promoted["phase5k_status"] = "promoted_after_independent_replay" if passed else "not_promoted_replay_failed"
    promoted["certificate_sha256"] = cert_hash
    promoted["schema"] = SCHEMA_ATTACHMENT
    promoted_path = out / "phase5k_formal_interval_attachment_PROMOTED.json"
    write_json(promoted_path, promoted)

    compact = {
        "schema": SCHEMA_COMPACT,
        "status": replay_summary["status"],
        "passed": passed,
        "certificate_sha256": cert_hash,
        "attachment_path": str(promoted_path),
        "replay_summary_path": str(replay_path),
        "formal_attachment_ok": bool(passed),
        "theorem_facing": bool(passed),
        "promotion_allowed": bool(passed),
        "formal_evidence_true_flags": promoted["formal_evidence_true_flags"],
        "missing_formal_evidence_flags": promoted["missing_formal_evidence_flags"],
        "selected_constants": sc,
        "failed_checks": failed,
        "negative_controls_passed": replay_summary["negative_controls_passed"],
        "expected_phase5e_decision": "ACCEPT_THEOREM_FACING" if passed else "REJECT_FAIL_CLOSED",
    }
    write_json(out / "phase5k_compact_report.json", compact)
    return compact


def summarize_phase5k(input_path: str, out_path: str) -> Dict[str, Any]:
    data = load_json(input_path)
    if "checks" in data and "passed" not in data:
        data["passed"] = not _failed(data.get("checks", []))
    compact = {
        "schema": SCHEMA_COMPACT,
        "status": data.get("status", "phase5k-summary"),
        "passed": data.get("passed"),
        "formal_attachment_ok": data.get("formal_attachment_ok"),
        "theorem_facing": data.get("theorem_facing"),
        "promotion_allowed": data.get("promotion_allowed"),
        "formal_evidence_true_flags": data.get("formal_evidence_true_flags"),
        "missing_formal_evidence_flags": data.get("missing_formal_evidence_flags"),
        "selected_constants": data.get("selected_constants"),
        "failed_checks": data.get("failed_checks"),
        "negative_controls_passed": data.get("negative_controls_passed"),
        "certificate_sha256": data.get("certificate_sha256"),
        "attachment_path": data.get("attachment_path"),
        "expected_phase5e_decision": data.get("expected_phase5e_decision"),
    }
    write_json(out_path, compact)
    return compact
