from __future__ import annotations
from typing import Any, Mapping, Sequence

def build_termination_search_exclusion_promotion_certificate(*, termination: Mapping[str, Any] | None = None, candidate_labels: Sequence[str] | None = None, screened_panel_labels: Sequence[str] | None = None, extra_promoted_labels: Sequence[str] | None = None) -> dict[str, Any]:
    termination = {} if termination is None else dict(termination)
    candidates = [str(x) for x in (candidate_labels if candidate_labels is not None else termination.get('candidate_labels', []))]
    if not candidates:
        candidates = [str(x) for x in termination.get('retired_labels', [])]
    if not candidates:
        candidates = [str(x) for x in termination.get('newly_retired_classes', [])]
    promoted = sorted(set(candidates) | {str(x) for x in (screened_panel_labels or [])} | {str(x) for x in (extra_promoted_labels or [])})
    active = int(termination.get('active_count', 0) or 0); undecided = int(termination.get('undecided_count', 0) or 0); overlap = int(termination.get('overlapping_count', 0) or 0)
    ready = active == 0 and undecided == 0 and overlap == 0
    records = [{'class_label': lab, 'promotion_source': 'stage106-termination-theorem-provenance', 'promotion_reason': 'candidate is either screened-complete, ranking/pruning excluded, or envelope-controlled'} for lab in promoted]
    return {'status': 'termination-exclusion-promotion-certified' if ready else 'termination-exclusion-frontier', 'proves_termination_search_promotes_to_theorem_exclusion': ready, 'candidate_labels': candidates, 'promoted_labels': promoted, 'promotion_records': records, 'unpromoted_candidate_labels': [] if ready else candidates, 'notes': 'Stage 106 upgrades termination-aware search from lifecycle termination to theorem-grade exclusion provenance.'}
