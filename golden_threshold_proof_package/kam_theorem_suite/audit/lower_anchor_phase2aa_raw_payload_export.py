from __future__ import annotations

"""Phase 2AA-B raw-validation payload exporter for Theorem III.

This module is a diagnostic/export layer only.  It attaches replayable raw
validation data to Phase-2O/2P single-segment candidates so Stage 1/Stage 2
validator-development audits can inspect actual samples, Fourier coefficients,
residual coefficients, scalar ledger terms, and finite-operator metadata.

It deliberately does not mark any candidate theorem-facing and it does not
change closure logic.  The payload is designed to make the next validator
upgrades honest:

* coefficient-aware tail/nonlinear guard prototypes need source samples,
  Fourier coefficients, residual coefficients, sigma, and scalar ledger terms;
* diagonal finite-Krawczyk prototypes need enough information to reconstruct the
  finite linearized operator and preconditioner used by the current graph
  equation; and
* FHL/parameterization-method probes need source samples, frequency/parameter
  data, and small-divisor/cohomology constants.
"""

from pathlib import Path
from typing import Any, Mapping
import math

import numpy as np

from ..analytic_norms import spectral_coefficients_from_samples, spectral_wavenumbers
from ..invariance_defect import residual_samples
from ..standard_map import HarmonicFamily
from ..torus_validator import linearized_augmented_operator_matrix

GOLDEN_INVERSE = (math.sqrt(5.0) - 1.0) / 2.0
RAW_PAYLOAD_VERSION = "phase2aa_raw_validation_payload_v1"


def _as_mapping(x: Any) -> Mapping[str, Any]:
    return x if isinstance(x, Mapping) else {}


def _finite_float(x: Any, default: float | None = None) -> float | None:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _finite_int(x: Any, default: int | None = None) -> int | None:
    y = _finite_float(x)
    if y is None:
        return default
    return int(y)


def _json_float(x: Any) -> float | None:
    y = _finite_float(x)
    return None if y is None else float(y)


def _real_list(arr: Any, *, max_len: int | None = None) -> list[float]:
    a = np.asarray(arr, dtype=float).reshape(-1)
    if max_len is not None:
        a = a[: int(max_len)]
    return [float(x) for x in a.tolist()]


def _complex_coeff_payload(coeffs: np.ndarray, *, max_len: int | None = None) -> dict[str, Any]:
    c = np.asarray(coeffs, dtype=complex).reshape(-1)
    if max_len is not None:
        c = c[: int(max_len)]
    return {
        "normalization": "numpy_fft_divided_by_N_shifted_like_spectral_coefficients_from_samples",
        "length": int(c.size),
        "real": [float(x) for x in c.real.tolist()],
        "imag": [float(x) for x in c.imag.tolist()],
    }


def _extract_source_validation(phase2n_attempt: Mapping[str, Any] | None) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    attempt = _as_mapping(phase2n_attempt)
    raw = _as_mapping(attempt.get("raw_certificate"))
    src = _as_mapping(raw.get("source_validation"))
    if not src:
        # Some future artifacts may store the validation dict directly.
        src = _as_mapping(attempt.get("source_validation"))
    return raw, src


def _extract_u_z_lambda(raw: Mapping[str, Any], src: Mapping[str, Any]) -> tuple[np.ndarray | None, np.ndarray | None, float | None, dict[str, Any]]:
    summary: dict[str, Any] = {"source_validation_present": bool(src)}
    u_raw = src.get("u", raw.get("u"))
    z_raw = src.get("z", raw.get("z"))
    lam = _finite_float(src.get("lambda_value", raw.get("lambda_value")))
    try:
        u = np.asarray(u_raw, dtype=float)
    except Exception:
        u = None
    if u is not None and u.size == 0:
        u = None
    try:
        z = np.asarray(z_raw, dtype=float)
    except Exception:
        z = None
    if z is not None and z.size == 0:
        z = None
    if lam is None and z is not None and z.size >= 1:
        lam = _finite_float(z[-1])
    summary.update({
        "has_u": bool(u is not None),
        "u_length": None if u is None else int(u.size),
        "has_z": bool(z is not None),
        "z_length": None if z is None else int(z.size),
        "has_lambda": bool(lam is not None),
        "lambda_value": None if lam is None else float(lam),
    })
    return u, z, lam, summary


def _input_value(input_summary: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(input_summary, Mapping):
        return input_summary.get(key, default)
    if hasattr(input_summary, key):
        return getattr(input_summary, key)
    if hasattr(input_summary, "to_dict"):
        try:
            d = input_summary.to_dict()
            if isinstance(d, Mapping):
                return d.get(key, default)
        except Exception:
            pass
    return default


def _row_value(row: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in row and row.get(key) is not None:
            return row.get(key)
    return default


def _scalar_ledger_payload(selected_row: Mapping[str, Any]) -> dict[str, Any]:
    radius = _finite_float(_row_value(selected_row, "radius_r"))
    residual = _finite_float(_row_value(selected_row, "residual_Y"))
    linear_z = _finite_float(_row_value(selected_row, "linear_Z", "linear_defect_Z"))
    finite_nl = _finite_float(_row_value(selected_row, "finite_nonlinear_term"))
    tail_T = _finite_float(_row_value(selected_row, "tail_T", "tail_bound_T"))
    tail_response = _finite_float(_row_value(selected_row, "tail_response_bound"))
    nonlinear_guard = _finite_float(_row_value(selected_row, "nonlinear_guard"))
    if tail_T is None and tail_response is not None and nonlinear_guard is not None:
        tail_T = float(tail_response + nonlinear_guard)
    if finite_nl is None and linear_z is not None and radius is not None:
        finite_nl = float(linear_z * radius)
    stored_margin = _finite_float(_row_value(selected_row, "radii_margin", "margin"))
    if radius is not None and residual is not None and linear_z is not None and tail_T is not None:
        recomputed = float(radius - (residual + linear_z * radius + tail_T))
    else:
        recomputed = None
    if radius is not None and residual is not None and finite_nl is not None:
        allowable = float(radius - finite_nl - residual)
    else:
        allowable = _finite_float(_row_value(selected_row, "allowable_tail_max"))
    return {
        "available": bool(recomputed is not None),
        "radius_r": radius,
        "residual_Y": residual,
        "linear_Z": linear_z,
        "finite_nonlinear_term": finite_nl,
        "finite_contraction_q": _finite_float(_row_value(selected_row, "finite_contraction_q")),
        "finite_poly_margin": _finite_float(_row_value(selected_row, "finite_poly_margin")),
        "tail_T": tail_T,
        "tail_response_bound": tail_response,
        "nonlinear_guard": nonlinear_guard,
        "allowable_tail_max": allowable,
        "radii_margin": stored_margin,
        "recomputed_margin": recomputed,
        "recompute_minus_stored": None if (recomputed is None or stored_margin is None) else float(recomputed - stored_margin),
        "formula": "radii_margin = radius_r - (residual_Y + linear_Z*radius_r + tail_T)",
    }


def _small_divisor_payload(raw: Mapping[str, Any], selected_row: Mapping[str, Any]) -> dict[str, Any]:
    audit = _as_mapping(raw.get("small_divisor_audit"))
    led = _as_mapping(selected_row.get("modewise_tail_ledger"))
    return {
        "available": bool(audit or led),
        "source": "raw_certificate.small_divisor_audit_and_selected_modewise_tail_ledger",
        "raw_small_divisor_audit": dict(audit),
        "golden_diophantine_constant": _finite_float(led.get("golden_diophantine_constant")),
        "worst_finite_inverse": _finite_float(led.get("worst_finite_inverse")),
        "worst_finite_inverse_mode": _finite_int(led.get("worst_finite_inverse_mode")),
        "global_inverse_bound": _finite_float(_row_value(selected_row, "global_inverse_bound"), _finite_float(raw.get("cohomological_inverse_bound"))),
        "cohomological_inverse_bound": _finite_float(raw.get("cohomological_inverse_bound")),
    }


def _finite_operator_payload(*, u: np.ndarray | None, rho: float | None, K: float | None, family: HarmonicFamily, raw: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "available": False,
        "representation": "replayable_operator_plus_norm_profiles",
        "replay_function": "kam_theorem_suite.torus_validator.linearized_augmented_operator_matrix(u, rho, K, HarmonicFamily())",
        "full_matrix_stored": False,
        "reason": None,
    }
    if u is None or rho is None or K is None:
        payload["reason"] = "missing_u_rho_or_K"
        return payload
    try:
        J = linearized_augmented_operator_matrix(np.asarray(u, dtype=float), float(rho), float(K), family)
        J = np.asarray(J, dtype=float)
        absJ = np.abs(J)
        row_sums = np.sum(absJ, axis=1)
        col_sums = np.sum(absJ, axis=0)
        diag = np.diag(J)
        payload.update({
            "available": True,
            "reason": None,
            "matrix_shape": [int(J.shape[0]), int(J.shape[1])],
            "jacobian_row_abs_sums": _real_list(row_sums),
            "jacobian_col_abs_sums": _real_list(col_sums),
            "jacobian_diagonal": _real_list(diag),
            "jacobian_inf_norm": float(np.max(row_sums)) if row_sums.size else 0.0,
            "jacobian_one_norm": float(np.max(col_sums)) if col_sums.size else 0.0,
            "finite_B_norm_from_raw_certificate": _json_float(raw.get("finite_B_norm")),
            "finite_lipschitz_bound_from_raw_certificate": _json_float(raw.get("finite_lipschitz_bound")),
            "finite_contraction_bound_from_raw_certificate": _json_float(raw.get("finite_contraction_bound")),
            "note": "Full matrix is intentionally not serialized by default; Stage-2 diagonal scaling can replay it from u/rho/K.",
        })
        return payload
    except Exception as exc:
        payload["reason"] = "linearized_operator_replay_failed"
        payload["exception"] = repr(exc)
        return payload


def _preconditioner_payload(raw: Mapping[str, Any], selected_row: Mapping[str, Any], finite_operator: Mapping[str, Any]) -> dict[str, Any]:
    b_norm = _finite_float(raw.get("finite_B_norm"))
    inv_bound = _finite_float(raw.get("cohomological_inverse_bound"))
    q = _finite_float(_row_value(selected_row, "finite_contraction_q"), _finite_float(raw.get("finite_contraction_bound")))
    proxy = [x for x in (b_norm, inv_bound, q) if x is not None]
    if len(proxy) < 2:
        proxy = proxy + [0.0] * (2 - len(proxy))
    return {
        "available": bool(b_norm is not None or inv_bound is not None),
        "representation": "replayable_preconditioner_metadata_and_norm_proxy",
        "replay_note": "The original approximate inverse matrix is not stored by this patch; Stage-2 may reconstruct finite inverse from the replayed Jacobian if needed.",
        "finite_B_norm": b_norm,
        "cohomological_inverse_bound": inv_bound,
        "finite_contraction_q": q,
        "inverse_norm_proxy_vector": [float(x) for x in proxy],
        "operator_payload_available": bool(finite_operator.get("available")),
    }


def build_raw_validation_payload(
    *,
    phase2n_attempt: Mapping[str, Any] | None,
    selected_row: Mapping[str, Any],
    input_summary: Mapping[str, Any] | Any,
    source_artifact: str | None = None,
    stage: str = "phase2p",
    include_samples: bool = True,
    include_coefficients: bool = True,
    include_residual_samples: bool = True,
    include_operator_profiles: bool = True,
) -> dict[str, Any]:
    raw, src = _extract_source_validation(phase2n_attempt)
    u, z, lam, source_summary = _extract_u_z_lambda(raw, src)
    family = HarmonicFamily()
    K = _finite_float(_input_value(input_summary, "K_mid"), _finite_float(raw.get("K")))
    if K is None:
        lo = _finite_float(_input_value(input_summary, "K_lo"))
        hi = _finite_float(_input_value(input_summary, "K_hi"))
        if lo is not None and hi is not None:
            K = 0.5 * (lo + hi)
    rho = _finite_float(_input_value(input_summary, "rho"), _finite_float(raw.get("rho"), GOLDEN_INVERSE))
    N = _finite_int(_input_value(input_summary, "N"), _finite_int(raw.get("N"), None))
    sigma = _finite_float(_row_value(selected_row, "sigma"), _finite_float(raw.get("sigma_used"), _finite_float(raw.get("sigma"))))
    oversample_factor = _finite_int(_row_value(selected_row, "oversample_factor"), _finite_int(_input_value(input_summary, "oversample_factor"), 16)) or 16

    payload: dict[str, Any] = {
        "raw_validation_payload_version": RAW_PAYLOAD_VERSION,
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "stage": str(stage),
        "source_artifact": str(source_artifact) if source_artifact is not None else None,
        "K_interval": [_json_float(_input_value(input_summary, "K_lo")), _json_float(_input_value(input_summary, "K_hi"))],
        "K_mid": K,
        "rho": rho,
        "N": N,
        "sigma": sigma,
        "oversample_factor": int(oversample_factor),
        "source_summary": source_summary,
        "grid_metadata": {
            "grid_type": "equispaced_periodic",
            "sample_count": None if u is None else int(u.size),
            "fft_normalization": "spectral_coefficients_from_samples / numpy FFT convention",
        },
        "scalar_ledger_recompute": _scalar_ledger_payload(selected_row),
        "selected_row_snapshot": dict(selected_row),
    }

    if u is not None:
        u_arr = np.asarray(u, dtype=float)
        payload["source_validation"] = {
            "available": True,
            "u": _real_list(u_arr) if include_samples else [],
            "z": _real_list(z) if (include_samples and z is not None) else [],
            "lambda_value": None if lam is None else float(lam),
            "N_from_u": int(u_arr.size),
        }
        if include_coefficients:
            coeffs = spectral_coefficients_from_samples(u_arr)
            payload["source_fourier_coefficients"] = _complex_coeff_payload(coeffs)
            payload["source_wavenumbers"] = _real_list(spectral_wavenumbers(len(coeffs)))
        if K is not None and rho is not None and lam is not None:
            try:
                resid = residual_samples(u_arr, float(rho), float(K), family, lambda_value=float(lam), oversample_factor=int(oversample_factor))
                resid = np.asarray(resid, dtype=float)
                rcoeffs = spectral_coefficients_from_samples(resid)
                payload["residual"] = {
                    "available": True,
                    "representation": "samples_and_fourier_coefficients",
                    "samples": _real_list(resid) if include_residual_samples else [],
                    "sample_count": int(resid.size),
                    "residual_inf": float(np.max(np.abs(resid))) if resid.size else 0.0,
                    "residual_l2": float(np.linalg.norm(resid)) if resid.size else 0.0,
                    "residual_coefficients": _complex_coeff_payload(rcoeffs),
                }
            except Exception as exc:
                payload["residual"] = {"available": False, "reason": "residual_replay_failed", "exception": repr(exc)}
        else:
            payload["residual"] = {"available": False, "reason": "missing_K_rho_or_lambda"}
    else:
        payload["source_validation"] = {"available": False, "reason": "source_validation_u_missing"}
        payload["residual"] = {"available": False, "reason": "source_validation_u_missing"}

    finite_operator = _finite_operator_payload(u=u, rho=rho, K=K, family=family, raw=raw) if include_operator_profiles else {"available": False, "reason": "operator_profiles_disabled"}
    payload["finite_linearization"] = finite_operator
    payload["preconditioner"] = _preconditioner_payload(raw, selected_row, finite_operator)
    payload["small_divisor_or_cohomology_constants"] = _small_divisor_payload(raw, selected_row)
    payload["tail_profile"] = {
        "available": bool(selected_row.get("modewise_tail_ledger") or selected_row.get("components")),
        "modewise_tail_ledger": dict(_as_mapping(selected_row.get("modewise_tail_ledger"))),
        "components": dict(_as_mapping(selected_row.get("components"))),
    }
    payload["stage1b_completeness_flags"] = {
        "has_source_samples": bool(u is not None),
        "has_fourier_coefficients": bool(u is not None and include_coefficients),
        "has_residual_coefficients_or_samples": bool(_as_mapping(payload.get("residual")).get("available")),
        "has_finite_linearized_operator_metadata": bool(_as_mapping(payload.get("finite_linearization")).get("available")),
        "has_preconditioner_metadata": bool(_as_mapping(payload.get("preconditioner")).get("available")),
        "has_scalar_ledger_recompute": bool(_as_mapping(payload.get("scalar_ledger_recompute")).get("available")),
        "has_tail_profile": bool(_as_mapping(payload.get("tail_profile")).get("available")),
        "has_small_divisor_or_cohomology_constants": bool(_as_mapping(payload.get("small_divisor_or_cohomology_constants")).get("available")),
    }
    return payload


def attach_raw_validation_payload_to_candidate(
    candidate: Mapping[str, Any],
    *,
    phase2n_attempt: Mapping[str, Any] | None,
    selected_row: Mapping[str, Any],
    input_summary: Mapping[str, Any] | Any,
    source_artifact: str | None,
    stage: str,
) -> dict[str, Any]:
    out = dict(candidate)
    selected_snapshot = dict(selected_row)
    out.setdefault("rows", [selected_snapshot])
    # Keep a second explicit row list with a stable name; Stage-1 audit and
    # humans can recompute scalar margins without navigating nested payloads.
    out["phase2aa_stage1b_selected_rows"] = [selected_snapshot]
    out["raw_validation_payload"] = build_raw_validation_payload(
        phase2n_attempt=phase2n_attempt,
        selected_row=selected_snapshot,
        input_summary=input_summary,
        source_artifact=source_artifact,
        stage=stage,
    )
    out["phase2aa_stage1b_export"] = {
        "enabled": True,
        "raw_validation_payload_version": RAW_PAYLOAD_VERSION,
        "diagnostic_only": True,
        "promotion_allowed": False,
        "does_not_change_theorem_facing_status": True,
    }
    return out


__all__ = [
    "RAW_PAYLOAD_VERSION",
    "attach_raw_validation_payload_to_candidate",
    "build_raw_validation_payload",
]
