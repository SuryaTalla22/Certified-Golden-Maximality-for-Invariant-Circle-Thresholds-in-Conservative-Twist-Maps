# Phase 2J Adaptive Rescue Status

Phase 2J implements the targeted rescue architecture for the eight lower-anchor segments that Phase 2I executed but could not promote.  It does **not** claim that the lower anchor is now proved.  It converts the Phase 2I fail-closed state into a precise, row-adaptive rescue plan modeled on the validated-solver methodology used for near-critical Greene-residue crossings: continuation-aware localization, predictive high-precision refinement, row-adaptive proof profiles, retry ladders, and strict separation between diagnostic attempts and theorem-facing certificates.

## Inputs

- `artifacts/proof_audit/lower_corridor/lower_anchor_phase2i_merged_candidate.json`
- `artifacts/proof_audit/lower_corridor/lower_anchor_phase2i_strict_ingestion_check.json`

## New code

- `kam_theorem_suite/audit/lower_anchor_phase2j_rescue_profiles.py`
- `kam_theorem_suite/audit/lower_anchor_phase2j_failure_atlas.py`
- `kam_theorem_suite/audit/lower_anchor_phase2j_adaptive_rescue.py`
- `scripts/audit/run_lower_anchor_phase2j_failure_atlas.py`
- `scripts/audit/run_lower_anchor_phase2j_rescue_summary.py`
- `tests/test_lower_anchor_phase2j_rescue.py`

## Generated artifacts

- `artifacts/proof_audit/lower_corridor/lower_anchor_phase2j_failure_atlas.json`
- `tables/proof_audit/lower_corridor/lower_anchor_phase2j_failure_atlas.csv`
- `scripts/audit/run_phase2j_rescue_segments.sh`
- `scripts/audit/run_phase2j_rescue_segments_dryrun.sh`
- `artifacts/proof_audit/lower_corridor/lower_anchor_phase2j_rescue_summary.json`
- `artifacts/proof_audit/replay/phase2j_rescue_tests.txt`

## Current diagnosis

The Phase 2J atlas confirms the Phase 2I diagnosis:

- total lower-anchor segments: 10
- theorem-ready prefix: 2 segments
- failed analytic segments: 8 segments
- minimum recomputed margin: `-0.001158602582069656`
- first failing segment: `phase2e_heavy_anchor_segment_002`
- final failing segment: `phase2e_heavy_anchor_segment_009`

The failures are analytic-radii failures, not missing-artifact failures.  Every failing row is classified by raw terms `Y`, `Z*r`, `T`, and `r`, and assigned a dominant failure term and a rescue profile.

## Rescue profile logic

The rescue planner assigns profiles by K-regime:

- `early`: moderate K; resolution ladder begins at `N=128`.
- `middle`: transition regime; resolution ladder extends to `N=512` or above.
- `near_critical`: close to the endpoint; resolution ladder extends to `N=768`.
- `endpoint`: final anchor segment; resolution ladder extends to `N=1024` and, when residual dominated, `N=2048`.

Each profile records:

- K-bisection count,
- overlap size,
- `N` ladder,
- oversampling ladder,
- sigma-cap sweep,
- high-precision dps target,
- radius-ladder metadata,
- predictive-center policy,
- refinement-round count.

The generated rescue script currently limits the number of variants per original failed segment to keep the bundle lightweight.  For a full HPC run, regenerate the atlas without `--max-variants-per-parent`.

## How to run the next expensive rescue attempt

From the repository root, in an environment with the real numerical stack available:

```bash
python scripts/audit/run_lower_anchor_phase2j_failure_atlas.py \
  --python-executable python \
  --max-variants-per-parent 8

bash scripts/audit/run_phase2j_rescue_segments.sh

python scripts/audit/run_lower_anchor_phase2j_rescue_summary.py
```

If rescue candidates become theorem-ready, merge the best theorem-ready subsegments with the original ready prefix and rerun:

```bash
python scripts/audit/regenerate_lower_anchor_chain.py \
  --candidate artifacts/proof_audit/lower_corridor/<merged_phase2j_candidate>.json \
  --strict
```

Only promote after strict Phase-2B ingestion passes.

## Fail-closed boundary

Phase 2J is a planning and rescue-execution layer.  It never weakens the Phase-2B gate.  A row remains non-promotable unless its recomputed raw inequality satisfies

```text
Y + Z r + T < r
```

with positive margin, source fields, analytic closure level, and non-diagnostic theorem-facing metadata.
