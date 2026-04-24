from kam_theorem_suite.validated_critical_surface_theorem import (
    build_validated_critical_surface_theorem_discharge_certificate,
    build_validated_critical_surface_theorem_promotion_certificate,
)


discharge = build_validated_critical_surface_theorem_discharge_certificate(
    validated_renormalization_package_promotion={
        'theorem_flags': {'validated_true_renormalization_fixed_point_package_available': True},
        'promotion_margin': 0.03,
    },
    stable_manifold_certificate={
        'theorem_status': 'proxy-stable-manifold-chart-identified',
        'stable_chart_radius': 0.03,
    },
    critical_surface_bridge_certificate={
        'theorem_status': 'proxy-critical-surface-family-bridge-identified',
    },
    validated_critical_surface_bridge_certificate={
        'theorem_status': 'proxy-critical-surface-window-bridge-validated',
        'theorem_flags': {
            'localized_transversality_window': True,
            'derivative_floor_positive': True,
            'window_narrow_enough': True,
        },
        'localized_center': 1.0,
        'localized_radius': 0.02,
        'transversality_margin': 0.07,
        'derivative_floor_proxy': 0.05,
    },
    active_assumptions=[
        'golden_stable_manifold_is_true_critical_surface',
        'family_chart_crossing_identifies_true_critical_parameter',
        'golden_critical_surface_transversality_on_class',
        'theorem_grade_banach_manifold_universality_class',
    ],
).to_dict()

promotion = build_validated_critical_surface_theorem_promotion_certificate(
    discharge_certificate=discharge,
).to_dict()

print(discharge['theorem_status'])
print(promotion['theorem_status'])
print(promotion['active_assumptions'])
