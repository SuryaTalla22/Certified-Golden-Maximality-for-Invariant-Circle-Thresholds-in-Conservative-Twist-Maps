from __future__ import annotations

from kam_theorem_suite.theorem_v_error_control import (
    build_theorem_v_explicit_error_certificate,
    build_theorem_v_final_error_law_certificate,
)
from tests.test_certified_tail_modulus_control import _synthetic_ladder


def test_stage86_final_error_law_promotes_explicit_error_package() -> None:
    explicit = build_theorem_v_explicit_error_certificate(_synthetic_ladder(), min_chain_length=5).to_dict()
    cert = build_theorem_v_final_error_law_certificate(
        explicit_error_certificate=explicit,
        reference_lower_bound=0.9709,
        min_uniform_chain_length=4,
    ).to_dict()
    assert cert['theorem_status'] == 'theorem-v-final-error-law-strong'
    assert cert['final_error_law_certified'] is True
    assert cert['continuation_ready'] is True
    assert cert['transport_ready'] is True
    assert cert['error_law_monotone'] is True
    assert cert['error_law_uniform_on_family'] is True
    assert cert['error_law_preserves_gap'] is True
    assert cert['gap_preservation_margin'] is not None and cert['gap_preservation_margin'] > 0.0
    assert cert['theorem_target_interval'] is not None
    assert cert['theorem_target_width'] is not None and cert['theorem_target_width'] > 0.0


def test_stage86_final_error_law_flags_gap_failure() -> None:
    explicit = build_theorem_v_explicit_error_certificate(_synthetic_ladder(), min_chain_length=5).to_dict()
    cert = build_theorem_v_final_error_law_certificate(
        explicit_error_certificate=explicit,
        reference_lower_bound=0.9720,
        min_uniform_chain_length=4,
    ).to_dict()
    assert cert['error_law_preserves_gap'] is False
    assert cert['theorem_status'] in {
        'theorem-v-final-error-law-gap-preservation-incomplete',
        'theorem-v-final-error-law-partial',
    }
    assert 'gap-preservation-not-certified' in cert['residual_error_law_burden']
