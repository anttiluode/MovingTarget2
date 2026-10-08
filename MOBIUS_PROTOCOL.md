# Möbius pings: frozen addendum

Frozen 2026-10-08, before the runner was written and before any outcome on seeds 4100–4119. The original protocol, receipt and gates are untouched.

Disclosure: the predictions below were motivated by short exploratory checks on separate random populations (uniform phases, a different random generator, 4–96 oscillators). Those checks did not use the protocol's seeds, initial states, queries or drift, and their numbers are not reported as results.

## Question

The frozen read law adds a complex pulse and renormalizes each unit. To first order in the amplitude a it equals the flow

dθ/dt = sin(φ − θ),

run for time a. That flow, for any a, is an exact Möbius transformation of the circle. Möbius maps of the circle form a three-parameter group (Watanabe & Strogatz 1993–94; Marvel, Mirollo & Strogatz 2009). Identical oscillators driven by such common pings keep N − 3 cross-ratios per group fixed.

1. Is the frozen compensation residual (1.51% versus 0.83% drift only) caused by the frozen law lacking an exact same-port inverse?
2. Can an observer that tracks three real numbers per group, without phase access, undo any number of reads with a fixed small number of correction pulses?
3. Are the cross-ratios invariant under Möbius reads, eroded by frozen-law reads, and rewritten by the frozen constrained drift?
4. Does a second harmonic added to the ping write the cross-ratios in proportion to its size?
5. Illustrations: does the order of two pings leave a common rotation a² sin(φ₂ − φ₁), and does a closed loop of pings leave a rotation equal to its enclosed area?

## What changes

Only the read law. The new law, `mobius`, is the exact time-a flow:

θ' = φ + 2 atan( tan((θ − φ)/2) · e^(−a) ), wrapped to [−π, π).

Initial states, held-out queries, wavevectors, the four sequential read queries, drift random streams and amplitudes (weak 0.05, strong 0.6) are the frozen ones. The listener is unchanged: the frozen software listener, i.e. mean phase advance under the frozen law at the probe amplitude. Changing how reads act does not change the measuring apparatus. Listener-free metrics are also reported: RMS wrapped phase error per state.

## Experiments

**M1. Frozen sequential protocol, law swapped.** Thirty-two reads cycling the four frozen queries at a = 0.05, four constrained drift steps after each read, the frozen drift velocities. Read only, read then the same pulse with reversed sign, and drift only, under each law.

**M2. Read burst with corrections.** Thirty-two reads cycling the same four queries, no drift between reads, at a = 0.05 (primary) and a = 0.25 (secondary). Corrections:

- none;
- frozen law, the same sign-reversed pulse after every read (64 pulses);
- frozen law, the best single Möbius map per group, fitted to the hidden initial phases (oracle; an upper bound for any one-map corrector);
- frozen law, the best three frozen-law pulses per group, fitted to the hidden initial phases (oracle);
- Möbius law with an odometer: the observer knows the query sequence and amplitude, never reads phases, multiplies one 2×2 SU(1,1) matrix per group (three real numbers each, 18 in all), then applies at most three per-group correction pulses solved from the inverse.

**M3. Constellation.** For each group, cross-ratios X_j = CR(z₀, z₁, z₂, z_j), j = 3…15: 78 numbers in all. Change is |atan X' − atan X|, which is bounded and scale-free. Measured after the M2 bursts under each law, and after the frozen 128-step constrained drift without reads.

**M4. Harmonic routing.** Ping flow dθ/dt = sin(φ − θ) + ε sin(2(φ − θ)), integrated with fourth-order Runge–Kutta, 64 substeps per pulse, ε ∈ {0, 10⁻⁴, 10⁻³, 10⁻², 10⁻¹}. Thirty-two burst reads at a = 0.05. Constellation change versus ε.

**M5. Order and loops.** For every seed and group at a = 0.05: two pings at φ₁ and φ₂ = φ₁ + Δ, Δ ∈ {π/6, π/2, 5π/6}, φ₁ the group's mean phase, applied in both orders; and the loop +a at φ₁, +a at φ₂, −a at φ₁, −a at φ₂. Compare the common rotation with a² sin(φ₂ − φ₁), and the non-uniform part with the common part.

## Gates

**G1.** Under the Möbius law, the M1 compensated state equals the drift-only state: maximum over seeds and reads of RMS phase difference < 10⁻⁹. Under the frozen law, M1 reproduces the frozen receipt's three sequential medians within 10⁻⁹ (harness check).

**G2.** M2 odometer at a = 0.05: maximum over seeds of final RMS phase error < 10⁻⁹, with at most three correction pulses per group, 18 real numbers of observer state and no phase access.

**G3.** M2 frozen law at a = 0.05: median RMS phase error > 10⁻⁶ after each of the per-read sign flip, the oracle best Möbius map and the oracle best three frozen-law pulses.

**G4.** M3: Möbius burst maximum constellation change < 10⁻⁹; frozen-law burst median > 10⁻⁶; frozen constrained drift median > 10⁻².

**G5.** M4: constellation change at ε = 0 below 10⁻⁹, and log–log slope of median change against ε over 10⁻⁴…10⁻¹ within [0.9, 1.1].

**G6.** M5: median relative error of the common rotation against a² sin(φ₂ − φ₁) < 2% for both the swapped pair and the loop; median ratio of non-uniform spread to common rotation < 5%.

No threshold, seed, amplitude or query change after outcomes. Implementation bugs found after outcomes get a dated note and a rerun, and the first receipt is kept.

## What a pass would and would not mean

A pass would show that, for identical oscillators with first-harmonic pings, reads have an exact group structure that the frozen law shares only to first order. Read damage then lives in three numbers per group and can be removed without phase access, while the cross-ratios form a memory that such pings cannot write.

It would not show biological plausibility, robustness to non-identical oscillators or noise, or a working odometer when uncontrolled drift is interleaved with reads. Drift does not commute with reads; that case is reported descriptively, not gated. Per-group correction pulses are a stronger access port than the frozen query port, and the odometer must know the read sequence and amplitude. Both are stated as costs.
