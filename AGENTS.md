# AGENTS.md — Bonobo Agent Operating Rules and Guardrails

## Purpose
This file defines how coding agents must behave when editing the Bonobo repository.

Bonobo prioritizes semantic stability, bounded edits, compatibility, and explicit layer separation. Agents must act conservatively.

## Current Research Priority
The immediate project priority is benchmark validation on a 2D Michell-style planar problem.

This means:
- validate equilibrium-informed, support-seeking growth before expanding scope
- preserve admissible intermediate states as an explicit concern
- treat material efficiency as the first benchmark performance target
- distinguish clearly between current benchmark goals and later ambitions
- do not introduce ML/search complexity before benchmark evidence justifies it

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

## Package and Environment Rules
- Never upgrade or downgrade dependencies unless explicitly instructed.
- Never modify Python version, conda environment, or package manifests during ordinary bug fixing.
- Prefer compatibility patches over dependency changes.
- Assume COMPAS API differences may exist across versions.

## Package Rules
- Canonical semantics live in `morph_engine/morph_engine/{model,grammar,evaluator}`.
- Benchmark scenarios, acceptance policies, traces, descriptors, summaries, and derived ML exports belong in `morph_engine/morph_engine/experiments`.
- Visualization/debug logic belongs in `bonobo/visual` and viewer scripts.
- Integration protocols belong in `morph-rhino-mcp` only.

## Safe Editing Rules
- Keep patches minimal and reversible.
- Do not move files unless requested.
- Do not rename public symbols without explicit instruction.
- Maintain deterministic behavior in experiment/debug tools.
- Do not collapse evaluator semantics into grammar rules.
- Do not redesign the engine around NumPy/PyTorch arrays as canonical state.
- Do not introduce RL, archive systems, MAP-Elites, GNN search complexity, or similar scope expansion before benchmark validation is explicitly requested.
- Documentation and code must distinguish:
  - current validated state
  - immediate benchmark target
  - later ambitions

## Semantic Guardrails
- Do not silently reinterpret `loadcases`, `temp_force`, reactions, support masks, or evaluator channel contracts.
- Do not claim capabilities as implemented if they are still provisional or benchmark-stage.
- If wording clarification is needed, keep the current code semantics intact unless the user explicitly requests semantic change.

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
- explain how the change fits the current benchmark priority rather than later-stage ambitions

For Class C work:
- do not proceed without explicit approval

## Expected Outputs
- Concise change summary.
- Exact files touched.
- Validation status: what was run and what could not be run.
- Known residual risk or wording uncertainty if semantics remain provisional.
