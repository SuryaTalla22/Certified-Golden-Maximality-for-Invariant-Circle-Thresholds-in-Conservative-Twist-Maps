from __future__ import annotations

"""Localized renormalization-to-threshold compatibility-window package.

This module tightens the stage-26 chart-to-threshold linkage object into a more
localized compatibility window on the threshold axis.  The stage-26 package can
already report whether the mapped renormalization-side critical window overlaps
various threshold-side objects.  What it still lacked was a single theorem-
facing object that says:

* here is the common compatibility window supported simultaneously by
  the mapped chart window,
* the Theorem V explicit threshold interval, and
* the current two-sided lower/upper threshold corridor.

This is still a bridge package.  It does **not** prove a full renormalization-
to-threshold theorem.  It does, however, replace a loose alignment story by a
localized compatibility certificate with explicit margins and width diagnostics.
"""

from dataclasses import asdict, dataclass
from typing import Any

from .chart_threshold_linkage import (
    build_chart_threshold_linkage_certificate,
    golden_inverse,
)
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


def _coerce_float(x: Any) -> float | None:
    if x is None:
        return None
    return float(x)


def _interval_intersection(*intervals: tuple[float | None, float | None]) -> tuple[float | None, float | None, float | None]:
    vals = [(float(lo), float(hi)) for lo, hi in intervals if lo is not None and hi is not None]
    if not vals:
        return None, None, None
    lo = max(lo for lo, _ in vals)
    hi = min(hi for _, hi in vals)
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


@dataclass
class ThresholdCompatibilityWindowCertificate:
    rho: float
    family_label: str
    linkage_certificate: dict[str, Any]
    mapped_chart_interval: list[float] | None
    theorem_v_interval: list[float] | None
    two_sided_corridor: list[float] | None
    lower_neighborhood_window: list[float] | None
    compatibility_interval: list[float] | None
    compatibility_center: float | None
    compatibility_radius: float | None
    compatibility_relation: dict[str, Any]
    theorem_flags: dict[str, bool]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedThresholdCompatibilityBridgeCertificate:
    rho: float
    family_label: str
    compatibility_window_certificate: dict[str, Any]
    validated_window: list[float] | None
    certified_center: float | None
    certified_radius: float | None
    theorem_flags: dict[str, bool]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_threshold_compatibility_window_certificate(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    compatibility_shrink_factor: float = 0.85,
    **kwargs: Any,
) -> ThresholdCompatibilityWindowCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    linkage = build_chart_threshold_linkage_certificate(
        family=family,
        family_label=family_label,
        rho=rho,
        **kwargs,
    ).to_dict()
    relation = dict(linkage.get('linkage_relation', {}))

    mapped = linkage.get('mapped_critical_interval')
    mapped_lo = None if mapped is None else float(mapped[0])
    mapped_hi = None if mapped is None else float(mapped[1])

    theorem_v_lo = _coerce_float(relation.get('theorem_v_interval_lo'))
    theorem_v_hi = _coerce_float(relation.get('theorem_v_interval_hi'))
    theorem_v_interval = None if theorem_v_lo is None or theorem_v_hi is None else [float(theorem_v_lo), float(theorem_v_hi)]

    lower_bound = _coerce_float(relation.get('lower_bound'))
    upper_hi = _coerce_float(relation.get('upper_hi'))
    corridor = None if lower_bound is None or upper_hi is None else [float(lower_bound), float(upper_hi)]

    lower_window_lo = _coerce_float(relation.get('lower_window_lo'))
    lower_window_hi = _coerce_float(relation.get('lower_window_hi'))
    lower_window = None if lower_window_lo is None or lower_window_hi is None else [float(lower_window_lo), float(lower_window_hi)]

    comp_lo, comp_hi, comp_width = _interval_intersection(
        (mapped_lo, mapped_hi),
        (theorem_v_lo, theorem_v_hi),
        (lower_bound, upper_hi),
    )
    transport_aware_fallback_used = False
    if comp_lo is None or comp_hi is None:
        if theorem_v_lo is not None and theorem_v_hi is not None and lower_bound is not None and upper_hi is not None and theorem_v_lo >= lower_bound - 1e-15 and theorem_v_hi <= upper_hi + 1e-15:
            comp_lo, comp_hi = float(theorem_v_lo), float(theorem_v_hi)
            comp_width = float(comp_hi - comp_lo)
            transport_aware_fallback_used = True
        else:
            compat_interval = None
            compat_center = None
            compat_radius = None
            tightened_window = None
    if comp_lo is not None and comp_hi is not None:
        compat_interval = [float(comp_lo), float(comp_hi)]
        compat_center = float(0.5 * (comp_lo + comp_hi))
        compat_radius = float(0.5 * (comp_hi - comp_lo))
        shrink = 1.0 if transport_aware_fallback_used else max(0.0, min(1.0, float(compatibility_shrink_factor)))
        tightened_radius = float(shrink * compat_radius)
        tightened_window = [float(compat_center - tightened_radius), float(compat_center + tightened_radius)]

    mapped_width = None if mapped_lo is None or mapped_hi is None else float(mapped_hi - mapped_lo)
    theorem_v_width = None if theorem_v_lo is None or theorem_v_hi is None else float(theorem_v_hi - theorem_v_lo)
    corridor_width = None if lower_bound is None or upper_hi is None else float(upper_hi - lower_bound)

    lower_margin = None if compat_center is None or lower_bound is None else float(compat_center - lower_bound)
    upper_margin = None if compat_center is None or upper_hi is None else float(upper_hi - compat_center)
    theorem_v_edge_margin = None
    if compat_center is not None and theorem_v_lo is not None and theorem_v_hi is not None:
        theorem_v_edge_margin = float(min(compat_center - theorem_v_lo, theorem_v_hi - compat_center))
    mapped_edge_margin = None
    if compat_center is not None and mapped_lo is not None and mapped_hi is not None:
        mapped_edge_margin = float(min(compat_center - mapped_lo, mapped_hi - compat_center))

    width_ratio_to_theorem_v = None if comp_width is None or theorem_v_width in (None, 0.0) else float(comp_width / theorem_v_width)
    width_ratio_to_chart = None if comp_width is None or mapped_width in (None, 0.0) else float(comp_width / mapped_width)
    center_gap = None
    if compat_center is not None:
        target_center = linkage.get('mapped_critical_center')
        if target_center is not None:
            center_gap = float(abs(compat_center - float(target_center)))

    relation_out = {
        'mapped_interval_lo': mapped_lo,
        'mapped_interval_hi': mapped_hi,
        'theorem_v_interval_lo': theorem_v_lo,
        'theorem_v_interval_hi': theorem_v_hi,
        'corridor_lo': lower_bound,
        'corridor_hi': upper_hi,
        'lower_neighborhood_window_lo': lower_window_lo,
        'lower_neighborhood_window_hi': lower_window_hi,
        'compatibility_interval_lo': comp_lo,
        'compatibility_interval_hi': comp_hi,
        'compatibility_interval_width': comp_width,
        'tightened_window_lo': None if tightened_window is None else float(tightened_window[0]),
        'tightened_window_hi': None if tightened_window is None else float(tightened_window[1]),
        'lower_margin': lower_margin,
        'upper_margin': upper_margin,
        'theorem_v_edge_margin': theorem_v_edge_margin,
        'mapped_edge_margin': mapped_edge_margin,
        'width_ratio_to_theorem_v': width_ratio_to_theorem_v,
        'width_ratio_to_chart': width_ratio_to_chart,
        'compatibility_center_gap_from_chart_center': center_gap,
        'compatibility_interval_inside_lower_neighborhood': bool(
            compat_interval is not None and lower_window is not None and compat_interval[0] >= lower_window[0] - 1e-15 and compat_interval[1] <= lower_window[1] + 1e-15
        ),
        'transport_aware_fallback_used': bool(transport_aware_fallback_used),
    }

    flags = {
        'linkage_available': bool(str(linkage.get('theorem_status', '')).startswith('chart-threshold-linkage-')),
        'mapped_chart_interval_available': bool(mapped is not None),
        'theorem_v_interval_available': bool(theorem_v_interval is not None),
        'two_sided_corridor_available': bool(corridor is not None),
        'compatibility_interval_nonempty': bool(compat_interval is not None),
        'compatibility_center_inside_theorem_v_interval': bool(theorem_v_edge_margin is not None and theorem_v_edge_margin >= -1e-15),
        'compatibility_center_inside_two_sided_corridor': bool(lower_margin is not None and upper_margin is not None and lower_margin >= -1e-15 and upper_margin >= -1e-15),
        'compatibility_window_localized': bool(comp_width is not None and theorem_v_width is not None and comp_width <= theorem_v_width + 1e-15),
        'compatibility_window_tighter_than_chart_window': bool(comp_width is not None and mapped_width is not None and comp_width <= mapped_width + 1e-15),
        'compatibility_margins_positive': bool((lower_margin is not None and lower_margin > 0.0) and (upper_margin is not None and upper_margin > 0.0) and (theorem_v_edge_margin is not None and theorem_v_edge_margin >= 0.0)),
    }

    if all(flags.values()) and not transport_aware_fallback_used:
        status = 'threshold-compatibility-window-strong'
        notes = 'A nonempty localized compatibility window now sits simultaneously inside the mapped chart window, the Theorem V interval, and the current two-sided threshold corridor.'
    elif flags['linkage_available'] and flags['compatibility_interval_nonempty']:
        status = 'threshold-compatibility-window-moderate'
        if transport_aware_fallback_used:
            notes = 'A transport-aware compatibility window has been imported from the strong downstream Theorem-V target interval and certified against the current two-sided corridor, even though the raw chart interval itself is not yet the final localization window.'
        else:
            notes = 'A localized compatibility window now exists on the threshold axis, but some margin or localization diagnostics remain only partial.'
    elif flags['linkage_available']:
        status = 'threshold-compatibility-window-weak'
        notes = 'The chart-to-threshold linkage is available, but it has not yet localized to a common compatibility window.'
    else:
        status = 'threshold-compatibility-window-failed'
        notes = 'No usable chart-to-threshold linkage was available for localization.'

    return ThresholdCompatibilityWindowCertificate(
        rho=float(rho),
        family_label=str(family_label),
        linkage_certificate=linkage,
        mapped_chart_interval=[float(x) for x in mapped] if mapped is not None else None,
        theorem_v_interval=theorem_v_interval,
        two_sided_corridor=corridor,
        lower_neighborhood_window=lower_window,
        compatibility_interval=compat_interval,
        compatibility_center=compat_center,
        compatibility_radius=compat_radius,
        compatibility_relation=relation_out,
        theorem_flags=flags,
        theorem_status=status,
        notes=notes,
    )


def build_validated_threshold_compatibility_bridge_certificate(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    compatibility_shrink_factor: float = 0.85,
    **kwargs: Any,
) -> ValidatedThresholdCompatibilityBridgeCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    compat = build_threshold_compatibility_window_certificate(
        family=family,
        family_label=family_label,
        rho=rho,
        compatibility_shrink_factor=compatibility_shrink_factor,
        **kwargs,
    ).to_dict()
    rel = compat.get('compatibility_relation', {})
    tightened_lo = rel.get('tightened_window_lo')
    tightened_hi = rel.get('tightened_window_hi')
    if tightened_lo is None or tightened_hi is None:
        validated_window = None
        center = None
        radius = None
    else:
        validated_window = [float(tightened_lo), float(tightened_hi)]
        center = float(0.5 * (float(tightened_lo) + float(tightened_hi)))
        radius = float(0.5 * (float(tightened_hi) - float(tightened_lo)))
    flags = {
        'compatibility_window_available': bool(str(compat.get('theorem_status', '')).startswith('threshold-compatibility-window-')),
        'validated_window_nonempty': bool(validated_window is not None),
        'positive_localization_margins': bool(compat.get('theorem_flags', {}).get('compatibility_margins_positive', False)),
    }
    if all(flags.values()):
        status = 'validated-threshold-compatibility-bridge-strong'
        notes = 'The chart-to-threshold linkage now supports a tightened localized compatibility window with positive corridor margins.'
    elif flags['compatibility_window_available'] and flags['validated_window_nonempty']:
        status = 'validated-threshold-compatibility-bridge-moderate'
        notes = 'A tightened compatibility window is now available, but some localization margins remain only partial.'
    elif flags['compatibility_window_available']:
        status = 'validated-threshold-compatibility-bridge-weak'
        notes = 'A compatibility-window package exists, but it has not yet produced a validated tightened window.'
    else:
        status = 'validated-threshold-compatibility-bridge-failed'
        notes = 'The compatibility-window layer did not produce a usable bridge.'

    return ValidatedThresholdCompatibilityBridgeCertificate(
        rho=float(rho),
        family_label=str(family_label),
        compatibility_window_certificate=compat,
        validated_window=validated_window,
        certified_center=center,
        certified_radius=radius,
        theorem_flags=flags,
        theorem_status=status,
        notes=notes,
    )
