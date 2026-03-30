# Vector GS Enrichment V1

## Why this step happened
Step 7 introduced Bonobo-native structural semantics, but only `ExtendNode`, `SplitNode`, and LOA were using that layer deeply. Connect, projection, and closure realizations were still mostly topology changes plus `temp_force`.

## What was enriched
- richer semantic force records:
  - `direction_kind`
  - `target_node`
  - `status`
  - `provenance`
- richer semantic node state:
  - explicit graph node-force ingestion
  - non-temporary force views
  - local balance / equilibrium summary
  - preferred unresolved-force LOA
- richer semantic assembly view:
  - support/load node access
  - semantically resolved node filtering

## Rule realizations materially deepened
- `CreateNode`
  - now has a provisional vector-GS floating-seed realization
- `ExtendNode`
  - continues to create semantic member-force records
- `SplitNode`
  - continues to decompose unresolved force into branch member-force records
- `ConnectTwoNodes`
  - direct connection now creates semantic member-force records instead of only clearing temp forces
- `ExtendAndConnectTwoNodes`
  - root/support linking now writes semantic member-force records on created members
- `CloseStructure`
  - closure now carries a provisional closing-force semantic record rather than only adding a bar
- `LOA intersection`
  - now delegates to the enriched connect helper so created links carry semantics too

## What stays canonical
The graph remains the single source of truth:
- nodes
- edges
- support/load metadata
- `temp_force`
- explicit node force records
- explicit edge member-force records

The semantics layer remains derived and synchronized from that graph.

## What still remains before full closure
- local re-equilibration is richer but still partial
- closure/support semantics are still provisional, not a full mechanics solve
- member-force semantics are explicit on more edges, but not globally solved everywhere
- support-connected growth is richer, but reliable fully equilibrated closure still needs more work

## How to inspect the engine now
- run policy baseline comparisons
- inspect representative runs in the viewer
- check edge `force` metadata and node semantic views
- compare support-path, residual, and unresolved-force histories together rather than reading topology alone

