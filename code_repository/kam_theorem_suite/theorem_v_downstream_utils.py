from __future__ import annotations

"""Helpers for downstream Theorem-V consumption.

These utilities let later theorem layers consume either the legacy raw Theorem-V
transport shell or the newer compressed downstream wrapper without having to
re-encode the same fallback logic at each consumer.
"""

from typing import Any, Mapping, Sequence


def _as_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "to_dict"):
        return dict(obj.to_dict())
    return dict(obj)


def _candidate_certificates(theorem_v_certificate: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if theorem_v_certificate is None:
        return []
    root = _as_dict(theorem_v_certificate)
    seen: set[int] = set()
    ordered: list[dict[str, Any]] = []

    def _push(obj: Any) -> None:
        if not isinstance(obj, Mapping):
            return
        d = _as_dict(obj)
        ident = id(d)
        if ident in seen:
            return
        seen.add(ident)
        ordered.append(d)

    _push(root)
    for key in ('downstream_certificate', 'compressed_certificate', 'certificate', 'theorem_v_shell', 'compressed_contract'):
        value = root.get(key)
        if isinstance(value, Mapping):
            _push(value)
    return ordered


def unwrap_theorem_v_shell(theorem_v_certificate: Mapping[str, Any] | None) -> dict[str, Any]:
    if theorem_v_certificate is None:
        return {}
    for cert in _candidate_certificates(theorem_v_certificate):
        shell = cert.get('theorem_v_shell')
        if isinstance(shell, Mapping):
            return dict(shell)
    cert = _as_dict(theorem_v_certificate)
    return cert


def extract_theorem_v_compressed_contract(theorem_v_certificate: Mapping[str, Any] | None) -> dict[str, Any]:
    for cert in _candidate_certificates(theorem_v_certificate):
        compressed = cert.get('compressed_contract')
        if isinstance(compressed, Mapping):
            return dict(compressed)
        status = str(cert.get('theorem_status', ''))
        if status.startswith('golden-theorem-v-compressed-contract-'):
            return cert
    return {}


def extract_theorem_v_status(theorem_v_certificate: Mapping[str, Any] | None) -> str | None:
    for cert in _candidate_certificates(theorem_v_certificate):
        status = cert.get('theorem_v_final_status')
        if status is not None:
            return str(status)
        status = cert.get('theorem_status')
        if status is not None:
            return str(status)
    return None


def theorem_v_is_downstream_final(theorem_v_certificate: Mapping[str, Any] | None) -> bool:
    if theorem_v_certificate is None:
        return False
    for cert in _candidate_certificates(theorem_v_certificate):
        status = str(cert.get('theorem_status', ''))
        if status.startswith('golden-theorem-v-final-strong'):
            return True
    compressed = extract_theorem_v_compressed_contract(theorem_v_certificate)
    return str(compressed.get('theorem_status', '')) == 'golden-theorem-v-compressed-contract-strong'


def _interval_from_pair(lo: Any, hi: Any) -> list[float] | None:
    if lo is None or hi is None:
        return None
    lo = float(lo); hi = float(hi)
    if hi < lo:
        return None
    return [lo, hi]


def extract_theorem_v_target_interval(theorem_v_certificate: Mapping[str, Any] | None) -> list[float] | None:
    for cert in _candidate_certificates(theorem_v_certificate):
        direct = cert.get('theorem_target_interval')
        if isinstance(direct, Sequence) and len(direct) == 2 and direct[0] is not None and direct[1] is not None:
            lo = float(direct[0]); hi = float(direct[1])
            if hi >= lo:
                return [lo, hi]
        final_error = cert.get('final_error_law')
        if isinstance(final_error, Mapping):
            direct = final_error.get('theorem_target_interval')
            if isinstance(direct, Sequence) and len(direct) == 2 and direct[0] is not None and direct[1] is not None:
                lo = float(direct[0]); hi = float(direct[1])
                if hi >= lo:
                    return [lo, hi]
        final_bridge = cert.get('final_transport_bridge')
        if isinstance(final_bridge, Mapping):
            direct = final_bridge.get('theorem_target_interval')
            if isinstance(direct, Sequence) and len(direct) == 2 and direct[0] is not None and direct[1] is not None:
                lo = float(direct[0]); hi = float(direct[1])
                if hi >= lo:
                    return [lo, hi]
        front = cert.get('convergence_front')
        if isinstance(front, Mapping):
            final_error = dict(front.get('theorem_v_final_error_control', {}))
            direct = final_error.get('theorem_target_interval')
            if isinstance(direct, Sequence) and len(direct) == 2 and direct[0] is not None and direct[1] is not None:
                lo = float(direct[0]); hi = float(direct[1])
                if hi >= lo:
                    return [lo, hi]
            explicit = dict(front.get('theorem_v_explicit_error_control', {}))
            interval = _interval_from_pair(explicit.get('compatible_limit_interval_lo'), explicit.get('compatible_limit_interval_hi'))
            if interval is not None:
                return interval
            relation = dict(front.get('relation', {}))
            interval = _interval_from_pair(relation.get('compatible_upper_lo'), relation.get('compatible_upper_hi'))
            if interval is not None:
                return interval
    compressed = extract_theorem_v_compressed_contract(theorem_v_certificate)
    target = dict(compressed.get('target_interval', {}))
    interval = _interval_from_pair(target.get('lo'), target.get('hi'))
    if interval is not None:
        return interval
    return None


def extract_theorem_v_gap_preservation_certified(theorem_v_certificate: Mapping[str, Any] | None) -> bool | None:
    for cert in _candidate_certificates(theorem_v_certificate):
        final_error = cert.get('final_error_law')
        if isinstance(final_error, Mapping) and final_error.get('error_law_preserves_gap') is not None:
            return bool(final_error.get('error_law_preserves_gap'))
        front = cert.get('convergence_front')
        if isinstance(front, Mapping):
            final_error = dict(front.get('theorem_v_final_error_control', {}))
            if final_error.get('error_law_preserves_gap') is not None:
                return bool(final_error.get('error_law_preserves_gap'))
    compressed = extract_theorem_v_compressed_contract(theorem_v_certificate)
    uniform = dict(compressed.get('uniform_majorant', {}))
    if uniform.get('preserves_golden_gap') is not None:
        return bool(uniform.get('preserves_golden_gap'))
    return None


def extract_theorem_v_gap_preservation_margin(theorem_v_certificate: Mapping[str, Any] | None) -> float | None:
    for cert in _candidate_certificates(theorem_v_certificate):
        margin = cert.get('gap_preservation_margin')
        if margin is not None:
            return float(margin)
        final_error = cert.get('final_error_law')
        if isinstance(final_error, Mapping) and final_error.get('gap_preservation_margin') is not None:
            return float(final_error.get('gap_preservation_margin'))
    return None
