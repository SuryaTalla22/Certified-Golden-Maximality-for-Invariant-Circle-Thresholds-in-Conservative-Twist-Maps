from __future__ import annotations

from pathlib import Path
import sys
from pprint import pprint

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.proof_driver import (  # noqa: E402
    build_golden_aposteriori_certificate_report,
    build_golden_aposteriori_continuation_report,
)


if __name__ == "__main__":
    cert = build_golden_aposteriori_certificate_report(
        K=0.3,
        N_values=(32, 48, 64),
        sigma_cap=0.02,
        use_multiresolution=True,
    )
    print("Single-parameter golden a-posteriori certificate:")
    pprint({
        "theorem_status": cert["theorem_status"],
        "selected_N": cert["selected_N"],
        "atlas_quality": cert["atlas_quality"],
        "selected_bridge_quality": cert["selected_bridge_quality"],
        "weighted_residual_l1": cert["weighted_residual_l1"],
        "cohomological_correction_bound": cert["cohomological_correction_bound"],
        "relative_correction_to_graph": cert["relative_correction_to_graph"],
    })

    cont = build_golden_aposteriori_continuation_report(
        K_values=[0.2, 0.3, 0.4],
        N_values=(32, 48, 64),
        sigma_cap=0.02,
        use_multiresolution=True,
    )
    print("\nContinuation summary:")
    pprint({
        "success_prefix_len": cont["success_prefix_len"],
        "last_success_K": cont["last_success_K"],
        "first_nonstrong_K": cont["first_nonstrong_K"],
        "step_statuses": [step["theorem_status"] for step in cont["steps"]],
    })
