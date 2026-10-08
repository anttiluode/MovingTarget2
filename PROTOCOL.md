# MovingTarget2: fixed behavior, moving coordinates

Frozen before implementation or outcome measurement, 2026-10-08.

## Question and scope

Can a population keep answering new pings while its individual phase coordinates change? Can a small, measurable response code predict those answers? Where does that code stop being sufficient?

This is a synthetic oscillator experiment, not a model fitted to neural recordings. Group membership and query ports are fixed and known. The drift generator deliberately preserves one complex phase moment in each group; discovering such preservation in biology is outside this experiment. The experiment tests the consequences and limitations of that constraint, not whether it arises naturally.

## Model

Six groups, sixteen unit-amplitude oscillators per group: 96 phase coordinates. Query points q are in [-pi, pi]^2. Group wavevectors are (1,0), (0,1), (1,1), (1,-1), (2,1), (1,2). A group receives the same complex additive pulse a exp(i k_g.q). After radial normalization, each unit advances by arg(1 + a exp(i(k_g.q - theta_gu))). The software listener reports the mean phase advance over all units. This assumes access to individual phase advances; it is not a demonstrated single-wire listener.

The first-moment code is m_g = mean_u exp(-i theta_gu): 12 real numbers. The exact finite-pulse answer has a convergent expansion in the higher moments m_gl = mean_u exp(-i l theta_gu). Order L stores 12L real numbers. We compare orders 1, 2, 4 and 8.

One drift step projects a fresh random phase velocity into the nullspace of the two first-moment constraints in each group, then retracts numerically onto the same constraint surface. The target is the **current** moment before that step. After a read it does not reset to the pre-read memory. Default phase step: 0.06 radians RMS before constraint projection. Sixteen checkpoints, eight steps per checkpoint.

## Splits and access

- Full evaluation seeds: 4100 through 4119, all reported; no seed selection.
- Per seed: 64 calibration queries, 512 independent held-out queries. Random streams for initialization, queries, drift, readout noise and sequential reads are separate.
- First-moment fitting uses only the calibration points and noisy software-listener answers at a=0.05. Noise standard deviation is 0.005 in answer/a units. No phase coordinates or held-out answers enter this fit.
- Calibration pings use fresh copies of the same initial state. This is a counterfactual measurement protocol with reset access, not free repeated interrogation of one physical memory.
- Exact moment codes are oracle references computed from the phases, clearly separated from fitted codes.
- A nearest-query table stores the same 64 measured answers and their 2-D query locations. A zero-answer baseline is also reported.
- Object state is fixed during each run. Individual angles move. Query points, wavevectors, fitting procedure and pulse strengths are fixed before results.

## Comparisons

1. Constrained drift vs unrestricted drift, using matched initial states and driving velocities.
2. Frozen fitted order-1 code, frozen exact codes, and current exact codes, evaluated on unseen queries. The current code is a reconstruction reference, not preservation of the initial object.
3. Weak a=0.05, intermediate a=0.25, strong a=0.6 probes. Listening is evaluated on copies; these comparisons do not accumulate read damage.
4. A shuffle of units across groups preserves the global phase multiset but breaks the semantic assignment to query ports. This tests whether one global average is sufficient.
5. Thirty-two actual reads at a=0.05, cycling four fixed query points. Compare read only, read followed by the same sign-reversed pulse, and drift without reads. Four constrained drift steps follow each read. No exact state copy is restored in this sequential experiment.

## Gates fixed in advance

H1 — Genuine coordinate motion under the constraint: median final wrapped phase RMS change >= 0.35 rad, and maximum first-moment change over runs/checkpoints < 1e-8.

H2 — Held-out compact prediction: median NRMSE of the frozen fitted 12-number code on final weak-ping answers <= 0.06, with at least 15/20 seeds <= 0.08. NRMSE = RMSE / RMS(initial held-out response), with no centering. Eightfold per-object scalar reduction is a storage count, not an empirical discovery.

H3 — Boundary of the weak equivalence: median strong-probe response drift is >= 2 times weak-probe drift; a current exact order-4 code reduces strong-probe reconstruction NRMSE by >= 3 times relative to current order 1. A failure is retained.

H4 — Semantic grouping matters: median weak response change after cross-group shuffling >= 0.4 NRMSE and >= 5 times the constrained-drift value.

H5 — Repeated reads, secondary: the sign-reversed pulse reduces median final weak-response change by >= 2 times relative to read only. This does not require exact phase restoration.

No improvement of failed gates by changing seeds, drift strength, budgets, pulse strengths or thresholds after measuring them. Corrections to implementation bugs require a dated explanation and rerun, retaining the initial receipt if outcomes were already produced.

## Accounting and interpretation

Report all seeds, per-seed metrics, across-seed median and interquartile range, numerical constraint errors, phase drift, held-out prediction, stronger-probe failure, sequential read damage, and shared/per-object/calibration/work costs. Do not count the population's own physical state as eliminated merely because its responses have a smaller code.

The shared wavevector table, known response law, fixed group identity, calibration/reset access, and software phase listener are assumptions. A twelve-number code is plausible here because weak response is first-order in six known modes. This establishes a bounded behavioral equivalence, not a new storage law, brain theory, learned arbitrary object manifold, or hardware advantage.
