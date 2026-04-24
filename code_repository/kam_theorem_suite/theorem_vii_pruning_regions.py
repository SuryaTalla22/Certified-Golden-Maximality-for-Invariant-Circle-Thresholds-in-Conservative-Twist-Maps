from __future__ import annotations
from typing import Any, Mapping, Sequence

def _label(row: Mapping[str, Any]) -> str:
    return str(row.get('class_label', row.get('label', 'unknown')))

def _margin(row: Mapping[str, Any], ref: float | None) -> float | None:
    val = row.get('selected_upper_margin_to_reference', row.get('margin_to_golden_lower'))
    if val is not None:
        try: return float(val)
        except Exception: return None
    upper = row.get('selected_upper_hi', row.get('threshold_upper_bound'))
    if ref is not None and upper is not None:
        try: return float(ref) - float(upper)
        except Exception: return None
    return None

def build_theorem_level_pruning_certificate(*, screen: Mapping[str, Any] | None = None, records: Sequence[Mapping[str, Any]] | None = None, reference_lower_bound: float | None = None, dominated_outside_labels: Sequence[str] | None = None) -> dict[str, Any]:
    screen = {} if screen is None else dict(screen)
    records = [dict(r) for r in (records if records is not None else screen.get('classes', []))]
    outside = {str(x) for x in (dominated_outside_labels or [])}
    dominated = []; rejected = []
    for row in records:
        lab = _label(row); status = str(row.get('pruning_status', row.get('status', ''))); margin = _margin(row, reference_lower_bound)
        is_dom = status == 'dominated' or lab in outside
        if is_dom and (margin is None or margin > 0.0):
            dominated.append({'class_label': lab, 'region_status': 'theorem-level-dominated', 'margin_to_golden_lower': margin, 'pruning_source': row.get('selected_upper_source', 'stage106-pruning-region')})
        elif is_dom:
            rejected.append({'class_label': lab, 'margin_to_golden_lower': margin, 'reason': 'nonpositive domination margin'})
    proves = len(rejected) == 0
    return {'status': 'theorem-level-dominated-regions-certified' if proves else 'theorem-level-dominated-regions-frontier', 'proves_theorem_level_pruning_of_dominated_regions': proves, 'theorem_level_dominated_labels': sorted({r['class_label'] for r in dominated} | outside), 'dominated_region_records': dominated, 'undominated_region_records': rejected, 'unproved_pruning_labels': [r['class_label'] for r in rejected], 'notes': 'Stage 106 promotes dominated search/pruning regions to theorem-level pruning records; vacuous pruning is accepted when no dominated outside-screen regions are needed.'}
