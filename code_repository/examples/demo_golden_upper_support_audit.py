from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.proof_driver import (  # noqa: E402
    build_golden_upper_support_audit_report,
    build_golden_two_sided_support_audit_bridge_report,
)


def main() -> None:
    audit = build_golden_upper_support_audit_report(
        n_terms=3,
        keep_last=1,
        min_q=5,
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        crossing_center_offsets=(0.0,),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=1,
        support_fraction_threshold=0.5,
        min_tail_members=1,
    )
    print({
        "audit_status": audit["theorem_status"],
        "witness_count": audit["witness_count"],
        "robust_qs": audit["robust_qs"],
        "audited_upper_source": audit["audited_upper_source"],
    })

    bridge = build_golden_two_sided_support_audit_bridge_report(
        K_values=(0.45, 0.55, 0.65),
        n_terms=3,
        keep_last=1,
        min_q=5,
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        crossing_center_offsets=(0.0,),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        max_rounds=1,
        support_fraction_threshold=0.5,
        min_tail_members=1,
    )
    print({
        "bridge_status": bridge["theorem_status"],
        "gap_to_upper": bridge["relation"]["gap_to_upper"],
        "upper_status": bridge["relation"]["upper_status"],
    })


if __name__ == "__main__":
    main()
