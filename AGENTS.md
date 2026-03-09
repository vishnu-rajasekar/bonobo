# AGENTS.md — Bonobo Agent Operating Rules and Guardrails

## Purpose

This file defines how coding agents must behave when editing the bonobo repository.

Bonobo prioritizes semantic stability, bounded edits, and compatibility.
Agents must act conservatively.

## Default operating mode

Assume:
- the project already mostly works
- the traceback identifies the primary failure surface
- minimal edits are preferred over broad improvements

Do not treat bug fixing as an opportunity to redesign the codebase.

## Task classes

### Class A — Local bug fix
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

### Class B — Scoped feature work
Use when the user requests a bounded new capability.

Rules:
- first provide or follow a short implementation plan
- keep changes within the requested module boundary
- preserve project semantics and naming
- avoid opportunistic cleanup
- do not expand scope silently

### Class C — Architectural change
Use only when explicitly requested.

Rules:
- never perform autonomously
- require explicit human approval
- do not silently move responsibilities across layers
- do not reinterpret semantics without discussion

## Package and environment rules

- Never upgrade or downgrade dependencies unless explicitly instructed.
- Never modify Python version, conda environment, or package manifests during ordinary bug fixing.
- Prefer compatibility patches over dependency changes.
- Assume COMPAS API differences may exist across versions.

## Safe editing rules

- Visualization bugs should remain in `bonobo/visual/` or the specific failing script.
- Do not edit core semantic layers during viewer/debug fixes.
- Do not restructure directories.
- Do not create abstractions unless necessary for the requested task.

## Stop conditions

Agents must stop and ask for guidance when:
- the fix requires more than 2 files for a local bug
- the traceback points to ambiguous root causes across layers
- 2 repair attempts have failed
- fixing the issue appears to require dependency changes
- the change would alter structural semantics

## Output expectations

For Class A bug fixes:
- explain the root cause briefly
- implement the smallest patch
- avoid unrelated edits

For Class B feature work:
- maintain narrow scope
- preserve compatibility

For Class C work:
- do not proceed without explicit approval

## Global Rules
1. Prefer traceback-driven debugging over speculative rewrites.
2. Preserve canonical semantics in model/grammar/evaluator layers.
3. Do not change package versions or add heavy dependencies unless explicitly instructed.
4. Keep unit tests independent of Rhino/MCP integration.

## Task Classes

### Class A — Local Bug Fix
- Trigger: clear traceback or isolated defect.
- Method:
  - smallest possible patch,
  - one file preferred,
  - two files max unless justified.
- Prohibited:
  - refactors,
  - dependency changes,
  - architectural reshaping.

### Class B — Scoped Feature Work
- Start with a short plan (scope, touched files, risk).
- Keep edits bounded to declared modules.
- Preserve existing semantics unless task explicitly changes them.
- Add or update tests only for touched behavior.

### Class C — Architectural Change
- Never autonomous.
- Requires explicit approval before code edits.
- Must include impact on schema, semantics, and migration/testing strategy.

## Package Rules
- Canonical semantics live in `morph_engine/morph_engine/{model,grammar,evaluator}`.
- Visualization/debug logic belongs in `bonobo/visual` and viewer scripts.
- Integration protocols belong in `morph-rhino-mcp` only.

## Safe Editing Rules
- Keep patches minimal and reversible.
- Do not move files unless requested.
- Do not rename public symbols without explicit instruction.
- Maintain deterministic behavior in experiment/debug tools.

## Stop Conditions
Stop and ask for direction when:
1. The fix requires semantic redefinition (loads/temp_force/reaction meanings).
2. More than 2 files are needed for a Class A bug fix.
3. Schema or serialization shape must change.
4. Runtime dependency changes seem required.

## Expected Outputs
- Concise change summary.
- Exact files touched.
- Validation status (what was run, what could not be run).
- Known residual risk if unresolved.
