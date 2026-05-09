# Phase 9: Proof-Audit Notebooks

Phase 9 adds a lightweight, reviewer-facing notebook layer over the proof-audit artifacts generated in Phases 2--8.  The notebooks are intentionally not heavy numerical regeneration notebooks.  They read the JSON/CSV proof payloads, recompute the visible margins that a referee is most likely to inspect, and write compact summaries under `artifacts/proof_audit/notebooks/`.

## Added files

- `kam_theorem_suite/audit/proof_audit_notebooks.py`
- `scripts/audit/generate_proof_audit_notebooks.py`
- `scripts/audit/execute_proof_audit_notebooks.py`
- `scripts/generate_proof_audit_notebooks.py`
- `scripts/execute_proof_audit_notebooks.py`
- `tests/test_proof_audit_notebooks.py`
- `notebooks/proof_audit/00_audit_index_and_environment.ipynb`
- `notebooks/proof_audit/01_lower_corridor_chain_audit.ipynb`
- `notebooks/proof_audit/02_upper_obstruction_margin_audit.ipynb`
- `notebooks/proof_audit/03_transport_budget_audit.ipynb`
- `notebooks/proof_audit/04_arithmetic_domain_exhaustion_audit.ipynb`
- `notebooks/proof_audit/05_gl2z_normalization_audit.ipynb`
- `notebooks/proof_audit/06_replay_validator_audit.ipynb`
- `notebooks/proof_audit/07_reviewer_dashboard.ipynb`

## Reviewer path

Regenerate the notebooks:

```bash
python -S scripts/audit/generate_proof_audit_notebooks.py
```

Execute them as a lightweight CI/preflight check:

```bash
python -S scripts/audit/execute_proof_audit_notebooks.py
```

The executor does not require `nbconvert` or `nbformat`; it reads the notebook JSON and executes code cells with ordinary Python.  This makes the notebook layer testable in minimal environments while leaving the files as standard `.ipynb` notebooks for interactive review.

## Current expected result

The Phase-9 dashboard reports:

```text
phase9_status = passed-with-known-lower-gap
strict_final_ready = false
known_lower_gap = true
```

This is the honest status of the repository.  The proof-audit notebooks verify that the upper obstruction, transport budget, arithmetic-domain grammar, GL(2,Z) normalization, and reviewer-mode hardened validator pass.  They also preserve the known Phase-2 blocker: the current lower-corridor artifact does not yet supply a proof-carrying near-critical final-anchor chain.

## Large-artifact policy

The notebooks do not store cached Theorem V/VI/VII/VIII/final-discharge artifacts in `artifacts/final_discharge/stage_cache/`.  They only consume lightweight proof-audit JSON/CSV payloads and write small notebook summaries.
