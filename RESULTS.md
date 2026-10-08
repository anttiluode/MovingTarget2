# Frozen twenty-seed result

Run: 2026-10-08. Protocol commit: [58aab4576c5fd31e0eb46f42757a0ca1f8b2574d](https://github.com/anttiluode/MovingTarget2/commit/58aab4576c5fd31e0eb46f42757a0ca1f8b2574d), published before the full outcome run. Seeds 4100..4119, all reported. No thresholds, seeds, query budgets or pulse strengths were changed after outcomes.

The compact code works in the deliberately preserved weak-response family. Stronger probes, changed semantic grouping and uncompensated reads expose three different ways that preservation can fail.

## Fixed gates

| Gate | Criterion | Observed | Outcome |
|---|---|---|---|
| H1: motion with preserved first moments | Median phase RMS >=0.35; maximum first-moment error <1e-8 | 0.630 rad; 6.13e-13 | Pass |
| H2: fitted small code | Median weak prediction NRMSE <=0.06; >=15/20 seeds <=0.08 | 0.01825; **20/20** seeds <=0.08 | Pass |
| H3: stronger-ping boundary | Strong response drift >=2x weak; current order-4 code improves reconstruction >=3x | Drift 14.17x; reconstruction 14.12x | Pass |
| H4: semantic assignment | Shuffle error >=0.4 and >=5x constrained weak drift | 0.9531; 110.9x | Pass |
| H5: repeated-read compensation | Sign reversal reduces response change >=2x | 0.9372 vs 0.01513, ratio 61.94x | Pass, in the fixed idealized protocol |

The ratios use medians of the corresponding metrics. They are not averages of per-seed ratios. Passing H1 reflects the imposed constraint; H2 tests finite calibration and generalization within the known response family. None of the gates tests spontaneous biological emergence.

## Held-out measurements

NRMSE uses the RMS response of the initial state at the same pulse amplitude as denominator. Values shown as percentages are 100 times this normalized error. IQR is the interval between the 25th and 75th percentiles across twenty seeds, not a confidence interval.

| Measurement | Median | IQR |
|---|---:|---:|
| Phase RMS change, radians | 0.6300 | 0.6064–0.6606 |
| Weak response change under constrained drift | 0.86% | 0.70–1.09% |
| Weak response change under matched unrestricted drift | 33.47% | 29.48–39.66% |
| Fitted first-moment code error before drift | 1.77% | 1.61–2.09% |
| Frozen fitted code error after drift | **1.83%** | 1.61–2.00% |
| Nearest-query table error after drift | 49.71% | 44.49–53.66% |
| Zero-answer error after drift | 100.00% | 99.97–100.02% |
| Strong response change under constrained drift | **12.18%** | 10.69–14.60% |
| Current exact order-1 code, strong prediction error | 16.16% | 14.88–17.44% |
| Current exact order-4 code, strong prediction error | **1.14%** | 1.04–1.37% |
| Frozen exact order-8 code, strong prediction error after drift | 12.17% | 10.68–14.60% |
| Weak response change after cross-group shuffle | **95.31%** | 83.27–106.00% |

The maximum fitted weak-code error was 2.85%. No held-out answers or phase coordinates entered its fit. The twelve fitted coefficients also absorb some finite-pulse truncation and calibration noise, so they need not equal the exact physical first moments.

The current order-4 reference reads the full phase state to obtain 48 real coefficients. Its low strong-probe error shows that higher moments describe the changed state. The frozen order-8 code stores 96 real coefficients and still misses the changed strong response by approximately the full 12.2% drift. Keeping more details from the old state does not force the substrate to preserve those details.

The nearest-query table stores the same 64 noisy measurements, using periodic nearest-neighbor distance on the query torus. It is a simple table baseline, not an equally informed Fourier reader. The code's advantage is expected from its correct shared model. There is no claim of beating arbitrary compression, learned decoders or digital registers.

## Sequential reads

The read sequence cycles q=(-0.7,0.9), (-0.2,0.4), (0.3,-0.1), (1.1,-0.6). Four matched constrained drift steps follow every read. Each drift step preserves the **current** moment, including any disturbance produced by reading. There is no restoration from a saved physical state.

| Protocol after 32 reads | Median later weak-response change | IQR |
|---|---:|---:|
| Drift only, no reads | 0.83% | 0.74–1.06% |
| Read only | 93.72% | 87.67–106.61% |
| Read then same sign-reversed pulse | **1.51%** | 1.39–1.63% |

The sign flip requires no decoded answer or stored per-unit state. It uses a second pulse at the same phase. The read-only protocol has 32 pulses and the compensated protocol 64, each with the same amplitude. This is a doubled-pulse-cost comparison, not matched energy. It applies to this four-query cycle, unit radii and instantaneous normalization; there is no test of arbitrary read sequences, finite relaxation, dynamical noise or pulse-timing errors here.

Only calibration answers receive measurement noise. Held-out and sequential evaluation use exact noiseless software observables. The modest drift-only error comes from changing higher moments that contribute to finite-amplitude weak pings.

## Costs and access

Float64 counts exclude Python object overhead and executable/library storage. The comparison is a payload/work accounting, not a measured peak-memory, runtime or energy benchmark.

| Item | Numeric payload or work | Role |
|---|---:|---|
| Per-object first-moment code | 12 real scalars = **96 bytes** | Stored coefficients for weak-response emulation |
| Resident physical phase population | 96 real scalars = **768 bytes** | Still present during every physical simulation |
| Shared wavevectors | 12 int64 values = **96 bytes** | Known mapping from a 2-D query to six group phases |
| Fixed group identity | Supplied by contiguous array layout/query ports | Its semantic assignment is assumed stable; shuffle exposes its importance |
| Calibration observations | 64 queries + 64 scalar answers = **1,536 bytes** | Training data, same for code and table baseline |
| Calibration reset snapshot | 96 phases = **768 bytes per saved state** | Every calibration ping is evaluated from the initial state; hardware reset is not implemented |
| Calibration design matrix | 64x12 float64 = **6,144 bytes** | Temporary fit workspace, plus NumPy/SVD workspace |
| Least-squares fit | Approximately O(P K^2), P=64 and K=12 | One calibration fit |
| Direct response calculation | 96 unit terms per query | Software listener requires per-unit phase changes |
| Weak coded response | Six complex mode terms per query | Known law plus retained coefficients |
| Order-4 response code | 48 real scalars = **384 bytes** | Higher-detail reconstruction reference |
| Order-8 response code | 96 real scalars = **768 bytes** | Same scalar count as the phase list, generally not a unique state encoding |
| Drift constraint values | Two per group, twelve in all | Specify the moment surface; not total controller storage |
| Drift controller result array and driving velocity | **768 bytes each** | Full-population arrays |
| Controller per-group Jacobians | **256 bytes each** | Projection/retraction, plus several 128-byte vectors and linalg temporaries |
| Compensation | One additional same-amplitude pulse per read | Leading disturbance reduction at increased pulse cost |

Thus **8x** is the ratio of per-object phase-list payload to weak-response-code payload. Both require the known query law. For one code the wavevector table adds another 96 bytes, before access/control costs. The physical implementation does not shrink to twelve state variables, and the experiment does not show that its full dynamics can be simulated from those variables.

## Verification and review correction

The independent read-only review reproduced the initial twenty-seed receipt and independently checked every calibration fit, final phase RMS and held-out weak prediction error. It found no mathematical or split-access defect, but identified an ambiguous cost field that counted twelve constraint values as “temporary” state while omitting the controller's other allocations.

That field was renamed and controller/reset/fit allocations were added. A failing cost-accounting test was added first and then passed. The full evaluation was rerun; outcomes are unchanged. The original receipt is retained in [compressed form](results/receipt-before-cost-clarification.json.gz); its uncompressed SHA256 is `f5cab61e02b601dbcae1f682ba9e16ff2aabcd60915950ad9d0f01cd90e492b6`.

The final suite has twenty tests. The full receipt is deterministic in the recorded Python/NumPy environment, and the verifier allows small cross-runtime floating-point roundoff. [REVIEW.md](REVIEW.md) records a minor deferred type-validation limitation.

## What survives

A population can change many internal coordinates while preserving a low-dimensional family of useful responses. Here that family can be estimated through noisy calibration pings and predicts unseen weak queries. Its boundary is experimentally visible: stronger queries expose higher moments, semantic regrouping breaks the grounded mapping, and reads change the future unless compensated.

The open mechanism question is how to maintain that behavioral family under uncontrolled drift with affordable local observation and correction. The current result supplies a precise target, not the biological or engineering mechanism that achieves it.
