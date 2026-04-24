from kam_theorem_suite.threshold_identification_localized_implication import (
    build_golden_threshold_identification_localized_implication_certificate,
)

cert = build_golden_threshold_identification_localized_implication_certificate(base_K_values=[0.3]).to_dict()
print(cert['theorem_status'])
print(cert['residual_burden_summary'])
