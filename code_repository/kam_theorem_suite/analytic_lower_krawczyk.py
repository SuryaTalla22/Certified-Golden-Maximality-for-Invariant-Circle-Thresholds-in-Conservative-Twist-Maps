from __future__ import annotations

"""Phase-2E analytic lower Krawczyk/radii-polynomial ledger.

This module is the theorem-facing bridge that was missing from the Phase-2D
heavy lower-anchor driver.  Phase 2D could ask the existing invariant-circle
validator for a compact ``theorem_margin`` but it did not expose a decomposed
analytic ledger with the raw terms that Phase-2B consumes.  The routines here
turn an analytic invariant-circle certificate into explicit terms

    Y + Z r + T < r,

where ``Y`` is an inverse-applied analytic residual bound, ``Z`` is the
linear/nonlinear response majorant at radius ``r``, and ``T`` is the Fourier
tail/transverse closure burden.  The code is intentionally fail-closed: if the
source certificate does not contain enough samples to recompute the defect
modewise, the ledger records a conservative aggregate fallback and marks the
modewise field as unavailable instead of silently promoting the result.

The implementation is not a new mathematical theorem by itself; it is a
proof-payload generator.  A candidate becomes theorem-facing only when every
segment obtains a positive outward-rounded margin and passes the same strict
Phase-2B ingestion checks used elsewhere in the repository.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence
import math

import numpy as np

from .standard_map import HarmonicFamily
from .analytic_norms import (
    analytic_weights,
    spectral_coefficients_from_samples,
    spectral_wavenumbers,
)
from .invariance_defect import residual_samples


_GOLDEN_RHO = (math.sqrt(5.0) - 1.0) / 2.0


@dataclass(frozen=True)
class ModewiseDivisorRow:
    k: int
    exact_gap: float
    inverse_multiplier: float
    analytic_weight: float
    weighted_inverse_multiplier: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModewiseDivisorLedger:
    rho: float
    sigma: float
    cutoff: int
    min_gap: float
    max_inverse_multiplier: float
    max_weighted_inverse_multiplier: float
    worst_k: int
    zero_mode_policy: str
    rows: tuple[ModewiseDivisorRow, ...]

    @property
    def certified(self) -> bool:
        return bool(self.cutoff > 0 and math.isfinite(self.min_gap) and self.min_gap > 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "sigma": float(self.sigma),
            "cutoff": int(self.cutoff),
            "min_gap": float(self.min_gap),
            "max_inverse_multiplier": float(self.max_inverse_multiplier),
            "max_weighted_inverse_multiplier": float(self.max_weighted_inverse_multiplier),
            "worst_k": int(self.worst_k),
            "zero_mode_policy": str(self.zero_mode_policy),
            "certified": bool(self.certified),
            "rows": [row.to_dict() for row in self.rows],
        }


@dataclass(frozen=True)
class AnalyticLowerRadiiLedger:
    rho: float
    K: float
    N: int
    sigma: float
    norm_name: str
    residual_Y: float
    linear_defect_Z: float
    tail_bound_T: float
    radius_r: float
    radii_lhs: float
    radii_margin: float
    finite_radii_margin: float | None
    source_theorem_margin: float | None
    modewise_residual_available: bool
    modewise_inverse_applied_residual: float | None
    aggregate_inverse_applied_residual: float | None
    nonlinear_response_bound: float
    tail_response_bound: float
    outward_rounding_tolerance: float
    divisor_ledger: ModewiseDivisorLedger
    closure_level: str
    theorem_ready: bool
    failure_reasons: tuple[str, ...]

    def to_candidate_terms(self) -> dict[str, Any]:
        return {
            "N": int(self.N),
            "sigma": float(self.sigma),
            "norm_name": str(self.norm_name),
            "residual_Y": float(self.residual_Y),
            "linear_defect_Z": float(self.linear_defect_Z),
            "tail_bound_T": float(self.tail_bound_T),
            "radius_r": float(self.radius_r),
            "radii_margin": float(self.radii_margin),
            "small_divisor_min": float(self.divisor_ledger.min_gap),
            "small_divisor_inverse_bound": float(self.divisor_ledger.max_inverse_multiplier),
            "small_divisor_source": "phase2e-modewise-divisor-ledger",
            "closure_level": str(self.closure_level),
            "theorem_ready": bool(self.theorem_ready),
            "finite_dimensional_only": bool(not self.theorem_ready),
            "failure_reasons": list(self.failure_reasons),
        }

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["failure_reasons"] = list(self.failure_reasons)
        d["divisor_ledger"] = self.divisor_ledger.to_dict()
        return d


def _as_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, Mapping):
        return dict(obj)
    if hasattr(obj, "to_dict"):
        return dict(obj.to_dict())
    return dict(getattr(obj, "__dict__", {}) or {})


def _nested_float(data: Mapping[str, Any], *keys: str) -> float | None:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, Mapping) or key not in cur:
            return None
        cur = cur[key]
    try:
        out = float(cur)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def _float(data: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in data:
            try:
                out = float(data[key])
            except Exception:
                continue
            if math.isfinite(out):
                return out
    return None


def exact_small_divisor_gap(rho: float, k: int) -> float:
    kk = abs(int(k))
    if kk == 0:
        return float("inf")
    return float(abs(np.exp(2j * np.pi * kk * float(rho)) - 1.0))


def build_modewise_divisor_ledger(
    cutoff: int,
    *,
    rho: float = _GOLDEN_RHO,
    sigma: float = 0.0,
    sample_limit: int = 16,
) -> ModewiseDivisorLedger:
    cutoff = int(max(0, cutoff))
    rows: list[ModewiseDivisorRow] = []
    min_gap = float("inf")
    max_inv = 0.0
    max_weighted_inv = 0.0
    worst_k = 0
    for k in range(1, cutoff + 1):
        gap = exact_small_divisor_gap(rho, k)
        inv = float("inf") if gap <= 0.0 else float(1.0 / gap)
        weight = float(math.exp(2.0 * math.pi * float(sigma) * abs(k)))
        weighted_inv = float(inv * weight)
        if gap < min_gap:
            min_gap = gap
            worst_k = k
        max_inv = max(max_inv, inv)
        max_weighted_inv = max(max_weighted_inv, weighted_inv)
        if len(rows) < sample_limit or k == cutoff:
            rows.append(ModewiseDivisorRow(int(k), float(gap), float(inv), float(weight), float(weighted_inv)))
    if cutoff == 0:
        min_gap = float("inf")
    return ModewiseDivisorLedger(
        rho=float(rho),
        sigma=float(sigma),
        cutoff=int(cutoff),
        min_gap=float(min_gap),
        max_inverse_multiplier=float(max_inv),
        max_weighted_inverse_multiplier=float(max_weighted_inv),
        worst_k=int(worst_k),
        zero_mode_policy="zero Fourier mode is controlled by the mean/lambda equation and is not divided by a small divisor",
        rows=tuple(rows),
    )


def _source_validation(data: Mapping[str, Any]) -> Mapping[str, Any]:
    val = data.get("source_validation")
    return val if isinstance(val, Mapping) else {}


def _extract_u_lambda(data: Mapping[str, Any]) -> tuple[np.ndarray | None, float | None]:
    src = _source_validation(data)
    u = src.get("u")
    lam = src.get("lambda_value")
    if u is None:
        # Some future records may store the samples at top level.
        u = data.get("u")
    if lam is None:
        lam = data.get("lambda_value")
    try:
        arr = np.asarray(u, dtype=float)
    except Exception:
        arr = None
    if arr is not None and arr.size == 0:
        arr = None
    try:
        lam_f = float(lam)
    except Exception:
        lam_f = None
    if lam_f is not None and not math.isfinite(lam_f):
        lam_f = None
    return arr, lam_f


def _modewise_inverse_applied_residual(
    *,
    u: np.ndarray,
    rho: float,
    K: float,
    family: HarmonicFamily,
    lambda_value: float,
    sigma: float,
    oversample_factor: int,
) -> tuple[float, float, int]:
    """Return inverse-applied residual and weighted residual l1.

    The residual is evaluated on an oversampled grid and transformed to Fourier
    coefficients.  For nonzero modes we divide by the exact cohomological
    multiplier.  For the zero mode we keep the weighted zero coefficient itself;
    the augmented graph equation controls the mean/lambda component separately.
    """

    resid = residual_samples(
        u,
        float(rho),
        float(K),
        family,
        lambda_value=float(lambda_value),
        oversample_factor=max(4, int(oversample_factor)),
    )
    coeffs = spectral_coefficients_from_samples(resid)
    k = spectral_wavenumbers(len(coeffs)).astype(int)
    weights = analytic_weights(len(coeffs), float(sigma))
    inverse_applied = 0.0
    weighted_l1 = 0.0
    for idx, kk in enumerate(k):
        mag = float(abs(coeffs[idx]))
        w = float(weights[idx])
        weighted_l1 += mag * w
        if int(kk) == 0:
            inv = 1.0
        else:
            gap = exact_small_divisor_gap(rho, int(kk))
            inv = float("inf") if gap <= 0.0 else 1.0 / gap
        inverse_applied += mag * w * inv
    return float(inverse_applied), float(weighted_l1), int(len(coeffs))


def build_analytic_lower_radii_ledger(
    certificate: Any,
    *,
    family: HarmonicFamily | None = None,
    oversample_factor: int = 8,
    outward_rounding_tolerance: float = 1.0e-12,
    safety_factor: float = 10.0,
    nonlinear_fraction_of_finite_margin: float = 0.25,
) -> AnalyticLowerRadiiLedger:
    """Build a decomposed Phase-2E lower analytic ledger from a certificate.

    The ledger uses actual residual coefficients when the source certificate
    exposes the collocation samples.  If samples are unavailable it falls back to
    the aggregate weighted residual and records the fallback as non-modewise.
    """

    family = family or HarmonicFamily()
    data = _as_dict(certificate)
    rho = _float(data, "rho")
    K = _float(data, "K")
    N = int(_float(data, "N") or 0)
    sigma = _float(data, "sigma_used", "sigma") or _nested_float(data, "defect_report", "sigma") or 0.0
    radius = _float(data, "finite_radius", "radius")
    finite_margin = _float(data, "finite_radii_margin")
    source_margin = _float(data, "theorem_margin", "analytic_theorem_margin")
    finite_B_norm = _float(data, "finite_B_norm")
    finite_L = _float(data, "finite_lipschitz_bound")
    finite_contraction = _float(data, "finite_contraction_bound")
    weighted_defect = _nested_float(data, "defect_report", "weighted_l1")
    tail_l1 = _nested_float(data, "tail_bound", "tail_l1")
    inv_bound = _float(data, "cohomological_inverse_bound")

    if rho is None:
        rho = _GOLDEN_RHO
    if K is None:
        K = 0.0
    if radius is None or radius <= 0.0:
        radius = 0.0
    if inv_bound is None:
        inv_bound = float("inf")

    divisor = build_modewise_divisor_ledger(max(1, N // 2), rho=float(rho), sigma=float(sigma))

    u, lam = _extract_u_lambda(data)
    modewise_available = bool(u is not None and lam is not None and N > 0)
    modewise_Y: float | None = None
    weighted_residual_l1: float | None = weighted_defect
    if modewise_available:
        try:
            modewise_Y, weighted_residual_l1, _ = _modewise_inverse_applied_residual(
                u=u,
                rho=float(rho),
                K=float(K),
                family=family,
                lambda_value=float(lam),
                sigma=float(sigma),
                oversample_factor=int(oversample_factor),
            )
        except Exception:
            modewise_available = False
            modewise_Y = None

    aggregate_Y = None
    if weighted_defect is not None and math.isfinite(inv_bound):
        aggregate_Y = float(weighted_defect) * float(inv_bound)
    if modewise_Y is not None and math.isfinite(modewise_Y):
        residual_Y = float(modewise_Y)
    elif aggregate_Y is not None:
        residual_Y = float(aggregate_Y)
    else:
        residual_Y = float("inf")

    # Encode the finite nonlinear/contraction contribution as Z*r.  The existing
    # finite-dimensional validator uses eta + 0.5*B*L*r^2 < r.  If a contraction
    # bound is available, it is the most direct dimensionless response term;
    # otherwise use 0.5*B*L*r.
    Z_candidates: list[float] = []
    if finite_contraction is not None:
        Z_candidates.append(float(finite_contraction))
    if finite_B_norm is not None and finite_L is not None and radius > 0.0:
        Z_candidates.append(float(0.5 * finite_B_norm * finite_L * radius))
    linear_Z = min((z for z in Z_candidates if math.isfinite(z) and z >= 0.0), default=float("inf"))

    tail_response = 0.0
    if tail_l1 is not None and math.isfinite(inv_bound):
        tail_response = float(tail_l1) * float(inv_bound)
    nonlinear_response = 0.0
    if finite_margin is not None and math.isfinite(finite_margin) and finite_margin > 0.0:
        nonlinear_response = max(0.0, float(nonlinear_fraction_of_finite_margin) * float(finite_margin))
    tail_T = float(tail_response + nonlinear_response)

    lhs = float(residual_Y + linear_Z * radius + tail_T)
    raw_margin = float(radius - lhs)
    rounded_margin = float(raw_margin - abs(float(outward_rounding_tolerance)))
    required = float(abs(outward_rounding_tolerance)) * float(max(1.0, safety_factor))

    failures: list[str] = []
    if not (math.isfinite(radius) and radius > 0.0):
        failures.append("radius_missing_or_nonpositive")
    if not math.isfinite(residual_Y):
        failures.append("residual_Y_not_finite")
    if not math.isfinite(linear_Z):
        failures.append("linear_defect_Z_not_finite")
    if not math.isfinite(tail_T):
        failures.append("tail_bound_T_not_finite")
    if not divisor.certified:
        failures.append("modewise_divisor_ledger_not_certified")
    if not modewise_available:
        failures.append("modewise_residual_coefficients_unavailable")
    if rounded_margin <= required:
        failures.append("analytic_radii_margin_not_safely_positive")
    if finite_margin is not None and finite_margin <= 0.0:
        failures.append("source_finite_radii_margin_nonpositive")
    theorem_ready = bool(not failures)

    return AnalyticLowerRadiiLedger(
        rho=float(rho),
        K=float(K),
        N=int(N),
        sigma=float(sigma),
        norm_name="phase2e-modewise-weighted-fourier-radii-polynomial" if modewise_available else "phase2e-aggregate-weighted-fourier-radii-polynomial-fallback",
        residual_Y=float(residual_Y),
        linear_defect_Z=float(linear_Z),
        tail_bound_T=float(tail_T),
        radius_r=float(radius),
        radii_lhs=float(lhs),
        radii_margin=float(rounded_margin),
        finite_radii_margin=None if finite_margin is None else float(finite_margin),
        source_theorem_margin=None if source_margin is None else float(source_margin),
        modewise_residual_available=bool(modewise_available),
        modewise_inverse_applied_residual=None if modewise_Y is None else float(modewise_Y),
        aggregate_inverse_applied_residual=None if aggregate_Y is None else float(aggregate_Y),
        nonlinear_response_bound=float(nonlinear_response),
        tail_response_bound=float(tail_response),
        outward_rounding_tolerance=float(outward_rounding_tolerance),
        divisor_ledger=divisor,
        closure_level="analytic_theorem_closure" if theorem_ready else "phase2e_analytic_radii_attempt_not_closed",
        theorem_ready=bool(theorem_ready),
        failure_reasons=tuple(failures),
    )


def choose_best_phase2e_ledger(
    ledgers: Sequence[AnalyticLowerRadiiLedger],
) -> AnalyticLowerRadiiLedger:
    if not ledgers:
        raise ValueError("at least one ledger is required")
    def score(x: AnalyticLowerRadiiLedger) -> tuple[float, float, float, int]:
        return (
            1.0 if x.theorem_ready else 0.0,
            float(x.radii_margin) if math.isfinite(x.radii_margin) else -float("inf"),
            float(x.source_theorem_margin) if x.source_theorem_margin is not None and math.isfinite(x.source_theorem_margin) else -float("inf"),
            int(x.N),
        )
    return max(ledgers, key=score)


__all__ = [
    "AnalyticLowerRadiiLedger",
    "ModewiseDivisorLedger",
    "ModewiseDivisorRow",
    "build_analytic_lower_radii_ledger",
    "build_modewise_divisor_ledger",
    "choose_best_phase2e_ledger",
    "exact_small_divisor_gap",
]
