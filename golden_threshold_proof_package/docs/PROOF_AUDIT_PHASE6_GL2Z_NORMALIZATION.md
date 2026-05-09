# Phase 6: GL(2,Z) Normalization Audit

This phase adds a proof-carrying audit for the manuscript's GL(2,Z) language.
The audit is deliberately scoped: GL(2,Z) is treated as a representative-selection
convention inside the certified normalization domain `Dnorm`, not as an analytic
conjugacy claim for the standard map or for all projectively related rotation
numbers.

## New code

- `kam_theorem_suite/audit/gl2z_normalization_audit.py`
- `scripts/audit/audit_gl2z_normalization.py`
- `scripts/audit_gl2z_normalization.py`
- `tests/test_gl2z_normalization_audit.py`

## Audit logic

The audit consumes `CERTIFIED_UNIVERSE.json`, constructs the certified
normalization-domain convention, enumerates bounded GL(2,Z) projective images of
the golden representative, groups accepted candidates by representative value,
and verifies that the only accepted value in `Dnorm` is the canonical golden
representative.

The final theorem-facing Boolean is not trusted as a status string. It is derived
from the following checks:

1. the normalization type is `representative_selection`;
2. the group is `GL(2,Z)`;
3. the representative rule is the certified positive-reduced continued-fraction
   convention;
4. exactly one distinct representative is accepted in `Dnorm`;
5. the accepted representative is the canonical golden representative;
6. no nongolden representative is accepted in `Dnorm`;
7. no analytic conjugacy claim is made or consumed.

## Generated outputs

- `artifacts/proof_audit/gl2z_normalization/gl2z_normalization_audit.json`
- `artifacts/proof_audit/gl2z_normalization/gl2z_normalization_audit.bundle.json`
- `tables/proof_audit/gl2z_normalization/gl2z_representative_candidates.csv`
- `tables/proof_audit/gl2z_normalization/gl2z_representative_candidates.tex`
- `tables/proof_audit/gl2z_normalization/gl2z_normalization_summary.csv`
- `tables/proof_audit/gl2z_normalization/gl2z_normalization_summary.tex`
- `figures/proof_audit/gl2z_normalization/gl2z_candidate_values.pdf`
- `figures/proof_audit/gl2z_normalization/gl2z_normalization_counts.pdf`

## Negative controls

The Phase-6 tests verify that the audit fails closed when:

- the representative convention is changed;
- a nongolden representative is accepted in `Dnorm`;
- analytic conjugacy is claimed or claimed outside `Dnorm`;
- the final-reduction shell has `analytic_conjugacy_claimed=True`;
- the final status Boolean is preserved but its raw dependencies are removed.

## Reviewer command

```bash
python scripts/audit/audit_gl2z_normalization.py --strict
```

A passing run reports `status=passed`, `analytic_conjugacy_claimed=false`, and
`accepted_distinct_representative_count=1`.
