from dataclasses import dataclass


@dataclass(frozen=True)
class VectorGSOperatorSpec:
    operator_id: str
    current_symbol: str
    current_module: str
    role: str
    provisional: bool
    notes: str


VECTOR_GS_OPERATOR_REGISTRY = [
    VectorGSOperatorSpec(
        operator_id="loa_intersection",
        current_symbol="LOAIntersectionRule",
        current_module="morph_engine.grammar.rules.loa_intersection_rule",
        role="vector_gs_operator",
        provisional=True,
        notes="Method-specific LOA construction helper. Not a top-level abstract grammar rule.",
    ),
    VectorGSOperatorSpec(
        operator_id="temp_force_resolution",
        current_symbol="ResolveTempForceV1",
        current_module="morph_engine.grammar.rules.resolve_temp_force_v1",
        role="vector_gs_operator",
        provisional=True,
        notes="Vector GS temp-force propagation helper. Not a frozen abstract grammar rule.",
    ),
    VectorGSOperatorSpec(
        operator_id="local_node_equilibration",
        current_symbol="equilibrate_node",
        current_module="morph_engine.grammar.operators.node_ops",
        role="vector_gs_operator",
        provisional=True,
        notes="Graph-derived local node balance helper used by enriched vector-GS rule realizations.",
    ),
    VectorGSOperatorSpec(
        operator_id="member_force_transfer",
        current_symbol="transfer_member_force",
        current_module="morph_engine.grammar.operators.force_ops",
        role="vector_gs_operator",
        provisional=True,
        notes="Translates member-force semantics between local rule contexts without introducing a second engine state.",
    ),
    VectorGSOperatorSpec(
        operator_id="triangle_closure_strategy",
        current_symbol="TriangleClosureRule",
        current_module="morph_engine.grammar.rules.triangle_closure_rule",
        role="vector_gs_closure_strategy",
        provisional=True,
        notes="Current vector GS closure strategy backing CloseStructure intent. Provisional runtime realization.",
    ),
    VectorGSOperatorSpec(
        operator_id="resolve_two_forces_strategy",
        current_symbol="ResolveTwoForcesRule",
        current_module="morph_engine.grammar.rules.resolve_two_forces_rule",
        role="vector_gs_connect_strategy",
        provisional=True,
        notes="Current vector GS direct two-node connection strategy. Provisional runtime realization.",
    ),
    VectorGSOperatorSpec(
        operator_id="single_node_root_link_strategy",
        current_symbol="SingleNodeRootLinkRule",
        current_module="morph_engine.grammar.rules.single_node_root_link_rule",
        role="vector_gs_extend_connect_strategy",
        provisional=True,
        notes="Benchmark-specific recovery strategy. Provisional and not part of the frozen abstract vocabulary.",
    ),
]


VECTOR_GS_NON_RULE_OPERATORS = [
    "loa_intersection",
    "temp_force_resolution",
    "closest_projection",
    "closest_link",
    "node_equilibration",
    "local_node_equilibration",
    "member_force_transfer",
    "resolve_two_forces_strategy",
    "triangle_closure_strategy",
]
