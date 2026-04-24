from __future__ import annotations

"""Conditional theorem packaging for the final golden-maximality reduction.

The repository now has theorem-facing shells for:

* Theorem IV analytic incompatibility,
* Theorem V transport / continuation,
* Theorem II->V threshold identification,
* Theorem VI eta-envelope packaging, and
* Theorem VII challenger exhaustion.

What is still missing is the last reduction step turning those packaged fronts into
an explicit conditional statement of golden maximality.  This module does not claim
that the final universal theorem is proved.  Instead it records which reduction-side
hypotheses are already discharged, which statement mode the current Theorem-VI shell
is using, and which remaining assumptions would promote the present theorem shells
into a conditional Theorem-VIII-style statement.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .golden_aposteriori import build_golden_theorem_iii_certificate, golden_inverse
from .standard_map import HarmonicFamily
from .theorem_iv_analytic_lift import build_golden_theorem_iv_certificate
from .theorem_v_transport_lift import build_golden_theorem_v_certificate
from .theorem_v_downstream_utils import (
    extract_theorem_v_gap_preservation_certified,
    extract_theorem_v_target_interval,
    theorem_v_is_downstream_final,
)
from .threshold_identification_lift import build_golden_theorem_ii_to_v_identification_certificate
from .theorem_vi_envelope_lift import build_golden_theorem_vi_certificate
from .theorem_vii_exhaustion_lift import build_golden_theorem_vii_certificate
from .theorem_vii_exhaustion_discharge import build_golden_theorem_vii_discharge_certificate
from .theorem_i_ii_workstream_lift import build_golden_theorem_i_ii_workstream_lift_certificate
from .theorem_viii_support_utils import is_theorem_vi_final_or_stage107_promotable, mark_assumption_rows_from_support
from .theorem_viii_final_discharge_support import extract_support_certificates


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'



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
    if str(cert.get('theorem_status', '')) == 'golden-theorem-v-compressed-contract-strong':
        return True
    compressed = dict(cert.get('compressed_contract', {}))
    if compressed.get('theorem_status') == 'golden-theorem-v-compressed-contract-strong':
        return True
    return _status_rank(str(cert.get('theorem_status', ''))) >= 3 and len(cert.get('open_hypotheses', [])) == 0


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)

def _candidate_sources_for_reduction_tree(root: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    sources: list[Mapping[str, Any]] = [root]
    for key in (
        'identification_shell',
        'threshold_identification_shell',
        'threshold_identification_discharge_shell',
        'transport_discharge_shell',
        'theorem_vi_shell',
        'theorem_vi_discharge_shell',
        'theorem_vii_shell',
    ):
        value = root.get(key)
        if isinstance(value, Mapping):
            sources.append(value)
    transport = root.get('transport_discharge_shell')
    if isinstance(transport, Mapping):
        discharge = transport.get('threshold_identification_discharge_shell')
        if isinstance(discharge, Mapping):
            sources.append(discharge)
            ident = discharge.get('identification_shell')
            if isinstance(ident, Mapping):
                sources.append(ident)
    vi_shell = root.get('theorem_vi_shell')
    if isinstance(vi_shell, Mapping):
        ident = vi_shell.get('threshold_identification_shell')
        if isinstance(ident, Mapping):
            sources.append(ident)
    vi_discharge = root.get('theorem_vi_discharge_shell')
    if isinstance(vi_discharge, Mapping):
        nested = _candidate_sources_for_reduction_tree(vi_discharge)
        for source in nested:
            if source not in sources:
                sources.append(source)
    return sources


def _find_nested_mapping_with_key(root: Any, key: str) -> dict[str, Any] | None:
    if isinstance(root, Mapping):
        for source in _candidate_sources_for_reduction_tree(root):
            value = source.get(key)
            if isinstance(value, Mapping):
                return dict(value)
    return None



def _extract_reduction_witness(identification: Mapping[str, Any], theorem_vi: Mapping[str, Any]) -> tuple[list[float] | None, float | None, str | None, str | None]:
    direct_witness = identification.get('discharged_bridge_native_tail_witness_interval')
    direct_width = _coerce_float(identification.get('discharged_bridge_native_tail_witness_width'))
    direct_source = identification.get('bridge_native_tail_witness_source')
    direct_status = identification.get('bridge_native_tail_witness_status')
    if isinstance(direct_witness, Sequence) and len(direct_witness) == 2:
        lo = float(direct_witness[0]); hi = float(direct_witness[1])
        if hi >= lo:
            return [lo, hi], direct_width, None if direct_source is None else str(direct_source), None if direct_status is None else str(direct_status)

    direct_witness = theorem_vi.get('discharged_identified_branch_witness_interval')
    direct_width = _coerce_float(theorem_vi.get('discharged_identified_branch_witness_width'))
    direct_source = theorem_vi.get('discharged_identified_branch_witness_source')
    direct_status = theorem_vi.get('discharged_identified_branch_witness_status')
    if isinstance(direct_witness, Sequence) and len(direct_witness) == 2:
        lo = float(direct_witness[0]); hi = float(direct_witness[1])
        if hi >= lo:
            return [lo, hi], direct_width, None if direct_source is None else str(direct_source), None if direct_status is None else str(direct_status)

    witness = identification.get('identified_bridge_native_tail_witness_interval')
    width = _coerce_float(identification.get('identified_bridge_native_tail_witness_width'))
    source = identification.get('bridge_native_tail_witness_source')
    status = identification.get('bridge_native_tail_witness_status')
    if isinstance(witness, Sequence) and len(witness) == 2:
        lo = float(witness[0]); hi = float(witness[1])
        if hi >= lo:
            return [lo, hi], width, None if source is None else str(source), None if status is None else str(status)
    return None, None, None, None


def _extract_vi_gap_geometry(theorem_vi: Mapping[str, Any]) -> tuple[float | None, float | None]:
    top_gap = _coerce_float(theorem_vi.get('current_top_gap_scale'))
    challenger_upper = _coerce_float(theorem_vi.get('current_most_dangerous_challenger_upper'))
    if top_gap is not None or challenger_upper is not None:
        return top_gap, challenger_upper

    near_relation = dict((theorem_vi.get('near_top_challenger_surface') or {}).get('near_top_relation', {}))
    top_gap = _coerce_float(near_relation.get('golden_lower_minus_most_dangerous_upper'))
    challenger_upper = _coerce_float(near_relation.get('most_dangerous_threshold_upper'))
    if top_gap is not None or challenger_upper is not None:
        return top_gap, challenger_upper

    proto_relation = dict((theorem_vi.get('proto_envelope_bridge') or {}).get('proto_envelope_relation', {}))
    if top_gap is None:
        top_gap = _coerce_float(proto_relation.get('anchor_lower_minus_panel_nongolden_upper'))
    if challenger_upper is None:
        challenger_upper = _coerce_float(proto_relation.get('panel_nongolden_max_upper_bound'))
    return top_gap, challenger_upper


def _extract_vii_near_top_exhaustion_summary(theorem_vii: Mapping[str, Any], theorem_vi: Mapping[str, Any], *, reference_lower_bound: float) -> tuple[float | None, float | None, int, str | None, str | None]:
    upper = _coerce_float(theorem_vii.get('current_near_top_exhaustion_upper_bound'))
    margin = _coerce_float(theorem_vii.get('current_near_top_exhaustion_margin'))
    pending = theorem_vii.get('current_near_top_exhaustion_pending_count')
    source = theorem_vii.get('current_near_top_exhaustion_source')
    status = theorem_vii.get('current_near_top_exhaustion_status')
    if any(x is not None for x in (upper, margin, pending, source, status)):
        return upper, margin, int(0 if pending is None else pending), None if source is None else str(source), None if status is None else str(status)

    termination = dict(theorem_vii.get('termination_aware_search_report', {}))
    active = int(termination.get('active_count', 0))
    deferred = int(termination.get('deferred_count', 0))
    undecided = int(termination.get('undecided_count', 0))
    overlapping = int(termination.get('overlapping_count', 0))
    pending_count = active + deferred + undecided + overlapping
    upper, _ = _extract_vi_gap_geometry(theorem_vi)
    if upper is None:
        upper = _coerce_float(theorem_vi.get('current_most_dangerous_challenger_upper'))
    # correct accidental top-gap assignment by re-reading challenger upper when needed
    if upper is not None and theorem_vi.get('current_most_dangerous_challenger_upper') is None:
        _, challenger_upper = _extract_vi_gap_geometry(theorem_vi)
        upper = challenger_upper
    margin = None if upper is None else float(reference_lower_bound - upper)
    if upper is None:
        status = 'near-top-exhaustion-summary-missing'
    elif margin is not None and margin > 0.0 and pending_count == 0:
        status = 'near-top-exhaustion-strong'
    elif margin is not None and margin > 0.0:
        status = 'near-top-exhaustion-partial'
    else:
        status = 'near-top-exhaustion-incompatible'
    return upper, margin, pending_count, 'theorem_vii_shell.termination_aware_search_report', status


def _summarize_current_reduction_geometry(identification: Mapping[str, Any], theorem_vi: Mapping[str, Any], theorem_vii: Mapping[str, Any], *, reference_lower_bound: float) -> tuple[float | None, float | None, float | None, float | None, float | None, float | None, int, float | None, str | None, str]:
    witness, witness_width, _, _ = _extract_reduction_witness(identification, theorem_vi)
    window = identification.get('overlap_window')
    window_width = _coerce_float(identification.get('overlap_width'))
    if not (isinstance(window, Sequence) and len(window) == 2):
        window = identification.get('identified_window')
        if window_width is None and isinstance(window, Sequence) and len(window) == 2:
            window_width = float(window[1]) - float(window[0])

    overlap_contains_witness = False
    if witness is not None and isinstance(window, Sequence) and len(window) == 2:
        overlap_contains_witness = float(window[0]) - 1.0e-15 <= float(witness[0]) and float(witness[1]) <= float(window[1]) + 1.0e-15
    witness_vs_overlap_margin = None if witness_width is None or window_width is None else float(window_width - witness_width)

    top_gap_scale, challenger_upper = _extract_vi_gap_geometry(theorem_vi)
    witness_lower = None if witness is None else float(witness[0])
    witness_width_vs_top_gap_margin = None if witness_width is None or top_gap_scale is None else float(top_gap_scale - witness_width)
    witness_lower_vs_challenger_upper_margin = None if witness_lower is None or challenger_upper is None else float(witness_lower - challenger_upper)

    exhaustion_upper, exhaustion_margin, pending_count, exhaustion_source, exhaustion_status = _extract_vii_near_top_exhaustion_summary(theorem_vii, theorem_vi, reference_lower_bound=reference_lower_bound)

    margins = [x for x in (witness_vs_overlap_margin, witness_width_vs_top_gap_margin, witness_lower_vs_challenger_upper_margin, exhaustion_margin) if x is not None]
    min_margin = None if not margins else float(min(margins))

    source_parts: list[str] = []
    if window is not None:
        source_parts.append('threshold_identification.current_window')
    if top_gap_scale is not None or challenger_upper is not None:
        source_parts.append('theorem_vi.current_gap_geometry')
    if exhaustion_upper is not None or exhaustion_source is not None:
        source_parts.append('theorem_vii.current_near_top_exhaustion_summary')
    source = ' + '.join(source_parts) if source_parts else None

    if witness is None:
        status = 'current-reduction-geometry-missing'
    elif not overlap_contains_witness or (witness_vs_overlap_margin is not None and witness_vs_overlap_margin < -1.0e-15):
        status = 'current-reduction-geometry-incompatible'
    elif (
        witness_width_vs_top_gap_margin is not None and witness_width_vs_top_gap_margin >= -1.0e-15
        and witness_lower_vs_challenger_upper_margin is not None and witness_lower_vs_challenger_upper_margin > 0.0
        and exhaustion_margin is not None and exhaustion_margin > 0.0
        and int(pending_count) == 0
    ):
        status = 'current-reduction-geometry-strong'
    elif min_margin is not None and min_margin >= -1.0e-15:
        status = 'current-reduction-geometry-partial'
    elif margins:
        status = 'current-reduction-geometry-incompatible'
    else:
        status = 'current-reduction-geometry-unresolved'

    return (
        witness_vs_overlap_margin,
        top_gap_scale,
        challenger_upper,
        exhaustion_upper,
        witness_width_vs_top_gap_margin,
        witness_lower_vs_challenger_upper_margin,
        int(pending_count),
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
class TheoremVIIIReductionHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVIIIReductionAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremVIIIReductionLiftCertificate:
    rho: float
    family_label: str
    statement_mode: str
    theorem_iii_shell: dict[str, Any]
    theorem_iv_shell: dict[str, Any]
    theorem_v_shell: dict[str, Any]
    threshold_identification_shell: dict[str, Any]
    theorem_vi_shell: dict[str, Any]
    theorem_vii_shell: dict[str, Any]
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
    final_threshold_law_ready: bool
    final_golden_top_gap_ready: bool
    final_universal_implication_ready: bool
    workstream_residual_caveat: list[str]
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
    hypotheses: list[TheoremVIIIReductionHypothesisRow]
    assumptions: list[TheoremVIIIReductionAssumptionRow]
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
            'theorem_iii_shell': dict(self.theorem_iii_shell),
            'theorem_iv_shell': dict(self.theorem_iv_shell),
            'theorem_v_shell': dict(self.theorem_v_shell),
            'threshold_identification_shell': dict(self.threshold_identification_shell),
            'theorem_vi_shell': dict(self.theorem_vi_shell),
            'theorem_vii_shell': dict(self.theorem_vii_shell),
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
            'final_threshold_law_ready': bool(self.final_threshold_law_ready),
            'final_golden_top_gap_ready': bool(self.final_golden_top_gap_ready),
            'final_universal_implication_ready': bool(self.final_universal_implication_ready),
            'workstream_residual_caveat': [str(x) for x in self.workstream_residual_caveat],
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



def _default_reduction_assumptions() -> list[TheoremVIIIReductionAssumptionRow]:
    return [
        TheoremVIIIReductionAssumptionRow(
            name='final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality',
            assumed=False,
            source='Theorem-VIII reduction lift assumption',
            note='Promote the packaged threshold-identification, envelope, and exhaustion statements into the final golden-maximality reduction theorem.',
        ),
        TheoremVIIIReductionAssumptionRow(
            name='gl2z_orbit_uniqueness_and_normalization_closed',
            assumed=False,
            source='Theorem-VIII reduction lift assumption',
            note='Close the normalization / modular-orbit uniqueness conventions so the final maximizer statement is genuinely unique up to the GL2(Z) golden orbit.',
        ),
        TheoremVIIIReductionAssumptionRow(
            name='final_universality_class_matches_reduction_statement',
            assumed=False,
            source='Theorem-VIII reduction lift assumption',
            note='Match the final reduction statement to the actual renormalization-stable universality class used by the theorem shells.',
        ),
    ]



def _build_hypotheses(*, theorem_iii: Mapping[str, Any], theorem_iv: Mapping[str, Any], theorem_v: Mapping[str, Any], identification: Mapping[str, Any], theorem_vi: Mapping[str, Any], theorem_vii: Mapping[str, Any], theorem_iii_final_certified: bool, theorem_iv_final_certified: bool, theorem_v_final_certified: bool, theorem_v_gap_preservation_certified: bool | None, current_reduction_geometry_min_margin: float | None, current_reduction_geometry_status: str | None) -> list[TheoremVIIIReductionHypothesisRow]:
    statement_mode = str(theorem_vi.get('statement_mode', 'unresolved'))
    rows = [
        TheoremVIIIReductionHypothesisRow(
            name='theorem_iii_final_certified',
            satisfied=bool(theorem_iii_final_certified),
            source='Theorem-III final lower theorem',
            note='Theorem III is available as a final infinite-dimensional lower theorem below threshold.',
            margin=None,
        ),
        TheoremVIIIReductionHypothesisRow(
            name='theorem_iv_front_complete',
            satisfied=_is_front_complete(theorem_iv),
            source='Theorem-IV shell',
            note='The analytic incompatibility shell is packaged with no remaining open front hypotheses.',
            margin=None,
        ),
        TheoremVIIIReductionHypothesisRow(
            name='theorem_iv_final_certified',
            satisfied=bool(theorem_iv_final_certified),
            source='Theorem-IV final incompatibility theorem',
            note='Theorem IV is available as a final analytic incompatibility theorem rather than only a front-complete shell.',
            margin=None,
        ),
        TheoremVIIIReductionHypothesisRow(
            name='theorem_v_front_complete',
            satisfied=_is_front_complete(theorem_v),
            source='Theorem-V shell',
            note='The transport / continuation shell is packaged with no remaining open front hypotheses.',
            margin=None,
        ),
        TheoremVIIIReductionHypothesisRow(
            name='theorem_v_final_certified',
            satisfied=bool(theorem_v_final_certified),
            source='Theorem-V final transport theorem',
            note='Theorem V is available as a final continuation/transport theorem rather than only a front-complete shell.',
            margin=None,
        ),
        TheoremVIIIReductionHypothesisRow(
            name='theorem_v_gap_preservation_certified',
            satisfied=bool(theorem_v_gap_preservation_certified),
            source='Theorem-V final error law',
            note='The final Theorem-V error law preserves the golden-gap geometry needed downstream by reduction.',
            margin=None,
        ),
        TheoremVIIIReductionHypothesisRow(
            name='threshold_identification_front_complete',
            satisfied=_is_front_complete(identification),
            source='Theorem-II->V identification shell',
            note='The renormalization-to-threshold identification shell is packaged with no remaining open front hypotheses.',
            margin=None,
        ),
        TheoremVIIIReductionHypothesisRow(
            name='theorem_vi_front_complete',
            satisfied=_is_front_complete(theorem_vi),
            source='Theorem-VI shell',
            note='The eta-envelope shell is packaged with no remaining open front hypotheses.',
            margin=None,
        ),
        TheoremVIIIReductionHypothesisRow(
            name='theorem_vii_front_complete',
            satisfied=_is_front_complete(theorem_vii),
            source='Theorem-VII shell',
            note='The challenger-exhaustion shell is packaged with no remaining open front hypotheses.',
            margin=None,
        ),
        TheoremVIIIReductionHypothesisRow(
            name='theorem_vi_statement_mode_resolved',
            satisfied=statement_mode in {'one-variable', 'two-variable'},
            source='Theorem-VI shell',
            note='The final arithmetic-threshold comparison statement is resolved into a one-variable or corrected two-variable form.',
            margin=None,
        ),
    ]
    if not theorem_iii_final_certified and 'analytic_invariant_circle_exists' not in theorem_iii:
        rows = [row for row in rows if row.name != 'theorem_iii_final_certified']
    if not theorem_iv_final_certified and 'analytic_incompatibility_certified' not in theorem_iv and 'nonexistence_contradiction_certified' not in theorem_iv:
        rows = [row for row in rows if row.name != 'theorem_iv_final_certified']
    if not theorem_v_final_certified and theorem_v_gap_preservation_certified is None:
        rows = [row for row in rows if row.name not in {'theorem_v_final_certified', 'theorem_v_gap_preservation_certified'}]
    if current_reduction_geometry_status not in {None, 'current-reduction-geometry-missing'}:
        rows.extend([
            TheoremVIIIReductionHypothesisRow(
                name='current_reduction_geometry_summary_available',
                satisfied=True,
                source='Theorem-VIII current reduction geometry summary',
                note='The baseline reduction shell exposes a native current reduction geometry summary tying witness localization, current top-gap geometry, and current near-top exhaustion into one object.',
                margin=current_reduction_geometry_min_margin,
            ),
            TheoremVIIIReductionHypothesisRow(
                name='current_reduction_geometry_summary_strong',
                satisfied=bool(current_reduction_geometry_status == 'current-reduction-geometry-strong'),
                source='Theorem-VIII current reduction geometry summary',
                note='The native current reduction geometry summary is already strong enough to localize the current witness against the present challenger and exhaustion geometry.',
                margin=current_reduction_geometry_min_margin,
            ),
        ])
    return rows



def build_golden_theorem_viii_reduction_lift_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    theorem_iii_certificate: Mapping[str, Any] | None = None,
    theorem_iv_certificate: Mapping[str, Any] | None = None,
    theorem_v_certificate: Mapping[str, Any] | None = None,
    threshold_identification_certificate: Mapping[str, Any] | None = None,
    threshold_identification_discharge_certificate: Mapping[str, Any] | None = None,
    theorem_vi_certificate: Mapping[str, Any] | None = None,
    theorem_vi_envelope_discharge_certificate: Mapping[str, Any] | None = None,
    theorem_vii_certificate: Mapping[str, Any] | None = None,
    theorem_vii_exhaustion_discharge_certificate: Mapping[str, Any] | None = None,
    theorem_i_ii_workstream_certificate: Mapping[str, Any] | None = None,
    theorem_viii_final_discharge_support_certificate: Mapping[str, Any] | None = None,
    assume_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality: bool = False,
    assume_gl2z_orbit_uniqueness_and_normalization_closed: bool = False,
    assume_final_universality_class_matches_reduction_statement: bool = False,
    **kwargs: Any,
) -> GoldenTheoremVIIIReductionLiftCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    inferred_from_vii_discharge = dict(theorem_vii_exhaustion_discharge_certificate) if theorem_vii_exhaustion_discharge_certificate is not None else None
    theorem_iii = dict(theorem_iii_certificate) if theorem_iii_certificate is not None else None

    if threshold_identification_discharge_certificate is not None:
        identification = dict(threshold_identification_discharge_certificate)
    elif inferred_from_vii_discharge is not None:
        identification = dict(inferred_from_vii_discharge.get('theorem_vi_discharge_shell', {}).get('threshold_identification_discharge_shell', {}))
    elif threshold_identification_certificate is not None:
        identification = dict(threshold_identification_certificate)
    elif theorem_vi_envelope_discharge_certificate is not None:
        identification = _find_nested_mapping_with_key(theorem_vi_envelope_discharge_certificate, 'threshold_identification_discharge_shell') or {}
    elif theorem_vi_certificate is not None:
        identification = _find_nested_mapping_with_key(theorem_vi_certificate, 'threshold_identification_shell') or {}
    else:
        identification = build_golden_theorem_ii_to_v_identification_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_ii_to_v_identification_certificate, kwargs),
        ).to_dict()

    if theorem_iv_certificate is not None:
        theorem_iv = dict(theorem_iv_certificate)
    else:
        theorem_iv = None
        for candidate in (
            identification,
            theorem_vi_envelope_discharge_certificate,
            theorem_vi_certificate,
            inferred_from_vii_discharge,
            theorem_vii_exhaustion_discharge_certificate,
            theorem_vii_certificate,
        ):
            if candidate:
                theorem_iv = _find_nested_mapping_with_key(candidate, 'theorem_iv_shell')
                if theorem_iv is not None:
                    break
        theorem_iv = theorem_iv or build_golden_theorem_iv_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_iv_certificate, kwargs),
        ).to_dict()

    if theorem_v_certificate is not None:
        theorem_v = dict(theorem_v_certificate)
    else:
        theorem_v = None
        for candidate in (
            identification,
            theorem_vi_envelope_discharge_certificate,
            theorem_vi_certificate,
            inferred_from_vii_discharge,
            theorem_vii_exhaustion_discharge_certificate,
            theorem_vii_certificate,
        ):
            if candidate:
                theorem_v = _find_nested_mapping_with_key(candidate, 'theorem_v_shell')
                if theorem_v is not None:
                    break
        theorem_v = theorem_v or build_golden_theorem_v_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_v_certificate, kwargs),
        ).to_dict()

    if theorem_vi_envelope_discharge_certificate is not None:
        theorem_vi = dict(theorem_vi_envelope_discharge_certificate)
    elif inferred_from_vii_discharge is not None:
        theorem_vi = dict(inferred_from_vii_discharge.get('theorem_vi_discharge_shell', {}))
    elif theorem_vi_certificate is not None:
        theorem_vi = dict(theorem_vi_certificate)
    else:
        theorem_vi = build_golden_theorem_vi_certificate(
            base_K_values=base_K_values,
            family=family,
            family_label=family_label,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_vi_certificate, kwargs),
        ).to_dict()

    if theorem_vii_exhaustion_discharge_certificate is not None:
        theorem_vii = dict(theorem_vii_exhaustion_discharge_certificate)
    elif theorem_vii_certificate is not None:
        theorem_vii = dict(theorem_vii_certificate)
    else:
        theorem_vii = build_golden_theorem_vii_certificate(
            base_K_values=base_K_values,
            family=family,
            **_filter_kwargs(build_golden_theorem_vii_certificate, kwargs),
        ).to_dict()

    if theorem_i_ii_workstream_certificate is not None:
        workstream = dict(theorem_i_ii_workstream_certificate)
    else:
        inferred_workstream = None
        for candidate in (identification, theorem_vi, theorem_vii):
            if candidate:
                inferred_workstream = _find_nested_mapping_with_key(candidate, 'theorem_i_ii_shell') or _find_nested_mapping_with_key(candidate, 'workstream_shell')
                if inferred_workstream:
                    break
        if inferred_workstream is not None:
            workstream = dict(inferred_workstream)
        elif identification or theorem_vi or theorem_vii or threshold_identification_certificate is not None or theorem_vi_certificate is not None or theorem_vii_certificate is not None or theorem_vii_exhaustion_discharge_certificate is not None:
            workstream = {
                'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete',
                'open_hypotheses': [],
                'active_assumptions': [],
                'workstream_codepath_strong': True,
                'workstream_papergrade_strong': False,
                'workstream_residual_caveat': ['inferred-upstream-workstream-placeholder'],
                'notes': 'A lightweight upstream workstream placeholder was used because downstream theorem shells were already present and no explicit Theorem I-II workstream certificate was supplied.',
            }
        else:
            workstream = build_golden_theorem_i_ii_workstream_lift_certificate(
                family=family,
                **_filter_kwargs(build_golden_theorem_i_ii_workstream_lift_certificate, kwargs),
            ).to_dict()

    if theorem_iii is None:
        inferred_theorem_iii = None
        for candidate in (
            inferred_from_vii_discharge,
            identification,
            theorem_vi,
            theorem_vii,
            threshold_identification_certificate,
            theorem_vi_certificate,
            theorem_vii_certificate,
        ):
            if candidate:
                inferred_theorem_iii = _find_nested_mapping_with_key(candidate, 'theorem_iii_shell')
                if inferred_theorem_iii is not None:
                    break
        if inferred_theorem_iii is not None:
            theorem_iii = dict(inferred_theorem_iii)
        elif (identification or theorem_vi or theorem_vii or threshold_identification_certificate is not None or theorem_vi_certificate is not None or theorem_vii_certificate is not None or theorem_vii_exhaustion_discharge_certificate is not None) and 'theorem_v_compressed_certificate' not in kwargs:
            theorem_iii = {
                'theorem_status': 'golden-theorem-iii-lower-corridor-inferred-placeholder',
                'open_hypotheses': [],
                'active_assumptions': [],
                'notes': 'A lightweight Theorem III placeholder was used because downstream theorem shells were already present and no explicit Theorem III certificate was supplied.',
            }
        else:
            theorem_iii = build_golden_theorem_iii_certificate(
                base_K_values=base_K_values,
                family=family,
                rho=rho,
                **_filter_kwargs(build_golden_theorem_iii_certificate, kwargs),
            ).to_dict()

    theorem_iii_final_certified = bool(str(theorem_iii.get('theorem_iii_final_status', theorem_iii.get('theorem_status', ''))).startswith('golden-theorem-iii-final-strong'))
    theorem_iii_lower_interval = theorem_iii.get('certified_below_threshold_interval')
    theorem_iv_final_certified = bool(str(theorem_iv.get('theorem_status', '')).startswith('golden-theorem-iv-final-strong'))
    theorem_v_final_certified = theorem_v_is_downstream_final(theorem_v)
    final_discharge_support = extract_support_certificates(theorem_viii_final_discharge_support_certificate) or extract_support_certificates(kwargs.get('theorem_viii_final_discharge_support_certificate'))
    theorem_vi_final_certified = is_theorem_vi_final_or_stage107_promotable(theorem_vi, final_discharge_support)
    theorem_vii_summary = _summarize_theorem_vii_consumption(theorem_vii)
    workstream_summary = _summarize_workstream_consumption(workstream)
    theorem_v_target_interval = extract_theorem_v_target_interval(theorem_v)
    theorem_v_gap_preservation_certified = extract_theorem_v_gap_preservation_certified(theorem_v)

    reference_lower_bound = _coerce_float(theorem_vii.get('reference_lower_bound'))
    if reference_lower_bound is None:
        reference_lower_bound = float(min(float(x) for x in base_K_values))

    current_reduction_geometry_witness_vs_overlap_margin, current_reduction_geometry_top_gap_scale, current_reduction_geometry_challenger_upper_bound, current_reduction_geometry_exhaustion_upper_bound, current_reduction_geometry_witness_width_vs_top_gap_margin, current_reduction_geometry_witness_lower_vs_challenger_upper_margin, current_reduction_geometry_pending_count, current_reduction_geometry_min_margin, current_reduction_geometry_source, current_reduction_geometry_status = _summarize_current_reduction_geometry(
        identification,
        theorem_vi,
        theorem_vii,
        reference_lower_bound=reference_lower_bound,
    )

    final_threshold_law_ready = bool(
        theorem_iii_final_certified
        and theorem_iv_final_certified
        and theorem_v_final_certified
        and bool(theorem_v_gap_preservation_certified)
        and theorem_vi_final_certified
        and theorem_vii_summary['codepath_final']
        and _is_front_complete(identification)
    )
    final_golden_top_gap_ready = bool(
        theorem_vi_final_certified
        and theorem_vii_summary['codepath_final']
        and current_reduction_geometry_status == 'current-reduction-geometry-strong'
    )
    final_universal_implication_ready = bool(final_threshold_law_ready and final_golden_top_gap_ready and workstream_summary['codepath_strong'])
    workstream_residual_caveat = [str(x) for x in workstream_summary['residual_caveat']]

    assumptions = _default_reduction_assumptions()
    assumption_map = {
        'final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality': bool(assume_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality),
        'gl2z_orbit_uniqueness_and_normalization_closed': bool(assume_gl2z_orbit_uniqueness_and_normalization_closed),
        'final_universality_class_matches_reduction_statement': bool(assume_final_universality_class_matches_reduction_statement),
    }
    for row in assumptions:
        row.assumed = bool(assumption_map.get(row.name, False))
    assumptions = mark_assumption_rows_from_support(assumptions, final_discharge_support)

    hypotheses = _build_hypotheses(
        theorem_iii=theorem_iii,
        theorem_iv=theorem_iv,
        theorem_v=theorem_v,
        identification=identification,
        theorem_vi=theorem_vi,
        theorem_vii=theorem_vii,
        theorem_iii_final_certified=theorem_iii_final_certified,
        theorem_iv_final_certified=theorem_iv_final_certified,
        theorem_v_final_certified=theorem_v_final_certified,
        theorem_v_gap_preservation_certified=theorem_v_gap_preservation_certified,
        current_reduction_geometry_min_margin=current_reduction_geometry_min_margin,
        current_reduction_geometry_status=current_reduction_geometry_status,
    )
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]

    upstream_active_assumptions = sorted({
        *[str(x) for x in theorem_iii.get('residual_theorem_iii_burden', [])],
        *[str(x) for x in theorem_iv.get('active_assumptions', [])],
        *[str(x) for x in theorem_v.get('active_assumptions', [])],
        *[str(x) for x in identification.get('active_assumptions', [])],
        *[str(x) for x in theorem_vi.get('active_assumptions', [])],
        *[str(x) for x in theorem_vii.get('active_assumptions', [])],
    })
    local_active_assumptions = [row.name for row in assumptions if not row.assumed]
    active_assumptions = sorted(set(upstream_active_assumptions) | set(local_active_assumptions))

    statement_mode = str(theorem_vi.get('statement_mode', 'unresolved'))
    if final_universal_implication_ready and theorem_vii_summary['papergrade_final'] and workstream_summary['papergrade_strong']:
        theorem_status = 'golden-theorem-viii-reduction-lift-final-universal-ready'
        notes = 'The reduction lift now consumes final III/IV/V/VI content, a codepath-and-papergrade-strong VII exhaustion object, and a papergrade-strong Workstream-A package.'
    elif final_universal_implication_ready and not workstream_summary['papergrade_strong']:
        theorem_status = 'golden-theorem-viii-reduction-lift-workstream-caveat-only'
        notes = 'The live code path now supports the final universal implication chain, but the remaining residue is concentrated in Workstream-A paper-grade cleanup.'
    elif final_universal_implication_ready and not theorem_vii_summary['papergrade_final']:
        theorem_status = 'golden-theorem-viii-reduction-lift-exhaustion-citation-incomplete'
        notes = 'The live code path now supports the final universal implication chain, but Theorem VII still carries citation-grade cleanup.'
    elif not open_hypotheses and not active_assumptions and statement_mode == 'one-variable':
        theorem_status = 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong'
        notes = 'All packaged theorem fronts are closed, the envelope mode is one-variable, and no remaining reduction assumptions are active.'
    elif not open_hypotheses and not active_assumptions and statement_mode == 'two-variable':
        theorem_status = 'golden-theorem-viii-reduction-lift-conditional-two-variable-strong'
        notes = 'All packaged theorem fronts are closed, the envelope mode is two-variable, and no remaining reduction assumptions are active.'
    elif not open_hypotheses:
        theorem_status = 'golden-theorem-viii-reduction-lift-front-complete'
        notes = 'The final reduction front is fully packaged, but the remaining upstream/local assumptions are still active.'
    elif len(discharged_hypotheses) > 0:
        theorem_status = 'golden-theorem-viii-reduction-lift-conditional-partial'
        notes = 'Some final-reduction hypotheses are already packaged, but at least one theorem shell or statement-mode dependency is still open.'
    else:
        theorem_status = 'golden-theorem-viii-reduction-lift-failed'
        notes = 'The final reduction layer does not yet have a usable packaged front.'

    if current_reduction_geometry_status not in {None, 'current-reduction-geometry-missing'}:
        notes += f" Current reduction geometry status: {str(current_reduction_geometry_status)}."
        if current_reduction_geometry_min_margin is not None:
            notes += f" Current reduction geometry minimum certified margin: {float(current_reduction_geometry_min_margin):.6g}."
    if final_universal_implication_ready and theorem_status != 'golden-theorem-viii-reduction-lift-failed':
        notes += ' Final universal implication chain is now assembled at the reduction-lift level.'
    if workstream_residual_caveat and theorem_status != 'golden-theorem-viii-reduction-lift-failed':
        notes += f" Workstream-A residual caveat: {', '.join(workstream_residual_caveat)}."
    if theorem_vii_summary['residual_citation_burden'] and theorem_status != 'golden-theorem-viii-reduction-lift-failed':
        notes += f" Theorem VII residual citation burden: {', '.join(theorem_vii_summary['residual_citation_burden'])}."

    return GoldenTheoremVIIIReductionLiftCertificate(
        rho=rho,
        family_label=family_label,
        statement_mode=statement_mode,
        theorem_iii_shell=theorem_iii,
        theorem_iv_shell=theorem_iv,
        theorem_v_shell=theorem_v,
        threshold_identification_shell=identification,
        theorem_vi_shell=theorem_vi,
        theorem_vii_shell=theorem_vii,
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
        final_threshold_law_ready=bool(final_threshold_law_ready),
        final_golden_top_gap_ready=bool(final_golden_top_gap_ready),
        final_universal_implication_ready=bool(final_universal_implication_ready),
        workstream_residual_caveat=[str(x) for x in workstream_residual_caveat],
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



def build_golden_theorem_viii_certificate(*args, **kwargs) -> GoldenTheoremVIIIReductionLiftCertificate:
    return build_golden_theorem_viii_reduction_lift_certificate(*args, **kwargs)


__all__ = [
    'TheoremVIIIReductionHypothesisRow',
    'TheoremVIIIReductionAssumptionRow',
    'GoldenTheoremVIIIReductionLiftCertificate',
    'build_golden_theorem_viii_reduction_lift_certificate',
    'build_golden_theorem_viii_certificate',
]
