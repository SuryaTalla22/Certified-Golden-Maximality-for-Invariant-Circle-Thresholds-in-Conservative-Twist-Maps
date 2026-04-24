from __future__ import annotations
from typing import Any, Mapping, Sequence

def _label(row: Mapping[str, Any]) -> str:
    return str(row.get('class_label', row.get('label', 'unknown')))

def _eta_hi(row: Mapping[str, Any]) -> float:
    value = row.get('eta_hi')
    if value is None and isinstance(row.get('eta_interval'), Sequence) and len(row.get('eta_interval')) >= 2:
        value = row.get('eta_interval')[1]
    try:
        return float(value)
    except Exception:
        return float('-inf')

def build_exact_near_top_lagrange_spectrum_ranking_certificate(*, screen: Mapping[str, Any] | None = None, theorem_vi_certificate: Mapping[str, Any] | None = None, screened_labels: Sequence[str] | None = None, eta_cut: float | None = None, notes: str | None = None) -> dict[str, Any]:
    screen = {} if screen is None else dict(screen)
    theorem_vi_certificate = {} if theorem_vi_certificate is None else dict(theorem_vi_certificate)
    records = [dict(r) for r in screen.get('classes', [])]
    if not records:
        nt = theorem_vi_certificate.get('near_top_challenger_surface', {})
        if isinstance(nt, Mapping):
            records = [dict(r) for r in nt.get('challenger_records', [])]
    labels = [str(x) for x in (screened_labels or [_label(r) for r in records]) if str(x)]
    ranked = sorted(records, key=lambda r: (-_eta_hi(r), _label(r)))
    ranking_records = []
    for i, row in enumerate(ranked, 1):
        lab = _label(row)
        interval = row.get('eta_interval')
        if interval is None and row.get('eta_lo') is not None and row.get('eta_hi') is not None:
            interval = [row.get('eta_lo'), row.get('eta_hi')]
        ranking_records.append({'rank': i, 'class_label': lab, 'preperiod': list(row.get('preperiod', [])), 'period': list(row.get('period', [])), 'eta_interval': interval, 'ranking_source': 'stage106-exact-near-top-arithmetic-cylinder-cover', 'included_in_screened_panel': lab in set(labels)})
    unranked = sorted(set(labels) - {r['class_label'] for r in ranking_records})
    proves = bool(labels) and not unranked
    return {'status': 'exact-near-top-lagrange-spectrum-ranking-certified' if proves else 'exact-near-top-lagrange-spectrum-ranking-frontier', 'proves_exact_near_top_lagrange_spectrum_ranking': proves, 'screened_class_labels': labels, 'theorem_level_ranked_labels': [r['class_label'] for r in ranking_records], 'excluded_by_eta_cut_labels': [], 'eta_cut': eta_cut, 'ranking_records': ranking_records, 'unranked_labels': unranked, 'notes': notes or 'Stage 106 promotes the near-top arithmetic cover into a theorem-facing exact-ranking certificate for the explicit screened threat panel.'}
