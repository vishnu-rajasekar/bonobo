# STRUCTURAL_SEMANTICS_LAYER_V1

## Why this layer exists
Graph topology plus `temp_force` was enough to prototype growth and benchmark control, but it was too shallow for meaningful vector graphic statics.

Juney's rules act on richer local structural state:
- node-local force lists
- member forces
- temporary forces
- transferred member forces
- local node equilibration / re-equilibration

Bonobo now introduces a native structural semantics layer to expose that richer local state without replacing the canonical graph.

## Canonical vs derived

### Canonical graph stores
- node geometry
- edge connectivity
- support masks
- load metadata
- `temp_force`
- explicit edge member-force records when known
- generic node/edge metadata

### Semantics layer derives
- node-local force lists
- semantic node/member/assembly views
- line of action from node-local unresolved force state
- member-force views oriented at each endpoint
- active/open node semantics
- support/load/internal node classification

The graph remains the single source of truth.
The semantics layer is a structured, graph-derived view.

## Bonobo-native semantic types
- `StructuralForce`
- `StructuralMemberView`
- `StructuralNodeView`
- `StructuralAssemblyView`

Conceptual bridge to Juney:
- Juney `Assembly` -> Bonobo `StructuralAssemblyView`
- Juney `Node` -> Bonobo `StructuralNodeView`
- Juney `Force` -> Bonobo `StructuralForce`
- Juney `Member` -> Bonobo `StructuralMemberView`

This is a semantic translation, not a runtime transplant.

## What the semantics layer does now
- builds local semantic force lists from loads, temp-force, and explicit member-force records
- gives nodes a Bonobo-native unresolved-force summary and active line of action
- lets member forces be stored canonically on edges as lightweight records
- lets rules consume local structural semantics before mutating the graph

## Rules currently refactored to use it
- `ExtendNodeRule`
- `SplitNodeRule`
- `get_line_of_action(...)` now reads the node semantic view rather than normalizing raw `temp_force` directly

## What became richer
`ExtendNodeRule` now:
- reads a semantic node view
- derives line of action from node-local unresolved-force state
- writes an explicit member-force record onto the new edge
- preserves unresolved force on the new node while making the member-force transition explicit

`SplitNodeRule` now:
- reads a semantic node view
- decomposes unresolved force across branches
- writes member-force records for both new branch edges
- keeps the branch-level force transition explicit in graph-backed semantics

## What is still missing
- a full member-force solve
- full node re-equilibration from complete local force polygons
- universally reliable closure-to-equilibrium transition
- polyhedral and Airy backends

This step makes Bonobo materially closer to Juney-like vector-GS semantics while preserving the current layered architecture and keeping the graph canonical.
