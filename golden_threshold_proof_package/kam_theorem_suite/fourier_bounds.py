from __future__ import annotations

"""Fourier-tail bounds in analytic-strip norms."""

from dataclasses import asdict, dataclass
from typing import Any
import math

import numpy as np

from .analytic_norms import spectral_wavenumbers


@dataclass
class FourierTailBound:
    sigma_used: float
    strip_width_proxy: float | None
    truncation: int
    tail_start_mode: int
    analytic_gap: float | None
    envelope_constant: float | None
    geometric_ratio: float | None
    tail_l1: float | None
    tail_l2: float | None
    tail_sup: float | None
    theorem_usable: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def certify_fourier_tail_bound_from_coeffs(
    coeffs: np.ndarray,
    *,
    sigma_used: float,
    strip_width_proxy: float | None,
    tail_start_mode: int | None = None,
) -> FourierTailBound:
    coeffs = np.asarray(coeffs, dtype=complex)
    N = len(coeffs)
    if tail_start_mode is None:
        tail_start_mode = max(1, N // 2 + 1)
    if strip_width_proxy is None or not np.isfinite(strip_width_proxy) or strip_width_proxy <= sigma_used:
        return FourierTailBound(
            sigma_used=float(sigma_used),
            strip_width_proxy=(None if strip_width_proxy is None else float(strip_width_proxy)),
            truncation=int(N),
            tail_start_mode=int(tail_start_mode),
            analytic_gap=None,
            envelope_constant=None,
            geometric_ratio=None,
            tail_l1=None,
            tail_l2=None,
            tail_sup=None,
            theorem_usable=False,
        )
    safe = float(strip_width_proxy)
    delta = safe - float(sigma_used)
    if delta <= 0.0:
        return FourierTailBound(
            sigma_used=float(sigma_used),
            strip_width_proxy=float(strip_width_proxy),
            truncation=int(N),
            tail_start_mode=int(tail_start_mode),
            analytic_gap=None,
            envelope_constant=None,
            geometric_ratio=None,
            tail_l1=None,
            tail_l2=None,
            tail_sup=None,
            theorem_usable=False,
        )
    k = spectral_wavenumbers(N)
    abs_k = np.abs(k)
    mags = np.abs(coeffs)
    envelope_constant = float(np.max(mags * np.exp(2.0 * np.pi * safe * abs_k), initial=0.0))
    ratio = math.exp(-2.0 * math.pi * delta)
    start = int(max(1, tail_start_mode))
    if ratio >= 1.0:
        return FourierTailBound(
            sigma_used=float(sigma_used),
            strip_width_proxy=float(strip_width_proxy),
            truncation=int(N),
            tail_start_mode=int(start),
            analytic_gap=float(delta),
            envelope_constant=float(envelope_constant),
            geometric_ratio=None,
            tail_l1=None,
            tail_l2=None,
            tail_sup=None,
            theorem_usable=False,
        )
    exp_factor = math.exp(-2.0 * np.pi * delta * start)
    tail_sup = envelope_constant * exp_factor
    tail_l1 = 2.0 * tail_sup / (1.0 - ratio)
    tail_l2 = math.sqrt(2.0) * tail_sup / math.sqrt(1.0 - ratio * ratio)
    return FourierTailBound(
        sigma_used=float(sigma_used),
        strip_width_proxy=float(strip_width_proxy),
        truncation=int(N),
        tail_start_mode=int(start),
        analytic_gap=float(delta),
        envelope_constant=float(envelope_constant),
        geometric_ratio=float(ratio),
        tail_l1=float(tail_l1),
        tail_l2=float(tail_l2),
        tail_sup=float(tail_sup),
        theorem_usable=True,
    )



@dataclass
class FourierTailClosureCertificate:
    sigma_used: float
    truncation: int
    tail_sum_certified: bool
    tail_decay_model: str
    tail_closure_margin: float | None
    tail_ready_for_theorem: bool
    base_tail_bound: dict[str, Any]
    theorem_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_fourier_tail_closure_certificate(bound: FourierTailBound, *, threshold: float = 1.0e-4) -> FourierTailClosureCertificate:
    margin = None
    certified = False
    if bound.theorem_usable and bound.tail_l1 is not None:
        margin = float(threshold - float(bound.tail_l1))
        certified = bool(margin > 0.0)
    status = 'fourier-tail-closure-failed'
    if bound.theorem_usable and certified:
        status = 'fourier-tail-closure-strong'
    elif bound.theorem_usable:
        status = 'fourier-tail-closure-partial'
    return FourierTailClosureCertificate(
        sigma_used=float(bound.sigma_used),
        truncation=int(bound.truncation),
        tail_sum_certified=bool(certified),
        tail_decay_model='analytic-geometric' if bound.theorem_usable else 'unavailable',
        tail_closure_margin=None if margin is None else float(margin),
        tail_ready_for_theorem=bool(certified),
        base_tail_bound=bound.to_dict(),
        theorem_status=str(status),
    )
