# SEMANTIC_CONTRACT_V1

Status: transitional/reference

This document is benchmark-facing and narrower than the canonical architecture docs.

For current benchmark geometry and scenario truth, prefer:
- [BENCHMARK_MITCHELL_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/BENCHMARK_MITCHELL_V1.md)
- [RUNTIME_CONTROL_PATH_HISTORY_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RUNTIME_CONTROL_PATH_HISTORY_V1.md)
- [RUNTIME_SEMANTICS_HISTORY_V1.md](/Users/apple/Desktop/DEV/bonobo/docs/RUNTIME_SEMANTICS_HISTORY_V1.md)

## Purpose of the Contract
Freeze benchmark-level meanings for the Michell-style planar benchmark so implementation work can remain bounded, comparable across runs, and explicit about what is canonical versus interpretive.

## Current Status / Scope
- this is a benchmark-level contract, not a full project ontology
- it reflects current Bonobo semantics where those are already implemented
- where semantics are still provisional, that uncertainty is stated directly
- this contract applies to the `v1` planar benchmark only

## load
- A load is an externally applied force recorded in `loadcases`.
- In the current workflow, the primary `v1` benchmark uses one point load at `(5, 2)` with vector `(0, -10)`.
- Load is engine truth, not a viewer-only concept.
- GDGS alignment target: applied loads are authored before generation and
  participate in the global force polygon as boundary force vectors.
- Force-vector direction is canonical. Viewer arrowheads must follow the stored
  vector direction rather than redefining load sign.

## support
- A support is a node with restrained degrees of freedom described by a support mask such as `fixed = [ux, uy, uz]`.
- For benchmark framing, the primary `v1` case is a cantilever-style root condition on the left side of the domain.
- The current implementation approximates that root condition with discrete fixed support nodes rather than a continuous boundary.
- That approximation should be treated as benchmark alignment work rather than hidden reinterpretation.

## reaction
- A reaction is currently an evaluator-derived constrained component absorbed from `temp_force` at restrained DOF.
- Reactions are not independently authored as canonical loads in the current workflow.
- If no constrained `temp_force` reaches a support, the evaluator may produce zero reactions.
- GDGS alignment target: reactions should be initialized from the applied loads
  and support reaction directions before growth, such that the external global
  force polygon can close in equilibrium.
- Reaction directions, including reaction-angle ranges where applicable, are
  benchmark parameters rather than viewer-only annotations.
- This target is not yet fully implemented. Until it is, benchmark reports must
  distinguish current evaluator-derived reactions from GDGS-style boundary
  reactions.

## force head/tail convention
- Force vectors are interpreted from tail to head in the stored vector
  direction.
- In a force polygon, consecutive vectors are placed head-to-tail. Global
  equilibrium requires the polygon to close, meaning the vector sum of authored
  loads and solved reactions is zero within tolerance.
- Local nodal equilibrium should follow the same convention: member, load, and
  reaction vectors around a node must close head-to-tail in force space.
- Compression/tension labels, member endpoint direction, and viewer glyphs must
  not silently invert this convention. If a display convention differs for
  readability, the artifact must state that it is display-only.

## node_residual
- `node_residual` is the unresolved force state that remains at a node under the current benchmark interpretation.
- In present code paths, this is closely related to per-node imbalance and the current `temp_force` bookkeeping.
- For `v1`, node residual should be treated as a benchmark diagnostic, not a separate frozen data model beyond what the evaluator already reports.

## temp_force
- `temp_force` currently reflects unresolved nodal imbalance used in growth and debug workflows.
- It is not yet a final, fully frozen physical semantics layer.
- For `v1`, it is the main canonical signal for where equilibrium has not yet been resolved in the implemented workflow.

## member
- A member is an accepted edge in the canonical graph.
- Viewer styling of members is interpretive only unless a member-level structural quantity is explicitly computed and stored.
- In particular, green members or other viewer color codes are not canonical structural truth by themselves.

## candidate geometry
- Candidate geometry is geometry proposed for consideration during a growth step.
- It may include points, segments, or other derived geometric previews associated with candidate rules.
- Candidate geometry is benchmark trace data, not accepted structure.

## accepted graph
- The accepted graph is the canonical graph state after accepted growth actions.
- This is the state used for summaries, descriptors, evaluator runs, and final graph exports.
- Acceptance should remain distinguishable from exploration in logs and digests.

## explored geometry
- Explored geometry is the set of candidate geometric proposals inspected during the run.
- It includes geometry that was considered but not accepted.
- Explored geometry is part of traceability and benchmark interpretation, not part of canonical accepted structure.

## viewer Meaning vs Engine Truth
- Viewer labels, color ramps, green-member styling, and chronology overlays are interpretive only.
- Engine truth lives in the graph state, evaluator outputs, and benchmark artifacts.
- If viewer meaning and engine meaning diverge, engine artifacts take precedence.

## structural Progress (v1)
Structural progress for `v1` should be defined minimally and honestly.

The preferred benchmark-level progress signals are:
- reduced residual magnitude, and/or
- reduced unresolved `temp_force` burden, and/or
- improved support connectivity or closure tendency,

provided the accepted graph remains geometrically admissible.

For `v1`, this is a benchmark interpretation and logging target. It should not be overstated as a fully solved acceptance theory if the current implementation does not yet enforce it consistently.

## Known Semantic Uncertainties
- External equilibrium scaffolds are a benchmark question being clarified, not an implemented fact.
- Support-seeking growth is an immediate benchmark concern, but its explicit mechanism is not yet frozen.
- `temp_force` is currently the practical unresolved-force signal, but its longer-term relation to benchmark-level closure logic may still evolve.
- Reaction semantics are evaluator-derived today; broader support-reaction semantics should not be claimed unless implemented.
- Viewer styling remains provisional and should never be used as the sole source of structural interpretation.
