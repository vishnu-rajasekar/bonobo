# ARCHITECTURE.md — Bonobo

## Repo Overview
Bonobo separates structural semantics, search logic, and integration layers.

## Core Semantic Zones (High-Risk)
- `morph_engine/morph_engine/model`
- `morph_engine/morph_engine/grammar`
- `morph_engine/morph_engine/evaluator`

Changes here affect canonical behavior and must be minimal, explicit, and test-backed.

## Visualization / Debug Zones (Low-Risk)
- `bonobo/visual/`
- `scripts/view_last_run.py`

Use these zones for diagnostics, rendering, and interpretation layers.

## Script Entrypoints
- `scripts/run_experiment.py`
- `scripts/run_force_growth.py`
- `scripts/view_last_run.py`

## Integration-Only Zone
- `morph-rhino-mcp/`

Treat as integration code. Do not mix into unit-test-only flows.

## Safe Zones
- `scripts/`
- `bonobo/visual/`
- `docs/`

## Restricted Zones
- Core semantic zones above.
- Any schema-affecting change in `StructuralGraph` serialization.
- Evaluator channel contracts.

## Environment Assumptions
- Python 3.10
- Conda env: `morph-engine`
- Dependency versions are pinned by project setup and should remain unchanged unless explicitly instructed.

## Editing Posture by Task Type
- Bug fix: smallest localized patch in the zone where failure originates.
- Feature work: bounded module scope, avoid semantic drift.
- Architecture change: requires explicit approval before implementation.
