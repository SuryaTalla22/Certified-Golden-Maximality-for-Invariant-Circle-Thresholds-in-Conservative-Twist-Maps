# Track B Phase 5G-b: sign/hash corrective

Phase 5G successfully replayed the residual and small-divisor components, but the generation path had two plumbing problems:

1. the generated attachment forced the wrong scalar residual sign (`+1`), while replay found the correct selected sign was `-1` for the selected lower-anchor branch;
2. the generated attachment recomputed the certificate hash using canonical JSON rather than the raw byte SHA256 expected by the Phase 5E promotion gate and established in Phase 5F-b.

This overlay patches the Phase 5G component module so the certificate hash is raw byte SHA256, and it adds Phase 5G-b wrapper scripts that default to `--force-sign -1`. It remains fail-closed: only the residual and small-divisor flags may be true, and Phase 5E must still reject until all remaining formal evidence flags are supplied.
