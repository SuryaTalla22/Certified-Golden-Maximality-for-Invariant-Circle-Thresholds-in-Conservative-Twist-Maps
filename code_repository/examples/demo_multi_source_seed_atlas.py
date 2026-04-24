from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kam_theorem_suite.seed_transfer import build_seed_profile_from_orbit
from kam_theorem_suite.seeded_campaigns import SeedBankEntry
from kam_theorem_suite.multi_source_seed_atlas import build_multi_source_seed_atlas
from kam_theorem_suite.standard_map import HarmonicFamily, solve_periodic_orbit

if __name__ == '__main__':
    family = HarmonicFamily()
    bank = []
    for (p, q, K) in [(3, 5, 0.9710), (5, 8, 0.9711), (8, 13, 0.9712)]:
        sol = solve_periodic_orbit(p, q, K, family)
        if not sol['success']:
            continue
        profile = build_seed_profile_from_orbit(sol['x'], p=p, q=q, K=K, family=family, label=f'{p}/{q}')
        bank.append(SeedBankEntry(label=f'{p}/{q}', p=p, q=q, rho=p / q, K_center=K, source_method='demo', seed_profile=profile.to_dict()))
    report = build_multi_source_seed_atlas(bank, target_p=13, target_q=21, target_K=0.97125, family=family).to_dict()
    print({
        'selected_method': report['selected_method'],
        'selected_source_labels': report['selected_source_labels'],
        'selected_residual_inf': report['selected_residual_inf'],
    })
