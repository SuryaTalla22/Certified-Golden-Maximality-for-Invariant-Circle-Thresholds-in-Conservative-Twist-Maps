from __future__ import annotations

import json
from pathlib import Path

from kam_theorem_suite.audit.lower_anchor_phase2aa_profiled_guard import analyze_candidate, run_profiled_guard_audit


def _candidate(tmp_path: Path, *, q: float = 0.9, margin: float = -1.0e-8) -> Path:
    n = 64
    u = [0.01 * __import__('math').sin(2.0 * __import__('math').pi * i / n) for i in range(n)]
    radius = 1.0e-6
    residual = 1.0e-8
    linear_z = 0.25
    tail_response = 3.5e-7
    guard = 1.2e-7
    tail_T = tail_response + guard
    recomputed = radius - (residual + linear_z * radius + tail_T)
    obj = {
        'raw_validation_payload': {
            'K_interval': [0.1, 0.2],
            'scalar_ledger_recompute': {
                'available': True,
                'radius_r': radius,
                'residual_Y': residual,
                'linear_Z': linear_z,
                'finite_contraction_q': q,
                'tail_response_bound': tail_response,
                'nonlinear_guard': guard,
                'tail_T': tail_T,
                'allowable_tail_max': radius - residual - linear_z * radius,
                'radii_margin': recomputed if margin is None else margin,
                'recomputed_margin': recomputed if margin is None else margin,
            },
            'source_validation': {'available': True, 'u': u},
            'residual': {'available': True, 'samples': [0.0] * (4 * n)},
            'source_fourier_coefficients': {'real': [1.0] + [0.0]*(n-1), 'imag': [0.0]*n},
            'tail_profile': {'modewise_tail_ledger': {'modewise_tail_response': tail_response, 'top_contributors': []}},
        }
    }
    p = tmp_path / 'phase2x_demo_p0005_pinpoint_modewise_tail_candidate.json'
    p.write_text(json.dumps(obj))
    return p


def test_analyze_candidate_produces_diagnostic_models(tmp_path: Path) -> None:
    p = _candidate(tmp_path, q=0.9, margin=-1.0e-8)
    obj = json.loads(p.read_text())
    rec = analyze_candidate(obj, candidate_path=p)
    d = rec.to_dict()
    assert d['diagnostic_only'] is True
    assert d['theorem_facing'] is False
    assert len(d['models']) >= 4
    assert d['old_ledger_replay_passed'] is True
    assert d['curvature_stats']['available'] == 1.0


def test_run_profiled_guard_audit_from_summary(tmp_path: Path) -> None:
    p = _candidate(tmp_path, q=0.9, margin=-1.0e-8)
    summary = tmp_path / 'summary.json'
    summary.write_text(json.dumps({'best_failed_rows': [{'path': str(p)}]}))
    rep = run_profiled_guard_audit(summary_path=summary, root='.')
    assert rep['record_count'] == 1
    assert rep['old_ledger_replay_passed_count'] == 1
    assert rep['diagnostic_only'] is True
    assert rep['promotion_allowed'] is False
