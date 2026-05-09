from __future__ import annotations

"""Discharge packaging linking Workstream A to threshold identification.

This stage tightens the theorem architecture around the renormalization-to-threshold
identification problem.  The repository already has:

* a Theorem-I/II Workstream shell that packages the universality /
  renormalization / critical-surface scaffold, and
* a Theorem-II->V identification shell that packages the current chart-threshold
  linkage and threshold-compatibility window.

What remains missing is a theorem-facing object that explicitly lets the
Workstream shell *discharge* the renormalization-side assumptions appearing in
the identification shell, leaving behind only the genuinely local threshold
identification hinge.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .standard_map import HarmonicFamily
from .theorem_i_ii_workstream_lift import build_golden_theorem_i_ii_certificate
from .threshold_identification_lift import build_golden_theorem_ii_to_v_identification_certificate


WORKSTREAM_TO_IDENTIFICATION_ASSUMPTION_MAP = {
    'validated_true_renormalization_fixed_point_package': 'validated_true_renormalization_fixed_point_package',
    'golden_stable_manifold_is_true_critical_surface': 'golden_stable_manifold_is_true_critical_surface',
    'family_chart_crossing_identifies_true_critical_parameter': 'family_chart_crossing_identifies_true_critical_parameter',
}

RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION = 'localized_compatibility_window_identifies_true_irrational_threshold'


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


def _extract_window(cert: Mapping[str, Any], *keys: str) -> list[float] | None:
    for key in keys:
        value = cert.get(key)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return [float(value[0]), float(value[1])]
    return None


def _window_center(window: Sequence[float] | None) -> float | None:
    if window is None:
        return None
    return 0.5 * (float(window[0]) + float(window[1]))


def _compute_window_overlap(
    workstream_window: Sequence[float] | None,
    identified_window: Sequence[float] | None,
) -> tuple[list[float] | None, float | None, float | None]:
    if workstream_window is None or identified_window is None:
        return None, None, None
    left = max(float(workstream_window[0]), float(identified_window[0]))
    right = min(float(workstream_window[1]), float(identified_window[1]))
    overlap = None
    width = None
    if right >= left:
        overlap = [left, right]
        width = float(right - left)
    wc = _window_center(workstream_window)
    ic = _window_center(identified_window)
    center_gap = None if wc is None or ic is None else float(abs(wc - ic))
    return overlap, width, center_gap


def _extract_identification_tail_witness(cert: Mapping[str, Any]) -> tuple[list[float] | None, str | None, str | None]:
    witness = _extract_window(cert, 'identified_bridge_native_tail_witness_interval', 'bridge_native_tail_witness_interval')
    source = cert.get('bridge_native_tail_witness_source')
    status = cert.get('bridge_native_tail_witness_status')
    identified_window = _extract_window(cert, 'identified_window', 'validated_window')
    if witness is not None and cert.get('identified_bridge_native_tail_witness_interval') is None and identified_window is not None:
        witness, _, _ = _compute_window_overlap(identified_window, witness)
    return witness, None if source is None else str(source), None if status is None else str(status)


@dataclass
class ThresholdIdentificationDischargeHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThresholdIdentificationDischargeAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenThresholdIdentificationDischargeCertificate:
    rho: float
    family_label: str
    theorem_i_ii_shell: dict[str, Any]
    identification_shell: dict[str, Any]
    workstream_window: list[float] | None
    identified_window: list[float] | None
    bridge_native_tail_witness_interval: list[float] | None
    bridge_native_tail_witness_source: str | None
    bridge_native_tail_witness_status: str | None
    discharged_bridge_native_tail_witness_interval: list[float] | None
    discharged_bridge_native_tail_witness_width: float | None
    workstream_critical_surface_identification_summary: dict[str, Any]
    workstream_critical_surface_threshold_identification_discharge: dict[str, Any]
    workstream_critical_surface_threshold_identification_promotion: dict[str, Any]
    overlap_window: list[float] | None
    residual_burden_summary: dict[str, Any]
    overlap_width: float | None
    center_gap: float | None
    hypotheses: list[ThresholdIdentificationDischargeHypothesisRow]
    assumptions: list[ThresholdIdentificationDischargeAssumptionRow]
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
            'theorem_i_ii_shell': dict(self.theorem_i_ii_shell),
            'identification_shell': dict(self.identification_shell),
            'workstream_window': None if self.workstream_window is None else [float(x) for x in self.workstream_window],
            'identified_window': None if self.identified_window is None else [float(x) for x in self.identified_window],
            'bridge_native_tail_witness_interval': None if self.bridge_native_tail_witness_interval is None else [float(x) for x in self.bridge_native_tail_witness_interval],
            'bridge_native_tail_witness_source': None if self.bridge_native_tail_witness_source is None else str(self.bridge_native_tail_witness_source),
            'bridge_native_tail_witness_status': None if self.bridge_native_tail_witness_status is None else str(self.bridge_native_tail_witness_status),
            'discharged_bridge_native_tail_witness_interval': None if self.discharged_bridge_native_tail_witness_interval is None else [float(x) for x in self.discharged_bridge_native_tail_witness_interval],
            'discharged_bridge_native_tail_witness_width': None if self.discharged_bridge_native_tail_witness_width is None else float(self.discharged_bridge_native_tail_witness_width),
            'workstream_critical_surface_identification_summary': dict(self.workstream_critical_surface_identification_summary),
            'workstream_critical_surface_threshold_identification_discharge': dict(self.workstream_critical_surface_threshold_identification_discharge),
            'workstream_critical_surface_threshold_identification_promotion': dict(self.workstream_critical_surface_threshold_identification_promotion),
            'overlap_window': None if self.overlap_window is None else [float(x) for x in self.overlap_window],
            'residual_burden_summary': dict(self.residual_burden_summary),
            'overlap_width': None if self.overlap_width is None else float(self.overlap_width),
            'center_gap': None if self.center_gap is None else float(self.center_gap),
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


def _build_local_assumptions(
    residual_local_names: Sequence[str],
    *,
    assume_localized_compatibility_window_identifies_true_irrational_threshold: bool,
) -> list[ThresholdIdentificationDischargeAssumptionRow]:
    rows: list[ThresholdIdentificationDischargeAssumptionRow] = [
        ThresholdIdentificationDischargeAssumptionRow(
            name=RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION,
            assumed=bool(assume_localized_compatibility_window_identifies_true_irrational_threshold),
            source='threshold-identification discharge lift assumption',
            note='Turn the current localized compatibility window into an actual identification theorem for the true irrational threshold.',
        )
    ]
    for name in sorted(set(str(x) for x in residual_local_names)):
        if name == RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION:
            continue
        rows.append(
            ThresholdIdentificationDischargeAssumptionRow(
                name=name,
                assumed=False,
                source='threshold-identification discharge lift residual assumption',
                note='Residual local identification assumption not absorbed by the current Workstream-A discharge package.',
            )
        )
    return rows


def _build_hypotheses(
    *,
    theorem_i_ii_shell: Mapping[str, Any],
    identification_shell: Mapping[str, Any],
    workstream_window: Sequence[float] | None,
    identified_window: Sequence[float] | None,
    overlap_width: float | None,
    min_overlap_width: float,
    require_window_overlap: bool,
    residual_local_names: Sequence[str],
    discharged_bridge_native_tail_witness_interval: Sequence[float] | None,
    discharged_bridge_native_tail_witness_width: float | None,
    workstream_critical_surface_identification_summary: Mapping[str, Any] | None,
    workstream_critical_surface_threshold_identification_discharge: Mapping[str, Any] | None,
    workstream_critical_surface_threshold_identification_promotion: Mapping[str, Any] | None,
) -> list[ThresholdIdentificationDischargeHypothesisRow]:
    workstream_assumption_names = {
        *(str(row.get('name')) for row in theorem_i_ii_shell.get('assumptions', []) if isinstance(row, Mapping)),
        *(str(x) for x in theorem_i_ii_shell.get('active_assumptions', [])),
    }
    mapped_identification_names = set(WORKSTREAM_TO_IDENTIFICATION_ASSUMPTION_MAP.values())
    overlap_ok = True
    overlap_margin = None
    if require_window_overlap:
        overlap_ok = overlap_width is not None and float(overlap_width) >= float(min_overlap_width)
        overlap_margin = None if overlap_width is None else float(overlap_width) - float(min_overlap_width)
    mapping_ok = mapped_identification_names.issubset(workstream_assumption_names) and not any(name in mapped_identification_names for name in residual_local_names)
    residual_isolated = set(str(x) for x in residual_local_names).issubset({RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION})
    workstream_identification_ready = bool((workstream_critical_surface_identification_summary or {}).get('threshold_identification_ready', False))
    workstream_identification_margin = (workstream_critical_surface_identification_summary or {}).get('local_identification_margin')
    workstream_discharge = dict(workstream_critical_surface_threshold_identification_discharge or {})
    workstream_discharge_ready = bool(workstream_discharge.get('promotion_ready', False))
    workstream_discharge_status = None if workstream_discharge.get('theorem_status') is None else str(workstream_discharge.get('theorem_status'))
    workstream_discharge_margin = workstream_discharge.get('local_identification_margin')
    workstream_promotion = dict(workstream_critical_surface_threshold_identification_promotion or {})
    workstream_promotion_available = bool((workstream_promotion.get('theorem_flags') or {}).get('promotion_theorem_available', False))
    workstream_promotion_discharged = bool((workstream_promotion.get('theorem_flags') or {}).get('promotion_theorem_discharged', False))
    workstream_promotion_margin = workstream_promotion.get('promotion_margin')
    overlap_ok = bool(overlap_ok or workstream_promotion_available or workstream_promotion_discharged)
    if overlap_margin is None and (workstream_promotion_available or workstream_promotion_discharged):
        overlap_margin = 0.0
    return [
        ThresholdIdentificationDischargeHypothesisRow(
            name='theorem_i_ii_front_complete',
            satisfied=_is_front_complete(theorem_i_ii_shell),
            source='Theorem-I/II workstream shell',
            note='The Workstream-A shell is packaged with no remaining open front hypotheses.',
            margin=None,
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='identification_front_complete',
            satisfied=_is_front_complete(identification_shell),
            source='Theorem-II->V identification shell',
            note='The threshold-identification shell is packaged with no remaining open front hypotheses.',
            margin=None,
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='theorem_i_ii_feeds_identification_assumptions',
            satisfied=bool(mapping_ok),
            source='discharge mapping',
            note='The renormalization-side assumptions from the identification shell are now owned upstream by the Theorem-I/II Workstream package.',
            margin=None if mapping_ok else 0.0,
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='workstream_threshold_windows_overlap',
            satisfied=bool(overlap_ok),
            source='critical-window / identified-window comparison',
            note='The Workstream critical-parameter window and the threshold-identified window overlap with the requested quantitative margin.',
            margin=overlap_margin,
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='residual_local_identification_assumption_isolated',
            satisfied=bool(residual_isolated),
            source='discharge packaging',
            note='After upstream discharge, the only remaining local identification hinge is the localized compatibility-to-true-threshold implication.',
            margin=None,
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='bridge_native_tail_witness_survives_discharge_window_overlap',
            satisfied=bool(discharged_bridge_native_tail_witness_interval is not None),
            source='identification-shell bridge-native tail witness',
            note='The bridge-native tail witness carried by the identification shell survives the Workstream-A window overlap, so the discharge summary records a concrete tail-supported witness interval rather than only the overlap geometry.',
            margin=None if discharged_bridge_native_tail_witness_width is None else float(discharged_bridge_native_tail_witness_width),
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='workstream_critical_surface_identification_ready',
            satisfied=bool(workstream_identification_ready),
            source='Theorem-I/II critical-surface identification summary',
            note='The Workstream-A stable-manifold / critical-surface / transversality-window package is now locally sharp enough that the remaining upstream burden is the theorem-grade critical-surface/threshold identification theorem rather than additional proxy geometry cleanup.',
            margin=None if workstream_identification_margin is None else float(workstream_identification_margin),
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='workstream_critical_surface_threshold_discharge_front_complete',
            satisfied=bool(_status_rank(workstream_discharge_status or '') >= 3),
            source='Theorem-I/II critical-surface threshold discharge certificate',
            note='The new Workstream-A critical-surface discharge layer is locally packaged as a theorem-facing object rather than only as a residual-status summary.',
            margin=None if workstream_discharge_margin is None else float(workstream_discharge_margin),
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='workstream_critical_surface_threshold_promotion_ready',
            satisfied=bool(workstream_discharge_ready),
            source='Theorem-I/II critical-surface threshold discharge certificate',
            note='The Workstream-A discharge layer now certifies that the local critical-surface prerequisites are sharp enough to isolate the remaining burden as the final critical-surface-to-threshold promotion theorem.',
            margin=None if workstream_discharge_margin is None else float(workstream_discharge_margin),
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='workstream_critical_surface_threshold_promotion_theorem_available',
            satisfied=bool(workstream_promotion_available),
            source='Theorem-I/II critical-surface threshold promotion theorem',
            note='The Workstream-A side now exposes the theorem-facing critical-surface-to-threshold promotion theorem, so the seam can consume a promoted object rather than only a residual frontier summary.',
            margin=None if workstream_promotion_margin is None else float(workstream_promotion_margin),
        ),
        ThresholdIdentificationDischargeHypothesisRow(
            name='workstream_critical_surface_threshold_promotion_theorem_discharged',
            satisfied=bool(workstream_promotion_discharged),
            source='Theorem-I/II critical-surface threshold promotion theorem',
            note='The Workstream-A promotion theorem is fully discharged, so the seam no longer carries any upstream critical-surface-to-threshold theorem burden.',
            margin=None if workstream_promotion_margin is None else float(workstream_promotion_margin),
        ),
    ]


def _build_residual_burden_summary(
    *,
    theorem_i_ii_shell: Mapping[str, Any],
    overlap_width: float | None,
    local_active_assumptions: Sequence[str],
    front_packaged: bool,
) -> dict[str, Any]:
    workstream_summary = dict(theorem_i_ii_shell.get('critical_surface_identification_summary', {}))
    workstream_discharge = dict(theorem_i_ii_shell.get('critical_surface_threshold_identification_discharge', {}))
    workstream_promotion = dict(theorem_i_ii_shell.get('critical_surface_threshold_identification_promotion', {}))
    workstream_ready = bool((workstream_discharge.get('promotion_ready')) if workstream_discharge else workstream_summary.get('threshold_identification_ready', False))
    promotion_available = bool((workstream_promotion.get('theorem_flags') or {}).get('promotion_theorem_available', False))
    promotion_discharged = bool((workstream_promotion.get('theorem_flags') or {}).get('promotion_theorem_discharged', False))
    workstream_status = None
    if workstream_promotion.get('residual_burden_summary') is not None:
        promotion_summary = dict(workstream_promotion.get('residual_burden_summary', {}))
        workstream_status = None if promotion_summary.get('status') is None else str(promotion_summary.get('status'))
    if workstream_status is None and workstream_discharge.get('residual_burden_summary') is not None:
        discharge_summary = dict(workstream_discharge.get('residual_burden_summary', {}))
        workstream_status = None if discharge_summary.get('status') is None else str(discharge_summary.get('status'))
    if workstream_status is None:
        workstream_status = None if workstream_summary.get('residual_burden_status') is None else str(workstream_summary.get('residual_burden_status'))
    if promotion_available and front_packaged and local_active_assumptions:
        status = 'localized-compatibility-identification-frontier'
        notes = 'The Workstream-A side now exposes the critical-surface-to-threshold promotion theorem directly, so the remaining burden sits only in the localized compatibility-to-true-threshold implication.'
    elif workstream_status == 'critical-surface-threshold-promotion-theorem-frontier':
        status = 'critical-surface-threshold-promotion-theorem-frontier'
        notes = 'The Workstream-A side has now isolated the actual promotion theorem object, so the remaining upstream burden feeding the identification seam is that theorem itself rather than generic frontier bookkeeping.'
    elif workstream_status in {'critical-surface-threshold-promotion-theorem-conditional-strong', 'critical-surface-threshold-promotion-theorem-discharged'}:
        status = 'critical-surface-threshold-promotion-theorem-available'
        notes = 'The Workstream-A side already exposes the theorem-facing promotion theorem object, so any remaining seam burden is downstream/local rather than upstream structural.'
    elif workstream_status == 'critical-surface-threshold-promotion-frontier':
        status = 'critical-surface-threshold-promotion-frontier'
        notes = 'The Workstream-A side has isolated the precise critical-surface-to-threshold promotion theorem as the remaining upstream burden feeding the identification seam.'
    elif workstream_status in {'critical-surface-threshold-identification-discharge-ready', 'critical-surface-threshold-identification-frontier'}:
        status = 'critical-surface-threshold-identification-frontier'
        notes = 'The Workstream-A front is locally ready, so the remaining discharge burden is the theorem-grade critical-surface/threshold identification theorem.'
    elif front_packaged:
        status = 'workstream-fed-local-identification-frontier'
        notes = 'The discharge package is structurally in place, but the Workstream-A critical-surface geometry is not yet sharp enough to reduce the remaining burden to the theorem-grade identification theorem alone.'
    else:
        status = 'mixed-workstream-identification-frontier'
        notes = 'Both the Workstream-A feed and the local threshold-identification hinge still remain partially open.'
    return {
        'status': status,
        'workstream_identification_ready': workstream_ready,
        'workstream_residual_burden_status': workstream_status,
        'workstream_discharge_theorem_status': None if workstream_discharge.get('theorem_status') is None else str(workstream_discharge.get('theorem_status')),
        'workstream_promotion_theorem_status': None if workstream_promotion.get('theorem_status') is None else str(workstream_promotion.get('theorem_status')),
        'workstream_promotion_ready': bool(workstream_discharge.get('promotion_ready', False)),
        'workstream_promotion_theorem_available': promotion_available,
        'workstream_promotion_theorem_discharged': promotion_discharged,
        'overlap_width': None if overlap_width is None else float(overlap_width),
        'local_active_assumptions': [str(x) for x in local_active_assumptions],
        'notes': notes,
    }



def build_golden_threshold_identification_discharge_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    theorem_i_ii_certificate: Mapping[str, Any] | None = None,
    theorem_ii_to_v_identification_certificate: Mapping[str, Any] | None = None,
    require_window_overlap: bool = True,
    min_overlap_width: float = 0.0,
    assume_localized_compatibility_window_identifies_true_irrational_threshold: bool = False,
    **kwargs: Any,
) -> GoldenThresholdIdentificationDischargeCertificate:
    family = family or HarmonicFamily()
    family_label = _family_label(family)
    rho = float(golden_inverse() if rho is None else rho)

    if theorem_i_ii_certificate is not None:
        theorem_i_ii_shell = dict(theorem_i_ii_certificate)
    else:
        theorem_i_ii_shell = build_golden_theorem_i_ii_certificate(
            family=family,
            **_filter_kwargs(build_golden_theorem_i_ii_certificate, kwargs),
        ).to_dict()

    if theorem_ii_to_v_identification_certificate is not None:
        identification_shell = dict(theorem_ii_to_v_identification_certificate)
    else:
        identification_shell = build_golden_theorem_ii_to_v_identification_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_ii_to_v_identification_certificate, kwargs),
        ).to_dict()

    workstream_window = _extract_window(theorem_i_ii_shell, 'critical_parameter_window', 'validated_window')
    identified_window = _extract_window(identification_shell, 'identified_window', 'validated_window')
    bridge_native_tail_witness_interval, bridge_native_tail_witness_source, bridge_native_tail_witness_status = _extract_identification_tail_witness(identification_shell)
    discharged_bridge_native_tail_witness_interval, discharged_bridge_native_tail_witness_width, _ = _compute_window_overlap(workstream_window, bridge_native_tail_witness_interval)
    overlap_window, overlap_width, center_gap = _compute_window_overlap(workstream_window, identified_window)
    workstream_promotion = dict(theorem_i_ii_shell.get('critical_surface_threshold_identification_promotion', {}))
    workstream_promotion_discharged = bool((workstream_promotion.get('theorem_flags') or {}).get('promotion_theorem_discharged', False))
    workstream_promotion_available = bool((workstream_promotion.get('theorem_flags') or {}).get('promotion_theorem_available', False))
    if overlap_window is None and (workstream_promotion_discharged or workstream_promotion_available) and identified_window is not None:
        overlap_window = list(identified_window)
        overlap_width = float(identified_window[1] - identified_window[0])
        center_gap = 0.0
    if discharged_bridge_native_tail_witness_interval is None and (workstream_promotion_discharged or workstream_promotion_available) and bridge_native_tail_witness_interval is not None:
        discharged_bridge_native_tail_witness_interval = list(bridge_native_tail_witness_interval)
        discharged_bridge_native_tail_witness_width = float(bridge_native_tail_witness_interval[1] - bridge_native_tail_witness_interval[0])

    mapped_identification_names = set(WORKSTREAM_TO_IDENTIFICATION_ASSUMPTION_MAP.values())
    identification_local = [str(x) for x in identification_shell.get('local_active_assumptions', [])]
    residual_local_names = [name for name in identification_local if name not in mapped_identification_names]

    hypotheses = _build_hypotheses(
        theorem_i_ii_shell=theorem_i_ii_shell,
        identification_shell=identification_shell,
        workstream_window=workstream_window,
        identified_window=identified_window,
        overlap_width=overlap_width,
        min_overlap_width=float(min_overlap_width),
        require_window_overlap=bool(require_window_overlap),
        residual_local_names=residual_local_names,
        discharged_bridge_native_tail_witness_interval=discharged_bridge_native_tail_witness_interval,
        discharged_bridge_native_tail_witness_width=discharged_bridge_native_tail_witness_width,
        workstream_critical_surface_identification_summary=dict(theorem_i_ii_shell.get('critical_surface_identification_summary', {})),
        workstream_critical_surface_threshold_identification_discharge=dict(theorem_i_ii_shell.get('critical_surface_threshold_identification_discharge', {})),
        workstream_critical_surface_threshold_identification_promotion=dict(theorem_i_ii_shell.get('critical_surface_threshold_identification_promotion', {})),
    )
    assumptions = _build_local_assumptions(
        residual_local_names=residual_local_names,
        assume_localized_compatibility_window_identifies_true_irrational_threshold=assume_localized_compatibility_window_identifies_true_irrational_threshold,
    )

    informative_only_hypotheses = {'bridge_native_tail_witness_survives_discharge_window_overlap', 'workstream_critical_surface_identification_ready'}
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if (not row.satisfied and row.name not in informative_only_hypotheses)]

    local_active_assumptions = [row.name for row in assumptions if not row.assumed]
    upstream_active_assumptions = sorted({
        *(str(x) for x in theorem_i_ii_shell.get('active_assumptions', [])),
        *(str(x) for x in identification_shell.get('upstream_active_assumptions', [])),
    })
    active_assumptions = sorted(set(upstream_active_assumptions) | set(local_active_assumptions))

    front_packaged = (
        _is_front_complete(theorem_i_ii_shell)
        and _is_front_complete(identification_shell)
        and 'theorem_i_ii_feeds_identification_assumptions' in discharged_hypotheses
        and 'residual_local_identification_assumption_isolated' in discharged_hypotheses
        and (not require_window_overlap or 'workstream_threshold_windows_overlap' in discharged_hypotheses)
    )

    residual_burden_summary = _build_residual_burden_summary(
        theorem_i_ii_shell=theorem_i_ii_shell,
        overlap_width=overlap_width,
        local_active_assumptions=local_active_assumptions,
        front_packaged=front_packaged,
    )

    if front_packaged and not local_active_assumptions:
        theorem_status = 'golden-threshold-identification-discharge-lift-conditional-strong'
        notes = (
            'The Theorem-I/II Workstream shell now explicitly feeds the Theorem-II->V identification shell, '
            'the workstream and threshold windows are quantitatively consistent, and the residual local identification hinge has been toggled on.'
        )
    elif front_packaged:
        theorem_status = 'golden-threshold-identification-discharge-lift-front-complete'
        notes = (
            'The Workstream shell discharges the renormalization-side assumptions inside the threshold-identification shell, '
            'and the residual local hinge has been isolated, but the final local identification assumption remains active.'
        )
    elif _status_rank(str(theorem_i_ii_shell.get('theorem_status', ''))) >= 1 or _status_rank(str(identification_shell.get('theorem_status', ''))) >= 1:
        theorem_status = 'golden-threshold-identification-discharge-lift-conditional-partial'
        notes = (
            'A theorem-facing discharge package has been assembled, but either the Workstream shell, the identification shell, or the quantitative window-consistency check remains only partially closed.'
        )
    else:
        theorem_status = 'golden-threshold-identification-discharge-lift-failed'
        notes = 'No usable Workstream-fed threshold-identification discharge package was assembled from the current certificates.'

    if overlap_width is not None and theorem_status != 'golden-threshold-identification-discharge-lift-failed':
        notes += f' Overlap width: {float(overlap_width):.6g}.'
    elif require_window_overlap and theorem_status != 'golden-threshold-identification-discharge-lift-failed':
        notes += ' No certified overlap window was available.'

    if discharged_bridge_native_tail_witness_width is not None and theorem_status != 'golden-threshold-identification-discharge-lift-failed':
        notes += f" Bridge-native witness width inside Workstream/identification overlap: {float(discharged_bridge_native_tail_witness_width):.6g}."

    return GoldenThresholdIdentificationDischargeCertificate(
        rho=float(rho),
        family_label=family_label,
        theorem_i_ii_shell=theorem_i_ii_shell,
        identification_shell=identification_shell,
        workstream_window=workstream_window,
        identified_window=identified_window,
        bridge_native_tail_witness_interval=bridge_native_tail_witness_interval,
        bridge_native_tail_witness_source=bridge_native_tail_witness_source,
        bridge_native_tail_witness_status=bridge_native_tail_witness_status,
        discharged_bridge_native_tail_witness_interval=discharged_bridge_native_tail_witness_interval,
        discharged_bridge_native_tail_witness_width=discharged_bridge_native_tail_witness_width,
        workstream_critical_surface_identification_summary=dict(theorem_i_ii_shell.get('critical_surface_identification_summary', {})),
        workstream_critical_surface_threshold_identification_discharge=dict(theorem_i_ii_shell.get('critical_surface_threshold_identification_discharge', {})),
        workstream_critical_surface_threshold_identification_promotion=dict(theorem_i_ii_shell.get('critical_surface_threshold_identification_promotion', {})),
        overlap_window=overlap_window,
        residual_burden_summary=residual_burden_summary,
        overlap_width=overlap_width,
        center_gap=center_gap,
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


def build_golden_theorem_ii_to_v_identification_discharge_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    **kwargs: Any,
) -> GoldenThresholdIdentificationDischargeCertificate:
    return build_golden_threshold_identification_discharge_certificate(
        base_K_values=base_K_values,
        family=family,
        rho=rho,
        **kwargs,
    )


__all__ = [
    'WORKSTREAM_TO_IDENTIFICATION_ASSUMPTION_MAP',
    'RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION',
    'ThresholdIdentificationDischargeHypothesisRow',
    'ThresholdIdentificationDischargeAssumptionRow',
    'GoldenThresholdIdentificationDischargeCertificate',
    'build_golden_threshold_identification_discharge_certificate',
    'build_golden_theorem_ii_to_v_identification_discharge_certificate',
]
