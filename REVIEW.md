# Review and verification record

2026-10-08. An independent read-only agent reviewed the core implementation against PROTOCOL.md, ran the eighteen tests then present, reproduced the full twenty-seed receipt, and checked stored calibration fits and final held-out metrics independently. It also tested coherent, antipodal and nearly coherent phase populations.

The reviewer found no critical issue and one important issue: the controller cost entry could be mistaken for total temporary storage. That entry now specifies only constraint values, with separate result-array, velocity, Jacobian, reset snapshot and fit-work entries. The cost regression test was observed failing before the correction, then the whole twenty-test suite passed. An additional analytic test demonstrates that equal first moments do not determine the next first moment after a read.

The raw first outcome receipt is retained as `results/receipt-before-cost-clarification.json.gz`. The accounting correction did not alter the research thresholds, data splits, seeds, dynamics or numerical outcomes. Its rerun is the canonical `results/receipt.json`.

## Deferred minor

The verifier compares keys and values with numerical tolerance but does not strictly distinguish JSON booleans from equivalent numbers. For example, `true` can compare equal to `1`. The checked-in receipt has valid types and the reviewer reproduced its results; `--verify` is a numerical reproduction check rather than a full schema validator. A strict schema/type validator is deferred.

## Scope rulings

The reviewer explicitly did not judge biological emergence, realizable listener/reset hardware, arbitrary-object compression, optimal code size or arbitrary read sequences. These remain outside this controlled experiment, and README/RESULTS state those limits. Extending a claim to them would require separate evidence.

Pulses with absolute amplitude at least one remain rejected: the supported power-series domain is part of the model and tested. Documents, citations, CI and publication were checked by the main agent after the code review. Reproduction was independently verified only in the available Python 3.12/NumPy 2.3.5 environment; CI is configured to check that environment family rather than assert universal cross-runtime determinism.
