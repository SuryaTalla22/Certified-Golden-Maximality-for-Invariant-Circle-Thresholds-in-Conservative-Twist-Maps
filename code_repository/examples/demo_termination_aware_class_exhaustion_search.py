from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite import ArithmeticClassSpec, build_termination_aware_class_exhaustion_search_report


def main() -> None:
    specs = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label="silver"),
        ArithmeticClassSpec(preperiod=(), period=(3,), label="bronze"),
        ArithmeticClassSpec(preperiod=(), period=(1, 2), label="mixed"),
    ]
    report = build_termination_aware_class_exhaustion_search_report(
        specs,
        reference_crossing_center=0.97135,
        reference_lower_bound=0.9711,
        rounds=3,
        per_round_budget=2,
        deferred_probe_budget=1,
        deferred_probe_every=2,
        initial_max_q=21,
        max_q_step=8,
        initial_keep_last=2,
        q_min=2,
        initial_subdivisions=2,
        max_depth=1,
        min_width=1e-3,
    )
    outdir = ROOT / 'outputs'
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / 'demo_termination_aware_class_exhaustion_search.json'
    path.write_text(json.dumps(report, indent=2))
    print(f"Wrote {path}")
    print(report['status'])


if __name__ == '__main__':
    main()
