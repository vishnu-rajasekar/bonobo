# Vector GS Migration Map V1

## Purpose
This note maps Juney's `GDGS` vector-GS concepts into Bonobo's layered architecture. It is an implementation guide, not a second source of truth.

## Core concept mapping
- Juney `Assembly` -> Bonobo canonical [`StructuralGraph`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/model/structural_graph.py) plus derived [`StructuralAssemblyView`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/semantics/assembly_view.py)
- Juney `Node` -> Bonobo [`StructuralNodeView`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/semantics/node.py)
- Juney `Force` -> Bonobo [`StructuralForce`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/semantics/force.py)
- Juney `Member` -> Bonobo [`StructuralMemberView`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/semantics/member.py)
- Juney node force list -> graph-derived node-local force list in the semantics builders
- Juney temp force -> canonical node `temp_force`, surfaced as semantic `temporary` forces
- Juney member force transfer -> semantic member-force records on graph edges plus transfer helpers in `force_ops`

## Force and reaction convention target
- Force vectors are tail-to-head values in their stored direction.
- Force polygons are constructed head-to-tail.
- Applied loads are authored before generation as external boundary forces.
- Support reactions should be solved or initialized from applied loads plus
  support reaction directions so the external global force polygon closes.
- Reaction angles and support reaction directions are benchmark/problem
  parameters, not late viewer annotations.
- Local member-force transfer must preserve this convention; endpoint ordering
  may not silently redefine compression, tension, load, or reaction sign.

## Canonical vs derived
- Canonical graph stores:
  - node geometry
  - edge connectivity
  - fixed/support metadata
  - loadcases
  - `temp_force`
  - explicit node force records when needed
  - explicit edge member-force records when known
- Derived semantics layer provides:
  - node-local force lists
  - arranged local force state
  - local balance / closing vectors
  - member endpoint interpretation
  - assembly-wide active-front and support/load views

## Rule mapping
- Juney Rule 1 `Create Node` -> direct but adapted port
  - Bonobo destination: [`create_node_rule.py`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/grammar/rules/create_node_rule.py)
  - status: provisional prototype
- Juney Rule 2 `Extend Node` -> adapted port
  - Bonobo destination: [`extend_node_rule.py`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/grammar/rules/extend_node_rule.py)
  - status: active
- Juney Rule 3 `Split Node` -> adapted port
  - Bonobo destination: [`split_node_rule.py`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/grammar/rules/split_node_rule.py)
  - status: active
- Juney Rule 4 `Connect with Element` -> adapted port
  - Bonobo destination: [`resolve_two_forces_rule.py`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/grammar/rules/resolve_two_forces_rule.py) plus `node_ops.resolve_two_forces`
  - status: provisional connect realization
- Juney Rule 5 `Connect via Projection` -> adapted port
  - Bonobo destination: [`single_node_root_link_rule.py`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/grammar/rules/single_node_root_link_rule.py) and `node_ops.find_root_link_targets`
  - status: provisional extend/connect realization
- Juney Rule 6 `System Close` -> adapted port
  - Bonobo destination: [`triangle_closure_rule.py`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/grammar/rules/triangle_closure_rule.py), [`loa_intersection_rule.py`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/grammar/rules/loa_intersection_rule.py), and close/connect helpers
  - status: partial
- Juney Rule 7 `End` -> harness-owned stop condition
  - Bonobo destination: experiment / grammar state machine
  - status: intentionally not ported as a heavyweight runtime object

## Helper migration
- `GetTempForce` -> direct port in [`force_ops.py`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/grammar/operators/force_ops.py)
- `FlipTempForceDir` -> direct port in `force_ops.py`
- `GetLineOfAction` -> adapted port through `StructuralNodeView.active_line_of_action`
- `TransferMemberForce` -> adapted port in `force_ops.py`
- `RearrangeForces` -> adapted port in [`node_ops.py`](/Users/apple/Desktop/DEV/bonobo/morph_engine/morph_engine/grammar/operators/node_ops.py)
- `EquilibrateNode` -> adapted port in `node_ops.py` and `StructuralNodeView.equilibrium_summary`
- `ConnectTwoForces` / `ResolveTwoForces` -> adapted ports in `node_ops.py`

## Deferred or intentionally not ported
- Rhino / Grasshopper geometry object model
- Juney's mutable `Assembly` object as a second canonical engine
- full global matrix-style force solve
- non-vector GS backends
