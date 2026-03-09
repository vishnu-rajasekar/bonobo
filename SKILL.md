# SKILL.md — Bonobo Structural Semantics

## Project Identity
Bonobo is a layered structural generation engine.

## Canonical Layers
1. Canonical Graph
2. Grammar (state transitions)
3. Evaluator (physics semantics)
4. Learning (policy over grammar)

Diversity and goal steering operate above evaluator.

## Core Meanings
- `loadcases`: external applied loads.
- `temp_force`: unresolved nodal imbalance used during growth/debug workflows.
- `fixed = [ux, uy, uz]`: support restraint mask (`1` restrained, `0` free).
- Reactions (current pipeline): constrained components absorbed from `temp_force` at fixed DOF.

## Invariants
- `StructuralGraph` is the canonical state container.
- Grammar rules must expose `propose()` and `apply()`.
- Evaluator channels must return:
  `{ "valid": bool, "metrics": dict, "signals": dict }`.
- Explicit signed axial member-force storage is **not** a stable invariant unless explicitly implemented.

## Visualization Semantics
- Centralized symbol generation lives in `bonobo/visual/symbols.py`.
- Keep symbol/color semantics stable unless explicitly changed by instruction.

## Stability Rule
Preserve semantic stability first; avoid redefining meanings of loads, `temp_force`, supports, reactions, or channel contracts during routine implementation.
