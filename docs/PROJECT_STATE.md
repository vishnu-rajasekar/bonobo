# Bonobo Project State (March 2026)

## 1) Current Architecture
- Layer 1: `StructuralGraph` canonical state (`morph_engine/morph_engine/model/structural_graph.py`)
- Layer 2: Grammar rules + engine (`morph_engine/morph_engine/grammar/`)
- Layer 3: Evaluator channels + ordered pipeline (`morph_engine/morph_engine/evaluator/`)
- Layer 4: Experiment harness (`morph_engine/morph_engine/experiments/`)
- Dev visualization: COMPAS viewer scripts + symbols (`scripts/view_last_run.py`, `bonobo/visual/symbols.py`)

## 2) Implemented Core
### Canonical Graph
- `StructuralGraph` is implemented with:
  - nodes/edges on COMPAS `Network`
  - support DOF (`fixed`)
  - transient force state (`temp_force`)
  - external loads API (`add_load`, `get_loads`)
  - JSON roundtrip (`to_json`, `from_json`)

### Grammar
- Implemented:
  - `Candidate`
  - `GrammarEngine.propose/apply`
  - `ExtendNode`
  - `ConnectNodes`
  - `SplitEdge`
  - `ResolveTempForceV1`
- Behavior:
  - rule application is deterministic in harness (first candidate selected)

### Evaluator
- Pipeline implemented in `Evaluator` with ordered channel execution and shared context.
- Implemented channels:
  - `maxwell_v1`
  - `geometry_planar_v1` (minimal placeholder)
  - `unbalanced_force_v1`
  - `reaction_absorption_v1` (mutates `temp_force` at supports)
  - `global_equilibrium_v1`
  - `structural_redundancy_v1`

### Experiment Harness
- `ExperimentLogger` writes run artifacts:
  - `config.json`, `final_graph.json`, `trace.json`, `metrics.json`
- `ExperimentRunner`:
  - seeds deterministic run via `seed`
  - initializes minimal graph
  - runs grammar/evaluator loop
  - logs outputs
- Config exists: `experiments/configs/basic_growth.json`
- Script exists: `scripts/run_experiment.py`

## 3) Visualization State
### Centralized Symbol Module
- `bonobo/visual/symbols.py` implemented:
  - `add_force_arrow(...)`
  - `add_support_symbol(...)`
  - colors:
    - load: `#377EE3`
    - reaction: `#54A547`
  - compression semantics: arrow head at node
  - Arrow compatibility:
    - uses `compas.geometry.Arrow` when available
    - falls back to `Line + head lines` if Arrow is unavailable

### Viewer Script
- `scripts/view_last_run.py` implemented:
  - loads latest run from `experiments/runs/*`
  - reconstructs graph from `final_graph.json`
  - draws:
    - supports (symbol)
    - load arrows
    - reaction arrows (from `metrics.json`)
    - members (styled by `MemberStyleResolver`)
    - fallback internal nodes as grey points
  - displays equilibrium status label

### Member Styling
- `morph_engine/morph_engine/visual/style_registry.py` currently focused on member semantics:
  - `classify_member(u, v, graph)`
  - `MemberStyleResolver.resolve(u, v, graph)`
  - `has_temp_forces(...)`
  - `is_graph_globally_equilibrated(...)`

## 4) Tests (High-Level)
- Unit tests exist for:
  - graph schema + roundtrip
  - load/temp force APIs
  - grammar rules + engine
  - evaluator channels + pipeline
  - experiment logger + runner
- `morph_engine/tests/test_handshake.py` is integration-style (MCP/local server dependency), not pure unit style.

## 5) Known Gaps / Placeholders
- Empty placeholder modules:
  - `morph_engine/morph_engine/app.py`
  - `morph_engine/morph_engine/grammar/actions.py`
  - `morph_engine/morph_engine/io/json_codec.py`
  - `morph-rhino-mcp/tools/clear.py`
- No explicit member axial force/sign data in core state yet.
- Member compression/tension in viewer is provisional, not solved from structural analysis.
- Current experiment behavior indicates non-convergence in many runs (global equilibrium often false, residual persists).

## 6) Semantics Snapshot (for new chat)
- `loadcases` = external loads.
- `temp_force` = unresolved imbalance carried by nodes/rules.
- `reaction_absorption_v1` absorbs constrained components of `temp_force` at fixed DOF.
- `global_equilibrium_v1` computes residual from `total_load + total_reaction`.
- Grammar is deterministic at harness layer (`candidates[0]`), so reproducibility is controlled by seed + rule order.

