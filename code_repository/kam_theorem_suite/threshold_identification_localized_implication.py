from __future__ import annotations

"""Final theorem-facing promotion for the II->V identification seam.

This stage packages the last local implication after transport-aware discharge.
The existing seam architecture already provides:

* a Workstream-fed threshold-identification discharge shell, and
* a transport-aware discharge shell that can reduce the local hinge to
  transport-locked threshold-branch uniqueness.

What remains is to promote that transport-locked branch witness into the final
identification theorem object for the seam itself whenever the upstream
critical-surface/threshold theorem is already available and the surviving local
witness geometry is compatible with the locked branch interval.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .standard_map import HarmonicFamily
from .threshold_identification_transport_discharge import (
    build_golden_theorem_ii_to_v_identification_transport_discharge_certificate,
)


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


def _filter_kwargs(fn, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    has_var_keyword = any(p.kind == p.VAR_KEYWORD for p in params.values())
    if has_var_keyword:
        return dict(kwargs)
    return {k: v for k, v in kwargs.items() if k in params}


def _status_rank(status: str) -> int:
    status = str(status)
    if 'conditional-one-variable-strong' in status or 'conditional-two-variable-strong' in status or status.endswith('-conditional-strong') or status.endswith('-strong') or status.endswith('-discharged'):
        return 4
    if status.endswith('-front-complete') or status.endswith('-front-only') or status.endswith('-available'):
        return 3
    if status.endswith('-conditional-partial') or status.endswith('-partial') or status.endswith('-moderate'):
        return 2
    if status.endswith('-weak') or status.endswith('-fragile'):
        return 1
    return 0


def _is_front_complete(cert: Mapping[str, Any]) -> bool:
    return _status_rank(str(cert.get('theorem_status', ''))) >= 3 and len(cert.get('open_hypotheses', [])) == 0


def _coerce_interval(value: Any) -> list[float] | None:
    if isinstance(value, (list, tuple)) and len(value) == 2 and value[0] is not None and value[1] is not None:
        lo = float(value[0]); hi = float(value[1])
        if hi >= lo:
            return [lo, hi]
    return None


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _interval_intersection(a: Sequence[float] | None, b: Sequence[float] | None) -> tuple[list[float] | None, float | None]:
    if a is None or b is None:
        return None, None
    lo = max(float(a[0]), float(b[0]))
    hi = min(float(a[1]), float(b[1]))
    if hi < lo:
        return None, None
    return [float(lo), float(hi)], float(hi - lo)


def _is_subset(a: Sequence[float] | None, b: Sequence[float] | None, *, tol: float = 1e-15) -> bool:
    if a is None or b is None:
        return False
    return float(a[0]) >= float(b[0]) - tol and float(a[1]) <= float(b[1]) + tol


UPSTREAM_AVAILABLE_STATUSES = {
    'critical-surface-threshold-promotion-theorem-available',
    'critical-surface-threshold-promotion-theorem-conditional-strong',
    'critical-surface-threshold-promotion-theorem-discharged',
}


@dataclass
class ThresholdIdentificationLocalizedImplicationHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenThresholdIdentificationLocalizedImplicationCertificate:
    rho: float
    family_label: str
    transport_discharge_shell: dict[str, Any]
    threshold_identification_discharge_shell: dict[str, Any]
    transport_locked_uniqueness_certificate: dict[str, Any]
    workstream_promotion_status: str | None
    overlap_window: list[float] | None
    locked_window: list[float] | None
    identified_threshold_branch_interval: list[float] | None
    identified_branch_inside_overlap_window: bool
    identified_branch_inside_locked_window: bool
    branch_overlap_interval: list[float] | None
    branch_overlap_width: float | None
    discharged_bridge_native_tail_witness_interval: list[float] | None
    discharged_bridge_native_tail_witness_width: float | None
    witness_branch_overlap_interval: list[float] | None
    witness_branch_overlap_width: float | None
    residual_burden_summary: dict[str, Any]
    hypotheses: list[ThresholdIdentificationLocalizedImplicationHypothesisRow]
    assumptions: list[dict[str, Any]]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    upstream_active_assumptions: list[str]
    local_active_assumptions: list[str]
    active_assumptions: list[str]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho': float(self.rho),
            'family_label': str(self.family_label),
            'transport_discharge_shell': dict(self.transport_discharge_shell),
            'threshold_identification_discharge_shell': dict(self.threshold_identification_discharge_shell),
            'transport_locked_uniqueness_certificate': dict(self.transport_locked_uniqueness_certificate),
            'workstream_promotion_status': None if self.workstream_promotion_status is None else str(self.workstream_promotion_status),
            'overlap_window': None if self.overlap_window is None else [float(x) for x in self.overlap_window],
            'locked_window': None if self.locked_window is None else [float(x) for x in self.locked_window],
            'identified_threshold_branch_interval': None if self.identified_threshold_branch_interval is None else [float(x) for x in self.identified_threshold_branch_interval],
            'identified_branch_inside_overlap_window': bool(self.identified_branch_inside_overlap_window),
            'identified_branch_inside_locked_window': bool(self.identified_branch_inside_locked_window),
            'branch_overlap_interval': None if self.branch_overlap_interval is None else [float(x) for x in self.branch_overlap_interval],
            'branch_overlap_width': None if self.branch_overlap_width is None else float(self.branch_overlap_width),
            'discharged_bridge_native_tail_witness_interval': None if self.discharged_bridge_native_tail_witness_interval is None else [float(x) for x in self.discharged_bridge_native_tail_witness_interval],
            'discharged_bridge_native_tail_witness_width': None if self.discharged_bridge_native_tail_witness_width is None else float(self.discharged_bridge_native_tail_witness_width),
            'witness_branch_overlap_interval': None if self.witness_branch_overlap_interval is None else [float(x) for x in self.witness_branch_overlap_interval],
            'witness_branch_overlap_width': None if self.witness_branch_overlap_width is None else float(self.witness_branch_overlap_width),
            'residual_burden_summary': dict(self.residual_burden_summary),
            'hypotheses': [row.to_dict() for row in self.hypotheses],
            'assumptions': [dict(x) for x in self.assumptions],
            'discharged_hypotheses': [str(x) for x in self.discharged_hypotheses],
            'open_hypotheses': [str(x) for x in self.open_hypotheses],
            'upstream_active_assumptions': [str(x) for x in self.upstream_active_assumptions],
            'local_active_assumptions': [str(x) for x in self.local_active_assumptions],
            'active_assumptions': [str(x) for x in self.active_assumptions],
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


def _extract_workstream_promotion_status(discharge_shell: Mapping[str, Any]) -> str | None:
    promotion = discharge_shell.get('workstream_critical_surface_threshold_identification_promotion')
    if isinstance(promotion, Mapping):
        status = promotion.get('theorem_status')
        if status is not None:
            return str(status)
        flags = dict(promotion.get('theorem_flags', {}))
        if flags.get('promotion_theorem_discharged'):
            return 'critical-surface-threshold-promotion-theorem-discharged'
        if flags.get('promotion_theorem_available'):
            return 'critical-surface-threshold-promotion-theorem-available'
    residual = discharge_shell.get('residual_burden_summary')
    if isinstance(residual, Mapping):
        status = residual.get('status')
        if status is not None:
            return str(status)
    return None


def _build_hypotheses(
    *,
    transport_discharge_shell: Mapping[str, Any],
    workstream_promotion_status: str | None,
    identified_threshold_branch_interval: Sequence[float] | None,
    overlap_window: Sequence[float] | None,
    locked_window: Sequence[float] | None,
    branch_overlap_width: float | None,
    witness_branch_overlap_width: float | None,
    transport_locked_uniqueness_certificate: Mapping[str, Any],
) -> list[ThresholdIdentificationLocalizedImplicationHypothesisRow]:
    threshold_identification_ready = bool(transport_locked_uniqueness_certificate.get('threshold_identification_ready', False)) or str(transport_discharge_shell.get('residual_burden_summary', {}).get('status', '')) == 'transport-locked-identification-ready' or bool(identified_threshold_branch_interval is not None and _is_front_complete(transport_discharge_shell))
    branch_inside_overlap = _is_subset(identified_threshold_branch_interval, overlap_window)
    branch_inside_locked = _is_subset(identified_threshold_branch_interval, locked_window)
    workstream_available = bool(workstream_promotion_status in UPSTREAM_AVAILABLE_STATUSES)
    return [
        ThresholdIdentificationLocalizedImplicationHypothesisRow(
            name='transport_discharge_front_complete',
            satisfied=_is_front_complete(transport_discharge_shell),
            source='transport-aware identification discharge shell',
            note='The transport-aware identification discharge shell is front-complete before promoting the final localized compatibility implication.',
            margin=None,
        ),
        ThresholdIdentificationLocalizedImplicationHypothesisRow(
            name='workstream_promotion_theorem_available',
            satisfied=workstream_available,
            source='Workstream-fed threshold-identification discharge shell',
            note='The upstream Workstream-A critical-surface/threshold promotion theorem is already available, so the seam no longer depends on an unresolved structural Workstream frontier.',
            margin=None,
        ),
        ThresholdIdentificationLocalizedImplicationHypothesisRow(
            name='transport_locked_threshold_branch_identified',
            satisfied=threshold_identification_ready,
            source='transport-locked threshold uniqueness certificate',
            note='The transport-locked witness now identifies the threshold branch inside the locked window rather than merely proving eventual uniqueness.',
            margin=_coerce_float(transport_locked_uniqueness_certificate.get('threshold_identification_margin')),
        ),
        ThresholdIdentificationLocalizedImplicationHypothesisRow(
            name='identified_branch_interval_inside_workstream_overlap_window',
            satisfied=branch_inside_overlap,
            source='comparison of identified threshold branch with discharged workstream overlap window',
            note='The identified transport-locked threshold branch lies inside the discharged Workstream/threshold overlap window.',
            margin=branch_overlap_width,
        ),
        ThresholdIdentificationLocalizedImplicationHypothesisRow(
            name='identified_branch_interval_inside_locked_window',
            satisfied=branch_inside_locked,
            source='comparison of identified threshold branch with transport-locked window',
            note='The identified threshold branch lies inside the transport-locked window used by the transport-aware discharge package.',
            margin=branch_overlap_width,
        ),
        ThresholdIdentificationLocalizedImplicationHypothesisRow(
            name='discharged_bridge_witness_supports_identified_branch',
            satisfied=bool(witness_branch_overlap_width is not None),
            source='discharged bridge-native witness geometry',
            note='The discharged bridge-native witness survives on the identified threshold branch interval, so the localized compatibility implication is supported by a witness that is simultaneously Workstream-compatible and transport-locked.',
            margin=witness_branch_overlap_width,
        ),
    ]


def _build_residual_burden_summary(
    *,
    open_hypotheses: Sequence[str],
    active_assumptions: Sequence[str],
    workstream_promotion_status: str | None,
) -> dict[str, Any]:
    if not open_hypotheses and not active_assumptions:
        status = 'localized-compatibility-implication-discharged'
    elif not open_hypotheses:
        status = 'localized-compatibility-implication-upstream-frontier'
    elif workstream_promotion_status not in UPSTREAM_AVAILABLE_STATUSES:
        status = None if workstream_promotion_status is None else str(workstream_promotion_status)
    else:
        status = 'localized-compatibility-implication-local-frontier'
    return {
        'status': status,
        'open_local_hypotheses': [str(x) for x in open_hypotheses],
        'upstream_active_assumptions': [str(x) for x in active_assumptions],
        'workstream_promotion_status': None if workstream_promotion_status is None else str(workstream_promotion_status),
        'localized_compatibility_implication_available': bool(not open_hypotheses),
        'localized_compatibility_implication_discharged': bool(not open_hypotheses and not active_assumptions),
    }


def build_golden_threshold_identification_localized_implication_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    threshold_identification_transport_discharge_certificate: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> GoldenThresholdIdentificationLocalizedImplicationCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)
    rho = float(golden_inverse() if rho is None else rho)

    if threshold_identification_transport_discharge_certificate is not None:
        transport_discharge_shell = dict(threshold_identification_transport_discharge_certificate)
    else:
        transport_discharge_shell = build_golden_theorem_ii_to_v_identification_transport_discharge_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_ii_to_v_identification_transport_discharge_certificate, kwargs),
        ).to_dict()

    discharge_shell = dict(transport_discharge_shell.get('threshold_identification_discharge_shell', {}))
    uniqueness_cert = dict(transport_discharge_shell.get('transport_locked_uniqueness_certificate', {}))
    workstream_promotion_status = _extract_workstream_promotion_status(discharge_shell)

    overlap_window = _coerce_interval(discharge_shell.get('overlap_window'))
    if overlap_window is None:
        overlap_window = _coerce_interval(discharge_shell.get('identified_window'))
    locked_window = _coerce_interval(transport_discharge_shell.get('locked_window'))
    identified_threshold_branch_interval = _coerce_interval(transport_discharge_shell.get('identified_threshold_branch_interval'))
    discharged_bridge_native_tail_witness_interval = _coerce_interval(discharge_shell.get('discharged_bridge_native_tail_witness_interval'))
    if discharged_bridge_native_tail_witness_interval is None:
        discharged_bridge_native_tail_witness_interval = _coerce_interval(discharge_shell.get('identified_bridge_native_tail_witness_interval'))
    discharged_bridge_native_tail_witness_width = _coerce_float(discharge_shell.get('discharged_bridge_native_tail_witness_width'))
    if discharged_bridge_native_tail_witness_width is None:
        discharged_bridge_native_tail_witness_width = _coerce_float(discharge_shell.get('identified_bridge_native_tail_witness_width'))

    branch_overlap_interval, branch_overlap_width = _interval_intersection(identified_threshold_branch_interval, overlap_window)
    witness_branch_overlap_interval, witness_branch_overlap_width = _interval_intersection(identified_threshold_branch_interval, discharged_bridge_native_tail_witness_interval)

    upstream_active_assumptions = [str(x) for x in transport_discharge_shell.get('active_assumptions', [])]
    local_active_assumptions: list[str] = []
    active_assumptions = list(upstream_active_assumptions)
    assumptions: list[dict[str, Any]] = []

    hypotheses = _build_hypotheses(
        transport_discharge_shell=transport_discharge_shell,
        workstream_promotion_status=workstream_promotion_status,
        identified_threshold_branch_interval=identified_threshold_branch_interval,
        overlap_window=overlap_window,
        locked_window=locked_window,
        branch_overlap_width=branch_overlap_width,
        witness_branch_overlap_width=witness_branch_overlap_width,
        transport_locked_uniqueness_certificate=uniqueness_cert,
    )
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    residual_burden_summary = _build_residual_burden_summary(
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
        workstream_promotion_status=workstream_promotion_status,
    )

    if not open_hypotheses and not active_assumptions:
        theorem_status = 'golden-theorem-ii-to-v-identification-theorem-discharged'
        notes = (
            'The transport-aware discharge shell is front-complete, the Workstream-A critical-surface/threshold theorem is already available, '
            'and the identified transport-locked branch sits inside the discharged overlap window with surviving bridge-native witness support. '
            'The II->V identification seam is therefore discharged in theorem-facing form.'
        )
    elif not open_hypotheses:
        theorem_status = 'golden-theorem-ii-to-v-identification-theorem-conditional-strong'
        notes = (
            'The local identification implication is now theorem-facing and fully packaged, but one or more upstream assumptions inherited from the transport-aware discharge shell remain active.'
        )
    elif any(row.satisfied for row in hypotheses):
        theorem_status = 'golden-theorem-ii-to-v-identification-theorem-conditional-partial'
        notes = (
            'The final localized compatibility implication has been isolated sharply, but one or more local interval/witness hypotheses remain open.'
        )
    else:
        theorem_status = 'golden-theorem-ii-to-v-identification-theorem-failed'
        notes = 'No usable final localized-compatibility implication theorem could be assembled from the current seam certificates.'

    if witness_branch_overlap_width is not None and theorem_status != 'golden-theorem-ii-to-v-identification-theorem-failed':
        notes += f' Witness/branch overlap width: {float(witness_branch_overlap_width):.6g}.'
    if branch_overlap_width is not None and theorem_status != 'golden-theorem-ii-to-v-identification-theorem-failed':
        notes += f' Branch/overlap-window width: {float(branch_overlap_width):.6g}.'

    return GoldenThresholdIdentificationLocalizedImplicationCertificate(
        rho=float(rho),
        family_label=family_label,
        transport_discharge_shell=transport_discharge_shell,
        threshold_identification_discharge_shell=discharge_shell,
        transport_locked_uniqueness_certificate=uniqueness_cert,
        workstream_promotion_status=workstream_promotion_status,
        overlap_window=overlap_window,
        locked_window=locked_window,
        identified_threshold_branch_interval=identified_threshold_branch_interval,
        identified_branch_inside_overlap_window=_is_subset(identified_threshold_branch_interval, overlap_window),
        identified_branch_inside_locked_window=_is_subset(identified_threshold_branch_interval, locked_window),
        branch_overlap_interval=branch_overlap_interval,
        branch_overlap_width=branch_overlap_width,
        discharged_bridge_native_tail_witness_interval=discharged_bridge_native_tail_witness_interval,
        discharged_bridge_native_tail_witness_width=discharged_bridge_native_tail_witness_width,
        witness_branch_overlap_interval=witness_branch_overlap_interval,
        witness_branch_overlap_width=witness_branch_overlap_width,
        residual_burden_summary=residual_burden_summary,
        hypotheses=hypotheses,
        assumptions=assumptions,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        upstream_active_assumptions=upstream_active_assumptions,
        local_active_assumptions=local_active_assumptions,
        active_assumptions=active_assumptions,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_theorem_ii_to_v_identification_theorem_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    **kwargs: Any,
) -> GoldenThresholdIdentificationLocalizedImplicationCertificate:
    return build_golden_threshold_identification_localized_implication_certificate(
        base_K_values=base_K_values,
        family=family,
        rho=rho,
        **kwargs,
    )


__all__ = [
    'ThresholdIdentificationLocalizedImplicationHypothesisRow',
    'GoldenThresholdIdentificationLocalizedImplicationCertificate',
    'build_golden_threshold_identification_localized_implication_certificate',
    'build_golden_theorem_ii_to_v_identification_theorem_certificate',
]
