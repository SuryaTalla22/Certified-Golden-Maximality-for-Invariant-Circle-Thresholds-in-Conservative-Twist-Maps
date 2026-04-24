from kam_theorem_suite.proof_driver import build_threshold_compatibility_window_report
from kam_theorem_suite.standard_map import HarmonicFamily

family = HarmonicFamily(harmonics=[(1.03, 1, 0.03), (0.07, 2, 0.01), (0.02, 3, -0.02)])
report = build_threshold_compatibility_window_report(family=family, family_label='demo')
print(report['theorem_status'])
print(report['compatibility_interval'])
