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
- [docs/CURRENT_STATUS.md](/Users/apple/Desktop/DEV/bonobo/docs/CURRENT_STATUS.md)
  - current strategic decision, active MVP path, and immediate work focus
- [ARCHITECTURE.md](/Users/apple/Desktop/DEV/bonobo/ARCHITECTURE.md)
  - current architecture truth
- [ROADMAP.md](/Users/apple/Desktop/DEV/bonobo/ROADMAP.md)
  - project direction and phase ordering
- [docs/VECTOR_GS_KERNEL_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/VECTOR_GS_KERNEL_V1.md)
  - active MVP kernel description and usage
- [docs/BENCHMARK_MITCHELL_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/BENCHMARK_MITCHELL_V1.md)
  - canonical benchmark definition
- [docs/PROJECT_EVOLUTION.md](/Users/apple/Desktop/DEV/bonobo/docs/PROJECT_EVOLUTION.md)
  - concise narrative of how the project evolved

## Transitional / Reference Docs
- [docs/SEMANTIC_CONTRACT_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/SEMANTIC_CONTRACT_V1.md)
  - benchmark semantics contract; useful but still benchmark-stage and narrower than architecture docs
- [docs/PAPER_EXPERIMENT_PLAN_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/PAPER_EXPERIMENT_PLAN_V1.md)
  - conference-paper-oriented experiment plan for the kernel MVP
- [docs/RUNTIME_CONTROL_PATH_HISTORY_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RUNTIME_CONTROL_PATH_HISTORY_V1.md)
  - consolidated history of the original runtime control path, interface freeze, and policy study work
- [docs/RUNTIME_SEMANTICS_HISTORY_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RUNTIME_SEMANTICS_HISTORY_V1.md)
  - consolidated history of the original runtime semantics strengthening work
- [docs/VECTOR_GS_MIGRATION_MAP_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/VECTOR_GS_MIGRATION_MAP_V1.md)
  - bridge mapping from Juney-style vector GS concepts into Bonobo runtime concepts
- [abstract.md](/Users/apple/Desktop/DEV/bonobo/abstract.md)
  - research-facing abstract, not implementation authority

## Historical / Archive Docs
Stored in `docs/archive/`.

These are preserved because they contain useful historical context, but they are not authoritative for the current repo state.

- [PROJECT_STATE_2026-03.md](/Users/apple/Desktop/DEV/bonobo/docs/archive/PROJECT_STATE_2026-03.md)
- [project_outline_reference.md](/Users/apple/Desktop/DEV/bonobo/docs/archive/project_outline_reference.md)
- [notes_brainstorm.md](/Users/apple/Desktop/DEV/bonobo/docs/archive/notes_brainstorm.md)

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
5. [docs/CURRENT_STATUS.md](/Users/apple/Desktop/DEV/bonobo/docs/CURRENT_STATUS.md)
6. [ARCHITECTURE.md](/Users/apple/Desktop/DEV/bonobo/ARCHITECTURE.md)
7. [ROADMAP.md](/Users/apple/Desktop/DEV/bonobo/ROADMAP.md)
8. [docs/VECTOR_GS_KERNEL_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/VECTOR_GS_KERNEL_V1.md)
9. [docs/BENCHMARK_MITCHELL_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/BENCHMARK_MITCHELL_V1.md)
10. [docs/RUNTIME_CONTROL_PATH_HISTORY_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RUNTIME_CONTROL_PATH_HISTORY_V1.md)
11. [docs/RUNTIME_SEMANTICS_HISTORY_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RUNTIME_SEMANTICS_HISTORY_V1.md)
12. other transitional/reference docs
13. `docs/archive/` historical material

## Archive / Retire Policy
- If a doc is still useful but no longer authoritative, move it to `docs/archive/` and make its status explicit.
- If a doc duplicates canonical content, reduce it to a pointer or archive it.
- Avoid leaving stale docs in active top-level locations without a status label.
