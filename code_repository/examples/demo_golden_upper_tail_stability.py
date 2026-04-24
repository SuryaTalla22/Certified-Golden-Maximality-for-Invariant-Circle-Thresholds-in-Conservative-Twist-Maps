from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from kam_theorem_suite.proof_driver import (
    build_golden_upper_tail_stability_report,
    build_golden_two_sided_tail_stability_bridge_report,
)

def main() -> None:
    audit = build_golden_upper_tail_stability_report(
        n_terms=3, keep_last=1, min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        crossing_center_offsets=(0.0,),
        initial_subdivisions=1, max_depth=0,
        refine_upper_ladder=False, max_rounds=1,
        support_fraction_threshold=0.5, min_tail_members=1,
        min_cluster_size=1, min_stable_tail_members=1,
    )
    print({"status": audit["theorem_status"], "clustered_atlas_count": len(audit["clustered_entry_indices"]), "stable_tail_qs": audit["stable_tail_qs"]})
    bridge = build_golden_two_sided_tail_stability_bridge_report(
        K_values=(0.45, 0.55, 0.65),
        n_terms=3, keep_last=1, min_q=5,
        atlas_shifts=(-4.0e-4, 0.0, 4.0e-4),
        atlas_center_offsets=(-6.0e-4, 0.0, 6.0e-4),
        crossing_center_offsets=(0.0,),
        initial_subdivisions=1, max_depth=0,
        refine_upper_ladder=False, max_rounds=1,
        support_fraction_threshold=0.5, min_tail_members=1,
        min_cluster_size=1, min_stable_tail_members=1,
    )
    print({"status": bridge["theorem_status"], "gap_to_upper": bridge["relation"]["gap_to_upper"], "stable_tail_qs": bridge["relation"]["stable_tail_qs"]})

if __name__ == '__main__':
    main()
