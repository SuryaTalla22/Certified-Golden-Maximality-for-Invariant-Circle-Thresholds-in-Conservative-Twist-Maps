from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.theorem_i_ii_workstream_lift import (
    build_golden_theorem_i_ii_workstream_lift_certificate,
)


def main() -> None:
    cert = build_golden_theorem_i_ii_workstream_lift_certificate(
        family=HarmonicFamily(),
    ).to_dict()
    print('status:', cert['theorem_status'])
    print('open hypotheses:')
    pprint(cert['open_hypotheses'])
    print('active assumptions:')
    pprint(cert['active_assumptions'])
    print('critical window:', cert['critical_parameter_window'])


if __name__ == '__main__':
    main()
