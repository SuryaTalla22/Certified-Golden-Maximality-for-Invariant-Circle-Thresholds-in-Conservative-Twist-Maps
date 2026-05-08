# Track B Phase 4b: lift-aware residual and aliasing audit

Phase 4 found weak automatic-reducibility diagnostics. This corrective audit does two things:

1. It fixes a diagnostic bug in the embedding residual: `x = theta + u` is a lift, not a periodic function, so it must not be FFT-shifted directly. The correct target is `theta + omega + u(theta+omega)`.
2. It audits derivative/tangent residuals and automatic-reducibility defects under oversampling and Fourier cutoffs. If scalar residuals are tiny but tangent defects remain large, the seed is likely collocation/aliasing-limited and must be refined at higher resolution before theorem-facing intervalization.

All outputs are diagnostic only.
