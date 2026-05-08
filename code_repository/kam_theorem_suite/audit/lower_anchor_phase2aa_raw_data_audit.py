from __future__ import annotations

"""Phase 2AA-A raw-data availability audit for Theorem III.

This module is deliberately diagnostic-only.  It does not create new theorem-
facing certificates and it does not promote any negative-margin Phase-2P row.
Its purpose is to answer the Stage-1 question from the Theorem-III closure plan:

    Do the existing Phase-2N/2O/2P artifacts contain enough raw data to build a
    genuinely sharper validator?

The audit follows candidate rows from Phase-2Y/Phase-2V summaries to their
candidate JSONs, checks for source samples/Fourier coefficients, residual data,
finite linearization data, approximate inverses/preconditioners, tail-profile
metadata, analytic weights, and parameters, and tries to recompute the displayed
scalar Phase-2P margin from artifact fields.  When source samples are available,
it also performs a non-promotional residual recomputation probe.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import csv
import json
import math
import re

try:  # optional; the audit remains useful even if numpy/imports fail
    import numpy as np
except Exception:  # pragma: no cover - minimal environment fallback
    np = None  # type: ignore[assignment]

GOLDEN_INVERSE = (math.sqrt(5.0) - 1.0) / 2.0


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def atomic_write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def finite_float(x: Any, default: float | None = None) -> float | None:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def finite_int(x: Any, default: int | None = None) -> int | None:
    y = finite_float(x)
    if y is None:
        return default
    return int(y)


def is_scalar_number(x: Any) -> bool:
    y = finite_float(x)
    return y is not None


def is_numeric_sequence(x: Any, *, min_len: int = 1) -> bool:
    if isinstance(x, (str, bytes, Mapping)):
        return False
    if not isinstance(x, Sequence):
        return False
    if len(x) < min_len:
        return False
    # Permit complex objects encoded as {"real": ..., "imag": ...} only for
    # metadata detection; array conversion is handled separately.
    sample = list(x[: min(len(x), 8)]) if hasattr(x, "__getitem__") else list(x)[:8]
    numeric = 0
    for item in sample:
        if is_scalar_number(item):
            numeric += 1
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, Mapping)) and item:
            numeric += int(any(is_scalar_number(v) for v in item[: min(len(item), 4)]))
    return numeric > 0


def sequence_length(x: Any) -> int | None:
    try:
        if isinstance(x, (str, bytes, Mapping)):
            return None
        if isinstance(x, Sequence):
            return len(x)
    except Exception:
        return None
    return None


def normalize_rel_path(path: str | Path, root: str | Path = ".") -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return Path(root) / p


def slug_piece_index(row: Mapping[str, Any]) -> int | None:
    for key in ("index", "piece_index", "piece", "piece_id"):
        val = finite_int(row.get(key))
        if val is not None:
            return val
    for key in ("path", "piece_path", "source", "_source_path"):
        raw = row.get(key)
        if not raw:
            continue
        m = re.search(r"p(\d{4})", str(raw))
        if m:
            return int(m.group(1))
    return None


# ---------------------------------------------------------------------------
# Recursive artifact inspection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArrayHit:
    path: str
    length: int
    kind: str
    key: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScalarHit:
    path: str
    value: float
    key: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ARRAY_KIND_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("source_samples", ("source_validation.u", ".u", "samples", "source_samples", "u_samples")),
    ("z_or_augmented_unknown", ("source_validation.z", ".z", "augmented", "unknown_vector")),
    ("residual_coefficients_or_samples", ("residual", "defect", "phi")),
    ("fourier_coefficients", ("coeff", "fourier", "spectrum", "hat")),
    ("tail_profile", ("tail_profile", "tail_envelope", "top_contributors", "tail_by_mode", "modewise")),
    ("finite_matrix_or_jacobian", ("matrix", "jacobian", "linearized", "linearisation", "finite_matrix", "df", "dphi")),
    ("approx_inverse_or_preconditioner", ("inverse", "preconditioner", "approx_inverse", "B_matrix", "right_inverse")),
)

SCALAR_KEYS: tuple[str, ...] = (
    "K", "K_mid", "K_lo", "K_hi", "rho", "omega", "lambda_value", "sigma", "source_sigma",
    "radius_r", "residual_Y", "linear_Z", "finite_contraction_q", "tail_T",
    "tail_response_bound", "nonlinear_guard", "allowable_tail_max", "radii_margin",
    "N", "oversample_factor", "tail_cutoff", "tail_start_mode",
)


def classify_array(path: str, key: str, value: Any) -> str | None:
    lower = f"{path}.{key}".lower()
    if not is_numeric_sequence(value, min_len=2):
        return None
    for kind, patterns in ARRAY_KIND_PATTERNS:
        if any(pat.lower() in lower for pat in patterns):
            return kind
    # As a fallback, long numerical arrays are still useful as raw data.
    n = sequence_length(value) or 0
    if n >= 32:
        return "unclassified_numeric_array"
    return None


def walk_payload(obj: Any, *, prefix: str = "") -> tuple[list[ArrayHit], list[ScalarHit], set[str]]:
    arrays: list[ArrayHit] = []
    scalars: list[ScalarHit] = []
    keys: set[str] = set()

    def rec(x: Any, p: str) -> None:
        if isinstance(x, Mapping):
            for k, v in x.items():
                key = str(k)
                path = f"{p}.{key}" if p else key
                keys.add(path)
                if key in SCALAR_KEYS or key.lower() in {s.lower() for s in SCALAR_KEYS}:
                    fv = finite_float(v)
                    if fv is not None:
                        scalars.append(ScalarHit(path=path, value=fv, key=key))
                kind = classify_array(p, key, v)
                if kind is not None:
                    n = sequence_length(v) or 0
                    arrays.append(ArrayHit(path=path, length=int(n), kind=kind, key=key))
                # Avoid walking huge numerical vectors element-by-element.
                if is_numeric_sequence(v, min_len=16):
                    continue
                rec(v, path)
        elif isinstance(x, Sequence) and not isinstance(x, (str, bytes)):
            # Only walk short lists of dictionaries, not numerical arrays.
            if len(x) <= 512 and not is_numeric_sequence(x, min_len=16):
                for i, v in enumerate(x):
                    rec(v, f"{p}[{i}]")

    rec(obj, prefix)
    return arrays, scalars, keys


def find_first_mapping_with_source_validation(obj: Any) -> Mapping[str, Any] | None:
    if isinstance(obj, Mapping):
        sv = obj.get("source_validation")
        if isinstance(sv, Mapping):
            return obj
        for key in ("raw_certificate", "raw_input", "raw_phase2n_attempt", "phase2n_result", "best", "attempt"):
            val = obj.get(key)
            found = find_first_mapping_with_source_validation(val)
            if found is not None:
                return found
        for val in obj.values():
            found = find_first_mapping_with_source_validation(val)
            if found is not None:
                return found
    elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        if len(obj) <= 1024:
            for val in obj:
                found = find_first_mapping_with_source_validation(val)
                if found is not None:
                    return found
    return None


def extract_candidate_rows(*payloads: Mapping[str, Any], target_indices: Sequence[int] = (), max_rows: int | None = None) -> list[dict[str, Any]]:
    """Extract candidate-row-shaped dictionaries from Phase-2Y/2V files."""
    rows: list[dict[str, Any]] = []
    seen: set[tuple[int | None, str | None, float | None, float | None]] = set()
    target_set = {int(x) for x in target_indices}

    def maybe_add(r: Any, source_name: str) -> None:
        if not isinstance(r, Mapping):
            return
        path = r.get("path") or r.get("piece_path") or r.get("source") or r.get("_source_path")
        idx = slug_piece_index(r)
        has_candidate_shape = path or idx is not None or "radii_margin" in r or "deficit" in r
        if not has_candidate_shape:
            return
        if target_set and idx not in target_set:
            return
        K_lo = finite_float(r.get("K_lo"))
        K_hi = finite_float(r.get("K_hi"))
        key = (idx, str(path) if path else None, K_lo, K_hi)
        if key in seen:
            return
        seen.add(key)
        d = dict(r)
        d["_audit_row_source"] = source_name
        if idx is not None:
            d.setdefault("index", idx)
        if path is not None:
            d.setdefault("path", path)
        rows.append(d)

    def scan(obj: Any, source_name: str) -> None:
        if isinstance(obj, Mapping):
            # Known containers in Phase 2Y/required-improvement and Phase 2V summaries.
            for key in (
                "required_improvement_rows", "best_failed_rows", "best_20_by_deficit", "safe_q_small_gap",
                "q_boundary", "q_over_one", "tail_or_guard_dominated", "minimal_closing_trials",
            ):
                val = obj.get(key)
                if isinstance(val, list):
                    for item in val:
                        maybe_add(item, f"{source_name}:{key}")
            # Do not fully recurse into sensitivity_trials unless explicitly filtered by target index; it can be large.
            if target_set:
                for key, val in obj.items():
                    if isinstance(val, (Mapping, list)):
                        scan(val, f"{source_name}:{key}")
        elif isinstance(obj, list):
            for item in obj:
                maybe_add(item, source_name)

    for i, payload in enumerate(payloads):
        if isinstance(payload, Mapping):
            scan(payload, f"payload{i}")
    # Prioritize explicit target rows, then small deficits / best margins.
    def score(row: Mapping[str, Any]) -> tuple[int, float]:
        idx = slug_piece_index(row)
        wanted = 0 if (not target_set or idx in target_set) else 1
        deficit = finite_float(row.get("deficit"))
        margin = finite_float(row.get("radii_margin"), finite_float(row.get("margin")))
        val = deficit if deficit is not None else (-margin if margin is not None else float("inf"))
        return (wanted, float(val))
    rows.sort(key=score)
    if max_rows is not None:
        rows = rows[: int(max_rows)]
    return rows


# ---------------------------------------------------------------------------
# Recomputation probes
# ---------------------------------------------------------------------------

def recompute_scalar_margin_from_row(row: Mapping[str, Any]) -> dict[str, Any]:
    radius = finite_float(row.get("radius_r"))
    residual = finite_float(row.get("residual_Y"))
    linear = finite_float(row.get("linear_Z"))
    tail_T = finite_float(row.get("tail_T"))
    tail_response = finite_float(row.get("tail_response_bound"))
    guard = finite_float(row.get("nonlinear_guard"))
    stored_margin = finite_float(row.get("radii_margin"), finite_float(row.get("margin")))
    if tail_T is None and tail_response is not None and guard is not None:
        tail_T = tail_response + guard
    required = [radius, residual, linear, tail_T]
    if any(x is None for x in required):
        return {"available": False, "reason": "missing_radius_residual_linear_or_tail"}
    computed = float(radius - (residual + linear * radius + tail_T))
    diff = None if stored_margin is None else float(computed - stored_margin)
    return {
        "available": True,
        "computed_margin": computed,
        "stored_margin": stored_margin,
        "absolute_error": None if diff is None else abs(diff),
        "signed_error": diff,
        "matches_1e_minus_10": bool(diff is not None and abs(diff) <= 1.0e-10),
        "tail_T_from_components_error": None if (tail_response is None or guard is None or finite_float(row.get("tail_T")) is None) else abs(float(row.get("tail_T")) - (tail_response + guard)),
    }


def _extract_source_samples_and_params(payload: Mapping[str, Any], row: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]:
    cert = find_first_mapping_with_source_validation(payload)
    src = cert.get("source_validation") if isinstance(cert, Mapping) and isinstance(cert.get("source_validation"), Mapping) else {}
    u = src.get("u") if isinstance(src, Mapping) else None
    lam = finite_float(src.get("lambda_value") if isinstance(src, Mapping) else None)
    # Search common raw fields for K/rho/sigma/N.
    raw_cert = cert if isinstance(cert, Mapping) else payload
    K = finite_float(raw_cert.get("K"), finite_float(row.get("K_mid")))
    if K is None:
        lo = finite_float(row.get("K_lo")); hi = finite_float(row.get("K_hi"))
        if lo is not None and hi is not None:
            K = 0.5 * (lo + hi)
    rho = finite_float(raw_cert.get("rho"), GOLDEN_INVERSE)
    sigma = finite_float(row.get("sigma"), finite_float(raw_cert.get("sigma_used"), finite_float(raw_cert.get("sigma"))))
    oversample = finite_int(row.get("oversample_factor"), finite_int(raw_cert.get("oversample_factor"), 16))
    return u, {"K": K, "rho": rho, "lambda_value": lam, "sigma": sigma, "oversample_factor": oversample}


def recompute_residual_probe(payload: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    if np is None:
        return {"available": False, "reason": "numpy_unavailable"}
    u, params = _extract_source_samples_and_params(payload, row)
    if u is None:
        return {"available": False, "reason": "source_validation_u_missing"}
    K = params.get("K"); rho = params.get("rho"); lam = params.get("lambda_value")
    sigma = params.get("sigma"); oversample = params.get("oversample_factor") or 16
    if K is None or rho is None or lam is None:
        return {"available": False, "reason": "K_rho_or_lambda_missing", "params": params}
    try:
        from kam_theorem_suite.standard_map import HarmonicFamily
        from kam_theorem_suite.invariance_defect import residual_samples
        from kam_theorem_suite.analytic_norms import spectral_coefficients_from_samples, weighted_fourier_norms_from_coeffs
        arr = np.asarray(u, dtype=float)
        resid = residual_samples(arr, float(rho), float(K), HarmonicFamily(), lambda_value=float(lam), oversample_factor=int(oversample))
        coeffs = spectral_coefficients_from_samples(resid)
        result: dict[str, Any] = {
            "available": True,
            "N_from_u": int(arr.size),
            "residual_inf": float(np.max(np.abs(resid))) if resid.size else 0.0,
            "residual_l2": float(np.linalg.norm(resid)) if resid.size else 0.0,
            "K_used": float(K),
            "rho_used": float(rho),
            "lambda_used": float(lam),
            "oversample_factor_used": int(oversample),
        }
        if sigma is not None:
            weighted_l1, weighted_l2, weighted_sup = weighted_fourier_norms_from_coeffs(coeffs, float(sigma))
            result.update({
                "sigma_used": float(sigma),
                "weighted_residual_l1": float(weighted_l1),
                "weighted_residual_l2": float(weighted_l2),
                "weighted_residual_sup": float(weighted_sup),
                "stored_residual_Y": finite_float(row.get("residual_Y")),
                "relative_error_vs_stored_residual_Y": None,
            })
            stored = finite_float(row.get("residual_Y"))
            if stored is not None and stored != 0.0:
                result["relative_error_vs_stored_residual_Y"] = abs(float(weighted_l1) - stored) / abs(stored)
        return result
    except Exception as exc:  # pragma: no cover - depends on artifact schema
        return {"available": False, "reason": "residual_recompute_exception", "exception": repr(exc), "params": params}


# ---------------------------------------------------------------------------
# Candidate audit
# ---------------------------------------------------------------------------

def audit_candidate(row: Mapping[str, Any], *, root: str | Path = ".", deep: bool = True) -> dict[str, Any]:
    idx = slug_piece_index(row)
    candidate_path_raw = row.get("path") or row.get("piece_path") or row.get("source") or row.get("_source_path")
    candidate_path = normalize_rel_path(candidate_path_raw, root) if candidate_path_raw else None
    result: dict[str, Any] = {
        "index": idx,
        "K_lo": finite_float(row.get("K_lo")),
        "K_hi": finite_float(row.get("K_hi")),
        "bucket": row.get("bucket"),
        "recommended_upgrade": row.get("recommended_upgrade"),
        "candidate_path": str(candidate_path_raw) if candidate_path_raw else None,
        "candidate_path_resolved": str(candidate_path) if candidate_path is not None else None,
        "artifact_exists": bool(candidate_path is not None and candidate_path.exists()),
        "input_row_source": row.get("_audit_row_source"),
        "input_row_margin": finite_float(row.get("radii_margin"), finite_float(row.get("margin"))),
        "input_row_q": finite_float(row.get("finite_contraction_q"), finite_float(row.get("q"))),
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
    }
    row_scalar_recompute = recompute_scalar_margin_from_row(row)
    result["input_row_scalar_margin_recompute"] = row_scalar_recompute

    if candidate_path is None or not candidate_path.exists():
        result["status"] = "missing_candidate_artifact"
        result["failure_fields"] = ["candidate_artifact_missing"]
        result["raw_data_stage1_ready"] = False
        return result
    try:
        payload = load_json(candidate_path)
    except Exception as exc:
        result["status"] = "candidate_json_load_failed"
        result["failure_fields"] = ["candidate_json_load_failed"]
        result["exception"] = repr(exc)
        result["raw_data_stage1_ready"] = False
        return result

    arrays, scalars, keys = walk_payload(payload)
    arrays_by_kind: dict[str, list[dict[str, Any]]] = {}
    for hit in arrays:
        arrays_by_kind.setdefault(hit.kind, []).append(hit.to_dict())
    for kind in list(arrays_by_kind):
        arrays_by_kind[kind] = sorted(arrays_by_kind[kind], key=lambda x: (-int(x["length"]), x["path"]))[:12]

    scalar_map: dict[str, list[dict[str, Any]]] = {}
    for hit in scalars:
        scalar_map.setdefault(hit.key, []).append(hit.to_dict())
    for key in list(scalar_map):
        scalar_map[key] = scalar_map[key][:8]

    # Candidate rows may live inside a Phase-2P report.  Find the best or matching row to recompute row-level scalar margin.
    embedded_rows: list[Mapping[str, Any]] = []
    if isinstance(payload, Mapping) and isinstance(payload.get("rows"), list):
        embedded_rows = [x for x in payload.get("rows", []) if isinstance(x, Mapping)]
    best_embedded: Mapping[str, Any] | None = None
    if embedded_rows:
        # Prefer exact model match, then largest margin.
        model = row.get("model_name")
        if model:
            for erow in embedded_rows:
                if erow.get("model_name") == model:
                    best_embedded = erow
                    break
        if best_embedded is None:
            best_embedded = max(embedded_rows, key=lambda x: finite_float(x.get("radii_margin"), -float("inf")) or -float("inf"))

    artifact_scalar_recompute = recompute_scalar_margin_from_row(best_embedded or row)
    residual_probe = recompute_residual_probe(payload if isinstance(payload, Mapping) else {}, best_embedded or row) if deep else {"available": False, "reason": "deep_disabled"}

    has_samples = bool(arrays_by_kind.get("source_samples"))
    has_coeffs = bool(arrays_by_kind.get("fourier_coefficients"))
    has_residuals = bool(arrays_by_kind.get("residual_coefficients_or_samples"))
    has_matrix = bool(arrays_by_kind.get("finite_matrix_or_jacobian"))
    has_inverse = bool(arrays_by_kind.get("approx_inverse_or_preconditioner"))
    has_tail_profile = bool(arrays_by_kind.get("tail_profile")) or ("modewise_tail_ledger" in "\n".join(keys))
    has_sigma = any(hit.key.lower() == "sigma" for hit in scalars) or any("sigma" in k.lower() for k in keys)
    has_small_divisor = any("small_divisor" in k.lower() or "diophantine" in k.lower() or "cohomolog" in k.lower() for k in keys)

    # What is enough for the two planned follow-up validator directions?
    enough_for_tail_guard_prototype = bool((has_samples or has_coeffs) and has_tail_profile and has_sigma and artifact_scalar_recompute.get("available"))
    enough_for_diagonal_scaling_prototype = bool(has_matrix and has_inverse)
    enough_for_fhl_export_probe = bool(has_samples and has_sigma and has_small_divisor)

    missing: list[str] = []
    if not (has_samples or has_coeffs):
        missing.append("source_samples_or_fourier_coefficients")
    if not has_residuals:
        missing.append("residual_coefficients_or_samples")
    if not has_matrix:
        missing.append("finite_linearized_matrix_or_operator")
    if not has_inverse:
        missing.append("approximate_inverse_or_preconditioner")
    if not has_tail_profile:
        missing.append("modewise_tail_profile")
    if not has_sigma:
        missing.append("analytic_weight_sigma")
    if not has_small_divisor:
        missing.append("small_divisor_or_cohomology_constants")
    if not artifact_scalar_recompute.get("available"):
        missing.append("scalar_ledger_fields_for_margin_recompute")

    result.update({
        "status": "raw-data-audit-complete",
        "candidate_schema": payload.get("schema") if isinstance(payload, Mapping) else None,
        "candidate_status": payload.get("status") if isinstance(payload, Mapping) else None,
        "array_hits_by_kind": arrays_by_kind,
        "scalar_hits": scalar_map,
        "key_count": len(keys),
        "embedded_phase2p_row_count": len(embedded_rows),
        "artifact_scalar_margin_recompute": artifact_scalar_recompute,
        "raw_residual_recompute_probe": residual_probe,
        "availability_flags": {
            "has_source_samples": has_samples,
            "has_fourier_coefficients": has_coeffs,
            "has_residual_coefficients_or_samples": has_residuals,
            "has_finite_matrix_or_jacobian": has_matrix,
            "has_approx_inverse_or_preconditioner": has_inverse,
            "has_modewise_tail_profile": has_tail_profile,
            "has_sigma_or_analytic_weight": has_sigma,
            "has_small_divisor_or_cohomology_constants": has_small_divisor,
            "enough_for_tail_guard_prototype": enough_for_tail_guard_prototype,
            "enough_for_diagonal_scaling_prototype": enough_for_diagonal_scaling_prototype,
            "enough_for_fhl_export_probe": enough_for_fhl_export_probe,
        },
        "missing_for_full_stage1_success": missing,
        "raw_data_stage1_ready": bool(
            (has_samples or has_coeffs)
            and has_residuals
            and has_matrix
            and has_inverse
            and has_tail_profile
            and has_sigma
            and has_small_divisor
            and artifact_scalar_recompute.get("available")
        ),
    })
    result["failure_fields"] = [] if result["raw_data_stage1_ready"] else ["raw_data_incomplete_for_full_validator_upgrade"]
    return result


def summarize_audits(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    def count_flag(name: str) -> int:
        return sum(bool(r.get("availability_flags", {}).get(name)) for r in records)

    buckets: dict[str, int] = {}
    recommended: dict[str, int] = {}
    for r in records:
        buckets[str(r.get("bucket") or "unknown")] = buckets.get(str(r.get("bucket") or "unknown"), 0) + 1
        recommended[str(r.get("recommended_upgrade") or "unknown")] = recommended.get(str(r.get("recommended_upgrade") or "unknown"), 0) + 1

    missing_counts: dict[str, int] = {}
    for r in records:
        for item in r.get("missing_for_full_stage1_success", []) or []:
            missing_counts[str(item)] = missing_counts.get(str(item), 0) + 1

    return {
        "status": "phase2aa-stage1-raw-data-audit-complete",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "record_count": len(records),
        "artifact_exists_count": sum(bool(r.get("artifact_exists")) for r in records),
        "raw_data_stage1_ready_count": sum(bool(r.get("raw_data_stage1_ready")) for r in records),
        "enough_for_tail_guard_prototype_count": count_flag("enough_for_tail_guard_prototype"),
        "enough_for_diagonal_scaling_prototype_count": count_flag("enough_for_diagonal_scaling_prototype"),
        "enough_for_fhl_export_probe_count": count_flag("enough_for_fhl_export_probe"),
        "has_source_samples_count": count_flag("has_source_samples"),
        "has_fourier_coefficients_count": count_flag("has_fourier_coefficients"),
        "has_residual_coefficients_or_samples_count": count_flag("has_residual_coefficients_or_samples"),
        "has_finite_matrix_or_jacobian_count": count_flag("has_finite_matrix_or_jacobian"),
        "has_approx_inverse_or_preconditioner_count": count_flag("has_approx_inverse_or_preconditioner"),
        "has_modewise_tail_profile_count": count_flag("has_modewise_tail_profile"),
        "bucket_counts": buckets,
        "recommended_upgrade_counts": recommended,
        "missing_field_counts": dict(sorted(missing_counts.items())),
        "stage1_gate_passed": bool(records) and all(bool(r.get("raw_data_stage1_ready")) for r in records),
        "next_actions": recommend_next_actions(records, missing_counts),
    }


def recommend_next_actions(records: Sequence[Mapping[str, Any]], missing_counts: Mapping[str, int]) -> list[str]:
    actions: list[str] = []
    n = len(records)
    if not n:
        return ["No candidate records were audited; check the Phase-2Y/summary input paths."]
    if missing_counts.get("finite_linearized_matrix_or_operator", 0) or missing_counts.get("approximate_inverse_or_preconditioner", 0):
        actions.append(
            "Modify Phase 2O/2P exporters to write finite linearized matrix/operator metadata and approximate inverse/preconditioner data for diagonal finite-Krawczyk scaling."
        )
    if missing_counts.get("source_samples_or_fourier_coefficients", 0):
        actions.append(
            "Modify Phase 2N exporter to include source_validation.u or Fourier coefficients for each promoted/diagnostic candidate."
        )
    if missing_counts.get("residual_coefficients_or_samples", 0):
        actions.append(
            "Add residual coefficient/sample export so coefficient-aware nonlinear/tail guards can be checked against raw residual data."
        )
    if missing_counts.get("small_divisor_or_cohomology_constants", 0):
        actions.append(
            "Export small-divisor/cohomology constants used by the current ledger; the FHL-style validator will need these fields."
        )
    tail_ready = sum(bool(r.get("availability_flags", {}).get("enough_for_tail_guard_prototype")) for r in records)
    if tail_ready:
        actions.append(
            f"Proceed with a diagnostic coefficient-aware tail/guard prototype on the {tail_ready} records that have samples/coefficients, sigma, and modewise tail data."
        )
    diag_ready = sum(bool(r.get("availability_flags", {}).get("enough_for_diagonal_scaling_prototype")) for r in records)
    if diag_ready:
        actions.append(
            f"Proceed with diagonal finite-Krawczyk scaling on the {diag_ready} records with finite matrix and inverse/preconditioner data."
        )
    if not actions:
        actions.append("Stage 1 passed for all audited records; proceed to Phase 2AA-B/C validator prototypes.")
    return actions


def write_csv(path: str | Path, records: Sequence[Mapping[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "index", "K_lo", "K_hi", "bucket", "recommended_upgrade", "artifact_exists", "raw_data_stage1_ready",
        "has_source_samples", "has_fourier_coefficients", "has_residual_coefficients_or_samples",
        "has_finite_matrix_or_jacobian", "has_approx_inverse_or_preconditioner", "has_modewise_tail_profile",
        "has_sigma_or_analytic_weight", "has_small_divisor_or_cohomology_constants",
        "enough_for_tail_guard_prototype", "enough_for_diagonal_scaling_prototype", "enough_for_fhl_export_probe",
        "input_row_margin", "input_row_q", "artifact_scalar_margin", "artifact_scalar_margin_error", "residual_probe_available",
        "weighted_residual_l1", "stored_residual_Y", "candidate_path",
        "missing_for_full_stage1_success",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in records:
            flags = r.get("availability_flags", {}) or {}
            scalar = r.get("artifact_scalar_margin_recompute", {}) or {}
            resid = r.get("raw_residual_recompute_probe", {}) or {}
            w.writerow({
                "index": r.get("index"),
                "K_lo": r.get("K_lo"),
                "K_hi": r.get("K_hi"),
                "bucket": r.get("bucket"),
                "recommended_upgrade": r.get("recommended_upgrade"),
                "artifact_exists": r.get("artifact_exists"),
                "raw_data_stage1_ready": r.get("raw_data_stage1_ready"),
                "has_source_samples": flags.get("has_source_samples"),
                "has_fourier_coefficients": flags.get("has_fourier_coefficients"),
                "has_residual_coefficients_or_samples": flags.get("has_residual_coefficients_or_samples"),
                "has_finite_matrix_or_jacobian": flags.get("has_finite_matrix_or_jacobian"),
                "has_approx_inverse_or_preconditioner": flags.get("has_approx_inverse_or_preconditioner"),
                "has_modewise_tail_profile": flags.get("has_modewise_tail_profile"),
                "has_sigma_or_analytic_weight": flags.get("has_sigma_or_analytic_weight"),
                "has_small_divisor_or_cohomology_constants": flags.get("has_small_divisor_or_cohomology_constants"),
                "enough_for_tail_guard_prototype": flags.get("enough_for_tail_guard_prototype"),
                "enough_for_diagonal_scaling_prototype": flags.get("enough_for_diagonal_scaling_prototype"),
                "enough_for_fhl_export_probe": flags.get("enough_for_fhl_export_probe"),
                "input_row_margin": r.get("input_row_margin"),
                "input_row_q": r.get("input_row_q"),
                "artifact_scalar_margin": scalar.get("computed_margin"),
                "artifact_scalar_margin_error": scalar.get("absolute_error"),
                "residual_probe_available": resid.get("available"),
                "weighted_residual_l1": resid.get("weighted_residual_l1"),
                "stored_residual_Y": resid.get("stored_residual_Y"),
                "candidate_path": r.get("candidate_path"),
                "missing_for_full_stage1_success": ";".join(str(x) for x in r.get("missing_for_full_stage1_success", []) or []),
            })


def build_stage1_audit(
    *,
    payloads: Sequence[Mapping[str, Any]],
    root: str | Path = ".",
    target_indices: Sequence[int] = (),
    max_rows: int | None = None,
    deep: bool = True,
) -> dict[str, Any]:
    rows = extract_candidate_rows(*payloads, target_indices=target_indices, max_rows=max_rows)
    records = [audit_candidate(row, root=root, deep=deep) for row in rows]
    summary = summarize_audits(records)
    return {
        "schema": "phase2aa_stage1_raw_data_audit_v1",
        "status": summary["status"],
        "summary": summary,
        "records": records,
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
    }
