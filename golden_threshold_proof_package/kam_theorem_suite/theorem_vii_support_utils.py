from __future__ import annotations
from typing import Any, Mapping

_PROOF_KEYS = {
    'exact_near_top_lagrange_spectrum_ranking_certificate': ('proves_exact_near_top_lagrange_spectrum_ranking',),
    'theorem_level_pruning_certificate': ('proves_theorem_level_pruning_of_dominated_regions',),
    'screened_panel_global_completeness_certificate': ('screened_panel_globally_complete',),
    'deferred_retired_domination_certificate': ('proves_deferred_or_retired_classes_are_globally_dominated',),
    'termination_search_exclusion_certificate': ('proves_termination_search_promotes_to_theorem_exclusion',),
    'omitted_class_global_control_certificate': ('omitted_classes_globally_controlled',),
    'near_top_threat_set_partition_certificate': ('partition_complete', 'proves_screened_panel_global_completeness'),
}

def certificate_proves(name: str, cert: Mapping[str, Any] | None) -> bool:
    cert = {} if cert is None else dict(cert)
    return any(bool(cert.get(k, False)) for k in _PROOF_KEYS.get(str(name), ()))

def certificate_strength(name: str, cert: Mapping[str, Any] | None) -> tuple[int, int, int]:
    cert = {} if cert is None else dict(cert)
    proves = 1 if certificate_proves(name, cert) else 0
    n = 0
    for key in ('ranking_records', 'theorem_level_complete_records', 'domination_records', 'promotion_records', 'control_records'):
        val = cert.get(key, [])
        if isinstance(val, list):
            n += len(val)
    status = str(cert.get('status', ''))
    bonus = 0 if any(x in status for x in ('frontier', 'missing', 'failed')) else 1
    return proves, n, bonus

def merge_support_certificates(base: Mapping[str, Mapping[str, Any]] | None, incoming: Mapping[str, Mapping[str, Any]] | None) -> dict[str, dict[str, Any]]:
    out = {str(k): dict(v) for k, v in ({} if base is None else dict(base)).items() if isinstance(v, Mapping)}
    for k, v in ({} if incoming is None else dict(incoming)).items():
        if not isinstance(v, Mapping):
            continue
        k = str(k); v = dict(v)
        if k not in out or certificate_strength(k, v) >= certificate_strength(k, out[k]):
            out[k] = v
    return out

def extract_stage106_support_certificates(payload: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    if payload is None:
        return {}
    payload = dict(payload)
    support = payload.get('support_certificates')
    if isinstance(support, Mapping):
        return {str(k): dict(v) for k, v in support.items() if isinstance(v, Mapping)}
    return {str(k): dict(v) for k, v in payload.items() if isinstance(v, Mapping)}
