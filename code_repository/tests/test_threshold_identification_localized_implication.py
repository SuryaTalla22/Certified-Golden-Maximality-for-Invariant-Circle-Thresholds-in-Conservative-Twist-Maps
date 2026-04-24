from __future__ import annotations

from kam_theorem_suite import proof_driver
from kam_theorem_suite import threshold_identification_localized_implication as mod


class DummyCert:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return dict(self._data)


def _transport_discharge(*, active=None, residual_status='transport-locked-identification-ready', overlap=None, locked=None, branch=None, witness=None, theorem_status='golden-threshold-identification-transport-discharge-lift-conditional-strong'):
    active = [] if active is None else list(active)
    return {
        'rho': 0.618,
        'family_label': 'standard-sine',
        'theorem_status': theorem_status,
        'open_hypotheses': [],
        'active_assumptions': list(active),
        'local_active_assumptions': [],
        'upstream_active_assumptions': list(active),
        'locked_window': list(locked or [0.971091, 0.971109]),
        'identified_threshold_branch_interval': list(branch or [0.971097, 0.971103]),
        'transport_locked_uniqueness_certificate': {
            'theorem_status': 'transport-locked-threshold-uniqueness-conditional-strong',
            'threshold_identification_ready': residual_status == 'transport-locked-identification-ready',
            'threshold_identification_interval': list(branch or [0.971097, 0.971103]),
            'threshold_identification_margin': 2.0e-6,
            'uniqueness_margin': 2.0e-6,
        },
        'threshold_identification_discharge_shell': {
            'overlap_window': list(overlap or [0.971092, 0.971108]),
            'identified_window': list(overlap or [0.971092, 0.971108]),
            'discharged_bridge_native_tail_witness_interval': list(witness or [0.971098, 0.971102]),
            'discharged_bridge_native_tail_witness_width': 4.0e-6,
            'residual_burden_summary': {'status': 'critical-surface-threshold-promotion-theorem-available'},
        },
        'residual_burden_summary': {'status': residual_status},
    }


def test_localized_implication_discharges_when_transport_locked_branch_is_supported(monkeypatch):
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate', lambda **kwargs: DummyCert(_transport_discharge()))

    cert = mod.build_golden_threshold_identification_localized_implication_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-ii-to-v-identification-theorem-discharged'
    assert cert['active_assumptions'] == []
    assert cert['residual_burden_summary']['status'] == 'localized-compatibility-implication-discharged'
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['workstream_promotion_theorem_available']['satisfied'] is True
    assert hyp['transport_locked_threshold_branch_identified']['satisfied'] is True
    assert hyp['identified_branch_interval_inside_workstream_overlap_window']['satisfied'] is True
    assert hyp['discharged_bridge_witness_supports_identified_branch']['satisfied'] is True


def test_localized_implication_remains_upstream_conditional_when_transport_shell_has_active_assumptions(monkeypatch):
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate', lambda **kwargs: DummyCert(_transport_discharge(active=['validated_function_space_continuation_transport'])))

    cert = mod.build_golden_threshold_identification_localized_implication_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-ii-to-v-identification-theorem-conditional-strong'
    assert cert['active_assumptions'] == ['validated_function_space_continuation_transport']
    assert cert['residual_burden_summary']['status'] == 'localized-compatibility-implication-upstream-frontier'


def test_localized_implication_stays_local_frontier_when_branch_leaves_overlap_window(monkeypatch):
    monkeypatch.setattr(mod, 'build_golden_theorem_ii_to_v_identification_transport_discharge_certificate', lambda **kwargs: DummyCert(_transport_discharge(branch=[0.971050, 0.971060], witness=[0.971098, 0.971102])))

    cert = mod.build_golden_threshold_identification_localized_implication_certificate(base_K_values=[0.3]).to_dict()
    assert cert['theorem_status'] == 'golden-theorem-ii-to-v-identification-theorem-conditional-partial'
    assert cert['residual_burden_summary']['status'] == 'localized-compatibility-implication-local-frontier'
    hyp = {row['name']: row for row in cert['hypotheses']}
    assert hyp['identified_branch_interval_inside_workstream_overlap_window']['satisfied'] is False
    assert hyp['discharged_bridge_witness_supports_identified_branch']['satisfied'] is False


def test_driver_exposes_localized_implication_reports(monkeypatch):
    monkeypatch.setattr(proof_driver, 'build_golden_threshold_identification_localized_implication_certificate', lambda **kwargs: DummyCert({
        'theorem_status': 'golden-theorem-ii-to-v-identification-theorem-discharged',
        'active_assumptions': [],
    }))
    monkeypatch.setattr(proof_driver, 'build_golden_theorem_ii_to_v_identification_theorem_certificate', lambda **kwargs: DummyCert({
        'theorem_status': 'golden-theorem-ii-to-v-identification-theorem-conditional-strong',
        'active_assumptions': ['validated_function_space_continuation_transport'],
    }))

    lift = proof_driver.build_golden_threshold_identification_localized_implication_report(base_K_values=[0.3])
    theorem = proof_driver.build_golden_theorem_ii_to_v_identification_theorem_report(base_K_values=[0.3])
    assert lift['theorem_status'] == 'golden-theorem-ii-to-v-identification-theorem-discharged'
    assert theorem['theorem_status'] == 'golden-theorem-ii-to-v-identification-theorem-conditional-strong'
