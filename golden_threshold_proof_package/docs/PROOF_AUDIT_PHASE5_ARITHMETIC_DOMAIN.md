# Phase 5 Proof-Audit: Arithmetic Grammar and Generated-Domain Exhaustion

This phase adds a proof-carrying audit layer for Theorem VII.  The goal is to make the certified arithmetic domain visible as a generated grammar with route-level control certificates, rather than as a compact list of near-top labels.

## New code

- `kam_theorem_suite/audit/arithmetic_domain_grammar.py`
- `scripts/audit/audit_arithmetic_domain.py`
- `scripts/audit_arithmetic_domain.py`
- `scripts/study_nonvacuous_omitted_tail_control.py`
- `tests/test_arithmetic_domain_grammar_audit.py`

The main dataclass is `GrammarRecord`, which records:

- label;
- continued-fraction pattern;
- eta interval, when available;
- generation rule;
- route: `screened`, `ranked`, `pruned`, `lifecycle`, `termination`, or `omitted`;
- control certificate;
- upper ceiling / lower reference / margin, when scalar comparison is the control mechanism;
- certified flag.

## Audit semantics

The Phase-5 audit accepts Theorem VII only if all of the following are true:

1. The domain grammar is generated before the final maximality conclusion.
2. Every generated record has one of the six accepted control routes.
3. Every generated record has a control certificate.
4. The required exact-ranking near-top labels `silver` and `bronze` are present.
5. VII failure fields are empty.
6. The omitted-tail route is either explicitly vacuous with an empty generated complement or nonvacuously envelope-certified.
7. The near-top upper ceiling is strictly below the golden lower anchor.
8. The final `domain_exhaustion_certified` Boolean is derived from the raw grammar records, interval separation, and failure-field counts.

Empty failure lists alone are not sufficient: an audit with no generated records fails closed.

## Generated outputs

Running:

```bash
python scripts/audit/audit_arithmetic_domain.py
python scripts/study_nonvacuous_omitted_tail_control.py
```

produces:

- `artifacts/proof_audit/arithmetic_domain/arithmetic_domain_audit.json`
- `artifacts/proof_audit/arithmetic_domain/arithmetic_domain_audit.bundle.json`
- `artifacts/proof_audit/arithmetic_domain/nonvacuous_omitted_tail_study.json`
- `tables/proof_audit/arithmetic_domain/arithmetic_domain_records.csv`
- `tables/proof_audit/arithmetic_domain/arithmetic_domain_records.tex`
- `tables/proof_audit/arithmetic_domain/domain_grammar_counts.csv`
- `tables/proof_audit/arithmetic_domain/domain_grammar_counts.tex`
- `figures/proof_audit/arithmetic_domain/domain_route_counts.pdf`
- `figures/proof_audit/arithmetic_domain/domain_grammar_tree.pdf`

The current audit reports eight generated records:

- 2 screened;
- 2 ranked;
- 1 pruned;
- 1 lifecycle-routed;
- 2 termination-promoted;
- 0 omitted;
- 0 uncontrolled.

The omitted-tail status is `vacuous_with_empty_complement`, matching the scoped generated-domain theorem.  The nonvacuous omitted-tail study is intentionally diagnostic and not theorem-facing.

## Bundle-size policy

This phase does not store Theorem V, VI, VII, VIII, or final-discharge theorem artifacts.  The arithmetic-domain proof audit is a lightweight `ProofAuditBundle` derived from `CERTIFIED_UNIVERSE.json` and a small generated-domain support payload.  The returned bundle retains I--IV upstream artifacts only, plus proof-audit JSON/CSV/PDF outputs.
