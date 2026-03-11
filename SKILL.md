# SKILL.md — Bonobo Structural Semantics

## Project Identity
Bonobo is a layered structural generation engine for interpretable, equilibrium-informed growth.

## Canonical Layers
1. Canonical Graph
2. Grammar (state transitions and local growth actions)
3. Evaluator (structural signals and validity semantics)
4. Experiment Harness (benchmark scenarios, traces, descriptors, summaries, derived exports)

Diversity, search, and learning remain downstream of benchmark validation.

## Core Meanings
- `loadcases`: external applied loads.
- `temp_force`: currently an unresolved nodal imbalance used in growth and debug workflows.
- `fixed = [ux, uy, uz]`: support restraint mask (`1` restrained, `0` free).
- Reactions in the current pipeline: evaluator-derived constrained components absorbed from `temp_force` at fixed DOF.

## Invariants
- `StructuralGraph` is the canonical state container.
- Grammar rules expose `propose()` and `apply()`.
- Evaluator channels return:
  `{ "valid": bool, "metrics": dict, "signals": dict }`.
- Explicit signed axial member-force storage is not a stable invariant unless explicitly implemented.
- Derived arrays and descriptors are exports, not the canonical internal representation.

## Current Benchmark Stance
- The immediate research step is to test benchmarked equilibrium-informed growth on a Michell-style planar problem.
- The project is currently evaluating whether external equilibrium scaffolds and support-seeking growth should be made more explicit.
- Do not describe those mechanisms as already implemented unless the code actually contains them.

## Visualization Semantics
- Centralized symbol generation lives in `bonobo/visual/symbols.py`.
- Viewer overlays are interpretive and may expose benchmark traces or evaluator outputs, but they do not define core semantics.

## Stability Rule
Preserve semantic stability first. Avoid redefining loads, `temp_force`, supports, reactions, evaluator contracts, or benchmark meanings during routine implementation unless the user explicitly requests that change.
