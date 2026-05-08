# Phase 2R: Automated Collar Propagation Pipeline

Phase 2R automates the successful Theorem III lower-collar workflow:

1. **Phase 2N** solves/audits a single collar segment.
2. **Phase 2O** produces a tail/radius candidate from the Phase 2N summary.
3. **Phase 2P** applies the strict modewise inverse-tail closure.
4. **Phase 2Q** assembles all theorem-ready collar segments into a chain certificate.

The automation script is deliberately an orchestrator. It does not replace the validators. It calls the existing scripts, checks the JSON outputs, promotes only theorem-ready Phase 2P candidates, and reruns Phase 2Q after each new segment.

## Main script

```bash
scripts/audit/run_lower_anchor_phase2r_auto_collar_pipeline.py
```

## Typical use after collars 000 and 001 are closed

Run collar 002 only first:

```bash
python scripts/audit/run_lower_anchor_phase2r_auto_collar_pipeline.py \
  --start-index 2 \
  --stop-index 2
```

Then continue to the final lower anchor:

```bash
python scripts/audit/run_lower_anchor_phase2r_auto_collar_pipeline.py \
  --start-index 3 \
  --target-hi 0.971636 \
  --final-anchor-hi 0.971636
```

The script is resumable by default. It skips theorem-ready segments that already exist and reuses existing intermediate summaries/candidates unless `--force` is passed.

## Output locations

- Logs: `artifacts/proof_audit/replay/phase2r_collar_*.log`
- Auto summary: `artifacts/proof_audit/lower_corridor/phase2r_auto/phase2r_auto_run_summary.json`
- Promoted Phase 2P candidates: `artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_collar_XXX_THEOREM_READY_candidate.json`
- Phase 2Q chain candidates: `artifacts/proof_audit/lower_corridor/phase2q_chain/phase2q_collar_000_XXX_chain_candidate.json`

## Important behavior

- The script requires an already closed prefix when assembling the chain. If collars 000 and 001 are already closed, start at `--start-index 2`.
- For each new collar, it tries to seed Phase 2N from the previous collar's Phase 2N JSON.
- It stops immediately if Phase 2P does not produce a theorem-facing/promotable candidate.
- It stops immediately if Phase 2Q cannot assemble the chain.
- If `--target-hi` is supplied, the last segment may be shortened so the chain ends exactly at the target.

## Dry run

```bash
python scripts/audit/run_lower_anchor_phase2r_auto_collar_pipeline.py \
  --start-index 2 \
  --stop-index 2 \
  --dry-run
```

## Inspect existing theorem-ready candidates

```bash
python scripts/audit/run_lower_anchor_phase2r_auto_collar_pipeline.py --inspect-existing
```
