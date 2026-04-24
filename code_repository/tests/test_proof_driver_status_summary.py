from __future__ import annotations

from kam_theorem_suite import proof_driver


class _Dummy:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def test_top_level_theorem_program_status_report_surfaces_current_reduction_geometry(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-partial',
        'open_hypotheses': ['validated_operator'],
        'active_assumptions': ['stable_manifold_exists'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-obstruction-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['analytic_incompatibility_lift'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['validated_transport_theorem'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-partial',
        'open_hypotheses': ['critical_surface_identifies_threshold'],
        'active_assumptions': ['unique_true_threshold_branch_inside_transport_locked_window'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-partial',
        'statement_mode': 'one-variable',
        'open_hypotheses': ['strict_golden_top_gap'],
        'active_assumptions': ['one_variable_eta_envelope_law'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-partial',
        'open_hypotheses': ['all_near_top_challengers_dominated'],
        'active_assumptions': ['finite_screened_panel_is_globally_complete'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'top-level status baseline',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['report_kind'] == 'golden-theorem-program-status-report'
    assert report['discharge_aware'] is False
    assert report['current_reduction_geometry_available'] is True
    assert report['current_reduction_geometry_status'] == 'current-reduction-geometry-strong'
    assert abs(report['current_reduction_geometry_minimum_certified_margin'] - 2.0e-05) < 1.0e-12
    assert report['implementation_summary']['current_reduction_geometry_status'] == 'current-reduction-geometry-strong'
    assert report['implementation_summary']['overall_theorem_status'] == 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong'
    assert report['theorem_status_summary']['theorem_vi']['statement_mode'] == 'one-variable'
    assert report['theorem_status_summary']['theorem_i_ii']['open_hypothesis_count'] == 1
    assert report['theorem_status_summary']['theorem_vii']['active_assumption_count'] == 1
    assert report['current_reduction_geometry_summary']['report_kind'] == 'theorem-viii-report'
    assert report['bottleneck_summary']['kind'] == 'theorem-structural'
    assert report['bottleneck_summary']['name'] == 'Theorems I-II'
    assert abs(report['bottleneck_summary']['smallest_certified_local_margin'] - 2.0e-05) < 1.0e-12
    assert report['implementation_summary']['bottleneck_kind'] == 'theorem-structural'
    assert report['recommended_next_move_kind'] == 'discharge-structural-frontier'
    assert report['recommended_next_move_target'] == 'Theorems I-II validated renormalization operator'
    assert 'Validate the true renormalization operator' in report['recommended_next_move_action']
    assert report['implementation_summary']['recommended_next_move_target'] == 'Theorems I-II validated renormalization operator'
    assert report['subreports']['theorem_viii']['theorem_status'] == 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong'



def test_top_level_theorem_program_discharge_status_report_surfaces_current_reduction_geometry(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-partial',
        'open_hypotheses': ['validated_operator'],
        'active_assumptions': ['stable_manifold_exists'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['analytic_incompatibility_lift'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['validated_transport_theorem'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_theorem_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-theorem-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'residual_burden_summary': {'status': 'localized-compatibility-implication-upstream-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_discharge_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-discharge-conditional-partial',
        'statement_mode': 'one-variable',
        'open_hypotheses': ['strict_golden_top_gap'],
        'active_assumptions': ['one_variable_eta_envelope_law'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_discharge_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-discharge-conditional-partial',
        'open_hypotheses': ['all_near_top_challengers_dominated'],
        'active_assumptions': ['finite_screened_panel_is_globally_complete'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_discharge_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-discharge-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 1.5e-05,
        'current_reduction_geometry_top_gap_scale': 3.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97105,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97105,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 1.2e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 2.2e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 1.2e-05,
        'current_reduction_geometry_source': 'top-level status discharge',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_discharge_status_report(base_K_values=[0.3])
    impl_alias = proof_driver.build_golden_implementation_discharge_status_report(base_K_values=[0.3])
    assert report['report_kind'] == 'golden-theorem-program-discharge-status-report'
    assert report['discharge_aware'] is True
    assert report['current_reduction_geometry_available'] is True
    assert report['current_reduction_geometry_status'] == 'current-reduction-geometry-strong'
    assert abs(report['current_reduction_geometry_minimum_certified_margin'] - 1.2e-05) < 1.0e-12
    assert report['implementation_summary']['current_reduction_geometry_source'] == 'top-level status discharge'
    assert report['theorem_status_summary']['identification_seam']['theorem_status'] == 'golden-theorem-ii-to-v-identification-theorem-conditional-strong'
    assert report['current_reduction_geometry_summary']['discharge_aware'] is True
    assert report['current_reduction_geometry_summary']['report_kind'] == 'theorem-viii-discharge-report'
    assert report['bottleneck_summary']['kind'] == 'theorem-structural'
    assert report['bottleneck_summary']['name'] == 'Theorems I-II'
    assert impl_alias['current_reduction_geometry_status'] == report['current_reduction_geometry_status']
    assert impl_alias['implementation_summary']['overall_theorem_status'] == report['implementation_summary']['overall_theorem_status']
    assert impl_alias['implementation_summary']['bottleneck_name'] == report['implementation_summary']['bottleneck_name']
    assert report['recommended_next_move_kind'] == 'discharge-structural-frontier'
    assert report['recommended_next_move_target'] == 'Theorems I-II validated renormalization operator'
    assert impl_alias['implementation_summary']['recommended_next_move_target'] == 'Theorems I-II validated renormalization operator'



def test_top_level_status_report_can_identify_local_geometric_bottleneck(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-partial',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': -1.0e-06,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': -1.0e-06,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': -2.0e-06,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': -2.0e-06,
        'current_reduction_geometry_source': 'geometry blocker fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-partial',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['bottleneck_summary']['kind'] == 'local-geometric'
    assert report['bottleneck_summary']['name'] == 'Current reduction geometry'
    assert abs(report['current_smallest_certified_local_margin'] + 2.0e-06) < 1.0e-12
    assert report['implementation_summary']['bottleneck_kind'] == 'local-geometric'
    assert report['recommended_next_move_kind'] == 'tighten-local-reduction-geometry'
    assert report['recommended_next_move_target'] == 'Current reduction geometry'
    assert 'shrink the discharged witness interval' in report['recommended_next_move_action']



def test_top_level_status_report_recommends_strict_golden_top_gap_when_that_is_the_vi_frontier(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-partial',
        'statement_mode': 'one-variable',
        'open_hypotheses': ['strict_golden_top_gap'],
        'active_assumptions': ['one_variable_eta_envelope_law'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'vi-top-gap fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['bottleneck_summary']['kind'] == 'theorem-structural'
    assert report['bottleneck_summary']['name'] == 'Theorem VI'
    assert report['recommended_next_move_kind'] == 'discharge-structural-frontier'
    assert report['recommended_next_move_target'] == 'Theorem VI strict golden top gap'
    assert 'strict golden top-gap inequality' in report['recommended_next_move_action']
    assert 'strict_golden_top_gap' in report['recommended_next_move_rationale']



def test_top_level_status_report_recommends_settling_statement_mode_when_vi_mode_is_unresolved(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-partial',
        'statement_mode': 'unresolved',
        'open_hypotheses': ['statement_mode_settled'],
        'active_assumptions': ['envelope_statement_mode_unresolved'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'vi-mode fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['bottleneck_summary']['kind'] == 'theorem-structural'
    assert report['bottleneck_summary']['name'] == 'Theorem VI'
    assert report['recommended_next_move_target'] == 'Theorem VI statement mode'
    assert 'Settle the final Theorem VI statement mode' in report['recommended_next_move_action']
    assert 'statement-mode structure' in report['recommended_next_move_rationale']


def test_top_level_status_report_preserves_vi_residual_global_burden_summary(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'statement_mode': 'unresolved',
        'open_hypotheses': [],
        'active_assumptions': ['one_variable_eta_envelope_law'],
        'residual_burden_summary': {'status': 'global-theorem-burden-only'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'vi-residual-burden fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['theorem_status_summary']['theorem_vi']['residual_burden_status'] == 'global-theorem-burden-only'


def test_top_level_status_report_preserves_vi_statement_mode_lock_status(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {'theorem_status': 'golden-theorem-v-transport-lift-front-complete', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-front-complete',
        'statement_mode': 'one-variable',
        'statement_mode_diagnostics': {'mode_lock_status': 'one-variable-supported'},
        'open_hypotheses': [],
        'active_assumptions': ['one_variable_eta_envelope_law'],
        'residual_burden_summary': {'status': 'global-theorem-burden-only'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong', 'open_hypotheses': [], 'active_assumptions': []})
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'vi-mode-lock fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['theorem_status_summary']['theorem_vi']['statement_mode_lock_status'] == 'one-variable-supported'


def test_top_level_status_report_recommends_theorem_vii_global_completeness_once_near_top_panel_is_closed(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['finite_screened_panel_is_globally_complete'],
        'residual_burden_summary': {'status': 'global-screened-panel-completeness-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'theorem-vii-global-frontier fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_kind'] == 'discharge-structural-frontier'
    assert report['recommended_next_move_target'] == 'Theorem VII global screened-panel completeness'
    assert 'global screened-panel completeness' in report['recommended_next_move_action'].lower()



def test_top_level_status_report_uses_identification_residual_burden_to_recommend_critical_surface_step(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-threshold-identification-transport-discharge-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': ['family_chart_crossing_identifies_true_critical_parameter'],
        'residual_burden_summary': {'status': 'critical-surface-threshold-promotion-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'identification-residual fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] == 'Identification seam critical-surface/threshold promotion theorem'
    assert 'critical-surface discharge package' in report['recommended_next_move_action']


def test_top_level_status_report_recommends_workstream_critical_surface_threshold_identification(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [
            'golden_stable_manifold_is_true_critical_surface',
            'family_chart_crossing_identifies_true_critical_parameter',
        ],
        'residual_burden_summary': {'status': 'critical-surface-threshold-promotion-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'workstream critical-surface frontier fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] == 'Theorems I-II critical-surface/threshold promotion theorem'
    assert report['recommended_next_move_kind'] == 'discharge-structural-frontier'



def test_top_level_status_report_recommends_promotion_theorem_when_workstream_frontier_is_promoted(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['theorem_grade_banach_manifold_universality_class', 'validated_true_renormalization_fixed_point_package'],
        'residual_burden_summary': {'status': 'critical-surface-threshold-promotion-theorem-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'promotion theorem fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] == 'Theorems I-II critical-surface/threshold promotion theorem'
    assert 'theorem-grade promotion theorem' in report['recommended_next_move_action']


def test_top_level_status_report_recommends_omitted_class_global_control_when_that_is_the_vii_frontier(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['omitted_nongolden_irrationals_outside_screened_panel_controlled'],
        'residual_burden_summary': {'status': 'omitted-class-global-control-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'theorem-vii-omitted-control fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] == 'Theorem VII omitted-class global control'
    assert 'omitted-class global-control theorem' in report['recommended_next_move_action']



def test_top_level_status_report_moves_off_theorem_vii_once_global_exhaustion_is_discharged(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-partial',
        'open_hypotheses': ['validated_operator'],
        'active_assumptions': ['stable_manifold_exists'],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'residual_burden_summary': {'status': 'fully-discharged'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'post-vii fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] == 'Theorems I-II validated renormalization operator'


def test_top_level_status_report_recommends_vii_global_support_when_that_is_the_frontier(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [
            'exact_near_top_lagrange_spectrum_ranking',
            'theorem_level_pruning_of_dominated_regions',
        ],
        'residual_burden_summary': {'status': 'global-exhaustion-support-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'theorem-vii-support fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] == 'Theorem VII global ranking / pruning support'
    assert 'ranking, pruning' in report['recommended_next_move_action'].lower()


def test_top_level_status_report_recommends_validated_renormalization_package_theorem_when_that_is_the_workstream_frontier(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['theorem_grade_banach_manifold_universality_class', 'golden_stable_manifold_is_true_critical_surface'],
        'residual_burden_summary': {'status': 'validated-renormalization-package-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'residual_burden_summary': {'status': 'fully-discharged'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'validated-package fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] == 'Theorems I-II validated renormalization package theorem'
    assert 'validated renormalization package' in report['recommended_next_move_action']

def test_top_level_status_report_recommends_validated_critical_surface_theorem_when_that_is_the_workstream_frontier(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['theorem_grade_banach_manifold_universality_class'],
        'residual_burden_summary': {'status': 'validated-critical-surface-theorem-promotion-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'validated-critical-surface-theorem fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] == 'Theorems I-II validated critical-surface theorem'


def test_top_level_status_report_recommends_validated_universality_class_theorem_when_that_is_the_workstream_frontier(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': ['theorem_grade_banach_manifold_universality_class'],
        'residual_burden_summary': {'status': 'validated-universality-class-theorem-promotion-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-front-complete',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-lift-conditional-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'universality frontier fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })
    report = proof_driver.build_golden_theorem_program_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] == 'Theorems I-II validated universality-class theorem'
    assert report['bottleneck_summary']['name'] == 'Theorems I-II'

def test_discharge_status_report_shifts_off_identification_seam_when_final_identification_theorem_is_discharged(monkeypatch) -> None:
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_i_ii_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-i-ii-workstream-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
        'residual_burden_summary': {'status': 'critical-surface-threshold-promotion-theorem-discharged'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_iv_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-iv-analytic-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_v_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-v-transport-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_theorem_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-ii-to-v-identification-theorem-discharged',
        'open_hypotheses': [],
        'active_assumptions': [],
        'residual_burden_summary': {'status': 'localized-compatibility-implication-discharged'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vi_discharge_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vi-envelope-discharge-lift-front-complete',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': ['one_variable_eta_envelope_law'],
        'residual_burden_summary': {'status': 'global-envelope-law-frontier'},
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_vii_discharge_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong',
        'open_hypotheses': [],
        'active_assumptions': [],
    })
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_viii_discharge_report', lambda **kwargs: {
        'theorem_status': 'golden-theorem-viii-reduction-discharge-lift-conditional-one-variable-strong',
        'statement_mode': 'one-variable',
        'open_hypotheses': [],
        'active_assumptions': [],
        'current_reduction_geometry_witness_vs_overlap_margin': 2.0e-05,
        'current_reduction_geometry_top_gap_scale': 4.0e-05,
        'current_reduction_geometry_challenger_upper_bound': 0.97106,
        'current_reduction_geometry_exhaustion_upper_bound': 0.97106,
        'current_reduction_geometry_witness_width_vs_top_gap_margin': 2.0e-05,
        'current_reduction_geometry_witness_lower_vs_challenger_upper_margin': 3.0e-05,
        'current_reduction_geometry_pending_count': 0,
        'current_reduction_geometry_min_margin': 2.0e-05,
        'current_reduction_geometry_source': 'final-identification-theorem fixture',
        'current_reduction_geometry_status': 'current-reduction-geometry-strong',
    })

    report = proof_driver.build_golden_theorem_program_discharge_status_report(base_K_values=[0.3])
    assert report['recommended_next_move_target'] != 'Identification seam localized compatibility implication'
    assert report['recommended_next_move_target'] in {'Theorem VI envelope law', 'Theorem VI strict golden top gap', 'Theorem VI statement mode'}
