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

## Memory, multilingual representations and architecture

These sources motivate the [memory-worlds research guide](docs/memory-worlds-and-languages.md). They are external results, not experiments reproduced in MovingTarget2.

| Source | Relevant finding | Boundary for this project |
|---|---|---|
| Horner et al. (2015), [Evidence for holistic episodic recollection via hippocampal pattern completion](https://www.nature.com/articles/ncomms8462), Nature Communications 6, 7462 | In a human associative-memory task, recall reinstated an additional event element; the amount of reinstatement was associated with hippocampal activity. | Evidence for cue-driven event retrieval, not literal nested rooms or a complete account of memory. |
| Davidson, Kloosterman & Wilson (2009), [Hippocampal replay of extended experience](https://pmc.ncbi.nlm.nih.gov/articles/PMC4364032/), Neuron 63(4), 497–507 | Rat hippocampal activity replayed extended spatial sequences in forward and reverse order during pauses. | Internal replay order is different from physical time's direction. |
| Lindsey et al. / Anthropic (2025), [On the Biology of a Large Language Model](https://transformer-circuits.pub/2025/attribution-graphs/biology.html) | Claude 3.5 Haiku combined shared multilingual features with language-specific circuits. Translated-paragraph feature overlap was greater in intermediate layers and greater than in a smaller model. | Partial shared computation in studied models and prompts; no universal language-free tensor or demonstrated Finnish result. |
| Wendler et al. (2024), [Do Llamas Work in English?](https://aclanthology.org/2024.acl-long.820/), ACL | Selected Llama-2 next-token tasks showed intermediate representations biased toward English before language-specific output. | A scoped result about Llama-2 and the tested tasks, not an architecture law for all multilingual models. |
| Beniwal, D & Singh (2024), [Cross-lingual Editing in Multilingual Language Models](https://aclanthology.org/2024.findings-eacl.140/), Findings of EACL | Edits in one language had limited propagation to others in BLOOM, mBERT and XLM-RoBERTa, particularly across the tested script families. | Behavioral non-transfer does not uniquely identify where a fact is stored internally. |
| Rae et al. (2019/ICLR 2020), [Compressive Transformers for Long-Range Sequence Modelling](https://arxiv.org/abs/1911.05507) | An attention model retains compressed older activations as long-range memory. | Compression of older context is established prior art. Repeated compression alone is not a novelty claim. |
| Zhang et al. (2025), [Frame Context Packing and Drift Prevention in Next-Frame-Prediction Video Diffusion Models](https://proceedings.neurips.cc/paper_files/paper/2025/hash/2bde8fef08f7ebe42b584266cbcfc909-Abstract-Conference.html), NeurIPS | Importance-based packing holds video context length fixed, with more capacity for important frames; separate methods address generation drift. | Compression can depend on importance rather than age alone. It does not validate a brain-memory model. |
| Su et al. (2021; revised 2023), [RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/abs/2104.09864) | RoPE rotates attention queries and keys according to token position. | Positional rotations do not repair changes caused by fine-tuning a model's learned representations. |

## Project genealogy

| Project | What carries forward |
|---|---|
| [MovingProblem](https://github.com/anttiluode/MovingProblem) | Separate invariant computation from named/oriented meaning; count alignment and semantic grounding. Its Gate 4 remains frozen. |
| [Kompressori](https://github.com/anttiluode/Kompressori) | Ask what past state changes about a future response operator. |
| [VMN](https://github.com/anttiluode/VMN) | Distinguish a retained state code from a fixed response matrix, and test query damage plus compensation. |
| [VMNClaude](https://github.com/anttiluode/VMNClaude) | A compressed answer can omit details needed for undo; observation access and transient timing must be counted. |
| [OpusPing](https://github.com/anttiluode/OpusPing) | Sender event and receiver state can jointly determine a lasting response change in an explicitly mechanistic synaptic model. |
| [AnttisBrain2](https://github.com/anttiluode/AnttisBrain2) | Rooms, moving moons and recursive reflections supplied a geometric language for frames, fading context and selective retrieval. A reflection must contain a recorded earlier state to serve as temporal memory. |
| MovingTarget2 | Define the remembered object through a family of new query responses, then test how much coordinate change that definition tolerates. |

Antti supplied the motivating image: a small state-carrying ping meeting machinery already shaped by previous events, and an object persisting while that machinery changes. The code and analysis here are Sol/Codex's synthetic test of one precise version of that image.
