from kam_theorem_suite.proof_driver import (
    build_validated_universality_class_theorem_discharge_report,
    build_validated_universality_class_theorem_promotion_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily
from pprint import pprint

family = HarmonicFamily()
discharge = build_validated_universality_class_theorem_discharge_report(
    family=family,
    universality_class_certificate={
        'admissible': True,
        'status': 'admissible',
        'admissibility_margins': {
            'exact_symplectic_margin': 1e-12,
            'twist_margin': 1.0,
            'anchor_amplitude_margin': 0.2,
            'anchor_phase_margin': 0.1,
            'higher_mode_energy_margin': 0.3,
            'weighted_mode_budget_margin': 2.0,
            'max_mode_margin': 4.0,
            'strip_width_margin': 0.05,
        },
    },
    renormalization_class_certificate={
        'admissible_near_chart': True,
        'status': 'near_golden_chart_scaffold',
        'chart_margins': {'chart_margin': 0.1},
    },
    active_assumptions=['theorem_grade_banach_manifold_universality_class'],
)
promotion = build_validated_universality_class_theorem_promotion_report(
    family=family,
    discharge_certificate=discharge,
)
pprint(discharge)
pprint(promotion)
