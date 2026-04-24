from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.proof_driver import build_stable_manifold_chart_report

family = HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])
report = build_stable_manifold_chart_report(family=family, family_label='demo_family')
print(report['theorem_status'])
print(report['stable_dimension'], report['unstable_dimension'])
print(report['graph_transform_contraction'])
