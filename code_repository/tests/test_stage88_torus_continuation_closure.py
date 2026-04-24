from __future__ import annotations

import math

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.torus_continuation import (
    build_torus_continuation_closure_certificate,
    continue_invariant_circle_validations,
)

GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


def test_stage88_torus_continuation_closure_smoke() -> None:
    report = continue_invariant_circle_validations(GOLDEN, [0.2, 0.25], HarmonicFamily(), N=32)
    cert = build_torus_continuation_closure_certificate(report).to_dict()
    assert cert['continuation_closure_status'] in {
        'torus-continuation-closure-strong',
        'torus-continuation-closure-partial',
    }
    assert cert['continuation_interval'] is not None
