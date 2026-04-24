from __future__ import annotations

import json
from pathlib import Path

from kam_theorem_suite.theorem_v_upper_seed import (
    build_golden_supercritical_obstruction_certificate_from_theorem_iv,
)


def _real_theorem_iv_artifact() -> dict:
    artifact = Path(__file__).resolve().parents[1] / 'artifacts' / 'final_discharge' / 'stage_cache' / 'theorem_iv.json'
    with artifact.open() as handle:
        return json.load(handle)


def test_theorem_v_upper_seed_reuses_real_theorem_iv_cache() -> None:
    cert = build_golden_supercritical_obstruction_certificate_from_theorem_iv(
        _real_theorem_iv_artifact()
    ).to_dict()

    assert cert['selected_upper_source'] == 'theorem-iv-final-object'
    assert cert['theorem_status'] in {
        'golden-supercritical-obstruction-strong',
        'golden-supercritical-obstruction-moderate',
    }

    approximants = cert['ladder']['approximants']
    qs = [int(a['q']) for a in approximants]
    assert len(approximants) >= 6
    assert 144 in qs
    assert 233 in qs
    assert cert['successful_crossing_count'] >= 4
    assert cert['successful_band_count'] >= 4
    assert cert['asymptotic_audit']['status']
