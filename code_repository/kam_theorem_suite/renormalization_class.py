from __future__ import annotations

"""Renormalization-class scaffolding for the universal theorem program.

This is intentionally modest.  It does not implement the renormalization
operator or prove the golden critical surface.  Instead, it gives the project a
first theorem-facing notion of *chart admissibility* near the standard/golden
regime so later fixed-point and stable-manifold code has a concrete interface to
plug into.
"""

from dataclasses import asdict, dataclass
from typing import Any

import math
import numpy as np

from .standard_map import HarmonicFamily
from .universality_class import (
    FamilyAnalyticProfile,
    build_family_analytic_profile,
    build_universality_class_certificate,
)


@dataclass
class RenormalizationChartProfile:
    chart_coordinates: dict[str, float]
    chart_radius_proxy: float
    stable_direction_proxy: float
    unstable_direction_proxy: float
    transversality_proxy: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RenormalizationClassCertificate:
    family_label: str
    universality_certificate: dict[str, Any]
    chart_profile: dict[str, Any]
    chart_margins: dict[str, float]
    chart_flags: dict[str, bool]
    admissible_near_chart: bool
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def _chart_coordinates(profile: FamilyAnalyticProfile) -> dict[str, float]:
    return {
        'anchor_amplitude_shift': float(profile.anchor_amplitude - 1.0),
        'anchor_phase_shift': float(profile.anchor_phase),
        'higher_mode_energy': float(profile.higher_mode_energy),
        'weighted_mode_l1': float(profile.weighted_mode_l1),
        'strip_complexity': float(1.0 / max(profile.strip_width_proxy, 1e-12)),
    }


def build_renormalization_chart_profile(family: HarmonicFamily) -> RenormalizationChartProfile:
    profile = build_family_analytic_profile(family)
    coords = _chart_coordinates(profile)
    stable_proxy = float(math.sqrt(coords['higher_mode_energy'] ** 2 + 0.05 * coords['weighted_mode_l1'] ** 2))
    unstable_proxy = float(math.sqrt(coords['anchor_amplitude_shift'] ** 2 + coords['anchor_phase_shift'] ** 2))
    transversality_proxy = float(abs(coords['anchor_amplitude_shift']) + 0.25 * abs(coords['anchor_phase_shift']) + 1e-3)
    radius_proxy = float(math.sqrt(stable_proxy**2 + unstable_proxy**2))
    return RenormalizationChartProfile(
        chart_coordinates=coords,
        chart_radius_proxy=float(radius_proxy),
        stable_direction_proxy=float(stable_proxy),
        unstable_direction_proxy=float(unstable_proxy),
        transversality_proxy=float(transversality_proxy),
    )


def build_renormalization_class_certificate(
    family: HarmonicFamily,
    *,
    family_label: str = 'harmonic_family',
    chart_radius_tol: float = 0.9,
    stable_budget: float = 0.6,
    unstable_budget: float = 0.4,
    transversality_floor: float = 1e-3,
) -> RenormalizationClassCertificate:
    base = build_universality_class_certificate(family, family_label=family_label)
    chart = build_renormalization_chart_profile(family)
    margins = {
        'universality_margin': 1.0 if base.admissible else -1.0,
        'chart_radius_margin': float(chart_radius_tol - chart.chart_radius_proxy),
        'stable_budget_margin': float(stable_budget - chart.stable_direction_proxy),
        'unstable_budget_margin': float(unstable_budget - chart.unstable_direction_proxy),
        'transversality_margin': float(chart.transversality_proxy - transversality_floor),
    }
    flags = {k.replace('_margin', ''): (v >= 0.0) for k, v in margins.items()}
    admissible = bool(all(flags.values()))
    status = 'near_golden_chart_scaffold' if admissible else 'outside_chart_scaffold'
    return RenormalizationClassCertificate(
        family_label=str(family_label),
        universality_certificate=base.to_dict(),
        chart_profile=chart.to_dict(),
        chart_margins=margins,
        chart_flags=flags,
        admissible_near_chart=admissible,
        status=status,
    )
