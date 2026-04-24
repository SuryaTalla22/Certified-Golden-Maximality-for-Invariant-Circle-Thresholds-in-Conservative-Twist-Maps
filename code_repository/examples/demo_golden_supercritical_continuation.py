from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite import (  # noqa: E402
    build_golden_supercritical_continuation_report,
    build_golden_two_sided_continuation_bridge_report,
    save_json,
)


def main() -> None:
    continuation = build_golden_supercritical_continuation_report(
        n_terms=5,
        keep_last=2,
        min_q=5,
        crossing_center_offsets=(-4.0e-4, 0.0, 4.0e-4),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
    )
    bridge = build_golden_two_sided_continuation_bridge_report(
        K_values=[0.3],
        N_values=(24,),
        use_multiresolution=False,
        n_terms=5,
        keep_last=2,
        min_q=5,
        crossing_center_offsets=(-4.0e-4, 0.0, 4.0e-4),
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
    )
    outdir = ROOT / 'outputs'
    outdir.mkdir(exist_ok=True)
    save_json({'continuation': continuation, 'bridge': bridge}, outdir / 'demo_golden_supercritical_continuation.json')
    print(json.dumps({
        'continuation_status': continuation['theorem_status'],
        'bridge_status': bridge['theorem_status'],
        'upper_support_size': continuation['stable_upper_support_size'],
    }, indent=2))


if __name__ == '__main__':
    main()
