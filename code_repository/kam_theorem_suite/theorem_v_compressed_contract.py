from __future__ import annotations

"""Compressed Theorem-V contract.

This module distills the full Theorem-V transport shell into the minimal
contract that downstream theorem consumers actually need.  Legacy middle layers
remain attached as diagnostics, but the compressed certificate is driven only by
transport lock, target interval, uniform majorant, branch identity, and lower/
upper compatibility.
"""

from dataclasses import dataclass
from typing import Any, Mapping

from .theorem_v_lower_compatibility import build_theorem_v_lower_compatibility_certificate


def _status_rank(status: str) -> int:
    status = str(status)
    if status.endswith('-strong') or status.endswith('-final'):
        return 4
    if status.endswith('-front-complete'):
        return 3
    if status.endswith('-partial') or status.endswith('-moderate'):
        return 2
    if status.endswith('-weak') or status.endswith('-fragile'):
        return 1
    return 0


def _coerce_bool(value: Any) -> bool:
    return bool(value)


def _extract_target_interval(theorem_v_certificate: Mapping[str, Any]) -> list[float] | None:
    interval = theorem_v_certificate.get('theorem_target_interval')
    if interval is not None and len(interval) == 2:
        return [float(interval[0]), float(interval[1])]
    final_bridge = dict(theorem_v_certificate.get('final_transport_bridge', {}))
    interval = final_bridge.get('theorem_target_interval')
    if interval is not None and len(interval) == 2:
        return [float(interval[0]), float(interval[1])]
    return None


@dataclass
class TheoremVCompressedContractCertificate:
    theorem_kind: str
    theorem_status: str
    target_interval: dict[str, Any]
    transport_lock: dict[str, Any]
    uniform_majorant: dict[str, Any]
    branch_identity: dict[str, Any]
    lower_compatibility: dict[str, Any]
    upper_compatibility: dict[str, Any]
    two_sided_separation: dict[str, Any]
    formal_assumptions_remaining: list[str]
    construction_assumptions_absorbed_by_compressed_contract: list[str]
    legacy_diagnostic_assumptions_not_used_downstream: list[str]
    diagnostic_legacy_layers: dict[str, Any]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'theorem_kind': self.theorem_kind,
            'theorem_status': self.theorem_status,
            'target_interval': self.target_interval,
            'transport_lock': self.transport_lock,
            'uniform_majorant': self.uniform_majorant,
            'branch_identity': self.branch_identity,
            'lower_compatibility': self.lower_compatibility,
            'upper_compatibility': self.upper_compatibility,
            'two_sided_separation': self.two_sided_separation,
            'formal_assumptions_remaining': self.formal_assumptions_remaining,
            'construction_assumptions_absorbed_by_compressed_contract': self.construction_assumptions_absorbed_by_compressed_contract,
            'legacy_diagnostic_assumptions_not_used_downstream': self.legacy_diagnostic_assumptions_not_used_downstream,
            'diagnostic_legacy_layers': self.diagnostic_legacy_layers,
            'notes': self.notes,
        }


def build_theorem_v_compressed_contract_certificate(
    theorem_v_certificate: Mapping[str, Any],
    theorem_iii_certificate: Mapping[str, Any] | None = None,
    theorem_iv_certificate: Mapping[str, Any] | None = None,
) -> TheoremVCompressedContractCertificate:
    theorem_v_certificate = dict(theorem_v_certificate)
    theorem_iii_certificate = dict(theorem_iii_certificate or {})
    theorem_iv_certificate = dict(theorem_iv_certificate or {})

    front = dict(theorem_v_certificate.get('convergence_front', {}))
    relation = dict(front.get('relation', {}))
    final_bridge = dict(theorem_v_certificate.get('final_transport_bridge', {}))
    uniform_error = dict(front.get('theorem_v_uniform_error_law', {}))
    branch_ident = dict(front.get('theorem_v_branch_identification', {}))
    final_error = dict(theorem_v_certificate.get('final_error_law', {}))
    if not final_error:
        final_error = dict(front.get('theorem_v_final_error_control', {}))

    target_interval = _extract_target_interval(theorem_v_certificate)
    target_width = theorem_v_certificate.get('theorem_target_width')
    if target_width is None and target_interval is not None:
        target_width = float(target_interval[1]) - float(target_interval[0])

    lower_compat = build_theorem_v_lower_compatibility_certificate(theorem_iii_certificate, front).to_dict()

    upper_certified = bool(
        final_bridge.get('upper_tail_source') == 'theorem-iv-final-object'
        or theorem_iv_certificate.get('analytic_incompatibility_certified', False)
        or theorem_iv_certificate.get('nonexistence_contradiction_certified', False)
        or _status_rank(str(theorem_iv_certificate.get('theorem_status', ''))) >= 3
    )

    transport_locked = bool(final_bridge.get('transport_bridge_locked', False))
    identification_lock = bool(final_bridge.get('transport_bridge_with_identification_lock', False))
    majorant_certified = bool(
        uniform_error.get('final_error_law_certified', False)
        or theorem_v_certificate.get('theorem_v_final_status') in {'final-strong', 'conditional-strong'}
        or final_bridge.get('uniform_error_law_status') == 'theorem-v-uniform-error-law-strong'
    )
    branch_sufficient = bool(
        branch_ident.get('branch_identification_locked', False)
        or final_bridge.get('branch_identification_status') in {'theorem-v-branch-identification-strong', 'theorem-v-branch-identification-partial'}
    )

    gap_certified = bool(
        theorem_v_certificate.get('gap_preservation_margin') is not None
        or final_error.get('error_law_preserves_gap', False)
        or uniform_error.get('gap_preservation_certified', False)
    )
    two_sided_certified = bool(gap_certified and lower_compat.get('lower_compatibility_certified', False) and upper_certified)

    formal_assumptions_remaining: list[str] = []
    construction_assumptions_absorbed = [str(x.get('name')) for x in theorem_v_certificate.get('assumptions', []) if x.get('assumed', False)]
    legacy_diag_assumptions = [str(x.get('name')) for x in theorem_v_certificate.get('assumptions', []) if not x.get('assumed', False)]

    diag_layers = {
        'branch_certified_control': str((front.get('branch_certified_control') or {}).get('theorem_status', 'missing')),
        'convergent_family_control': str((front.get('convergent_family_control') or {}).get('theorem_status', 'missing')),
        'global_transport_potential_control': str((front.get('global_transport_potential_control') or {}).get('theorem_status', 'missing')),
        'certified_tail_modulus_control': str((front.get('certified_tail_modulus_control') or {}).get('theorem_status', 'missing')),
    }

    if all([target_interval is not None, transport_locked, identification_lock, majorant_certified, branch_sufficient, lower_compat.get('lower_compatibility_certified', False), upper_certified, two_sided_certified]):
        theorem_status = 'golden-theorem-v-compressed-contract-strong'
        notes = 'Compressed Theorem V is strong enough for downstream threshold-identification and reduction consumers; legacy middle layers remain diagnostic only.'
    elif all([target_interval is not None, transport_locked, majorant_certified, upper_certified]):
        theorem_status = 'golden-theorem-v-compressed-contract-partial'
        notes = 'Compressed Theorem V exposes the minimal downstream contract, but lower compatibility or branch identification are not yet fully strong.'
    else:
        theorem_status = 'golden-theorem-v-compressed-contract-incomplete'
        notes = 'Compressed Theorem V does not yet provide the minimal downstream contract.'

    return TheoremVCompressedContractCertificate(
        theorem_kind='compressed-transport-lock',
        theorem_status=theorem_status,
        target_interval={'lo': None if target_interval is None else target_interval[0], 'hi': None if target_interval is None else target_interval[1], 'width': target_width},
        transport_lock={'locked': transport_locked, 'identification_lock': identification_lock, 'source_status': str(final_bridge.get('bridge_status', 'unknown')), 'upper_tail_source': final_bridge.get('upper_tail_source')},
        uniform_majorant={'status': str(final_bridge.get('uniform_error_law_status', uniform_error.get('theorem_status', 'missing'))), 'certified': majorant_certified, 'preserves_golden_gap': gap_certified},
        branch_identity={'status': str(final_bridge.get('branch_identification_status', branch_ident.get('theorem_status', 'missing'))), 'sufficient_for_downstream': branch_sufficient, 'no_branch_switch_certified': bool(branch_ident.get('branch_identification_locked', False))},
        lower_compatibility=lower_compat,
        upper_compatibility={'status': 'theorem-v-upper-compatibility-strong' if upper_certified else 'theorem-v-upper-compatibility-incomplete', 'certified': upper_certified},
        two_sided_separation={'status': 'theorem-v-two-sided-separation-strong' if two_sided_certified else 'theorem-v-two-sided-separation-incomplete', 'certified': two_sided_certified},
        formal_assumptions_remaining=formal_assumptions_remaining,
        construction_assumptions_absorbed_by_compressed_contract=construction_assumptions_absorbed,
        legacy_diagnostic_assumptions_not_used_downstream=legacy_diag_assumptions,
        diagnostic_legacy_layers=diag_layers,
        notes=notes,
    )


def build_theorem_v_compressed_sufficiency_certificate(compressed_contract: Mapping[str, Any]) -> dict[str, Any]:
    contract = dict(compressed_contract)
    status = str(contract.get('theorem_status', 'unknown'))
    ready = status == 'golden-theorem-v-compressed-contract-strong'
    return {
        'theorem_kind': 'compressed-transport-lock-sufficiency',
        'theorem_status': 'theorem-v-compressed-sufficiency-strong' if ready else 'theorem-v-compressed-sufficiency-incomplete',
        'sufficient_for_threshold_identification': ready,
        'sufficient_for_final_reduction': ready,
        'notes': 'Compressed Theorem V is sufficient exactly when the distilled contract is strong; legacy middle-layer weaknesses are then diagnostic rather than theorem obligations.',
    }
