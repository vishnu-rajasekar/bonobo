# PROJECT_EVOLUTION

## Purpose
This document preserves the short historical arc of Bonobo so older notes do not need to remain active sources of truth.

## 1. Initial Aims
Bonobo began as a broad structural generation research project with ambitions around:
- transtypological structural morphology
- graphic statics as the analysis engine
- feasibility goals such as material reduction and scaffold-free construction
- eventual learned guidance, including RL and graph-based models

Early notes also framed the project as part of a larger building-science ecosystem and explored a wide set of structural typologies from the start.

## 2. Architectural Clarification
The project gradually converged on a cleaner layered model:
- canonical structural state in `StructuralGraph`
- grammar for local generative moves
- evaluator for structural signals and diagnostics
- experiment harness for benchmark scenarios, traceability, and derived exports

This was an important shift away from loosely coupled exploratory scripts toward an auditable engine structure.

## 3. Benchmark-First Shift
As the project matured, the emphasis moved away from vague exploratory growth toward disciplined benchmark validation.

The Michell-style planar benchmark became:
- a proving ground
- a regression check
- a way to test admissible intermediate states and equilibrium-related progress

It also became clear that the benchmark should validate the architecture rather than define it.

## 4. Current Refactor Phase
The current phase introduced two major clarifications:
- abstract grammar rule vocabulary was frozen
- runtime behavior was aligned around `GrammarAction` and provisional vector-GS realizations

This clarified that:
- grammar rules are the action language
- vector GS is the current realization backend
- many legacy `*_rule.py` files are really operators or strategy shims
- policy-facing observation and reward interfaces should remain derived rather than canonical

## 5. Future Direction
The intended next direction is:
- strengthen semantic clarity and runtime alignment
- add non-learning policy baselines over `GrammarAction`
- keep RL as a later step, not an immediate coding target
- leave room for future GS backends such as polyhedral or Airy / stress-based methods

The project therefore remains benchmark-disciplined, architecture-first, and intentionally extensible.
