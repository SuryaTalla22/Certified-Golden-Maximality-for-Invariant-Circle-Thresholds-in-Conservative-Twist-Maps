from __future__ import annotations

"""Transport-aware discharge packaging for threshold identification.

This stage sharpens the Workstream-fed threshold-identification discharge shell by
feeding in the conditional Theorem-V transport shell.  The previous discharge
stage isolated a still-broad local hinge:

    localized_compatibility_window_identifies_true_irrational_threshold

The current repository already has enough transport-facing structure to say
something more precise.  In the best current theorem-facing form, the role of
Theorem V is to *lock* the identified threshold window to the compatible
transport corridor.  Once that lock is in place, the residual local hinge can
be reduced from a monolithic identification statement to a smaller local
uniqueness statement inside the transport-locked window.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .standard_map import HarmonicFamily
from .theorem_v_transport_lift import build_golden_theorem_v_certificate
from .theorem_v_downstream_utils import (
    extract_theorem_v_gap_preservation_certified,
    extract_theorem_v_gap_preservation_margin,
    extract_theorem_v_status,
    extract_theorem_v_target_interval,
    theorem_v_is_downstream_final,
    unwrap_theorem_v_shell,
)
from .threshold_identification_discharge import (
    RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION,
    build_golden_theorem_ii_to_v_identification_discharge_certificate,
)
from .transport_locked_threshold_uniqueness import (
    build_transport_locked_threshold_uniqueness_certificate,
)

BROAD_TRANSPORT_UNIQUENESS_ASSUMPTION = 'unique_branch_continuation_to_true_irrational_threshold'
RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION = 'unique_true_threshold_branch_inside_transport_locked_window'


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
    if 'conditional-one-variable-strong' in status or 'conditional-two-variable-strong' in status or status.endswith('-conditional-strong') or status.endswith('-strong'):
        return 4
    if status.endswith('-front-complete') or status.endswith('-front-only'):
        return 3
    if status.endswith('-conditional-partial') or status.endswith('-partial') or status.endswith('-moderate'):
        return 2
    if status.endswith('-weak') or status.endswith('-fragile'):
        return 1
    return 0


def _is_front_complete(cert: Mapping[str, Any]) -> bool:
    return _status_rank(str(cert.get('theorem_status', ''))) >= 3 and len(cert.get('open_hypotheses', [])) == 0


def _extract_window(payload: Mapping[str, Any], *keys: str) -> list[float] | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, (list, tuple)) and len(value) == 2 and value[0] is not None and value[1] is not None:
            lo = float(value[0])
            hi = float(value[1])
            if hi >= lo:
                return [lo, hi]
    return None


def _extract_transport_interval(theorem_v_shell: Mapping[str, Any]) -> list[float] | None:
    return extract_theorem_v_target_interval(theorem_v_shell)


def _interval_intersection(a: Sequence[float] | None, b: Sequence[float] | None) -> tuple[list[float] | None, float | None, float | None]:
    if a is None or b is None:
        return None, None, None
    lo = max(float(a[0]), float(b[0]))
    hi = min(float(a[1]), float(b[1]))
    if hi < lo:
        return None, None, None
    width = float(hi - lo)
    center_gap = abs(0.5 * (float(a[0]) + float(a[1])) - 0.5 * (float(b[0]) + float(b[1])))
    return [float(lo), float(hi)], width, float(center_gap)


@dataclass
class ThresholdIdentificationTransportDischargeHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThresholdIdentificationTransportDischargeAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenThresholdIdentificationTransportDischargeCertificate:
    rho: float
    family_label: str
    theorem_v_shell: dict[str, Any]
    threshold_identification_discharge_shell: dict[str, Any]
    theorem_v_final_status: str | None
    transport_target_interval: list[float] | None
    transport_gap_preservation_margin: float | None
    theorem_v_gap_preservation_certified: bool | None
    transport_interval: list[float] | None
    identified_window: list[float] | None
    locked_window: list[float] | None
    locked_window_width: float | None
    center_gap: float | None
    baseline_active_assumptions: list[str]
    reduced_active_assumptions: list[str]
    transport_locked_uniqueness_certificate: dict[str, Any]
    identified_threshold_branch_interval: list[float] | None
    residual_burden_summary: dict[str, Any]
    hypotheses: list[ThresholdIdentificationTransportDischargeHypothesisRow]
    assumptions: list[ThresholdIdentificationTransportDischargeAssumptionRow]
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
            'theorem_v_shell': dict(self.theorem_v_shell),
            'threshold_identification_discharge_shell': dict(self.threshold_identification_discharge_shell),
            'theorem_v_final_status': None if self.theorem_v_final_status is None else str(self.theorem_v_final_status),
            'transport_target_interval': None if self.transport_target_interval is None else [float(x) for x in self.transport_target_interval],
            'transport_gap_preservation_margin': None if self.transport_gap_preservation_margin is None else float(self.transport_gap_preservation_margin),
            'theorem_v_gap_preservation_certified': None if self.theorem_v_gap_preservation_certified is None else bool(self.theorem_v_gap_preservation_certified),
            'transport_interval': None if self.transport_interval is None else [float(x) for x in self.transport_interval],
            'identified_window': None if self.identified_window is None else [float(x) for x in self.identified_window],
            'locked_window': None if self.locked_window is None else [float(x) for x in self.locked_window],
            'locked_window_width': None if self.locked_window_width is None else float(self.locked_window_width),
            'center_gap': None if self.center_gap is None else float(self.center_gap),
            'baseline_active_assumptions': [str(x) for x in self.baseline_active_assumptions],
            'reduced_active_assumptions': [str(x) for x in self.reduced_active_assumptions],
            'transport_locked_uniqueness_certificate': dict(self.transport_locked_uniqueness_certificate),
            'identified_threshold_branch_interval': None if self.identified_threshold_branch_interval is None else [float(x) for x in self.identified_threshold_branch_interval],
            'residual_burden_summary': dict(self.residual_burden_summary),
            'hypotheses': [row.to_dict() for row in self.hypotheses],
            'assumptions': [row.to_dict() for row in self.assumptions],
            'discharged_hypotheses': [str(x) for x in self.discharged_hypotheses],
            'open_hypotheses': [str(x) for x in self.open_hypotheses],
            'upstream_active_assumptions': [str(x) for x in self.upstream_active_assumptions],
            'local_active_assumptions': [str(x) for x in self.local_active_assumptions],
            'active_assumptions': [str(x) for x in self.active_assumptions],
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


def _build_assumptions(*, assume_unique_true_threshold_branch_inside_transport_locked_window: bool, transport_locked_uniqueness_certified: bool = False) -> list[ThresholdIdentificationTransportDischargeAssumptionRow]:
    return [
        ThresholdIdentificationTransportDischargeAssumptionRow(
            name=RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION,
            assumed=bool(assume_unique_true_threshold_branch_inside_transport_locked_window or transport_locked_uniqueness_certified),
            source='transport-aware identification discharge assumption',
            note=(
                'After locking the identified threshold window to the transport-compatible corridor, only a local uniqueness statement '
                'for the true threshold branch inside that locked window remains to promote identification. '
                'When the dedicated transport-locked uniqueness certificate is strong, this local hinge is discharged rather than merely assumed.'
            ),
        )
    ]


def _build_hypotheses(
    theorem_v_shell: Mapping[str, Any],
    discharge_shell: Mapping[str, Any],
    transport_interval: Sequence[float] | None,
    identified_window: Sequence[float] | None,
    locked_window: Sequence[float] | None,
    locked_window_width: float | None,
    center_gap: float | None,
    baseline_active_assumptions: Sequence[str],
    reduced_active_assumptions: Sequence[str],
    transport_locked_uniqueness_certificate: Mapping[str, Any] | None = None,
) -> list[ThresholdIdentificationTransportDischargeHypothesisRow]:
    lock_margin = None
    locked_by_transport = False
    if transport_interval is not None and identified_window is not None:
        lock_margin = min(float(identified_window[0]) - float(transport_interval[0]), float(transport_interval[1]) - float(identified_window[1]))
        locked_by_transport = lock_margin >= -1e-15
    reduction = float(len(baseline_active_assumptions) - len(reduced_active_assumptions))
    return [
        ThresholdIdentificationTransportDischargeHypothesisRow(
            name='theorem_v_transport_front_complete',
            satisfied=bool(_is_front_complete(theorem_v_shell) or theorem_v_is_downstream_final(theorem_v_shell)),
            source='Theorem-V transport lift',
            note='The conditional Theorem-V transport shell is front-complete before transport-aware discharge is applied.',
            margin=None,
        ),
        ThresholdIdentificationTransportDischargeHypothesisRow(
            name='threshold_identification_discharge_front_complete',
            satisfied=_is_front_complete(discharge_shell),
            source='threshold-identification discharge lift',
            note='The Workstream-fed threshold-identification discharge shell is front-complete before transport-aware discharge is applied.',
            margin=None,
        ),
        ThresholdIdentificationTransportDischargeHypothesisRow(
            name='identified_window_locked_by_transport_interval',
            satisfied=bool(locked_by_transport),
            source='comparison of identified window with Theorem-V compatible interval',
            note='The identified threshold window sits inside the compatible transport interval, so the transport corridor locks the identification window.',
            margin=None if lock_margin is None else float(lock_margin),
        ),
        ThresholdIdentificationTransportDischargeHypothesisRow(
            name='transport_lock_window_nonempty',
            satisfied=bool(locked_window is not None),
            source='transport/identification interval intersection',
            note='The transport-compatible interval and the identified window have a nonempty common locked window.',
            margin=None if locked_window_width is None else float(locked_window_width),
        ),
        ThresholdIdentificationTransportDischargeHypothesisRow(
            name='transport_identification_center_consistent',
            satisfied=bool(center_gap is None or (locked_window is not None and center_gap <= 0.5 * ((transport_interval[1] - transport_interval[0]) + (identified_window[1] - identified_window[0])) + 1e-15)),
            source='transport/identification center comparison',
            note='The centers of the transport-compatible interval and identified window are mutually consistent on the threshold axis.',
            margin=None if center_gap is None else float(center_gap),
        ),
        ThresholdIdentificationTransportDischargeHypothesisRow(
            name='broader_identification_hinge_reduced_to_locked_window_uniqueness',
            satisfied=(
                (RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION in baseline_active_assumptions and locked_window is not None and reduction >= 0.0)
                or bool((transport_locked_uniqueness_certificate or {}).get('threshold_identification_ready', False))
            ),
            source='transport-aware discharge packaging',
            note='The monolithic local identification hinge and the broader Theorem-V uniqueness assumption have been replaced downstream by a smaller local uniqueness hinge on the transport-locked window.',
            margin=reduction,
        ),
        ThresholdIdentificationTransportDischargeHypothesisRow(
            name='transport_locked_uniqueness_certificate_strengthened',
            satisfied=bool(str((transport_locked_uniqueness_certificate or {}).get('theorem_status', '')).endswith('-conditional-strong')),
            source='transport-locked-threshold-uniqueness certificate',
            note='The dedicated transport-locked uniqueness certificate has collapsed the late transport chain to a single admissible branch inside the locked window.',
            margin=None if transport_locked_uniqueness_certificate is None else float(((transport_locked_uniqueness_certificate or {}).get('uniqueness_margin') or 0.0)),
        ),
        ThresholdIdentificationTransportDischargeHypothesisRow(
            name='transport_locked_branch_identifies_true_threshold_object',
            satisfied=bool((transport_locked_uniqueness_certificate or {}).get('threshold_identification_ready', False)),
            source='transport-locked threshold-branch promotion',
            note='The transport-locked witness is now tight enough to identify the selected threshold branch inside the locked window rather than only certify local uniqueness.',
            margin=None if transport_locked_uniqueness_certificate is None else float(((transport_locked_uniqueness_certificate or {}).get('threshold_identification_margin') or 0.0)),
        ),
    ]


def _build_residual_burden_summary(
    *,
    open_hypotheses: Sequence[str],
    local_active_assumptions: Sequence[str],
    upstream_active_assumptions: Sequence[str],
    transport_locked_uniqueness_certificate: Mapping[str, Any],
    upstream_discharge_residual_burden_status: str | None = None,
) -> dict[str, Any]:
    local_front_hypotheses = [
        str(x)
        for x in open_hypotheses
        if str(x) not in {'transport_locked_uniqueness_certificate_strengthened', 'transport_locked_branch_identifies_true_threshold_object'}
    ]
    local_uniqueness_assumptions = [
        str(x) for x in local_active_assumptions if str(x) == RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION
    ]
    upstream_theorem_assumptions = [str(x) for x in upstream_active_assumptions]
    threshold_identification_ready = bool(transport_locked_uniqueness_certificate.get('threshold_identification_ready', False))
    residual_identification_obstruction = transport_locked_uniqueness_certificate.get('residual_identification_obstruction')
    if threshold_identification_ready and not local_front_hypotheses and not local_uniqueness_assumptions and not upstream_theorem_assumptions:
        status = 'transport-locked-identification-ready'
    elif threshold_identification_ready and not local_front_hypotheses and not local_uniqueness_assumptions:
        if upstream_discharge_residual_burden_status in {'critical-surface-threshold-promotion-theorem-frontier', 'critical-surface-threshold-promotion-frontier'}:
            status = str(upstream_discharge_residual_burden_status)
        elif upstream_discharge_residual_burden_status in {'critical-surface-threshold-promotion-theorem-available', 'critical-surface-threshold-promotion-theorem-conditional-strong', 'critical-surface-threshold-promotion-theorem-discharged'}:
            status = 'transport-locked-identification-ready'
        else:
            status = 'critical-surface-threshold-identification-frontier'
    elif local_front_hypotheses or local_uniqueness_assumptions:
        status = 'transport-locked-local-uniqueness-frontier'
    else:
        status = 'mixed-local-and-upstream-identification-burden'
    return {
        'status': status,
        'local_front_hypotheses': local_front_hypotheses,
        'local_uniqueness_assumptions': local_uniqueness_assumptions,
        'upstream_theorem_assumptions': upstream_theorem_assumptions,
        'transport_locked_threshold_identification_ready': threshold_identification_ready,
        'identified_threshold_branch_interval': None if transport_locked_uniqueness_certificate.get('threshold_identification_interval') is None else [float(x) for x in transport_locked_uniqueness_certificate.get('threshold_identification_interval')],
        'residual_identification_obstruction': None if residual_identification_obstruction is None else str(residual_identification_obstruction),
        'transport_locked_uniqueness_status': None if transport_locked_uniqueness_certificate.get('theorem_status') is None else str(transport_locked_uniqueness_certificate.get('theorem_status')),
        'transport_locked_uniqueness_margin': None if transport_locked_uniqueness_certificate.get('uniqueness_margin') is None else float(transport_locked_uniqueness_certificate.get('uniqueness_margin')),
        'transport_locked_threshold_identification_margin': None if transport_locked_uniqueness_certificate.get('threshold_identification_margin') is None else float(transport_locked_uniqueness_certificate.get('threshold_identification_margin')),
    }


def build_golden_threshold_identification_transport_discharge_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    theorem_v_certificate: Mapping[str, Any] | None = None,
    threshold_identification_discharge_certificate: Mapping[str, Any] | None = None,
    transport_locked_uniqueness_certificate: Mapping[str, Any] | None = None,
    assume_unique_true_threshold_branch_inside_transport_locked_window: bool = False,
    **kwargs: Any,
) -> GoldenThresholdIdentificationTransportDischargeCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)
    rho = float(golden_inverse() if rho is None else rho)

    if theorem_v_certificate is not None:
        theorem_v_input = dict(theorem_v_certificate)
        theorem_v_shell = theorem_v_input if theorem_v_is_downstream_final(theorem_v_input) else unwrap_theorem_v_shell(theorem_v_input)
    else:
        theorem_v_shell = build_golden_theorem_v_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_v_certificate, kwargs),
        ).to_dict()

    if threshold_identification_discharge_certificate is not None:
        discharge_shell = dict(threshold_identification_discharge_certificate)
    else:
        discharge_shell = build_golden_theorem_ii_to_v_identification_discharge_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_ii_to_v_identification_discharge_certificate, kwargs),
        ).to_dict()

    theorem_v_final_status = extract_theorem_v_status(theorem_v_certificate if theorem_v_certificate is not None else theorem_v_shell)
    transport_target_interval = _extract_transport_interval(theorem_v_certificate if theorem_v_certificate is not None else theorem_v_shell)
    transport_gap_preservation_margin = extract_theorem_v_gap_preservation_margin(theorem_v_certificate if theorem_v_certificate is not None else theorem_v_shell)
    theorem_v_gap_preservation_certified = extract_theorem_v_gap_preservation_certified(theorem_v_certificate if theorem_v_certificate is not None else theorem_v_shell)
    transport_interval = transport_target_interval
    identified_window = _extract_window(discharge_shell, 'identified_window', 'validated_window')
    locked_window, locked_window_width, center_gap = _interval_intersection(transport_interval, identified_window)

    if transport_locked_uniqueness_certificate is not None:
        uniqueness_cert = dict(transport_locked_uniqueness_certificate)
    else:
        uniqueness_cert = build_transport_locked_threshold_uniqueness_certificate(
            theorem_v_certificate=theorem_v_shell,
            transport_interval=transport_interval,
            identified_window=identified_window,
            locked_window=locked_window,
        ).to_dict()
    transport_locked_uniqueness_certified = bool(uniqueness_cert.get('threshold_identification_ready', False)) or str(uniqueness_cert.get('theorem_status', '')).endswith('-conditional-strong')

    baseline_active_assumptions = sorted({
        *(str(x) for x in theorem_v_shell.get('active_assumptions', [])),
        *(str(x) for x in discharge_shell.get('active_assumptions', [])),
    })
    upstream_active_assumptions = sorted({
        *(str(x) for x in discharge_shell.get('upstream_active_assumptions', [])),
        *(str(x) for x in theorem_v_shell.get('active_assumptions', []) if str(x) != BROAD_TRANSPORT_UNIQUENESS_ASSUMPTION),
    })
    assumptions = _build_assumptions(
        assume_unique_true_threshold_branch_inside_transport_locked_window=assume_unique_true_threshold_branch_inside_transport_locked_window,
        transport_locked_uniqueness_certified=transport_locked_uniqueness_certified,
    )
    local_active_assumptions = [row.name for row in assumptions if not row.assumed]
    active_assumptions = sorted(set(upstream_active_assumptions) | set(local_active_assumptions))
    reduced_active_assumptions = list(active_assumptions)

    hypotheses = _build_hypotheses(
        theorem_v_shell=theorem_v_shell,
        discharge_shell=discharge_shell,
        transport_interval=transport_interval,
        identified_window=identified_window,
        locked_window=locked_window,
        locked_window_width=locked_window_width,
        center_gap=center_gap,
        baseline_active_assumptions=baseline_active_assumptions,
        reduced_active_assumptions=reduced_active_assumptions,
        transport_locked_uniqueness_certificate=uniqueness_cert,
    )
    informative_only_hypotheses = {'transport_locked_uniqueness_certificate_strengthened', 'transport_locked_branch_identifies_true_threshold_object'}
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if (not row.satisfied and row.name not in informative_only_hypotheses)]
    residual_burden_summary = _build_residual_burden_summary(
        open_hypotheses=open_hypotheses,
        local_active_assumptions=local_active_assumptions,
        upstream_active_assumptions=upstream_active_assumptions,
        transport_locked_uniqueness_certificate=uniqueness_cert,
        upstream_discharge_residual_burden_status=None if discharge_shell.get('residual_burden_summary') is None else str(dict(discharge_shell.get('residual_burden_summary', {})).get('status')) if dict(discharge_shell.get('residual_burden_summary', {})).get('status') is not None else None,
    )

    front_packaged = not open_hypotheses
    if front_packaged and not local_active_assumptions:
        theorem_status = 'golden-threshold-identification-transport-discharge-lift-conditional-strong'
        notes = (
            'The Workstream-fed identification shell and the Theorem-V transport shell now assemble into a transport-aware discharge package. '
            'The identified window is locked by the transport corridor, and the dedicated transport-locked uniqueness certificate discharges the residual local uniqueness hinge.'
        )
        if bool(uniqueness_cert.get('threshold_identification_ready', False)):
            notes += ' The same witness now serves as a threshold-branch identification certificate inside the locked window.'
    elif front_packaged:
        theorem_status = 'golden-threshold-identification-transport-discharge-lift-front-complete'
        notes = (
            'The identified threshold window is now transport-locked, so the residual local identification burden has been sharpened '
            'from a monolithic compatibility-to-threshold statement to uniqueness inside the transport-locked window. '
            'That hinge remains active unless the dedicated transport-locked uniqueness certificate closes it.'
        )
    elif _status_rank(str(theorem_v_shell.get('theorem_status', ''))) >= 1 or _status_rank(str(discharge_shell.get('theorem_status', ''))) >= 1:
        theorem_status = 'golden-threshold-identification-transport-discharge-lift-conditional-partial'
        notes = (
            'A transport-aware discharge package has been assembled, but either the Theorem-V transport shell, the Workstream-fed identification shell, '
            'or the transport-lock diagnostics remain only partial.'
        )
    else:
        theorem_status = 'golden-threshold-identification-transport-discharge-lift-failed'
        notes = 'No usable transport-aware identification discharge package was assembled from the current certificates.'

    if theorem_v_final_status is not None and theorem_status != 'golden-threshold-identification-transport-discharge-lift-failed':
        notes += f' Consumed Theorem-V status: {str(theorem_v_final_status)}.'
        if transport_gap_preservation_margin is not None:
            notes += f' Transport gap-preservation margin: {float(transport_gap_preservation_margin):.6g}.'

    return GoldenThresholdIdentificationTransportDischargeCertificate(
        rho=float(rho),
        family_label=family_label,
        theorem_v_shell=theorem_v_shell,
        threshold_identification_discharge_shell=discharge_shell,
        theorem_v_final_status=theorem_v_final_status,
        transport_target_interval=transport_target_interval,
        transport_gap_preservation_margin=None if transport_gap_preservation_margin is None else float(transport_gap_preservation_margin),
        theorem_v_gap_preservation_certified=theorem_v_gap_preservation_certified,
        transport_interval=transport_interval,
        identified_window=identified_window,
        locked_window=locked_window,
        locked_window_width=locked_window_width,
        center_gap=center_gap,
        baseline_active_assumptions=baseline_active_assumptions,
        reduced_active_assumptions=reduced_active_assumptions,
        transport_locked_uniqueness_certificate=uniqueness_cert,
        identified_threshold_branch_interval=None if uniqueness_cert.get('threshold_identification_interval') is None else [float(x) for x in uniqueness_cert.get('threshold_identification_interval')],
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


def build_golden_theorem_ii_to_v_identification_transport_discharge_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    **kwargs: Any,
) -> GoldenThresholdIdentificationTransportDischargeCertificate:
    return build_golden_threshold_identification_transport_discharge_certificate(
        base_K_values=base_K_values,
        family=family,
        rho=rho,
        **kwargs,
    )


__all__ = [
    'BROAD_TRANSPORT_UNIQUENESS_ASSUMPTION',
    'RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION',
    'ThresholdIdentificationTransportDischargeHypothesisRow',
    'ThresholdIdentificationTransportDischargeAssumptionRow',
    'GoldenThresholdIdentificationTransportDischargeCertificate',
    'build_golden_threshold_identification_transport_discharge_certificate',
    'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate',
]
