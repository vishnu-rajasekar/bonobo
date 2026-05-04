# Paper Experiment Plan V1

## Purpose
Define a conservative, conference-paper-oriented experiment plan for evaluating the active vector GS kernel MVP without overstating current implementation maturity.

## Research Claim
The intended near-term claim is that a semantically rich vector graphic statics generator can produce interpretable sequential structural growth under bounded problem definitions, while preserving machine-readable traces and supporting comparison across simple seeded policies.

This is not yet a claim of:
- general structural design automation
- broad typological coverage
- learned guidance superiority
- full equilibrium closure across all cases

## MVP Scope
The MVP scope is:
- `vector_gs_kernel_v1` as the active generator
- seeded repeated runs
- compact benchmark/problem definitions
- interpretable traces and final assemblies
- conservative quantitative comparison across a small policy set

The MVP does not require:
- full reintegration into the layered Bonobo runtime
- large-scale benchmark suites
- advanced search or reinforcement learning

## Benchmarks
Use a small problem family only.

Minimum expected benchmark surface:
- a cantilever-like planar load/support case
- one or two nearby variations only if they remain directly comparable

Benchmarks should remain:
- small
- reproducible
- visually inspectable
- sufficient to reveal structural growth behavior

## Policies to Compare
Primary comparison set:
- random
- weighted random
- greedy/heuristic if present or added in a lightweight form

If Q-learning or related methods are not already implemented for the kernel, they should not be included in the paper MVP comparison.

## Metrics
Prefer lightweight, interpretable metrics:
- completion rate
- accepted step count
- material proxy
- residual or equilibrium-related measure
- support connectivity
- final node count
- final member count
- max and mean valence
- member length statistics
- diversity proxy across generated alternatives

If a metric is provisional, that should be stated directly in reporting.

## Artifact Requirements
Each run should preserve at least:
- seed
- problem id
- policy id
- step trace
- accepted and rejected rule information if available
- final assembly
- final metrics

The artifact shape should remain stable enough for repeatable analysis and figure generation.

## Paper Figures
Expected figure classes:
- sequential growth trace
- representative rule examples
- policy comparison summary
- multiple design alternatives for the same problem
- boundary or keep-out adaptation examples if available and already implemented

## Success Criteria
The paper-facing MVP is successful if it shows:
- reproducible seeded generation
- interpretable sequential structural growth
- nontrivial structural alternatives
- consistent artifact capture
- conservative quantitative comparison across simple policies

## Explicit Non-Claims
This paper-stage MVP should not claim:
- full structural optimality
- universal equilibrium closure
- broad typology completeness
- construction staging intelligence
- learned policy superiority
- general-purpose architectural design synthesis
