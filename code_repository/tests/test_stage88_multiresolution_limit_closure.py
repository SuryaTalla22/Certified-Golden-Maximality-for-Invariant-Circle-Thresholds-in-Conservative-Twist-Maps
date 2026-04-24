from __future__ import annotations

from kam_theorem_suite.irrational_existence_atlas import (
    ResolutionComparison,
    ResolutionValidationEntry,
    MultiResolutionValidationReport,
    build_multiresolution_limit_closure_certificate,
)
import numpy as np


def _entry(N: int, *, success: bool = True):
    return ResolutionValidationEntry(
        N=N,
        success=success,
        bridge_quality='strong' if success else 'failed',
        radius=1e-6,
        residual_inf=1e-8,
        oversampled_residual_inf=1e-8,
        fourier_tail_l2=1e-8,
        strip_width_proxy=0.02,
        contraction_bound=0.2,
        lambda_value=0.0,
        message='ok',
        solver_iterations=3,
        u=np.zeros(N),
        z=np.zeros(N + 1),
    )


def test_stage88_multiresolution_limit_closure_strong() -> None:
    report = MultiResolutionValidationReport(
        rho=0.618,
        K=0.3,
        family_label='standard-sine',
        resolutions=[_entry(32), _entry(48)],
        comparisons=[ResolutionComparison(32, 48, 1e-4, 1e-3, 1e-4, 1e-3, 0.2, 0.5, 1.0, True)],
        all_success=True,
        finest_success_N=48,
        stable_success_prefix=2,
        success_count=2,
        atlas_quality='strong',
        recommended_quality_floor='strong',
        stability_summary={'stable_pair_count': 1},
    )
    cert = build_multiresolution_limit_closure_certificate(report).to_dict()
    assert cert['multiresolution_closure_status'] == 'multiresolution-limit-closure-strong'
    assert cert['limit_profile_ready_for_closure'] is True


def test_stage88_multiresolution_limit_closure_partial_when_pairs_are_not_stable() -> None:
    report = MultiResolutionValidationReport(
        rho=0.618,
        K=0.3,
        family_label='standard-sine',
        resolutions=[_entry(32), _entry(48)],
        comparisons=[ResolutionComparison(32, 48, 1e-1, 5e-2, 1e-1, 5e-2, 1.2, 1.5, 0.8, False)],
        all_success=True,
        finest_success_N=48,
        stable_success_prefix=1,
        success_count=2,
        atlas_quality='moderate',
        recommended_quality_floor='moderate',
        stability_summary={'stable_pair_count': 0},
    )
    cert = build_multiresolution_limit_closure_certificate(report).to_dict()
    assert cert['multiresolution_closure_status'] == 'multiresolution-limit-closure-partial'
    assert cert['limit_profile_ready_for_closure'] is False
