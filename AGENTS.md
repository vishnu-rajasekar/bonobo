# AGENTS.md — Panther

Panther is a structural grammar research engine with physics-informed evaluation.

## Core Rules
1. Unit tests must never require Rhino or MCP.
2. Integration code must not be placed in unit test directories.
3. Do not change schema versions without updating tests.
4. Grammar rules must implement `propose()` and `apply()`.
5. Evaluator channels must return:
   { "valid": bool, "metrics": dict, "signals": dict }

## Running Checks
pytest

## Code Locations
- Canonical graph: morph_engine/morph_engine/model/
- Grammar rules: morph_engine/morph_engine/grammar/rules/
- Evaluator channels: morph_engine/morph_engine/evaluator/channels/
- IO / JSON: morph_engine/morph_engine/io/
- Learning (future): morph_engine/morph_engine/learning/
- Interfaces (future): morph_engine/morph_engine/interfaces/

Do not introduce heavy dependencies into core modules.
