# RUNTIME_SEMANTICS_HISTORY_V1

Status: transitional/reference

## Purpose
This document consolidates the main historical runtime documents that described semantic strengthening in the original Bonobo runtime before the project shifted to the standalone `vector_gs_kernel_v1` MVP path.

It preserves the record of:
- generator-readiness work
- unresolved-force and support semantics audits
- semantic strengthening steps
- the graph-derived structural semantics layer
- later runtime enrichment toward richer vector-GS behavior

This material remains useful for future reintegration, but it is not the active MVP implementation guide.

## Scope
This note summarizes and supersedes the following runtime-history docs:
- `docs/GENERATOR_READINESS_V1.md`
- `docs/SEMANTICS_AUDIT_V1.md`
- `docs/SEMANTICS_STRENGTHENING_V1.md`
- `docs/STRUCTURAL_SEMANTICS_LAYER_V1.md`
- `docs/VECTOR_GS_ENRICHMENT_V1.md`

## 1. Generator-Readiness Milestone
The runtime reached a point where:
- `GrammarAction`-based control existed
- non-learning policies could be compared
- support-connected multi-step episodes could be generated

But this did not yet imply honest closure or equilibrium resolution.

The main finding was:
- topology and episode depth improved before semantics did
- the next bottleneck was unresolved-force semantics, not policy machinery

## 2. Semantic Bottleneck Audit
The runtime audit showed that:
- unresolved nodal imbalance lived in `temp_force`
- reaction absorption only acted on force already present at fixed nodes
- support-connected topology could exist without meaningful force transfer

This meant:
- support paths at the graph level were not enough
- closure members could improve topology without improving residual
- episodes often ended by exhausting admissible moves rather than approaching true closure

## 3. Semantic Strengthening Step
One focused runtime step turned direct support engagement into a semantic event by:
- transferring unresolved force to the fixed support node when a direct support link was created
- exposing unresolved-force and absorbed-magnitude histories in artifacts

This made residual behavior more meaningful in some runs, but improvement remained selective rather than universal.

The runtime moved beyond universally flat residual histories, but still did not achieve reliable honest closure.

## 4. Structural Semantics Layer
The runtime then introduced a Bonobo-native structural semantics layer over the canonical graph.

Canonical graph remained responsible for:
- node geometry
- edge connectivity
- support masks
- load metadata
- `temp_force`
- explicit member-force records when known

Derived semantics exposed:
- node-local force lists
- semantic node/member/assembly views
- local line-of-action interpretation
- active/open node semantics
- support/load/internal classification

Bonobo-native semantic types introduced:
- `StructuralForce`
- `StructuralMemberView`
- `StructuralNodeView`
- `StructuralAssemblyView`

This was a semantic translation of richer vector-GS concepts, not a second runtime truth.

## 5. Runtime Vector-GS Enrichment
Later runtime enrichment deepened:
- semantic force records
- local node equilibrium summaries
- support/load access in semantic assembly views
- rule realizations for create/extend/split/connect/closure

The graph remained canonical, while more vector-GS meaning was carried by semantic views and edge/node force metadata.

This made the runtime materially richer, but it also increased adaptation overhead, which contributed to the later tactical shift toward the standalone kernel.

## 6. Why This Still Matters
This runtime semantics history should be preserved because it records:
- what semantic bottlenecks were already discovered
- what forms of graph-derived semantics were already tried
- what support/closure improvements were partially successful
- what future reintegration should avoid re-learning from scratch

It should be read as historical runtime reference, not as the active MVP semantics implementation.
