from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.proof_driver import (
    build_universality_class_report,
    build_renormalization_class_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily


def main() -> None:
    family = HarmonicFamily(harmonics=[(1.0, 1, 0.0), (0.08, 2, 0.03)])
    print('Universality-class report:')
    pprint(build_universality_class_report(family=family, family_label='demo_family'))
    print('\nRenormalization-class report:')
    pprint(build_renormalization_class_report(family=family, family_label='demo_family'))


if __name__ == '__main__':
    main()
