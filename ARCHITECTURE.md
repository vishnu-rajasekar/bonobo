# ARCHITECTURE.md — Bonobo

## Project Framing
Bonobo is a layered structural generation engine for sequential, equilibrium-informed growth. The architecture is deliberately split so that structural semantics, growth actions, evaluator signals, and benchmark orchestration remain separable and inspectable.

## Canonical Layers
1. `StructuralGraph`
   - Canonical structural state
   - Loads, supports, `temp_force`, metadata, and serialization live here
2. Grammar
   - Local growth actions and state transitions
   - Proposes and applies admissible graph transformations
3. Evaluator
   - Computes structural signals, validity, and benchmark-facing metrics
   - Must remain separate from grammar logic
4. Experiment Harness
   - Scenario definition
   - Benchmark acceptance policies
   - Trace logging, descriptors, summaries, and derived ML exports

## Layer Responsibilities
- Equilibrium should guide growth through evaluator-derived signals and experiment-layer benchmark acceptance, not by collapsing evaluator semantics into grammar rules.
- Visualization is interpretive only. It may expose traces, labels, and diagnostics, but it is not a source of canonical semantics.
- Diversity, search, and learning are downstream of benchmark validation. They should not drive architectural decisions before the benchmark contract is credible.
- Derived array exports belong in the experiment layer or dedicated descriptor utilities, not in `StructuralGraph` as the internal representation.

## Core Semantic Zones (High-Risk)
- `morph_engine/morph_engine/model`
- `morph_engine/morph_engine/grammar`
- `morph_engine/morph_engine/evaluator`

Changes in these zones affect canonical behavior and must be minimal, explicit, and test-backed.

## Experiment / Interpretation Zones
- `morph_engine/morph_engine/experiments`
- `bonobo/visual/`
- `scripts/run_experiment.py`
- `scripts/view_last_run.py`

These are the correct places for benchmark scenarios, acceptance criteria, traceability tooling, descriptors, derived exports, and interpretive rendering.

## Integration-Only Zone
- `morph-rhino-mcp/`

Treat as integration code. Do not mix it into unit-test-only flows or core semantic contracts.

## Environment Assumptions
- Python 3.10
- Conda env: `morph-engine`
- Dependency versions remain pinned unless explicitly changed

## Editing Posture by Task Type
- Bug fix: smallest localized patch in the zone where failure originates
- Feature work: bounded module scope, avoid semantic drift
- Documentation update: clarify current state, immediate benchmark target, and later ambitions without overstating implementation
- Architecture change: requires explicit approval before implementation
