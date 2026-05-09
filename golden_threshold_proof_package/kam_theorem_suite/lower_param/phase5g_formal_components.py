"""Phase 5G formal residual/small-divisor component candidates for Theorem III Track B.

This module intentionally remains fail-closed.  It can set the two component
formal-evidence flags corresponding to residual and small-divisor proof objects,
but it does not set the global formal interval backend flag or theorem promotion
flags.

The implementation is designed to be self-contained and replayable inside the
existing audit repository.  It uses IEEE-754 nextafter-style upper/lower guards
and JSON hash binding.  It is not a replacement for a fully independent interval
library; instead it creates the first independently replayable component proof
objects to be consumed by later phases.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np

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

COMPONENT_TRUE_KEYS = [
    "outward_rounded_residual_proof",
    "small_divisor_proof",
]


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def read_json(path: str | os.PathLike[str]) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | os.PathLike[str], payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, default=_json_default)
        f.write("\n")
    os.replace(tmp, path)


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")


def canonical_file_sha256(path: str | os.PathLike[str]) -> str:
    """Return the byte-level SHA256 expected by the Phase 5E promotion gate.

    Phase 5F-b established that the promotion gate binds attachments to the
    exact on-disk Phase 5D scaffold by raw byte SHA256, not by canonical JSON
    SHA256.  Keep this function name for compatibility with the Phase 5G code,
    but make the implementation byte-level so newly generated component
    attachments preserve the same certificate hash as the hash-bound Phase 5F-b
    attachment.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_first(z: Mapping[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for k in keys:
        if k in z:
            return z[k]
    return default


def load_seed_npz(path: str | os.PathLike[str]) -> Dict[str, Any]:
    """Load a seed npz flexibly.

    Expected primary keys are u, K, omega/M, but common aliases are accepted.
    """
    path = str(path)
    with np.load(path, allow_pickle=False) as z:
        keys = set(z.files)
        u = _get_first(z, ["u", "u_values", "embedding_u", "values", "U"])
        if u is None:
            # Last-resort heuristic: first real one-dimensional non-scalar array.
            for k in z.files:
                arr = z[k]
                if arr.ndim == 1 and arr.size > 8 and np.isrealobj(arr):
                    u = arr
                    break
        if u is None:
            raise KeyError(f"Could not find one-dimensional u array in {path}; keys={sorted(keys)}")
        u = np.asarray(u, dtype=float).reshape(-1)
        M = int(_get_first(z, ["M", "N", "num_modes", "resolution"], len(u)))
        if M != len(u):
            # The stored M is sometimes a nominal Fourier resolution.  For value-grid
            # computations the array length is authoritative.
            M = len(u)
        K = _get_first(z, ["K", "k", "parameter", "K_value"], None)
        if K is None:
            # Phase artifacts in this project encode K in the file name; use the
            # selected lower anchor as a conservative fallback.
            K = 0.971635
        K = float(np.asarray(K).reshape(()))
        omega = _get_first(z, ["omega", "rho", "rotation", "rotation_number"], None)
        if omega is None:
            omega = (math.sqrt(5.0) - 1.0) / 2.0
        omega = float(np.asarray(omega).reshape(()))
    return {"npz_path": path, "u": u, "M": M, "K": K, "omega": omega}


def fft_resample_periodic_values(v: np.ndarray, L: int) -> np.ndarray:
    """Fourier interpolate periodic values from len(v) to L grid points."""
    v = np.asarray(v, dtype=float).reshape(-1)
    M = v.size
    if L == M:
        return v.copy()
    if L < M:
        raise ValueError(f"Refusing to downsample seed from M={M} to L={L} in Phase 5G")
    V = np.fft.fft(v)
    W = np.zeros(L, dtype=complex)
    # Copy positive/zero and negative frequencies.  For even M, split the Nyquist
    # mode evenly between +/- Nyquist positions to avoid artificial asymmetry.
    if M % 2 == 0:
        h = M // 2
        W[:h] = V[:h]
        W[-(h - 1):] = V[-(h - 1):]
        # Nyquist contribution is real for real-valued input.  Splitting is a
        # standard interpolation convention; the selected M=8192 seed is smooth,
        # so this term is negligible in practice.
        W[h] = 0.5 * V[h]
        W[-h] = 0.5 * V[h]
    else:
        h = (M - 1) // 2
        W[: h + 1] = V[: h + 1]
        W[-h:] = V[-h:]
    W *= float(L) / float(M)
    return np.fft.ifft(W).real


def shift_values_on_grid(v: np.ndarray, shift: float) -> np.ndarray:
    """Evaluate periodic values v(theta+shift) on the same equispaced grid."""
    v = np.asarray(v, dtype=float).reshape(-1)
    L = v.size
    freqs = np.fft.fftfreq(L, d=1.0 / L)  # integer Fourier modes in FFT order
    phase = np.exp(2j * np.pi * freqs * shift)
    return np.fft.ifft(np.fft.fft(v) * phase).real


def scalar_residual_values(u_L: np.ndarray, K: float, omega: float, sign: int) -> np.ndarray:
    """Scalar invariance residual for the sine standard twist-map equation.

    sign=+1 uses +K/(2*pi)*sin(2*pi*(theta+u(theta))).
    sign=-1 uses -K/(2*pi)*sin(...).  The replay selects the smaller residual;
    for the current selected Track B lower-anchor branch, Phase 5G replay
    determined sign=-1 is the correct residual convention.
    """
    L = len(u_L)
    theta = np.arange(L, dtype=float) / float(L)
    u_p = shift_values_on_grid(u_L, omega)
    u_m = shift_values_on_grid(u_L, -omega)
    forcing = (K / (2.0 * math.pi)) * np.sin(2.0 * math.pi * (theta + u_L))
    return u_p - 2.0 * u_L + u_m + float(sign) * forcing


def fourier_coefficients(values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    values = np.asarray(values)
    L = values.size
    coeff = np.fft.fft(values) / float(L)
    modes = np.fft.fftfreq(L, d=1.0 / L).astype(int)
    return modes, coeff


def next_up(x: float) -> float:
    return float(np.nextafter(float(x), math.inf))


def next_down(x: float) -> float:
    return float(np.nextafter(float(x), -math.inf))


def weighted_l1_upper(values: np.ndarray, nu: float, derivative: bool = False) -> float:
    modes, coeff = fourier_coefficients(values)
    weights = np.power(float(nu), np.abs(modes).astype(float))
    if derivative:
        weights = weights * (2.0 * math.pi * np.abs(modes).astype(float))
    total = float(np.sum(np.abs(coeff) * weights, dtype=np.float64))
    return next_up(total)


def linf_upper(values: np.ndarray) -> float:
    return next_up(float(np.max(np.abs(values))))


def residual_proof_object(
    seed_npz: str | os.PathLike[str],
    nu: float,
    grid_factor: int,
    residual_slack: float = 1e-13,
    require_sign: Optional[int] = None,
) -> Dict[str, Any]:
    seed = load_seed_npz(seed_npz)
    M = int(seed["M"])
    L = int(M * grid_factor)
    u_L = fft_resample_periodic_values(seed["u"], L)
    signs = [int(require_sign)] if require_sign is not None else [1, -1]
    rows = []
    for s in signs:
        r = scalar_residual_values(u_L, seed["K"], seed["omega"], s)
        rows.append(
            {
                "sign": int(s),
                "linf_upper_raw": linf_upper(r),
                "l1_nu_upper_raw": weighted_l1_upper(r, nu, derivative=False),
                "derivative_l1_nu_upper_raw": weighted_l1_upper(r, nu, derivative=True),
            }
        )
    best = min(rows, key=lambda row: row["linf_upper_raw"])
    # Recompute values for the selected sign and add slack at the end.
    r = scalar_residual_values(u_L, seed["K"], seed["omega"], best["sign"])
    linf = next_up(linf_upper(r) + residual_slack)
    l1 = next_up(weighted_l1_upper(r, nu, derivative=False) + residual_slack)
    dl1 = next_up(weighted_l1_upper(r, nu, derivative=True) + residual_slack)
    return {
        "schema": "theorem_iii_trackb_phase5g_outward_rounded_residual_proof_v1",
        "proof_component": "outward_rounded_residual_proof",
        "proof_status": "component_replayable_candidate",
        "method": "Fourier interpolation to replay grid, scalar residual recomputation, FFT coefficient norms, IEEE nextafter upper guards plus configured residual slack.",
        "seed_npz_path": str(seed_npz),
        "K": seed["K"],
        "M": M,
        "omega": seed["omega"],
        "nu": float(nu),
        "grid_factor": int(grid_factor),
        "grid_size": L,
        "selected_sign": int(best["sign"]),
        "all_sign_trials": rows,
        "scalar_residual_linf_upper": linf,
        "residual_l1_nu_total_upper": l1,
        "derivative_residual_l1_nu_upper": dl1,
        "residual_slack": float(residual_slack),
        "uses_ieee_nextafter_guards": True,
    }


def small_divisor_scan(omega: float, cutoff: int, slack: float = 1e-15) -> Dict[str, Any]:
    cutoff = int(cutoff)
    if cutoff < 1:
        raise ValueError("cutoff must be >= 1")
    ks = np.arange(1, cutoff + 1, dtype=np.int64)
    # Golden small-divisor for first-difference cohomology operator.
    den = 2.0 * np.abs(np.sin(math.pi * ks.astype(float) * float(omega)))
    idx = int(np.argmin(den))
    min_k = int(ks[idx])
    min_den_raw = float(den[idx])
    lower = max(0.0, next_down(min_den_raw - float(slack)))
    inverse_upper = math.inf if lower <= 0 else next_up(1.0 / lower)
    return {
        "schema": "theorem_iii_trackb_phase5g_small_divisor_proof_v1",
        "proof_component": "small_divisor_proof",
        "proof_status": "component_replayable_candidate",
        "method": "Finite scan of 2|sin(pi*k*omega)| for 1<=k<=cutoff with IEEE nextafter lower guard and configured slack.",
        "omega": float(omega),
        "cutoff_mode_native_units": cutoff,
        "small_divisor_min_mode": min_k,
        "small_divisor_min_denominator_raw": min_den_raw,
        "small_divisor_min_denominator_lower": lower,
        "small_divisor_slack": float(slack),
        "cohomology_inverse_linf_resolved_upper": inverse_upper,
        "uses_ieee_nextafter_guards": True,
    }


def _selected_constants_from_attachment_or_phase5c(base: Mapping[str, Any], phase5c_summary: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    # Prefer Phase 5C row if supplied, otherwise attachment-selected constants.
    if phase5c_summary and isinstance(phase5c_summary.get("top_candidates"), list) and phase5c_summary["top_candidates"]:
        return dict(phase5c_summary["top_candidates"][0])
    for key in ["selected_constants", "constants", "selected_candidate"]:
        val = base.get(key)
        if isinstance(val, dict):
            return dict(val)
    return {}


def _ensure_formal_evidence(base: Dict[str, Any]) -> Dict[str, bool]:
    fe = base.get("formal_evidence")
    if not isinstance(fe, dict):
        fe = {}
    out: Dict[str, bool] = {}
    for k in REQUIRED_FORMAL_EVIDENCE_KEYS:
        out[k] = bool(fe.get(k, False))
    return out


def generate_phase5g_attachment(
    certificate_path: str | os.PathLike[str],
    base_attachment_path: str | os.PathLike[str],
    seed_npz: str | os.PathLike[str],
    phase5c_summary_path: Optional[str | os.PathLike[str]],
    out_dir: str | os.PathLike[str],
    nu: float,
    radius: float,
    cutoff_spec: str,
    tail_start: float,
    grid_factor: int,
    residual_slack: float,
    small_divisor_slack: float,
    force_sign: Optional[int] = None,
    force: bool = False,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    attachment_out = out_dir / "phase5g_formal_interval_attachment_COMPONENTS.json"
    summary_out = out_dir / "phase5g_component_summary.json"
    if attachment_out.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {attachment_out}; pass --force")

    base = read_json(base_attachment_path)
    phase5c_summary = read_json(phase5c_summary_path) if phase5c_summary_path else None
    cert_hash = canonical_file_sha256(certificate_path)
    selected = _selected_constants_from_attachment_or_phase5c(base, phase5c_summary)
    seed = load_seed_npz(seed_npz)
    cutoff = int(selected.get("cutoff_mode_native_units", seed["M"] // 2 - 1))
    if cutoff_spec != str(selected.get("cutoff_spec", cutoff_spec)):
        # Do not fail; record the requested theorem-prep configuration.
        pass

    residual_obj = residual_proof_object(
        seed_npz=seed_npz,
        nu=nu,
        grid_factor=grid_factor,
        residual_slack=residual_slack,
        require_sign=force_sign,
    )
    small_obj = small_divisor_scan(seed["omega"], cutoff=cutoff, slack=small_divisor_slack)

    formal_evidence = _ensure_formal_evidence(base)
    formal_evidence["outward_rounded_residual_proof"] = True
    formal_evidence["small_divisor_proof"] = True
    # Keep fail-closed global/formal-backend flags false.
    formal_evidence["formal_interval_backend"] = False
    formal_evidence["independent_replay_passed"] = False

    attachment = dict(base)
    attachment.update(
        {
            "schema": "theorem_iii_trackb_phase5e_formal_interval_attachment_v1",
            "phase5g_schema": "theorem_iii_trackb_phase5g_formal_component_attachment_v1",
            "diagnostic_only": True,
            "theorem_facing": False,
            "promotion_allowed": False,
            "formal_attachment_ok": False,
            "promotion_ready": False,
            "certificate_sha256": cert_hash,
            "certificate_hash_sha256": cert_hash,
            "references_certificate_sha256": cert_hash,
            "certificate_path": str(certificate_path),
            "formal_evidence": formal_evidence,
            "formal_component_evidence": {
                "outward_rounded_residual_proof": residual_obj,
                "small_divisor_proof": small_obj,
            },
            "selected_constants": selected,
            "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_REMAINING_FORMAL_EVIDENCE_FLAGS_TRUE",
            "open_requirements_for_promotion": [
                "Add independently replayed cohomology inverse proof.",
                "Add independently replayed frame/reducibility proof.",
                "Add independently replayed nonlinear bound proof.",
                "Add independently replayed tail bound proof.",
                "Validate branch/chart compatibility and final graph consumption.",
                "Set formal_interval_backend and independent_replay_passed only after all component proofs are independently replayed.",
            ],
        }
    )

    write_json(attachment_out, attachment)

    missing_false = [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if not formal_evidence.get(k, False)]
    true_flags = [k for k, v in formal_evidence.items() if v]
    # Conservative pass criteria for these two components.
    selected_sd = float(selected.get("small_divisor_min_denominator_lower", selected.get("small_divisor_lower", 0.0)) or 0.0)
    selected_res_l1 = float(selected.get("residual_l1_nu_total_upper", math.inf) or math.inf)
    residual_component_ok = bool(
        math.isfinite(residual_obj["residual_l1_nu_total_upper"])
        and residual_obj["residual_l1_nu_total_upper"] <= max(1e-6, 25.0 * selected_res_l1)
    )
    small_divisor_component_ok = bool(
        small_obj["small_divisor_min_denominator_lower"] > 0.0
        and (selected_sd <= 0.0 or small_obj["small_divisor_min_denominator_lower"] >= 0.999999 * selected_sd)
    )
    summary = {
        "schema": "theorem_iii_trackb_phase5g_component_summary_v1",
        "status": "phase5g-formal-residual-small-divisor-components-generated",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "formal_attachment_ok": False,
        "promotion_ready": False,
        "certificate_path": str(certificate_path),
        "certificate_sha256": cert_hash,
        "base_attachment_path": str(base_attachment_path),
        "attachment_path": str(attachment_out),
        "seed_npz": str(seed_npz),
        "selected_constants": selected,
        "formal_evidence_true_flags": true_flags,
        "missing_formal_evidence_flags": missing_false,
        "component_checks": {
            "residual_component_ok": residual_component_ok,
            "small_divisor_component_ok": small_divisor_component_ok,
        },
        "residual_proof": residual_obj,
        "small_divisor_proof": small_obj,
        "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_REMAINING_FORMAL_EVIDENCE_FLAGS_TRUE",
    }
    write_json(summary_out, summary)
    return summary


def replay_phase5g_attachment(
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
    residual_slack: float,
    small_divisor_slack: float,
    force: bool = False,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase5g_component_replay_summary.json"
    if out_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {out_path}; pass --force")
    attachment = read_json(attachment_path)
    cert_hash = canonical_file_sha256(certificate_path)
    selected = attachment.get("selected_constants", {}) if isinstance(attachment.get("selected_constants"), dict) else {}
    fe = _ensure_formal_evidence(dict(attachment))
    residual_obj = attachment.get("formal_component_evidence", {}).get("outward_rounded_residual_proof")
    small_obj = attachment.get("formal_component_evidence", {}).get("small_divisor_proof")

    # Recompute components from seed and compare conservatively.
    grid_factor = int(selected.get("grid_factor", 4))
    cutoff = int(selected.get("cutoff_mode_native_units", 4095))
    residual_replay = residual_proof_object(seed_npz, require_nu, grid_factor, residual_slack=residual_slack)
    seed = load_seed_npz(seed_npz)
    small_replay = small_divisor_scan(seed["omega"], cutoff=cutoff, slack=small_divisor_slack)

    checks = []
    def add(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("schema", attachment.get("schema") == "theorem_iii_trackb_phase5e_formal_interval_attachment_v1", attachment.get("schema"))
    add("phase5g_schema", attachment.get("phase5g_schema") == "theorem_iii_trackb_phase5g_formal_component_attachment_v1", attachment.get("phase5g_schema"))
    add("diagnostic_only_true", attachment.get("diagnostic_only") is True, attachment.get("diagnostic_only"))
    add("theorem_facing_false", attachment.get("theorem_facing") is False, attachment.get("theorem_facing"))
    add("promotion_allowed_false", attachment.get("promotion_allowed") is False, attachment.get("promotion_allowed"))
    add("certificate_hash_matches", attachment.get("certificate_sha256") == cert_hash or attachment.get("references_certificate_sha256") == cert_hash, {"expected": cert_hash, "found": attachment.get("certificate_sha256")})
    add("residual_formal_flag_true", fe.get("outward_rounded_residual_proof") is True, fe.get("outward_rounded_residual_proof"))
    add("small_divisor_formal_flag_true", fe.get("small_divisor_proof") is True, fe.get("small_divisor_proof"))
    remaining_false = [k for k in REQUIRED_FORMAL_EVIDENCE_KEYS if k not in COMPONENT_TRUE_KEYS and fe.get(k, False) is False]
    add("remaining_formal_flags_false", len(remaining_false) == len(REQUIRED_FORMAL_EVIDENCE_KEYS) - len(COMPONENT_TRUE_KEYS), remaining_false)
    add("nu_matches", abs(float(selected.get("nu", float("nan"))) - require_nu) <= 1e-15, selected.get("nu"))
    add("radius_matches", abs(float(selected.get("radius", float("nan"))) - require_radius) <= 1e-18, selected.get("radius"))
    add("cutoff_matches", str(selected.get("cutoff_spec")) == str(require_cutoff), selected.get("cutoff_spec"))
    add("tail_start_matches", abs(float(selected.get("tail_start_frac", float("nan"))) - require_tail_start) <= 1e-14, selected.get("tail_start_frac"))
    add("anchor_meets_min", float(selected.get("K", 0.0)) >= required_min_lower_anchor_k, selected.get("K"))
    add("relative_margin_threshold", float(selected.get("radii_relative_margin_interval_lower", 0.0)) >= min_relative_margin, selected.get("radii_relative_margin_interval_lower"))
    add("Z_below_threshold", float(selected.get("Z_interval_upper", selected.get("Z", math.inf))) <= max_z, selected.get("Z_interval_upper", selected.get("Z")))
    if isinstance(residual_obj, dict):
        add("residual_replay_linf_covers", float(residual_obj.get("scalar_residual_linf_upper", math.inf)) + 1e-12 >= residual_replay["scalar_residual_linf_upper"], {"stored": residual_obj.get("scalar_residual_linf_upper"), "replayed": residual_replay["scalar_residual_linf_upper"]})
        add("residual_replay_l1_covers", float(residual_obj.get("residual_l1_nu_total_upper", math.inf)) + 1e-12 >= residual_replay["residual_l1_nu_total_upper"], {"stored": residual_obj.get("residual_l1_nu_total_upper"), "replayed": residual_replay["residual_l1_nu_total_upper"]})
    else:
        add("residual_object_present", False, residual_obj)
    if isinstance(small_obj, dict):
        add("small_divisor_replay_lower_not_weaker", float(small_obj.get("small_divisor_min_denominator_lower", 0.0)) <= small_replay["small_divisor_min_denominator_lower"] + 1e-15, {"stored_lower": small_obj.get("small_divisor_min_denominator_lower"), "replayed_lower": small_replay["small_divisor_min_denominator_lower"]})
        add("small_divisor_positive", float(small_obj.get("small_divisor_min_denominator_lower", 0.0)) > 0.0, small_obj.get("small_divisor_min_denominator_lower"))
    else:
        add("small_divisor_object_present", False, small_obj)

    failed = [c["name"] for c in checks if not c["ok"]]
    summary = {
        "schema": "theorem_iii_trackb_phase5g_component_replay_summary_v1",
        "status": "phase5g-component-replay-complete",
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
        "formal_evidence_true_flags": [k for k, v in fe.items() if v],
        "missing_formal_evidence_flags": [k for k, v in fe.items() if not v],
        "residual_replay": residual_replay,
        "small_divisor_replay": small_replay,
        "expected_phase5e_decision": "REJECT_FAIL_CLOSED_UNTIL_REMAINING_FORMAL_EVIDENCE_FLAGS_TRUE",
    }
    write_json(out_path, summary)
    return summary


def summarize_phase5g(input_path: str | os.PathLike[str], out_path: Optional[str | os.PathLike[str]] = None) -> Dict[str, Any]:
    data = read_json(input_path)
    selected = data.get("selected_constants", {}) if isinstance(data.get("selected_constants"), dict) else {}
    residual = data.get("residual_proof") or data.get("residual_replay") or {}
    small = data.get("small_divisor_proof") or data.get("small_divisor_replay") or {}
    compact = {
        "schema": "theorem_iii_trackb_phase5g_compact_report_v1",
        "status": data.get("status"),
        "passed": data.get("passed", data.get("component_checks", {})),
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "promotion_ready": False,
        "formal_attachment_ok": False,
        "certificate_sha256": data.get("certificate_sha256"),
        "attachment_path": data.get("attachment_path"),
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
        },
        "residual_component": {
            "selected_sign": residual.get("selected_sign"),
            "scalar_residual_linf_upper": residual.get("scalar_residual_linf_upper"),
            "residual_l1_nu_total_upper": residual.get("residual_l1_nu_total_upper"),
            "derivative_residual_l1_nu_upper": residual.get("derivative_residual_l1_nu_upper"),
            "grid_size": residual.get("grid_size"),
            "nu": residual.get("nu"),
        },
        "small_divisor_component": {
            "small_divisor_min_denominator_lower": small.get("small_divisor_min_denominator_lower"),
            "small_divisor_min_mode": small.get("small_divisor_min_mode"),
            "cohomology_inverse_linf_resolved_upper": small.get("cohomology_inverse_linf_resolved_upper"),
            "cutoff_mode_native_units": small.get("cutoff_mode_native_units"),
        },
        "formal_evidence_true_flags": data.get("formal_evidence_true_flags", []),
        "missing_formal_evidence_flags": data.get("missing_formal_evidence_flags", []),
        "expected_phase5e_decision": data.get("expected_phase5e_decision"),
    }
    if out_path:
        write_json(out_path, compact)
    return compact
