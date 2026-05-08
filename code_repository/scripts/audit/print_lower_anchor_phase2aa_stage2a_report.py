#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _thin_record(rec: dict, max_models: int = 6) -> dict:
    models = sorted(
        rec.get('models', []) or [],
        key=lambda m: m.get('radii_margin_profiled') if m.get('radii_margin_profiled') is not None else -1e99,
        reverse=True,
    )[:max_models]
    return {
        'index': rec.get('index'),
        'K_lo': rec.get('K_lo'),
        'K_hi': rec.get('K_hi'),
        'q': rec.get('q'),
        'old_radii_margin': rec.get('old_radii_margin'),
        'old_tail_response_bound': rec.get('old_tail_response_bound'),
        'old_nonlinear_guard': rec.get('old_nonlinear_guard'),
        'old_ledger_replay_passed': rec.get('old_ledger_replay_passed'),
        'curvature_stats': rec.get('curvature_stats'),
        'required_reductions': rec.get('required_reductions'),
        'best_model_name': rec.get('best_model_name'),
        'best_profiled_margin': rec.get('best_profiled_margin'),
        'best_profiled_classification': rec.get('best_profiled_classification'),
        'recommended_next_action': rec.get('recommended_next_action'),
        'top_models': [{
            'model_name': m.get('model_name'),
            'model_kind': m.get('model_kind'),
            'guard_factor': m.get('nonlinear_guard_factor'),
            'tail_factor': m.get('tail_response_factor'),
            'profiled_margin': m.get('radii_margin_profiled'),
            'margin_improvement': m.get('margin_improvement'),
            'would_close_tail_guard': m.get('would_close_tail_guard_inequality'),
            'would_close_with_q_gate': m.get('would_close_with_q_gate'),
            'classification': m.get('classification'),
        } for m in models],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description='Print compact Phase 2AA Stage 2A profiled-guard report.')
    ap.add_argument('--audit', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--top-n', type=int, default=10)
    args = ap.parse_args()
    audit_path = Path(args.audit)
    obj = json.loads(audit_path.read_text())
    records = sorted(
        obj.get('records', []) or [],
        key=lambda r: r.get('best_profiled_margin') if r.get('best_profiled_margin') is not None else -1e99,
        reverse=True,
    )
    compact = {
        'source': str(audit_path),
        'status': obj.get('status'),
        'diagnostic_only': obj.get('diagnostic_only'),
        'theorem_facing': obj.get('theorem_facing'),
        'promotion_allowed': obj.get('promotion_allowed'),
        'record_count': obj.get('record_count'),
        'old_ledger_replay_passed_count': obj.get('old_ledger_replay_passed_count'),
        'q_safe_count': obj.get('q_safe_count'),
        'q_blocked_count': obj.get('q_blocked_count'),
        'records_with_any_q_gated_diagnostic_closure': obj.get('records_with_any_q_gated_diagnostic_closure'),
        'records_with_any_tail_guard_diagnostic_closure_before_q_gate': obj.get('records_with_any_tail_guard_diagnostic_closure_before_q_gate'),
        'recommended_next_action_counts': obj.get('recommended_next_action_counts'),
        'model_q_gated_close_counts': obj.get('model_q_gated_close_counts'),
        'model_tail_guard_close_counts': obj.get('model_tail_guard_close_counts'),
        'model_mean_margin_improvements': obj.get('model_mean_margin_improvements'),
        'interpretation': obj.get('interpretation'),
        'top_records_by_profiled_margin': [_thin_record(r) for r in records[:int(args.top_n)]],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(compact, indent=2, sort_keys=True) + '\n')
    print(json.dumps(compact, indent=2, sort_keys=True))
    print(f"WROTE: {out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
