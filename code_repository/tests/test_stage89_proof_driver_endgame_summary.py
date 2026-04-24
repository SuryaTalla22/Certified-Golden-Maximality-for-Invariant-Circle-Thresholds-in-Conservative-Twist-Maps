from __future__ import annotations

from kam_theorem_suite import proof_driver


def test_stage89_proof_driver_endgame_summary(monkeypatch) -> None:
    theorem_viii = {
        'theorem_status': 'golden-universal-theorem-workstream-caveat-only',
        'statement_mode': 'one-variable',
        'current_reduction_geometry_summary': {
            'available': True,
            'status': 'current-reduction-geometry-strong',
            'minimum_certified_margin': 0.005,
            'source': 'test',
        },
        'final_certificate_ready_for_code_path': True,
        'final_certificate_ready_for_paper': False,
        'remaining_true_mathematical_burden': [],
        'remaining_workstream_paper_grade_burden': ['workstream-proxy-caveat'],
        'remaining_exhaustion_paper_grade_burden': [],
    }

    def _row(name: str, status: str):
        return {'theorem_name': name, 'theorem_status': status, 'statement_mode': 'one-variable', 'open_hypotheses': [], 'active_assumptions': []}

    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: _row('Theorems I-II', 'golden-theorem-i-ii-workstream-lift-conditional-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iii_report', lambda **kwargs: _row('Theorem III', 'golden-theorem-iii-final-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_lower_neighborhood_report', lambda **kwargs: {'theorem_status': 'golden-lower-neighborhood-stability-strong'})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: _row('Theorem IV', 'golden-theorem-iv-final-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: _row('Theorem V', 'golden-theorem-v-final-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: _row('Identification shell', 'golden-identification-shell-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_discharge_report', lambda **kwargs: _row('Identification discharge', 'golden-identification-discharge-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_transport_discharge_report', lambda **kwargs: _row('Identification transport discharge', 'golden-identification-transport-discharge-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_theorem_report', lambda **kwargs: _row('Identification seam', 'golden-identification-front-complete'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: _row('Theorem VI base', 'golden-theorem-vi-envelope-lift-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_discharge_report', lambda **kwargs: _row('Theorem VI', 'golden-theorem-vi-envelope-discharge-lift-global-one-variable-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: _row('Theorem VII base', 'golden-theorem-vii-exhaustion-lift-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_discharge_report', lambda **kwargs: _row('Theorem VII', 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong'))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-viii-reduction-lift-strong'})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_discharge_report', lambda **kwargs: theorem_viii)

    report = proof_driver.build_golden_theorem_program_discharge_status_report(base_K_values=[0.2, 0.25])
    summary = report['implementation_summary']
    assert summary['theorem_viii_final_status'] == 'golden-universal-theorem-workstream-caveat-only'
    assert summary['final_universal_theorem_ready_for_code_path'] is True
    assert summary['final_universal_theorem_ready_for_paper'] is False
    assert summary['true_mathematical_burden_remaining'] == []
    assert summary['workstream_residual_caveat'] == ['workstream-proxy-caveat']
