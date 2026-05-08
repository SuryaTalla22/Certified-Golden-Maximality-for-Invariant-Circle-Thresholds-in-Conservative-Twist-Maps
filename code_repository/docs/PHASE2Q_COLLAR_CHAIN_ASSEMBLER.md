# Phase 2Q: Collar-Chain Assembler for Theorem III

Phase 2Q is the chain-level audit layer for the Theorem III lower-anchor collar.
It does not run Newton solves, Phase 2O, or Phase 2P.  It consumes theorem-ready
Phase-2P segment candidates and checks that they form a continuous, theorem-facing
collar chain.

## Purpose

Earlier phases close individual collar segments:

- Phase 2N produces a single-N lower-anchor candidate.
- Phase 2O diagnoses tail/radius closure.
- Phase 2P replaces the scalar tail response with a strict modewise tail response
  and promotes a local segment when the radii margin is positive.

Phase 2Q turns those local closures into a proof-carrying chain artifact.  It checks:

1. every segment candidate is `theorem_facing=true`;
2. every segment candidate is `promotion_allowed=true`;
3. every segment candidate has `closure_level=phase2p_modewise_tail_closure`;
4. every selected Phase-2P row has `theorem_ready=true`;
5. every selected row has empty `failure_reasons`;
6. every candidate has empty `failure_fields`;
7. every segment has `radii_margin > min_segment_margin`;
8. every segment has `tail_T < allowable_tail_max`;
9. sorted intervals are adjacent/overlapping;
10. optional expected start/end and Regime-I handoff endpoints are covered.

## Inputs

The preferred inputs are explicit Phase-2P theorem-ready candidates, for example:

```text
artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_collar_000_FULL_THEOREM_READY_candidate.json
artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_collar_001_THEOREM_READY_candidate.json
```

Use explicit paths rather than a broad glob if the directory also contains diagnostic,
micro-width, or non-full candidates.

## Outputs

The command-line script writes three files:

- a full JSON chain audit report;
- a CSV segment table;
- a theorem-facing chain candidate JSON.

When the chain closes, the candidate has:

```json
{
  "theorem_facing": true,
  "promotion_allowed": true,
  "closure_level": "phase2q_collar_chain_closure",
  "failure_fields": []
}
```

## Typical command

```bash
python scripts/audit/run_lower_anchor_phase2q_chain_assembler.py \
  --candidate artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_collar_000_FULL_THEOREM_READY_candidate.json \
  --candidate artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_collar_001_THEOREM_READY_candidate.json \
  --expected-start 0.9600001 \
  --expected-end 0.9610002 \
  --expected-regime-i-hi 0.9600001 \
  --overlap-tolerance 1e-10 \
  --out artifacts/proof_audit/lower_corridor/phase2q_chain/phase2q_collar_000_001_chain_audit.json \
  --csv tables/proof_audit/lower_corridor/phase2q_chain/phase2q_collar_000_001_chain_segments.csv \
  --candidate-out artifacts/proof_audit/lower_corridor/phase2q_chain/phase2q_collar_000_001_chain_candidate.json
```

## Full collar target

Once enough Phase-2P segments have closed, rerun Phase 2Q with all theorem-ready
collar candidates and:

```text
--expected-start 0.9600001
--expected-regime-i-hi 0.9600001
--final-anchor-hi 0.971636
```

The full Theorem III lower-collar chain is closed only when the final chain candidate
is theorem-facing and `final_anchor_reached=true`.
