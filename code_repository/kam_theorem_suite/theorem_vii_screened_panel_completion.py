from __future__ import annotations
from typing import Any, Mapping, Sequence

def _label(row: Mapping[str, Any]) -> str:
    return str(row.get('class_label', row.get('label', 'unknown')))

def build_screened_panel_global_completeness_witness(*, screen: Mapping[str, Any] | None = None, records: Sequence[Mapping[str, Any]] | None = None, arithmetic_ranking_certificate: Mapping[str, Any] | None = None, pruning_region_certificate: Mapping[str, Any] | None = None) -> dict[str, Any]:
    screen = {} if screen is None else dict(screen)
    records = [dict(r) for r in (records if records is not None else screen.get('classes', []))]
    labels = [_label(r) for r in records]
    overlapping = [_label(r) for r in records if str(r.get('pruning_status', '')) == 'overlapping']
    undecided = [_label(r) for r in records if str(r.get('pruning_status', '')) == 'undecided']
    complete_records = [{'class_label': _label(r), 'completion_source': 'stage106-screened-panel-finite-threat-cover', 'completion_reason': 'screened class belongs to the exact near-top finite threat panel and is consumed by the Stage 106 partition certificate', 'certificate_name': 'screened_panel_global_completeness_certificate'} for r in records]
    ranking_ready = bool((arithmetic_ranking_certificate or {}).get('proves_exact_near_top_lagrange_spectrum_ranking', False))
    pruning_ready = bool((pruning_region_certificate or {}).get('proves_theorem_level_pruning_of_dominated_regions', False))
    complete = bool(labels) and not overlapping and not undecided and ranking_ready and pruning_ready and len(complete_records) == len(labels)
    return {'status': 'screened-panel-global-completeness-certified' if complete else 'screened-panel-global-completeness-frontier', 'screened_panel_globally_complete': complete, 'screened_panel_labels': labels, 'theorem_level_complete_labels': labels if complete else [], 'theorem_level_complete_records': complete_records, 'panel_has_no_overlaps': not overlapping, 'panel_has_no_undecided': not undecided, 'overlapping_labels': overlapping, 'undecided_labels': undecided, 'missing_completion_labels': [] if complete else labels, 'notes': 'Stage 106 treats the explicitly screened near-top panel as the finite theorem-facing threat panel once exact ranking and pruning support are available.'}
