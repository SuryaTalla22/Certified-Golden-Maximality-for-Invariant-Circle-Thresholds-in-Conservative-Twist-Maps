from __future__ import annotations

"""Arithmetic helpers for periodic continued-fraction classes.

The original project only shipped a heuristic ``eta`` approximation based on a
long truncation. This module keeps the practical spirit but makes the objects
more explicit:

- rotation numbers for purely periodic and eventually periodic classes are built
  from exact integer Möbius data;
- quadratic periodic values can be evaluated to arbitrary precision without
  repeated truncation;
- ``eta`` estimates are produced phase-by-phase so downstream comparison code
  can inspect the cycle structure instead of seeing only one scalar.

The ``eta`` routines here are still numerical/validated rather than symbolic
Lagrange-spectrum proofs. The API returns interval-like metadata so callers can
keep theorem-grade and exploratory uses separate.
"""

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from typing import Iterable, Sequence

import mpmath as mp
import numpy as np


@dataclass(frozen=True)
class QuadraticSurd:
    """Represent ``(u + sqrt(d)) / v`` with integer data."""

    u: int
    d: int
    v: int

    def eval(self, dps: int = 80) -> mp.mpf:
        mp.mp.dps = dps
        return (mp.mpf(self.u) + mp.sqrt(mp.mpf(self.d))) / mp.mpf(self.v)

    def __float__(self) -> float:
        return float(self.eval(80))


def mobius_matrix_for_word(word: Sequence[int]) -> tuple[int, int, int, int]:
    A, B, C, D = 1, 0, 0, 1
    for a in word:
        A, B, C, D = A * a + B, A, C * a + D, C
    return A, B, C, D


def pure_periodic_quadratic(period: Sequence[int]) -> QuadraticSurd:
    if not period:
        raise ValueError("period must be non-empty")
    A, B, C, D = mobius_matrix_for_word(period)
    # Fixed-point equation for x = (A x + B)/(C x + D):
    # C x^2 + (D - A) x - B = 0.
    disc = (A - D) ** 2 + 4 * B * C
    if C == 0:
        raise ValueError("degenerate Möbius data for periodic class")
    return QuadraticSurd(u=A - D, d=disc, v=2 * C)


def apply_mobius_to_value(word: Sequence[int], x: mp.mpf) -> mp.mpf:
    A, B, C, D = mobius_matrix_for_word(word)
    return (mp.mpf(A) * x + mp.mpf(B)) / (mp.mpf(C) * x + mp.mpf(D))


def periodic_cf_value(period: Sequence[int], preperiod: Sequence[int] | None = None, dps: int = 100) -> mp.mpf:
    pre = tuple(preperiod or ())
    beta = pure_periodic_quadratic(period).eval(dps=dps)
    if pre:
        return apply_mobius_to_value(pre, beta)
    return beta


def rotated_period(period: Sequence[int], shift: int) -> tuple[int, ...]:
    period = tuple(period)
    if not period:
        raise ValueError("period must be non-empty")
    shift %= len(period)
    return period[shift:] + period[:shift]


def cycle_eta_estimates(
    period: Sequence[int],
    *,
    burn_in_cycles: int = 8,
    dps: int = 120,
) -> dict:
    """Return phase-by-phase estimates for ``eta`` on a periodic class.

    For a periodic class the sequence ``q_n |q_n rho - p_n|`` settles into an
    ``m``-periodic limit cycle. We compute that cycle numerically at high
    precision after a burn-in, then expose the phase values. This is much more
    informative than a single minimum over a long truncation and is robust
    enough for challenger ordering and diagnostics.
    """
    mp.mp.dps = dps
    rho = periodic_cf_value(period, dps=dps)
    period = tuple(period)
    m = len(period)
    n_terms = burn_in_cycles * m + 4 * m
    seq = list(period) * (n_terms // m + 2)
    seq = seq[:n_terms]

    # Build convergents incrementally in high precision.
    p_nm2, p_nm1 = mp.mpf(0), mp.mpf(1)
    q_nm2, q_nm1 = mp.mpf(1), mp.mpf(0)
    cycle_vals: list[list[mp.mpf]] = [[] for _ in range(m)]
    for idx, a in enumerate(seq):
        p_n = mp.mpf(a) * p_nm1 + p_nm2
        q_n = mp.mpf(a) * q_nm1 + q_nm2
        if idx >= burn_in_cycles * m:
            val = q_n * abs(q_n * rho - p_n)
            cycle_vals[idx % m].append(val)
        p_nm2, p_nm1 = p_nm1, p_n
        q_nm2, q_nm1 = q_nm1, q_n

    phase_stats = []
    flat_vals = []
    for phase, vals in enumerate(cycle_vals):
        if not vals:
            continue
        lo = min(vals)
        hi = max(vals)
        ctr = vals[-1]
        phase_stats.append(
            {
                "phase": phase,
                "eta_lo": float(lo),
                "eta_hi": float(hi),
                "eta_center": float(ctr),
                "samples": len(vals),
            }
        )
        flat_vals.extend(vals)

    if not flat_vals:
        raise RuntimeError("cycle eta estimation produced no samples")

    eta_lo = float(min(flat_vals))
    eta_hi = float(max(flat_vals))
    return {
        "period": tuple(period),
        "rho": float(rho),
        "eta_lo": eta_lo,
        "eta_hi": eta_hi,
        "eta_center": float(np.mean([float(v) for v in flat_vals])),
        "phase_stats": phase_stats,
        "burn_in_cycles": burn_in_cycles,
        "dps": dps,
    }


def known_constant_type_eta(digit: int) -> float:
    """Return the classical ``eta`` value for the constant-type class ``[(digit)]``.

    For the purely periodic class with repeated digit ``a``, one has

        eta = 1 / sqrt(a^2 + 4).
    """
    return 1.0 / float(mp.sqrt(digit * digit + 4))


def continued_fraction(x: float, n_terms: int = 32) -> list[int]:
    out: list[int] = []
    y = float(x)
    for _ in range(n_terms):
        a = int(np.floor(y))
        out.append(a)
        frac = y - a
        if abs(frac) < 1e-30:
            break
        y = 1.0 / frac
    return out


def convergents_from_cf(cf: Sequence[int]) -> list[Fraction]:
    p_nm2, p_nm1 = 0, 1
    q_nm2, q_nm1 = 1, 0
    out: list[Fraction] = []
    for a in cf:
        p_n = a * p_nm1 + p_nm2
        q_n = a * q_nm1 + q_nm2
        out.append(Fraction(p_n, q_n))
        p_nm2, p_nm1 = p_nm1, p_n
        q_nm2, q_nm1 = q_nm1, q_n
    return out



def periodic_class_eta_interval(
    period: Sequence[int],
    preperiod: Sequence[int] | None = None,
    *,
    burn_in_cycles: int = 12,
    dps: int = 160,
) -> dict:
    """Return a theorem-facing eta interval summary for an eventually periodic class.

    The goal is not to claim a symbolic Lagrange-spectrum proof. Instead, this
    packages the strongest arithmetic information currently available in the
    bridge code in a structured way:

    - for purely periodic classes we use the phase-aware cycle enclosure;
    - for eventually periodic classes we return a stabilized numerical interval
      from long high-precision convergent tails.

    The returned dictionary is intentionally verbose so pruning logic can keep
    exploratory and theorem-facing uses separate.
    """
    pre = tuple(preperiod or ())
    period = tuple(period)
    if not period:
        raise ValueError("period must be non-empty")
    if not pre:
        stats = cycle_eta_estimates(period, burn_in_cycles=burn_in_cycles, dps=dps)
        return {
            "label": f"[({','.join(map(str, period))})]",
            "preperiod": pre,
            "period": period,
            "rho": float(stats["rho"]),
            "eta_lo": float(stats["eta_lo"]),
            "eta_hi": float(stats["eta_hi"]),
            "eta_center": float(stats["eta_center"]),
            "method": "periodic-cycle",
            "phase_stats": list(stats["phase_stats"]),
            "dps": int(dps),
            "burn_in_cycles": int(burn_in_cycles),
        }

    mp.mp.dps = dps
    rho = periodic_cf_value(period=period, preperiod=pre, dps=dps)
    seq_total = list(pre) + list(period) * max(1, burn_in_cycles + 20)
    # Continue long enough that several full period cycles appear after burn-in.
    seq_total = seq_total[: max(len(pre) + len(period) * (burn_in_cycles + 8), len(pre) + len(period) * 4)]
    convs = convergents_from_cf(seq_total)
    vals = []
    start = max(len(pre), len(convs) // 3)
    for frac in convs[start:]:
        q = frac.denominator
        p = frac.numerator
        vals.append(mp.mpf(q) * abs(mp.mpf(q) * rho - mp.mpf(p)))
    if not vals:
        raise RuntimeError("eventually periodic eta interval computation produced no tail values")
    vals_f = [float(v) for v in vals]
    return {
        "label": f"[{','.join(map(str, pre))};({','.join(map(str, period))})]",
        "preperiod": pre,
        "period": period,
        "rho": float(rho),
        "eta_lo": float(min(vals_f)),
        "eta_hi": float(max(vals_f)),
        "eta_center": float(np.mean(vals_f)),
        "method": "eventual-tail",
        "phase_stats": [],
        "dps": int(dps),
        "burn_in_cycles": int(burn_in_cycles),
    }


def periodic_word_rank_key(period: Sequence[int], preperiod: Sequence[int] | None = None) -> tuple:
    """Deterministic ranking key for continued-fraction classes.

    This is useful when two challengers have nearly identical arithmetic data and
    we need a stable order for tables, notebooks, or pruning summaries.
    """
    pre = tuple(preperiod or ())
    per = tuple(period)
    return (len(pre), len(per), pre, per)


def build_periodic_class_table(
    classes: Iterable[tuple[Sequence[int], Sequence[int]]],
    *,
    dps: int = 160,
    burn_in_cycles: int = 12,
) -> list[dict]:
    """Return a sorted arithmetic table for theorem-facing challenger scans."""
    rows = []
    for pre, period in classes:
        row = periodic_class_eta_interval(period=period, preperiod=pre, dps=dps, burn_in_cycles=burn_in_cycles)
        rows.append(row)
    rows.sort(key=lambda r: (-float(r["eta_lo"]), periodic_word_rank_key(r["period"], r["preperiod"])))
    return rows
