from __future__ import annotations

"""Analytic-strip norm helpers for theorem-facing invariant-circle validation.

These utilities promote the older collocation diagnostics into explicit weighted
Fourier norms on a chosen strip width ``sigma``.  The goal is modest but
important: downstream certificates can now talk about concrete analytic norms
rather than only raw grid residuals and heuristic tail decay.
"""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass
class AnalyticStripProfile:
    sigma: float
    truncation: int
    max_resolved_mode: int
    coeff_l1: float
    coeff_l2: float
    coeff_sup: float
    weighted_l1: float
    weighted_l2: float
    weighted_sup: float
    mean_mode_abs: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def spectral_wavenumbers(N: int) -> np.ndarray:
    return np.fft.fftfreq(int(N), d=1.0 / int(N))



def spectral_coefficients_from_samples(samples: np.ndarray) -> np.ndarray:
    arr = np.asarray(samples, dtype=float)
    return np.fft.fft(arr) / len(arr)



def analytic_weights(N: int, sigma: float) -> np.ndarray:
    k = spectral_wavenumbers(int(N))
    return np.exp(2.0 * np.pi * float(sigma) * np.abs(k))



def weighted_fourier_norms_from_coeffs(coeffs: np.ndarray, sigma: float) -> tuple[float, float, float]:
    coeffs = np.asarray(coeffs, dtype=complex)
    weights = analytic_weights(len(coeffs), sigma)
    weighted = np.abs(coeffs) * weights
    return float(np.sum(weighted)), float(np.sqrt(np.sum(weighted**2))), float(np.max(weighted, initial=0.0))



def choose_safe_sigma(*, strip_width_proxy: float | None, sigma_cap: float = 0.04, fraction: float = 0.5, floor: float = 1e-4) -> float:
    if strip_width_proxy is None or not np.isfinite(strip_width_proxy) or strip_width_proxy <= 0.0:
        return float(min(max(floor, sigma_cap * 0.25), sigma_cap))
    return float(min(sigma_cap, max(floor, fraction * float(strip_width_proxy))))



def build_analytic_strip_profile_from_coeffs(coeffs: np.ndarray, sigma: float) -> AnalyticStripProfile:
    coeffs = np.asarray(coeffs, dtype=complex)
    N = len(coeffs)
    abs_coeffs = np.abs(coeffs)
    k = spectral_wavenumbers(N)
    weighted_l1, weighted_l2, weighted_sup = weighted_fourier_norms_from_coeffs(coeffs, sigma)
    mass = float(np.sum(abs_coeffs))
    mean_mode_abs = 0.0 if mass <= 0.0 else float(np.sum(np.abs(k) * abs_coeffs) / mass)
    return AnalyticStripProfile(
        sigma=float(sigma),
        truncation=int(N),
        max_resolved_mode=int(max(1, N // 2)),
        coeff_l1=float(np.sum(abs_coeffs)),
        coeff_l2=float(np.sqrt(np.sum(abs_coeffs**2))),
        coeff_sup=float(np.max(abs_coeffs, initial=0.0)),
        weighted_l1=float(weighted_l1),
        weighted_l2=float(weighted_l2),
        weighted_sup=float(weighted_sup),
        mean_mode_abs=float(mean_mode_abs),
    )



def build_analytic_strip_profile(samples: np.ndarray, sigma: float) -> AnalyticStripProfile:
    coeffs = spectral_coefficients_from_samples(np.asarray(samples, dtype=float))
    return build_analytic_strip_profile_from_coeffs(coeffs, sigma)



@dataclass
class TheoremNormProfile:
    sigma_used: float
    truncation: int
    analytic_norm: float
    derivative_norm: float
    norm_translation_certified: bool
    norm_profile_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_theorem_norm_profile_from_strip_profile(profile: AnalyticStripProfile) -> TheoremNormProfile:
    analytic_norm = float(profile.weighted_l1)
    derivative_norm = float(2.0 * np.pi * max(1.0, profile.mean_mode_abs) * profile.weighted_l1)
    certified = bool(np.isfinite(analytic_norm) and np.isfinite(derivative_norm) and analytic_norm >= 0.0 and derivative_norm >= 0.0)
    if certified and analytic_norm > 0.0:
        status = 'theorem-norm-profile-strong'
    elif certified:
        status = 'theorem-norm-profile-degenerate'
    else:
        status = 'theorem-norm-profile-failed'
    return TheoremNormProfile(
        sigma_used=float(profile.sigma),
        truncation=int(profile.truncation),
        analytic_norm=float(analytic_norm),
        derivative_norm=float(derivative_norm),
        norm_translation_certified=bool(certified),
        norm_profile_status=str(status),
    )


def build_theorem_norm_profile(samples: np.ndarray, sigma: float) -> TheoremNormProfile:
    return build_theorem_norm_profile_from_strip_profile(build_analytic_strip_profile(samples, sigma))
