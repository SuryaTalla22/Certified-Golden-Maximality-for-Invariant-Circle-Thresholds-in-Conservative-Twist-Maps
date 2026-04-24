from __future__ import annotations

"""Small-divisor audits for theorem-facing invariant-circle certificates."""

from dataclasses import asdict, dataclass
from typing import Any, Callable
import math

import numpy as np


@dataclass
class SmallDivisorEntry:
    k: int
    exact_gap: float
    lower_bound: float | None
    ratio_to_lower_bound: float | None
    certified_against_lower_bound: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SmallDivisorAudit:
    rho: float
    cutoff: int
    label: str
    min_exact_gap: float
    min_lower_bound: float | None
    cohomological_inverse_bound: float
    lower_bound_pass: bool
    entries: list[SmallDivisorEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho': float(self.rho),
            'cutoff': int(self.cutoff),
            'label': str(self.label),
            'min_exact_gap': float(self.min_exact_gap),
            'min_lower_bound': self.min_lower_bound,
            'cohomological_inverse_bound': float(self.cohomological_inverse_bound),
            'lower_bound_pass': bool(self.lower_bound_pass),
            'entries': [row.to_dict() for row in self.entries],
        }



def exact_small_divisor_gap(rho: float, k: int) -> float:
    kk = int(k)
    if kk == 0:
        return float('inf')
    return float(abs(np.exp(2j * np.pi * kk * float(rho)) - 1.0))



def golden_small_divisor_lower_bound(k: int) -> float:
    kk = abs(int(k))
    if kk == 0:
        return float('inf')
    return float(4.0 / (math.sqrt(5.0) * kk))



def build_small_divisor_audit(
    rho: float,
    cutoff: int,
    *,
    lower_bound: Callable[[int], float] | None = None,
    label: str = 'exact-audit',
) -> SmallDivisorAudit:
    entries: list[SmallDivisorEntry] = []
    min_exact = float('inf')
    min_lb = float('inf') if lower_bound is not None else None
    lower_pass = True
    for k in range(1, int(cutoff) + 1):
        exact = exact_small_divisor_gap(rho, k)
        lb = None if lower_bound is None else float(lower_bound(k))
        ratio = None if lb is None or lb <= 0.0 else float(exact / lb)
        certified = True if lb is None else bool(exact + 1e-14 >= lb)
        lower_pass = lower_pass and certified
        min_exact = min(min_exact, exact)
        if min_lb is not None and lb is not None:
            min_lb = min(min_lb, lb)
        entries.append(SmallDivisorEntry(
            k=int(k),
            exact_gap=float(exact),
            lower_bound=(None if lb is None else float(lb)),
            ratio_to_lower_bound=(None if ratio is None else float(ratio)),
            certified_against_lower_bound=bool(certified),
        ))
    if not np.isfinite(min_exact) or min_exact <= 0.0:
        inv = float('inf')
    else:
        inv = float(1.0 / min_exact)
    return SmallDivisorAudit(
        rho=float(rho),
        cutoff=int(cutoff),
        label=str(label),
        min_exact_gap=float(min_exact),
        min_lower_bound=(None if min_lb is None or not np.isfinite(min_lb) else float(min_lb)),
        cohomological_inverse_bound=float(inv),
        lower_bound_pass=bool(lower_pass),
        entries=entries,
    )



def build_golden_small_divisor_audit(cutoff: int, *, rho: float | None = None) -> SmallDivisorAudit:
    if rho is None:
        rho = (math.sqrt(5.0) - 1.0) / 2.0
    return build_small_divisor_audit(float(rho), int(cutoff), lower_bound=golden_small_divisor_lower_bound, label='golden-lower-bound-audit')



@dataclass
class SmallDivisorClosureCertificate:
    rho: float
    cutoff: int
    divisor_tail_law_certified: bool
    small_divisor_closure_margin: float | None
    small_divisor_ready_for_theorem: bool
    theorem_status: str
    base_audit: dict[str, Any]
    exact_inverse_bound: float | None = None
    weighted_inverse_bound: float | None = None
    weighted_correction_bound: float | None = None
    readiness_threshold: float | None = None
    strip_loss_sigma: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_small_divisor_closure_certificate(audit: SmallDivisorAudit, *, inverse_bound_threshold: float = 10.0, effective_defect: float | None = None, finite_margin: float | None = None, strip_loss_sigma: float | None = None, relative_margin_fraction: float = 0.8) -> SmallDivisorClosureCertificate:
    exact_inverse = None
    weighted_inverse = None
    weighted_correction = None
    readiness_threshold = None
    margin = None
    certified = False
    if np.isfinite(audit.cohomological_inverse_bound):
        exact_inverse = float(audit.cohomological_inverse_bound)
        weighted_inverse = float(exact_inverse)
        if strip_loss_sigma is not None and np.isfinite(strip_loss_sigma) and strip_loss_sigma > 0.0:
            weighted_inverse = float(exact_inverse * np.exp(-2.0 * np.pi * float(strip_loss_sigma) * max(1, int(audit.cutoff))))
        if effective_defect is not None and np.isfinite(effective_defect) and finite_margin is not None and np.isfinite(finite_margin) and finite_margin > 0.0:
            weighted_correction = float(max(0.0, float(effective_defect)) * weighted_inverse)
            readiness_threshold = float(max(0.0, float(relative_margin_fraction)) * float(finite_margin))
            margin = float(readiness_threshold - weighted_correction)
            certified = bool(audit.lower_bound_pass and margin > 0.0)
        else:
            margin = float(inverse_bound_threshold - exact_inverse)
            certified = bool(audit.lower_bound_pass and margin > 0.0)
    status = 'small-divisor-closure-failed'
    if certified:
        status = 'small-divisor-closure-strong'
    elif audit.lower_bound_pass:
        status = 'small-divisor-closure-partial'
    return SmallDivisorClosureCertificate(rho=float(audit.rho), cutoff=int(audit.cutoff), divisor_tail_law_certified=bool(certified), small_divisor_closure_margin=None if margin is None else float(margin), small_divisor_ready_for_theorem=bool(certified), theorem_status=str(status), base_audit=audit.to_dict(), exact_inverse_bound=exact_inverse, weighted_inverse_bound=weighted_inverse, weighted_correction_bound=weighted_correction, readiness_threshold=readiness_threshold, strip_loss_sigma=None if strip_loss_sigma is None or not np.isfinite(strip_loss_sigma) else float(strip_loss_sigma))
