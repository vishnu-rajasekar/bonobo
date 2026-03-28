# GENERATION_CORE_V1

## Terminology
- Episode: one full run
- Step: one accepted action
- Rule: grammar-level move type
- Action: one concrete application of a rule
- GS Operator: reusable structural-geometric operator
- Policy: action selection strategy outside the grammar/operator layer
- Open: unresolved `temp_force` remains
- Closed: no unresolved `temp_force` remains

## Current Structure
- Reusable vector graphic-statics logic now lives in `morph_engine/morph_engine/grammar/operators/`.
- Grammar rules remain thin orchestration wrappers that produce actions and apply graph changes.
- Evaluator remains separate and is still the layer for reactions, imbalance diagnostics, and residual checks.
- Experiment code remains responsible for benchmark loop control, ranking, logging, and termination.

## Implemented Operator Groups
- `force_ops.py`
  - `get_temp_force`
  - `flip_temp_force_dir`
  - `get_line_of_action`
  - `transfer_member_force`
  - directed and bidirected LOA intersection helpers
- `node_ops.py`
  - `get_active_nodes`
  - `rearrange_forces` as a vector-ordering utility
  - `equilibrate_node`
  - `temp_node_equilibrium`
  - `search_connection`
  - `find_closest_projection`
  - `find_closest_link`
  - `connect_two_forces`
  - `connect_two_forces_direct`
  - `resolve_two_forces`
- `member_ops.py`
  - `get_member_nodes`
  - `get_member_force` when explicit member-force metadata exists

## Adaptation Note
- The operator grouping and names are adapted from Juney Lee's graphic-statics library in `GDGS/GraphicStatics.py`.
- Rhino/Grasshopper-specific geometry and force-object semantics were not copied.
- Only the subset that maps cleanly to current Bonobo semantics is implemented directly.

## Deferred Families
- `vector_gs` is the only implemented operator family now.
- Polyhedral operators are deferred.
- Airy/stress-based operators are deferred.

## Benchmark Seed Note
- The primary Michell benchmark no longer starts with pre-inserted support-to-load members.
- Legacy seeded behavior is still available through an explicit scenario flag or the retained secondary sanity benchmark.
