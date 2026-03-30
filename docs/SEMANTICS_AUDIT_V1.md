# SEMANTICS_AUDIT_V1

## Scope
This note captures the semantic bottleneck exposed after Step 5: support-connected multi-step episodes existed, but unresolved force and residual stayed flat.

## Where unresolved force lives now
- Bonobo stores unresolved nodal imbalance on nodes as `temp_force`.
- `ReactionAbsorptionChannel` only absorbs force that is present on fixed support nodes.
- `GlobalEquilibriumChannel` computes residual from total load plus absorbed support reaction.

## What the representative runs showed before Step 6
Representative support-connected runs from Step 5 had the pattern:
- topology continued for several accepted steps
- support paths existed through real edges
- `temp_force_count` stayed flat
- residual stayed flat at `10.0`
- episodes ended by `no_admissible_candidate`

Example pattern from a support-connected run:
- `split_node_rule` increased active unresolved fronts
- `triangle_closure_rule` added closure members but did not change force state
- `single_node_root_link_rule` created a direct support edge but left `temp_force` on the free source node
- reaction absorption therefore saw nothing new to absorb

## Actual semantic bottleneck
The key gap was:
- direct support engagement was still mostly a topology event, not a force-transfer event

That meant:
- support-connected topology was real at the graph level
- but semantic support engagement was incomplete unless unresolved force itself reached a fixed node
- closure members could improve shape without improving residual

## Immediate semantic targets
1. When a direct support link is formed from an active unresolved front, unresolved force should transfer to the fixed support node.
2. Run artifacts should report unresolved-force magnitude and support-absorption events, not only edge/node counts.
3. Residual improvement should remain tied to actual support absorption, not to purely topological closure.
