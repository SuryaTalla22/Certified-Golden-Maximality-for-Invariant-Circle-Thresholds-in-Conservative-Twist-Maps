from __future__ import annotations

"""Conditional theorem packaging for the current Theorem VI eta-envelope front.

The repository already has:

* a threshold-identification shell tying the current threshold-side certificates
  to the renormalization/critical-surface scaffold,
* a local ``(eta, Lambda)`` anchor via :mod:`eta_comparison`,
* a proto-envelope bridge comparing that anchor to exploratory panel data, and
* a near-top multi-class challenger layer via :mod:`eta_challenger_comparison`.

What it still lacks is the final theorem deciding whether the correct global
comparison statement is genuinely one-variable in ``eta`` or whether an extra
renormalization covariate must appear.  This module packages that situation
honestly.  It does not claim a final envelope theorem; instead it records which
front hypotheses are already discharged and which remaining assumptions would
promote the present scaffold into a conditional Theorem-VI-style statement.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .eta_challenger_comparison import (
    EtaChallengerSpec,
    build_campaign_driven_eta_challenger_comparison_certificate,
    build_near_top_eta_challenger_comparison_certificate,
)
from .eta_comparison import (
    build_eta_threshold_comparison_certificate,
    build_proto_envelope_eta_bridge_certificate,
)
from .class_campaigns import ArithmeticClassSpec, build_class_ladder_report, build_multi_class_campaign
from .envelope import (
    build_eta_global_envelope_certificate,
    build_eta_mode_obstruction_certificate,
    build_eta_mode_reduction_certificate,
    build_strict_golden_top_gap_theorem_candidate,
)
from .standard_map import HarmonicFamily
from .certification import bisection_crossing_bracket
from .threshold_identification_lift import (
    build_golden_theorem_ii_to_v_identification_certificate,
)


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"



def _filter_kwargs(fn, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    has_var_keyword = any(p.kind == p.VAR_KEYWORD for p in params.values())
    if has_var_keyword:
        return dict(kwargs)
    return {k: v for k, v in kwargs.items() if k in params}



def _status_rank(status: str) -> int:
    status = str(status)
    if status.endswith('-conditional-one-variable-strong') or status.endswith('-conditional-two-variable-strong') or status.endswith('-conditional-strong') or status.endswith('-strong'):
        return 4
    if status.endswith('-front-complete') or status.endswith('-front-only'):
        return 3
    if status.endswith('-conditional-partial') or status.endswith('-moderate') or status.endswith('-partial'):
        return 2
    if status.endswith('-weak'):
        return 1
    return 0



def _is_front_complete(cert: Mapping[str, Any]) -> bool:
    status = str(cert.get('theorem_status', ''))
    return _status_rank(status) >= 3 and len(cert.get('open_hypotheses', [])) == 0




def _has_threshold_bounded_panel(cert: Mapping[str, Any]) -> bool:
    flags = dict(cert.get('theorem_flags', {}))
    if bool(flags.get('at_least_one_threshold_bounded_challenger', False)):
        return True
    for rec in cert.get('challenger_records', []):
        if isinstance(rec, Mapping) and rec.get('threshold_upper_bound') is not None:
            return True
    return False


def _near_top_surface_needs_promotion(cert: Mapping[str, Any] | None) -> bool:
    if cert is None:
        return True
    status = str(cert.get('theorem_status', ''))
    flags = dict(cert.get('theorem_flags', {}))
    if _status_rank(status) < 2:
        return True
    if not bool(flags.get('challenger_records_available', False)):
        return True
    if not _has_threshold_bounded_panel(cert):
        return True
    return False


def _proto_needs_panel(cert: Mapping[str, Any] | None) -> bool:
    if cert is None:
        return True
    flags = dict(cert.get('theorem_flags', {}))
    relation = dict(cert.get('proto_envelope_relation', {}))
    if not bool(flags.get('anchor_well_defined', False)):
        return True
    if not bool(flags.get('panel_available', False)):
        return True
    if relation.get('panel_nongolden_max_upper_bound') is None:
        return True
    return False


def _eta_anchor_needs_refresh(cert: Mapping[str, Any] | None) -> bool:
    if cert is None:
        return True
    flags = dict(cert.get('theorem_flags', {}))
    if _status_rank(str(cert.get('theorem_status', ''))) >= 4:
        return False
    return not all(
        bool(flags.get(name, False))
        for name in (
            'threshold_bridge_available',
            'eta_interval_available',
            'eta_anchor_inside_arithmetic_domain',
            'local_envelope_anchor_well_defined',
            'positive_threshold_gap',
            'golden_endpoint_anchor',
        )
    )


def _default_vi_challenger_classes() -> list[ArithmeticClassSpec]:
    return [
        ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
        ArithmeticClassSpec(preperiod=(), period=(3,), label='bronze'),
        ArithmeticClassSpec(preperiod=(1,), period=(2,), label='near-golden-12'),
    ]




def _score_vi_screened_bracket_candidate(
    bracket: Mapping[str, Any],
    *,
    initial_lo: float,
    initial_hi: float,
    tol: float,
    approx_label: str,
    q: int,
) -> dict[str, Any]:
    klo = _coerce_float(bracket.get('K_lo'))
    khi = _coerce_float(bracket.get('K_hi'))
    width = None if klo is None or khi is None else float(khi - klo)
    edge_tol = max(10.0 * float(tol), 1.0e-9)
    edge_attained = False
    if klo is not None and khi is not None:
        edge_attained = bool(abs(klo - float(initial_lo)) <= edge_tol or abs(khi - float(initial_hi)) <= edge_tol)
    localized_kind = None if bracket.get('localized_window_kind') is None else str(bracket.get('localized_window_kind'))
    success = bool(bracket.get('success', False))
    proof_ready = bool(bracket.get('proof_ready', False))
    if klo is None or khi is None:
        trust = 'unavailable'
    elif proof_ready and not edge_attained:
        trust = 'trusted-proof-ready'
    elif success and not edge_attained:
        trust = 'trusted-interior-window'
    elif success and edge_attained:
        trust = 'edge-attained-window'
    else:
        trust = 'candidate-window'
    return {
        'label': str(approx_label),
        'q': int(q),
        'success': success,
        'proof_ready': proof_ready,
        'K_lo': klo,
        'K_hi': khi,
        'width': width,
        'localized_window_kind': localized_kind,
        'edge_attained': bool(edge_attained),
        'trust_status': trust,
    }


def _choose_vi_screened_threshold_bound(candidates: Sequence[Mapping[str, Any]]) -> tuple[float | None, float | None, dict[str, Any]]:
    trusted = [dict(c) for c in candidates if c.get('K_lo') is not None and c.get('K_hi') is not None and str(c.get('trust_status', '')).startswith('trusted-')]
    successful = [dict(c) for c in candidates if c.get('K_lo') is not None and c.get('K_hi') is not None]
    exploratory_upper = None if not successful else float(max(float(c['K_hi']) for c in successful))
    exploratory_label = None if not successful else str(max(successful, key=lambda c: float(c['K_hi']))['label'])
    if trusted:
        best = max(trusted, key=lambda c: (int(c.get('q', 0)), -float(c.get('width') or 1.0)))
        return float(best['K_lo']), float(best['K_hi']), {
            'screening_status': 'trusted-threshold-upper-bound',
            'trusted_threshold_bound': True,
            'selected_label': str(best.get('label')),
            'selected_q': int(best.get('q', 0)),
            'selected_trust_status': str(best.get('trust_status')),
            'selected_localized_window_kind': best.get('localized_window_kind'),
            'selected_edge_attained': bool(best.get('edge_attained', False)),
            'exploratory_threshold_upper_bound': exploratory_upper,
            'exploratory_ceiling_attained_by': exploratory_label,
        }
    edge_only = [dict(c) for c in successful if bool(c.get('edge_attained', False))]
    if edge_only:
        worst = max(edge_only, key=lambda c: float(c['K_hi']))
        return None, None, {
            'screening_status': 'edge-attained-exploratory-only',
            'trusted_threshold_bound': False,
            'selected_label': None,
            'selected_q': None,
            'selected_trust_status': None,
            'selected_localized_window_kind': None,
            'selected_edge_attained': None,
            'exploratory_threshold_upper_bound': exploratory_upper,
            'exploratory_ceiling_attained_by': str(worst.get('label')),
            'residual_burden': 'the current class only exposes edge-attained crossing windows, so its local ceiling remains exploratory rather than trusted for Theorem VI',
        }
    return None, None, {
        'screening_status': 'no-usable-threshold-upper-bound',
        'trusted_threshold_bound': False,
        'selected_label': None,
        'selected_q': None,
        'selected_trust_status': None,
        'selected_localized_window_kind': None,
        'selected_edge_attained': None,
        'exploratory_threshold_upper_bound': exploratory_upper,
        'exploratory_ceiling_attained_by': exploratory_label,
        'residual_burden': 'no usable screened threshold upper bound was produced for this challenger class',
    }



def _build_vi_screened_challenger_specs(
    *,
    eta_anchor: Mapping[str, Any],
    family: HarmonicFamily,
    challenger_classes: Sequence[ArithmeticClassSpec] | None,
    kwargs: Mapping[str, Any],
) -> list[EtaChallengerSpec]:
    anchor = dict(eta_anchor.get('local_envelope_anchor', {}))
    reference_center = _coerce_float(anchor.get('threshold_center'))
    if reference_center is None:
        return []
    classes = list(challenger_classes or _default_vi_challenger_classes())
    out: list[EtaChallengerSpec] = []
    max_q = int(kwargs.get('vi_panel_max_q', kwargs.get('vi_campaign_max_q', 8)))
    keep_last = int(kwargs.get('vi_panel_keep_last', kwargs.get('vi_campaign_keep_last', 2)))
    q_min = int(kwargs.get('vi_panel_q_min', kwargs.get('vi_campaign_q_min', 2)))
    crossing_half_width = float(kwargs.get('vi_panel_crossing_half_width', kwargs.get('vi_campaign_crossing_half_width', 2.5e-3)))
    tol = float(kwargs.get('vi_panel_tol', 1e-6))
    max_iter = int(kwargs.get('vi_panel_max_iter', 18))
    initial_lo = float(reference_center - crossing_half_width)
    initial_hi = float(reference_center + crossing_half_width)
    for spec in classes:
        try:
            ladder = build_class_ladder_report(
                spec,
                max_q=max_q,
                q_min=q_min,
                keep_last=keep_last,
            ).to_dict()
        except Exception:
            continue
        approximants = list(ladder.get('approximants', []))
        eta_certificate = {
            'rho': ladder.get('rho'),
            'eta_lo': ladder.get('eta_lo'),
            'eta_hi': ladder.get('eta_hi'),
            'eta_center': ladder.get('eta_center'),
            'method': ladder.get('arithmetic_method', 'periodic-class-ladder'),
        }
        candidate_windows: list[dict[str, Any]] = []
        for approx in reversed(approximants):
            p = approx.get('p')
            q = approx.get('q')
            if p is None or q is None:
                continue
            try:
                bracket = bisection_crossing_bracket(
                    p=int(p),
                    q=int(q),
                    family=family,
                    K_lo=initial_lo,
                    K_hi=initial_hi,
                    max_iter=max_iter,
                    tol=tol,
                    auto_localize=True,
                )
            except Exception:
                continue
            candidate_windows.append(
                _score_vi_screened_bracket_candidate(
                    bracket,
                    initial_lo=initial_lo,
                    initial_hi=initial_hi,
                    tol=tol,
                    approx_label=str(approx.get('label', f"{p}/{q}")),
                    q=int(q),
                )
            )
        threshold_lo, threshold_hi, screening = _choose_vi_screened_threshold_bound(candidate_windows)
        out.append(EtaChallengerSpec(
            preperiod=tuple(spec.preperiod),
            period=tuple(spec.period),
            label=spec.normalized_label(),
            eta_certificate=eta_certificate,
            threshold_lower_bound=threshold_lo,
            threshold_upper_bound=threshold_hi,
            metadata={
                'source': 'theorem-vi-screened-rational-panel',
                'screened_from_ladder': True,
                'max_q': max_q,
                'keep_last': keep_last,
                'candidate_windows': candidate_windows,
                **screening,
            },
        ))
    return out


def _extract_panel_records_from_near_top(cert: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = cert.get('panel_records', [])
    out: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, Mapping):
            out.append(dict(row))
    return out


def _build_vi_campaign_near_top_certificate(
    *,
    eta_anchor: Mapping[str, Any],
    family: HarmonicFamily,
    family_label: str,
    challenger_campaign_report: Mapping[str, Any] | None = None,
    challenger_campaign_classes: Sequence[ArithmeticClassSpec] | None = None,
    kwargs: Mapping[str, Any],
) -> dict[str, Any] | None:
    campaign_kwargs = dict(kwargs)
    if challenger_campaign_report is None:
        anchor = dict(eta_anchor.get('local_envelope_anchor', {}))
        reference_lower = _coerce_float(anchor.get('threshold_lower'))
        reference_center = _coerce_float(anchor.get('threshold_center'))
        if reference_lower is None or reference_center is None:
            return None
        classes = list(challenger_campaign_classes or _default_vi_challenger_classes())
        try:
            challenger_campaign_report = build_multi_class_campaign(
                classes,
                reference_label='golden',
                reference_lower_bound=float(reference_lower),
                reference_crossing_center=float(reference_center),
                family=family,
                max_q=int(campaign_kwargs.pop('vi_campaign_max_q', 8)),
                keep_last=int(campaign_kwargs.pop('vi_campaign_keep_last', 1)),
                q_min=int(campaign_kwargs.pop('vi_campaign_q_min', 2)),
                auto_localize_crossing=bool(campaign_kwargs.pop('vi_campaign_auto_localize_crossing', True)),
                min_width=float(campaign_kwargs.pop('vi_campaign_min_width', 1e-3)),
                crossing_half_width=float(campaign_kwargs.pop('vi_campaign_crossing_half_width', 2.5e-3)),
                band_offset_lo=float(campaign_kwargs.pop('vi_campaign_band_offset_lo', 3.5e-3)),
                band_offset_hi=float(campaign_kwargs.pop('vi_campaign_band_offset_hi', 1.8e-2)),
            ).to_dict()
        except Exception:
            return None
    try:
        campaign_cert = build_campaign_driven_eta_challenger_comparison_certificate(
            challenger_campaign_report,
            golden_eta_threshold_certificate=eta_anchor,
            family_label=family_label,
            max_records=int(kwargs.get('max_records', 0)) or None,
        ).to_dict()
    except Exception:
        return None
    near = campaign_cert.get('near_top_certificate')
    return dict(near) if isinstance(near, Mapping) else None


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)

def _candidate_sources_for_identification_tree(root: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    sources: list[Mapping[str, Any]] = [root]
    for key in (
        'identification_shell',
        'threshold_identification_shell',
        'threshold_identification_discharge_shell',
        'transport_discharge_shell',
        'theorem_vi_shell',
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
    discharge = root.get('threshold_identification_discharge_shell')
    if isinstance(discharge, Mapping):
        ident = discharge.get('identification_shell')
        if isinstance(ident, Mapping):
            sources.append(ident)
    return sources


def _find_nested_mapping_with_key(root: Any, key: str) -> dict[str, Any] | None:
    if isinstance(root, Mapping):
        for source in _candidate_sources_for_identification_tree(root):
            value = source.get(key)
            if isinstance(value, Mapping):
                return dict(value)
    return None



@dataclass
class TheoremVIEnvelopeHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVIEnvelopeAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremVIEnvelopeLiftCertificate:
    rho: float
    family_label: str
    statement_mode: str
    statement_mode_diagnostics: dict[str, Any]
    mode_reduction_certificate: dict[str, Any]
    mode_obstruction_certificate: dict[str, Any]
    current_local_top_gap_certificate: dict[str, Any]
    screened_near_top_dominance_certificate: dict[str, Any]
    strict_golden_top_gap_certificate: dict[str, Any]
    global_nongolden_ceiling_certificate: dict[str, Any]
    global_envelope_certificate: dict[str, Any]
    strict_golden_top_gap_theorem_candidate: dict[str, Any]
    residual_burden_summary: dict[str, Any]
    threshold_identification_shell: dict[str, Any]
    eta_threshold_anchor: dict[str, Any]
    proto_envelope_bridge: dict[str, Any]
    near_top_challenger_surface: dict[str, Any]
    hypotheses: list[TheoremVIEnvelopeHypothesisRow]
    assumptions: list[TheoremVIEnvelopeAssumptionRow]
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
            'statement_mode_diagnostics': dict(self.statement_mode_diagnostics),
            'mode_reduction_certificate': dict(self.mode_reduction_certificate),
            'mode_obstruction_certificate': dict(self.mode_obstruction_certificate),
            'current_local_top_gap_certificate': dict(self.current_local_top_gap_certificate),
            'screened_near_top_dominance_certificate': dict(self.screened_near_top_dominance_certificate),
            'strict_golden_top_gap_certificate': dict(self.strict_golden_top_gap_certificate),
            'global_nongolden_ceiling_certificate': dict(self.global_nongolden_ceiling_certificate),
            'global_envelope_certificate': dict(self.global_envelope_certificate),
            'strict_golden_top_gap_theorem_candidate': dict(self.strict_golden_top_gap_theorem_candidate),
            'residual_burden_summary': dict(self.residual_burden_summary),
            'threshold_identification_shell': dict(self.threshold_identification_shell),
            'eta_threshold_anchor': dict(self.eta_threshold_anchor),
            'proto_envelope_bridge': dict(self.proto_envelope_bridge),
            'near_top_challenger_surface': dict(self.near_top_challenger_surface),
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



def _default_envelope_assumptions() -> list[TheoremVIEnvelopeAssumptionRow]:
    return [
        TheoremVIEnvelopeAssumptionRow(
            name='one_variable_eta_envelope_law',
            assumed=False,
            source='Theorem-VI envelope lift assumption',
            note='The true threshold law is controlled by a monotone one-variable envelope in eta alone.',
        ),
        TheoremVIEnvelopeAssumptionRow(
            name='corrected_two_variable_envelope_law',
            assumed=False,
            source='Theorem-VI envelope lift assumption',
            note='If eta alone is insufficient, the correct final statement is a two-variable envelope theorem with one extra renormalization covariate.',
        ),
        TheoremVIEnvelopeAssumptionRow(
            name='renormalization_covariate_control_on_class',
            assumed=False,
            source='Theorem-VI envelope lift assumption',
            note='Control the extra renormalization covariate uniformly on the chosen renormalization-stable class.',
        ),
        TheoremVIEnvelopeAssumptionRow(
            name='strict_golden_top_gap_theorem',
            assumed=False,
            source='Theorem-VI envelope lift assumption',
            note='Promote the current finite near-top gap evidence into a theorem-grade strict golden top-gap statement.',
        ),
        TheoremVIEnvelopeAssumptionRow(
            name='challenger_exhaustion_beyond_current_panel',
            assumed=False,
            source='Theorem-VI envelope lift assumption',
            note='Eliminate omitted non-golden irrational challengers beyond the current explicit near-top panel.',
        ),
    ]



def _build_assumptions(
    *,
    assume_one_variable_eta_envelope_law: bool,
    assume_corrected_two_variable_envelope_law: bool,
    assume_renormalization_covariate_control_on_class: bool,
    assume_strict_golden_top_gap_theorem: bool,
    assume_challenger_exhaustion_beyond_current_panel: bool,
) -> list[TheoremVIEnvelopeAssumptionRow]:
    assumption_map = {
        'one_variable_eta_envelope_law': bool(assume_one_variable_eta_envelope_law),
        'corrected_two_variable_envelope_law': bool(assume_corrected_two_variable_envelope_law),
        'renormalization_covariate_control_on_class': bool(assume_renormalization_covariate_control_on_class),
        'strict_golden_top_gap_theorem': bool(assume_strict_golden_top_gap_theorem),
        'challenger_exhaustion_beyond_current_panel': bool(assume_challenger_exhaustion_beyond_current_panel),
    }
    rows: list[TheoremVIEnvelopeAssumptionRow] = []
    for row in _default_envelope_assumptions():
        rows.append(
            TheoremVIEnvelopeAssumptionRow(
                name=row.name,
                assumed=bool(assumption_map.get(row.name, False)),
                source=row.source,
                note=row.note,
            )
        )
    return rows



def _build_hypotheses(
    identification: Mapping[str, Any],
    eta_anchor: Mapping[str, Any],
    proto: Mapping[str, Any],
    near_top: Mapping[str, Any],
    current_local_top_gap_certificate: Mapping[str, Any] | None = None,
) -> list[TheoremVIEnvelopeHypothesisRow]:
    eta_flags = dict(eta_anchor.get('theorem_flags', {}))
    proto_flags = dict(proto.get('theorem_flags', {}))
    near_flags = dict(near_top.get('theorem_flags', {}))
    near_relation = dict(near_top.get('near_top_relation', {}))
    proto_relation = dict(proto.get('proto_envelope_relation', {}))

    top_gap = near_relation.get('golden_lower_minus_most_dangerous_upper')
    if top_gap is None:
        top_gap = proto_relation.get('anchor_lower_minus_panel_nongolden_upper')

    eta_endpoint_gap = dict(eta_anchor.get('eta_relation', {})).get('eta_gap_to_golden_endpoint')
    local_gap = dict(current_local_top_gap_certificate or {})
    exploratory_top_gap_positive = bool(local_gap.get('exploratory_top_gap_positive', False)) or bool(near_flags.get('panel_gap_positive', False)) or bool(proto_flags.get('anchor_gap_against_panel_positive', False))

    return [
        TheoremVIEnvelopeHypothesisRow(
            name='threshold_identification_front_complete',
            satisfied=_is_front_complete(identification),
            source='threshold-identification lift',
            note='The current Theorem II→V identification shell has no remaining front hypotheses, even if conditional assumptions remain active.',
            margin=None,
        ),
        TheoremVIEnvelopeHypothesisRow(
            name='eta_threshold_anchor_strong',
            satisfied=_status_rank(str(eta_anchor.get('theorem_status', ''))) >= 4,
            source='eta-threshold comparison',
            note='A strong local (eta, threshold) anchor is available at the golden endpoint.',
            margin=None if eta_endpoint_gap is None else float(-eta_endpoint_gap),
        ),
        TheoremVIEnvelopeHypothesisRow(
            name='proto_envelope_anchor_available',
            satisfied=bool(proto_flags.get('eta_threshold_anchor_available', False)) and bool(proto_flags.get('anchor_well_defined', False)),
            source='proto-envelope eta bridge',
            note='The local eta-threshold anchor is packaged in a theorem-facing proto-envelope comparison layer.',
            margin=None,
        ),
        TheoremVIEnvelopeHypothesisRow(
            name='near_top_challenger_surface_available',
            satisfied=bool(near_flags.get('golden_anchor_available', False)) and bool(near_flags.get('challenger_records_available', False)),
            source='near-top eta challenger comparison',
            note='A genuine near-top challenger surface exists on the shared (eta, threshold) axis.',
            margin=None,
        ),
        TheoremVIEnvelopeHypothesisRow(
            name='threshold_bounded_near_top_challengers_dominated',
            satisfied=bool(near_flags.get('all_threshold_bounded_challengers_dominated', False)),
            source='near-top eta challenger comparison',
            note='Every challenger with an attached threshold upper bound lies below the trusted golden lower anchor.',
            margin=None if top_gap is None else float(top_gap),
        ),
        TheoremVIEnvelopeHypothesisRow(
            name='no_undecided_near_top_challengers',
            satisfied=bool(near_flags.get('no_undecided_challengers', False)),
            source='near-top eta challenger comparison',
            note='No currently tracked near-top challenger remains in the undecided bucket.',
            margin=None,
        ),
        TheoremVIEnvelopeHypothesisRow(
            name='exploratory_top_gap_positive',
            satisfied=exploratory_top_gap_positive,
            source='proto-envelope / near-top comparison',
            note='The current finite panel already exhibits a positive golden-over-nongolden top-gap diagnostic, either explicitly or via screened local domination after deferring purely exploratory edge-attained ceilings.',
            margin=None if top_gap is None else float(top_gap),
        ),
    ]



def _choose_statement_mode(
    assumptions: Sequence[TheoremVIEnvelopeAssumptionRow],
    statement_mode_certificate: Mapping[str, Any] | None = None,
    mode_reduction_certificate: Mapping[str, Any] | None = None,
) -> tuple[str, set[str]]:
    amap = {row.name: bool(row.assumed) for row in assumptions}
    if amap.get('one_variable_eta_envelope_law', False):
        return 'one-variable', {
            'one_variable_eta_envelope_law',
            'strict_golden_top_gap_theorem',
            'challenger_exhaustion_beyond_current_panel',
        }
    if amap.get('corrected_two_variable_envelope_law', False) or amap.get('renormalization_covariate_control_on_class', False):
        return 'two-variable', {
            'corrected_two_variable_envelope_law',
            'renormalization_covariate_control_on_class',
            'strict_golden_top_gap_theorem',
            'challenger_exhaustion_beyond_current_panel',
        }

    reduction = dict(mode_reduction_certificate or {})
    theorem_mode = str(reduction.get('theorem_mode', 'unresolved'))
    reduction_status = str(reduction.get('theorem_mode_status', 'statement-mode-reduction-unresolved'))
    if theorem_mode == 'one-variable' and bool(reduction.get('reduction_certified', False)):
        return 'one-variable', {
            'strict_golden_top_gap_theorem',
            'challenger_exhaustion_beyond_current_panel',
        }
    if theorem_mode == 'two-variable' and (bool(reduction.get('reduction_certified', False)) or 'two-variable-reduction-certified' in reduction_status):
        return 'two-variable', {
            'strict_golden_top_gap_theorem',
            'challenger_exhaustion_beyond_current_panel',
        }
    certificate = dict(statement_mode_certificate or {})
    mode_lock_status = str(certificate.get('mode_lock_status', ''))
    candidate_mode = str(certificate.get('candidate_mode', 'unresolved'))
    if candidate_mode == 'one-variable' and 'one-variable-supported' in mode_lock_status:
        return 'one-variable', {
            'one_variable_eta_envelope_law',
            'strict_golden_top_gap_theorem',
            'challenger_exhaustion_beyond_current_panel',
        }
    if candidate_mode == 'two-variable' and 'two-variable-supported' in mode_lock_status:
        return 'two-variable', {
            'corrected_two_variable_envelope_law',
            'renormalization_covariate_control_on_class',
            'strict_golden_top_gap_theorem',
            'challenger_exhaustion_beyond_current_panel',
        }
    return 'unresolved', {row.name for row in assumptions}

def _build_current_local_top_gap_certificate(
    proto: Mapping[str, Any],
    near_top: Mapping[str, Any],
    *,
    screened_near_top_dominance_certificate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    proto_flags = dict(proto.get('theorem_flags', {}))
    near_flags = dict(near_top.get('theorem_flags', {}))
    near_relation = dict(near_top.get('near_top_relation', {}))
    proto_relation = dict(proto.get('proto_envelope_relation', {}))
    screened = dict(screened_near_top_dominance_certificate or {})

    top_gap = _coerce_float(near_relation.get('golden_lower_minus_most_dangerous_upper'))
    if top_gap is None:
        top_gap = _coerce_float(proto_relation.get('anchor_lower_minus_panel_nongolden_upper'))
    challenger_upper = _coerce_float(near_relation.get('most_dangerous_threshold_upper'))
    if challenger_upper is None:
        challenger_upper = _coerce_float(proto_relation.get('panel_nongolden_max_upper_bound'))
    if challenger_upper is None:
        challenger_upper = _coerce_float(screened.get('trusted_ceiling_upper_bound'))

    panel_gap_positive = bool(near_flags.get('panel_gap_positive', False)) or bool(proto_flags.get('anchor_gap_against_panel_positive', False))
    dominated = bool(near_flags.get('all_threshold_bounded_challengers_dominated', False))
    no_undecided = bool(near_flags.get('no_undecided_challengers', False))
    trusted_records = [dict(rec) for rec in screened.get('trusted_threshold_bounded_records', []) if isinstance(rec, Mapping)]
    deferred_records = [dict(rec) for rec in screened.get('deferred_exploratory_records', []) if isinstance(rec, Mapping)]

    screened_domination_positive = (
        top_gap is None
        and not trusted_records
        and bool(deferred_records)
        and dominated
        and no_undecided
    )

    if top_gap is None and screened_domination_positive:
        status = 'current-local-top-gap-screened-domination-positive'
        witness_kind = 'screened-domination-with-deferred-exploratory'
    elif top_gap is None:
        status = 'current-local-top-gap-unavailable'
        witness_kind = 'none'
    elif top_gap > 0.0 and panel_gap_positive and dominated and no_undecided:
        status = 'current-local-top-gap-strong'
        witness_kind = 'explicit-positive-gap'
    elif top_gap > 0.0 and (dominated or no_undecided or panel_gap_positive):
        status = 'current-local-top-gap-partial'
        witness_kind = 'explicit-positive-gap'
    elif top_gap > 0.0:
        status = 'current-local-top-gap-weak-positive'
        witness_kind = 'explicit-positive-gap'
    else:
        status = 'current-local-top-gap-nonpositive'
        witness_kind = 'explicit-nonpositive-gap'

    exploratory_positive = bool((top_gap is not None and top_gap > 0.0 and (panel_gap_positive or dominated or no_undecided)) or screened_domination_positive)

    return {
        'top_gap_scale': top_gap,
        'current_most_dangerous_challenger_upper': challenger_upper,
        'panel_gap_positive': panel_gap_positive,
        'all_threshold_bounded_challengers_dominated': dominated,
        'no_undecided_near_top_challengers': no_undecided,
        'trusted_threshold_bounded_records_available': bool(trusted_records),
        'deferred_exploratory_records_present': bool(deferred_records),
        'screened_domination_positive_without_numeric_gap': bool(screened_domination_positive),
        'exploratory_top_gap_positive': exploratory_positive,
        'top_gap_witness_kind': witness_kind,
        'status': status,
        'local_geometry_supports_top_gap_promotion': status in {
            'current-local-top-gap-strong',
            'current-local-top-gap-partial',
            'current-local-top-gap-screened-domination-positive',
        },
    }


def _build_screened_near_top_dominance_certificate(near_top: Mapping[str, Any]) -> dict[str, Any]:
    records = [dict(rec) for rec in near_top.get('challenger_records', []) if isinstance(rec, Mapping)]
    trusted_bounded: list[dict[str, Any]] = []
    deferred_exploratory: list[dict[str, Any]] = []
    for rec in records:
        provenance = dict(rec.get('provenance', {}))
        if rec.get('threshold_upper_bound') is not None:
            trusted_bounded.append({
                'label': rec.get('label'),
                'threshold_upper_bound': rec.get('threshold_upper_bound'),
                'status': rec.get('status'),
                'source': provenance.get('source'),
                'screening_status': provenance.get('screening_status'),
                'selected_label': provenance.get('selected_label'),
            })
        elif provenance.get('exploratory_threshold_upper_bound') is not None:
            deferred_exploratory.append({
                'label': rec.get('label'),
                'status': rec.get('status'),
                'source': provenance.get('source'),
                'screening_status': provenance.get('screening_status'),
                'exploratory_threshold_upper_bound': provenance.get('exploratory_threshold_upper_bound'),
                'exploratory_ceiling_attained_by': provenance.get('exploratory_ceiling_attained_by'),
                'residual_burden': provenance.get('residual_burden'),
            })
    relation = dict(near_top.get('near_top_relation', {}))
    top_gap = _coerce_float(relation.get('golden_lower_minus_most_dangerous_upper'))
    trusted_ceiling = None if not trusted_bounded else float(max(float(rec['threshold_upper_bound']) for rec in trusted_bounded if rec.get('threshold_upper_bound') is not None))
    trusted_label = None if not trusted_bounded else str(max(trusted_bounded, key=lambda rec: float(rec.get('threshold_upper_bound') or float('-inf')))['label'])
    status = 'screened-near-top-dominance-open'
    if trusted_bounded and top_gap is not None and top_gap > 0.0:
        status = 'screened-near-top-dominance-positive-gap'
    elif trusted_bounded and top_gap is not None:
        status = 'screened-near-top-dominance-nonpositive-gap'
    elif deferred_exploratory:
        status = 'screened-near-top-dominance-exploratory-deferred'
    return {
        'trusted_threshold_bounded_records': trusted_bounded,
        'deferred_exploratory_records': deferred_exploratory,
        'trusted_ceiling_upper_bound': trusted_ceiling,
        'trusted_ceiling_attained_by': trusted_label,
        'trusted_panel_gap': top_gap,
        'status': status,
        'local_dominance_certified_over_trusted_panel': bool(trusted_bounded) and top_gap is not None and top_gap > 0.0,
        'remaining_burden': (
            'none' if status == 'screened-near-top-dominance-positive-gap' else
            'promote or eliminate the deferred exploratory challenger ceilings so the local top-gap certificate is no longer sensitive to unresolved near-top classes'
        ),
    }


def _merge_statement_mode_certificates(
    proto: Mapping[str, Any],
    near_top: Mapping[str, Any],
    *,
    current_local_top_gap_certificate: Mapping[str, Any],
) -> dict[str, Any]:
    proto_cert = dict(proto.get('statement_mode_certificate', {}))
    near_cert = dict(near_top.get('statement_mode_certificate', {}))
    certificates = [cert for cert in (near_cert, proto_cert) if cert]

    if not certificates:
        return {
            'candidate_mode': 'unresolved',
            'mode_lock_status': 'statement-mode-unresolved',
            'status': 'statement-mode-certificate-unresolved',
            'sources': [],
            'evidence_margin': None,
            'residual_obstruction': 'no finite statement-mode certificate is currently available from the eta comparison layers',
        }

    locked_two = [cert for cert in certificates if cert.get('candidate_mode') == 'two-variable' and 'two-variable-supported' in str(cert.get('mode_lock_status', ''))]
    locked_one = [cert for cert in certificates if cert.get('candidate_mode') == 'one-variable' and 'one-variable-supported' in str(cert.get('mode_lock_status', ''))]

    if locked_two:
        chosen = max(locked_two, key=lambda cert: float(cert.get('evidence_margin') or 0.0))
        status = 'statement-mode-certificate-two-variable-supported'
        mode_lock_status = 'two-variable-supported'
        candidate_mode = 'two-variable'
    elif certificates and all(cert.get('candidate_mode') == 'one-variable' and 'one-variable-supported' in str(cert.get('mode_lock_status', '')) for cert in certificates):
        chosen = min(locked_one, key=lambda cert: float(cert.get('evidence_margin') or 0.0)) if locked_one else certificates[0]
        status = 'statement-mode-certificate-one-variable-supported'
        mode_lock_status = 'one-variable-supported'
        candidate_mode = 'one-variable'
    else:
        chosen = certificates[0]
        status = 'statement-mode-certificate-unresolved'
        mode_lock_status = 'statement-mode-unresolved'
        candidate_mode = 'unresolved'

    return {
        **{k: v for k, v in chosen.items() if k != 'sources'},
        'candidate_mode': candidate_mode,
        'mode_lock_status': mode_lock_status,
        'status': status,
        'sources': [
            {
                'source': 'near-top-challenger-surface' if cert is near_cert else 'proto-envelope-bridge',
                'candidate_mode': cert.get('candidate_mode'),
                'mode_lock_status': cert.get('mode_lock_status'),
                'evidence_margin': cert.get('evidence_margin'),
            }
            for cert in certificates
        ],
        'current_local_top_gap_status': None if current_local_top_gap_certificate.get('status') is None else str(current_local_top_gap_certificate.get('status')),
        'current_local_geometry_supports_top_gap_promotion': bool(current_local_top_gap_certificate.get('local_geometry_supports_top_gap_promotion', False)),
    }


def _build_global_nongolden_ceiling_certificate(
    proto: Mapping[str, Any],
    near_top: Mapping[str, Any],
) -> dict[str, Any]:
    near_cert = dict(near_top.get('global_nongolden_ceiling_certificate', {}))
    if near_cert:
        return near_cert

    near_relation = dict(near_top.get('near_top_relation', {}))
    proto_relation = dict(proto.get('proto_envelope_relation', {}))
    upper = _coerce_float(near_relation.get('most_dangerous_threshold_upper'))
    if upper is None:
        upper = _coerce_float(proto_relation.get('panel_nongolden_max_upper_bound'))
    golden_anchor = dict(near_top.get('golden_anchor_certificate', {}))
    threshold_interval = golden_anchor.get('threshold_interval')
    golden_lower = None if not isinstance(threshold_interval, Sequence) or len(threshold_interval) != 2 else float(threshold_interval[0])
    margin = None if golden_lower is None or upper is None else float(golden_lower - upper)
    status = 'global-ceiling-partial' if upper is not None else 'global-ceiling-unavailable'
    return {
        'global_nongolden_upper_ceiling': upper,
        'golden_lower_witness': golden_lower,
        'global_gap_margin': margin,
        'global_ceiling_status': status,
        'tail_control_available': False,
        'remaining_burden': 'the near-top challenger layer has not yet exposed an explicit global ceiling decomposition',
    }


def _build_statement_mode_diagnostics(
    assumptions: Sequence[TheoremVIEnvelopeAssumptionRow],
    current_local_top_gap_certificate: Mapping[str, Any],
    statement_mode_certificate: Mapping[str, Any] | None = None,
    mode_reduction_certificate: Mapping[str, Any] | None = None,
    mode_obstruction_certificate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    amap = {row.name: bool(row.assumed) for row in assumptions}
    one_variable = bool(amap.get('one_variable_eta_envelope_law', False))
    two_variable = bool(amap.get('corrected_two_variable_envelope_law', False))
    covariate = bool(amap.get('renormalization_covariate_control_on_class', False))
    certificate = dict(statement_mode_certificate or {})
    reduction = dict(mode_reduction_certificate or {})

    if one_variable and not two_variable and not covariate:
        candidate_mode = 'one-variable'
        residual_burden = 'promote the current finite-gap evidence into the theorem-grade one-variable eta-envelope law'
        status = 'statement-mode-explicit-one-variable'
        mode_lock_status = 'assumption-forced-one-variable'
    elif two_variable or covariate:
        candidate_mode = 'two-variable'
        residual_burden = 'prove the corrected two-variable envelope theorem and control the renormalization covariate on the chosen class'
        status = 'statement-mode-explicit-two-variable'
        mode_lock_status = 'assumption-forced-two-variable'
    else:
        candidate_mode = str(certificate.get('candidate_mode', 'unresolved'))
        mode_lock_status = str(certificate.get('mode_lock_status', 'statement-mode-unresolved'))
        status = str(certificate.get('status', 'statement-mode-certificate-unresolved'))
        if reduction.get('reduction_certified', False) and reduction.get('theorem_mode') == 'one-variable':
            if str(reduction.get('theorem_mode_status', '')) == 'one-variable-reduction-certified-screened-panel':
                residual_burden = 'global challenger exhaustion beyond the current trusted panel is deferred to Theorem VII'
                status = 'statement-mode-one-variable-screened-panel-certified'
            else:
                residual_burden = 'none'
                status = 'statement-mode-one-variable-theorem-certified'
        elif reduction.get('reduction_certified', False) and reduction.get('theorem_mode') == 'two-variable':
            residual_burden = 'prove the corrected two-variable envelope law and control the renormalization covariate on the class'
            status = 'statement-mode-two-variable-theorem-certified'
        elif candidate_mode == 'one-variable' and 'one-variable-supported' in mode_lock_status:
            residual_burden = 'the finite eta-only evidence now supports one-variable mode; the remaining burden is to prove the theorem-grade one-variable envelope law and strict golden top gap'
        elif candidate_mode == 'two-variable' and 'two-variable-supported' in mode_lock_status:
            residual_burden = 'the finite panel now supports a corrected two-variable statement; the remaining burden is to prove the two-variable envelope law and control the renormalization covariate on the class'
        else:
            residual_burden = 'settle whether Theorem VI is genuinely one-variable in eta or requires the corrected two-variable formulation'

    theorem_statement_mode = str(reduction.get('theorem_mode', candidate_mode))
    return {
        'candidate_mode': candidate_mode,
        'diagnostic_statement_mode': candidate_mode,
        'theorem_statement_mode': theorem_statement_mode,
        'theorem_mode_certified': bool(reduction.get('reduction_certified', False)),
        'status': status,
        'mode_lock_status': mode_lock_status,
        'evidence_margin': _coerce_float(certificate.get('evidence_margin')),
        'one_variable_law_assumed': one_variable,
        'corrected_two_variable_law_assumed': two_variable,
        'renormalization_covariate_control_assumed': covariate,
        'finite_statement_mode_certificate': certificate,
        'mode_reduction_certificate': reduction,
        'mode_obstruction_certificate': dict(mode_obstruction_certificate or {}),
        'current_top_gap_scale': _coerce_float(current_local_top_gap_certificate.get('top_gap_scale')),
        'current_local_top_gap_status': None if current_local_top_gap_certificate.get('status') is None else str(current_local_top_gap_certificate.get('status')),
        'current_local_geometry_supports_top_gap_promotion': bool(current_local_top_gap_certificate.get('local_geometry_supports_top_gap_promotion', False)),
        'residual_statement_mode_burden': residual_burden,
    }

def _build_strict_golden_top_gap_certificate(
    *,
    statement_mode_diagnostics: Mapping[str, Any],
    current_local_top_gap_certificate: Mapping[str, Any],
    global_nongolden_ceiling_certificate: Mapping[str, Any],
    global_envelope_certificate: Mapping[str, Any],
    strict_golden_top_gap_theorem_candidate: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_mode = str(statement_mode_diagnostics.get('candidate_mode', 'unresolved'))
    theorem_mode = str(statement_mode_diagnostics.get('theorem_statement_mode', candidate_mode))
    mode_lock_status = str(statement_mode_diagnostics.get('mode_lock_status', 'statement-mode-unresolved'))
    top_gap_scale = _coerce_float(current_local_top_gap_certificate.get('top_gap_scale'))
    local_status = str(current_local_top_gap_certificate.get('status', 'current-local-top-gap-unavailable'))
    local_geometry_supports = bool(current_local_top_gap_certificate.get('local_geometry_supports_top_gap_promotion', False))
    dominated = bool(current_local_top_gap_certificate.get('all_threshold_bounded_challengers_dominated', False))
    no_undecided = bool(current_local_top_gap_certificate.get('no_undecided_near_top_challengers', False))
    mode_locked = bool(statement_mode_diagnostics.get('theorem_mode_certified', False)) or (('supported' in mode_lock_status) and candidate_mode in {'one-variable', 'two-variable'})

    if bool(strict_golden_top_gap_theorem_candidate.get('global_strict_top_gap_certified', False)):
        status = f'strict-golden-top-gap-theorem-{theorem_mode}-certified'
        remaining_burden = 'none'
    elif not mode_locked and not (local_status == 'current-local-top-gap-screened-domination-positive' and dominated and no_undecided):
        status = 'strict-golden-top-gap-positive-but-mode-unresolved'
        remaining_burden = 'lock the final Theorem VI statement mode before promoting the positive finite top gap into a theorem-facing strict golden top-gap certificate'
    elif local_status == 'current-local-top-gap-screened-domination-positive' and dominated and no_undecided:
        status = 'strict-golden-top-gap-screened-domination-certified'
        remaining_burden = 'the local screened-panel strict golden top gap is now certified; the remaining burden is global challenger exhaustion beyond the current trusted panel, which is deferred to Theorem VII'
    elif local_status == 'current-local-top-gap-strong' and dominated and no_undecided:
        status = 'strict-golden-top-gap-screened-panel-strong'
        remaining_burden = 'globalize the screened-panel strict golden top gap by proving the matching envelope law and exhausting omitted non-golden challengers beyond the current panel'
    elif local_geometry_supports:
        status = 'strict-golden-top-gap-screened-panel-partial'
        remaining_burden = 'strengthen the current local gap geometry to a screened-panel strong certificate, then globalize it beyond the current challenger panel'
    elif top_gap_scale is None or top_gap_scale <= 0.0:
        status = 'strict-golden-top-gap-unavailable'
        remaining_burden = 'the current finite eta panel does not yet exhibit a positive golden-over-nongolden top gap'
    else:
        status = 'strict-golden-top-gap-positive-only'
        remaining_burden = 'the finite top gap is positive, but the current local geometry is still too weak to treat it as a screened-panel strict golden top-gap certificate'

    return {
        'statement_mode': theorem_mode,
        'mode_lock_status': mode_lock_status,
        'top_gap_scale': top_gap_scale,
        'local_geometry_status': local_status,
        'screened_panel_strict_top_gap_status': status,
        'screened_panel_strict_top_gap_certified': status in {'strict-golden-top-gap-screened-panel-strong', 'strict-golden-top-gap-screened-domination-certified', f'strict-golden-top-gap-theorem-{theorem_mode}-certified'},
        'screened_panel_strict_top_gap_partially_certified': status in {'strict-golden-top-gap-screened-panel-strong', 'strict-golden-top-gap-screened-panel-partial', 'strict-golden-top-gap-screened-domination-certified', f'strict-golden-top-gap-theorem-{theorem_mode}-certified'},
        'local_top_gap_promoted_beyond_raw_gap': status in {'strict-golden-top-gap-screened-panel-strong', 'strict-golden-top-gap-screened-panel-partial', 'strict-golden-top-gap-screened-domination-certified', f'strict-golden-top-gap-theorem-{theorem_mode}-certified'},
        'remaining_global_burden': remaining_burden,
        'global_nongolden_ceiling_status': None if global_nongolden_ceiling_certificate.get('global_ceiling_status') is None else str(global_nongolden_ceiling_certificate.get('global_ceiling_status')),
        'global_nongolden_upper_ceiling': _coerce_float(global_nongolden_ceiling_certificate.get('global_nongolden_upper_ceiling')),
        'global_envelope_status': None if global_envelope_certificate.get('theorem_status') is None else str(global_envelope_certificate.get('theorem_status')),
        'global_strict_top_gap_status': None if strict_golden_top_gap_theorem_candidate.get('global_strict_top_gap_status') is None else str(strict_golden_top_gap_theorem_candidate.get('global_strict_top_gap_status')),
        'global_strict_top_gap_certified': bool(strict_golden_top_gap_theorem_candidate.get('global_strict_top_gap_certified', False)),
        'global_strict_top_gap_margin': _coerce_float(strict_golden_top_gap_theorem_candidate.get('global_strict_top_gap_margin')),
    }

def _refine_local_active_assumptions(
    local_active_assumptions: Sequence[str],
    *,
    strict_golden_top_gap_certificate: Mapping[str, Any],
    global_nongolden_ceiling_certificate: Mapping[str, Any],
) -> list[str]:
    refined = [str(x) for x in local_active_assumptions]
    if bool(strict_golden_top_gap_certificate.get('local_top_gap_promoted_beyond_raw_gap', False)):
        refined = [x for x in refined if x != 'strict_golden_top_gap_theorem']
    if bool(global_nongolden_ceiling_certificate.get('global_ceiling_theorem_certified', False)):
        refined = [x for x in refined if x != 'challenger_exhaustion_beyond_current_panel']
    return refined

def _build_residual_burden_summary(
    *,
    open_hypotheses: Sequence[str],
    local_active_assumptions: Sequence[str],
    upstream_active_assumptions: Sequence[str],
    current_local_top_gap_certificate: Mapping[str, Any],
    strict_golden_top_gap_certificate: Mapping[str, Any],
    statement_mode_diagnostics: Mapping[str, Any],
    mode_reduction_certificate: Mapping[str, Any],
    global_nongolden_ceiling_certificate: Mapping[str, Any],
    screened_near_top_dominance_certificate: Mapping[str, Any],
) -> dict[str, Any]:
    upstream_front_hypotheses = [h for h in open_hypotheses if h == 'threshold_identification_front_complete']
    local_front_hypotheses = [h for h in open_hypotheses if h not in upstream_front_hypotheses]
    global_theorem_assumptions = [str(x) for x in local_active_assumptions] + [str(x) for x in upstream_active_assumptions]
    local_geometry_ready = str(current_local_top_gap_certificate.get('status', '')).endswith('strong') and not local_front_hypotheses
    theorem_mode_certified = bool(mode_reduction_certificate.get('reduction_certified', False))
    global_ceiling_certified = bool(global_nongolden_ceiling_certificate.get('global_ceiling_theorem_certified', False))
    global_gap_certified = bool(strict_golden_top_gap_certificate.get('global_strict_top_gap_certified', False))

    if local_geometry_ready and theorem_mode_certified and global_ceiling_certified and global_gap_certified and not global_theorem_assumptions:
        status = 'theorem-vi-globally-discharged'
    elif local_geometry_ready and global_theorem_assumptions:
        status = 'global-theorem-burden-only'
    elif not open_hypotheses and not global_theorem_assumptions:
        status = 'fully-discharged'
    elif local_front_hypotheses:
        status = 'local-frontier-still-open'
    else:
        status = 'mixed-local-and-global'

    deferred_handoff = [str(rec.get('label')) for rec in screened_near_top_dominance_certificate.get('deferred_exploratory_records', []) if isinstance(rec, Mapping)]
    return {
        'status': status,
        'local_front_hypotheses': local_front_hypotheses,
        'upstream_front_hypotheses': upstream_front_hypotheses,
        'global_theorem_assumptions': global_theorem_assumptions,
        'theorem_vii_handoff_labels': deferred_handoff,
        'theorem_vii_handoff_active': bool(deferred_handoff),
        'statement_mode_residual_burden': None if statement_mode_diagnostics.get('residual_statement_mode_burden') is None else str(statement_mode_diagnostics.get('residual_statement_mode_burden')),
        'current_local_geometry_status': None if current_local_top_gap_certificate.get('status') is None else str(current_local_top_gap_certificate.get('status')),
        'current_local_geometry_supports_top_gap_promotion': bool(current_local_top_gap_certificate.get('local_geometry_supports_top_gap_promotion', False)),
        'strict_golden_top_gap_status': None if strict_golden_top_gap_certificate.get('screened_panel_strict_top_gap_status') is None else str(strict_golden_top_gap_certificate.get('screened_panel_strict_top_gap_status')),
        'strict_golden_top_gap_promoted_beyond_raw_gap': bool(strict_golden_top_gap_certificate.get('local_top_gap_promoted_beyond_raw_gap', False)),
        'strict_golden_top_gap_remaining_burden': None if strict_golden_top_gap_certificate.get('remaining_global_burden') is None else str(strict_golden_top_gap_certificate.get('remaining_global_burden')),
        'mode_reduction_status': None if mode_reduction_certificate.get('theorem_mode_status') is None else str(mode_reduction_certificate.get('theorem_mode_status')),
        'mode_reduction_certified': theorem_mode_certified,
        'mode_reduction_burden': None if mode_reduction_certificate.get('remaining_burden') is None else str(mode_reduction_certificate.get('remaining_burden')),
        'global_ceiling_status': None if global_nongolden_ceiling_certificate.get('global_ceiling_status') is None else str(global_nongolden_ceiling_certificate.get('global_ceiling_status')),
        'global_ceiling_certified': global_ceiling_certified,
        'global_ceiling_burden': None if global_nongolden_ceiling_certificate.get('remaining_burden') is None else str(global_nongolden_ceiling_certificate.get('remaining_burden')),
        'screened_near_top_dominance_status': None if screened_near_top_dominance_certificate.get('status') is None else str(screened_near_top_dominance_certificate.get('status')),
        'screened_near_top_dominance_certified': bool(screened_near_top_dominance_certificate.get('local_dominance_certified_over_trusted_panel', False)),
        'screened_near_top_dominance_burden': None if screened_near_top_dominance_certificate.get('remaining_burden') is None else str(screened_near_top_dominance_certificate.get('remaining_burden')),
    }

def build_golden_theorem_vi_envelope_lift_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    challenger_specs: Sequence[EtaChallengerSpec] | None = None,
    challenger_campaign_report: Mapping[str, Any] | None = None,
    challenger_campaign_classes: Sequence[ArithmeticClassSpec] | None = None,
    auto_build_screened_near_top_panel: bool = True,
    threshold_identification_certificate: Mapping[str, Any] | None = None,
    threshold_bridge_certificate: Mapping[str, Any] | None = None,
    eta_threshold_certificate: Mapping[str, Any] | None = None,
    proto_envelope_certificate: Mapping[str, Any] | None = None,
    near_top_certificate: Mapping[str, Any] | None = None,
    assume_one_variable_eta_envelope_law: bool = False,
    assume_corrected_two_variable_envelope_law: bool = False,
    assume_renormalization_covariate_control_on_class: bool = False,
    assume_strict_golden_top_gap_theorem: bool = False,
    assume_challenger_exhaustion_beyond_current_panel: bool = False,
    **kwargs: Any,
) -> GoldenTheoremVIEnvelopeLiftCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    if threshold_identification_certificate is not None:
        identification = dict(threshold_identification_certificate)
    else:
        identification = build_golden_theorem_ii_to_v_identification_certificate(
            base_K_values=base_K_values,
            family=family,
            family_label=family_label,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_ii_to_v_identification_certificate, kwargs),
        ).to_dict()

    inherited_threshold_bridge = dict(threshold_bridge_certificate) if threshold_bridge_certificate is not None else _find_nested_mapping_with_key(identification, 'threshold_compatibility_bridge')
    inherited_eta_anchor = dict(eta_threshold_certificate) if eta_threshold_certificate is not None else _find_nested_mapping_with_key(identification, 'eta_threshold_anchor')
    inherited_proto = dict(proto_envelope_certificate) if proto_envelope_certificate is not None else _find_nested_mapping_with_key(identification, 'proto_envelope_bridge')
    inherited_near_top = dict(near_top_certificate) if near_top_certificate is not None else _find_nested_mapping_with_key(identification, 'near_top_challenger_surface')

    if inherited_eta_anchor is not None and not _eta_anchor_needs_refresh(inherited_eta_anchor):
        eta_anchor = dict(inherited_eta_anchor)
    else:
        eta_kwargs = _filter_kwargs(build_eta_threshold_comparison_certificate, kwargs)
        if inherited_threshold_bridge is not None:
            eta_kwargs.setdefault('threshold_bridge_certificate', inherited_threshold_bridge)
        eta_anchor = build_eta_threshold_comparison_certificate(
            family=family,
            family_label=family_label,
            rho=rho,
            **eta_kwargs,
        ).to_dict()

    if inherited_near_top is not None and not _near_top_surface_needs_promotion(inherited_near_top):
        near_top = dict(inherited_near_top)
    else:
        near_top = None
        screened_specs = None
        if auto_build_screened_near_top_panel and challenger_specs is None and challenger_campaign_report is None:
            screened_specs = _build_vi_screened_challenger_specs(
                eta_anchor=eta_anchor,
                family=family,
                challenger_classes=challenger_campaign_classes,
                kwargs=kwargs,
            )
            if screened_specs:
                near_top = build_near_top_eta_challenger_comparison_certificate(
                    screened_specs,
                    golden_eta_threshold_certificate=eta_anchor,
                    family=family,
                    family_label=family_label,
                    rho=rho,
                    **_filter_kwargs(build_near_top_eta_challenger_comparison_certificate, kwargs),
                ).to_dict()
        if near_top is None and challenger_campaign_report is not None:
            near_top = _build_vi_campaign_near_top_certificate(
                eta_anchor=eta_anchor,
                family=family,
                family_label=family_label,
                challenger_campaign_report=challenger_campaign_report,
                challenger_campaign_classes=challenger_campaign_classes,
                kwargs=kwargs,
            )
        elif near_top is None and auto_build_screened_near_top_panel and challenger_specs is None:
            near_top = _build_vi_campaign_near_top_certificate(
                eta_anchor=eta_anchor,
                family=family,
                family_label=family_label,
                challenger_campaign_report=None,
                challenger_campaign_classes=challenger_campaign_classes,
                kwargs=kwargs,
            )
        if near_top is None:
            near_top = build_near_top_eta_challenger_comparison_certificate(
                challenger_specs if challenger_specs is not None else screened_specs,
                golden_eta_threshold_certificate=eta_anchor,
                family=family,
                family_label=family_label,
                rho=rho,
                **_filter_kwargs(build_near_top_eta_challenger_comparison_certificate, kwargs),
            ).to_dict()

    proto_panel_records = _extract_panel_records_from_near_top(near_top)
    if inherited_proto is not None and not _proto_needs_panel(inherited_proto):
        proto = dict(inherited_proto)
    else:
        proto_kwargs = _filter_kwargs(build_proto_envelope_eta_bridge_certificate, kwargs)
        if proto_panel_records:
            proto_kwargs.setdefault('panel_records', proto_panel_records)
        proto = build_proto_envelope_eta_bridge_certificate(
            family=family,
            family_label=family_label,
            rho=rho,
            eta_threshold_certificate=eta_anchor,
            **proto_kwargs,
        ).to_dict()

    assumptions = _build_assumptions(
        assume_one_variable_eta_envelope_law=assume_one_variable_eta_envelope_law,
        assume_corrected_two_variable_envelope_law=assume_corrected_two_variable_envelope_law,
        assume_renormalization_covariate_control_on_class=assume_renormalization_covariate_control_on_class,
        assume_strict_golden_top_gap_theorem=assume_strict_golden_top_gap_theorem,
        assume_challenger_exhaustion_beyond_current_panel=assume_challenger_exhaustion_beyond_current_panel,
    )
    screened_near_top_dominance_certificate = _build_screened_near_top_dominance_certificate(near_top)
    current_local_top_gap_certificate = _build_current_local_top_gap_certificate(
        proto,
        near_top,
        screened_near_top_dominance_certificate=screened_near_top_dominance_certificate,
    )
    statement_mode_certificate = _merge_statement_mode_certificates(
        proto,
        near_top,
        current_local_top_gap_certificate=current_local_top_gap_certificate,
    )
    global_nongolden_ceiling_certificate = _build_global_nongolden_ceiling_certificate(proto, near_top)
    mode_obstruction_certificate = build_eta_mode_obstruction_certificate(statement_mode_certificate)
    mode_reduction_certificate = build_eta_mode_reduction_certificate(
        statement_mode_certificate,
        mode_obstruction_certificate=mode_obstruction_certificate,
        current_local_top_gap_status=current_local_top_gap_certificate.get('status'),
        anchor_globalization_certificate=dict(proto.get('anchor_globalization_certificate', {})),
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
    )
    if assume_one_variable_eta_envelope_law:
        mode_reduction_certificate = {
            **mode_reduction_certificate,
            'theorem_mode': 'one-variable',
            'theorem_mode_status': 'assumption-forced-one-variable',
            'reduction_certified': True,
            'remaining_burden': 'none',
        }
    elif assume_corrected_two_variable_envelope_law or assume_renormalization_covariate_control_on_class:
        mode_reduction_certificate = {
            **mode_reduction_certificate,
            'theorem_mode': 'two-variable',
            'theorem_mode_status': 'assumption-forced-two-variable',
            'reduction_certified': True,
            'remaining_burden': 'none',
        }
    global_nongolden_ceiling_certificate = _build_global_nongolden_ceiling_certificate(proto, near_top)
    global_envelope_certificate = build_eta_global_envelope_certificate(
        golden_lower_witness=_coerce_float(global_nongolden_ceiling_certificate.get('golden_lower_witness')),
        nongolden_global_upper_ceiling=_coerce_float(global_nongolden_ceiling_certificate.get('global_nongolden_upper_ceiling')),
        mode_reduction_certificate=mode_reduction_certificate,
        ceiling_decomposition=global_nongolden_ceiling_certificate,
        theorem_mode=mode_reduction_certificate.get('theorem_mode'),
    )
    strict_golden_top_gap_theorem_candidate = build_strict_golden_top_gap_theorem_candidate(global_envelope_certificate)
    statement_mode, relevant_local_assumptions = _choose_statement_mode(
        assumptions,
        statement_mode_certificate,
        mode_reduction_certificate=mode_reduction_certificate,
    )
    local_active_assumptions = [row.name for row in assumptions if row.name in relevant_local_assumptions and not row.assumed]
    upstream_active_assumptions = [str(x) for x in identification.get('active_assumptions', [])]

    hypotheses = _build_hypotheses(identification, eta_anchor, proto, near_top, current_local_top_gap_certificate=current_local_top_gap_certificate)
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    statement_mode_diagnostics = _build_statement_mode_diagnostics(
        assumptions,
        current_local_top_gap_certificate,
        statement_mode_certificate,
        mode_reduction_certificate=mode_reduction_certificate,
        mode_obstruction_certificate=mode_obstruction_certificate,
    )
    strict_golden_top_gap_certificate = _build_strict_golden_top_gap_certificate(
        statement_mode_diagnostics=statement_mode_diagnostics,
        current_local_top_gap_certificate=current_local_top_gap_certificate,
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
        global_envelope_certificate=global_envelope_certificate,
        strict_golden_top_gap_theorem_candidate=strict_golden_top_gap_theorem_candidate,
    )
    local_active_assumptions = _refine_local_active_assumptions(
        local_active_assumptions,
        strict_golden_top_gap_certificate=strict_golden_top_gap_certificate,
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
    )
    active_assumptions = upstream_active_assumptions + local_active_assumptions
    residual_burden_summary = _build_residual_burden_summary(
        open_hypotheses=open_hypotheses,
        local_active_assumptions=local_active_assumptions,
        upstream_active_assumptions=upstream_active_assumptions,
        current_local_top_gap_certificate=current_local_top_gap_certificate,
        screened_near_top_dominance_certificate=screened_near_top_dominance_certificate,
        strict_golden_top_gap_certificate=strict_golden_top_gap_certificate,
        statement_mode_diagnostics=statement_mode_diagnostics,
        mode_reduction_certificate=mode_reduction_certificate,
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
    )

    if not open_hypotheses and not active_assumptions and statement_mode == 'one-variable' and bool(strict_golden_top_gap_theorem_candidate.get('global_strict_top_gap_certified', False)):
        theorem_status = 'golden-theorem-vi-envelope-lift-global-one-variable-strong'
        notes = (
            'The current eta-anchor, proto-envelope, near-top challenger, and identification fronts are all closed, and the repository now certifies both the one-variable theorem mode and the global strict golden top gap.'
        )
    elif not open_hypotheses and not active_assumptions and statement_mode == 'two-variable' and bool(strict_golden_top_gap_theorem_candidate.get('global_strict_top_gap_certified', False)):
        theorem_status = 'golden-theorem-vi-envelope-lift-global-two-variable-strong'
        notes = (
            'The current eta-anchor, proto-envelope, near-top challenger, and identification fronts are all closed, and the repository now certifies the corrected theorem mode together with the global strict golden top gap.'
        )
    elif not open_hypotheses and not active_assumptions and statement_mode == 'one-variable':
        theorem_status = 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong'
        notes = (
            'The current eta-anchor, proto-envelope, near-top challenger, and identification fronts are all closed, and the one-variable eta law plus the strict top-gap/exhaustion assumptions are all assumed. '
            'This is the strongest current conditional Theorem-VI statement supported by the repository.'
        )
    elif not open_hypotheses and not active_assumptions and statement_mode == 'two-variable':
        theorem_status = 'golden-theorem-vi-envelope-lift-conditional-two-variable-strong'
        notes = (
            'The current eta-anchor, proto-envelope, near-top challenger, and identification fronts are all closed, and the corrected two-variable envelope law plus covariate control/top-gap/exhaustion assumptions are all assumed. '
            'This is the strongest current conditional corrected Theorem-VI statement supported by the repository.'
        )
    elif (
        not open_hypotheses
        and statement_mode == 'one-variable'
        and bool(statement_mode_diagnostics.get('theorem_mode_certified', False))
        and str(mode_reduction_certificate.get('theorem_mode_status', '')) == 'one-variable-reduction-certified-screened-panel'
        and bool(strict_golden_top_gap_certificate.get('screened_panel_strict_top_gap_certified', False))
    ):
        theorem_status = 'golden-theorem-vi-envelope-lift-screened-one-variable-strong'
        notes = (
            'The present Theorem VI front is locally theorem-grade in one-variable mode: identification is front-complete, the eta anchor is strong, the screened near-top panel certifies a positive local top-gap witness, and the strict golden top-gap certificate is promoted beyond raw exploratory geometry. '
            'The remaining burden is no longer local Theorem VI geometry; it is the global challenger-exhaustion handoff to Theorem VII.'
        )
    elif not open_hypotheses:
        theorem_status = 'golden-theorem-vi-envelope-lift-front-complete'
        notes = (
            'The present eta-envelope front is fully assembled: the identification shell is front-complete, a strong eta anchor exists, the proto-envelope bridge is in place, and the current near-top challenger surface has been packaged. '
            'What remains is the final choice and proof of the global envelope statement and challenger exhaustion.'
        )
        if residual_burden_summary.get('status') == 'global-theorem-burden-only':
            notes += ' The current finite VI geometry is already locally strong, so the remaining burden is theorem-grade/global rather than additional local gap assembly.'
        if strict_golden_top_gap_certificate.get('screened_panel_strict_top_gap_certified', False):
            notes += ' The current strict golden top gap is now promoted from a raw positive gap to a screened-panel certificate in the locked statement mode.'
    elif any(row.satisfied for row in hypotheses):
        theorem_status = 'golden-theorem-vi-envelope-lift-conditional-partial'
        notes = (
            'The repository now has a theorem-facing Theorem-VI envelope shell, but the current eta/proto-envelope/challenger front is only partially closed. '
            'Open front hypotheses must close before the remaining statement-choice assumptions become the only blockers.'
        )
    else:
        theorem_status = 'golden-theorem-vi-envelope-lift-failed'
        notes = 'The current data do not yet assemble into a usable conditional Theorem-VI envelope lift certificate.'

    return GoldenTheoremVIEnvelopeLiftCertificate(
        rho=float(rho),
        family_label=family_label,
        statement_mode=statement_mode,
        statement_mode_diagnostics=statement_mode_diagnostics,
        mode_reduction_certificate=mode_reduction_certificate,
        mode_obstruction_certificate=mode_obstruction_certificate,
        current_local_top_gap_certificate=current_local_top_gap_certificate,
        screened_near_top_dominance_certificate=screened_near_top_dominance_certificate,
        strict_golden_top_gap_certificate=strict_golden_top_gap_certificate,
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
        global_envelope_certificate=global_envelope_certificate,
        strict_golden_top_gap_theorem_candidate=strict_golden_top_gap_theorem_candidate,
        residual_burden_summary=residual_burden_summary,
        threshold_identification_shell=identification,
        eta_threshold_anchor=eta_anchor,
        proto_envelope_bridge=proto,
        near_top_challenger_surface=near_top,
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



def build_golden_theorem_vi_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    **kwargs: Any,
) -> GoldenTheoremVIEnvelopeLiftCertificate:
    return build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        family_label=family_label,
        rho=rho,
        **kwargs,
    )


__all__ = [
    'TheoremVIEnvelopeHypothesisRow',
    'TheoremVIEnvelopeAssumptionRow',
    'GoldenTheoremVIEnvelopeLiftCertificate',
    'build_golden_theorem_vi_envelope_lift_certificate',
    'build_golden_theorem_vi_certificate',
]
