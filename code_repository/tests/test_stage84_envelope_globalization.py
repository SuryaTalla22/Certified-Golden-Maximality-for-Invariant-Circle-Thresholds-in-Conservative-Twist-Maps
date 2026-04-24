from __future__ import annotations

from kam_theorem_suite.envelope import (
    build_eta_global_envelope_certificate,
    build_eta_mode_obstruction_certificate,
    build_eta_mode_reduction_certificate,
    build_strict_golden_top_gap_theorem_candidate,
)


def test_stage84_two_variable_obstruction_promotes_corrected_theorem_mode() -> None:
    statement_mode_certificate = {
        'candidate_mode': 'two-variable',
        'mode_lock_status': 'two-variable-supported',
        'status': 'statement-mode-certificate-two-variable-supported',
        'evidence_margin': 3.0e-3,
    }
    obstruction = build_eta_mode_obstruction_certificate(statement_mode_certificate)
    reduction = build_eta_mode_reduction_certificate(
        statement_mode_certificate,
        mode_obstruction_certificate=obstruction,
        current_local_top_gap_status='current-local-top-gap-strong',
    )
    assert obstruction['one_variable_obstruction_certified'] is True
    assert reduction['theorem_mode'] == 'two-variable'
    assert reduction['reduction_certified'] is True


def test_stage84_one_variable_support_stays_diagnostic_without_reduction() -> None:
    statement_mode_certificate = {
        'candidate_mode': 'one-variable',
        'mode_lock_status': 'one-variable-supported',
        'status': 'statement-mode-certificate-one-variable-supported',
        'evidence_margin': 2.0e-3,
    }
    reduction = build_eta_mode_reduction_certificate(
        statement_mode_certificate,
        current_local_top_gap_status='current-local-top-gap-strong',
    )
    assert reduction['theorem_mode'] == 'unresolved'
    assert reduction['theorem_mode_status'] == 'one-variable-diagnostic-support-only'
    assert reduction['reduction_certified'] is False


def test_stage84_global_envelope_candidate_yields_global_strict_top_gap_certificate() -> None:
    reduction = {
        'theorem_mode': 'two-variable',
        'theorem_mode_status': 'two-variable-reduction-certified-from-obstruction',
        'reduction_certified': True,
    }
    ceiling = {
        'global_ceiling_status': 'global-ceiling-strong',
        'tail_control_available': True,
    }
    envelope = build_eta_global_envelope_certificate(
        golden_lower_witness=0.97163,
        nongolden_global_upper_ceiling=0.97110,
        mode_reduction_certificate=reduction,
        ceiling_decomposition=ceiling,
        theorem_mode='two-variable',
    )
    candidate = build_strict_golden_top_gap_theorem_candidate(envelope)
    assert envelope['theorem_status'] == 'global-envelope-theorem-two-variable-certified'
    assert candidate['global_strict_top_gap_certified'] is True
    assert candidate['global_strict_top_gap_status'] == 'strict-golden-top-gap-theorem-two-variable-certified'
