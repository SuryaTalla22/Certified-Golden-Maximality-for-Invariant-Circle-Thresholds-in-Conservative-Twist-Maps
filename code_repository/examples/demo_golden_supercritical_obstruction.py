from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite import build_golden_supercritical_obstruction_report, build_golden_two_sided_bridge_report, save_json  # noqa: E402


def main() -> None:
    obstruction = build_golden_supercritical_obstruction_report(
        n_terms=5,
        keep_last=2,
        min_q=5,
        initial_subdivisions=1,
        max_depth=0,
    )
    bridge = build_golden_two_sided_bridge_report(
        K_values=[0.3],
        N_values=(24,),
        use_multiresolution=False,
        n_terms=5,
        keep_last=2,
        min_q=5,
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
    )
    outdir = ROOT / 'outputs'
    outdir.mkdir(exist_ok=True)
    save_json({'obstruction': obstruction, 'bridge': bridge}, outdir / 'demo_golden_supercritical_obstruction.json')
    print(json.dumps({'obstruction_status': obstruction['theorem_status'], 'bridge_status': bridge['theorem_status']}, indent=2))


if __name__ == '__main__':
    main()
