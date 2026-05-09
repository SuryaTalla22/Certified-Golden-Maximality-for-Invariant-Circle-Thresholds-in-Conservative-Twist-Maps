# Phase 2V: Targeted Micro-Rescue Closer

Phase 2V is a narrow replacement for broad Phase 2U retries when a hard gap has many microsegments that miss by only a few `1e-8` and Phase 2P runs begin timing out.

## Why Phase 2V exists

Phase 2U used fixed microsegments, but its fast/aggressive profiles still ran more Phase 2O/2P combinations than needed. In the collar-012b1 case, the best rows repeatedly concentrated near:

- `sigma = 1e-7`
- `tail_cutoff = 1536` or nearby
- `radius_multiplier ≈ 1.08–1.20`
- `oversample = 16`

Phase 2V therefore runs a finer subdivision with a narrow evidence-driven grid.

## Recommended usage

Use Phase 2V on the hard interval with `256` pieces first. Run in chunks if the allocation is short.

```bash
python scripts/audit/run_lower_anchor_phase2v_targeted_micro_rescue.py \
  --label collar_012b1_v256 \
  --K-lo 0.9662501 \
  --K-hi 0.9663752 \
  --seed-json artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_collar_012a_N1024_os16_sg0p0001.json \
  --pieces 256 \
  --workers 48 \
  --profile needle
```

If needed, run chunks:

```bash
--piece-start 0 --piece-stop 64
--piece-start 64 --piece-stop 128
--piece-start 128 --piece-stop 192
--piece-start 192 --piece-stop 256
```

Then assemble:

```bash
python scripts/audit/run_lower_anchor_phase2v_targeted_micro_rescue.py \
  --label collar_012b1_v256 \
  --K-lo 0.9662501 \
  --K-hi 0.9663752 \
  --pieces 256 \
  --assemble-only
```

## Profiles

- `needle`: narrow, recommended default.
- `needle1536`: minimal grid around the historically best `sigma=1e-7`, `tail_cutoff=1536` pair.
- `rescue`: modestly wider, but still far smaller than Phase 2U aggressive.

## Outputs

Outputs are written under:

- `artifacts/proof_audit/lower_corridor/phase2v_micro/<label>/`
- `tables/proof_audit/lower_corridor/phase2v_micro/<label>/`
- `artifacts/proof_audit/replay/phase2v_<label>/`

The run summary is:

```text
artifacts/proof_audit/lower_corridor/phase2v_micro/<label>/phase2v_<label>_run_summary.json
```

