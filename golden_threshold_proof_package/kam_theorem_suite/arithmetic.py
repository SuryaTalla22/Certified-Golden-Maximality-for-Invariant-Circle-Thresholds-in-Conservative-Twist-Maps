from __future__ import annotations

"""Arithmetic helpers for challenger generation and ordering.

This module preserves the public surface of the original bridge suite while
adding access to more structured periodic-class arithmetic. The recommended
workflow is now:

- use :mod:`kam_theorem_suite.arithmetic_exact` when theorem-facing code needs
  explicit quadratic/phase information;
- use the helpers below for panel generation, plotting, and exploratory scans.
"""

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import floor
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from .arithmetic_exact import (
    continued_fraction,
    convergents_from_cf,
    cycle_eta_estimates,
    known_constant_type_eta,
    periodic_cf_value,
)


def periodic_cf_to_float(period: Sequence[int], preperiod: Sequence[int] | None = None, depth: int = 200) -> float:
    # ``depth`` is retained for backward compatibility, but the improved
    # implementation no longer truncates blindly.
    return float(periodic_cf_value(period=period, preperiod=preperiod, dps=max(80, depth)))


def approximate_eta_from_periodic_cf(period: Sequence[int], preperiod: Sequence[int] | None = None, depth: int = 120) -> float:
    """Return a stable ``eta`` approximation for an eventually periodic class.

    For purely periodic classes, this delegates to phase-aware cycle estimates.
    For classes with a preperiod it falls back to a long convergent computation,
    since the asymptotic cycle is still periodic but phase alignment is slightly
    more delicate.
    """
    pre = tuple(preperiod or ())
    period = tuple(period)
    if not pre:
        stats = cycle_eta_estimates(period, burn_in_cycles=max(8, depth // max(1, len(period))), dps=max(120, depth))
        return float(stats["eta_lo"])

    import mpmath as mp

    mp.mp.dps = max(120, depth)
    seq_total = list(pre) + list(period) * max(1, (depth + 800) // max(1, len(period)) + 2)
    seq_total = seq_total[: depth + 800]

    val = mp.mpf("0")
    for a in reversed(seq_total[1:]):
        val = mp.mpf("1") / (mp.mpf(a) + val)
    rho = mp.mpf(seq_total[0]) + val

    convs = convergents_from_cf(seq_total[:depth])
    vals = []
    start = max(10, len(convs) // 3)
    for frac in convs[start:]:
        q = frac.denominator
        p = frac.numerator
        vals.append(mp.mpf(q) * abs(mp.mpf(q) * rho - mp.mpf(p)))
    if not vals:
        return float("nan")
    tail = vals[len(vals) // 2 :]
    return float(min(tail))


def class_label(period: Sequence[int], preperiod: Sequence[int] | None = None) -> str:
    pre = ",".join(map(str, preperiod or []))
    per = ",".join(map(str, period))
    if pre:
        return f"[{pre};({per})]"
    return f"[({per})]"


def generate_periodic_classes(
    max_digit: int = 5,
    max_period: int = 4,
    include_golden: bool = True,
    primitive_only: bool = True,
) -> List[Tuple[Tuple[int, ...], Tuple[int, ...]]]:
    out: List[Tuple[Tuple[int, ...], Tuple[int, ...]]] = []
    seen = set()
    if include_golden:
        golden = (tuple(), (1,))
        out.append(golden)
        seen.add(golden)
    for L in range(1, max_period + 1):
        for period in product(range(1, max_digit + 1), repeat=L):
            if primitive_only:
                ok = True
                for s in range(1, L):
                    if L % s == 0 and period == period[:s] * (L // s):
                        ok = False
                        break
                if not ok:
                    continue
            item = (tuple(), tuple(period))
            if item in seen:
                continue
            out.append(item)
            seen.add(item)
    return out


def convergent_ladder_for_rotation(rotation: float, max_q: int = 144) -> List[Fraction]:
    cf = continued_fraction(rotation, n_terms=64)
    convs = convergents_from_cf(cf)
    return [f for f in convs if f.denominator <= max_q]


def eta_panel_dataframe(classes: Sequence[Tuple[Tuple[int, ...], Tuple[int, ...]]]):
    import pandas as pd

    rows = []
    for pre, period in classes:
        rho = periodic_cf_to_float(period=period, preperiod=pre)
        eta = approximate_eta_from_periodic_cf(period=period, preperiod=pre, depth=120)
        row = {
            "label": class_label(period=period, preperiod=pre),
            "preperiod": list(pre),
            "period": list(period),
            "rho": rho,
            "eta_approx": eta,
        }
        if not pre and len(period) == 1:
            row["eta_constant_type_exact"] = known_constant_type_eta(period[0])
        rows.append(row)
    df = pd.DataFrame(rows)
    return df.sort_values(["eta_approx", "label"], ascending=[False, True]).reset_index(drop=True)
