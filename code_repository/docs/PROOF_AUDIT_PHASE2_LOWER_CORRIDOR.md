# Phase 2 proof-audit implementation: lower-corridor continuation chain

This repository snapshot adds the Phase-2 lower-corridor audit layer requested in the targeted improvement plan.

## What was added

- `kam_theorem_suite/audit/lower_corridor_chain.py`
  - `LowerChainSegment`
  - `LowerChainVerification`
  - `extract_existing_lower_segments(...)`
  - `verify_lower_chain(...)`
  - `build_lower_chain_audit_bundle(...)`
  - `write_lower_chain_audit(...)`
  - lightweight PDF/table generation helpers
- `scripts/audit/audit_lower_corridor_chain.py`
- `tests/test_lower_corridor_chain_audit.py`
- generated Phase-2 artifacts:
  - `artifacts/proof_audit/lower_corridor/lower_corridor_audit.json`
  - `artifacts/proof_audit/lower_corridor/lower_corridor_audit.bundle.json`
  - `tables/proof_audit/lower_corridor/lower_corridor_segments.csv`
  - `tables/proof_audit/lower_corridor/lower_corridor_segments.tex`
  - `figures/proof_audit/lower_corridor/lower_chain_margins.pdf`
  - `figures/proof_audit/lower_corridor/lower_chain_resolution.pdf`
  - `figures/proof_audit/lower_corridor/lower_chain_tail_majorant.pdf`
  - `figures/proof_audit/lower_corridor/lower_chain_overlap.pdf`

## Validator semantics

Each lower-chain segment records the explicit inequality

```text
Y_j + Z_j r_j + T_Nj(r_j) < r_j
```

The audit recomputes the margin

```text
m_j = r_j - (Y_j + Z_j r_j + T_Nj(r_j))
```

and rejects the chain if any theorem-facing segment has a nonpositive recomputed margin, if a stored margin disagrees with the recomputed margin, if an adjacent chart/branch-overlap witness is missing or nonpositive, or if the chain does not reach the final near-critical anchor.

## Current repository result

The current artifact-extraction audit is intentionally fail-closed:

```text
status: failed
lower_chain_verified: false
final_anchor_reached: false
final_anchor: [0.9716350, 0.9716360]
covered_interval from cached Theorem-III evidence: [0.2, 0.265]
min_radii_margin: 7.999959887077787e-09
min_overlap_width: 7.999959887077787e-09
failure_fields: ["final_anchor_not_reached"]
```

This is the correct result for the current cached Theorem-III artifact: the local and neighborhood lower-side proof fields close, but they do not by themselves contain a proof-carrying near-critical lower-anchor segment. The final replay therefore refuses to consume this Theorem-III artifact as a proof-audit-derived final lower anchor.

## Running the audit

```bash
python scripts/audit/audit_lower_corridor_chain.py
```

Use strict mode to make the current failure return a nonzero exit status:

```bash
python scripts/audit/audit_lower_corridor_chain.py --strict
```

## Tests run for this phase

```bash
pytest -q tests/test_phase0_phase1_proof_audit.py tests/test_lower_corridor_chain_audit.py
python -m py_compile \
  kam_theorem_suite/audit/lower_corridor_chain.py \
  kam_theorem_suite/audit/artifact_shell_builder.py \
  kam_theorem_suite/paper_replay_inputs.py \
  scripts/audit/audit_lower_corridor_chain.py
```

The full repository test suite includes heavier exploratory tests and timed out in this environment, so the phase-specific proof-audit regression suite above is the tested target for this bundle.
