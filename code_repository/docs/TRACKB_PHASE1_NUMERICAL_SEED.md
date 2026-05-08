# Track B / Phase 1: numerical seed for Theorem III

This stage is diagnostic only. It computes approximate golden invariant-circle embeddings near the Theorem-III lower-anchor target. It does **not** produce a theorem-facing certificate.

The solver uses the scalar standard-map parameterization equation

```text
u(t+w) - 2u(t) + u(t-w) - K/(2*pi) sin(2*pi*(t+u(t))) = 0.
```

The exported embedding is `x(t)=t+u(t)`, `r(t)=x(t)-x(t-w)`. Outputs are marked `diagnostic_only=true`, `theorem_facing=false`, and `promotion_allowed=false`.

Main script:

```bash
python scripts/audit/run_theorem_iii_trackb_phase1_seed.py \
  --anchors 0.96630,0.96800,0.97000,0.97100,0.97150,0.9716350 \
  --resolutions 256,512,1024 \
  --workers 64 \
  --continuation-steps 40 \
  --out-dir artifacts/proof_audit/theorem_iii_trackb/phase1_seed
```

Outputs:

```text
artifacts/proof_audit/theorem_iii_trackb/phase1_seed/
  phase1_seed_summary.json
  phase1_seed_results.csv
  records/*.json
  embeddings/*.npz
```
