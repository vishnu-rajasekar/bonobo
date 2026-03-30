# DOCS_INDEX

## Purpose
This file defines the current documentation hierarchy for Bonobo.

The goal is to keep a small canonical doc set, preserve useful project history, and make stale or transitional material explicit rather than ambiguous.

## Status Labels
- `canonical`: current source of truth
- `transitional/reference`: useful, but narrower in scope or tied to an active migration/refactor
- `historical/archive`: preserved for project evolution and older thinking; not authoritative for current implementation

## Canonical Docs
- [AGENTS.md](/Users/apple/Desktop/DEV/bonobo/AGENTS.md)
  - primary Codex / agent operating rules
- [SKILL.md](/Users/apple/Desktop/DEV/bonobo/SKILL.md)
  - working vocabulary, refactor priorities, stable interfaces
- [CONVENTIONS.md](/Users/apple/Desktop/DEV/bonobo/CONVENTIONS.md)
  - naming, testing, and serialization conventions
- [README.md](/Users/apple/Desktop/DEV/bonobo/README.md)
  - project-facing overview
- [ARCHITECTURE.md](/Users/apple/Desktop/DEV/bonobo/ARCHITECTURE.md)
  - current architecture truth
- [ROADMAP.md](/Users/apple/Desktop/DEV/bonobo/ROADMAP.md)
  - project direction and phase ordering
- [docs/BENCHMARK_MITCHELL_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/BENCHMARK_MITCHELL_V1.md)
  - canonical benchmark definition
- [docs/PROJECT_EVOLUTION.md](/Users/apple/Desktop/DEV/bonobo/docs/PROJECT_EVOLUTION.md)
  - concise narrative of how the project evolved

## Transitional / Reference Docs
- [docs/SEMANTIC_CONTRACT_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/SEMANTIC_CONTRACT_V1.md)
  - benchmark semantics contract; useful but still benchmark-stage and narrower than architecture docs
- [docs/NEXT_STEPS_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/NEXT_STEPS_V1.md)
  - immediate benchmark implementation brief
- [docs/GENERATION_CORE_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/GENERATION_CORE_V1.md)
  - GS-operator refactor summary
- [docs/RL_INTERFACE_FREEZE_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RL_INTERFACE_FREEZE_V1.md)
  - Step 1 interface freeze
- [docs/RUNTIME_GRAMMAR_ALIGNMENT_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RUNTIME_GRAMMAR_ALIGNMENT_V1.md)
  - Step 2 runtime/action alignment
- [docs/RESEARCH_LOG.md](/Users/apple/Desktop/DEV/bonobo/docs/RESEARCH_LOG.md)
  - terse research milestones
- [abstract.md](/Users/apple/Desktop/DEV/bonobo/abstract.md)
  - research-facing abstract, not implementation authority

## Historical / Archive Docs
Stored in `docs/archive/`.

These are preserved because they contain useful historical context, but they are not authoritative for the current repo state.

- [ARCHITECTURE_legacy.md](/Users/apple/Desktop/DEV/bonobo/docs/archive/ARCHITECTURE_legacy.md)
- [PROJECT_STATE_2026-03.md](/Users/apple/Desktop/DEV/bonobo/docs/archive/PROJECT_STATE_2026-03.md)
- [project_outline_reference.md](/Users/apple/Desktop/DEV/bonobo/docs/archive/project_outline_reference.md)
- [notes_brainstorm.md](/Users/apple/Desktop/DEV/bonobo/docs/archive/notes_brainstorm.md)
- [test_prompt_dump.md](/Users/apple/Desktop/DEV/bonobo/docs/archive/test_prompt_dump.md)

## Package Readmes
- [morph_engine/README.md](/Users/apple/Desktop/DEV/bonobo/morph_engine/README.md)
  - package-level orientation only
- [morph-rhino-mcp/README.md](/Users/apple/Desktop/DEV/bonobo/morph-rhino-mcp/README.md)
  - integration package orientation only

## Changelog
- [CHANGELOG.md](/Users/apple/Desktop/DEV/bonobo/CHANGELOG.md)
  - lightweight version/history summary
  - not a substitute for architecture or semantic docs

## Precedence Order
1. [AGENTS.md](/Users/apple/Desktop/DEV/bonobo/AGENTS.md)
2. [SKILL.md](/Users/apple/Desktop/DEV/bonobo/SKILL.md)
3. [CONVENTIONS.md](/Users/apple/Desktop/DEV/bonobo/CONVENTIONS.md)
4. [README.md](/Users/apple/Desktop/DEV/bonobo/README.md)
5. [ARCHITECTURE.md](/Users/apple/Desktop/DEV/bonobo/ARCHITECTURE.md)
6. [ROADMAP.md](/Users/apple/Desktop/DEV/bonobo/ROADMAP.md)
7. [docs/BENCHMARK_MITCHELL_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/BENCHMARK_MITCHELL_V1.md)
8. [docs/RL_INTERFACE_FREEZE_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RL_INTERFACE_FREEZE_V1.md)
9. [docs/RUNTIME_GRAMMAR_ALIGNMENT_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RUNTIME_GRAMMAR_ALIGNMENT_V1.md)
10. other transitional/reference docs
11. `docs/archive/` historical material

## Archive / Retire Policy
- If a doc is still useful but no longer authoritative, move it to `docs/archive/` and make its status explicit.
- If a doc duplicates canonical content, reduce it to a pointer or archive it.
- Avoid leaving stale docs in active top-level locations without a status label.
