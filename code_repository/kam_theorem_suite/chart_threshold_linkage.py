from __future__ import annotations

"""Chart-to-irrational-threshold linkage package.

This module is the next theorem-facing move after the localized
transversality-window package.  The renormalization side can now produce:

* a candidate fixed-point enclosure,
* a spectral splitting proxy,
* a stable-manifold chart scaffold,
* a localized family crossing window.

What it still lacked was an explicit bridge to the irrational-threshold side of
Theorems III--V.  This module supplies that bridge in the most honest form the
current repository supports.

It does **not** prove that the renormalization critical parameter equals the
analytic irrational threshold.  Instead it builds a machine-readable linkage
certificate that compares:

* the renormalization-side localized critical window,
* the lower-side golden existence support,
* the upper-side golden incompatibility support, and
* the Theorem V explicit irrational-threshold interval.

The result is a theorem-facing object stating whether those four pieces line up
on a common threshold axis.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .golden_aposteriori import build_golden_aposteriori_certificate, golden_inverse
from .golden_lower_neighborhood_stability import build_golden_lower_neighborhood_stability_certificate
from .standard_map import HarmonicFamily
from .theorem_iv_obstruction import build_golden_irrational_incompatibility_certificate
from .theorem_v_error_control import build_theorem_v_explicit_error_certificate
from .theorem_v_downstream_utils import extract_theorem_v_target_interval
from .transversality_window import build_validated_critical_surface_bridge_certificate


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _filter_kwargs(fn, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    return {k: v for k, v in kwargs.items() if k in params}


def _as_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, 'to_dict'):
        return dict(obj.to_dict())
    raise TypeError(f'Cannot coerce object of type {type(obj)!r} to dict')


def _interval_intersection(
    a_lo: float | None,
    a_hi: float | None,
    b_lo: float | None,
    b_hi: float | None,
) -> tuple[float | None, float | None, float | None]:
    if a_lo is None or a_hi is None or b_lo is None or b_hi is None:
        return None, None, None
    lo = max(float(a_lo), float(b_lo))
    hi = min(float(a_hi), float(b_hi))
    if hi < lo:
        return None, None, None
    return float(lo), float(hi), float(hi - lo)


def _coerce_float(x: Any) -> float | None:
    if x is None:
        return None
    return float(x)

def _find_recursive_value(obj: Any, key: str) -> Any:
    if isinstance(obj, Mapping):
        if key in obj and obj.get(key) is not None:
            return obj.get(key)
        for value in obj.values():
            found = _find_recursive_value(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _find_recursive_value(value, key)
            if found is not None:
                return found
    return None


def _extract_lower_support(lower: Mapping[str, Any]) -> tuple[float | None, float | None, float | None]:
    lower_bound = _coerce_float(lower.get('stable_lower_bound'))
    lower_window_lo = _coerce_float(lower.get('stable_window_lo'))
    lower_window_hi = _coerce_float(lower.get('stable_window_hi'))
    if lower_bound is None:
        certified_interval = lower.get('certified_below_threshold_interval')
        if isinstance(certified_interval, Sequence) and len(certified_interval) == 2 and certified_interval[1] is not None:
            lower_bound = float(certified_interval[1])
            if lower_window_lo is None and certified_interval[0] is not None:
                lower_window_lo = float(certified_interval[0])
            if lower_window_hi is None:
                lower_window_hi = float(certified_interval[1])
    if lower_bound is None and str(lower.get('analytic_theorem_status', '')).startswith('analytic-torus-bridge-'):
        lower_bound = _coerce_float(lower.get('K'))
    if lower_window_lo is None and lower_window_hi is None and lower_bound is not None:
        lower_window_lo = lower_bound
        lower_window_hi = lower_bound
    return lower_bound, lower_window_lo, lower_window_hi


def _extract_upper_support(upper: Mapping[str, Any]) -> tuple[float | None, float | None, float | None, float | None]:
    upper_lo = _coerce_float(upper.get('selected_upper_lo'))
    upper_hi = _coerce_float(upper.get('selected_upper_hi'))
    barrier_lo = _coerce_float(upper.get('selected_barrier_lo'))
    barrier_hi = _coerce_float(upper.get('selected_barrier_hi'))
    if upper_lo is None:
        upper_lo = _coerce_float(_find_recursive_value(upper, 'selected_upper_lo'))
    if upper_hi is None:
        upper_hi = _coerce_float(_find_recursive_value(upper, 'selected_upper_hi'))
    if barrier_lo is None:
        barrier_lo = _coerce_float(_find_recursive_value(upper, 'selected_barrier_lo'))
    if barrier_hi is None:
        barrier_hi = _coerce_float(_find_recursive_value(upper, 'selected_barrier_hi'))
    return upper_lo, upper_hi, barrier_lo, barrier_hi


@dataclass
class ChartThresholdLinkageCertificate:
    rho: float
    family_label: str
    threshold_axis: dict[str, float]
    renormalization_bridge: dict[str, Any]
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    theorem_v_explicit_error_control: dict[str, Any]
    mapped_critical_center: float
    mapped_critical_radius: float | None
    mapped_critical_interval: list[float] | None
    linkage_relation: dict[str, Any]
    theorem_flags: dict[str, bool]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenChartThresholdBridgeCertificate:
    rho: float
    family_label: str
    linkage_certificate: dict[str, Any]
    aligned_interval: list[float] | None
    threshold_gap: float | None
    theorem_flags: dict[str, bool]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_chart_threshold_linkage_certificate(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    threshold_center: float = 0.971159,
    threshold_scale: float = 1.0,
    base_K_values: Sequence[float] | None = None,
    ladder: dict[str, Any] | None = None,
    lower_certificate: Mapping[str, Any] | None = None,
    upper_certificate: Mapping[str, Any] | None = None,
    theorem_v_certificate: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ChartThresholdLinkageCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    renorm_bridge = _as_dict(
        build_validated_critical_surface_bridge_certificate(
            family,
            family_label=family_label,
            **_filter_kwargs(build_validated_critical_surface_bridge_certificate, kwargs),
        )
    )

    localized_center = float(renorm_bridge.get('localized_center', 0.0))
    localized_radius = _coerce_float(renorm_bridge.get('localized_radius'))
    mapped_center = float(threshold_center + threshold_scale * localized_center)
    if localized_radius is None:
        mapped_interval = [float(mapped_center), float(mapped_center)]
        mapped_radius = None
    else:
        a = float(threshold_center + threshold_scale * (localized_center - localized_radius))
        b = float(threshold_center + threshold_scale * (localized_center + localized_radius))
        lo = min(a, b)
        hi = max(a, b)
        mapped_interval = [float(lo), float(hi)]
        mapped_radius = float(0.5 * (hi - lo))

    if lower_certificate is not None:
        lower = _as_dict(lower_certificate)
        lower_source = 'precomputed-lower-certificate'
    elif base_K_values is not None:
        lower = _as_dict(
            build_golden_lower_neighborhood_stability_certificate(
                base_K_values=base_K_values,
                family=family,
                rho=rho,
                **_filter_kwargs(build_golden_lower_neighborhood_stability_certificate, kwargs),
            )
        )
        lower_source = 'golden-lower-neighborhood-stability'
    else:
        lower = _as_dict(
            build_golden_aposteriori_certificate(
                K=mapped_center,
                family=family,
                rho=rho,
                **_filter_kwargs(build_golden_aposteriori_certificate, kwargs),
            )
        )
        lower_source = 'golden-aposteriori-at-critical-estimate'

    if upper_certificate is not None:
        upper = _as_dict(upper_certificate)
        upper_source = 'precomputed-upper-certificate'
    else:
        upper = _as_dict(
            build_golden_irrational_incompatibility_certificate(
                family=family,
                rho=rho,
                **_filter_kwargs(build_golden_irrational_incompatibility_certificate, kwargs),
            )
        )
        upper_source = 'golden-irrational-incompatibility'

    if theorem_v_certificate is not None:
        theorem_v = _as_dict(theorem_v_certificate)
        theorem_v_source = 'precomputed-theorem-v-certificate'
    elif ladder is not None:
        theorem_v = _as_dict(
            build_theorem_v_explicit_error_certificate(
                ladder,
                rho_target=rho,
                family_label=family_label,
                **_filter_kwargs(build_theorem_v_explicit_error_certificate, kwargs),
            )
        )
        theorem_v_source = 'theorem-v-explicit-error-control'
    else:
        theorem_v = {}
        theorem_v_source = 'none'

    lower_bound, lower_window_lo, lower_window_hi = _extract_lower_support(lower)

    upper_lo, upper_hi, barrier_lo, barrier_hi = _extract_upper_support(upper)

    theorem_v_interval = extract_theorem_v_target_interval(theorem_v)
    theorem_v_lo = None if theorem_v_interval is None else float(theorem_v_interval[0])
    theorem_v_hi = None if theorem_v_interval is None else float(theorem_v_interval[1])
    aligned_lo, aligned_hi, aligned_width = _interval_intersection(
        mapped_interval[0],
        mapped_interval[1],
        theorem_v_lo,
        theorem_v_hi,
    )
    chart_two_sided_lo, chart_two_sided_hi, chart_two_sided_width = _interval_intersection(
        mapped_interval[0],
        mapped_interval[1],
        lower_window_lo,
        upper_hi,
    )

    theorem_v_center = None if theorem_v_lo is None or theorem_v_hi is None else float(0.5 * (theorem_v_lo + theorem_v_hi))
    theorem_v_width = None if theorem_v_lo is None or theorem_v_hi is None else float(theorem_v_hi - theorem_v_lo)
    center_gap = None if theorem_v_center is None else float(abs(mapped_center - theorem_v_center))
    width_ratio = None if theorem_v_width is None or theorem_v_width <= 0.0 or mapped_radius is None else float((2.0 * mapped_radius) / theorem_v_width)
    lower_to_upper_gap = None if lower_bound is None or upper_hi is None else float(upper_hi - lower_bound)
    upper_barrier_gap = None if upper_hi is None or barrier_lo is None else float(barrier_lo - upper_hi)

    relation = {
        'lower_source': lower_source,
        'upper_source': upper_source,
        'theorem_v_source': theorem_v_source,
        'lower_bound': lower_bound,
        'lower_window_lo': lower_window_lo,
        'lower_window_hi': lower_window_hi,
        'upper_lo': upper_lo,
        'upper_hi': upper_hi,
        'barrier_lo': barrier_lo,
        'barrier_hi': barrier_hi,
        'theorem_v_interval_lo': theorem_v_lo,
        'theorem_v_interval_hi': theorem_v_hi,
        'aligned_interval_lo': aligned_lo,
        'aligned_interval_hi': aligned_hi,
        'aligned_interval_width': aligned_width,
        'chart_two_sided_interval_lo': chart_two_sided_lo,
        'chart_two_sided_interval_hi': chart_two_sided_hi,
        'chart_two_sided_interval_width': chart_two_sided_width,
        'critical_estimate_above_lower_bound': bool(lower_bound is not None and mapped_center + 1e-15 >= lower_bound),
        'critical_estimate_below_upper_bound': bool(upper_hi is not None and mapped_center - 1e-15 <= upper_hi),
        'critical_estimate_inside_theorem_v_interval': bool(theorem_v_lo is not None and theorem_v_hi is not None and theorem_v_lo - 1e-15 <= mapped_center <= theorem_v_hi + 1e-15),
        'critical_window_intersects_theorem_v_interval': bool(aligned_width is not None),
        'critical_window_intersects_two_sided_window': bool(chart_two_sided_width is not None),
        'chart_window_to_theorem_v_center_gap': center_gap,
        'chart_window_to_theorem_v_width_ratio': width_ratio,
        'lower_to_upper_gap': lower_to_upper_gap,
        'upper_to_barrier_gap': upper_barrier_gap,
    }

    flags = {
        'renormalization_bridge_validated': bool(str(renorm_bridge.get('theorem_status', '')).startswith('proxy-critical-surface-window-bridge-')),
        'mapped_interval_available': bool(mapped_interval is not None),
        'lower_support_available': bool(lower_bound is not None or lower_window_lo is not None),
        'upper_support_available': bool(upper_hi is not None),
        'theorem_v_interval_available': bool(theorem_v_lo is not None and theorem_v_hi is not None),
        'critical_estimate_above_lower_bound': bool(relation['critical_estimate_above_lower_bound']),
        'critical_estimate_below_upper_bound': bool(relation['critical_estimate_below_upper_bound']),
        'critical_window_intersects_theorem_v_interval': bool(relation['critical_window_intersects_theorem_v_interval']),
        'critical_window_intersects_two_sided_window': bool(relation['critical_window_intersects_two_sided_window']),
        'critical_estimate_inside_theorem_v_interval': bool(relation['critical_estimate_inside_theorem_v_interval']),
        'upper_barrier_gap_positive': bool(upper_barrier_gap is not None and upper_barrier_gap > 0.0),
    }

    if all(flags.values()):
        status = 'chart-threshold-linkage-strong'
        notes = 'The localized renormalization-side critical window aligns simultaneously with the Theorem V explicit threshold interval and the current two-sided lower/upper threshold package.'
    elif flags['renormalization_bridge_validated'] and flags['theorem_v_interval_available'] and flags['critical_window_intersects_theorem_v_interval']:
        status = 'chart-threshold-linkage-moderate'
        notes = 'The localized renormalization-side critical window now interfaces directly with the irrational-threshold machinery and overlaps the Theorem V interval, but the full two-sided alignment is not yet complete.'
    elif flags['renormalization_bridge_validated'] and (flags['lower_support_available'] or flags['upper_support_available'] or flags['theorem_v_interval_available']):
        status = 'chart-threshold-linkage-weak'
        notes = 'The renormalization-side bridge is now connected to the threshold-side packages, but the current threshold-axis overlap remains only partial.'
    else:
        status = 'chart-threshold-linkage-failed'
        notes = 'The current renormalization-side bridge did not yet connect cleanly to the available threshold-side certificates.'

    return ChartThresholdLinkageCertificate(
        rho=float(rho),
        family_label=str(family_label),
        threshold_axis={
            'threshold_center': float(threshold_center),
            'threshold_scale': float(threshold_scale),
        },
        renormalization_bridge=renorm_bridge,
        lower_side=lower,
        upper_side=upper,
        theorem_v_explicit_error_control=theorem_v,
        mapped_critical_center=float(mapped_center),
        mapped_critical_radius=mapped_radius,
        mapped_critical_interval=[float(x) for x in mapped_interval] if mapped_interval is not None else None,
        linkage_relation=relation,
        theorem_flags=flags,
        theorem_status=status,
        notes=notes,
    )


def build_golden_chart_threshold_bridge_certificate(
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    **kwargs: Any,
) -> GoldenChartThresholdBridgeCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)
    linkage = build_chart_threshold_linkage_certificate(
        family=family,
        family_label=family_label,
        rho=rho,
        **kwargs,
    ).to_dict()
    relation = linkage.get('linkage_relation', {})
    aligned_lo = relation.get('aligned_interval_lo')
    aligned_hi = relation.get('aligned_interval_hi')
    aligned_interval = None if aligned_lo is None or aligned_hi is None else [float(aligned_lo), float(aligned_hi)]
    gap = relation.get('lower_to_upper_gap')
    flags = {
        'chart_threshold_linkage_available': bool(linkage.get('theorem_status', '').startswith('chart-threshold-linkage-')),
        'aligned_interval_nonempty': bool(aligned_interval is not None),
        'two_sided_gap_positive': bool(gap is not None and float(gap) > 0.0),
    }
    if flags['aligned_interval_nonempty'] and flags['two_sided_gap_positive']:
        status = 'golden-chart-threshold-bridge-strong'
        notes = 'The renormalization-side crossing window and the threshold-side packages now share a nonempty aligned interval on the golden threshold axis.'
    elif flags['chart_threshold_linkage_available']:
        status = 'golden-chart-threshold-bridge-partial'
        notes = 'A usable chart-to-threshold linkage now exists, but the common aligned interval is still only partial.'
    else:
        status = 'golden-chart-threshold-bridge-failed'
        notes = 'The renormalization-side package did not yet produce a usable chart-to-threshold bridge.'
    return GoldenChartThresholdBridgeCertificate(
        rho=float(rho),
        family_label=str(family_label),
        linkage_certificate=linkage,
        aligned_interval=aligned_interval,
        threshold_gap=(None if gap is None else float(gap)),
        theorem_flags=flags,
        theorem_status=status,
        notes=notes,
    )
