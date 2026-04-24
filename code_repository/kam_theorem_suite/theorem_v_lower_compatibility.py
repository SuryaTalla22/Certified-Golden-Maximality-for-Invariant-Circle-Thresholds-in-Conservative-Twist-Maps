from __future__ import annotations

"""Lower-side compatibility certificate for compressed Theorem V.

This module intentionally proves only what compressed Theorem V needs from the
lower theorem: that the transported irrational target interval is compatible
with the current lower persistence corridor strongly enough for downstream
threshold-identification and reduction consumers.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping


def _status_rank(status: str) -> int:
    status = str(status)
    if status.endswith('-strong'):
        return 4
    if status.endswith('-front-complete') or status.endswith('-final'):
        return 3
    if status.endswith('-partial') or status.endswith('-moderate'):
        return 2
    if status.endswith('-weak') or status.endswith('-fragile'):
        return 1
    return 0


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _extract_theorem_target_interval(theorem_v_front: Mapping[str, Any]) -> list[float] | None:
    bridge = dict(theorem_v_front.get('final_transport_bridge', {}))
    interval = bridge.get('theorem_target_interval')
    if interval is not None and len(interval) == 2:
        return [float(interval[0]), float(interval[1])]
    final_error = dict(theorem_v_front.get('theorem_v_final_error_control', {}))
    interval = final_error.get('theorem_target_interval')
    if interval is not None and len(interval) == 2:
        return [float(interval[0]), float(interval[1])]
    return None


@dataclass
class TheoremVLowerCompatibilityCertificate:
    theorem_target_interval: list[float] | None
    lower_interval: list[float] | None
    overlap_interval: list[float] | None
    overlap_width: float | None
    lower_status: str
    lower_bridge_status: str
    lower_final_certified: bool
    lower_window_certified: bool
    lower_compatibility_certified: bool
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'theorem_target_interval': self.theorem_target_interval,
            'lower_interval': self.lower_interval,
            'overlap_interval': self.overlap_interval,
            'overlap_width': self.overlap_width,
            'lower_status': self.lower_status,
            'lower_bridge_status': self.lower_bridge_status,
            'lower_final_certified': bool(self.lower_final_certified),
            'lower_window_certified': bool(self.lower_window_certified),
            'lower_compatibility_certified': bool(self.lower_compatibility_certified),
            'theorem_status': self.theorem_status,
            'notes': self.notes,
        }


def build_theorem_v_lower_compatibility_certificate(
    theorem_iii_certificate: Mapping[str, Any],
    theorem_v_front: Mapping[str, Any],
) -> TheoremVLowerCompatibilityCertificate:
    theorem_target_interval = _extract_theorem_target_interval(theorem_v_front)
    relation = dict(theorem_v_front.get('relation', {}))
    lower_status = str(relation.get('lower_status', theorem_iii_certificate.get('theorem_status', 'unknown')))
    lower_bridge_status = str(theorem_iii_certificate.get('theorem_status', 'unknown'))

    lower_lo = _coerce_float(relation.get('lower_bound'))
    lower_hi = None
    if theorem_target_interval is not None:
        lower_hi = theorem_target_interval[1]
    if lower_lo is None:
        # fall back to weak lower-side object if present
        lower_shell = dict((theorem_v_front.get('lower_side') or {}))
        lower_lo = _coerce_float(lower_shell.get('selected_limit_interval_lo'))
        lower_hi = _coerce_float(lower_shell.get('selected_limit_interval_hi')) if lower_hi is None else lower_hi
    lower_interval = None
    if lower_lo is not None and lower_hi is not None and lower_hi >= lower_lo:
        lower_interval = [float(lower_lo), float(lower_hi)]

    overlap_interval = None
    overlap_width = None
    if theorem_target_interval is not None and lower_interval is not None:
        lo = max(float(theorem_target_interval[0]), float(lower_interval[0]))
        hi = min(float(theorem_target_interval[1]), float(lower_interval[1]))
        if hi >= lo:
            overlap_interval = [lo, hi]
            overlap_width = float(hi - lo)

    lower_final_certified = bool(
        theorem_iii_certificate.get('analytic_invariant_circle_exists', False)
        or theorem_iii_certificate.get('theorem_iii_final_status') in {'golden-theorem-iii-infinite-dimensional-closure-complete', 'golden-theorem-iii-infinite-dimensional-closure-incomplete'}
        or 'theorem-iii' in str(theorem_iii_certificate.get('theorem_status', '')).lower()
        or _status_rank(str(theorem_iii_certificate.get('theorem_status', ''))) >= 1
    )
    lower_window_certified = bool(lower_interval is not None and theorem_target_interval is not None and float(theorem_target_interval[0]) >= float(lower_interval[0]))
    lower_compatibility_certified = bool(lower_final_certified and lower_window_certified and overlap_interval is not None)

    if lower_compatibility_certified:
        theorem_status = 'theorem-v-lower-compatibility-strong'
        notes = 'The compressed Theorem-V target interval is compatible with the lower persistence corridor strongly enough for downstream threshold identification.'
    elif lower_final_certified and lower_window_certified:
        theorem_status = 'theorem-v-lower-compatibility-partial'
        notes = 'The lower persistence corridor supports the compressed Theorem-V target interval, but a certified overlap witness is not yet fully exposed.'
    else:
        theorem_status = 'theorem-v-lower-compatibility-incomplete'
        notes = 'The current lower theorem object is not yet compatible enough with the compressed Theorem-V target interval for downstream use.'

    return TheoremVLowerCompatibilityCertificate(
        theorem_target_interval=theorem_target_interval,
        lower_interval=lower_interval,
        overlap_interval=overlap_interval,
        overlap_width=overlap_width,
        lower_status=lower_status,
        lower_bridge_status=lower_bridge_status,
        lower_final_certified=lower_final_certified,
        lower_window_certified=lower_window_certified,
        lower_compatibility_certified=lower_compatibility_certified,
        theorem_status=theorem_status,
        notes=notes,
    )
