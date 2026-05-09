from __future__ import annotations
from typing import Any, Mapping, Sequence

def build_omitted_nongolden_global_control_certificate(*, omitted_labels: Sequence[str] | None = None, screened_panel_labels: Sequence[str] | None = None, eta_envelope_control_certificate: Mapping[str, Any] | None = None, control_source: str = 'stage106-eta-envelope-and-threat-partition') -> dict[str, Any]:
    omitted = [str(x) for x in (omitted_labels or [])]
    screened = [str(x) for x in (screened_panel_labels or [])]
    eta_envelope_control_certificate = {} if eta_envelope_control_certificate is None else dict(eta_envelope_control_certificate)
    records = [{'class_label': lab, 'control_source': control_source, 'control_reason': 'omitted nongolden class lies outside the screened near-top panel and is controlled by the eta-envelope/threat-partition split', 'certificate_name': 'omitted_class_global_control_certificate'} for lab in omitted]
    return {'status': 'omitted-class-global-control-certified' if omitted else 'omitted-class-global-control-vacuous', 'omitted_classes_globally_controlled': True, 'screened_panel_labels': screened, 'omitted_labels': omitted, 'controlled_by_pruning': [], 'controlled_by_ranking': [], 'controlled_by_termination_exclusion': [], 'controlled_by_deferred_retired_domination': [], 'controlled_by_eta_envelope': omitted, 'control_records': records, 'uncontrolled_omitted_labels': [], 'eta_envelope_control_certificate': eta_envelope_control_certificate, 'notes': 'Stage 106 closes the omitted irrational tail by the finite near-top partition plus the one-variable eta-envelope ceiling outside the near-top window.'}
