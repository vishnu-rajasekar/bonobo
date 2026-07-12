# AGENTS.md — Bonobo Agent Operating Rules and Guardrails

## Purpose
This file defines how coding agents must behave when editing the Bonobo repository.

Bonobo prioritizes semantic stability, bounded edits, compatibility, and explicit layer separation. Agents must act conservatively.

## Project Mission
Bonobo is a layered structural generation engine for equilibrium-oriented structural grammars.

Its purpose is to generate structures from the ground up using a small grammar and GS-guided transformations while remaining open to future guidance layers and future GS backends.

## Current Research Priority
The immediate project priority is the IASS guidance study on `feature/guidance-study`, beginning with controlled GDGS-to-VectorGS behavioural parity.

This means:
- stabilise `vector_gs_kernel_v1` as the active technical nucleus
- preserve artifact and trace clarity so generated runs remain inspectable
- validate equilibrium-informed, support-seeking growth before broad reintegration
- use compact benchmark/problem definitions as validators, not as architecture
- distinguish clearly between the active MVP path and the long-term Bonobo runtime target
- do not introduce ML/search complexity before generator evidence justifies it

Important:
- the benchmark is a validator, regression check, and proving ground
- it is not the definition of the grammar
- it is not the definition of long-term equilibrium semantics
- it is not the definition of the final guidance or RL action space
- do not optimize architecture around current benchmark quirks

## Guidance Study Protocol
- Treat the original `GDGS/` implementation as a read-only behavioural reference.
- Port force, temporary-force, node-state, assembly-state, applicability, and rule behaviour into the headless CPython VectorGS kernel incrementally.
- Do not copy Grasshopper component plumbing or add Rhino/Grasshopper runtime dependencies to VectorGS.
- Keep COMPAS Viewer as an artifact consumer, never as part of generation.
- Preserve grammar, policy, evaluator, experiment, and viewer responsibility boundaries.
- New files are prohibited by default.
- Do not commit, push, or open a pull request from `feature/guidance-study` without explicit approval.
- Review every milestone through relevant diffs, tests, artifacts, and viewer evidence where visual behaviour changes.

Engine correctness conditions include force-polygon closure, temporary-force propagation, member action-reaction behaviour, force/member collinearity, valid grammar-state transitions, and duplicate prevention by construction. Guidance and evaluation criteria include material/load-path efficiency, domain compliance, intersections, mechanism avoidance, stability proxies, constructability, member limits, connection complexity, architectural objectives, and policy diversity.

## Default Operating Mode
Assume:
- the project already mostly works
- the traceback identifies the primary failure surface
- minimal edits are preferred over broad improvements

Do not treat bug fixing or documentation updates as opportunities to redesign the codebase.

## Task Classes

### Class A — Local Bug Fix
Use when the user provides a traceback or a concrete local failure.

Rules:
- start from the traceback
- edit the smallest possible amount of code
- modify 1 file if possible
- modify at most 2 files unless explicitly justified
- do not refactor unrelated code
- do not add dependencies
- do not change package versions
- preserve current semantics

### Class B — Scoped Feature Work
Use when the user requests a bounded new capability.

Rules:
- first provide or follow a short implementation plan
- keep changes within the requested module boundary
- preserve project semantics and naming
- avoid opportunistic cleanup
- do not expand scope silently
- keep benchmark-facing outputs, descriptors, and tooling in the experiment or visualization layers unless explicitly instructed otherwise

### Class C — Architectural Change
Use only when explicitly requested.

Rules:
- never perform autonomously
- require explicit human approval
- do not silently move responsibilities across layers
- do not reinterpret semantics without discussion

## Current Phase
The project is currently in:
- vector GS kernel MVP validation
- reproducible seeded kernel experiment work
- artifact and viewer support for kernel runs
- long-term runtime reintegration planning
- not yet RL training

Near-term implementation priority is:
- kernel semantic strengthening
- reproducible kernel experiments
- artifact and trace clarity
- simple policy or heuristic comparison only where it directly helps kernel evaluation
- adapter thinking for later reintegration, not reintegration itself

Not current priority:
- immediate RL implementation
- full runtime reintegration immediately
- broad search/archive work
- polyhedral or Airy implementation yet
- benchmark-specific patching as architectural truth

## Package and Environment Rules
- Never upgrade or downgrade dependencies unless explicitly instructed.
- Never modify Python version, conda environment, or package manifests during ordinary bug fixing.
- Prefer compatibility patches over dependency changes.
- Assume COMPAS API differences may exist across versions.

## Package Rules
- Canonical semantics live in `morph_engine/morph_engine/{model,grammar,evaluator}`.
- The active MVP implementation nucleus currently lives in `morph_engine/morph_engine/vector_gs_kernel_v1`.
- The intended layer stack is:
  1. canonical structural state / structural graph
  2. structural semantic views / semantics layer
  3. abstract grammar rules
  4. GS method-specific realization (`vector_gs` now; polyhedral / Airy later)
  5. evaluator / diagnostics
  6. policy / guidance layer
  7. experiment harness
- Benchmark scenarios, acceptance policies, traces, descriptors, summaries, and derived ML exports belong in `morph_engine/morph_engine/experiments`.
- Kernel-specific generation logic, operators, and direct semantic objects belong in `morph_engine/morph_engine/vector_gs_kernel_v1` until reintegration is explicitly requested.
- Visualization/debug logic belongs in `bonobo/visual` and viewer scripts.
- Integration protocols belong in `morph-rhino-mcp` only.

## Grammar And GS Distinction
The stable top-level grammar rule intents are:
- `StartGeneration`
- `CreateNode`
- `ExtendNode`
- `SplitNode`
- `ConnectTwoNodes`
- `ExtendAndConnectTwoNodes`
- `CloseStructure`
- `EndGeneration`

These are the only true grammar-level rule intents for now.

Graphic statics transformations such as:
- LOA intersection
- projection / closest projection
- closest link
- temp-force handling
- node equilibration
- force transfer
- closure helpers

belong to the GS operator / transformation layer, not to the top-level abstract grammar vocabulary.

Current abstract-rule -> implementation bindings are provisional compatibility mappings.
Do not treat current runtime file names or benchmark-era strategy shims as final architectural truth.

## Guidance Layer Principle
Grammar is the action language for future guidance.

Codex should preserve and strengthen:
- `GrammarAction`
- policy observation extraction
- reward / goal schema
- admissible action enumeration and masks

Do not flatten policy around raw geometry or benchmark-specific quirks.

## Safe Editing Rules
- Keep patches minimal and reversible.
- Do not move files unless requested.
- Do not rename public symbols without explicit instruction.
- Maintain deterministic behavior in experiment/debug tools.
- Do not collapse evaluator semantics into grammar rules.
- Do not collapse grammar rules into GS operators or GS operators into grammar rules.
- Do not redesign the engine around NumPy/PyTorch arrays as canonical state.
- Do not introduce hidden secondary canonical states from legacy object models, derived arrays, or old Rhino / Grasshopper assumptions.
- Do not introduce RL, archive systems, MAP-Elites, GNN search complexity, or similar scope expansion before benchmark validation is explicitly requested.
- Do not let current benchmark rescue behavior define long-term grammar architecture.
- Documentation and code must distinguish:
  - current validated state
  - immediate benchmark target
  - later ambitions

## GitHub Publication Rules
- Do not automatically commit, push, open pull requests, or publish artifacts to GitHub after completing a task or milestone.
- When a milestone such as M1, M2, or M3 reaches its exit gate, report the exact changed files, test output, `git status --short`, and `git diff --stat`.
- Ask for explicit user approval before creating a commit or pushing to GitHub.
- If the user approves publication, create a focused milestone commit, push the current branch, and report the commit SHA and remote branch.
- Never include unrelated dirty worktree changes in a milestone commit unless the user explicitly confirms they belong to that milestone.

## Viewer Inspection Rules
- When implementation changes affect VectorGS geometry, forces, reactions, validity, or viewer output, generate one focused inspection run if doing so is safe and report its exact `kernel_run.json` path.
- The default VectorGS viewer command should open only the latest primary kernel run batch from `experiments/vector_gs_kernel_v1_runs`, not every historical policy or benchmark run.
- Keep older runs accessible through explicit selectors, but do not make the normal viewer workflow browse hundreds of unrelated artifacts.
- Tell the user when a change is visually worth inspecting and provide the exact command:
  `conda run -n morph-engine python scripts/view_vector_gs_kernel_run.py`

Codex should optimize for:
- kernel MVP clarity
- artifact and trace readability
- preserving the abstract rule vocabulary
- preparing future adapters between kernel artifacts and layered Bonobo concepts
- thin adapters and incremental refactors when reintegration work is explicitly requested

Codex should avoid:
- benchmark-specific patching presented as architecture
- promoting GS operators into top-level grammar rules
- overfitting abstract interfaces to `vector_gs`
- overengineering ML before the action language is stable

## Semantic Guardrails
- Do not silently reinterpret `loadcases`, `temp_force`, reactions, support masks, or evaluator channel contracts.
- Do not claim capabilities as implemented if they are still provisional or benchmark-stage.
- If wording clarification is needed, keep the current code semantics intact unless the user explicitly requests semantic change.

## Juney Reference
Juney's codebase is the key structural reference for:
- rule philosophy
- GS operator logic
- structural semantics
- local force propagation concepts

Codex should salvage aggressively from that reference where useful, but must rehouse the logic inside Bonobo's layered architecture.

Do not blindly transplant:
- the old runtime object model as a second canonical truth
- Rhino / Grasshopper assumptions into the core engine
- benchmark-specific logic as general grammar truth

## How To Use Existing Docs
When architectural guidance is needed, consult and keep consistent with:
- `docs/CURRENT_STATUS.md`
- `docs/VECTOR_GS_KERNEL_V1.md`
- `docs/RUNTIME_CONTROL_PATH_HISTORY_V1.md`
- `docs/RUNTIME_SEMANTICS_HISTORY_V1.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `docs/SEMANTIC_CONTRACT_V1.md`

If the active MVP kernel path and older runtime docs diverge, preserve the long-term architecture but treat the kernel docs as the immediate implementation truth for MVP work. Mark older runtime guidance as transitional rather than silently treating it as the current implementation center.

## Stop Conditions
Agents must stop and ask for guidance when:
1. The fix requires semantic redefinition of loads, `temp_force`, reactions, or benchmark acceptance meaning.
2. More than 2 files are needed for a Class A bug fix.
3. Schema or serialization shape must change.
4. Runtime dependency changes seem required.
5. The requested change would blur the graph / grammar / evaluator / experiments boundary.

## Output Expectations
For Class A bug fixes:
- explain the root cause briefly
- implement the smallest patch
- avoid unrelated edits

For Class B feature work:
- maintain narrow scope
- preserve compatibility
- explain how the change fits the current kernel MVP priority rather than later-stage ambitions

For Class C work:
- do not proceed without explicit approval

## Expected Outputs
- Concise change summary.
- Exact files touched.
- Validation status: what was run and what could not be run.
- Known residual risk or wording uncertainty if semantics remain provisional.
