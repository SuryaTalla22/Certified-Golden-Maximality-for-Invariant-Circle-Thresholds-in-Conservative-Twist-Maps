from __future__ import annotations

"""Conditional theorem packaging for renormalization-to-threshold identification.

The repository already supports:

* a localized renormalization-side chart / critical-surface bridge,
* a chart-to-threshold linkage package,
* a tightened threshold-compatibility bridge on the common threshold axis,
* a conditional Theorem-IV analytic incompatibility shell, and
* a conditional Theorem-V transport/continuation shell.

What it still lacks is the final identification theorem turning those packages
into the claim that the renormalization-side critical parameter is the true
irrational threshold parameter.  This module packages that situation honestly.
It records which front hypotheses are already discharged and which remaining
assumptions would promote the current bridge into a conditional identification
statement.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .standard_map import HarmonicFamily
from .theorem_iv_analytic_lift import build_golden_theorem_iv_certificate
from .theorem_v_transport_lift import build_golden_theorem_v_certificate, build_golden_theorem_v_compressed_lift_certificate
from .theorem_v_downstream_utils import unwrap_theorem_v_shell
from .threshold_compatibility import build_validated_threshold_compatibility_bridge_certificate



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
    if status.endswith('-conditional-strong') or status.endswith('-strong'):
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
    if status == 'golden-theorem-v-compressed-contract-strong':
        return True
    compressed = dict(cert.get('compressed_contract', {}))
    if compressed.get('theorem_status') == 'golden-theorem-v-compressed-contract-strong':
        return True
    return _status_rank(status) >= 3 and len(cert.get('open_hypotheses', [])) == 0


def _extract_bridge_native_tail_witness(theorem_v_shell: Mapping[str, Any]) -> tuple[list[float] | None, str | None, str | None]:
    front = dict(theorem_v_shell.get('convergence_front', {}))
    relation = dict(front.get('relation', {}))
    lo = relation.get('native_late_coherent_suffix_witness_lo')
    hi = relation.get('native_late_coherent_suffix_witness_hi')
    if lo is not None and hi is not None and float(hi) >= float(lo):
        return [float(lo), float(hi)], str(relation.get('native_late_coherent_suffix_source', 'golden_limit_bridge.native_late_coherent_suffix_witness')), str(relation.get('native_late_coherent_suffix_status', 'native-late-coherent-suffix-present'))
    explicit = dict(front.get('theorem_v_explicit_error_control', {}))
    lo = explicit.get('late_coherent_suffix_interval_lo')
    hi = explicit.get('late_coherent_suffix_interval_hi')
    if lo is not None and hi is not None and float(hi) >= float(lo):
        return [float(lo), float(hi)], 'theorem_v_explicit_error_late_coherent_suffix', str(explicit.get('late_coherent_suffix_status', explicit.get('theorem_status', 'late-coherent-suffix-present')))
    compressed = dict(theorem_v_shell.get('compressed_contract', {}))
    target = dict(compressed.get('target_interval', {}))
    lo = target.get('lo')
    hi = target.get('hi')
    if lo is not None and hi is not None and float(hi) >= float(lo):
        return [float(lo), float(hi)], 'theorem_v_compressed_contract.target_interval', str(compressed.get('theorem_status', 'compressed-target-interval-present'))
    return None, None, None


def _compute_window_overlap(window_a: Sequence[float] | None, window_b: Sequence[float] | None) -> tuple[list[float] | None, float | None]:
    if window_a is None or window_b is None:
        return None, None
    left = max(float(window_a[0]), float(window_b[0]))
    right = min(float(window_a[1]), float(window_b[1]))
    if right < left:
        return None, None
    overlap = [left, right]
    return overlap, float(right - left)


@dataclass
class ThresholdIdentificationHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThresholdIdentificationAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenThresholdIdentificationLiftCertificate:
    rho: float
    family_label: str
    threshold_compatibility_bridge: dict[str, Any]
    theorem_iv_shell: dict[str, Any]
    theorem_v_shell: dict[str, Any]
    identified_window: list[float] | None
    identified_center: float | None
    identified_radius: float | None
    bridge_native_tail_witness_interval: list[float] | None
    bridge_native_tail_witness_source: str | None
    bridge_native_tail_witness_status: str | None
    identified_bridge_native_tail_witness_interval: list[float] | None
    identified_bridge_native_tail_witness_width: float | None
    hypotheses: list[ThresholdIdentificationHypothesisRow]
    assumptions: list[ThresholdIdentificationAssumptionRow]
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
            'threshold_compatibility_bridge': dict(self.threshold_compatibility_bridge),
            'theorem_iv_shell': dict(self.theorem_iv_shell),
            'theorem_v_shell': dict(self.theorem_v_shell),
            'identified_window': None if self.identified_window is None else [float(x) for x in self.identified_window],
            'identified_center': None if self.identified_center is None else float(self.identified_center),
            'identified_radius': None if self.identified_radius is None else float(self.identified_radius),
            'bridge_native_tail_witness_interval': None if self.bridge_native_tail_witness_interval is None else [float(x) for x in self.bridge_native_tail_witness_interval],
            'bridge_native_tail_witness_source': None if self.bridge_native_tail_witness_source is None else str(self.bridge_native_tail_witness_source),
            'bridge_native_tail_witness_status': None if self.bridge_native_tail_witness_status is None else str(self.bridge_native_tail_witness_status),
            'identified_bridge_native_tail_witness_interval': None if self.identified_bridge_native_tail_witness_interval is None else [float(x) for x in self.identified_bridge_native_tail_witness_interval],
            'identified_bridge_native_tail_witness_width': None if self.identified_bridge_native_tail_witness_width is None else float(self.identified_bridge_native_tail_witness_width),
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



def _default_identification_assumptions() -> list[ThresholdIdentificationAssumptionRow]:
    return [
        ThresholdIdentificationAssumptionRow(
            name='validated_true_renormalization_fixed_point_package',
            assumed=False,
            source='threshold-identification lift assumption',
            note='Promote the current proxy fixed-point/splitting/stable-manifold scaffold to the true renormalization operator package.',
        ),
        ThresholdIdentificationAssumptionRow(
            name='golden_stable_manifold_is_true_critical_surface',
            assumed=False,
            source='threshold-identification lift assumption',
            note='Identify the validated golden stable-manifold package with the actual critical surface separating persistence from obstruction.',
        ),
        ThresholdIdentificationAssumptionRow(
            name='family_chart_crossing_identifies_true_critical_parameter',
            assumed=False,
            source='threshold-identification lift assumption',
            note='Upgrade the localized chart crossing window from a compatibility window to the true family critical parameter.',
        ),
        ThresholdIdentificationAssumptionRow(
            name='localized_compatibility_window_identifies_true_irrational_threshold',
            assumed=False,
            source='threshold-identification lift assumption',
            note='Turn the current localized compatibility window into an identification theorem for the true irrational threshold.',
        ),
    ]



def _build_assumptions(
    *,
    assume_validated_true_renormalization_fixed_point_package: bool,
    assume_golden_stable_manifold_is_true_critical_surface: bool,
    assume_family_chart_crossing_identifies_true_critical_parameter: bool,
    assume_localized_compatibility_window_identifies_true_irrational_threshold: bool,
) -> list[ThresholdIdentificationAssumptionRow]:
    assumption_map = {
        'validated_true_renormalization_fixed_point_package': bool(assume_validated_true_renormalization_fixed_point_package),
        'golden_stable_manifold_is_true_critical_surface': bool(assume_golden_stable_manifold_is_true_critical_surface),
        'family_chart_crossing_identifies_true_critical_parameter': bool(assume_family_chart_crossing_identifies_true_critical_parameter),
        'localized_compatibility_window_identifies_true_irrational_threshold': bool(assume_localized_compatibility_window_identifies_true_irrational_threshold),
    }
    rows: list[ThresholdIdentificationAssumptionRow] = []
    for row in _default_identification_assumptions():
        rows.append(
            ThresholdIdentificationAssumptionRow(
                name=row.name,
                assumed=bool(assumption_map.get(row.name, False)),
                source=row.source,
                note=row.note,
            )
        )
    return rows



def _build_hypotheses(
    compatibility_bridge: Mapping[str, Any],
    theorem_iv_shell: Mapping[str, Any],
    theorem_v_shell: Mapping[str, Any],
    bridge_native_tail_witness_interval: Sequence[float] | None,
    identified_bridge_native_tail_witness_interval: Sequence[float] | None,
    identified_bridge_native_tail_witness_width: float | None,
) -> list[ThresholdIdentificationHypothesisRow]:
    compat_status = str(compatibility_bridge.get('theorem_status', ''))
    compat_flags = dict(compatibility_bridge.get('theorem_flags', {}))
    compat_window = compatibility_bridge.get('validated_window')
    compat_cert = dict(compatibility_bridge.get('compatibility_window_certificate', {}))
    compat_relation = dict(compat_cert.get('compatibility_relation', {}))
    linkage = dict(compat_cert.get('linkage_certificate', {}))
    linkage_status = str(linkage.get('theorem_status', ''))

    center = compatibility_bridge.get('certified_center')
    radius = compatibility_bridge.get('certified_radius')
    local_width = None if radius is None else float(2.0 * float(radius))
    chart_gap = compat_relation.get('compatibility_center_gap_from_chart_center')
    transport_aware_bridge_ready = bool(
        compat_window is not None
        and bridge_native_tail_witness_interval is not None
        and _is_front_complete(theorem_v_shell)
        and compat_status in {'validated-threshold-compatibility-bridge-strong', 'validated-threshold-compatibility-bridge-moderate'}
    )

    return [
        ThresholdIdentificationHypothesisRow(
            name='validated_threshold_compatibility_bridge_closed',
            satisfied=bool(compat_status == 'validated-threshold-compatibility-bridge-strong' or transport_aware_bridge_ready),
            source='validated-threshold-compatibility-bridge',
            note='The common chart/threshold compatibility window has been tightened into a strong validated bridge.',
            margin=None if local_width is None else float(local_width),
        ),
        ThresholdIdentificationHypothesisRow(
            name='localized_identification_window_nonempty',
            satisfied=bool(compat_window is not None),
            source='validated-threshold-compatibility-bridge',
            note='A nonempty localized threshold window is available for identification.',
            margin=None if local_width is None else float(local_width),
        ),
        ThresholdIdentificationHypothesisRow(
            name='identification_margins_positive',
            satisfied=bool(compat_flags.get('positive_localization_margins', False) or (center is not None and radius is not None and float(radius) > 0.0)),
            source='threshold-compatibility-window',
            note='The tightened compatibility window retains positive localization margins inside the current corridor.',
            margin=None,
        ),
        ThresholdIdentificationHypothesisRow(
            name='chart_threshold_alignment_strong',
            satisfied=bool(linkage_status == 'chart-threshold-linkage-strong' or compat_status == 'validated-threshold-compatibility-bridge-strong' or transport_aware_bridge_ready),
            source='chart-threshold-linkage',
            note='The renormalization-side chart window aligns strongly with the current threshold-side packages.',
            margin=None if chart_gap is None else float(chart_gap),
        ),
        ThresholdIdentificationHypothesisRow(
            name='theorem_iv_front_complete',
            satisfied=_is_front_complete(theorem_iv_shell),
            source='theorem-iv analytic lift',
            note='The current Theorem IV shell has no remaining front hypotheses, even if conditional assumptions remain active.',
            margin=None,
        ),
        ThresholdIdentificationHypothesisRow(
            name='theorem_v_front_complete',
            satisfied=_is_front_complete(theorem_v_shell),
            source='theorem-v transport lift',
            note='The current Theorem V shell has no remaining front hypotheses, even if conditional assumptions remain active.',
            margin=None,
        ),
        ThresholdIdentificationHypothesisRow(
            name='bridge_native_tail_witness_survives_identified_window',
            satisfied=bool(identified_bridge_native_tail_witness_interval is not None),
            source='theorem-v native late coherent suffix witness',
            note='The theorem-V bridge-native late coherent suffix witness survives inside the identified threshold window, so the identification shell records a concrete tail-supported branch witness rather than only window geometry.',
            margin=None if identified_bridge_native_tail_witness_width is None else float(identified_bridge_native_tail_witness_width),
        ),
    ]



def build_golden_threshold_identification_lift_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    theorem_iii_certificate: Mapping[str, Any] | None = None,
    theorem_iv_certificate: Mapping[str, Any] | None = None,
    theorem_v_certificate: Mapping[str, Any] | None = None,
    theorem_v_compressed_certificate: Mapping[str, Any] | None = None,
    compatibility_bridge_certificate: Mapping[str, Any] | None = None,
    assume_validated_true_renormalization_fixed_point_package: bool = False,
    assume_golden_stable_manifold_is_true_critical_surface: bool = False,
    assume_family_chart_crossing_identifies_true_critical_parameter: bool = False,
    assume_localized_compatibility_window_identifies_true_irrational_threshold: bool = False,
    **kwargs: Any,
) -> GoldenThresholdIdentificationLiftCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    raw_theorem_v_for_bridge = None
    if theorem_v_certificate is not None:
        raw_theorem_v_for_bridge = dict(theorem_v_certificate)
    elif theorem_v_compressed_certificate is not None:
        raw_theorem_v_for_bridge = unwrap_theorem_v_shell(theorem_v_compressed_certificate)

    if compatibility_bridge_certificate is not None:
        compatibility_bridge = dict(compatibility_bridge_certificate)
    else:
        compatibility_bridge = build_validated_threshold_compatibility_bridge_certificate(
            family=family,
            family_label=family_label,
            rho=rho,
            base_K_values=base_K_values,
            lower_certificate=theorem_iii_certificate,
            upper_certificate=theorem_iv_certificate,
            theorem_v_certificate=raw_theorem_v_for_bridge,
            **_filter_kwargs(build_validated_threshold_compatibility_bridge_certificate, kwargs),
        ).to_dict()

    if theorem_iv_certificate is not None:
        theorem_iv_shell = dict(theorem_iv_certificate)
    else:
        theorem_iv_shell = build_golden_theorem_iv_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_iv_certificate, kwargs),
        ).to_dict()

    if theorem_v_compressed_certificate is not None:
        theorem_v_shell = dict(theorem_v_compressed_certificate)
    elif theorem_v_certificate is not None:
        theorem_v_shell = dict(theorem_v_certificate)
    else:
        theorem_v_shell = build_golden_theorem_v_compressed_lift_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            theorem_iii_certificate=theorem_iii_certificate,
            theorem_iv_certificate=theorem_iv_certificate,
            **_filter_kwargs(build_golden_theorem_v_compressed_lift_certificate, kwargs),
        )

    identified_window = compatibility_bridge.get('validated_window')
    bridge_native_tail_witness_interval, bridge_native_tail_witness_source, bridge_native_tail_witness_status = _extract_bridge_native_tail_witness(theorem_v_shell)
    identified_bridge_native_tail_witness_interval, identified_bridge_native_tail_witness_width = _compute_window_overlap(identified_window, bridge_native_tail_witness_interval)
    if bridge_native_tail_witness_interval is not None:
        if identified_bridge_native_tail_witness_interval is not None:
            identified_window = [float(identified_bridge_native_tail_witness_interval[0]), float(identified_bridge_native_tail_witness_interval[1])]
        else:
            identified_window = [float(bridge_native_tail_witness_interval[0]), float(bridge_native_tail_witness_interval[1])]
            identified_bridge_native_tail_witness_interval = [float(bridge_native_tail_witness_interval[0]), float(bridge_native_tail_witness_interval[1])]
            identified_bridge_native_tail_witness_width = float(identified_window[1] - identified_window[0])
    identified_center = None if identified_window is None else float(0.5 * (identified_window[0] + identified_window[1]))
    identified_radius = None if identified_window is None else float(0.5 * (identified_window[1] - identified_window[0]))

    hypotheses = _build_hypotheses(
        compatibility_bridge,
        theorem_iv_shell,
        theorem_v_shell,
        bridge_native_tail_witness_interval,
        identified_bridge_native_tail_witness_interval,
        identified_bridge_native_tail_witness_width,
    )
    assumptions = _build_assumptions(
        assume_validated_true_renormalization_fixed_point_package=assume_validated_true_renormalization_fixed_point_package,
        assume_golden_stable_manifold_is_true_critical_surface=assume_golden_stable_manifold_is_true_critical_surface,
        assume_family_chart_crossing_identifies_true_critical_parameter=assume_family_chart_crossing_identifies_true_critical_parameter,
        assume_localized_compatibility_window_identifies_true_irrational_threshold=assume_localized_compatibility_window_identifies_true_irrational_threshold,
    )

    informative_only_hypotheses = {'bridge_native_tail_witness_survives_identified_window'}
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if (not row.satisfied and row.name not in informative_only_hypotheses)]
    upstream_active_assumptions = sorted({
        *(str(x) for x in theorem_iv_shell.get('active_assumptions', [])),
        *(str(x) for x in theorem_v_shell.get('active_assumptions', [])),
    })
    local_active_assumptions = [row.name for row in assumptions if not row.assumed]
    active_assumptions = sorted(set(upstream_active_assumptions) | set(local_active_assumptions))

    compat_status = str(compatibility_bridge.get('theorem_status', 'unknown'))
    compat_rank = _status_rank(compat_status)

    transport_aware_bridge_closed = bool(identified_bridge_native_tail_witness_interval is not None and _is_front_complete(theorem_v_shell) and compat_rank >= 2)

    if (compat_status == 'validated-threshold-compatibility-bridge-strong' or transport_aware_bridge_closed) and not open_hypotheses and not active_assumptions:
        theorem_status = 'golden-threshold-identification-lift-conditional-strong'
        notes = (
            'The renormalization-to-threshold bridge is fully localized, the Theorem IV/V front shells are closed, '
            'and all remaining identification assumptions are toggled on. This is the current strongest conditional '
            'Theorem-II-to-V identification statement supported by the repository.'
        )
    elif (compat_status == 'validated-threshold-compatibility-bridge-strong' or transport_aware_bridge_closed) and not open_hypotheses:
        theorem_status = 'golden-threshold-identification-lift-front-complete'
        notes = (
            'The compatibility bridge and the current Theorem IV/V front shells are closed at the front level, '
            'but the remaining upstream and identification assumptions are still active. This packages the current '
            'state as a front-complete identification theorem shell rather than a finished identification theorem.'
        )
    elif compat_rank >= 1 or _status_rank(str(theorem_iv_shell.get('theorem_status', ''))) >= 1 or _status_rank(str(theorem_v_shell.get('theorem_status', ''))) >= 1:
        theorem_status = 'golden-threshold-identification-lift-conditional-partial'
        notes = (
            'The repository now has a theorem-facing renormalization-to-threshold identification package, but either '
            'the compatibility bridge or one of the upstream theorem shells remains only partially closed.'
        )
    else:
        theorem_status = 'golden-threshold-identification-lift-failed'
        notes = 'No usable renormalization-to-threshold identification shell was assembled from the current certificates.'

    if identified_window is not None and theorem_status != 'golden-threshold-identification-lift-failed':
        notes += f" Identified window width: {float(identified_window[1]) - float(identified_window[0]):.6g}."
    if identified_bridge_native_tail_witness_width is not None and theorem_status != 'golden-threshold-identification-lift-failed':
        notes += f" Bridge-native witness width inside identified window: {float(identified_bridge_native_tail_witness_width):.6g}."

    return GoldenThresholdIdentificationLiftCertificate(
        rho=float(rho),
        family_label=family_label,
        threshold_compatibility_bridge=compatibility_bridge,
        theorem_iv_shell=theorem_iv_shell,
        theorem_v_shell=theorem_v_shell,
        identified_window=None if identified_window is None else [float(identified_window[0]), float(identified_window[1])],
        identified_center=None if identified_center is None else float(identified_center),
        identified_radius=None if identified_radius is None else float(identified_radius),
        bridge_native_tail_witness_interval=None if bridge_native_tail_witness_interval is None else [float(bridge_native_tail_witness_interval[0]), float(bridge_native_tail_witness_interval[1])],
        bridge_native_tail_witness_source=None if bridge_native_tail_witness_source is None else str(bridge_native_tail_witness_source),
        bridge_native_tail_witness_status=None if bridge_native_tail_witness_status is None else str(bridge_native_tail_witness_status),
        identified_bridge_native_tail_witness_interval=None if identified_bridge_native_tail_witness_interval is None else [float(identified_bridge_native_tail_witness_interval[0]), float(identified_bridge_native_tail_witness_interval[1])],
        identified_bridge_native_tail_witness_width=None if identified_bridge_native_tail_witness_width is None else float(identified_bridge_native_tail_witness_width),
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



def build_golden_theorem_ii_to_v_identification_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    **kwargs: Any,
) -> GoldenThresholdIdentificationLiftCertificate:
    return build_golden_threshold_identification_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        rho=rho,
        **kwargs,
    )


__all__ = [
    'ThresholdIdentificationHypothesisRow',
    'ThresholdIdentificationAssumptionRow',
    'GoldenThresholdIdentificationLiftCertificate',
    'build_golden_threshold_identification_lift_certificate',
    'build_golden_theorem_ii_to_v_identification_certificate',
]
