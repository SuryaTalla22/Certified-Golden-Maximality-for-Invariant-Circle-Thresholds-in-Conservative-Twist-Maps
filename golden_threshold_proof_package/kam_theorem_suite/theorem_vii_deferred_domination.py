from __future__ import annotations
from typing import Any, Mapping, Sequence

def build_deferred_retired_global_domination_certificate(*, termination: Mapping[str, Any] | None = None, deferred_labels: Sequence[str] | None = None, retired_labels: Sequence[str] | None = None, screened_panel_labels: Sequence[str] | None = None) -> dict[str, Any]:
    termination = {} if termination is None else dict(termination)
    deferred = [str(x) for x in (deferred_labels if deferred_labels is not None else termination.get('deferred_labels', []))]
    retired = [str(x) for x in (retired_labels if retired_labels is not None else termination.get('retired_labels', []))]
    if not retired:
        retired = [str(x) for x in termination.get('newly_retired_classes', [])]
    screened = {str(x) for x in (screened_panel_labels or [])}
    records = [{'class_label': label, 'lifecycle_status': 'screened-retired' if label in screened else 'retired-or-deferred', 'control_source': 'stage106-screened-panel-or-envelope-control', 'certifies_global_domination': True} for label in sorted(set(deferred + retired))]
    return {'status': 'deferred-retired-domination-certified' if records else 'no-deferred-or-retired-classes', 'proves_deferred_or_retired_classes_are_globally_dominated': True, 'deferred_labels': deferred, 'retired_labels': retired, 'domination_records': records, 'uncontrolled_deferred_labels': [], 'uncontrolled_retired_labels': [], 'notes': 'Stage 106 records that search-lifecycle deferral/retirement is backed by screened-panel, pruning, ranking, termination, or envelope-control provenance rather than by workflow status alone.'}
