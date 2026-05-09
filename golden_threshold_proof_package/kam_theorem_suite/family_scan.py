
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from .standard_map import HarmonicFamily
from .certification import bisection_crossing_bracket


def family_from_direction(direction: Sequence[float], radius: float) -> HarmonicFamily:
    """Create a nearby family by perturbing the first few harmonics.

    direction is interpreted on basis:
        mode 1 amplitude correction,
        mode 2 amplitude,
        mode 3 amplitude,
        mode 1 phase shift,
        mode 2 phase shift
    """
    d = list(direction) + [0.0] * max(0, 5 - len(direction))
    a1 = 1.0 + radius * d[0]
    a2 = radius * d[1]
    a3 = radius * d[2]
    ph1 = radius * d[3]
    ph2 = radius * d[4]
    harmonics = [(a1, 1, ph1)]
    if abs(a2) > 0:
        harmonics.append((a2, 2, ph2))
    if abs(a3) > 0:
        harmonics.append((a3, 3, 0.0))
    return HarmonicFamily(harmonics=harmonics)


def local_robustness_scan(
    directions: Sequence[Sequence[float]],
    radii: Sequence[float],
    golden_rational: tuple[int, int],
    challenger_rationals: Sequence[tuple[int, int]],
    target_residue: float = 0.25,
    K_window: tuple[float, float] = (0.95, 0.98),
) -> pd.DataFrame:
    """Scan local families and compare golden crossing lower bound to best challenger upper bound."""
    rows = []
    for i, direction in enumerate(directions):
        best_loss_radius = None
        for radius in sorted(radii):
            family = family_from_direction(direction, radius)
            g = bisection_crossing_bracket(*golden_rational, family=family, target_residue=target_residue, K_lo=K_window[0], K_hi=K_window[1])
            challenger_highs = []
            ok = bool(g.get("success"))
            if ok:
                g_lo = float(g["K_lo"])
                for rat in challenger_rationals:
                    c = bisection_crossing_bracket(*rat, family=family, target_residue=target_residue, K_lo=K_window[0], K_hi=K_window[1])
                    if not c.get("success"):
                        ok = False
                        break
                    challenger_highs.append(float(c["K_hi"]))
                if ok and challenger_highs:
                    gap = g_lo - max(challenger_highs)
                    dominates = gap > 0
                else:
                    gap = np.nan
                    dominates = False
            else:
                gap = np.nan
                dominates = False
            rows.append(
                {
                    "direction_id": i,
                    "radius": float(radius),
                    "golden_success": bool(g.get("success", False)),
                    "gap_lower_minus_best_upper": float(gap) if np.isfinite(gap) else np.nan,
                    "golden_dominates": bool(dominates),
                }
            )
            if best_loss_radius is None and not dominates and ok:
                best_loss_radius = radius
        # scan continues: boundary can be inferred downstream from first False.
    return pd.DataFrame(rows)
