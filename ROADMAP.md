# Bonobo Roadmap

## Phase 1 — Canonical Core (Established)
- `StructuralGraph` as canonical state container
- grammar rule proposal and application loop
- evaluator pipeline with channel contracts
- experiment harness, run logging, and viewer/debug tooling
- basic semantic tests around loads, `temp_force`, reactions, grammar, and evaluator flow

## Phase 2 — Benchmarked Equilibrium Growth (Current)
- freeze the semantic contract enough for a defensible benchmark
- validate a Michell-style 2D planar benchmark before expanding scope
- require benchmark traces, descriptors, summaries, and acceptance criteria
- test whether support-seeking growth and external equilibrium scaffolds should be made more explicit
- assess admissibility of intermediate states, not only final residuals
- treat material efficiency as the first benchmark performance target

## Phase 3 — Goal Steering and Diversity
- introduce explicit multi-objective scoring over valid benchmark outcomes
- extend descriptors to compare typology and static-scheme variation
- compare multiple valid solutions for the same boundary/load problem
- keep diversity as a measured downstream objective, not a substitute for benchmark grounding

## Phase 4 — Construction-Aware and Domain-Aware Growth
- support bounded-volume and curved-surface conformance
- evaluate staged stability and scaffold-free growth criteria
- add fabrication-aware and assembly-aware constraints where technically justified
- extend beyond the first planar benchmark only after the benchmark contract is credible

## Phase 5 — Learned Guidance and Repertoire Mapping
- add graph encoders over benchmarked state/action traces
- use learned components first as policy suggestion or ranking support
- build archive or latent-space memory only if benchmark evidence justifies it
- consider reinforcement learning later, not as an immediate priority
