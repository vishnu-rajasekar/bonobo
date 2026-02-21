# SKILL.md — Structural Semantics

Panther architecture:

1. StructuralGraph (canonical state)
2. Grammar (state transitions)
3. Evaluator (physics semantics)
4. Learning (policy selection over grammar)

Loads:
- loadcases = external loads
- temp_force = imbalance vector used for growth

Supports:
- fixed = [ux, uy, uz] (1 = restrained)

Reactions:
- reaction = -temp_force component at fixed DOF

Channels:
- Must be deterministic
- May mutate graph only if explicitly intended

Diversity:
- Will be handled at experiment layer (not evaluator layer)
