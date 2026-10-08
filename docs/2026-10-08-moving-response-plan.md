# Moving Response Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test compact queryable memory under changing oscillator coordinates, including the failure boundary.

**Architecture:** A small NumPy core implements phase responses, moment codes and constrained drift. A deterministic experiment uses separate random streams, fits a code from calibration pings and writes full receipts. Markdown mathematics and costs explain the assumptions and measured results.

**Tech Stack:** Python 3.10+, NumPy, matplotlib, standard-library unittest; CPU only.

**Spec:** PROTOCOL.md

## Global Constraints

- Only MovingTarget2 is modified; MovingProblem and the other repositories are references.
- Fixed seeds 4100..4119, 64 calibration and 512 held-out query points, six groups of sixteen phases.
- Listener/reset access and shared semantic ports are disclosed.
- No training or parameter selection on held-out queries.
- Failed research gates are results, not code errors.

## Review Focus

- Phase wrapping near +/-pi must not produce false large disturbance.
- A degenerate phase population must preserve its moment or reject a step, rather than silently drift off the constraint.
- Finite-pulse expansion must remain valid only for |a|<1.
- A read must change the current drift constraint, rather than have its damage erased by an old target.
- Fitted-code inputs must exclude held-out answers and hidden phase coordinates.

### Task 1: Core equations and drift

**Files:** moving_target.py; tests/test_math.py; tests/test_drift.py.

**Interfaces:** exact_response(phases, wavevectors, queries, amplitude); phase_moments(phases, order); coded_response(code, wavevectors, queries, amplitude); fit_code(wavevectors, queries, answers, amplitude, order); drift_step(phases, velocity, step); apply_ping(phases, wavevectors, query, amplitude).

- [ ] Write failing tests for a hand-computed phase jump, power-series tail bound, equal first moments with different strong answers, noisy held-out response fitting, and mean preservation under nonzero phase motion.
- [ ] Run `python -m unittest discover -s tests -v` and confirm missing core fails.
- [ ] Implement the equations and numerical constraint retraction, plus input validation.
- [ ] Run the suite, verify preservation/current-target behavior, commit.

### Task 2: Frozen experiment

**Files:** experiment.py; tests/test_experiment.py; results/receipt.json; results/response_drift.svg.

**Interfaces:** run_seed(seed, config) returns JSON-safe per-seed metrics; run_experiment(config) returns protocol/configuration and every seed's receipt; CLI writes receipts and figure.

- [ ] Write failing integration tests for deterministic reruns, disjoint calibration/held-out points, explicit oracle-vs-fit methods, and actual sequential read damage.
- [ ] Implement split random streams, held-out comparisons, cost accounting and fixed gate evaluation.
- [ ] Run the suite and one-seed smoke check, commit.
- [ ] Run all 20 fixed seeds. Retain every result; do not modify the research thresholds.

### Task 3: Explain, review and publish

**Files:** README.md; MATH.md; RESULTS.md; PAPERS.md; .github/workflows/tests.yml.

- [ ] Write the result around the measured behavior and limits, with mathematical derivation and complete cost table.
- [ ] Review the whole implementation and data access against PROTOCOL.md; fix material issues with failing tests first.
- [ ] Run the whole suite and deterministic receipt reproduction; validate generated figure.
- [ ] Publish the verified files to MovingTarget2 with a branch-head lease; fetch the remote head and files to verify them.
