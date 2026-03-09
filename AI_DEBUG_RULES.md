# AI_DEBUG_RULES.md — Bonobo Debug Workflow

## Scope

This file defines the required workflow for runtime bug fixing.

## Procedure

When a traceback is provided:

1. Start from the traceback, not from broad assumptions.
2. Identify the first bonobo project file in the traceback that plausibly caused the failure.
3. Treat that file as the primary fix location.
4. Implement the smallest possible patch.
5. Preserve semantics from `SKILL.md`.
6. Respect safe and restricted zones from `ARCHITECTURE.md`.
7. Do not refactor unrelated code.
8. Do not change package versions.
9. Validate syntax before rerunning:
   - `python -m py_compile <file>`
10. Rerun only the script that originally failed.
11. Stop after 2 failed attempts and ask for guidance.

## Compatibility rule

For library/API mismatches:
- prefer version-compatible code paths
- do not solve compatibility issues by changing installed packages unless explicitly instructed

## Bug-fix quality bar

A good fix is:
- local
- reversible
- semantically safe
- compatible with current environment
- minimal in scope

## 1) Traceback-First
- Start from the concrete failing traceback.
- Patch the failing call path first.
- Avoid broad cleanups before reproducing/fixing the error.

## 2) Smallest-Patch Policy
- Prefer minimal local edits.
- Keep bug fixes single-file when possible.
- Avoid refactors during debugging unless they are required to remove the failure.

## 3) Syntax Validation
- Validate changed files with syntax checks before runtime checks.
- Prefer quick compile/import checks for touched modules.

## 4) Rerun Scope
- After patching, rerun only the originally failing script/test first.
- Expand validation only after the primary failure is resolved.

## 5) Compatibility-First
- Handle COMPAS/version differences in code paths (fallback logic) rather than changing versions.
- Keep package versions unchanged unless explicitly instructed.

## 6) Attempt Limit
- Stop after 2 failed patch attempts on the same issue.
- Report what failed, what was tried, and request user guidance for next direction.

## Environment Assumptions
- Python 3.10
- Conda env: `morph-engine`
- No implicit dependency upgrades/downgrades.
- Refer environment.yml and pyproject.toml for dependencies. 
- Never break the dependency chain unless absolutely necessary. 
