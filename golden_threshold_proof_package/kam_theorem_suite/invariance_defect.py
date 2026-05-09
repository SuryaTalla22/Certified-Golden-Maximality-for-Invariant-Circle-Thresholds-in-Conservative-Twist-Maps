from __future__ import annotations

"""Analytic-strip invariance-defect reports for approximate invariant circles."""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .analytic_norms import spectral_coefficients_from_samples, spectral_wavenumbers, weighted_fourier_norms_from_coeffs
from .standard_map import HarmonicFamily


@dataclass
class InvarianceDefectReport:
    rho: float
    K: float
    sigma: float
    oversample_factor: int
    lambda_value: float
    weighted_l1: float
    weighted_l2: float
    weighted_sup: float
    residual_inf: float
    residual_l2: float
    truncation: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)




def evaluate_trig_interpolant_from_coeffs(coeffs: np.ndarray, theta: np.ndarray) -> np.ndarray:
    coeffs = np.asarray(coeffs, dtype=complex)
    N = len(coeffs)
    k = spectral_wavenumbers(N)
    theta = np.asarray(theta, dtype=float)
    expo = np.exp(2j * np.pi * np.outer(theta, k))
    vals = expo @ coeffs
    return np.real_if_close(vals, tol=1000).astype(float)

def residual_samples(
    u: np.ndarray,
    rho: float,
    K: float,
    family: HarmonicFamily,
    *,
    lambda_value: float,
    oversample_factor: int = 8,
) -> np.ndarray:
    u = np.asarray(u, dtype=float)
    coeffs = spectral_coefficients_from_samples(u)
    M = max(int(oversample_factor) * len(u), len(u))
    theta = np.arange(M, dtype=float) / float(M)
    u_theta = evaluate_trig_interpolant_from_coeffs(coeffs, theta)
    u_plus = evaluate_trig_interpolant_from_coeffs(coeffs, (theta + float(rho)) % 1.0)
    u_minus = evaluate_trig_interpolant_from_coeffs(coeffs, (theta - float(rho)) % 1.0)
    resid = u_plus + u_minus - 2.0 * u_theta - float(K) * family.force(theta + u_theta) - float(lambda_value)
    return np.asarray(resid, dtype=float)



def build_invariance_defect_report(
    u: np.ndarray,
    rho: float,
    K: float,
    family: HarmonicFamily,
    *,
    lambda_value: float,
    sigma: float,
    oversample_factor: int = 8,
) -> InvarianceDefectReport:
    resid = residual_samples(u, rho, K, family, lambda_value=lambda_value, oversample_factor=oversample_factor)
    coeffs = spectral_coefficients_from_samples(resid)
    weighted_l1, weighted_l2, weighted_sup = weighted_fourier_norms_from_coeffs(coeffs, sigma)
    return InvarianceDefectReport(
        rho=float(rho),
        K=float(K),
        sigma=float(sigma),
        oversample_factor=int(oversample_factor),
        lambda_value=float(lambda_value),
        weighted_l1=float(weighted_l1),
        weighted_l2=float(weighted_l2),
        weighted_sup=float(weighted_sup),
        residual_inf=float(np.linalg.norm(resid, ord=np.inf)),
        residual_l2=float(np.linalg.norm(resid)),
        truncation=int(len(u)),
    )



@dataclass
class InvarianceDefectClosureCertificate:
    rho: float
    K: float
    sigma: float
    resolved_defect: float
    tail_defect_bound: float
    combined_theorem_defect: float
    defect_ready_for_closure: bool
    theorem_status: str
    base_report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_invariance_defect_closure_certificate(report: InvarianceDefectReport, *, defect_threshold: float = 1.0e-5, tail_fraction: float = 0.25) -> InvarianceDefectClosureCertificate:
    resolved = float(report.weighted_l1)
    tail_bound = float(max(0.0, tail_fraction * report.weighted_sup))
    combined = float(resolved + tail_bound)
    certified = bool(np.isfinite(combined) and combined <= float(defect_threshold))
    if certified:
        status = 'invariance-defect-closure-strong'
    elif np.isfinite(combined):
        status = 'invariance-defect-closure-partial'
    else:
        status = 'invariance-defect-closure-failed'
    return InvarianceDefectClosureCertificate(
        rho=float(report.rho),
        K=float(report.K),
        sigma=float(report.sigma),
        resolved_defect=float(resolved),
        tail_defect_bound=float(tail_bound),
        combined_theorem_defect=float(combined),
        defect_ready_for_closure=bool(certified),
        theorem_status=str(status),
        base_report=report.to_dict(),
    )
