from kam_theorem_suite.golden_supercritical import build_golden_supercritical_obstruction_certificate
from kam_theorem_suite.irrational_limit_control import build_rational_irrational_convergence_certificate


def main() -> None:
    upper = build_golden_supercritical_obstruction_certificate(
        n_terms=4,
        keep_last=2,
        min_q=5,
        initial_subdivisions=1,
        max_depth=0,
        refine_upper_ladder=False,
        asymptotic_min_members=1,
    ).to_dict()
    cert = build_rational_irrational_convergence_certificate(
        upper["ladder"],
        refined=upper.get("refined"),
        asymptotic_audit=upper.get("asymptotic_audit"),
        rho_target=upper["rho"],
        family_label=upper["family_label"],
        min_members=2,
    )
    out = cert.to_dict()
    print(out["theorem_status"])
    print(out["selected_tail_qs"])
    print(out["limit_interval_lo"], out["limit_interval_hi"])


if __name__ == "__main__":
    main()
