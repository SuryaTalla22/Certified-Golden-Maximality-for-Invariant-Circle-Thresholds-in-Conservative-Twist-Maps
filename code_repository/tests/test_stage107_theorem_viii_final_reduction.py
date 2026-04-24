from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from pathlib import Path


class Obj:
    def __init__(self, d=None):
        self.d = d or {}
    def to_dict(self):
        return dict(self.d)


@dataclass
class HarmonicFamily:
    harmonics: tuple = ((1.0, 1),)


def _install_stage107_stubs():
    pkg_path = Path(__file__).resolve().parents[1] / "kam_theorem_suite"
    for name in list(sys.modules):
        if name == "kam_theorem_suite" or name.startswith("kam_theorem_suite."):
            del sys.modules[name]
    package = types.ModuleType("kam_theorem_suite")
    package.__path__ = [str(pkg_path)]
    sys.modules["kam_theorem_suite"] = package

    def stub_module(name, **attrs):
        module = types.ModuleType("kam_theorem_suite." + name)
        for key, value in attrs.items():
            setattr(module, key, value)
        sys.modules["kam_theorem_suite." + name] = module
        return module

    def build_stub(**kwargs):
        return Obj({"theorem_status": "stub-front-complete", "open_hypotheses": [], "active_assumptions": []})

    stub_module("standard_map", HarmonicFamily=HarmonicFamily)
    stub_module("golden_aposteriori", build_golden_theorem_iii_certificate=build_stub, golden_inverse=lambda: 0.6180339887498948)
    stub_module("theorem_iv_analytic_lift", build_golden_theorem_iv_certificate=build_stub)
    stub_module("theorem_v_transport_lift", build_golden_theorem_v_certificate=build_stub)
    stub_module("threshold_identification_lift", build_golden_theorem_ii_to_v_identification_certificate=build_stub)
    stub_module("theorem_vi_envelope_lift", build_golden_theorem_vi_certificate=build_stub)
    stub_module("theorem_vii_exhaustion_lift", build_golden_theorem_vii_certificate=build_stub)
    stub_module("theorem_vii_exhaustion_discharge", build_golden_theorem_vii_discharge_certificate=build_stub)
    stub_module("theorem_i_ii_workstream_lift", build_golden_theorem_i_ii_workstream_lift_certificate=build_stub, build_golden_theorem_i_ii_certificate=build_stub)
    stub_module("threshold_identification_discharge", RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION="localized_identification_hinge")
    stub_module("threshold_identification_transport_discharge", RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION="transport_locked_identification_hinge")


def _stage107_shells():
    workstream = {"theorem_status": "golden-theorem-i-ii-workstream-papergrade-final", "open_hypotheses": [], "active_assumptions": [], "workstream_codepath_strong": True, "workstream_papergrade_strong": True, "workstream_residual_caveat": [], "residual_burden_summary": {"promotion_theorem_discharged": True, "status": "workstream-papergrade-final"}}
    theorem_iii = {"theorem_status": "golden-theorem-iii-final-strong", "theorem_iii_final_status": "golden-theorem-iii-final-strong", "open_hypotheses": [], "active_assumptions": [], "residual_theorem_iii_burden": [], "certified_below_threshold_interval": [0.9716350, 0.9716360]}
    theorem_iv = {"theorem_status": "golden-theorem-iv-final-strong", "open_hypotheses": [], "active_assumptions": [], "analytic_incompatibility_certified": True}
    theorem_v = {"theorem_status": "golden-theorem-v-compressed-contract-strong", "open_hypotheses": [], "active_assumptions": [], "compressed_contract": {"theorem_status": "golden-theorem-v-compressed-contract-strong", "target_interval": {"lo": 0.9716350, "hi": 0.9716370}, "uniform_majorant": {"preserves_golden_gap": True}}}
    ident = {"theorem_status": "golden-threshold-identification-discharge-lift-front-complete", "open_hypotheses": [], "active_assumptions": [], "overlap_window": [0.971634, 0.971638], "overlap_width": 0.000004, "discharged_bridge_native_tail_witness_interval": [0.9716352, 0.9716355], "discharged_bridge_native_tail_witness_width": 0.0000003, "bridge_native_tail_witness_source": "stage107-test-identification", "bridge_native_tail_witness_status": "discharged"}
    theorem_vi = {"theorem_status": "golden-theorem-vi-envelope-lift-screened-one-variable-strong", "statement_mode": "one-variable", "open_hypotheses": [], "active_assumptions": [], "residual_burden_summary": {"status": "theorem-vi-screened-local-final"}, "current_top_gap_scale": 0.000010, "current_most_dangerous_challenger_upper": 0.9716348, "discharged_identified_branch_witness_interval": [0.9716352, 0.9716355], "discharged_identified_branch_witness_width": 0.0000003, "threshold_identification_discharge_shell": ident}
    theorem_vii = {"theorem_status": "golden-theorem-vii-exhaustion-discharge-lift-conditional-strong", "open_hypotheses": [], "active_assumptions": [], "theorem_vii_codepath_final": True, "theorem_vii_papergrade_final": True, "theorem_vii_residual_citation_burden": [], "current_near_top_exhaustion_upper_bound": 0.9716347, "current_near_top_exhaustion_margin": 0.0000003, "current_near_top_exhaustion_pending_count": 0, "current_near_top_exhaustion_source": "stage106-global-exhaustion-support", "current_near_top_exhaustion_status": "near-top-exhaustion-strong", "theorem_vi_discharge_shell": theorem_vi}
    return workstream, theorem_iii, theorem_iv, theorem_v, ident, theorem_vi, theorem_vii


def test_stage107_support_closes_all_viii_assumptions_and_builds_final_discharge():
    _install_stage107_stubs()
    from kam_theorem_suite.theorem_viii_final_discharge_support import build_theorem_viii_final_discharge_support_certificate
    from kam_theorem_suite.theorem_viii_reduction_lift import build_golden_theorem_viii_reduction_lift_certificate
    from kam_theorem_suite.theorem_viii_reduction_discharge import build_golden_theorem_viii_reduction_discharge_lift_certificate

    workstream, theorem_iii, theorem_iv, theorem_v, ident, theorem_vi, theorem_vii = _stage107_shells()
    support = build_theorem_viii_final_discharge_support_certificate(
        threshold_identification_certificate=ident,
        theorem_i_ii_workstream_certificate=workstream,
        theorem_iii_certificate=theorem_iii,
        theorem_iv_certificate=theorem_iv,
        theorem_v_certificate=theorem_v,
        theorem_vi_certificate=theorem_vi,
        theorem_vii_certificate=theorem_vii,
    )
    viii = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.971635, 0.971637],
        theorem_i_ii_workstream_certificate=workstream,
        theorem_iii_certificate=theorem_iii,
        theorem_iv_certificate=theorem_iv,
        theorem_v_certificate=theorem_v,
        threshold_identification_discharge_certificate=ident,
        theorem_vi_envelope_discharge_certificate=theorem_vi,
        theorem_vii_exhaustion_discharge_certificate=theorem_vii,
        theorem_viii_final_discharge_support_certificate=support,
    ).to_dict()
    discharge = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.971635, 0.971637],
        baseline_theorem_viii_certificate=viii,
        theorem_viii_certificate=viii,
        theorem_vii_exhaustion_discharge_certificate=theorem_vii,
        theorem_vi_envelope_discharge_certificate=theorem_vi,
        threshold_identification_discharge_certificate=ident,
        theorem_i_ii_workstream_certificate=workstream,
        theorem_viii_final_discharge_support_certificate=support,
    ).to_dict()

    assert support["all_viii_assumptions_dischargeable"] is True
    assert support["undischarged_viii_assumptions"] == []
    assert viii["theorem_status"] == "golden-theorem-viii-reduction-lift-final-universal-ready"
    assert viii["open_hypotheses"] == []
    assert viii["active_assumptions"] == []
    assert discharge["theorem_status"] == "golden-universal-theorem-final-strong"
    assert discharge["open_hypotheses"] == []
    assert discharge["active_assumptions"] == []
    assert discharge["remaining_true_mathematical_burden"] == []
    assert discharge["final_certificate_ready_for_code_path"] is True
    assert discharge["final_certificate_ready_for_paper"] is True
    assert discharge["final_golden_maximality_discharge"] is True
