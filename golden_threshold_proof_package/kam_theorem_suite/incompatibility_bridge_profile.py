from __future__ import annotations

"""Robustness profiles for the upper incompatibility theorem bridge.

The stage-34 theorem bridge compressed the current upper-side obstruction stack
into one explicit hypothesis ledger, but stage-35 showed a practical weakness:
under honest lightweight runs the strict bridge can fail even when a slightly
relaxed, still theorem-facing profile closes cleanly.

This module addresses that bottleneck without hiding it.  It evaluates a small
ladder of bridge profiles, records which ones close, and selects the strongest
currently usable bridge together with a robustness summary.  The result is not a
new theorem; it is a sharper object for deciding whether the current upper-side
front is merely failing a strict profile or genuinely failing altogether.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .incompatibility_theorem_bridge import (
    build_golden_incompatibility_theorem_bridge_certificate,
)
from .standard_map import HarmonicFamily


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'


def _status_rank(status: str) -> int:
    if status.endswith('-strong'):
        return 4
    if status.endswith('-moderate'):
        return 3
    if status.endswith('-weak'):
        return 2
    if status.endswith('-fragile'):
        return 1
    return 0


def _strictness_rank(name: str) -> int:
    order = {'strict': 3, 'balanced': 2, 'lightweight': 1}
    return int(order.get(str(name), 0))


@dataclass
class IncompatibilityBridgeProfileRow:
    profile_name: str
    profile_parameters: dict[str, Any]
    bridge: dict[str, Any]
    status_rank: int
    strictness_rank: int
    bridge_margin: float | None
    usable: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenIncompatibilityBridgeProfileCertificate:
    rho: float
    family_label: str
    profile_results: list[dict[str, Any]]
    selected_profile_name: str
    selected_bridge: dict[str, Any]
    selected_status_rank: int
    viable_profile_names: list[str]
    strong_profile_names: list[str]
    viable_profile_count: int
    strong_profile_count: int
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_DEFAULT_PROFILE_ORDER = ('strict', 'balanced', 'lightweight')


def _default_profiles(
    require_suffix_tail: bool,
    min_tail_members: int,
) -> list[dict[str, Any]]:
    return [
        {
            'name': 'strict',
            'min_cluster_size': 2,
            'min_tail_members': max(2, int(min_tail_members)),
            'min_support_fraction': 0.75,
            'min_entry_coverage': 0.75,
            'min_gap_to_width_ratio': 1.0,
            'require_suffix_tail': bool(require_suffix_tail),
        },
        {
            'name': 'balanced',
            'min_cluster_size': 1,
            'min_tail_members': max(1, int(min_tail_members)),
            'min_support_fraction': 0.6,
            'min_entry_coverage': 0.6,
            'min_gap_to_width_ratio': 0.5,
            'require_suffix_tail': False,
        },
        {
            'name': 'lightweight',
            'min_cluster_size': 1,
            'min_tail_members': 1,
            'min_support_fraction': 0.5,
            'min_entry_coverage': 0.5,
            'min_gap_to_width_ratio': 0.25,
            'require_suffix_tail': False,
        },
    ]


def build_golden_incompatibility_bridge_profile_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    profile_overrides: Sequence[Mapping[str, Any]] | None = None,
    require_suffix_tail: bool = False,
    min_tail_members: int = 2,
    **bridge_kwargs,
) -> GoldenIncompatibilityBridgeProfileCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)

    profiles = list(profile_overrides) if profile_overrides is not None else _default_profiles(
        require_suffix_tail=bool(require_suffix_tail),
        min_tail_members=int(min_tail_members),
    )
    results: list[IncompatibilityBridgeProfileRow] = []

    for base in profiles:
        params = dict(base)
        name = str(params.pop('name', 'custom'))
        params.setdefault('require_suffix_tail', False)
        bridge = build_golden_incompatibility_theorem_bridge_certificate(
            family=family,
            rho=rho,
            **params,
            **bridge_kwargs,
        ).to_dict()
        status = str(bridge.get('theorem_status', 'golden-incompatibility-theorem-bridge-failed'))
        rank = _status_rank(status)
        results.append(IncompatibilityBridgeProfileRow(
            profile_name=name,
            profile_parameters={'name': name, **params},
            bridge=bridge,
            status_rank=rank,
            strictness_rank=_strictness_rank(name),
            bridge_margin=None if bridge.get('bridge_margin') is None else float(bridge['bridge_margin']),
            usable=rank >= 2,
        ))

    if results:
        selected = max(
            results,
            key=lambda row: (
                int(row.status_rank),
                int(row.strictness_rank),
                float('-inf') if row.bridge_margin is None else float(row.bridge_margin),
                len(row.bridge.get('certified_tail_qs', []) or []),
                int(row.bridge.get('supporting_entry_count', 0)),
            ),
        )
    else:
        selected = IncompatibilityBridgeProfileRow(
            profile_name='none',
            profile_parameters={'name': 'none'},
            bridge={'theorem_status': 'golden-incompatibility-theorem-bridge-failed'},
            status_rank=0,
            strictness_rank=0,
            bridge_margin=None,
            usable=False,
        )

    viable_names = [row.profile_name for row in results if row.usable]
    strong_names = [row.profile_name for row in results if row.status_rank >= 4]
    viable_count = len(viable_names)
    strong_count = len(strong_names)

    if selected.status_rank >= 4 and strong_count >= 2:
        status = 'golden-incompatibility-bridge-profile-strong'
        notes = 'Multiple bridge profiles close strongly, and the selected upper bridge is not a one-profile accident.'
    elif selected.status_rank >= 4:
        status = 'golden-incompatibility-bridge-profile-moderate'
        notes = 'A strong upper bridge closes under the selected profile, but robustness across stricter profiles is still limited.'
    elif selected.status_rank >= 3 or viable_count >= 2:
        status = 'golden-incompatibility-bridge-profile-weak'
        notes = 'At least one usable upper bridge closes, but the profile ladder still shows sensitivity in the current tail-support/gap conditions.'
    elif selected.status_rank >= 1:
        status = 'golden-incompatibility-bridge-profile-fragile'
        notes = 'Only a fragile upper bridge survives the current profile ladder.'
    else:
        status = 'golden-incompatibility-bridge-profile-failed'
        notes = 'No usable upper bridge closes across the current profile ladder.'

    return GoldenIncompatibilityBridgeProfileCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        profile_results=[row.to_dict() for row in results],
        selected_profile_name=str(selected.profile_name),
        selected_bridge=dict(selected.bridge),
        selected_status_rank=int(selected.status_rank),
        viable_profile_names=[str(x) for x in viable_names],
        strong_profile_names=[str(x) for x in strong_names],
        viable_profile_count=int(viable_count),
        strong_profile_count=int(strong_count),
        theorem_status=status,
        notes=notes,
    )


__all__ = [
    'build_golden_incompatibility_bridge_profile_certificate',
    'GoldenIncompatibilityBridgeProfileCertificate',
]
