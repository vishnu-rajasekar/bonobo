# SKILL.md — Bonobo Working Vocabulary And Refactor Skills

## Project Identity
Bonobo is a layered structural generation engine for interpretable, equilibrium-informed growth.

## Working Vocabulary
- `state`: canonical structural state held in `StructuralGraph`
- `abstract rule`: one of the frozen grammar intents such as `ExtendNode` or `CloseStructure`
- `operator` / `transformation`: method-specific GS logic used to realize an abstract rule
- `action`: one concrete applicable grammar action, represented by `GrammarAction`
- `observation`: policy-facing derived state view
- `reward spec`: policy-facing goal and constraint schema
- `policy`: selector over admissible grammar actions
- `episode`: one full run
- `step`: one accepted action
- `abstract rule vs method-specific realization`: the grammar intent is stable; the `vector_gs` realization is current and provisional

## Canonical Layers
1. Canonical Graph
2. Structural Semantic Views / Semantics Layer
3. Abstract Grammar Rules
4. GS Method-Specific Realization (`vector_gs` now; polyhedral / Airy later)
5. Evaluator (structural signals and validity semantics)
6. Policy / Guidance Layer
7. Experiment Harness (benchmark scenarios, traces, descriptors, summaries, derived exports)

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

## Current Stable Interfaces
- Frozen abstract grammar vocabulary:
  - `StartGeneration`
  - `CreateNode`
  - `ExtendNode`
  - `SplitNode`
  - `ConnectTwoNodes`
  - `ExtendAndConnectTwoNodes`
  - `CloseStructure`
  - `EndGeneration`
- `GrammarAction` is the policy-facing action container.
- Policy observation schema is frozen as a derived view.
- Reward schema is frozen as a policy-facing specification, not a final optimization theory.
- `vector_gs` registry and runtime bindings exist, but current mappings are provisional compatibility mappings.

## Current Benchmark Stance
- The immediate research step is to test benchmarked equilibrium-informed growth on a Michell-style planar problem.
- The project is currently evaluating whether external equilibrium scaffolds and support-seeking growth should be made more explicit.
- Do not describe those mechanisms as already implemented unless the code actually contains them.
- The benchmark is a validator and regression check, not the definition of the grammar or the final policy action space.

## Refactor Priorities
1. runtime / action-language alignment
2. semantic deepening without breaking layer boundaries
3. policy baselines over grammar actions
4. later RL or other learning-based guidance
5. later alternative GS backends

## Safe Refactor Patterns
- add an adapter rather than rewrite a working runtime path
- mark provisional mappings explicitly
- move GS logic into the operator layer
- preserve benchmark behavior where practical while improving architecture
- add focused interface tests when touching runtime action paths
- keep docs concise and update them when interfaces change

## Anti-Patterns
- adding new benchmark-only grammar rules casually
- equating current implementation file names with final abstract architecture
- promoting GS operators into top-level grammar rules
- letting benchmark quirks define long-term interfaces
- mixing evaluator semantics with grammar generation logic
- introducing hidden secondary canonical states

## Future RL Guidance
- RL is not yet the next coding step.
- Grammar actions are the future policy language.
- State embeddings are future derived observations, not canonical state.
- Variable action sets should be handled through admissible-action enumeration and masks.
- Future guidance work should consume `GrammarAction`, observation extraction, and reward specs rather than inventing a second action language.

## Visualization Semantics
- Centralized symbol generation lives in `bonobo/visual/symbols.py`.
- Viewer overlays are interpretive and may expose benchmark traces or evaluator outputs, but they do not define core semantics.

## Role Of Juney's Code
- Juney's codebase is the main structural reference for vector-GS operator logic and rule philosophy.
- Salvage semantics and operator ideas aggressively.
- Rehouse them inside Bonobo's architecture instead of copying the old runtime object model or Rhino / Grasshopper assumptions.

## How To Use Existing Docs
Consult and keep consistent with:
- `docs/RL_INTERFACE_FREEZE_V1.md`
- `docs/RUNTIME_GRAMMAR_ALIGNMENT_V1.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `docs/SEMANTIC_CONTRACT_V1.md`

If those newer interface docs disagree with older runtime code, treat the runtime mapping as provisional and prefer the frozen interface docs.

## Stability Rule
Preserve semantic stability first. Avoid redefining loads, `temp_force`, supports, reactions, evaluator contracts, or benchmark meanings during routine implementation unless the user explicitly requests that change.
