from __future__ import annotations

"""Proxy renormalization-operator scaffolding for Workstream A.

This module is intentionally honest about what it is and is not.

It does *not* implement the rigorous golden renormalization operator from the
full theorem architecture.  Instead, it creates the first theorem-facing
operator surface that later validated fixed-point and stable-manifold code can
use:

* families are mapped to normalized chart representatives,
* higher modes are damped in a stable-direction proxy,
* family-level admissibility and chart certificates are threaded through the
  operator output, and
* every application emits explicit contraction / normalization diagnostics.

The point is to move the repository from "renormalization is completely absent"
to "there is a concrete operator interface with machine-readable diagnostics".
"""

from dataclasses import asdict, dataclass
from typing import Any

import math

from .standard_map import HarmonicFamily
from .universality_class import build_family_analytic_profile
from .renormalization_class import (
    build_renormalization_chart_profile,
    build_renormalization_class_certificate,
)


@dataclass
class ProxyRenormalizedFamily:
    harmonics: list[tuple[float, int, float]]
    anchor_scale: float
    higher_mode_contraction_ratio: float
    phase_contraction_ratio: float

    def to_family(self) -> HarmonicFamily:
        return HarmonicFamily(harmonics=list(self.harmonics))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RenormalizationOperatorCertificate:
    family_label: str
    input_chart_profile: dict[str, Any]
    output_chart_profile: dict[str, Any]
    input_class_certificate: dict[str, Any]
    output_class_certificate: dict[str, Any]
    proxy_output_family: dict[str, Any]
    operator_parameters: dict[str, float]
    normalization_metrics: dict[str, float]
    contraction_metrics: dict[str, float]
    operator_flags: dict[str, bool]
    operator_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def _sorted_harmonics(family: HarmonicFamily) -> list[tuple[float, int, float]]:
    harmonics = list(getattr(family, 'harmonics', []) or [(1.0, 1, 0.0)])
    harmonics = [(float(a), int(m), float(p)) for a, m, p in harmonics]
    harmonics.sort(key=lambda h: (h[1], abs(h[2]), abs(h[0])))
    return harmonics



def _anchor_from_harmonics(harmonics: list[tuple[float, int, float]]) -> tuple[float, float]:
    for amp, mode, phase in harmonics:
        if int(mode) == 1:
            return float(amp), float(phase)
    return 0.0, 0.0



def apply_proxy_renormalization_operator(
    family: HarmonicFamily,
    *,
    stable_damping: float = 0.6,
    phase_damping: float = 0.5,
    mode_penalty_power: float = 1.0,
    anchor_target_amplitude: float = 1.0,
) -> ProxyRenormalizedFamily:
    """Return a normalized proxy chart iterate.

    The map is chosen to be structurally sensible rather than theorem-grade:
    the anchor mode is rescaled to a fixed target amplitude, anchor phase is
    damped, and higher modes are contracted by a stable-direction damping factor
    and a mode-dependent penalty.
    """
    harmonics = _sorted_harmonics(family)
    anchor_amp, _anchor_phase = _anchor_from_harmonics(harmonics)
    if abs(anchor_amp) < 1e-12:
        anchor_scale = 1.0
    else:
        anchor_scale = float(anchor_target_amplitude / anchor_amp)

    out: list[tuple[float, int, float]] = []
    higher_in = 0.0
    higher_out = 0.0
    for amp, mode, phase in harmonics:
        scaled_amp = float(anchor_scale * amp)
        if int(mode) == 1:
            new_amp = float(anchor_target_amplitude)
            new_phase = float(phase_damping * phase)
        else:
            mode_penalty = float(max(1, int(mode)) ** (-mode_penalty_power))
            new_amp = float(stable_damping * mode_penalty * scaled_amp)
            new_phase = float(phase_damping * phase)
            higher_in += float(abs(scaled_amp))
            higher_out += float(abs(new_amp))
        out.append((new_amp, int(mode), new_phase))

    contraction_ratio = 0.0 if higher_in <= 0.0 else float(higher_out / higher_in)
    return ProxyRenormalizedFamily(
        harmonics=out,
        anchor_scale=float(anchor_scale),
        higher_mode_contraction_ratio=float(contraction_ratio),
        phase_contraction_ratio=float(abs(phase_damping)),
    )



def build_renormalization_operator_certificate(
    family: HarmonicFamily,
    *,
    family_label: str = 'harmonic_family',
    stable_damping: float = 0.6,
    phase_damping: float = 0.5,
    mode_penalty_power: float = 1.0,
    anchor_target_amplitude: float = 1.0,
) -> RenormalizationOperatorCertificate:
    base_class = build_renormalization_class_certificate(family, family_label=family_label)
    in_profile = build_renormalization_chart_profile(family)
    proxy = apply_proxy_renormalization_operator(
        family,
        stable_damping=stable_damping,
        phase_damping=phase_damping,
        mode_penalty_power=mode_penalty_power,
        anchor_target_amplitude=anchor_target_amplitude,
    )
    out_family = proxy.to_family()
    out_class = build_renormalization_class_certificate(out_family, family_label=f'{family_label}_renorm')
    out_profile = build_renormalization_chart_profile(out_family)
    analytic_in = build_family_analytic_profile(family)
    analytic_out = build_family_analytic_profile(out_family)

    radius_ratio = float(
        out_profile.chart_radius_proxy / max(in_profile.chart_radius_proxy, 1e-12)
        if in_profile.chart_radius_proxy > 0.0
        else 0.0
    )
    higher_ratio = float(
        analytic_out.higher_mode_energy / max(analytic_in.higher_mode_energy, 1e-12)
        if analytic_in.higher_mode_energy > 0.0
        else 0.0
    )
    anchor_error = abs(float(analytic_out.anchor_amplitude) - float(anchor_target_amplitude))
    phase_ratio = float(
        abs(analytic_out.anchor_phase) / max(abs(analytic_in.anchor_phase), 1e-12)
        if abs(analytic_in.anchor_phase) > 0.0
        else 0.0
    )

    normalization_metrics = {
        'anchor_scale': float(proxy.anchor_scale),
        'anchor_target_amplitude': float(anchor_target_amplitude),
        'anchor_output_error': float(anchor_error),
        'input_anchor_phase_abs': float(abs(analytic_in.anchor_phase)),
        'output_anchor_phase_abs': float(abs(analytic_out.anchor_phase)),
    }
    contraction_metrics = {
        'chart_radius_ratio': float(radius_ratio),
        'higher_mode_energy_ratio': float(higher_ratio),
        'phase_ratio': float(phase_ratio),
        'proxy_higher_mode_contraction_ratio': float(proxy.higher_mode_contraction_ratio),
    }
    flags = {
        'input_chart_admissible': bool(base_class.admissible_near_chart),
        'output_chart_admissible': bool(out_class.admissible_near_chart),
        'anchor_normalized': bool(anchor_error <= 1e-12),
        'higher_modes_nonexpanding': bool(higher_ratio <= 1.0 + 1e-12),
        'chart_radius_nonexpanding': bool(radius_ratio <= 1.0 + 1e-12),
        'phase_nonexpanding': bool(phase_ratio <= 1.0 + 1e-12),
    }
    status = 'proxy-renormalization-operator-stable-chart' if all(flags.values()) else 'proxy-renormalization-operator-mixed'
    return RenormalizationOperatorCertificate(
        family_label=str(family_label),
        input_chart_profile=in_profile.to_dict(),
        output_chart_profile=out_profile.to_dict(),
        input_class_certificate=base_class.to_dict(),
        output_class_certificate=out_class.to_dict(),
        proxy_output_family=proxy.to_dict(),
        operator_parameters={
            'stable_damping': float(stable_damping),
            'phase_damping': float(phase_damping),
            'mode_penalty_power': float(mode_penalty_power),
            'anchor_target_amplitude': float(anchor_target_amplitude),
        },
        normalization_metrics=normalization_metrics,
        contraction_metrics=contraction_metrics,
        operator_flags=flags,
        operator_status=status,
    )
