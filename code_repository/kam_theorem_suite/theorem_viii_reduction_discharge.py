from __future__ import annotations

"""Discharge-aware packaging for the final golden-maximality reduction.

This stage tightens Theorem VIII by explicitly feeding the discharge-aware
identification, Theorem-VI, and Theorem-VII shells into the final reduction
layer.  The existing reduction lift can already *consume* those sharper shells,
but it does not record how much upstream burden is removed, nor does it isolate
which active assumptions are still genuinely global after the sharpened stack is
used.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .theorem_v_downstream_utils import (
    extract_theorem_v_gap_preservation_certified,
    extract_theorem_v_target_interval,
    theorem_v_is_downstream_final,
)

from .golden_aposteriori import build_golden_theorem_iii_certificate, golden_inverse
from .standard_map import HarmonicFamily
from .theorem_viii_reduction_lift import build_golden_theorem_viii_certificate
from .theorem_vii_exhaustion_discharge import build_golden_theorem_vii_discharge_certificate
from .threshold_identification_discharge import RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION
from .threshold_identification_transport_discharge import RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION
from .theorem_i_ii_workstream_lift import build_golden_theorem_i_ii_workstream_lift_certificate
from .theorem_viii_support_utils import is_theorem_vi_final_or_stage107_promotable, support_proves_assumption
from .theorem_viii_final_discharge_support import extract_support_certificates


NON_GLOBAL_HINGE_ASSUMPTIONS = {
    'final_function_space_promotion',
    'obstruction_excludes_analytic_circle',
    'universality_class_embedding',
    'validated_function_space_continuation_transport',
    'unique_branch_continuation_to_true_irrational_threshold',
    'uniform_error_law_preserves_golden_gap',
    RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION,
    RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION,
}


_ORCHESTRATION_ONLY_KWARGS = {
    'theorem_iii_certificate',
    'theorem_iv_certificate',
    'theorem_v_certificate',
    'theorem_v_compressed_certificate',
    'threshold_identification_certificate',
    'threshold_identification_discharge_certificate',
    'theorem_vi_certificate',
    'theorem_vi_envelope_discharge_certificate',
    'theorem_vii_certificate',
    'theorem_vii_exhaustion_discharge_certificate',
    'theorem_i_ii_workstream_certificate',
    'baseline_theorem_viii_certificate',
}


def _filter_kwargs(fn, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    filtered = {k: v for k, v in kwargs.items() if k not in _ORCHESTRATION_ONLY_KWARGS}
    params = signature(fn).parameters
    has_var_keyword = any(p.kind == p.VAR_KEYWORD for p in params.values())
    if has_var_keyword:
        return filtered
    return {k: v for k, v in filtered.items() if k in params}


def _status_rank(status: str) -> int:
    status = str(status)
    if ('final-universal-ready' in status or 'universal-theorem-final-strong' in status or 'conditional-one-variable-strong' in status or 'conditional-two-variable-strong' in status or status.endswith('-conditional-strong') or status.endswith('-strong')):
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




def _forward_builder_kwargs(fn, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    has_var_keyword = any(p.kind == p.VAR_KEYWORD for p in params.values())
    if has_var_keyword:
        return dict(kwargs)
    return {k: v for k, v in kwargs.items() if k in params}


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


def _extract_vi_gap_geometry(theorem_vi_discharge: Mapping[str, Any]) -> tuple[float | None, float | None]:
    top_gap = _coerce_float(theorem_vi_discharge.get('current_top_gap_scale'))
    challenger_upper = _coerce_float(theorem_vi_discharge.get('current_most_dangerous_challenger_upper'))
    if top_gap is not None or challenger_upper is not None:
        return top_gap, challenger_upper
    theorem_vi_shell = dict(theorem_vi_discharge.get('theorem_vi_shell', {}))
    near_relation = dict((theorem_vi_shell.get('near_top_challenger_surface') or {}).get('near_top_relation', {}))
    proto_relation = dict((theorem_vi_shell.get('proto_envelope_bridge') or {}).get('proto_envelope_relation', {}))
    top_gap = _coerce_float(near_relation.get('golden_lower_minus_most_dangerous_upper'))
    if top_gap is None:
        top_gap = _coerce_float(proto_relation.get('anchor_lower_minus_panel_nongolden_upper'))
    challenger_upper = _coerce_float(near_relation.get('most_dangerous_threshold_upper'))
    if challenger_upper is None:
        challenger_upper = _coerce_float(proto_relation.get('panel_nongolden_max_upper_bound'))
    return top_gap, challenger_upper


def _extract_vi_witness_geometry_summary(theorem_vi_discharge: Mapping[str, Any]) -> tuple[float | None, float | None, float | None, float | None, float | None, str | None]:
    top_gap = _coerce_float(theorem_vi_discharge.get('current_top_gap_scale'))
    challenger_upper = _coerce_float(theorem_vi_discharge.get('current_most_dangerous_challenger_upper'))
    fallback_top_gap, fallback_challenger_upper = _extract_vi_gap_geometry(theorem_vi_discharge)
    if top_gap is None:
        top_gap = fallback_top_gap
    if challenger_upper is None:
        challenger_upper = fallback_challenger_upper

    width_vs_gap_margin = _coerce_float(theorem_vi_discharge.get('discharged_witness_width_vs_current_top_gap_margin'))
    lower_vs_challenger_margin = _coerce_float(theorem_vi_discharge.get('discharged_witness_lower_vs_current_near_top_challenger_upper_margin'))

    witness = theorem_vi_discharge.get('discharged_identified_branch_witness_interval')
    witness_width = _coerce_float(theorem_vi_discharge.get('discharged_identified_branch_witness_width'))
    witness_lower = None
    if isinstance(witness, Sequence) and len(witness) == 2:
        witness_lower = float(witness[0])

    if width_vs_gap_margin is None and witness_width is not None and top_gap is not None:
        width_vs_gap_margin = float(top_gap - witness_width)
    if lower_vs_challenger_margin is None and witness_lower is not None and challenger_upper is not None:
        lower_vs_challenger_margin = float(witness_lower - challenger_upper)

    min_margin = _coerce_float(theorem_vi_discharge.get('discharged_witness_geometry_min_margin'))
    margins = [x for x in (width_vs_gap_margin, lower_vs_challenger_margin) if x is not None]
    if min_margin is None and margins:
        min_margin = float(min(margins))

    status = theorem_vi_discharge.get('discharged_witness_geometry_status')
    if status is None:
        if witness is None:
            status = 'discharged-witness-geometry-missing'
        elif width_vs_gap_margin is not None and lower_vs_challenger_margin is not None:
            if width_vs_gap_margin >= -1.0e-15 and lower_vs_challenger_margin > 0.0:
                status = 'discharged-witness-geometry-strong'
            elif width_vs_gap_margin >= -1.0e-15 or lower_vs_challenger_margin > 0.0:
                status = 'discharged-witness-geometry-partial'
            else:
                status = 'discharged-witness-geometry-incompatible'
        else:
            status = 'discharged-witness-geometry-unresolved'

    return top_gap, challenger_upper, width_vs_gap_margin, lower_vs_challenger_margin, min_margin, None if status is None else str(status)


def _extract_vii_near_top_exhaustion_summary(theorem_vii_discharge: Mapping[str, Any], theorem_vi_discharge: Mapping[str, Any]) -> tuple[float | None, float | None, int, str | None, str | None]:
    upper = _coerce_float(theorem_vii_discharge.get('current_near_top_exhaustion_upper_bound'))
    margin = _coerce_float(theorem_vii_discharge.get('current_near_top_exhaustion_margin'))
    pending = theorem_vii_discharge.get('current_near_top_exhaustion_pending_count')
    source = theorem_vii_discharge.get('current_near_top_exhaustion_source')
    status = theorem_vii_discharge.get('current_near_top_exhaustion_status')
    if any(x is not None for x in (upper, margin, source, status, pending)):
        return upper, margin, int(0 if pending is None else pending), None if source is None else str(source), None if status is None else str(status)

    termination = dict(theorem_vii_discharge.get('theorem_vii_shell', {}).get('termination_aware_search_report', {}))
    active_count = int(termination.get('active_count', 0))
    deferred_count = int(termination.get('deferred_count', 0))
    undecided_count = int(termination.get('undecided_count', 0))
    overlap_count = int(termination.get('overlapping_count', 0))
    pending_count = active_count + deferred_count + undecided_count + overlap_count
    upper = _coerce_float(theorem_vi_discharge.get('current_most_dangerous_challenger_upper'))
    if upper is None:
        upper = _coerce_float(theorem_vii_discharge.get('reference_lower_bound'))
        if upper is not None:
            upper = None
    reference_lower = _coerce_float(theorem_vii_discharge.get('reference_lower_bound'))
    margin = None if upper is None or reference_lower is None else float(reference_lower - upper)
    if upper is None:
        status = 'near-top-exhaustion-summary-missing'
    elif margin is not None and margin > 0.0 and pending_count == 0:
        status = 'near-top-exhaustion-strong'
    elif margin is not None and margin > 0.0:
        status = 'near-top-exhaustion-partial'
    else:
        status = 'near-top-exhaustion-incompatible'
    source_parts = []
    if theorem_vi_discharge.get('current_most_dangerous_challenger_upper') is not None:
        source_parts.append('theorem_vi_discharge.current_most_dangerous_challenger_upper')
    if termination:
        source_parts.append('theorem_vii_discharge.theorem_vii_shell.termination_aware_search_report')
    source = ' + '.join(source_parts) if source_parts else None
    return upper, margin, pending_count, source, status


def _extract_discharged_identified_branch_witness(
    theorem_vi_discharge: Mapping[str, Any],
    threshold_identification_discharge: Mapping[str, Any],
) -> tuple[list[float] | None, str | None, str | None, float | None]:
    witness = theorem_vi_discharge.get('discharged_identified_branch_witness_interval')
    source = theorem_vi_discharge.get('discharged_identified_branch_witness_source')
    status = theorem_vi_discharge.get('discharged_identified_branch_witness_status')
    width = theorem_vi_discharge.get('discharged_identified_branch_witness_width')
    if isinstance(witness, Sequence) and len(witness) == 2:
        lo = float(witness[0])
        hi = float(witness[1])
        if hi >= lo:
            return [lo, hi], None if source is None else str(source), None if status is None else str(status), None if width is None else float(width)
    witness = threshold_identification_discharge.get('discharged_bridge_native_tail_witness_interval')
    source = threshold_identification_discharge.get('bridge_native_tail_witness_source')
    status = threshold_identification_discharge.get('bridge_native_tail_witness_status')
    width = threshold_identification_discharge.get('discharged_bridge_native_tail_witness_width')
    if isinstance(witness, Sequence) and len(witness) == 2:
        lo = float(witness[0])
        hi = float(witness[1])
        if hi >= lo:
            return [lo, hi], None if source is None else str(source), None if status is None else str(status), None if width is None else float(width)
    return None, None, None, None


def _summarize_current_reduction_geometry(
    threshold_identification_discharge: Mapping[str, Any],
    discharged_identified_branch_witness_interval: Sequence[float] | None,
    discharged_identified_branch_witness_width: float | None,
    inherited_current_top_gap_scale: float | None,
    inherited_current_most_dangerous_challenger_upper: float | None,
    inherited_discharged_witness_width_vs_current_top_gap_margin: float | None,
    inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin: float | None,
    inherited_current_near_top_exhaustion_upper_bound: float | None,
    inherited_current_near_top_exhaustion_margin: float | None,
    inherited_current_near_top_exhaustion_pending_count: int,
    inherited_current_near_top_exhaustion_source: str | None,
) -> tuple[float | None, float | None, float | None, float | None, float | None, float | None, int, float | None, str | None, str]:
    overlap_window = threshold_identification_discharge.get('overlap_window')
    overlap_width = _coerce_float(threshold_identification_discharge.get('overlap_width'))
    overlap_contains_witness = False
    if discharged_identified_branch_witness_interval is not None and isinstance(overlap_window, Sequence) and len(overlap_window) == 2:
        overlap_contains_witness = float(overlap_window[0]) - 1.0e-15 <= float(discharged_identified_branch_witness_interval[0]) and float(discharged_identified_branch_witness_interval[1]) <= float(overlap_window[1]) + 1.0e-15
    witness_vs_overlap_margin = None if discharged_identified_branch_witness_width is None or overlap_width is None else float(overlap_width - float(discharged_identified_branch_witness_width))
    top_gap_scale = inherited_current_top_gap_scale
    challenger_upper_bound = inherited_current_most_dangerous_challenger_upper
    witness_width_vs_top_gap_margin = inherited_discharged_witness_width_vs_current_top_gap_margin
    witness_lower_vs_challenger_upper_margin = inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin
    exhaustion_upper_bound = inherited_current_near_top_exhaustion_upper_bound
    exhaustion_margin = inherited_current_near_top_exhaustion_margin
    pending_count = int(inherited_current_near_top_exhaustion_pending_count)

    numeric_margins = [
        x for x in (
            witness_vs_overlap_margin,
            witness_width_vs_top_gap_margin,
            witness_lower_vs_challenger_upper_margin,
            exhaustion_margin,
        ) if x is not None
    ]
    min_margin = None if not numeric_margins else float(min(numeric_margins))

    source_parts: list[str] = []
    if threshold_identification_discharge.get('overlap_window') is not None:
        source_parts.append('threshold_identification_discharge.overlap_window')
    if top_gap_scale is not None or challenger_upper_bound is not None:
        source_parts.append('theorem_vi_discharge.current witness geometry summary')
    if exhaustion_upper_bound is not None or exhaustion_margin is not None or inherited_current_near_top_exhaustion_source is not None:
        source_parts.append('theorem_vii_discharge.current near-top exhaustion summary')
    source = ' + '.join(source_parts) if source_parts else None

    if discharged_identified_branch_witness_interval is None:
        status = 'current-reduction-geometry-missing'
    elif not overlap_contains_witness or (witness_vs_overlap_margin is not None and witness_vs_overlap_margin < -1.0e-15):
        status = 'current-reduction-geometry-incompatible'
    elif (
        witness_width_vs_top_gap_margin is not None
        and witness_width_vs_top_gap_margin >= -1.0e-15
        and witness_lower_vs_challenger_upper_margin is not None
        and witness_lower_vs_challenger_upper_margin > 0.0
        and exhaustion_margin is not None
        and exhaustion_margin > 0.0
        and pending_count == 0
    ):
        status = 'current-reduction-geometry-strong'
    elif min_margin is not None and min_margin >= -1.0e-15:
        status = 'current-reduction-geometry-partial'
    elif numeric_margins:
        status = 'current-reduction-geometry-incompatible'
    else:
        status = 'current-reduction-geometry-unresolved'

    return (
        witness_vs_overlap_margin,
        top_gap_scale,
        challenger_upper_bound,
        exhaustion_upper_bound,
        witness_width_vs_top_gap_margin,
        witness_lower_vs_challenger_upper_margin,
        pending_count,
        min_margin,
        source,
        status,
    )



def _is_theorem_vi_final(cert: Mapping[str, Any]) -> bool:
    status = str(cert.get('theorem_status', ''))
    residual_status = str((cert.get('residual_burden_summary') or {}).get('status', ''))
    return (
        'global-one-variable-strong' in status
        or 'global-two-variable-strong' in status
        or residual_status == 'theorem-vi-globally-discharged'
    )


def _summarize_theorem_vii_consumption(cert: Mapping[str, Any]) -> dict[str, Any]:
    status = str(cert.get('theorem_status', ''))
    codepath_final = bool(cert.get('theorem_vii_codepath_final', _status_rank(status) >= 3 and len(cert.get('open_hypotheses', [])) == 0))
    papergrade_final = bool(cert.get('theorem_vii_papergrade_final', False))
    residual = [str(x) for x in cert.get('theorem_vii_residual_citation_burden', [])]
    if not residual and not papergrade_final:
        residual_status = str((cert.get('residual_burden_summary') or {}).get('status', ''))
        if residual_status:
            residual.append(residual_status)
    return {
        'codepath_final': codepath_final,
        'papergrade_final': papergrade_final,
        'residual_citation_burden': residual,
    }


def _summarize_workstream_consumption(cert: Mapping[str, Any]) -> dict[str, Any]:
    status = str(cert.get('theorem_status', ''))
    residual = dict(cert.get('residual_burden_summary', {}))
    embedded_summary = dict(cert.get('workstream_consumption_summary', {}))
    codepath_strong = bool(cert.get('workstream_codepath_strong', embedded_summary.get('codepath_strong', _status_rank(status) >= 3)))
    papergrade_strong = bool(cert.get('workstream_papergrade_strong', embedded_summary.get('papergrade_strong', codepath_strong and len(cert.get('active_assumptions', [])) == 0 and residual.get('promotion_theorem_discharged', False))))
    residual_caveat: list[str] = [str(x) for x in cert.get('workstream_residual_caveat', embedded_summary.get('residual_caveat', []))]
    residual_status = str(residual.get('status', ''))
    if not residual_caveat and not papergrade_strong:
        if residual_status:
            residual_caveat.append(residual_status)
        if len(cert.get('active_assumptions', [])) > 0:
            residual_caveat.append('workstream-papergrade-cleanup-active-assumptions')
    return {
        'codepath_strong': codepath_strong,
        'papergrade_strong': papergrade_strong,
        'residual_caveat': residual_caveat,
        'residual_status': residual_status,
        'papergrade_theorem_status': str(cert.get('papergrade_theorem_status', embedded_summary.get('papergrade_theorem_status', ''))),
    }


@dataclass
class TheoremVIIIReductionDischargeHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVIIIReductionDischargeAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremVIIIReductionDischargeLiftCertificate:
    rho: float
    family_label: str
    statement_mode: str
    baseline_reduction_shell: dict[str, Any]
    theorem_viii_shell: dict[str, Any]
    theorem_vii_discharge_shell: dict[str, Any]
    theorem_vi_discharge_shell: dict[str, Any]
    threshold_identification_discharge_shell: dict[str, Any]
    theorem_viii_final_discharge_support_certificate: dict[str, Any]
    theorem_iii_final_certified: bool
    theorem_iii_lower_interval: list[float] | None
    theorem_iv_final_certified: bool
    theorem_v_final_certified: bool
    theorem_vi_final_certified: bool
    theorem_vii_codepath_final: bool
    theorem_vii_papergrade_final: bool
    theorem_vii_residual_citation_burden: list[str]
    workstream_consumption_summary: dict[str, Any]
    theorem_v_target_interval: list[float] | None
    theorem_v_gap_preservation_certified: bool | None
    all_upstream_theorems_consumed: bool
    final_threshold_law_ready: bool
    final_golden_top_gap_ready: bool
    final_universal_statement: str
    golden_maximality_conclusion_certified: bool
    modular_orbit_uniqueness_certified: bool
    remaining_workstream_paper_grade_burden: list[str]
    remaining_exhaustion_paper_grade_burden: list[str]
    remaining_true_mathematical_burden: list[str]
    final_certificate_ready_for_paper: bool
    final_certificate_ready_for_code_path: bool
    discharged_identified_branch_witness_interval: list[float] | None
    discharged_identified_branch_witness_width: float | None
    discharged_identified_branch_witness_source: str | None
    discharged_identified_branch_witness_status: str | None
    inherited_current_top_gap_scale: float | None
    inherited_current_most_dangerous_challenger_upper: float | None
    inherited_discharged_witness_width_vs_current_top_gap_margin: float | None
    inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin: float | None
    inherited_discharged_witness_geometry_min_margin: float | None
    inherited_discharged_witness_geometry_status: str | None
    inherited_current_near_top_exhaustion_upper_bound: float | None
    inherited_current_near_top_exhaustion_margin: float | None
    inherited_current_near_top_exhaustion_pending_count: int
    inherited_current_near_top_exhaustion_source: str | None
    inherited_current_near_top_exhaustion_status: str | None
    current_reduction_geometry_witness_vs_overlap_margin: float | None
    current_reduction_geometry_top_gap_scale: float | None
    current_reduction_geometry_challenger_upper_bound: float | None
    current_reduction_geometry_exhaustion_upper_bound: float | None
    current_reduction_geometry_witness_width_vs_top_gap_margin: float | None
    current_reduction_geometry_witness_lower_vs_challenger_upper_margin: float | None
    current_reduction_geometry_pending_count: int
    current_reduction_geometry_min_margin: float | None
    current_reduction_geometry_source: str | None
    current_reduction_geometry_status: str
    residual_global_active_assumptions: list[str]
    residual_non_global_hinges: list[str]
    hypotheses: list[TheoremVIIIReductionDischargeHypothesisRow]
    assumptions: list[TheoremVIIIReductionDischargeAssumptionRow]
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
            'statement_mode': str(self.statement_mode),
            'baseline_reduction_shell': dict(self.baseline_reduction_shell),
            'theorem_viii_shell': dict(self.theorem_viii_shell),
            'theorem_vii_discharge_shell': dict(self.theorem_vii_discharge_shell),
            'theorem_vi_discharge_shell': dict(self.theorem_vi_discharge_shell),
            'threshold_identification_discharge_shell': dict(self.threshold_identification_discharge_shell),
            'theorem_viii_final_discharge_support_certificate': dict(self.theorem_viii_final_discharge_support_certificate),
            'final_discharge_support_certificate': dict(self.theorem_viii_final_discharge_support_certificate),
            'theorem_iii_final_certified': bool(self.theorem_iii_final_certified),
            'theorem_iii_lower_interval': None if self.theorem_iii_lower_interval is None else [float(x) for x in self.theorem_iii_lower_interval],
            'theorem_iv_final_certified': bool(self.theorem_iv_final_certified),
            'theorem_v_final_certified': bool(self.theorem_v_final_certified),
            'theorem_vi_final_certified': bool(self.theorem_vi_final_certified),
            'theorem_vii_codepath_final': bool(self.theorem_vii_codepath_final),
            'theorem_vii_papergrade_final': bool(self.theorem_vii_papergrade_final),
            'theorem_vii_residual_citation_burden': [str(x) for x in self.theorem_vii_residual_citation_burden],
            'workstream_consumption_summary': dict(self.workstream_consumption_summary),
            'theorem_v_target_interval': None if self.theorem_v_target_interval is None else [float(x) for x in self.theorem_v_target_interval],
            'theorem_v_gap_preservation_certified': None if self.theorem_v_gap_preservation_certified is None else bool(self.theorem_v_gap_preservation_certified),
            'all_upstream_theorems_consumed': bool(self.all_upstream_theorems_consumed),
            'final_threshold_law_ready': bool(self.final_threshold_law_ready),
            'final_golden_top_gap_ready': bool(self.final_golden_top_gap_ready),
            'final_universal_statement': str(self.final_universal_statement),
            'golden_maximality_conclusion_certified': bool(self.golden_maximality_conclusion_certified),
            'final_golden_maximality_discharge': bool(self.golden_maximality_conclusion_certified),
            'modular_orbit_uniqueness_certified': bool(self.modular_orbit_uniqueness_certified),
            'remaining_workstream_paper_grade_burden': [str(x) for x in self.remaining_workstream_paper_grade_burden],
            'remaining_exhaustion_paper_grade_burden': [str(x) for x in self.remaining_exhaustion_paper_grade_burden],
            'remaining_true_mathematical_burden': [str(x) for x in self.remaining_true_mathematical_burden],
            'final_certificate_ready_for_paper': bool(self.final_certificate_ready_for_paper),
            'final_certificate_ready_for_code_path': bool(self.final_certificate_ready_for_code_path),
            'discharged_identified_branch_witness_interval': None if self.discharged_identified_branch_witness_interval is None else [float(x) for x in self.discharged_identified_branch_witness_interval],
            'discharged_identified_branch_witness_width': None if self.discharged_identified_branch_witness_width is None else float(self.discharged_identified_branch_witness_width),
            'discharged_identified_branch_witness_source': None if self.discharged_identified_branch_witness_source is None else str(self.discharged_identified_branch_witness_source),
            'discharged_identified_branch_witness_status': None if self.discharged_identified_branch_witness_status is None else str(self.discharged_identified_branch_witness_status),
            'inherited_current_top_gap_scale': None if self.inherited_current_top_gap_scale is None else float(self.inherited_current_top_gap_scale),
            'inherited_current_most_dangerous_challenger_upper': None if self.inherited_current_most_dangerous_challenger_upper is None else float(self.inherited_current_most_dangerous_challenger_upper),
            'inherited_discharged_witness_width_vs_current_top_gap_margin': None if self.inherited_discharged_witness_width_vs_current_top_gap_margin is None else float(self.inherited_discharged_witness_width_vs_current_top_gap_margin),
            'inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin': None if self.inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin is None else float(self.inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin),
            'inherited_discharged_witness_geometry_min_margin': None if self.inherited_discharged_witness_geometry_min_margin is None else float(self.inherited_discharged_witness_geometry_min_margin),
            'inherited_discharged_witness_geometry_status': None if self.inherited_discharged_witness_geometry_status is None else str(self.inherited_discharged_witness_geometry_status),
            'inherited_current_near_top_exhaustion_upper_bound': None if self.inherited_current_near_top_exhaustion_upper_bound is None else float(self.inherited_current_near_top_exhaustion_upper_bound),
            'inherited_current_near_top_exhaustion_margin': None if self.inherited_current_near_top_exhaustion_margin is None else float(self.inherited_current_near_top_exhaustion_margin),
            'inherited_current_near_top_exhaustion_pending_count': int(self.inherited_current_near_top_exhaustion_pending_count),
            'inherited_current_near_top_exhaustion_source': None if self.inherited_current_near_top_exhaustion_source is None else str(self.inherited_current_near_top_exhaustion_source),
            'inherited_current_near_top_exhaustion_status': None if self.inherited_current_near_top_exhaustion_status is None else str(self.inherited_current_near_top_exhaustion_status),
            'current_reduction_geometry_witness_vs_overlap_margin': None if self.current_reduction_geometry_witness_vs_overlap_margin is None else float(self.current_reduction_geometry_witness_vs_overlap_margin),
            'current_reduction_geometry_top_gap_scale': None if self.current_reduction_geometry_top_gap_scale is None else float(self.current_reduction_geometry_top_gap_scale),
            'current_reduction_geometry_challenger_upper_bound': None if self.current_reduction_geometry_challenger_upper_bound is None else float(self.current_reduction_geometry_challenger_upper_bound),
            'current_reduction_geometry_exhaustion_upper_bound': None if self.current_reduction_geometry_exhaustion_upper_bound is None else float(self.current_reduction_geometry_exhaustion_upper_bound),
            'current_reduction_geometry_witness_width_vs_top_gap_margin': None if self.current_reduction_geometry_witness_width_vs_top_gap_margin is None else float(self.current_reduction_geometry_witness_width_vs_top_gap_margin),
            'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': None if self.current_reduction_geometry_witness_lower_vs_challenger_upper_margin is None else float(self.current_reduction_geometry_witness_lower_vs_challenger_upper_margin),
            'current_reduction_geometry_pending_count': int(self.current_reduction_geometry_pending_count),
            'current_reduction_geometry_min_margin': None if self.current_reduction_geometry_min_margin is None else float(self.current_reduction_geometry_min_margin),
            'current_reduction_geometry_source': None if self.current_reduction_geometry_source is None else str(self.current_reduction_geometry_source),
            'current_reduction_geometry_status': str(self.current_reduction_geometry_status),
            'residual_global_active_assumptions': [str(x) for x in self.residual_global_active_assumptions],
            'residual_non_global_hinges': [str(x) for x in self.residual_non_global_hinges],
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


def _coerce_assumption_rows(rows: Sequence[Mapping[str, Any]]) -> list[TheoremVIIIReductionDischargeAssumptionRow]:
    out: list[TheoremVIIIReductionDischargeAssumptionRow] = []
    for row in rows:
        out.append(
            TheoremVIIIReductionDischargeAssumptionRow(
                name=str(row.get('name', 'unknown-assumption')),
                assumed=bool(row.get('assumed', False)),
                source=str(row.get('source', 'Theorem-VIII reduction lift assumption')),
                note=str(row.get('note', '')),
            )
        )
    return out


def _build_hypotheses(
    baseline: Mapping[str, Any],
    theorem_viii: Mapping[str, Any],
    theorem_vii_discharge: Mapping[str, Any],
    theorem_vi_discharge: Mapping[str, Any],
    threshold_identification_discharge: Mapping[str, Any],
    theorem_iii_final_certified: bool,
    theorem_iv_final_certified: bool,
    theorem_v_final_certified: bool,
    theorem_v_gap_preservation_certified: bool | None,
    residual_global_active_assumptions: Sequence[str],
    residual_non_global_hinges: Sequence[str],
    discharged_identified_branch_witness_interval: Sequence[float] | None,
    discharged_identified_branch_witness_width: float | None,
    inherited_current_top_gap_scale: float | None,
    inherited_current_most_dangerous_challenger_upper: float | None,
    inherited_discharged_witness_width_vs_current_top_gap_margin: float | None,
    inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin: float | None,
    inherited_discharged_witness_geometry_min_margin: float | None,
    inherited_current_near_top_exhaustion_margin: float | None,
    inherited_current_near_top_exhaustion_pending_count: int,
    inherited_current_near_top_exhaustion_status: str | None,
    current_reduction_geometry_witness_vs_overlap_margin: float | None,
    current_reduction_geometry_top_gap_scale: float | None,
    current_reduction_geometry_challenger_upper_bound: float | None,
    current_reduction_geometry_exhaustion_upper_bound: float | None,
    current_reduction_geometry_witness_width_vs_top_gap_margin: float | None,
    current_reduction_geometry_witness_lower_vs_challenger_upper_margin: float | None,
    current_reduction_geometry_pending_count: int,
    current_reduction_geometry_min_margin: float | None,
    current_reduction_geometry_status: str | None,
) -> list[TheoremVIIIReductionDischargeHypothesisRow]:
    baseline_upstream = [str(x) for x in baseline.get('upstream_active_assumptions', [])]
    new_upstream = [str(x) for x in theorem_viii.get('upstream_active_assumptions', [])]
    reduction = float(len(baseline_upstream) - len(new_upstream))
    statement_mode = str(theorem_viii.get('statement_mode', 'unresolved'))
    local_hinge_set = {str(x) for x in threshold_identification_discharge.get('local_active_assumptions', [])}
    witness_vs_overlap_margin = current_reduction_geometry_witness_vs_overlap_margin
    top_gap = current_reduction_geometry_top_gap_scale
    challenger_upper = current_reduction_geometry_challenger_upper_bound
    witness_vs_gap_margin = current_reduction_geometry_witness_width_vs_top_gap_margin
    witness_above_challenger_margin = current_reduction_geometry_witness_lower_vs_challenger_upper_margin
    geometry_min_margin = current_reduction_geometry_min_margin
    return [
        TheoremVIIIReductionDischargeHypothesisRow(
            name='theorem_viii_front_complete',
            satisfied=_is_front_complete(theorem_viii),
            source='Theorem-VIII reduction lift',
            note='The discharge-aware final reduction shell has no remaining open front hypotheses.',
            margin=None,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='theorem_vii_discharge_front_complete',
            satisfied=_is_front_complete(theorem_vii_discharge),
            source='Theorem-VII exhaustion discharge lift',
            note='The discharge-aware challenger-exhaustion shell is front-complete.',
            margin=None,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='theorem_vi_discharge_front_complete',
            satisfied=_is_front_complete(theorem_vi_discharge),
            source='Theorem-VI envelope discharge lift',
            note='The discharge-aware envelope shell is front-complete.',
            margin=None,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='threshold_identification_discharge_front_complete',
            satisfied=_is_front_complete(threshold_identification_discharge),
            source='threshold-identification discharge lift',
            note='The discharge-aware identification shell is front-complete.',
            margin=None,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='theorem_iii_consumed_as_final_theorem',
            satisfied=bool(theorem_iii_final_certified),
            source='Theorem-III final lower theorem',
            note='The reduction consumes Theorem III as a final lower theorem rather than only a lower-side front.',
            margin=None,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='theorem_iv_consumed_as_final_theorem',
            satisfied=bool(theorem_iv_final_certified),
            source='Theorem-IV final incompatibility theorem',
            note='Theorem VIII inherits a final Theorem-IV analytic incompatibility theorem rather than only a front-complete shell.',
            margin=None,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='theorem_v_consumed_as_final_theorem',
            satisfied=bool(theorem_v_final_certified),
            source='Theorem-V final transport theorem',
            note='Theorem VIII now consumes Theorem V as a final continuation/transport theorem rather than merely inheriting a front-complete shell.',
            margin=None,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='theorem_v_gap_preservation_available_for_reduction',
            satisfied=bool(theorem_v_gap_preservation_certified),
            source='Theorem-V final error law',
            note='Theorem VIII inherits a final Theorem-V gap-preservation certificate from the continuation/error law.',
            margin=None,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='reduction_upstream_burden_reduced_by_discharge',
            satisfied=len(new_upstream) <= len(baseline_upstream),
            source='comparison of Theorem-VIII upstream assumptions before/after discharge',
            note='Feeding the discharge-aware Theorems II->VII shells into Theorem VIII should weakly reduce the inherited upstream burden.',
            margin=reduction,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='residual_identification_hinge_isolated',
            satisfied=local_hinge_set.issubset({RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION, RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION}),
            source='threshold-identification discharge lift',
            note='After the discharge-aware propagation into Theorem VIII, the only residual identification-side local hinge is either the localized compatibility-window identification assumption or its sharper transport-locked uniqueness refinement.',
            margin=None if not local_hinge_set else float(len(local_hinge_set)),
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='residual_global_assumptions_explicit',
            satisfied=statement_mode in {'one-variable', 'two-variable', 'unresolved'} and len(residual_global_active_assumptions) >= 0,
            source='Theorem-VIII reduction discharge lift',
            note='The discharge-aware reduction shell exposes an explicit statement mode and a separated list of genuinely global active assumptions.',
            margin=float(len(residual_global_active_assumptions)),
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='residual_non_global_hinges_explicit',
            satisfied=set(str(x) for x in residual_non_global_hinges).issubset(NON_GLOBAL_HINGE_ASSUMPTIONS),
            source='Theorem-VIII reduction discharge lift',
            note='All remaining non-global hinges carried by the discharge-aware reduction shell are explicitly classified.',
            margin=float(len(residual_non_global_hinges)),
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='discharged_identified_branch_witness_available_for_reduction',
            satisfied=bool(discharged_identified_branch_witness_interval is not None),
            source='Theorem-VI / threshold-identification discharge stack',
            note='The final reduction stack inherits a concrete discharged identified branch witness interval from the II->V seam.',
            margin=None if discharged_identified_branch_witness_width is None else float(discharged_identified_branch_witness_width),
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='discharged_witness_narrower_than_identification_overlap_for_reduction',
            satisfied=bool(
                discharged_identified_branch_witness_interval is not None
                and current_reduction_geometry_status in {'current-reduction-geometry-strong', 'current-reduction-geometry-partial'}
                and witness_vs_overlap_margin is not None
                and witness_vs_overlap_margin >= -1.0e-15
            ),
            source='threshold-identification discharge lift',
            note='The identified branch witness carried into final reduction is fully contained in the II->V discharge overlap and is no wider than that overlap window, so the reduction sees a genuinely localized witness rather than only coarse compatibility geometry.',
            margin=witness_vs_overlap_margin,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='discharged_witness_compatible_with_current_top_gap_scale_for_reduction',
            satisfied=bool(
                discharged_identified_branch_witness_interval is not None
                and current_reduction_geometry_status in {'current-reduction-geometry-strong', 'current-reduction-geometry-partial'}
                and witness_vs_gap_margin is not None
                and witness_vs_gap_margin >= -1.0e-15
                and witness_above_challenger_margin is not None
                and witness_above_challenger_margin > 0.0
            ),
            source='Theorem-VI envelope / near-top challenger geometry',
            note='The witness interval inherited by final reduction is sharp enough relative to the current exploratory golden-over-challenger top-gap scale and already sits above the current most dangerous bounded challenger upper threshold.',
            margin=geometry_min_margin,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='inherited_near_top_exhaustion_summary_available_for_reduction',
            satisfied=bool(inherited_current_near_top_exhaustion_status is not None),
            source='Theorem-VII exhaustion discharge summary',
            note='The final reduction layer inherits an explicit Theorem-VII near-top dominance/exhaustion summary instead of unpacking search internals directly.',
            margin=None if inherited_current_near_top_exhaustion_margin is None else float(inherited_current_near_top_exhaustion_margin),
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='inherited_near_top_exhaustion_summary_strong_for_reduction',
            satisfied=bool(
                inherited_current_near_top_exhaustion_status == 'near-top-exhaustion-strong'
                and inherited_current_near_top_exhaustion_margin is not None
                and inherited_current_near_top_exhaustion_margin > 0.0
                and int(current_reduction_geometry_pending_count) == 0
            ),
            source='Theorem-VII exhaustion discharge summary',
            note='The inherited Theorem-VII summary already records positive near-top dominance against the current challenger upper bound with no pending challenger lifecycle burden.',
            margin=inherited_current_near_top_exhaustion_margin,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='current_reduction_geometry_summary_available_for_reduction',
            satisfied=bool(current_reduction_geometry_status is not None and current_reduction_geometry_status != 'current-reduction-geometry-missing'),
            source='Theorem-VIII current reduction geometry summary',
            note='The final reduction shell packages the inherited II->VII witness, overlap, gap, and exhaustion geometry as one native current reduction geometry summary.',
            margin=current_reduction_geometry_min_margin,
        ),
        TheoremVIIIReductionDischargeHypothesisRow(
            name='current_reduction_geometry_summary_strong_for_reduction',
            satisfied=bool(current_reduction_geometry_status == 'current-reduction-geometry-strong'),
            source='Theorem-VIII current reduction geometry summary',
            note='The native current reduction geometry summary simultaneously records localized witness containment, witness sharpness versus the current top-gap scale, witness dominance over the current challenger upper bound, and a strong near-top exhaustion margin with no pending burden.',
            margin=current_reduction_geometry_min_margin,
        ),
    ]


def build_golden_theorem_viii_reduction_discharge_lift_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    baseline_theorem_viii_certificate: Mapping[str, Any] | None = None,
    theorem_viii_certificate: Mapping[str, Any] | None = None,
    theorem_vii_exhaustion_discharge_certificate: Mapping[str, Any] | None = None,
    theorem_vi_envelope_discharge_certificate: Mapping[str, Any] | None = None,
    threshold_identification_discharge_certificate: Mapping[str, Any] | None = None,
    theorem_i_ii_workstream_certificate: Mapping[str, Any] | None = None,
    theorem_viii_final_discharge_support_certificate: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> GoldenTheoremVIIIReductionDischargeLiftCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    baseline_kwargs = dict(kwargs)
    for key in (
        'baseline_theorem_viii_certificate',
        'theorem_viii_certificate',
        'theorem_vii_exhaustion_discharge_certificate',
        'theorem_vi_envelope_discharge_certificate',
        'threshold_identification_discharge_certificate',
    ):
        baseline_kwargs.pop(key, None)
    if theorem_vii_exhaustion_discharge_certificate is not None:
        baseline_kwargs.setdefault('theorem_vii_exhaustion_discharge_certificate', theorem_vii_exhaustion_discharge_certificate)
    if theorem_vi_envelope_discharge_certificate is not None:
        baseline_kwargs.setdefault('theorem_vi_envelope_discharge_certificate', theorem_vi_envelope_discharge_certificate)
    if threshold_identification_discharge_certificate is not None:
        baseline_kwargs.setdefault('threshold_identification_discharge_certificate', threshold_identification_discharge_certificate)
    if theorem_i_ii_workstream_certificate is not None:
        baseline_kwargs.setdefault('theorem_i_ii_workstream_certificate', theorem_i_ii_workstream_certificate)
    if theorem_viii_final_discharge_support_certificate is not None:
        baseline_kwargs.setdefault('theorem_viii_final_discharge_support_certificate', theorem_viii_final_discharge_support_certificate)

    if baseline_theorem_viii_certificate is not None:
        baseline = dict(baseline_theorem_viii_certificate)
    else:
        baseline = build_golden_theorem_viii_certificate(
            base_K_values=base_K_values,
            family=family,
            family_label=family_label,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_viii_certificate, baseline_kwargs),
        ).to_dict()

    if theorem_vii_exhaustion_discharge_certificate is not None:
        theorem_vii_discharge = dict(theorem_vii_exhaustion_discharge_certificate)
    else:
        theorem_vii_discharge = build_golden_theorem_vii_discharge_certificate(
            base_K_values=base_K_values,
            family=family,
            **_filter_kwargs(build_golden_theorem_vii_discharge_certificate, kwargs),
        ).to_dict()

    inferred_theorem_vi_discharge = dict(theorem_vii_discharge.get('theorem_vi_discharge_shell', {}))
    inferred_identification_discharge = dict(inferred_theorem_vi_discharge.get('threshold_identification_discharge_shell', {}))

    theorem_vi_discharge = dict(theorem_vi_envelope_discharge_certificate) if theorem_vi_envelope_discharge_certificate is not None else inferred_theorem_vi_discharge
    threshold_identification_discharge = dict(threshold_identification_discharge_certificate) if threshold_identification_discharge_certificate is not None else inferred_identification_discharge

    if theorem_viii_certificate is not None:
        theorem_viii = dict(theorem_viii_certificate)
    else:
        reduction_kwargs = dict(kwargs)
        reduction_kwargs.update({
            'theorem_vii_exhaustion_discharge_certificate': theorem_vii_discharge,
            'theorem_vi_envelope_discharge_certificate': theorem_vi_discharge or None,
            'threshold_identification_discharge_certificate': threshold_identification_discharge or None,
            'theorem_viii_final_discharge_support_certificate': theorem_viii_final_discharge_support_certificate,
        })
        baseline_theorem_iii = dict(baseline.get('theorem_iii_shell', {}))
        baseline_theorem_iv = dict(baseline.get('theorem_iv_shell', {}))
        baseline_theorem_v = dict(baseline.get('theorem_v_shell', {}))
        baseline_workstream = dict(baseline.get('workstream_shell', {}))
        if baseline_theorem_iii:
            reduction_kwargs.setdefault('theorem_iii_certificate', baseline_theorem_iii)
        if baseline_theorem_iv:
            reduction_kwargs.setdefault('theorem_iv_certificate', baseline_theorem_iv)
        if baseline_theorem_v:
            reduction_kwargs.setdefault('theorem_v_certificate', baseline_theorem_v)
        if baseline_workstream:
            reduction_kwargs.setdefault('theorem_i_ii_workstream_certificate', baseline_workstream)
        theorem_viii = build_golden_theorem_viii_certificate(
            base_K_values=base_K_values,
            family=family,
            family_label=family_label,
            rho=rho,
            **_forward_builder_kwargs(build_golden_theorem_viii_certificate, reduction_kwargs),
        ).to_dict()

    theorem_iii_shell = dict(theorem_viii.get('theorem_iii_shell', {}))
    theorem_iii_final_certified = bool(str(theorem_iii_shell.get('theorem_iii_final_status', theorem_iii_shell.get('theorem_status', ''))).startswith('golden-theorem-iii-final-strong'))
    theorem_iii_lower_interval = theorem_iii_shell.get('certified_below_threshold_interval')
    theorem_iv_shell = dict(theorem_viii.get('theorem_iv_shell', {}))
    theorem_iv_final_certified = bool(str(theorem_iv_shell.get('theorem_status', '')).startswith('golden-theorem-iv-final-strong'))
    theorem_v_shell = dict(theorem_viii.get('theorem_v_shell', {}))
    theorem_v_final_certified = theorem_v_is_downstream_final(theorem_v_shell)
    theorem_v_target_interval = extract_theorem_v_target_interval(theorem_v_shell)
    theorem_v_gap_preservation_certified = extract_theorem_v_gap_preservation_certified(theorem_v_shell)

    if theorem_i_ii_workstream_certificate is not None:
        workstream = dict(theorem_i_ii_workstream_certificate)
    else:
        workstream = build_golden_theorem_i_ii_workstream_lift_certificate(
            family=family,
            **_filter_kwargs(build_golden_theorem_i_ii_workstream_lift_certificate, kwargs),
        ).to_dict()

    final_discharge_support = extract_support_certificates(theorem_viii_final_discharge_support_certificate) or extract_support_certificates(theorem_viii)
    assumptions = _coerce_assumption_rows(theorem_viii.get('assumptions', []))
    upstream_active_assumptions = [str(x) for x in theorem_viii.get('upstream_active_assumptions', [])]
    local_active_assumptions = [str(x) for x in theorem_viii.get('local_active_assumptions', [])]
    active_assumptions = [str(x) for x in theorem_viii.get('active_assumptions', [])]
    active_assumptions = [x for x in active_assumptions if not support_proves_assumption(final_discharge_support, x)]
    local_active_assumptions = [x for x in local_active_assumptions if not support_proves_assumption(final_discharge_support, x)]

    residual_non_global_hinges = sorted(set(x for x in active_assumptions if x in NON_GLOBAL_HINGE_ASSUMPTIONS))
    residual_global_active_assumptions = sorted(set(x for x in active_assumptions if x not in NON_GLOBAL_HINGE_ASSUMPTIONS))

    discharged_identified_branch_witness_interval, discharged_identified_branch_witness_source, discharged_identified_branch_witness_status, discharged_identified_branch_witness_width = _extract_discharged_identified_branch_witness(
        theorem_vi_discharge,
        threshold_identification_discharge,
    )
    inherited_current_top_gap_scale, inherited_current_most_dangerous_challenger_upper, inherited_discharged_witness_width_vs_current_top_gap_margin, inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin, inherited_discharged_witness_geometry_min_margin, inherited_discharged_witness_geometry_status = _extract_vi_witness_geometry_summary(theorem_vi_discharge)
    inherited_current_near_top_exhaustion_upper_bound, inherited_current_near_top_exhaustion_margin, inherited_current_near_top_exhaustion_pending_count, inherited_current_near_top_exhaustion_source, inherited_current_near_top_exhaustion_status = _extract_vii_near_top_exhaustion_summary(theorem_vii_discharge, theorem_vi_discharge)
    current_reduction_geometry_witness_vs_overlap_margin, current_reduction_geometry_top_gap_scale, current_reduction_geometry_challenger_upper_bound, current_reduction_geometry_exhaustion_upper_bound, current_reduction_geometry_witness_width_vs_top_gap_margin, current_reduction_geometry_witness_lower_vs_challenger_upper_margin, current_reduction_geometry_pending_count, current_reduction_geometry_min_margin, current_reduction_geometry_source, current_reduction_geometry_status = _summarize_current_reduction_geometry(
        threshold_identification_discharge,
        discharged_identified_branch_witness_interval,
        discharged_identified_branch_witness_width,
        inherited_current_top_gap_scale,
        inherited_current_most_dangerous_challenger_upper,
        inherited_discharged_witness_width_vs_current_top_gap_margin,
        inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin,
        inherited_current_near_top_exhaustion_upper_bound,
        inherited_current_near_top_exhaustion_margin,
        inherited_current_near_top_exhaustion_pending_count,
        inherited_current_near_top_exhaustion_source,
    )

    hypotheses = _build_hypotheses(
        baseline=baseline,
        theorem_viii=theorem_viii,
        theorem_vii_discharge=theorem_vii_discharge,
        theorem_vi_discharge=theorem_vi_discharge,
        threshold_identification_discharge=threshold_identification_discharge,
        theorem_iii_final_certified=theorem_iii_final_certified,
        theorem_iv_final_certified=theorem_iv_final_certified,
        theorem_v_final_certified=theorem_v_final_certified,
        theorem_v_gap_preservation_certified=theorem_v_gap_preservation_certified,
        residual_global_active_assumptions=residual_global_active_assumptions,
        residual_non_global_hinges=residual_non_global_hinges,
        discharged_identified_branch_witness_interval=discharged_identified_branch_witness_interval,
        discharged_identified_branch_witness_width=discharged_identified_branch_witness_width,
        inherited_current_top_gap_scale=inherited_current_top_gap_scale,
        inherited_current_most_dangerous_challenger_upper=inherited_current_most_dangerous_challenger_upper,
        inherited_discharged_witness_width_vs_current_top_gap_margin=inherited_discharged_witness_width_vs_current_top_gap_margin,
        inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin=inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin,
        inherited_discharged_witness_geometry_min_margin=inherited_discharged_witness_geometry_min_margin,
        inherited_current_near_top_exhaustion_margin=inherited_current_near_top_exhaustion_margin,
        inherited_current_near_top_exhaustion_pending_count=inherited_current_near_top_exhaustion_pending_count,
        inherited_current_near_top_exhaustion_status=inherited_current_near_top_exhaustion_status,
        current_reduction_geometry_witness_vs_overlap_margin=current_reduction_geometry_witness_vs_overlap_margin,
        current_reduction_geometry_top_gap_scale=current_reduction_geometry_top_gap_scale,
        current_reduction_geometry_challenger_upper_bound=current_reduction_geometry_challenger_upper_bound,
        current_reduction_geometry_exhaustion_upper_bound=current_reduction_geometry_exhaustion_upper_bound,
        current_reduction_geometry_witness_width_vs_top_gap_margin=current_reduction_geometry_witness_width_vs_top_gap_margin,
        current_reduction_geometry_witness_lower_vs_challenger_upper_margin=current_reduction_geometry_witness_lower_vs_challenger_upper_margin,
        current_reduction_geometry_pending_count=current_reduction_geometry_pending_count,
        current_reduction_geometry_min_margin=current_reduction_geometry_min_margin,
        current_reduction_geometry_status=current_reduction_geometry_status,
    )
    if not theorem_iii_final_certified:
        hypotheses = [row for row in hypotheses if row.name != 'theorem_iii_consumed_as_final_theorem']
    if not theorem_iv_final_certified:
        hypotheses = [row for row in hypotheses if row.name != 'theorem_iv_consumed_as_final_theorem']
    if not theorem_v_final_certified and theorem_v_gap_preservation_certified is None:
        hypotheses = [row for row in hypotheses if row.name not in {'theorem_v_consumed_as_final_theorem', 'theorem_v_gap_preservation_available_for_reduction'}]
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]

    theorem_vi_final_certified = is_theorem_vi_final_or_stage107_promotable(theorem_vi_discharge, final_discharge_support)
    theorem_vii_summary = _summarize_theorem_vii_consumption(theorem_vii_discharge)
    workstream_summary = _summarize_workstream_consumption(workstream)
    statement_mode = str(theorem_viii.get('statement_mode', 'unresolved'))
    all_upstream_theorems_consumed = bool(
        theorem_iii_final_certified
        and theorem_iv_final_certified
        and theorem_v_final_certified
        and theorem_vi_final_certified
        and theorem_vii_summary['codepath_final']
        and _is_front_complete(threshold_identification_discharge)
    )
    final_threshold_law_ready = bool(all_upstream_theorems_consumed and bool(theorem_v_gap_preservation_certified))
    final_golden_top_gap_ready = bool(current_reduction_geometry_status == 'current-reduction-geometry-strong' and theorem_vii_summary['codepath_final'])
    modular_orbit_uniqueness_certified = 'gl2z_orbit_uniqueness_and_normalization_closed' not in active_assumptions
    remaining_true_mathematical_burden: list[str] = []
    if not theorem_iii_final_certified:
        remaining_true_mathematical_burden.append('theorem_iii_final_not_consumed')
    if not theorem_iv_final_certified:
        remaining_true_mathematical_burden.append('theorem_iv_final_not_consumed')
    if not theorem_v_final_certified:
        remaining_true_mathematical_burden.append('theorem_v_final_not_consumed')
    if not theorem_vi_final_certified:
        remaining_true_mathematical_burden.append('theorem_vi_final_not_consumed')
    if not theorem_vii_summary['codepath_final']:
        remaining_true_mathematical_burden.append('theorem_vii_codepath_not_final')
    if not _is_front_complete(threshold_identification_discharge):
        remaining_true_mathematical_burden.append('identification_seam_not_final')
    if not bool(theorem_v_gap_preservation_certified):
        remaining_true_mathematical_burden.append('theorem_v_gap_preservation_not_final')
    if current_reduction_geometry_status != 'current-reduction-geometry-strong':
        remaining_true_mathematical_burden.append('reduction_geometry_not_strong')
    if not modular_orbit_uniqueness_certified:
        remaining_true_mathematical_burden.append('gl2z_orbit_uniqueness_and_normalization_closed')
    remaining_workstream_paper_grade_burden = [] if workstream_summary['papergrade_strong'] else [str(x) for x in workstream_summary['residual_caveat']]
    remaining_exhaustion_paper_grade_burden = [] if theorem_vii_summary['papergrade_final'] else [str(x) for x in theorem_vii_summary['residual_citation_burden']]
    final_certificate_ready_for_code_path = bool(not remaining_true_mathematical_burden and workstream_summary['codepath_strong'])
    final_certificate_ready_for_paper = bool(final_certificate_ready_for_code_path and not remaining_workstream_paper_grade_burden and not remaining_exhaustion_paper_grade_burden)
    final_universal_statement = 'golden-maximality on the GL2(Z)-orbit of the golden ratio' if statement_mode in {'one-variable', 'two-variable'} else 'unresolved-final-universal-statement'
    golden_maximality_conclusion_certified = bool(final_threshold_law_ready and final_golden_top_gap_ready and final_certificate_ready_for_code_path)

    if final_certificate_ready_for_paper:
        theorem_status = 'golden-universal-theorem-final-strong'
        notes = 'All upstream theorems are consumed, the reduction geometry is strong, and only paper-grade presentation residue has vanished.'
    elif final_certificate_ready_for_code_path and remaining_workstream_paper_grade_burden and not remaining_exhaustion_paper_grade_burden:
        theorem_status = 'golden-universal-theorem-workstream-caveat-only'
        notes = 'The universal theorem is closed in the code path, with the remaining burden isolated to Workstream-A paper-grade cleanup.'
    elif final_certificate_ready_for_code_path and remaining_exhaustion_paper_grade_burden and not remaining_workstream_paper_grade_burden:
        theorem_status = 'golden-universal-theorem-exhaustion-citation-incomplete'
        notes = 'The universal theorem is closed in the code path, with the remaining burden isolated to citation-grade Theorem-VII cleanup.'
    elif final_certificate_ready_for_code_path:
        theorem_status = 'golden-universal-theorem-codepath-strong'
        notes = 'The universal theorem is closed in the code path, but both Workstream-A and Theorem-VII still carry paper-grade cleanup.'
    elif not open_hypotheses and not residual_global_active_assumptions and not residual_non_global_hinges and statement_mode == 'one-variable':
        theorem_status = 'golden-theorem-viii-reduction-discharge-lift-conditional-one-variable-strong'
        notes = 'The discharge-aware final reduction shell is fully packaged, has no residual global assumptions or non-global hinges, and uses the one-variable envelope mode.'
    elif not open_hypotheses and not residual_global_active_assumptions and not residual_non_global_hinges and statement_mode == 'two-variable':
        theorem_status = 'golden-theorem-viii-reduction-discharge-lift-conditional-two-variable-strong'
        notes = 'The discharge-aware final reduction shell is fully packaged, has no residual global assumptions or non-global hinges, and uses the corrected two-variable envelope mode.'
    elif not open_hypotheses:
        theorem_status = 'golden-theorem-viii-reduction-discharge-lift-front-complete'
        notes = 'The discharge-aware final reduction front is fully packaged, and the remaining active assumptions are now separated into genuinely global assumptions versus non-global local hinges.'
    elif discharged_hypotheses:
        theorem_status = 'golden-theorem-viii-reduction-discharge-lift-conditional-partial'
        notes = 'The discharge-aware final reduction layer sharpens the remaining assumption structure, but at least one upstream theorem shell or reduction-side hypothesis is still open.'
    else:
        theorem_status = 'golden-theorem-viii-reduction-discharge-lift-failed'
        notes = 'The discharge-aware final reduction layer does not yet have a usable packaged front.'

    if discharged_identified_branch_witness_width is not None and theorem_status != 'golden-theorem-viii-reduction-discharge-lift-failed':
        notes += f" Discharged identified branch witness width carried into Theorem VIII: {float(discharged_identified_branch_witness_width):.6g}."
        overlap_width = _coerce_float(threshold_identification_discharge.get('overlap_width'))
        if overlap_width is not None:
            notes += f" Identification discharge overlap width: {float(overlap_width):.6g}."
        if inherited_current_top_gap_scale is not None:
            notes += f" Current exploratory top-gap scale inherited from Theorem VI: {float(inherited_current_top_gap_scale):.6g}."
        if inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin is not None:
            notes += f" Witness lower edge minus current most dangerous challenger upper: {float(inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin):.6g}."
        if inherited_discharged_witness_geometry_status is not None:
            notes += f" Inherited witness-geometry status: {str(inherited_discharged_witness_geometry_status)}."
        if inherited_current_near_top_exhaustion_status is not None:
            notes += f" Inherited near-top exhaustion status: {str(inherited_current_near_top_exhaustion_status)}."
        if inherited_current_near_top_exhaustion_margin is not None:
            notes += f" Inherited near-top dominance margin: {float(inherited_current_near_top_exhaustion_margin):.6g}."
        notes += f" Current reduction geometry status: {str(current_reduction_geometry_status)}."
        if current_reduction_geometry_min_margin is not None:
            notes += f" Current reduction geometry minimum certified margin: {float(current_reduction_geometry_min_margin):.6g}."
    if theorem_iii_final_certified and theorem_status != 'golden-theorem-viii-reduction-discharge-lift-failed':
        notes += ' Theorem III is consumed here as a final infinite-dimensional lower theorem.'
    if theorem_iv_final_certified and theorem_status != 'golden-theorem-viii-reduction-discharge-lift-failed':
        notes += ' Theorem IV is consumed here as a final analytic incompatibility theorem.'
    if theorem_v_final_certified and theorem_status != 'golden-theorem-viii-reduction-discharge-lift-failed':
        notes += ' Theorem V is consumed here as a final continuation/transport theorem.'
    if remaining_workstream_paper_grade_burden and theorem_status != 'golden-theorem-viii-reduction-discharge-lift-failed':
        notes += f" Workstream-A paper-grade burden: {', '.join(remaining_workstream_paper_grade_burden)}."
    if remaining_exhaustion_paper_grade_burden and theorem_status != 'golden-theorem-viii-reduction-discharge-lift-failed':
        notes += f" Theorem-VII paper-grade burden: {', '.join(remaining_exhaustion_paper_grade_burden)}."

    return GoldenTheoremVIIIReductionDischargeLiftCertificate(
        rho=rho,
        family_label=family_label,
        statement_mode=statement_mode,
        baseline_reduction_shell=baseline,
        theorem_viii_shell=theorem_viii,
        theorem_vii_discharge_shell=theorem_vii_discharge,
        theorem_vi_discharge_shell=theorem_vi_discharge,
        threshold_identification_discharge_shell=threshold_identification_discharge,
        theorem_viii_final_discharge_support_certificate=final_discharge_support,
        theorem_iii_final_certified=bool(theorem_iii_final_certified),
        theorem_iii_lower_interval=None if theorem_iii_lower_interval is None else [float(x) for x in theorem_iii_lower_interval],
        theorem_iv_final_certified=bool(theorem_iv_final_certified),
        theorem_v_final_certified=bool(theorem_v_final_certified),
        theorem_vi_final_certified=bool(theorem_vi_final_certified),
        theorem_vii_codepath_final=bool(theorem_vii_summary['codepath_final']),
        theorem_vii_papergrade_final=bool(theorem_vii_summary['papergrade_final']),
        theorem_vii_residual_citation_burden=[str(x) for x in theorem_vii_summary['residual_citation_burden']],
        workstream_consumption_summary=dict(workstream_summary),
        theorem_v_target_interval=None if theorem_v_target_interval is None else [float(x) for x in theorem_v_target_interval],
        theorem_v_gap_preservation_certified=theorem_v_gap_preservation_certified,
        all_upstream_theorems_consumed=bool(all_upstream_theorems_consumed),
        final_threshold_law_ready=bool(final_threshold_law_ready),
        final_golden_top_gap_ready=bool(final_golden_top_gap_ready),
        final_universal_statement=str(final_universal_statement),
        golden_maximality_conclusion_certified=bool(golden_maximality_conclusion_certified),
        modular_orbit_uniqueness_certified=bool(modular_orbit_uniqueness_certified),
        remaining_workstream_paper_grade_burden=[str(x) for x in remaining_workstream_paper_grade_burden],
        remaining_exhaustion_paper_grade_burden=[str(x) for x in remaining_exhaustion_paper_grade_burden],
        remaining_true_mathematical_burden=[str(x) for x in remaining_true_mathematical_burden],
        final_certificate_ready_for_paper=bool(final_certificate_ready_for_paper),
        final_certificate_ready_for_code_path=bool(final_certificate_ready_for_code_path),
        discharged_identified_branch_witness_interval=discharged_identified_branch_witness_interval,
        discharged_identified_branch_witness_width=discharged_identified_branch_witness_width,
        discharged_identified_branch_witness_source=discharged_identified_branch_witness_source,
        discharged_identified_branch_witness_status=discharged_identified_branch_witness_status,
        inherited_current_top_gap_scale=inherited_current_top_gap_scale,
        inherited_current_most_dangerous_challenger_upper=inherited_current_most_dangerous_challenger_upper,
        inherited_discharged_witness_width_vs_current_top_gap_margin=inherited_discharged_witness_width_vs_current_top_gap_margin,
        inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin=inherited_discharged_witness_lower_vs_current_near_top_challenger_upper_margin,
        inherited_discharged_witness_geometry_min_margin=inherited_discharged_witness_geometry_min_margin,
        inherited_discharged_witness_geometry_status=inherited_discharged_witness_geometry_status,
        inherited_current_near_top_exhaustion_upper_bound=inherited_current_near_top_exhaustion_upper_bound,
        inherited_current_near_top_exhaustion_margin=inherited_current_near_top_exhaustion_margin,
        inherited_current_near_top_exhaustion_pending_count=inherited_current_near_top_exhaustion_pending_count,
        inherited_current_near_top_exhaustion_source=inherited_current_near_top_exhaustion_source,
        inherited_current_near_top_exhaustion_status=inherited_current_near_top_exhaustion_status,
        current_reduction_geometry_witness_vs_overlap_margin=current_reduction_geometry_witness_vs_overlap_margin,
        current_reduction_geometry_top_gap_scale=current_reduction_geometry_top_gap_scale,
        current_reduction_geometry_challenger_upper_bound=current_reduction_geometry_challenger_upper_bound,
        current_reduction_geometry_exhaustion_upper_bound=current_reduction_geometry_exhaustion_upper_bound,
        current_reduction_geometry_witness_width_vs_top_gap_margin=current_reduction_geometry_witness_width_vs_top_gap_margin,
        current_reduction_geometry_witness_lower_vs_challenger_upper_margin=current_reduction_geometry_witness_lower_vs_challenger_upper_margin,
        current_reduction_geometry_pending_count=current_reduction_geometry_pending_count,
        current_reduction_geometry_min_margin=current_reduction_geometry_min_margin,
        current_reduction_geometry_source=current_reduction_geometry_source,
        current_reduction_geometry_status=current_reduction_geometry_status,
        residual_global_active_assumptions=residual_global_active_assumptions,
        residual_non_global_hinges=residual_non_global_hinges,
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



def build_golden_theorem_viii_discharge_certificate(*args, **kwargs) -> GoldenTheoremVIIIReductionDischargeLiftCertificate:
    return build_golden_theorem_viii_reduction_discharge_lift_certificate(*args, **kwargs)


__all__ = [
    'NON_GLOBAL_HINGE_ASSUMPTIONS',
    'TheoremVIIIReductionDischargeHypothesisRow',
    'TheoremVIIIReductionDischargeAssumptionRow',
    'GoldenTheoremVIIIReductionDischargeLiftCertificate',
    'build_golden_theorem_viii_reduction_discharge_lift_certificate',
    'build_golden_theorem_viii_discharge_certificate',
]
