# Certified golden-threshold proof package

This repository is the paper-facing certified proof package for the standard-sine
golden-threshold maximality theorem.  The theorem is scoped to the certified
universe described in `CERTIFIED_UNIVERSE.json` and to the theorem-facing
artifacts listed in `ARTIFACT_MANIFEST.tsv`.  The final proof path is replayable
through the scripts in `scripts/` and audited by the validator conventions in
`docs/VALIDATOR_SPEC.md`.

The repository also contains examples and notebooks from the development history.
Those files are useful for provenance and experimentation, but they are not the
official proof path.  The official proof/audit path is:

```text
CERTIFIED_UNIVERSE.json
ARTIFACT_MANIFEST.tsv
HASHES.sha256
docs/VALIDATOR_SPEC.md
docs/CERTIFICATE_GLOSSARY.md
docs/REFEREE_AUDIT_PROTOCOL.md
scripts/replay_minimal.py
scripts/replay_downstream_from_cache.py
scripts/replay_full.py
```

## What the archive claims

Within the certified theorem universe, the final replay verifies the terminal
status

```text
golden-universal-theorem-final-strong
```

with

```text
active_assumptions = []
open_hypotheses = []
remaining_true_mathematical_burden = []
final_golden_maximality_discharge = true
```

This is a scoped computer-assisted theorem claim.  It is not a claim about every
analytic conservative twist map, every possible forcing family, or every
uncertified arithmetic normalization.  Changes to the map family, arithmetic
domain, threshold branch, or normalization require regenerated certificates and a
new manifest.

## Repository layout

```text
kam_theorem_suite/       theorem and validator modules
scripts/                 paper-facing replay and manifest scripts
tests/                   regression and negative-control tests
docs/                    validator specification, glossary, referee audit protocol
artifacts/final_discharge/stage_cache/
                         cached heavy upstream theorem artifacts
examples/                exploratory examples and provenance material
notebooks/               staged/exploratory notebook provenance
```

## Install

A clean development/audit environment can be created with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

For a minimal runtime environment without tests/notebooks:

```bash
pip install -e .
```

## Replay levels

The proof package separates three replay levels.

| Replay level | Command | Purpose |
|---|---|---|
| Minimal smoke replay | `python scripts/replay_minimal.py` | Verifies the final theorem ledger from compact theorem-facing shells.  This does not require heavy Theorem-IV regeneration. |
| Downstream from cache | `python scripts/replay_downstream_from_cache.py` | Requires cached I--II/III/IV artifacts and regenerates the V-and-beyond final-discharge logic.  This is the standard referee-facing replay. |
| Full archival replay | `python scripts/replay_full.py` | Fail-closed placeholder documenting the heavy Theorem-IV archival path.  It must be wired to the archival heavy-regeneration command before being described as a one-command full replay. |

The downstream replay is intentionally fail-closed by default.  It requires:

```text
artifacts/final_discharge/stage_cache/theorem_i_ii.json
artifacts/final_discharge/stage_cache/theorem_iii.json
artifacts/final_discharge/stage_cache/theorem_iv.json
```

and checks their hashes against `HASHES.sha256` when that ledger is present.

## Standard audit commands

```bash
# Verify all listed hashes.
sha256sum -c HASHES.sha256

# Regenerate the lightweight final theorem ledger.
python scripts/replay_minimal.py --out artifacts/paper_replay/minimal

# Regenerate V-and-beyond from cached heavy upstream artifacts.
python scripts/replay_downstream_from_cache.py --out artifacts/paper_replay/downstream_from_cache

# Regenerate the manifest/hash ledger after any artifact change.
python scripts/generate_artifact_manifest.py --root .

# Run publication-facing tests and negative controls.
pytest -q tests/test_paper_replay_scripts.py tests/test_negative_final_replay_controls.py
```

## Negative controls

The publication-facing tests check that the replay rejects, among other things:

- raw or diagnostic Theorem-V shells in place of the compressed theorem-facing contract;
- nonfinal Theorem-VII/global-exhaustion burdens;
- final-reduction scope mismatch;
- branch/chart mismatch at the identification seam;
- eroded or nonpositive interval margins;
- missing cached upstream artifacts in downstream replay;
- required artifact hash mismatches;
- nonempty omitted-label failure fields.

These tests are part of the audit argument: the validator is expected to fail
closed when theorem-facing hypotheses, margins, provenance, or scope conditions
are not satisfied.

## Regenerating the manifest and hash ledger

After changing generated artifacts, run:

```bash
python scripts/generate_artifact_manifest.py --root .
sha256sum -c HASHES.sha256
```

The manifest lists every JSON file in `artifacts/final_discharge/stage_cache/`.
`HASHES.sha256` lists those artifacts plus the core paper-facing audit files.

## Full Theorem-IV regeneration

The heavy Theorem-IV regeneration path is not launched automatically from this
paper-facing snapshot.  The cached Theorem-IV artifacts are included for the
standard referee replay.  If a future archival environment exposes a one-command
heavy regeneration path, wire it into `scripts/replay_full.py`, record the
hardware/runtime in `RELEASE_INFO.md`, regenerate the cache, and update both
`ARTIFACT_MANIFEST.tsv` and `HASHES.sha256`.
