from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json

from kam_theorem_suite.seed_transfer import build_seed_profile_from_orbit, build_seed_transfer_report
from kam_theorem_suite.standard_map import HarmonicFamily, solve_periodic_orbit

def main() -> None:
    family = HarmonicFamily()
    src = solve_periodic_orbit(5, 8, 0.9711, family)
    if not src['success']:
        raise RuntimeError(f"source solve failed: {src['message']}")
    profile = build_seed_profile_from_orbit(src['x'], p=5, q=8, K=0.9711, family=family, label='5/8')
    rep = build_seed_transfer_report(profile, target_p=8, target_q=13, target_K=0.9712, family=family)
    print(json.dumps(rep.to_dict(), indent=2)[:2000])

if __name__ == '__main__':
    main()
