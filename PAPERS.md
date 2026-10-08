# Sources and ancestry

The mathematics of moment expansions, behavioral equivalence, constrained level surfaces and representational drift is established. This repository applies those ideas to a specific ping-query model and measures its limits.

## Primary research

| Source | Relevant finding | Boundary for MovingTarget2 |
|---|---|---|
| Rule & O'Leary (2022), [Self-healing codes](https://www.pnas.org/doi/10.1073/pnas.2106692119), PNAS 119(7), e2106692119 | Model mechanisms using Hebbian and homeostatic plasticity can stabilize readouts of changing population codes. | That is a mechanism for tracking drift. Our constrained drift is an intervention, not a replication of their learning rule. |
| Keinath, Mosser & Brandon (2022), [The representation of context in mouse hippocampus is preserved despite neural drift](https://www.nature.com/articles/s41467-022-30198-7), Nature Communications 13, 2415; [accessible abstract](https://pubmed.ncbi.nlm.nih.gov/35504915/) | In the studied CA1 recordings, population change was largely orthogonal to contextual representation, supporting consistent context readout across weeks. | A particular preserved contextual variable does not imply every object or future query is preserved. |
| Naumann, Keijser & Sprekeler (2022), [Invariant neural subspaces maintained by feedback modulation](https://elifesciences.org/articles/76096), eLife 11, e76096 | Feedback modulation reorients population activity to maintain an invariant task-relevant subspace across contexts. | Our fixed response moments and known query ports are supplied rather than learned by a modulator. |
| [Stiefel Manifold Dynamical Systems for Tracking Representational Drift](https://pubmed.ncbi.nlm.nih.gov/41959124/) (2026) | A state-space model explicitly treats evolving neural representations. | Coordinate tracking and compact query sufficiency are related questions, not the same experiment. |

The logarithmic expansion in MATH.md is derived directly. Its power-series identity and geometric remainder estimate are standard algebra/analysis; no new theorem about biological memory is claimed.

## Project genealogy

| Project | What carries forward |
|---|---|
| [MovingProblem](https://github.com/anttiluode/MovingProblem) | Separate invariant computation from named/oriented meaning; count alignment and semantic grounding. Its Gate 4 remains frozen. |
| [Kompressori](https://github.com/anttiluode/Kompressori) | Ask what past state changes about a future response operator. |
| [VMN](https://github.com/anttiluode/VMN) | Distinguish a retained state code from a fixed response matrix, and test query damage plus compensation. |
| [VMNClaude](https://github.com/anttiluode/VMNClaude) | A compressed answer can omit details needed for undo; observation access and transient timing must be counted. |
| [OpusPing](https://github.com/anttiluode/OpusPing) | Sender event and receiver state can jointly determine a lasting response change in an explicitly mechanistic synaptic model. |
| MovingTarget2 | Define the remembered object through a family of new query responses, then test how much coordinate change that definition tolerates. |

Antti supplied the motivating image: a small state-carrying ping meeting machinery already shaped by previous events, and an object persisting while that machinery changes. The code and analysis here are Sol/Codex's synthetic test of one precise version of that image.
