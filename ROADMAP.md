# Bonobo Roadmap

## Phase 1 — Canonical Core and Runtime Foundations (Established / Retained)
- `StructuralGraph` as canonical state container
- grammar rule proposal and application loop
- evaluator pipeline with channel contracts
- experiment harness, run logging, and viewer/debug tooling
- basic semantic tests around loads, `temp_force`, reactions, grammar, and evaluator flow

## Phase 2 — Vector GS Kernel MVP (Current)
- treat `vector_gs_kernel_v1` as the active technical nucleus
- prioritize semantically rich vector-GS growth over broad runtime polish
- preserve seeded reproducibility, interpretable traces, and inspectable artifacts
- validate a compact kernel benchmark/problem family before reintegration
- keep the layered Bonobo runtime intact as the long-term target rather than replacing it

## Phase 3 — Kernel Experiment Harness and Paper Study (Immediate Next)
- define the conference-paper-oriented experiment surface for the kernel
- compare simple policies such as random, weighted random, and lightweight heuristics where justified
- stabilize artifact schemas, metrics, and viewer support for kernel runs
- produce figures and summaries that show sequential growth, alternatives, and conservative performance comparisons

## Phase 4 — Adapter-Based Reintegration (Later)
- build adapters from kernel `Assembly` concepts into `StructuralGraph`
- map kernel rule traces into Bonobo grammar and experiment concepts where appropriate
- reuse evaluator and experiment infrastructure without collapsing the architecture into the kernel
- keep reintegration incremental and test-backed

## Phase 5 — Domain-Aware Spatial Structures (Later)
- support bounded-volume and curved-surface conformance
- extend beyond the first planar kernel problems only after the generator core is credible
- treat broader domain adaptation as a later extension, not an MVP promise

## Phase 6 — Guidance Layer and Learning (Later)
- add learned components only as a guidance layer over a credible generator
- keep ML downstream of interpretable artifacts, formal problem specs, and semantic labels
- use learned components first for suggestion, ranking, or comparison support
- reinforcement learning is not the next coding step

## Phase 7 — Construction-Aware Growth (Later)
- investigate staged stability and scaffold-free growth only after generator and reintegration work are credible
- add fabrication-aware and assembly-aware constraints where technically justified
- keep these ambitions separate from the current kernel MVP claim
